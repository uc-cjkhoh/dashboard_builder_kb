# Relationships & cardinality

Logical links between a column of one entity and a column of another, drawn on the Data Source canvas. A relationship is the
**user's declaration** used for joins and layout — ClickHouse never creates or validates it
([golden rule 5](../conventions/golden-rules.md#5-relationships-are-logical-declarations-not-database-facts)).
Code: `Features/Relations/` (`relations.js`, `relation-rules.js`, `relations.css`). Shape: [data-model.md](../reference/data-model.md#relationship).

A **union or unpivot card** ([query-sources.md](query-sources.md)) takes no relationship: its rows aren't draggable, and dropping a
table column on one toasts "A union or unpivot can't be related to a table yet."

## Drawing a link — drag a column

Relationships are made by **drag and drop only**: drag a column row (`.col-row`, `draggable`; payload MIME `application/x-ch-column`) and drop it on a row of
another card. There are no connector handles and no join-key checkboxes; the columns a relationship uses are simply the ones it joins.
The row under the pointer takes a solid accent outline when the link is allowed and a dashed muted outline (drop effect none) when it isn't; the dragged row dims.
A refused drop is reported (below). An allowed drop is checked first, then opens the join + cardinality dialog (`<dialog>`, `.card-choice`: `1:1 | 1:N | N:1 | N:M`);
picking one draws the link (cancelling changes nothing). `link-drag.js` (pure) holds the payload parse and `dropDecision()`, which reuses `linkIssue()`.
Removing a link: click its badge, then Delete.

**The how-to line.** While any table card has no relationship, a pill at the foot of the Data Source (`.rel-guide`) says "Drag a column onto a column in another table to relate them."
It goes once every card has one. There is no keyboard path for creating a link yet (see [backlog](../backlog/README.md)).

## What may be linked

`relation-rules.js` (pure) `linkIssue()` (`linkProblem()` is its message) blocks a link, with no cardinality dialog, when:

- both ends are on the **same table**;
- the same two columns are **already related** (either direction);
- the key **kinds differ** — only number↔number, text↔text, date↔date and boolean↔boolean link
  (`keysCompatible`); `compound` and `other` columns never link.
- a column is **already in a relationship** (see Rules below).

**How a refusal shows.** A **type mismatch** opens a warning modal (`type-warning.js`, `.dialog--warn`): the title "Data types don't match" with a warning icon,
both columns as `table.column` with their exact ClickHouse type and kind (`Float64 · number`), one sentence on why (a join compares values, so both must be the same kind),
and — for a number / text / date / boolean key — the free columns of the other table that would fit (or that it has none). A single **Got it** button closes it; Esc does too.
Every other refusal (same table, already related, column already used) stays a toast.

## Rendering

- Links are **elbow lines with rounded corners** between the two column rows, in two SVG overlays: the lines (`.rel-svg`, `.rel-link`) sit
  **under** the cards, so a link to a far card slips under the cards between; the badges (`.rel-svg--labels`) sit **over** them, so a badge wider than the
  gutter is never clipped. A wider invisible hit path (`.rel-link__hit`) makes the line easy to click; line and badge act as one link (hover, click).
- The route (`link-route.js`, pure): a link leaves a card's side straight out, turns at right angles and enters the other card straight in.
  Cards with a gutter of at least 32px face each other and the link turns in the middle of the gutter, so its badge sits equally far from both cards; closer or overlapping cards both use the right
  edge and the link loops out past the farther one. Links sharing a gutter take lanes 8px apart (the first runs on the middle, the next two either side); a badge that would cover another steps down.
- **Shape-coded endpoints** (`.rel-end`) — a tick for "one", a crow's foot for "many", square to the card edge — so cardinality
  reads without colour.
- **Rules.** A column is in at most one relationship (`relationshipOf` in `relation-rules.js`; the click, drag and workbook-import paths all refuse a second one, naming the column).
  Every table card belongs to a relationship: once the model holds two or more table cards, one with none is marked **Needs a partner** (`.entity__need`, dashed `--warn` outline —
  text and outline, not colour alone). A union / unpivot takes no relationship and is exempt; a lone card is not flagged.
  **Consequence:** such a card is held out of worksheets. Its fields don't appear in the field pane (with every table held out, the pane says to relate them first), and a view or
  dashboard widget that still reads one (`heldOutProblem`, `worksheet-view.js`) shows "<table> isn't related to another table yet. Relate it in the Data Source to use its fields." and
  sends no query. Relating the card restores it. A card may relate to several others (star schemas and chains are fine).
- **Pinned keys.** A column in a relationship moves out of the scrolling list into the card's key strip (`.entity__keys`, accent wash) above it and goes back to its place when the link goes,
  so a link's end is always on a visible row however far the list is scrolled.
  Pinned rows are ordered by their **partner**, not by column order (`pinOrder`, `orderStrip` in `relations.js`): by the partner card's top edge, then by the order the relationships were made.
  Both cards of a pair see the same order, so their links run parallel — straight when the cards' tops line up, never crossing; a card with partners above and below lists the upper
  partner's keys first. The order is recomputed when a card moves.
  **Magnetic alignment.** While a card is dragged, its top edge is pulled onto the position that puts a pinned key row level with its partner's (`straightenTops` in `canvas.js`,
  `snapTop` in `align-snap.js`, pure) when the pointer is within 12px of it, so the link becomes one straight line; hold **Alt** to drag without the pull. Collapsed cards don't pull.
- A **cardinality badge** (`.rel-badge`, a pill) sits on the link's middle run — "1:N", or "1:N · left" / "· right" / "· full" for an outer join.
- Resting links use `--ink-3`; a link is `--accent` while **hovered, selected or being drawn**, and the two key rows it joins take the accent wash
  (`.col-row--linked`) so which columns a line connects reads at a glance.

## Editing & cleanup

- Clicking a link opens the edit/delete dialog (change cardinality or join type, or remove).
- Links re-route live on `entity:moved`.
- Removing an entity prunes its links; `rel:changed`
  fires.

## Join type (P31, T02-12, T02-13)

The dialog's **Join** choice, worded with the two tables (the link runs first-clicked key → second, so the
first is the **left** side): **Inner — only rows that match**, **Keep all rows of {first table}** (`left`),
**Keep all rows of {second table}** (`right`), **Keep all rows of both** (`full`). Unmatched rows have NULL
for the other side's fields (they read "—"). The badge says it in words ("1:N · left", "· right", "· full").
Saved per relationship (`joinType`); a workbook without one, or with an unknown one, reads as inner.

**Preserved-side rule.** A link saved with the new dialog is *fixed* (`joinFixed`): it keeps the table it names
whichever table the view starts from — the plan walks outward from the base, and a fixed link crossed
second-to-first swaps `left`/`right` (`planJoinType`). **Older links** (a workbook saved before this, `joinFixed`
absent, type `left`) keep the old rule: `LEFT JOIN`, keeping the base-side table in either direction. The edit
dialog shows such a link as "Keep rows of the base table (older link)"; saving the dialog with any choice
(including re-saving that one) is what fixes it: picking "Keep all rows of {table}" converts it, and picking the
older-link choice leaves it legacy. Right and full are always fixed.

**Behaviours chosen** (see [clickhouse-integration.md](../reference/clickhouse-integration.md#worksheet-query-queryasync)):
a filter on a table whose rows were NULL-extended drops those rows (the outer join then acts inner for that
filter); `count()` counts NULL-extended rows; a NULL join key never matches, so such rows appear unmatched
on both sides of a full join. Grouping by the *non-preserved* table's key shows NULL for the unmatched rows. **Refused (400):** a top-N filter on a view with a right or full join, and
right/full joins on a connection whose server refuses settings (`join_use_nulls` is required). Approximate
mode reads such a view exactly (no sample).

## Check this join (join safety preview)

The relationship dialog (new link and edit) has a **Check this join** button: one bounded, read-only call
(`POST /api/relationships/preview`, [api.md](../reference/api.md#relationship-preview)) that reads at most the first
1,000,000 rows of each table and reports, in plain words: the share of each table's rows that have a match in the other
("94% of the rows in orders have a match in customers; 6% don't"), how often a key repeats on each side, NULL keys (never
match), and the shape the data shows (`1:1`, `1:N`, `N:1`, `N:M`; first letter = the first table). Pure wording:
`join-preview-model.js`. **Sampled results** (a side reached the row bound): the note comes first ("Based on the first N rows of each table, in no particular order"), the shares are worded "within the sample", and nothing that needs the two slices to overlap is raised as a warning — "no keys match" becomes a neutral "can't tell from a sample" note and keys repeating on both sides becomes "may be many-to-many". A declared "one" side whose keys repeat still warns (a repeat is a fact about that table). The preview reads each table twice (its own stats, and as the other side's key set) with no `ORDER BY`, so on a table being written to the two reads can differ.

**Warnings** (icon + text, amber; never block saving — the relationship stays the user's declaration): keys repeat **materially** on **both** sides
(average at least 1.1 rows per key on each — `MATERIAL_AVG`; a lone stray duplicate is only a note; many-to-many fan-out, sums and counts can double-count; one combined warning that also names a conflicting declaration); a side declared "one" whose keys repeat (edit dialog only — a new link has no
declaration yet, so it gets the reading instead); no keys match at all. While running, the button is disabled and a busy note shows;
the result area is an always-present `role="status"` region; a failure (e.g. incompatible key kinds, ClickHouse refusing to compare the two types — a plain 400 — or a timeout) shows the server message with an error icon. Closing the dialog cancels the request.
Not done: no hint on the drawn line, and nothing is saved with the relationship.

## What cardinality means

`1:N` from A→B means "one row in A relates to many rows in B, matched on the chosen columns." It drives
the endpoint markers and the join direction. It is **intent, not a data guarantee** — ClickHouse
won't stop A's "one" side from having duplicates, so worksheet joins can fan out on the many side
([D12](../reference/decisions.md#d12--subtabs-are-dashboards-over-one-shared-data-source)).
