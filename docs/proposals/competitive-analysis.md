# Competitive analysis & feature roadmap — vs. Tableau and Google Analytics 4

**Purpose.** Record, honestly, where this Dashboard Builder stands against two very
different mature tools — **Tableau** (enterprise BI / data exploration) and **Google
Analytics 4** (web & product analytics) — and lay out **every capability** we'd need to
add to compete, **ordered by difficulty** with the tools/tech each requires and its impact
on our architecture.

> A forward-looking gap analysis, not a commitment. Several items tension with current decisions
> ([D1](../reference/decisions.md#d1--read-only-against-clickhouse) read-only,
> [D2](../reference/decisions.md#d2--thin-session-scoped-proxy-no-application-database) no application
> database, [D4](../reference/decisions.md#d4--vanilla-js--hand-written-css-no-spa-framework) vanilla JS);
> those tensions are called out per item and summarized in
> [§6](#6-architectural-implications--the-two-walls-well-hit). The near-term build order lives in
> [roadmap.md](roadmap.md).

## 1. Reality check — what we are today

A **drag-and-drop, Tableau-style worksheet over ClickHouse.** You connect, browse a schema, drag tables
onto a shared data model, draw logical relationships, and build worksheets: multi-field Columns/Rows
shelves with automatic cross-table joins, 23 chart types (incl. heatmap, treemap, histogram, box plot, waterfall, funnel, gauge, bullet, Sankey, small multiples,
KPI + sparkline, crosstab), a Marks toolbar (Color/Size/Label/Detail/Tooltip/Shape/Path/Angle), typed
filters (`in`/`between`), click-to-filter, single-table drill-down, a Pages shelf, formatting, and
PNG/SVG/CSV export. Quick wins **#1–#8 below are built** ([features/](../features/worksheet.md)).

What it is not: the server is a thin, **read-only** proxy with **no application database**. Work is
saved only in the user's browser (plus exported files); there are no users, roles, shared workbooks or
server-side saved work, and each dashboard is a single worksheet. That is a legitimate niche — *a fast visual explorer for people who know their ClickHouse
schema* — but not a BI platform and not a product-analytics suite. The rest of this doc is the distance
to each.

**How to read the difficulty scale** (rough engineering effort, one competent team):

| Tier | Effort | Meaning |
|---|---|---|
| **XS** | hours–1 day | config / small client change |
| **S** | days | one module, existing data path |
| **M** | 1–2 weeks | new query shapes + UI, modest server work |
| **L** | 3–8 weeks | a new subsystem or a hard cross-cutting change |
| **XL** | months+ | a platform in its own right (new infra, new team surface) |

## 2. Master list — every capability, ordered by difficulty

Easiest first; ✓ = built. Maps (#11) are out of scope for v1 ([D18](../reference/decisions.md#d18--marks-card-and-pages-shelf-are-client-encodings-on-the-existing-query-shape)); calculated fields (#13) are [roadmap P25](roadmap.md#p25--data-pane-authoring). "Closes gap with" = **T** Tableau, **G** GA4, **B** both. Effort per tier
above. "Impact" flags the architectural cost beyond just writing the feature.

| # | Capability | Gap | Tools / tech required | Effort | Impact |
|---|---|---|---|---|---|
| 1 | ✓ built — **Adopt a real charting library** (replace hand-rolled SVG) — the foundation everything visual rides on | B | Apache **ECharts** *or* **Vega-Lite** (declarative, fits our data shapes); keep it self-hosted, no CDN | S | Frontend dep; rendering swap in `ws-chart` |
| 2 | ✓ built — **Chart formatting & encodings** — number/date formats, axis titles, legends, sort, top-N, color-by-dimension, labels | B | charting lib (#1) + small config UI | XS–S | none |
| 3 | ✓ built — **More chart types on the existing query path** — area, stacked/grouped bar, pie/donut, scatter, histogram, KPI + sparkline, combo / dual-axis | T | #1 + one new 2-measure query shape | S | none |
| 4 | ✓ built — **Statistical chart types** — heatmap, treemap, box plot | T | #1 + ClickHouse `quantile()/quantiles()`, 2-dim group-by | S–M | none |
| 5 | ✓ built — **Export** — PNG/SVG of a chart, CSV of the underlying rows | B | charting lib export + a CSV endpoint (read-only, bounded) | S | minor server |
| 6 | ✓ built, worksheet-scoped (cross-widget → P24) — **Dashboard filter & parameter controls** — dropdowns, date-range pickers, sliders that apply across widgets | B | client filter state + parameterized re-query (values **bound**, per [D6](../reference/decisions.md#d6--identifiers-validated-against-the-live-catalog--backtick-quoted)) | M | dashboard-level state model |
| 7 | ✓ built, worksheet-scoped (cross-widget → P24) — **Cross-filtering / click-to-filter** — click a bar → filter the rest of the dashboard  | B | event bus + inject `WHERE` into each widget's query | M | interaction/state layer |
| 8 | ✓ built, single-table — **Hierarchical drill-down** — year→qtr→month, country→state→city, with breadcrumb | T | hierarchy metadata + re-query at finer grain | M–L | metadata model |
| 9 | **Funnel analysis** — ordered-step drop-off | G | ClickHouse **`windowFunnel()`** + funnel UI | M–L | new query builder; needs event data (#17) to be useful |
| 10 | **Cohort / retention analysis** — retention grids & curves | G | ClickHouse **`retention()`** + cohort UI | M–L | as #9 |
| 11 | **Geographic maps** — choropleth, point/bubble maps | T | **MapLibre GL** or **Leaflet** (self-hosted tiles/GeoJSON) + boundary data; ClickHouse geo fns | M–L | geo-asset management |
| 12 | **Path / flow exploration** — page-to-page Sankey | G | ClickHouse **`sequenceMatch`/`sequenceCount`** + Sankey viz | L | as #9 |
| 13 | **Calculated fields / custom metrics** — on-the-fly measures, IF/THEN, ratios, LOD-style scoped aggregates | T | a **safe expression engine**: parser → whitelisted → ClickHouse SQL (identifiers validated, funcs whitelisted, values bound) | L | new engine; the single biggest injection-surface item — must honor [D6](../reference/decisions.md#d6--identifiers-validated-against-the-live-catalog--backtick-quoted) rigorously |
| 13.5 | **Segment / audience builder** — reusable saved filters, set logic, export | G | expression engine (#13) + persistence (#15) | L | depends on #13, #15 |
| 14 | **Richer data blending** — LEFT/RIGHT/FULL joins, cross-source blending, aggregate-then-join | T | join-planner extension in `QueryAsync`; UI for join type/keys | L | extends the existing auto-join ([D12](../reference/decisions.md#d12--subtabs-are-dashboards-over-one-shared-data-model)) |
| 15 | ✓ in-browser (auto-save + file Export/Import, [D21](../reference/decisions.md#d21--workbooks-persist-in-the-browser-not-on-the-server)); server-side sharing still open — **Dashboard persistence** — save/load/share work ([O1](../reference/decisions.md#open-questions)) | B | an **application datastore** (Postgres/SQLite) or JSON store + save/load API | M–L | **breaks [D2](../reference/decisions.md#d2--thin-session-scoped-proxy-no-application-database)** (introduces the app DB we deliberately avoided) — prerequisite for #16, #18, #19, #20 |
| 16 | **Saved connections / connection profiles** ([O2](../reference/decisions.md#open-questions)) | B | app DB (#15) + a **secret store** (never persist CH passwords in plaintext — [D2](../reference/decisions.md#d2--thin-session-scoped-proxy-no-application-database)/rule 3) | M | needs #15 + secrets infra |
| 17 | **Event tracking model & ingestion pipeline** — the thing that makes GA-style analysis *possible* | G | event schema (events/sessions/users) + a **JS tracking SDK/collector** (custom or **Snowplow**) + a queue (**Kafka**/Redpanda) + ClickHouse MergeTree tables + materialized views | XL | a platform; also needs a **write path** ClickHouse-side (outside our read-only app — [D1](../reference/decisions.md#d1--read-only-against-clickhouse)) |
| 18 | **Sessionization & core metrics** — sessions, engaged time, DAU/WAU/MAU, identity stitching | G | ClickHouse window fns + materialized views over #17's events | L–XL | depends on #17 |
| 19 | **AuthN / AuthZ** — accounts, SSO, roles (RBAC) | T | **OIDC** via ASP.NET Core Identity *or* an external IdP (**Keycloak** / Entra ID / Auth0) | L | new auth subsystem; needs #15 |
| 20 | **Collaboration** — publishing workflow, sharing, comments, version history | T | app DB (#15) + auth (#19) + notifications | L–XL | depends on #15, #19 |
| 21 | **Scheduling, alerting & embedding** — scheduled report delivery, threshold alerts, signed-embed of a dashboard | B | a job runner (**Hangfire**/Quartz) + email/webhook + embed tokens | L | needs #15, #19 |
| 22 | **Governance & data security** — row-level security, data catalog, certified sources, audit logs | T | per-user query-injection policy engine + catalog store + audit sink | XL | needs #15, #19; deep query-layer change |
| 23 | **Visual ETL / data prep** (Tableau Prep equivalent) — cleanse, reshape, materialize | T | **dbt** + an orchestrator (**Airflow**/Dagster/Prefect) *or* a bespoke pipeline engine; ClickHouse materialized views | XL | **breaks [D1](../reference/decisions.md#d1--read-only-against-clickhouse) read-only** (needs DDL/DML) — effectively a second product |
| 24 | **Attribution modeling** — first/last/linear/data-driven; conversion paths | G | marketing touch data + attribution models (rule-based → ML) | XL | needs #17, #18 |
| 25 | **Ad-platform & data connectors** — Google Ads/GA/CRM ingest | G | a **connector framework** + **OAuth** to external APIs + scheduled sync | XL | needs #15, #23, secrets |
| 26 | **ML-driven insight** — anomaly detection, forecasting, "smart insights" (GA4 Insights) | G | a modeling layer (Python service, MindsDB, or ClickHouse ML fns) + feature store | XL | new service surface |

## 3. What ClickHouse gives us for free (lowers several costs)

Worth calling out, because it makes some GA4-class features **cheaper than they look**:

- **`windowFunnel()`** → funnels (#9), **`retention()`** → cohorts (#10),
  **`sequenceMatch`/`sequenceCount`** → path analysis (#12). These are the hard parts of a
  web-analytics engine, and they're built into the database.
- **`quantile*`, `median`, `stddev*`, `histogram`** → box plots / histograms / stats (#4).
- **Geo functions** (`geoDistance`, `pointInPolygon`, H3/S2 helpers) → maps (#11).
- **Materialized views + `AggregatingMergeTree`** → cheap sessionization / rollups (#18).

The gap to GA4 is therefore **less about query capability** and **more about the ingestion
pipeline, the event schema, and the pre-built product logic** wrapped around these
functions (#17 is the real mountain).

## 4. Grouped by theme (the same items, by where the work lives)

- **Visualization depth (mostly client, low risk):** #1–#5, #11 — a charting library plus a
  map component closes most of the *visual* gap with Tableau quickly.
- **Interactivity (client + query params):** #6, #7, #8 — turns static charts into an
  exploratory dashboard; high perceived value, moderate cost.
- **Analytical power (server/query engine):** #13, #13.5, #14 — calculated fields and
  richer joins; the expression engine is the flagship, and the flagship risk.
- **Product-analytics platform (new infra):** #9, #10, #12, #17, #18, #24, #26 — dominated
  by #17; without an event pipeline the analytics modules have nothing to run on.
- **Enterprise platform (persistence, identity, governance):** #15, #16, #19, #20, #21,
  #22, #23 — the "boring" enterprise substrate that Tableau's value actually rests on.

## 5. Consolidated tools & infrastructure to acquire

| Concern | Candidate tool(s) | Introduced by |
|---|---|---|
| Charting | Apache ECharts **or** Vega-Lite (self-hosted) | #1 |
| Mapping | MapLibre GL / Leaflet + GeoJSON/tiles | #11 |
| Expression engine | custom parser → whitelisted ClickHouse SQL | #13 |
| Application datastore | PostgreSQL (or SQLite to start) | #15 |
| Secret store | Vault / cloud KMS / protected config | #16 |
| Event collection | Snowplow **or** custom collector + JS SDK | #17 |
| Streaming/queue | Kafka / Redpanda | #17 |
| Identity | ASP.NET Core Identity **or** Keycloak / Entra / Auth0 (OIDC) | #19 |
| Jobs/scheduling | Hangfire / Quartz | #21 |
| ETL / transform | dbt + Airflow / Dagster / Prefect | #23 |
| ML/insights | Python service / MindsDB / ClickHouse ML | #26 |

## 6. Architectural implications — the two walls we'll hit

Two current decisions block whole categories above and must be *consciously* revisited, not
drifted past:

1. **[D2](../reference/decisions.md#d2--thin-session-scoped-proxy-no-application-database) — no application database.** Everything about *saving* work
   (#15), *users* (#19), *sharing/governance* (#20, #22) requires a persistent app-side
   store. This is the first wall: the moment we promise "log in and your dashboard is still
   here," we're building the subsystem D2 exists to avoid. Resolve [O1](../reference/decisions.md#open-questions)/
   [O2](../reference/decisions.md#open-questions) first.

2. **[D1](../reference/decisions.md#d1--read-only-against-clickhouse) — read-only against ClickHouse.** Product analytics (#17) needs an
   **ingest/write path**, and visual ETL (#23) needs **DDL/DML**. Neither belongs in *this*
   read-only app. The competitive move is a **separate ingestion/transform service** that
   writes ClickHouse, leaving our app as the read-only *presentation* layer over it — not
   loosening D1 here.

**Bottom line.** The visualization and interactivity quick wins (#1–#8) are built; the remaining
worksheet-parity work is scoped in [roadmap.md](roadmap.md). Beyond that, competing with **Tableau**
means building the **enterprise substrate** (persist → identify → govern), and competing
with **GA4** means building an **event platform** (#17) before any of the marquee analytics
modules have data to stand on. Those are product bets, each measured in months.
