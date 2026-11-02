# Worksheet — shelves, crosstab, sort, format, joins

Each worksheet tab is one Tableau-style worksheet: a field pane beside shelves you drag fields onto, and a view that renders the result. A dashboard tab composes worksheets ([tabs.md](../workbook/tabs.md)).

- **Code:** `Features/Dashboard/` — `dashboards.js`, `worksheet-view.js`, `worksheet-render.js`, `render-*.js`, `sheet-plan.js`, `result-model.js`, `filter-rules.js`, `toolbar-rules.js`, `query-runner.js`, `chart.js`, `contrast.js`, `_Dashboard.cshtml`, `dashboard.css`, `QueryController.cs`.
- **Companion docs:** chart types and export → [worksheet-charts.md](worksheet-charts.md). Marks, Filters, Date range & comparison, click-to-filter, Drill and Pages → [worksheet-encodings.md](worksheet-encodings.md).
- **Sheet state shape:** [data-model.md](../../reference/data-model.md#worksheet-sheet).

## At a glance

- **What it is:** one Tableau-style worksheet per tab. Drag fields onto **Columns** / **Rows** (and Marks slots); the view is a chart or a crosstab.
- **One request:** the sheet becomes a single bounded `POST /api/query` (`buildPlan`), run latest-wins with a short-lived cache; limits are rejected, never clamped.

**Sections:** Layout · Shelves & pills · Calculated fields on the worksheet · Drop-time limits · Building the query · Query lifecycle · Cross-table joins · View data · Table view · Sort · Format

## Layout

Data sits on top; view controls sit on the chart ([design/layout.md](../../design/layout.md#worksheet--data-header-and-chart-card)).

1. **Data header** — the **Columns** and **Rows** shelves (full-width lanes, always visible) and the open Marks editor panel. The Marks slots themselves live in the field pane ([worksheet-encodings.md](worksheet-encodings.md#marks-slots)).
2. **Chart card** — flush (no margin, no radius). Its head is the **view bar**, left to right:
   - field-pane toggle;
   - the one chart-type control (`chartTypePicker`, [worksheet-charts.md](worksheet-charts.md#chart-type-control));
   - sort picker · Format · Export · Refresh · **Full screen** (icon buttons with tooltips and `aria-label`s).

   Below the view bar come the Format card, the result notice and the chart. Full screen and print: [layout.md](../../design/layout.md#full-screen--print).

### Worksheet chrome (P23)

- **Undo / Redo** — buttons beside the chart-type picker, plus `Ctrl/⌘+Z` and `Ctrl/⌘+Shift+Z` / `Ctrl+Y` (not while typing in a field). Every committed edit records the sheet as it was: 50 steps per worksheet, this session only. Pages autoplay doesn't record. Code: `Dashboard/history.js`.
- **Sheet actions** (⋯ in the view bar):
  - **Swap Rows and Columns**.
  - **Clear sheet…** — asks to confirm, keeps the chart type; Undo restores.
  - **Fit** — Standard (a slot per category, the pane scrolls), Fit width, Fit height, Entire view (the fitted axis shares the pane and its labels thin out).
  - **Show title and caption** / **Show filter cards**.
  - Fit and the two toggles carry only a tick at the end of the row (radio-style for Fit); no icon, no extra text.
- **Title and caption** under the view bar — click to edit, `Enter` saves, `Esc` cancels. Empty means the automatic one (the tab name; "sum amount by customers.name · 2 filters"). Printed too.
- **Status bar** at the foot of the chart card: marks · rows × columns (Table / Text) · measures · the selection · `Updated hh:mm:ss`. The time is when the data was last read from ClickHouse; a cached result keeps the time it was fetched (`fetchCached` stamps `queriedAt`).
- **Print header** (`beginPrint`): title, caption, date range, filters, the notice, the update time and the print time. It also lists each calculated field the view uses, and those it refers to, as `Calculation: Name = formula` (cut at 200 characters; `data-notes.js`).

### Field pane

Beside the data header and chart card, the **field pane** holds, top to bottom: **Marks** (soft `--surface-3` slots; accent wash when set or open), the search box, then **each model table that is in a relationship** (a table card with none is held out — [relationships.md](../data-source/relationships.md#rendering)).

- **Resize** by dragging its right edge, or `←`/`→` on the handle.
- **Hide / show** with the first button of the view bar; the worksheet takes the room. It sets `aria-expanded` and is remembered in `localStorage` as `dashboardbuilder.fields.collapsed`, like the sidebar rail.
- **Calculated fields** and **Hierarchies** are not in the pane. While a worksheet is open they are two icons in the sidebar body ([layout.md](../../design/layout.md#sidebar)), each opening a dialog to add, edit or use them (below).
- **Add a field** by dragging it onto a shelf or tool, pressing its **`＋`**, or double-clicking it. The `＋` is the keyboard path; both send measures to Rows and dimensions to Columns.

Style: the fields are the focus. Each table is a solid tile (`.ws-table`: `--line-2` stroke, `--elev-2`) on the quiet `--surface-2` pane. Its fields are flat 32px rows (hover wash, the add `+` on hover), with the type icon tinted by role (`--dim-ink` for dimensions, `--meas-ink` for measures), under sentence-case **Dimensions** / **Measures** labels. The groups share one collapsible design (`field-group.js`: `<details class="ws-group">`, chevron + bold name, 4px between rows, 8px between groups); collapsed groups survive a pane rebuild.

### Field pane basics (P28)

- **Search** at the top filters fields by column or display name; non-matches get `hidden`.
- **Context popup** on a field: right-click, the ContextMenu key, `Shift+F10`, or `Enter` on the focused row. The same keys open the popup on every pill and field row below (`Core/menu.js` `openContextMenu`). It offers:
  - **Rename…** — inline, 1–60 characters. This is a *display name* shown on the field, pills, axes, legends, table headers and the sort picker. The query always uses the real, catalog-validated column. Renamed fields read in italics.
  - **Default aggregation** (numeric fields) — the aggregation a new measure pill starts with.
  - **Hide from the field list**, with a **Show hidden (n)** toggle.
  - **Copy name** (T02-28) puts the display name on the clipboard; **Copy column name** puts the real column when renamed. A calculated field's popup also has **Copy formula** (not for a group).
- Settings are per workbook (`fields` in the file; store `fieldMeta`).

### Data type cast and member labels

The popup also has **Data type** (a query-time cast, `cast`: `text` | `number` | `date`) and **Edit member labels…** (display-only labels). Both are in [field-settings.md](field-settings.md).

## Shelves & pills

- **Columns** and **Rows** each hold **any number** of pills. The shelf sets the crosstab axis: Rows dimensions are the **left stub**, Columns dimensions the **top header**.
- **Reorder** by dragging a pill's grip (⠿) within a shelf or across to the other one. Dropping onto a pill inserts before it; dropping onto empty space appends. Dimension order sets nesting / category order; measure order sets series order.
- **Invariant: measures always sit behind dimensions** on a shelf. `normaliseShelf` re-sorts after every drop, role change or add, keeping relative order within each group.
- **Role** defaults from type (numeric → measure, else dimension) and can be changed per pill from its popup. `roleOf(f)` resolves it.
- **Invalid pills.** A pill whose settings can't be sent (a filter with an unparseable value, a column no longer in the catalog) is **invalid**. It shows a dashed `--danger-line` border, a warning icon and a tooltip with the reason. It is left out of the query, never silently altered.

### Pill options

Options are not inline. Right-click a pill (or focus it and press `Enter` / the ContextMenu key / `Shift+F10`) to open its **context popup**; `Esc` closes it and refocuses the pill. `Dashboard/pill-options.js` lists what each pill offers:

- a measure: aggregation radios, **Table calculation…** (opens its editor);
- a number: **Continuous** (measure) / **Discrete** (dimension) radios; any other flippable pill: **Use as dimension / measure**; and **Field choices…**;
- a date dimension: the date part radios with **Finer** / **Coarser**, and the **Show all date labels** tick;
- a filter: its operator radios, **Apply on every dashboard** and the value editor.

The pill itself shows only its name (a filter: name, operator and value), the cast tag, and Remove.

### Aggregation

A measure pill's aggregation radios offer only what the column's type supports (`aggsFor` in `filter-rules.js`):

| Column type | Aggregations |
|---|---|
| numbers | `sum/avg/min/max/median/percentile/stddev/variance/count/countDistinct/countNonNull/attr` |
| text **and dates** | `count/countDistinct/countNonNull/min/max/attr` |
| otherwise (boolean, compound) | `count/countDistinct/countNonNull` |

- `countDistinct` maps to ClickHouse `uniqExact`.
- Aggregation meanings (median interpolation, sample statistics): [api.md](../../reference/api.md#measure-values-and-aggregations).
- `attr` is the single value of a group, or empty ([calculated-fields.md](calculated-fields.md#formulas)).
- Changing a pill's role to a type that doesn't support its aggregation resets it and says so.

**Percentile** — numeric fields only. A text column cast to a number counts; uncast text is refused, as for `median`.

- Choosing `Percentile…` in the pill's popup adds a percent box inside the popup, labelled "Percentile for …, 0 to 100". It takes an integer or decimal with up to six decimals and starts at 90.
- The pill keeps the fraction as `p` (0..1; 99.5 is `0.995`) and is named `orders.amount · p90`.
- The measure is labelled `p90 amount` everywhere (chart, table, CSV, Top-N and sort choices; `p99.5 amount`).
- A value outside 0–100 shows "Percentile must be between 0 and 100 percent." (warning icon, `aria-invalid`). It is never stored or sent; the view keeps the last good percentile.
- Two percentiles of one field are separate measures. Leaving percentile drops `p`.
- Percentile is **not** in a field's default-aggregation menu. A calculated pill keeps its own list (use `PERCENTILE([f], p)`).

### Quick table calculations (P27)

A measure pill's **fx** button opens its editor.

- **Calculations:** **Running total, % of total, Difference, % difference, Rank** (competition style, highest first), **Percentile rank** (0–100%, highest = 100) or **Moving average** (window 2–30).
- **Along:** Columns, Rows (Auto = Columns when it has dimensions) or **Specific dimensions**:
  - a checkbox per Rows / Columns dimension; the ticked ones run together, the rest restart;
  - unticking all re-ticks all;
  - a same-named dimension is labelled with its shelf and date part;
  - the choice is positional, so reordering dimensions re-points it.
- **Computed in the browser** over the returned rows in sort order, restarting for each member of the other shelf's dimensions. No new query.
- **Display:** the measure is renamed ("sum amount · running total"). Percentages read "23.4%" in the table and charts.
- **Cut-off result:** the info line says "Table calculations use only the rows shown — more exist."
- Code: `Dashboard/table-calc.js`; saved on the pill as `tableCalc`.

### Date parts (P26)

A date dimension pill has a part picker:

- **Auto** — the chart-wide Format → Group dates. A new date pill stays on Auto (not Tableau's Year default, which would collapse a month of data to one point).
- **Exact**.
- **Year / Quarter / Month / Week / Day / Hour** — truncated, continuous.
- **Quarter of year / Month of year / Day of week / Hour of day** — discrete.

**−** / **+** step coarser / finer through year → quarter → month → day → hour. A `Date` column stops at day and offers no hour parts.

- Keys read as "2024", "2024 Q3", "Mar 2024", "Week of 2024-03-04", "Mon", "Q2", "09:00" (`Dashboard/date-parts.js`).
- A part-grouped axis isn't click-filterable.
- Saved on the pill (`datePart`); the server maps it to one whitelisted function.
- **Axis labels:** an **eye** toggle beside the picker picks **Thin out** (default: the date axis fits the pane and labels thin out) or **Show all** (a slot and label per date). Saved as `dateLabels`; `Dashboard/date-labels.js`.

### Field choices (P40)

A pill's **⇄** button opens a *Choices* editor. Drop up to 8 fields there (the shown one included).

- The chart card then shows a **"Columns: show" / "Rows: show"** switcher per such slot, under the view bar.
- Picking a field swaps it into the slot with the same role. A measure keeps its aggregation when the new field supports it, else takes the first one it does.
- Every choice is an ordinary field, validated by the server like any pill.
- Removing the shown choice shows the next. One choice left = an ordinary pill. The slot's only field shows no remove button.
- Saved on the pill (`choices`). The ⇄ turns accent-coloured when set.

## Calculated fields on the worksheet

A calculated field is a pill like any other; where it goes, where it is refused and its error state are in [calculated-fields.md](calculated-fields.md#what-a-calculated-pill-is).

It is not a column. `buildPlan` hands pills to the pure seam `Calc/calc-plan.js` (`wireDim`, `wireMeasure`, `topByRef` / `wireTopBy`, `planTables`), which emits the expanded `calc` tree in place of `db` / `table` / `column`. The tables a calculation reads join the query's table list like any field.

## Drop-time limits

Adding a field that would push a view over a cap is **refused with a toast naming the cap** — never silently dropped. Code: `checkAdd` in `filter-rules.js`; limits in `Core/validate.js` `LIMITS`.

| Cap | Limit |
|---|---|
| Fields per shelf (Columns, Rows, Detail, Tooltip) | 20 |
| Dimensions in one view (shelves + Detail + Shape + a categorical Colour + the drill level) | 12 |
| Measures in one view (shelf measures + numeric Size / Colour / Label / Path / Tooltip) | 10 |
| User filters | 8 |
| Drill levels | 6 |

- **The counts are conservative.** They ignore the chart type, so a stale encoding the current chart doesn't use still counts and can make a drop at the cap refuse. Remove it to free the slot.
- **The server enforces the same view caps** with 400s ([api.md](../../reference/api.md#limits)). It allows more filters than the 8 here because the worksheet appends its own ([limits](../../reference/api.md#limits)).

## Building the query

`buildPlan()` (`sheet-plan.js`) turns the sheet into one `POST /api/query` request. It is pure: it reads only the sheet and an explicit context.

- Rows dimensions → `rowDimensions[]`; Columns dimensions → `columnDimensions[]`; numeric pills → `measures[]`; plus filters and a `limit`.
- Only **valid** filters are sent (`checkFilter`). Each filter's `category` decides how the value is parsed; it is kept on the pill and back-filled from the column catalog for older workbooks.
- No measures → the server adds an implicit `count()`.
- The canonical dimension / measure ordering comes from `planDims` / `planMeasures`. The renderer re-derives it, so the two stay in lock-step.
- SQL shape: [clickhouse-integration.md](../../reference/clickhouse-integration.md#worksheet-query-queryasync).

## Query lifecycle

Every shelf, encoding or format change calls `commit()` → `worksheet:changed` → `runChart()`.

### The worksheet view

`runChart()` runs the editor's one worksheet view (`createWorksheetView` in `worksheet-view.js`, on `#ws-chart`).

- The view owns its gate, table pager and fresh flag. `chart.js` keeps one chart per container, with its own palette order and member colours.
- The view draws through `renderWorksheet` (`worksheet-render.js`). The editor only hands it its state as options: `interactive`, `onSelect`, `onDrill`, `onLegend`, `legendFocus`, the tooltip and member-colour panels' hooks, `statusBar`, `notices`.
- **Three modes of `interactive`:**
  - the editor's own view is fully interactive;
  - `interactive: false` (a static view) draws the same marks with no selection, drill or status line and a highlight-only legend — nothing is ever hidden;
  - `interactive: "select"` (the dashboard widget) keeps the marks selectable: a click calls `onSelect` and never drills. It has the same highlight-only legend, no status line and no editor panels. It also takes `cross()` (the dashboard selection, see [dashboards.md](../workbook/dashboards.md#cross-widget-filtering)) and `onUnselectable`.

### What happens next

Code: `Dashboard/query-runner.js`, unit-tested in `tests/js/`. Each fetch and draw is timed into the Performance dialog (`Core/perf-log.js`; render time = the synchronous draw only).

1. **Latest wins.** `runChart` takes a ticket from a gate. Starting a new query **aborts** the previous request, and the server stops it too ([clickhouse-integration.md](../../reference/clickhouse-integration.md#database-level-guards)). Any answer that arrives for a superseded ticket is dropped, so a slow old result can never overwrite a newer chart. Leaving for the Data Source cancels the in-flight query.
2. **Cache before query.** The request (endpoint + full plan) is the cache key. The last **16** results per worksheet are kept. Presentation-only changes (legend, decimals, axis titles, data labels, colour-by-category) and paging back through the Pages shelf therefore re-render instantly with **no** ClickHouse query. Anything that changes the plan (fields, filters, sort, Top-N, chart family) queries.
3. **Refresh and Cancel.**
   - **Refresh** (icon button on the view bar) drops the worksheet's cache and re-queries with `fresh`, so the server's 60-second result cache is bypassed too ([D25](../../reference/decisions/decisions.md#d25--a-short-lived-server-result-cache-and-approximate-mode)). Use it when the data in ClickHouse has changed.
   - A result from the server cache says so on the info line.
   - While a query runs, **Loading…** carries a **Cancel** button. It aborts the request (the server stops the ClickHouse query) and leaves "Query cancelled — Refresh runs it again."
4. **Truncation notice.** Top-N **All** (the default) asks for up to **5000** groups ([D24](../../reference/decisions/decisions.md#d24--showing-all-data-bounded-requests-paging-other-date-grouping)), so below that, sorting only reorders.
   - If the server reports `truncated` (more groups than the limit) and no **Other** mark shows it, an info line at the top of the chart card says: "Showing the first 50 in sort order — more exist. Raise Top-N in Format, or add a filter."
   - At the 5000 cap it drops the Top-N hint ("…Add a filter to narrow it.").
   - The Table view shows its own progress instead (below).
   - Box plots get the same notice, plus "Showing the first 500 outliers — more exist." when outlier points were capped.
   - A date-grouped axis adds "Dates grouped by month — set Group dates in Format to change."
   - Code: the line is `#ws-chart-notice`, a sibling of `#ws-chart`, so re-renders never wipe it.
5. **Errors** show in the chart pane. A render error is caught and shown there too, never a blank view. The server's `{ error }` sentence is shown as-is. A query stopped by the server's time limit says so ("ran longer than 12 seconds … add a filter, lower Top-N, or use fewer fields").

## Cross-table joins

Fields may come from **different tables**. The client finds a **join path** — a breadth-first search (BFS) over the drawn relationship graph — and the server builds aliased joins along it, each of its relationship's join type ([relationships.md](../data-source/relationships.md)).

- Tables with no connecting relationship → a "draw a relationship" warning, never a malformed query.
- A union or unpivot card is read alone ([query-sources.md](../data-source/query-sources.md)).

## View data

View data shows the rows **behind** a view. Two entry points open the rows dialog ([schema-browser.md § Row preview](../data-source/schema-browser.md#row-preview)):

- the Export menu's **View data** — the whole view;
- the selection bar's **View data** (`ws-select`, beside Keep only / Exclude) — the selected mark.

It shows the first **100** rows (server cap 1000) of the view's **base table** — the first table the view uses — from `POST /api/rows` ([api.md § Rows](../../reference/api.md#rows)).

How the request is built: `viewData` in `dashboards.js` builds the usual plan with the selection removed, then `buildRowsRequest` (`Rows/rows-model.js`) turns it into the request.

- **Sent:** the view's filters that sit **on the base table** (user and shared filters, drill path, page, date range), already resolved (relative dates → a bound `between`, parameter values applied).
- **Selected mark:** added as a bound `=` on its column, whatever Keep only / Exclude is set to.
- **Left out, and named** in an amber note in the dialog (never silently): whatever a single-table read **cannot** apply — filters on **joined** tables, a mark on a joined table, a **NULL** mark, and Top-N rankings. So for a joined view the rows are the base table's, not the joined result. This is a decision: rows are of one table, never a join.
- **Dialog:** the title is "Data behind this view" or "Data behind <table.column = value>". The dialog, its truncation notice ("First N rows — more exist") and its CSV export are the schema browser's.
- **Empty or broken views:** a view with no fields yet says "Add fields before viewing data."; an invalid calculation shows its problem instead.

## Table view — a true Rows × Columns crosstab

`crosstabTable()` (`render-table.js`) pivots the flat grouped rows in the browser (ClickHouse has no `PIVOT`).

- **Layout:** Row-shelf dimensions form the nested **left stub** (rowSpan-merged repeats). Column-shelf dimensions form the nested **top header** (colSpan). Measures are the **cell values**.
- **Measure-name band:** it sits on whichever shelf holds the measures. On Columns it runs across the top; on Rows down the left, transposing the grid. Measures on both → a note, falling back to the top band.
- **Colour:** a Colour dimension adds a free extra top-header level.

### Conditional formatting (P37)

Format → Conditional formatting, in the Table and Text views. Set per measure, keyed by column + aggregation, so it survives shelf reorders.

- **Cells:**
  - **None**;
  - **Colour scale** — Low → high (surface → `--chart-cat-1`), or **Diverging** (`--chart-cat-6` ← surface → `--chart-cat-1`) around a **Midpoint**. Auto midpoint = 0 when values straddle it, else the middle;
  - **Data bars** — from zero; negatives extend left in `--chart-cat-6`.
- **Rules:** up to **5** rules "value op threshold → Good / Bad / Warning / Note". The first match wins and overrides the scale or bar for that cell. Rules wear the status tokens **and an icon** (✓ / error / warning / info).
- **Contrast:** scale tints top out at 85%, and each cell's ink is picked for ≥ 4.5:1 (`contrast.js`).
- **Key:** above the table, showing each scale's low / high (and centre) and each rule. While pages are still loading it says "Scales and bars use the N rows loaded so far."
- Code: rules in `Dashboard/conditional-model.js` (unit-tested).

### Paging

Every row is shown, a page at a time.

- The table asks for 500 rows plus the total (`withTotal`). When the pane scrolls within 400px of its end, the next 500 load (`offset`), and the crosstab redraws from all loaded rows.
- The notice line reads "Rows 1–500 of 12,345 — scroll to load more", then "12,345 rows".
- Loaded pages are kept while only presentation changes. Refresh or any plan change starts over.
- Code: `runTable` in `worksheet-view.js`; rules in `scale-model.js`.

## Sort

The view bar's **sort picker** (`sortControl`) shows the current order (`↑ customers.name`).

- Its menu lists the in-play fields ("Sort by") and **Ascending / Descending**.
- Default: ascending by the first field (`sortSummary` in `viewbar-model.js`).
- With nothing on the shelves it is disabled.
- It sets the query `ORDER BY` on the field's generated alias (`k{n}` / `v{n}`). The server then appends the remaining dimension keys ascending, so the crosstab layout stays stable.

## Format

A collapsible **Format** card (`formatPanel`, state on `sheet.format`) changes presentation without touching the query — except Top-N.

| Setting | Effect |
|---|---|
| Number format | auto / compact / currency / percent + decimals (0–3 in the UI; a workbook may carry up to 10) |
| Date format | for date-like dimension labels |
| Top-N | Caps the chart query's `LIMIT`: All, 5, 10, 20, 50, 100, or **= a number parameter** (P32, clamped to 1–5000). **All** (the default) asks for up to 5000 groups. A set value keeps that many in sort order, so ascending and descending show different groups when there are more. A one-dimension bar / pie / donut / treemap then adds an **Other (N more)** mark (muted ink, not clickable) aggregating the rest. Also sets the histogram bin count |
| Target | KPI: a goal for the first measure — progress bar + "% of target" ([worksheet-encodings.md](worksheet-encodings.md#date-range--comparison)). Gauge: the arc's maximum. Bullet: the target tick and bands ([worksheet-charts.md](worksheet-charts.md#chart-types)) |
| A fall is good | with a Date range comparison: a fall shows as good (`--up`), a rise as bad |
| Conditional formatting | Table / Text: colour scale, data bars and rules per measure ([Table view](#table-view--a-true-rows--columns-crosstab)) |
| Approximate (faster) | `uniq` distinct counts and, on a table with a sampling key, a 10% sample ([exact vs sampled](../../reference/clickhouse-calculations.md#aggregates-exact-and-approximate)); median, percentile, standard deviation, variance and ATTR are estimates, and the info line says so. Labelled on the info line ([D25](../../reference/decisions/decisions.md#d25--a-short-lived-server-result-cache-and-approximate-mode)) |
| Fit | Standard / Fit width / Fit height / Entire view (also in the ⋯ sheet actions) |
| Group dates | Charts: group the first date/time dimension by Auto (default — exact when ≤ 400 values, else the finest grain with ≤ 400 buckets), Exact, Hour, Day, Week, Month, Quarter or Year. A grouped axis isn't click-filterable |
| Legend | show / position |
| Data labels | on / off |
| Colour-by-category | single-measure bar: colour each bar by its category |
| X / Y axis titles | name the **physical** axes (X = bottom, Y = left); ≤ 80 characters |

Number and date formats also drive the crosstab and KPI tiles through the shared `Core/format.js` (`makeValueFormatter` / `makeCategoryFormatter`), so every view reads identically.
