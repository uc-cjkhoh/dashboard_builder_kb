# ClickHouse: compiling calculated fields and aggregates

How a `calc` tree becomes SQL, and the one aggregate writer shared by plain and calculated measures. The rest of the SQL: [clickhouse-integration.md](clickhouse-integration.md). The tree's wire format and rules: [api-calculated-fields.md](api-calculated-fields.md).

## The compile path

A `calc` tree becomes SQL in four steps; no formula text and no literal is ever written into SQL.

1. **Request rules** (`RequestRules.ValidateQuery`, no catalog): the depth, node and label limits ([api.md § Limits](api.md#limits)) and the role rules ([api-calculated-fields.md § Rules](api-calculated-fields.md#rules)). The tree check is `CalcValidator.CheckLimits`.
2. **Catalog** (gateway `CompileCalcAsync` → `ResolveCalcRefsAsync`):
   - Every `field` node (`CalcFields`) is first checked against the tables already in the query (`from` and
     joins). A field on any other table is a 400 "Field references a table not in the query." whether or not
     the column exists. This runs before any catalog lookup, so a calculation never causes a `DESCRIBE` of a
     table outside the query.
   - The field then goes through `ColumnsOf` + `QualifyAsync`: `DESCRIBE`-validated (already cached for tables
     in the query), quoted by `Identifier.cs`, aliased `t0` / `tN`. So a calculation may reference any table in
     the query, including a left-joined one (its unmatched side is NULL under `join_use_nulls`).
   - A column the catalog doesn't know on such a table is left out, so the validator names it ("Unknown field t.c.").
3. **Validate** (`ClickHouse/Calc/CalcValidator.cs`): types the tree bottom-up from the column categories
   (number, text, date, boolean; anything else is refused) and derives aggregate vs row-level. A bad tree is
   rejected with a `CalcException` (a plain sentence plus the node path, `measures[0].calc.l.arg`), which the
   gateway reports as a 400. The gateway re-checks the role and the `sum` / `avg`-needs-a-number rule against
   the derived type (`CalcMeasureSql`, `CalcDimensionSql`).
4. **Compile** (`ClickHouse/Calc/CalcCompiler.cs`):
   - **Numbers and literals:** numeric columns are widened with `toFloat64(...)` (no unsigned wrap, no integer or `Decimal` rounding).
     `a / b` → `(a / nullIf(b, 0))` (division by zero is NULL, never `inf`). Each number literal is bound as `{c{n}p{m}:Float64}`
     and each text literal as `{c{n}p{m}:String}`; `c{n}` is unique per compiled calculation in the request.
   - **Aggregates** go through the shared `AggregateSql` (table below), so a calculated `SUM` is scaled and a `COUNTD` estimated
     exactly as a plain measure is. A row-level measure is then wrapped by its pill aggregation; an aggregate tree is used as is;
     a dimension groups by its row-level expression.
   - **Logic nodes:** `(a = b)` (also `!= < <= > >=`), `and(a, b)`, `or(a, b)`, `not(a)`, `if(c, a, b)` (IF/IIF),
     `multiIf(c1, a1, …, else)` (CASE; `NULL` last without an ELSE), `ifNull(a, b)`, `isNull(a)`, `true` / `false` / `NULL` keywords, `(a IN ({p0}, {p1}, …))` (every value a bound `Float64` or `String`; a NULL value gives NULL). A NULL condition is
     not true: IF takes its else, CASE the next WHEN (pinned by the live smoke test).
   - **Text functions** (`fn` nodes, every argument compiled once in source order): `toString(x)` (`TEXT`; `STR` parses to the same `text` node), `lowerUTF8`, `upperUTF8`, `trimBoth`/`trimLeft`/`trimRight`, `toFloat64(lengthUTF8(…))`, `leftUTF8`/`rightUTF8(t, {UInt32})`, `substringUTF8(t, {UInt32}, {UInt32})` (`MID`), `toFloat64(positionUTF8(t, s))` (`FIND`), `replaceAll`, `concat`, `(position(t, s) > 0)`, `startsWith`,
     `endsWith`, the case-insensitive twins `(positionCaseInsensitiveUTF8(t, s) > 0)` and `startsWith`/`endsWith(lowerUTF8(t), lowerUTF8(s))` (new function names `ICONTAINS` etc., not a flag, so the wire shape stays `fn` + `args`), `if(isNull(t), NULL, arrayElementOrNull(splitByString({sep:String}, assumeNotNull(t)), {k:UInt32}))`.
   - **Date functions:**
     - `toFloat64(dateDiff({unit:String}, a, b))`. `dateDiff` on a `Date` with a time unit reads midnight to midnight (24 hours a day).
     - `addYears`/`addQuarters`/`addMonths`/`addWeeks`/`addDays`/`addHours`/`addMinutes`/`addSeconds(d, {n:Int32})` (fixed name per unit, unit never in SQL), applied to `toDateTime64(d, 0)` and
       kept only strictly between 1900-01-03 and 2299-12-29 UTC, else NULL (a plain `Date` would wrap and a `DateTime` clamp to 1970 on overflow).
     - `toFloat64(toYear|toMonth|toDayOfMonth|toQuarter|toISOWeek|toDayOfWeek(d))`.
     - `toFloat64(toISOYear(d))`; `dateName('weekday'|'month', toDateTime64(d, 0))` (English, locale-free; the part is whitelisted and written as a fixed word, nothing bound).
    - `DATETRUNC`: `dateTrunc('<unit>', toDateTime64(d, 0))` with the whitelisted unit as a fixed word. The year to week units answer a `Date32`, so they are wrapped in `toDateTime64(…, 0)` and every unit returns one `DateTime64` type.
    - `MAKEDATE(y, m, d)`: `makeDate32` rolls an impossible day over (30 Feb is 1 Mar) and answers 1970-01-01 for a bad month, so the call is guarded: `if(y = floor(y) AND m = floor(m) AND d = floor(d) AND y >= 1901 AND y <= 2298 AND m >= 1 AND m <= 12 AND d >= 1 AND d <= 31 AND toDayOfMonth(x) = d, toDateTime64(x, 0), NULL)` with `x = makeDate32(toInt32(y), toInt32(m), toInt32(d))`. The day round trip catches the rolled dates; a NULL part makes the condition NULL, so the answer is NULL.
    - `DATE(t)` = `TypeCast.ParseDate`: the cast's digit guard, then `toDate` of `parseDateTime64BestEffortOrNull(t, 0)`, kept only between 1970-01-02 and 2149-01-01 (else NULL).
   - **Booleans:** a boolean-typed calculation is wrapped in `toBool(...)`. As a dimension it is `toString(...)` of that, so keys read `true` / `false` (a plain Bool field keeps `True` / `False`).

**One compile, one parameter list.**

- Each calculation is compiled once. Its SQL string is reused in the page, the total (`count()` over the
  grouped query), the Other statement and inline in the Top-N subquery.
- Every statement is sent with the request's one `parameters` list (filter values `p{i}` and calculation
  literals `c{n}p{m}`). The auto date-grain probe reuses only the date expression and the `WHERE`, so it is
  sent just the parameters its SQL names (`ParametersUsedBy`).
- A calculated dimension is never date-grouped: `dateBucket` takes the first *real* temporal dimension
  wherever the calculation sits.
- The result cache key includes the tree, so two requests that differ only in a calculation never share a result.
- **Tests:** `CalcCompilerTests`, `CalcValidatorTests`, `CalcRulesTests`, `CalcGatewayTests`, `CalcJsonTests`, and the
  shared fixture (also run by `node --test`). Live tests run against the dev app and a real ClickHouse; the script creates and drops the tables
  and checks results against hand-written `SELECT`s or hand-computed values: `tests/live/calc-smoke.mjs`
  (`test_cj.calc_smoke_*`), `logic-smoke.mjs` (`bk_logic`), `text-smoke.mjs` (`bk_text`).

**Compile spikes** (`node tests/live/calc-spikes.mjs`, SELECT only, inline sources). A bound parameter inside a
`SELECT` / `GROUP BY` expression works (also `GROUP BY` the full expression). `toFloat64` over `UInt32`,
`Decimal(18,2)` and `Nullable(Float64)` works: there is no unsigned wrap (`toFloat64(UInt32 2) - toFloat64(Decimal 10.00)` is
`-8`), and a NULL operand makes the result NULL. `sum(x) / nullIf(sum(y), 0)` with every `y` = 0 returns JSON `null`;
`nullIf` keeps the SQL NULL for other writers and downstream arithmetic.

## Aggregates, exact and approximate

`AggregateSql` is one function for plain and calculated measures. "Sampled" means `approximate` on a base table with a sampling key, read `SAMPLE 0.1`.

| Aggregate (formula → wire) | Exact | Sampled | Approximate, unsampled |
|---|---|---|---|
| `SUM` → `sum` | `sum(x)` | `sum(x * t0._sample_factor)` | `sum(x)` |
| rows → `count` (plain measures only) | `count()` | `sum(t0._sample_factor)` | `count()` |
| `COUNT` → `countNonNull` | `count(x)` | `sum(if(isNotNull(x), t0._sample_factor, 0))` | `count(x)` |
| `AVG`, `MIN`, `MAX` → `avg`, `min`, `max` | as written | unscaled | as written |
| `COUNTD` → `countDistinct` | `uniqExact(x)` | `uniq(x)` | `uniq(x)` |
| `MEDIAN`, `PERCENTILE` (also the plain `median` / `percentile` measure) | `quantileExactInclusive(0.5)(x)`, `quantileExactInclusive({p:Float64})(x)` (interpolating) | unscaled | as exact |
| `STDDEV`, `VARIANCE` → `stddev`, `variance` | `if(count(x) < 2, NULL, stddevSamp(x))` (`varSamp`) | unscaled | as exact |
| `ATTR` → `attr` | `if(uniqExact(x) = 1, min(x), NULL)` | unscaled | as exact |

- The last four rows are never scaled: on a sampled table they run over the sample (estimates).
- The percentile fraction is the only user value, and it is bound: `AggNode.P` or a plain measure's `MeasureRef.P` as `mp{n}`, a Top-N's `topBy.P` as `tp{i}`
  (`Float64`, 0..1 checked again in `BindFraction`; ClickHouse accepts a query parameter as a parametric aggregate's argument). Function names are fixed text.
- `count(x) < 2` keeps a one-value group NULL (bare `stddevSamp` is NaN, which JSON cannot carry). `min(x)`,
  not `any`, ignores NULL rows in `attr`. `PlainRankSql` (Top-N) uses the same writer.

**Top-N rank, exact vs approximate.** A rank by a plain measure is always exact and unscaled
(`PlainRankSql`; only the order matters). A rank by a calculation compiles through the table above, so in
approximate mode it uses `uniq` for `COUNTD` and scaled sums on a sampled table. The two ranks are not
aligned, on purpose. Likewise `approx.distinct` in the response ignores a `COUNTD` inside a Top-N `topBy`
(it reflects the result's measures only).
