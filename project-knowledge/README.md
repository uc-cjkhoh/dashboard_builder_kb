# Drag-and-Drop Dashboard Builder for ClickHouse

An ASP.NET Core web app for **visually exploring a ClickHouse server**. You connect, browse databases
and tables, **drag tables onto a shared data source** and **draw logical relationships** between them.
You then build **Tableau-style worksheets**, one per worksheet tab, that chart data across the related
tables, and add dashboard tabs to arrange them. Read this page first for what the app does and where
to go next.

**Status:** built and running at `https://10.168.49.20:8443/dashboardbuilder`. This directory is the
knowledge base. The source lives at `/unified/user/cj/web_development/prototype/dashboard_builder/`
([development.md](operations/development.md)). Unbuilt work: [backlog/](backlog/README.md).

## Project statement

1. One-page web app with a **left-side panel** to add a connection to a ClickHouse server.
2. When connected, show a **dropdown of the available databases**.
3. After a database is selected, list its **tables**.
4. **Drag a table** onto the right-hand panel to display it in an **entity view**.
5. Create **new worksheet and dashboard tabs** and build from the dragged tables.
6. Every dragged table must have **one or more columns selected** to define relationships between
   tables (one-to-one, one-to-many, …).

## What you can do

| Area | Capability | Doc |
|---|---|---|
| Connect | validated form (host/port/user), TLS with an explicit self-signed-cert opt-in under Advanced; credentials stay in the server session | [connection.md](features/data-source/connection.md) |
| Browse | database picker → searchable, draggable table chips | [schema-browser.md](features/data-source/schema-browser.md) |
| Model | entity cards with type badges | [canvas.md](features/data-source/canvas.md) |
| Union / unpivot | stack 2–5 tables, or turn wide columns into rows, and use the result like a table | [query-sources.md](features/data-source/query-sources.md) |
| Relate | drag-to-relate links with 1:1 / 1:N / N:1 / N:M cardinality | [relationships.md](features/data-source/relationships.md) |
| Tabs | Data Source tab + any number of worksheet and dashboard tabs (50 in all) | [tabs.md](features/workbook/tabs.md) |
| Worksheet | Columns/Rows shelves, automatic cross-table joins, crosstab, sort, format | [worksheet.md](features/worksheet/worksheet.md) |
| Charts | 23 types incl. heatmap, treemap, histogram, box plot, waterfall, funnel, gauge, bullet, Sankey, small multiples, KPI; PNG/SVG/CSV export | [worksheet-charts.md](features/worksheet/worksheet-charts.md) |
| Encodings | Marks (Color, Size, Label, Detail, Tooltip, Shape, Path, Angle), Filters, click-to-filter, Drill, Pages | [worksheet-encodings.md](features/worksheet/worksheet-encodings.md) |
| Calculations | named formulas (aggregates, logic, text and date functions, parameters, groups) used like fields | [calculated-fields.md](features/worksheet/calculated-fields.md) |
| Dashboards | arrange worksheets, text, images, navigation buttons and spacers on a 12-column grid | [dashboards.md](features/workbook/dashboards.md) |
| Workbook | auto-saved in the browser, restored on reconnect, Export/Import as a validated file | [workbook.md](features/workbook/workbook.md) |

## Start here

| If you want to… | Read |
|---|---|
| Understand the system and request flow | [ARCHITECTURE.md](ARCHITECTURE.md) |
| Know the rules before changing anything | [CLAUDE.md](../CLAUDE.md) → [golden-rules.md](engineering/golden-rules.md) |
| See the visual language | [design/overview.md](design/overview.md) |
| Know what the API accepts and returns | [api.md](reference/api.md) (errors, limits) |
| Browse every topic | [index.md](index.md) |
| Build, run, test | [development.md](operations/development.md) |
| Deploy or operate it | [deployment.md](operations/deployment.md) |
| Know why a decision was made | [decisions.md](reference/decisions/decisions.md) |

## Tech stack

| Layer | Choice |
|---|---|
| Runtime | .NET 10 LTS on AlmaLinux 9 |
| Web | ASP.NET Core MVC in **feature folders** — one Shell page + attribute-routed JSON API controllers |
| Frontend | vanilla JS ES modules + hand-written CSS with design tokens (Flat 2.0 + glass chrome, crimson accent, light/dark: System / Light / Dark toggle); no framework, no build step |
| Charts | Apache ECharts, self-hosted (SVG renderer) |
| ClickHouse driver | `ClickHouse.Client` (ADO.NET over HTTPS, port `8443`) |
| Hosting | Kestrel under systemd, behind Apache httpd TLS at path `/dashboardbuilder` |
| Persistence | browser only — the workbook auto-saves to `localStorage`; no server database |

## What this is not

- **Not a ClickHouse admin tool.** It reads schema and runs bounded `SELECT`s. It never creates,
  alters, drops or writes anything, and ClickHouse itself enforces that on every query
  ([golden rule 1](engineering/golden-rules.md#1-the-server-is-read-only-against-clickhouse)).
- **Relationships are logical, not enforced.** ClickHouse has no foreign keys. The links you draw are
  declarations the app uses for joins; the database neither creates nor validates them.
- **Not stored on a server.** There is no application database. Your workbook lives in your browser
  and in files you export; it is not shared with other users or browsers.
- **Not multi-user.** No accounts, auth, sharing or saved connections; one connection per browser
  session.
- **Not a full BI suite.** No scheduled reports or alerting — see the [backlog](backlog/README.md).
