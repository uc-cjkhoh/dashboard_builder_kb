# Data model

The shapes the app works with — on the server (transient, per request) and in the
browser (the builder state). There is **no application database** ([decision D2](project/decisions.md));
these are in-memory / JSON shapes, not persisted tables.

## Server-side (transient)

### Connection (session-scoped)
Held in `ConnectionRegistry`, keyed by session. Never serialized to the client.

| Field | Notes |
|---|---|
| `host` | ClickHouse host |
| `port` | **`8443`** (HTTPS interface) — the target server is TLS-only (native TLS is `9440`, unused); plaintext `8123`/`9000` not available |
| `user` | ClickHouse user |
| `password` | **server-only**; never returned, never logged |
| `secure` | **use TLS — required** for the real server (defaults on; paired with port `8443`) |
| `allowInvalidCert` | accept a self-signed / untrusted server cert (defaults **on** — internal servers; [decision D11](project/decisions.md)) |

Only derived, non-secret facts (e.g. "connected", server version) are exposed to the client.

### Introspection results (pass-through JSON)
The server returns lists it just read from ClickHouse; it does not store them.
- **databases**: `string[]` (from `SHOW DATABASES`).
- **tables**: `string[]` (from `SHOW TABLES FROM {db}`).
- **columns**: `{ name, type }[]` (from `DESCRIBE TABLE {db}.{table}`), `type` is a raw
  ClickHouse type string — see [clickhouse-integration.md](clickhouse-integration.md#type-mapping).
- **preview**: `{ columns: string[], rows: cell[][] }` (from `SELECT … LIMIT n`).

## Client-side (the builder state)

All builder state lives in the browser ([decision D2](project/decisions.md)). One
in-memory model per open page; each **subtab** owns an independent slice.

```
BuilderState
└── tabs: Tab[]
     each Tab {
       id, name,
       entities: Entity[],
       relationships: Relationship[],
       widgets: Widget[]        // later phase
     }
```

> **Built:** `store.js` implements this with a **correction to the earlier subtab design** — the
> `entities` + `relationships` are **one shared data model** (not per-tab), and the `dashboards`
> array holds the subtabs — each **is a worksheet** (one viz) with a `sheet`:
> `{ columns:[field], rows:[field], filters:[{db,table,column,op,value}],
> chartType:'bar'|'line'|'table', sort:{by,dir}|null }`, built by dragging fields onto shelves.
> `sort` is null by default (ascending by the first field). Fields may span
> **different tables**; the client resolves a **join path** over the drawn relationships and the
> server executes the join ([O4](project/decisions.md), *execute joins*). State is in-memory only
> ([O1](project/decisions.md)).
>
> **Multi-field shelves (Tableau-style).** `columns` and `rows` are each an **ordered list** of
> field pills — both shelves accept any number of fields. A field's *role* defaults from its type but
> is **overridable per pill** (`role:'dimension'|'measure'`, Tableau's convert-to-dimension/measure):
> - a **dimension** → `GROUP BY` (pill: `{db,table,column,category,role:'dimension'}`);
> - a **measure** → aggregated (pill adds `role:'measure', agg:'sum'|'avg'|'min'|'max'|'count'|'countDistinct'`).
>
> Default role is numeric → measure, else dimension; the pill's convert button (`Σ`/`#`) flips it, so a
> **numeric field can be used as a dimension** (group by its raw values) or any field aggregated.
> `countDistinct` counts unique values (server maps it to ClickHouse `uniqExact`); agg options are
> type-aware (no `sum`/`avg` offered for text). `roleOf(f)` (dashboards.js) resolves the effective role.
>
> **The shelf sets the crosstab axis** (not just cosmetic). `buildPlan()` (dashboards.js) sends the
> Rows-shelf dimensions as `rowDimensions[]` (the pivot's **left stub**), the Columns-shelf
> dimensions as `columnDimensions[]` (the **top header**), and every numeric pill as `measures[]`
> (the **cell** values). With no measures the server adds an implicit `count`. The server groups by
> all dimensions (rows first, then columns) and returns
> `{ rowDimensions:[name], columnDimensions:[name], measures:[name], rows:[{keys:[rowVals…,colVals…], values:[]}] }`,
> ordered by the dimension keys for the Table view (`orderByDimensions:true`) or by the first measure
> for charts.
>
> **Table view = a true Rows×Columns crosstab** (see `crosstabTable()` in dashboards.js): the client
> pivots the flat grouped rows into a matrix with nested headers (colSpan on top, rowSpan on the left
> stub). Per the Tableau model, the **measure-name band sits on whichever shelf the numeric pills are
> on** — measures on Columns show across the top, measures on Rows down the left (transposing the
> grid). Measures on **both** shelves is ill-defined for one value grid → the app shows a note and
> falls back to the top band. **Charts (bar/line) are still Phase 1**: they flatten `rowDims++colDims`
> onto the category axis, one series per measure; true chart-axis orientation is Phase 2. See
> [app/modules.md](app/modules.md) and [clickhouse-integration.md](clickhouse-integration.md).

### Entity
A table dropped onto the canvas.

| Field | Notes |
|---|---|
| `id` | client id (e.g. `db.table` + counter; card can appear once per tab) |
| `db`, `table` | source, from the drag payload |
| `x`, `y` | position on the canvas |
| `columns` | `{ name, type }[]` from `DESCRIBE` |
| `joinKeys` | `Set<columnName>` — the column(s) the user checked; **required** to relate (see below) |
| `preview` | cached sample rows for the data grid |

### Relationship
A **logical** link between two entities ([decision D5](project/decisions.md)) — the
database neither creates nor validates it.

| Field | Notes |
|---|---|
| `id` | client id |
| `from` | `{ entityId, column }` — a checked join key on entity A |
| `to` | `{ entityId, column }` — a checked join key on entity B |
| `cardinality` | one of `1:1`, `1:N`, `N:1`, `N:M` |

**Rule from the statement:** *every table dragged in must have one or more columns
selected to build relationships.* Enforce it in the UI — an entity with no `joinKeys`
cannot be an endpoint of a relationship, and the app should nudge the user to pick a
key. The keys are the user's declaration of "these columns line up"; ClickHouse is never
asked to confirm it.

### Cardinality semantics
`1:N` from A→B means "one row in A relates to many rows in B, matched on the chosen
columns." It drives:
- the **endpoint markers** (shape-coded one vs. many — [drag-and-drop.md](drag-and-drop.md));
- how a future joined query / widget would aggregate ([open question O4](project/decisions.md)).

It does **not** imply any uniqueness in the data — ClickHouse won't stop A's "one" side
from having duplicates. Treat cardinality as intent, and if joins are ever executed,
handle the many-sided fan-out explicitly.

### Widget (later phase)
`{ id, kind: 'kpi' | 'chart', title, source, config }`, deferred — see
[modules.md](app/modules.md) module 7 and [open question O3](project/decisions.md).

## Persistence

None in v1: refresh loses builder state ([decision D2](project/decisions.md),
[open question O1](project/decisions.md)). If added, the natural unit is a **Tab**
serialized to JSON (entities with positions + join keys + relationships), keyed by
session — **never** persisting connection passwords.
