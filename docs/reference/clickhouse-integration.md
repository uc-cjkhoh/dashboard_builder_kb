# ClickHouse integration

How the server talks to ClickHouse: driver and connection, the exact SQL, the identifier-injection
defence, and type mapping. Code: `src/DashboardBuilder/ClickHouse/` — `ClickHouseGateway.cs` (all SQL),
`Identifier.cs`, `ClickHouseType.cs`, `CsvUtil.cs`, `ConnectionRegistry.cs`, the `*Models.cs` records.

## Driver & connection

- **Driver:** `ClickHouse.Client` 7.x (ADO.NET) over the **HTTP interface**
  ([D3](decisions.md#d3--clickhouseclient-over-the-http-interface)); TLS via `Protocol=https` on
  `ClickHouseConnectionStringBuilder`.
- **Ports:** the target server exposes only TLS ports — **`8443`** (HTTPS, used) and `9440` (native
  TLS, unused). Plaintext `8123`/`9000` are unavailable, so a real connection is always `secure` on
  `8443` ([D10](decisions.md#d10--connect-over-tls-only-https-port-8443)). A local throwaway container
  may expose plain `8123` for testing.
- **Connection string** is assembled server-side from the session's `ClickHouseConnectionInfo`; the
  password comes from the session store and is never logged or returned.
- **Validate on connect:** open and run `SELECT 1` before reporting "connected".
- **The `HttpClient`** handed to the driver:
  - accepts an untrusted cert **only** when `allowInvalidCert && secure`
    (`BypassesCertificateValidation`) — [D11](decisions.md#d11--tls-certificate-validation-safe-by-default-explicit-per-connection-opt-in);
  - **must** set `AutomaticDecompression` — ClickHouse.Client asks for compressed responses and throws
    otherwise;
  - has a **15s `Timeout`** so an unresponsive host fails cleanly.

## Database-level guards

`BuildConnectionString` appends ClickHouse settings (`set_` keys) that ride on **every** query:

| Setting | Value | Why |
|---|---|---|
| `readonly` | `2` | the server itself refuses DDL/DML — read-only no longer rests on our builders alone ([D1](decisions.md#d1--read-only-against-clickhouse)) |
| `max_execution_time` | `12` s (`MaxExecutionSeconds`) | a runaway query stops server-side, before the 15s HTTP timeout (`HttpTimeoutSeconds`) |
| `cancel_http_readonly_queries_on_client_close` | `1` | when the browser aborts a superseded query, the request is cancelled and ClickHouse kills the query |

- **Cancellation path:** browser `AbortController` → ASP.NET `RequestAborted` (the controllers'
  `CancellationToken`) → the driver's HTTP request is cancelled → ClickHouse stops the query.
- **Timeout message:** ClickHouse code **159** maps to **504** "The query ran longer than 12 seconds and
  was stopped. Add a filter, lower Top-N, or use fewer fields." (`ApiControllerBase.DescribeFailure`).
  On a connection without the time limit the 15s HTTP timeout stops the query instead, and gets the
  same 504 (with "15 seconds"). A client abort (`IsClientAbort`) is left to the framework; every other
  failure stays a generic 502.

### Step-down when the server refuses a setting

The guard level (`QueryGuards` on `ClickHouseConnectionInfo`) is settled once, in `ValidateAsync`, and
every later query uses it. On a refusal `NextGuards` picks the next level and `SELECT 1` is retried:

| Level | Settings sent | Reached when |
|---|---|---|
| `Full` | all three | default |
| `NoTimeLimit` | `readonly=2`, cancel-on-disconnect | code **452** (SETTING_CONSTRAINT_VIOLATION) — a profile constraint, almost always on `max_execution_time` |
| `None` | nothing | code **164** (READONLY — the account is already read-only), or 164/452 again at `NoTimeLimit` |

- Any other error ends the retries with the usual "Could not connect" message. At most three attempts.
- At `None` via 164 the server's own read-only still guards; at `None` via a `readonly` constraint,
  read-only rests on the SQL builders alone.
- The step-down is logged at Information (`ClickHouse refused guard settings Full; retrying with …`) —
  levels only, never the connection string.
- Unit-tested in `QueryGuardTests`.

### A wrong password can be a network restriction

ClickHouse users can be scoped by **source IP** (`<networks>` in `users.d/*.xml`, or `HOST IP`). From a
disallowed IP the server answers like a bad credential: `Code: 194 … password is incorrect, or there is
no user with such name … (REQUIRED_PASSWORD)`, HTTP **401** — even with the right password. The
ClickHouse on `10.168.49.13` limits `default` to `127.0.0.1`, so from the app host it always 401s.

- **Fix:** connect with a network-enabled account. Don't chase the password or change server access
  control (out of scope — [golden rule 1](../conventions/golden-rules.md#1-the-server-is-read-only-against-clickhouse)).
- **To tell them apart:** run `SELECT 1` over HTTPS from the app host and from the DB host with the same
  password; local success + remote 401 = allowed-networks, not the password.

## The queries (all read-only)

| Purpose | Gateway method | SQL |
|---|---|---|
| Validate connection | `ValidateAsync` | `SELECT 1` |
| List databases / tables | `ListDatabasesAsync` / `ListTablesAsync` | `SHOW DATABASES` / `SHOW TABLES FROM {db}` |
| Describe columns | `DescribeColumnsAsync` | `DESCRIBE TABLE {db}.{table}` |
| Distinct values | `DistinctValuesAsync` | `SELECT DISTINCT {col} AS v FROM … WHERE v IS NOT NULL ORDER BY v LIMIT n` (1..1000, rejected outside) |
| Column profile | `ProfileColumnAsync` (`ClickHouseGateway.Profile.cs`) | two statements over `(SELECT {col} AS v FROM {db}.{table} LIMIT 1000000)` (a compound / unclassified type is read as `toString`): `SELECT count(), countIf(isNull(v)), uniq(v)[, toString(min(v)), toString(max(v))]` (min/max for numeric and date columns, hidden when empty or all-NULL) and `SELECT if(isNull(v), NULL, left(toString(v), 101)), count() … GROUP BY v ORDER BY count() DESC, v ASC LIMIT n` (top `n` 1..50, default 10). `uniq` is approximate; `sampled` is true when the table has ≥ 1,000,000 rows |
| Worksheet query | `QueryAsync` | see below |
| Histogram | `HistogramAsync` | `WITH (SELECT min…) AS lo, (SELECT max…) AS hi, if(hi>lo,(hi-lo)/{bins},1) AS width SELECT least(toUInt32(floor(({c}-lo)/width)),{bins-1}) AS bin, … count() … GROUP BY bin … ORDER BY bin` |
| Box plot | `BoxPlotAsync` | `SELECT [{dim} AS label,] min, quantile(0.25), quantile(0.5), quantile(0.75), max … [GROUP BY label] LIMIT n` |
| Raw rows | `RowsAsync` | `SELECT {col}, … FROM {db}.{table} [WHERE …bound…] LIMIT n+1` — the columns are catalog-checked (default: the first 200), filters use `BuildSingleTableFilters`, **no ORDER BY**, `n` 1..1000 (rejected outside), an extra probe row sets `truncated`; each column is selected as `if(isNull(c), NULL, left(toString(c), 1001))` so a cell is cut to 1000 characters (+ `…`) inside ClickHouse; rows × columns ≤ 50,000 |
| CSV export | `QueryAsync` | the worksheet query, serialised by `CsvUtil` |

`{db}`, `{table}`, `{col}` are **interpolated identifiers** (see below); every other variable part is a
bound parameter or a validated integer (out-of-range limits are rejected before the builder runs —
[api.md § Limits](api.md#limits)). **Join preview** (`JoinPreviewAsync`, `ClickHouse/JoinPreview.cs`, [api.md](api.md#relationship-preview)): one `SELECT` per side, run together, over `(SELECT {col} AS k FROM {db}.{table} LIMIT n)` grouped by key — rows, NULL rows, distinct keys, max repeat, and `k IN (the other table's first n keys)` counts (text keys compare as `toString`); n is 1..1,000,000.

### Worksheet query (`QueryAsync`)

`SELECT {rowDims} AS k0…, {colDims} AS kR…, {agg}({m0}) AS v0, … FROM t0 [INNER JOIN tN ON …] [WHERE …]
[GROUP BY k0, …] ORDER BY … LIMIT n [OFFSET m]`

- **Joins:** the base table is `t0`; each join edge attaches a table aliased `tN` in order, so any
  dimension, measure or filter can live on any included table. An edge is `INNER`/`LEFT`/`RIGHT`/`FULL JOIN` (`type`,
  `JoinKeyword`); an outer one ends the request `SETTINGS join_use_nulls = 1` (right/full without it: 400). Filters are `WHERE`
  (a NULL-extended side's rows drop); right/full reject `top` (400) and skip `SAMPLE`. Tests: `JoinTypeTests`.
- **Dimensions** arrive split by shelf — `rowDimensions[]` then `columnDimensions[]` — and group in that
  order, so each row's keys are `[rowDim…, colDim…]`. `measures[]` aggregate as `v0, v1, …`. No measures
  → an implicit `count()`.
- **Ordering:** `sort:{column, desc}` names a generated alias (`k{n}`/`v{n}`), validated against the
  request's counts; the remaining dimension keys follow ascending. Default: ascending by the first
  dimension (or first measure).
- **Limit:** default 50; 1..5000 (else 400; CSV export 1..100,000 —
  [D24](decisions.md#d24--showing-all-data-bounded-requests-paging-other-date-grouping)); sent as limit **+ 1** (`ProbeLimit(n, max)`). If the probe row comes
  back, it is dropped and the result is flagged `truncated` (`TrimProbeRow`) — the client shows a
  notice. The box plot does the same. Unit-tested in `TruncationTests`.
- **Paging:** `offset` adds `OFFSET m` to the same ordered query (the Table view's pages). The order ends
  with every group key, so pages never overlap or skip.
- **Total** (`withTotal`): `SELECT count() FROM (<grouped query>)` on its own connection, alongside the page.
- **Other** (`otherBucket`, one dimension, a truncated first page): `SELECT uniqExact(k) + max(isNull(k)) AS n, <measures>
  FROM … WHERE … AND k NOT IN (SELECT k0 FROM (<ordered query> LIMIT n)) SETTINGS transform_null_in = 1`
  — the same filters, the shown keys excluded exactly (a shown NULL group isn't recounted; a NULL group
  past the limit is counted — `uniqExact` alone skips NULL). If the server
  refuses the setting the result comes back without `other` (logged), never an error.
- **Date parts** (P26, `datePart` on a dimension): `toStartOfYear` / `toStartOfQuarter` / `toStartOfMonth`
  / `toMonday` / `toDate` / `toStartOfHour` (truncations) or `toQuarter` / `toMonth` / `toDayOfWeek` /
  `toHour` (discrete) via `DatePartExpression` — a whitelist, `hour` on a `Date` column becomes `day`,
  `hourOfDay` needs a time; a part on a non-date column is a 400. A dimension with its own part is left
  out of the chart-wide `dateBucket`. Tests: `DatePartTests`.
- **Type cast** (T02-34, `cast` on a dimension, measure, filter or `topBy`): `text` | `number` | `date`,
  validated in `RequestRules` (unknown word or a cast on a calculation = 400 at `….cast`) and applied in
  `TypeCast.Apply` after the catalog-checked, quoted column: to text `toString`; text → number
  `toFloat64OrNull(toString(x))` kept only when finite (`inf`, `nan`, `1e999` are NULL; padded, comma and hex text are NULL too); boolean → number `toFloat64`; text → date `parseDateTimeBestEffortOrNull(toString(x))`, but text of only digits, spaces, signs, commas and dots is NULL unless it is `YYYYMMDD` (best-effort would read `10` as the 10th of the *current* month);
  an already-matching type is left alone, and number/date → date or date → number is a 400. Only `OrNull`
  variants, so bad data is NULL. A filter on a cast column compares those values, so a row that failed to
  convert is NULL: `=`, `!=`, `>`, `between` and `in` drop it, `notin` keeps it. The cast column's category (and "not a `Date`") then drives the aggregation
  check, filter value coercion and date parts. Join keys, histogram, box plot and distinct values ignore it.
  Tests: `TypeCastTests`, `tests/live/cast-smoke.mjs`.
- **Date grouping** (`dateBucket`): the first temporal dimension is wrapped in one whitelisted function —
  `toStartOfHour` / `toDate` / `toMonday` / `toStartOfMonth` / `toStartOfQuarter` / `toStartOfYear`
  (`BucketExpression`; a Date column never goes finer than day). `auto` first reads `uniq`, `min`, `max`
  under the view's filters: ≤ 400 distinct values stays exact, else the finest grain with ≤ 400 buckets
  (`PickGrain`). The response says which key and grain (`bucket`). Tests: `ScaleTests`.
- **Richer filters** (P30): text match via `positionCaseInsensitiveUTF8` / `startsWith` / `endsWith` on
  `lowerUTF8`, the text bound as a `String`; **top-N** is built after the other conditions as
  `col IN (SELECT col FROM <same joins> WHERE <other filters> GROUP BY col ORDER BY <agg> DESC|ASC LIMIT n)`.
  Tests: `RicherFilterTests`.
- **Result cache** (P33): `QueryAsync` answers a repeat of the same request on the same server + user from
  `IMemoryCache` for 60 s (logged; `cached: true`); `fresh` skips and replaces it (`CacheKey`, tested: no
  password, `fresh` ignored). **Approximate** (`approximate`): `uniq` instead of `uniqExact`; when
  `system.tables.sampling_key` is set for the base table, `FROM … AS t0 SAMPLE 0.1` with `count()` →
  `sum(t0._sample_factor)` and `sum(x)` → `sum(x * t0._sample_factor)`; a refused sampled query re-runs
  unsampled. The response's `approx` says what was done. Exercised live (a `SAMPLE BY` table, plain and
  calculated measures, a calculated Top-N rank) by `tests/live/calc-smoke.mjs`.
- **Compression:** API responses are Brotli/gzip-compressed (fastest level, `Program.cs`).
- **Response:** `QueryResult { rowDimensions, columnDimensions, measures, rows:[{keys, values}], truncated, total?, other?, bucket? }`;
  `values` are numbers, strings (`min` / `max` of a text or date column — read by the measure's category) or `null`
  (NULL, or `NaN` / `∞` from an aggregate over no rows); the client pivots it ([worksheet.md](../features/worksheet.md#table-view--a-true-rows--columns-crosstab)).
- **Errors:** invalid identifier, table-not-in-query, `sum` / `avg` on a non-numeric column, or a value
  that doesn't fit its column → 400 ([api.md](api.md#errors)).

### Calculated fields — the compile path

A `calc` tree on a dimension, measure or Top-N `topBy` ([api.md § Calculated fields](api.md#calculated-fields-calc))
becomes SQL in four steps; no formula text and no literal is ever written into SQL.

1. **Request rules** (`RequestRules.ValidateQuery`, no catalog): tree depth ≤ 12 and ≤ 200 nodes
   (`CalcValidator.CheckLimits`), label ≤ 60, the role rules (aggregate tree ↔ `agg` null; row-level
   measure needs a value aggregation; no aggregate in a dimension; no `datePart`; no `calc` on a join key).
2. **Catalog** (gateway `CompileCalcAsync` → `ResolveCalcRefsAsync`): every `field` node (`CalcFields`) is
   first checked against the tables already in the query (`from` and joins) — a field on any other table
   is a 400 "Field references a table not in the query." whether or not the column exists, before any
   catalog lookup, so a calculation never causes a `DESCRIBE` of a table outside the query. Then it goes
   through `ColumnsOf` + `QualifyAsync` — `DESCRIBE`-validated (already cached for tables in the query),
   quoted by `Identifier.cs`, aliased `t0` / `tN` — so a calculation may reference any table in the query,
   including a left-joined one (its unmatched side is NULL under `join_use_nulls`). A column the catalog
   doesn't know on such a table is left out, so the validator names it ("Unknown field t.c.").
3. **Validate** (`ClickHouse/Calc/CalcValidator.cs`): types the tree bottom-up from the column categories
   (number, text, date, boolean; anything else is refused), derives aggregate vs row-level, and rejects a bad
   tree with a `CalcException` (a plain sentence plus the node path, `measures[0].calc.l.arg`) that the
   gateway reports as a 400. The gateway re-checks the role and
   the `sum` / `avg`-needs-a-number rule against the derived type (`CalcMeasureSql`, `CalcDimensionSql`).
4. **Compile** (`ClickHouse/Calc/CalcCompiler.cs`): numeric columns widened with `toFloat64(...)` (no unsigned wrap, no integer or `Decimal` rounding); `a / b` → `(a / nullIf(b, 0))` (division by zero is NULL, never `inf`); each number literal bound
   as `{c{n}p{m}:Float64}` and each text literal as `{c{n}p{m}:String}` — `c{n}` unique per compiled calculation in the request; aggregates through the shared `AggregateSql` (table below), so a calculated `SUM` is scaled and a `COUNTD` estimated
   exactly as a plain measure is. A row-level measure is then wrapped by its pill aggregation; an aggregate tree is used as is; a dimension groups by its row-level expression. Logic nodes: `(a = b)` (also `!= < <= > >=`), `and(a, b)`, `or(a, b)`,
   `not(a)`, `if(c, a, b)` (IF/IIF), `multiIf(c1, a1, …, else)` (CASE; `NULL` last without an ELSE), `ifNull(a, b)`, `isNull(a)`; a NULL condition is not true (IF takes its else, CASE the next WHEN — pinned by the live smoke).
   Text functions (`fn` nodes, every argument compiled once in source order): `lowerUTF8`, `upperUTF8`, `trimBoth`, `toFloat64(lengthUTF8(…))`, `leftUTF8`/`rightUTF8(t, {UInt32})`, `replaceAll`, `concat`, `(position(t, s) > 0)`, `startsWith`,
   `endsWith`, `if(isNull(t), NULL, arrayElementOrNull(splitByString({sep:String}, assumeNotNull(t)), {k:UInt32}))`.
   Date functions: `toFloat64(dateDiff({unit:String}, a, b))`, `addYears`/`addQuarters`/`addMonths`/`addWeeks`/`addDays`/`addHours`/`addMinutes`/`addSeconds(d, {n:Int32})` (fixed name per unit, unit never in SQL) applied to `toDateTime64(d, 0)` and
   kept only strictly between 1900-01-03 and 2299-12-29 UTC, else NULL (a plain `Date` would wrap and a `DateTime` clamp to 1970 on overflow), `toFloat64(toYear|toMonth|toDayOfMonth|toQuarter|toISOWeek|toDayOfWeek(d))`, and `DATE(t)` =
   `TypeCast.ParseDate`: the cast's digit guard, then `toDate` of `parseDateTime64BestEffortOrNull(t, 0)` kept only between 1970-01-02 and 2149-01-01 (else NULL). `dateDiff` on a `Date` with a time unit reads midnight to midnight (24 hours a day).
   A boolean-typed calculation is wrapped in `toBool(...)`; as a dimension, `toString(...)` of it so keys read `true` / `false` (a plain Bool field keeps `True` / `False`).

**One compile, one parameter list.** Each calculation is compiled once; its SQL string is reused in the
page, the total (`count()` over the grouped query), the Other statement and inline in the Top-N
subquery, and every statement is sent with the request's one `parameters` list (filter values `p{i}` and
calculation literals `c{n}p{m}`). The auto date-grain probe reuses only the date expression and the
`WHERE`, so it is sent just the parameters its SQL names (`ParametersUsedBy`). A calculated dimension is
never date-grouped: `dateBucket` takes the first *real* temporal dimension wherever the calculation sits.
The result cache key includes the tree, so two requests that differ only in a calculation never share a
result. Tests: `CalcCompilerTests`, `CalcValidatorTests`, `CalcRulesTests`, `CalcGatewayTests`, `CalcJsonTests`, the
shared fixture (also run by `node --test`); live (dev app + a real ClickHouse, tables created and dropped by the
script, results checked against hand-written `SELECT`s or hand-computed values): `tests/live/calc-smoke.mjs`
(`test_cj.calc_smoke_*`), `logic-smoke.mjs` (`bk_logic`), `text-smoke.mjs` (`bk_text`).

**Compile spikes** (`node tests/live/calc-spikes.mjs`, SELECT only, inline sources). A bound parameter inside a
`SELECT` / `GROUP BY` expression works (also `GROUP BY` the full expression). `toFloat64` over `UInt32`,
`Decimal(18,2)` and `Nullable(Float64)` works: no unsigned wrap (`toFloat64(UInt32 2) - toFloat64(Decimal 10.00)` is
`-8`), a NULL operand makes the result NULL. `sum(x) / nullIf(sum(y), 0)` with every `y` = 0 returns JSON `null`;
`nullIf` keeps the SQL NULL for other writers and downstream arithmetic.

**Aggregates, exact and approximate** (`AggregateSql` — one function for plain and calculated measures;
"sampled" = `approximate` on a base table with a sampling key, read `SAMPLE 0.1`):

| Aggregate (formula → wire) | Exact | Sampled | Approximate, unsampled |
|---|---|---|---|
| `SUM` → `sum` | `sum(x)` | `sum(x * t0._sample_factor)` | `sum(x)` |
| rows → `count` (plain measures only) | `count()` | `sum(t0._sample_factor)` | `count()` |
| `COUNT` → `countNonNull` | `count(x)` | `sum(if(isNotNull(x), t0._sample_factor, 0))` | `count(x)` |
| `AVG`, `MIN`, `MAX` → `avg`, `min`, `max` | as written | unscaled | as written |
| `COUNTD` → `countDistinct` | `uniqExact(x)` | `uniq(x)` | `uniq(x)` |
| `MEDIAN`, `PERCENTILE` → `median`, `percentile` | `quantileExactInclusive(0.5)(x)`, `quantileExactInclusive({p:Float64})(x)` (interpolating) | unscaled | as exact |
| `STDDEV`, `VARIANCE` → `stddev`, `variance` | `if(count(x) < 2, NULL, stddevSamp(x))` (`varSamp`) | unscaled | as exact |
| `ATTR` → `attr` | `if(uniqExact(x) = 1, min(x), NULL)` | unscaled | as exact |

The last four are never scaled: on a sampled table they run over the sample (estimates). The percentile fraction is the only user value: bound (`AggNode.P`, `Float64`, validated 0..1;
ClickHouse accepts a query parameter as a parametric aggregate's argument); function names are fixed text.
`count(x) < 2` keeps a one-value group NULL (bare `stddevSamp` is NaN, which JSON cannot carry); `min(x)`,
not `any`, ignores NULL rows in `attr`. `PlainRankSql` (Top-N) uses the same writer.

**Top-N rank, exact vs approximate.** A rank by a plain measure is always exact and unscaled
(`PlainRankSql` — only the order matters). A rank by a calculation compiles through the table above, so in
approximate mode it uses `uniq` for `COUNTD` and scaled sums on a sampled table; the two ranks are not
aligned on purpose. Likewise `approx.distinct` in the response ignores a `COUNTD` inside a Top-N `topBy`
(it reflects the result's measures only).

### Shared defences in the builders

- **Whitelists:** aggregations `count/sum/avg/min/max/countDistinct/countNonNull/median/stddev/variance/attr`
  (`countDistinct` → `uniqExact`, `countNonNull` → `count(col)`; `median`, `stddev`, `variance` need a numeric
  column, `attr` any column but a compound one; no plain `percentile` — it needs a fraction); calculation node kinds,
  operators and functions (`CalcValidator`, `CalcCatalog`); operators `= != > >= < <= in notin between` (plus text match and top-N).
- **Typed bound values** (`FilterValues.Coerce`, `ClickHouse/RequestValidation.cs`): the value is
  converted to the column's category from the same `DESCRIBE` before binding — number → `{p0:Float64}`
  (plain decimal only), date / datetime → ISO text bound as `String` (a `Date` / `Date32` column rejects a
  time part), boolean → `UInt8`, text → `String`; compound / other types can't be filtered. Binding is via
  ClickHouse.Client's `AddParameter` (`using ClickHouse.Client.Utility`). `in` and `notin` bind `Array(Float64)` /
  `Array(String)` / `Array(UInt8)`, ≤ 500 values; `between` binds two bounds and requires From ≤ To. A value
  that doesn't fit is a 400, never a ClickHouse 502.
- **Rejected, not no-op'd, on the server:** an empty `in` / `notin`, a half or inverted range, an unknown operator.
  (The client never sends a blank filter, so the user-visible behaviour of an empty filter is still
  "ignored".)
- **Pure, unit-tested helpers** (reached via `InternalsVisibleTo`): `BuildCondition`,
  `BuildSingleTableFilters`, `FilterValues`, `RequestRules`, `ClampBuckets`, `ClampDistinct`, `CsvUtil`.
  The `Clamp*` helpers are defence in depth: `RequestRules` rejects out-of-range input first.
- **Histogram / box plot** are single-table: the column must be `DESCRIBE`-validated and **numeric**;
  the max value is clamped into the last bin. Their `filters` (`StatFilter`) go through the same typed
  `BuildSingleTableFilters` — `in` and `between` included.

## Identifier injection

ClickHouse binds **values**, not **identifiers** — `SHOW TABLES FROM ?` is not a thing. Client-supplied
names written into SQL text are an injection vector (`; DROP …`, cross-database reads). Before any
identifier reaches a query
([golden rule 2](../conventions/golden-rules.md#2-never-interpolate-an-identifier-you-havent-validated),
[D6](decisions.md#d6--identifiers-validated-against-the-live-catalog--backtick-quoted)):

1. **Validate against the live catalog** for the current connection — `db` ∈ `SHOW DATABASES`, `table`
   ∈ `SHOW TABLES FROM db`, column ∈ that table's `DESCRIBE` (ordinal match). Anything else →
   `UnknownIdentifierException`. This alone defeats injection: only real names pass.
2. **Backtick-quote** with internal backticks doubled (`Identifier.Quote`) — defence in depth.

Both steps live in `ClickHouse/Identifier.cs`; never hand-format an identifier at a call site. A
`LIMIT` is a value — validate it as an integer; a table name is not — validate then quote.

Richer metadata, if ever needed, comes from `system.databases` / `system.tables` / `system.columns`
(`is_in_primary_key`, comment, …) — remember a primary key is a sparse index, not a constraint.

## Type mapping

`DESCRIBE` returns ClickHouse type strings. `ClickHouseType.Categorize(type)` unwraps `Nullable(...)` /
`LowCardinality(...)`, takes the base name before `(`, and returns a display category used for the
entity-card badge, field role default and grid alignment:

| Example types | Category |
|---|---|
| `UInt64`, `Int32`, `Float64`, `Decimal(18,4)` | `numeric` (right-aligned, monospace) |
| `String`, `FixedString(n)`, `Enum8(...)`, `UUID`, `IPv4` | `text` |
| `Date`, `Date32`, `DateTime`, `DateTime64(3)` | `temporal` |
| `Bool` / `Boolean` | `boolean` |
| `Array(T)`, `Map(K,V)`, `Tuple(...)`, `Nested` | `compound` |
| anything else | `other` |

`FormatCell` stringifies non-numeric values (keys, distinct values, text measures): invariant-culture
numbers, `[a, b]` for arrays/tuples, hex for byte blobs, `true` / `false`, and **ISO dates** — a
`DateTime` at exactly midnight renders date-only (`2024-01-31`), otherwise `yyyy-MM-dd HH:mm:ss`.
NULLs stay JSON `null`.

## Safety & performance

- **Always bound** — every statement carries a validated `LIMIT`; there is no `SELECT *` path.
- **No FK metadata exists** — relationships are user-defined ([data-model.md](data-model.md#relationship)).
- **Scope every query** to the connection + database the request names; sessions never bleed.
- **Errors** are mapped to clean messages (502, or 504 for a server time-out, via `SafeError`) — never
  the connection string or password.
