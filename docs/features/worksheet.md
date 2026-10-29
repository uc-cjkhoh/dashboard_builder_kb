# Worksheet — shelves, crosstab, sort, format, joins

Each worksheet tab (a dashboard tab composes worksheets — [tabs.md](tabs.md)) is one Tableau-style worksheet: a field pane beside shelves you drag fields onto,
and a view that renders the result. Code: `Features/Dashboard/` (`dashboards.js`, `worksheet-view.js`, `worksheet-render.js`, `render-*.js`, `sheet-plan.js`, `result-model.js`, `filter-rules.js`,
`toolbar-rules.js`, `query-runner.js`, `chart.js`, `contrast.js`, `_Dashboard.cshtml`, `dashboard.css`,
`QueryController.cs`). Companion docs: chart types and export in
[worksheet-charts.md](worksheet-charts.md); Marks, Filters, Date range & comparison, click-to-filter, Drill and Pages in
[worksheet-encodings.md](worksheet-encodings.md). Sheet state shape:
[data-model.md](../reference/data-model.md#worksheet-sheet).

## Layout

Data on top, view controls on the chart ([design/layout.md](../design/layout.md#worksheet--data-header-and-chart-card)):

1. **Data header** — **Columns** and **Rows** shelves (full-width lanes, always visible), then the
   **Marks** lane: a visible row of encodings plus a **More** menu — Color, Size, Label, Detail,
   Tooltip, Shape, Path, Angle, Filters, Drill, Pages ([worksheet-encodings.md](worksheet-encodings.md#encodings-toolbar)).
2. **Chart card** — its head is the **view bar**: chart-type picker (`chartTypePicker`) · sort picker ·
   Format · Export · Refresh · **Full screen** (icon buttons with tooltips and `aria-label`s); then the
   Format card, the result notice and the chart. Full screen, print and the phone layout:
   [layout.md](../design/layout.md#phone-layout--640px).

**Worksheet chrome** (P23):

- **Undo / Redo** — buttons beside the chart-type picker and `Ctrl/⌘+Z`, `Ctrl/⌘+Shift+Z` / `Ctrl+Y`
  (not while typing in a field). Every committed edit records the sheet as it was (50 steps per
  worksheet, this session only); Pages autoplay doesn't record (`Dashboard/history.js`).
- **Sheet actions** (⋯ in the view bar): **Swap Rows and Columns**, **Clear sheet…** (confirm; keeps the
  chart type; Undo restores), **Fit** — Standard (a slot per category, the pane scrolls), Fit width, Fit
  height, Entire view (the fitted axis shares the pane; its labels thin out) — and **Show title and
  caption**.
- **Title and caption** under the view bar: click to edit, `Enter` saves, `Esc` cancels; empty = the
  automatic one (the tab name; "sum amount by customers.name · 2 filters", in italics). Printed too.
- **Status bar** at the foot of the chart card: marks · rows × columns (Table / Text) · measures · the
  selection · `Updated hh:mm:ss`, when the data was last read from ClickHouse (a cached result keeps the time it
  was fetched; `fetchCached` stamps `queriedAt`).
- **Print header** (`beginPrint`): title, caption, date range, filters, the notice, then each calculated field
  the view uses as `Calculation: Name = formula` (also those it refers to; formulas cut at 200 characters,
  `data-notes.js`), the update time and the print time.

Beside them, the **field pane** (drag its right edge, or `←`/`→` on the handle, to resize it) lists each model table as a collapsible group (`<details>`, open by
default) with small **Dimensions** / **Measures** labels inside; each field shows a type icon (text,
number, date, bool) rather than a coloured letter.

**Field pane basics** (P28): a **search** box at the top filters fields by column or display name
(non-matches get `hidden`); each field's **⋯** menu offers **Rename…** (inline, 1–60 characters — a
*display name* shown on the field, pills, axes, legends, table headers and the sort picker; the query always
uses the real, catalog-validated column; renamed fields read in italics), **Default aggregation** (numeric
fields: the aggregation a new measure pill starts with) and **Hide from the field list** (with a **Show
hidden (n)** toggle). Settings are per workbook (`fields` in the file; store `fieldMeta`).

**Data type cast** (T02-34): the ⋯ menu also has **Data type** — *Original*, or the casts that make sense
for the column: text → Number / Date, number or date → Text, boolean → Text / Number, anything else → Text
(`castChoices`; the setting is `cast`: `text` | `number` | `date`). The server converts in the query, so the
field groups, aggregates, filters and ranks (Top-N) as its new type; a value that doesn't fit becomes empty
(NULL), never an error. The field takes the new category everywhere: it moves to Dimensions / Measures, offers
that type's aggregations, operators and date parts, and shows an **as Number** tag (icon + text) on its chip
and pills. Changing a cast re-categorises the pills, filters, drill levels and shared filters that read the field
(`syncCastCategories`). Calculated fields have their own type and take no cast. Histogram and box plot don't
support a cast field yet (a hint, no request); the filter value picker still lists the stored text.
View data leaves out filters and a selected mark on a cast field (it reads stored values) and says so.
A value that fails to convert is NULL, so filters on it drop it (`notin` keeps it). Code: `Dashboard/cast-model.js`, `ClickHouse/TypeCast.cs`.

**Member labels** (T02-29): **Edit member labels…** (not offered on date fields) opens a dialog listing the field's
top members (the bounded distinct-values read, first 200) with one label input each (≤ 80 characters; blank or
equal to the value = no label; labels are **unique within a field** — one equal to another member's label or raw value is refused naming that member (a file with such labels opens with the first kept and the rest dropped and reported); a value over 100 characters can't be labelled; **Reset all**; Enter moves down the list, Esc discards). The map is the field setting
`memberAliases` (`{ [rawValue]: label }`, ≤ 200 entries, key ≤ 100 characters; `Dashboard/member-labels.js`). It is
**display only**: queries, grouping, sorting, filters, drill and selections keep the raw value. A label replaces the
text drawn for a member on category axes, pie slices and legends, colour-split series, heatmap / treemap / Sankey /
small-multiples labels, tooltips (default head, the template's `<table.column>` field and Tooltip fields, all still
HTML-escaped), crosstab headers and the Label mark, each **by key position** (`withMemberLabels`: two fields may label
the same raw value differently). A filter card / `in` picker shows the label with the raw value as secondary text and
title, and ticking a member stores the raw value. A click-selection chip, the legend selection chip, the drill
breadcrumb and the dashboard filter chip name the member by its label when it is picked (the stored label text does
not follow a later edit). Member colours stay keyed by the raw member. Maps are null-prototype objects read with own-key
checks, so a member called `constructor` or `__proto__` is an ordinary member. CSV export and View data carry raw values (and group names), never labels. Not labelled: calculated or group
dimensions, date-part keys, bucketed numeric keys, NULL, Pages.

Drag a field onto a shelf or tool, or press its **`＋`** (keyboard path: measures go to Rows, dimensions
to Columns).

## Shelves & pills

- **Columns** and **Rows** each hold **any number** of pills. The shelf sets the crosstab axis: Rows
  dimensions are the **left stub**, Columns dimensions the **top header**.
- **Quick table calculations** (P27): a measure pill's **fx** button opens its editor — **Running total,
  % of total, Difference, % difference, Rank** (competition style, highest first) or **Moving average**
  (window 2–30) — **Along** Columns or Rows (Auto = Columns when it has dimensions). Computed in the
  browser over the returned rows in sort order, restarting for each member of the other shelf's
  dimensions; no new query. The measure is renamed ("sum amount · running total"); percentages read "23.4%"
  in the table and charts. Over a cut-off result the info line says "Table calculations use only the rows
  shown — more exist." (`Dashboard/table-calc.js`; saved on the pill as `tableCalc`).
- **Date parts** (P26): a date dimension pill has a part picker — **Auto** (the chart-wide Format →
  Group dates), **Exact**, **Year / Quarter / Month / Week / Day / Hour** (truncated, continuous), or
  **Quarter of year / Month of year / Day of week / Hour of day** (discrete) — with **−** / **+** stepping
  coarser / finer through year → quarter → month → day → hour (a `Date` column stops at day and offers
  no hour parts). Keys read as "2024", "2024 Q3", "Mar 2024", "Week of 2024-03-04", "Mon", "Q2", "09:00"
  (`Dashboard/date-parts.js`). A part-grouped axis isn't click-filterable. A new date pill stays on
  **Auto** (not Tableau's Year default, which would collapse a month of data to one point). Saved on the
  pill (`datePart`); the server maps it to one whitelisted function.
- **Field choices** (P40): a pill's **⇄** button opens a *Choices* editor — drop up to 8 fields there
  (the shown one included). The chart card then shows a **"Columns: show" / "Rows: show"** switcher per
  such slot, under the view bar; picking a field swaps it into the slot (same role; a measure keeps its
  aggregation when the new field supports it, else takes the first it does). Every choice is an
  ordinary field, validated by the server like any pill. Removing the shown choice shows the next; one
  choice left = an ordinary pill. Saved on the pill (`choices`). The ⇄ turns accent-coloured when set.
- **Reorder** by dragging a pill's grip (⠿) within a shelf or across to the other one; dropping onto a
  pill inserts before it, onto empty space appends. Dimension order sets nesting/category order;
  measure order sets series order.
- **Invariant: measures always sit behind dimensions** on a shelf — `normaliseShelf` re-sorts after
  every drop, role change or add, keeping relative order within each group.
- **Role** defaults from type (numeric → measure, else dimension) and is convertible per pill: `Σ`
  turns a dimension into a measure, `#` a measure into a dimension. `roleOf(f)` resolves it.
- **Aggregation** dropdown on measure pills offers only what the column's type supports
  (`aggsFor` in `filter-rules.js`): `sum/avg/min/max/median/percentile/stddev/variance/count/countDistinct/countNonNull/attr`
  for numbers; `count/countDistinct/countNonNull/min/max/attr` for text **and dates**;
  `count/countDistinct/countNonNull` otherwise (boolean, compound). `countDistinct` maps to ClickHouse `uniqExact`;
  `median` interpolates between the two middle values (like Excel `PERCENTILE.INC`), `stddev` / `variance` the sample statistics (empty for one value), `attr`
  the single value of a group or empty ([calculated-fields.md](calculated-fields.md#formulas)).
  **Percentile** (numeric fields only; a text column cast to a number counts, uncast text is refused as for `median`): choosing
  `Percentile…` in the pill's menu adds a percent box (labelled "Percentile for …, 0 to 100"; an integer or decimal with up to six
  decimals, starts at 90). The pill keeps the fraction as `p` (0..1; 99.5 is `0.995`), is named `orders.amount · p90`, and the measure
  is labelled `p90 amount` everywhere (chart, table, CSV, Top-N and sort choices; `p99.5 amount`). A value outside 0–100 shows the
  message ("Percentile must be between 0 and 100 percent.", warning icon, `aria-invalid`) and is never stored or sent: the view keeps
  the last good percentile. Two percentiles of one field (p25 and p75) are separate measures. Leaving percentile drops `p`.
  Percentile is **not** in a field's default-aggregation menu (a default would need a default fraction). A calculated pill keeps
  its own list (use `PERCENTILE([f], p)` in the formula). Changing a pill's role to a type that
  doesn't support its aggregation resets it and says so. The server rejects `sum` / `avg` on a
  non-numeric column with a 400.
- Pill tints: dimension blue (`--dim-*`), measure teal (`--meas-*`), Marks encodings violet (`--enc-*`).
  A pill whose settings can't be sent (a filter with an unparseable value, a column that is no longer
  in the catalog) is **invalid**: dashed `--danger-line` border, warning icon and a tooltip with the
  reason — and it is left out of the query, never silently altered.

## Calculated fields on the worksheet

A calculated field ([calculated-fields.md](calculated-fields.md)) is a pill like any other on Rows, Columns,
Color and the Size / Label / Path / Detail / Tooltip slots, and can rank a Top-N filter or be the sort target
(a stored sort follows the pill when its aggregation changes). It is not a column: `buildPlan` hands pills to
the pure seam `Calc/calc-plan.js` (`wireDim`, `wireMeasure`, `topByRef` / `wireTopBy`, `planTables`), which
emits the expanded `calc` tree in place of `db` / `table` / `column`; the tables a calculation reads join the
query's table list like any field. A calculated pill shows its live name and no field-choice switch.

- A calculation that can't be computed sends no query: the chart slot (and CSV export) shows
  `Calculation 'X' can't be computed: …` (`calcProblem`).
- A sheet whose only pills are field-less calculations (`1+2`) shows the hint "Add a field from a table — a
  calculation with no field in it has nothing to group or total."
- A measure named for a calculation uses its name; a plain non-null count reads `non-null <name>`.
- Click-to-filter is off while the primary dimension is a calculation; filters, Pages, drill, the date range,
  shared filters, selection, Shape and Angle refuse a calculated pill.

## Drop-time limits

Adding a field that would push a view over a cap is **refused with a toast naming the cap** — never
silently dropped (`checkAdd` in `filter-rules.js`; limits in `Core/validate.js` `LIMITS`):

| Cap | Limit |
|---|---|
| Fields per shelf (Columns, Rows, Detail, Tooltip) | 20 |
| Dimensions in one view (shelves + Detail + Shape + a categorical Colour + the drill level) | 12 |
| Measures in one view (shelf measures + numeric Size / Colour / Label / Path / Tooltip) | 10 |
| User filters | 8 |
| Drill levels | 6 |

The dimension and measure counts are conservative: they ignore the chart type, so a stale encoding the
current chart doesn't use still counts and can make a drop at the cap refuse (remove it to free the
slot). The server enforces the same view caps with 400s
([api.md](../reference/api.md#limits)); it allows more filters (20) because the worksheet appends the
shared filters (≤ 4), the drill path (≤ 5), the page, the selection and the date range to the user's 8.

## Building the query

`buildPlan()` (`sheet-plan.js`, pure: it reads only the sheet and an explicit context) turns the sheet into one `POST /api/query` request: Rows dimensions → `rowDimensions[]`,
Columns dimensions → `columnDimensions[]`, numeric pills → `measures[]`, plus filters and a `limit`.
Only **valid** filters are sent (`checkFilter`); each filter's `category` (kept on the pill, back-filled
from the column catalog for older workbooks) decides how the value is parsed. No
measures → the server adds an implicit `count()`. The canonical dimension/measure ordering comes from
`planDims` / `planMeasures`, which the renderer re-derives so the two stay in lock-step. SQL shape:
[clickhouse-integration.md](../reference/clickhouse-integration.md#worksheet-query-queryasync).

## Query lifecycle

Every shelf, encoding or format change calls `commit()` → `worksheet:changed` → `runChart()`, which runs the
editor's one worksheet view (`createWorksheetView` in `worksheet-view.js`, on `#ws-chart`; the view owns its
gate, table pager and fresh flag, and `chart.js` keeps one chart per container, with its own palette order and
member colours). The view draws through `renderWorksheet` (`worksheet-render.js`); the editor only hands it
its state as options — `interactive`, `onSelect`, `onDrill`, `onLegend`, `legendFocus`, the tooltip and
member-colour panels' hooks, `statusBar`, `notices` — so a view with `interactive: false` draws the same marks
with no selection, drill or status line and a highlight-only legend (nothing is ever hidden) (a static view). `interactive: "select"` (the dashboard widget) keeps the marks selectable — a click calls `onSelect` and never drills — with the same highlight-only legend, no status line and no editor panels; it also takes `cross()` (the dashboard selection, see [dashboards.md](dashboards.md#cross-widget-filtering)) and `onUnselectable`. The editor's own view is fully interactive.
What happens next
(`Dashboard/query-runner.js`, unit-tested in `tests/js/`):

1. **Latest wins.** `runChart` takes a ticket from a gate; starting a new query **aborts** the previous
   request (the server stops it too — [clickhouse-integration.md](../reference/clickhouse-integration.md#database-level-guards))
   and any answer that arrives for a superseded ticket is dropped, so a slow old result can never
   overwrite a newer chart. Leaving for the Data Model cancels the in-flight query.
2. **Cache before query.** The request (endpoint + full plan) is the cache key. The last **16** results
   per worksheet are kept, so presentation-only changes (legend, decimals, axis titles, data labels,
   colour-by-category) and paging back through the Pages shelf re-render instantly with **no** ClickHouse
   query. Anything that changes the plan (fields, filters, sort, Top-N, chart family) queries.
3. **Refresh** (icon button) on the view bar drops the worksheet's cache and re-queries with `fresh`, so
   the server's 60-second result cache is bypassed too ([D25](../reference/decisions.md#d25--a-short-lived-server-result-cache-and-approximate-mode)) —
   use it when the data in ClickHouse has changed. A result from the server cache says so on the info line.
   While a query runs, **Loading…** carries a **Cancel** button: it aborts the request (the server stops the
   ClickHouse query) and leaves "Query cancelled — Refresh runs it again."
4. **Truncation notice.** Top-N **All** (the default) asks for up to **5000** groups
   ([D24](../reference/decisions.md#d24--showing-all-data-bounded-requests-paging-other-date-grouping)), so below that sorting only reorders. If the
   server reports `truncated` (more groups than the limit) and no **Other** mark shows it, an info line at
   the top of the chart card (`#ws-chart-notice`, a sibling of `#ws-chart` so re-renders never wipe it) says so: "Showing the first 50 in sort order — more
   exist. Raise Top-N in Format, or add a filter." At the 5000 cap it drops the Top-N hint ("…Add a filter
   to narrow it."); the Table view shows its own progress instead (below). Box plots get the same notice. A date-grouped
   axis adds "Dates grouped by month — set Group dates in Format to change."
5. **Errors** show in the chart pane — a render error is caught and shown there too, never a blank
   view. The server's `{ error }` sentence is shown as-is. A query stopped by the server's time limit says so ("ran longer
   than 12 seconds … add a filter, lower Top-N, or use fewer fields").

## Cross-table joins

Fields may come from **different tables**. The client finds a **join path** (BFS over the drawn
relationship graph) and the server builds aliased `INNER JOIN`s along it. Tables with no connecting
relationship → a "draw a relationship" warning, never a malformed query.

## View data

The rows **behind** a view: the Export menu's **View data** (whole view) and the selection bar's **View data**
(`ws-select`, beside Keep only / Exclude: the selected mark) open the rows dialog
([schema-browser.md § Row preview](schema-browser.md#row-preview)) with the first **100** rows (server cap 1000) of the
view's **base table** — the first table the view uses — from `POST /api/rows`
([api.md § Rows](../reference/api.md#rows)). `viewData` in `dashboards.js` builds the usual plan with the selection
removed, then `buildRowsRequest` (`Rows/rows-model.js`) turns it into the request:

- the view's filters that sit **on the base table** (user and shared filters, drill path, page, date range) are sent,
  already resolved (relative dates → a bound `between`, parameter values applied);
- the **selected mark** is added as a bound `=` on its column — whatever Keep only / Exclude is set to;
- what a single-table read **cannot** apply is left out and named in an amber note in the dialog, never silently:
  filters on **joined** tables, a mark on a joined table, a **NULL** mark, and Top-N rankings. So for a joined view
  the rows are the base table's, not the joined result (a decision: rows are of one table, never a join).
- The dialog title is "Data behind this view" or "Data behind <table.column = value>"; the dialog, its truncation
  notice ("First N rows — more exist") and its CSV export are the schema browser's. A view with no fields yet says
  "Add fields before viewing data."; an invalid calculation shows its problem instead.

## Table view — a true Rows × Columns crosstab

`crosstabTable()` (`render-table.js`) pivots the flat grouped rows client-side (ClickHouse has no `PIVOT`):

- Row-shelf dimensions form the nested **left stub** (rowSpan-merged repeats); Column-shelf dimensions
  the nested **top header** (colSpan); measures are the **cell values**.
- The **measure-name band sits on whichever shelf holds the measures** — on Columns it runs across the
  top, on Rows down the left (transposing the grid). Measures on both → a note, falling back to the top
  band.
- A Colour dimension adds a free extra top-header level.
- **Conditional formatting** (P37, Format → Conditional formatting, Table and Text views). Per measure
  (keyed by column + aggregation, so it survives shelf reorders): **Cells** = None, **Colour scale**
  (Low → high: surface → `--chart-cat-1`; or **Diverging**: `--chart-cat-6` ← surface → `--chart-cat-1`
  around a **Midpoint** — auto = 0 when values straddle it, else the middle) or **Data bars** (from zero;
  negatives extend left in `--chart-cat-6`); plus up to **5 rules** "value op threshold → Good / Bad /
  Warning / Note", first match wins and overrides the scale or bar for that cell. Rules wear the status
  tokens **and an icon** (✓ / error / warning / info); scale tints top out at 85% and each cell's ink is
  picked for ≥ 4.5:1 (`contrast.js`). A key above the table shows each scale's low / high (and centre) and
  each rule; while pages are still loading it says "Scales and bars use the N rows loaded so far."
  Rules: `Dashboard/conditional-model.js` (unit-tested).
- **Every row, a page at a time.** The table asks for 500 rows plus the total (`withTotal`); as the pane
  scrolls within 400px of its end the next 500 load (`offset`), and the crosstab redraws from all loaded
  rows. The notice line reads "Rows 1–500 of 12,345 — scroll to load more", then "12,345 rows". Loaded
  pages are kept while only presentation changes; Refresh or any plan change starts over
  (`runTable` in `worksheet-view.js`; rules in `scale-model.js`).

## Sort

The view bar's **sort picker** (`sortControl`) shows the current order (`↑ customers.name`); its menu
lists the in-play fields ("Sort by") and **Ascending / Descending** — default ascending by the first
field (`sortSummary` in `viewbar-model.js`). With nothing on the shelves it is disabled. It sets the query `ORDER BY` on the field's generated alias
(`k{n}` / `v{n}`); the server then appends the remaining dimension keys ascending so the crosstab
layout stays stable.

## Format

A collapsible **Format** card (`formatPanel`, state on `sheet.format`) changes presentation without
touching the query, except Top-N:

| Setting | Effect |
|---|---|
| Number format | auto / compact / currency / percent + decimals (0–3 in the UI; a workbook may carry up to 10) |
| Date format | for date-like dimension labels |
| Top-N | caps the chart query's `LIMIT` (All, 5, 10, 20, 50, 100, or **= a number parameter** — P32, clamped to 1–5000). **All** (the default) asks for up to 5000 groups; a set value keeps that many in sort order, so ascending and descending then show different groups when there are more — a one-dimension bar / pie / donut / treemap adds an **Other (N more)** mark (muted ink, not clickable) aggregating the rest. The server rejects a limit outside 1..5000. Also the histogram bin count |
| Target | KPI: a goal for the first measure — progress bar + "% of target" ([worksheet-encodings.md](worksheet-encodings.md#date-range--comparison)); Gauge: the arc's maximum; Bullet: the target tick and bands ([worksheet-charts.md](worksheet-charts.md#chart-types)) |
| A fall is good | with a Date range comparison: a fall shows as good (`--up`), a rise as bad |
| Conditional formatting | Table / Text: colour scale, data bars and rules per measure ([Table view](#table-view--a-true-rows--columns-crosstab)) |
| Approximate (faster) | `uniq` distinct counts and, on a table with a sampling key, a 10% sample scaled up (counts and sums only; median, percentile, standard deviation, variance and ATTR are computed on the sample and not scaled, so they are estimates; the info line says so when such a measure is shown) — labelled on the info line ([D25](../reference/decisions.md#d25--a-short-lived-server-result-cache-and-approximate-mode)) |
| Fit | Standard / Fit width / Fit height / Entire view (also in the ⋯ sheet actions) |
| Group dates | charts: group the first date/time dimension by Auto (default — exact when ≤ 400 values, else the finest grain with ≤ 400 buckets), Exact, Hour, Day, Week, Month, Quarter or Year. A grouped axis isn't click-filterable |
| Legend | show / position |
| Data labels | on / off |
| Colour-by-category | single-measure bar: colour each bar by its category |
| X / Y axis titles | name the **physical** axes (X = bottom, Y = left); ≤ 80 characters |

Number and date formats also drive the crosstab and KPI tiles through the shared
`Core/format.js` (`makeValueFormatter` / `makeCategoryFormatter`), so every view reads identically.
