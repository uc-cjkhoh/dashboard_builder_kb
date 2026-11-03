---
components: [src/DashboardBuilder/Features/Board/board-layout.js, src/DashboardBuilder/Features/Core/menu.js, src/DashboardBuilder/Features/Core/ui.js, src/DashboardBuilder/Features/Dashboard/dashboards.js, src/DashboardBuilder/Features/Shell/perf-panel.js, src/DashboardBuilder/Features/Shell/scheme-toggle.js, src/DashboardBuilder/Features/Shell/sidebar.js]
---
# Layout rules

How the one page is laid out, what scrolls where, and how elements align. Read it before changing
any region's size, spacing or position. Regions and their behaviour are in
[features/](../../concepts/worksheet/worksheet.md); tokens in [tokens.md](tokens.md).

## The fixed shell

- `html, body { height: 100%; overflow: hidden }` — **the page never scrolls**
  ([golden rule 8](../../development/coding-standards.md#8-keep-the-shell-fixed-scroll-inside-panels)).
- The shell is a full-screen grid: **glass sidebar** (`var(--sidebar-w)`) + **content area**. Both sit
  over the body's fixed `--wash` background, so the glass has something to blur. Chrome is glass; data
  surfaces (entity cards, chart area, crosstab, field list) are solid `--surface`.
- Scrolling happens **inside regions**: the sidebar's table list, each entity card's column list, the
  worksheet field pane and the chart area. Scrollbars are thin and themed (muted ink thumb, accent on
  hover).

## Alignment grid

Related items share one edge, measured on what the eye sees (glyphs and text), not on hit boxes.

- **One 16px gutter (`--s4`) everywhere.** It applies to the sidebar brand row and sections,
  `.canvas__bar`, `.view` padding, the worksheet field pane (`--ws-fields-w`, default 236px; `--s2 --s4`
  padding), `.ws-shelves` and the `.ws-chart-card` margin.
  - On the left, the tabs' edge, the first entity card and the field-pane rows line up.
  - On the right, the appearance toggle, the shelves and the chart card line up.
  - `+`-placed entity cards start on the gutter
    ([canvas.md](../../concepts/data-source/canvas.md#dragging-a-table-onto-the-canvas)).
- **Full-width lists align with their siblings.** `.table-list` keeps 2px shadow room with a matching
  `-4px` inline margin (equal to its padding), so table chips share the search box's edges.
  - A chip is a flat 32px row: no border or shadow, and an ink wash on hover / focus.
  - Its table icon sits on the 8px left gutter. The hover grip overlays the icon.
  - The preview and `+` buttons overlay the row's right end on hover / focus instead of reserving space.
- **Entity cards** are measured on ink, not boxes (checked on the Data Source with the glyph's drawn
  bounds):
  - **One 16px gutter (`--s4`) on both sides**, so the space left of the content equals the space right
    of it. The head's title, the column names and a source card's note start on it. The type text, the
    head's ✕ ink and the pinned strip's type text end on it. A union / unpivot card uses the same lanes.
  - Right end of the head: the caret sits just left of the ✕, and the title takes the left gutter. The ✕
    is pulled out by its 12px slack (`margin-right: -(--s2 + --s1)`) so its ink ends on the gutter. The
    glyph is a 16px box in a 32px button, with strokes 4px inside.
  - The scrolling list reserves its 10px scrollbar (`scrollbar-gutter: stable`) and its rows give up that
    much right padding. The type text therefore ends on the same line whether or not the list overflows.
  - Vertical: caret, title, name and type text all share one optical centre (the cap-height midpoint of
    the 14px text) within 0.5px. The first and last rows sit 4px inside the list's top and bottom edges.
    A failed card's status line uses the same 16px gutter.
- **Nothing touches.**
  - Menu lists (`.menu__list`, including the two-column chart picker) have a 4px gap between items.
  - Stacked `<details>` field rows are spaced 4px apart (`.ws-group > :not(summary) + *`).
  - Single-choice `<select>`s show a chevron on the 16px gutter instead of the UA arrow; pill selects
    keep the native one.
- **Ghost icon buttons at a row's end overhang by their 8px glyph slack** (`margin-inline: -8px`), so
  the glyph meets the edge. This applies to `#sidebar-toggle`, the appearance toggle (`.scheme`), the
  view bar's chart picker and last icon button, the tool-panel ✕, and both `.entity__head` buttons (the
  caret and ✕ in the head's right end). Reset the overhang wherever the button is centred (collapsed rail).
- **Checkboxes carry no UA margin** (`.form-check input`: 14px, `margin: 0`). A sub-option
  (`.form-check--sub`, `.form-warn`) indents by checkbox + gap, i.e. to its parent's label text.
  `.entity__title` is padded so it starts at the column-name x.
- **Buttons centre their label** (`.btn { justify-content: center }`), including stretched ones.

## Sidebar

- **Resizable:** a right-edge handle (`.sidebar__resizer`, `Shell/sidebar.js`) drags `--sidebar-w`
  between a minimum and **30% of the viewport**.
- **Collapsible:** the toggle at the right of the brand row (`#sidebar-toggle`, `sidebar` icon) collapses
  the sidebar to a **rail `--topbar-h` wide** holding only that button (`.app.is-sidebar-collapsed`).
  - The Connection/Schema body (`#sidebar-body`) and the resizer get `hidden`.
  - `aria-expanded` and the label ("Collapse sidebar" / "Expand sidebar") follow the state.
  - The chosen width survives a collapse. The state is remembered in this browser (`localStorage`
    `dashboardbuilder.sidebar.collapsed`, read/write wrapped in `try`).
  - Anything that focuses a sidebar control first calls `expandSidebar()`; the canvas empty-state
    button does.
- **The body follows the tab.** `Shell/sidebar.js` sets `.app[data-view="model"|"sheet"|"board"]` from
  `view:changed`.
  - **Data Source:** the full sidebar, with connection, database and tables.
  - **Worksheet and dashboard:** the sidebar shrinks to a `--topbar-h` rail that holds the brand mark.
    The brand name, toggle, resizer and the connection / database / tables are `display: none`.
  - On a **worksheet** the rail also carries the tool icons in one column, 1 × N (`#ws-tools`,
    `.sidebar__tool`, 40px, filled by `dashboards.js`). They use the frosted control tier: `--ctl-edge`
    ≥ 3:1 border, full-ink icon, accent on hover. The tools are **Calculated fields** (`calc` icon) and
    **Hierarchies** (`drill` icon). Each has its name as `aria-label` / tooltip and opens a dialog.
  - A dashboard's rail has the mark only.
  - The user's own collapse choice is untouched and returns with the Data Source tab.
- The brand name is one line (ellipsis), so the toggle never makes the brand row taller
  than `--topbar-h`.
- Glass rail in the active theme (light or dark). Its section headings (screen-reader-only, below) are sentence case.
- Contents: **Connection** (form or one-row summary; see [connection.md](../../concepts/data-source/connection.md)), the
  **Database** picker, then **Tables** with a search box ([schema-browser.md](../../concepts/data-source/schema-browser.md)).
- The empty Data Source shows one centred sentence + one button that focuses the control for the next
  step ([canvas.md](../../concepts/data-source/canvas.md#empty-state)).

The sidebar has **no section titles and no dividers** below the brand row; the Connection / Database /
Tables headings are screen-reader-only. Spacing groups the connected summary and the database picker,
then the search box and table list. The connected summary is a flat row: status dot on the gutter,
host, and edit and disconnect ghost buttons. **Union** and **Unpivot** are pinned under the scrolling
list with one hairline above them.

## Tab bar

A glass bar across the top of the content area (`.canvas__bar`). From left to right it holds:

1. Frosted-pill tabs; the active one has an accent fill and bold text.
2. The quiet autosave text.
3. The **Workbook** overflow menu ([tabs.md](../../concepts/workbook/tabs.md),
   [workbook.md](../../concepts/workbook/workbook.md)).
4. The **performance** gauge button (`#perf-btn`, `Shell/perf-panel.js`) opens the timings dialog
   ([frontend-modules.md](../../architecture/frontend-modules.md)); it sits flush against the next button, no overlap.
5. Right-most, the **appearance toggle** (`#scheme-btn`, `Shell/scheme-toggle.js`). It is an icon button
   whose glyph shows the current choice (monitor / sun / moon; label "Appearance: System"). It opens a
   System / Light / Dark radio menu ([tokens.md § Light and dark](tokens.md#light-and-dark)).

The bar's contents are vertically centred. It shares `--topbar-h` with the sidebar brand block, so the
two bottom borders line up across the shell. If the tabs wrap, the bar grows taller than the brand.

## Entity cards

- **Structure:** a head on `--surface-2` (table name alone in 600 weight) over an internally scrolling
  column list up to 240px tall. The column type is plain muted text.
- **Surface:** a solid card lifted off the wash, with a visible `--line-2` stroke, the two-layer
  `--elev-card` shadow (`--elev-card-hover` on hover) and a 1px `--card-rim` highlight along the head's
  top edge.
- **Placement:** the Data Source ground is a 24px dot grid. Cards snap to 8px and are placed on a 312px
  slot with a 96px gutter, which holds a link's elbow and badge
  ([canvas.md](../../concepts/data-source/canvas.md#canvas-ground)). The gutter is canvas placement, not
  component spacing, so it sits outside the 4 / 8 / 16 / 24 steps.
- **No data rows on the card.** A table's rows open in a dialog from its schema-browser chip.
- A caret in the head collapses the card to its title bar. A key column's name turns accent.

## Worksheet — data header and chart card

Data controls sit in the glass header; view controls sit on the chart card they act on
([worksheet.md](../../concepts/worksheet/worksheet.md#layout)):

1. **Data header** (`.ws-shelves`, glass): **Columns**, **Rows** and **Marks** lanes.
   - Each lane is a fixed label column + zone (`88px 1fr`, wide enough for "COLUMNS"), so every lane
     starts at the same x.
   - Pills are 24px, so a filled lane stays as tall as an empty one.
   - The Marks slots sit in the field pane
     ([Marks slots](../../concepts/worksheet/worksheet-marks.md#marks-slots)).
   - One Marks editor (`.ws-toolpanel`, in `.ws-toolfly`) is open at a time, floating beside the field pane — see [worksheet-marks.md](../../concepts/worksheet/worksheet-marks.md).
2. **Chart card** (`.ws-chart-card`, solid): a head (`.ws-chart-head`) with the **view bar**
   (`.ws-viewbar`), then the Format card when open, the result notice, and the chart pane.
   - View bar, left: the field-pane toggle, the chart-type picker and undo / redo.
   - View bar, right: the sort picker and a tight icon group (**Format** · **Analytics** · **Export** ·
     **Refresh** · **⋯ sheet actions** · **Full screen**, 4px apart).
   - The card has no margin or radius and isn't overflow-clipped, so its menus can extend past it.

**Pickers** (`.ws-pick`) are ghost buttons whose label *is* the current value, with no field captions.

- Chart type shows its icon + name (`▮ Bar ⌄`) and opens a two-column grid of every type.
- Sort shows direction + field (`↑ customers.name ⌄`) and opens "Sort by" (fields) + Ascending/Descending.
- Choices are `menuitemradio` items; the chosen one is bold and ticked.

New view controls extend the view bar or the Format card; new data channels become Marks tools. Every
control is `--ctl-h` tall.

**Resizable field pane:** a handle on its right edge (`#ws-fields-resizer`, the shared `.resizer` look)
sets `.worksheet`'s `--ws-fields-w` (default 236px) between 180px and 40% of the worksheet. Drag it, or
press `←`/`→` for 16px steps. The width is remembered in this browser (`dashboardbuilder.fields.width`).

## Dashboard board

The dashboard tab (`.view--board`, padding 0, no scroll of its own) is a two-column grid:

- **Side panel:** 240px, in the worksheet's field-pane slot.
- **Main column:** a bar over `#board-scroll`, which scrolls inside itself while the page stays fixed.
  The bar holds the name, widget count, the edit status line, Undo / Redo, Full screen and Print. The
  status line reserves two lines so the canvas never shifts.

**Canvas:** 12 columns with rows of `calc(var(--ctl-h) * 2)` and `var(--s2)` gaps. Widgets are absolutely
positioned from the pure `board-layout.js`.

**Widget:** a surface card (`--r`, `--elev-2`) with:

- a `--surface-2` header (grab cursor; the page's `:focus-visible` ring on a focused widget);
- a 16px corner grip;
- while dragging, a dashed ghost with an `--ink-2` border. When the drop is refused, the ghost shows a
  `--danger-solid` border and a `--danger-bg` label with an icon and text.

Behaviour: [dashboards.md](../../concepts/workbook/dashboards.md).

## Full screen & print

- **Full screen** (view bar, last icon): the chart card alone, edge to edge, through the Fullscreen API.
  Where the API is refused, a fixed overlay with an `Esc` handler stands in. `Esc` or the button leaves
  full screen, and so does switching views.
- **Print / PDF** (Export menu → **Print / PDF…**, or the browser's print): landscape, only the active
  chart card.
  - A print header (`.ws-print-head`, added on `beforeprint`, removed on `afterprint`) shows the
    worksheet name, the Date range and applied filters, the notice line and the print time.
  - The chart is drawn at 1000 × 560 for the page (`sizeChart`); a crosstab repeats its header on each page.
  - Output is black on white (`--print-paper` / `--print-ink`) whatever the scheme.

## The `hidden` attribute

`[hidden] { display: none !important }`. Interactive regions carry an author `display` (flex/grid)
that would otherwise beat the UA `[hidden]` rule. The `!important` makes the `hidden` attribute the
single show/hide switch app-wide: empty states, inline errors, the dropzone hint, the connect-first
gate, the cert warning. **Toggle via `hidden`, never `style.display`**
([golden rule 6](../../development/coding-standards.md#6-toggle-visibility-with-the-hidden-attribute-not-styledisplay)).

## Dialogs

Modals use native `<dialog>` (focus trap, `Esc` closes): a solid `--surface` panel with `--elev-28`
over a plain `--scrim` (no blur). A styled confirm `<dialog>` replaces `window.confirm`, for example when
removing an entity that has relationships or closing a non-empty dashboard.

`listDialog(title, items)` (`Core/ui.js`) shows a titled list with one OK button. It is used for
workbook import / restore issue reports.

## Menus

`Core/menu.js` `wireMenu(button, list)` turns a button plus a `[role=menu]` solid list (`.menu`,
`.menu__list`, `.menu__item`) into a keyboard-operable popover:

- click toggles it, and arrow keys move focus;
- `Esc`, an outside click, focus leaving or choosing an item closes it;
- opening one menu closes the others.

Visibility is the `hidden` attribute.

The **context popup** (`openContextMenu` / `wireContextMenu`) is the same list with no button.

- It opens at the pointer on right-click, or under the element on the ContextMenu key, `Shift+F10` or
  `Enter`.
- It sits on `<body>` (`.ctx-menu`, fixed, kept inside the viewport).
- It holds items, radio / tick rows and custom rows (such as a filter's value editor).
- `Esc`, `Tab`, an outside click, scroll or resize close it; `Esc` returns focus to the element.
