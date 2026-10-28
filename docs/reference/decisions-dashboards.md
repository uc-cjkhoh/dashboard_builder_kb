# Decisions — dashboards

Continues [decisions.md](decisions.md) (D1–D25) and [decisions-calculated-fields.md](decisions-calculated-fields.md) (D26–D60, D65–D66).
Behaviour: [tabs.md](../features/tabs.md), [workbook.md](../features/workbook.md). Edit an entry in place when it changes.

### D61 — Worksheets and dashboards are separate tab kinds; workbook format v2
**Tableau-style.** A worksheet stays a tab edited exactly as before; a dashboard is a second tab kind that composes existing
worksheets (and text) on a 12-column snap grid, and one worksheet may sit on several dashboards. The store keeps **one ordered
`tabs` list** — `{ id: "ws#n", kind: "worksheet", name, sheet }` and `{ id: "db#n", kind: "dashboard", name, widgets }` — so the strip
order is the data order. The editor's old vocabulary is renamed inside (`dashboards` → worksheet tabs, `worksheet:changed`, ids
`ws#n`), and **"dashboard" now means only the new kind**; `dashboard:changed` signals a change to a dashboard's widgets.
- **Limits** are client-side only, like calculations (the server never sees a dashboard; no new endpoint, D21 stands): 50 tabs of either
  kind, 12 widgets per dashboard, `w` 2–12, `h` 2–24 (text 1–24), `y + h` ≤ 96, heading ≤ 80, body ≤ 2000. Creation refuses past a
  limit with a toast; **import repairs and reports** instead of refusing the file — clamp into the grid, move an overlapping widget to the
  first free spot, drop one that has no worksheet or no room (`Board/board-model.js`, pure and node-tested).
- **Format v2** saves `worksheets`, `dashboards` (widgets point at worksheets by index), `tabs` (the strip order) and `active`
  (`{ kind, index }`); bookmarks carry `worksheet` / `worksheetName` since a bookmark captures a worksheet. The version is bumped
  because the shape changed: **an older build refuses a v2 file** rather than opening it and silently losing the dashboards.
- **The v1 reader stays for good** (`migrateV1`): every v1 `dashboards[i]` becomes `worksheets[i]`, the tab order and `active` follow, and a
  valid v1 file opens with identical content and no issues. Autosave writes `dashboardbuilder.workbook.v2|host|port|user`; with no v2 entry it
  reads the v1 key and **leaves it in place** (never rewritten or deleted), so an older build open in another tab keeps working.
- **Rejected:** keeping version 1 and adding a `dashboards` list beside the old one (names would collide with v1's meaning and an old build
  would drop dashboards without saying so); a second renderer or per-widget app copy for widgets (one worksheet view serves the tab and the widget —
  [worksheet.md](../features/worksheet.md)); duplicating a dashboard (its widgets would share worksheets and layout — build another).

## D62 — The board renders only the active dashboard, through the editor's result cache

- **Decision.** Only the active dashboard has live views: leaving it destroys every widget's worksheet view, and showing it rebuilds
  them. Widgets run through the **same result cache as the worksheet editor** (`sharedResults`, keyed by the exact request), so a
  widget draws what its worksheet tab just ran and a re-shown dashboard re-queries only what changed or failed. Widget positions are
  computed in JS by the pure `board-layout.js` (not CSS grid), and below 720px of canvas width widgets stack full width in reading order.
- **Why.** Twelve live charts on a hidden tab would hold queries and chart instances for nothing, and "stale" tracking would be
  extra state; rebuilding from a content-addressed cache is correct by construction. JS geometry is what pointer snapping, the ghost
  and keyboard moves need next, and it makes the narrow-canvas rule testable. A 2-column widget on a narrow grid is ~100px, so
  stacking beats shrinking.
- **Rejected:** keeping hidden dashboards alive (leaks); a separate cache per widget (the same query would run twice after an edit);
  CSS grid with `grid-column` (no pixel geometry to snap against).

## D63 — Board edits are refused, never repaired; every verdict is pure; history is in memory

- **Decision.** A move, resize, keyboard step or panel drop that overlaps a widget, leaves the grid or breaks a size limit is **refused
  with a reason and changes nothing** (the golden-rule-3 stance: reject, don't clamp) — the one verdict, `explainRefusal`, serves the
  ghost, the drop and the keys. The only leniency is a panel drop's x, which slides left to keep the default width inside the 12 columns
  (the pointer stays within the widget). The pointer state machine, snapping, key steps, text validation and history are DOM-free modules
  with node tests; `board-interact.js` only turns events into points. Undo reuses the worksheet editor's `history.js` (snapshots of the
  **widget list**, keyed by dashboard id) and is **in memory** — a reload keeps the autosaved layout but not the steps. A text widget now
  defaults to 12 × 2 (a 1-row cell showed no body), can still be shrunk to 1 row, and opens over its neighbours while its edit form is open.
- **Why.** A silent relocation (pushing neighbours aside, clamping into the grid) would make a drop land somewhere the user didn't aim,
  and an exact verdict is testable. Persisting history would mean storing a stack of past layouts in the workbook for a rarely needed
  feature, and the editor's history is not persisted either.
- **Rejected:** auto-pushing overlapped widgets down (unpredictable, can run past 96 rows); a CSS-grid drag library (no tokens, no node
  tests, a dependency); persisting undo; a second history implementation for the board.


## D64 — One transient dashboard selection filters the other widgets

- **Decision.** A mark click in a worksheet widget sets the dashboard's one selection; every other worksheet widget adds the same bound
  `=` the worksheet's own click selection uses, **only when the selected table is already in its query** (never a join; otherwise a
  note). The source is exempt and fades the other marks; a header chip clears it. In memory only; it ends with the dashboard being shown,
  its source widget, or the source's primary dimension. Widgets run `interactive: "select"` (select, never drill).
- **Why.** The smallest model that closes cross-sheet filtering without a join graph or an actions UI; a shared table is the same
  requirement Tableau's filter actions have, and the filter stays within the server's 20 and golden rule 3.
- **Detail.** The dashboard selection replaces a target's own click selection only when it applies (else the widget keeps its own);
  the source's fade re-runs the view from the result cache rather than restyling the live chart.
- **Rejected:** forcing a join to reach a widget; saving the selection; multi-select and configurable actions (T08-20..24).

### D69 — A named hierarchy is a workbook list a sheet copies from, not a reference
A hierarchy is `{ id, name, levels }` on the workbook; applying it writes a fresh `sheet.drill` (the same shape the Drill tool builds), so the drill state
machine, bookmarks, undo and the query path are untouched and a sheet keeps working when the hierarchy is renamed, edited or deleted. A live reference would need
a missing-hierarchy state on every sheet and bookmark. The cost: editing a hierarchy doesn't update sheets that already used it (re-apply it). Levels are plain
columns of one table (a calculated or cast field is refused — a cast or formula could change under a stored level), the limits are client-side only, and the optional
workbook field needs no version bump because the reader ignores unknown fields and an absent one means none. A dropped hierarchy replaces the drill rather than appending.
