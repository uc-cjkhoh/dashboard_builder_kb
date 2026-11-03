---
components: [src/DashboardBuilder/Features/Core/format.js, src/DashboardBuilder/Features/Dashboard/conditional-model.js, src/DashboardBuilder/Features/Dashboard/contrast.js, src/DashboardBuilder/Features/Dashboard/render-table.js, src/DashboardBuilder/Features/Dashboard/scale-model.js, src/DashboardBuilder/Features/Dashboard/viewbar-model.js, src/DashboardBuilder/Features/Dashboard/worksheet-view.js]
---
# Worksheet table view — crosstab, paging, sort, format

The Rows × Columns table view and the formatting that applies to every view. Layout and shelves: [worksheet.md](worksheet.md).

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
| Approximate (faster) | `uniq` distinct counts and, on a table with a sampling key, a 10% sample ([exact vs sampled](../../reference/clickhouse-calculations.md#aggregates-exact-and-approximate)); median, percentile, standard deviation, variance and ATTR are estimates, and the info line says so. Labelled on the info line ([D25](../../decisions/decisions-platform.md#d25--a-short-lived-server-result-cache-and-approximate-mode)) |
| Fit | Standard / Fit width / Fit height / Entire view (also in the ⋯ sheet actions) |
| Group dates | Charts: group the first date/time dimension by Auto (default — exact when ≤ 400 values, else the finest grain with ≤ 400 buckets), Exact, Hour, Day, Week, Month, Quarter or Year. A grouped axis isn't click-filterable |
| Legend | show / position |
| Data labels | on / off |
| Colour-by-category | single-measure bar: colour each bar by its category |
| X / Y axis titles | name the **physical** axes (X = bottom, Y = left); ≤ 80 characters |

Number and date formats also drive the crosstab and KPI tiles through the shared `Core/format.js` (`makeValueFormatter` / `makeCategoryFormatter`), so every view reads identically.
