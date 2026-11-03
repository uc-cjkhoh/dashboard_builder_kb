---
components: []
---
# Glossary

Domain terms as used in this project. Read it when a word in the other docs is ambiguous; where a term
has a subtle or non-obvious meaning here, that is called out.

| Term | Meaning in this project |
|---|---|
| **Connection** | The session's ClickHouse connection (host/port/user/password/TLS) held on the server; credentials never leave it. [connection.md](../concepts/data-source/connection.md) |
| **Database / Table** | ClickHouse objects discovered by introspection (`SHOW DATABASES`, `SHOW TABLES`). Read-only. |
| **Introspection** | Reading schema metadata (`SHOW`, `DESCRIBE`, `system.*`) — never modifying it. [clickhouse-integration.md](clickhouse-integration.md) |
| **Table chip** | A draggable sidebar item carrying `db` + `table` in its drag payload. [schema-browser.md](../concepts/data-source/schema-browser.md) |
| **Data Source** | The pinned tab: the one shared canvas of entities + relationships every worksheet builds from. [tabs.md](../concepts/workbook/tabs.md) |
| **Entity / entity card** | A table dropped onto the Data Source canvas, shown as a card of columns with type badges. [canvas.md](../concepts/data-source/canvas.md) |
| **Join key** | A column a relationship uses. Made by dragging it onto a column of another table; pinned to the card's key strip. |
| **Relationship** | A **logical** link between a column of one entity and a column of another — the user's declaration, **not** a database constraint. [relationships.md](../concepts/data-source/relationships.md) |
| **Cardinality** | `1:1`, `1:N`, `N:1`, `N:M`. Intent, not a data guarantee — ClickHouse enforces no uniqueness. |
| **Worksheet** | A tab after the Data Source holding one Tableau-style chart or table. It is the view builder: field pane + Columns/Rows shelves + encodings toolbar + one chart or table. [worksheet.md](../concepts/worksheet/worksheet.md) |
| **Dashboard** | A tab that composes worksheets and text on a grid. [tabs.md](../concepts/workbook/tabs.md) |
| **Dimension / measure** | A field that groups (`GROUP BY`) vs. one that is aggregated. The default comes from the column type; each pill can be switched. |
| **Shelf / pill** | A drop zone (Columns, Rows) and a field placed on it. |
| **Encoding** | A Marks channel (Color, Size, Label, Detail, Tooltip, Shape, Path, Angle) mapping a field to a mark property. [worksheet-encodings.md](../concepts/worksheet/worksheet-encodings.md) |
| **Workbook** | The whole builder state (Data Source + every worksheet and dashboard). Auto-saved in the browser per server + user; exportable as a JSON file. Never holds a password. [workbook.md](../concepts/workbook/workbook.md) |
| **Truncated result** | A grouped query that hit its row limit; the worksheet shows a "more exist" notice. |
| **Crosstab** | The Table view: Rows × Columns pivot of measures, built client-side. |
| **MergeTree primary key** | ClickHouse's sort/sparse-index key — **not** a uniqueness constraint and **not** a foreign-key target. |
| **Identifier injection** | The risk of interpolating client-supplied db/table/column names into SQL. Mitigated by validating every name against the live catalog, then backtick-quoting it. |
| **The shell** | The fixed, non-scrolling full-screen layout (glass sidebar + content area); regions scroll internally. [layout.md](design/layout.md) |
