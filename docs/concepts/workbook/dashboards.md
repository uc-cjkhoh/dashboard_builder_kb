---
components: [src/DashboardBuilder/Features/Board/, src/DashboardBuilder/Features/Dashboard/, tests/js/, tests/live/]
---
# Dashboards — the board

A dashboard tab (`.tab--dashboard`) composes the workbook's worksheets, text blocks, images, navigation buttons and spacers on a 12-column snap grid.

- Tab kinds, store records and events: [tabs.md](tabs.md), [data-model.md](../../reference/data-model.md#tabs-and-dashboards).
- Saving: [workbook.md](workbook.md).
- Why separate tab kinds: [D61](../../decisions/decisions-dashboards.md#d61--worksheets-and-dashboards-are-separate-tab-kinds-workbook-format-v2).

**Code:** `Features/Board/`

- `board.js` — orchestration, undo / redo, full screen, print
- `board-widget.js` — one widget, inline text edit
- `board-panel.js` — the side panel
- `board-interact.js` — pointer, keyboard and panel-drop wiring
- `nav-edit.js` — the button widget's inline form
- `board.css`, `_Board.cshtml` (`#board-view`)
- Pure, node-tested modules:
  - `board-layout.js` — cell ↔ pixel geometry
  - `board-model.js` — widget rules and limits
  - `board-drag.js` — the pointer state machine
  - `board-keys.js`, `text-edit.js`, `image-model.js`, `nav-model.js`, `board-history.js`

## At a glance

- **What it is:** a 12-column grid of up to 12 widgets — worksheets, text, images, navigation buttons and spacers.
- **Editing:** add from the side panel (button or drag), then move and resize by mouse or keyboard. A refused move snaps back and says why; it is never silently moved elsewhere.
- **Worksheet widgets** show the worksheet's current sheet, read-only except for selecting marks. A mark click filters the other widgets (cross-widget filtering, never saved).
- **Only the active dashboard renders**, and widgets reuse the worksheet editor's result cache, so re-showing an unchanged board sends no query.
- **Undo / redo** covers layout edits for the session only. The layout itself is autosaved with the workbook.
- **Desktop only:** the board has no phone or tablet layout; print lays out a single column (fixed-size boards keep their arrangement).

## Layout

### Side panel and bar

- **Side panel** (left, 240px; the worksheet's field-pane slot) lists:
  - the workbook's worksheets, each with an **Add** button (`aria-label` "Add the worksheet “Sales” to the dashboard");
  - then **Add text**, **Add image** (a file picker), **Add button** and **Add spacer**.

  The list redraws only when a worksheet is added, closed or renamed, so a button keeps focus when a widget is added.
- **Bar** above the canvas holds, in order: the dashboard's name, "n of 12 widgets", the **status line** (below),
  the **Size** select, **Undo** / **Redo**, **Full screen** and **Print**.

### Size

Each dashboard has its own size (`Board/board-size.js`).

- **Automatic** (default): the canvas fills its panel.
- **Fixed** preset: 800 × 600, 1024 × 768, 1280 × 720, 1366 × 768 or 1920 × 1080.
  - A fixed board is exactly that box.
  - Columns span the width, and the rows in use (down to the lowest widget) stretch to share the height
    (`layoutBoard(…, { fixed })`, `fixedRowH`), so drag and resize snap to the drawn rows.
  - Rows never shrink below 16px, so a tall stack in a short box overflows.
  - The panel scrolls when the window is smaller than the box.
- **Range** (the "Range…" option): an Automatic board bounded by up to four optional pixel limits (**Min width**, **Max width**, **Min height**, **Max height**; an empty input is no limit), saved as `range` on the dashboard.
  - The board is the panel width clamped into the width limits, centred when narrower; a minimum above the panel makes the panel scroll.
  - Its height is the rows' height clamped into the height limits; past the maximum the board scrolls inside itself (stable scrollbar gutter; drag, resize and drops add the scroll offset).
  - A fixed size wins and drops the range (also on import, with an issue); print ignores the range (page width, stacked).
  - Inputs are grouped under visible "Width" and "Height" labels with "Min" / "Max". An invalid set (out of limits, minimum above maximum, no limit) is refused in place: only the offending inputs get `aria-invalid`, the status line says which limit, and nothing is clamped or saved.
- **Limits:** 320–3840 × 240–2400 whole pixels (`sizeError`, `rangeError`). An import outside them opens Automatic with an issue.
- A loaded size that is not a preset gets its own option in the select. Size and range are not part of undo / redo.

### Canvas

- **Grid** (`#board-scroll`): 12 columns, row height `calc(var(--ctl-h) * 2)`, gap `var(--s2)`.
- **Positioning:** widgets are absolutely positioned from `board-layout.js`
  (`layoutBoard(widgets, panelWidth, { rowH, gap })` → pixel rects). `board.js` reads the row height and gap from the tokens.
- **Scrolling:** the canvas grows downward (at most 96 rows) and scrolls **inside its panel**; the page never scrolls (golden rule 8).
- Column width follows the canvas width. A `ResizeObserver` on the grid re-lays out.
- An empty dashboard shows "Empty dashboard" with an icon. The field list beside it is the way to add widgets.

## Adding and removing

- **Add** (worksheet) and **Add text** place the widget with `placeNew`: the first free spot, scanning rows top to bottom.
  The default size is 6 × 4 (text 12 × 2).
  - They call `setWidgets` → `dashboard:changed`, which the workbook autosave already listens to.
  - A worksheet may be added more than once.
  - The new widget scrolls into view.
  - When nothing fits (12 widgets, or no free row under the 96-row limit), a danger toast says so and nothing is added:
    "A dashboard holds at most 12 widgets." / "The dashboard is full — …".
- **Add image** takes a PNG, JPEG, GIF or WebP file (`image-model.js`: `validateImageFile`, `isImageSrc`).
  - Limits: at most 256 KB each, at most 4 images per dashboard, and 2 MB of pictures in the whole workbook.
    Import enforces these too and drops what no longer fits.
  - Anything else (SVG, another type, empty, too big, a fifth image) toasts the reason and adds nothing.
  - The picture is read as a data URL and **saved inside the workbook** (autosave and export), so the workbook is self-contained.
    There is no upload to the server and no remote-URL image: a link would fetch from a third party each time the board opens and break offline
    ([D71](../../decisions/decisions-dashboards.md#d71--dashboard-images-are-workbook-data-urls-not-links)).
- **Add spacer** adds a blank 2 × 1 block.
- **Text widgets** start with the heading "Text" and no body. They are 12 × 2 by default and may be resized down to 1 row.
- **Dragging:** a worksheet row in the side panel is **draggable** (see Dropping from the panel). **Add** stays the keyboard path.
- **Announcements:** adding also announces "Added “name” to the dashboard." through the polite live region (`#toast-live`).
  A worksheet widget's loading state has a **Cancel** button labelled "Cancel loading <worksheet name>".
- **Remove** (header button, `aria-label` "Remove “name” from the dashboard") drops the widget and toasts "Removed “name”. Undo brings it back.".
  The removal is recorded like any other edit, so Undo restores it. Focus moves to the next widget's Remove button (else **Add text**). Siblings are not redrawn.
- **Closing a worksheet** removes its widgets from every dashboard ([tabs.md](tabs.md)).
  A widget whose worksheet is missing reads "This worksheet was closed."

## Widgets

Each widget is an `<article class="board-widget">` with a header (title, then icon buttons) over a body.

| Kind | Header | Body |
|---|---|---|
| **Worksheet** | the worksheet's name; **Edit** (switches to that worksheet's tab) and **Remove** | a select-only worksheet view (`interactive: "select"`) of the worksheet's sheet |
| **Image** | the file name as alt text (`aria-label`); **Remove** (no Edit) | the picture, contained (`object-fit: contain`, never cropped or stretched); 6 × 4, 2–12 wide, 2–24 tall |
| **Button** | no title (the header shows only the icon buttons; the accessible name is the widget's `aria-label`, the label); **Edit** and **Remove** | one primary button with the label; see [Button widget](#button-widget) below; 4 × 2, 2–12 wide, 1–24 tall |
| **Spacer** | "Spacer"; **Remove** (no Edit) | empty, hatched on screen so it can be found; invisible in print; 2 × 1, 2–12 wide, 1–24 tall |
| **Text** | the heading (empty reads "Text"); **Edit** (inline, below) and **Remove** | the body text, plain (`textContent`; line breaks kept and wrapped, no Markdown, no markup) |

**Focus and accessibility.** Every widget is a focusable group with a visible neutral focus wash and a corner grip at its bottom-right.
It has `tabindex="0"`, `role="group"`, `aria-roledescription="dashboard widget"`, `aria-label` set to its name,
and `aria-describedby` pointing at a one-line key hint.

### Button widget

- **Edit** opens an inline form:
  - **Label** ≤ 40;
  - **Tooltip** ≤ 200;
  - **Goes to** — a list of every other tab, "Nowhere yet" by default.
- **Linked:** the button shows the label with an arrow icon, and the tooltip as its `title`. A click opens the target tab (`switchTab`).
- **Unlinked, or its target closed:** the button is `aria-disabled` (still keyboard-focusable, click ignored).
  Its `aria-label` says "not linked to a tab", and its tooltip reads "Not linked to a tab. Use Edit to choose one."

### Worksheet widgets

- **What it shows.** A worksheet widget is `createWorksheetView(body, getContext, { interactive: "select", cross, onSelect })`
  ([worksheet-query.md](../worksheet/worksheet-query.md#query-lifecycle)).
  - It has its own latest-wins gate, table pager and chart instance, so widgets never abort or overwrite each other.
  - It reads the worksheet's **current** sheet on every run.
  - It applies the workbook's shared filters, parameters and calculations through the same `planCtx()` as the editor.
- **What you can do in it.** **A mark click selects** (see [Cross-widget filtering](#cross-widget-filtering)).
  There is no drill, Pages, status bar or editor panels. Tooltips, table paging and the legend highlight stay
  ([worksheet-encodings.md](../worksheet/worksheet-encodings.md)).
  The result notice (e.g. "more rows exist") shows under the header.
- **Failure and hint states render inside the widget**, in the worksheet's own words: a rejected query, "Drag fields onto Columns
  and Rows…", fields from unrelated tables, a calculation that can't be computed. A failing widget leaves its siblings drawn.
- **Queries and caching:**
  - Queries are scoped by worksheet id and go through the **editor's result cache** (`sharedResults` in `dashboards.js`, keyed by the exact request).
    So a widget draws what its worksheet tab just ran, and an unchanged sheet is served without a query.
  - A widget whose request failed is not cached and runs again when shown.
  - Up to 12 queries run in parallel; the browser queues past its per-origin limit.
  - **Known cost:** there is no in-flight de-duplication. Two widgets of one worksheet shown together (or a widget run while the same request is in flight)
    each send the query.

## Editing the layout

All geometry and verdicts are pure. `board-interact.js` turns events into points relative to the grid (so scrolling mid-drag needs no correction),
draws the **ghost** and commits. Every committed edit is **one undo step** and fires `dashboard:changed` (autosave).

- **Move and resize with the pointer.** Press the widget **header** (not its buttons) and drag to move; drag the **corner grip** to resize.
  - Pointer capture is on the header / grip. A press that travels under 4px is a click, not a drag.
  - The pointer delta snaps to the nearest whole cell (`snapMove`, `snapResize`).
    The dragged widget dims, and a dashed **ghost** covers the target cells.
  - **Refused drops:** when the target overlaps another widget, runs off the grid or breaks a size limit, the ghost turns refused
    (danger border + "Can't drop here" with an icon). A release then **snaps back**: nothing moves, and the status line says why
    ("Can't move: it would overlap “Sales”."). The widget is never silently moved elsewhere.
  - `pointercancel`, a lost capture, window blur and Esc end the drag with no ghost and no change.
- **Keyboard.** Focus a widget (Tab):
  - **arrows** move it one cell;
  - **Shift + arrows** resize from the bottom-right (Right / Down grow, Left / Up shrink).

  Each key press is a committed step; a refused one changes nothing. Keys act only while the widget itself (not a button or field inside it) has focus,
  and focus stays on the widget after a step.
- **Status line** (`#board-status`, a polite live region, visible in the bar).
  - Messages: "Moved to column 3, row 2", "Resized to 4 columns by 3 rows", "Text updated.", "Undid the last change.",
    or the refusal in the danger colour with a warning icon. It clears after 8 seconds.
  - The refusal wording comes from one place for the drag, the keys and the drop: `explainRefusal` in `board-model.js`.
    It checks whole cells, size limits (w 2–12; h 2–24 worksheet, 1–24 text), left / right / top edge and 96 rows, then "it would overlap “name”".
- **Dropping from the panel.** Drag a worksheet row (MIME type `application/x-dashboardbuilder-worksheet`, carrying the worksheet id) over the canvas.
  - The ghost shows a default-size (6 × 4) widget whose top-left is the cell under the pointer, slid left just far enough to stay inside the 12 columns.
  - The drop adds it there. Like Add, an added widget toasts "Added …".
  - A taken or too-low cell, or a 12th-plus widget, refuses with the status line and adds nothing.
  - Other drags are ignored.
- **Text edit.** **Edit** on a text widget replaces its body with a form.
  - Fields: a labelled **Heading** input (≤ 80) and **Text** textarea (≤ 2 000), with `maxLength` from `LIMITS` and a live "n / max" count.
  - **Save:** Enter in the heading, Ctrl+Enter, or the **Save** button. **Discard:** Esc or **Cancel**. Focus returns to **Edit** either way.
  - `validateTextEdit` (`text-edit.js`) trims and checks both fields. An invalid save stays open, with a message under the field
    (`role="alert"`, `aria-invalid`) and focus on it.
  - A save that changes nothing is not an undo step.
  - While the form is open, the widget grows over its neighbours (`.is-editing`), since a 2-row cell can't hold it.
  - If the text changes underneath (an undo), the form closes.
- **Undo / redo.**
  - **Controls:** buttons in the bar (disabled when there is nothing to do), and **Ctrl+Z**, **Ctrl+Shift+Z** / **Ctrl+Y** while a dashboard tab is active.
    Shortcuts never act while typing in an input, textarea, select or dialog, and never on a worksheet tab (the worksheet editor keeps its own shortcut).
  - **What is recorded:** `Dashboard/history.js` (the editor's snapshot stack, 50 deep), keyed by dashboard id, holds the **widget list** before each edit:
    add, remove, move, resize, text edit.
  - A restore drops worksheet widgets whose worksheet has been closed since (`restorable`).
  - **History is in memory.** A reload or a workbook open starts empty (the layout itself is autosaved), and closing a dashboard forgets its history.

## Cross-widget filtering

A click on a mark in one worksheet widget filters the **other** worksheet widgets to that value
(`Board/board.js`, pure rules in `Dashboard/dashboard-select.js`,
[D64](../../decisions/decisions-dashboards.md#d64--one-transient-dashboard-selection-filters-the-other-widgets)).

- **One selection per dashboard:** `{ db, table, column, value, label, sourceWidgetId }`.
  - It is taken from the clicked widget's primary dimension (the current level on a drill hierarchy — a widget never drills).
  - Another click replaces it; the same mark in the same widget clears it.
  - Legend clicks only highlight.
- **What selects nothing:**
  - a NULL member or the "Other" group (the status line says why — never `= NULL`);
  - date-grouped or date-part first keys;
  - calculated primary dimensions (the worksheet's refusal);
  - **a field with a data type cast (it can't start a cross-filter)**;
  - table, and the types click-to-filter excludes ([worksheet-encodings.md](../worksheet/worksheet-encodings.md#click-to-filter)).
- **Targets** are every other worksheet widget, including a second copy of the same worksheet.
  - Each adds one bound `=` filter through the same `selectionFilter` the worksheet's click selection uses, replacing that widget's own click selection.
  - This happens only when the selected column's **table is already in the widget's query**; it never forces a join.
  - A widget it can't reach sends no new query, keeps its data and says so in its notice
    ("orders.region: selected on another sheet, not applied here — its table isn't in this view.").
  - A histogram or box plot (single-table endpoints) says it doesn't take it.
  - Casts follow the plan as in the editor.
  - **Filter budget:** 8 own + 4 shared + 5 drill + 1 page + 1 period + 1 selection = the server's 20.
- **The source widget** is never filtered.
  - It fades the other marks (bar, stacked, pie, donut; the other types have no per-mark style).
  - It keeps **every** mark of the selected value at full strength (two row dimensions give several).
  - It shows an outline and a header badge "Selected: <label>" (text and icon, so the fade is never the only cue).
- **The chip** in the bar reads "Filtering by orders.region = EU", with a labelled clear button (focus returns to the source widget).
  The polite status line announces set and clear. The value is data: always `textContent`.
- **Transient:** in memory only, never in the workbook or autosave. It ends when:
  - the dashboard stops being shown (tab switch, workbook open, reload);
  - its source widget is removed or its worksheet closed;
  - the source's primary dimension is no longer the selected column.

  The worksheet tab never applies it.
- **Each widget runs on its own latest-wins gate.** `view.sync()` re-runs a widget only if the selection changed what it shows (`crossSignature`).
  Clearing is a result-cache hit. A failing target shows its own error; the others still filter.
- Marks stay pointer-only (no keyboard mark picking); the chip's clear button is keyboard reachable.

## Lifecycle

- **Only the active dashboard renders.** Leaving it (another tab, the Data Source) destroys every widget:
  queries aborted, chart instances and their resize observers released, DOM removed.
  - Showing it again rebuilds the widgets. A worksheet edited meanwhile draws its new sheet; an unedited one comes from the cache.
  - `worksheet:changed` for a widget's sheet while its dashboard is on screen re-runs that widget.
- **Layout changes** (add, remove, move, resize, a rename, `tabs:changed`) **reconcile by widget id**.
  Existing widgets keep their view, chart and focus; a move or resize re-lays out, and each chart re-fits with no query.
- **Theme changes:** `theme:changed` and `scheme:changed` re-run every live view — a cache hit, repainted in the new colours, no query.
  A widget that showed an **error** has nothing cached, so a theme flip queries it again.
- **Resize** re-lays out the grid, and each chart re-fits through its own observer (`chart.js`); no query.
- **After a reload**, a widget that drew a hint before its tables' columns arrived runs again once they do (`entity:loaded`).

## Full screen and print

- **Full screen** shows the bar and canvas (the whole board) full screen, using the Fullscreen API with a fallback to a fixed overlay.
  The button's text changes to "Exit full screen". Esc or the button exits.
- **Print** prints the canvas only. The side panel, bar buttons and widget buttons are hidden (`@media print` in `board.css`).
  - **Automatic size:** on `beforeprint` the board lays itself out **stacked at a fixed 1000px page width** (`layoutBoard(…, { stack: true })`),
    and the widgets print **in flow, one column** (`position: relative`, `break-inside: avoid`).
    This is because an absolutely positioned widget could be split or cropped across pages.
    The on-screen arrangement (side by side) is not kept on paper.
  - **Chart size:** each worksheet widget's chart is sized to its printed cell (`sizeChart(body, { width, height })`, from the cell box less header and padding).
    This overrides the worksheet print rule that fixes every chart canvas at 1000 × 560. `afterprint` restores the screen layout and chart sizes.
  - **Fixed size:** a **fixed-size** dashboard instead prints its box with the on-screen arrangement kept, absolutely positioned and
    scaled down proportionally to the 1000px page width (never up).
- Image and CSV export stay per worksheet (reach them with **Edit**).

## Tests

**Cross-widget filtering**

- `tests/js/dashboard-select.test.mjs`, `selection-dim.test.mjs`, and the cross-filter cases of `sheet-plan`, `worksheet-view` and `worksheet-render`.
- `tests/live/crossfilter-ui.mjs` — real clicks on mocked data: the bound filter and the queries sent, the source's fade and badge,
  the chip and its keyboard clear, an unreachable widget's note, replace / clear, a failing target, latest-wins, not saved,
  cleared by tab switch / source removal / dimension change / reload, a second copy, light and dark screenshots.

**Buttons, images and spacers**

- `tests/js/nav-model.test.mjs` — the button's edit rules, targets, import cleaning, saved form.
- `tests/live/nav-ui.mjs` — Add button, the inline form and its messages, a click opens a worksheet and a dashboard,
  autosave holds the target by tab index, reload restores, a closed target unlinks it.
- `tests/js/image-model.test.mjs` and the image / spacer cases of `board-model.test.mjs`.
- `tests/live/image-spacer-ui.mjs` — real file input: a PNG is decoded and drawn with its alt text, SVG / non-image / oversize files
  and a fifth image refused, spacer, autosave holds a data URL, reload restores, spacer hidden under print media, undo; light and dark screenshots.

**Layout and editing**

- `tests/js/board-layout.test.mjs` — geometry, the 96-row limit, print stacking.
- `board-model.test.mjs` — rules and limits.
- `board-drag.test.mjs` — pixel → cell snapping, ghost, click threshold, every refusal, cancel, panel drop plan.
- `board-keys.test.mjs` — every step and refusal message.
- `text-edit.test.mjs`, `board-history.test.mjs`.
- `tests/live/board-edit-ui.mjs` — real mouse events: move and resize with the ghost, overlapping / off-grid drops that snap back,
  keyboard and the live status, text edit / limits / Esc, undo and redo of every edit type by button and shortcut, panel drag,
  pointercancel / blur / Esc, reload keeps the layout but not the history;
  light and dark screenshots with the ghost, a refused ghost and the focus wash.

**Whole board**

- `tests/live/board-ui.mjs` — mocked API: three widget kinds draw with their own queries, a failing widget, Remove, Edit, disposal on
  tab switch, a worksheet edit, theme flip, resize re-fit without a query, full screen, reload from autosave, a shared filter and a parameter in a
  widget's query, a calculated field + cast + tooltip template + member colour in a widget, table paging inside a widget, the Cancel
  label and live-region announcement, and print layout checked under emulated print media with the chart-to-cell geometry;
  light, dark and print screenshots.

Not verified: the browser's real print dialog and PDF pages.
