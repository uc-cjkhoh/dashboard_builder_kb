# Calculation engine — calculated fields (T04, T05-01)

Part of the [proposal](web-application-proposal.md#34-calculation-and-query-engine-t04-t05). Inventory: [`tableau-features.md`](tableau-features.md) chapters 4 and 5. Status: Plan A (server, shared fixture, pure client modules) and Plan B (field pane, dialog, plan integration, workbook, explainer) are built and on `main` in the app repo; not deployed. Current behaviour: [calculated-fields.md](../features/calculated-fields.md).

## Goal

A user can write a formula over fields from the data model, name it, and use it like a field: `SUM([orders.amount]) / SUM([orders.qty])` on a shelf, in a chart, sorted, Top-N-ranked and table-calculated, with the arithmetic done by ClickHouse inside the existing read-only, bounded, identifier-safe query path.

Closes **T04-11** (editor), **T04-13** (row-level vs aggregate), **T04-14** (arithmetic and ratios), **T04-04** (non-null count) and **T05-01** (evaluation-order explainer). Release 0 of the [proposal](web-application-proposal.md#9-delivery-and-risks).

## Non-goals

- No text, date, `IF`/`CASE`/`IFNULL`, percentile, standard-deviation, `ATTR`, parameter or LOD functions (T04-03…27, T05-22…27). They are later rows in the function table; nothing in the pipeline is specific to arithmetic.
- No filter on a calculated field, no calculation inside the histogram or box-plot views, no table-calculation formulas (the existing quick table calculations apply to a calculated measure unchanged).
- No server storage: calculations live in the workbook (golden rule 4 and D21 stand). No endpoint writes anything.

## Anti-goals

A formula that returns a plausible but wrong number is a failure even if every test passes: ratios of sums must not become sums of ratios, an integer overflow must not wrap silently, and a divide by zero must not show `inf`.

## Decisions

| # | Decision | Why |
|---|---|---|
| E1 | The request carries an **expression tree** (JSON), never formula text. The server never parses text. | No text-to-SQL path to attack; one authoritative validator. |
| E2 | A measure or dimension may carry `Calc` (a tree) instead of a column. The result keeps `k{n}`/`v{n}` aliases in request order. | Pivot, sort, Top-N and charts work unchanged. |
| E3 | A tree is **aggregate** if it contains an aggregate function, else **row-level**. A formula mixing both is a 400. | Tableau's rule; avoids silent grain errors. |
| E4 | Row-level numeric calc → measure, aggregated by the pill (default `SUM`). Row-level text/date/boolean calc → dimension (`GROUP BY` the expression). Aggregate calc → measure with no further aggregation. | Same roles as fields today. |
| E5 | `a / b` compiles to `a / nullIf(b, 0)`: dividing by zero gives NULL, shown as a dash. | One documented rule; never `inf`/`NaN` in a chart. |
| E6 | Every numeric field inside a calculation is wrapped `toFloat64(...)`. Values above 2^53 lose precision. | Avoids unsigned/integer wrap-around and Decimal surprises; matches how results are read (as doubles). |
| E7 | Calculations are **workbook-level**: `calculations: [{ id, name, formula }]`. The workbook stores **formula text**; the tree is re-derived on open. | One source of truth; no stale trees after a grammar change. Reverses the earlier proposal sketch that stored the tree. |
| E8 | Fields are referenced `[table.column]`, or `[db.table.column]` when two databases share a table name. A calc is referenced by `[Name]`; names may not contain `.`. | The `.` tells column from calc and leaves room for parameters (`[Name]`, later). |
| E9 | A calc may reference another calc. The **client expands** references into one tree before sending (cycle check there); the server sees only trees. | The server needs no calc registry; the cap on nodes bounds the cost. |
| E10 | The aggregation compile step is **shared** with plain measures (one function: aggregate name + SQL expression + `sampled` + `approximate` → SQL). Approximate mode scales a calculated `SUM` by `_sample_factor` and uses `uniq` for `COUNTD`, exactly as for a plain measure. | One place defines aggregate semantics. |
| E11 | Add whitelisted aggregation `countNonNull` (`count(col)`) to plain measures; `COUNT([f])` in a formula is the same. Existing `count` (all rows) keeps its meaning. | Closes T04-04 without changing saved workbooks. |
| E12 | A calculated field can sit on **Rows, Columns and the mark slots** (colour, size, label, tooltip, detail), be a sort target and a Top-N rank (`TopBy`). It **cannot** be a filter, a Pages field, a drill level or the date-range field: those entry points refuse it with "Calculated fields can't be used here yet". **Click-to-filter and cross-widget selection are off** when the primary dimension is a calculation. A calculated dimension is never date-grouped or bucketed. | Every one of those creates a `db.table.column` filter or reads a column's raw type; a calculation has neither. |
| E13 | The server **derives the role from the tree** and rejects a mismatch with a 400 naming the field: an aggregate tree is valid only in a `MeasureRef` with `Agg` null; a row-level tree in a `MeasureRef` needs `Agg` ∈ `sum`, `avg`, `min`, `max`, `countDistinct`, `countNonNull` (`count` of rows is rejected: it would ignore the calculation); a row-level tree is valid in a `ColumnRef`; an aggregate tree there is a 400. | The wire contract has one valid reading; a client bug can't produce a wrong grain. |
| E14 | A reference is `[table.column]` or `[db.table.column]`. A 2-part reference that matches tables in more than one database is an error asking for the 3-part form. A table appears at most once in a query, so it is never ambiguous within one. **Columns or tables whose names contain `.`, `[` or `]` are not supported in this release**: autocomplete doesn't offer them and a typed reference to one is an error. Spaces are fine inside the brackets. | Keeps the lexer and the shared fixture simple; the names are rare. |
| E15 | A calculation whose formula points at a field no longer in the model **stays**, with an error state in the field pane and the dialog. A worksheet using it shows "Calculation 'X' can't be computed: orders.qty isn't in the model" and sends no query. Import reports it as an issue. | Dropping it would silently change a user's charts. |

**Approximate mode on a sampled base table** (one function, used by plain and calculated measures):

| Aggregate | Exact | Sampled / approximate |
|---|---|---|
| `sum(x)` | `sum(x)` | `sum(x * t0._sample_factor)` |
| `count` (rows) | `count()` | `sum(t0._sample_factor)` |
| `countNonNull(x)` | `count(x)` | `sum(if(isNotNull(x), t0._sample_factor, 0))` |
| `avg`, `min`, `max` | as written | unscaled |
| `countDistinct(x)` | `uniqExact(x)` | `uniq(x)` (when `Approximate`) |

## Language (first release)

```text
expr      := term (("+" | "-") term)*
term      := factor (("*" | "/") factor)*
factor    := "-" factor | number | "(" expr ")" | aggregate | ref
aggregate := ("SUM" | "AVG" | "MIN" | "MAX" | "COUNT" | "COUNTD") "(" expr ")"
ref       := "[" name "]"
```

- Function names are case-insensitive; numbers are decimals with an optional exponent: `12`, `1.5`, `.5`, and also `1.` and `1e3` (no `1,000`); a number that isn't finite (`1e999`) is an error.
- Types: `number`, `text`, `date`, `boolean` — from the catalog categories (numeric, text, temporal, boolean). A field of any other category is rejected ("can't be used in a calculation").
- `SUM`/`AVG`: number argument. `MIN`/`MAX`: number, date or text. `COUNT`/`COUNTD`: any argument; `COUNT` counts non-null values.
- Arithmetic needs number operands. Nesting an aggregate inside an aggregate is a 400.

## Wire format

```json
{ "k": "bin", "op": "/",
  "l": { "k": "agg", "fn": "sum", "arg": { "k": "field", "db": "shop", "table": "orders", "column": "amount" } },
  "r": { "k": "agg", "fn": "sum", "arg": { "k": "field", "db": "shop", "table": "orders", "column": "qty" } } }
```

Node kinds: `field`, `num` (`v`), `un` (`op: "-"`), `bin` (`op` ∈ `+ - * /`), `agg` (`fn`, `arg`). Request additions, all optional and backward compatible: `ColumnRef.Calc`, `MeasureRef.Calc` (also usable as a Top-N `TopBy`). A node that has `Calc` ignores `Db/Table/Column`.

**Limits** (`CalcLimits` in `ClickHouse/Calc/CalcCatalog.cs`, mirrored by `CALC_LIMITS` in `Features/Calc/calc-types.js` and `LIMITS` in `Features/Core/validate.js`; over the limit is a 400, never clamped): formula ≤ 500 characters; tree depth ≤ 12 and ≤ 200 nodes after expansion; ≤ 20 calculations per workbook; name ≤ 60 characters and unique. Calculated dimensions and measures count toward the existing 12 and 10.

## Server

New `ClickHouse/Calc/`:

| File | Responsibility |
|---|---|
| `ExprNode.cs` | the node records and their JSON converter (discriminator `k`; unknown `k` is a 400). |
| `CalcCatalog.cs` | `CalcLimits`, `CalcType`, `CalcException` and the function table: per aggregate, the argument types it accepts and its result type. The only place a function exists. |
| `CalcValidator.cs` | `Validate(node, categoryOf)` (`categoryOf` maps db, table, column to a catalog category or null) → `CalcInfo { Type, IsAggregate, Tables }`; throws `CalcException` (a plain sentence and the node path, `l.arg`), which the gateway wraps into a `RequestValidationException` at `measures[0].calc.l.arg`. |
| `CalcCompiler.cs` | `Compile(node, qualified, parameters, paramPrefix, sampled, approximate)` → SQL, where `qualified` returns `(Sql, Category)` for a field the gateway resolved through `QualifyAsync` (catalog check + quote, `Identifier.cs` only); number literals are **bound** as `{c{n}p{m}:Float64}` (`c{n}` per compiled calculation); no user text reaches SQL. |

`ClickHouseGateway.cs` calls them where it now builds `dimExprs`/`measExprs`; a referenced table that isn't in the query is the existing "Field references a table not in the query" error, raised before any catalog lookup. `ValidateQuery` rejects a calc over the limits before the gateway runs.

## Client

New `Features/Calc/` (vanilla modules, tokens only):

| File | Responsibility |
|---|---|
| `calc-parser.js` (pure) | `parseFormula(text, resolve)` → `{ ast }` or `{ error: { message, pos } }`; `resolve` maps a reference to a field, a calc or nothing. |
| `calc-types.js` (pure) | the same function table as `CalcCatalog.cs`; `check(ast)` → `{ type, isAggregate, tables }`. |
| `calc-model.js` (pure) | `expandCalcs(ast, calcsByName)` with cycle detection, capped at `CALC_LIMITS.nodes`; `roleOfCalc`. The workbook-level limits (20 calculations, name length) are Plan B's. |
| `eval-order.js` (pure) | `describeEvaluation(sheet)` → the ordered stages for the explainer (below). |
| `calc-dialog.js`, `calc.css` | the editor dialog: name, formula box with `[` autocomplete, live message, a chip showing "Aggregate · number" or "Row-level · text". |

Integration (after the 24a extraction): the field pane gains a **Calculated fields** group (create, edit, delete); a pill may be `{ calc: id, role, agg? }`; `planDims`/`planMeasures` emit `Calc` trees; the tables a calc references join the plan's `involved` list like any field; `fieldId` and display names handle calc pills; deleting a calc used by a worksheet asks first and clears those pills. `workbook-model.js` validates `calculations` and the pills that point at them, reporting a dangling reference as an import issue, never silently.

**Evaluation-order explainer (T05-01).** A "How this is computed" popover on the view bar lists, for the current sheet: 1 filters ClickHouse applies — own, shared, drill, page, selection, period, and the Top-N *filter* (a `member IN (top n by measure)` condition); 2 row-level calculations; 3 group by the dimensions; 4 aggregates and aggregate calculations; 5 the display cap (Top-N "All" = 5000 groups) and the Other bucket; 6 table calculations, run in the browser on the returned groups. Text only, generated from the sheet.

## Persistence

`calculations: [{ id, name, formula }]` in the workbook, ≤ 20; ids are cross-references inside the file, as for entities. Pills reference `calc: id`. A calculation whose formula can't be resolved on open is kept in an error state (E15). A workbook without `calculations` opens as before; no format version bump is needed for this field alone ([workbook.md](../features/workbook.md); the 24b v2 migration must carry it).

## Testing

- **Shared fixture** `tests/fixtures/calc-cases.json`: a top-level `catalog` (`"db.table"` → column → category) and `cases`, each `{ name, formula?, ast, expect: { type, isAggregate, tables } | { error, path } }` or `{ name, formula, parseError }`. `node --test` checks `parseFormula(formula)` equals `ast` and `check(ast)` equals `expect`; xUnit validates `ast` and compares. Neither suite has cases the other doesn't run.
- **SQL (xUnit):** exact SQL for the ratio, a row-level `SUM([price] * [qty])`, a calculated dimension, a Top-N ranked by a calc, and approximate mode (`sum(... * t0._sample_factor)`); division by zero → NULL; every literal bound (asserts no literal in the SQL text).
- **Rejections:** unknown function and field, wrong arity, text in arithmetic, aggregate nested in aggregate, aggregate/row-level mix, depth and node limits, a table not in the query, a `k` the converter doesn't know.
- **Browser (mocked API):** create `SUM(a)/SUM(b)`, drag to a shelf, the request carries the tree and the chart draws; an invalid formula shows the message and blocks Save; delete-in-use; reload restores.
- **Live smoke:** against the shared test ClickHouse server (database `test_cj`, tables `calc_smoke_*` created and dropped by the script), ratio of sums equals the hand-computed fixture, including a zero denominator and NULLs.

## Spikes before the plan commits

1. ClickHouse accepts a **bound parameter inside a SELECT/GROUP BY expression** and `nullIf`/`toFloat64` over `Nullable` and `Decimal` columns as the compiler emits them.
2. A row-level `SUM([price] * [qty])` on a large table stays inside the 12 s limit; if not, the message the user sees is the existing timeout one.
3. `NaN`/`∞` can't reach the JSON writer (the result path already maps them to null).

## Spike results

Run with `node tests/live/calc-spikes.mjs` (SELECT only, inline sources; script in the app repo).

- **S1 — bound parameter in a GROUP BY expression: works.** `toFloat64(q) * {c0p0:Float64} AS k0 ... GROUP BY k0` returns keys 10 and 20 with counts 1 and 2; writing `GROUP BY` as the full expression instead of the alias also works.
- **S2 — `toFloat64` over `UInt32`, `Decimal(18,2)`, `Nullable(Float64)`: works.** `toFloat64(UInt32 2) - toFloat64(Decimal 10.00)` is `-8` (no unsigned wrap); `toFloat64` of a NULL `Nullable(Float64)` or `Nullable(Decimal(18,2))` is NULL, and arithmetic with a NULL operand is NULL.
- **S3 — division by zero: works.** `sum(toFloat64(x)) / nullIf(sum(toFloat64(y)), 0)` with every `y` = 0 comes back as JSON `null` in `FORMAT JSON`. The same expression without `nullIf` also comes back as `null` (the JSON writer maps `inf`/`nan` to `null` by default), so `nullIf` keeps the SQL result NULL for the other writers and for downstream arithmetic rather than changing the JSON shape.

## Order of work — two plans

- **Plan A — done** (on `main` in the app repo, not deployed): `ClickHouse/Calc/`, the gateway integration (including the shared aggregate compile and `countNonNull`), request limits, the shared fixture, the three spikes, and the pure client modules (`calc-parser`, `calc-types`, `calc-model`, `eval-order`). None of it touches `dashboards.js`. xUnit and `node --test` pass the shared fixture, and the live smoke (`tests/live/calc-smoke.mjs`) matches the hand-computed ratio and a hand-written `SELECT` for every other scenario. The server contract is in [api.md § Calculated fields](../reference/api.md#calculated-fields-calc) and [clickhouse-integration.md](../reference/clickhouse-integration.md#calculated-fields--the-compile-path).
- **Plan B — built** (on `main` in the app repo, not deployed). It lands on `dashboards.js` as it is, with new logic in new pure modules (`Features/Calc/`). Scope: the field-pane group, calc pills and the entry-point refusals (E12), plan integration, the dialog, the workbook field and dangling-reference handling (E15), the explainer UI, the browser checks (`tests/live/calc-ui.mjs`), and the KB. Behaviour: [calculated-fields.md](../features/calculated-fields.md); decisions: [D26–D32](../reference/decisions-calculated-fields.md). Merging `dashboards.js` with the scheme-toggle work is the owner's.
  Still open:
  - `tests/live/calc-smoke.mjs` needs the shared test server and credentials, so it is a manual check; the repo has no CI. Re-run it before every deploy. (`tests/live/calc-ui.mjs` needs only the dev app, and `tests/js/calc-limits.test.mjs` keeps the three copies of the calculation limits equal.)

## Left to the builder

File-internal structure of the parser, the autocomplete interaction details and the dialog layout (the dialog is the one screen here; settle its mockup before building it), error-message wording beyond the examples, and the exact SQL aliasing of calculated expressions.
