# Worksheet charts — types, rendering, export

What the worksheet can draw and how. Shelves and the base query are in [worksheet.md](worksheet.md); encodings in [worksheet-encodings.md](worksheet-encodings.md).

## At a glance

- **23 chart types**, picked from one chart-type control in the view bar. A field mapping a type can't draw shows a **hint**, never an error.
- **One query path for most types:** the bounded `POST /api/query`. Histogram and box plot have their own endpoints.
- **ECharts is vendored and only `chart.js` touches it.** Table, Text and KPI are native DOM. Colours come from `--chart-*` tokens.
- **Every category is labelled;** the pane scrolls instead of squeezing. Big charts zoom and switch to canvas.
- **Analytics** (reference lines, bands, trend, forecast, totals) are computed in the browser over the returned rows.
- **Export:** SVG, PNG, CSV (up to 100,000 rows) and Print / PDF.

**Sections:** Chart types · Chart type control · Analytics · Orientation · Query paths · Rendering · Export

## Chart types

Pick a type from the view bar's **Chart** picker or from [the chart-type control](#chart-type-control). Code: `CHART_TYPES` in `Dashboard/viewbar-model.js` (23 types).

An invalid field mapping shows a friendly **hint**, never an error (e.g. "A point chart plots two measures (X and Y) — add a second measure"). The rules live in `Dashboard/show-me-rules.js` (`CHART_NEEDS` / `chartIssue()`) and are shared with the chart-type menu, so the two never disagree.

| Type | Needs | Notes |
|---|---|---|
| Bar | ≥1 measure | grouped at ≥2 measures |
| Stacked bar | ≥1 measure | |
| Line / Area | ≥1 measure | Path can reorder vertices |
| Pie / Donut | 1 dimension + 1 measure | legend-labelled slices; measure → angle |
| Scatter | 2 measures (X, Y) | Size, continuous Colour and Shape apply |
| Combo (dual-axis) | 2 measures | The 1st measure as bars; the rest on a right axis as a line (Format → **Right-axis marks**: Line, Bars or Area). Always vertical. Format → **Synchronise axes** shares one range |
| Square / Circle | as scatter | scatter builder with a symbol override |
| Heatmap | 2 dimensions + 1 measure | Single-hue token colour scale. Format → **Shape**: **Squares** (cells) or **Circles**. Circles are scatter marks on the same category grid: 80 % of the smaller cell side, 6–48 px, re-sized with the pane. Cells without a value draw no circle. Circles are coloured by the same value legend; labels, tooltip and Reverse palette behave as for squares; the cell banding is dropped |
| Treemap | 1–2 dimensions + 1 measure | nested rectangles sized by the measure |
| Histogram | 1 numeric field | equal-width bins; own endpoint |
| Box plot | 1 numeric field (+ optional group dimension) | Q1 / median / Q3, whiskers at the 1.5 IQR (interquartile range) fences, outlier points beyond them (hollow rings, ≤ 500); own endpoint |
| Waterfall | ≥1 dimension + 1 measure | Each value is a change from the running total, then a **Total** bar. Increases `--chart-cat-1`, decreases `--chart-cat-6`, total muted — legend-named, and each step labelled with its sign. May run below zero (drawn as a custom series) |
| Funnel | 1 dimension + 1 measure | Stages widest first, each labelled with value and % of the first. Label ink picked per stage |
| Gauge | 1 measure, no dimension | Arc from 0 to Format → **Target** (else a round maximum). Value and "% of target" written in the middle |
| Bullet | 1 measure (+ ≤1 dimension), + an optional 2nd measure, + Format → **Target** | Per member: the value bar over three bands (< 50 %, 50–75 %, 75–100 % of target) with the target tick. Format → **Target field** picks the view's second (or later) measure as the target, so each member has its own target (the tooltip shows it and the %). With no field, the fixed **Target** number applies to every member. With neither, a hint |
| Sankey (flow) | 2 dimensions + 1 measure | Flows from the first dimension's members to the second's. Non-positive flows are skipped. A member on both sides stays two nodes |
| Small multiples | 2 dimensions + ≥1 measure | A mini line chart per member of the **first** dimension (at most 24 panels, with a notice), the second along each x axis, one shared y scale |
| KPI | measures | big number per measure; with a dimension, an inline SVG **sparkline** of the trend |
| Text | — | renders the crosstab text grid |
| Table | — | the crosstab ([worksheet.md](worksheet.md#table-view--a-true-rows--columns-crosstab)) |

### Text measure values

- `min` / `max` of a text or date field return a **string**. An aggregate over no rows returns `null`.
- Only **Table, Text and KPI** can show a string value. Any other chart type shows a hint: "Min/Max of a text or date field shows as Table, Text or KPI — switch the chart type, or use Count."
- Null values render as "—".

### The P36 types (Waterfall, Funnel, Gauge, Bullet, Sankey, Small multiples)

- All six run on the ordinary `/api/query` result.
- Sizing: Waterfall scrolls like a bar chart; Bullet grows down the left; Funnel, Gauge, Sankey and Small multiples always fit the pane.
- They aren't click-to-filter targets.
- Code: `renderP36` in `render-special.js`; builders in `chart.js`; pure helpers `waterfallSteps`, `niceMax`, `multiplesGrid` (unit-tested).

### Measures and dimensions

- No dimensions at all → KPI tiles.
- Scatter / combo / stacked read the first two measure pills. A shelf already holds any number of measures, so there is no separate 2nd-measure shelf.

## Chart type control

One control picks the chart type. The view bar's picker (icon + name, e.g. **KPI**) opens a two-column menu of every type. Show Me's cues are folded into it, for the fields **already on the sheet**. Code: rules in `Dashboard/show-me-rules.js` (pure, unit-tested); counts per candidate type in `showMeCounts` in `dashboards.js`.

- **Dimmed types.** A type the fields can't draw is dimmed, with the reason as its tooltip. It is still pickable; the chart then shows the hint. The first matching rule wins:
  1. Min/Max of a text or date value → only Table / Text / KPI.
  2. A discrete Colour split on bar / stacked / line / area needs exactly one measure. With one it is valid, since the split renders before the rule table.
  3. Histogram / box plot need a numeric field.
  4. Then `CHART_NEEDS`.
- **Best fit.** The best fit carries the Show Me icon (tooltip "Best fit for these fields"), only if it is valid and Columns / Rows aren't empty. It is chosen from the dimensions on Columns / Rows (plus a drill level); encodings don't steer it:
  - none → nothing;
  - text Min/Max → Table;
  - ≥ 3 dims → Table;
  - 0 dims → Scatter at 2 measures, else KPI;
  - a date dimension → Line;
  - 1 dim → Bar;
  - 2 dims + 1 measure → Heatmap;
  - otherwise Table.
- **Picking.** The current type is ticked. Picking sets the type in one commit (one undo step); Columns / Rows stay where they are.

## Analytics (P21)

The view bar's **Analytics** button opens a card, like Format (`analyticsPanel`, `sheet.analytics`). Everything is computed in the browser over the rows returned (`Dashboard/analytics-model.js`, unit-tested). Over a cut-off result the info line says "Analytics use only the rows shown — more exist."

### Adding items

On Bar / Line / Area the card opens with a row of **items**: Reference line, Band, Trend line (and Forecast on Line / Area).

- **Drag** an item onto the chart, or **press** its button (keyboard). It switches on at a default (Average, Mean ± 1σ, Linear, 3 steps), and the selects below show and edit it.
- An item already on is shown pressed, with a check after its label (each item has its own icon). Pressing it again switches it off. A drop on an item already on changes nothing.
- A drop is accepted only while the card is open (`analyticsDrop`).
- Focus returns to the pressed item after the re-render.
- Code: items and defaults are `itemsFor` / `addItem` / `removeItem` in `analytics-model.js`. Items write the ordinary saved `sheet.analytics` shape.

### Bar / Line / Area

- **Reference line** — Average, Median, Minimum, Maximum or a Constant. Drawn dashed and labelled "Average: 16".
- **Band** — shaded and labelled with its rule. Its ends are typed **from / to** numbers, **Mean ± 1σ** / **± 2σ** (sample standard deviation, ≥ 2 values), or a percentile range **P25–P75** / **P10–P90** (linear interpolation).
  - Choosing Typed range draws nothing until two different numbers are typed.
  - With too few values (or typed ends that are equal) there is no band, and an info line says why.
  - A σ / percentile band's label says "(shown rows)".
- **Which measure (line and band).** They read the measure chosen in **of**: any measure on the shelf, shown when there are two or more. A non-default choice is named in the label ("Average (sum discount): 35"). They read the rows shown, with the "Other" remainder left out.
- **Trend** — Linear, Logarithmic (`a + b·ln(x+1)`) or Polynomial (2nd order) least squares, on the first measure in category order. Drawn dotted and named at its end with its R² ("Trend · R² 0.93").
- **Forecast** (Line / Area) — 3, 6 or 12 steps that extend the trend (linear if none is picked) into "Forecast +1 …" categories.

### Table / Text

- **Grand totals** — a Total column when Columns has dimensions, a Grand total row when Rows has.
- **Subtotals** — after each first-level Rows group, with ≥ 2 Rows dimensions and the measures across the top.
- Totals use each measure's aggregation (`combine`): sums and counts add; min / max take the min / max. An average, a distinct count or a table calculation shows "—" rather than a wrong number.

## Orientation

`chartOrientation(sheet)` follows Tableau:

- A **dimension on Rows** (and none on Columns) renders **horizontal** bars: category down the left, first on top.
- A dimension on Columns renders vertical (the default).
- `buildCartesian` swaps the axes for bar / stacked / line / area.
- Row-dimension facets / small multiples are not supported.

**Line style** (Format; Line, Area, Combo; also the dashed comparison lines, not the trend line):

- **Straight** — point to point.
- **Step** — each value holds until the next category, then changes.
- **Step (centred)** — a connected step that changes half-way between two categories (stored as `jump`).
- Code: `format.lineStyle`; ECharts `step` `end` / `middle` via `lineStep`.

### Dual axis, marker size, marker shape and mark borders

- **Right-axis marks** (combo only; `format.secondaryType` `line` | `bar` | `area`, default `line`) — draws every measure after the first on the right axis as lines, bars or a filled line. Bars on the right axis sit beside the left bars. The line style applies to line and area.
- **Synchronise axes** (combo, and Line / Area with Dual axis on; `format.syncAxes`, default off) — gives both value axes the same `min` / `max`. Off, each axis scales on its own.
  - The range covers all the measures' finite values, rounded out to a 1 / 2 / 5 × 10ⁿ step.
  - It includes 0 for the combo (its first measure is bars) and for an area chart, but not for a line chart.
  - Null, NaN and non-numbers are skipped. No data leaves the axes automatic. All zero gives 0–1.
  - Code: `syncRange` in `Dashboard/axis-sync-model.js`.
- **Dual axis** (Line and Area; `format.dualAxis`, default off) — with two or more measures, draws every measure after the first on a right value axis, in the chart's own mark (lines, or filled lines). Code: `dualAxisOn` in `Dashboard/axis-sync-model.js`.
  - Titles: the right axis is titled with the names of the measures on it (`rightAxisTitle`); the left with the first measure (or Format → Y title). The legend names every series. A long right-axis title is cut with an ellipsis (the legend lists every measure).
  - **Synchronise axes** appears with it (a line chart's shared range need not include 0; an area chart's does). Right-axis marks is combo only.
  - Which axis: comparison lines ride their measure's axis. The reference line and band sit on the series of the measure they read (Analytics → of), so a right-axis measure's line is drawn on the right scale. The trend and forecast follow the first measure on the left.
  - With a dimension on Rows (horizontal chart) the Dual axis checkbox is disabled and the chart keeps one axis.
  - Not built: scatter, independent mark types per measure, a user-set axis range.
- **Marker size (px)** (`format.markerSize`: blank = automatic, else a whole number 4–40) — out-of-range input is refused with a toast, never clamped. It sets the point size of:
  - scatter / square / circle marks when no Size field is mapped (default 14, shape scatter 12);
  - line / area / combo markers (default 8, which also keeps the dots on a long series);
  - the circle heatmap (otherwise 80 % of the cell).
  - It is not offered on squares heatmaps or on charts without point marks.
- **Mark border** (`format.markBorder` `none` | `thin` (1 px) | `thick` (3 px), default `none`) — strokes marks in the muted chart ink (`--chart-muted`, so it follows light and dark).
  - Applies to bars (also stacked, combo, colour-by-category and the Other bar), scatter / shape points, line markers, heatmap cells, pie / donut slices, treemap tiles and funnel steps.
  - `none` keeps the default look: the heatmap, pie, treemap and funnel keep their surface-coloured gaps. A chosen border replaces that edge (`edgeOr`).
  - Code: pure mapping in `Dashboard/mark-style-model.js` (`markBorder`, `edgeOr`, `markerSizeOr`, `markerSizeError`).
- **Marker shape** (line / area / combo; `format.markerShape` `circle` | `square` | `diamond` | `triangle`, default `circle`) — sets the symbol of the line markers (`markerSymbol` maps to the ECharts symbol). The shape is the same on every series of the sheet.
- Both Format cards and the dashboard widgets read the same sheet `format`, so non-interactive views draw the options too. Browser check: `tests/live/charts2-ui.mjs`.

## Query paths

- **Standard types** (bar … treemap, KPI, table) all use the one bounded `POST /api/query`. Heatmap and treemap pivot its 2-dimension result in the browser (`renderHeatmap` / `renderTreemap` in `render-special.js`; pivots in `result-model.js`).
- **Histogram and box plot** are single-table shapes with their own endpoints (`POST …/histogram`, `…/boxplot`). They bypass `buildPlan` (`runStatChart`) and read the first numeric field. Bins default to 20; the server rejects a count outside 1..100.
- SQL for each: [clickhouse-integration.md](../../reference/clickhouse-integration.md#the-queries-all-read-only).

## Rendering — the ECharts adapter

### Library and theming

- **Apache ECharts** is vendored at `Features/Core/vendor/echarts.min.js` and loaded as a classic global script **before** the module graph ([D13](../../reference/decisions/decisions.md#d13--charting-via-self-hosted-apache-echarts-svg-renderer-themed-from-tokens)).
- **`chart.js` is the only module that touches ECharts.**
  - `renderChart(container, spec)` maps a result to an option and manages **one live instance per container** (SVG renderer). The palette order and member colours are per-container state too.
  - `disposeChart()` tears the instance down before every repaint.
  - It dispatches by family: `buildCartesian`, `buildPie`, `buildScatter`, `buildScatterShapes`, `buildHeatmap`, `buildTreemap`, `buildHistogram`, `buildBoxplot`.
- **Table, Text and KPI are native DOM**, not ECharts.
- **Themed from tokens.** `chart.js` reads `--chart-*` via `getComputedStyle`. Text wears ink tokens; marks wear the series colour ([design/tokens.md](../../design/tokens.md#chart-tokens)).
  - It re-renders the active chart on `scheme:changed`, when light / dark is flipped ([tokens.md § Light and dark](../../design/tokens.md#light-and-dark); listener in `dashboards.js`).
  - Treemap tile labels pick their ink per tile with `contrast.js`.
- **Resize.** A `ResizeObserver` on the chart host calls `instance.resize()` (sidebar drag, window). The host is absolutely positioned to fill the padded `.ws-chart` pane, so ECharts always has a definite size.

### Category axes and sizing

- **Every category is shown and labelled — the pane scrolls instead of squeezing.**
  - `chartFit` (`Dashboard/chart-fit.js`, pure) gives each category a slot: 28px along a bottom axis (wider for grouped bars: 12px per bar), 24px down a left axis. It sets the host's `--chart-min-w` / `--chart-min-h`.
  - A chart with more categories than fit (e.g. 50 customers on a narrow pane) keeps that size and `#ws-chart` scrolls: sideways for vertical bars / lines / area / combo / histogram / boxplot, down for horizontal bars, both for a heatmap.
  - Category axes label every category (`interval: 0`, no `hideOverlap`). Bottom labels turn upright when they can't sit side by side (re-checked on resize). Bottom labels truncate at 160px, left labels at 200px; the tooltip carries the full name.
  - Pie, donut, treemap and scatter have no category axis and always fit the pane.
- **Fit** (P23, `format.fit`) — `applyFitMode` drops the minimum width / height (and the zoom) on the fitted axis. Its labels then thin out (`hideOverlap`) instead of forcing a slot each.
- **Big charts.**
  - Past **1,000** categories an axis stops growing. A themed **zoom slider** (plus wheel / drag in the plot) shows a pane-width window of categories at a time (`addZoom`).
  - Past **1,500** marks the chart draws on **canvas** instead of SVG. Bars use ECharts' large mode (unless a bar carries its own colour) and lines use LTTB sampling, so peaks survive (`tuneForSize`).
  - Canvas charts skip the entrance animation.

### Date axis labels

Only when the chart's first dimension is a date. Code: `Dashboard/date-axis.js` (pure), wired in `chart.js` `dateAxisLabels`.

- **Shortening.** Datetime labels are shortened to what varies across the data: midnight-only reads as dates, one day as times, one year drops the year, zero seconds drop. Other text is left alone.
- **Thin out** draws only as many labels as fit the measured text width (canvas `measureText` in the axis font) plus 8px.
  - Labels are spread evenly with the **first and last always shown** and none touching; end labels hang inward. A left axis needs 18px a label.
  - When ticks land a day or more apart, the time of day is dropped.
  - A bottom axis that can't hold three horizontal labels turns them upright.
  - Works on the left axis of horizontal bars too, and is re-planned on resize.
- **Show all** keeps every label, shortened.
- The tooltip keeps the full value.

### Special marks and clicks

- **Comparison series** (`compare: true`, P35) don't make a chart multi-series; the measure keeps the brand colour. A line is dashed and faded; a bar muted and hatched (an ECharts `decal`). The legend names each — [worksheet-encodings.md](worksheet-encodings.md#date-range--comparison).
- **Other mark:** `otherIndex` colours the "Other (N more)" bar / slice with `--chart-muted`.
- Chart clicks are forwarded to the worksheet for click-to-filter and drill ([worksheet-encodings.md](worksheet-encodings.md#click-to-filter)).

## Export

The view bar's **Export** menu (`exportControl`, icon button) also holds **Print / PDF…** ([layout.md](../../design/layout.md#full-screen--print)).

- **SVG** — serialises the rendered `<svg>` element (`instance.getDom()`). `renderToSVGString` exists only on SSR (server-side rendering) instances, so it is not used.
- **PNG** — rasterises that SVG through a canvas (`exportChart` in `chart.js`).
- **When SVG / PNG are offered:** only when a chart instance exists; Table / KPI / Text export CSV instead. A canvas chart exports PNG from the canvas, and SVG by redrawing the same option off-screen as SVG.
- **CSV** — posts the same bounded worksheet plan to `POST /api/query/export.csv`.
  - It asks for the **whole result**: up to 100,000 rows, no Top-N, no paging, no Other row (same date grouping as the view).
  - Serialised by `CsvUtil`: RFC-4180 quoting plus a **formula-injection guard** (a leading `= + - @` is prefixed with `'`).
- Histogram and box-plot data have no CSV export (their shape is not a `QueryRequest`).
