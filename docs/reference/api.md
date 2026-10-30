# API reference

The JSON API under `/api` (prefixed by `PathBase` when proxied). Every endpoint is **read-only**
against ClickHouse ([golden rule 1](../conventions/golden-rules.md#1-the-server-is-read-only-against-clickhouse)).
Controllers are attribute-routed `[ApiController]`s subclassing `Features/ApiControllerBase.cs`; the
SQL each runs is in [clickhouse-integration.md](clickhouse-integration.md#the-queries-all-read-only).

## Errors

Every failure returns **one JSON shape**: `{ "error": "<sentence>", "field": "<path>?" }` — `field` is
the offending input (`host`, `filters[2].values`, `measures[0]`) and is omitted when there isn't one. The
sentence is user-facing: no CLR type names, parser positions, stack traces or credentials. The client
(`Core/api.js`) shows `error` as-is; a non-JSON error body becomes "Server error (status)." /
"Request failed (status).".

| Code | When | Body |
|---|---|---|
| 200 | success | the result |
| 400 | invalid input: model binding (missing field, wrong type, malformed or empty JSON), a [limit](#limits) broken, a filter value that doesn't fit its column, an aggregation the column can't take, an unknown sort column, or (query/stat routes) an unknown identifier or a table not in the query | `{ error, field? }` |
| 404 | unknown database / table / column on the **schema** routes (`UnknownIdentifierException`) | `{ error }` |
| 409 | no connection in this session (`NotConnected`) | `{ error }` |
| 413 | request body over 256 KB | `{ "error": "Request too large." }` |
| 502 | ClickHouse (or the network / TLS) rejected or failed the query — credential-safe message; only the exception *type* is logged | `{ error }` |
| 504 | the query hit the server-side time limit (12 s), or the 15 s HTTP timeout on a connection without it — actionable message, see [guards](clickhouse-integration.md#database-level-guards) | `{ error }` |
| 500 | our own bug — anything else | `{ "error": "Unexpected error (ref <traceId>)." }`; the same ref and exception type are logged |

- **Order of checks:** model binding runs first, so `POST /api/query {}` is **400** "'from' is required."
  even with no connection; a valid body without a connection is 409. For [calculated fields](#calculated-fields-calc)
  only a malformed tree (unknown or missing `k`, a missing or wrongly typed member, a non-finite number,
  or nesting past MVC's JSON depth limit of 32 — about 30 levels of tree, "'measures[0].calc' has an
  invalid value.") fails in binding; every semantic check — role, limits, label, unknown field, type — runs in
  `RequestRules` / the gateway inside `RunAsync`, i.e. **after** the 409 gate. So does a plain measure's
  missing `agg` ("'measures[0].agg' is required.").
- Machinery: `ApiBehaviorOptions.InvalidModelStateResponseFactory` (`Features/ApiErrors.cs`) shapes
  binding failures (first error only); `ApiControllerBase.RunAsync` maps validation → 400, unknown
  identifier → 400/404, ClickHouse failures → 502/504 and anything else → 500; `UseExceptionHandler`
  catches whatever escapes a controller. Log category is the controller's full type name
  (`DashboardBuilder.Features.Dashboard.QueryController`, …).
- **Known gap:** an unmatched `/api/*` route returns an **empty-body 404** (no `{ error }`).

## Limits

Inputs are **rejected, never silently clamped or dropped** (`ApiLimits` in `ClickHouse/RequestValidation.cs`;
the client mirrors them in `Core/validate.js` `LIMITS` and checks first, so a valid UI never hits these):

| Input | Limit |
|---|---|
| Request body (JSON APIs) | 256 KB → 413 |
| Connect `host` / `user` / `password` | ≤ 253 / 64 / 256 characters; host is a name, IPv4 or IPv6 with no scheme, port or path; `port` required, 1–65535 |
| Row + column dimensions | ≤ 12 in total |
| Measures | ≤ 10 (calculated measures count toward it, as calculated dimensions count toward the 12) |
| Joins | ≤ 10 |
| Filters per query | **≤ 20** (`MaxFilters`). The client allows 8 user filters, and the worksheet appends the shared filters (≤ 4), the drill path (≤ 5), the page, the selection and the date range |
| Member colours (client-side only) | ≤ 100 coloured members per field, ≤ 20 fields per sheet, member key ≤ 100 characters, colour `#rrggbb` (`LIMITS.memberColors` / `memberColorFields` / `memberField` / `memberKey`) |
| `in` / `notin` values | ≤ 500; a filter value ≤ 1000 characters |
| `limit` (rows) | 1–1000, default 100 (`MaxRowsLimit`, mirrored by `LIMITS.viewRows`); ≤ 200 `columns` (`MaxRowsColumns`); a cell ≤ 1000 characters (`MaxCellLength`, cut not rejected); rows × columns ≤ 50,000 (`MaxRowsCells`, `LIMITS.viewCells`) |
| `limit` (query, box plot, distinct) | 1–5000 (default 50; [D24](decisions.md#d24--showing-all-data-bounded-requests-paging-other-date-grouping)) · CSV export 1–100,000 · distinct 1–1000 (default 200) |
| `limit` (profile) | 1–50 top values, default 10 (`MaxProfileTop`); `column` ≤ 1000 characters (`MaxColumnName`); scan bound 1,000,000 rows (`ProfileSampleRows`), a value ≤ 100 characters (`ProfileValueLength`) — mirrored by `PROFILE_LIMITS` in `Schema/column-profile-model.js` |
| `offset` (query) | 0–10,000,000 |
| Filter `op` | also `contains`, `startsWith`, `endsWith` (text columns, value required) and `top` (value 1–1000 + `topBy` measure, optional `bottom`; worksheet query only — histogram / box plot reject it) |
| `joins[].type` | `inner` (default), `left`, `right` or `full` (anything else 400, `joins[i].type`; `top` filters with right/full 400); a join key can't carry `calc` (400, `joins[i].left.calc` / `.right.calc`) |
| `calc` tree (dimension, measure, `topBy`) | depth ≤ 12 (root is depth 1), ≤ 200 nodes (`CalcLimits.MaxDepth`, `MaxNodes`); the label in `column` ≤ 60 characters (`CalcLimits.MaxName`, error at `….column`). Formula ≤ 500 characters and ≤ 20 calculations per workbook are client-only (`CalcLimits.MaxFormula`, `MaxCalcs`; mirrored by `LIMITS.calcFormula`, `LIMITS.calculations`, `LIMITS.calcName` in `validate.js` and by `CALC_LIMITS` in `Features/Calc/calc-types.js`) — the server never sees formula text |
| `fresh`, `approximate` (query) | booleans — skip the result cache; approximate mode ([D25](decisions.md#d25--a-short-lived-server-result-cache-and-approximate-mode)). The response adds `cached` and `approx: { distinct, sample }` |
| `datePart` (a row / column dimension) | `auto`, `exact`, `year`, `quarter`, `month`, `week`, `day`, `hour`, `quarterOfYear`, `monthOfYear`, `dayOfWeek`, `hourOfDay`; date columns only |
| `cast` (dimension, measure, filter, `topBy`) | `text`, `number`, `date`; the column is read as that type (NULL where a value doesn't convert). Unknown word, a calculation, or a pairing with no safe conversion (date → number, number → date) is a 400 at `….cast` / the field |
| `dateBucket` (query) | `auto`, `hour`, `day`, `week`, `month`, `quarter`, `year` |
| Histogram `buckets` | 1–100 |
| `sort.column` | must be a generated `k{n}` / `v{n}` alias for this request |

## Typed filter values

A filter value is converted to its column's category before it is bound, from the `DESCRIBE` the
validator already runs; a value that doesn't fit is a **400** naming the value and column, never a
ClickHouse 502:

- **number** → plain decimal / exponent (no `1,000`, `0x10`, `NaN`); bound `Float64`.
- **date / datetime** → ISO `YYYY-MM-DD`, `YYYY-MM-DD HH:MM[:SS]` (`T` allowed); bound as `String`. A
  `Date` / `Date32` column **rejects a time component**.
- **boolean** → `true` / `false` / `1` / `0`; bound `UInt8`.
- **text** → any; **compound / other** → 400 ("can't be compared").
- `between` needs both bounds and From ≤ To (number, date); `in` and `notin` (Exclude; keeps NULL rows) need ≥ 1 value.

Temporal values are **ISO everywhere** — keys, distinct values and box-plot labels use `YYYY-MM-DD` (a
midnight `DateTime` also renders date-only) or `YYYY-MM-DD HH:MM:SS`, so what the app shows round-trips as
a filter value.

## Connection

Controller: `Features/Connection/ConnectionController.cs`.

| Method & path | Purpose | ClickHouse |
|---|---|---|
| `POST /api/connection` | validate and store the session connection (host, port, user, password, secure, allowInvalidCert); steps the guard settings down if the server refuses one | `SELECT 1` |
| `GET /api/connection` | current connection view — password-free | — |
| `POST /api/connection/disconnect` | drop the session connection; body `{}` (proxy-safe) | — |
| `DELETE /api/connection` | same, direct to Kestrel only — the `:8443` proxy 403s `DELETE` | — |

## Schema

Controller: `Features/Schema/SchemaController.cs`.

| Method & path | Purpose | ClickHouse |
|---|---|---|
| `GET /api/databases` | list databases | `SHOW DATABASES` |
| `GET /api/databases/{db}/tables` | list tables | `SHOW TABLES FROM {db}` |
| `GET /api/databases/{db}/tables/{table}/columns` | columns `{name, type, category}` | `DESCRIBE TABLE` |
| `POST /api/databases/{db}/tables/{table}/profile` | column profile; body `{ column, limit? }` → `{ column, type, category, rows, nulls, distinct, min, max, top: [{ value, count, cut }], sampled, sampleLimit }`. Reads the **first 1,000,000 rows ClickHouse returns, in no particular order** — not a statistical sample (`sampled` = the table has at least that many); `distinct` is approximate (`uniq`, non-null); `min`/`max` are text, numeric and date columns only; `value` null = SQL NULL, cut at 100 characters, counted in characters not bytes (`cut`); values that differ only after character 100 count together; ties in `top` break by value. Unknown column/table → 404 | two bounded `SELECT`s |
| `GET /api/databases/{db}/tables/{table}/columns/{column}/distinct?limit=` | distinct values for an `in` filter / Pages (default 200, 1–1000 else 400) | `SELECT DISTINCT … LIMIT n` |

## Rows

Controller: `Features/Rows/RowsController.cs`. `POST /api/rows` reads the **first rows of one table** — no
aggregation, no `ORDER BY`, no joins.

| Field | Rule |
|---|---|
| `db`, `table` | required; validated against the live catalog (unknown → 400) |
| `columns` | optional, ≤ 200, each a catalog column (unknown → 400, `columns[i]` blank → 400); order kept. Default: the table's first 200 |
| `filters` | optional `StatFilter`s (`column`, `op`, `value`, `values`) — the typed rules of the histogram / box plot ([Typed filter values](#typed-filter-values)), ≤ 20, each bound; `top` is a 400; unknown column → 400 |
| `limit` | 1–1000, default 100; outside → 400 (`limit`), never clamped. **rows × columns ≤ 50,000** (`MaxRowsCells`): over it is a 400 on `limit` saying how many rows fit (checked after the default column set is known) |

Response `{ columns: [{name, type}], rows: [[string \| null]], truncated, limit, columnsTruncated }`: every cell is
display text (numbers invariant, dates ISO, arrays compact) or `null` for SQL NULL; a cell is cut at 1000
characters plus `…` — **inside ClickHouse** (each column is selected as `if(isNull(c), NULL, left(toString(c), 1001))`), so a huge value never leaves it; arrays, tuples, maps and dates read as `toString` prints them. `truncated` = more rows matched than `limit`; `columnsTruncated` = the default column set was cut.
Errors use the usual `{ error, field? }` shape: 400 rule breaks and unknown names, 409 not connected, 502 / 504 ClickHouse.

### Union

Controller: `Features/Rows/UnionController.cs`. `POST /api/union` stacks the **first rows of 2–5 tables of one database**
(`UNION ALL`) and answers in the `/api/rows` shape; the first column is `Source table` (the table's name, bound as a
parameter), then the shared columns. No ordering, no aggregation, no filters.

| Field | Rule |
|---|---|
| `db`, `tables` | `db` required; `tables` 2–5 names (`ApiLimits.MaxUnionTables`, mirrored by `LIMITS.unionTables`), each blank → 400 (`tables[i]`), unknown → 400/404 |
| `columns` | optional, ≤ 200. Default: the columns **every** table has with the same name **and kind** (text / number / date …), in the first table's order; none shared → 400 (`tables`). A requested column missing from a table is an unknown identifier; one whose kind differs between tables is a 400 (`columns[i]`). Types shown are the first table's |
| `limit` | 1–1000, default 100, never clamped; (columns + 1) × rows ≤ 50,000. Each table gets an even share (`ceil(limit / tables)`) and is read to share + 1 inside ClickHouse, so every table shows; `truncated` = some table (or the total) had more; `columnsTruncated` when more than 200 columns are shared |

Cells are cut in SQL like `/api/rows`. The UI (`Union` button in the Tables header → `Rows/union-dialog.js`) shows the first 20.

### Unpivot

Controller: `Features/Rows/UnpivotController.cs`. `POST /api/unpivot` turns **wide columns of one table into rows**: each source row becomes
one row per chosen column, answered in the `/api/rows` shape. Columns: the `keep` columns, then `Field` (the column's name, bound as a
parameter) and `Value` (the cell as text, NULL stays `null`; typed `String`). A kept column already named `Field` or `Value` makes ours `Field_` / `Value_`. Helper aliases in the SQL (here and in the union) use a prefix (`__u`, grown with `_`) that no table column starts with, because ClickHouse resolves a select alias ahead of a same-named column. No ordering, no aggregation, no filters.

| Field | Rule |
|---|---|
| `db`, `table` | required; unknown → 400/404 |
| `columns` | 2–50 distinct names (`ApiLimits.MaxUnpivotColumns`, mirrored by `LIMITS.unpivotColumns`); blank or repeated → 400 (`columns[i]`); unknown → unknown identifier; all must be the **same kind** (text / number / date …), else 400 (`columns[i]`) |
| `keep` | optional, ≤ 5 (`MaxUnpivotKeep` / `LIMITS.unpivotKeep`); blank → 400 (`keep[i]`); also in `columns` → 400 (`keep[i]`) |
| `limit` | 1–1000, default 100, never clamped. The statement has one `LIMIT limit + 1`, which ClickHouse applies **after** the `arrayJoin`, so it bounds the unpivoted rows (a source row is read only as far as needed); `truncated` = more existed |

Cells are cut in SQL like `/api/rows`. The UI (`Unpivot` button in the Tables header → `Rows/unpivot-dialog.js`) shows the first 20.

## Relationship preview

Controller: `Features/Relations/RelationsController.cs`. `POST /api/relationships/preview` — the relationship
dialog's "Check this join": bounded, read-only match and duplicate counts for one key pair. Joins nothing, writes nothing.

| Field | Rule |
|---|---|
| `from`, `to` | `{ db, table, column }` each, all required (400 at `from.db`, `to.column`, …); catalog-validated (unknown → 400) |
| key kinds | must be joinable and equal: number-number, text-text, date-date, boolean-boolean — else 400 `Can't relate a.x (numeric) to b.y (text) — join keys must hold the same kind of value.` (field `to.column`) |
| `sampleLimit` | optional, 1–1,000,000 (default and cap `MaxSampleRows`): rows read from **each** table; outside → 400 (`sampleLimit`), never clamped |

Response `{ from, to, sampleLimit, sampled }`; each side `{ rows, nullRows, keys, matchedKeys, matchedRows, maxDuplicates, avgDuplicates }`
over the rows examined: `keys` = distinct non-NULL keys, `matchedKeys`/`matchedRows` = those present on the other side (NULL never
matches), `maxDuplicates`/`avgDuplicates` = how often a key repeats within the side. `sampled` is true when a side reached the bound
(its numbers describe the first `sampleLimit` rows of each table, in no particular order — the two slices need not overlap, so match shares are only "within the sample"; each table is read twice, as its own stats and as the other side's key set, with no `ORDER BY`, so the reads can differ on a table being written to). A ClickHouse "types can't be compared" error (codes 43, 53, 70, 386) is a plain 400 at `to.column`. Errors: usual `{ error, field? }`; 409 not connected, 502 / 504 ClickHouse.

## Query

Controller: `Features/Dashboard/QueryController.cs`. All `POST` with a JSON body.

| Method & path | Purpose | Shape |
|---|---|---|
| `POST /api/query` | worksheet query across joined tables; optional `offset` (paging), `withTotal`, `otherBucket`, `dateBucket` | `QueryRequest` → `QueryResult` (incl. `truncated`, `total?`, `other?`, `bucket?`) — `values` entries are a **number, a string or `null`** (see below) |
| `POST /api/query/export.csv` | CSV of the same plan, up to 100,000 rows (never an Other row) | `QueryRequest` → `text/csv` |
| `POST /api/databases/{db}/tables/{table}/histogram` | equal-width bins over one numeric column | `HistogramRequest` |
| `POST /api/databases/{db}/tables/{table}/boxplot` | five-number summary, optionally grouped | `BoxPlotRequest` → `{ groups, truncated, outliers, outliersTruncated }`; a group is `{ label, min, q1, median, q3, max, lowerWhisker, upperWhisker }` (whiskers = extreme values inside Q1 − 1.5 IQR / Q3 + 1.5 IQR), an outlier `{ label, value }`, at most 500 (`ApiLimits.MaxBoxOutliers`; `outliersTruncated` when more exist) |

**Measure values** (`QueryResultRow.Values`, `IReadOnlyList<object?>`) are a JSON number, a **string**
(`min` / `max` of a text or date column), or `null` (SQL NULL, or `NaN` / `∞` from an aggregate over no
rows). Consumers must not assume numbers — [worksheet-charts.md](../features/worksheet-charts.md#chart-types).
`sum`, `avg`, `median`, `percentile`, `stddev` and `variance` on a non-numeric column are a 400 (`count` / `countDistinct` /
`countNonNull` / `min` / `max` are fine on any column; `attr` on any but a compound column). Aggregations:
`count` (rows), `sum`, `avg`, `min`, `max`, `countDistinct`, `countNonNull` (non-NULL values of the column,
`count(col)`), `median` (linear interpolation between the two middle values, like Excel `PERCENTILE.INC`), `stddev` / `variance` (sample; NULL for fewer than two values),
`attr` (the one distinct non-NULL value of the group, else NULL), `percentile`. The result column is named
`<agg> <column>` (`median amount`, `attr status`); a percentile is `p<percent> <column>` (`p90 amount`, `p99.5 amount`).
A **`percentile`** measure carries **`p`**, a finite number 0..1 (JSON `0.9`), required exactly when `agg` is `percentile` and refused
on any other aggregation or on a calculated measure; a missing or out-of-range `p` is a 400 at `measures[i].p` (never clamped), and a Top-N
`topBy` is checked the same at `filters[i].topBy.p`. `p` reaches SQL only as a bound `Float64` and is part of the cache key.

### Calculated fields (`calc`)

A row or column dimension (`ColumnRef`), a measure (`MeasureRef`) and a Top-N `topBy` may carry a
`calc` expression tree; the browser parses the formula and sends only the tree — no formula text
reaches the server or SQL.

```json
{ "db": "shop", "table": "orders", "column": "Margin", "agg": null,
  "calc": { "k": "bin", "op": "/",
    "l": { "k": "agg", "fn": "sum", "arg": { "k": "field", "db": "shop", "table": "orders", "column": "amount" } },
    "r": { "k": "agg", "fn": "sum", "arg": { "k": "field", "db": "shop", "table": "orders", "column": "qty" } } } }
```

- **Nodes** (discriminator `k`): `field` (`db`, `table`, `column`), `num` (`v`, finite), `un` (`op: "-"`),
  `bin` (`op` ∈ `+ - * /`), `str` (`v`, ≤ 100 characters, bound as a `String` parameter), `cmp` (`op` ∈ `= != < <= > >=`, `l`, `r`),
  `logic` (`op` ∈ `and or`, `l`, `r`), `not` (`arg`), `case` (`whens`: `[{ "c": cond, "t": result }]` — at least one — and an optional
  `else`; `IF`/`IIF` are one arm plus `else`), `ifnull` (`l`, `r`), `isnull` (`arg`), `fn` (`fn` ∈ `lower upper trim len left right replace concat contains startswith endswith split datediff dateadd year month day quarter week weekday date`, `args`: array), `agg` (`fn` ∈ `sum avg min max count countd median stddev variance percentile attr`, `arg`, and `p` for
  `percentile`). `count` counts non-NULL values (as `countNonNull`), `countd` distinct values. `p` is a finite
  number 0..1, required for `percentile` and refused on every other function (400 at `….calc.p`, "PERCENTILE
  needs a fraction between 0 and 1." / "SUM takes no fraction."); it is bound as a `Float64` parameter. Every referenced table must already be in the
  query (`from` or a join) — else the usual 400 "Field references a table not in the query."
- **With `calc` set**, `db` / `table` / `column` are not used in SQL, but they must still be present
  (an absent `column` is a binding 400, "'measures[0].column' is required.") — send empty strings when there
  is no label. `column` is only the **display label** (≤ 60 characters; longer is a 400 at `….column`),
  echoed in the result's `rowDimensions` / `measures`; an empty `column` falls back to `"calculation"`.
- **Role rules** (400, field `….calc`): an **aggregate** tree (contains an `agg` node) is valid only as a
  measure or `topBy` with `agg` absent or `null`; a **row-level** tree as a measure / `topBy` needs `agg` ∈
  `sum`, `avg`, `min`, `max`, `countDistinct`, `countNonNull`, `median`, `stddev`, `variance`, `attr` (`count` of
  rows is rejected — it would ignore the calculation; `percentile` has no row-level form; `sum` / `avg` /
  `median` / `stddev` / `variance` need a number); a row-level tree is valid as a dimension, an
  aggregate one there is a 400; a calculated dimension takes no `datePart` (`….datePart`) and is never
  date-grouped by `dateBucket`.
- **Text-function typing** (400 at `….calc.args.<i>` or the call): a text argument must be text ("LOWER needs a text — orders.amount is number."),
  the argument count is fixed ("LEFT takes 2 arguments.", "CONCAT takes 2 to 10 arguments."), `LEFT`/`RIGHT` length a number literal 0..1000, `SPLIT`
  position a literal 1..1000 and separator a text literal of 1..20 characters ("SPLIT's separator must be text written in the formula, 1 to 20 characters."); an unknown
  name is "Unknown function x.". Limits `CalcLimits.MaxCount` / `MaxSeparator` / `MaxConcat`, mirrored in `CALC_LIMITS`.
- **Date-function typing** (400 at `….calc.args.<i>`): a date argument must be a date ("YEAR needs a date — orders.status is text. Use DATE() to turn text into a date."; `DATE` takes text); the `DATEDIFF`/`DATEADD` unit is a `str` node from `year quarter month week day hour minute second`, any case ("DATEDIFF's unit must be one of 'year', … written in the formula as text."); the `DATEADD` amount is a `num` node, or `un` `-` over one, a whole number within ±100000 ("DATEADD's amount must be a whole number from -100000 to 100000 written in the formula."; `CalcLimits.MaxDateAmount`, `CALC_LIMITS.dateAmount`). Arity is fixed ("DATEDIFF takes 3 arguments.").
- **Logic typing** (400 at the node path; `w0.c` is the first WHEN's condition, `w1.t` the second's result, `else`):
  a condition must be boolean ("A condition needs a boolean — orders.amount is number."), every result one type ("All
  results must be the same type — …"), a comparison two values of one type, never boolean ("Comparison needs two values
  of the same type — …"), `AND`/`OR`/`NOT` booleans, a text literal ≤ 100 characters ("A text value can be at most 100
  characters."), a `case` with no arm ("A CASE needs at least one WHEN."). A boolean calculation is a dimension (keys
  `true` / `false` / `null`) or, when it aggregates, a measure; it takes no `sum`/`avg`.
- **Tree errors** name the node: `measures[0].calc.arg`, `rowDimensions[1].calc.l.r` — e.g. "SUM needs a
  number — orders.region is text.", "Unknown field orders.nope.", "Can't mix an aggregate with a
  row-level value in one formula.", "An aggregate can't contain another aggregate.", "That formula is too
  deep." / "too large.".
- **Results:** a number-typed calculation's values are numbers (division by zero → `null`); `min` / `max`
  of a text or date calculation are strings. A calculated dimension's keys are strings like any key —
  numbers in invariant form (`"0.3333333333333333"`, `"20"`), `null` for a NULL key.

The histogram and box-plot requests carry `filters` (`StatFilter`: column, op, value, values) that are
applied with the same typed rules as the worksheet query; filters on other tables can't apply to a
single-table view, so the client counts them and shows a notice.

There are no single-table `aggregate`, `preview` or `count` routes under `/api/databases/{db}/tables/{table}/` — they
were removed (a request to them is an unmatched route, 404). Raw rows have one home: `POST /api/rows` ([Rows](#rows)).

Request/response models: `ClickHouse/QueryModels.cs`, `StatisticalModels.cs`, `SchemaModels.cs`.

## Page

`GET /` → `Features/Shell/ShellController.cs` renders the one page. Feature assets are served at
`/features/<Feature>/<file>` (`.css`/`.js` only).
