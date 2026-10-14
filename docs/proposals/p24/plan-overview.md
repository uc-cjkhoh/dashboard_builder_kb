# P24a + P24b Implementation Plan — overview

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended)
> or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax
> for tracking.

**Goal:** Make the worksheet query-and-render path instantiable (24a, no visible change), then add dashboard
tabs that lay several worksheets and text blocks out on a 12-column snap grid (24b), with workbook format v2.

**Architecture:** `chart.js` keeps one ECharts instance per container; a new `Dashboard/worksheet-view.js`
owns the query-and-render path behind `createWorksheetView`; the worksheet editor (`dashboards.js`) and the
new `Features/Board/` canvas each create views. The store holds one ordered `tabs` list of worksheets and
dashboards; pure `board-layout.js` does all grid math; `workbook-model.js` reads v1 and writes v2.

**Tech Stack:** vanilla ES modules (no build step, no framework, no CDN); ECharts (self-hosted, `Core/vendor/`);
`node:test` + `node:assert/strict`; a headless-Chromium harness (`playwright-core`, mocked `/api`) under
`tests/browser/`; ASP.NET Core serves the page (no server change).

**Spec:** [../p24-dashboards.md](../p24-dashboards.md) — read it first; this plan implements it exactly.

## Task files

| Tasks | File | Delivers |
|---|---|---|
| 1 | [plan-runtime-a.md](plan-runtime-a.md), [plan-runtime-a2.md](plan-runtime-a2.md) | browser harness in the repo (`tests/browser/`); `chart.js` per container |
| 2 | [plan-runtime-a3.md](plan-runtime-a3.md) | store `tabs` + worksheet renames |
| 3 | [plan-runtime-b.md](plan-runtime-b.md), [plan-runtime-b2.md](plan-runtime-b2.md) | `sheet-plan.js` + `worksheet-view.js` extracted; **checkpoint: 24a shippable** |
| 4 | [plan-model.md](plan-model.md) | `board-layout.js` |
| 5 | [plan-model-2.md](plan-model-2.md) | store dashboards + widgets; `LIMITS.tabs` / widget limits |
| 6 | [plan-model-3.md](plan-model-3.md) | workbook v2, `migrateV1`, autosave v2 key with v1 fallback |
| 7 | [plan-board.md](plan-board.md) | tab kinds, **+** menu, `dashboard` icon; editor guards (`onSheet()`) |
| 8 | [plan-board-2.md](plan-board-2.md), [plan-board-3.md](plan-board-3.md) | the Board canvas: `_Board.cshtml`, `board-drag.js`, `board.css`, `board.js` |
| 9 | [plan-present.md](plan-present.md) | full screen / print / theme / bookmarks on dashboards; v1-autosave browser check |
| 10 | [plan-finish.md](plan-finish.md) | KB docs, delete spec + plan, merge, publish, deploy |

## Shared interfaces (every task file uses exactly these names)

**`Dashboard/chart.js` (Task 1)** — container-first; state in a `WeakMap`:
`renderChart(container, spec)`, `disposeChart(container)`, `hasChartInstance(container)`,
`sizeChart(container, size | null)`, `exportChart(container, kind)`, `focusSeries(container, name, type)`,
`animateNextChart(container, fresh)`. No module-level chart instance remains; `disposeChart` resets the
chart but keeps the container's animate flag (today's dispose → mark fresh → render order relies on it).

**`Core/store.js` after Task 2** (24a; names only, behaviour unchanged):
- `tabs` — ordered array of `{ id: "ws#N", kind: "worksheet", name, sheet }`
- `worksheetList()`, `tabById(id)`, `isModelActive()`, `activeTabId()`, `activeWorksheet()` (null unless a
  worksheet tab is active)
- `createWorksheet(name)`, `updateSheet(id, sheet)` → emits `worksheet:changed { id }`,
  `worksheetHasContent(id)`, `switchTab(id)`, `renameTab(id, name)`, `closeTab(id)`
- `activeView`: `{ kind: "model" } | { kind: "worksheet", id }`
- Removed: `dashboards`, `activeDashboard`, `activeDashboardId`, `createDashboard`, `switchDashboard`,
  `renameDashboard`, `closeDashboard`, `dashboardHasContent`, event `dashboard:changed` (re-added with its new
  meaning in Task 5). Default worksheet name stays "Dashboard" until Task 7 (24a = no visible change).

**`Dashboard/worksheet-view.js` (Task 3):**
`createWorksheetView({ chartEl, noticeEl, statusEl = null, interactive = true, hooks = {} })` →
`{ run(sheet, scopeId, { fresh = false } = {}), resize(), dispose(), cancel(), clearFocus() }`;
`export const resultCache` (the one shared `createResultCache()`). `hooks` (all optional; the editor passes
all, the Board none): `onSelect(field, raw)`, `onDrill(raw)`, `onLegendSelect(sheet, field, raw, again)`.
`cancel()` aborts an in-flight query but keeps loaded table pages; `clearFocus()` resets legend focus.
**`Dashboard/sheet-plan.js` (Task 3)** — store-reading, DOM-free: `buildPlan`, `planDims`, `planMeasures`,
`sortTargets`, the chart-type sets and the drill / pages / period helpers; imported by the editor and the view.

**`Core/store.js` after Task 5** (24b):
- `tabs` also holds `{ id: "db#N", kind: "dashboard", name, widgets }`;
  widget = `{ id: "w#N", kind: "sheet", sheetId, x, y, w, h } | { id: "w#N", kind: "text", heading, body, x, y, w, h }`
- `activeView` adds `{ kind: "dashboard", id }`; `activeBoard()`; `boardList()`
- `createBoard(name)`, `updateBoard(id, widgets)` → emits `dashboard:changed { id }`,
  `boardsUsing(sheetId)` → `[{ id, name }]`; `closeTab(worksheetId)` also removes that worksheet's widgets
  from every dashboard (emitting `dashboard:changed` for each)
- `nextWidgetId()` → `"w#N"`

**`Board/board-layout.js` (Task 4)** — pure, no imports:
`GRID = { cols: 12, maxRows: 96, maxWidgets: 12 }`, `SIZE_LIMITS = { sheet: { minW: 2, minH: 2 }, text: { minW: 2, minH: 1 }, maxW: 12, maxH: 24 }`,
`DEFAULT_SIZE = { sheet: { w: 6, h: 4 }, text: { w: 12, h: 1 } }`,
`overlaps(a, b)`, `fits(widgets, rect, ignoreId = null)`, `firstFree(widgets, w, h)` → `{ x, y } | null`,
`clampRect(kind, rect)`, `cellsFromPixels(px, cellPx, gapPx)`, `moveBy(widgets, id, dx, dy)` → rect | null,
`resizeBy(widgets, id, dw, dh)` → rect | null, `normaliseLayout(widgets)` → `{ widgets, issues: string[] }`.

**`Workbook/workbook-model.js` (Task 6):** `WORKBOOK_VERSION = 2`; `migrateV1(obj)` → v2 object;
`parseWorkbook` accepts v1 (migrated) and v2; `autosaveKey(conn)` → `dashboardbuilder.workbook.v2|host|port|user`,
`legacyAutosaveKey(conn)` → the `v1` key; `savedWorkbookText(view, read)` → the v2 text, else the v1 text.
File ids are never saved: every `ws#` / `db#` / `w#` is minted on open (no seq bumping).

## Global Constraints

- App root `/unified/user/cj/web_development/prototype/dashboard_builder` (local git repo); work on branch
  `p24-dashboards` created from `main`; run commands from the app root.
- JS suite: `~/.nvm/versions/node/v24.20.0/bin/node --test tests/js/*.test.mjs`; .NET: `dotnet test`;
  browser: `NODE_PATH=~/pw-harness/node_modules ~/.nvm/versions/node/v24.20.0/bin/node tests/browser/run.mjs`
  (Task 1 Step 1 installs `playwright-core` there; `mock.mjs` loads it via `createRequire`, which honours
  `NODE_PATH` — a bare ES `import` does not). `node --check` every changed module.
- Dev run: `cd src/DashboardBuilder && dotnet run --no-launch-profile --urls http://localhost:5180`; stop with
  `fuser -k 5180/tcp` — **never** `pkill -f DashboardBuilder.dll` (matches the live service).
- Read-only server untouched; no framework / CDN / build step; `hidden` for visibility; tokens only; never
  colour alone; the page never scrolls — panels (and the canvas) scroll inside ([golden rules](../../conventions/golden-rules.md)).
- Limits (spec): ≤ 12 widgets / dashboard; ≤ 50 tabs of both kinds (`LIMITS.tabs`); `w` 2–12; `h` 2–24
  (text 1–24); `y + h` ≤ 96; heading ≤ 80 chars; body ≤ 2 000. Out-of-range input is rejected or reported,
  never silently clamped — except on import, where every clamp is reported in `issues`.
- 24a is a refactor: after Tasks 1–3 every existing test and every browser check passes unchanged.
- Commit at the end of each task; message ends `Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>`.

## Review Focus

1. **A worksheet edited while its dashboard is hidden** — returning to the dashboard must show the edit
   (leaving disposes every widget; showing re-runs each worksheet's current sheet). Pinned in Task 8
   (browser: edit sheet → back to dashboard → the widget's chart shows the edit; the request may be served
   from the shared cache, so the check asserts the drawn result, not a new query).
2. **Two widgets on the same worksheet** — both render; one's latest-wins gate must not abort the other.
   Pinned in Task 3 (two views, one scope) and Task 8 (browser: same sheet twice).
3. **Closing a worksheet used on dashboards, then Undo on the dashboard** — the widget removal is not a
   dashboard undo step that resurrects a widget pointing at a deleted worksheet. Pinned in Task 5 (store test)
   and Task 8 (undo skips / drops widgets whose `sheetId` no longer exists).
4. **A v1 autosave with bookmarks and an active tab** — migrates with bookmarks still pointing at the right
   worksheet and the same tab active. Pinned in Task 6.
5. **Resizing the browser / side panel** — widget charts resize without re-querying, and the grid column width
   follows the panel. Pinned in Task 8 (browser: viewport change → no new `/api/query`, chart width changes).

## Done when

All ten tasks are checked; both suites and the browser harness pass in light and dark; the user has reviewed
24a (checkpoint after Task 3) and the dashboard screenshots; the KB reflects the built state with the spec
and this `p24/` folder deleted; the live service is redeployed.
