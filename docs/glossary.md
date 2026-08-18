# Glossary

Domain terms as used in this project. Where a term has a subtle or non-obvious meaning
here, that's called out.

| Term | Meaning in this project |
|---|---|
| **Connection** | A session-scoped ClickHouse connection (host/port/user/password/TLS) held on the server; credentials never leave the server. [data-model.md](data-model.md) |
| **Database / Table** | ClickHouse objects, discovered by introspection (`SHOW DATABASES`, `SHOW TABLES`). Read-only. |
| **Introspection** | Reading schema metadata (`SHOW`, `DESCRIBE`, `system.*`) — never modifying it. [clickhouse-integration.md](clickhouse-integration.md) |
| **Table chip** | A draggable item in the sidebar table list; carries its `db`+`table` in the drag payload. [drag-and-drop.md](drag-and-drop.md) |
| **Canvas** | The white right-hand workspace where entities and relationships live; the drop target. [modules.md](app/modules.md) |
| **Entity / Entity card** | A table dropped onto the canvas, rendered as a card with columns, type badges, join-key checkboxes, and a sample-data grid. [data-model.md](data-model.md) |
| **Entity view** | The visual representation of a table as an entity (the card + its preview rows). |
| **Preview** | A small `SELECT … LIMIT n` sample of a table's rows shown in the entity card. Always bounded. |
| **Join key** | A column the user checks to say "this participates in a relationship." Every dragged-in table must select ≥1. [data-model.md](data-model.md) |
| **Relationship** | A **logical** link between two entities' join keys — the user's declaration, **not** a database constraint. [decision D5](project/decisions.md) |
| **Cardinality** | The relationship's shape: `1:1`, `1:N`, `N:1`, `N:M`. Intent, not a data guarantee — ClickHouse enforces no uniqueness. |
| **Subtab / Dashboard** | An independent tab on the canvas with its own entities, relationships, and widgets. [modules.md](app/modules.md) |
| **Widget** | A KPI tile or chart derived from a tab's data (later phase). [modules.md](app/modules.md) |
| **MergeTree primary key** | ClickHouse's sort/sparse-index key — **not** a uniqueness constraint and **not** a foreign-key target. A frequent source of false assumptions. [decision D5](project/decisions.md) |
| **Identifier injection** | The risk from interpolating client-supplied db/table/column names into SQL (they can't be bound as parameters). Mitigated by validate-against-catalog + backtick-quote. [clickhouse-integration.md](clickhouse-integration.md) |
| **The shell** | The fixed, non-scrolling full-screen layout (black sidebar + white canvas); regions scroll internally. [DESIGN.md](../DESIGN.md#layout-rules) |
