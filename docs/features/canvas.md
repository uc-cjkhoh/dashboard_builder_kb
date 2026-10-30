# Canvas & entity cards

The **Data Model** view: the drop target where tables become entity cards. Built on the native HTML5
Drag and Drop API — no library ([D4](../reference/decisions.md#d4--vanilla-js--hand-written-css-no-spa-framework)).
Code: `Features/Canvas/` (`_Canvas.cshtml`, `canvas.js`, `empty-state.js`, `canvas.css`). Relationship drawing on top of
the cards is [relationships.md](relationships.md).

## Dragging a table onto the canvas

- A sidebar chip's `dragstart` sets `application/x-ch-table` = `{db, table}` with
  `effectAllowed = 'copy'` ([schema-browser.md](schema-browser.md#table-list)). The **custom MIME type**
  means the canvas accepts only our chips, never arbitrary text or files.
- The canvas handles `dragover` (`preventDefault()`, `dropEffect = 'copy'`) and `drop`.
- A drop whose payload isn't `{db, table}` strings is ignored. A table **already on the canvas** is not
  added twice: the existing card is scrolled into view and focused (`tabindex="-1"`) and a toast says so.
- The `table:add` event (the chip's `＋` fallback) takes the same path. A dropped table always lands in
  the shared model — `table:add` switches to the Data Model tab first ([tabs.md](tabs.md)).
- A `＋`-added card goes in the **first free grid slot** (300 × 300 cells from the 16px view gutter,
  24px gap, as many columns as fit the visible canvas), so it never covers another card's title. A dropped card lands at the drop point.

## Creating an entity

On drop:

1. Read `{db, table}` and create an `Entity` at the drop point (id `db.table#n`) —
   [data-model.md](../reference/data-model.md#entity).
2. Fetch columns: `GET …/columns` (`DESCRIBE`, each column tagged with a display category).
3. Render the card with a **loading** status (amber) until columns arrive; a failed fetch shows a
   **failed** status (red) with **Retry**, never a bare error.
4. Hide the empty state (`.canvas__empty`) once the canvas has ≥1 entity — via `hidden`.

## Union and unpivot cards

A union or unpivot added from the sidebar dialogs ([query-sources.md](query-sources.md)) arrives as a `source:add` event and becomes a card in the first
free slot (the Data Model is shown first). Its `table` is the source's automatic name and its columns load from `POST /api/source/columns`. It looks
like a table card without the key checkboxes, key glyphs and profile buttons (a source takes no relationship), with one note line under the head
saying how its columns are matched; column names and the note start where the title text does. Remove and collapse work as on any card.

## Empty state

With no entities the canvas shows **one sentence and one button**, chosen by `emptyState()` in
`empty-state.js` (pure) and the button focuses the control for that step (expanding a collapsed sidebar
first — `expandSidebar()`, [layout.md](../design/layout.md#sidebar)):

| State | Sentence | Button → focuses |
|---|---|---|
| not connected | "Connect to a ClickHouse server to begin." | Connect → `#conn-host` |
| no database chosen | "Choose a database in the sidebar." | Choose a database → `#db-select` |
| database chosen | "Drag a table here from the sidebar to start your data model." | Find a table → `#table-search` |

## Card anatomy

- **Head** (`.entity__head`): the table name (600) with the database muted before it, a collapse caret,
  a remove icon. The card width follows the `db.table` text, from `--entity-min` (300px) to `--entity-max`
  (480px) on `#model-view` (`card-width.js`, pure); beyond the maximum the name ellipsises (full name in its
  `title`). Link anchors read the measured card box, so any width stays correct.
- **Column rows** (`.col-row`): a **type icon** (number / text / date / bool), name, a **type badge**
  (`.col-row__type`, from the type category), and a **join-key checkbox** (`.col-row__key`); ticked key
  columns show the key icon.
- Flat solid card: 1px stroke, `--elev-2` (`--elev-16` while dragging).
- **No rows on the card.** Cards are uniform height with an internally-scrolling column list; a table's rows are
  previewed from its chip in the schema browser ([schema-browser.md](schema-browser.md#row-preview)).
- The caret toggles `.entity--collapsed`, leaving only the title bar.

## Moving & removing

- Cards move by dragging the **head** with pointer events (a separate gesture from chip DnD); the
  entity's `x, y` update and `entity:moved` fires so links re-route.
- Removing a card removes its relationships, with a confirm dialog when any exist. If a half-drawn link
  was waiting on that card, it is cancelled (no dangling "undefined" toast).

## Join keys

The project statement requires that **every dragged-in table selects one or more columns** for
relationships. Ticking a join-key checkbox adds the column to `entity.joinKeys` (and highlights the
row) and fires `joinkey:changed`. An entity with no join key cannot be a relationship endpoint; a
checked key shows the connector handle used to draw links.
