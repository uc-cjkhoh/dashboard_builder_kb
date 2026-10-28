# P24a + P24b — Worksheet views and multi-worksheet dashboards

P24 is split into four phases; this spec covers the first two. 24a (the widget runtime) and the data side of 24b (tab kinds, store, limits, validation, workbook format v2) are built — [tabs.md](../features/tabs.md), [data-model.md](../reference/data-model.md#tabs-and-dashboards), [workbook.md](../features/workbook.md), [D61](../reference/decisions-dashboards.md#d61--worksheets-and-dashboards-are-separate-tab-kinds-workbook-format-v2). The board renders (stage 2, [dashboards.md](../features/dashboards.md)); still to build is its editing (stage 3, [backlog/dashboards.md](dashboards.md)):

| Phase | What | This spec |
|---|---|---|
| **24a** | Widget runtime — the worksheet query-and-render path becomes instantiable; `chart.js` keeps one chart per container | yes |
| **24b** | Dashboard composition — worksheets and dashboards as separate tab kinds; a snap-grid canvas of worksheet and text widgets; workbook format v2 | yes |
| 24c | Cross-widget filtering — a mark selected in one widget filters the others | later spec |
| 24d | Stories — ordered, captioned snapshots | later spec |

When built, the behaviour moves into a new [features/](../features/worksheet.md) file `dashboards.md` and the
docs listed under [Docs](#docs), [backlog/dashboards.md](dashboards.md) keeps
only 24c / 24d, and this file and its plan are deleted
([kb-maintenance.md](../conventions/kb-maintenance.md#when-you-make-a-change)).

## Goals

- Several worksheets on one canvas, arranged and resized on a grid, each re-querying independently.
- Today's worksheet editor and every worksheet behaviour unchanged — a tab that is a worksheet works exactly
  as a dashboard tab does now.
- One renderer: a widget draws a worksheet exactly as its own tab does.
- Existing saved workbooks (format v1, file or autosave) open without loss.

## Non-goals

- No cross-widget filtering, mark selection, drill or Pages inside a widget (24c); no stories (24d).
- No dashboard-level filter controls, images, web pages or floating (overlapping) widgets.
- No server change — no new endpoint, no server-side persistence (decision D21 stands; O1 stays open).
- No Markdown in text blocks.

## Decisions

| # | Decision | Why |
|---|---|---|
| B1 | **Tableau-style**: worksheets stay tabs edited as today; a dashboard tab composes existing worksheets; one worksheet may sit on several dashboards | keeps the 3.4k-line editor untouched; matches D16's wording and the roadmap |
| B2 | **12-column snap grid**, `{x, y, w, h}` in cells, no overlap | predictable, easy to persist and validate; fits the fixed shell (the canvas scrolls inside its panel) |
| B3 | Widgets: **worksheet** and **text** only | nearly every dashboard needs a heading; filter controls overlap 24c |
| B4 | Widgets are **view-only** (tooltips, legend highlight, table paging); **Edit** opens the worksheet tab | per-widget drill / selection state belongs with 24c |
| B5 | **Approach A** — extract `createWorksheetView`; `chart.js` keyed by container | one renderer (rejected: a second simplified renderer — drifts; iframes — N app copies, cross-frame 24c) |
| B6 | Internal rename: today's `dashboard` (= one worksheet) becomes `worksheet` in code | "dashboard" must mean only the new kind |

Recorded as [D61](../reference/decisions-dashboards.md#d61--worksheets-and-dashboards-are-separate-tab-kinds-workbook-format-v2) (it answers O3 for the data side).

## 24a — Widget runtime (no visible change)

### `chart.js` — one instance per container

- Replace the module-level `instance` / `resizeObserver` / `lastOption` / `onCanvas` / `animateNext` with a
  `WeakMap<container, state>`.
- Every export takes the container first: `renderChart(container, spec)`, `disposeChart(container)`,
  `hasChartInstance(container)`, `sizeChart(container, size)`, `exportChart(container, kind)`,
  `focusSeries(container, …)`, `animateNextChart(container, fresh)`. Rendering into one container never
  disposes another's chart.

### `Dashboard/worksheet-view.js` — the query-and-render path

- **Moves out of the `initDashboards()` closure:** `buildPlan`, `runChart`, `runTable` (with its pager),
  `runStatChart`, `fetchCached`, `renderChart` and its helpers (`renderColorSplit`, `renderHeatmap`,
  `renderTreemap`, `renderP36`, `crosstabTable`, scatter shapes, path order, notices).
- **API:** `createWorksheetView({ chartEl, noticeEl, statusEl, interactive, onSelect, results })` →
  `{ run(sheet, scopeId, { fresh }), resize(), dispose() }`.
  - Each view owns its `createLatestGate()` and its per-render flags (`bucketedKey`, `calcPercent`,
    `extraNotice`, `freshResult`, `tablePager`), so views never abort or overwrite each other.
  - `results` is the shared `createResultCache()`; `scopeId` is the worksheet id, so a widget and its
    worksheet tab share cached results.
  - `interactive: false` → no mark selection, drill or Pages; tooltips and legend highlight stay.
    `interactive: true` → the editor's behaviour, calling `onSelect` for click-to-filter / drill.
- **Stays in `dashboards.js`** (the worksheet editor): field pane, shelves, Marks tools, view bar, Show Me,
  Format / Analytics cards, status chips, undo / redo, full screen and print of one worksheet. It creates
  one interactive view for its chart pane.
- **Done when (24a):** the app behaves exactly as before — both suites and the P22 browser checks green —
  and two views can render into two containers at once (browser check).

## 24b — Dashboards

### Tabs, store and workbook format

Built: [tabs.md](../features/tabs.md), [data-model.md](../reference/data-model.md#tabs-and-dashboards) and [workbook.md](../features/workbook.md) describe the strip, the `tabs` / widget records, `activeView`, the events, `LIMITS.tabs`, the widget limits and the import clean-up. The widget rules (`overlaps`, `firstFreeSpot`, `placeNew`, `checkPlacement`) are in `Board/board-model.js` for the canvas to use.

### Canvas

- 12 columns; row height `calc(var(--ctl-h) * 2)`; gap `var(--s3)`; the canvas grows downward and scrolls
  inside its panel (golden rule 8). Column width follows the panel width.
- **Limits** (in `validate.js` `LIMITS`, mirrored in the import check): ≤ 12 widgets per dashboard;
  `w` 2–12 for both kinds; `h` 2–24 for worksheet widgets, 1–24 for text; `y + h` ≤ 96 rows; heading ≤ 80
  characters, body ≤ 2 000.
- **Side panel** (the field-pane slot): the workbook's worksheets, each with **Add**, and **Add text**.
  Add (or drag a worksheet onto the canvas) places the widget at the first free spot scanning rows top to
  bottom, default 6 × 4 (text 12 × 1); with no room under the row limit, a toast says the canvas is full.
- **Move:** drag the widget header; **resize:** drag the bottom-right corner. Both snap to cells, show a
  ghost of the target cells, and a drop that would overlap another widget or leave the grid snaps back with
  a status message — never silently moved elsewhere. Keyboard: with a widget focused, arrows move by one
  cell, Shift+arrows resize, each a committed step.
- **Widget header:** worksheet name (or text heading), **Edit** (worksheet → switches to its tab; text →
  inline edit), **Remove**. A worksheet widget's body is the view; a text widget's body is the text.
- **Undo / redo** on the dashboard tab (same `history.js`, keyed by dashboard id): add, remove, move, resize,
  text edit — one step each.

### Rendering and data

- Only the **active** dashboard renders; switching away disposes its views. Each worksheet widget gets
  `createWorksheetView({ interactive: false })` and runs its worksheet's sheet with `scopeId = sheetId`.
- Shared filters and parameters apply to every widget exactly as to every worksheet; each worksheet's own
  filters stay its own.
- A widget's failure or unmet-mapping hint renders **inside that widget** with the worksheet's own text; its
  siblings are unaffected. Tables page and scroll inside the widget.
- A worksheet edit marks its widgets stale; they re-run when their dashboard is next shown. A resize re-sizes
  the chart without re-querying.
- On `theme:changed`, every live view re-renders from cache.
- ≤ 12 parallel queries per dashboard; the browser queues past its per-origin limit — no client queue.

### Full screen, print, export, bookmarks

- On a dashboard tab, full screen and print apply to the **whole canvas**; print sizes each widget's chart to
  its printed cell box.
- Image / CSV export stay per worksheet (reach them via **Edit**). Bookmarks capture worksheets only; the
  bookmark action is hidden on dashboard tabs, and a bookmark whose worksheet was closed is reported, as
  today.

## Code

| File | Change |
|---|---|
| `Features/Dashboard/chart.js` | per-container state (24a) |
| `Features/Dashboard/worksheet-view.js` | **new** — the query-and-render path (24a) |
| `Features/Dashboard/sheet-plan.js` | **new** — DOM-free plan building (`buildPlan`, `planDims`, `planMeasures`, sort targets), shared by the editor and the view (24a) |
| `Features/Dashboard/dashboards.js` | editor only; uses one view; store renames (24a) |
| `Features/Board/` | `_Board.cshtml`, `board-model.js` (built); **built:** `board.js`, `board-widget.js`, `board-panel.js`, `board.css`, `board-layout.js` (cell → pixels, stacking); **to build:** `board-drag.js` (pointer move / resize), `board-layout.js` additions (snap from pixels, clamp, keyboard bounds) and undo |
| tests | `board-layout.test.mjs` (geometry built; snapping to build), `tests/live/board-ui.mjs` (render built); `board-model.test.mjs`, `workbook-v2.test.mjs`, `store-tabs.test.mjs` and `tests/live/tabs-ui.mjs` exist |

## Testing

- **Pure:** `board-layout` — snap from pixels, collision, first free spot, clamp, keyboard move / resize
  bounds;
  `worksheet-view` plan building over the existing plan cases.
- **Browser (headless, mocked API, light + dark):** two worksheets on one dashboard each send their own
  query and draw; one failing query leaves the other drawn; move + resize persist across reload; overlap
  drop snaps back; Edit opens the worksheet; text widget edit + undo; every earlier browser check still passes.
- `dotnet test` unchanged and green.

## Docs

New `features/dashboards.md` (the board); extend `features/tabs.md`, `reference/frontend-modules.md`, `design/layout.md` (the canvas)
and `ARCHITECTURE.md`; `backlog/dashboards.md` keeps only 24c, 24d once the board is built.

## Done when

24b board: ≥ 2 worksheets on one dashboard, arranged and resized on the grid, re-querying independently; text widgets;
the KB updated and this file deleted.
