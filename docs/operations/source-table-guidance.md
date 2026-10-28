# Source-table guidance

Practical advice for people who own the ClickHouse tables the Dashboard Builder reads. The app never
changes a table ([golden rule 1](../conventions/golden-rules.md#1-the-server-is-read-only-against-clickhouse)),
so every fix below is made on the ClickHouse side. Each section says what the app sends, then what that
means for table design. This is guidance, not a guarantee: ClickHouse's own docs decide how an index or
partition behaves, and the app does not check or enforce any of it.

## What the app sends

Every worksheet view is a bounded aggregate ([clickhouse-integration.md](../reference/clickhouse-integration.md#worksheet-query-queryasync)):

`SELECT dims, aggregates FROM base [JOIN …] WHERE filters GROUP BY dims ORDER BY … LIMIT n`

- **Filters** are `WHERE` conditions: `=`, `!=`, `>`, `>=`, `<`, `<=`, `in` / `notin`, `between`, text
  match, and relative date ranges (resolved in the browser to a bound `between` over whole days —
  [worksheet-encodings.md](../features/worksheet-encodings.md)).
- **Top-N** is a subquery `col IN (SELECT col … GROUP BY col ORDER BY agg LIMIT n)` over the same joins.
- **Date grouping** wraps the date column in `toStartOfMonth`, `toDate` and similar functions.
- **Rows preview, column profile and join preview** read a table directly, with row bounds
  (details in [Previews](#previews-and-the-first-million-rows)).

There is no `SELECT *` path and no unbounded query. The app does not read ClickHouse's index or
partition metadata and does not tune its SQL per table; a well-laid-out table is simply faster.

## Sorting key (`ORDER BY` / primary key)

ClickHouse's primary key is a sparse index that follows the table's `ORDER BY`. It prunes data best for
conditions on its leading columns.

- Put the columns that dashboards filter on most first: usually the date or time column and a tenant,
  customer or account id, whichever your dashboards narrow by most often.
- Order the key from lower to higher cardinality after that, so equal values sit together and compress well.
- A filter on a column that is not in the key still works, but reads far more data. Because every
  view re-aggregates from the table, the cost repeats on each change of the view.
- A calculated filter or a column cast (`toFloat64OrNull(toString(x))` and friends) wraps the column in a
  function, so it cannot use the key the way a plain comparison does.
- A primary key is a sparse index, not a uniqueness constraint
  ([clickhouse-integration.md](../reference/clickhouse-integration.md#identifier-injection)); do not rely on it
  to deduplicate rows the dashboard counts.

## Partitioning

- Partition by month (`toYYYYMM(date)`) or at most by day for very large tables. Partitions exist to drop
  or move old data, not to speed up a dashboard; the sorting key does that.
- Do not partition by a high-cardinality column (user id, tenant id, a string). It creates many small
  parts, which slows inserts and every query that spans them.
- A relative date range ("last 30 days", "this month") is a plain `between` on the date column, so a
  date-based partition key lets ClickHouse skip whole months. It only helps when the filter is on the
  partition column itself, not on a cast or calculated version of it.

## Column types

The app reads types from `DESCRIBE` and groups them into categories: numeric, text, temporal,
boolean, compound, other ([clickhouse-integration.md](../reference/clickhouse-integration.md#type-mapping)).

- **Use real `Date` / `DateTime` columns, not strings.** Date grouping, date parts and relative date
  filters need a temporal column. The worksheet's type cast (text to date through
  `parseDateTimeBestEffortOrNull`, with a digit guard) is a workaround for data you cannot change: it
  returns NULL for text it cannot read, runs for every row of every query, and defeats the key and
  partition pruning. Fix the column type at the source.
- **Use real numeric types for measures.** `sum`, `avg`, `median`, `stddev` and `variance` need a numeric
  column and are refused (400) on text. A number stored as text goes through `toFloat64OrNull`, with the
  same costs as above.
- **`LowCardinality(String)`** suits a text dimension with few distinct values (status, country,
  channel); it is smaller and faster to group and filter. It is not worth it for a column with
  millions of distinct values. The app unwraps `LowCardinality(...)` and `Nullable(...)` when it
  categorises a column, so neither changes how a field appears.
- **Compound columns** (`Array`, `Map`, `Tuple`, `Nested`) cannot be filtered, linked or aggregated by
  the builder ([relationships.md](../features/relationships.md#what-may-be-linked)). Expose a scalar column
  (or a view that unnests it) for anything dashboards need.
- **Very long strings** are not a problem for the previews (cells are cut to 1,000 characters and the
  profile groups on the first 100), but a long string used as a dimension gives wide group keys.

## Join keys

A relationship is a logical declaration, not a database fact ([data-model.md](../reference/data-model.md)).
At run time it is a `JOIN … ON` between the two key columns.

- **Make both key columns the same type.** The app only allows number-to-number, text-to-text,
  date-to-date and boolean-to-boolean links ([relationships.md](../features/relationships.md#what-may-be-linked)),
  but it does not look deeper: `UInt32` against `String` of digits is blocked, while `UInt32` against
  `Int64` links and relies on ClickHouse to compare them. If ClickHouse refuses to compare two types,
  "Check this join" reports it as a 400 ([relationships.md](../features/relationships.md#check-this-join-join-safety-preview)).
- **Keep the same width and sign too** (`UInt64` on both sides, not `UInt64` and `Int32`) so the join does not
  rely on implicit conversion.
- **A cast does not apply to join keys** ([clickhouse-integration.md](../reference/clickhouse-integration.md#worksheet-query-queryasync));
  the key columns are used as they are.
- **Join from the large table to the small one.** ClickHouse builds the right-hand table in memory. Keep the
  dimension table (customers, products) small and the fact table large, and keep keys unique on the
  "one" side. Use "Check this join" to see repeats: keys repeating materially on both sides is many-to-many
  fan-out, and sums and counts can double-count.
- **Index the key as a sorting-key column** on the large side when you can (after the tenant and
  date columns), so a filter plus join reads less.
- A NULL join key never matches ([relationships.md](../features/relationships.md#join-type-p31-t02-12-t02-13)).

## NULLs

- The app treats NULL as "no value": `count(x)` skips it, a NULL group shows as a null key, `in`
  and `between` drop NULL rows, `notin` keeps them.
- `Nullable(T)` costs an extra mask column and slows scans a little. Use it only when "unknown" differs
  from a real value. If a default such as `0` or an empty string already means "none", the dashboard will
  count and average that default as data: `avg` over zeros-for-missing is wrong. Choose one convention per
  column and keep it.
- A left, right or full join makes the app send `join_use_nulls = 1`, so unmatched rows return NULL
  instead of the type's default (`0`, empty string). The measures then skip them. The setting needs a
  ClickHouse account allowed to change it: on a connection whose server refuses settings, right and
  full joins are refused (400) ([relationships.md](../features/relationships.md#join-type-p31-t02-12-t02-13)).
- A dimension that is NULL for a share of rows forms its own group, which counts toward the 5,000-group
  cap.

## Limits that shape table design

| Limit | Value | Effect |
|---|---|---|
| Query time | 12 s `max_execution_time` on every query ([clickhouse-integration.md](../reference/clickhouse-integration.md#database-level-guards)) | A slower query is stopped and the user sees a 504 "ran longer than 12 seconds" message. If the account's profile forbids the setting, the app steps down and the 15 s HTTP timeout applies instead. |
| Chart / table groups | 1..5,000 groups per request, 50 by default; CSV export up to 100,000 ([api.md](../reference/api.md#limits)) | The result is cut and flagged `truncated`; the client shows a notice. A dimension with more distinct values than that cannot be shown in full. |
| Result cache | 60 s per identical request ([clickhouse-integration.md](../reference/clickhouse-integration.md#worksheet-query-queryasync)) | Repeat views are fast; a changed filter is a new query. |

- **12 seconds is a hard budget.** A fact table that needs a full scan to answer a month filter will time
  out as it grows. Fix the sorting key and partitioning first; then pre-aggregate.
- **Keep dimensions to a plottable size.** A chart is capped at 5,000 groups, and a GROUP BY on a
  column with millions of values spends its time before the cap applies (top-N and the "Other" bucket
  still aggregate everything). Offer a coarser column (month instead of timestamp, region instead of
  postcode) alongside the fine one.
- **Distinct counts and medians cost most.** `uniqExact` and `quantileExactInclusive` hold every
  value of a group in memory. The approximate mode swaps in `uniq` (see below).

## Pre-aggregated tables and materialized views

For a very large fact table, point the builder at a summary instead of the raw rows.

- Build a table or materialized view at the grain dashboards use (day, tenant, key dimensions), with
  `SummingMergeTree` or `AggregatingMergeTree` for additive totals, and sorted by the filter columns.
- Aggregate in a way that stays correct when re-aggregated: store `sum` and `count`, not an average,
  because the builder takes `avg` or `sum` over your rows, and it cannot merge ClickHouse
  aggregate-function states.
- Distinct counts do not re-aggregate: a day-level `uniq` summed over months over-counts. Keep the raw
  or a separate table for those.
- Expose the summary as its own table; the builder lists tables and views from `SHOW TABLES` and
  treats them alike. A view can be read, but the sorting key and partitioning of its underlying table
  are what make it fast.

## Sampling and approximate mode

The worksheet has an "Approximate (faster)" option
([worksheet.md](../features/worksheet.md#format), [D25](../reference/decisions.md#d25--a-short-lived-server-result-cache-and-approximate-mode)).
What it does, from [clickhouse-integration.md](../reference/clickhouse-integration.md#worksheet-query-queryasync):

- Distinct counts use `uniq` instead of `uniqExact`. This needs nothing from the table.
- If `system.tables.sampling_key` is set for the base table, the query adds `SAMPLE 0.1` (a fixed 10%) and scales
  counts and sums by `_sample_factor`. Median, percentile, standard deviation, variance and ATTR run on the
  sample unscaled, so they are estimates; the info line says so.
- A refused sampled query re-runs unsampled; a view with a right or full join, or without a sampling key,
  is read exactly. The response's `approx` says what was done.

What this means for you:

- The builder uses sampling only when the table already declares `SAMPLE BY`. It does not add one.
- To make sampling available, declare `SAMPLE BY` on a column that is in the `ORDER BY`, uses an
  evenly distributed hash such as `intHash32(id)`, and appears in the key. This has to be decided when the
  table is created.
- A sample of 10% is an estimate; small groups can be badly off. It is not a substitute for a good
  sorting key.

## Previews and the first million rows

- **Row preview** (`/api/rows`): `LIMIT n+1` with no `ORDER BY`, up to 1,000 rows. Cheap on any table
  since ClickHouse stops at the limit.
- **Column profile** reads at most the first 1,000,000 rows of the column, so the numbers describe that
  slice ("sampled" at 1,000,000 or more), not the whole table
  ([clickhouse-integration.md](../reference/clickhouse-integration.md#the-queries-all-read-only)).
- **Check this join** reads at most 1,000,000 rows per side, with no `ORDER BY`. The first million
  rows are not a statistical sample: on a table sorted by date they are the oldest rows
  ([relationships.md](../features/relationships.md#check-this-join-join-safety-preview)).

## Checklist

- [ ] The sorting key starts with the columns dashboards filter on (date, tenant or customer id).
- [ ] Partitioned by month (or coarser); never by a high-cardinality column.
- [ ] Dates are `Date` / `DateTime`, measures are numeric, so no casts are needed.
- [ ] Low-distinct text dimensions are `LowCardinality(String)`.
- [ ] Join keys have the same type on both sides; the "one" side's keys are unique.
- [ ] "Check this join" shows no unexpected many-to-many warning.
- [ ] NULL versus a default value is a deliberate choice per column.
- [ ] A typical dashboard view answers well inside 12 seconds on the full table.
- [ ] Dimensions have a coarse variant under 5,000 distinct values.
- [ ] Very large fact tables have a pre-aggregated table or materialized view.
- [ ] If approximate mode matters, the table declares `SAMPLE BY` on a hashed key in its `ORDER BY`.

## Related

[clickhouse-integration.md](../reference/clickhouse-integration.md) · [relationships.md](../features/relationships.md) ·
[worksheet.md](../features/worksheet.md) · [development.md](development.md)
