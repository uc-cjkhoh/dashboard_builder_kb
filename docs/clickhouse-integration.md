# ClickHouse integration

How the ASP.NET Core server talks to ClickHouse: the driver, the connection, the exact
introspection/preview SQL, type handling, and the **identifier-injection** rules that
keep read-only queries safe. Server code lives under `src/DashboardBuilder/ClickHouse/`
([ARCHITECTURE.md](../ARCHITECTURE.md)).

## Driver & connection

- **Driver:** `ClickHouse.Client` **7.x** (ADO.NET provider) over the **HTTP interface**
  ([decision D3](project/decisions.md)). Standard `DbConnection` / `DbCommand` usage. TLS is
  selected with `Protocol=https` on `ClickHouseConnectionStringBuilder`.
- **Ports (secure-only requirement):** the target ClickHouse exposes **only the TLS
  ports** — **`8443`** (HTTPS interface, the one this app uses) and **`9440`** (native
  TCP over TLS, not used here). The plaintext ports `8123`/`9000` are **not** available.
  So a real connection is always **`secure` (TLS) on port `8443`** — treat that as the
  default, not an option. (A local throwaway container may still expose plain `8123` for
  testing — [development.md](development.md) — but anything pointed at the real server is
  TLS on 8443.)
- **Connection string** is assembled server-side from the session connection
  ([data-model.md](data-model.md)) — host, port (`8443`), user, password, and the TLS flag
  (`secure=true`, i.e. `ClickHouse.Client`'s HTTPS protocol). The password is taken from
  the session store; it is **never** logged or returned.
- **Validate on connect:** open the connection and run `SELECT 1` before reporting
  "connected". Surface a clean error (no credentials in the message) on failure.
- **Self-signed certs:** the server's cert is self-signed, so `ClickHouseGateway` hands the
  driver an `HttpClient` whose handler (a) accepts an untrusted cert when `allowInvalidCert`
  is set ([decision D11](project/decisions.md)) and (b) **must set `AutomaticDecompression`** —
  ClickHouse.Client requests compressed responses and throws *"server returned compressed
  result but HttpClient did not decompress it"* otherwise. The HttpClient also carries a
  bounded `Timeout` so an unresponsive host fails cleanly instead of hanging.

> **Gotcha — a "wrong password" can actually be a network restriction.** ClickHouse users
> can be scoped by **source IP** (`<networks>` in `users.d/*.xml`, or `HOST IP` on a
> SQL-created user). When a request comes from a **disallowed IP**, the server rejects it
> with a message that *looks* like a bad credential:
> `Code: 194 … Authentication failed: password is incorrect, or there is no user with such
> name … (REQUIRED_PASSWORD)` (HTTP **401**) — even when the password is correct.
> Concretely: the ClickHouse on `10.168.49.13` restricts its **`default`** user to
> `<ip>127.0.0.1</ip>`, so `default` authenticates **only from the ClickHouse host itself**.
> From the app host (`10.168.49.20`) it always 401s. **Fix: connect with a different,
> network-enabled account** — do *not* chase the password (it's a red herring) or change
> the server's access control. To tell the two apart, run `SELECT 1` over the HTTPS
> interface from the app host and from the DB host; if it succeeds locally but 401s
> remotely with the *same* password, it's the account's allowed-networks list, not the
> password. (Server-side access control is out of scope for this app — golden rule 1.)

## The queries (all read-only)

| Purpose | SQL | Status |
|---|---|---|
| Validate connection | `SELECT 1` | ✅ P1 |
| List databases | `SHOW DATABASES` | ✅ P3 |
| List tables | `SHOW TABLES FROM {db}` | ✅ P3 |
| Describe columns | `DESCRIBE TABLE {db}.{table}` | ✅ P4 |
| Preview rows | `SELECT * FROM {db}.{table} LIMIT {n}` | ✅ P4 |
| Row count (KPI) | `SELECT count() FROM {db}.{table}` | ✅ |
| Chart aggregate (single table) | `SELECT {dim}, {agg}({m}) FROM {db}.{t} [WHERE …] [GROUP BY {dim}] ORDER BY value DESC LIMIT n` | ✅ |
| Worksheet query (joined, crosstab) | `SELECT {rd…} AS k0…, {cd…} AS kR…, {agg}({m0}) AS v0, … FROM t0 [INNER JOIN tN ON …] [WHERE …] [GROUP BY k0, …] ORDER BY (k0,… \| v0 DESC) LIMIT n` | ✅ |
| Distinct values (P14 filter) | `SELECT DISTINCT {col} AS v FROM {db}.{t} WHERE v IS NOT NULL ORDER BY v LIMIT n` | ✅ |
| Histogram (P12) | `WITH (SELECT min({c}) FROM … [WHERE]) AS lo, (SELECT max({c}) …) AS hi, if(hi>lo,(hi-lo)/{bins},1) AS width SELECT least(toUInt32(floor(({c}-lo)/width)),{bins-1}) AS bin, lo+bin*width AS x0, …, count() FROM … [WHERE] GROUP BY bin,x0,x1 ORDER BY bin` | ✅ |
| Box plot (P12) | `SELECT [{dim} AS label,] min({m}), quantile(0.25)({m}), quantile(0.5)({m}), quantile(0.75)({m}), max({m}) FROM {db}.{t} [WHERE] [GROUP BY label] LIMIT n` | ✅ |
| CSV export (P13) | *reuses the worksheet query* → serialised by `CsvUtil` (RFC-4180 + formula-injection guard) | ✅ |

> **Worksheet join query (`QueryAsync`).** The base table is `t0`; each join edge attaches a table
> (`INNER JOIN … AS tN ON t0.k = tN.k`) aliased in order, so any dimension/measure/filter can live
> on any included table. Dimensions arrive **split by shelf** — `rowDimensions[]` (Rows → crosstab
> left stub) then `columnDimensions[]` (Columns → top header) — and are grouped in that order, so
> each row's keys are `[rowDim…, colDim…]` (selected `k0, k1, …`); `measures[]` are aggregated as
> `v0, v1, …`. **No measures → an implicit `count()`.** Ordering: `sort:{column,desc}` names a
> generated alias (`k{n}`/`v{n}`, server-validated against the counts — never interpolated blindly);
> the server orders by it, then appends the remaining dimension keys ascending so the crosstab layout
> stays stable. **Default is ascending by the first dimension** (or first measure if none). The
> response is
> `QueryResult { rowDimensions:[name], columnDimensions:[name], measures:[name], rows:[{keys, values}] }`;
> the client pivots it into the Rows×Columns matrix. ClickHouse has no native `PIVOT`, so the pivot
> is done client-side over one bounded `GROUP BY` (verified against `sumIf` cross-tabs). Every table +
> column is catalog-validated and quoted; aggregations/operators whitelisted; filter values bound.
> Invalid identifier / table-not-in-query → **400**.
>
> **Aggregate/chart query (`AggregateAsync`).** Dimension / measure / filter columns are validated
> against the table's `DESCRIBE` and quoted; the aggregation (`count/sum/avg/min/max/countDistinct`,
the last mapped to `uniqExact`) and filter
> operators (`= != > >= < <=`) come from **whitelists**; filter **values are bound as typed
> parameters** (`{p0:Float64}` for numeric columns else `{p0:String}`, via ClickHouse.Client's
> `AddParameter` extension — `using ClickHouse.Client.Utility`) — never interpolated. Row count is
> clamped. An invalid identifier/agg/op → the endpoint's **400**.
>
> **Statistical shapes (P12) & richer filters (P14) keep the same defences.** `HistogramAsync` and
> `BoxPlotAsync` are **single-table** (a distribution is one column): the column is `DESCRIBE`-validated,
> quoted, and required to be **numeric**; the bin count is clamped (1..100) and the max value is clamped
> into the last bucket so a bucketing query can't explode; the box plot's `LIMIT` is clamped. Filter
> `WHERE` clauses on these paths run through the pure **`BuildSingleTableFilters`** (same whitelist +
> binding). `DistinctValuesAsync` powers the P14 `in`-filter dropdown — one column, `DISTINCT … ORDER BY
> … LIMIT n` with `n` clamped (1..1000) so a high-cardinality column can't flood the client. The P14
> filter operators **`in`** and **`between`** are built by the pure **`BuildCondition`**: `in` binds an
> `Array(String)` (or `Array(Float64)` when every value parses) — `{p0:Array(String)}` — and `between`
> binds two typed bounds; **all values stay bound, never interpolated**, an empty `in`/partial range is a
> **no-op** (never `IN ()`), and an unknown operator → **400**. These pure builders are unit-tested with
> hostile columns/operators.

> **List tables validates `{db}` first.** `ListTablesAsync` calls `SHOW DATABASES` and confirms
> the requested name is present (ordinal match) before interpolating `SHOW TABLES FROM
> {Identifier.Quote(db)}` — the two-part defence of golden rule 2. An unknown/hostile name
> throws `UnknownIdentifierException` → the endpoint returns **404**, so nothing hostile ever
> reaches SQL.

Richer metadata, if needed, comes from the system catalog instead of `SHOW`/`DESCRIBE`:
- `system.databases`, `system.tables`, `system.columns` (name, type, `is_in_primary_key`,
  comment, …). Useful for filtering, ordering, or showing which columns are in the
  sort/primary key — but remember that's a **sparse index, not a constraint**
  ([decision D5](project/decisions.md)).

`{db}`, `{table}` above are **interpolated identifiers** — see the injection rules below.
`{n}` (the preview limit) is a **value** and should be a **bound parameter** or a
validated integer, not string-concatenated.

## Identifier injection — the one that will bite you

ClickHouse (like most SQL) lets you bind **values** as parameters but **not
identifiers**. `SHOW TABLES FROM ?` and `DESCRIBE ?` are not a thing — the db/table/column
names must be written into the SQL text. Those names arrive from the client, so unguarded
they are an injection vector (`; DROP …`, cross-database reads, etc.).

**Rule ([decision D6](project/decisions.md), [CLAUDE.md](../CLAUDE.md) golden rule):**
before any identifier reaches a query it must be

1. **Validated against the live catalog** for the *current* connection — the `db` is one
   of `SHOW DATABASES`, the `table` is one of `SHOW TABLES FROM {db}`, the column is one
   of that table's `DESCRIBE`. Reject anything not present. This alone defeats injection
   because only real object names pass.
2. **Backtick-quoted with internal backticks escaped** — ClickHouse quotes identifiers
   with backticks; `` ` `` inside a name is doubled (`` `` ``). Quoting is defense in
   depth on top of validation.

Centralize both steps in one helper (`ClickHouse/Identifier.cs`) and route **every**
interpolated identifier through it. Never hand-format an identifier at a call site.

> Why not "just parameterize"? Because you can't — parameters bind values. The preview's
> `LIMIT` *is* a value, so bind or integer-validate that; the table name is *not*, so it
> must go through validate-then-quote.

## Type mapping

`DESCRIBE`/`system.columns` return **ClickHouse type strings**, not SQL-92
([CLAUDE.md](../CLAUDE.md) gotcha). Expect wrappers and rich types:

| Example type | Display hint |
|---|---|
| `UInt64`, `Int32`, `Float64`, `Decimal(18,4)` | numeric → right-align (`.num`), monospace |
| `String`, `FixedString(n)` | text |
| `Nullable(T)` | render `T`, mark nullable |
| `LowCardinality(T)` | treat as `T` for display |
| `Array(T)`, `Map(K,V)`, `Tuple(…)` | compound → show compactly / truncate in preview |
| `Enum8('a'=1,…)` | enum |
| `Date`, `DateTime`, `DateTime64(3)` | temporal |
| `UUID`, `IPv4`, `IPv6` | opaque id/text |

Keep a small mapper that reduces a type string to a **display category** (numeric / text /
temporal / compound / other) for the entity card's type badge and grid alignment. Don't
assume `int`/`varchar`.

> **Built (P4):** `ClickHouse/ClickHouseType.cs` — `Categorize(type)` unwraps
> `Nullable(...)` / `LowCardinality(...)`, takes the base name before `(`, and returns
> `numeric | text | temporal | boolean | compound | other` (unit-tested). `DescribeColumnsAsync`
> attaches the category to each `{name,type}`; `PreviewAsync` clamps the limit to
> `MaxPreviewRows = 500` and stringifies cells (`FormatCell` — invariant numbers, `[a, b]` for
> arrays/tuples, hex for byte blobs, JSON `null` for NULLs). Both validate db+table against the
> catalog first (unknown → the endpoint's 404).

## Safety & performance notes

- **Always bound previews** (`LIMIT`); never `SELECT *` a table without a limit — some
  tables are billions of rows ([CLAUDE.md](../CLAUDE.md) gotcha).
- **No FK metadata exists** — don't look for it; relationships are user-defined
  ([data-model.md](data-model.md)).
- **Scope every query** to the connection + database the request names; two sessions (or
  two databases in one session) must not bleed into each other.
- **Errors:** map ClickHouse errors to clean client messages; never include the
  connection string or password.
