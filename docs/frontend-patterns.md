# Frontend patterns

Conventions for the browser code. The frontend is **vanilla JS (ES modules) + hand-written
CSS** with design tokens ([decision D4](project/decisions.md)) — no SPA framework, no build
step required. Files live in `wwwroot/js/` and `wwwroot/css/`.

## Module layout

One page, small focused ES modules, each owning a region from [modules.md](app/modules.md):

| Module | Owns |
|---|---|
| `connection.js` | connection form, `POST/DELETE /api/connection`, indicator pill, gating |
| `schema.js` | database `<select>`, table list, chip rendering + drag payload |
| `canvas.js` | drop handling, entity cards, preview grid, card movement |
| `relations.js` | join-key selection, drawing links, cardinality |
| `tabs.js` | subtab strip, per-tab builder state |
| `api.js` | `fetch` helpers (JSON, error handling) |
| `ui.js` | shared helpers: toast, dialogs, pill, the `hidden` toggle |
| `store.js` | shared model (entities, relationships) + dashboards (widgets) + active view + event bus |
| `tabs.js` | view strip: pinned Data Model tab + dashboard subtabs (add / switch / rename / close) |
| `dashboards.js` | Tableau-style worksheet: field pane + drag-to-shelf + join-path + chart |
| `chart.js` | charting adapter: maps a `{categories, series:[{name,data}]}` result → an ECharts option (bar/line, one series per measure), themed from `--chart-*` tokens |
| `sidebar.js` | resizable sidebar (drag handle → `--sidebar-w`, capped at 30vw) |

Keep DOM ownership clear — a module mutates only its region and communicates via a small
shared state object or custom events, not by reaching into another module's nodes.

> **Built:** `api.js`, `ui.js`, `connection.js`, `schema.js`, `canvas.js`, `relations.js`,
> `store.js`, `tabs.js`, `dashboards.js` (+ `app.js` wiring them, listeners before the initial
> status check).
>
> **Two surfaces, one shared model.** `store.js` holds ONE shared **data model**
> (`entities` + `relationships`) and a list of **dashboards** (each with its own `widgets`).
> `activeView` is either the model or a dashboard; `canvas.js`/`relations.js` render the model
> into `#model-view`, `dashboards.js` renders the active dashboard's widgets into `#dashboard-view`,
> and each shows/hides its view on `view:changed`. `tabs.js` draws the strip: a pinned **Data
> Model** tab + dashboard subtabs + `[+]`. The **event bus** carries `entity:moved` /
> `entity:removed` / `joinkey:changed` / `rel:changed` (model) and `view:changed` / `tabs:changed`
> / `dashboard:changed` (views). A dropped table always lands in the shared model (`table:add`
> calls `showModel()` first). `ui.js` provides `confirmDialog` + `<dialog>` helpers
> (`openDialog`/`closeDialog` fall back to the `open` attribute where `showModal` is unavailable,
> e.g. headless jsdom). `connection.js` reads its inputs by **element
> id** (`conn-host`, `conn-port`, `conn-user`, `conn-password`, `conn-secure`) rather than
> `form.host` named access, and on any state change dispatches a **`connection:changed`**
> `CustomEvent` on `document` (detail = the connection view, or `{connected:false}`).
> `schema.js` listens for that to load/clear databases (never touching the form), and each
> table chip dispatches **`table:add`** (`{db,table}`) as the non-drag fallback — `canvas.js`
> (P4) will consume `table:add` and the `application/x-ch-table` drag payload alike.
> **Init order matters:** register `schema.js`'s listener before `connection.js` fires its
> initial status check.

## The `hidden`-attribute toggle (do this, not `style.display`)

The stylesheet declares `[hidden] { display:none !important }`
([DESIGN.md](../DESIGN.md#layout-rules)) so a single attribute reliably shows/hides any
element regardless of its author `display` (flex/grid). Use tiny helpers:

```js
export const show = el => el.hidden = false;
export const hide = el => el.hidden = true;
```

Never toggle `el.style.display` — it fights the `!important` rule and creates
show/hide bugs. Empty states, inline field errors, the dropzone hint, and the
"connect first" gate all flip via `hidden`. `ui.js` exports `show` / `hide` /
`toggle(el, visible)`.

## Status pill & toast (`ui.js`)

- `setPill(el, state, text)` — `state` ∈ `idle | connecting | connected | failed`, mapped to
  a class (`pill--muted/warn/ok/danger`) **and a glyph and label**, so status is never colour
  alone. Text is written as a text node, never HTML.
- `toast(message, kind)` — `kind` ∈ `ok | danger | info`; auto-hides after 5s via the
  `hidden` toggle. The single `#toast` element is `role="status"` + `aria-live="polite"`.

## Fetch & errors

- Central `api.js`: JSON in/out, always check `res.ok`, parse a structured error body,
  and surface it via the toast or an inline `.field-error` — **never** dump a raw
  stack/connection string (the server already scrubs credentials —
  [clickhouse-integration.md](clickhouse-integration.md)).
- **Path-base aware.** `api.js` prefixes every request with the app's base path, derived
  from its own module URL (`new URL(".", import.meta.url)` → `/<base>`), so the same code
  works served at the site root **or** under a reverse-proxy subpath (e.g.
  `/dashboardbuilder`). The server side is `app.UsePathBase(...)` from the `PathBase` config
  value, and Razor `~/` asset links resolve under it automatically — so nothing hardcodes the
  prefix. Keep API paths passed to `api.js` root-relative (`/api/...`); don't prepend a base
  at call sites. See [development.md](development.md#hosting-under-a-path-prefix-reverse-proxy).
- Reflect request lifecycle in the UI with the status pills: idle → loading (amber) →
  ok (green) / failed (red). Status is **icon + text + color**
  ([DESIGN.md](../DESIGN.md#accessibility-posture)).

## Charts (P9)

- **Self-hosted library, no CDN.** Bar/line render via **Apache ECharts**, vendored at
  `wwwroot/js/vendor/echarts.min.js` and loaded as a **global classic script before** the
  module graph (so `window.echarts` is ready). It's a **viz library, not an SPA framework**
  — [D4](project/decisions.md) stands; modules stay vanilla-JS. **Table** and **KPI** are
  native DOM, not the library's job.
- **`chart.js` is the only place that touches ECharts.** `renderChart(container, {type,
  categories, series:[{name,data}]})` maps our result to an option and manages **one live
  instance** (SVG renderer); `disposeChart()` tears it down. `dashboards.js` calls
  `disposeChart()` before every repaint and `renderChart(...)` only for bar/line (Table and
  KPI are native DOM). One series per measure; the category axis carries the concatenated
  dimension keys.
- **Themed from tokens, not literals.** `chart.js` reads `--chart-*` off `:root` via
  `getComputedStyle` (resolving one level of `var()` indirection) so charts track the design
  system ([DESIGN.md](../DESIGN.md)); **text wears ink tokens, the mark wears the series
  color**. A single series wears the brand accent; **multiple** series draw from the
  validated categorical ramp `--chart-cat-1..8` in fixed order, with a legend ([D13](project/decisions.md)).
- **Resize:** a `ResizeObserver` on the chart host calls `instance.resize()` (sidebar drag /
  window). The host is absolutely positioned to fill the padded `.ws-chart` pane so the
  library always has a definite size.

## Feedback colors

- Success flash / toast uses `--ok-bg`. **Never** `--brand-soft` (same red as
  `--danger-soft`) — it reads as an error. This is a [CLAUDE.md golden rule](../CLAUDE.md#golden-rules).

## Dialogs & confirms

Use the native `<dialog>` element (focus trap, `Esc` to close) for connect-error detail
and destructive confirms (removing an entity with relationships, closing a non-empty
tab). A styled confirm `<dialog>` replaces `window.confirm`.

## Tabs / per-dashboard state

`tabs.js` holds one builder-state slice per subtab ([data-model.md](data-model.md)).
Switching tabs swaps which entities/relationships render on the canvas; each tab is
independent. The active tab carries `aria-current`. v1 state is in-memory
([open question O1](project/decisions.md)).

## Drag & drop

Native HTML5 DnD with a custom MIME type for table chips, plus non-drag fallbacks for
accessibility — full detail in [drag-and-drop.md](drag-and-drop.md).
