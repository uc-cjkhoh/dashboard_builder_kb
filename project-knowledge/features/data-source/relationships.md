# Relationships & cardinality

A relationship is a logical link between a column of one entity and a column of another, drawn on the Data Source canvas.
It is the **user's declaration**, used for joins and layout. ClickHouse never creates or validates it
([golden rule 5](../../engineering/golden-rules.md#5-relationships-are-logical-declarations-not-database-facts)).
Shape: [data-model.md](../../reference/data-model.md#relationship).

**Code:** `Features/Relations/` — `relations.js`, `relation-rules.js`, `relations.css`.

A **union or unpivot card** ([query-sources.md](query-sources.md)) takes no relationship. Its rows aren't draggable, and dropping a
table column on one toasts "A union or unpivot can't be related to a table yet."

## At a glance

- **Drag a column onto a column** of another card to relate them, then pick the join type and cardinality in a dialog.
- **One relationship per column.** Kinds must match (number↔number, text↔text, date↔date, boolean↔boolean).
- **Every table card needs a partner** once there are two or more; an unrelated card is held out of worksheets.
- **Join type** is inner, left, right or full, worded with the table names.
- **Check this join** previews match rates and key repeats; its warnings never block saving.
- **Cardinality is intent, not a data guarantee** — joins can still fan out.

## Drawing a link — drag a column

Relationships are made by **drag and drop only**. There are no connector handles and no join-key checkboxes;
the columns a relationship uses are simply the ones it joins.

1. Drag a column row (`.col-row`, `draggable`; payload MIME type `application/x-ch-column`) and drop it on a row of another card.
2. While dragging, the dragged row dims. The row under the pointer shows whether the drop is allowed:
   - a solid accent outline when the link is allowed;
   - a dashed muted outline (drop effect none) when it isn't.
3. A refused drop is reported (see [What may be linked](#what-may-be-linked)).
4. An allowed drop is checked first, then opens the join + cardinality dialog (`<dialog>`, `.card-choice`: `1:1 | 1:N | N:1 | N:M`).
5. Picking one draws the link. Cancelling changes nothing.

`link-drag.js` (pure) holds the payload parse and `dropDecision()`, which reuses `linkIssue()`.

To remove a link, click its badge, then Delete.

**The how-to line.** While any table card has no relationship, a pill at the foot of the Data Source (`.rel-guide`) says
"Drag a column onto a column in another table to relate them." It goes once every card has one.
There is no keyboard path for creating a link yet (see [backlog](../../backlog/README.md)).

## What may be linked

`linkIssue()` in `relation-rules.js` (pure; `linkProblem()` is its message) blocks a link, with no cardinality dialog, when:

- both ends are on the **same table**;
- the same two columns are **already related** (either direction);
- the key **kinds differ** — only number↔number, text↔text, date↔date and boolean↔boolean link
  (`keysCompatible`); `compound` and `other` columns never link;
- a column is **already in a relationship** (see Rules below).

**How a refusal shows.**

- A **type mismatch** opens a warning modal (`type-warning.js`, `.dialog--warn`):
  - the title "Data types don't match" with a warning icon;
  - both columns as `table.column`, with their exact ClickHouse type and kind (`Float64 · number`);
  - one sentence on why: a join compares values, so both must be the same kind;
  - for a number / text / date / boolean key, the free columns of the other table that would fit (or that it has none).

  A single **Got it** button closes it; Esc does too.
- Every other refusal (same table, already related, column already used) stays a toast.

## Rendering

**Lines and badges**

- Links are **elbow lines with rounded corners** between the two column rows, drawn in two SVG overlays:
  - the lines (`.rel-svg`, `.rel-link`) sit **under** the cards, so a link to a far card slips under the cards between;
  - the badges (`.rel-svg--labels`) sit **over** them, so a badge wider than the gutter is never clipped.
- A wider invisible hit path (`.rel-link__hit`) makes the line easy to click. Line and badge act as one link (hover, click).
- A **cardinality badge** (`.rel-badge`, a pill) sits on the link's middle run: "1:N", or "1:N · left" / "· right" / "· full" for an outer join.
- **Shape-coded endpoints** (`.rel-end`) show cardinality without colour: a tick for "one", a crow's foot for "many", square to the card edge.
- **Colour:** resting links use `--ink-3`. A link is `--accent` while **hovered, selected or being drawn**, and the two key rows it joins take the
  accent wash (`.col-row--linked`), so which columns a line connects reads at a glance.

**Routing** (`link-route.js`, pure)

- A link leaves a card's side straight out, turns at right angles and enters the other card straight in.
- Cards with a gutter of at least 32px face each other, and the link turns in the middle of the gutter, so its badge sits equally far from both cards.
- Closer or overlapping cards both use the right edge, and the link loops out past the farther one.
- Links sharing a gutter take lanes 8px apart: the first runs on the middle, the next two either side.
- A badge that would cover another steps down.

**Rules.**

- A column is in at most one relationship (`relationshipOf` in `relation-rules.js`).
  The click, drag and workbook-import paths all refuse a second one, naming the column.
- Every table card belongs to a relationship. Once the model holds two or more table cards, one with none is marked **Needs a partner**
  (`.entity__need`, dashed `--warn` outline — text and outline, not colour alone).
  A union / unpivot takes no relationship and is exempt; a lone card is not flagged.
- **Consequence:** such a card is held out of worksheets.
  - Its fields don't appear in the field pane. With every table held out, the pane says to relate them first.
  - A view or dashboard widget that still reads one (`heldOutProblem`, `worksheet-view.js`) sends no query and shows
    "<table> isn't related to another table yet. Relate it in the Data Source to use its fields."
  - Relating the card restores it.
- A card may relate to several others (star schemas and chains are fine).

**Pinned keys.**

- A column in a relationship moves out of the scrolling list into the card's key strip above it (`.entity__keys`, accent wash).
  It goes back to its place when the link goes. So a link's end is always on a visible row, however far the list is scrolled.
- Pinned rows are ordered by their **partner**, not by column order (`pinOrder`, `orderStrip` in `relations.js`):
  by the partner card's top edge, then by the order the relationships were made.
- Both cards of a pair see the same order, so their links run parallel: straight when the cards' tops line up, never crossing.
  A card with partners above and below lists the upper partner's keys first.
- The order is recomputed when a card moves.

**Magnetic alignment.**

- While a card is dragged, its top edge is pulled onto the position that puts a pinned key row level with its partner's,
  when the pointer is within 12px of it. The link then becomes one straight line (`straightenTops` in `canvas.js`, `snapTop` in `align-snap.js`, pure).
- Hold **Alt** to drag without the pull. Collapsed cards don't pull.

## Editing & cleanup

- Clicking a link opens the edit/delete dialog: change the cardinality or join type, or remove it.
- Links re-route live on `entity:moved`.
- Removing an entity prunes its links, and `rel:changed` fires.

## Join type (P31, T02-12, T02-13)

The dialog's **Join** choice is worded with the two tables. The link runs from the first-clicked key to the second, so the first table is the **left** side.

| Choice | Join type |
|---|---|
| **Inner — only rows that match** | inner |
| **Keep all rows of {first table}** | `left` |
| **Keep all rows of {second table}** | `right` |
| **Keep all rows of both** | `full` |

- Unmatched rows have NULL for the other side's fields (they read "—").
- The badge says it in words ("1:N · left", "· right", "· full").
- The choice is saved per relationship (`joinType`). A workbook without one, or with an unknown one, reads as inner.

**Preserved-side rule.**

- A link saved with the current dialog is *fixed* (`joinFixed`): it keeps the table it names, whichever table the view starts from.
  The plan walks outward from the base, and a fixed link crossed second-to-first swaps `left`/`right` (`planJoinType`).
- **Older links** (saved by an earlier build: `joinFixed` absent, type `left`) keep the old rule: `LEFT JOIN`, keeping the base-side table in either direction.
  The edit dialog shows such a link as "Keep rows of the base table (older link)".
- Saving the dialog with any choice (including re-saving that one) is what fixes it.
  Picking "Keep all rows of {table}" converts it; picking the older-link choice leaves it legacy.
- Right and full are always fixed.

**Behaviours chosen** (see [clickhouse-integration.md](../../reference/clickhouse-integration.md#worksheet-query-queryasync)):

- A filter on a table whose rows were NULL-extended drops those rows, so the outer join then acts inner for that filter.
- `count()` counts NULL-extended rows.
- A NULL join key never matches, so such rows appear unmatched on both sides of a full join.
- Grouping by the *non-preserved* table's key shows NULL for the unmatched rows.
- **Refused (400):** a top-N filter on a view with a right or full join; right/full joins on a connection whose server refuses settings
  (`join_use_nulls` is required).
- Approximate mode reads such a view exactly (no sample).

## Check this join (join safety preview)

The relationship dialog (new link and edit) has a **Check this join** button. It makes one bounded, read-only call
(`POST /api/relationships/preview`, [api.md](../../reference/api.md#relationship-preview)) that reads at most the first
1,000,000 rows of each table. Pure wording: `join-preview-model.js`.

**What it reports**, in plain words:

- the share of each table's rows that have a match in the other ("94% of the rows in orders have a match in customers; 6% don't");
- how often a key repeats on each side;
- NULL keys (they never match);
- the shape the data shows (`1:1`, `1:N`, `N:1`, `N:M`; the first letter is the first table).

**Sampled results** (a side reached the row bound):

- The note comes first: "Based on the first N rows of each table, in no particular order".
- The shares are worded "within the sample".
- Nothing that needs the two slices to overlap is raised as a warning. "No keys match" becomes a neutral "can't tell from a sample" note,
  and keys repeating on both sides becomes "may be many-to-many".
- A declared "one" side whose keys repeat still warns, because a repeat is a fact about that table.
- The preview reads each table twice (its own stats, and as the other side's key set) with no `ORDER BY`, so on a table being written to the two reads can differ.

**Warnings** (icon + text, amber) never block saving; the relationship stays the user's declaration. They are:

- keys repeat **materially** on **both** sides — an average of at least 1.1 rows per key on each (`MATERIAL_AVG`).
  Many-to-many fan-out means sums and counts can double-count. A lone stray duplicate is only a note.
  This is one combined warning that also names a conflicting declaration.
- a side declared "one" whose keys repeat. Edit dialog only: a new link has no declaration yet, so it gets the reading instead.
- no keys match at all.

**States:**

- While running, the button is disabled and a busy note shows.
- The result area is an always-present `role="status"` region.
- A failure shows the server message with an error icon. Examples: incompatible key kinds, ClickHouse refusing to compare the two types (a plain 400), or a timeout.
- Closing the dialog cancels the request.

Not done: no hint on the drawn line, and nothing is saved with the relationship.

## What cardinality means

`1:N` from A→B means "one row in A relates to many rows in B, matched on the chosen columns."
It drives the endpoint markers and the join direction.

It is **intent, not a data guarantee**. ClickHouse won't stop A's "one" side from having duplicates, so worksheet joins can fan out on the many side
([D12](../../reference/decisions/decisions.md#d12--subtabs-are-dashboards-over-one-shared-data-source)).
