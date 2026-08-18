# Build plan

The path from this knowledge base to a running drag-and-drop dashboard builder. Phases
are ordered so each ends in something demonstrable and the **read-only + credential-safe**
invariants exist from the first ClickHouse call — not bolted on later.

> **Status: P0–P7 done (Tableau-style worksheet + cross-table joins + **colour marks / Color shelf** [D14](docs/project/decisions.md) shipped; click-to-filter is tracked as P15); P8 ✅ (security re-audit clean, TLS validation safe-by-default [D11](docs/project/decisions.md), a11y pass, test pass; deployed live 2026-08-17 — see [deployment.md](docs/deployment.md)). P9 ✅ (charting-library foundation, [D13](docs/project/decisions.md)); P10 ✅ (chart formatting & encodings); P11 ✅ (chart-type expansion — area/stacked/pie/donut/scatter/combo/KPI+sparkline; **histogram deferred to P12** as it needs a bucketing query shape); P12 ✅ (statistical charts — heatmap/treemap/histogram/box plot), P13 ✅ (export — PNG/SVG + bounded CSV), P14 ✅ (dashboard filters — `in`/`between` + distinct-values controls, worksheet-scoped; [D15](docs/project/decisions.md)); P15 ✅ (click-to-filter — Keep only / Exclude on the worksheet; [D16](docs/project/decisions.md)); P16 = the last *competitive uplift* quick win (#8, drill-down). P17 ✅ = worksheet controls layout (usability — two-tier header). **P18–P25 = [Tableau worksheet parity](#tableau-worksheet-parity--gap-analysis-p18p25)** — gaps from auditing against Tableau's worksheet workspace (Marks card, Pages shelf, Analytics pane, Show Me, worksheet chrome/toolbar, multi-worksheet dashboards, Data-pane authoring).**
> The app lives on the build host at
> `10.168.49.20:/unified/user/cj/web_development/prototype/dashboard_builder/`
> ([D9](docs/project/decisions.md)) — .NET 10 SDK, `src/DashboardBuilder` + `tests/DashboardBuilder.Tests`.
> `dotnet build` and `dotnet test` (63 passing) are green; a live connect to the ClickHouse on
> `8443` succeeds ([D10](docs/project/decisions.md)/[D11](docs/project/decisions.md)); the schema
> endpoints list real databases/tables, describe columns, preview/count rows, and run bounded,
> identifier-safe **aggregate + joined chart queries** (group-by + count/sum/avg/min/max + bound
> filters + `JOIN`s), rejecting unknown/hostile identifiers as 400/404. **Structure
> ([D12](docs/project/decisions.md)):** one **shared data model** (dragged tables + relationships) +
> **dashboard subtabs**, each a **Tableau-style worksheet** — drag fields onto Columns/Rows/Filters
> shelves; fields from **different tables join automatically** along the drawn relationships, and a
> **Color shelf** splits marks into coloured series ([D14](docs/project/decisions.md)). Next:
> click-to-filter actions (P15) + the P12–P16 uplift track. The whole UI is verified end-to-end via
> headless jsdom against the real modules (incl. the cross-table join), plus a live full-stack
> connect; the frontend is client-only apart from the read-only query endpoints.
> The KB ([ARCHITECTURE.md](ARCHITECTURE.md), [DESIGN.md](DESIGN.md), [CLAUDE.md](CLAUDE.md),
> [docs/](docs/README.md)) is the spec each phase implements. Keep docs and code in step:
> when a phase changes a decision, update [docs/project/decisions.md](docs/project/decisions.md)
> in the same change.

## Guiding order

1. Prove the **backend + safety** before any UI polish (a leaky/injectable proxy is the
   real risk).
2. Then the **shell + connection** so there's something to look at.
3. Then the **statement's core loop**: browse → drag → entity view → relate → subtabs.
4. Widgets, persistence, hardening last.

## Milestones at a glance

| Phase | Outcome | Depends on |
|---|---|---|
| P0 ✅ | Scaffold + design tokens compile and serve the shell | — |
| P1 ✅ | Safe, read-only ClickHouse gateway + connection endpoints (tested) | P0 |
| P2 ✅ | Connection panel wired end-to-end; connected/failed states | P1 |
| P3 ✅ | Database picker + draggable table list | P2 |
| P4 ✅ | Drag→drop→**entity view** with columns + preview | P3 |
| P5 ✅ | Join-key selection + **relationships** with cardinality | P4 |
| P6 ✅ | **Dashboard subtabs** over one shared data model ([D12](docs/project/decisions.md)) | P4 |
| P7 ✅ | **Tableau-style worksheet** — drag fields to shelves, charts, **cross-table joins**, **colour marks** ([Color shelf, D14](docs/project/decisions.md); deployed live 2026-08-18) done; click-to-filter actions tracked as **P15** | P5, P6 |
| P8 ✅ | Hardening: security ✅, a11y ✅, tests ✅, deployed live ✅ | all |
| — | *Competitive uplift — visualization & interactivity quick wins (#1–#8, [competitive-analysis.md](docs/project/competitive-analysis.md)). Build on P7; each independently shippable.* | |
| P9 ✅ | **Charting library foundation** (#1) — bar/line re-rendered via self-hosted ECharts, token-themed ([D13](docs/project/decisions.md)) | P7 |
| P10 ✅ | **Chart formatting & encodings** (#2) — number/date formats, axis titles, legend, top-N, data labels, colour-by-category | P9 |
| P11 ✅ | **Chart-type expansion** (#3) — area, stacked/grouped, pie/donut, scatter, KPI+sparkline, combo/dual-axis (histogram → P12) | P9, P10 |
| P12 ✅ | **Statistical chart types** (#4) — heatmap, treemap, histogram, box plot (new query shapes) | P9 |
| P13 ✅ | **Export** (#5) — chart PNG/SVG + bounded CSV of the rows | P9 |
| P14 ✅ | **Dashboard filters & parameters** (#6) — `in`/`between` + distinct-values controls (worksheet-scoped) | P7 |
| P15 ✅ | **Cross-filtering / click-to-filter** (#7) — click a mark → Keep only / Exclude (worksheet-scoped) | P14 |
| P16 | **Hierarchical drill-down** (#8) | P14 |
| — | *Usability — keeps the worksheet manageable as feature phases pile controls onto it.* | |
| P17 ✅ | **Worksheet controls layout** — two-tier header: slim **view bar** (chart/sort/format) + **stacked shelf lanes** (Columns/Rows/Filters); deployed live | P7, P10, P11 |
| — | *[Tableau worksheet parity](#tableau-worksheet-parity--gap-analysis-p18p25) — gaps found by auditing against Tableau's worksheet workspace anatomy.* | |
| P18–P19 | **Marks card** — Size/Label/Detail/Tooltip/continuous-Colour, then Shape/Path/Angle + mark types | P7 |
| P20 | **Pages shelf** — page/animate the view through a dimension | P7 |
| P21 | **Analytics pane** — reference/trend/average lines, forecast, totals/subtotals | P7 |
| P22 | **Show Me** — recommend valid viz types + auto-place fields | P11, P18 |
| P23 | **Worksheet chrome & toolbar** — title/caption, field labels, status bar, undo/redo, swap, clear, fit | P7 |
| P24 | **Multi-worksheet dashboards & stories** — compose many worksheets on one canvas | P7, P14 |
| P25 | **Data-pane authoring** — calculated fields, groups, sets, bins, folders, hierarchies | P4 |

---

## P0 — Scaffold & design system
**Goal:** an ASP.NET Core app that serves one empty page in the RED/BLACK/WHITE shell.
- **Build on host `10.168.49.20`, under `/unified/user/cj/web_development/prototype/dashboard_builder/`**
  ([development.md](docs/development.md)) — all scaffolding/compilation happens there.
- Create `src/DashboardBuilder` per the [directory map](ARCHITECTURE.md#directory-map-target-once-scaffolded)
  (i.e. `/unified/user/cj/web_development/prototype/dashboard_builder/src/DashboardBuilder`).
- `Program.cs`: Razor Page `Index` + session; a stub `/api` group.
- `wwwroot/css/site.css`: the full `:root` **token block** and layout rules from
  [DESIGN.md](DESIGN.md) (fixed no-scroll shell, `[hidden]{display:none!important}`,
  sidebar + canvas split).
- **Done when:** `dotnet run` serves the black-sidebar / white-canvas shell; no page scroll.

## P1 — ClickHouse gateway (safety-first)
**Goal:** a read-only gateway and a connection endpoint, with the injection defense in place
**before** any table names flow through it.
- `ClickHouse/ConnectionRegistry.cs` (session-scoped), `ClickHouseGateway.cs`,
  `Identifier.cs` (validate-against-catalog + backtick-quote — [decision D6](docs/project/decisions.md)).
- `POST /api/connection` (validate with `SELECT 1`, store), `DELETE /api/connection`.
- **Tests (this is the phase to write them):** `Identifier` unit tests with hostile inputs;
  connection endpoint integration test against a throwaway ClickHouse
  ([development.md](docs/development.md)).
- **Done when:** connecting to a real ClickHouse returns success; bad creds fail cleanly
  with no secret in the response/logs; identifier tests pass.
- **Guards:** read-only ([D1](docs/project/decisions.md)); credentials server-only
  ([CLAUDE.md](CLAUDE.md)).

## P2 — Connection panel (UI)
**Goal:** the sidebar connection flow, end to end.
- `wwwroot/js/connection.js` + `api.js` + `ui.js` (toast, `hidden` helpers).
- Connection form, **indicator pill** (idle→connecting→connected/failed), and gating of the
  rest of the sidebar/canvas via the `hidden` attribute.
- **Done when:** a user connects from the UI and sees a green connected pill; failure shows a
  red pill + clean message; disconnect resets state.

## P3 — Schema browser
**Goal:** browse databases and tables from the connection.
- `GET /api/databases`, `GET /api/databases/{db}/tables` in the gateway.
- `wwwroot/js/schema.js`: database `<select>`, table list, **draggable chips** with the
  custom-MIME drag payload ([drag-and-drop.md](docs/drag-and-drop.md)).
- **Done when:** selecting a database lists its tables as draggable chips; switching
  databases swaps the list.

## P4 — Drag, drop & entity view *(the heart of the statement)*
**Goal:** drag a table to the canvas and see it as an entity with columns + sample rows.
- `GET …/columns` (`DESCRIBE`) and `GET …/preview?limit=` (`SELECT … LIMIT`) in the gateway,
  with the **type → display-category** mapper ([clickhouse-integration.md](docs/clickhouse-integration.md)).
- `wwwroot/js/canvas.js`: drop handling, entity card (head, column rows with type badges,
  internally-scrolling data grid), card movement, loading/failed pills, empty-state toggle.
- **Done when:** dropping a table renders an entity card with real columns and previewed
  rows; large tables preview safely (bounded `LIMIT`); cards can be moved and removed.

## P5 — Relationships
**Goal:** the statement's requirement — every dragged table selects join column(s), and
users draw typed relationships.
- Join-key checkboxes update `entity.joinKeys`; entity with no key can't be a relationship
  endpoint ([data-model.md](docs/data-model.md)).
- `wwwroot/js/relations.js`: draw an SVG link between two join-key rows, **cardinality**
  picker (1:1/1:N/N:1/N:M), **shape-coded** endpoints, select-to-edit/delete, keyboard
  fallback.
- **Done when:** a user checks keys on two entities, draws a 1:N link with correct
  one/many markers, edits/deletes it; removing an entity removes its links (with confirm).
- **Reminder:** links are logical declarations, not DB constraints ([D5](docs/project/decisions.md)).

## P6 — Subtabs (dashboards)
**Goal:** multiple independent dashboards on the canvas.
- `wwwroot/js/tabs.js`: tab strip, add/rename/close (confirm if non-empty), one
  builder-state slice per tab; active tab `aria-current`.
- **Done when:** adding a tab gives a fresh canvas; each tab keeps its own entities +
  relationships; switching tabs swaps the canvas. (v1 state in-memory —
  [O1](docs/project/decisions.md).)

## P7 — Dashboard widgets *(stretch)*
**Goal:** simple KPIs/charts from a tab's data.
- Minimal `Widget` model ([data-model.md](docs/data-model.md)); KPI tiles (`--fs-kpi`,
  `--up`/`--down`) first, then a basic chart. Whether joins are executed is
  [open question O4](docs/project/decisions.md) — resolve before building join-backed widgets.
- **Done when:** a user adds a KPI tile bound to an entity/column and it renders.

## P8 — Hardening & deploy
**Goal:** production-ready.
- Security pass: re-audit read-only invariant, identifier validation on every path, no
  credential in logs/responses, TLS to ClickHouse.
- Accessibility pass: labels, `aria-live` status, keyboard paths for drag/relate, contrast.
- Test pass: unit + integration coverage per [development.md](docs/development.md); manual
  UX script.
- Deploy ([O5](docs/project/decisions.md), **resolved**): Kestrel under **systemd**, fronted by
  a **reverse proxy** terminating TLS. On the build host (`10.168.49.20`) this is **Apache httpd**
  on `443`, proxying the path prefix `/dashboardbuilder` → `127.0.0.1:5006`; the app is
  `PathBase`-aware (config key `PathBase`). Reverse proxy + PathBase are already in place and
  verified; the remaining P8 work is the **systemd unit off a `dotnet publish`** under
  `/var/www/webapps/` (currently a transient `dotnet run`). See [development.md](docs/development.md).
- **Done when:** the security/a11y checklists pass, `dotnet test` is green, and the app runs
  under systemd behind the reverse proxy.
- **✅ Status (2026-08-17):**
  - **Security pass ✅** — read-only invariant re-audited (zero DDL/DML; every `CommandText` is
    `SELECT`/`SHOW`/`DESCRIBE`); identifiers catalog-validated + backtick-quoted on every
    interpolation path; no credential in logs/responses (password only flows request →
    `ConnectionInfo` → connection string). **TLS to ClickHouse hardened** — certificate
    validation is now safe-by-default with an explicit per-connection opt-in ([D11](docs/project/decisions.md)).
  - **Accessibility pass ✅** — audited against [DESIGN.md § Accessibility posture](DESIGN.md).
    Fixed the P7 worksheet gaps: a keyboard/non-drag **＋ to add a field to a shelf** (mirrors the
    sidebar chip), **accessible names** on the aggregation/filter-operator/sort-by selects, and
    `aria-pressed` on the chart-type toggle. `prefers-reduced-motion`, `aria-live` status regions,
    `aria-current` tabs, shape-coded cardinality already in place.
  - **Test pass ✅** — `dotnet test` **63 passing** (added the certificate-validation unit tests
    and the `/api/query` without-connection 409). Live-ClickHouse integration + manual UX script
    remain the only non-automatable gaps (no ClickHouse/headless browser on the build host).
  - **Deploy ✅ (shipped 2026-08-17)** — republished (`dotnet publish -c Release`) into
    `/var/www/webapps/dashboardbuilder/` and the **systemd** service restarted; the P8 build now
    serves live behind Apache on `443` ([deployment.md](docs/deployment.md)) — verified `200` at
    `https://10.168.49.20/dashboardbuilder/` with the cert opt-in + a11y assets present. ⚠ Behaviour
    change now in effect: the self-signed target ([D11](docs/project/decisions.md)) requires the
    "Trust invalid / self-signed certificate" box ticked to connect.

---

# Competitive uplift — visualization & interactivity (P9–P16)

Turns the **quick wins (#1–#8)** from
[competitive-analysis.md](docs/project/competitive-analysis.md) into phases — the
highest-ROI, lowest-risk distance toward Tableau-class visuals and interactivity. Each
**builds on the P7 worksheet**, is **independently shippable**, and inherits the
[cross-phase definition of done](#cross-phase-definition-of-done) (read-only, identifier
safety, `hidden` visibility, tokens). These are **feature** phases; P8's security/a11y/test
passes apply to each as it lands. Track-wide guards:

- **Self-host the charting library — no CDN.** Vendor it into `wwwroot/` and serve it under
  the app's `no-cache` static policy. A viz library is a **dependency, not an SPA
  framework** — [D4](docs/project/decisions.md) still holds (vanilla-JS modules render into
  `#ws-chart`).
- **Chart colors from design tokens** ([CLAUDE.md](CLAUDE.md) rule 6, [DESIGN.md](DESIGN.md)):
  a token-derived, WCAG-AA categorical palette; never encode by color alone.
- **Every new query stays read-only, bounded, and identifier-safe** — new filters/drill
  values are **bound parameters**, never interpolated ([D6](docs/project/decisions.md));
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
- **Doc:** [frontend-patterns.md](docs/frontend-patterns.md) (charting adapter),
  [DESIGN.md](DESIGN.md) (chart palette tokens).
- **✅ Shipped:** ECharts vendored at `wwwroot/js/vendor/echarts.min.js` (SVG renderer, loaded
  before the module graph); `wwwroot/js/chart.js` adapter maps results → option, themed from
  `--chart-*` tokens; `dashboards.js` routes **bar/line** to it and keeps **table/KPI** as
  native DOM. Build clean + 56 tests green; page and the vendored lib serve `200` (no-cache)
  via `https://10.168.49.20/dashboardbuilder/` ([D13](docs/project/decisions.md)). The
  hand-rolled `.chart-bar*/.chart-line` code + CSS were removed. *Pending a live in-browser
  render check against real data (no headless browser on the host to automate it).*

## P10 — Chart formatting & encodings *(quick win #2)*
**Goal:** per-chart formatting without touching the query.
- Number/date formats, axis titles, legend toggle/position, sort order, **top-N**, data
  labels, **color-by-dimension** — stored on the widget config (in-memory per
  [O1](docs/project/decisions.md)).
- **Done when:** a user formats a chart (e.g. currency axis, top-10, sorted desc, colored by
  category) and it renders and persists for the session.
- **Doc:** [modules.md](docs/app/modules.md) (worksheet formatting).
- **✅ Shipped 2026-08-17:** a collapsible **Format panel** (`formatPanel` in `dashboards.js`, toggled
  from the shelves row) drives `sheet.format` ([store.js](../src/DashboardBuilder/wwwroot/js/store.js)
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
- **Doc:** [modules.md](docs/app/modules.md) (chart types), [data-model.md](docs/data-model.md)
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
- **Doc:** [clickhouse-integration.md](docs/clickhouse-integration.md) (2-dim + quantile
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
- **Guards:** read-only ([D1](docs/project/decisions.md)); never an unbounded export.
- **Doc:** [clickhouse-integration.md](docs/clickhouse-integration.md),
  [modules.md](docs/app/modules.md).
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
  parameters** (reuse the existing aggregate/query param path — [D6](docs/project/decisions.md)).
- **Done when:** setting a dashboard date range / category re-queries and updates every
  applicable widget; a control on a field absent from a widget's tables is a clear no-op;
  filters are scoped to their dashboard.
- **Doc:** [data-model.md](docs/data-model.md) (dashboard filter state),
  [modules.md](docs/app/modules.md), [clickhouse-integration.md](docs/clickhouse-integration.md)
  (bounded distinct-values query).
- **✅ Shipped 2026-08-18 (worksheet-scoped):** since a dashboard is still **one worksheet** (multi-
  worksheet composition is P24), P14 landed as **richer Filters-shelf controls** that all bind as typed
  parameters ([D6](docs/project/decisions.md)). New ops **`in`** (a multi-select populated from a
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
- **Doc:** [modules.md](docs/app/modules.md) (interactions),
  [frontend-patterns.md](docs/frontend-patterns.md) (event bus).
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
- **Doc:** [data-model.md](docs/data-model.md) (hierarchy metadata),
  [modules.md](docs/app/modules.md).

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
- **Doc:** [modules.md](docs/app/modules.md) §7 (worksheet layout), [DESIGN.md](DESIGN.md)
  (toolbar alignment, `--ctl-h`).
- **✅ Shipped 2026-08-17:** `renderShelves` builds a `.ws-viewbar` (chart left; sort + format right)
  above a `.ws-shelf-stack` of three `.ws-shelf` grid lanes (`72px 1fr`); `.ws-shelves` is now a flex
  column; the Format panel opens as a `surface-2` card under the view bar. **Deployed live** (verified
  `200` at `https://10.168.49.20/dashboardbuilder/`). *(In-browser render check still pending — no
  headless browser on the host.)*

---

# Tableau worksheet parity — gap analysis (P18–P25)

Verified the builder's worksheet against Tableau Desktop's **worksheet workspace** anatomy
([help.tableau.com › environment_workspace](https://help.tableau.com/current/pro/desktop/en-us/environment_workspace.htm#workspace-area)):
the numbered workspace parts (Data pane, Analytics pane, Columns/Rows/Pages/Filters shelves, the
**Marks card** + its encoding targets, Show Me, legends, sheet tabs incl. worksheet/dashboard/story,
title/caption, field labels, toolbar, status bar). Below: what we **have**, what is **already on the
roadmap** (P12–P16), and the **still-missing** parts, which become **P18–P25**. Same guards as the
uplift track: **read-only, bounded, identifier-safe** ([D1](docs/project/decisions.md)/[D6](docs/project/decisions.md)),
`hidden` visibility, tokens; each phase independently shippable.

### Coverage matrix

| Tableau workspace part | Builder today | Verdict |
|---|---|---|
| **Data pane** — fields split Dimensions/Measures | field pane per model table ✓ | **Have** (authoring extras missing → P25) |
| **Columns / Rows shelves** | ✓ multi-pill, role-convert, agg picker | **Have** |
| **Filters shelf** | op + typed value pill | **Partial** — no range / relative-date / top-N / multi-select **list** filter; interactive **filter cards** = **P14** |
| **Marks card — Color** | Color shelf (P7, discrete) + colour-by-category (P10) | **Have (discrete)**; continuous colour (measure→gradient), opacity/border → **P18** |
| **Marks card — Size** | — | **Missing → P18** |
| **Marks card — Label / Text** | data-labels *toggle* (format) | **Partial** — no field-on-Label, no Text mark → **P18** |
| **Marks card — Detail** | — | **Missing → P18** |
| **Marks card — Tooltip** | ECharts default tooltip | **Partial** — no custom / field-driven tooltip → **P18** |
| **Marks card — Shape** | — | **Missing → P19** |
| **Marks card — Path** | — | **Missing → P19** |
| **Marks card — Angle** | pie maps measure→slice implicitly | **Covered (pie)** |
| **Mark-type dropdown** | chart-type dropdown (bar/stacked/line/area/pie/donut/scatter/combo/KPI/table) | **Partial** — no Square/Circle/Text/Gantt/Density mark types → **P19**; Map **out of scope** (no geo in v1) |
| **Pages shelf** | — | **Missing → P20** |
| **Analytics pane** — reference/constant/average lines & bands, trend line, forecast, totals/subtotals | — | **Missing → P21** (box plot / statistical marks already = **P12**) |
| **Show Me** | chart-type dropdown + invalid-mapping hints | **Partial** — no recommend-and-auto-place panel → **P22** |
| **Legends** (colour/size/shape) | ECharts colour legend + position toggle | **Partial** — display-only; size/shape legends need P18/P19; interactive **highlight/​filter on legend** = **P15** |
| **Worksheet Title / Caption** | — | **Missing → P23** |
| **Field labels** (row/column) | crosstab corner + axis titles | **Partial → P23** |
| **Toolbar** — undo/redo, swap rows↔cols, clear sheet, fit, highlight | scattered inline controls only | **Missing → P23** |
| **Status bar** — marks count, rows×cols, aggregate of selection | — | **Missing → P23** |
| **Sheet tabs** — worksheet **/ dashboard / story** | Data-Model tab + subtabs, **each = one worksheet** | **Partial** — no multi-worksheet **dashboard** composition, no **story** → **P24** |
| **Drill-down / hierarchies** | — | **= P16** |
| Side bar / Data Source / Start page | connection sidebar + schema browser | **Have (equivalent)** |

> **Biggest architectural gap:** in Tableau a **dashboard** *composes several worksheets* on one canvas;
> in the builder a "dashboard" subtab **is a single worksheet** (one `sheet`, one `#ws-chart`). True
> multi-view dashboards are **P24** — the others (P18–P23, P25) enrich the single worksheet.

### New phases at a glance

| Phase | Outcome | Depends on |
|---|---|---|
| P18 | **Marks card I** — Size, Label/Text, Detail, Tooltip; continuous Color (generalises the P7 Color shelf) | P7 |
| P19 | **Marks card II** — Shape, Path, Angle + mark-type expansion (square/circle/text/gantt/density) | P18 |
| P20 | **Pages shelf** — page/animate the view through a dimension | P7 |
| P21 | **Analytics pane** — reference/average/constant lines & bands, trend line, forecast, totals/subtotals | P7 |
| P22 | **Show Me** — recommend valid viz types for the current fields & auto-place | P11, P18 |
| P23 | **Worksheet chrome & toolbar** — Title, Caption, field labels, status bar; undo/redo, swap rows↔cols, clear, fit, highlight | P7 |
| P24 | **Multi-worksheet dashboards & stories** — compose many worksheets/KPIs on one canvas + story points | P7, P14 |
| P25 | **Data-pane authoring** — calculated fields, groups, sets, bins, folders, hierarchies | P4 |

---

## P18 — Marks card I: Size · Label · Detail · Tooltip (+ continuous Colour)
**Goal:** turn the P7 Color shelf into a proper **Marks card** — a cluster of encoding targets that
map a field onto a mark property, all on the **existing bounded aggregate/join query**.
- **Size** — a measure → mark size (bubble scatter, variable bar/line width); a size legend.
- **Label / Text** — drop a **field** on Label (not just the P10 on/off toggle); a **Text/table mark**
  writing the field value into the mark.
- **Detail** — a dimension that **adds group-by granularity without a visual channel** (like Color's
  query treatment, minus the colour) — more marks, same encodings.
- **Tooltip** — a **custom tooltip** template with chosen fields (ECharts formatter driven by the
  sheet's tooltip field list), replacing the fixed default.
- **Continuous Colour** — a **measure** on Colour → a sequential token-derived gradient (today Colour
  is discrete only); keep a colour legend, never colour-alone.
- **Done when:** a bubble chart (Size = measure), a labelled chart (Label = field), an added-detail
  chart, and a custom tooltip each render from a valid mapping; invalid mappings show a **hint**, not
  an error (P11 rule). Marks-card encodings persist per session ([O1](docs/project/decisions.md)).
- **Guards:** Size/Detail that add a group-by go through the **same validated, bounded** query path as
  Color ([D14](docs/project/decisions.md)); no new query shape beyond an extra dimension/measure.
- **Doc:** [modules.md](docs/app/modules.md) §7 (Marks card), [data-model.md](docs/data-model.md)
  (encoding model), [frontend-patterns.md](docs/frontend-patterns.md) (chart adapter).

## P19 — Marks card II: Shape · Path · Angle + mark types
**Goal:** the remaining Marks-card encodings and mark vocabulary.
- **Shape** — a dimension → distinct point shapes (scatter / shape charts); a shape legend
  (shape is a second non-colour channel, so identity survives greyscale).
- **Path** — a field that **orders** the vertices of a line/polygon mark (connected scatter, custom
  line order) rather than the default category order.
- **Angle** — explicit for pie (already implicit); expose it where a radial mark needs it.
- **Mark types** — extend the mark-type dropdown with **Square, Circle, Text, Gantt Bar, Density**
  (heatmap-ish) marks. **Map is out of scope** (no geospatial in v1 — record in
  [decisions.md](docs/project/decisions.md)).
- **Done when:** shape-encoded scatter, a path-ordered line, and at least the Square/Circle/Text marks
  render; each unmet mapping shows a hint.
- **Doc:** [modules.md](docs/app/modules.md) §7, [DESIGN.md](DESIGN.md) (shape vocabulary / a11y —
  never colour-alone).

## P20 — Pages shelf
**Goal:** Tableau's **Pages** — step or animate the view through the members of a dimension.
- A **Pages** shelf takes one dimension; a page **control** (play/step/loop + current-member label)
  filters the view to one member at a time via the existing **bound-parameter** filter path.
- **Done when:** dropping a dimension on Pages yields a control that pages through its members,
  re-rendering the chart per member; respects `prefers-reduced-motion` (no autoplay when set).
- **Guards:** each page is one **bound** filter value ([D6](docs/project/decisions.md)); members list
  comes from a **bounded distinct-values** query (shared with P14).
- **Doc:** [modules.md](docs/app/modules.md) §7, [clickhouse-integration.md](docs/clickhouse-integration.md).

## P21 — Analytics pane
**Goal:** the second side-bar tab — drop-on analytics that overlay the view.
- **Reference lines / bands** (constant, or from an aggregate: average/median/min/max), **constant
  line**, **average line**; **trend line** (linear/log/poly, computed client-side over returned rows),
  **forecast** (simple), and **Totals** — grand totals + **subtotals** in the crosstab.
- **Done when:** a user adds an average reference line, a linear trend line, and column grand totals,
  and they render/update with the query; all overlays are **client-side over the bounded result**
  (no new server aggregate beyond optional totals rows).
- **Guards:** totals stay within the read-only aggregate path; no unbounded scans.
- **Doc:** [modules.md](docs/app/modules.md) §7 (analytics overlays), [DESIGN.md](DESIGN.md)
  (reference-line styling tokens).

## P22 — Show Me
**Goal:** Tableau's **Show Me** — recommend the view types that fit the fields in play and build one
in a click.
- A **Show Me** panel lists chart types with the **valid ones enabled** for the current
  dimension/measure selection (reusing `chartIssue()` logic) and, on pick, **auto-places** fields on
  the right shelves/encodings.
- **Done when:** with fields selected, Show Me highlights the applicable types and one click produces
  the chart with sensible shelf placement; inapplicable types are greyed with the reason.
- **Doc:** [modules.md](docs/app/modules.md) §7 (Show Me), [frontend-patterns.md](docs/frontend-patterns.md).

## P23 — Worksheet chrome & toolbar
**Goal:** the worksheet's framing UI and editing actions.
- **Title** (editable, defaulting to the sheet name) and **Caption** (auto-generated summary,
  editable); **field labels** for rows/columns in the view; a **status bar** (marks count, rows×cols,
  aggregate of the current selection).
- **Toolbar** actions: **undo/redo** (a worksheet-state history stack), **swap rows↔columns**,
  **clear sheet**, **fit** (standard / fit-width / fit-height / entire view), **highlight**.
- **Done when:** title/caption render and edit; undo/redo traverse shelf/format changes; swap
  transposes Columns↔Rows; clear empties the sheet (with confirm if non-empty); fit modes change the
  chart sizing.
- **Doc:** [modules.md](docs/app/modules.md) §7, [DESIGN.md](DESIGN.md) (toolbar, `--ctl-h`).

## P24 — Multi-worksheet dashboards & stories
**Goal:** close the **biggest** architectural gap — a Tableau **dashboard** *composes several
worksheets*; today a subtab is a single worksheet.
- Introduce a **dashboard-composition** view: a grid/free canvas that hosts **multiple worksheet
  widgets** (charts, crosstabs, KPI tiles) with per-widget sizing/placement, sharing the one data
  model. Optionally **story** points (ordered, captioned snapshots). Revisit
  [O1](docs/project/decisions.md) persistence and [O3](docs/project/decisions.md) widget richness.
- **Done when:** a user places ≥2 worksheets on one dashboard canvas, arranges/resizes them, and each
  re-queries independently; a story sequences several views with captions.
- **Depends on:** P14 (dashboard-level filters make multi-widget composition worthwhile).
- **Doc:** [ARCHITECTURE.md](ARCHITECTURE.md), [data-model.md](docs/data-model.md) (dashboard vs
  worksheet), [modules.md](docs/app/modules.md).

## P25 — Data-pane authoring
**Goal:** author derived fields in the Data pane, like Tableau.
- **Calculated fields** (a computed **SELECT expression**), **groups** (map members → a label),
  **sets** (a named member subset), **bins** (numeric bucketing — overlaps the **P12** histogram
  shape), **folders**, and **hierarchies** (ordered levels — the drill metadata of **P16**).
- **Done when:** a user defines a calculated field and uses it on a shelf; a group and a bin render;
  hierarchy/drill reuses P16.
- **Guards (critical):** calculated fields are **read-only** ([D1](docs/project/decisions.md)) and
  **injection-safe** — evaluate only a **whitelisted set of scalar functions/operators**, forbid
  subqueries, semicolons, and any DDL/DML; validate every identifier against the live catalog
  ([D6](docs/project/decisions.md)). This is the one phase that lets user text into a SQL *expression*,
  so treat the whitelist as a golden-rule surface. Record the approach in
  [decisions.md](docs/project/decisions.md).
- **Doc:** [clickhouse-integration.md](docs/clickhouse-integration.md) (calc-expression whitelist),
  [data-model.md](docs/data-model.md).

---

## Cross-phase definition of done
Every phase closes only when: read-only invariant intact; no credential leak; identifiers
validated + quoted where interpolated; visibility via `hidden`; colors via tokens; the
touched KB doc updated in the same change ([CLAUDE.md](CLAUDE.md#definition-of-done-for-a-change)).

## Open questions to resolve along the way
[O1](docs/project/decisions.md) persistence (before P6 ships beyond in-memory) ·
[O2](docs/project/decisions.md) saved connections · [O3](docs/project/decisions.md) widget
richness (before P7) · [O4](docs/project/decisions.md) execute joins? (before join-backed
widgets) · [O5](docs/project/decisions.md) prod proxy/TLS (**resolved** — Apache httpd + PathBase on `10.168.49.20`).

## Suggested first step
Start **P0 + P1 together**: scaffold the project and stand up the safe gateway with the
identifier tests. That front-loads the one genuinely risky part (SQL-identifier safety) and
gives every later phase a trustworthy foundation. **Do not** begin until you're ready to
build — this plan and the KB are the current deliverable.
