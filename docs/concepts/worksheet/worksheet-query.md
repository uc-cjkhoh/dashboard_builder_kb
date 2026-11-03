---
components: [src/DashboardBuilder/Features/Core/perf-log.js, src/DashboardBuilder/Features/Dashboard/chart.js, src/DashboardBuilder/Features/Dashboard/dashboards.js, src/DashboardBuilder/Features/Dashboard/query-runner.js, src/DashboardBuilder/Features/Dashboard/sheet-plan.js, src/DashboardBuilder/Features/Dashboard/worksheet-render.js, src/DashboardBuilder/Features/Dashboard/worksheet-view.js, src/DashboardBuilder/Features/Rows/rows-model.js, tests/js/]
---
# Worksheet query — plan, lifecycle, joins

How a worksheet becomes one bounded query and how the result comes back. Layout and shelves: [worksheet.md](worksheet.md).

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
   - **Refresh** (icon button on the view bar) drops the worksheet's cache and re-queries with `fresh`, so the server's 60-second result cache is bypassed too ([D25](../../decisions/decisions-platform.md#d25--a-short-lived-server-result-cache-and-approximate-mode)). Use it when the data in ClickHouse has changed.
   - A result from the server cache says so under the list in the "How this is computed" popover (not on the info line).
   - While a query runs, **Loading…** carries a **Cancel** button. It aborts the request (the server stops the ClickHouse query) and leaves "Query cancelled — Refresh runs it again."
4. **Truncation notice.** Top-N **All** (the default) asks for up to **5000** groups ([D24](../../decisions/decisions-platform.md#d24--showing-all-data-bounded-requests-paging-other-date-grouping)), so below that, sorting only reorders.
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
