# Modules — the screens & panels

How the single page decomposes into functional regions, what each does, and which
design classes ([DESIGN.md](../../DESIGN.md)) and endpoints ([ARCHITECTURE.md](../../ARCHITECTURE.md))
it uses. Everything lives on **one page**; "modules" are regions, not separate routes.

```
┌─────────────────────────┬────────────────────────────────────────────────┐
│  SIDEBAR (black)         │  CANVAS (white)                                 │
│  ┌───────────────────┐  │  ┌──────────────────────────────────────────┐  │
│  │ 1 Connection panel │  │  │ 5 Subtab strip:  [Dashboard 1] [+]        │  │
│  ├───────────────────┤  │  ├──────────────────────────────────────────┤  │
│  │ 2 Database picker  │  │  │ 4 Canvas / dropzone                       │  │
│  ├───────────────────┤  │  │    ┌─ entity ─┐        ┌─ entity ─┐        │  │
│  │ 3 Table list       │  │  │    │ orders   │──1:N──▶│ order_it │        │  │
│  │   [orders]  ⠿drag  │  │  │    └──────────┘        └──────────┘        │  │
│  │   [customers]      │  │  │ 6 Widgets (KPIs/charts) [later phase]     │  │
│  └───────────────────┘  │  └──────────────────────────────────────────┘  │
└─────────────────────────┴────────────────────────────────────────────────┘
```

> **Sidebar (all sections):** black chrome with a refined brand mark, tight uppercase section
> labels, flat draggable table chips, and thin themed scrollbars. It is **resizable** — drag the
> right-edge handle (`sidebar.js`, `.sidebar__resizer`) to set `--sidebar-w`, capped at **30% of
> the viewport**. Modern-minimalist language adapted from the reference admin console.

## 1. Connection panel  ·  sidebar top
Add a ClickHouse connection: host, port (**`8443`** — the server is TLS-only; native TLS
is `9440`), user, password, `secure` toggle (**on**).
**Connect** validates via `POST /api/connection` and shows a connection **indicator pill**
(idle → connecting → connected / failed). Until connected, the database picker, table
list, and canvas dropzone are gated (shown via the `hidden` attribute). Credentials go
to the server session only — never echoed back.
> **User account gotcha:** ClickHouse users can be **source-IP-restricted**, and a blocked
> IP is reported as a *false* "password is incorrect" (`401 … REQUIRED_PASSWORD`). The
> `default` user on the `10.168.49.13` server is localhost-only, so from the app host
> (`10.168.49.20`) you must use a different, network-enabled account. See
> [clickhouse-integration.md](../clickhouse-integration.md#driver--connection).
- Classes: `.conn-form`, `.form-field`, `.pill--ok/warn/danger/muted`, `.toast`.
- Endpoint: `POST /api/connection`, `GET /api/connection` (restore on load), `DELETE /api/connection`.
- **Built (P2):** wired end-to-end in `connection.js` — pill idle→connecting→connected/failed,
  toast feedback, and the schema section gated via `hidden` until connected. (The
  `allowInvalidCert` flag defaults on server-side per [D11](../project/decisions.md); no UI toggle
  yet.)
- **Refined:** once connected the form is **replaced by a compact summary** (`.conn-summary`)
  showing the connected **host** + `user · TLS · :port`, with icon actions to **change** (✎,
  re-opens the form with a Cancel) or **disconnect** (⏻). The form returns on disconnect.

## 2. Database picker  ·  sidebar
Once connected, a native `<select>` lists databases from `GET /api/databases`
(`SHOW DATABASES`). Choosing one loads its tables (module 3). Switching databases
replaces the table list but leaves the canvas untouched (an entity keeps the
`db.table` it was dropped from).
- Classes: `.select`. Endpoint: `GET /api/databases`.
- **Built (P3):** `schema.js` fills the `<select>` (with a disabled "Select a database…"
  placeholder) on the `connection:changed` event and clears it on disconnect.

## 3. Table list  ·  sidebar
Draggable **table chips** for the selected database, from
`GET /api/databases/{db}/tables` (`SHOW TABLES FROM {db}`). Each chip is
`draggable="true"` and carries its `db`+`table` in the drag payload. Optional filter box
(`role="search"`) narrows the list. Dragging a chip onto the canvas creates an entity
(module 4).
- Classes: `.table-list`, `.table-chip`. Endpoint: `GET …/tables`.
- Details of the drag mechanics: [drag-and-drop.md](../drag-and-drop.md).
- **Built (P3):** `schema.js` renders the chips (icon + name), sets the
  `application/x-ch-table` dragstart payload, and adds a `＋` **fallback** button that
  dispatches a `table:add` event (canvas.js/P4 will consume both). No filter box yet. The
  list scrolls internally. The `{db}` is validated against the live catalog server-side, so
  an unknown/hostile database name is rejected **404** before any SQL interpolation.

## 4. Canvas & entity view  ·  Data Model
The drop target. Empty state shows a "drag a table here" hint (`.canvas__empty`, toggled
via `hidden`). On drop, the app fetches columns (`DESCRIBE`) and renders an **entity card**:
- head: `db.table` name + collapse caret + remove icon;
- column rows: name, a **type badge**, and a **join-key checkbox** (used by relationships).
- **No row preview** — entity cards are a **uniform height** with an internally-scrolling
  column list; sample/aggregated data lives in **dashboard widgets** (§7), not here.

Cards are repositionable by dragging their head. Removing a card also removes any
relationships attached to it (confirm dialog).
- Classes: `.entity`, `.col-row`, `.entity__grid`, `.data`.
- Endpoints: `GET …/columns`, `GET …/preview?limit=`.
- Data shapes: [data-model.md](../data-model.md).
- **Built (P4):** `canvas.js` accepts drops of the `application/x-ch-table` payload (and the
  `table:add` fallback), renders the card with a **loading→loaded/failed** status (failed
  offers **Retry**), fetches columns+preview in parallel, right-aligns numeric columns and
  marks NULLs, and moves cards by dragging the head (pointer events). The join-key checkbox
  toggles `entity.joinKeys` + a highlight; **drawing relationships from those keys is P5**.
  Preview is bounded server-side (limit clamped to 500). A **caret in the head collapses/expands**
  the columns + preview (`.entity--collapsed`), leaving just the title bar.

## 5. Data Model tab + dashboard subtabs  ·  content top
The view strip is a **pinned "Data Model" tab** (the shared entity canvas — modules 4 & 6) plus
**dashboard subtabs**. The Data Model — dragged tables + relationships — is **shared**; each
dashboard is built *from* it. `[+]` adds a dashboard; dashboards rename (double-click) and close
(confirm if they hold widgets); the active view is `aria-current`. In v1 all state is in-memory
([decisions.md](../project/decisions.md)).
- Classes: `.tabs`, `.tab`, `.tab--model`, `.tab-add`, `.tab__close`, `.tab__label`, `.tab__rename`,
  `.view--model`, `.view--dashboard`.
- **Built:** `tabs.js` + a `store.js` holding one shared model + a `dashboards` list. `store.activeView`
  is the model or a dashboard; `canvas.js`/`relations.js` show `#model-view` when the model is active,
  `dashboards.js` shows the `#dashboard-view` **worksheet** otherwise. A dropped table always goes to
  the shared model. Each dashboard is one worksheet (§7).

## 6. Relationship builder  ·  overlay on canvas
Connect two entities: check a join-key column on each, then draw a link and pick a
**cardinality** (1:1, 1:N, N:1, N:M). The link is rendered as an SVG/segment between the
two column rows, with shape-coded endpoints (one vs. many) and a cardinality badge.
Selecting a link lets you change cardinality or delete it.
- Classes: `.rel-link`, `.rel-end--one/--many`, `.rel-badge`, `.rel-connector`, `.card-choice`.
- Semantics (logical, not DB-enforced): [data-model.md](../data-model.md).
- Interaction: [drag-and-drop.md](../drag-and-drop.md).
- **Built (P5):** `relations.js` — connector handles on checked keys, **click-to-click** creation
  (no drag), a cardinality `<dialog>`, SVG links with shape-coded endpoints + badge, click-to-edit/
  delete, live re-route on move, and cascade cleanup on entity removal / key uncheck.

## 7. Dashboard worksheet (Tableau-style)  ·  dashboard view
Each dashboard **is a worksheet**: a **field pane** (each model table's columns split into
**Dimensions** and **Measures**) beside **Columns / Rows / Filters** shelves and a chart. You
**drag fields onto shelves** to build the chart (`dashboards.js`).
- **Two-tier header (P17).** The worksheet header is split so it scales as features pile on: a slim
  **view bar** on top holds the presentation controls only — **Chart** type (left), **Sort** and
  **Format** (right) — and below it the data shelves are **stacked full-width lanes** (`.ws-shelf-stack`),
  each an aligned **label column + drop zone** (`Columns`, `Rows`, `Filters`). The **Format** panel opens
  as a card directly under the view bar. This replaced the earlier single wrapping row (which grew
  unmanageable once P10/P11 added Sort/Chart/Format). Data pills never enter the view bar; new view
  controls extend the view bar / Format card, new data goes to the shelf lanes.
- **Multi-field shelves.** **Columns** and **Rows** each hold **any number** of field pills; the
  **shelf sets the crosstab axis**. A pill's role defaults from type but is **convertible** via its
  button — `Σ` turns a dimension into a measure, `#` turns a measure into a dimension — so a numeric
  field can group as a dimension, or any field be aggregated. Measure pills show an agg dropdown
  (`sum/avg/min/max/count/countDistinct` for numbers; `count/countDistinct/min/max` for text);
  **countDistinct** counts unique values (`uniqExact`). **Filters** ← fields (op + value pills).
  Dimension pills are red-tinted, measure pills green.
- **Table = a true Rows×Columns crosstab** (`crosstabTable()`). Row-shelf dimensions form the **left
  stub** (nested, with rowSpan-merged repeats); Column-shelf dimensions the **top header** (nested,
  colSpan); measures are the **cell values**. The **measure-name band sits on whichever shelf the
  numeric pills are on** — measures on Columns run across the top, on Rows down the left (transposing
  the grid). Measures on *both* shelves → a note + fallback to the top band. Built by pivoting the
  flat grouped rows client-side (ClickHouse has no `PIVOT`).
- **Chart types (P11).** Picked from a dropdown: **Bar** (grouped at ≥2 measures), **Stacked bar**,
  **Line**, **Area**, **Pie**, **Donut**, **Scatter** (two measures → X/Y), **Combo (dual-axis)** (1st
  measure bars + a right-axis line), **KPI** (big number; with a dimension, an inline **sparkline** of
  the trend), and **Table**. `chart.js` dispatches by family (`buildCartesian`/`buildPie`/`buildScatter`);
  cartesian types flatten `rowDims++colDims` onto the category axis, **one series per measure** (legend
  for ≥2 series; single = brand red, multiple = dataviz categorical palette). No dimensions → **KPI
  tiles**. An invalid field mapping shows a **hint** (e.g. "Scatter plots two measures"), never an
  error. Scatter/combo/stacked read the first two measure pills — **no separate 2nd-measure shelf**,
  since a shelf already holds any number of measures. All on the existing bounded aggregate/join query;
  **histogram** needs a bucketing query shape and lands in P12. True chart-axis orientation
  (measure-on-Columns → horizontal bars, row-dims → facets) is still **Phase 2**.
- **Sort** (`sortControl`). A dropdown of the in-play fields (dimensions + measures) plus an
  **Asc ↑ / Desc ↓** toggle; **default is ascending by the first field**. It drives the query
  `ORDER BY` (the chosen field's `k{n}`/`v{n}` alias); the crosstab always appends the remaining
  dimension keys ascending so the pivot layout stays stable under any sort.
- **Format (P10).** A collapsible **Format** panel (toggled from the shelves row) sets per-chart
  presentation on `sheet.format`, applied without changing the query: **number format**
  (auto/compact/currency/percent + decimals), **date format** for date-like dimension labels,
  **top-N** (caps the chart's `LIMIT`), **legend** show/position, **data labels**, **colour-by-category**
  (single-measure bar), and **X/Y axis titles**. Number/date formats also drive the crosstab and KPI
  tiles via the shared `format.js` helpers. Persists for the session (in-memory, [O1](../project/decisions.md)).
- **Cross-table joins:** fields from *different* tables are joined automatically along the drawn
  relationships — the client finds a **join path** (BFS over the relationship graph) and the
  server (`POST /api/query`) builds the aliased `JOIN`s. Unrelated tables → a "draw a
  relationship" warning, not a bad query.
- Classes: `.worksheet`, `.ws-fields`, `.ws-field`; header (P17): `.ws-viewbar`
  (`.ws-viewbar__group--right`), `.ws-shelf-stack`, `.ws-shelf`, `.ws-toolbtn`, `.ws-charttype__sel`,
  `.ws-format`; `.ws-pill` (`.ws-pill--dimension` / `.ws-pill--measure`), `.ws-kpi-row`, `.ws-spark`;
  crosstab: `.xtab`, `.xt-corner`, `.xt-colhdr`, `.xt-rowhdr`, `.xt-meas`, `.xt-wrap`.
- **Next (Phase 2):** chart-axis orientation (crosstab semantics for bar/line) and **click-to-filter
  actions** (click a bar to filter the sheet — P15). Colour-by-category marks shipped in P10 (single-
  measure bar); a categorical **colour-by a second dimension** across series is still open.

## Cross-cutting UI
- **Toast** (`.toast`, `aria-live`) for transient feedback — success uses `--ok-bg`,
  never `--brand-soft`.
- **Dialogs** (native `<dialog>`) for connect errors detail and destructive confirms.
- **No page scroll**; every list/grid scrolls inside its region ([DESIGN.md](../../DESIGN.md#layout-rules)).
