# Canvas & entity cards

The **Data Source** view: the drop target where tables become entity cards. Built on the native HTML5
Drag and Drop API — no library ([D4](../reference/decisions.md#d4--vanilla-js--hand-written-css-no-spa-framework)).
Code: `Features/Canvas/` (`_Canvas.cshtml`, `canvas.js`, `empty-state.js`, `canvas.css`). Relationship drawing on top of
the cards is [relationships.md](relationships.md).

## Canvas ground

A 24px dot grid (`--line-2` dots, offset by the 16px gutter) on `.view--model`, `background-attachment: local` so it scrolls with the cards.
Cards snap to its 8px steps; the free-slot step (312 + 48 = 360) is a whole number of dot cells. While a table chip is dragged over, the ground takes a faint accent wash
and the dashed accent outline.

## Dragging a table onto the canvas

- A sidebar chip's `dragstart` sets `application/x-ch-table` = `{db, table}` with
  `effectAllowed = 'copy'` ([schema-browser.md](schema-browser.md#table-list)). The **custom MIME type**
  means the canvas accepts only our chips, never arbitrary text or files.
- The canvas handles `dragover` (`preventDefault()`, `dropEffect = 'copy'`) and `drop`.
- A drop whose payload isn't `{db, table}` strings is ignored. A table **already on the canvas** is not
  added twice: the existing card is scrolled into view and focused (`tabindex="-1"`) and a toast says so.
- The `table:add` event (the chip's `＋` fallback) takes the same path. A dropped table always lands in
  the shared model — `table:add` switches to the Data Source tab first ([tabs.md](tabs.md)).
- A `＋`-added card goes in the **first free grid slot** (312 × 312 cells from the 16px view gutter,
  a 96px gutter between cards — room for a link's elbow and badge — as many columns as fit the visible canvas), so it never covers another card's title. A dropped card lands at the drop point.

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
free slot (the Data Source is shown first). Its `table` is the source's automatic name and its columns load from `POST /api/source/columns`. It looks
like a table card without profile buttons or drag handles (a source takes no relationship), with one note line under the head
saying how its columns are matched; its title, column names and note start at the same x as a table card's (the left lane stays empty on both). Remove and collapse work as on any card.

## Empty state

With no entities the canvas shows **a ghost model** (two dashed cards joined by an elbow link with its one / many ends, drawn in tokens,
`aria-hidden`), **one sentence and one button**, chosen by `emptyState()` in
`empty-state.js` (pure) and the button focuses the control for that step (expanding a collapsed sidebar
first — `expandSidebar()`, [layout.md](../design/layout.md#sidebar)):

| State | Sentence | Button → focuses |
|---|---|---|
| not connected | "Connect to a ClickHouse server to begin." | Connect → `#conn-host` |
| no database chosen | "Choose a database in the sidebar." | Choose a database → `#db-select` |
| database chosen | "Drag a table here from the sidebar to start your data source." | Find a table → `#table-search` |

## Card anatomy

- **Head** (`.entity__head`): the table name alone (600; the full `db.table` is its tooltip), a collapse caret and a remove icon at its right end. The database appears, muted after the name, only when another card holds the same table name from a different database. The card width follows the title text, from `--entity-min` (312px — the slot width) to `--entity-max`
  (480px) on `#model-view` (`card-width.js`, pure); beyond the maximum the name ellipsises (full name in its
  `title`). Link anchors read the measured card box, so any width stays correct.
- **Column rows** (`.col-row`): a **type icon** (number / text / date / bool), name, a **type badge**
  (`.col-row__type`, from the type category), and nothing else, on a 16px gutter at both edges so the left space equals the right (names line up under the head's title). A row is a drag handle for relationships (relationships.md); a column in a relationship is pinned to the card's key strip and its name turns accent.
- Solid card with depth: `--line-2` stroke, `--elev-card` (a tight contact shadow plus a wide soft one; `--elev-card-hover` on hover, `--elev-16` while dragging) and a `--card-rim` highlight on the head's top edge. The head sits on `--surface-2`.
- The type is plain muted monospace text at the row's end (no chip); a joined row's name is accent.
- **No rows on the card.** The column list scrolls inside the card up to 240px tall (a short table is only as tall as its columns); a table's rows are
  previewed from its chip in the schema browser ([schema-browser.md](schema-browser.md#row-preview)).
- The caret toggles `.entity--collapsed`, leaving only the title bar.

## Moving & removing

- Cards move by dragging the **head** with pointer events (a separate gesture from chip DnD); the
  entity's `x, y` snap to 8px steps and update and `entity:moved` fires so links re-route.
- Removing a card removes its relationships, with a confirm dialog when any exist. If a half-drawn link
  was waiting on that card, it is cancelled (no dangling "undefined" toast).

## Join keys

There is no join-key setting. A column is a join key because a relationship uses it: dragging one column onto another creates the relationship
([relationships.md](relationships.md)), and the card pins both columns to its key strip. An entity takes part in as many relationships as it has free columns.
