---
components: [src/DashboardBuilder/Features/Dashboard/action-model.js, src/DashboardBuilder/Features/Dashboard/chart.js, src/DashboardBuilder/Features/Dashboard/collapse-model.js, src/DashboardBuilder/Features/Dashboard/hierarchy-dialog.js, src/DashboardBuilder/Features/Dashboard/period-model.js]
---
# Worksheet encodings — click-to-filter, Drill, Pages, date range

Interactions that narrow or step through the data. All ride the **existing** bounded aggregate/join query and the bound-parameter filter path; no encoding adds a server query shape ([D18](../../decisions/decisions-platform.md#d18--marks-card-and-pages-shelf-are-client-encodings-on-the-existing-query-shape)).

Base worksheet: [worksheet.md](worksheet.md). Marks and colours: [worksheet-marks.md](worksheet-marks.md). Filters: [worksheet-filters.md](worksheet-filters.md). State shapes: [data-model.md](../../reference/data-model.md#marks-pages-selection-drill).

## At a glance

- **Click-to-filter** selects a mark's primary-dimension value, then offers Keep only / Exclude / View data.
- **Drill** walks an ordered same-table hierarchy. **Pages** steps one dimension one member at a time.
- **Date range** is a filter with an optional comparison period.

## Click-to-filter

Clicking a chart mark **selects** its primary-dimension value into `sheet.selection`. Code: `chart.js` forwards the ECharts click; `selectHandler` / `toggleSelection` map `dataIndex` → the raw value.

A **selection chip** (`.ws-select`) offers:

- **Keep only** → `col = value` · **Exclude** → `col != value` · **✕** clear.
- **Legend clicks** (P29):
  - Clicking a legend item **highlights** that series; the others dim (ECharts `emphasis.focus: "series"`). Clicking it again clears.
  - When the legend lists a dimension's members — a Colour split, a Shape split, or a pie / donut's slices — the click also **selects** that member. The bar then offers Keep only / Exclude exactly as a mark click does.
  - A legend of measures only highlights.
  - The legend never hides series on click. ECharts' toggle is undone at once and the click is handed to the worksheet a tick later, so a re-render never disposes the chart mid-event.
- **Link action** (P39) — when the sheet has one (Format → **Link action**: a label and an `https://` address with `{value}`):
  - An **"<label> ↗"** button opens that address with the selected value URL-encoded into `{value}`, in a new tab with `noopener`. Nothing opens without that click.
  - Only `https:` links with a host are accepted. `http:`, `javascript:`, `data:` and the like are refused with the reason. A value can't change the host or break out of its slot.
  - One link action per sheet (`sheet.urlAction`). Rules: `Dashboard/action-model.js` (unit-tested).
- **Parameter action** (P39) — when the sheet has one (Format → **Parameter action** → a parameter, or None):
  - A **"Set <parameter>"** button on the chip writes the selected value into that parameter. Nothing changes without the click.
  - The value is checked like any parameter edit (its type and allowed values). A refused value changes nothing and a toast says why.
  - A parameter deleted leaves no button and clears the action (also on opening a workbook without it). One per sheet (`sheet.paramAction = { param }`); the parameter's usual consumers (filters, Top N, calculated fields) re-run as for any edit.
  - Sets (a click adding a member) need P25 and stay in the backlog.

How the action applies:

- It is a bound-parameter filter appended in `buildPlan` **only when the column's table is already in the query** — a click never forces a join.
- Exclude is a single-value `!=`. To exclude several members, use a `not in` filter.
- Clicking the same mark again clears it.
- Works on bar, stacked, line, area, combo, pie, donut and scatter (incl. colour-split). Other types and null values are no-ops.
- On a dashboard the same click filters the other widgets at once ([dashboards.md](../workbook/dashboards.md#cross-widget-filtering)).
- Why select-then-act: [D16](../../decisions/decisions-platform.md#d16--click-to-filter-is-a-select-then-act-worksheet-selection).

## Drill-down

The **Drill** tool takes ≥2 dimension fields **from one table** as an ordered hierarchy (year → quarter → month) on `sheet.drill`:

1. The **current level leads the group-by.** `buildPlan` prepends it as the first row dimension, so it drives the category axis.
2. Clicking a mark **drills one level finer**, pinning the clicked value. Every pinned ancestor is a bound `=` filter on the drill table (same table → never a join). An active drill takes clicks instead of selection.
3. A **breadcrumb** shows `All › 2023 › Q2`. Each crumb jumps up; **Up** goes up one level. Clicking at the finest level does nothing. Style: `.ws-drill`, `--warn` tint.

- A hierarchy holds at most **6** levels; a further add is refused with a toast.
- Editing the levels resets the descent.
- A hierarchy with no shelf fields renders an implicit-count chart of the current level.
- Why one table: [D17](../../decisions/decisions-platform.md#d17--drill-down-is-a-single-table-hierarchy-on-the-bound-param-path).

### Named hierarchies

A **named hierarchy** (T03-29) is a reusable drill path kept on the workbook: `{ id, name, levels: [{ db, table, column }] }`.

- **Rules:** 2–6 levels, all from one table, no repeated column (the same rules as the Drill tool). At most **20** per workbook. A name of 1–60 characters, unique case-insensitively.
- **Not allowed as a level:** a calculated field (the calc refusal text) or a field with a type cast ("A field with a type cast can't be a hierarchy level").
- **Managing them.** The sidebar's drill icon on a worksheet tab opens the Hierarchies dialog (`Dashboard/hierarchy-dialog.js`). Its own **+ New hierarchy** button starts a new one. Double-clicking a hierarchy row (not its buttons) presses **Use**: it sets the worksheet's drill levels and closes the dialog; the **Use** button is the keyboard path.
  - Each row has **Use** (sets the worksheet's drill levels), **Edit** and **Delete** (Delete confirms).
  - Editing: a name, a table, and an ordered level list built with an "Add a level" picker and per-level **Up / Down / Remove** buttons (labelled, keyboard-operable; focus stays on the control just used).
- **Applying.** **Use** on a dialog row **replaces the sheet's drill** with `{ levels, depth: 0, path: [] }` — the structure a hand-built drill has, each level carrying its column's category — so the chart, breadcrumb and click-to-drill behave identically.
- **The sheet gets a copy** of the levels. Renaming, editing or deleting the hierarchy later never changes a sheet that already used it.
- **Refusals.** A column cast after the hierarchy was made refuses with the cast message, and a column no longer in the table refuses too. The dialog's Edit keeps a level whose column has vanished until it is removed or replaced.
- Hierarchies are client-side only (the server never sees one) and save with the workbook ([workbook.md](../workbook/workbook.md)).

### Expand / collapse headers

In the Table and Text views, a Rows or Columns header that has a next level below it (every dimension but the last on its shelf) carries a **+ / −** button before its label.

- **Collapsing** hides every level below that header. The header stands for them as one row (or column, spanning the remaining header levels). The outermost collapsed header wins.
- **No button** on a last-level header or the measure band. The Dashboard widget draws a sheet's saved collapsed state but has no buttons — only the editor toggles.
- **Accessibility:** a real `<button>` with `aria-expanded` and an `aria-label` of "Collapse <header> (rows)" / "Expand <header> (columns)". The icon changes with the state, the header text beside it names the member, and focus returns to the button after the redraw.
- Code: `Dashboard/collapse-model.js`, drawn by `crosstabTable`.

- **Values stay correct.** A collapsed header's cells are its children's cells combined by the measure's own aggregation (`combine`, the rule the subtotals and grand totals use): sums and counts add; min / max take min / max.
  - An average, median, distinct count, percentile or table calculation cannot be rebuilt from its parts, so it shows "—". Nothing is re-aggregated in the browser.
  - Totals and the subtotal row read the full data, so they don't change. A first-level subtotal row is not drawn under a collapsed first-level header (the header's own row is that total).
- **No query.** Collapsing is presentation only: it redraws from the cached result (like a format change).
  - While the table is still paging, or the result was cut at its group limit, a collapsed cell (and a collapsed row's or column's total) reads "—" rather than a partial sum.
  - Colour scales and data bars are measured on the values shown, collapsed sums included.
- **State** is `sheet.collapsed = { rows: [key…], cols: [key…] }` (absent until a header is collapsed). It is saved with the workbook and restored on load ([workbook.md](../workbook/workbook.md)).
  - A key names the dimensions down to the header plus its member path, so re-ordering the shelves never collapses other members. A key whose members no longer exist is ignored.
  - Import keeps only string keys (≤ 200 per axis, each ≤ 600 characters) and reports the rest.
  - A click first prunes keys that match no current header. At 200 collapsed headers a further collapse is refused with a toast and nothing changes.
  - Undo / redo cover it (the sheet snapshot). Client-side only: the server never sees it.

## Pages

The **Pages** tool takes one dimension (`sheet.pages`).

- **Page control** (`.ws-pages`) below the shelves: shows the current member and count, with previous / next stepping (wrapping).
- **Play / Pause** autoplays every 1.5s — **omitted under `prefers-reduced-motion`**. The autoplay timer is cleared on view switch.
- **Filtering:** each page applies the current member as a bound `=` filter, only when its table is already in the query.
- **Members** come from the bounded distinct-values query (shared with `in`), capped at 200 with the same "more exist" notice. A load failure shows the server's message.

## Date range & comparison

The **Date range** tool (calendar icon, P35) takes one date / date-time field (`sheet.period`); anything else is refused with a toast. Its panel (`periodEditor`) picks:

- **Range** — Last 7 / 28 / 30 / 90 days (ending today), This / Last month, quarter, year, or **Custom** (two day pickers). Whole days, inclusive, in the [app time zone](../../reference/time-zone.md)'s calendar.
- **Compare to** — No comparison, **Previous period** (the same number of days just before), **Same period last year** (29 Feb → 28 Feb) or **Custom**.

- **Default:** a new range is **Last 30 days vs previous period**.
- **Resolved days** show in the panel and the chart card's notice line ("1 Sept – 30 Sept 2026 vs 2 Aug – 31 Aug 2026"). An incomplete custom range says so and isn't applied.
- **Query:** the range is one bound `between` filter on the field (days for `Date`, `00:00:00`–`23:59:59` for `DateTime`). Like a filter, it may bring its table into the query.

### The comparison

The comparison is the same query over the comparison range. It is cached like any result; a failure toasts and the chart still draws. It shows on:

| View | Shows |
|---|---|
| **KPI** (no dimensions) — the scorecard | Under each value: ▲ / ▼ / ■ + signed % + "vs previous period", coloured `--up` / `--down` (good / bad) with an `aria-label`; the previous value in its tooltip. Format → **A fall is good** flips the tone. Format → **Target** (KPI) adds a progress bar and "78% of 40,000" under the first measure (✓ when met) |
| **Line / Area** | a dashed, faded line per measure, named "<measure> (previous period)" in the legend |
| **Bar** | a hatched, muted bar beside each bar, named in the legend |

- **Matching rows:** rows line up **by position** when the first group key is the range's own date field (day 1 with day 1). Otherwise they line up **by the same keys** (e.g. the same country).
- Other chart types apply the range only, and the panel says so.
- Rules: `Dashboard/period-model.js` (unit-tested).
