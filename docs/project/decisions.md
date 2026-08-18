# Decisions & rationale

The design/architecture decisions behind the builder, why they were made, and the
open questions still to settle. This is the **"why" record** — when a decision changes,
update the entry here (and the doc it affects) in the same change.

> This project is greenfield: there is **no prior implementation and no bug history**.
> Entries below are *forward-looking decisions*, not a post-mortem of a shipped app.

## Accepted decisions

### D1 — Read-only against ClickHouse
The app introspects schema and previews rows; it issues **no DDL/DML**. Keeps the
security surface small, matches the statement (browse/drag/relate — not edit data), and
means a leaked/over-scoped connection can't mutate the server. *Enforced as a golden
rule in [CLAUDE.md](../../CLAUDE.md).*

### D2 — Server is a thin, session-scoped ClickHouse proxy; no application database
The statement needs no user accounts or server-side records to function. Builder state
(entities, relationships, tabs) lives in the browser. Avoiding an app DB removes a whole
subsystem (schema, migrations, ORM) and its attack surface. *See [ARCHITECTURE.md](../../ARCHITECTURE.md).*
- **Trade-off:** dashboards don't survive a refresh in v1 → see **O1**.

### D3 — `ClickHouse.Client` over the HTTP interface
Mainstream, maintained ADO.NET driver with familiar `DbConnection`/`DbCommand`
semantics over the **HTTPS interface** (see **D10** for the secure-port requirement).
- **Rejected:** native TCP protocol (`9000`/secure `9440`) — marginally faster, but heavier
  client and no benefit for introspection + small previews. Revisit only if large streamed
  reads become a feature.
- Details: [clickhouse-integration.md](../clickhouse-integration.md).

### D4 — Vanilla JS + hand-written CSS (no SPA framework)
One page with bespoke interactions (drag/drop canvas, SVG relationship links). A
framework's routing/state machinery buys little here and adds build tooling and payload.
Native APIs (HTML5 DnD, `<dialog>`, `<select>`, `fetch`) cover the needs.
- **Rejected:** React/TS SPA (build pipeline + bundle for one page); **Blazor Server**
  (a SignalR circuit and server round-trips for pure-client canvas interactions is the
  wrong shape). Revisit React only if the canvas grows into a large stateful editor.
- Patterns: [frontend-patterns.md](../frontend-patterns.md).

### D5 — Relationships are logical declarations, not database constraints
ClickHouse enforces no foreign keys and no uniqueness (a MergeTree primary key is a
sparse index). The 1:1/1:N/N:M links are the **user's assertions**, used by the app for
joins/layout — the DB is never asked to create or validate them. This is a core mental
model, called out in the [README](../../README.md), [data-model.md](../data-model.md),
and [CLAUDE.md](../../CLAUDE.md).

### D6 — Identifiers validated against the live catalog + backtick-quoted
DB/table/column names can't be bound as SQL parameters, so they're interpolated. To
prevent injection they must be confirmed to exist for the current connection and
backtick-escaped, in one shared helper (`ClickHouse/Identifier.cs`). *See
[clickhouse-integration.md](../clickhouse-integration.md).*

### D7 — Design language: RED / BLACK / WHITE, fixed no-scroll shell
A black chrome rail vs. white workspace makes "controls vs. canvas" obvious; one reserved
accent (red) marks the single important thing per view. Token-driven CSS, WCAG-AA
contrast, status by icon+text+color. *Full spec: [DESIGN.md](../../DESIGN.md).*

### D8 — Target .NET 10 LTS on AlmaLinux 9
The current LTS (released Nov 2025), for the longest support horizon; available via the
AlmaLinux 9 appstream / Microsoft feed. *See [development.md](../development.md).*

### D9 — Build on host `10.168.49.20` at `/unified/user/cj/web_development/prototype/dashboard_builder/`
Firm requirement: the app is scaffolded and compiled on that host, in that folder, so
`src/DashboardBuilder` lives at
`/unified/user/cj/web_development/prototype/dashboard_builder/src/DashboardBuilder`. This KB lives separately
(under `.../knowledge/…`) and is not the build location. *See [development.md](../development.md),
[BUILD_PLAN.md](../../BUILD_PLAN.md) P0.*
- **Migrated 2026-08-13** from the original build host `10.168.49.13` to `10.168.49.20`
  (same path). The source tree was copied (build artifacts excluded and rebuilt on the new
  host); `dotnet build` and `dotnet test` (56 passing) are green there, and Kestrel serves
  the page + read-only API. On `10.168.49.20` the .NET 10 SDK is on the global `PATH`
  (`10.0.108`, `/usr/lib64/dotnet`) — no `~/.dotnet` prefix needed.

### D12 — Subtabs are dashboards over ONE shared data model (not per-tab entity canvases)
Corrects an earlier build where each subtab was its own entity-view canvas. Per the statement
("create subtabs and **build a dashboard from the dragged tables**") and the user, the entity
views + relationships are **one shared data model**; the subtabs are **dashboards** built from it
by adding **widgets**. The view strip is a pinned **Data Model** tab + dashboard tabs; `store.js`
holds one shared `entities`/`relationships` plus a `dashboards` list (each with `widgets`).
- **UX (user-directed):** each dashboard is a **Tableau-style worksheet** — a field pane +
  **Columns / Rows / Filters** shelves you **drag fields onto** to build a chart (bar/line/table/KPI).
- **Cross-table (O4 = yes):** fields from different tables are **joined** automatically along the
  drawn relationships. The client finds a join path (BFS over the relationship graph); the server's
  `QueryAsync` builds the aliased, identifier-safe `JOIN`s (`POST /api/query`). Unrelated tables →
  a "draw a relationship" warning. *See [clickhouse-integration.md](../clickhouse-integration.md),
  [data-model.md](../data-model.md), [modules.md](../app/modules.md) §7.*

### D11 — TLS certificate validation: safe-by-default, explicit per-connection opt-in (P8 — resolved 2026-08-17)
The target ClickHouse presents a **self-signed certificate** on `8443`, so default chain
validation rejects it (`UntrustedRoot`). **P8 hardening** made certificate validation the
**default**: a secure connection now **validates the server certificate** against the host trust
store unless the user explicitly opts in **per connection** with `allowInvalidCert:true` —
surfaced as a "Trust invalid / self-signed certificate" checkbox shown under Secure (unchecked
by default, warns while checked). The bypass is gated on `secure`
(`(req.AllowInvalidCert ?? false) && secure` — a plain connection can never bypass) and is
applied via `HttpClientHandler.DangerousAcceptAnyServerCertificateValidator` only when
`ClickHouseGateway.BypassesCertificateValidation(info)` is true. `ConnectionView` now reports
`allowInvalidCertificate` so the summary can flag a bypassed connection (`TLS ⚠ cert unverified`).
This **supersedes the original opt-out default** (`allowInvalidCert:true`), completing the P8
item this decision had deferred ("production should trust the server's CA … and set
`allowInvalidCert:false`"). TLS (D10) still holds — traffic is always encrypted.
- **Consequence for the known target:** because that ClickHouse is self-signed, connecting to
  it now requires ticking the opt-in (an informed choice) — or, better, trusting its CA.
- **Trade-off:** even with the opt-in ticked there is no MITM protection on the ClickHouse
  path; the stronger fix remains trusting the server's CA or a pinned cert.
- **Implementation note:** a hand-supplied HttpClient must also set
  `AutomaticDecompression` — ClickHouse.Client requests compressed responses and otherwise
  throws "server returned compressed result but HttpClient did not decompress it".
  See [clickhouse-integration.md](../clickhouse-integration.md#driver--connection).

### D10 — Connect over TLS only: HTTPS port `8443` (native TLS `9440`)
Firm requirement: the target ClickHouse exposes **only its secure ports** — **`8443`**
(HTTPS interface, which this app uses) and **`9440`** (native TCP over TLS, unused per
**D3**). The plaintext ports `8123`/`9000` are **not** available, so every real connection
is `secure` (TLS) on `8443` — the `secure` flag defaults on and port `8443` is the default,
not an option. (A local throwaway container may still expose plain `8123` for testing only.)
*See [clickhouse-integration.md](../clickhouse-integration.md#driver--connection),
[data-model.md](../data-model.md).*

### D13 — Charting via self-hosted Apache ECharts (SVG renderer), themed from tokens
The worksheet's **bar/line** charts render through **Apache ECharts**, vendored into
`wwwroot/js/vendor/echarts.min.js` (**no CDN** — served under the app's `no-cache` static
policy) and loaded as a global **before** the ES-module graph. A thin `wwwroot/js/chart.js`
adapter maps our `{rows:[{label,value}]}` result to an ECharts option, themed entirely from
the `--chart-*` CSS tokens (SVG renderer: crisp + lighter DOM). **Table and KPI stay native
DOM** — neither is a charting-library concern.
- **Why a library, not more hand-rolled SVG:** P11/P12 need many chart types (scatter,
  heatmap, treemap, box plot) with tooltips/legends/axes that are costly to hand-build;
  ECharts covers them with one dependency. A **viz library is not an SPA framework** —
  [D4](#d4--vanilla-js--hand-written-css-no-spa-framework) still holds; the app stays
  vanilla-JS modules rendering into `#ws-chart`.
- **Rejected:** Vega-Lite (heavier multi-file stack; less convenient imperative
  theming/resize for our token-driven look).
- **Series colour:** single series wears the brand accent; **multi-measure** charts use the
  **validated categorical** ramp `--chart-cat-1..8` (dataviz colourblind/contrast-checked) with a
  legend. **Colour-by a dimension's *values*** across series shipped in P7 — see
  [D14](#d14--colour-marks-are-an-extra-group-by-the-client-pivots-into-series). *See
  [BUILD_PLAN P9](../../BUILD_PLAN.md), [frontend-patterns.md](../frontend-patterns.md#charts-p9),
  [DESIGN.md](../../DESIGN.md).*

### D14 — Colour marks are an extra group-by the client pivots into series (P7 — 2026-08-18)
The worksheet gained a Tableau-style **Color shelf** (one dimension). Rather than a new query shape,
the colour dimension is sent as **one more group-by**, appended **last** to the request's
`ColumnDimensions`; the server's key order stays `[rowDims…, colDims…, color]`. The client
(`renderColorSplit` in `dashboards.js`) treats that trailing key specially: for **bar/stacked/line/
area** it **pivots** the flat grouped rows into **one series per distinct colour value** (bar →
grouped, stacked → stacked, line/area → one line each); a **Table** takes it for free as an extra
top-header level. This keeps [D1](#d1--read-only-against-clickhouse) read-only and stays on the
**existing bounded aggregate/join path** ([D6](#d6--identifiers-validated-against-the-live-catalog--backtick-quoted)
identifier safety unchanged), so no `QueryModels`/gateway change was needed.
- **Constraints:** colour-split renders for **one measure** (multi-measure + colour → a hint, not an
  error, per P11); chart types that don't consume colour (pie/donut/scatter/combo/KPI) show a **lane
  note** and ignore the pill rather than silently mis-querying (colour is only added to the query for
  those types in `COLOR_USES`). Category × colour combos are still capped by the query `LIMIT`
  (Top-N), so the result stays bounded; beyond 8 values the `--chart-cat-*` ramp repeats (legend
  disambiguates — never colour-alone).
- **Pill colour:** a new **`--info-*`** violet token trio (matching `--chart-cat-7`) distinguishes the
  Color pill from dimension (red) and measure (green) — tokens only, per
  [D7](#d7--design-language-red--black--white-fixed-no-scroll-shell) / DESIGN rule 6.
- **Rejected:** a dedicated server `color` field / new query shape (unnecessary — it's just a
  group-by); a continuous colour gradient for measure-on-colour (deferred; v1 groups by value).
- **Not click-to-filter:** the other P7 "next" item (click a mark to filter the sheet) still lands in
  [P15](../../BUILD_PLAN.md), which depends on the P14 dashboard-filter machinery.

### D15 — Statistical charts, export & richer filters stay on read-only, bounded, bound-param paths (P12–P14 — 2026-08-18)
P12–P14 added visualisation and interactivity without weakening the two invariants
([D1](#d1--read-only-against-clickhouse) read-only, [D6](#d6--identifiers-validated-against-the-live-catalog--backtick-quoted) identifier safety):
- **P12 statistical charts.** **Heatmap/treemap reuse the existing multi-dimension `/api/query`** (no
  new shape — the client pivots the 2-dim result). **Histogram** and **box plot** are the genuinely new
  single-table shapes: histogram buckets one numeric column with a `WITH (min)/(max)` +
  `floor((col-lo)/width)` in **one bounded statement** (bins clamped 1..100, the max value clamped into
  the last bin); box plot is `min`/`quantile(.25|.5|.75)`/`max`, optionally grouped, bounded `LIMIT`.
  Both are **single-table** (a distribution is one column) — joins add nothing here, so they take their
  own endpoints rather than complicating `QueryAsync`.
- **P13 export.** Chart image is client-only (**SVG** native from the SVG renderer; **PNG** rasterised
  from that SVG via canvas). **CSV** reuses `QueryAsync` (same bounded plan) and serialises through a
  pure `CsvUtil` — RFC-4180 quoting **plus a formula-injection guard** (a leading `= + - @` is prefixed
  with `'`), because exported cells open in spreadsheets. No new query surface; read-only.
- **P14 filters.** A dashboard is still one worksheet ([D12](#d12--subtabs-are-dashboards-over-one-shared-data-model-not-per-tab-entity-canvases)),
  so P14 landed as **richer Filters-shelf controls**, not cross-widget wiring (that needs P24). New ops
  **`in`** (multi-select from a **bounded distinct-values** query) and **`between`** (range) join the
  scalars; all values are **bound parameters** — `in` as an `Array(String|Float64)`, `between` as two
  bounds — via a new pure **`BuildCondition`** that `QueryAsync` now calls. An empty `in` / partial
  range is a **no-op** (never `IN ()`).
- **Testing.** The safety-critical logic was extracted into **pure, unit-tested** helpers
  (`ClampBuckets`, `ClampDistinct`, `BuildSingleTableFilters`, `BuildCondition`, `CsvUtil`) reachable via
  `InternalsVisibleTo` — the SQL string/param shapes and hostile-input rejection are asserted without a
  live server; the endpoints keep the without-connection **409** gate. 63 → **100 tests**.
- **Deferred:** histogram/box-plot CSV (their shape isn't a `QueryRequest`); cross-**widget** filters +
  parameters proper (→ P24 multi-worksheet dashboards); click-to-filter (→ P15).

### D16 — Click-to-filter ships as worksheet-scoped selection machinery (P15 — 2026-08-18)
P15's "click a mark to filter the dashboard's other widgets" presumes **multiple widgets** — but a
dashboard is still **one worksheet** (multi-view composition is P24). So P15 landed as the **transient
mark-selection machinery** on that single worksheet, which is exactly what P24 will reuse for cross-widget
filtering. Clicking a chart mark forwards the ECharts `click` (`chart.js`), the client maps the mark's
`dataIndex` → the **primary dimension**'s raw value, and stores `sheet.selection`. A **selection chip**
offers **Keep only** (`col = value`) / **Exclude** (`col != value`) / clear; the action becomes a
**bound-parameter** filter appended in `buildPlan` — reusing the P14 path, and **only when the selected
column's table is already in the query** so a click can never force an unresolved join. Clicking the same
mark or ✕ clears; the chip is the visible selection.
- **Why not filter on click immediately (Tableau's filter action)?** On a single widget, self-filtering to
  the clicked value collapses the chart to one mark. Making the click a **selection** with explicit
  Keep-only/**Exclude** keeps it useful (Exclude is genuinely handy on one chart) and non-destructive until
  the user chooses — and matches Tableau's select-then-act model.
- **Scope:** wired for bar/stacked/line/area/combo/pie/donut/scatter (incl. colour-split, where the primary
  value is the first non-colour dimension). Heatmap/treemap/histogram/box-plot/KPI/table are no-ops (their
  marks don't map 1:1 to a single primary-dimension value); a null value is a no-op (can't cleanly bind
  `= NULL`). **Pure client** — no new query surface (reuses [D15](#d15--statistical-charts-export--richer-filters-stay-on-read-only-bounded-bound-param-paths-p12p14--2026-08-18)'s bound-param filters), so the read-only invariant is untouched.
- **Deferred:** cross-**widget** propagation + an event-bus fan-out (→ P24 multi-worksheet dashboards).

## Open questions

| # | Question | Leaning |
|---|---|---|
| **O1** | Do dashboards persist across sessions? | Start ephemeral (in-memory). If needed, add opt-in **JSON persistence** (a file/store keyed by session) before any user DB. Don't introduce auth just for this. |
| **O2** | Where are multiple saved connections stored? | v1: one active connection per session, not saved. Later: named connection profiles — **without** persisting passwords server-side. |
| **O3** | How rich are dashboard widgets in v1? | Ship browse→drop→relate first; KPIs/charts are a later phase. Keep widget model minimal until the core is solid. |
| **O4** | Do we execute the *joins* the relationships imply (run a joined query), or only record them? | **Resolved: yes.** Worksheet charts run a bounded, identifier-safe joined/aggregate query over the drawn relationships (`POST /api/query`, `QueryAsync`) — [D12](#d12--subtabs-are-dashboards-over-one-shared-data-model-not-per-tab-entity-canvases). Fan-out on the many side is the user's declared intent (cardinality is not enforced). |
| **O5** | Reverse proxy & TLS termination in prod | **Resolved on `10.168.49.20`:** **Apache httpd** on `443` (self-signed TLS) proxies `/dashboardbuilder` → Kestrel on `127.0.0.1:5006`; the app is `PathBase`-aware (config key `PathBase`). Firewall exposes only `443`, so raw app ports aren't reachable. Durable runs use a **systemd** unit off a `dotnet publish` under `/var/www/webapps/`, matching the neighbor apps. *See [development.md](../development.md).* |

Resolve an open question by promoting it to an accepted decision (with rationale) and
updating the affected doc.
