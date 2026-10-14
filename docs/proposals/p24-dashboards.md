# P24a + P24b — Worksheet views and multi-worksheet dashboards

A proposal, not yet built. P24 is split into four phases; this spec covers the first two:

| Phase | What | This spec |
|---|---|---|
| **24a** | Widget runtime — the worksheet query-and-render path becomes instantiable; `chart.js` keeps one chart per container | yes |
| **24b** | Dashboard composition — worksheets and dashboards as separate tab kinds; a snap-grid canvas of worksheet and text widgets; workbook format v2 | yes |
| 24c | Cross-widget filtering — a mark selected in one widget filters the others | later spec |
| 24d | Stories — ordered, captioned snapshots | later spec |

When built, the behaviour moves into a new [features/](../features/worksheet.md) file `dashboards.md` and the
docs listed under [Docs](#docs), [roadmap.md](roadmap.md#p24--multi-worksheet-dashboards--stories) keeps
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

Recorded as **D26** in [decisions.md](../reference/decisions.md) when built; it answers O3.

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
- **Store rename:** `dashboards` → `worksheets`, `activeDashboard` → `activeWorksheet`,
  `createDashboard` → `createWorksheet`, `dashboard:changed` → `worksheet:changed`, ids `ws#N`.
- **Done when (24a):** the app behaves exactly as before — both suites and the P22 browser checks green —
  and two views can render into two containers at once (browser check).

## 24b — Dashboards

### Tabs

- Strip: **Data Model** (pinned), then worksheet and dashboard tabs in one ordered list, each with its kind's
  icon (`chart-bar` / a new `dashboard` icon) and its kind in the accessible name.
- **+** opens a menu: *New worksheet* / *New dashboard*. Default names "Worksheet N" / "Dashboard N".
- `LIMITS.dashboards` (50) is renamed `LIMITS.tabs` and covers both kinds; it is enforced at creation (a toast
  says why) as well as on import.
- Closing a **worksheet** used by dashboards: the confirm names them ("Used on: Sales overview, Ops") and its
  widgets are removed from them. Closing a dashboard never touches its worksheets.

### Store

```
tabs:    [ { id: "ws#3", kind: "worksheet", name, sheet },
           { id: "db#1", kind: "dashboard", name, widgets: [ widget, … ] }, … ]
widget:  { id: "w#7", kind: "sheet", sheetId: "ws#3", x, y, w, h }
       | { id: "w#8", kind: "text", heading, body, x, y, w, h }
```

`activeView` becomes `{ kind: "model" } | { kind: "worksheet", id } | { kind: "dashboard", id }`. Events:
`dashboard:changed { id }` (new meaning: layout / text edits), `worksheet:changed { id }`.

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

### Workbook format v2

```
{ format, version: 2, savedAt, entities, relationships, theme, sharedFilters, fields, parameters, bookmarks,
  worksheets: [ { name, sheet } ],
  dashboards: [ { name, widgets: [ { kind: "sheet", sheet: <worksheet index>, x, y, w, h }
                                 | { kind: "text", heading, body, x, y, w, h } ] } ],
  tabs:   [ { kind: "worksheet" | "dashboard", index } ],     // strip order
  active: { kind, index } | null }
```

- **v1 → v2** (`migrateV1`): every v1 `dashboards[i]` becomes `worksheets[i]`; no dashboards; tab order =
  worksheet order; `active` and bookmark `dashboard` indexes carry over as worksheet indexes.
- **Import validation** (into the existing `issues` list, never silent): a widget whose worksheet index is
  missing is dropped; an off-grid or undersized widget is clamped; an overlapping widget is moved to the
  first free spot; widgets past 12 and tabs past 50 are dropped — each reported.
- **Autosave** writes key `dashboardbuilder.workbook.v2|host|port|user`; on load, if it is absent, the v1 key
  is read and migrated (and left in place).

## Code

| File | Change |
|---|---|
| `Features/Dashboard/chart.js` | per-container state (24a) |
| `Features/Dashboard/worksheet-view.js` | **new** — the query-and-render path (24a) |
| `Features/Dashboard/dashboards.js` | editor only; uses one view; store renames (24a) |
| `Features/Core/store.js`, `Core/validate.js`, `Core/icons.js` | `tabs`, widgets, renames, limits, `dashboard` icon |
| `Features/Tabs/tabs.js` | two tab kinds, **+** menu, worksheet-in-use confirm |
| `Features/Board/` | **new** — `_Board.cshtml`, `board.js` (canvas, widgets, side panel, undo), `board.css`, `board-layout.js` (pure: snap, collide, first free, clamp) |
| `Features/Workbook/workbook-model.js`, `workbook.js` | v2 format, `migrateV1`, widget validation, v2 autosave key with v1 fallback |
| `Features/Shell/Index.cshtml`, `app.js` | mount the Board feature |
| tests | `board-layout.test.mjs` (new), `workbook-model.test.mjs` (v2 + migration), `chart.js` per-container and `worksheet-view` where pure |

## Testing

- **Pure:** `board-layout` — snap from pixels, collision, first free spot, clamp, keyboard move / resize
  bounds; `workbook-model` — v2 round trip, v1 file → v2, each import issue above, 12 / 50 caps;
  `worksheet-view` plan building over the existing plan cases.
- **Browser (headless, mocked API, light + dark):** two worksheets on one dashboard each send their own
  query and draw; one failing query leaves the other drawn; move + resize persist across reload; overlap
  drop snaps back; Edit opens the worksheet; text widget edit + undo; a v1 autosave opens as worksheets;
  closing a used worksheet names its dashboards; every P22 check still passes.
- `dotnet test` unchanged and green.

## Docs

New `features/dashboards.md`; update `features/tabs.md`, `features/workbook.md`, `features/worksheet.md`
(it is now "a worksheet tab"), `reference/data-model.md`, `reference/frontend-modules.md`,
`reference/decisions.md` (D26, O3 answered; D16's "a dashboard is one worksheet" reworded), `ARCHITECTURE.md`,
`design/layout.md` (the canvas), `proposals/roadmap.md` (P24 → 24c, 24d only).

## Done when

24a: no visible change, all suites and P22 checks green, two views render side by side. 24b: ≥ 2 worksheets
on one dashboard, arranged and resized on the grid, re-querying independently; text widgets; v1 workbooks
and autosaves open as worksheets; the KB updated and this file deleted.
