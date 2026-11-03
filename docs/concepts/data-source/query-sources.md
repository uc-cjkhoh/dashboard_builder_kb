---
components: [src/DashboardBuilder/ClickHouse/SourceSql.cs, src/DashboardBuilder/Features/Canvas/canvas.js, src/DashboardBuilder/Features/Core/source-model.js, src/DashboardBuilder/Features/Rows/SourceController.cs, src/DashboardBuilder/Features/Rows/union-dialog.js, src/DashboardBuilder/Features/Rows/unpivot-dialog.js]
---
# Union and unpivot as a data source

A **union** stacks 2–5 tables. An **unpivot** turns wide same-kind columns of one table into `Field` / `Value` rows.
Either can be added to the Data Source as a card and read by worksheets like a table.
The row **preview** of each is in [schema-browser.md](schema-browser.md#union).

**Code:**

- `Features/Core/source-model.js` — the pure rules
- `Features/Canvas/canvas.js` — the card
- `Features/Rows/union-dialog.js` / `unpivot-dialog.js` — the **Add to model** buttons
- `Features/Rows/SourceController.cs`
- `ClickHouse/SourceSql.cs` — the derived table

## At a glance

- **Add** a union or unpivot from its sidebar dialog with **Add to model**; it becomes a card with an automatic, non-editable name.
- **Union columns** are the ones every table shares by name and kind, after `Source table`; types widen to an exact type where one exists, else `Float64` with a warning.
- **Reads alone:** a source can't be joined or related to another table, and View data, profile, histogram and box plot are unavailable over it.
- **Cost:** sources are read in full; the 12 s time limit and the table / column caps are the only bounds.

## Adding one

- **Buttons.** The Union and Unpivot dialogs have **Show rows** (the preview) and **Add to model** (primary).
  Both are enabled by the same pick rules.
  Add to model fires `source:add`. The canvas switches to the Data Source and puts the card in the first free slot
  ([canvas.md](canvas.md#union-and-unpivot-cards)).
- **Name.** The name is automatic and not editable: `Union: a + b` or `Unpivot: sales`, cut to 200 characters (`LIMITS.sourceName`).
  - If a table of the database or a card on the canvas already uses the name, it gets ` 2`, ` 3` … (`takenNames`, `uniqueName`).
  - The name is the entity's `table`, so every field reads `db.<name>.column` unchanged and labels read `Union: a + b.region`.
- **Columns** come from `POST /api/source/columns` ([api.md § Source columns](../../reference/api.md#source-columns)).
- A union with more than 200 shared columns lists the first 200 and says so in a toast.

### Union columns

- `Source table` comes first (text; the table's name).
- Then come the columns **every table has with the same name and kind**. This is the preview's rule, stated on the card ("Columns shared by name and kind.").
  There is no renaming or manual alignment.
- A shared column already called `Source table` makes ours `Source table_`.

**How types are combined:**

1. Types are compared **without** `Nullable` / `LowCardinality`.
2. When the base types are equal (`Int64` and `Nullable(Int64)`, `Bool` and `Nullable(Bool)`), nothing is cast.
   The column is declared `Nullable` if any table's is.
3. When they truly differ:
   - numbers are read as the widest **exact** type.
     Integers of one signedness take the widest width. Signed with unsigned takes the next signed width (`UInt64` + `Int64` → `Int128`, `UInt128` → `Int256`).
   - text is read as `String`;
   - dates are read as `DateTime64(3)`.
4. Only when no exact type exists does a numeric column fall back to `Float64`.
   That happens with a `Decimal` in the mix, a 64-bit integer beside a float, or `UInt256` beside a signed type.
   The card then shows a second line, "Types differ: read as Float64, large values may round." (`lossy` in the columns response).
5. A compound column of differing types is a 400.

### Unpivot columns

- The kept columns come first, then `Field` (text; the column's name) and `Value`.
- `Value` has the unpivoted columns' kind. Its type is theirs if equal after dropping `Nullable`, else the union's rules above.
- A column already named `Field` / `Value` makes ours `Field_` / `Value_`.
- Unlike the preview, `Value` keeps its kind, so it aggregates (sum, avg …) and filters like a column of that kind.

## Reading one

- **Like a table.** The sheet plan ([worksheet.md](../worksheet/worksheet.md)) sends `source` (the definition) beside `from` = `{ db, table: name }`.
  Every field reference names the same `(db, name)`.
  Dimensions, measures, filters (including Top-N), sort, date grouping, paging, Other, approximate distinct counts, CSV
  export and the plan cache all work as for a table.
- **Reads alone.** A view that mixes a source with another table is refused in the view with
  "A union or unpivot can't be combined with another table yet — use only its own fields in this view." (`sourceProblem`).
  - The server refuses a source with `joins` (400 `joins`).
  - A source card takes no join keys and no relationship; dropping a table column on its rows says so.
  - A saved workbook's source entity carries no keys.
- **Filter member lists** (`in`, Pages, member labels, groups) use a one-dimension `/api/query` over the source (limit 201, `distinctPlan`)
  instead of the table `distinct` endpoint.
- **Not available over a source** (each says so, and nothing is sent):
  - **View data** (raw rows of one table);
  - column **profile** (no button on the card);
  - **histogram** and **box plot** (single-table endpoints);
  - the approximate-mode 10 % sample (the source is read in full).

## Cost limit

A source query reads every source table in full, so a wide unpivot or a union of large tables multiplies the scan.
An unpivot reads its table once, via `arrayJoin`, but forms up to 50 rows per source row.

- The only server-side bound is `max_execution_time` (12 s).
  That bound is absent when the connection's profile refuses settings ([sharp-edges.md](../../development/sharp-edges.md#clickhouse)).
- The 50-column unpivot cap and the 2–5 table union cap are the only extra limits. No row-read guard is added.

## Saved with the workbook

An entity of a source is saved as `{ id, db, table: name, x, y, joinKeys: [], source }`, where `source` is
`{ kind: "union", db, name, tables, columns? }` or `{ kind: "unpivot", db, name, table, columns, keep }`
([data-model.md](../../reference/data-model.md#workbook-file)).

On open:

- `cleanSource` re-checks the source against the same limits, and checks that `db` / `name` match the entity.
  One that fails (including a name over 200 characters) is skipped with an import issue.
- A second entity with the same `db.table` as another (a source named like a real table) is skipped, as any duplicate is.
- A saved relationship that ends at a source is dropped with an issue.
- The columns are fetched again from the server, so a table that has since changed shows its current columns.

## SQL shape

The query is read-only and bounded like every worksheet query: the statement keeps its `LIMIT` (page + 1), the 12 s time limit and `readonly=2`.
The source is a derived table read as `t0`:

- Union: `FROM (SELECT {us0:String} AS `Source table`, `a`, toInt128(`n`) AS `n` FROM `db`.`t1` UNION ALL SELECT {us1:String} AS … FROM `db`.`t2`) AS t0`.
- Unpivot: `FROM (SELECT `k`, tupleElement(`__up`, 1) AS `Field`, tupleElement(`__up`, 2) AS `Value` FROM (SELECT `k`, arrayJoin([({uf0:String}, `q1`), ({uf1:String}, `q2`)]) AS `__up` FROM `db`.`t`)) AS t0`.

Safety rules:

- Every database, table and column is catalog-validated (`DESCRIBE`) and quoted by `Identifier` only.
- The union's table labels and the unpivot's field names are **bound** `String` parameters (`us#`, `uf#`).
  They are sent with every statement of the request: page, total, Other.
- Statements that reuse only part of the request (the auto date-grain probe) carry the parameters of their `FROM` too.
- The helper alias prefix grows until no table column starts with it.

## Not built

Listed in [data-model.md](../../development/backlog/data-model.md):

- joining a source to another table, or a relationship from a source;
- manual column alignment and rename for a union;
- editing a source in place;
- Show rows / profile / histogram / box plot over a source;
- unions across databases.
