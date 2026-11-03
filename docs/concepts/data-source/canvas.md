---
components: [src/DashboardBuilder/Features/Canvas/]
---
# Canvas & entity cards

The **Data Source** view is the drop target where tables become entity cards. It uses the browser's native HTML5
Drag and Drop API, with no library ([D4](../../decisions/decisions-platform.md#d4--vanilla-js--hand-written-css-no-spa-framework)).
Drawing relationships on top of the cards is covered in [relationships.md](relationships.md).

**Code:** `Features/Canvas/`

- `_Canvas.cshtml` — the view markup
- `canvas.js` — drop handling, cards, moving and removing
- `empty-state.js` — the empty-state choice (pure)
- `canvas.css` — styles

## Canvas ground

- The ground is a 24px dot grid that scrolls with the cards.
  It is drawn on `.view--model` with `--line-2` dots, offset by the 16px gutter, and `background-attachment: local`.
- Cards snap to the grid's 8px steps.
  The free-slot step (312 + 48 = 360) is a whole number of dot cells.
- While a table chip is dragged over the canvas, the ground takes a faint accent wash and the dashed accent outline.

## Dragging a table onto the canvas

- **Only our chips are accepted.** A sidebar chip's `dragstart` sets `application/x-ch-table` = `{db, table}` with
  `effectAllowed = 'copy'` ([schema-browser.md](schema-browser.md#table-list)). Because the MIME type is custom,
  the canvas never accepts arbitrary text or files.
- The canvas handles `dragover` (`preventDefault()`, `dropEffect = 'copy'`) and `drop`.
- A drop whose payload isn't `{db, table}` strings is ignored.
- **No duplicates.** A table already on the canvas is not added twice. Instead, the existing card is scrolled into view
  and focused (`tabindex="-1"`), and a toast says so.
- **The `＋` button takes the same path.** The chip's `＋` fallback fires the `table:add` event, which is handled like a drop.
  A dropped table always lands in the shared model: `table:add` switches to the Data Source tab first ([tabs.md](../workbook/tabs.md)).
- **Where a card lands:**
  - A dropped card lands at the drop point.
  - A `＋`-added card goes in the **first free grid slot**, so it never covers another card's title.
    Slots are 312 × 312 cells measured from the 16px view gutter, with a 96px gutter between cards (room for a link's elbow and badge),
    and as many columns as fit the visible canvas.

## Creating an entity

On drop:

1. Read `{db, table}` and create an `Entity` at the drop point (id `db.table#n`) —
   [data-model.md](../../reference/data-model.md#entity).
2. Fetch the columns with `GET …/columns` (`DESCRIBE`). Each column is tagged with a display category.
3. Render the card with a **loading** status (amber) until the columns arrive.
   A failed fetch shows a **failed** status (red) with **Retry**, never a bare error.
4. Once the canvas has at least one entity, hide the empty state (`.canvas__empty`) with `hidden`.

## Union and unpivot cards

A union or unpivot added from the sidebar dialogs ([query-sources.md](query-sources.md)) becomes a card in the first free slot.

- It arrives as a `source:add` event, and the Data Source is shown first.
- Its `table` is the source's automatic name. Its columns load from `POST /api/source/columns`.
- It looks like a table card, but without profile buttons or drag handles, because a source takes no relationship.
- One note line under the head says how its columns are matched.
- Its title, column names and note start at the same x as a table card's (the left lane stays empty on both).
- Remove and collapse work as on any card.

## Empty state

With no entities, the canvas shows **a ghost model**, **one sentence** and **one button**.

- The ghost model is two dashed cards joined by an elbow link with its one / many ends, drawn in tokens and `aria-hidden`.
- The sentence and button are chosen by `emptyState()` in `empty-state.js` (pure).
- The button focuses the control for that step. If the sidebar is collapsed, it expands it first
  (`expandSidebar()`, [layout.md](../../reference/design/layout.md#sidebar)).

| State | Sentence | Button → focuses |
|---|---|---|
| not connected | "Connect to a ClickHouse server to begin." | Connect → `#conn-host` |
| no database chosen | "Choose a database in the sidebar." | Choose a database → `#db-select` |
| database chosen | "Drag a table here from the sidebar to start your data source." | Find a table → `#table-search` |

## Card anatomy

- **Head** (`.entity__head`, on `--surface-2`):
  - The table name alone, in weight 600. The full `db.table` is its tooltip.
  - The database appears, muted after the name, only when another card holds the same table name from a different database.
  - A collapse caret and a remove icon sit at its right end. The caret toggles `.entity--collapsed`, leaving only the title bar.
- **Card width** follows the title text, from `--entity-min` (312px, the slot width) to `--entity-max` (480px) on `#model-view`
  (`card-width.js`, pure). Beyond the maximum the name ellipsises, with the full name in its `title`.
  Link anchors read the measured card box, so any width stays correct.
- **Column rows** (`.col-row`) show a **type icon** (number / text / date / bool), the name and a **type badge**
  (`.col-row__type`, from the type category), and nothing else.
  - The type is plain muted monospace text at the row's end (no chip).
  - Rows sit on a 16px gutter at both edges, so the left space equals the right and names line up under the head's title.
  - A row is a drag handle for relationships ([relationships.md](relationships.md)).
  - A column in a relationship is pinned to the card's key strip, and its name turns accent.
- **No rows on the card.** The column list scrolls inside the card, up to 240px tall; a short table is only as tall as its columns.
  A table's rows are previewed from its chip in the schema browser ([schema-browser.md](schema-browser.md#row-preview)).
- **Look:** a solid card with depth.
  - `--line-2` stroke and a `--card-rim` highlight on the head's top edge.
  - Shadow `--elev-card` (a tight contact shadow plus a wide soft one), `--elev-card-hover` on hover and `--elev-16` while dragging.

## Moving & removing

- **Moving:** drag a card by its **head**. This uses pointer events, a separate gesture from dragging a chip with drag and drop.
  The entity's `x, y` snap to 8px steps and update, and `entity:moved` fires so links re-route.
- **Removing** a card removes its relationships, with a confirm dialog when any exist.
  If a half-drawn link was waiting on that card, it is cancelled (no dangling "undefined" toast).

## Join keys

There is no join-key setting. A column is a join key because a relationship uses it.

- Dragging one column onto another creates the relationship ([relationships.md](relationships.md)), and the card pins both columns to its key strip.
- An entity takes part in as many relationships as it has free columns.
