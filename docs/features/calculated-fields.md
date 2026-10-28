# Calculated fields

A **calculated field** is a named formula over fields of the data model, used like a field:
`SUM([orders.amount]) / SUM([orders.qty])` on a shelf, in a mark slot, in a Top-N rank. The browser keeps
the formula text; before a query it expands and type-checks the formula into a tree that ClickHouse
computes on the read-only, bounded path ([clickhouse-integration.md](../reference/clickhouse-integration.md#calculated-fields--the-compile-path),
wire shape in [api.md](../reference/api.md#calculated-fields-calc)). Code: `Features/Calc/`
([frontend-modules.md](../reference/frontend-modules.md)); the dialog and pane group are wired from
`Dashboard/dashboards.js`. Rationale: [decisions.md](../reference/decisions.md) D26–D47.

## Formulas

- Grammar: `expr := term (("+"|"-") term)*`; `term := factor (("*"|"/") factor)*`;
  `factor := "-" factor | number | "(" expr ")" | aggregate | ref`; `aggregate := FN "(" expr ")"`;
  `ref := "[" name "]"`. Numbers are decimals with an optional exponent (`12`, `1.5`, `.5`, `1.`, `1e3`; no
  `1,000`; a non-finite `1e999` is an error). `SUM`/`AVG` take a number; `MIN`/`MAX` a number, date or text;
  `COUNT`/`COUNTD` any type; arithmetic needs numbers; an aggregate inside an aggregate is refused. A field of
  a category other than numeric, text, temporal or boolean can't be used.
- Operators `+ − * /`, parentheses, numbers, and the aggregates `SUM`, `AVG`, `MIN`, `MAX`, `COUNT`,
  `COUNTD` (function names are case-insensitive). The function table lives in `calc-types.js`.
- A **reference** is `[table.column]` (`[db.table.column]` when two databases hold the same table name) or
  `[Name]` for another calculation. Calculations can refer to calculations; the browser expands every
  reference into one tree before sending, so the server never sees a calculation name.
- Division by zero gives an empty (NULL) value, never an error.
- A formula with no field references (`1+2`) is valid. It needs a field from a table elsewhere on the sheet
  to have anything to group or total.

### Roles and types

The check yields a type (number, text, date, boolean) and whether the formula is an **aggregate**:

| Formula | Role | Used as |
|---|---|---|
| contains an aggregate (`SUM([a]) / SUM([b])`) | measure | aggregated by the server, no further aggregation |
| row-level text, date or boolean | dimension | a group key |
| row-level number | measure **or** dimension | measure sums it per row (`SUM([price] * [qty])`); dimension groups by it |

Mixing an aggregate with a bare row-level field in one formula is refused by the checker with a message.

### Limits

Read from `Core/validate.js` `LIMITS` (`calculations`, `calcFormula`, `calcName`) and `CALC_LIMITS` in
`calc-types.js` (formula length, depth, nodes) — the server mirrors depth, nodes and name length in
`CalcLimits`. A formula over the length limit, a tree over the depth or node limit, a name over the length
limit and a workbook over the calculation count are refused with a message; none is clamped.

## The dialog

**New calculated field** (field pane) and **Edit…** open one dialog (`calc-dialog.js`; all logic in
`calc-dialog-model.js`):

- **Name** — 1 to `LIMITS.calcName` characters after trimming, no `.`, `[` or `]`, unique ignoring case.
  A name problem shows only after the box was touched and never hides the formula's own message.
- **Formula** — a text box. Typing `[` opens an autocomplete of fields and other calculations (a
  calculation never offers itself); arrow keys move, Enter or Tab (after arrowing) accepts, Esc closes the
  list and not the dialog. A fresh formula text is always a string: CRLF is normalised, control characters
  and over-long text give a message, never an exception.
- **Live message** — the first problem, in plain words, with `(at character N)` and a caret mark when the
  parser knows the position. Unknown field and cycle messages name the cause.
- **Role chip** — icon plus text, never colour alone: `Aggregate · number`, `Row-level · text`, "No
  formula yet", or "Can't be saved".
- **Use as** — a Measure / Dimension choice, shown only for a **row-level number**. It is a session-only
  default for chips dragged afterwards; it is not saved in the workbook. A pill already placed keeps its
  own role.
- **Save** is disabled until the draft names, parses, resolves, type-checks and expands without a cycle.
  Cancel and Esc discard. Saving an edit under a new name rewrites `[Old]` to `[New]` in every other
  calculation's formula, so no reference breaks (`[table.Old]` is left alone).

## Field pane group

A **Calculated fields** group sits above the tables: a **New calculated field** button (disabled at the
count limit) and one chip per calculation showing its name, role chip (`Aggregate · number` …) and a
**⋯** menu:

| Action | Behaviour |
|---|---|
| Edit… | opens the dialog |
| Duplicate | adds `<name> copy` (`copy 2` … when taken) with the same formula and Use-as choice |
| Delete… | refused with a toast `Used by calculation 'B'.` while another calculation refers to it; when worksheets or shared Top-N filters use it, a confirm says how many, and Delete clears its pills (and a sort or Top-N ranking aimed at it) from them; otherwise it deletes at once |

A calculation that can't be computed (its field left the model, an imported cycle) shows an **Error**
badge instead of the role chip, its message as the tooltip, and cannot be dragged or added. The search
box filters the group by name. Chips drag or **+** onto shelves like fields; the **+** goes to Rows for a
measure and Columns for a dimension.

## What a calculated pill is

A pill `{ calc: id, db: "", table: "", column: <name at last save>, category, role, agg? }`.
`category` follows the type (`numeric`, `text`, `temporal`, `boolean`); the empty `db` / `table` keep every
reader of `f.db` / `f.table` / `f.column` safe, and the **live name** always comes from the workbook's list
by `calc` id. A row-level number used as a measure carries `agg: "sum"`. After any calculation change every
sheet's pills refresh their category, role and name (`syncCalcPills`).

Calculated pills go on Rows, Columns, Color, and the Size, Label, Path and Detail / Tooltip slots, and may be
a Top-N ranking measure and a sort target. A calculated dimension is never date-grouped: its pill shows no
date-part picker or step buttons, and a saved `datePart` is removed (on sync and on open).

A calculated **measure's** aggregation menu offers only sum, avg, min, max, distinct count and non-null count
(`CALC_AGGS`, mirroring the server's `CalcCatalog.RowLevelAggregations`) — never `count`, which the server
refuses for a calculation; a saved `count` resets to sum on open. After undo, redo, applying a bookmark or
opening a workbook, the sheet's calculated pills re-read the live calculation's type and role.

**Top-N by a calculation.** A Top-N filter ranked by a calculation stores `topBy: { db: "", table: "", column,
calc: id, agg? }` and is saved and restored like any other. Deleting the calculation counts that filter as a
use (the confirm appears); confirming keeps the filter but clears its ranking, and the filter panel ranks by
the first shelf measure again (until then the filter reports "Pick a measure to rank by." and is not sent).
The same holds for a **shared** Top-N filter: it counts as a use ("… and 1 shared Top N filter"), and its ranking
is cleared. A Top-N whose calculation can no longer be computed stops the view with the usual
`Calculation 'X' can't be computed: …` message; a ranking that cannot be wired is never sent as `topBy: null`.
A Top-N whose calculation can't be computed is refused like a pill (below).

### Where a calculated field is refused

Dropping one on any of these shows the toast **`Calculated fields can't be used here yet.`**, adds no pill:
a filter, Pages, drill-down, the date range, a shared filter, a click selection, the Shape and Angle slots,
and a field-choice list (a calculated pill has no field choices). Click-to-filter is **off** when the
primary dimension (the drill level, else the first Rows / Columns dimension) is a calculation; the legend
still highlights.

**Histogram and box plot** run single-table endpoints that know nothing of calculations: with a calculated
pill on Columns or Rows they show **`Histogram and box plot don't use calculated fields yet.`** in the chart
slot and send no query.

## Error state

A calculation that can't be computed (unknown or removed field, missing table, cycle, a calculation that
no longer exists) is kept, not dropped. Any sheet that uses it (a pill, or a Top-N ranked by it) sends **no query** and shows, in the chart
slot and for CSV export, `Calculation 'X' can't be computed: <reason>`. Fix or delete the calculation and
the view recomputes. A sheet whose only pills are field-less calculations shows the hint "Add a field from
a table — a calculation with no field in it has nothing to group or total." (no query).

## Non-null count

**Non-null count** is a valid aggregation for every field category (`aggsFor`), shown as `non-null <name>` everywhere: the server names the
result column that way (`countNonNull`, `count(col)`), so the chart, the CSV header and a compare result agree. A
calculation's `COUNT(...)` is the same aggregate.

## How this is computed

A view-bar button opens a popover (`explain-popover.js`, text only; Esc or an outside click closes it and
returns focus) listing, for the current sheet, the six stages in the order they run:

1. **Filters** — own, shared, drill, page, selection, date range and Top-N filter that ClickHouse applies.
2. **Row-level calculations** — worked out for each remaining row.
3. **Group by** — the dimensions, or a single group when there are none.
4. **Aggregates** — including aggregate calculations.
5. **Cap and Other** — the display cap (Top-N "All" = 5000 groups) and the Other bucket when the chart folds one.
6. **Table calculations** — run in the browser on the returned groups.

The text is generated from the live sheet (`eval-order.js`), so it is current whenever it opens.
