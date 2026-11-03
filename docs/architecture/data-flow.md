---
components: []
---
# Data flow

How one request moves from connect to render and persistence, step by step. Read it to know which layer owns which check.

1. **Connect.** The sidebar form posts host, port, user, password, TLS and the cert opt-in. The server
   builds a `ClickHouse.Client` connection, validates it with `SELECT 1`, and stores it in the
   session's `ConnectionRegistry`. Credentials never return to the client and are never logged.
   → [connection.md](../concepts/data-source/connection.md)
2. **Browse.** List databases, then a database's tables. The database name is validated before it is
   quoted into SQL. Tables render as draggable chips. → [schema-browser.md](../concepts/data-source/schema-browser.md)
3. **Model.** Dropping a chip fetches the table's columns (`DESCRIBE`, type-categorised) and renders an
   entity card. Dragging one column onto another declares a relationship with a cardinality. This
   happens entirely client-side. → [canvas.md](../concepts/data-source/canvas.md), [relationships.md](../concepts/data-source/relationships.md)
4. **Build a worksheet.** On a worksheet tab, fields dragged onto shelves and encodings become one plan:
   dimensions, measures, filters, sort, limit. The client resolves a **join path** over the drawn
   relationships. → [worksheet.md](../concepts/worksheet/worksheet.md)
5. **Query.** Unless the result is already cached for this worksheet, the client sends the plan and
   aborts any query it supersedes. The server then:
   1. validates the request's shape and limits, rejecting out-of-range input rather than clamping it;
   2. validates every table and column against the catalog and quotes them;
   3. converts and binds every value by its column's type;
   4. applies the limit, plus one probe row to detect truncation;
   5. builds the `JOIN`s and runs one bounded `GROUP BY` under ClickHouse's `readonly=2` and a 12 s
      time limit.

   Histogram and box plot use their own single-table endpoints.
   → [worksheet-query.md § Query lifecycle](../concepts/worksheet/worksheet-query.md#query-lifecycle),
   [clickhouse-integration.md](../reference/clickhouse-integration.md)
6. **Render.** The client pivots the flat result into a crosstab or hands it to the ECharts adapter.
   Clicks feed back into the plan as bound filters (click-to-filter, drill, pages).
   → [worksheet-charts.md](../concepts/worksheet/worksheet-charts.md), [worksheet-encodings.md](../concepts/worksheet/worksheet-encodings.md)
7. **Persist.** Every change auto-saves the workbook to the browser; reconnecting restores it.
   → [workbook.md](../concepts/workbook/workbook.md)

Every endpoint and status code: [api.md](../reference/api.md). State shapes:
[data-model.md](../reference/data-model.md).
