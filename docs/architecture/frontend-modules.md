---
components: [src/DashboardBuilder/Features/Board/, src/DashboardBuilder/Features/Calc/, src/DashboardBuilder/Features/Canvas/, src/DashboardBuilder/Features/Connection/, src/DashboardBuilder/Features/Core/, src/DashboardBuilder/Features/Dashboard/, src/DashboardBuilder/Features/Relations/, src/DashboardBuilder/Features/Rows/, src/DashboardBuilder/Features/Schema/, src/DashboardBuilder/Features/Shell/, src/DashboardBuilder/Features/Story/, src/DashboardBuilder/Features/Tabs/]
---
# Frontend modules & patterns

A map of every browser module and what it owns, plus the wiring, fetch and UI-helper conventions they
share. Read it to find where a piece of frontend behaviour lives before changing it.

The browser code is **vanilla JS ES modules + hand-written CSS**, with no framework and no build step
([golden rule 10](../development/coding-standards.md#10-self-hosted-framework-free-frontend)). Each
feature's JS/CSS sits beside its controller and view under `src/DashboardBuilder/Features/<Feature>/`.
Shared helpers live in `Features/Core/`. Why: [D19](../decisions/decisions-platform.md#d19--mvc-in-feature-folders).

"Pure" below means the module never touches the DOM and runs under `node --test`. Tags such as P26 or
T02-34 are build-plan (Pnn) and backlog (Tnn-nn) item ids.

## Module map

Grouped by feature folder; each entry is the module, then what it owns.

### Shell/ — page bootstrap and chrome

- `Shell/app.js` — bootstrap
  - hydrates `[data-icon]` placeholders, installs the global `error` / `unhandledrejection` handlers (danger toast "Something went wrong — try again."; aborted queries and the benign `ResizeObserver loop` notice are ignored), wires every module's `init*`, listeners before the initial status check
- `Shell/scheme-toggle.js` — the tab bar's appearance toggle: System / Light / Dark radio menu (`Core/menu.js`), glyph + label follow the choice
- `Shell/perf-panel.js` — the sidebar's gauge tile (`#perf-btn`, bottom of the sidebar body; `sidebar.js` takes it out of the DOM on the Data Source tab and puts it back elsewhere) opens the Performance dialog: recent query / render timings newest first (time in the app zone, kind, query ms, rows, cache hit or miss, render ms) with a one-line summary, **Copy as text** (tab-separated) and **Clear**; a native `<dialog>` (Esc closes, focus returns to the button); updates live while open
- `Core/timezone.js` — pure: the app time zone (`<meta name="app-timezone">`, [time-zone.md](../reference/time-zone.md)): `clockIn`, `dateIn`, `todayIn`, `offsetLabel`.
- `Shell/activity-bar.js` — the **activity chip** (`#activity`, bottom-right, solid, `role=status` / `aria-live=polite`): while any API request is in flight it says what the app is waiting on and for how long ("Loading tables in sales… · 3 s"). Shown after 300 ms (no flash on fast requests), refreshed each second, `hidden` when idle.
- `Core/activity-model.js` — pure: `describeRequest(method, path)` builds the plain-words label from the method and URL path **only** (database / table / column names; never a request body — golden rule 4); `createActivity()` tracks in-flight requests; `activityLine(snapshot)` is the text (oldest request, "+n more", elapsed, "still waiting on ClickHouse" after 10 s). `api.js` registers every request in `request()` and `exportCsv()` and clears it in `finally`, so success, error and abort all end it.
- `Core/perf-log.js` — pure: a bounded in-memory ring (200) of timing entries `{ at, kind, ms, rows, cached, renderMs }`; only whitelisted numbers / kind are kept — never a request, SQL, value or credential; browser memory only, gone with the tab. `Dashboard/worksheet-view.js` records each fetch (`ms`, rows, cache hit) and each draw (`renderMs`)
- `Shell/sidebar.js` — resizable sidebar (`Core/resizer.js` handle → `--sidebar-w`, capped at 30vw) + collapse-to-rail toggle (remembered in `localStorage`); exports `expandSidebar()`

### Connection/

- `Connection/connection.js` — connection form, compact summary, gating — [connection.md](../concepts/data-source/connection.md)
- `Connection/recent-sources.js` — pure: `remember` / `forget` / `sanitize` recent connection sources (host as entered, port, user, TLS flags — never a password), most recent first, max 5; `formValues` refills the form from one
- `Connection/connection-rules.js` — pure: `advancedShouldOpen` (the Advanced section opens when TLS is off or the cert opt-in is on), `summaryTitle` (compact-summary tooltip), `formFromView`

### Schema/ — database picker and table list

- `Schema/schema.js` — database `<select>`, table search, table chips + drag payload — [schema-browser.md](../concepts/data-source/schema-browser.md)
- `Schema/column-profile-dialog.js`, `Schema/column-profile-model.js` — the column profile dialog (`openColumnProfile(db, table, column)`, opened from a field row on a canvas card) and its pure rules:
  - `profileRequest`, `formatShare`, `roleOf`, `summarize` — [schema-browser.md](../concepts/data-source/schema-browser.md#column-profile--field-details)
- `Schema/table-filter.js` — pure: `matchTables(names, query)` — the table search

### Canvas/ and Relations/ — the Data Source canvas

- `Canvas/canvas.js` — drop handling, entity cards, card movement, empty state — [canvas.md](../concepts/data-source/canvas.md)
- `Canvas/empty-state.js` — pure: `emptyState({connected, databaseSelected})` → the sentence, button and control to focus
- `Relations/relations.js` — drag- and keyboard-to-relate (`link-keys.js`), links, the Relationships description card (`relation-describe.js`), cardinality, pinned keys — [relationships.md](../concepts/data-source/relationships.md)
- `Relations/join-preview-model.js`, `Relations/join-check.js` — pure wording and declared-vs-observed comparison of a join preview (`describePreview`, `observedCardinality`, `pct`, `previewRequest`); the dialog's "Check this join" section (DOM, `textContent` only)
- `Relations/link-route.js` — pure: `linkSides` (which card edge each end uses), `linkRoute` (the elbow's corner points, lanes, badge spot), `roundedPath` — the link geometry
- `Relations/key-pairs.js`, `Relations/key-pairs-ui.js` — a compound key: pure `suggestPairs`, `addPair`, `compoundName`, `MAX_EXTRA_PAIRS`; the dialog's "Also match on" section (native controls, `textContent` only)
- `Relations/relation-rules.js` — pure (`relEnds` lists every column a link uses, extra pairs included): `keysCompatible`, `findDuplicate`, `linkProblem` — what may be linked; `JOIN_TYPES`, `normalizeJoinType`, `joinChoices`, `planJoinType`, `joinBadge` — join types

### Tabs/, Board/ and Story/ — tabs, the dashboard board and stories

- `Tabs/tabs.js` — Data Source tab + one ordered list of worksheet, dashboard and story tabs, the `[+]` menu, close confirms — [tabs.md](../concepts/workbook/tabs.md)
- `Board/board-model.js` — pure (P24b):
  - widget geometry and limits — `overlaps`, `inBounds`, `firstFreeSpot`, `placeNew`, `placeAt` (a drop), `checkPlacement`, `explainRefusal` (the refusal in words), the import clean-up `cleanWidgets`, `savedWidgets`, `removeSheetWidgets`, `dashboardsUsing`, `defaultTabName` — [data-model.md](../reference/data-model.md#tabs-and-dashboards)
- `Story/story-model.js` — pure (node-tested): `validateCaption`, `addStep`, `removeStep`, `moveStep`, `setCaption`, `goTo` (never wraps), `dropTarget` (used by `closeTab`), `offeredTargets`, `targetKind`, `stepName`, `savedSteps`, `cleanSteps` (import: bad steps skipped and reported) — [stories.md](../concepts/workbook/stories.md)
- `Story/story.js` — the story tab's body (`#story-view`): add row, step strip (tablist), caption editor, step tools, Previous / Next, the stage (a static `createWorksheetView` or a dashboard link), print
- `Board/board-size.js` — pure (node-tested): dashboard size — `SIZE_PRESETS`, `SIZE_LIMITS`, `sizeError`, `cleanSize` (import), `savedSize`, `sizeKey` / `sizeLabel`; size range — `rangeError`, `cleanRange`, `savedRange`, `rangedWidth` / `rangedHeight` — [dashboards.md](../concepts/workbook/dashboards.md#layout)
- `Board/board-layout.js` — pure (node-tested):
  - cell → pixel geometry — `layoutBoard(widgets, panelWidth, { rowH, gap, stack?, fixed? })` → `{ stacked, height, rects }` (`stack` is for print), `fixedRowH`, `columnWidth`, `widgetOrder` (reading order)
  - pixel → cell: `cellAt`, `snapMove`, `snapResize`, `cellRect` — [dashboards.md](../concepts/workbook/dashboards.md#layout)
- `Board/board.js` — the dashboard tab's body (`#board-view`):
  - shows the active dashboard only, reconciles its widgets by id, lays them out from the tokens, add / remove, theme and resize handling, full screen and print — [dashboards.md](../concepts/workbook/dashboards.md)
- `Board/board-widget.js` · `board-panel.js` — one widget (focusable; header with Edit / Remove over a select-only `createWorksheetView` or a text body; the corner grip; the inline text form) and the side panel (worksheets with Add, draggable with `SHEET_MIME`; Add text)
- `Board/board-drag.js` — pure: the pointer state machine `createDrag()` (`start` / `move` → ghost / `end` → `commit` \| `revert` \| `none` / `cancel`, `DRAG_THRESHOLD`), `ghostFor`, `dropPlan` (a panel drop)
- `Board/nav-model.js` · `nav-edit.js` — navigation button: pure `validateNavEdit`, `navTargets`, `navChanged`, `clearNavTarget` (used by `closeTab`); `nav-edit.js` builds the inline form (label, tooltip, Goes to)
- `Board/board-keys.js` · `text-edit.js` · `image-model.js` · `board-history.js` — pure: `validateImageFile`, `isImageSrc`, `altFromName` (image widgets: raster data URLs only, size-bounded)
  - `keyStep` (arrow / Shift+arrow → candidate + status, or the refusal), `movedMessage`, `resizedMessage`
  - `validateTextEdit`, `textChanged`
  - `createBoardHistory` (the editor's `history.js`, keyed by dashboard id), `restorable`
- `Board/board-interact.js` — DOM wiring over the pure modules: pointer move / resize with capture, the ghost, keyboard steps, dropping a worksheet from the panel — [dashboards.md](../concepts/workbook/dashboards.md#editing-the-layout)
- `Tabs/duplicate-model.js` — pure: duplicate-worksheet naming, limit check, sheet copy (node-tested)

### Dashboard/ — worksheet editor, view and rendering

- `Dashboard/dashboards.js` — the worksheet editor: field pane, shelves, toolbar, status bar, selection / drill / legend handling
  - owns exactly one worksheet view (exports `planCtx`, `categoryOf`, `castOf` and the shared `sharedResults` cache for the board's widgets) and passes its state in as the view's options (`interactive`, `onSelect`, `onDrill`, `onLegend`, …) — it draws nothing itself — [worksheet.md](../concepts/worksheet/worksheet.md)
- `Dashboard/worksheet-view.js` — `createWorksheetView(container, getContext, options)` → `{ run, sync, refresh, cancel, destroy }`: plan → latest-wins fetch through the shared result cache → `renderWorksheet` into one container
  - owns its own gate, table pager, fresh flag and the last drawing's notice line.
  - `getContext()` supplies `dash`, `noticeEl` (or null), `results`, `plan` (the `sheet-plan.js` context), `categoryOf`, `castOf`.
  - `options` (static, all optional):
    - `interactive`: `true` the editor; `"select"` a dashboard widget (marks select, nothing drills, no status bar); `false` static.
    - `cross()`: the dashboard selection, `{ filter }` or `{ selected }`. `sync()` re-runs only when it changed what the view shows.
    - Hooks: `onSelect(dimField, raw)`, `onDrill(raw)`, `onLegend({ sheet, field, name, raw, bucketed })`, `legendFocus()`, `onTooltipFields`, `onMemberColors`.
    - Other: `statusBar`, `notices(sheet)`, `draw` (test seam).
  - Also the single-table histogram / box plot path, and re-exports the `notices.js` helpers — [worksheet-query.md](../concepts/worksheet/worksheet-query.md#query-lifecycle)
- `Dashboard/worksheet-render.js` — `renderWorksheet(container, sheet, result, cmp, { plan, interactive, hooks })` → `{ extraNotice }`:
  - the one entry point that draws a result — Other mark, date-part labels, display names, P27 table calculations, then dispatches to a family module.
  - Reads only its arguments (a render context `rc` carries `bucketedKey`, `calcPercent`, `extraNotice`, `interactive`, `hooks`), never the editor, so any view can draw a worksheet
- `Dashboard/box-model.js` — pure box-plot data: `boxData` (whisker-to-whisker rows), `outlierPoints` (label → category index), `outlierNotice`, `MAX_OUTLIERS` (mirrors `ApiLimits.MaxBoxOutliers`)
- `Dashboard/render-table.js` · `render-kpi.js` · `render-cartesian.js` · `render-special.js` · `render-handlers.js` · `render-dom.js` — DOM drawing, one family each: crosstab / text table with totals and conditional formatting (P37)
  - KPI tiles and sparkline
  - series charts (bar / stacked / line / area / combo, pie / donut, scatter family, shape scatter, colour split, analytics, comparison series)
  - heatmap, treemap, the P36 types, histogram and box plot
  - the interaction wiring (`selectHandler`, `legendSpec`, `memberSpec`; with `rc.interactive` false there is no click / drill handler and the legend is highlight-only — a click highlights an item and a second click clears it, nothing is hidden and no host hook runs)
  - shared `el` / `hint` / `warn` / `iconSpan`
- `Dashboard/collapse-model.js` — pure (node-tested, T03-29):
  - `collapseKey`, `rollUp` (distinct tuples → one node per visible row / column under the collapsed headers), `expandNodes`, `leafValue` (a collapsed pair is `combine`d, null for a non-additive measure or partial rows), `headerKeys`, `applyToggle` (prune + cap), `shownValues` (conditional-format extents), `collapsedOf`, `canToggle`, `cleanCollapsed` (import clean-up)
- `Dashboard/data-notes.js` — pure (node-tested): `updatedText(queriedAt)`, `usedCalculations(sheet, calcs)`, `calcDefinitionLines` — the status bar's update time and the print header's calculation definitions
- `Dashboard/result-model.js` · `grid-model.js` · `notices.js` — pure (node-tested):
  - the shaping of a result for drawing — `primaryDim`, `chartOrientation`, `aliasNames`, `pathOrderedRows`, `marksChannels`, `scatterShapeGroups`, `colorSplitData`, `heatmapData`, `treemapTree`, `sankeyLinks`, `multiplesData`, `statusText`, `captionText`
  - the tuple / leaf / span pivots of the crosstab
  - the notice text builders (`joinNotices`, `periodNotice`, `speedNotice`, `invalidFilterNotice`)
- `Dashboard/sheet-plan.js` — pure:
  - the worksheet query plan from explicit inputs — `buildPlan(sheet, periodRange, ctx, { crossFilter })`, `involvedTables`, `selectionFilter`, `planDims`, `planMeasures`, `sortTargets`, `fieldId`, `measureName`, `periodFilters`, `toServerFilter`, drill / pages filters
  - `ctx = { calculations, entities, relationships, sharedFilters, parameters, metaOf, nameOf, columnType }` — [worksheet-query.md](../concepts/worksheet/worksheet-query.md#building-the-query)
- `Dashboard/chart.js` — the only ECharts adapter; one chart per container element (state in a `WeakMap`), every export takes the container first
  - [worksheet-charts.md](../concepts/worksheet/worksheet-charts.md#rendering--the-echarts-adapter)
- `Dashboard/contrast.js` — pure: WCAG (Web Content Accessibility Guidelines) `luminance`, `contrastRatio`, `pickInk` (treemap label ink)
- `Dashboard/colour-scale-model.js` — pure (T03-19): continuous colour ramp hues, diverging colours and symmetric range, pinned range validation and span — [worksheet-marks.md](../concepts/worksheet/worksheet-marks.md#member-colours-and-palette-order-t01-20-t03-33)
- `Dashboard/scale-model.js` — pure:
  - `scalePlan` (limit / paging / Other / date grouping per chart type), `withOther`, `tableProgress`, `needsNextPage`, `bucketNotice` — [worksheet-table-view.md](../concepts/worksheet/worksheet-table-view.md#table-view--a-true-rows--columns-crosstab)
- `Dashboard/date-axis.js` — pure:
  - `axisLabelPlan` (which category labels a bottom / left axis draws — evenly spread, first and last kept, none touching, upright when tight), `shortDateLabels`, `parseDateLabel` — [worksheet-charts.md](../concepts/worksheet/worksheet-charts.md#rendering--the-echarts-adapter)
- `Dashboard/chart-fit.js` — pure:
  - `chartFit(spec, width, height)` — the room a chart's category axes need (min width/height, label rotation, zoom window), `markCount` (canvas vs SVG) — [worksheet-charts.md](../concepts/worksheet/worksheet-charts.md#rendering--the-echarts-adapter)
- `Dashboard/viewbar-model.js` — pure: `CHART_TYPES`, `chartIcon` / `chartLabel` (the chart-type picker), `sortSummary` (what the sort picker shows)
- `Dashboard/query-runner.js` — pure: latest-wins gate, per-worksheet result cache, truncation notice — [worksheet-query.md](../concepts/worksheet/worksheet-query.md#query-lifecycle)

### Dashboard/ — field pane, pills and shelves

- `Dashboard/filter-rules.js` — pure: `aggsFor`, `checkFilter`, `statFilters`, `withCategories`, `viewCounts`, `checkAdd` (drop-time caps) — [worksheet.md](../concepts/worksheet/worksheet.md#drop-time-limits)
- `Dashboard/show-me-rules.js` — pure:
  - chart-type field rules (`CHART_NEEDS`, `chartIssue`, the shared hint texts, `roleOf`) and the chart-type menu's cues — `issueFor`, `bestType`, `showMeOptions` — [worksheet-charts.md](../concepts/worksheet/worksheet-charts.md#chart-type-control)
- `Dashboard/toolbar-rules.js` — pure: `visibleTools(chartType, tools)` — which Marks slots are quiet — [worksheet-marks.md](../concepts/worksheet/worksheet-marks.md#marks-slots)
- `Dashboard/field-choices.js` — pure: `choicesOf`, `sameRef`, `switchField`, `removeChoice` (a slot's field choices, P40)
- `Dashboard/placement-model.js` — pure: `defaultShelf(role)` (measures to Rows, dimensions to Columns) for the `＋` button and double-click
- `Dashboard/pill-options.js` — pure: `fieldPillOptions` / `filterPillOptions` (the entries of a pill's context popup), `filterSummary`, `markGrid` (Marks slots in rows of three)
- `Dashboard/field-group.js` — the one collapsible `<details class="ws-group">` of the field pane (Marks, tables)
- `Dashboard/fields-pane-model.js` — pure: the field pane's hide / show state (`fieldsPaneView`, `readCollapsed`, storage key)
- `Dashboard/field-copy-model.js` — `fieldCopies(field)`: the Copy items on a worksheet field's ⋯ menu (name, column name, formula)
- `Dashboard/hierarchy-model.js` — pure (T03-29):
  - `checkHierarchyName`, `checkLevels` (2–6, one table, no calc / cast), `checkHierarchy`, `cleanHierarchies` (import clean-up), `drillFromHierarchy` (→ `sheet.drill`), `CAST_REFUSAL`
- `Dashboard/hierarchy-dialog.js` — T03-29: the Hierarchies dialog (rows with Use, Edit, Delete)
  - `store.js` holds `hierarchies` + `setHierarchies` / `addHierarchy` / `updateHierarchy` / `removeHierarchy` (`hierarchies:changed`)
- `Dashboard/history.js` — pure (P23): per-worksheet undo / redo stacks of sheet snapshots (50), keyed by tab id
- `Dashboard/cast-model.js` — pure (T02-34): `castChoices`, `effectiveCategory`, `withCasts` (adds `cast` to the plan), `syncCastCategories`, `statCastProblem`
- `Dashboard/date-parts.js` — pure (P26): `DATE_PART_CHOICES`, `stepPart` (+ / −), `partLabel`, `labelParts`
- `Dashboard/member-labels.js` — pure (T02-29):
  - `aliasOf` / `setAlias` / `cleanMemberAliases` (null-prototype maps, own keys), `keyAliasMaps`, `withMemberLabels` (position-aware category formatter), `labelOf`, `memberRows`, `aliasesFromInputs` — [worksheet.md](../concepts/worksheet/worksheet.md)
- `Dashboard/member-labels-dialog.js` — DOM: `openMemberLabelsDialog` — the field ⋯ menu's Edit member labels…

### Dashboard/ — encodings, analytics and formatting models

- `Dashboard/dashboard-select.js` · `selection-dim.js` — pure (P24c):
  - the dashboard selection — `nextSelection`, `selectionRefusal`, `crossFilterOf`, `appliesTo`, `selectedIndexOf`, `crossFor`, `crossSignature`, `stillValid`, the chip and note texts
  - `applySelectionDim` (fade unselected bar / stacked / pie / donut marks) — [dashboards.md](../concepts/workbook/dashboards.md#cross-widget-filtering)
- `Dashboard/action-model.js` — pure (P39): `templateError`, `buildActionUrl` (https-only, encoded `{value}`), `cleanAction`; the parameter action: `cleanParamAction`, `applyParamAction`
- `Dashboard/analytics-model.js` — pure (P21):
  - `refValue`, `refConstant` (a constant line's bound parameter), `trendFit` (linear / log / poly2 least squares, R²), `trendSeries` (+ forecast), `combine` (totals by aggregation), `bandBounds` / `bandLabel` / `bandChoice` (typed, mean ± kσ and percentile bands), `pickMeasure`, `ANALYTICS_ITEMS` / `itemsFor` / `itemActive` / `addItem` / `removeItem` (the pane's draggable items)
- `Dashboard/table-calc.js` — pure (P27): `computeCalc` (running / % of total / difference / % difference / compound growth / rank / percentile rank / moving average, partitioned by the other shelf or by the unticked dimensions), `applyTableCalcs`
- `Dashboard/font-model.js` — pure: `FONT_CHOICES`, `fontToken`, `fontClass` — [worksheet-marks.md](../concepts/worksheet/worksheet-marks.md)
- `Dashboard/table-style-model.js` — pure: `tableStyleClasses`, `TABLE_ALIGN_CHOICES`, `TABLE_DENSITY_CHOICES`, `TABLE_SHADE_CHOICES` — [worksheet-encodings.md](../concepts/worksheet/worksheet-encodings.md)
- `Dashboard/line-style-model.js` / `heatmap-model.js` / `bullet-model.js` — pure: `LINE_STYLE_CHOICES`, `lineStep`, `linesTakeStyle`
  - `HEATMAP_SHAPE_CHOICES`, `circleSize`
  - `targetChoices`, `bulletTargets`, `bandsFor`
  - `axis-sync-model.js` (`syncRange`, `secondaryKind`, `SECONDARY_CHOICES`) and `mark-style-model.js` (`markBorder`, `edgeOr`, `markerSymbol`, `MARKER_SHAPE_CHOICES`, `markerSizeOr`, `markerSizeError`, `MARKER_SIZE`) — [worksheet-charts.md](../concepts/worksheet/worksheet-charts.md)
- `Dashboard/gantt-model.js` — pure: `ganttBars` (start + length -> bars, date or number, skipped count), `ganttTime`, `ganttAxisTime`, `ganttLabelMargin`, `ganttNotice`
- `Dashboard/tooltip-model.js` — pure (T01-19):
  - `parseTooltip`, `checkTooltipText`, `tooltipHtml` (escaped parts only), `tooltipCatalog` — [worksheet-marks.md](../concepts/worksheet/worksheet-marks.md#tooltip-text-t01-19-and-the-tooltip-modal)
- `Dashboard/tooltip-style.js` — pure:
  - `TIP_SIZES`, `TIP_COLOURS` (palette key → CSS token), `checkTooltipStyle`, `lineStyleCss`, and the modal's line model (`toLines`, `fromLines`, `moveLine`, `addLine`, `removeLine`, `insertField`) — [worksheet-marks.md](../concepts/worksheet/worksheet-marks.md#tooltip-text-t01-19-and-the-tooltip-modal)
- `Dashboard/tooltip-formats.js` — pure: `checkTooltipFormats`, `pruneFormats`, `tipLookup` (raw value -> text with per-field formats, reusing `Core/format.js`), `sampleLookup`, `looksDate`
- `Dashboard/tooltip-dialog.js` — DOM: the "Edit tooltip…" modal (lines editor, field formats, live preview)
- `Dashboard/period-model.js` — pure (P35):
  - `resolveRange` / `compareRange` (presets, previous period, last year), `rangeFilter`, `rangeLabel`, `changeOf` / `toneOf` / `pctText`, `alignCompare`, `targetProgress` — [worksheet-encodings.md](../concepts/worksheet/worksheet-encodings.md#date-range--comparison)
- `Dashboard/conditional-model.js` — pure (P37):
  - `measureKey`, `extentOf`, `midpointOf`, `scaleColors` (tint + contrast-picked ink), `barGeometry`, `matchRule`, `isActive` — [worksheet-table-view.md](../concepts/worksheet/worksheet-table-view.md#table-view--a-true-rows--columns-crosstab)
- `Dashboard/colour-model.js` — pure (T01-20, T03-33):
  - member colour map validation / set / clear / lookup, palette and ramp reversal, swatches — [worksheet-marks.md](../concepts/worksheet/worksheet-marks.md#member-colours-and-palette-order-t01-20-t03-33)

### Rows/ — row previews, union and unpivot

- `Rows/rows-model.js` — pure:
  - `tableRowsRequest`, `buildRowsRequest({plan, selection, limit})` (base-table filters + the mark as a bound `=`; `notes` for what couldn't apply), `rowsSummary`, `cellText`, `rowsToCsv`, `DEFAULT_LIMIT` — [worksheet-query.md](../concepts/worksheet/worksheet-query.md#view-data)
- `Rows/rows-dialog.js` — the rows dialog:
  - `openTablePreview(db, table)` (schema browser) and `openRowsDialog({title, subtitle, request, notes, filename, load})` (`load` defaults to `api.rows`) — [schema-browser.md](../concepts/data-source/schema-browser.md#row-preview)
- `Rows/union-model.js` — pure: `unionRequest(db, tables)` (2–5 different tables, throws a sentence otherwise), `unionPickState`, `UNION_LIMIT` (20) — [api.md § Union](../reference/api.md#union)
- `Rows/union-dialog.js` — `openUnionDialog(db, tables)`: tick 2–5 tables, then **Show rows** (`openRowsDialog` with `api.union` rows) or **Add to model** (`source:add`)
- `Rows/unpivot-model.js` — pure:
  - `unpivotRequest(db, table, columns, keep)` (2–50 columns, ≤ 5 kept, no column in both roles; throws a sentence otherwise), `unpivotPickState(cols, columns, keep)` (same-kind rule), `UNPIVOT_LIMIT` (20) — [api.md § Unpivot](../reference/api.md#unpivot)
- `Rows/unpivot-dialog.js` — `openUnpivotDialog(db, tables)`: table select, two checkbox lists (turn into rows / keep), then **Show rows** (`openRowsDialog` with `api.unpivot` rows) or **Add to model** (`source:add`)

### Calc/ — calculated fields

- `Calc/split-model.js` — pure:
  - `splitPlan({field, sep, pieces, calcs, name})` → `{ ok, calcs: [{name, formula}] }` — one `SPLIT([db.table.col], 'sep', k)` calculation per piece (2–10, separator 1–20 characters, free names, 20-calculation limit)
- `Calc/split-dialog.js` — `openSplitDialog({field, fieldName})`: separator + pieces, live name list, adds the calculations; opened from a text field's menu **Split…** in `dashboards.js`
- `Calc/clean-model.js` — pure:
  - `cleanOps(category)`, `parseRecode(text)`, `cleanPlan({field, category, op, value, pairs, keep, calcs, name})` → `{ ok, calcs: [{name, formula}] }` — one `TRIM` / `IFNULL` / `CASE` / `DATE` calculation (recode ≤ 20 pairs, texts ≤ 100 characters, formula ≤ 500, free name, 20-calculation limit)
- `Calc/clean-dialog.js` — `openCleanDialog({field, fieldName, category})`: operation select, value or `old = new` lines, live formula preview; opened from a field's menu **Clean…** in `dashboards.js`
- `Calc/calc-parser.js` — pure:
  - `parseFormula(text, resolve)` — hand-written tokenizer + recursive descent into wire-shaped nodes (`field`, `num`, `str`, `bool`, `null`, `un`, `bin`, `agg`, `cmp`, `logic`, `not`, `in`, `case`, `ifnull`, `isnull`, `fn` (the text functions); `IF`/`IIF`/`ZN`, the keyword `IF … THEN … END`, the simple `CASE` and `BETWEEN` desugar to `case`/`ifnull`/`cmp`/`logic`) plus client-only `{ k: "calc", name }`
- `Calc/calc-types.js` — pure: `CALC_LIMITS`, the `FUNCTIONS` table, `check(ast, categoryOf)` → `{ type, isAggregate, tables }` or an error; a twin of the server's `CalcCatalog` / `CalcValidator`, tied by `tests/fixtures/calc-cases.json`
- `Calc/calc-params.js` — pure: `[@Name]` support — `substituteParams` (param node → `num` / `str` / `date()` literal), `paramLiteral`, `paramRefs`, `calcsUsingParam`, `calcParamNames`, `renameParamInFormulas`
- `Calc/calc-model.js` — pure: `expandCalcs` (replaces `{ k: "calc" }` references with their trees; cycle and size guard), `roleOfCalc`
- `Calc/calc-resolve.js` — pure: `catalogFromEntities`, `makeResolve`, `compileCalculation(calc, calcs, catalog, params)` (parse → expand → substitute parameters → check), `calcTables`
- `Calc/calc-workbook.js` — pure: `checkName`, `mapRefs` (rewrite refs outside text literals), `renameInFormulas`, `usedBy`, `cleanCalculation(s)` — the workbook list rules
- `Calc/calc-pill.js` — pure:
  - the calc-pill shape (`makeCalcPill`, `newCalcFilter`, `isCalcPill`, `pillName`), `refusal` (the places a calculated field is refused, [D33](../decisions/decisions-calculated-fields.md#d33--calculated-fields-are-refused-wherever-a-plain-column-is-assumed)), `pillSlots`, `syncCalcPills`, `usesCalc`, `clearCalcPills`
- `Calc/calc-plan.js` — pure: the worksheet plan seam — `wireDim`, `wireMeasure`, `planTables`, `calcProblem`, `filterCalcProblem` / `wireCalcFilter` (a calculated filter), `measureLabel`, `aggWord(agg, p)` (`p90`), `topByRef` / `wireTopBy` (both carry `p` for a percentile), `resolveSortTarget`
- `Calc/calc-dialog-model.js` — pure: `evaluateDraft` (validation), `chipFor` (role chip), `suggest` (`[` field, `[@` parameter and function-name autocomplete)
- `Calc/function-help.js` — pure: the function glossary `FUNCTION_HELP` (derived from `calc-types.js` + the logic keywords), `searchHelp`, `groupHelp`, `functionItems` — the dialog's Functions panel and name autocomplete
- `Calc/calc-pane-model.js` — pure: `paneState` (group items), `deleteCalcPlan`, `showUseAs` / session Use-as choice, `normaliseFormula`
- `Calc/group-model.js` — pure (T02-30):
  - `groupTree` (CASE / OR-of-equals tree), `groupCost`, `MAX_GROUP_MEMBERS`, `maxMembersFor`, `otherLabel` (remainder label), `checkGroupSpec`, `cleanGroupSpec`, `groupCalcName`, member ↔ group assignments — [calculated-fields-groups.md](../concepts/worksheet/calculated-fields-groups.md)
- `Calc/group-dialog.js` — DOM: `openGroupDialog({ field, fieldName, calcId?, load })` — the Group… dialog
- `Calc/calc-dialog.js` — DOM: `openCalcDialog(id?)` — the New / Edit calculated-field dialog
- `Calc/eval-order.js` — pure: `describeEvaluation` (the six stages), `evaluationInput(sheet, …)` — [calculated-fields.md](../concepts/worksheet/calculated-fields.md#how-this-is-computed)
- `Calc/explain-popover.js` — DOM: `explainControl(getInput, { signal })` — the view bar's "How this is computed" button and popover
- `Calc/calc.css` — styles for the dialog, the role chip, the pane group and the explainer (tokens only)

### Workbook/ — saving, import/export and workbook dialogs

- `Workbook/parameters-dialog.js` — P32: the Parameters dialog (sidebar Parameters icon)
- `Workbook/theme-dialog.js` — the Theme dialog (Settings menu)
- `Workbook/workbook.js` — auto-save, restore on connect, Export/Import — [workbook.md](../concepts/workbook/workbook.md)
- `Workbook/workbook-model.js` — pure:
  - workbook serialize (v2) / `parseWorkbook` (full validation + issue list; v1 files via `migrateV1`) / `sanitizeSheet` / storage keys (`storageKey`, `legacyStorageKey`) — [workbook.md](../concepts/workbook/workbook.md#validation-parseworkbook)

### Core/ — shared helpers

- `Core/parameters-model.js` — pure (P32): `checkValue` (type + allowed values), `checkStep` (positive step size), `checkParamName`, `withParamValue`, `effectiveTopN`, `paramTypeFor`, `cleanParameter`
- `Core/theme-model.js` — pure (P41): accent presets + palettes (light / dark), `deriveAccent` (custom colour → contrast-checked set, or a refusal), `themeVars`, `cleanTheme` — [tokens.md](../reference/design/tokens.md#workbook-themes-p41)
- `Core/scheme-model.js` — pure: `SCHEME_PREFS`, `normalizePref`, `resolveScheme(pref, osDark)` — [tokens.md](../reference/design/tokens.md#light-and-dark)
- `Core/scheme-boot.js` — classic `<head>` script: sets `data-scheme` before first paint (mirrors `resolveScheme`)
- `Core/scheme.js` — owns `<html data-scheme>`: `isDark`, `schemePref`, `setSchemePref` (`localStorage`), follows the OS while System; emits `scheme:changed`
- `Core/theme.js` — applies the workbook theme's custom properties on `:root` (`theme:changed`, `scheme:changed`)
- `Core/source-model.js` — pure ([query-sources.md](../concepts/data-source/query-sources.md)):
  - `unionSource` / `unpivotSource` (the definition + automatic name, throws a sentence), `uniqueName`, `takenNames`, `wireSource`, `cleanSource` (workbook re-check), `sourceOfTable(entities, db, table)`, `sourceProblem(keys, entities)` (the mixed-view refusal), `sourceNote`, `distinctPlan` / `distinctMembers` (a filter's member list over a source)
- `Core/api.js` — `fetch` helpers (JSON, errors, path base, optional `AbortSignal`); `api.sourceColumns(source)` → `POST /api/source/columns`
- `Core/ui.js` — toast, pill, `show`/`hide`/`toggle`, `fieldError` / `clearFieldError` / `checkField`, `listDialog`, `confirmDialog`, `openDialog`/`closeDialog`, `copyText(text, what)` (clipboard + toast)
- `Core/validate.js` — pure input parsers (`host`, `port`, `text`, `number`, `dateTime`, `filterValue`, `range`, `percent`, with `isFraction` / `percentLabel` for the percentile fraction) returning `{ ok, value }` or `{ ok:false, error }`, plus `LIMITS` and `HOST_MESSAGES`
  - mirror of the server's `ApiLimits` / `RequestRules`
- `Core/sheet-schema.js` — pure: the allowed values for a saved sheet (chart types, categories, filter ops, formats, Top-N)
- `Core/icons.js` — the inline-SVG icon set — `icon(name, {size, label})`, `PATHS`, `ICON_NAMES`
- `Core/menu.js` — `wireMenu(button, list)` — keyboard-operable popover menu (`menuitem` / `menuitemradio` items)
  - `openContextMenu` / `wireContextMenu` — the context popup (right-click, ContextMenu key, `Shift+F10`, `Enter`)
  - animated open/close via `motion.js`
- `Core/context-menu-model.js` — pure: `placeMenu` (keep a popup in the viewport), `opensContext` (which keydown opens it), `nextFocus`
- `Core/motion.js` — `enter` / `exit` (WAAPI, the Web Animations API; opacity + transform, Fluent timing) and `reducedMotion()`; no-ops under reduced motion — [motion-accessibility.md](../reference/design/motion-accessibility.md#motion)
- `Core/resizer.js` — `wireResizer(handle, …)` — drag / arrow-key width handle (`role="separator"`) used by the sidebar and the field pane; pure `clampWidth`
- `Core/store.js` — shared model + the ordered worksheet / dashboard tabs + active view + event bus — [data-model.md](../reference/data-model.md#client-side--featurescorestorejs)
- `Core/format.js` — value and category formatters shared by charts, crosstab, KPI

## Wiring

- **Imports** use uniform relative paths: a peer feature `../<Feature>/x.js`, shared `../Core/x.js`.
  Assets are served at `/features/<Feature>/<file>` and linked from Razor as `~/features/…`.
- **DOM ownership:** a module mutates only its own region and talks to others through the `store.js`
  **event bus** or `document` `CustomEvent`s — never by reaching into another module's nodes.
- **Cross-feature calls:** the Workbook feature rebuilds the model through `canvas.addEntity` /
  `canvas.clearModel` and `relations.restoreRelationship` — exported functions, not DOM reach-ins.
- **Pure modules** (for example `query-runner.js`, `sheet-plan.js`, `result-model.js`, `grid-model.js`, `notices.js`, `workbook-model.js`, `board-model.js`, `validate.js`, `sheet-schema.js`,
  `filter-rules.js`, `show-me-rules.js`, `toolbar-rules.js`, `pill-options.js`, `fields-pane-model.js`, `context-menu-model.js`, `contrast.js`, `relation-rules.js`, `table-filter.js`,
  `connection-rules.js`, `empty-state.js`, `api.js`'s `basePathFrom`) hold the testable logic and never
  touch the DOM; they run under `node --test` ([testing.md](../how-to/testing.md#test)).
- **Document events:** `connection:changed` (connection.js → schema.js, workbook.js), `table:add` `{db, table}`
  (schema.js `＋` → canvas.js).
- **Init order:** `schema.js` and `workbook.js` register their `connection:changed` listeners before
  `connection.js` fires the initial `GET /api/connection` — otherwise the schema list and the workbook
  restore miss the first connect.
- **ECharts** is a classic global script loaded before the module graph (`window.echarts`).

## Fetch & errors (`api.js`)

- **JSON in/out.** Every call checks `res.ok` and reads the `{ error }` sentence (`errorMessage`). It
  defensively also reads a ProblemDetails `title`, else falls back to "Server error (status)." /
  "Request failed (status).". The message is surfaced via a toast or inline message — never a raw stack
  or connection string. The error contract: [api.md § Errors](../reference/api.md#errors).
- **Path-base aware:** every request is prefixed with the base path derived from the module's own URL
  (`basePathFrom(import.meta.url)` strips the trailing `/features/Core/`), so the same code works at `/`
  or under `/dashboardbuilder`. If `api.js` ever moves, update that pattern, or every API call 404s.
- Pass root-relative `/api/...` paths; never prepend a base at a call site.
- State-changing calls are `POST` with a JSON body — the proxy 403s `DELETE` and body-less requests
  ([sharp edges](../development/sharp-edges.md#hosting--deploy)).

## UI helpers (`ui.js`)

- **Visibility:** `show(el)` / `hide(el)` / `toggle(el, visible)` flip the `hidden` attribute — never
  `style.display`.
- **`copyText(text, what)`** — writes to the clipboard and toasts "Copied <what>." (or a danger toast when the browser blocks it).
- **`toast(message, kind)`** — `ok | danger | info`. `info` / `ok` auto-hide after 5 s; **`danger` stays
  until dismissed** (a close button). The visible `#toast` is not a live region; messages are announced
  through the persistent visually-hidden `#toast-live`.
- **`fieldError(input, msg)` / `clearFieldError(input)` / `checkField(input, result)`** — set
  `aria-invalid` and an inline `.field-error` linked by `aria-describedby`, cleared on the next `input`.
  `checkField` applies a `validate.js` result and returns the value or `undefined`.
- **`listDialog(title, items)`** — a titled issue list with one OK button (workbook reports).
- **Dialogs:** native `<dialog>`. `confirmDialog` replaces `window.confirm`. `openDialog`/`closeDialog`
  fall back to the `open` attribute where `showModal` is unavailable (e.g. jsdom).
