# Proposal: Tableau-benchmarked analytics for the Dashboard Builder

**Document type:** Product and technical proposal
**Basis:** Alexander Loth, *Visual Analytics with Tableau* (Wiley, 2019), as itemised in [`tableau-features.md`](tableau-features.md) — **229 in-scope requirements** with stable `TNN-NN` IDs
**Status:** Proposed. Nothing here is built until a plan is approved; current behaviour is documented under [`docs/features/`](../features/worksheet.md).
**Updated:** 28 October 2026

---

## 1. Executive proposal

Grow the existing **Dashboard Builder** toward the Tableau-style workflow in the inventory, **on its current stack and under its current rules**:

1. **Connect** — a session-scoped, read-only connection to the user's ClickHouse server.
2. **Model** — drag tables onto the Data Model, declare relationships, rename/alias/hide/group fields.
3. **Explore and calculate** — shelves, marks, filters, aggregations, calculated fields, parameters, table calculations and, later, level-of-detail (LOD) expressions.
4. **Visualize and analyze** — charts, Show Me, reference lines, trend, forecast, clustering, maps.
5. **Compose** — dashboards with tiled/floating layout and cross-sheet actions; stories later.
6. **Keep and show** — the browser holds the workbook; Export/Import is the share format; presentation mode and PDF/PNG/CSV export are the outputs.

**Core recommendation:** extend the calculation and query path first (§3.4). A richer editor over a query layer that returns wrong numbers is not an improvement.

The book documents **Tableau circa 2019 (Desktop 2019.1)**. "Coverage" here means the *workflow* exists; it does not mean Tableau's expression grammar, optimiser, rendering or forecast numbers are reproduced.

### 1.1 Who it is for

One person at a time. There is no author/viewer split, no sign-in and no sharing service.

| Audience | Workflow | Success |
|---|---|---|
| Analyst with ClickHouse access | Connect → model tables → build worksheets → compose dashboards | Answers questions without writing SQL or frontend code. |
| Same analyst, later | Re-open an exported workbook, reconnect, refresh | The workbook restores exactly; no data or credentials were stored in it. |

The target workload is large ClickHouse tables (the existing design scenario is hundreds of millions of rows a month). Queries run at an **aggregated grain on the server**; the browser only ever receives bounded results.

### 1.2 Scope boundary

- **Single-user, browser-held state.** The workbook lives in `localStorage` and in exported files ([D21](../reference/decisions.md#d21--workbooks-persist-in-the-browser-not-on-the-server)).
- **ClickHouse only, read-only.** No other database engine, no file uploads, no writes ([golden rules](../conventions/golden-rules.md) 1–4).
- **No application database, accounts, publication, extracts or saved prep flows.** The 60 requirements that needed them are listed in [`tableau-features.md` § Removed](tableau-features-excluded.md#removed-server-side-features).
- **Self-hosted, framework-free frontend, no CDN** (golden rule 10). New libraries must be vendored; each needs a written reason.
- **Not a Tableau clone:** no `.twb/.twbx/.hyper` compatibility, no Tableau branding, no pixel-identical UI, no claim of identical regression/forecast output.

---

## 2. Scope and delivery policy

| Priority | Count | Meaning |
|---|---:|---|
| **P0** | **44** | Essential authoring and trustworthy queries. |
| **P1** | **107** | Core self-service analytics breadth; ship in small increments. |
| **P2** | **67** | Advanced: LOD, geography, statistics, richer dashboards. |
| **P3** | **10** | Optional or thinly specified; only with a stated use case. |
| **Document only** | **1** | T02-37, source-side indexing advice — documentation, not a feature. |

Priorities are the inventory's. They are a starting order, not a plan. The [gap analysis](gap-analysis.md) marks each of the 229 IDs as built, partial or open against the running app (68 / 52 / 109; 18 of the 44 P0 items not yet built) and the order of what remains follows its dependencies (§9).

### 2.1 Coverage by subsystem

| Subsystem | Inventory | Where it lands |
|---|---|---|
| Workspace and workbooks | `T01` (28) | `Features/Core`, `Features/Workbook`, `Features/Dashboard` |
| Data source and model | `T02` (26) | `Features/Schema`, `Canvas`, `Relations`; `ClickHouse/ClickHouseGateway.cs` |
| Charts and encodings | `T03` (34) | `Features/Dashboard/chart.js`, `dashboards.js` |
| Aggregations, calculations, parameters | `T04` (33) | Expression compiler in `ClickHouse/`; editor in `Features/Dashboard` |
| Table calculations and LOD | `T05` (27) | Client post-aggregate engine; LOD compiled to SQL |
| Maps | `T06` (21) | New `Features/Maps` module; bundled static geography |
| Statistics and forecasting | `T07` (26) | Client modules on bounded results |
| Dashboards and actions | `T08` (30) | `Features/Dashboard` (P24 snap-grid), `Tabs` |
| Consumption and ask-data | `T09` (4) | `Features/Dashboard`, later a local grammar parser |

---

## 3. Functional specification

### 3.1 Workspace and authoring (T01)

Keep the current fixed shell: sidebar of fields, shelves and encodings above a canvas, tabs for the Data Model and one worksheet per dashboard tab ([worksheet.md](../features/worksheet.md)).

Interaction contract (new work must respect it):
- Dropping a measure on a shelf selects `SUM` unless overridden; dropping a dimension changes grouping.
- The aggregation can be changed from the pill without touching the source.
- Switching chart type keeps compatible bindings and says why an incompatible one was dropped.
- A workbook stores **specifications and metadata**, never data and never executable code.
- Every state-changing edit is undoable; the aggregation grain and active filters are always visible in plain words.
- Everything reachable by drag-and-drop has a keyboard path.

### 3.2 Data source and model (T02)

One input path: **ClickHouse tables**.

- Schema browser → table chips → Data Model → logical relationships with cardinality ([relationships.md](../features/relationships.md)). Inner and left joins today; right and full joins, compound and non-equality predicates and join-key suggestion are inventory items to add, each compiled through the existing identifier validation.
- **Join safety:** show matched/unmatched estimates and warn on fan-out before a join is used by a worksheet (cardinality is the user's declaration, not a database fact — rule 5).
- Field metadata (alias, hidden, group, split, type cast) lives in the workbook's `fields` map and is applied when queries are built; the source tables are never altered.
- **Unions** are compiled to `UNION ALL` with explicit column alignment. **Unpivot** and **split** compile to ClickHouse array/string functions.
- Live only. Show the time of the last query and the state of a failed one; never present stale numbers as current.

Invariants:
1. Source data is never modified; every statement is `SELECT`/`SHOW`/`DESCRIBE`.
2. Null, empty string, zero, invalid date and non-finite number stay distinct values.
3. A worksheet references tables and columns by catalog identity; a column that disappears is reported, not silently dropped.

### 3.3 Charts and encodings (T03)

The worksheet `sheet` object ([data-model.md](../reference/data-model.md#worksheet-sheet)) stays the single source of truth for editing, saving, rendering and export. Charts render through the existing ECharts adapter; do not let ECharts option objects leak into the saved workbook.

Chart families to cover: bar, line (straight/step/jump), scatter, text crosstab, highlight table, circle heatmap, pie, bullet, waterfall/Gantt, bump, dual-axis, side-by-side measures, maps and statistical views (T03-02 … T03-16, T05-19, T06, T07).

**Show Me** is a deterministic compatibility table, not generative AI; unavailable options say why. Visualisation rules: label the aggregation, keep legends consistent, use palettes that survive colour-blindness and greyscale (golden rule 9), and cap or aggregate marks (charts ≤ 5000 groups, [D24](../reference/decisions.md#d24--showing-all-data-bounded-requests-paging-other-date-grouping)). Source rows are reached through an explicit drill-to-detail, never by loading everything.

### 3.4 Calculation and query engine (T04, T05)

The differentiator and the highest correctness risk. A browser-side typed AST is re-validated by the server and compiled to ClickHouse SQL — never formula text interpolated into SQL — and table calculations run in the browser on the bounded result. Full design: [calculation-engine.md](calculation-engine.md).

### 3.5 Data shaping without prep flows (T02-26 … T02-34, T04)

The Prep-style flow builder is out of scope: it needs saved flows and materialised output. The cleaning actions that do **not** need materialisation stay, as query-time transformations in the model: rename, alias, group, trim, recode, split, type cast, date construction and replace-null, each stored in `fields` or as a calculated field. A profile card (distinct values, null share, frequency) per field is a bounded `SELECT` and may be added as a read-only inspector.

### 3.6 Advanced analytics (T07)

Everything runs in the browser on the bounded aggregated result; there is no external statistical runtime and no scripting editor.

- **Reference analytics (P1/P2):** constant, average and reference lines; bands; distribution and box plot; subtotals and grand totals; median/average with CI.
- **Regression (P2/P3):** linear first, then logarithmic, exponential, polynomial, power; show the formula, R², p-value and sample size; hide models the data can't support.
- **Forecast (P2):** exponential smoothing with adjustable horizon, optional seasonality, incomplete-period and missing-value policy, interval band, model description. Distinguish prediction from confidence intervals.
- **K-means (P2):** chosen features, fixed or suggested k, **seeded** for reproducibility, optional standardisation, cluster label saved as a dimension in the workbook.

New numeric code goes in pure JS modules under `tests/js/` coverage so it can be tested with `node --test` against fixtures.

### 3.7 Maps (T06)

- Bundle country and administrative boundaries and a place-name reference as **static, licensed, same-origin assets**; no tile or geocoding service is ever called.
- A location that isn't in the reference needs explicit latitude/longitude or uploaded GeoJSON — **never guess coordinates**; unknown locations are flagged.
- GeoJSON is read **in the browser** from a user-chosen file and held in the workbook state only if small enough to pass the workbook size limits; Shapefile/KML are P3.
- Layers: symbol, filled, density, pie-on-map, dual-axis combinations, theme, pan/zoom, chart-in-tooltip.

### 3.8 Dashboards, actions and stories (T08)

- Layout: tiled by default, floating where needed, fixed/automatic/range sizing, phone/tablet/desktop preview, text, image, blank and navigation objects, legends and filter cards. P24 (snap-grid, multi-worksheet dashboards, workbook v2) is the foundation; build on it.
- **Actions** form an explicit graph:

```text
Source sheet event ──> action type ──> target sheet(s)
 select / hover / menu    filter · highlight · navigate · go to sheet
 multi-select             match by chosen field(s); clear: all / none / keep
```

A selected mark filters targets by its **group keys**, bound as typed values (rule 3), never by display labels. Cross-sheet field mappings are explicit when two sheets use different tables.
- **Stories (P2)** are ordered steps with captions and back/next. Set actions stay P3.

### 3.9 Keep, export and present (T01-24, T01-28/29, T09)

- **Save/open** is the browser workbook plus Export/Import ([workbook.md](../features/workbook.md)). A file holds definitions only, never data and never credentials.
- **Export:** PNG (exists), CSV (≤ 100,000 rows, exists), PDF (new). Neutralise spreadsheet formula injection in CSV cells.
- **Presentation mode** and a phone-sized read layout cover "viewing" for the one user and anyone they show the screen to.
- **Ask-data (P3):** an explainable local grammar (`sum of Sales by Region for 2025`) that shows its parse before running. No external model.

---

## 4. Architecture

No change of style: one ASP.NET Core MVC app (Kestrel) serves the single page plus a read-only JSON API; the browser holds all builder state ([ARCHITECTURE.md](../../ARCHITECTURE.md)).

| Layer | Technology (unchanged) | New work lands in |
|---|---|---|
| Frontend | Vanilla JS ES modules, plain CSS tokens, no build step | A feature folder per subsystem (`Features/<Name>/`) |
| Charts | ECharts behind the existing adapter | `chart.js`; chart specs stay in `sheet` |
| API | ASP.NET Core `[ApiController]`s on `ApiControllerBase` | `Features/Dashboard/QueryController.cs` and siblings |
| ClickHouse access | `ClickHouseGateway` (all SQL), `Identifier`, `RequestValidation` | The expression compiler beside the Gateway |
| State | `Core/store.js` + workbook JSON in `localStorage`/files | `Core/sheet-schema.js`, `Workbook/workbook-model.js` |
| Tests | xUnit (`tests/DashboardBuilder.Tests`) and `node --test` (`tests/js`) | Fixture-driven golden tests |

### 4.1 Query path

Browser spec → client `validate.js` → `POST /api/query` → server `RequestRules` (authoritative) → identifier validation against the live catalog → bound, `LIMIT`ed `SELECT` with `readonly=2` and the time limit → bounded `QueryResult` → client-side table calculations, analytics and rendering. The short-lived server result cache ([D25](../reference/decisions.md#d25--a-short-lived-server-result-cache-and-approximate-mode)) stays keyed by the full request, so a changed filter or parameter cannot reuse an old result.

**Why not load tables into the browser?** Large tables would freeze it. Only bounded aggregates, capped preview rows and paged drill-through leave the server.

### 4.2 Keeping the server and client in step

Every new input has a limit in `ClickHouse/RequestValidation.cs` **and** a mirror in `Features/Core/validate.js` ([api.md § Limits](../reference/api.md#limits)). Out-of-range input is a 400, never clamped. New workbook fields are validated by `sheet-schema.js` on open and reset to defaults with a report.

---

## 5. Persistence

There is no database. The workbook JSON ([data-model.md § Workbook file](../reference/data-model.md#workbook-file)) is the only durable artefact; this proposal adds fields to it under a new `version` with an upgrade path from the old one.

Candidate additions (each needs a schema, limits and migration, decided in the plan):

| Field | Holds |
|---|---|
| `calculations` | named calculated fields: `{ id, name, formula }` — formula **text**; the tree is re-derived on open ([calculation-engine.md](calculation-engine.md#persistence)) |
| `groups`, `hierarchies`, `sets` | dimension groups, drill hierarchies (T02-30, T03-29) |
| `actions` | dashboard action graph (§3.8) |
| `stories` | ordered steps |
| `clusters` | model settings + seed (labels are recomputed, not stored) |

A stored calculation: `{ "id": "c1", "name": "Success rate", "formula": "SUM([calls.success]) / SUM([calls.total])" }`.

Detect and report a stored reference to a column that no longer exists on open.

---

## 6. API changes (suggested first iteration)

Existing endpoints and limits are in [api.md](../reference/api.md). The proposal adds only **read-only** routes:

| Endpoint | Purpose |
|---|---|
| `POST /api/query` (extended) | Accept calculation trees (the server validates them with the query; there is no separate validate endpoint), LOD terms, extra join types and a `datePart`/function whitelist; same limits, same response shape. |
| `POST /api/databases/{db}/tables/{table}/profile` | Bounded per-column profile: distinct count, null share, top values (§3.5). |

No endpoint accepts SQL text. No endpoint writes. Credentials never appear in a request, response, log, URL or workbook (rule 4).

---

## 7. Journeys and acceptance scenarios

**A — Dashboard from ClickHouse tables (P0).** Connect → drag two tables, declare the relationship → build a bar and a line sheet with aggregates and filters → edit tooltip, labels and colours → compose a dashboard → click a mark in one sheet to filter the other (both sheets include the clicked field's table; a sheet that doesn't shows a note instead, [P24c](p24c-cross-widget-filtering.md)) → reload → Export → Import into a fresh browser and reconnect. *Acceptance:* every displayed aggregate equals the fixture's documented totals, including null handling and duplicated source rows; the imported workbook is identical.

**B — Date and KPI analysis (P1).** Date hierarchy at month/day/hour; `SUM(success)/SUM(total)`; target line from a parameter. *Acceptance:* changing a date filter or parameter only re-queries affected sheets; the weighted rate is a ratio of sums.

**C — Joining and shaping (P1).** Join Orders, People and Returns; alias, group, split and recode fields; union two region tables. *Acceptance:* left joins keep unmatched left rows; union column alignment is explicit; source tables are untouched.

**D — Statistics (P2).** Forecast with interval band and model description; k-means with a seed; regression only where the data supports it. *Acceptance:* identical settings and data give identical output; missing-value behaviour is documented.

**E — Map dashboard (P2).** Symbol and filled maps from a geographic field or GeoJSON beside a time series. *Acceptance:* unknown locations are flagged; no request leaves the app origin.

---

## 8. Quality attributes

### 8.1 Performance

| Dimension | Target | Qualification |
|---|---|---|
| First uncached chart | P95 ≤ 5 s on a designated benchmark table | Hardware and table documented when measured; not a promise for arbitrary servers. |
| Cached filter interaction | P95 ≤ 1 s | Bounded group count. |
| Marks | Aggregate or cap beyond 10,000 marks | Existing cap is 5000 groups ([D24](../reference/decisions.md#d24--showing-all-data-bounded-requests-paging-other-date-grouping)); reconcile in the plan. |
| Server time limit | 12 s per query (existing) | Failure shows an actionable message, not stale data. |

### 8.2 Safety

Controls that already exist and must be preserved by every new feature: read-only SQL with `readonly=2`, identifier validation and quoting in one place, bound typed values, bounded results, session-only credentials, credential-safe errors. Additions for this scope: neutralise CSV formula injection; parse GeoJSON defensively (size and depth limits, no remote references); make no network request except to the app origin; keep workbook files free of credentials.

### 8.3 Testing

- **Unit (xUnit):** operators, nulls, aggregation, date and week logic, AST validation (arity, types, whitelist), identifier safety, limits.
- **Golden data:** small fixtures with exact expected SQL and results — duplicates, nulls, joins, missing dates, aliases, rejected functions.
- **JS (`node --test`):** table calculations, regression, forecast, k-means (fixed seed), workbook upgrade and validation.
- **Visual:** axis scales, continuous vs discrete dates, legends, map overlap, export size, phone layout.
- **Live smoke:** against a throwaway ClickHouse ([development.md](../operations/development.md)).
- **Traceability:** maintain a matrix of each `TNN-NN` → status (built/partial/open) → test. The first version is the [gap analysis](gap-analysis.md).

---

## 9. Delivery and risks

Order by dependency, not by chapter: the [gap analysis](gap-analysis.md) is done; next come the calculation engine, model breadth, chart and dashboard gaps, analytics, maps. The release table, the four spikes that gate the engine design and the risk register are in [delivery-and-risks.md](delivery-and-risks.md).

## 10. Decisions

**Decided (28 October 2026):**
- The current stack stays; the proposal's React/FastAPI/DuckDB/PostgreSQL stack is dropped.
- The product stays single-user; every server-side feature was removed from the inventory and this proposal.

**Defaults I propose, open to change:**
- Table calculations and analytics run in the browser on bounded results.
- Prep flows are out; non-materialising cleaning is covered by field metadata and calculated fields (§3.5).
- PDF export is the only new export format.
- Natural-language query is P3 and a deterministic grammar.

**To settle in the plan:** workbook version bump and limits for the new fields; whether LOD sits in a subquery or a window; the mark cap (5000 vs 10,000); the charting additions that need ECharts extensions or a vendored library.

---

## Appendix — Sourced vs proposal-authored

Chapter and page coverage per domain is in [`tableau-features.md`](tableau-features.md) (printed book pagination).

Guidebook-derived: the capabilities in [`tableau-features.md`](tableau-features.md). Proposal-authored: the ordering, AST compilation approach, API and workbook additions, targets, tests and release order. Excluded or removed: 13 exclusions and 60 server-side removals, listed there.
