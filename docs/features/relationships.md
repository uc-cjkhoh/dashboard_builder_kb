# Relationships & cardinality

Logical links between two entities' join keys, drawn on the Data Model canvas. A relationship is the
**user's declaration** used for joins and layout — ClickHouse never creates or validates it
([golden rule 5](../conventions/golden-rules.md#5-relationships-are-logical-declarations-not-database-facts)).
Code: `Features/Relations/` (`relations.js`, `relation-rules.js`, `relations.css`). Shape: [data-model.md](../reference/data-model.md#relationship).

## Drawing a link — click-to-click

1. Tick a join key on entity A and on entity B ([canvas.md](canvas.md#join-keys)). Each checked key
   shows a `.rel-connector` handle.
2. Click A's handle, then a key handle on B. (No drag — this path is also the keyboard path.)
3. The link is checked first (below); if it passes, pick the **cardinality** — `1:1 | 1:N | N:1 | N:M` — in a `<dialog>` (`.card-choice`).

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
- A **cardinality badge** (`.rel-badge`) sits at the midpoint — "1:N", or "1:N · left" for a left join.
- Resting links use `--ink-2`; a link is `--accent` blue only while **selected or being drawn**.

## Editing & cleanup

- Clicking a link opens the edit/delete dialog (change cardinality or join type, or remove).
- Links re-route live on `entity:moved`.
- Removing an entity, or unticking a join key a link depends on, prunes those links; `rel:changed`
  fires.

## Join type (P31)

The cardinality dialog's **Join** choice: **Inner** (the default — only rows that match on both sides)
or **Left** (keep the rows of the tables already in the view even when the other side has no match;
their fields read as empty / "—"). A left link's worksheet joins are sent as `type: "left"` and emitted
as `LEFT JOIN` (a whitelisted keyword) with `join_use_nulls = 1`, so unmatched values are NULL, not
ClickHouse's zero / "" defaults (on a server that refuses settings the defaults show). The direction is
the query's: rows of whichever table the view reached first are kept. Saved per relationship
(`joinType`).

## What cardinality means

`1:N` from A→B means "one row in A relates to many rows in B, matched on the chosen columns." It drives
the endpoint markers and the join direction. It is **intent, not a data guarantee** — ClickHouse
won't stop A's "one" side from having duplicates, so worksheet joins can fan out on the many side
([D12](../reference/decisions.md#d12--subtabs-are-dashboards-over-one-shared-data-model)).
