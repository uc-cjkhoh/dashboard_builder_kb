# Union and unpivot as a data source

A **union** (2–5 tables stacked) or an **unpivot** (wide same-kind columns of one table turned into `Field` / `Value` rows) can be added
to the Data Source as a card and read by worksheets like a table. Code: `Features/Core/source-model.js` (pure rules),
`Features/Canvas/canvas.js` (the card), `Features/Rows/union-dialog.js` / `unpivot-dialog.js` (the **Add to model** buttons),
`Features/Rows/SourceController.cs`, `ClickHouse/SourceSql.cs` (the derived table). The row **preview** of each is in
[schema-browser.md](schema-browser.md#union).

## Adding one

- The Union and Unpivot dialogs have **Show rows** (the preview) and **Add to model** (primary; enabled by the same pick rules). Add to
  model fires `source:add`; the canvas switches to the Data Source and puts the card in the first free slot
  ([canvas.md](canvas.md#union-and-unpivot-cards)).
- **Name** (automatic, not editable): `Union: a + b` or `Unpivot: sales`, cut to 200 characters (`LIMITS.sourceName`); a name already used by
  a table of the database or a card on the canvas gets ` 2`, ` 3` … (`takenNames`, `uniqueName`). The name is the entity's `table`, so every
  field reads `db.<name>.column` unchanged and labels read `Union: a + b.region`.
- **Columns** come from `POST /api/source/columns` ([api.md § Source columns](../reference/api.md#source-columns)):
  - Union: `Source table` (text; the table's name) then the columns **every table has with the same name and kind** — the preview's rule,
    stated on the card ("Columns shared by name and kind."). No renaming or manual alignment. Types are compared **without** `Nullable` / `LowCardinality`: when
    the base types are equal (`Int64` and `Nullable(Int64)`, `Bool` and `Nullable(Bool)`) nothing is cast and the column is declared `Nullable` if any
    table's is. When they truly differ, numbers are read as the widest **exact** type (integers of one signedness: the widest width; signed with
    unsigned: the next signed width, `UInt64` + `Int64` → `Int128`, `UInt128` → `Int256`), text as `String`, dates as `DateTime64(3)`. Only when no
    exact type exists (a `Decimal` in the mix, a 64-bit integer beside a float, `UInt256` beside a signed) does a numeric column fall back to
    `Float64` and the card shows a second line "Types differ: read as Float64, large values may round." (`lossy` in the columns response). A
    compound column of differing types is a 400. A shared column already called `Source table` makes ours `Source table_`.
  - Unpivot: the kept columns, then `Field` (text; the column's name) and `Value` (the unpivoted columns' kind; their type if equal after dropping `Nullable`, else the
    union's rules above). A column already named `Field` / `Value` makes ours `Field_` / `Value_`. Unlike the preview, `Value`
    keeps its kind, so it aggregates (sum, avg …) and filters like a column of that kind.
- A union with more than 200 shared columns lists the first 200 and says so in a toast.

## Reading one

- The sheet plan ([worksheet.md](worksheet.md)) sends `source` (the definition) beside `from` = `{ db, table: name }`; every field reference names the
  same `(db, name)`. Dimensions, measures, filters (including Top-N), sort, date grouping, paging, Other, approximate distinct counts, CSV
  export and the plan cache work as for a table.
- **Reads alone.** A view that mixes a source with another table is refused in the view: "A union or unpivot can't be combined with another
  table yet — use only its own fields in this view." (`sourceProblem`), and the server refuses a source with `joins` (400 `joins`). A source card
  takes no join keys and no relationship (dropping a table column on its rows says so); a saved workbook's source entity carries no keys.
- A filter's member list (`in`, Pages, member labels, groups) is a one-dimension `/api/query` over the source (limit 201, `distinctPlan`) instead
  of the table `distinct` endpoint.
- Not available over a source (each says so, nothing is sent): **View data** (raw rows of one table), column **profile** (no button on the card),
  **histogram** and **box plot** (single-table endpoints), and the approximate-mode 10 % sample (the source is read in full).

## Cost limit

A source query reads every source table in full (an unpivot reads its table once, via `arrayJoin`, but forms up to 50 rows per source row), so a wide
unpivot or a union of large tables multiplies the scan. The only server-side bound is `max_execution_time` (12 s) — and that is absent when the
connection's profile refuses settings ([sharp-edges.md](../conventions/sharp-edges.md#clickhouse)). The 50-column unpivot cap and the 2–5 table
union cap are the only extra limits; no row-read guard is added.

## Saved with the workbook

An entity of a source is saved as `{ id, db, table: name, x, y, joinKeys: [], source }` where `source` is `{ kind: "union", db, name, tables, columns? }` or
`{ kind: "unpivot", db, name, table, columns, keep }` ([data-model.md](../reference/data-model.md#workbook-file)). On open `cleanSource`
re-checks it against the same limits and that `db` / `name` match the entity; one that fails (including a name over 200 characters) is skipped with an import issue. A second entity with the same `db.table` as another (a source named like a real table) is skipped as any duplicate is, and a saved relationship that ends at a source is dropped with an issue. The columns are
fetched again from the server, so a table that has since changed shows its current columns.

## SQL shape

Read-only and bounded like every worksheet query: the statement keeps its `LIMIT` (page + 1), the 12 s time limit and `readonly=2`. The source is
a derived table read as `t0`:

- Union: `FROM (SELECT {us0:String} AS `Source table`, `a`, toInt128(`n`) AS `n` FROM `db`.`t1` UNION ALL SELECT {us1:String} AS … FROM `db`.`t2`) AS t0`.
- Unpivot: `FROM (SELECT `k`, tupleElement(`__up`, 1) AS `Field`, tupleElement(`__up`, 2) AS `Value` FROM (SELECT `k`, arrayJoin([({uf0:String}, `q1`), ({uf1:String}, `q2`)]) AS `__up` FROM `db`.`t`)) AS t0`.
- Every database, table and column is catalog-validated (`DESCRIBE`) and quoted by `Identifier` only; the union's table labels and the unpivot's field
  names are **bound** `String` parameters (`us#`, `uf#`, sent with every statement of the request: page, total, Other). The helper alias prefix
  grows until no table column starts with it. Statements that reuse only part of the request (the auto date-grain probe) carry the parameters of
  their `FROM` too.

## Not built

Listed in [data-model.md](../backlog/data-model.md): joining a source to another table, a relationship from a source, manual column alignment
and rename for a union, editing a source in place, Show rows / profile / histogram / box plot over a source, unions across databases.
