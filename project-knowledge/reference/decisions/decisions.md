# Decisions & rationale

The "why" record: each architecture or design decision, its reason, and what was rejected. When a
decision changes, **edit its entry in place** (and the doc it affects) in the same change. To resolve an
open question, promote it to a decision.

## Where each decision lives

| Decisions | File |
|---|---|
| D1–D25 | this file |
| D26–D60, D65–D68, D73 (calculated fields, parameters, member labels, groups, split / unpivot) | [decisions-calculated-fields.md](decisions-calculated-fields.md) |
| D61–D64, D69, D71–D72, D74, D79–D80 (dashboards, hierarchies, option controls, desktop-only, compound join keys, Gantt) | [decisions-dashboards.md](decisions-dashboards.md) |
| D70 (recent connection sources) | [decisions-connection.md](decisions-connection.md) |
| D75–D77 (`NULL`, `IN` / `BETWEEN`, keyword `IF`), D78 (`MAKEDATE`, `DATENAME`) | [decisions-logic.md](decisions-logic.md) |

## Platform & safety

### D1 — Read-only against ClickHouse
The app introspects the schema and runs bounded `SELECT`s. It issues **no DDL/DML** (no statements that
create, change or delete schema or data).
- **Why:** it keeps the security surface small and matches the statement (browse / drag / relate /
  chart — not edit data). A leaked or over-scoped connection can't change the server.
- **Enforced twice.** Our SQL builders emit only reads, *and* every query carries ClickHouse's own
  `readonly=2`, so the server itself refuses a write even if a builder bug produced one. The same
  settings add a server-side time limit and cancel-on-disconnect.
- **Why `readonly=2`, not 1:** level 1 also forbids changing settings, which would reject the driver's
  own per-request settings and our time limit. Level 2 still blocks every write and DDL.
- **A server that refuses a setting doesn't block connecting:** the connection steps down at connect time
  ([guards and step-down](../clickhouse-integration.md#database-level-guards)).
- Golden rule: [rule 1](../../engineering/golden-rules.md#1-the-server-is-read-only-against-clickhouse).

### D2 — Thin, session-scoped proxy; no application database
Builder state lives in the browser; the server only holds the session's connection.
- **Why:** the statement needs no user accounts or server-side records. Avoiding an app database removes
  a whole subsystem (schema, migrations, ORM) and its attack surface.
- **Trade-off:** dashboards don't survive a reload → [O1](#open-questions).

### D3 — `ClickHouse.Client` over the HTTP interface
The app uses `ClickHouse.Client` over HTTPS.
- **Why:** a mainstream, maintained ADO.NET driver with familiar `DbConnection`/`DbCommand` semantics.
- **Rejected:** the native TCP protocol (`9000` / TLS `9440`). It is marginally faster, but a heavier
  client with no benefit for introspection and bounded aggregates. Revisit only if large streamed reads
  become a feature.

### D6 — Identifiers validated against the live catalog + backtick-quoted
Every database, table and column name must exist for the current connection and is backtick-escaped,
in one helper (`ClickHouse/Identifier.cs`).
- **Why:** names can't be bound as parameters, so they are interpolated into SQL; validating and quoting
  them prevents injection. Values, by contrast, are always bound.
- Detail: [clickhouse-integration.md](../clickhouse-integration.md#identifier-injection).

### D10 — Connect over TLS only: HTTPS port `8443`
`secure` is on by default and `8443` is the default port.
- **Why:** the target ClickHouse exposes only its secure ports ([ports](../clickhouse-integration.md#driver--connection)).

### D11 — TLS certificate validation: safe-by-default, explicit per-connection opt-in
A secure connection **validates the server certificate** against the host trust store. The user may opt
in per connection to skip it with "Trust invalid / self-signed certificate" (`allowInvalidCert`).
- **How it shows:** the checkbox appears only under Secure and shows a warning while ticked. The
  connection summary flags it (`TLS ⚠ cert unverified`).
- **Enforced in:** the bypass is gated on TLS (`allowInvalidCert && secure`). It is applied via
  `DangerousAcceptAnyServerCertificateValidator` only when `BypassesCertificateValidation(info)` is true.
- **Consequence:** the known target is self-signed, so connecting to it requires the opt-in — or,
  better, trusting its CA.
- **Trade-off:** with the opt-in there is no man-in-the-middle protection on the ClickHouse leg. The
  stronger fix is trusting the server's CA or pinning its cert. Traffic is always encrypted (D10).

## Frontend & design

### D4 — Vanilla JS + hand-written CSS (no SPA framework)
The frontend is plain JavaScript and CSS, with no single-page-app (SPA) framework.
- **Why:** one page with bespoke interactions (drag/drop canvas, SVG links, worksheet). A framework's
  routing and state machinery buys little and adds build tooling and payload. Native APIs (HTML5 drag
  and drop, `<dialog>`, `<select>`, `fetch`) cover the needs.
- **Rejected:** a React/TS SPA (a build pipeline and bundle for one page); **Blazor Server** (a SignalR
  circuit and server round-trips are the wrong shape for pure-client canvas interaction). Revisit React
  only if the canvas grows into a large stateful editor.

### D7 — Design language: RED / BLACK / WHITE, fixed no-scroll shell
**Superseded by [D22](#d22--fluent-glass-design-language).** This was the original red / black / white identity.
- **Why retired:** red was both the brand accent and the danger colour (`--brand-soft` and the danger
  tint were the same hex), so a soft-red flash read as an error.
- **What survives:** the **fixed no-scroll shell**, token-driven CSS, WCAG-AA contrast, and status by
  icon + text + colour.

### D13 — Charting via self-hosted Apache ECharts (SVG renderer), themed from tokens
Charts render through ECharts, vendored at `Features/Core/vendor/echarts.min.js` (**no CDN**, served
`no-cache`) and loaded as a global before the module graph. `chart.js` is the only adapter and themes
every chart from `--chart-*` tokens. Table, Text and KPI stay native DOM.
- **Why a library:** the chart vocabulary (scatter, heatmap, treemap, box plot, dual-axis, legends,
  tooltips) is costly to hand-build. A viz library is **not** an SPA framework, so D4 holds.
- **Why SVG:** the SVG renderer is crisp and enables SVG export.
- **Rejected:** Vega-Lite — a heavier multi-file stack with less convenient imperative theming and resize.
- **Series colour:** one series wears the accent (`--accent`). Several series draw the categorical ramp
  `--chart-cat-1..8` (light and dark values) with a legend.

### D19 — MVC in feature folders
ASP.NET Core MVC with **one folder per feature** under `Features/`: controller, view partial
(`_<Feature>.cshtml`), stylesheet and ES modules together. Features are listed in the
[code map](../../ARCHITECTURE.md#code-map). Shared server infrastructure stays in `ClickHouse/`; the shared frontend in
`Features/Core/`. API controllers subclass `Features/ApiControllerBase.cs` (`NotConnected` /
`SafeError`) and return `IResult`.
- **Why:** a single 1k-line `site.css` and a flat `js/` had outgrown easy navigation. Co-locating a
  feature's server, view, style and script makes each region self-contained. Still vanilla, no build
  step (D4).
- **Serving assets outside `wwwroot`:** a second static-file provider maps `/features` with a content
  type map of **only `.css`/`.js`** (`ServeUnknownFileTypes=false`), so co-located `.cs`/`.cshtml`
  files return 404. The csproj marks `Features/**/*.css;*.js` as `Content` copied on publish.

### D22 — Fluent glass design language
Supersedes [D7](#d7--design-language-red--black--white-fixed-no-scroll-shell).
Windows 11 Fluent structure with Flat Design 2.0 surfaces:
- **warm neutrals + one crimson accent**;
- **glass chrome** (sidebar, tab bar, worksheet header: translucent tint + backdrop blur + 1px stroke +
  top rim) over a warm background wash;
- **solid data surfaces and overlays** (entity cards, chart area, crosstab, menus, popovers, toasts,
  dialogs);
- **light and dark** (System / Light / Dark toggle).

Spec: [design/overview.md](../../design/overview.md), [tokens.md](../../design/tokens.md).
- **Why:** the red / black identity was heavy, ambiguous (brand vs. danger) and showed every control at
  once. A calmer palette with progressive disclosure (Advanced connection settings, the encodings More
  menu, the Workbook menu, collapsible field groups) lets a first-time user see only what matters.
  Nothing is removed, and an encoding that holds fields is never hidden.
- **Red accent without red-means-error ambiguity** (the reason D7 was retired). Danger is a distinct
  vermilion (`--danger-*`) and always carries an icon and words. Field pills are blue / teal / violet.
  The focus ring is neutral ink, and a focused input keeps a neutral border with an accent underline, so
  focus never looks like an invalid field.
- **Glass only where nothing sits beneath it but the wash.** On a blurred panel over content, the text
  underneath reads through the text on top, so anything that floats is solid ([tokens.md](../../design/tokens.md)).
- **Light / dark is a viewer preference**, remembered per browser and never saved in the workbook: it is how
  *this* viewer wants to read, not part of the shared analysis ([tokens.md § Light and dark](../../design/tokens.md#light-and-dark)).
- **Icons:** one self-hosted inline-SVG set (`Core/icons.js`); no icon font. **Calm motion:** no hover-lift,
  shimmer or pulse ([motion-accessibility.md](../../design/motion-accessibility.md#motion)).
- **Rejected:** a from-scratch view rewrite (risk in the 1.8k-line `dashboards.js`) and a colour-only
  reskin (doesn't reduce visual weight). The module graph and markup stayed; the token block was
  replaced and each stylesheet re-pointed by meaning.

## Builder model & worksheet

### D5 — Relationships are logical declarations, not database constraints
The 1:1 / 1:N / N:1 / N:M links are the **user's assertions**, used for joins and layout. The database
is never asked to create or validate them.
- **Why:** ClickHouse enforces no foreign keys and no uniqueness (a MergeTree primary key is a sparse
  index).

### D12 — Subtabs are dashboards over one shared data source
The dragged tables + relationships form **one shared data source** (the pinned Data Source tab).
Worksheets and dashboards are built *from* it ([D61](decisions-dashboards.md)). Each worksheet tab **is
one Tableau-style worksheet** — a field pane plus shelves you drag fields onto.
- **Joins are executed.** Fields from different tables join automatically along the drawn
  relationships. The client finds a join path (breadth-first search over the relationship graph);
  `QueryAsync` builds aliased, identifier-safe joins of each relationship's type.
- Fan-out on the many side is the user's declared intent; cardinality is not enforced. Unrelated tables
  show a "draw a relationship" warning.
- **Rejected:** one independent entity canvas per subtab — the statement asks to "build a dashboard
  from the dragged tables", i.e. one model, many views.

### D14 — Colour marks are an extra group-by the client pivots into series
A categorical Colour field is sent as **one more group-by**, appended last. The client pivots that
trailing key into one series per value: bar → grouped, stacked → stacked, line/area → one line each; a
Table gets an extra header level.
- **Why:** no new query shape, so D1/D6 are untouched.
- **Constraints:** colour-split needs one measure (otherwise a hint). Types outside `COLOR_USES` show a
  lane note rather than mis-querying. Combinations stay capped by the query `LIMIT`. Past 8 values the
  ramp repeats and the legend disambiguates.
- **Rejected:** a dedicated server `color` field — it is just a group-by.

### D15 — Statistical charts, export and richer filters stay on read-only, bounded, bound-param paths
- **Heatmap and treemap** reuse the multi-dimension `/api/query`.
- **Histogram and box plot** are the only new shapes. They are single-table (a distribution is one
  column), so they take their own endpoints rather than complicating `QueryAsync`.
- **Export:** SVG/PNG are client-only. CSV reuses `QueryAsync`, and `CsvUtil` adds a formula-injection
  guard because exported cells open in spreadsheets.
- **Filters:** `in` (from a bounded distinct-values query) and `between` bind as typed parameters via
  the pure `BuildCondition`.
- **Not supported:** histogram/box-plot CSV (their shape isn't a `QueryRequest`).

### D16 — Click-to-filter is a select-then-act worksheet selection
Clicking a mark **selects** its primary-dimension value, and a chip offers **Keep only** / **Exclude** /
clear. The choice applies as a bound filter only when the column's table is already in the query (a
click never forces a join).
- **Why not filter immediately (Tableau's filter action)?** A worksheet shows one chart, and
  self-filtering to the clicked value collapses it to one mark. Select-then-act keeps the chart useful
  (Exclude is handy on one chart) and non-destructive.
- **Scope:** bar/stacked/line/area/combo/pie/donut/scatter. Types whose marks don't map 1:1 to a
  primary value, and null values (`= NULL` can't be bound), are no-ops.
- The same selection-to-filter path (`selectionFilter`) is the basis for cross-widget filtering on a
  dashboard ([D64](decisions-dashboards.md#d64--one-transient-dashboard-selection-filters-the-other-widgets)).

### D17 — Drill-down is a single-table hierarchy on the bound-param path
One hierarchy per worksheet: ≥2 ordered columns from **one table**. The current level leads the
group-by; a click drills finer and pins the value as a bound `=` filter.
- **Why one table?** Every pin is an equality filter on the drill table, so drilling can never force an
  unresolved join. Cross-table hierarchies would need join reasoning per pin.
- **Why a click drills instead of selecting:** on an active hierarchy, descending *is* the natural
  gesture. The finest level is a no-op, and table/KPI views navigate via the breadcrumb.

### D18 — Marks card and Pages shelf are client encodings on the existing query shape
Color/Size/Label/Detail/Tooltip/Shape/Path/Angle and Pages reuse the bounded aggregate/join query and
the bound-filter path — **no new endpoints or query shapes**.
- The canonical plan is derived in one place (`planDims` / `planMeasures`) and re-derived by the
  renderer. With no encodings set, the plan is byte-identical to a plain shelves plan.
- **Continuous colour is scatter-only:** `visualMap` over point arrays is the clean idiom.
  Bar-gradient is not supported.
- **Gantt Bar and Density marks are not built** (no clean bounded shape). **Maps are out of scope** —
  no geo data source, tiles or projection; that would need its own decision.
- The encodings live in one **icon toolbar** with a single open editor, not stacked lanes, so the
  header stays short as channels are added.

## Hosting

### D8 — .NET 10 LTS on AlmaLinux 9
- **Why:** it is the current long-term-support (LTS) release, for the longest support horizon, and it
  is available from the AlmaLinux 9 appstream.

### D9 — App source lives outside the KB, on the build host
The app is built at `/unified/user/cj/web_development/prototype/dashboard_builder/` on `10.168.49.20`.
This KB (`…/knowledge/web_development/dashboard_builder`) holds docs only.
- Both are on the same shared filesystem, so a KB session can build the app directly.
- The app folder is a local git repo (so changes can be reviewed as diffs); the KB is the
  documentation of record. See [development.md](../../operations/development.md).

### D20 — Apache reverse proxy + `PathBase` + systemd
Every .NET app on the host sits behind **Apache httpd**, which terminates TLS at a path prefix and
proxies to a localhost Kestrel port. **systemd** runs the app off a framework-dependent publish.
- The app is `PathBase`-aware (config key `PathBase`), and the client derives the same prefix from its
  module URL, so nothing hardcodes it.
- The firewall exposes only the Apache ports. Live layout: [deployment.md](../../operations/deployment.md).

### D21 — Workbooks persist in the browser, not on the server
The builder state auto-saves to the browser's `localStorage` (one workbook per server + user) and moves
between browsers as an exported JSON file. Nothing is stored server-side, so D2 holds — no app database,
no accounts.
- **Why:** losing everything on reload was the biggest gap against Tableau's saved workbooks, and the
  browser can close it without new infrastructure or a new attack surface.
- **Never stored:** the connection, host credentials or any password. A workbook reopens against
  whatever server the session is connected to.
- **Keyed by server + user** so a workbook built against one server never auto-opens against another.
- **Trade-off:** not shared across browsers or users; cleared with the site data. Export is the backup.
- **Rejected:** server-side JSON files keyed by session (sessions reset on restart: storage without durability).
- Detail: [workbook.md](../../features/workbook/workbook.md).

### D23 — Validation contract: validate on both sides, server authoritative, reject don't clamp
Every input is checked **twice**: inline on the client (`Core/validate.js`, so the user sees the problem
at the field) and authoritatively on the server (`ClickHouse/RequestValidation.cs`). Detail:
[api.md § Errors and Limits](../api.md#errors), [workbook.md](../../features/workbook/workbook.md#validation-parseworkbook).
- **Reject rather than silently clamp, drop or coerce.** Dropping extra filters, truncating `in` lists,
  clamping `Limit` or ignoring a sort alias would each produce wrong results without a word. Instead
  each is a 400 with a sentence naming the input. Internal clamps remain only as defence in depth.
- **One error shape** `{ error, field? }` with honest codes ([api.md § Errors](../api.md#errors)); a typed filter
  value that doesn't fit its column is a 400, not a ClickHouse 502 ([typed values](../api.md#typed-filter-values)).
- **The server filter cap is higher than the client's** because the worksheet appends its own filters
  ([limits](../api.md#limits)), so a server cap equal to the client's would reject legitimate views.
- **The client mirrors the server's limits** (`LIMITS` ↔ `ApiLimits`). Drops that would break a view cap
  are refused with a toast. There is no automated drift test between the two.
- **Workbooks are validated field by field.** Repairs are reset-to-default **and reported** (issues
  dialog), hard failures refuse the file, and an unreadable stored workbook is backed up, never
  overwritten.
- **Known gaps:** an unmatched `/api/*` route returns an empty-body 404; the client rejects IPv6 zone IDs
  the server accepts.

### D24 — Showing all data: bounded requests (paging, Other, date grouping)
"Show all data" is met **without unbounded queries** — every request still has a `LIMIT` (golden rule 3):
- **Tables page.** The Table view asks for 500 rows (`limit` + `offset`) plus the group count
  (`withTotal`), and loads the next page as the pane nears its end. Every row is reachable and each
  request is small. Paging is stable: the `ORDER BY` always ends with every group key, and keys are unique.
- **Charts summarise.** Top-N **All** (the default) asks for up to **5000** groups (`MaxRowLimit`), so
  "All" never silently means a smaller number and flipping the sort never shows *different* groups.
  - A one-dimension bar / pie / donut / treemap folds everything past its limit into one **Other** mark
    (`otherBucket`), so totals stay right.
  - A date/time axis is **grouped by a calendar grain** (`dateBucket`, Format → Group dates, `auto` by
    default), so a long time range returns months, not millions of timestamps.
  - Past 1,000 categories an axis zooms (slider), and past 1,500 marks the chart draws on canvas.
- **CSV export** asks for the whole result up to **100,000** rows (`MaxExportRows`), no Top-N.
- **Rejected:** a no-`LIMIT` "All" (rejected at the user's request — one group-by on a high-cardinality
  key could return millions of groups); virtualised table rendering (the crosstab's merged row headers
  don't survive it — the table redraws from the loaded rows instead, fine to tens of thousands of rows).
- **Known limits:** a date-grouped axis can't be click-filtered (its labels are bucket starts). "Other"
  is skipped (the chart is still drawn) if the server refuses the `transform_null_in` setting.

### D25 — A short-lived server result cache (and approximate mode)
Worksheet results are kept **in the server's memory for 60 seconds** per server + user + exact request
(`IMemoryCache`, ~256 size units; the key never holds the password).
- **Why:** two dashboards, two users of the same account, or a quick back-and-forth reuse one
  ClickHouse query. `fresh` bypasses and replaces the entry; a cached result says so on the info line.
- The cache is per process (a restart empties it) and holds only results the user could already see —
  no application database (D2 stands).

**Approximate mode** (Format) trades exactness for speed and is always labelled; what it changes in SQL is in
[clickhouse-integration.md](../clickhouse-integration.md#the-queries-all-read-only).

## Open questions

| # | Question | Leaning |
|---|---|---|
| **O1** | Should workbooks persist on the server (shared across browsers/users)? | Browser persistence is decided ([D21](#d21--workbooks-persist-in-the-browser-not-on-the-server)). Server-side storage only with accounts — see [platform.md](../../backlog/platform.md). |
| **O2** | Where are multiple saved connections stored? | One active connection per session, not saved. Later: named profiles **without** persisting passwords server-side. |
| **O3** | How far does dashboard composition go? | Worksheets and dashboards are separate tab kinds and a dashboard's data is built ([D61](decisions-dashboards.md)); the board canvas and its editing are built ([D62](decisions-dashboards.md), [D63](decisions-dashboards.md)); composition would revisit O1 only if dashboards were shared. |
