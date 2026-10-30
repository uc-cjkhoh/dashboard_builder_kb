# Dashboards — the board

A dashboard tab (`.tab--dashboard`) composes the workbook's worksheets, text blocks, images, navigation buttons and spacers on a 12-column snap grid. Code:
`Features/Board/` — `board.js` (orchestration, undo / redo, full screen, print), `board-widget.js` (one widget, inline text edit),
`board-panel.js` (the side panel), `board-interact.js` (pointer, keyboard and panel-drop wiring), and the pure, node-tested
`board-layout.js` (cell ↔ pixel geometry), `board-model.js` (widget rules and limits), `board-drag.js` (the pointer state machine),
`board-keys.js`, `text-edit.js`, `image-model.js`, `nav-model.js` and `board-history.js`; `nav-edit.js` is the button's inline form; `board.css`, `_Board.cshtml` (`#board-view`). Tab kinds, store records and events: [tabs.md](tabs.md), [data-model.md](../reference/data-model.md#tabs-and-dashboards);
saving: [workbook.md](workbook.md). Why separate tab kinds: [D61](../reference/decisions-dashboards.md#d61--worksheets-and-dashboards-are-separate-tab-kinds-workbook-format-v2).

## Layout

- **Side panel** (left, 240px; the worksheet's field-pane slot): the workbook's worksheets, each with an **Add** button
  (`aria-label` "Add the worksheet “Sales” to the dashboard"), then **Add text**, **Add image** (a file picker), **Add button** and **Add spacer**. The list redraws only when a worksheet is
  added, closed or renamed, so a button keeps focus when a widget is added.
- **Bar** above the canvas: the dashboard's name, "n of 12 widgets", the **status line** (below), the **Size** select, **Undo** / **Redo**,
  **Full screen** and **Print**.
- **Size** (`Board/board-size.js`, per dashboard): **Automatic** (default; the canvas fills its panel and stacks when narrow, as below) or a
  **fixed** preset (800 × 600, 1024 × 768, 1280 × 720, 1366 × 768, 1920 × 1080). A fixed board is exactly that box, never stacked: columns span the
  width and the rows in use (down to the lowest widget) stretch to share the height (`layoutBoard(…, { fixed })`, `fixedRowH`), so
  drag and resize snap to the drawn rows. The panel scrolls when the window is smaller than the box. Limits 320–3840 × 240–2400 whole
  pixels (`sizeError`; an import outside them opens Automatic with an issue). Rows never shrink below 16px — a tall stack in a short box overflows. Not part of undo / redo. A loaded size that is not a preset gets its own option in the select.
- **Canvas** (`#board-scroll`): 12 columns; row height `calc(var(--ctl-h) * 2)`, gap `var(--s2)`; widgets are absolutely
  positioned from `board-layout.js` (`layoutBoard(widgets, panelWidth, { rowH, gap })` → pixel rects; `board.js` reads the row
  height and gap from the tokens). The canvas grows downward (at most 96 rows) and scrolls **inside its panel** — the page never
  scrolls (golden rule 8). Column width follows the canvas width; a `ResizeObserver` on the grid re-lays out.
- **Narrow canvas:** below `STACK_BELOW` = 720px the grid is unusable, so widgets **stack full width in reading order** (by row,
  then column), each keeping its row count; the DOM order is the same reading order. At viewport width ≤ 760px the side panel
  moves above the canvas as a short scrolling list. The shell keeps its sidebar at every width, so a phone user collapses it first.
- An empty dashboard shows "Empty dashboard" with an icon — the field list beside it is the way to add widgets

## Adding and removing

- **Add** (worksheet) and **Add text** place the widget with `placeNew` (the first free spot scanning rows top to bottom; 6 × 4,
  text 12 × 2) and call `setWidgets` → `dashboard:changed`, which the workbook autosave already listens to. When nothing fits
  (12 widgets, or no free row under the 96-row limit) a danger toast says so ("A dashboard holds at most 12 widgets." / "The
  dashboard is full — …") and nothing is added. A worksheet may be added more than once. The new widget scrolls into view.
- **Add image** takes a PNG, JPEG, GIF or WebP file (`image-model.js`: `validateImageFile`, `isImageSrc`) — at most 256 KB, at most 4 images per
  dashboard and 2 MB of pictures in the whole workbook (also enforced on import, which drops what no longer fits); anything else (SVG, another type, empty, too big, a fifth image) toasts the reason and adds nothing. The picture is read
  as a data URL and **saved inside the workbook** (autosave and export), so it is self-contained: there is no upload to the server and no
  remote-URL image (a link would fetch from a third party each time the board opens and break offline — [D71](../reference/decisions-dashboards.md#d71--dashboard-images-are-workbook-data-urls-not-links)). **Add spacer** adds a blank 2 × 1 block.
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
| **Worksheet** | the worksheet's name; **Edit** (switches to that worksheet's tab) and **Remove** | a select-only worksheet view (`interactive: "select"`) of the worksheet's sheet |
| **Image** | the file name as alt text (`aria-label`); **Remove** (no Edit) | the picture, contained (`object-fit: contain`, never cropped or stretched); 6 × 4, 2–12 wide, 2–24 tall |
| **Button** | no title (the header shows only the icon buttons; the accessible name is the widget's `aria-label`, the label); **Edit** (inline form: **Label** ≤ 40, **Tooltip** ≤ 200, **Goes to** — a list of every other tab, "Nowhere yet" by default) and **Remove** | one primary button with the label (an arrow icon when linked) and the tooltip as its `title`; a click opens the target tab (`switchTab`); unlinked, or its target closed, it is `aria-disabled` (still keyboard-focusable, click ignored), its `aria-label` says "not linked to a tab" and its tooltip reads "Not linked to a tab. Use Edit to choose one."; 4 × 2, 2–12 wide, 1–24 tall |
| **Spacer** | "Spacer"; **Remove** (no Edit) | empty, hatched on screen so it can be found; invisible in print; 2 × 1, 2–12 wide, 1–24 tall |
| **Text** | the heading (empty reads "Text"); **Edit** (inline, below) and **Remove** | the body text, plain (`textContent`; line breaks kept and wrapped, no Markdown, no markup) |

Every widget is a focusable group (`tabindex="0"`, `role="group"`, `aria-roledescription="dashboard widget"`, `aria-label` its name,
`aria-describedby` a one-line key hint) with a visible focus ring, and has a corner grip at its bottom-right.

- A worksheet widget is `createWorksheetView(body, getContext, { interactive: "select", cross, onSelect })` ([worksheet.md](worksheet.md#query-lifecycle)):
  its own latest-wins gate, table pager and chart instance, so widgets never abort or overwrite each other. It reads the
  worksheet's **current** sheet on every run and applies the workbook's shared filters, parameters and calculations through the
  same `planCtx()` as the editor. **A mark click selects (see [Cross-widget filtering](#cross-widget-filtering)); no drill, Pages, status bar or editor panels; tooltips, table paging and the legend
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

## Cross-widget filtering

A click on a mark in one worksheet widget filters the **other** worksheet widgets to that value (`Board/board.js`, pure rules in
`Dashboard/dashboard-select.js`, [D64](../reference/decisions-dashboards.md#d64--one-transient-dashboard-selection-filters-the-other-widgets)).

- **One selection per dashboard**, `{ db, table, column, value, label, sourceWidgetId }`, taken from the clicked widget's primary
  dimension (the current level on a drill hierarchy — a widget never drills). Another click replaces it; the same mark in the same
  widget clears it. A NULL member or the "Other" group (the status line says why — never `= NULL`), date-grouped or date-part first keys, calculated primary dimensions (the worksheet's refusal), and **a field with a data type cast (it can't start a cross-filter)**,
  table and the types click-to-filter excludes ([worksheet-encodings.md](worksheet-encodings.md#click-to-filter)) select nothing.
  Legend clicks only highlight.
- **Targets** (every other worksheet widget, a second copy of the same worksheet included) add one bound `=` filter through the
  same `selectionFilter` the worksheet's click selection uses, replacing that widget's own click selection — only when the selected
  column's **table is already in the widget's query**; it never forces a join. A widget it can't reach sends no new query, keeps its
  data and says so in its notice ("orders.region: selected on another sheet, not applied here — its table isn't in this view."); a
  histogram or box plot (single-table endpoints) says it doesn't take it. Casts follow the plan as in the editor. Filter budget: 8 own
  + 4 shared + 5 drill + 1 page + 1 period + 1 selection = the server's 20.
- **The source** is never filtered. It fades the other marks (bar, stacked, pie, donut; the other types have no per-mark style) and
  keeps **every** mark of the selected value (two row dimensions give several) at full strength, and shows an outline and a header badge "Selected: <label>" (text and icon, so the fade is never the only cue).
- **The chip** in the bar reads "Filtering by orders.region = EU" with a labelled clear button (focus returns to the source widget);
  the polite status line announces set and clear. The value is data: always `textContent`.
- **Transient:** in memory only, never in the workbook or autosave. It ends when the dashboard stops being shown (tab switch,
  workbook open, reload), when its source widget is removed or its worksheet closed, and when the source's primary dimension is no
  longer the selected column. The worksheet tab never applies it.
- **Each widget runs on its own latest-wins gate.** `view.sync()` re-runs a widget only if the selection changed what it shows
  (`crossSignature`); clearing is a result-cache hit. A failing target shows its own error; the others still filter.
- Marks stay pointer-only (no keyboard mark picking); the chip's clear button is keyboard reachable.

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
  the screen layout and chart sizes. The arrangement on screen (side by side) is not kept on paper. A **fixed-size** dashboard instead
  prints its box with the on-screen arrangement kept, absolutely positioned and scaled down proportionally to the 1000px page width (never up).
- Image and CSV export, and bookmarks, stay per worksheet (reach them with **Edit**); the bookmark action is hidden on a dashboard.

## Tests

`tests/js/dashboard-select.test.mjs`, `selection-dim.test.mjs`, the cross-filter cases of `sheet-plan`, `worksheet-view` and `worksheet-render`; `tests/live/crossfilter-ui.mjs` (real clicks on mocked data: the bound filter and the queries sent, the source's fade and badge, the chip and its keyboard clear, an unreachable widget's note, replace / clear, a failing target, latest-wins, not saved, cleared by tab switch / source removal / dimension change / reload, a second copy, light and dark screenshots).

`tests/js/nav-model.test.mjs` (the button's edit rules, targets, import cleaning, saved form); `tests/live/nav-ui.mjs` (Add button, the inline form and its messages, a click opens a worksheet and a dashboard, autosave holds the target by tab index, reload restores, a closed target unlinks it); `tests/js/image-model.test.mjs` and the image / spacer cases of `board-model.test.mjs`; `tests/live/image-spacer-ui.mjs` (real file input: a PNG is decoded and drawn with its alt text, SVG / non-image / oversize files and a fifth image refused, spacer, autosave holds a data URL, reload restores, spacer hidden under print media, undo; light and dark screenshots).

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
