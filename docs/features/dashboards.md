# Dashboards — the board

A dashboard tab (`.tab--dashboard`) composes the workbook's worksheets and text blocks on a 12-column snap grid. Code:
`Features/Board/` — `board.js` (orchestration, full screen, print), `board-widget.js` (one widget), `board-panel.js` (the side
panel), pure `board-layout.js` (cell → pixel geometry) and `board-model.js` (widget rules and limits), `board.css`, `_Board.cshtml`
(`#board-view`). Tab kinds, store records and events: [tabs.md](tabs.md), [data-model.md](../reference/data-model.md#tabs-and-dashboards);
saving: [workbook.md](workbook.md). Why separate tab kinds: [D61](../reference/decisions-dashboards.md#d61--worksheets-and-dashboards-are-separate-tab-kinds-workbook-format-v2).

## Layout

- **Side panel** (left, 240px; the worksheet's field-pane slot): the workbook's worksheets, each with an **Add** button
  (`aria-label` "Add the worksheet “Sales” to the dashboard"), then **Add text**. The list redraws only when a worksheet is
  added, closed or renamed, so a button keeps focus when a widget is added.
- **Bar** above the canvas: the dashboard's name, "n of 12 widgets", **Full screen** and **Print**.
- **Canvas** (`#board-scroll`): 12 columns; row height `calc(var(--ctl-h) * 2)`, gap `var(--s3)`; widgets are absolutely
  positioned from `board-layout.js` (`layoutBoard(widgets, panelWidth, { rowH, gap })` → pixel rects; `board.js` reads the row
  height and gap from the tokens). The canvas grows downward (at most 96 rows) and scrolls **inside its panel** — the page never
  scrolls (golden rule 8). Column width follows the canvas width; a `ResizeObserver` on the grid re-lays out.
- **Narrow canvas:** below `STACK_BELOW` = 560px the grid is unusable, so widgets **stack full width in reading order** (by row,
  then column), each keeping its row count; the DOM order is the same reading order. At viewport width ≤ 760px the side panel
  moves above the canvas as a short scrolling list. The shell keeps its sidebar at every width, so a phone user collapses it first.
- An empty dashboard shows "This dashboard is empty — add a worksheet or a text block from the list on the left."

## Adding and removing

- **Add** (worksheet) and **Add text** place the widget with `placeNew` (the first free spot scanning rows top to bottom; 6 × 4,
  text 12 × 1) and call `setWidgets` → `dashboard:changed`, which the workbook autosave already listens to. When nothing fits
  (12 widgets, or no free row under the 96-row limit) a danger toast says so ("A dashboard holds at most 12 widgets." / "The
  dashboard is full — …") and nothing is added. A worksheet may be added more than once. The new widget scrolls into view.
- A text widget starts with the heading "Text" and no body. Editing its text, and moving or resizing any widget, are not built yet
  ([backlog](../backlog/dashboards.md)).
- **Remove** (header button, `aria-label` "Remove “name” from the dashboard") drops the widget, toasts "Removed “name”.", and moves
  focus to the next widget's Remove button (else **Add text**). Siblings are not redrawn. There is no undo yet.
- Closing a worksheet removes its widgets from every dashboard ([tabs.md](tabs.md)); a widget whose worksheet is missing reads
  "This worksheet was closed."

## Widgets

Each widget is an `<article class="board-widget">` with a header — title, then icon buttons — over a body.

| Kind | Header | Body |
|---|---|---|
| **Worksheet** | the worksheet's name; **Edit** (switches to that worksheet's tab) and **Remove** | a non-interactive worksheet view of the worksheet's sheet |
| **Text** | the heading; **Remove** | the body text, plain (`textContent`; line breaks kept, no Markdown, no markup) |

- A worksheet widget is `createWorksheetView(body, getContext, { interactive: false })` ([worksheet.md](worksheet.md#query-lifecycle)):
  its own latest-wins gate, table pager and chart instance, so widgets never abort or overwrite each other. It reads the
  worksheet's **current** sheet on every run and applies the workbook's shared filters, parameters and calculations through the
  same `planCtx()` as the editor. **No mark selection, drill, Pages or status bar; tooltips, table paging and the legend
  highlight stay** ([worksheet-encodings.md](worksheet-encodings.md)). The result notice (e.g. "more rows exist") shows under the header.
- **Failure and hint states render inside the widget**, in the worksheet's own words (a rejected query, "Drag fields onto Columns
  and Rows…", fields from unrelated tables, a calculation that can't be computed); a failing widget leaves its siblings drawn.
- Queries are scoped by worksheet id and go through the **editor's result cache** (`sharedResults` in `dashboards.js`, keyed by the
  exact request), so a widget draws what its worksheet tab just ran and an unchanged sheet is served without a query. A widget
  whose request failed is not cached and runs again when shown. Up to 12 queries run in parallel; the browser queues past its
  per-origin limit.

## Lifecycle

- **Only the active dashboard renders.** Leaving it (another tab, the Data Model) destroys every widget — queries aborted, chart
  instances and their resize observers released, DOM removed. Showing it again rebuilds the widgets; a worksheet that was edited
  meanwhile draws its new sheet, an unedited one comes from the cache. (`worksheet:changed` for a widget's sheet while its dashboard
  is on screen re-runs that widget.)
- A layout change (add, remove, a rename, `tabs:changed`) **reconciles by widget id**: existing widgets keep their view and chart.
- `theme:changed` and `scheme:changed` re-run every live view — a cache hit, repainted in the new colours, no query.
- **Resize** re-lays out the grid and each chart re-fits through its own observer (`chart.js`); no query. After a reload a widget that
  drew a hint before its tables' columns arrived runs again once they do (`entity:loaded`).

## Full screen and print

- **Full screen** shows the bar and canvas (the whole board) full screen (Fullscreen API, falling back to a fixed overlay;
  Esc / the button exits).
- **Print** prints the canvas only: the grid is laid out at a fixed 1000px page width, with the side panel, bar buttons and widget
  buttons hidden (`@media print` in `board.css`).
- Image and CSV export, and bookmarks, stay per worksheet (reach them with **Edit**); the bookmark action is hidden on a dashboard.

## Tests

`tests/js/board-layout.test.mjs` (geometry, the 96-row limit, stacking), `board-model.test.mjs` (rules and limits);
`tests/live/board-ui.mjs` (mocked API: three widget kinds draw with their own queries, a failing widget, Remove, Edit, disposal on
tab switch, a worksheet edit, theme flip, phone stacking, full screen, reload from autosave; light, dark and phone screenshots).
