# Glossary

Domain terms as used in this project. Where a term has a subtle or non-obvious meaning here, that is
called out.

| Term | Meaning in this project |
|---|---|
| **Connection** | The session's ClickHouse connection (host/port/user/password/TLS) held on the server; credentials never leave it. [connection.md](../features/connection.md) |
| **Database / Table** | ClickHouse objects discovered by introspection (`SHOW DATABASES`, `SHOW TABLES`). Read-only. |
| **Introspection** | Reading schema metadata (`SHOW`, `DESCRIBE`, `system.*`) — never modifying it. [clickhouse-integration.md](clickhouse-integration.md) |
| **Table chip** | A draggable sidebar item carrying `db`+`table` in its drag payload. [schema-browser.md](../features/schema-browser.md) |
| **Data Model** | The pinned tab: the one shared canvas of entities + relationships every dashboard builds from. [tabs.md](../features/tabs.md) |
| **Entity / entity card** | A table dropped onto the Data Model canvas, shown as a card of columns with type badges and join-key checkboxes. [canvas.md](../features/canvas.md) |
| **Join key** | A column the user checks to say "this participates in a relationship." Every dragged-in table must select ≥1. |
| **Relationship** | A **logical** link between two entities' join keys — the user's declaration, **not** a database constraint. [relationships.md](../features/relationships.md) |
| **Cardinality** | `1:1`, `1:N`, `N:1`, `N:M`. Intent, not a data guarantee — ClickHouse enforces no uniqueness. |
| **Dashboard** | A tab after the Data Model; each **is one worksheet**. |
| **Worksheet** | Tableau-style view builder: field pane + Columns/Rows shelves + encodings toolbar + one chart or table. [worksheet.md](../features/worksheet.md) |
| **Dimension / measure** | A field that groups (`GROUP BY`) vs. one that is aggregated. Defaults from type; convertible per pill. |
| **Shelf / pill** | A drop zone (Columns, Rows) and a field placed on it. |
| **Encoding** | A Marks channel (Color, Size, Label, Detail, Tooltip, Shape, Path, Angle) mapping a field to a mark property. [worksheet-encodings.md](../features/worksheet-encodings.md) |
| **Workbook** | The whole builder state (Data Model + every dashboard). Auto-saved in the browser per server + user; exportable as a JSON file. Never holds a password. [workbook.md](../features/workbook.md) |
| **Truncated result** | A grouped query that hit its row limit; the worksheet shows a "more exist" notice. |
| **Crosstab** | The Table view: Rows × Columns pivot of measures, built client-side. |
| **MergeTree primary key** | ClickHouse's sort/sparse-index key — **not** a uniqueness constraint and **not** a foreign-key target. |
| **Identifier injection** | The risk of interpolating client-supplied db/table/column names into SQL. Mitigated by validate-against-catalog + backtick-quote. |
| **The shell** | The fixed, non-scrolling full-screen layout (glass sidebar + content area); regions scroll internally. [layout.md](../design/layout.md) |
