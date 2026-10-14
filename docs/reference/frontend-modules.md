# Frontend modules & patterns

The browser code is **vanilla JS ES modules + hand-written CSS**, no framework and no build step
([golden rule 10](../conventions/golden-rules.md#10-self-hosted-framework-free-frontend)). Each
feature's JS/CSS sits beside its controller and view under `src/DashboardBuilder/Features/<Feature>/`;
shared helpers live in `Features/Core/`. Why: [D19](decisions.md#d19--mvc-in-feature-folders).

## Module map

| Module | Owns |
|---|---|
| `Shell/app.js` | bootstrap — hydrates `[data-icon]` placeholders, installs the global `error` / `unhandledrejection` handlers (danger toast "Something went wrong — try again."; aborted queries and the benign `ResizeObserver loop` notice are ignored), wires every module's `init*`, listeners before the initial status check |
| `Shell/sidebar.js` | resizable sidebar (`Core/resizer.js` handle → `--sidebar-w`, capped at 30vw) + collapse-to-rail toggle (remembered in `localStorage`); exports `expandSidebar()` |
| `Connection/connection.js` | connection form, summary, pill, gating — [connection.md](../features/connection.md) |
| `Connection/connection-rules.js` | pure: `advancedShouldOpen` (the Advanced section opens when TLS is off or the cert opt-in is on) |
| `Schema/schema.js` | database `<select>`, table search, table chips + drag payload — [schema-browser.md](../features/schema-browser.md) |
| `Schema/table-filter.js` | pure: `matchTables(names, query)` — the table search |
| `Canvas/canvas.js` | drop handling, entity cards, card movement, empty state — [canvas.md](../features/canvas.md) |
| `Canvas/empty-state.js` | pure: `emptyState({connected, databaseSelected})` → the sentence, button and control to focus |
| `Relations/relations.js` | join-key connectors, links, cardinality — [relationships.md](../features/relationships.md) |
| `Relations/relation-rules.js` | pure: `keysCompatible`, `findDuplicate`, `linkProblem` — what may be linked |
| `Tabs/tabs.js` | Data Model tab + dashboard tabs — [tabs.md](../features/tabs.md) |
| `Dashboard/dashboards.js` | the worksheet: field pane, shelves, toolbar, plan, render — [worksheet.md](../features/worksheet.md) |
| `Dashboard/chart.js` | the only ECharts adapter — [worksheet-charts.md](../features/worksheet-charts.md#rendering--the-echarts-adapter) |
| `Dashboard/contrast.js` | pure: WCAG `luminance`, `contrastRatio`, `pickInk` (treemap label ink) |
| `Dashboard/filter-rules.js` | pure: `aggsFor`, `checkFilter`, `statFilters`, `withCategories`, `viewCounts`, `checkAdd` (drop-time caps) — [worksheet.md](../features/worksheet.md#drop-time-limits) |
| `Dashboard/toolbar-rules.js` | pure: `visibleTools(chartType, tools)` — visible row vs More — [worksheet-encodings.md](../features/worksheet-encodings.md#encodings-toolbar) |
| `Core/parameters-model.js` | pure (P32): `checkValue` (type + allowed values), `withParamValue`, `effectiveTopN`, `paramTypeFor`, `cleanParameter` |
| `Workbook/parameters-dialog.js` | P32: the Parameters dialog (Workbook menu) |
| `Core/theme-model.js` | pure (P41): accent presets + palettes (light / dark), `deriveAccent` (custom colour → contrast-checked set, or a refusal), `themeVars`, `cleanTheme` — [tokens.md](../design/tokens.md#workbook-themes-p41) |
| `Core/theme.js` | applies the workbook theme's custom properties on `:root` (`theme:changed`, scheme flips) |
| `Workbook/theme-dialog.js` | the Theme dialog (Workbook menu) |
| `Workbook/bookmarks-dialog.js` | P39: Save view as bookmark…, the Bookmarks list, `applyBookmark` |
| `Dashboard/action-model.js` | pure (P39): `templateError`, `buildActionUrl` (https-only, encoded `{value}`), `cleanAction` |
| `Dashboard/analytics-model.js` | pure (P21): `refValue`, `trendFit` (linear / log / poly2 least squares, R²), `trendSeries` (+ forecast), `combine` (totals by aggregation) |
| `Dashboard/history.js` | pure (P23): per-dashboard undo / redo stacks of sheet snapshots (50) |
| `Dashboard/table-calc.js` | pure (P27): `computeCalc` (running / % of total / difference / % difference / rank / moving average, partitioned by the other shelf), `applyTableCalcs` |
| `Dashboard/date-parts.js` | pure (P26): `DATE_PART_CHOICES`, `stepPart` (+ / −), `partLabel`, `labelParts` |
| `Dashboard/period-model.js` | pure (P35): `resolveRange` / `compareRange` (presets, previous period, last year), `rangeFilter`, `rangeLabel`, `changeOf` / `toneOf` / `pctText`, `alignCompare`, `targetProgress` — [worksheet-encodings.md](../features/worksheet-encodings.md#date-range--comparison) |
| `Dashboard/conditional-model.js` | pure (P37): `measureKey`, `extentOf`, `midpointOf`, `scaleColors` (tint + contrast-picked ink), `barGeometry`, `matchRule`, `isActive` — [worksheet.md](../features/worksheet.md#table-view--a-true-rows--columns-crosstab) |
| `Dashboard/scale-model.js` | pure: `scalePlan` (limit / paging / Other / date grouping per chart type), `withOther`, `tableProgress`, `needsNextPage`, `bucketNotice` — [worksheet.md](../features/worksheet.md#table-view--a-true-rows--columns-crosstab) |
| `Dashboard/chart-fit.js` | pure: `chartFit(spec, width, height)` — the room a chart's category axes need (min width/height, label rotation, zoom window), `markCount` (canvas vs SVG) — [worksheet-charts.md](../features/worksheet-charts.md#rendering--the-echarts-adapter) |
| `Dashboard/viewbar-model.js` | pure: `CHART_TYPES`, `chartIcon` / `chartLabel` (the chart-type picker), `sortSummary` (what the sort picker shows) |
| `Dashboard/query-runner.js` | pure: latest-wins gate, per-dashboard result cache, truncation notice — [worksheet.md](../features/worksheet.md#query-lifecycle) |
| `Workbook/workbook.js` | auto-save, restore on connect, Export/Import — [workbook.md](../features/workbook.md) |
| `Workbook/workbook-model.js` | pure: workbook serialize / `parseWorkbook` (full validation + issue list) / `sanitizeSheet` / storage key — [workbook.md](../features/workbook.md#validation-parseworkbook) |
| `Core/api.js` | `fetch` helpers (JSON, errors, path base, optional `AbortSignal`) |
| `Core/ui.js` | toast, pill, `show`/`hide`/`toggle`, `fieldError` / `clearFieldError` / `checkField`, `listDialog`, `confirmDialog`, `openDialog`/`closeDialog` |
| `Core/validate.js` | pure input parsers (`host`, `port`, `text`, `number`, `dateTime`, `filterValue`, `range`) returning `{ ok, value }` or `{ ok:false, error }`, plus `LIMITS` and `HOST_MESSAGES` — mirror of the server's `ApiLimits` / `RequestRules` |
| `Core/sheet-schema.js` | pure: the allowed values for a saved sheet (chart types, categories, filter ops, formats, Top-N) |
| `Core/icons.js` | the inline-SVG icon set — `icon(name, {size, label})`, `PATHS`, `ICON_NAMES` |
| `Core/menu.js` | `wireMenu(button, list)` — keyboard-operable popover menu (`menuitem` / `menuitemradio` items); animated open/close via `motion.js` |
| `Core/motion.js` | `enter` / `exit` (WAAPI, opacity + transform, Fluent timing) and `reducedMotion()`; no-ops under reduced motion — [motion-accessibility.md](../design/motion-accessibility.md#motion) |
| `Core/resizer.js` | `wireResizer(handle, …)` — drag / arrow-key width handle (`role="separator"`) used by the sidebar and the field pane; pure `clampWidth` |
| `Core/store.js` | shared model + dashboards + active view + event bus — [data-model.md](data-model.md#client-side--featurescorestorejs) |
| `Core/format.js` | value and category formatters shared by charts, crosstab, KPI |

## Wiring

- **Imports** use uniform relative paths: a peer feature `../<Feature>/x.js`, shared `../Core/x.js`.
  Assets are served at `/features/<Feature>/<file>` and linked from Razor as `~/features/…`.
- **DOM ownership:** a module mutates only its own region and talks to others through the `store.js`
  **event bus** or `document` `CustomEvent`s — never by reaching into another module's nodes.
- **Cross-feature calls:** the Workbook feature rebuilds the model through `canvas.addEntity` /
  `canvas.clearModel` and `relations.restoreRelationship` — exported functions, not DOM reach-ins.
- **Pure modules** (`query-runner.js`, `workbook-model.js`, `validate.js`, `sheet-schema.js`,
  `filter-rules.js`, `toolbar-rules.js`, `contrast.js`, `relation-rules.js`, `table-filter.js`,
  `connection-rules.js`, `empty-state.js`, `api.js`'s `basePathFrom`) hold the testable logic and never
  touch the DOM; they run under `node --test` ([development.md](../operations/development.md#test)).
- **Document events:** `connection:changed` (connection.js → schema.js, workbook.js), `table:add` `{db, table}`
  (schema.js `＋` → canvas.js).
- **Init order:** `schema.js` and `workbook.js` register their `connection:changed` listeners before
  `connection.js` fires the initial `GET /api/connection` — otherwise the schema list and the workbook
  restore miss the first connect.
- **ECharts** is a classic global script loaded before the module graph (`window.echarts`).

## Fetch & errors (`api.js`)

- JSON in/out; always checks `res.ok` and reads the `{ error }` sentence (`errorMessage`; defensively
  also ProblemDetails `title`, else "Server error (status)." / "Request failed (status).") and surfaces it
  via a toast or inline message — never a raw stack or connection string. The error contract:
  [api.md § Errors](api.md#errors).
- **Path-base aware:** every request is prefixed with the base path derived from the module's own URL
  (`basePathFrom(import.meta.url)` strips the trailing `/features/Core/`), so the same code works at `/`
  or under `/dashboardbuilder`. If `api.js` ever moves, update that pattern — otherwise every API call
  404s. Pass root-relative `/api/...` paths; never prepend a base at a call site.
- State-changing calls are `POST` with a JSON body — the proxy 403s `DELETE` and body-less requests
  ([sharp edges](../conventions/sharp-edges.md#hosting--deploy)).

## UI helpers (`ui.js`)

- **Visibility:** `show(el)` / `hide(el)` / `toggle(el, visible)` flip the `hidden` attribute — never
  `style.display`.
- **`setPill(el, state, text)`** — `idle | connecting | connected | failed` → `pill--muted/warn/ok/danger`
  plus an icon and label; text written as a text node, never HTML.
- **`toast(message, kind)`** — `ok | danger | info`; `info` / `ok` auto-hide after 5 s, **`danger` stays
  until dismissed** (a close button). The visible `#toast` is not a live region — messages are announced
  through the persistent visually-hidden `#toast-live`.
- **`fieldError(input, msg)` / `clearFieldError(input)` / `checkField(input, result)`** — set
  `aria-invalid`, an inline `.field-error` linked by `aria-describedby`, cleared on the next `input`;
  `checkField` applies a `validate.js` result and returns the value or `undefined`.
- **`listDialog(title, items)`** — a titled issue list with one OK button (workbook reports).
- **Dialogs:** native `<dialog>`; `confirmDialog` replaces `window.confirm`. `openDialog`/`closeDialog`
  fall back to the `open` attribute where `showModal` is unavailable (e.g. jsdom).
