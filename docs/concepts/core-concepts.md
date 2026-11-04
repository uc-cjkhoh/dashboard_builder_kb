---
components: []
---
# Core concepts

What a user can do in the app, and which doc describes each capability.

| Area | Capability | Doc |
|---|---|---|
| Connect | validated form (host/port/user), TLS, with self-signed certificates trusted by default (untick under Advanced to verify); credentials stay in the server session | [connection.md](data-source/connection.md) |
| Browse | database picker → searchable, draggable table chips | [schema-browser.md](data-source/schema-browser.md) |
| Model | entity cards with type badges | [canvas.md](data-source/canvas.md) |
| Union / unpivot | stack 2–5 tables, or turn wide columns into rows, and use the result like a table | [query-sources.md](data-source/query-sources.md) |
| Relate | drag-to-relate links with 1:1 / 1:N / N:1 / N:M cardinality | [relationships.md](data-source/relationships.md) |
| Tabs | Data Source tab + any number of worksheet and dashboard tabs (50 in all) | [tabs.md](workbook/tabs.md) |
| Worksheet | Columns/Rows shelves, automatic cross-table joins, crosstab, sort, format | [worksheet.md](worksheet/worksheet.md) |
| Charts | 23 types incl. heatmap, treemap, histogram, box plot, waterfall, funnel, gauge, bullet, Sankey, small multiples, KPI; PNG/SVG/CSV export | [worksheet-charts.md](worksheet/worksheet-charts.md) |
| Encodings | Marks (Color, Size, Label, Detail, Tooltip, Shape, Path, Angle), Filters, click-to-filter, Drill, Pages | [worksheet-encodings.md](worksheet/worksheet-encodings.md) |
| Calculations | named formulas (aggregates, logic, text and date functions, parameters, groups) used like fields | [calculated-fields.md](worksheet/calculated-fields.md) |
| Dashboards | arrange worksheets, text, images, navigation buttons and spacers on a 12-column grid | [dashboards.md](workbook/dashboards.md) |
| Workbook | auto-saved in the browser, restored on reconnect, Export/Import as a validated file | [workbook.md](workbook/workbook.md) |
