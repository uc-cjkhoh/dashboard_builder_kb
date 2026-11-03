---
components: [src/DashboardBuilder/Features/Board/, src/DashboardBuilder/Features/Canvas/, src/DashboardBuilder/Features/Core/, src/DashboardBuilder/Features/Dashboard/, src/DashboardBuilder/Features/Relations/, src/DashboardBuilder/Features/Story/, src/DashboardBuilder/Features/Tabs/]
---
# Tabs — Data Source, worksheets, dashboards and stories

The tab strip runs across the top of the content area and switches between the Data Source, worksheets, dashboards and stories.

- Why one shared model: [D12](../../decisions/decisions-platform.md#d12--subtabs-are-dashboards-over-one-shared-data-source).
- Why two tab kinds: [D61](../../decisions/decisions-dashboards.md#d61--worksheets-and-dashboards-are-separate-tab-kinds-workbook-format-v2).

**Code:**

- `Features/Tabs/` — `tabs.js`, `tabs.css`, `duplicate-model.js`
- `Core/store.js` — the shared state the tabs sit over
- `Features/Board/` — the dashboard tab's body
- `Features/Story/` — the story tab's body ([stories.md](stories.md))

## The strip

- **Look.** Tabs are frosted pills (tier-2 glass controls). The active tab has an accent fill and bold text.
  It carries `aria-current`.
- **Data Source tab.** A pinned **Data Source** tab (`.tab--model`) comes first: the shared entity canvas
  ([canvas.md](../data-source/canvas.md) + [relationships.md](../data-source/relationships.md)). It cannot be closed.
- **Worksheets and dashboards.** After it comes **one ordered list** of three tab kinds.
  Each tab shows its kind's icon (`.tab__kind`, decoration only), and its accessible name includes the kind
  (`aria-label` "Sales (worksheet)" / "Overview (dashboard)" / "Tour (story)").
  - **Worksheet** (`.tab--worksheet`, icon `chart-bar`) — one Tableau-style worksheet ([worksheet.md](../worksheet/worksheet.md)).
  - **Dashboard** (`.tab--dashboard`, icon `dashboard`) — a board of worksheet, text, image, button and spacer widgets ([dashboards.md](dashboards.md)).
    Its data (widgets, limits, validation, save and open) is in [data-model.md](../../reference/data-model.md#tabs-and-dashboards).
  - **Story** (`.tab--story`, icon `story`) — ordered, captioned steps over worksheets and dashboards ([stories.md](stories.md)).

### New tab

- **`[+]`** (`.tab-add`, `aria-haspopup="menu"`) opens a menu: **New worksheet / New dashboard / New story**.
  The menu is `Core/menu.js`: arrows move, Esc closes and returns focus to `[+]`, and Enter / Space on a focused item acts.
- A new tab is active, and its label is focused.
- Default names are **"Worksheet N" / "Dashboard N" / "Story N"**, where N is the first number not in use by a tab of that kind.
- **Limit:** a workbook holds at most **50 tabs of either kind** (`LIMITS.tabs`).
  Creating one past it toasts "A workbook holds at most 50 tabs — close one first.", adds nothing and keeps focus on `[+]`.
  Import caps it the same way ([workbook.md](workbook.md#validation-parseworkbook)).

### Rename

- Double-click a label, or focus it and press `F2` (or `Enter` on the active tab), to edit it inline (`.tab__rename`, `maxlength` 60).
- The name is trimmed and must be 1–60 characters. An empty name reverts and toasts "Tab name is required."
- Keyboard focus returns to the tab's label afterwards.
- Clicking the tab that is already open does nothing.
- The double-click listener sits on the strip (`#tabs`), not the label. Every switch rebuilds the strip, so a label-level listener would lose the double-click.

### Close

The close icon (`.tab__close`, `aria-label` "Close <name>") closes a tab.

- **A worksheet used by dashboards** confirms by name: "Close the worksheet “Sales”? Used on: Overview, Ops. It will be removed
  from those dashboards." Once closed, its widgets are removed from them, and each dashboard is notified with `dashboard:changed`.
- **A worksheet on no dashboard** confirms only when it holds content.
- **A dashboard with widgets** confirms ("The worksheets on it are not affected."). Closing a dashboard never touches a worksheet.
- **A worksheet or dashboard shown by story steps** leaves those steps (each story is notified with `story:changed`); the confirm names the stories, and a worksheet or dashboard shown only by stories confirms too.
- **A story with steps** confirms ("The worksheets and dashboards it shows are not affected.").

### Duplicate

The duplicate icon (`.tab__dup`, `aria-label` "Duplicate <name>") appears on **worksheets only**. A dashboard is not duplicated (build another).

- `store.duplicateWorksheet` deep-copies the sheet: shelves, calculated-field pills, filters, marks, format and chart type.
- It resets the transient state: the selection is cleared, drill goes back to its first level, and pages go to the first member (members reload).
  The copy has no undo history.
- **Name:** `<name> copy`, then `<name> copy 2`, … A copy of a copy reuses the base name. The name is trimmed to 60 characters.
- The copy is inserted right after the source and made active.
- At the tab limit it toasts "A workbook holds at most 50 tabs." and adds nothing.
- The naming, limit check and sheet copy are pure (`Tabs/duplicate-model.js`).

## How views switch

- **Current view.** `store.currentView()` is `{ kind: "model" }`, `{ kind: "worksheet", id }`, `{ kind: "dashboard", id }` or `{ kind: "story", id }`.
- **Who renders what:**
  - `canvas.js` / `relations.js` render `#model-view` when the model is active.
  - `dashboards.js` renders the active worksheet into `#worksheet-view` (`isWorksheetActive()`).
  - `board.js` shows `#board-view` for a dashboard (`isDashboardActive()`). It renders only the active one and destroys its views when you leave it.
  - `story.js` shows `#story-view` for a story (`isStoryActive()`), likewise.
- **Events:**
  - Each module shows/hides its own view on `view:changed`.
  - The strip redraws on `tabs:changed`.
  - `worksheet:changed { id }` means a worksheet's sheet was replaced.
  - `dashboard:changed { id }` means a dashboard's widgets changed.
  - `story:changed { id }` means a story's steps changed.
- Closing the active tab activates its right-hand neighbour (else the left one, else the Data Source).
- All tabs build from the **same** entities and relationships: a table added while on a worksheet still lands in the shared model.

## Persistence

- Tabs (in strip order), entities, relationships, worksheets and dashboards are saved as the browser **workbook** and restored on reconnect.
- The strip's right end holds one **Workbook** overflow menu (Import / Export) — [workbook.md](workbook.md).
