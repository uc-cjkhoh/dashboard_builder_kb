# Decisions — dashboards

Continues [decisions.md](decisions.md) (D1–D25) and [decisions-calculated-fields.md](decisions-calculated-fields.md) (D26–D60).
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
  computed in JS by the pure `board-layout.js` (not CSS grid), and below 560px of canvas width widgets stack full width in reading order.
- **Why.** Twelve live charts on a hidden tab would hold queries and chart instances for nothing, and "stale" tracking would be
  extra state; rebuilding from a content-addressed cache is correct by construction. JS geometry is what pointer snapping, the ghost
  and keyboard moves need next, and it makes the narrow-canvas rule testable. A 2-column widget on a phone-width grid is ~80px, so
  stacking beats shrinking.
- **Rejected:** keeping hidden dashboards alive (leaks); a separate cache per widget (the same query would run twice after an edit);
  CSS grid with `grid-column` (no pixel geometry to snap against).
