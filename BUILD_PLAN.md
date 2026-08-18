# Build plan

The path from this knowledge base to a running drag-and-drop dashboard builder. Phases
are ordered so each ends in something demonstrable and the **read-only + credential-safe**
invariants exist from the first ClickHouse call — not bolted on later.

> **Status: P0–P6 done; P7 in progress (Tableau-style worksheet + cross-table joins shipped); P8 ✅ (security re-audit clean, TLS validation safe-by-default [D11](docs/project/decisions.md), a11y pass, test pass; deployed live 2026-08-17 — see [deployment.md](docs/deployment.md)). P9 ✅ (charting-library foundation, [D13](docs/project/decisions.md)); P10 ✅ (chart formatting & encodings); P11 ✅ (chart-type expansion — area/stacked/pie/donut/scatter/combo/KPI+sparkline; **histogram deferred to P12** as it needs a bucketing query shape); P12–P16 = the rest of the *competitive uplift* track ([competitive-analysis.md](docs/project/competitive-analysis.md) quick wins #4–#8). P17 ◑ = worksheet controls layout (usability — two-tier header).**
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
> shelves; fields from **different tables join automatically** along the drawn relationships. Next:
> colour marks + more chart types + click-to-filter actions. The whole UI is verified end-to-end via
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
| P7 ◑ | **Tableau-style worksheet** — drag fields to shelves, charts, **cross-table joins** done; marks + click-to-filter actions next | P5, P6 |
| P8 ✅ | Hardening: security ✅, a11y ✅, tests ✅, deployed live ✅ | all |
| — | *Competitive uplift — visualization & interactivity quick wins (#1–#8, [competitive-analysis.md](docs/project/competitive-analysis.md)). Build on P7; each independently shippable.* | |
| P9 ✅ | **Charting library foundation** (#1) — bar/line re-rendered via self-hosted ECharts, token-themed ([D13](docs/project/decisions.md)) | P7 |
| P10 ✅ | **Chart formatting & encodings** (#2) — number/date formats, axis titles, legend, top-N, data labels, colour-by-category | P9 |
| P11 ✅ | **Chart-type expansion** (#3) — area, stacked/grouped, pie/donut, scatter, KPI+sparkline, combo/dual-axis (histogram → P12) | P9, P10 |
| P12 | **Statistical chart types** (#4) — heatmap, treemap, box plot (new query shapes) | P9 |
| P13 | **Export** (#5) — chart PNG/SVG + bounded CSV of the rows | P9 |
| P14 | **Dashboard filters & parameters** (#6) — cross-widget controls | P7 |
| P15 | **Cross-filtering / click-to-filter** (#7) | P14 |
| P16 | **Hierarchical drill-down** (#8) | P14 |
| — | *Usability — keeps the worksheet manageable as feature phases pile controls onto it.* | |
| P17 ✅ | **Worksheet controls layout** — two-tier header: slim **view bar** (chart/sort/format) + **stacked shelf lanes** (Columns/Rows/Filters); deployed live | P7, P10, P11 |

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

## P13 — Export *(quick win #5)*
**Goal:** export a chart image and the rows behind it.
- Client: **PNG/SVG** from the charting library.
- Server: `GET …/export.csv` for a widget's query — **read-only, bounded `LIMIT`**, streamed;
  identifiers validated; never `SELECT *` without a bound; no secret in output.
- **Done when:** a user exports a chart PNG and a CSV of its rows; the CSV respects the row cap.
- **Guards:** read-only ([D1](docs/project/decisions.md)); never an unbounded export.
- **Doc:** [clickhouse-integration.md](docs/clickhouse-integration.md),
  [modules.md](docs/app/modules.md).

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
