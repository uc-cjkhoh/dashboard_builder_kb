---
components: [src/DashboardBuilder/Features/Calc/, src/DashboardBuilder/Features/Dashboard/calc-manager.js, src/DashboardBuilder/Features/Dashboard/dashboards.js]
---
# Calculated fields

A **calculated field** is a named formula over fields of the data source, used like a field: `SUM([orders.amount]) / SUM([orders.qty])` on a shelf, in a mark slot, in a Top-N rank.

The browser keeps the formula text. Before a query it expands and type-checks the formula into a tree, which ClickHouse computes on the read-only, bounded path ([compile path](../../reference/clickhouse-calculations.md#the-compile-path); wire shape in [api-calculated-fields.md](../../reference/api-calculated-fields.md)).

- **Code:** `Features/Calc/` ([frontend-modules.md](../../architecture/frontend-modules.md)). The dialog and pane group are wired from `Dashboard/dashboards.js`.

## At a glance

- **Where it runs:** the server receives the expanded tree, never formula text, and compiles it to bounded, bound-value SQL. Role is derived (aggregate or row-level, never both) and re-derived by the server.
- **Broken is not deleted:** a calculation that can't compute is kept; its sheets send no query and say why.
- Rationale per rule: [decisions-calculated-fields.md](../../decisions/decisions-calculated-fields.md).

## The dialog

The list dialog is in [Field pane group](#field-pane-group). **New calculated field** and **Edit…** open one editing dialog. Code: `calc-dialog.js`; all logic in `calc-dialog-model.js`.

The editing dialog has:

- **Name** — 1 to `LIMITS.calcName` characters after trimming, no `.`, `[` or `]`, unique ignoring case. A name problem shows only after the box was touched, and never hides the formula's own message.
- **Formula** — a text box.
  - **Field autocomplete:** typing `[` opens a list of fields and other calculations (a calculation never offers itself). Arrow keys move; Enter or Tab (after arrowing) accepts; Esc closes the list and not the dialog.
  - **Function autocomplete:** typing the start of a function name (a letter prefix outside `[ ]` and outside a text literal, e.g. `LO`) offers up to 12 matching functions in the same list, each with its signature (`LOWER(text)`). Not offered when the caret is inside a word. Accepting inserts `LOWER(` with the caret after the bracket; before an existing `(` no second one is added. `AND`, `OR`, `NOT` and `CASE` insert the word and a space.
  - **Robust input:** CRLF is normalised; control characters and over-long text give a message, never an exception.
- **Functions** — a button under the formula opens a help panel (`aria-expanded`; Esc closes the panel and not the dialog).
  - A search box filters the glossary (name, group, plain-words sentence, signature). The list is grouped Aggregate, Logic, Text, Date.
  - Hovering or focusing a row shows its detail: signature, what it does, what it takes, what it gives, one example formula and the empty-value (NULL) rule.
  - Clicking a row inserts its signature at the caret (replacing a selection). **Insert example** inserts the example of the function last focused with the keyboard or clicked (hovering only previews).
  - After an insert, focus returns to the formula box, so Esc then closes the dialog. The dialog body scrolls so Cancel / Save stay visible.
  - Code: the glossary (`function-help.js`) derives names, arity and result types from `calc-types.js`. A test fails when a function has no entry or an entry has no function, and checks that every example formula parses and type-checks.
- **Live message** — the first problem, in plain words, with `(at character N)` and a caret mark when the parser knows the position. Unknown field and cycle messages name the cause.
- **Role chip** — icon plus text, never colour alone: `Aggregate · number`, `Row-level · text`, `Row-level · boolean`, "No formula yet", or "Can't be saved".
- **Use as** — a Measure / Dimension choice, shown only for a **row-level number**. It is a session-only default for chips dragged afterwards and is not saved in the workbook. A pill already placed keeps its own role.
- **Save** is disabled until the draft names, parses, resolves, type-checks and expands without a cycle. Cancel and Esc discard. Saving an edit under a new name rewrites `[Old]` to `[New]` in every other calculation's formula, so no reference breaks (`[table.Old]` is left alone).

## Field pane group

Calculations are not in the field pane itself. On a worksheet tab, the sidebar's calculator icon opens the **Calculated fields** dialog (`Dashboard/calc-manager.js`). It lists one row per calculation: its chip (name, role chip such as `Aggregate · number`, the add **+** and a **⋯** menu) and an **Edit** button. **New calculated field** sits in the dialog footer and is disabled at the count limit. The dialog redraws while open whenever calculations change. The **⋯** menu:

| Action | Behaviour |
|---|---|
| Edit… | opens the dialog (a group field: the Group dialog, [below](calculated-fields-groups.md)) |
| Duplicate | adds `<name> copy` (`copy 2` … when taken) with the same formula (or groups) and Use-as choice |
| Delete… | Refused with a toast `Used by calculation 'B'.` while another calculation refers to it. When worksheets or shared Top-N filters use it, a confirm says how many, and Delete clears its pills and filters (and a sort or Top-N ranking aimed at it) from them. Otherwise it deletes at once |

- **Broken calculation** (its field left the model, an imported cycle): shows an **Error** badge instead of the role chip, with its message as the tooltip. It cannot be dragged or added.
- **Adding:** the **+** puts a calculation on a shelf (Rows for a measure, Columns for a dimension); calculations are not dragged from this list.

## What a calculated pill is

A pill is `{ calc: id, db: "", table: "", column: <name at last save>, category, role, agg? }`.

- `category` follows the type (`numeric`, `text`, `temporal`, `boolean`).
- The empty `db` / `table` keep every reader of `f.db` / `f.table` / `f.column` safe. The **live name** always comes from the workbook's list by `calc` id.
- A row-level number used as a measure carries `agg: "sum"`.
- After any calculation change, every sheet's pills refresh their category, role and name (`syncCalcPills`). After undo, redo or opening a workbook, the sheet's calculated pills re-read the live calculation's type and role.

**Where it goes.** Calculated pills go on Rows, Columns, Color, and the Size, Label, Path and Detail / Tooltip slots. They may be a Top-N ranking measure and a sort target.

- A calculated dimension is never date-grouped: no date-part picker, and a saved `datePart` is removed.
- A calculated **measure's** aggregation menu offers only sum, avg, min, max, distinct count and non-null count (`CALC_AGGS`, mirroring the server's `CalcCatalog.RowLevelAggregations`). It never offers `count`, which the server refuses for a calculation; a saved `count` resets to sum on open.

**Top-N by a calculation.** A Top-N filter ranked by a calculation stores `topBy: { db: "", table: "", column, calc: id, agg? }` and is saved and restored like any other.

- **Deleting the calculation** counts that filter as a use (the confirm appears). Confirming keeps the filter but clears its ranking. The filter panel then ranks by the first shelf measure again; until then the filter reports "Pick a measure to rank by." and is not sent.
- **Shared Top-N filters** behave the same: it counts as a use ("… and 1 shared Top N filter"), and its ranking is cleared.
- **A calculation that can no longer be computed** stops the view with the usual `Calculation 'X' can't be computed: …` message. A ranking that cannot be wired is never sent as `topBy: null`. Such a Top-N is refused like a pill (below).

### Where a calculated field is refused

Dropping one on any of these shows the toast **`Calculated fields can't be used here yet.`** and adds no pill:

- Pages, drill-down, the date range, a shared filter, a click selection (a **filter** takes a row-level calculation — [Filters](worksheet-filters.md#calculated-fields-as-filters)); an aggregate one is refused there too, with `Calculation 'X' can't be a filter: …`;
- the Shape and Angle slots;
- a field-choice list (a calculated pill has no field choices).

Click-to-filter is **off** when the primary dimension (the drill level, else the first Rows / Columns dimension) is a calculation; the legend still highlights.

**Histogram and box plot** run single-table endpoints that know nothing of calculations. With a calculated pill on Columns or Rows they show **`Histogram and box plot don't use calculated fields yet.`** in the chart slot and send no query.

## Error state

A calculation that can't be computed is kept, not dropped (an unknown or removed field, a missing table, a cycle, a deleted calculation).

- Any sheet that uses it (a pill, or a Top-N ranked by it) sends **no query**. It shows `Calculation 'X' can't be computed: <reason>` in the chart slot and for CSV export. Fix or delete the calculation and the view recomputes.
- A sheet whose only pills are field-less calculations (`1+2`) shows "Add a field from a table — a calculation with no field in it has nothing to group or total." and sends no query.

## Non-null count

**Non-null count** is a valid aggregation for every field category (`aggsFor`), shown as `non-null <name>` everywhere (the server names the result column that way, so chart, CSV header and compare agree). A calculation's `COUNT(...)` is the same aggregate.

## How this is computed

A view-bar button opens a popover listing, for the current sheet, the six stages in the order they run. Code: `explain-popover.js` (text only); Esc or an outside click closes it and returns focus.

1. **Filters** — own, shared, drill, page, selection, date range and Top-N filter that ClickHouse applies.
2. **Row-level calculations** — worked out for each remaining row.
3. **Group by** — the dimensions, or a single group when there are none.
4. **Aggregates** — including aggregate calculations.
5. **Cap and Other** — the display cap (Top-N "All" = 5000 groups) and the Other bucket when the chart folds one.
6. **Table calculations** — run in the browser on the returned groups.

The text is generated from the live sheet (`eval-order.js`), so it is current whenever it opens.
