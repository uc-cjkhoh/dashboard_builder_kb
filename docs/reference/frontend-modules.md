# Frontend modules & patterns

The browser code is **vanilla JS ES modules + hand-written CSS**, no framework and no build step
([golden rule 10](../conventions/golden-rules.md#10-self-hosted-framework-free-frontend)). Each
feature's JS/CSS sits beside its controller and view under `src/DashboardBuilder/Features/<Feature>/`;
shared helpers live in `Features/Core/`. Why: [D19](decisions.md#d19--mvc-in-feature-folders).

## Module map

| Module | Owns |
|---|---|
| `Shell/app.js` | bootstrap — hydrates `[data-icon]` placeholders, installs the global `error` / `unhandledrejection` handlers (danger toast "Something went wrong — try again."; aborted queries and the benign `ResizeObserver loop` notice are ignored), wires every module's `init*`, listeners before the initial status check |
| `Shell/scheme-toggle.js` | the tab bar's appearance toggle: System / Light / Dark radio menu (`Core/menu.js`), glyph + label follow the choice |
| `Shell/sidebar.js` | resizable sidebar (`Core/resizer.js` handle → `--sidebar-w`, capped at 30vw) + collapse-to-rail toggle (remembered in `localStorage`); exports `expandSidebar()` |
| `Connection/connection.js` | connection form, summary, pill, gating — [connection.md](../features/connection.md) |
| `Connection/connection-rules.js` | pure: `advancedShouldOpen` (the Advanced section opens when TLS is off or the cert opt-in is on) |
| `Schema/schema.js` | database `<select>`, table search, table chips + drag payload — [schema-browser.md](../features/schema-browser.md) |
| `Schema/column-profile-dialog.js`, `Schema/column-profile-model.js` | the column profile dialog (`openColumnProfile(db, table, column)`, opened from a field row on a canvas card) and its pure rules: `profileRequest`, `formatShare`, `roleOf`, `summarize` — [schema-browser.md](../features/schema-browser.md#column-profile--field-details) |
| `Schema/table-filter.js` | pure: `matchTables(names, query)` — the table search |
| `Canvas/canvas.js` | drop handling, entity cards, card movement, empty state — [canvas.md](../features/canvas.md) |
| `Canvas/empty-state.js` | pure: `emptyState({connected, databaseSelected})` → the sentence, button and control to focus |
| `Relations/relations.js` | join-key connectors, links, cardinality — [relationships.md](../features/relationships.md) |
| `Relations/join-preview-model.js`, `Relations/join-check.js` | pure wording and declared-vs-observed comparison of a join preview (`describePreview`, `observedCardinality`, `pct`, `previewRequest`); the dialog's "Check this join" section (DOM, `textContent` only) |
| `Relations/relation-rules.js` | pure: `keysCompatible`, `findDuplicate`, `linkProblem` — what may be linked; `JOIN_TYPES`, `normalizeJoinType`, `joinChoices`, `planJoinType`, `joinBadge` — join types |
| `Tabs/tabs.js` | Data Model tab + one ordered list of worksheet and dashboard tabs, the `[+]` menu, close confirms — [tabs.md](../features/tabs.md) |
| `Board/board-model.js` | pure (P24b): widget geometry and limits — `overlaps`, `inBounds`, `firstFreeSpot`, `placeNew`, `checkPlacement`, the import clean-up `cleanWidgets`, `savedWidgets`, `removeSheetWidgets`, `dashboardsUsing`, `defaultTabName` — [data-model.md](data-model.md#tabs-and-dashboards) |
| `Board/board.js` | the dashboard tab's body (`#board-view`): a placeholder panel until the board canvas lands |
| `Tabs/duplicate-model.js` | pure: duplicate-worksheet naming, limit check, sheet copy (node-tested) |
| `Dashboard/dashboards.js` | the worksheet editor: field pane, shelves, toolbar, status bar, selection / drill / legend handling; owns exactly one worksheet view and passes its state in as the view's options (`interactive`, `onSelect`, `onDrill`, `onLegend`, …) — it draws nothing itself — [worksheet.md](../features/worksheet.md) |
| `Dashboard/worksheet-view.js` | `createWorksheetView(container, getContext, options)` → `{ run, refresh, cancel, destroy }`: plan → latest-wins fetch through the shared result cache → `renderWorksheet` into one container; owns its own gate, table pager, fresh flag and the last drawing's notice line. `getContext()` supplies `dash`, `noticeEl` (or null), `results`, `plan` (the `sheet-plan.js` context), `categoryOf`, `castOf`. `options` (static, all optional): `interactive` (false = a static widget — no mark selection, drill, legend click or status bar), `onSelect(dimField, raw)`, `onDrill(raw)`, `onLegend({ sheet, field, name, raw, bucketed })`, `legendFocus()`, `onTooltipFields`, `onMemberColors`, `statusBar`, `notices(sheet)`, `draw` (test seam). Also the single-table histogram / box plot path; re-exports the `notices.js` helpers — [worksheet.md](../features/worksheet.md#query-lifecycle) |
| `Dashboard/worksheet-render.js` | `renderWorksheet(container, sheet, result, cmp, { plan, interactive, hooks })` → `{ extraNotice }`: the one entry point that draws a result — Other mark, date-part labels, display names, P27 table calculations, then dispatches to a family module. Reads only its arguments (a render context `rc` carries `bucketedKey`, `calcPercent`, `extraNotice`, `interactive`, `hooks`), never the editor, so any view can draw a worksheet |
| `Dashboard/render-table.js` · `render-kpi.js` · `render-cartesian.js` · `render-special.js` · `render-handlers.js` · `render-dom.js` | DOM drawing, one family each: crosstab / text table with totals and conditional formatting (P37); KPI tiles and sparkline; series charts (bar / stacked / line / area / combo, pie / donut, scatter family, shape scatter, colour split, analytics, comparison series); heatmap, treemap, the P36 types, histogram and box plot; the interaction wiring (`selectHandler`, `legendSpec`, `memberSpec`; with `rc.interactive` false there is no click / drill handler and the legend is highlight-only — a click highlights an item and a second click clears it, nothing is hidden and no host hook runs); shared `el` / `hint` / `warn` / `iconSpan` |
| `Dashboard/result-model.js` · `grid-model.js` · `notices.js` | pure (node-tested): the shaping of a result for drawing — `primaryDim`, `chartOrientation`, `aliasNames`, `pathOrderedRows`, `marksChannels`, `scatterShapeGroups`, `colorSplitData`, `heatmapData`, `treemapTree`, `sankeyLinks`, `multiplesData`, `statusText`, `captionText`; the tuple / leaf / span pivots of the crosstab; the notice text builders (`joinNotices`, `periodNotice`, `speedNotice`, `invalidFilterNotice`) |
| `Dashboard/sheet-plan.js` | pure: the worksheet query plan from explicit inputs — `buildPlan(sheet, periodRange, ctx)`, `planDims`, `planMeasures`, `sortTargets`, `fieldId`, `measureName`, `periodFilters`, `toServerFilter`, drill / pages filters; `ctx = { calculations, entities, relationships, sharedFilters, parameters, metaOf, nameOf, columnType }` — [worksheet.md](../features/worksheet.md#building-the-query) |
| `Dashboard/chart.js` | the only ECharts adapter; one chart per container element (state in a `WeakMap`), every export takes the container first — [worksheet-charts.md](../features/worksheet-charts.md#rendering--the-echarts-adapter) |
| `Dashboard/contrast.js` | pure: WCAG `luminance`, `contrastRatio`, `pickInk` (treemap label ink) |
| `Dashboard/filter-rules.js` | pure: `aggsFor`, `checkFilter`, `statFilters`, `withCategories`, `viewCounts`, `checkAdd` (drop-time caps) — [worksheet.md](../features/worksheet.md#drop-time-limits) |
| `Dashboard/show-me-rules.js` | pure: chart-type field rules (`CHART_NEEDS`, `chartIssue`, the shared hint texts, `roleOf`) and Show Me — `issueFor`, `bestType`, `showMeOptions`, `placeFor`, `samePlacement` — [worksheet-charts.md](../features/worksheet-charts.md#show-me) |
| `Dashboard/toolbar-rules.js` | pure: `visibleTools(chartType, tools)` — visible row vs More — [worksheet-encodings.md](../features/worksheet-encodings.md#encodings-toolbar) |
| `Core/parameters-model.js` | pure (P32): `checkValue` (type + allowed values), `withParamValue`, `effectiveTopN`, `paramTypeFor`, `cleanParameter` |
| `Workbook/parameters-dialog.js` | P32: the Parameters dialog (Workbook menu) |
| `Core/theme-model.js` | pure (P41): accent presets + palettes (light / dark), `deriveAccent` (custom colour → contrast-checked set, or a refusal), `themeVars`, `cleanTheme` — [tokens.md](../design/tokens.md#workbook-themes-p41) |
| `Core/scheme-model.js` | pure: `SCHEME_PREFS`, `normalizePref`, `resolveScheme(pref, osDark)` — [tokens.md](../design/tokens.md#light-and-dark) |
| `Core/scheme-boot.js` | classic `<head>` script: sets `data-scheme` before first paint (mirrors `resolveScheme`) |
| `Core/scheme.js` | owns `<html data-scheme>`: `isDark`, `schemePref`, `setSchemePref` (`localStorage`), follows the OS while System; emits `scheme:changed` |
| `Core/theme.js` | applies the workbook theme's custom properties on `:root` (`theme:changed`, `scheme:changed`) |
| `Workbook/theme-dialog.js` | the Theme dialog (Workbook menu) |
| `Workbook/bookmarks-dialog.js` | P39: Save view as bookmark…, the Bookmarks list, `applyBookmark` |
| `Rows/rows-model.js` | pure: `tableRowsRequest`, `buildRowsRequest({plan, selection, limit})` (base-table filters + the mark as a bound `=`; `notes` for what couldn't apply), `rowsSummary`, `cellText`, `rowsToCsv`, `DEFAULT_LIMIT` — [worksheet.md](../features/worksheet.md#view-data) |
| `Rows/rows-dialog.js` | the rows dialog: `openTablePreview(db, table)` (schema browser) and `openRowsDialog({title, subtitle, request, notes, filename})` — [schema-browser.md](../features/schema-browser.md#row-preview) |
| `Dashboard/action-model.js` | pure (P39): `templateError`, `buildActionUrl` (https-only, encoded `{value}`), `cleanAction` |
| `Dashboard/analytics-model.js` | pure (P21): `refValue`, `trendFit` (linear / log / poly2 least squares, R²), `trendSeries` (+ forecast), `combine` (totals by aggregation) |
| `Dashboard/history.js` | pure (P23): per-worksheet undo / redo stacks of sheet snapshots (50), keyed by tab id |
| `Dashboard/table-calc.js` | pure (P27): `computeCalc` (running / % of total / difference / % difference / rank / moving average, partitioned by the other shelf), `applyTableCalcs` |
| `Dashboard/cast-model.js` | pure (T02-34): `castChoices`, `effectiveCategory`, `withCasts` (adds `cast` to the plan), `syncCastCategories`, `statCastProblem` |
| `Dashboard/line-style-model.js` / `heatmap-model.js` / `bullet-model.js` | pure: `LINE_STYLE_CHOICES`, `lineStep`, `linesTakeStyle`; `HEATMAP_SHAPE_CHOICES`, `circleSize`; `targetChoices`, `bulletTargets`, `bandsFor` — [worksheet-charts.md](../features/worksheet-charts.md) |
| `Dashboard/date-parts.js` | pure (P26): `DATE_PART_CHOICES`, `stepPart` (+ / −), `partLabel`, `labelParts` |
| `Dashboard/tooltip-model.js` | pure (T01-19): `parseTooltip`, `checkTooltipText`, `tooltipHtml` (escaped parts only), `tooltipCatalog` — [worksheet-encodings.md](../features/worksheet-encodings.md#tooltip-text-t01-19) |
| `Dashboard/period-model.js` | pure (P35): `resolveRange` / `compareRange` (presets, previous period, last year), `rangeFilter`, `rangeLabel`, `changeOf` / `toneOf` / `pctText`, `alignCompare`, `targetProgress` — [worksheet-encodings.md](../features/worksheet-encodings.md#date-range--comparison) |
| `Dashboard/conditional-model.js` | pure (P37): `measureKey`, `extentOf`, `midpointOf`, `scaleColors` (tint + contrast-picked ink), `barGeometry`, `matchRule`, `isActive` — [worksheet.md](../features/worksheet.md#table-view--a-true-rows--columns-crosstab) |
| `Dashboard/colour-model.js` | pure (T01-20, T03-33): member colour map validation / set / clear / lookup, palette and ramp reversal, swatches — [worksheet-encodings.md](../features/worksheet-encodings.md#member-colours-and-palette-order-t01-20-t03-33) |
| `Dashboard/scale-model.js` | pure: `scalePlan` (limit / paging / Other / date grouping per chart type), `withOther`, `tableProgress`, `needsNextPage`, `bucketNotice` — [worksheet.md](../features/worksheet.md#table-view--a-true-rows--columns-crosstab) |
| `Dashboard/chart-fit.js` | pure: `chartFit(spec, width, height)` — the room a chart's category axes need (min width/height, label rotation, zoom window), `markCount` (canvas vs SVG) — [worksheet-charts.md](../features/worksheet-charts.md#rendering--the-echarts-adapter) |
| `Dashboard/viewbar-model.js` | pure: `CHART_TYPES`, `chartIcon` / `chartLabel` (the chart-type picker), `sortSummary` (what the sort picker shows) |
| `Dashboard/query-runner.js` | pure: latest-wins gate, per-worksheet result cache, truncation notice — [worksheet.md](../features/worksheet.md#query-lifecycle) |
| `Calc/calc-parser.js` | pure: `parseFormula(text, resolve)` — hand-written tokenizer + recursive descent into wire-shaped nodes (`field`, `num`, `str`, `un`, `bin`, `agg`, `cmp`, `logic`, `not`, `case`, `ifnull`, `isnull`, `fn` (the text functions); `IF`/`IIF`/`ZN` and the simple `CASE` desugar to `case`/`ifnull`/`cmp`) plus client-only `{ k: "calc", name }` |
| `Calc/calc-types.js` | pure: `CALC_LIMITS`, the `FUNCTIONS` table, `check(ast, categoryOf)` → `{ type, isAggregate, tables }` or an error; a twin of the server's `CalcCatalog` / `CalcValidator`, tied by `tests/fixtures/calc-cases.json` |
| `Calc/calc-model.js` | pure: `expandCalcs` (replaces `{ k: "calc" }` references with their trees; cycle and size guard), `roleOfCalc` |
| `Calc/calc-resolve.js` | pure: `catalogFromEntities`, `makeResolve`, `compileCalculation(calc, calcs, catalog)` (parse → expand → check), `calcTables` |
| `Calc/calc-workbook.js` | pure: `checkName`, `renameInFormulas`, `usedBy`, `cleanCalculation(s)` — the workbook list rules |
| `Calc/calc-pill.js` | pure: the calc-pill shape (`makeCalcPill`, `isCalcPill`, `pillName`), `refusal` (E12 entry points), `pillSlots`, `syncCalcPills`, `usesCalc`, `clearCalcPills` |
| `Calc/calc-plan.js` | pure: the worksheet plan seam — `wireDim`, `wireMeasure`, `planTables`, `calcProblem`, `measureLabel`, `topByRef` / `wireTopBy`, `resolveSortTarget` |
| `Calc/calc-dialog-model.js` | pure: `evaluateDraft` (validation), `chipFor` (role chip), `suggest` (`[` field autocomplete and function-name autocomplete) |
| `Calc/function-help.js` | pure: the function glossary `FUNCTION_HELP` (derived from `calc-types.js` + the logic keywords), `searchHelp`, `groupHelp`, `functionItems` — the dialog's Functions panel and name autocomplete |
| `Calc/calc-pane-model.js` | pure: `paneState` (group items), `deleteCalcPlan`, `showUseAs` / session Use-as choice, `normaliseFormula` |
| `Calc/calc-dialog.js` | DOM: `openCalcDialog(id?)` — the New / Edit calculated-field dialog |
| `Calc/eval-order.js` | pure: `describeEvaluation` (the six stages), `evaluationInput(sheet, …)` — [calculated-fields.md](../features/calculated-fields.md#how-this-is-computed) |
| `Calc/explain-popover.js` | DOM: `explainControl(getInput, { signal })` — the view bar's "How this is computed" button and popover |
| `Calc/calc.css` | styles for the dialog, the role chip, the pane group and the explainer (tokens only) |
| `Workbook/workbook.js` | auto-save, restore on connect, Export/Import — [workbook.md](../features/workbook.md) |
| `Workbook/workbook-model.js` | pure: workbook serialize (v2) / `parseWorkbook` (full validation + issue list; v1 files via `migrateV1`) / `sanitizeSheet` / storage keys (`storageKey`, `legacyStorageKey`) — [workbook.md](../features/workbook.md#validation-parseworkbook) |
| `Core/api.js` | `fetch` helpers (JSON, errors, path base, optional `AbortSignal`) |
| `Core/ui.js` | toast, pill, `show`/`hide`/`toggle`, `fieldError` / `clearFieldError` / `checkField`, `listDialog`, `confirmDialog`, `openDialog`/`closeDialog` |
| `Core/validate.js` | pure input parsers (`host`, `port`, `text`, `number`, `dateTime`, `filterValue`, `range`) returning `{ ok, value }` or `{ ok:false, error }`, plus `LIMITS` and `HOST_MESSAGES` — mirror of the server's `ApiLimits` / `RequestRules` |
| `Core/sheet-schema.js` | pure: the allowed values for a saved sheet (chart types, categories, filter ops, formats, Top-N) |
| `Core/icons.js` | the inline-SVG icon set — `icon(name, {size, label})`, `PATHS`, `ICON_NAMES` |
| `Core/menu.js` | `wireMenu(button, list)` — keyboard-operable popover menu (`menuitem` / `menuitemradio` items); animated open/close via `motion.js` |
| `Core/motion.js` | `enter` / `exit` (WAAPI, opacity + transform, Fluent timing) and `reducedMotion()`; no-ops under reduced motion — [motion-accessibility.md](../design/motion-accessibility.md#motion) |
| `Core/resizer.js` | `wireResizer(handle, …)` — drag / arrow-key width handle (`role="separator"`) used by the sidebar and the field pane; pure `clampWidth` |
| `Core/store.js` | shared model + the ordered worksheet / dashboard tabs + active view + event bus — [data-model.md](data-model.md#client-side--featurescorestorejs) |
| `Core/format.js` | value and category formatters shared by charts, crosstab, KPI |

## Wiring

- **Imports** use uniform relative paths: a peer feature `../<Feature>/x.js`, shared `../Core/x.js`.
  Assets are served at `/features/<Feature>/<file>` and linked from Razor as `~/features/…`.
- **DOM ownership:** a module mutates only its own region and talks to others through the `store.js`
  **event bus** or `document` `CustomEvent`s — never by reaching into another module's nodes.
- **Cross-feature calls:** the Workbook feature rebuilds the model through `canvas.addEntity` /
  `canvas.clearModel` and `relations.restoreRelationship` — exported functions, not DOM reach-ins.
- **Pure modules** (`query-runner.js`, `sheet-plan.js`, `result-model.js`, `grid-model.js`, `notices.js`, `workbook-model.js`, `board-model.js`, `validate.js`, `sheet-schema.js`,
  `filter-rules.js`, `show-me-rules.js`, `toolbar-rules.js`, `contrast.js`, `relation-rules.js`, `table-filter.js`,
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
