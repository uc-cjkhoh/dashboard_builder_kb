# Data model

The shapes the app works with — transient on the server, in-memory in the browser. There is **no
application database** ([D2](decisions.md#d2--thin-session-scoped-proxy-no-application-database)):
nothing is stored server-side. The browser keeps the builder state as a **workbook**
([D21](decisions.md#d21--workbooks-persist-in-the-browser-not-on-the-server), [file shape](#workbook-file)).

## Server side (per session / per request)

### Connection

`ClickHouseConnectionInfo`, held in the session-scoped `ConnectionRegistry`. Never serialized to the
client — `GET /api/connection` returns a password-free view.

| Field | Notes |
|---|---|
| `host` | ClickHouse host |
| `port` | `8443` (HTTPS) on the target server |
| `user` | ClickHouse user |
| `password` | **server-only** — never returned, never logged |
| `secure` | TLS; on by default |
| `allowInvalidCert` | trust a self-signed cert; off by default, effective only when `secure` |
| `guards` | `QueryGuards` — `Full` / `NoTimeLimit` / `None`: which database-level settings this server accepted at connect ([step-down](clickhouse-integration.md#step-down-when-the-server-refuses-a-setting)) |
| `serverEnforcesReadOnly` | set at connect when the account already rejects setting changes — queries then run without the gateway's guard settings |

### Introspection results (pass-through)

- **databases** — `string[]`; **tables** — `string[]`.
- **columns** — `{ name, type, category }[]`; `type` is the raw ClickHouse string, `category` its
  display category ([type mapping](clickhouse-integration.md#type-mapping)).
- **query** — `QueryResult { rowDimensions, columnDimensions, measures, rows:[{keys, values}], truncated }`;
  `keys` are strings (ISO for dates) or `null`; **`values` entries are a number, a string (`min` / `max`
  of a text or date column) or `null`** — never assume a number. `truncated` is true when more groups
  exist beyond the limit (box plot: `{ groups, truncated }`). Optional: `total` (every group, when
  `withTotal`), `other: { groups, values }` (the aggregate past the limit, when `otherBucket`), `bucket:
  { key, grain }` (which key was date-grouped).
- **Errors** are always `{ error, field? }` — [api.md](api.md#errors).

## Client side — `Features/Core/store.js`

```
entities:      Map id → Entity              ┐ ONE shared data model
relationships: Map id → Relationship        ┘ (the Data Model tab)
tabs:          [ Tab, … ]                   ONE ordered list — worksheet and dashboard tabs (below)
activeView:    { kind: "model" } | { kind: "worksheet", id } | { kind: "dashboard", id }
bus:           EventTarget — entity:added · entity:loaded · entity:moved · entity:removed
                             joinkey:changed · rel:changed · view:changed · tabs:changed
                             worksheet:changed { id } · dashboard:changed { id }
```

### Entity

A table dropped onto the canvas ([canvas.md](../features/canvas.md)).

| Field | Notes |
|---|---|
| `id` | `db.table#n` |
| `db`, `table` | source, from the drag payload |
| `x`, `y` | canvas position |
| `columns` | `{ name, type, category }[]` from `DESCRIBE` |
| `joinKeys` | `Set<columnName>` — the user's checked keys; required to be a relationship endpoint |
| `el` | the card's DOM node |
| `pendingKeys` | join keys a just-opened workbook ticks once the columns load (kept if loading fails) |

### Relationship

A **logical** link — the database neither creates nor validates it
([golden rule 5](../conventions/golden-rules.md#5-relationships-are-logical-declarations-not-database-facts)).

| Field | Notes |
|---|---|
| `id` | client id |
| `from` | `{ entityId, column }` — a checked join key on entity A |
| `to` | `{ entityId, column }` — a checked join key on entity B |
| `cardinality` | `1:1` · `1:N` · `N:1` · `N:M` — intent, not a data guarantee |
| `joinType` | `inner` (default) / `left` / `right` / `full` (P31, T02-12/13) — which side keeps its unmatched rows (FROM = left, TO = right) |
| `joinFixed` | `true` once saved by the join dialog: the sides are the link's own. Absent/false with `left` = older link, keeps the base side |

The project statement requires every dragged-in table to select ≥1 join key; the UI enforces it by
letting only checked keys be endpoints ([relationships.md](../features/relationships.md)).

### Tabs and dashboards

```
Tab:     { id: "ws#n", kind: "worksheet", name, sheet }                 one worksheet (the editor)
       | { id: "db#n", kind: "dashboard", name, widgets: [Widget] }      a board of widgets
Widget:  { id: "w#n", kind: "sheet", sheetId: "ws#n", x, y, w, h }       a worksheet's view
       | { id: "w#n", kind: "text", heading, body, x, y, w, h }          a text block
```

Tab names are 1–60 characters; a workbook holds at most **50 tabs** of either kind. A dashboard lays widgets on a **12-column snap
grid** in whole cells with no overlap: `w` 2–12, `h` 2–24 (text 1–24), `y + h` ≤ 96, at most **12 widgets**, text `heading` ≤ 80 and
`body` ≤ 2000 characters (`LIMITS`, `Core/validate.js`; the rules and the first-free-spot scan are pure, in `Board/board-model.js`).
A widget points at a worksheet by tab id; one worksheet may sit on several dashboards, even twice on one. `store` helpers:
`worksheets()` / `dashboards()` (the tabs of a kind), `createWorksheet` / `createDashboard` (null at the tab limit),
`duplicateWorksheet`, `closeTab` (a closed worksheet's widgets leave every dashboard), `updateSheet` (→ `worksheet:changed`),
`setWidgets` + `nextWidgetId` (→ `dashboard:changed`). Nothing here reaches the server — dashboards add no endpoint
([D61](decisions-dashboards.md#d61--worksheets-and-dashboards-are-separate-tab-kinds-workbook-format-v2)).

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
  tooltipText: null | string,   // T01-19 tooltip template with <Field> placeholders (≤ 300; null = automatic)
  memberColors: {},              // T01-20 { "table.column": { member: "#rrggbb" } } (format.paletteReverse: bool, T03-33)
  title: null | string, caption: null | string, showTitle: boolean,   // P23 (null = automatic)
  showFilterCards: boolean,                                          // P30
  analytics: null | { ref: { kind, value? }, band: { from, to } | null, trend, forecast, totals: { grand, sub } },   // P21
  urlAction: null | { label, template },   // P39 link action — https:// with {value}
  period: null | { db, table, column, category: "temporal", preset, from, to, compare, compareFrom, compareTo },
  marks:  { size, label, detail: [], tooltip: [], shape, path, angle },
  format: { numberFormat, decimals, currencySymbol, dateFormat, topN, dateBucket, target, downIsGood, conditional, legend,
            dataLabels, colorByDimension, xTitle, yTitle,
            lineStyle, heatmapShape, targetMeasure }
}
```

- **Format chart settings:** `lineStyle` `straight` | `step` | `jump` (default `straight`; `jump` is shown as Step (centred)); `heatmapShape` `square` | `circle` (default `square`); `targetMeasure` null or a shelf-measure index 1–19 (the bullet's target field; null = the fixed `target`). A target field that no longer points at a later shelf measure is ignored and cleared when Format opens. An unknown value is reset with a workbook import issue; a workbook without them opens unchanged.
- **Pill:** `{ db, table, column, category, role?, agg?, datePart?, tableCalc?, choices? }` — `datePart` (P26) on a date dimension, `tableCalc` (P27) `{ type, along, window? }` on a measure, `choices` (P40) the slot's alternative fields. `role` overrides the type default
  (`'dimension'` → `GROUP BY`; `'measure'` → aggregated with `agg` ∈ `aggsFor(category)`:
  `sum/avg/min/max/median/stddev/variance/count/countDistinct/countNonNull/attr` for numbers,
  `count/countDistinct/countNonNull/min/max/attr` for text and dates, `count/countDistinct/countNonNull` otherwise). `roleOf(f)` in `dashboards.js` resolves it.
- **Filter:** `op` ∈ `= != > >= < <= in between`; `value` is a string for the scalar operators, `values`
  a string list for `in` (≤ 500) and a `[from, to]` pair for `between`. `category` decides how the value
  is parsed ([worksheet-encodings.md](../features/worksheet-encodings.md#filters)); it is back-filled from
  the column catalog when absent (older workbooks).
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

How each reaches the query: [worksheet-encodings.md](../features/worksheet-encodings.md#marks). Every
pinned value (`pages`, `selection`, `drill.path`) becomes a **bound** filter, never interpolated.

## Workbook file

What [workbook.md](../features/workbook.md) saves to `localStorage` and exports (`workbook-model.js`):

```
{
  format: "dashboard-builder-workbook", version: 2 (integer ≥ 1; version 1 files still open), savedAt: ISO-8601,
  entities:      [ { id, db, table, x, y, joinKeys: [column] } ],
  relationships: [ { from: { entityId, column }, to: { entityId, column }, cardinality, joinType } ],
  worksheets:    [ { name, sheet } ],      // sheet as above, minus pages.members
  dashboards:    [ { name, widgets: [ { kind: "sheet", sheet: worksheetIndex, x, y, w, h }
                                    | { kind: "text", heading, body, x, y, w, h } ] } ],
  tabs:          [ { kind: "worksheet" | "dashboard", index } ],   // the strip's order, ≤ 50
  active:        { kind, index } | null    // null = Data Model
  fields:        { "db.table.column": { alias?, agg?, hidden? } }   // P28 — ≤ 2000
  parameters:    [{ id: "prm<n>", name, type: number|text|date, value, allowed: { kind: any|list|range, list?, min?, max?, step? } }]   // P32 — ≤ 20
  bookmarks:     [{ name, worksheet: index | null, worksheetName, sheet, sharedFilters, savedAt }]   // P39 — ≤ 30
  sharedFilters: Filter[]                  // P40 — ≤ 4, applied by every worksheet where their table is in the view
  theme:         { accent: "crimson" | "blue" | "teal" | "violet" | "graphite" | "#rrggbb", palette: "default" | "okabe" | "muted" }
}
```

Entity ids are only cross-references inside the file; opening it creates fresh ids (worksheet and dashboard ids too — widgets and
bookmarks point at worksheets by index). A v1 file (`dashboards: [{ name, sheet }]`, numeric `active`, bookmarks with `dashboard` /
`dashName`) is migrated on read ([workbook.md](../features/workbook.md#format-v2-and-old-files)). No connection
details or passwords are ever included. On open, every field is validated against
`Core/sheet-schema.js` and the `LIMITS` above; invalid parts are reset to defaults and reported
([workbook.md § Validation](../features/workbook.md#validation-parseworkbook)). The dashboard's cross-widget selection ([dashboards.md](../features/dashboards.md#cross-widget-filtering)) lives only in the board's memory. `selection` is never
restored.
