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
  even with no connection; a valid body without a connection is 409.
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
| Measures | ≤ 10 |
| Joins | ≤ 10 |
| Filters per query | **≤ 20** (`MaxFilters`). The client allows 8 user filters, and the worksheet appends the shared filters (≤ 4), the drill path (≤ 5), the page, the selection and the date range |
| `in` values | ≤ 500; a filter value ≤ 1000 characters |
| `limit` (query, box plot, distinct) | 1–5000 (default 50; [D24](decisions.md#d24--showing-all-data-bounded-requests-paging-other-date-grouping)) · CSV export 1–100,000 · distinct 1–1000 (default 200) |
| `offset` (query) | 0–10,000,000 |
| Filter `op` | also `contains`, `startsWith`, `endsWith` (text columns, value required) and `top` (value 1–1000 + `topBy` measure, optional `bottom`; worksheet query only — histogram / box plot reject it) |
| `joins[].type` | `inner` (default) or `left` |
| `fresh`, `approximate` (query) | booleans — skip the result cache; approximate mode ([D25](decisions.md#d25--a-short-lived-server-result-cache-and-approximate-mode)). The response adds `cached` and `approx: { distinct, sample }` |
| `datePart` (a row / column dimension) | `auto`, `exact`, `year`, `quarter`, `month`, `week`, `day`, `hour`, `quarterOfYear`, `monthOfYear`, `dayOfWeek`, `hourOfDay`; date columns only |
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
- `between` needs both bounds and From ≤ To (number, date); `in` needs ≥ 1 value.

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
| `GET /api/databases/{db}/tables/{table}/columns/{column}/distinct?limit=` | distinct values for an `in` filter / Pages (default 200, 1–1000 else 400) | `SELECT DISTINCT … LIMIT n` |

## Query

Controller: `Features/Dashboard/QueryController.cs`. All `POST` with a JSON body.

| Method & path | Purpose | Shape |
|---|---|---|
| `POST /api/query` | worksheet query across joined tables; optional `offset` (paging), `withTotal`, `otherBucket`, `dateBucket` | `QueryRequest` → `QueryResult` (incl. `truncated`, `total?`, `other?`, `bucket?`) — `values` entries are a **number, a string or `null`** (see below) |
| `POST /api/query/export.csv` | CSV of the same plan, up to 100,000 rows (never an Other row) | `QueryRequest` → `text/csv` |
| `POST /api/databases/{db}/tables/{table}/histogram` | equal-width bins over one numeric column | `HistogramRequest` |
| `POST /api/databases/{db}/tables/{table}/boxplot` | five-number summary, optionally grouped | `BoxPlotRequest` → `{ groups, truncated }` |

**Measure values** (`QueryResultRow.Values`, `IReadOnlyList<object?>`) are a JSON number, a **string**
(`min` / `max` of a text or date column), or `null` (SQL NULL, or `NaN` / `∞` from an aggregate over no
rows). Consumers must not assume numbers — [worksheet-charts.md](../features/worksheet-charts.md#chart-types).
`sum` and `avg` on a non-numeric column are a 400 (`count` / `countDistinct` / `min` / `max` are fine on any
column).

The histogram and box-plot requests carry `filters` (`StatFilter`: column, op, value, values) that are
applied with the same typed rules as the worksheet query; filters on other tables can't apply to a
single-table view, so the client counts them and shows a notice.

There are no single-table `aggregate`, `preview` or `count` endpoints — they were removed (a request to
them is an unmatched route, 404).

Request/response models: `ClickHouse/QueryModels.cs`, `StatisticalModels.cs`, `SchemaModels.cs`.

## Page

`GET /` → `Features/Shell/ShellController.cs` renders the one page. Feature assets are served at
`/features/<Feature>/<file>` (`.css`/`.js` only).
