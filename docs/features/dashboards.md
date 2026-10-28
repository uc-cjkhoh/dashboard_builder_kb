# Dashboards — the board

A dashboard tab (`.tab--dashboard`) composes the workbook's worksheets and text blocks on a 12-column snap grid. Code:
`Features/Board/` — `board.js` (orchestration, undo / redo, full screen, print), `board-widget.js` (one widget, inline text edit),
`board-panel.js` (the side panel), `board-interact.js` (pointer, keyboard and panel-drop wiring), and the pure, node-tested
`board-layout.js` (cell ↔ pixel geometry), `board-model.js` (widget rules and limits), `board-drag.js` (the pointer state machine),
`board-keys.js`, `text-edit.js` and `board-history.js`; `board.css`, `_Board.cshtml` (`#board-view`). Tab kinds, store records and events: [tabs.md](tabs.md), [data-model.md](../reference/data-model.md#tabs-and-dashboards);
saving: [workbook.md](workbook.md). Why separate tab kinds: [D61](../reference/decisions-dashboards.md#d61--worksheets-and-dashboards-are-separate-tab-kinds-workbook-format-v2).

## Layout

- **Side panel** (left, 240px; the worksheet's field-pane slot): the workbook's worksheets, each with an **Add** button
  (`aria-label` "Add the worksheet “Sales” to the dashboard"), then **Add text**. The list redraws only when a worksheet is
  added, closed or renamed, so a button keeps focus when a widget is added.
- **Bar** above the canvas: the dashboard's name, "n of 12 widgets", the **status line** (below), **Undo** / **Redo**, **Full screen**
  and **Print**.
- **Canvas** (`#board-scroll`): 12 columns; row height `calc(var(--ctl-h) * 2)`, gap `var(--s3)`; widgets are absolutely
  positioned from `board-layout.js` (`layoutBoard(widgets, panelWidth, { rowH, gap })` → pixel rects; `board.js` reads the row
  height and gap from the tokens). The canvas grows downward (at most 96 rows) and scrolls **inside its panel** — the page never
  scrolls (golden rule 8). Column width follows the canvas width; a `ResizeObserver` on the grid re-lays out.
- **Narrow canvas:** below `STACK_BELOW` = 720px the grid is unusable, so widgets **stack full width in reading order** (by row,
  then column), each keeping its row count; the DOM order is the same reading order. At viewport width ≤ 760px the side panel
  moves above the canvas as a short scrolling list. The shell keeps its sidebar at every width, so a phone user collapses it first.
- An empty dashboard shows "This dashboard is empty — add a worksheet or a text block from the list on the left."

## Adding and removing

- **Add** (worksheet) and **Add text** place the widget with `placeNew` (the first free spot scanning rows top to bottom; 6 × 4,
  text 12 × 2) and call `setWidgets` → `dashboard:changed`, which the workbook autosave already listens to. When nothing fits
  (12 widgets, or no free row under the 96-row limit) a danger toast says so ("A dashboard holds at most 12 widgets." / "The
  dashboard is full — …") and nothing is added. A worksheet may be added more than once. The new widget scrolls into view.
- A text widget starts with the heading "Text" and no body; a text widget is 12 × 2 by default and may be resized down to 1 row.
- A worksheet row in the side panel is **draggable** (see Dropping from the panel); **Add** stays the keyboard path.
- Adding also announces "Added “name” to the dashboard." through the polite live region (`#toast-live`). A worksheet widget's loading
  state has a **Cancel** button labelled "Cancel loading <worksheet name>".
- **Remove** (header button, `aria-label` "Remove “name” from the dashboard") drops the widget, toasts "Removed “name”.", and moves
  focus to the next widget's Remove button (else **Add text**). Siblings are not redrawn. There is no undo yet.
- Closing a worksheet removes its widgets from every dashboard ([tabs.md](tabs.md)); a widget whose worksheet is missing reads
  "This worksheet was closed."

## Widgets

Each widget is an `<article class="board-widget">` with a header — title, then icon buttons — over a body.

| Kind | Header | Body |
|---|---|---|
| **Worksheet** | the worksheet's name; **Edit** (switches to that worksheet's tab) and **Remove** | a non-interactive worksheet view of the worksheet's sheet |
| **Text** | the heading (empty reads "Text"); **Edit** (inline, below) and **Remove** | the body text, plain (`textContent`; line breaks kept and wrapped, no Markdown, no markup) |

Every widget is a focusable group (`tabindex="0"`, `role="group"`, `aria-roledescription="dashboard widget"`, `aria-label` its name,
`aria-describedby` a one-line key hint) with a visible focus ring, and has a corner grip at its bottom-right.

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
  per-origin limit. Known cost: two widgets of one worksheet shown together (or a widget run while the same request is in flight)
  each send the query — there is no in-flight de-duplication.

## Editing the layout

All geometry and verdicts are pure; `board-interact.js` turns events into points (relative to the grid, so scrolling mid-drag needs no
correction), draws the **ghost** and commits. Every committed edit is **one undo step** and fires `dashboard:changed` (autosave).

- **Move** — press the widget **header** (not its buttons) and drag; **resize** — drag the **corner grip**. Pointer capture on the
  header / grip; a press that travels under 4px is a click, not a drag. The pointer delta snaps to the nearest whole cell
  (`snapMove`, `snapResize`); the dragged widget dims and a dashed **ghost** covers the target cells. When the target overlaps
  another widget, runs off the grid, or breaks a size limit the ghost turns refused (danger border + "Can't drop here" with an
  icon), and a release **snaps back**: nothing moves and the status line says why ("Can't move: it would overlap “Sales”.") —
  never silently moved elsewhere. `pointercancel`, a lost capture, window blur and Esc end the drag with no ghost and no change.
  `touch-action: none` on the header and grip. **No drag on a stacked (narrow) canvas** — the header and grip are plain there.
- **Keyboard** — focus a widget (Tab): **arrows** move it one cell, **Shift + arrows** resize from the bottom-right (Right / Down
  grow, Left / Up shrink). Each key press is a committed step; a refused one changes nothing. Keys act only while the widget itself
  (not a button or field inside it) has focus, and focus stays on the widget after a step. Works on a stacked canvas too.
- **Status line** (`#board-status`, a polite live region and visible in the bar): "Moved to column 3, row 2", "Resized to 4 columns
  by 3 rows", "Text updated.", "Undid the last change.", or the refusal in the danger colour with a warning icon. The refusal wording is
  `explainRefusal` in `board-model.js` (one place for the drag, the keys and the drop): whole cells, size limits (w 2–12; h 2–24
  worksheet, 1–24 text), left / right / top edge, 96 rows, then "it would overlap “name”". It clears after 8 seconds.
- **Dropping from the panel** — dragging a worksheet row (MIME `application/x-dashboardbuilder-worksheet`, carrying the worksheet id)
  over the canvas shows the ghost of a default-size (6 × 4) widget whose top-left is the cell under the pointer, slid left just far
  enough to stay inside the 12 columns; the drop adds it there (an added widget, like Add, toasts "Added …"). A taken or too-low
  cell, or a 12th-plus widget, refuses with the status line and adds nothing; a stacked canvas says to use **Add**. Other drags are ignored.
- **Text edit** — **Edit** on a text widget replaces its body with a form: a labelled **Heading** input (≤ 80) and **Text** textarea
  (≤ 2 000), `maxLength` from `LIMITS`, a live "n / max" count, **Save** and **Cancel**. Enter in the heading or Ctrl+Enter saves;
  Esc or Cancel discards; focus returns to **Edit**. `validateTextEdit` (`text-edit.js`) trims and checks both fields, and an invalid
  save stays open with a message under the field (`role="alert"`, `aria-invalid`) and focus on it. A save that changes nothing is not
  an undo step. The widget grows (over its neighbours, `.is-editing`) while the form is open, since a 2-row cell can't hold it. If the
  text changes underneath (an undo), the form closes.
- **Undo / redo** — buttons in the bar (disabled when there is nothing to do) and **Ctrl+Z**, **Ctrl+Shift+Z** / **Ctrl+Y** while a
  dashboard tab is active, never while typing in an input, textarea, select or dialog and never on a worksheet tab (the worksheet
  editor keeps its own shortcut). `Dashboard/history.js` (the editor's snapshot stack, 50 deep) keyed by dashboard id, holding the
  **widget list** before each edit: add, remove, move, resize, text edit. A restore drops worksheet widgets whose worksheet has been
  closed since (`restorable`). History is **in memory**: a reload or a workbook open starts empty (the layout itself is autosaved),
  and closing a dashboard forgets its history.

## Lifecycle

- **Only the active dashboard renders.** Leaving it (another tab, the Data Model) destroys every widget — queries aborted, chart
  instances and their resize observers released, DOM removed. Showing it again rebuilds the widgets; a worksheet that was edited
  meanwhile draws its new sheet, an unedited one comes from the cache. (`worksheet:changed` for a widget's sheet while its dashboard
  is on screen re-runs that widget.)
- A layout change (add, remove, move, resize, a rename, `tabs:changed`) **reconciles by widget id**: existing widgets keep their view,
  chart and focus; a move or resize re-lays out and each chart re-fits with no query.
- `theme:changed` and `scheme:changed` re-run every live view — a cache hit, repainted in the new colours, no query. A widget that
  showed an **error** has nothing cached, so a theme flip queries it again.
- **Resize** re-lays out the grid and each chart re-fits through its own observer (`chart.js`); no query. After a reload a widget that
  drew a hint before its tables' columns arrived runs again once they do (`entity:loaded`).

## Full screen and print

- **Full screen** (the button's text changes to "Exit full screen") shows the bar and canvas (the whole board) full screen (Fullscreen API, falling back to a fixed overlay;
  Esc / the button exits).
- **Print** prints the canvas only, with the side panel, bar buttons and widget buttons hidden (`@media print` in `board.css`). On
  `beforeprint` the board lays itself out **stacked at a fixed 1000px page width** (`layoutBoard(…, { stack: true })`) and the widgets
  print **in flow, one column** (`position: relative`, `break-inside: avoid`) — an absolutely positioned widget could be split or
  cropped across pages. Each worksheet widget's chart is sized to its printed cell (`sizeChart(body, { width, height })` from the cell
  box less header and padding), overriding the worksheet print rule that fixes every chart canvas at 1000 × 560; `afterprint` restores
  the screen layout and chart sizes. The arrangement on screen (side by side) is not kept on paper.
- Image and CSV export, and bookmarks, stay per worksheet (reach them with **Edit**); the bookmark action is hidden on a dashboard.

## Tests

`tests/js/board-layout.test.mjs` (geometry, the 96-row limit, stacking), `board-model.test.mjs` (rules and limits), `board-drag.test.mjs`
(pixel → cell snapping, ghost, click threshold, every refusal, cancel, panel drop plan), `board-keys.test.mjs` (every step and refusal
message), `text-edit.test.mjs`, `board-history.test.mjs`; `tests/live/board-edit-ui.mjs` (real mouse events: move and resize with the
ghost, overlapping / off-grid drops that snap back, keyboard and the live status, text edit / limits / Esc, undo and redo of every edit
type by button and shortcut, panel drag, pointercancel / blur / Esc, no drag when stacked, reload keeps the layout but not the history;
light and dark screenshots with the ghost, a refused ghost and the focus ring);
`tests/live/board-ui.mjs` (mocked API: three widget kinds draw with their own queries, a failing widget, Remove, Edit, disposal on
tab switch, a worksheet edit, theme flip, phone stacking, full screen, reload from autosave, a shared filter and a parameter in a
widget's query, a calculated field + cast + tooltip template + member colour in a widget, table paging inside a widget, the Cancel
label and live-region announcement, and print layout checked under emulated print media with the chart-to-cell geometry; light,
dark, phone and print screenshots). Not verified: the browser's real print dialog and PDF pages.
