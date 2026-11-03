# Competitive uplift — visualization & interactivity (P9–P16)

Turns the **quick wins (#1–#8)** from
[competitive-analysis.md](../../archive/docs/project/competitive-analysis.md) into phases — the
highest-ROI, lowest-risk distance toward Tableau-class visuals and interactivity. Each
**builds on the P7 worksheet**, is **independently shippable**, and inherits the
[cross-phase definition of done](build-plan-p18-p25.md#cross-phase-definition-of-done) (read-only, identifier
safety, `hidden` visibility, tokens). These are **feature** phases; P8's security/a11y/test
passes apply to each as it lands. Track-wide guards:

- **Self-host the charting library — no CDN.** Vendor it into `wwwroot/` and serve it under
  the app's `no-cache` static policy. A viz library is a **dependency, not an SPA
  framework** — [D4](../../archive/docs/project/decisions.md) still holds (vanilla-JS modules render into
  `#ws-chart`).
- **Chart colors from design tokens** ([CLAUDE.md](../../archive/CLAUDE.md) rule 6, [DESIGN.md](../../archive/DESIGN.md)):
  a token-derived, WCAG-AA categorical palette; never encode by color alone.
- **Every new query stays read-only, bounded, and identifier-safe** — new filters/drill
  values are **bound parameters**, never interpolated ([D6](../../archive/docs/project/decisions.md));
  new dimensions/measures are catalog-validated + quoted; row counts clamped.

## P9 — Charting library foundation *(quick win #1)*
**Goal:** replace the hand-rolled SVG rendering with a real charting library, with the
existing Bar/Line/Table visually intact.
- Vendor a **self-hosted** build of **Apache ECharts** or **Vega-Lite** into
  `wwwroot/js/vendor/`; add a thin `wwwroot/js/chart.js` adapter mapping a worksheet result
  → chart spec, rendering into `#ws-chart`.
- Wire the **chart palette to CSS tokens**; keep status/marks distinguishable beyond color.
- **Done when:** the current Bar/Line/Table render through the library with no regression;
  the bundle is fully self-hosted (no CDN/network calls); jsdom UI check still green.
- **Doc:** [frontend-patterns.md](../../archive/docs/frontend-patterns.md) (charting adapter),
  [DESIGN.md](../../archive/DESIGN.md) (chart palette tokens).
- **✅ Shipped:** ECharts vendored at `wwwroot/js/vendor/echarts.min.js` (SVG renderer, loaded
  before the module graph); `wwwroot/js/chart.js` adapter maps results → option, themed from
  `--chart-*` tokens; `dashboards.js` routes **bar/line** to it and keeps **table/KPI** as
  native DOM. Build clean + 56 tests green; page and the vendored lib serve `200` (no-cache)
  via `https://10.168.49.20/dashboardbuilder/` ([D13](../../archive/docs/project/decisions.md)). The
  hand-rolled `.chart-bar*/.chart-line` code + CSS were removed. *Pending a live in-browser
  render check against real data (no headless browser on the host to automate it).*

## P10 — Chart formatting & encodings *(quick win #2)*
**Goal:** per-chart formatting without touching the query.
- Number/date formats, axis titles, legend toggle/position, sort order, **top-N**, data
  labels, **color-by-dimension** — stored on the widget config (in-memory per
  [O1](../../archive/docs/project/decisions.md)).
- **Done when:** a user formats a chart (e.g. currency axis, top-10, sorted desc, colored by
  category) and it renders and persists for the session.
- **Doc:** [modules.md](../../archive/docs/app/modules.md) (worksheet formatting).
- **✅ Shipped 2026-08-17:** a collapsible **Format panel** (`formatPanel` in `dashboards.js`, toggled
  from the shelves row) drives `sheet.format` ([store.js](../../src/DashboardBuilder/wwwroot/js/store.js)
  `defaultFormat()`): **number format** (auto/compact/currency/percent + decimals), **date format** for
  date-like dimension labels, **top-N** (caps the chart query `LIMIT`), **legend** show/position,
  **data labels**, **colour-by-category** (single-measure bar), and **X/Y axis titles**. Formats flow
  through a shared pure module `wwwroot/js/format.js` (`makeValueFormatter`/`makeCategoryFormatter`) so
  charts (`chart.js`), the crosstab, and KPI tiles read identically. Sort already shipped in P7. All
  presentation-only (no new query surface) except top-N; config persists per session (O1). Build clean
  + 63 tests green; module graph + assets serve `200`. **Deployed live 2026-08-17** (republished +
  service restarted; verified `200` at `https://10.168.49.20/dashboardbuilder/`). *(In-browser render
  check still pending — no headless browser on the host, per P9's note.)*

## P11 — Chart-type expansion *(quick win #3)*
**Goal:** more chart types on the **existing** aggregate/join query path.
- Area, stacked/grouped bar, pie/donut, **scatter**, histogram, KPI + sparkline,
  **combo / dual-axis**. Scatter and dual-axis need a **second measure** — extend the
  worksheet to accept a 2nd measure shelf; still one bounded aggregate query.
- **Done when:** each type is selectable and renders from a valid field mapping; invalid
  mappings are disabled with a hint (not an error).
- **Doc:** [modules.md](../../archive/docs/app/modules.md) (chart types), [data-model.md](../../archive/docs/data-model.md)
  (widget encoding for the 2nd measure).
- **✅ Shipped 2026-08-17:** the chart-type picker (a **dropdown** now the list is long) offers
  **Bar, Stacked bar, Line, Area, Pie, Donut, Scatter, Combo (dual-axis), KPI, Table**. `chart.js`
  dispatches by family — `buildCartesian` (bar/stacked/line/area/combo, incl. a **secondary y-axis**
  for the combo line), `buildPie` (pie/donut, legend-labelled slices), `buildScatter` (two measures →
  X/Y value axes). **KPI+sparkline**: KPI tiles show a headline number, and with a dimension add an
  inline SVG **sparkline** of the trend (no extra ECharts instance). `chartIssue()` returns a friendly
  **hint** (never an error) when a mapping is invalid (e.g. "Scatter plots two measures — add a second
  measure"). **No 2nd-measure shelf was needed** — the P7 worksheet already accepts any number of
  measure pills, so scatter/combo/stacked read `measures[0..1]`. All on the **existing bounded
  aggregate/join query** (no new query shape). **Histogram was deferred to P12**: a true histogram
  needs a bucketing expression (`floor(x/w)*w` group-by), which is exactly P12's "new query shape"
  work — folding it here would have violated P11's "existing query path" guard. Build clean + 63 tests
  green; module graph + assets serve `200`. **Deployed live 2026-08-17** (republished + service
  restarted; verified `200` at `https://10.168.49.20/dashboardbuilder/`). *(In-browser render check
  still pending — no headless browser on the host, per P9's note.)*

## P12 — Statistical chart types *(quick win #4)*
**Goal:** heatmap, treemap, box plot, **histogram** — the first phase that adds a **query shape**.
- Extend the gateway aggregate to support **two dimensions** (heatmap/treemap), **quantiles**
  (`quantile()`/`quantiles()`, plus min/median/max for box plots), and **numeric bucketing**
  (`floor(col/width)*width` group-by) for a **histogram** (moved here from P11 — it needs this new
  query shape). All identifiers validated + quoted; bucket width/limits clamped.
- **Done when:** a 2-dimension heatmap, a treemap, and a box plot render from real data;
  queries are bounded and injection-safe.
- **Doc:** [clickhouse-integration.md](../../archive/docs/clickhouse-integration.md) (2-dim + quantile
  aggregate shapes).
- **✅ Shipped 2026-08-18:** four chart types added. **Heatmap** and **treemap** reuse the existing
  multi-dimension `/api/query` (no new shape) — the client pivots the 2-dim result into ECharts
  heatmap cells / a treemap tree (`renderHeatmap`/`renderTreemap` in `dashboards.js`, `buildHeatmap`/
  `buildTreemap` in `chart.js`; heatmap colour is a token-driven single-hue `--brand-soft`→`--brand`
  visualMap). **Histogram** and **box plot** are new single-table query shapes on the gateway:
  `HistogramAsync` (equal-width bucketing via a `WITH (min)/(max)` + `floor((col-lo)/width)` in one
  bounded statement, bins clamped 1..100) and `BoxPlotAsync` (`min`/`quantile(.25|.5|.75)`/`max`,
  optionally grouped). New endpoints `POST …/histogram` + `…/boxplot`; they bypass `buildPlan`
  (`runStatChart`). A new pure `BuildSingleTableFilters` + `ClampBuckets` are unit-tested (hostile
  columns/ops rejected). Build clean + **77 tests**. *(In-browser render pending — no headless browser
  on host.)*

## P13 — Export *(quick win #5)*
**Goal:** export a chart image and the rows behind it.
- Client: **PNG/SVG** from the charting library.
- Server: `GET …/export.csv` for a widget's query — **read-only, bounded `LIMIT`**, streamed;
  identifiers validated; never `SELECT *` without a bound; no secret in output.
- **Done when:** a user exports a chart PNG and a CSV of its rows; the CSV respects the row cap.
- **Guards:** read-only ([D1](../../archive/docs/project/decisions.md)); never an unbounded export.
- **Doc:** [clickhouse-integration.md](../../archive/docs/clickhouse-integration.md),
  [modules.md](../../archive/docs/app/modules.md).
- **✅ Shipped 2026-08-18:** an **Export ▾** menu on the view bar (`exportControl` in `dashboards.js`).
  **PNG/SVG** come from the live ECharts instance — SVG is obtained by **serialising the rendered
  `<svg>` element** (`instance.getDom()`; `renderToSVGString` only exists on SSR instances, so relying
  on it silently failed — fixed 2026-08-18), PNG is rasterised from that SVG through a canvas
  (`exportChart` in `chart.js`); offered only when a chart
  instance exists (Table/KPI → use CSV). **CSV** posts the same bounded worksheet plan to
  `POST /api/query/export.csv`, which reuses `QueryAsync` then serialises via a new pure `CsvUtil`
  (RFC-4180 quoting + **formula-injection guard** — a leading `= + - @` is neutralised). Read-only,
  same `LIMIT` clamp as the chart. `CsvUtil` unit-tested; **87 tests**. *(Histogram/box-plot CSV
  deferred — their shape isn't a `QueryRequest`.)*

## P14 — Dashboard filters & parameters *(quick win #6)*
**Goal:** dashboard-level controls that filter every applicable widget.
- Controls: category dropdown (from a **bounded** distinct-values query), date-range picker,
  numeric slider; a per-dashboard **filter-state** slice.
- Apply by injecting an extra `WHERE` into each widget's query with **values bound as typed
  parameters** (reuse the existing aggregate/query param path — [D6](../../archive/docs/project/decisions.md)).
- **Done when:** setting a dashboard date range / category re-queries and updates every
  applicable widget; a control on a field absent from a widget's tables is a clear no-op;
  filters are scoped to their dashboard.
- **Doc:** [data-model.md](../../archive/docs/data-model.md) (dashboard filter state),
  [modules.md](../../archive/docs/app/modules.md), [clickhouse-integration.md](../../archive/docs/clickhouse-integration.md)
  (bounded distinct-values query).
- **✅ Shipped 2026-08-18 (worksheet-scoped):** since a dashboard is still **one worksheet** (multi-
  worksheet composition is P24), P14 landed as **richer Filters-shelf controls** that all bind as typed
  parameters ([D6](../../archive/docs/project/decisions.md)). New ops **`in`** (a multi-select populated from a
  **bounded distinct-values** query — `GET …/columns/{col}/distinct`, `DistinctValuesAsync`, clamped
  1..1000) and **`between`** (a two-bound range) join the scalar ops; the client renders the matching
  control per op (`filterValueControl`/`populateDistinct` in `dashboards.js`). Server-side a new pure
  **`BuildCondition`** centralises all three shapes — `in` binds an `Array(String|Float64)`, `between`
  two bounds, scalars one — and `QueryAsync`'s filter loop now calls it (empty `in`/partial range =
  no-op, never `IN ()`). `BuildCondition` + `ClampDistinct` unit-tested (incl. array binding + hostile
  op); **100 tests**. Cross-**widget** filtering proper arrives with P24; click-to-filter is P15.

## P15 — Cross-filtering / click-to-filter *(quick win #7)*
**Goal:** click a mark to filter the rest of the dashboard (the P7 "next" item).
- A mark selection (bar/point/cell) emits on the client event bus → becomes a **transient
  dashboard filter** (P14 machinery) → re-queries the other widgets; click-again / clear
  resets; the source widget shows the active selection.
- **Done when:** clicking a bar filters the dashboard's other widgets by that dimension
  value; clearing restores; the selection is visible.
- **Depends on:** P14 (filter state + bound re-query).
- **Doc:** [modules.md](../../archive/docs/app/modules.md) (interactions),
  [frontend-patterns.md](../../archive/docs/frontend-patterns.md) (event bus).
- **✅ Shipped 2026-08-18 (worksheet-scoped):** since a dashboard is still one worksheet (cross-*widget*
  filtering is P24), P15 landed as the **transient-selection machinery** on that worksheet — the exact
  mechanism P24 will reuse. Clicking a chart mark (`chart.js` forwards the ECharts `click`; the client
  maps `dataIndex` → the primary dimension's raw value via `selectHandler`/`toggleSelection`) sets
  `sheet.selection`; a **selection chip** (`selectionChip` in `dashboards.js`) shows it with **Keep only**
  (`col = value`), **Exclude** (`col != value`) and clear. Keep/Exclude apply as a **bound-parameter**
  filter appended in `buildPlan` (only when the selected column's table is already in the query — never
  forces a join), re-querying via the P14 path. Clicking the same mark or ✕ clears; the chip is the
  visible selection. Wired for bar/stacked/line/area/combo/pie/donut/scatter (incl. colour-split);
  null values and non-mapped types are no-ops. Pure client change — build clean, **100 tests** green.
  *(In-browser click check pending — no headless browser on host.)*

## P16 — Hierarchical drill-down *(quick win #8)*
**Goal:** descend a hierarchy within a chart (year→quarter→month, country→state→city).
- Define **hierarchy metadata** (ordered levels over columns of one table) in the data
  model; clicking a mark (or a drill control) re-queries one level finer with the parent
  value **pinned as a bound filter**; breadcrumb + drill-up.
- **Done when:** a user defines a 2–3 level hierarchy, drills down by clicking, sees a
  breadcrumb, and drills back up; queries bounded + identifier-safe.
- **Depends on:** P14 (bound filter injection).
- **Doc:** [data-model.md](../../archive/docs/data-model.md) (hierarchy metadata),
  [modules.md](../../archive/docs/app/modules.md).
- **✅ Shipped 2026-08-18 (worksheet-scoped, single-table hierarchy):** a new **Drill-down shelf lane**
  takes ≥2 dimension fields **from one table** as ordered levels, stored on `sheet.drill`
  (`{ levels, depth, path }` — [store.js](../../src/DashboardBuilder/wwwroot/js/store.js)). The **current
  level leads the group-by** — `buildPlan` prepends it as the first row dimension (`k0`), so it drives
  the category axis and is the sheet's `primaryDim`. Clicking a mark **drills one level finer**
  (`selectHandler` → `drillDown`), pinning the clicked value; each pinned ancestor rides along as a
  **bound-parameter `=`** filter on the drill table — same table, so it **never forces a join** (reuses
  the P14/[D16](../../archive/docs/project/decisions.md) filter path). A **breadcrumb chip** (`drillChip`, amber
  `.ws-drill`) shows `All › 2023 › Q2` with each crumb clickable to jump up and a **▲ Up** control;
  finest-level clicks are a no-op, editing the levels resets the descent, and a hierarchy alone renders
  an implicit-count chart of the level. **Pure client — no new server query surface** ([D17](../../archive/docs/project/decisions.md)),
  so the read-only invariant is untouched; build clean + **100 tests** green. **Deployed live 2026-08-18**
  (verified `200` + drill assets at `https://10.168.49.20/dashboardbuilder/`). *(In-browser click-drill
  check pending — no headless browser on the host, per P9's note.)*

---

# Usability

## P17 — Worksheet controls layout *(manageability)*
**Goal:** the worksheet header stopped scaling — Columns/Rows/Filters shelves and the Sort/Chart/
Format controls all shared one wrapping row, and each feature phase (P10 format, P11 types) made it
denser. Restructure so the surface stays legible as P12–P16 add still more controls.
- **Two tiers.** A slim **view bar** on top holds the "how to present" controls — **Chart** type
  (left), **Sort** + **Format** (right) — never data pills, so it can't grow unbounded. Below it, the
  data shelves become **stacked full-width lanes**: `Columns`, `Rows`, `Filters`, each an aligned
  **label column + drop zone** so pills have room and every lane starts at the same x. The **Format**
  panel (P10) opens as a card directly under the view bar.
- **Decision:** chose *stacked shelves + slim view bar* over a right-hand settings rail (which would
  cost ~220px of chart width) and over a grouped single row (still dense). Keeps the chart full-width;
  future view controls extend the view bar / Format card, future data goes to the shelf lanes.
- **Done when:** Columns/Rows/Filters read as three clean lanes; Sort/Chart/Format sit in a separate
  top bar; nothing wraps chaotically; all controls stay on `--ctl-h`, tokens, and `hidden` visibility.
- **Doc:** [modules.md](../../archive/docs/app/modules.md) §7 (worksheet layout), [DESIGN.md](../../archive/DESIGN.md)
  (toolbar alignment, `--ctl-h`).
- **✅ Shipped 2026-08-17:** `renderShelves` builds a `.ws-viewbar` (chart left; sort + format right)
  above a `.ws-shelf-stack` of three `.ws-shelf` grid lanes (`72px 1fr`); `.ws-shelves` is now a flex
  column; the Format panel opens as a `surface-2` card under the view bar. **Deployed live** (verified
  `200` at `https://10.168.49.20/dashboardbuilder/`). *(In-browser render check still pending — no
  headless browser on the host.)*

---
