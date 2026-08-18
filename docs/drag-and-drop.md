# Drag & drop, entity cards, and relationships

The core interaction: dragging a table onto the canvas, rendering it as an entity, and
drawing logical relationships between entities. Built on the **native HTML5 Drag and Drop
API** — no library ([decision D4](project/decisions.md)). Client code:
`wwwroot/js/canvas.js` (drop + cards) and `wwwroot/js/relations.js` (links).

## 1. Dragging a table from the sidebar

Each `.table-chip` is `draggable="true"`. On `dragstart` it writes its source into the
drag payload:

```js
e.dataTransfer.setData('application/x-ch-table', JSON.stringify({ db, table }));
e.dataTransfer.effectAllowed = 'copy';
```

- Use a **custom MIME type** (`application/x-ch-table`) so the canvas only accepts our
  chips, not arbitrary text/files.
- The canvas (`.canvas`) handles `dragover` (call `preventDefault()` so it's a valid drop
  target, set `dropEffect = 'copy'`) and `drop`.

> **Built (P3):** the sidebar side of this — draggable chips, the `dragstart` payload above,
> and a `＋` fallback button dispatching `table:add` `{db,table}` — lives in `schema.js`. The
> canvas `dragover`/`drop` handler and `table:add` listener are P4 (`canvas.js`).

## 2. Dropping → creating an entity

On `drop` over the canvas:
1. Read `{ db, table }` from `dataTransfer`.
2. Fetch columns (`GET …/columns` → `DESCRIBE`) and a preview (`GET …/preview?limit=`)
   — see [clickhouse-integration.md](clickhouse-integration.md).
3. Create an `Entity` ([data-model.md](data-model.md)) positioned at the drop point and
   render an **entity card**:
   - **head**: `db.table` + remove icon (`.iconbtn--danger`);
   - **column rows** (`.col-row`): name, **type badge** (`.col-row__type`), and a
     **join-key checkbox** (`.col-row__key`);
   - **data grid** (`.entity__grid` / `.data`): the sample rows, scrolling internally.
4. Hide the empty-state hint once the canvas has ≥1 entity (via the `hidden` attribute —
   [DESIGN.md](../DESIGN.md#layout-rules)).

While a drop is in flight the card shows a **loading** pill (amber) until columns/preview
arrive; a failed fetch shows a **failed** pill (red) with a retry, never a bare error.

> **Built (P4):** `canvas.js` implements the drop → entity card (columns fetched in parallel
> with the preview), the loading/failed status + Retry, numeric right-align, and card
> movement via pointer events on the head. Join-key checkboxes toggle `entity.joinKeys` (a
> highlight for now); **relationship drawing from those keys is P5** (`relations.js`).

## 3. Moving entities on the canvas

Entity cards are repositioned by dragging their **head** (`.entity__head`). This is a
separate gesture from sidebar-chip dragging — implement it with pointer events (or a
second HTML5 DnD source scoped to the head) and update the entity's `x,y`. Relationship
links re-route as cards move.

## 4. Selecting join keys

The statement requires that **every dragged-in table selects one or more columns** for
relationships ([data-model.md](data-model.md)). The join-key checkbox on each column row
adds/removes the column from the entity's `joinKeys`. An entity with no join key:
- shows a subtle "pick a join key" affordance, and
- cannot be an endpoint of a relationship until at least one key is chosen.

## 5. Drawing a relationship

To relate entity A and entity B:
1. The user checks a join key on A and a join key on B.
2. They start a link from A's key row (a small connector handle) and release on B's key
   row — or use an explicit "relate" action that asks for the two endpoints.
3. A **cardinality** picker sets `1:1 | 1:N | N:1 | N:M`.

Render the link as an SVG path (`.rel-link`) between the two column rows, with:
- **shape-coded endpoints** — a "one" marker vs. a "many" (crow's-foot-style) marker, so
  cardinality is readable **without color** ([DESIGN.md](../DESIGN.md#accessibility-posture));
- a small **cardinality badge** (`.rel-badge`) at the midpoint;
- `--brand` (red) styling only while the link is **selected or being drawn**; resting
  links use `--ink-2`.

Selecting a link lets the user change its cardinality or delete it. Removing an entity
removes its links (with a confirm dialog if any exist).

> **Built (P5):** `relations.js` + a shared `store.js` (entities, relationships, and an event
> bus so canvas/relations coordinate without touching each other's DOM). Creation is
> **click-to-click**, not drag: a checked join key shows a `.rel-connector` handle; click one,
> then a key on another entity, then pick a cardinality in a `<dialog>`. Links render in an SVG
> overlay with **shape-coded** one/many endpoints (a tick vs. a crow's foot) and a cardinality
> badge; clicking a link opens the edit/delete dialog. Links re-route on `entity:moved`, and a
> removed entity or an unchecked join key prunes the links that depended on it. The
> relationship model matches [data-model.md](data-model.md); it stays a logical declaration
> (D5).

> Reminder: a relationship is a **logical declaration** the app uses for layout/joins —
> ClickHouse does not create or validate it ([decision D5](project/decisions.md)). The
> cardinality is intent, not a data guarantee.

## Accessibility

Drag/drop is pointer-centric, so provide non-drag fallbacks: an "Add to canvas" action on
each table chip, and a keyboard/click path to create a relationship (pick entity A key →
pick entity B key → choose cardinality) via a dialog. Icon-only handles carry `aria-label`s.
