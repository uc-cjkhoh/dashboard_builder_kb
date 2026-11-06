---
components: [src/DashboardBuilder/Features/Board/board-model.js, src/DashboardBuilder/Features/Core/sheet-schema.js, src/DashboardBuilder/Features/Core/store.js, src/DashboardBuilder/Features/Core/validate.js, src/DashboardBuilder/Features/Dashboard/dashboards.js, src/DashboardBuilder/Features/Workbook/workbook-model.js]
---
# Data model — state shapes

The data shapes the app works with: the server's per-session connection and results, the browser's
store, the worksheet `sheet` object and the saved workbook file. Read it before changing state, a sheet
field or the workbook format.

Server-side shapes are transient; browser shapes live in memory. There is **no application database**
([D2](../decisions/decisions-platform.md#d2--thin-session-scoped-proxy-no-application-database)), so nothing is stored
server-side. The browser keeps the builder state as a **workbook**
([D21](../decisions/decisions-platform.md#d21--workbooks-persist-in-the-browser-not-on-the-server), [file shape](#workbook-file)).
Tags such as P26 or T02-34 are build-plan (Pnn) and backlog (Tnn-nn) item ids.

## Server side (per session / per request)

### Connection

`ClickHouseConnectionInfo`, held in the session-scoped `ConnectionRegistry`. It is never serialized to the
client; `GET /api/connection` returns a password-free view.

| Field | Notes |
|---|---|
| `host` | ClickHouse host |
| `port` | `8443` (HTTPS) on the target server |
| `user` | ClickHouse user |
| `password` | **server-only** — never returned, never logged |
| `secure` | TLS; on by default |
| `allowInvalidCert` | trust a self-signed cert; ticked by default in the form, off when a request omits it; effective only when `secure` |
| `guards` | `QueryGuards` — `Full` / `NoTimeLimit` / `None`: which database-level settings this server accepted at connect ([step-down](clickhouse-integration.md#step-down-when-the-server-refuses-a-setting)) |
| `serverEnforcesReadOnly` | set at connect when the account already rejects setting changes — queries then run without the gateway's guard settings |

### Introspection results (pass-through)

- **databases** — `string[]`; **tables** — `string[]`.
- **columns** — `{ name, type, category }[]`; `type` is the raw ClickHouse string, `category` its
  display category ([type mapping](clickhouse-integration.md#type-mapping)).
- **query** — `QueryResult { rowDimensions, columnDimensions, measures, rows:[{keys, values}], truncated }`.
  - `keys` are strings (ISO for dates) or `null`.
  - **`values` entries are a number, a string (`min` / `max` of a text or date column) or `null`** — never assume a number.
  - `truncated` is true when more groups exist beyond the limit (box plot: `{ groups, truncated }`).
  - Optional: `total` (every group, when `withTotal`), `other: { groups, values }` (the aggregate past the
    limit, when `otherBucket`), `bucket: { key, grain }` (which key was date-grouped).
- **Errors** are always `{ error, field? }` — [api.md](api.md#errors).

## Client side — `Features/Core/store.js`

```
entities:      Map id → Entity              ┐ ONE shared data source
relationships: Map id → Relationship        ┘ (the Data Source tab)
tabs:          [ Tab, … ]                   ONE ordered list — worksheet and dashboard tabs (below)
activeView:    { kind: "model" } | { kind: "worksheet", id } | { kind: "dashboard", id }
bus:           EventTarget — entity:added · entity:loaded · entity:moved · entity:removed
                             rel:changed · view:changed · tabs:changed
                             worksheet:changed { id } · dashboard:changed { id }
```

### Entity

A table dropped onto the canvas ([canvas.md](../concepts/data-source/canvas.md)).

| Field | Notes |
|---|---|
| `id` | `db.table#n` |
| `db`, `table` | source, from the drag payload |
| `x`, `y` | canvas position |
| `columns` | `{ name, type, category }[]` from `DESCRIBE` |
| `el` | the card's DOM node |
| `source` | present on a union / unpivot entity: `{ kind: "union", db, name, tables, columns? }` or `{ kind: "unpivot", db, name, table, columns, keep }`; `table` is then `name`, `columns` come from `/api/source/columns` — [query-sources.md](../concepts/data-source/query-sources.md) |

### Relationship

A **logical** link — the database neither creates nor validates it
([golden rule 5](../development/coding-standards.md#5-relationships-are-logical-declarations-not-database-facts)).

| Field | Notes |
|---|---|
| `id` | client id |
| `from` | `{ entityId, column }` — a column on entity A (it is pinned to A's key strip) |
| `to` | `{ entityId, column }` — a column on entity B |
| `cardinality` | `1:1` · `1:N` · `N:1` · `N:M` — intent, not a data guarantee |
| `joinType` | `inner` (default) / `left` / `right` / `full` (P31, T02-12/13) — which side keeps its unmatched rows (FROM = left, TO = right) |
| `pairs` | optional `[{ from, to }]` — extra column pairs of a compound key (at most 3), on A's and B's entities; their columns count as in this relationship |
| `aggregateFirst` | optional `true` — total each table by the key before joining ([D86](../decisions/decisions-dashboards.md#d86--aggregate-before-joining-is-a-per-relationship-option-on-a-two-table-view)); absent = the plain join |
| `filterDirection` | optional `"single"` (only with `aggregateFirst`) — a filter changes only its own table; absent = both |
| `joinFixed` | `true` once saved by the join dialog: the sides are the link's own. Absent or false with `left`: a link saved before the dialog set it; it keeps the base side |

A column is in at most one relationship. With two or more table cards, each card should be in one; a card
with none is held out of worksheets ([relationships.md](../concepts/data-source/relationships.md)).

### Tabs and dashboards

```
Tab:     { id: "ws#n", kind: "worksheet", name, sheet }                 one worksheet (the editor)
       | { id: "db#n", kind: "dashboard", name, widgets: [Widget], size }  a board of widgets; size = null (automatic) | { width, height } px
       | { id: "st#n", kind: "story", name, steps: [Step] }               ordered captioned steps (Story/story-model.js)
Step:    { caption, target: "ws#n" | "db#n" }                             the worksheet or dashboard the step shows
Widget:  { id: "w#n", kind: "sheet", sheetId: "ws#n", x, y, w, h }       a worksheet's view
       | { id: "w#n", kind: "text", heading, body, x, y, w, h }          a text block
       | { id: "w#n", kind: "image", alt, src, x, y, w, h }              a picture; src = a base64 PNG / JPEG / GIF / WebP data URL
       | { id: "w#n", kind: "nav", label, tip, target, x, y, w, h }      a button; target = a tab id (worksheet or dashboard) | null
       | { id: "w#n", kind: "spacer", x, y, w, h }                       a blank block
```

#### Tab and widget limits

The limits are `LIMITS` in `Core/validate.js`. The rules and the first-free-spot scan are pure, in `Board/board-model.js`.

- Tab names are 1–60 characters. A workbook holds at most **50 tabs** of either kind.
- A dashboard lays widgets on a **12-column snap grid** in whole cells with no overlap: `w` 2–12, `h` 2–24
  (text 1–24), `y + h` ≤ 96, at most **12 widgets**.
- Text: `heading` ≤ 80 and `body` ≤ 2000 characters.
- Images: at most **4 images** per dashboard and 2 MB of picture data per workbook; each file ≤ 256 KB, `alt` ≤ 120.
- A story holds at most **20 steps**; a caption is ≤ 300 characters (rejected past it, never cut).
- A spacer and a nav button are 1–24 rows tall, like text. A button `label` is 1–40 characters and its `tip`
  ≤ 200. Closing the target tab unlinks the button (`target` → null).

#### Store helpers

A widget points at a worksheet by tab id; one worksheet may sit on several dashboards, even twice on one.

- `worksheets()` / `dashboards()` / `stories()` — the tabs of a kind.
- `createWorksheet` / `createDashboard` / `createStory` — null at the tab limit. Also `duplicateWorksheet`.
- `closeTab` — a closed worksheet's widgets leave every dashboard, and a closed worksheet or dashboard's steps leave every story.
- `updateSheet` (→ `worksheet:changed`), `setWidgets` + `nextWidgetId` (→ `dashboard:changed`), `setSteps` (→ `story:changed`).

Nothing here reaches the server; dashboards add no endpoint
([D61](../decisions/decisions-dashboards.md#d61--worksheets-and-dashboards-are-separate-tab-kinds-workbook-format-v2)).

## Worksheet (`sheet`)

`emptySheet()`:

```
{
  columns: [pill], rows: [pill],      // ordered shelves; dimensions before measures
  color:   [pill],                    // ≤1 field — Color encoding (categorical or continuous)
  filters: [{ db, table, column, category, op, value | values, param?, topBy?, bottom? }],   // param: P32; topBy / bottom: P30 top-N
  chartType: "bar",                   // see CHART_TYPES
  sort:      null | { by: fieldId, dir: "asc" | "desc" },
  selection: null | {...}, drill: null | {...}, pages: null | {...},
  collapsed: { rows: [key], cols: [key] },   // T03-29 collapsed crosstab headers; the key exists only once one is collapsed
  tooltipText: null | string,   // T01-19 tooltip template with <Field> placeholders (≤ 300; null = automatic)
  tooltipFormats?: { [field]: { number?, decimals?, date? } },   // T01-19 per-field tooltip formats (≤ 24 fields); absent = the view's formats
  memberColors: {},              // T01-20 { "table.column": { member: "#rrggbb" } } (format.paletteReverse: bool, T03-33; format.colorRamp brand|blue|green|amber|violet, colorMin / colorMax number|null, T03-19; colorScale sequential|diverging, colorPair default|amber-violet|green-violet, colorCentre number|null; colorSteps 0|3–9, 0 = continuous)
  title: null | string, caption: null | string, showTitle: boolean,   // P23 (null = automatic)
  showFilterCards: boolean,                                          // P30
  analytics: null | { ref: { kind, value?, param?, measure? }, band: { from, to, fromParam?, toParam? } | { kind: "stddev", k: 1|2|3 } | { kind: "percentile", lo, hi } | null, trend, forecast, totals: { grand, sub } },   // P21
  urlAction: null | { label, template },   // P39 link action — https:// with {value}
  paramAction: null | { param },           // P39 parameter action — a click can set this parameter (id) to the mark's value
  period: null | { db, table, column, category: "temporal", preset, from, to, compare, compareFrom, compareTo },
  marks:  { size, label, detail: [], tooltip: [], shape, path, angle },
  format: { numberFormat, decimals, currencySymbol, dateFormat, topN, dateBucket, target, downIsGood, conditional, legend,
            dataLabels, colorByDimension, xTitle, yTitle,
            lineStyle, heatmapShape, targetMeasure,
            syncAxes, dualAxis, secondaryType, markerSize, markBorder, markerShape, font, tableAlign, tableDensity, tableShade }
}
```

- **Format font:** `font` `default` | `serif` | `mono` (default `default`) — the family of chart and table text.
- **Format table settings:** `tableAlign` `auto` | `left` | `center` | `right` (default `auto`), `tableDensity` `standard` | `compact` | `roomy` (default `standard`), `tableShade` `none` | `banded` | `header` | `both` (default `none`); they apply to Table and Text views.
- **Format chart settings:**

  | Key | Values |
  |---|---|
  | `lineStyle` | `straight` \| `step` \| `jump` (default `straight`; `jump` is shown as Step (centred)) |
  | `heatmapShape` | `square` \| `circle` (default `square`) |
  | `targetMeasure` | null or a shelf-measure index 1–19 — the bullet's target field; null = the fixed `target` |
  | `syncAxes` | boolean (default false) |
  | `dualAxis` | boolean (default false; line / area right axis) |
  | `secondaryType` | `line` \| `bar` \| `area` (default `line`) |
  | `markerSize` | null (automatic) or a whole number 4–40 |
  | `markBorder` | `none` \| `thin` \| `thick` (default `none`) |
  | `markerShape` | `circle` \| `square` \| `diamond` \| `triangle` (default `circle`) |

  A target field that no longer points at a later shelf measure is ignored and cleared when Format opens.
  An unknown value is reset with a workbook import issue. A workbook without these keys opens unchanged.
- **Pill:** `{ db, table, column, category, role?, agg?, datePart?, tableCalc?, choices? }`.
  - `datePart` (P26) is on a date dimension; `tableCalc` (P27) `{ type, along, window?, using? }` on a
    measure; `choices` (P40) holds the slot's alternative fields.
  - `role` overrides the type default: `'dimension'` → `GROUP BY`; `'measure'` → aggregated with `agg` ∈ `aggsFor(category)`.
    That is `sum/avg/min/max/median/stddev/variance/count/countDistinct/countNonNull/attr` for numbers,
    `count/countDistinct/countNonNull/min/max/attr` for text and dates, and `count/countDistinct/countNonNull` otherwise.
    `roleOf(f)` in `dashboards.js` resolves it.
- **Filter:** `op` ∈ `= != > >= < <= in between`. `value` is a string for the scalar operators; `values` is
  a string list for `in` (≤ 500) and a `[from, to]` pair for `between`. `category` decides how the value
  is parsed ([worksheet-filters.md](../concepts/worksheet/worksheet-filters.md#filters)). When absent
  (in workbooks saved without it), it is back-filled from the column catalog.
- **Caps** (client `LIMITS`, `Core/validate.js`; the server's view caps are in
  [api.md § Limits](api.md#limits)): 20 pills per shelf · 12 dimensions · 10 measures · 8 filters ·
  6 drill levels · 100 entities · 200 relationships · 50 tabs · 12 widgets per dashboard · tab name 60 characters · axis
  title 80 · filter value 1000.
- **Format defaults:** `numberFormat:"auto"`, `decimals:null`, `currencySymbol:"$"`,
  `dateFormat:"auto"`, `topN:null` (All — up to 5000), `dateBucket:"auto"`, `conditional:{}` (P37: `{ [db.table.column:agg]: { mode: none|scale|bars, scale: sequential|diverging, mid, rules: [{ op, value, tone: good|bad|warn|info }] } }`), `legend:"auto"`, `dataLabels:false`,
  `colorByDimension:false`, axis titles `null`.

### Marks, pages, selection, drill

| Key | Shape | Meaning |
|---|---|---|
| `marks.size` | pill \| null | numeric → scatter bubble size |
| `marks.label` | pill \| null | value drawn on each mark |
| `marks.detail` | [pill] | dimensions adding group-by granularity |
| `marks.tooltip` | [pill] | custom tooltip lines |
| `marks.shape` | pill \| null | dimension → point symbols (scatter family) |
| `marks.path` | pill \| null | orders line/area vertices |
| `marks.angle` | pill \| null | radial magnitude (pie already maps its measure to angle) |
| `pages` | `{ db, table, column, category, index, members? }` | the current member `members[index]` filters the view |
| `selection` | `{ db, table, column, value, label, action }` | a clicked mark; `action` null \| `"keep"` \| `"exclude"` |
| `drill` | `{ levels:[pill], depth, path:[{column, value, label}] }` | ≥2 levels from one table; `path.length === depth`; depth clamped to the levels |

How each reaches the query: [worksheet-marks.md](../concepts/worksheet/worksheet-marks.md#marks). Every
pinned value (`pages`, `selection`, `drill.path`) becomes a **bound** filter, never interpolated.

## Workbook file

What [workbook.md](../concepts/workbook/workbook.md) saves to `localStorage` and exports (`workbook-model.js`):

```
{
  format: "dashboard-builder-workbook", version: 2 (integer ≥ 1; version 1 files still open), savedAt: ISO-8601,
  entities:      [ { id, db, table, x, y, joinKeys: [column], source? } ],   // source: a union / unpivot entity (its table = source.name); re-validated on open, a bad one skipped
  relationships: [ { from: { entityId, column }, to: { entityId, column }, cardinality, joinType, pairs?, aggregateFirst?, filterDirection? } ],
  worksheets:    [ { name, sheet } ],      // sheet as above, minus pages.members
  dashboards:    [ { name, widgets: [ { kind: "sheet", sheet: worksheetIndex, x, y, w, h }
                                    | { kind: "text", heading, body, x, y, w, h } ],
                     size?: { width, height },   // fixed pixels; absent = automatic (older files). Anything outside the limits (not whole pixels, 320–3840 × 240–2400) → automatic with an import issue, never clamped
                     range?: { minWidth?, maxWidth?, minHeight?, maxHeight? },   // an automatic board's pixel limits (same limits; min <= max, one at least); invalid → dropped with an import issue
                     notes?: string } ],   // the dashboard's data note: ≤ 1000 characters after trimming, absent when empty; over-long or not text → dropped with an import issue
  stories?:      [ { name, steps: [ { caption, target: { kind: "worksheet" | "dashboard", index } } ] } ],   // P24d — optional (absent in older files), ≤ 20 steps, caption ≤ 300
  tabs:          [ { kind: "worksheet" | "dashboard" | "story", index } ],   // the strip's order, ≤ 50
  active:        { kind, index } | null    // null = Data Source
  fields:        { "db.table.column": { alias?, agg?, hidden?, cast?, memberAliases?: { [rawValue]: label } } }   // P28, T02-34, T02-29 — ≤ 2000
  parameters:    [{ id: "prm<n>", name, type: number|text|date, value, allowed: { kind: any|list|range, list?, min?, max?, step? } }]   // P32 — ≤ 20
  hierarchies?:  [{ id: "hier<n>", name, levels: [{ db, table, column }] }]   // T03-29 — optional, ≤ 20, 2–6 same-table levels; a sheet's drill copies them
  sharedFilters: Filter[]                  // P40 — ≤ 4, applied by every worksheet where their table is in the view
  theme:         { accent: "signal" | "ultramarine" | "monospace" | "blue" | "crimson" | "teal" | "violet" | "graphite" | "#rrggbb", palette: "default" | "okabe" | "muted" }
}
```

- **Ids:** entity ids are only cross-references inside the file. Opening it creates fresh ids, for worksheets
  dashboards and stories too; widgets point at worksheets by index, steps at worksheets or dashboards.
- **Version 1 files** (`dashboards: [{ name, sheet }]`, numeric `active`) are migrated on read ([workbook.md](../concepts/workbook/workbook.md#format-v2-and-old-files)).
- **No connection details or passwords** are ever included.
- **Validation:** on open, every field is validated against `Core/sheet-schema.js` and the `LIMITS` above.
  Invalid parts are reset to defaults and reported ([workbook.md § Validation](../concepts/workbook/workbook.md#validation-parseworkbook)).
- **Not saved:** the dashboard's cross-widget selection ([dashboards.md](../concepts/workbook/dashboards.md#cross-widget-filtering))
  lives only in the board's memory. `selection` is never restored.
