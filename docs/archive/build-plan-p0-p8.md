> **ARCHIVED — frozen record of the P0–P20 build, not maintained.** Paths and links below predate the
> KB restructure and the feature-folder migration and may be stale. Current state: [README](../../README.md);
> what's left to build: [docs/proposals/roadmap.md](../../docs/proposals/roadmap.md).

# Build plan

The path from this knowledge base to a running drag-and-drop dashboard builder. Phases
are ordered so each ends in something demonstrable and the **read-only + credential-safe**
invariants exist from the first ClickHouse call — not bolted on later.

> **Status: P0–P7 done (Tableau-style worksheet + cross-table joins + **colour marks / Color shelf** [D14](../../archive/docs/project/decisions.md) shipped; click-to-filter is tracked as P15); P8 ✅ (security re-audit clean, TLS validation safe-by-default [D11](../../archive/docs/project/decisions.md), a11y pass, test pass; deployed live 2026-08-17 — see [deployment.md](../../archive/docs/deployment.md)). P9 ✅ (charting-library foundation, [D13](../../archive/docs/project/decisions.md)); P10 ✅ (chart formatting & encodings); P11 ✅ (chart-type expansion — area/stacked/pie/donut/scatter/combo/KPI+sparkline; **histogram deferred to P12** as it needs a bucketing query shape); P12 ✅ (statistical charts — heatmap/treemap/histogram/box plot), P13 ✅ (export — PNG/SVG + bounded CSV), P14 ✅ (dashboard filters — `in`/`between` + distinct-values controls, worksheet-scoped; [D15](../../archive/docs/project/decisions.md)); P15 ✅ (click-to-filter — Keep only / Exclude on the worksheet; [D16](../../archive/docs/project/decisions.md)); P16 ✅ (hierarchical drill-down — single-table hierarchy on the bound-param path, breadcrumb + drill-up; [D17](../../archive/docs/project/decisions.md)) — the last *competitive uplift* quick win (#8). P17 ✅ = worksheet controls layout (usability — two-tier header). **[Tableau worksheet parity](build-plan-p18-p25.md#tableau-worksheet-parity--gap-analysis-p18p25): P18 ✅ (Marks card I — Size/Label/Detail/Tooltip + continuous Colour), P19 ✅ (Marks card II — Shape/Path/Angle + Square/Circle/Text marks; [D18](../../archive/docs/project/decisions.md)), P20 ✅ (Pages shelf — step/animate through a dimension). Remaining: P21 Analytics pane, P22 Show Me, P23 worksheet chrome/toolbar, P24 multi-worksheet dashboards, P25 Data-pane authoring.**
> **Structure (2026-08-20):** migrated to **ASP.NET Core MVC in feature folders** — each feature owns its
> controller/view/CSS/JS under `src/DashboardBuilder/Features/<Feature>/`; behaviour unchanged, 100 tests
> green ([D19](../../archive/docs/project/decisions.md)). File paths named in the per-phase notes below are historical
> (`wwwroot/js/x.js` → `Features/<Feature>/x.js`, `wwwroot/css/site.css` → `Features/Core/core.css` +
> per-feature CSS); see [ARCHITECTURE.md](../../archive/ARCHITECTURE.md) for the current map.
>
> The app lives on the build host at
> `10.168.49.20:/unified/user/cj/web_development/prototype/dashboard_builder/`
> ([D9](../../archive/docs/project/decisions.md)) — .NET 10 SDK, `src/DashboardBuilder` + `tests/DashboardBuilder.Tests`.
> `dotnet build` and `dotnet test` (63 passing) are green; a live connect to the ClickHouse on
> `8443` succeeds ([D10](../../archive/docs/project/decisions.md)/[D11](../../archive/docs/project/decisions.md)); the schema
> endpoints list real databases/tables, describe columns, preview/count rows, and run bounded,
> identifier-safe **aggregate + joined chart queries** (group-by + count/sum/avg/min/max + bound
> filters + `JOIN`s), rejecting unknown/hostile identifiers as 400/404. **Structure
> ([D12](../../archive/docs/project/decisions.md)):** one **shared data model** (dragged tables + relationships) +
> **dashboard subtabs**, each a **Tableau-style worksheet** — drag fields onto Columns/Rows/Filters
> shelves; fields from **different tables join automatically** along the drawn relationships, and a
> **Color shelf** splits marks into coloured series ([D14](../../archive/docs/project/decisions.md)). Next:
> click-to-filter actions (P15) + the P12–P16 uplift track. The whole UI is verified end-to-end via
> headless jsdom against the real modules (incl. the cross-table join), plus a live full-stack
> connect; the frontend is client-only apart from the read-only query endpoints.
> The KB ([ARCHITECTURE.md](../../archive/ARCHITECTURE.md), [DESIGN.md](../../archive/DESIGN.md), [CLAUDE.md](../../archive/CLAUDE.md),
> [docs/](../../archive/docs/README.md)) is the spec each phase implements. Keep docs and code in step:
> when a phase changes a decision, update [docs/project/decisions.md](../../archive/docs/project/decisions.md)
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
| P6 ✅ | **Dashboard subtabs** over one shared data model ([D12](../../archive/docs/project/decisions.md)) | P4 |
| P7 ✅ | **Tableau-style worksheet** — drag fields to shelves, charts, **cross-table joins**, **colour marks** ([Color shelf, D14](../../archive/docs/project/decisions.md); deployed live 2026-08-18) done; click-to-filter actions tracked as **P15** | P5, P6 |
| P8 ✅ | Hardening: security ✅, a11y ✅, tests ✅, deployed live ✅ | all |
| — | *Competitive uplift — visualization & interactivity quick wins (#1–#8, [competitive-analysis.md](../../archive/docs/project/competitive-analysis.md)). Build on P7; each independently shippable.* | |
| P9 ✅ | **Charting library foundation** (#1) — bar/line re-rendered via self-hosted ECharts, token-themed ([D13](../../archive/docs/project/decisions.md)) | P7 |
| P10 ✅ | **Chart formatting & encodings** (#2) — number/date formats, axis titles, legend, top-N, data labels, colour-by-category | P9 |
| P11 ✅ | **Chart-type expansion** (#3) — area, stacked/grouped, pie/donut, scatter, KPI+sparkline, combo/dual-axis (histogram → P12) | P9, P10 |
| P12 ✅ | **Statistical chart types** (#4) — heatmap, treemap, histogram, box plot (new query shapes) | P9 |
| P13 ✅ | **Export** (#5) — chart PNG/SVG + bounded CSV of the rows | P9 |
| P14 ✅ | **Dashboard filters & parameters** (#6) — `in`/`between` + distinct-values controls (worksheet-scoped) | P7 |
| P15 ✅ | **Cross-filtering / click-to-filter** (#7) — click a mark → Keep only / Exclude (worksheet-scoped) | P14 |
| P16 ✅ | **Hierarchical drill-down** (#8) | P14 |
| — | *Usability — keeps the worksheet manageable as feature phases pile controls onto it.* | |
| P17 ✅ | **Worksheet controls layout** — two-tier header: slim **view bar** (chart/sort/format) + **stacked shelf lanes** (Columns/Rows/Filters); deployed live | P7, P10, P11 |
| — | *[Tableau worksheet parity](build-plan-p18-p25.md#tableau-worksheet-parity--gap-analysis-p18p25) — gaps found by auditing against Tableau's worksheet workspace anatomy.* | |
| P18 ✅ / P19 ✅ | **Marks card** — Size/Label/Detail/Tooltip/continuous-Colour, then Shape/Path/Angle + mark types | P7 |
| P20 ✅ | **Pages shelf** — page/animate the view through a dimension | P7 |
| P21 | **Analytics pane** — reference/trend/average lines, forecast, totals/subtotals | P7 |
| P22 | **Show Me** — recommend valid viz types + auto-place fields | P11, P18 |
| P23 | **Worksheet chrome & toolbar** — title/caption, field labels, status bar, undo/redo, swap, clear, fit | P7 |
| P24 | **Multi-worksheet dashboards & stories** — compose many worksheets on one canvas | P7, P14 |
| P25 | **Data-pane authoring** — calculated fields, groups, sets, bins, folders, hierarchies | P4 |

---

## P0 — Scaffold & design system
**Goal:** an ASP.NET Core app that serves one empty page in the RED/BLACK/WHITE shell.
- **Build on host `10.168.49.20`, under `/unified/user/cj/web_development/prototype/dashboard_builder/`**
  ([development.md](../../archive/docs/development.md)) — all scaffolding/compilation happens there.
- Create `src/DashboardBuilder` per the [directory map](../../archive/ARCHITECTURE.md#directory-map-target-once-scaffolded)
  (i.e. `/unified/user/cj/web_development/prototype/dashboard_builder/src/DashboardBuilder`).
- `Program.cs`: Razor Page `Index` + session; a stub `/api` group.
- `wwwroot/css/site.css`: the full `:root` **token block** and layout rules from
  [DESIGN.md](../../archive/DESIGN.md) (fixed no-scroll shell, `[hidden]{display:none!important}`,
  sidebar + canvas split).
- **Done when:** `dotnet run` serves the black-sidebar / white-canvas shell; no page scroll.

## P1 — ClickHouse gateway (safety-first)
**Goal:** a read-only gateway and a connection endpoint, with the injection defense in place
**before** any table names flow through it.
- `ClickHouse/ConnectionRegistry.cs` (session-scoped), `ClickHouseGateway.cs`,
  `Identifier.cs` (validate-against-catalog + backtick-quote — [decision D6](../../archive/docs/project/decisions.md)).
- `POST /api/connection` (validate with `SELECT 1`, store), `DELETE /api/connection`.
- **Tests (this is the phase to write them):** `Identifier` unit tests with hostile inputs;
  connection endpoint integration test against a throwaway ClickHouse
  ([development.md](../../archive/docs/development.md)).
- **Done when:** connecting to a real ClickHouse returns success; bad creds fail cleanly
  with no secret in the response/logs; identifier tests pass.
- **Guards:** read-only ([D1](../../archive/docs/project/decisions.md)); credentials server-only
  ([CLAUDE.md](../../archive/CLAUDE.md)).

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
  custom-MIME drag payload ([drag-and-drop.md](../../archive/docs/drag-and-drop.md)).
- **Done when:** selecting a database lists its tables as draggable chips; switching
  databases swaps the list.

## P4 — Drag, drop & entity view *(the heart of the statement)*
**Goal:** drag a table to the canvas and see it as an entity with columns + sample rows.
- `GET …/columns` (`DESCRIBE`) and `GET …/preview?limit=` (`SELECT … LIMIT`) in the gateway,
  with the **type → display-category** mapper ([clickhouse-integration.md](../../archive/docs/clickhouse-integration.md)).
- `wwwroot/js/canvas.js`: drop handling, entity card (head, column rows with type badges,
  internally-scrolling data grid), card movement, loading/failed pills, empty-state toggle.
- **Done when:** dropping a table renders an entity card with real columns and previewed
  rows; large tables preview safely (bounded `LIMIT`); cards can be moved and removed.

## P5 — Relationships
**Goal:** the statement's requirement — every dragged table selects join column(s), and
users draw typed relationships.
- Join-key checkboxes update `entity.joinKeys`; entity with no key can't be a relationship
  endpoint ([data-model.md](../../archive/docs/data-model.md)).
- `wwwroot/js/relations.js`: draw an SVG link between two join-key rows, **cardinality**
  picker (1:1/1:N/N:1/N:M), **shape-coded** endpoints, select-to-edit/delete, keyboard
  fallback.
- **Done when:** a user checks keys on two entities, draws a 1:N link with correct
  one/many markers, edits/deletes it; removing an entity removes its links (with confirm).
- **Reminder:** links are logical declarations, not DB constraints ([D5](../../archive/docs/project/decisions.md)).

## P6 — Subtabs (dashboards)
**Goal:** multiple independent dashboards on the canvas.
- `wwwroot/js/tabs.js`: tab strip, add/rename/close (confirm if non-empty), one
  builder-state slice per tab; active tab `aria-current`.
- **Done when:** adding a tab gives a fresh canvas; each tab keeps its own entities +
  relationships; switching tabs swaps the canvas. (v1 state in-memory —
  [O1](../../archive/docs/project/decisions.md).)

## P7 — Dashboard widgets *(stretch)*
**Goal:** simple KPIs/charts from a tab's data.
- Minimal `Widget` model ([data-model.md](../../archive/docs/data-model.md)); KPI tiles (`--fs-kpi`,
  `--up`/`--down`) first, then a basic chart. Whether joins are executed is
  [open question O4](../../archive/docs/project/decisions.md) — resolve before building join-backed widgets.
- **Done when:** a user adds a KPI tile bound to an entity/column and it renders.

## P8 — Hardening & deploy
**Goal:** production-ready.
- Security pass: re-audit read-only invariant, identifier validation on every path, no
  credential in logs/responses, TLS to ClickHouse.
- Accessibility pass: labels, `aria-live` status, keyboard paths for drag/relate, contrast.
- Test pass: unit + integration coverage per [development.md](../../archive/docs/development.md); manual
  UX script.
- Deploy ([O5](../../archive/docs/project/decisions.md), **resolved**): Kestrel under **systemd**, fronted by
  a **reverse proxy** terminating TLS. On the build host (`10.168.49.20`) this is **Apache httpd**
  on `443`, proxying the path prefix `/dashboardbuilder` → `127.0.0.1:5006`; the app is
  `PathBase`-aware (config key `PathBase`). Reverse proxy + PathBase are already in place and
  verified; the remaining P8 work is the **systemd unit off a `dotnet publish`** under
  `/var/www/webapps/` (currently a transient `dotnet run`). See [development.md](../../archive/docs/development.md).
- **Done when:** the security/a11y checklists pass, `dotnet test` is green, and the app runs
  under systemd behind the reverse proxy.
- **✅ Status (2026-08-17):**
  - **Security pass ✅** — read-only invariant re-audited (zero DDL/DML; every `CommandText` is
    `SELECT`/`SHOW`/`DESCRIBE`); identifiers catalog-validated + backtick-quoted on every
    interpolation path; no credential in logs/responses (password only flows request →
    `ConnectionInfo` → connection string). **TLS to ClickHouse hardened** — certificate
    validation is now safe-by-default with an explicit per-connection opt-in ([D11](../../archive/docs/project/decisions.md)).
  - **Accessibility pass ✅** — audited against [DESIGN.md § Accessibility posture](../../archive/DESIGN.md).
    Fixed the P7 worksheet gaps: a keyboard/non-drag **＋ to add a field to a shelf** (mirrors the
    sidebar chip), **accessible names** on the aggregation/filter-operator/sort-by selects, and
    `aria-pressed` on the chart-type toggle. `prefers-reduced-motion`, `aria-live` status regions,
    `aria-current` tabs, shape-coded cardinality already in place.
  - **Test pass ✅** — `dotnet test` **63 passing** (added the certificate-validation unit tests
    and the `/api/query` without-connection 409). Live-ClickHouse integration + manual UX script
    remain the only non-automatable gaps (no ClickHouse/headless browser on the build host).
  - **Deploy ✅ (shipped 2026-08-17)** — republished (`dotnet publish -c Release`) into
    `/var/www/webapps/dashboardbuilder/` and the **systemd** service restarted; the P8 build now
    serves live behind Apache on `443` ([deployment.md](../../archive/docs/deployment.md)) — verified `200` at
    `https://10.168.49.20/dashboardbuilder/` with the cert opt-in + a11y assets present. ⚠ Behaviour
    change now in effect: the self-signed target ([D11](../../archive/docs/project/decisions.md)) requires the
    "Trust invalid / self-signed certificate" box ticked to connect.

---
