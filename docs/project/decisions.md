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
  legend. **Colour-by-dimension** (categorical ramp keyed to a dimension's *values*) is still
  future work. *See [BUILD_PLAN P9](../../BUILD_PLAN.md),
  [frontend-patterns.md](../frontend-patterns.md#charts-p9), [DESIGN.md](../../DESIGN.md).*

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
