# Worksheet charts — types, rendering, export

What the worksheet can draw and how. Shelves and the base query are in [worksheet.md](worksheet.md);
encodings in [worksheet-encodings.md](worksheet-encodings.md).

## Chart types

Picked from the view bar's **Chart** picker (`CHART_TYPES` in `Dashboard/viewbar-model.js`, 23 types) or from
[Show Me](#show-me). An invalid field mapping shows a friendly **hint**, never an error — the rules live in
`Dashboard/show-me-rules.js` (`CHART_NEEDS` / `chartIssue()`, e.g. "A point chart plots two measures (X and
Y) — add a second measure"), shared with Show Me so the two never disagree.

| Type | Needs | Notes |
|---|---|---|
| Bar | ≥1 measure | grouped at ≥2 measures |
| Stacked bar | ≥1 measure | |
| Line / Area | ≥1 measure | Path can reorder vertices |
| Pie / Donut | 1 dimension + 1 measure | legend-labelled slices; measure → angle |
| Scatter | 2 measures (X, Y) | Size, continuous Colour and Shape apply |
| Combo (dual-axis) | 2 measures | 1st as bars, 2nd as a right-axis line; always vertical |
| Square / Circle | as scatter | scatter builder with a symbol override |
| Heatmap | 2 dimensions + 1 measure | single-hue token colour scale; Format → **Shape** **Squares** (cells) or **Circles** (scatter marks on the same category grid, 80 % of the smaller cell side, 6–48 px, coloured by the same value legend; labels, tooltip and Reverse palette behave as for squares, the cell banding is dropped) |
| Treemap | 1–2 dimensions + 1 measure | nested rectangles sized by the measure |
| Histogram | 1 numeric field | equal-width bins; own endpoint |
| Box plot | 1 numeric field (+ optional group dimension) | min/Q1/median/Q3/max; own endpoint |
| Waterfall | ≥1 dimension + 1 measure | each value a change from the running total, then a **Total** bar; increases `--chart-cat-1`, decreases `--chart-cat-6`, total muted — legend-named and each step labelled with its sign; may run below zero (drawn as a custom series) |
| Funnel | 1 dimension + 1 measure | stages widest first, each labelled with value and % of the first; label ink picked per stage |
| Gauge | 1 measure, no dimension | arc from 0 to Format → **Target** (else a round maximum); value and "% of target" written in the middle |
| Bullet | 1 measure (+ ≤1 dimension), + an optional 2nd measure, + Format → **Target** | per member: the value bar over three bands (< 50 %, 50–75 %, 75–100 % of target) with the target tick. Format → **Target field** picks the view's second (or later) measure as the target, so each member has its own target (the tooltip shows it and the %); with no field the fixed **Target** number applies to every member; with neither, a hint |
| Sankey (flow) | 2 dimensions + 1 measure | flows from the first dimension's members to the second's; non-positive flows skipped; a member on both sides stays two nodes |
| Small multiples | 2 dimensions + ≥1 measure | a mini line chart per member of the **first** dimension (at most 24 panels, with a notice), the second along each x axis, one shared y scale |
| KPI | measures | big number per measure; with a dimension, an inline SVG **sparkline** of the trend |
| Text | — | renders the crosstab text grid |
| Table | — | the crosstab ([worksheet.md](worksheet.md#table-view--a-true-rows--columns-crosstab)) |

**Text measure values.** `min` / `max` of a text or date field return a **string**, and an aggregate over
no rows returns `null`. Only **Table, Text and KPI** can show a string value; any other chart type shows
a hint ("Min/Max of a text or date field shows as Table, Text or KPI — switch the chart type, or use
Count."). Null values render as "—".

All six P36 types run on the ordinary `/api/query` result (`renderP36` in `dashboards.js`; builders in
`chart.js`, pure helpers `waterfallSteps`, `niceMax`, `multiplesGrid` unit-tested). Waterfall scrolls like a
bar chart; Bullet grows down the left; Funnel, Gauge, Sankey and Small multiples always fit the pane. They
aren't click-to-filter targets.

No dimensions at all → KPI tiles. Scatter/combo/stacked read the first two measure pills — a shelf
already holds any number of measures, so there is no separate 2nd-measure shelf.

## Show Me

The view bar's **Show Me** button (beside the Chart picker) opens a card — one card at a time with Format /
Analytics — listing every chart type for the fields **already on the sheet** (no field selection). Rules:
`Dashboard/show-me-rules.js` (pure, unit-tested); counts per candidate type: `showMeCounts` in `dashboards.js`.

- **Greyed** tile (`aria-disabled`, still focusable): the type can't draw these fields; the reason is its
  tooltip, and activating it writes the reason to the card's status line. Checked in order, first hit wins:
  Min/Max of a text or date value → only Table / Text / KPI; a discrete Colour split on bar / stacked /
  line / area needs exactly one measure — and with one it is valid, since the split renders before the rule
  table; histogram / box plot need a numeric field; then `CHART_NEEDS`.
- **Recommended** tile: accent outline + "Recommended" text, only if valid and Columns / Rows aren't empty. From the dimensions on Columns /
  Rows (plus a drill level) — encodings don't steer it: none → nothing; text Min/Max → Table; ≥ 3 dims →
  Table; 0 dims → Scatter at 2 measures, else KPI; a date dimension → Line; 1 dim → Bar; 2 dims + 1
  measure → Heatmap; otherwise Table.
- **Current** tile: pressed, with a check icon. No fields → "Add fields to Columns or Rows to see
  suggestions."; Esc closes the card and returns focus to the button.
- **A click** sets the type and re-lays **only Columns / Rows** (`placeFor`) in one commit — one undo step;
  re-picking a layout already in place commits nothing. Dimensions keep group-by order (Rows, then
  Columns); measures keep series order; no pill is added or dropped.

| Family | Types | Columns | Rows |
|---|---|---|---|
| Horizontal bars (kept when only Rows has dims) | bar, stacked | measures | dimensions |
| Category × measure | bar, stacked, waterfall, funnel, bullet, kpi, pie, donut, treemap, gauge, histogram, boxplot | dimensions | measures |
| Time series | line, area, combo | dimensions, dates first | measures |
| Measure × measure | scatter, square, circle | dimensions, then measure 1 | the other measures |
| Two dimensions | heatmap, sankey, multiples | the other dimensions, then measures | the first dimension |
| Text table | table, text | measures | dimensions |

## Analytics (P21)

The view bar's **Analytics** button opens a card (like Format; `analyticsPanel`, `sheet.analytics`).
Everything is computed in the browser over the rows returned (`Dashboard/analytics-model.js`,
unit-tested); over a cut-off result the info line says "Analytics use only the rows shown — more exist."

- **Bar / Line / Area**, on the first measure in category order: a **reference line** — Average, Median,
  Minimum, Maximum or a Constant — drawn dashed and labelled "Average: 16"; a **band** between two
  constants, shaded and labelled; a **trend** — Linear, Logarithmic (`a + b·ln(x+1)`) or Polynomial (2nd
  order) least squares — drawn dotted and named at its end with its R² ("Trend · R² 0.93"); and on Line /
  Area a **forecast** of 3, 6 or 12 steps that extends the trend (linear if none is picked) into
  "Forecast +1 …" categories.
- **Table / Text**: **Grand totals** (a Total column when Columns has dimensions, a Grand total row when
  Rows has) and **Subtotals** (after each first-level Rows group, with ≥ 2 Rows dimensions and the
  measures across the top). Totals use each measure's aggregation (`combine`): sums and counts add,
  min / max take the min / max; an average, a distinct count or a table calculation shows "—" rather than a
  wrong number.

## Orientation

`chartOrientation(sheet)` follows Tableau: a **dimension on Rows** (and none on Columns) renders
**horizontal** bars (category down the left, first on top); a dimension on Columns renders vertical
(the default). Format → **Line style** (Line, Area, Combo; also the dashed comparison lines, not the trend line) draws **Straight** (point to point), **Step** (each value holds until the next category, then changes) or **Jump** (the value changes half-way between two categories) — `format.lineStyle`, ECharts `step` `end` / `middle` via `lineStep`. `buildCartesian` swaps the axes for bar/stacked/line/area. Row-dimension facets / small
multiples are not supported.

## Query paths

- **Standard types** (bar … treemap, KPI, table) all use the one bounded `POST /api/query`; heatmap and
  treemap pivot its 2-dimension result client-side (`renderHeatmap` / `renderTreemap`).
- **Histogram and box plot** are single-table shapes with their own endpoints
  (`POST …/histogram`, `…/boxplot`). They bypass `buildPlan` (`runStatChart`) and read the first
  numeric field. Bins default 20; the server rejects a count outside 1..100.
- SQL for each: [clickhouse-integration.md](../reference/clickhouse-integration.md#the-queries-all-read-only).

## Rendering — the ECharts adapter

- **Apache ECharts** is vendored at `Features/Core/vendor/echarts.min.js` and loaded as a classic
  global script **before** the module graph ([D13](../reference/decisions.md#d13--charting-via-self-hosted-apache-echarts-svg-renderer-themed-from-tokens)).
- **`chart.js` is the only module that touches ECharts.** `renderChart(container, spec)` maps a result
  to an option and manages **one live instance** (SVG renderer); `disposeChart()` tears it down before
  every repaint. It dispatches by family: `buildCartesian`, `buildPie`, `buildScatter`,
  `buildScatterShapes`, `buildHeatmap`, `buildTreemap`, `buildHistogram`, `buildBoxplot`.
- **Table, Text and KPI are native DOM**, not ECharts.
- **Themed from tokens**: `chart.js` reads `--chart-*` via `getComputedStyle`; text wears ink tokens,
  marks wear the series colour ([design/tokens.md](../design/tokens.md#chart-tokens)). It re-renders the
  active chart on `scheme:changed` — light / dark flipped ([tokens.md § Light and dark](../design/tokens.md#light-and-dark); listener in `dashboards.js`). Treemap tile labels
  pick their ink per tile with `contrast.js`.
- **Resize**: a `ResizeObserver` on the chart host calls `instance.resize()` (sidebar drag, window).
  The host is absolutely positioned to fill the padded `.ws-chart` pane so ECharts always has a
  definite size.
- **Every category is shown and labelled — the pane scrolls instead of squeezing.** `chartFit`
  (`Dashboard/chart-fit.js`, pure) gives each category a slot — 28px along a bottom axis (wider for
  grouped bars: 12px per bar), 24px down a left axis — and sets the host's `--chart-min-w` /
  `--chart-min-h`. A chart with more categories than fit (e.g. 50 customers on a narrow pane) keeps that
  size and `#ws-chart` scrolls: sideways for vertical bars/lines/area/combo/histogram/boxplot, down for
  horizontal bars, both for a heatmap. Category axes label every category (`interval: 0`, no
  `hideOverlap`); bottom labels turn upright when they can't sit side by side (re-checked on resize) and
  truncate at 160px, left labels at 200px — the tooltip carries the full name. Pie, donut, treemap and
  scatter have no category axis and always fit the pane.
- **Fit** (P23, `format.fit`): `applyFitMode` drops the minimum width / height (and the zoom) on the fitted
  axis, whose labels then thin out (`hideOverlap`) instead of forcing a slot each.
- **Big charts.** Past **1,000** categories an axis stops growing: a themed **zoom slider** (plus wheel /
  drag in the plot) shows a pane-width window of categories at a time (`addZoom`). Past **1,500** marks
  the chart draws on **canvas** instead of SVG; bars use ECharts' large mode (unless a bar carries its own
  colour) and lines LTTB sampling, so peaks survive (`tuneForSize`). Canvas charts skip the entrance
  animation.
- **Comparison series** (`compare: true`, P35): they don't make a chart multi-series (the measure keeps
  the brand colour); a line is dashed and faded, a bar muted and hatched (an ECharts `decal`), and the
  legend names each — [worksheet-encodings.md](worksheet-encodings.md#date-range--comparison).
- **Other mark:** `otherIndex` colours the "Other (N more)" bar / slice with `--chart-muted`.
- Chart clicks are forwarded to the worksheet for click-to-filter and drill
  ([worksheet-encodings.md](worksheet-encodings.md#click-to-filter)).

## Export

The view bar's **Export** menu (`exportControl`, icon button) — also **Print / PDF…**
([layout.md](../design/layout.md#full-screen--print)):

- **SVG** — serialises the rendered `<svg>` element (`instance.getDom()`); `renderToSVGString` exists
  only on SSR instances, so it is not used.
- **PNG** — rasterises that SVG through a canvas (`exportChart` in `chart.js`).
- SVG/PNG are offered only when a chart instance exists; Table/KPI/Text export CSV instead. A canvas
  chart exports PNG from the canvas and SVG by redrawing the same option off-screen as SVG.
- **CSV** — posts the same bounded worksheet plan to `POST /api/query/export.csv`, serialised by
  `CsvUtil`: RFC-4180 quoting plus a **formula-injection guard** (a leading `= + - @` is prefixed with
  `'`). Asks for the **whole result** — up to 100,000 rows, no Top-N, no paging, no Other row (same date grouping as the view).
- Histogram and box-plot data have no CSV export (their shape is not a `QueryRequest`).
