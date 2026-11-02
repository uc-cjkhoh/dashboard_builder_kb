# Decisions — dashboards

Continues [decisions.md](decisions.md) (D1–D25) and [decisions-calculated-fields.md](decisions-calculated-fields.md) (D26–D60, D65–D68, D73).
Behaviour: [tabs.md](../../features/workbook/tabs.md), [workbook.md](../../features/workbook/workbook.md). Edit an entry in place when it changes.

### D61 — Worksheets and dashboards are separate tab kinds; workbook format v2
**Tableau-style.** A worksheet is a tab edited on its own. A dashboard is a second tab kind that composes existing
worksheets (and text) on a 12-column snap grid; one worksheet may sit on several dashboards.
- **One ordered list.** The store keeps **one ordered `tabs` list** — `{ id: "ws#n", kind: "worksheet", name, sheet }` and
  `{ id: "db#n", kind: "dashboard", name, widgets }` — so the strip order is the data order.
- **Naming.** Inside the editor, worksheet tabs use worksheet names (not `dashboards`): the event `worksheet:changed` and ids
  `ws#n`. **"Dashboard" means only the composing kind**; `dashboard:changed` signals a change to a dashboard's widgets.
- **Limits are client-side only**, like calculations: the server never sees a dashboard, there is no new endpoint, and D21 stands.
  - 50 tabs of either kind, 12 widgets per dashboard, `w` 2–12, `h` 2–24 (text 1–24), `y + h` ≤ 96, heading ≤ 80, body ≤ 2000.
  - Creation past a limit is refused with a toast.
  - **Import repairs and reports** instead of refusing the file: it clamps into the grid, moves an overlapping widget to the
    first free spot, and drops one that has no worksheet or no room (`Board/board-model.js`, pure and node-tested).
- **Format v2** saves `worksheets`, `dashboards` (widgets point at worksheets by index), `tabs` (the strip order) and `active`
  (`{ kind, index }`). Bookmarks carry `worksheet` / `worksheetName`, since a bookmark captures a worksheet.
  - **Why the version bump:** the shape changed, so **an older build refuses a v2 file** rather than opening it and silently
    losing the dashboards.
- **The v1 reader stays for good** (`migrateV1`). Every v1 `dashboards[i]` becomes `worksheets[i]`, the tab order and `active`
  follow, and a valid v1 file opens with identical content and no issues.
  - Autosave writes `dashboardbuilder.workbook.v2|host|port|user`. With no v2 entry it reads the v1 key and **leaves it in
    place** (never rewritten or deleted), so an older build open in another tab keeps working.
- **Rejected:**
  - keeping version 1 and adding a `dashboards` list beside the old one — names would collide with v1's meaning, and an old
    build would drop dashboards without saying so;
  - a second renderer or a per-widget app copy for widgets — one worksheet view serves the tab and the widget
    ([worksheet.md](../../features/worksheet/worksheet.md));
  - duplicating a dashboard — its widgets would share worksheets and layout; build another instead.

### D62 — The board renders only the active dashboard, through the editor's result cache
Only the active dashboard has live views: leaving it destroys every widget's worksheet view, and showing it rebuilds them.
- **Shared cache.** Widgets run through the **same result cache as the worksheet editor** (`sharedResults`, keyed by the exact
  request). A widget draws what its worksheet tab just ran, and a re-shown dashboard re-queries only what changed or failed.
- **Layout in JS.** Widget positions are computed by the pure `board-layout.js` (not CSS grid). Below 720px of canvas width,
  widgets stack full width in reading order.
- **Why:**
  - Twelve live charts on a hidden tab would hold queries and chart instances for nothing, and "stale" tracking would be extra
    state. Rebuilding from a content-addressed cache is correct by construction.
  - JS geometry is what pointer snapping, the ghost and keyboard moves need, and it makes the narrow-canvas rule testable.
  - A 2-column widget on a narrow grid is ~100px wide, so stacking beats shrinking.
- **Rejected:** keeping hidden dashboards alive (leaks); a separate cache per widget (the same query would run twice after an
  edit); CSS grid with `grid-column` (no pixel geometry to snap against).

### D63 — Board edits are refused, never repaired; every verdict is pure; history is in memory
A move, resize, keyboard step or panel drop that overlaps a widget, leaves the grid or breaks a size limit is **refused with a
reason and changes nothing** (the golden-rule-3 stance: reject, don't clamp).
- **One verdict.** `explainRefusal` serves the ghost, the drop and the keys.
- **One leniency:** a panel drop's x slides left to keep the default width inside the 12 columns (the pointer stays within the
  widget).
- **Pure modules.** The pointer state machine, snapping, key steps, text validation and history are DOM-free modules with node
  tests. `board-interact.js` only turns events into points.
- **Undo** reuses the worksheet editor's `history.js` (snapshots of the **widget list**, keyed by dashboard id) and is **in
  memory**: a reload keeps the autosaved layout but not the steps.
- **Text widgets** default to 12 × 2 (a 1-row cell showed no body), can still be shrunk to 1 row, and open over their
  neighbours while the edit form is open.
- **Why:** a silent relocation (pushing neighbours aside, clamping into the grid) would make a drop land somewhere the user
  didn't aim, and an exact verdict is testable. Persisting history would mean storing a stack of past layouts in the workbook
  for a rarely needed feature, and the editor's history is not persisted either.
- **Rejected:** auto-pushing overlapped widgets down (unpredictable, can run past 96 rows); a CSS-grid drag library (no tokens,
  no node tests, a dependency); persisting undo; a second history implementation for the board.

### D64 — One transient dashboard selection filters the other widgets
A mark click in a worksheet widget sets the dashboard's one selection. Every other worksheet widget adds the same bound `=`
that the worksheet's own click selection uses — **only when the selected table is already in its query** (never a join;
otherwise a note).
- **Source widget.** The source is exempt and fades the other marks; a header chip clears the selection.
- **Lifetime.** In memory only. It ends when the dashboard stops being shown, when its source widget is removed, or when the
  source's primary dimension changes.
- Widgets run `interactive: "select"` (select, never drill).
- **Why:** the smallest model that closes cross-sheet filtering without a join graph or an actions UI. A shared table is the
  same requirement Tableau's filter actions have, and the filter stays within the server's cap of 20 and golden rule 3.
- **Detail.** The dashboard selection replaces a target's own click selection only when it applies (otherwise the widget keeps
  its own). The source's fade re-runs the view from the result cache rather than restyling the live chart.
- **Rejected:** forcing a join to reach a widget; saving the selection; multi-select and configurable actions (backlog IDs
  T08-20..24).

### D69 — A named hierarchy is a workbook list a sheet copies from, not a reference
A hierarchy is `{ id, name, levels }` on the workbook. Applying it writes a fresh `sheet.drill` (the same shape the Drill tool
builds).
- **Why a copy:** the drill state machine, bookmarks, undo and the query path are untouched, and a sheet keeps working when the
  hierarchy is renamed, edited or deleted. A live reference would need a missing-hierarchy state on every sheet and bookmark.
- **Cost:** editing a hierarchy doesn't update sheets that already used it (re-apply it).
- **Levels** are plain columns of one table. A calculated or cast field is refused, because a cast or formula could change
  under a stored level.
- **Limits** are client-side only.
- **No version bump:** the workbook field is optional, the reader ignores unknown fields, and an absent one means none.
- **Dropping a hierarchy** onto a sheet replaces the drill rather than appending, and clears the sheet's mark selection, as
  drilling does.
- **No next-id counter is saved:** sheets copy levels, not ids, so a reused id binds to nothing.

### D71 — Dashboard images are workbook data URLs, not links
An image widget stores its picture as a base64 data URL in the workbook, read from a file picker in the browser.
- **Limits:** PNG, JPEG, GIF or WebP; ≤ 256 KB per file, ≤ 4 per dashboard and ≤ 2 MB of picture data across the whole
  workbook. They are enforced when adding and again on import, which drops whatever no longer fits. Alt text is ≤ 120
  characters and defaults to the file name.
- **Import** re-validates every picture with the same pattern and drops a widget whose source is anything else.
- **Rejected:**
  - a remote `https:` URL — the board would call a third party every time it opens (tracking, availability, mixed trust) and
    the workbook would stop being self-contained, against golden rules 4 and 10;
  - a server-side upload store — it would add persistence the app deliberately lacks (no application database);
  - SVG — a vector file can carry script.
- **Cost:** workbook size (at most 2 MB of pictures in browser storage; a full quota shows a "Not saved — browser storage is
  full" warning, distinct from storage being unavailable), and no in-place replace — remove the widget and add another.

### D72 — Option controls live in a context popup; one chart-type control
A pill, field row or filter shows only what it is. Every option it has (aggregation, role, table calculation, date part and
label policy, field choices, a filter's operator / sharing / value) opens in one reusable popup.
- **How it opens:** right-click, the ContextMenu key, `Shift+F10` or `Enter` on the focused element. The popup is
  `Core/menu.js` `openContextMenu`, a `role=menu` list on `<body>`, so no panel clips it.
- **Why:** inline controls cost width on every pill whether used or not, and hid what a pill *is* behind what it can *do*.
- **Cost:** discoverability — each such element carries the tooltip "Right-click for options".
- **One chart-type control.** The chart-type picker and Show Me were one decision shown twice. The picker is the single control
  (its dimmed items and best-fit icon are Show Me's cues), and picking only sets the type. Show Me's re-layout of Columns / Rows
  is not offered: it was the redundant half.
- **Marks** live in the field pane as a three-column slot grid with no More menu, so every encoding is one click or drop away.
