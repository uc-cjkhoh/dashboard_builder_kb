# Tabs — Data Model, worksheets and dashboards

The view strip across the top of the content area. Code: `Features/Tabs/` (`tabs.js`, `tabs.css`,
`duplicate-model.js`) over the shared state in `Core/store.js`; the dashboard tab's body is `Features/Board/`.
Why one shared model: [D12](../reference/decisions.md#d12--subtabs-are-dashboards-over-one-shared-data-model);
why two tab kinds: [D61](../reference/decisions-dashboards.md#d61--worksheets-and-dashboards-are-separate-tab-kinds-workbook-format-v2).

## The strip

- Tabs are frosted pills (tier-2 glass controls): the active tab has an accent fill, edge and underline and bold text. A pinned **Data Model** tab (`.tab--model`) — the shared entity canvas ([canvas.md](canvas.md) +
  [relationships.md](relationships.md)). It cannot be closed.
- After it, **one ordered list** of two tab kinds, each with its kind's icon (`.tab__kind`, decoration only) and the kind in
  its accessible name (`aria-label` "Sales (worksheet)" / "Overview (dashboard)"):
  - **Worksheet** (`.tab--worksheet`, icon `chart-bar`) — one Tableau-style worksheet ([worksheet.md](worksheet.md)).
  - **Dashboard** (`.tab--dashboard`, icon `dashboard`) — a board of worksheet, text, image and spacer widgets ([dashboards.md](dashboards.md)). Its
    data — widgets, limits, validation, save and open — is in
    [data-model.md](../reference/data-model.md#tabs-and-dashboards).
- **`[+]`** (`.tab-add`, `aria-haspopup="menu"`) opens a menu **New worksheet / New dashboard** (`Core/menu.js`: arrows move, Esc
  closes and returns focus to `[+]`, Enter / Space on a focused item acts). A new tab is active and its label is focused. Default
  names are **"Worksheet N" / "Dashboard N"**, N the first number not in use by a tab of that kind.
- **Limit:** a workbook holds at most **50 tabs of either kind** (`LIMITS.tabs`). Creating one past it toasts "A workbook holds at
  most 50 tabs — close one first.", adds nothing and keeps focus on `[+]`; import caps it the same way ([workbook.md](workbook.md#validation-parseworkbook)).
- **Rename:** double-click a label, or focus it and press `F2` (or `Enter` on the active
  tab), to edit inline (`.tab__rename`, `maxlength` 60). The name is trimmed and must be 1–60
  characters; an empty name reverts and toasts "Tab name is required." Keyboard focus returns to the
  tab's label afterwards. Clicking the tab that is already open does nothing, and the double-click
  listener sits on the strip (`#tabs`), not the label — every switch rebuilds the strip, so a label-level
  listener would lose the double-click.
- The close icon (`.tab__close`, `aria-label` "Close <name>") closes a tab:
  - a **worksheet** used by dashboards confirms by name — "Close the worksheet “Sales”? Used on: Overview, Ops. It will be removed
    from those dashboards." — and, once closed, its widgets are removed from them (each dashboard notified with `dashboard:changed`);
    a worksheet on no dashboard confirms only when it holds content;
  - a **dashboard** with widgets confirms ("The worksheets on it are not affected."); closing one never touches a worksheet.
- The duplicate icon (`.tab__dup`, `aria-label` "Duplicate <name>") appears on **worksheets only**: `store.duplicateWorksheet` deep-copies the sheet
  (shelves, calculated-field pills, filters, marks, format, chart type) and resets the transient state — selection cleared, drill back at
  its first level, pages at the first member (members reload) — and the copy has no undo history. It is named `<name> copy`, then `<name> copy 2`, …
  (a copy of a copy reuses the base name; trimmed to 60 characters), inserted right after the source and made active. At the tab limit
  it toasts "A workbook holds at most 50 tabs." and adds nothing. The naming, limit check and sheet copy are pure
  (`Tabs/duplicate-model.js`). A dashboard is not duplicated (build another).
- The active tab carries `aria-current`.
- The Workbook menu's **Save view as bookmark…** is hidden while a dashboard tab is active (bookmarks capture worksheets only).

## How views switch

- `store.currentView()` is `{ kind: "model" }`, `{ kind: "worksheet", id }` or `{ kind: "dashboard", id }`. `canvas.js` / `relations.js`
  render `#model-view` when the model is active; `dashboards.js` renders the active worksheet into `#worksheet-view`
  (`isWorksheetActive()`); `board.js` shows `#board-view` for a dashboard (`isDashboardActive()`) and renders only the active one, destroying its views when you leave it.
- Each module shows/hides its own view on `view:changed`; the strip redraws on `tabs:changed`. `worksheet:changed { id }` means a
  worksheet's sheet was replaced; `dashboard:changed { id }` means a dashboard's widgets changed.
- Closing the active tab activates its right-hand neighbour (else the left one, else the Data Model).
- All tabs build from the **same** entities and relationships — a table added while on a
  worksheet still lands in the shared model.

## Persistence

Tabs (in strip order), entities, relationships, worksheets and dashboards are saved as the browser **workbook** and restored on
reconnect. The strip's right end holds the quiet autosave text and one **Workbook** overflow menu
(Import / Export) — [workbook.md](workbook.md).
