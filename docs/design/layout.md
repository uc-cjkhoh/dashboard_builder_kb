# Layout rules

How the one page is laid out and what scrolls where. Regions and their behaviour are in
[features/](../features/worksheet.md); tokens in [tokens.md](tokens.md).

## The fixed shell

- `html, body { height: 100%; overflow: hidden }` — **the page never scrolls**
  ([golden rule 8](../conventions/golden-rules.md#8-keep-the-shell-fixed-scroll-inside-panels)).
- The shell is a full-screen grid: **glass sidebar** (`var(--sidebar-w)`) + **content area**, both over
  the body's fixed `--wash` background so the glass has something to blur. Chrome is glass; data
  surfaces (entity cards, chart area, crosstab, field list) are solid `--surface`.
- Scrolling happens **inside regions** — the sidebar's table list, each entity card's column list, the
  worksheet field pane and chart area. Scrollbars are thin and themed (muted ink thumb, accent on hover).

## Alignment grid

Related items share one edge, measured on what the eye sees (glyphs and text), not on hit boxes.

- **One 16px gutter (`--s4`) everywhere:** sidebar brand row and sections, `.canvas__bar`, `.view`
  padding, the worksheet field pane (`--ws-fields-w`, default 236px; `--s2 --s4` padding), `.ws-shelves` and the
  `.ws-chart-card` margin. So the tabs' left edge = first entity card = field-pane rows, and the
  appearance toggle = shelves = chart card on the right. `+`-placed entity cards start on the gutter
  ([canvas.md](../features/canvas.md#dragging-a-table-onto-the-canvas)).
- **Full-width lists align with their siblings:** `.table-list` keeps 2px shadow room with a matching
  `-4px` inline margin (equal to its padding), so table chips share the search box's edges. A chip is a flat 32px row (no border or shadow; an ink wash on hover / focus) whose table icon sits on the 8px left gutter; the hover grip overlays the icon, and the preview and `+` buttons overlay the row's right end on hover / focus instead of reserving space.
- **Entity cards** are measured on ink, not boxes (checked on the Data Source with the glyph's drawn bounds):
  - **One 16px gutter (`--s4`) on both sides**, so the space left of the content equals the space right of it: the head's title, the column names and a source card's note start on it; the type text, the head's ✕ ink and the pinned strip's type text end on it. A union / unpivot card uses the same lanes.
  - Right end of the head: the caret sits just left of the ✕ (the title takes the left gutter); the ✕ is pulled out by its 12px slack (`margin-right: -(--s2 + --s1)`: the glyph is a 16px box in a 32px button, strokes 4px inside) so its ink ends on the gutter.
  - The scrolling list reserves its 10px scrollbar (`scrollbar-gutter: stable`) and its rows give up that much right padding, so the type text ends on the same line whether or not the list overflows.
  - Vertical: caret, title, name and type text all share one optical centre (the cap-height midpoint of the 14px text) within 0.5px; the first and last row sit 4px inside the list's top and bottom edges. A failed card's status line uses the same 16px gutter.
- **Nothing touches:** menu lists (`.menu__list`, incl. the two-column chart picker) have a 4px gap between items; stacked `<details>` field rows are spaced 4px apart (`.ws-group > :not(summary) + *`). Single-choice `<select>`s show a chevron on the 16px gutter instead of the UA arrow (pill selects keep the native one).
- **Ghost icon buttons at a row's end overhang by their 8px glyph slack** (`margin-inline: -8px`), so
  the glyph meets the edge: `#sidebar-toggle`, the appearance toggle (`.scheme`), the view bar's chart picker and last
  icon button, the tool-panel ✕, and both `.entity__head` buttons (the caret and ✕ in the head's right end). Reset the overhang wherever the button is centred (collapsed rail).
- **Checkboxes carry no UA margin** (`.form-check input`: 14px, `margin: 0`); a
  sub-option (`.form-check--sub`, `.form-warn`) indents by checkbox + gap, i.e. to its parent's label text.
  `.entity__title` is padded so it starts at the column-name x.
- **Buttons centre their label** (`.btn { justify-content: center }`), including stretched ones.

## Sidebar

- **Resizable:** a right-edge handle (`.sidebar__resizer`, `Shell/sidebar.js`) drags `--sidebar-w`
  between a minimum and **30% of the viewport**.
- **Collapsible:** the toggle at the right of the brand row (`#sidebar-toggle`, `sidebar` icon) collapses the
  sidebar to a **rail `--topbar-h` wide** holding only that button (`.app.is-sidebar-collapsed`); the
  Connection/Schema body (`#sidebar-body`) and the resizer get `hidden`. `aria-expanded` and the label
  ("Collapse sidebar" / "Expand sidebar") follow the state. The chosen width survives a collapse, and the
  state is remembered in this browser (`localStorage` `dashboardbuilder.sidebar.collapsed`, read/write
  wrapped in `try`). Anything that focuses a sidebar control first calls `expandSidebar()`
  (the canvas empty-state button does).
- **Data Source only:** the sidebar body (`#sidebar-body`: connection, database, tables) belongs to the Data Source tab. `Shell/sidebar.js` sets `.app[data-view="model"|"sheet"]` from
  `view:changed`; on any worksheet or dashboard tab the body, its resizer, the brand name and the toggle are `display: none` and the column shrinks to a `--topbar-h` rail
  holding the brand mark, so the worksheet gets the room. The user's own collapse choice is untouched and returns with the Data Source tab.
- The brand name is one line (ellipsis), so the toggle never makes the brand row taller
  than `--topbar-h`.
- Glass rail in the active theme (light or dark). Section titles are sentence case, `--fs-body` 600.
- Contents: **Connection** (form or one-row summary — [connection.md](../features/connection.md)), the
  **Database** picker, then **Tables** with a search box ([schema-browser.md](../features/schema-browser.md)).
- The empty Data Source shows one centred sentence + one button that focuses the control for the next
  step ([canvas.md](../features/canvas.md#empty-state)).

The sidebar has **no section titles and no dividers** below the brand row (the Connection / Database / Tables headings are screen-reader-only): spacing groups the connected summary and the database picker, then the search box and table list. The connected summary is a flat row (status dot on the gutter, host, edit and disconnect ghost buttons). **Union** and **Unpivot** are pinned under the scrolling list with one hairline above them.

## Tab bar

A glass bar across the top of the content area (`.canvas__bar`): frosted-pill tabs (the active one with an accent
fill, edge and underline), then — at the right — the quiet autosave text, the **Workbook** overflow menu
([tabs.md](../features/tabs.md), [workbook.md](../features/workbook.md)) and, right-most, the **appearance
toggle** (`#scheme-btn`, `Shell/scheme-toggle.js`): an icon button whose glyph shows the current choice
(monitor / sun / moon; label "Appearance: System") opening a System / Light / Dark radio menu
([tokens.md § Light and dark](tokens.md#light-and-dark)). Its contents are vertically centred and it
shares `--topbar-h` with the sidebar brand block, so the two bottom borders line up across the shell; if the
tabs wrap, the bar grows taller than the brand.

## Entity cards

A head on `--surface-2` (table name alone in 600 weight) over an
internally-scrolling column list up to 240px tall: solid card lifted off the wash: a visible `--line-2` stroke, the two-layer `--elev-card` shadow (`--elev-card-hover` on hover) and a 1px `--card-rim` highlight along the head's top edge; the column type is plain muted text.
The Data Source ground is a 24px dot grid; cards snap to 8px and are placed on a 312px slot with a 96px gutter, which holds a link's elbow and badge
([canvas.md](../features/canvas.md#canvas-ground)). The gutter is canvas placement, not component spacing, so it sits outside the 4 / 8 / 16 / 24 steps. No rows on the card: a table's rows
open in a dialog from its schema-browser chip. A caret in the head collapses the card to its title bar; a key column's name turns accent.

## Worksheet — data header and chart card

Data controls sit in the glass header; view controls sit on the chart card they act on
([features/worksheet.md](../features/worksheet.md#layout)):

1. **Data header** (`.ws-shelves`, glass) — **Columns**, **Rows** and **Marks** lanes, each a fixed
   label column + zone (`88px 1fr`, wide enough for "COLUMNS") so every lane starts at the same x. Pills are 24px, so a filled lane
   stays as tall as an empty one. The Marks slots sit in the field pane
   ([Marks slots](../features/worksheet-encodings.md#marks-slots)); one editor panel (`.ws-toolpanel`) opens under the lanes at a time.
2. **Chart card** (`.ws-chart-card`, solid) — a head (`.ws-chart-head`) with the **view bar**
   (`.ws-viewbar`): the field-pane toggle, the chart-type picker and undo / redo on the left; the sort picker and a tight icon group
   (**Format** · **Analytics** · **Export** · **Refresh** · **⋯ sheet actions** · **Full screen**, 4px apart) on the right. Then the Format card when open, the
   result notice, and the chart pane. The card has no margin or radius and isn't overflow-clipped, so its menus can extend past it.

**Pickers** (`.ws-pick`) are ghost buttons whose label *is* the current value — no field captions:
chart type shows its icon + name (`▮ Bar ⌄`) and opens a two-column grid of every type; sort shows
direction + field (`↑ customers.name ⌄`) and opens "Sort by" (fields) + Ascending/Descending. Choices are
`menuitemradio` items, the chosen one bold and ticked. New view controls extend the view bar or the
Format card; new data channels become Marks tools. Every control is `--ctl-h` tall.

**Resizable field pane:** a handle on its right edge (`#ws-fields-resizer`, the shared `.resizer` look)
sets `.worksheet`'s `--ws-fields-w` (default 236px) between 180px and 40% of the worksheet — drag, or
`←`/`→` in 16px steps; remembered in this browser (`dashboardbuilder.fields.width`).

## Dashboard board

The dashboard tab (`.view--board`, padding 0, no scroll of its own) is a two-column grid: a 240px side panel (the worksheet's
field-pane slot) and the main column — a bar (name, widget count, the edit status line, Undo / Redo, Full screen, Print; the status line reserves two lines so the canvas never shifts) over `#board-scroll`, which scrolls inside
itself while the page stays fixed. The canvas is 12 columns with rows of `calc(var(--ctl-h) * 2)` and `var(--s2)` gaps; widgets are
absolutely positioned from the pure `board-layout.js`. Below 720px of canvas width widgets stack full width in reading order; at
viewport ≤ 760px the panel moves above the canvas (max-height 9rem, scrolling). A widget is a surface card (`--r`, `--elev-2`) with a
`--surface-2` header (grab cursor; the page's `:focus-visible` ring on a focused widget), a 16px corner grip, and while dragging a dashed ghost (`--ink-2` border; `--danger-solid` border, `--danger-bg` label with an icon and text when refused). Behaviour: [dashboards.md](../features/dashboards.md).

## Phone layout (≤ 640px)

The shell keeps its fixed frame; the sidebar starts on its rail (not remembered — a wide screen keeps the
user's choice) and opens over the content. The worksheet becomes one column: the data header (a **Fields**
button, then Columns / Rows / Marks with 84px labels, tools wrapping), then the chart card at ≥ 380px tall;
`.ws-main` scrolls inside itself. The field pane opens as an overlay from **Fields** (`.is-fields-open`)
and closes on a tap outside it or `Esc`. The view bar wraps: chart type, then sort and the icon group.
These are responsive CSS rules (`dashboard.css`), not visibility toggles — `hidden` stays the only
show/hide switch for state.

## Full screen & print

- **Full screen** (view bar, last icon): the chart card alone, edge to edge, through the Fullscreen API
  (a fixed overlay with an `Esc` handler where the API is refused); `Esc` or the button leaves; switching
  views leaves it.
- **Print / PDF** (Export menu → **Print / PDF…**, or the browser's print): landscape, only the active
  chart card, under a print header — the worksheet name, the Date range and applied filters, the notice
  line and the print time (`.ws-print-head`, added on `beforeprint`, removed on `afterprint`). The chart is
  drawn at 1000 × 560 for the page (`sizeChart`); a crosstab repeats its header on each page. Black on
  white (`--print-paper` / `--print-ink`) whatever the scheme.

## The `hidden` attribute

`[hidden] { display: none !important }` — interactive regions carry an author `display` (flex/grid)
that would otherwise beat the UA `[hidden]` rule. The `!important` makes the `hidden` attribute the
single show/hide switch app-wide: empty states, inline errors, the dropzone hint, the connect-first
gate, the cert warning. **Toggle via `hidden`, never `style.display`**
([golden rule 6](../conventions/golden-rules.md#6-toggle-visibility-with-the-hidden-attribute-not-styledisplay)).

## Dialogs

Native `<dialog>` for modals (focus trap, `Esc` closes): a solid `--surface` panel with `--elev-28` over a plain `--scrim` (no blur). A styled confirm
`<dialog>` replaces `window.confirm` (removing an entity that has relationships, closing a non-empty
dashboard).

`listDialog(title, items)` (`Core/ui.js`) shows a titled list with one OK button — used for workbook
import / restore issue reports.

## Menus

`Core/menu.js` `wireMenu(button, list)` turns a button plus a `[role=menu]` solid list (`.menu`,
`.menu__list`, `.menu__item`) into a keyboard-operable popover: click toggles it, arrow keys move focus,
`Esc` / outside click / focus leaving / choosing an item close it, and opening one menu closes the
others. Visibility is the `hidden` attribute.

The **context popup** (`openContextMenu` / `wireContextMenu`) is the same list with no button: it opens at the pointer on right-click, or under the element on the
ContextMenu key, `Shift+F10` or `Enter`; it sits on `<body>` (`.ctx-menu`, fixed, kept inside the viewport), holds items, radio / tick rows and custom rows (a filter's value editor),
and `Esc`, `Tab`, an outside click, scroll or resize close it (`Esc` returns focus to the element).
