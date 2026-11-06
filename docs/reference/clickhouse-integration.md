---
components: [src/DashboardBuilder/, tests/live/]
---
# ClickHouse integration

How the server talks to ClickHouse: driver and connection, the exact SQL, the identifier-injection
defence, and type mapping. Read it before adding or changing a query or anything in the gateway.

Code lives in `src/DashboardBuilder/ClickHouse/`: `ClickHouseGateway.cs` (all SQL), `Identifier.cs`,
`ClickHouseType.cs`, `CsvUtil.cs`, `ConnectionRegistry.cs` and the `*Models.cs` records. Tags such as P26
or T02-34 are build-plan (Pnn) and backlog (Tnn-nn) item ids; D-numbers are [decisions](../decisions/decisions-platform.md).

## Driver & connection

- **Driver:** `ClickHouse.Client` 7.x (ADO.NET) over the **HTTP interface**
  ([D3](../decisions/decisions-platform.md#d3--clickhouseclient-over-the-http-interface)); TLS via `Protocol=https` on
  `ClickHouseConnectionStringBuilder`.
- **Ports:** the target server exposes only TLS ports: **`8443`** (HTTPS, used) and `9440` (native
  TLS, unused). Plaintext `8123`/`9000` are unavailable, so a real connection is always `secure` on
  `8443` ([D10](../decisions/decisions-platform.md#d10--connect-over-tls-only-https-port-8443)). A local throwaway container
  may expose plain `8123` for testing.
- **Connection string** is assembled server-side from the session's `ClickHouseConnectionInfo`; the
  password comes from the session store and is never logged or returned.
- **Validate on connect:** open and run `SELECT 1` before reporting "connected".
- **The `HttpClient`** handed to the driver:
  - accepts an untrusted cert **only** when `allowInvalidCert && secure`
    (`BypassesCertificateValidation`) — [D11](../decisions/decisions-platform.md#d11--tls-certificate-trust-self-signed-is-accepted-by-default-untick-to-verify);
  - **must** set `AutomaticDecompression` — ClickHouse.Client asks for compressed responses and throws
    otherwise;
  - has a **15s `Timeout`** so an unresponsive host fails cleanly.

## Database-level guards

`BuildConnectionString` appends ClickHouse settings (`set_` keys) that ride on **every** query:

| Setting | Value | Why |
|---|---|---|
| `readonly` | `2` | the server itself refuses DDL/DML (schema and data changes), so read-only does not rest on our builders alone ([D1](../decisions/decisions-platform.md#d1--read-only-against-clickhouse)) |
| `max_execution_time` | `12` s (`MaxExecutionSeconds`) | a runaway query stops server-side, before the 15s HTTP timeout (`HttpTimeoutSeconds`) |
| `cancel_http_readonly_queries_on_client_close` | `1` | when the browser aborts a superseded query, the request is cancelled and ClickHouse kills the query |

- **Cancellation path:** browser `AbortController` → ASP.NET `RequestAborted` (the controllers'
  `CancellationToken`) → the driver's HTTP request is cancelled → ClickHouse stops the query.
- **Timeout message:** ClickHouse code **159** maps to **504** "The query ran longer than 12 seconds and
  was stopped. Add a filter, lower Top-N, or use fewer fields." (`ApiControllerBase.DescribeFailure`).
- On a connection without the time limit, the 15s HTTP timeout stops the query instead and gets the
  same 504 (with "15 seconds").
- A client abort (`IsClientAbort`) is left to the framework. Every other failure stays a generic 502.

### Step-down when the server refuses a setting

The guard level (`QueryGuards` on `ClickHouseConnectionInfo`) is settled once, in `ValidateAsync`, and
every later query uses it. On a refusal, `NextGuards` picks the next level and `SELECT 1` is retried:

| Level | Settings sent | Reached when |
|---|---|---|
| `Full` | all three | default |
| `NoTimeLimit` | `readonly=2`, cancel-on-disconnect | code **452** (SETTING_CONSTRAINT_VIOLATION) — a profile constraint, almost always on `max_execution_time` |
| `None` | nothing | code **164** (READONLY — the account is already read-only), or 164/452 again at `NoTimeLimit` |

- Any other error ends the retries with the usual "Could not connect" message. At most three attempts.
- At `None` reached via 164, the server's own read-only still guards. At `None` reached via a `readonly`
  constraint, read-only rests on the SQL builders alone.
- The step-down is logged at Information (`ClickHouse refused guard settings Full; retrying with …`) —
  levels only, never the connection string.
- Unit-tested in `QueryGuardTests`.

### A wrong password can be a network restriction

ClickHouse users can be scoped by **source IP** (`<networks>` in `users.d/*.xml`, or `HOST IP`). From a
disallowed IP the server answers as if the credential were wrong, even with the right password:
`Code: 194 … password is incorrect, or there is no user with such name … (REQUIRED_PASSWORD)`, HTTP **401**.
The ClickHouse on `10.168.49.13` limits `default` to `127.0.0.1`, so from the app host it always returns 401.

- **Fix:** connect with a network-enabled account. Don't chase the password or change server access
  control (out of scope — [golden rule 1](../development/coding-standards.md#1-the-server-is-read-only-against-clickhouse)).
- **To tell them apart:** run `SELECT 1` over HTTPS from the app host and from the DB host with the same
  password; local success + remote 401 = allowed-networks, not the password.

## The queries (all read-only)

| Purpose | Gateway method | SQL |
|---|---|---|
| Validate connection | `ValidateAsync` | `SELECT 1` |
| List databases / tables | `ListDatabasesAsync` / `ListTablesAsync` | `SHOW DATABASES` / `SHOW TABLES FROM {db}` |
| Describe columns | `DescribeColumnsAsync` | `DESCRIBE TABLE {db}.{table}` |
| Distinct values | `DistinctValuesAsync` | `SELECT DISTINCT {col} AS v FROM … WHERE v IS NOT NULL ORDER BY v LIMIT n` (1..1000, rejected outside) |
| Column profile | `ProfileColumnAsync` (`ClickHouseGateway.Profile.cs`) | two statements over a `LIMIT 1000000` subquery — [below](#column-profile-box-plot-raw-rows-and-join-preview) |
| Worksheet query | `QueryAsync` | see below |
| Histogram | `HistogramAsync` | `WITH (SELECT min…) AS lo, (SELECT max…) AS hi, if(hi>lo,(hi-lo)/{bins},1) AS width SELECT least(toUInt32(floor(({c}-lo)/width)),{bins-1}) AS bin, … count() … GROUP BY bin … ORDER BY bin` |
| Box plot | `BoxPlotAsync` | `SELECT [{dim} AS label,] min, quantile(0.25), quantile(0.5), quantile(0.75), max … [GROUP BY label] LIMIT n`, then two more — [below](#column-profile-box-plot-raw-rows-and-join-preview) |
| Raw rows | `RowsAsync` | `SELECT {col}, … FROM {db}.{table} [WHERE …bound…] LIMIT n+1` — [below](#column-profile-box-plot-raw-rows-and-join-preview) |
| CSV export | `QueryAsync` | the worksheet query, serialised by `CsvUtil` |

`{db}`, `{table}`, `{col}` are **interpolated identifiers** ([see below](#identifier-injection)). Every other
variable part is a bound parameter or a validated integer. Out-of-range limits are rejected before the
builder runs ([api.md § Limits](api.md#limits)).

### Column profile, box plot, raw rows and join preview

- **Column profile** — two statements over a `LIMIT 1000000` subquery of the column:
  - `SELECT count(), countIf(isNull(v)), uniq(v)[, toString(min(v)), toString(max(v))]`. Min/max are for
    numeric and date columns only, hidden when empty or all-NULL; compound types read as `toString`.
  - `SELECT label, cut, count() FROM (SELECT leftUTF8(toString(c), 100) AS label, lengthUTF8(toString(c)) > 100 AS cut …) GROUP BY label, cut ORDER BY count() DESC, label LIMIT n`
    (`n` 1..50, default 10). It groups on the cut label, so a huge string is never a key and values
    differing only after character 100 count together.
  - Both end `SETTINGS max_rows_to_read = 1000000, read_overflow_mode = 'break', max_bytes_before_external_group_by, max_memory_usage`,
    so the bound holds for views / Merge / Distributed tables. A server refusing the settings (codes 115,
    164, 452) gets the plain statement.
  - `uniq` is approximate. `sampled` is true at ≥ 1,000,000 rows.
- **Box plot** — after the summary `SELECT`, two more bounded SELECTs run on the same filtered rows, joining
  per-group Q1/Q3 (`CROSS JOIN` when ungrouped). The same bound filter parameters are reused.
  - `BuildBoxWhiskerSql`: `minIf`/`maxIf` inside the Tukey fences.
  - `BuildBoxOutlierSql`: values beyond them, with a `LIMIT 501` probe.
- **Raw rows** — the columns are catalog-checked (default: the first 200) and filters use
  `BuildSingleTableFilters`. There is **no ORDER BY**. `n` is 1..1000 (rejected outside), and an extra probe
  row sets `truncated`. Each column is selected as `if(isNull(c), NULL, left(toString(c), 1001))`, so a
  cell is cut inside ClickHouse ([limits](api.md#rows)).
- **Join preview** (`JoinPreviewAsync`, `ClickHouse/JoinPreview.cs`, [api.md](api.md#relationship-preview)) —
  one `SELECT` per side, run together, over `(SELECT {col} AS k FROM {db}.{table} LIMIT n)` grouped by key.
  It counts rows, NULL rows, distinct keys, max repeat, and `k IN (the other table's first n keys)`. Text
  keys compare as `toString`. `n` is 1..1,000,000.

### Worksheet query (`QueryAsync`)

`SELECT {rowDims} AS k0…, {colDims} AS kR…, {agg}({m0}) AS v0, … FROM t0 [INNER JOIN tN ON …] [WHERE …]  (t0 may be a union / unpivot derived table, [query-sources.md](../concepts/data-source/query-sources.md#sql-shape))
[GROUP BY k0, …] ORDER BY … LIMIT n [OFFSET m]`

- **Joins:** the base table is `t0`. Each join edge attaches a table aliased `tN` in order, so any
  dimension, measure or filter can live on any included table. An edge is `INNER`/`LEFT`/`RIGHT`/`FULL JOIN`
  (`type`, `JoinKeyword`). A compound key's `pairs` are catalog-validated and ANDed into `ON` (`JoinOn`; tests `CompoundJoinTests`, `tests/live/compound-smoke.mjs`). An outer one ends the request `SETTINGS join_use_nulls = 1` (right/full without it: 400).
  Filters are `WHERE`, so a NULL-extended side's rows drop. Right/full reject `top` (400) and skip `SAMPLE`. Tests: `JoinTypeTests`.
- **Dimensions** arrive split by shelf — `rowDimensions[]` then `columnDimensions[]` — and group in that
  order, so each row's keys are `[rowDim…, colDim…]`. `measures[]` aggregate as `v0, v1, …`. No measures
  → an implicit `count()`.
- **Ordering:** `sort:{column, desc}` names a generated alias (`k{n}`/`v{n}`), validated against the
  request's counts. The remaining dimension keys follow ascending. Default: ascending by the first
  dimension (or first measure).
- **Limit:** validated ([api.md § Limits](api.md#limits)), then sent as limit **+ 1** (`ProbeLimit(n, max)`). If the probe row comes
  back, it is dropped and the result is flagged `truncated` (`TrimProbeRow`), and the client shows a
  notice. The box plot does the same. Unit-tested in `TruncationTests`.
- **Paging:** `offset` adds `OFFSET m` to the same ordered query (the Table view's pages). The order ends
  with every group key, so pages never overlap or skip.
- **Total** (`withTotal`): `SELECT count() FROM (<grouped query>)` on its own connection, alongside the page.
- **Other** (`otherBucket`, one dimension, a truncated first page): `SELECT uniqExact(k) + max(isNull(k)) AS n, <measures>
  FROM … WHERE … AND k NOT IN (SELECT k0 FROM (<ordered query> LIMIT n)) SETTINGS transform_null_in = 1`
  It uses the same filters and excludes the shown keys exactly. A shown NULL group isn't recounted; a NULL group
  past the limit is counted (`uniqExact` alone skips NULL). If the server refuses the setting, the result
  comes back without `other` (logged), never an error.
- **Date parts** (P26, `datePart` on a dimension): `toStartOfYear` / `toStartOfQuarter` / `toStartOfMonth`
  / `toMonday` / `toDate` / `toStartOfHour` (truncations) or `toQuarter` / `toMonth` / `toDayOfWeek` /
  `toHour` (discrete) via `DatePartExpression`, a whitelist. `hour` on a `Date` column becomes `day`;
  `hourOfDay` needs a time; a part on a non-date column is a 400. A dimension with its own part is left
  out of the chart-wide `dateBucket`. Tests: `DatePartTests`.
- **Type cast** (T02-34, `cast` on a dimension, measure, filter or `topBy`): `text` | `number` | `date`.
  It is validated in `RequestRules` (an unknown word or a cast on a calculation = 400 at `….cast`) and applied
  in `TypeCast.Apply` after the catalog-checked, quoted column:
  - to text: `toString`;
  - text → number: `toFloat64OrNull(toString(x))`, kept only when finite (`inf`, `nan`, `1e999` are NULL; padded, comma and hex text are NULL too);
  - boolean → number: `toFloat64`;
  - text → date: `parseDateTimeBestEffortOrNull(toString(x))`, but text of only digits, spaces, signs, commas and dots is NULL unless it is `YYYYMMDD` (best-effort would read `10` as the 10th of the *current* month);
  - an already-matching type is left alone; number/date → date or date → number is a 400.

  Only `OrNull` variants are used, so bad data is NULL. A filter on a cast column compares those values, so a
  row that failed to convert is NULL: `=`, `!=`, `>`, `between` and `in` drop it, `notin` keeps it. The cast
  column's category (and "not a `Date`") then drives the aggregation check, filter value coercion and date
  parts. Join keys, histogram, box plot and distinct values ignore it. Tests: `TypeCastTests`, `tests/live/cast-smoke.mjs`.
- **Date grouping** (`dateBucket`): the first temporal dimension is wrapped in one whitelisted function:
  `toStartOfHour` / `toDate` / `toMonday` / `toStartOfMonth` / `toStartOfQuarter` / `toStartOfYear`
  (`BucketExpression`; a Date column never goes finer than day). `auto` first reads `uniq`, `min`, `max`
  under the view's filters. ≤ 400 distinct values stays exact; otherwise it picks the finest grain with ≤ 400 buckets
  (`PickGrain`). The response says which key and grain (`bucket`). Tests: `ScaleTests`.
- **Richer filters** (P30): text match uses `positionCaseInsensitiveUTF8` / `startsWith` / `endsWith` on
  `lowerUTF8`, with the text bound as a `String`. **Top-N** is built after the other conditions as
  `col IN (SELECT col FROM <same joins> WHERE <other filters> GROUP BY col ORDER BY <agg> DESC|ASC LIMIT n)`.
  Tests: `RicherFilterTests`.
- **Measure filter** (`having`, [D84](../decisions/decisions-filters.md#d84--a-filter-on-an-aggregated-measure-having-keeps-groups-after-grouping)): `BuildHaving` appends ` HAVING (v0 >= {h0:Float64}) AND (…)` after `GROUP BY` (before `ORDER BY` / `LIMIT`, and inside the group-count statement). The operand is the generated `v{n}` alias of a validated measure index — never client text — the operator comes from `BuildCondition`'s whitelist narrowed to `RequestRules.HavingOps`, and every number is a bound `Float64`. Top-N's rank subquery doesn't carry it; the Other statement isn't built with it (400). Tests: `HavingTests`; live: `tests/live/having-smoke.mjs`.
- **Result cache** (P33): `QueryAsync` answers a repeat of the same request on the same server + user from
  `IMemoryCache` for 60 s (logged; `cached: true`). `fresh` skips and replaces it (`CacheKey`; tested: no
  password, `fresh` ignored).
- **Approximate** (`approximate`): `uniq` instead of `uniqExact`. When `system.tables.sampling_key` is set
  for the base table, it reads `FROM … AS t0 SAMPLE 0.1`, with `count()` → `sum(t0._sample_factor)` and
  `sum(x)` → `sum(x * t0._sample_factor)`. A refused sampled query re-runs unsampled. The response's `approx` says what was done. Exercised live (a `SAMPLE BY` table, plain and
  calculated measures, a calculated Top-N rank) by `tests/live/calc-smoke.mjs`.
- **Compression:** API responses are Brotli/gzip-compressed (fastest level, `Program.cs`).
- **Response:** `QueryResult` and its `values` rules are in [api.md](api.md#measure-values-and-aggregations); the client pivots it ([worksheet-table-view.md](../concepts/worksheet/worksheet-table-view.md#table-view--a-true-rows--columns-crosstab)).

### Calculated fields and aggregates

A `calc` tree compiles in four steps (request rules, catalog, validate, compile) with one parameter list per request; the aggregate table (exact, sampled, approximate) and Top-N rank rules are in [clickhouse-calculations.md](clickhouse-calculations.md).

### Shared defences in the builders

- **Whitelists:** aggregations ([api.md](api.md#measure-values-and-aggregations); `countDistinct` → `uniqExact`,
  `countNonNull` → `count(col)`), calculation node kinds, operators and functions (`CalcValidator`, `CalcCatalog`), and
  filter operators `= != > >= < <= in notin between` (plus text match and top-N).
- **Typed bound values** (`FilterValues.Coerce`, `ClickHouse/RequestValidation.cs`): the rules are
  [api.md § Typed filter values](api.md#typed-filter-values). Binding is via ClickHouse.Client's `AddParameter`
  (`using ClickHouse.Client.Utility`): number → `{p0:Float64}`, date / datetime → `String`, boolean → `UInt8`,
  text → `String`; `in` / `notin` bind `Array(Float64)` / `Array(String)` / `Array(UInt8)`.
- **Rejected on the server, not silently ignored:** an empty `in` / `notin`, a half or inverted range, an unknown operator.
  The client never sends a blank filter, so to the user an empty filter is still "ignored".
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
([golden rule 2](../development/coding-standards.md#2-never-interpolate-an-identifier-you-havent-validated),
[D6](../decisions/decisions-platform.md#d6--identifiers-validated-against-the-live-catalog--backtick-quoted)):

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
