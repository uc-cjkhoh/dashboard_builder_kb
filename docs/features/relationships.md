# Relationships & cardinality

Logical links between two entities' join keys, drawn on the Data Model canvas. A relationship is the
**user's declaration** used for joins and layout — ClickHouse never creates or validates it
([golden rule 5](../conventions/golden-rules.md#5-relationships-are-logical-declarations-not-database-facts)).
Code: `Features/Relations/` (`relations.js`, `relation-rules.js`, `relations.css`). Shape: [data-model.md](../reference/data-model.md#relationship).

## Drawing a link — click-to-click

1. Tick a join key on entity A and on entity B ([canvas.md](canvas.md#join-keys)). Each checked key
   shows a `.rel-connector` handle.
2. Click A's handle, then a key handle on B. (This path is also the keyboard path.)
3. The link is checked first (below); if it passes, pick the **cardinality** — `1:1 | 1:N | N:1 | N:M` — in a `<dialog>` (`.card-choice`).

## Drawing a link — drag a column

Drag any column row (`.col-row`, `draggable`; payload MIME `application/x-ch-column`) and drop it on a row of
another card. The row under the pointer takes a solid accent outline when the link is allowed and a dashed
muted outline (drop effect none) when it isn't; the dragged row dims. A refused drop toasts the same reason
as a click. An allowed drop opens the same join + cardinality dialog; picking a cardinality ticks both
columns as join keys and draws the link (cancelling changes nothing). `link-drag.js` (pure) holds the
payload parse and `dropDecision()`, which reuses `linkProblem()`.

## What may be linked

`relation-rules.js` (pure) `linkProblem()` blocks a link — with a toast naming both columns and their
types, and no cardinality dialog — when:

- both ends are on the **same table**;
- the same two columns are **already related** (either direction);
- the key **kinds differ** — only number↔number, text↔text, date↔date and boolean↔boolean link
  (`keysCompatible`); `compound` and `other` columns never link.

## Rendering

- Links are SVG paths in an overlay (`.rel-svg`, `.rel-link`) between the two column rows, with a wider
  invisible hit path (`.rel-link__hit`) for clicking.
- **Shape-coded endpoints** (`.rel-end`) — a tick for "one", a crow's foot for "many" — so cardinality
  reads without colour.
- A **cardinality badge** (`.rel-badge`) sits at the midpoint — "1:N", or "1:N · left" / "· right" / "· full" for an outer join.
- Resting links use `--ink-2`; a link is `--accent` blue only while **selected or being drawn**.

## Editing & cleanup

- Clicking a link opens the edit/delete dialog (change cardinality or join type, or remove).
- Links re-route live on `entity:moved`.
- Removing an entity, or unticking a join key a link depends on, prunes those links; `rel:changed`
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
([D12](../reference/decisions.md#d12--subtabs-are-dashboards-over-one-shared-data-model)).
