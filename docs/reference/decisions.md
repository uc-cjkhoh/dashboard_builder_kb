# Decisions & rationale

The "why" record: each architecture/design decision, its reason, and what was rejected. When a
decision changes, **edit its entry in place** (and the doc it affects) in the same change; resolve an
open question by promoting it to a decision.

## Platform & safety

### D1 — Read-only against ClickHouse
The app introspects schema and runs bounded `SELECT`s; it issues **no DDL/DML**. This keeps the
security surface small, matches the statement (browse / drag / relate / chart — not edit data), and
means a leaked or over-scoped connection can't mutate the server. Enforced as
[golden rule 1](../conventions/golden-rules.md#1-the-server-is-read-only-against-clickhouse).
- **Enforced twice.** Our SQL builders emit only reads, *and* every query carries ClickHouse's own
  `readonly=2`, so the server itself refuses a write even if a builder bug produced one. The same
  settings add a server-side time limit and cancel-on-disconnect
  ([clickhouse-integration.md](clickhouse-integration.md#database-level-guards)).
- **Why `readonly=2`, not 1:** level 1 also forbids changing settings, which would reject the driver's
  own per-request settings and our time limit. Level 2 still blocks every write and DDL.
- **A server that refuses a setting doesn't block connecting.** The connection steps down at connect
  time: a profile constraint (code 452, usually on the time limit) drops only `max_execution_time`; an
  account already locked read-only (code 164) runs with no settings — the server is guarding it. Only if
  `readonly` itself is constrained does read-only rest on our SQL builders alone
  ([guards](clickhouse-integration.md#database-level-guards)).

### D2 — Thin, session-scoped proxy; no application database
The statement needs no user accounts or server-side records. Builder state lives in the browser; the
server only holds the session's connection. Avoiding an app DB removes a whole subsystem (schema,
migrations, ORM) and its attack surface.
- **Trade-off:** dashboards don't survive a reload → [O1](#open-questions).

### D3 — `ClickHouse.Client` over the HTTP interface
A mainstream, maintained ADO.NET driver with familiar `DbConnection`/`DbCommand` semantics over HTTPS.
- **Rejected:** the native TCP protocol (`9000` / TLS `9440`) — marginally faster, but a heavier client
  with no benefit for introspection and bounded aggregates. Revisit only if large streamed reads become
  a feature.

### D6 — Identifiers validated against the live catalog + backtick-quoted
DB/table/column names can't be bound as parameters, so they are interpolated. To prevent injection each
must exist for the current connection and is backtick-escaped, in one helper (`ClickHouse/Identifier.cs`).
Values, by contrast, are always bound. See
[clickhouse-integration.md](clickhouse-integration.md#identifier-injection).

### D10 — Connect over TLS only: HTTPS port `8443`
The target ClickHouse exposes only its secure ports — `8443` (HTTPS, used) and `9440` (native TLS,
unused per D3). Plaintext `8123`/`9000` are unavailable, so `secure` defaults on and `8443` is the
default port. A local throwaway container may still use plain `8123` for testing.

### D11 — TLS certificate validation: safe-by-default, explicit per-connection opt-in
A secure connection **validates the server certificate** against the host trust store. The user may opt
in per connection with "Trust invalid / self-signed certificate" (`allowInvalidCert`), shown only under
Secure and warning while ticked. The bypass is gated on TLS (`allowInvalidCert && secure`) and applied
via `DangerousAcceptAnyServerCertificateValidator` only when `BypassesCertificateValidation(info)` is
true; the connection summary flags it (`TLS ⚠ cert unverified`).
- **Consequence:** the known target is self-signed, so connecting to it requires the opt-in — or,
  better, trusting its CA.
- **Trade-off:** with the opt-in there is no MITM protection on the ClickHouse leg; the stronger fix is
  trusting the server's CA or pinning its cert. Traffic is always encrypted (D10).

## Frontend & design

### D4 — Vanilla JS + hand-written CSS (no SPA framework)
One page with bespoke interactions (drag/drop canvas, SVG links, worksheet). A framework's routing/state
machinery buys little and adds build tooling and payload; native APIs (HTML5 DnD, `<dialog>`,
`<select>`, `fetch`) cover the needs.
- **Rejected:** a React/TS SPA (build pipeline + bundle for one page); **Blazor Server** (a SignalR
  circuit and server round-trips for pure-client canvas interaction is the wrong shape). Revisit React
  only if the canvas grows into a large stateful editor.

### D7 — Design language: RED / BLACK / WHITE, fixed no-scroll shell
**Superseded by [D22](#d22--fluent-glass-design-language).** The original red / black / white identity. Retired because red was both the brand accent and the danger
colour (`--brand-soft` and the danger tint were the same hex), so a soft-red flash read as an error. What
survives: the **fixed no-scroll shell**, token-driven CSS, WCAG-AA contrast, and status by icon + text +
colour.

### D13 — Charting via self-hosted Apache ECharts (SVG renderer), themed from tokens
Charts render through ECharts vendored at `Features/Core/vendor/echarts.min.js` (**no CDN**, served
`no-cache`), loaded as a global before the module graph. `chart.js` is the only adapter and themes every
chart from `--chart-*` tokens; the SVG renderer is crisp and enables SVG export. Table, Text and KPI stay
native DOM.
- **Why a library:** the chart vocabulary (scatter, heatmap, treemap, box plot, dual-axis, legends,
  tooltips) is costly to hand-build. A viz library is **not** an SPA framework — D4 holds.
- **Rejected:** Vega-Lite — a heavier multi-file stack with less convenient imperative theming/resize.
- **Series colour:** one series wears the accent (`--accent`); several draw the categorical ramp
  `--chart-cat-1..8` (light and dark values) with a legend.

### D19 — MVC in feature folders
ASP.NET Core MVC with **one folder per feature** under `Features/`: controller, view partial
(`_<Feature>.cshtml`), stylesheet and ES modules together. Features: Shell, Connection, Schema, Canvas,
Relations, Tabs, Dashboard. Shared server infra stays in `ClickHouse/`; shared frontend in
`Features/Core/`. API controllers subclass `Features/ApiControllerBase.cs` (`NotConnected` /
`SafeError`) and return `IResult`.
- **Serving assets outside `wwwroot`:** a second static-file provider maps `/features` with a content
  type map of **only `.css`/`.js`** (`ServeUnknownFileTypes=false`), so co-located `.cs`/`.cshtml`
  return 404. The csproj marks `Features/**/*.css;*.js` as `Content` copied on publish.
- **Why:** a single 1k-line `site.css` and a flat `js/` had outgrown easy navigation; co-locating a
  feature's server, view, style and script makes each region self-contained. Still vanilla, no build
  step (D4).

### D22 — Fluent glass design language
Supersedes [D7](#d7--design-language-red--black--white-fixed-no-scroll-shell).
Windows 11 Fluent structure with Flat Design 2.0 surfaces: **warm neutrals + one crimson accent**,
**glass chrome** (sidebar, tab bar, worksheet header: translucent tint + backdrop blur + 1px stroke + top
rim) over a warm background wash, **solid data surfaces and overlays** (entity cards, chart area, crosstab,
menus, popovers, toasts, dialogs), **light and dark** (System / Light / Dark toggle). Spec: [DESIGN.md](../../DESIGN.md),
[tokens.md](../design/tokens.md).
- **Red accent without red-means-error ambiguity** (the reason D7 was retired): danger is a distinct
  vermilion (`--danger-*`) and always carries an icon and words; field pills are blue / teal / violet;
  the focus ring is neutral ink, and a focused input keeps a neutral border with an accent underline, so
  focus never looks like an invalid field.
- **Why:** the red / black identity was heavy, ambiguous (brand vs. danger) and showed every control at
  once. A calmer palette with progressive disclosure (Advanced connection settings, the encodings More
  menu, the Workbook menu, collapsible field groups) lets a first-time user see only what matters —
  nothing is removed, and an encoding that holds fields is never hidden.
- **Glass only where nothing sits beneath it but the wash.** A blurred panel over content lets the text
  underneath read through the text on top, so anything that floats (menus, popovers, toasts, dialogs) is
  solid. `@supports` and `prefers-reduced-transparency` fall back to an opaque `--surface-2`.
- **Light / dark is a viewer preference** — System (follows `prefers-color-scheme`, the default) / Light /
  Dark, remembered per browser and never saved in the workbook: it is how *this* viewer wants to read,
  not part of the shared analysis. One `data-scheme` attribute drives the tokens
  ([tokens.md § Light and dark](../design/tokens.md#light-and-dark)).
- **Icons:** one self-hosted inline-SVG set (`Core/icons.js`) replaces Unicode glyph icons; no icon font.
- **Calm motion:** no hover-lift transforms, shimmer or pulse; durations 150 / 200 / 250 ms, all zeroed
  under `prefers-reduced-motion`.
- **`--ink-3` is `#5b6b81`**, darker than the Fluent grey, to reach ≥ 4.5:1 on `--surface-2`.
- **Rejected:** a from-scratch view rewrite (risk in the 1.8k-line `dashboards.js`) and a colour-only
  reskin (doesn't reduce visual weight). The module graph and markup stayed; the token block was
  replaced and each stylesheet re-pointed by meaning.

## Builder model & worksheet

### D5 — Relationships are logical declarations, not database constraints
ClickHouse enforces no foreign keys and no uniqueness (a MergeTree primary key is a sparse index). The
1:1 / 1:N / N:1 / N:M links are the **user's assertions**, used for joins and layout; the DB is never
asked to create or validate them.

### D12 — Subtabs are dashboards over one shared data model
The dragged tables + relationships form **one shared data model** (the pinned Data Model tab);
dashboards are built *from* it. Each dashboard tab **is one Tableau-style worksheet** — a field pane
plus shelves you drag fields onto.
- **Joins are executed.** Fields from different tables join automatically along the drawn
  relationships: the client finds a join path (BFS over the relationship graph); `QueryAsync` builds
  aliased, identifier-safe `INNER JOIN`s. Fan-out on the many side is the user's declared intent —
  cardinality is not enforced. Unrelated tables → a "draw a relationship" warning.
- **Rejected:** one independent entity canvas per subtab — the statement asks to "build a dashboard
  from the dragged tables", i.e. one model, many views.

### D14 — Colour marks are an extra group-by the client pivots into series
A categorical Colour field is sent as **one more group-by**, appended last; the client pivots that
trailing key into one series per value (bar → grouped, stacked → stacked, line/area → one line each; a
Table gets an extra header level). No new query shape, so D1/D6 are untouched.
- **Constraints:** colour-split needs one measure (else a hint); types outside `COLOR_USES` show a lane
  note rather than mis-querying; combos stay capped by the query `LIMIT`; past 8 values the ramp
  repeats and the legend disambiguates.
- **Pill tint:** `--enc-*` violet separates encoding pills from dimensions (`--dim-*` blue) and measures
  (`--meas-*` teal).
- **Rejected:** a dedicated server `color` field — it is just a group-by.

### D15 — Statistical charts, export and richer filters stay on read-only, bounded, bound-param paths
- **Heatmap/treemap** reuse the multi-dimension `/api/query`; **histogram** and **box plot** are the only
  new shapes — single-table (a distribution is one column), so they take their own endpoints rather
  than complicating `QueryAsync`. Bins clamped 1..100; the max value clamped into the last bin.
- **Export:** SVG/PNG are client-only; CSV reuses `QueryAsync` and `CsvUtil` adds a formula-injection
  guard because exported cells open in spreadsheets.
- **Filters:** `in` (from a bounded distinct-values query) and `between` bind as typed parameters via
  the pure `BuildCondition`; an empty `in` / partial range is a no-op, never `IN ()`.
- **Testing:** the safety-critical builders are pure functions unit-tested with hostile input, so SQL
  and parameter shapes are asserted without a live server.
- **Not supported:** histogram/box-plot CSV (their shape isn't a `QueryRequest`).

### D16 — Click-to-filter is a select-then-act worksheet selection
A dashboard is one worksheet, so clicking a mark **selects** its primary-dimension value and a chip
offers **Keep only** / **Exclude** / clear, applied as a bound filter only when the column's table is
already in the query (a click never forces a join).
- **Why not filter immediately (Tableau's filter action)?** On a single view, self-filtering to the
  clicked value collapses the chart to one mark. Select-then-act keeps it useful (Exclude is handy on
  one chart) and non-destructive.
- **Scope:** bar/stacked/line/area/combo/pie/donut/scatter; types whose marks don't map 1:1 to a
  primary value, and null values (can't bind `= NULL`), are no-ops. The same `sheet.selection` is the
  basis for cross-worksheet filtering ([P24c](../backlog/p24c-cross-widget-filtering.md)).

### D17 — Drill-down is a single-table hierarchy on the bound-param path
One hierarchy per worksheet: ≥2 ordered columns from **one table**. The current level leads the
group-by; a click drills finer and pins the value as a bound `=` filter.
- **Why one table?** Every pin is an equality filter on the drill table, so drilling can never force an
  unresolved join. Cross-table hierarchies would need join reasoning per pin.
- **Why a click drills instead of selecting:** on an active hierarchy, descending *is* the natural
  gesture; the finest level is a no-op and table/KPI views navigate via the breadcrumb.

### D18 — Marks card and Pages shelf are client encodings on the existing query shape
Color/Size/Label/Detail/Tooltip/Shape/Path/Angle and Pages reuse the bounded aggregate/join query and
the bound-filter path — **no new endpoints or query shapes**. The canonical plan is derived in one
place (`planDims` / `planMeasures`) and re-derived by the renderer, so with no encodings set the plan is
byte-identical to a plain shelves plan.
- **Continuous colour is scatter-only** — `visualMap` over point arrays is the clean idiom;
  bar-gradient is not supported.
- **Gantt Bar and Density marks are not built** (no clean bounded shape). **Maps are out of scope** —
  no geo data model, tiles or projection; that would need its own decision.
- **Pages autoplay respects `prefers-reduced-motion`** (Play omitted; stepping always works).
- The encodings live in one **icon toolbar** with a single open editor, not stacked lanes, so the
  header stays short as channels are added.

## Hosting

### D8 — .NET 10 LTS on AlmaLinux 9
The current LTS, for the longest support horizon; available from the AlmaLinux 9 appstream.

### D9 — App source lives outside the KB, on the build host
The app is built at `/unified/user/cj/web_development/prototype/dashboard_builder/` on `10.168.49.20`;
this KB (`…/knowledge/web_development/dashboard_builder`) holds docs only. Both are on the same shared
filesystem, so a KB session can build the app directly. The app folder is a local git repo (so changes can
be reviewed as diffs); the KB is the documentation of record. See
[development.md](../operations/development.md).

### D20 — Apache reverse proxy + `PathBase` + systemd
Every .NET app on the host sits behind **Apache httpd** terminating TLS, at a path prefix, proxied to a
localhost Kestrel port and run by **systemd** off a framework-dependent publish. The app is
`PathBase`-aware (config key `PathBase`) and the client derives the same prefix from its module URL, so
nothing hardcodes it. The firewall exposes only the Apache ports. Live layout:
[deployment.md](../operations/deployment.md).

### D21 — Workbooks persist in the browser, not on the server
The builder state auto-saves to the browser's `localStorage` (one workbook per server + user) and moves
between browsers as an exported JSON file. Nothing is stored server-side, so D2 holds — no app database,
no accounts.
- **Why:** losing everything on reload was the biggest gap against Tableau's saved workbooks, and the
  browser can close it without new infrastructure or a new attack surface.
- **Never stored:** the connection, host credentials or any password. A workbook reopens against
  whatever server the session is connected to.
- **Keyed by server + user** so a workbook built against one server never auto-opens against another.
- **Trade-off:** not shared across browsers or users; cleared with the browser's site data. Export is
  the backup and the way to share.
- **Rejected:** server-side JSON files keyed by session — sessions are in-memory and reset on restart,
  so it would add storage without durability.
- Detail: [workbook.md](../features/workbook.md).

### D23 — Validation contract: validate on both sides, server authoritative, reject don't clamp
Every input is checked **twice** — inline on the client (`Core/validate.js`, so the user sees the problem
at the field) and authoritatively on the server (`ClickHouse/RequestValidation.cs`). Detail:
[api.md § Errors and Limits](api.md#errors), [workbook.md](../features/workbook.md#validation-parseworkbook).
- **Reject rather than silently clamp, drop or coerce.** Before, extra filters were dropped, `in` lists
  truncated, `Limit` clamped and a sort alias ignored — all producing wrong results without a word. Now
  each is a 400 with a sentence naming the input; internal clamps remain only as defence in depth.
- **One error shape** `{ error, field? }` with honest codes: 400 invalid input · 404 unknown schema name ·
  409 not connected · 413 body > 256 KB · 502 ClickHouse failure · 504 timeout · 500 our bug (with a trace
  ref). No type names or credentials ever reach the body.
- **Typed filter values:** a value is parsed by its column's category before binding; a mismatch is a 400,
  not a ClickHouse 502. Temporal values are ISO throughout so shown values round-trip as filters.
- **Server filter cap is 20, the client's is 8.** The worksheet appends the shared filters (≤ 4), the drill
  path (≤ 5), the page, the selection and the date range to the user's filters, so a server cap of 8 would
  400 legitimate views.
- **The client mirrors the server's limits** (`LIMITS` ↔ `ApiLimits`); drops that would break a view cap
  are refused with a toast. There is no automated drift test between the two.
- **Workbooks are validated field by field**; repairs are reset-to-default **and reported** (issues
  dialog), hard failures refuse the file, and an unreadable stored workbook is backed up, never
  overwritten.
- **Unused endpoints removed:** `…/aggregate`, `…/preview`, `…/count` had no callers and are gone.
- **Known gaps:** an unmatched `/api/*` route returns an empty-body 404; the client rejects IPv6 zone IDs
  the server accepts.

### D24 — Showing all data: bounded requests (paging, Other, date grouping)
"Show all data" is met **without unbounded queries** — every request still has a `LIMIT` (golden rule 3):
- **Tables page.** The Table view asks for 500 rows (`limit` + `offset`) plus the group count
  (`withTotal`), and loads the next page as the pane nears its end — every row is reachable, each
  request small. Paging is stable: the `ORDER BY` always ends with every group key, and keys are unique.
- **Charts summarise.** Top-N **All** (the default) asks for up to **5000** groups (`MaxRowLimit`, raised
  from 500 — before, "All" silently meant 50, so flipping the sort showed *different* groups). A
  one-dimension bar / pie / donut / treemap folds everything past its limit into one **Other** mark
  (`otherBucket`), so totals stay right. A date/time axis is **grouped by a calendar grain**
  (`dateBucket`, Format → Group dates, `auto` by default) so a long time range returns months, not
  millions of timestamps. Past 1,000 categories an axis zooms (slider) and past 1,500 marks the chart
  draws on canvas.
- **CSV export** asks for the whole result up to **100,000** rows (`MaxExportRows`), no Top-N.
- **Responses are compressed** (Brotli/gzip, fastest level) — JSON pages shrink 5–10×.
- **Rejected:** a no-`LIMIT` "All" (built, then reverted at the user's request — one group-by on a
  high-cardinality key could return millions of groups); virtualised table rendering (the crosstab's
  merged row headers don't survive it — the table redraws from the loaded rows instead, fine to tens of
  thousands of rows).
- **Known limits:** a date-grouped axis can't be click-filtered (its labels are bucket starts); "Other"
  is skipped (chart still drawn) if the server refuses the `transform_null_in` setting.

### D25 — A short-lived server result cache (and approximate mode)
Worksheet results are kept **in the server's memory for 60 seconds** per server + user + exact request
(`IMemoryCache`, ~256 size units; the key never holds the password), so two dashboards, two users of the
same account, or a quick back-and-forth reuse one ClickHouse query. **Refresh** sends `fresh` to bypass
and replace the entry; a cached result says so on the info line. It is per process (a restart empties it)
and holds only results the user could already see — no application database (D2 stands).
**Approximate mode** (Format) trades exactness for speed, always labelled: `uniq` for distinct counts, and
a 10% `SAMPLE` (counts and sums scaled by `_sample_factor`) on a base table that declares a sampling key.
If the server refuses the sampled query it runs once more unsampled (logged).

Calculated-field decisions D26–D52: [decisions-calculated-fields.md](decisions-calculated-fields.md).

## Open questions

| # | Question | Leaning |
|---|---|---|
| **O1** | Should workbooks persist on the server (shared across browsers/users)? | Browser persistence is decided ([D21](#d21--workbooks-persist-in-the-browser-not-on-the-server)). Server-side storage only with accounts — see [platform.md](../backlog/platform.md). |
| **O2** | Where are multiple saved connections stored? | One active connection per session, not saved. Later: named profiles **without** persisting passwords server-side. |
| **O3** | How far does dashboard composition go? | Today one worksheet per tab; multi-worksheet dashboards are the [P24a + b spec](../backlog/p24-dashboards-spec.md) and would revisit O1. |
