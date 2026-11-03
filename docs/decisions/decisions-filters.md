---
components: [src/DashboardBuilder/ClickHouse/Identifier.cs, src/DashboardBuilder/Features/Core/validate.js]
---
# Decisions — filters on calculated fields

Part of the [decisions](decisions-platform.md) record: one decision, edited in place when it changes.

### D82 — A calculated field is a row filter, applied before grouping
Decided 2026-11-02 (autonomous build). A calculated field may be a **Filters** field; a calculation that aggregates may not.
- **Order of operations:** the calculation's compiled row-level expression is one more `WHERE` condition, `AND`ed with the plain filters, the selection, the drill path, the page and the date range. Rows are filtered **before** any aggregate runs, **before** a Top-N ranks its members (a Top-N ranks within the rows the other filters keep, as it already does for plain filters), and before table calculations and the display cap, which work on the grouped result. The Evaluation order popover counts it as a row-level calculation.
- **An aggregate calculation is refused** (400 at `filters[i].calc`, and a toast on drop): an aggregate has no row to test. A `HAVING`-style filter would cut groups after aggregation, which changes what every other filter and Top-N means, so it waits for the level-of-detail work ([backlog](../development/backlog/calculations.md)).
- **Wire:** `QueryFilter.calc` carries the tree; `db` and `table` are empty and `column` is the calculation's label (≤ 60 characters, as for a dimension). The compared values are bound as `p{i}`, the calculation's own literals as `c{n}`; the calculation goes through the one calc compiler, so identifiers are catalog-checked and quoted in `Identifier.cs` and a field on a table not in the query is a 400 (the worksheet adds the calculation's tables to the joins). Values are coerced by the calculation's **type** (number, text, date, boolean), with the same rules as a plain column; a calculation takes no cast.
- **Operators:** all of a plain field's except `top` (400 `filters[i].calc`) and, for a date, `in the` (a calculation's date width is unknown). `=` / `!=` / ordering on a calculation that yields NULL drop those rows, while `not in` keeps them (as for a plain column). No new limits: the 20-filter, 500-value and 1000-character bounds apply unchanged and are already mirrored in `Core/validate.js`.
- **Not shared:** a shared filter applies where its table is in the view; a calculation has no one table, so **Apply on every dashboard** is not offered.
- **Rejected:** evaluating the filter in the browser (the result is bounded, the filter must cut rows first); `HAVING` for an aggregate; sending the calculation's name instead of its tree (the server holds no calculations).
