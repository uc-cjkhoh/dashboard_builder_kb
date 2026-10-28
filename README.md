# Drag-and-Drop Dashboard Builder for ClickHouse

An ASP.NET Core web app for **visually exploring a ClickHouse server**: connect, browse databases and
tables, **drag tables onto a shared data model**, **draw logical relationships** between them, and
build **Tableau-style worksheets** — one per worksheet tab — that chart data across the related tables, and add dashboard tabs for arranging them.

**Status:** built and running at `https://10.168.49.20:8443/dashboardbuilder`. This directory is the
knowledge base; the source lives at `/unified/user/cj/web_development/prototype/dashboard_builder/`
([development.md](docs/operations/development.md)). Unbuilt work: [docs/backlog/](docs/backlog/README.md).

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
| Connect | validated form (host/port/user), TLS with an explicit self-signed-cert opt-in under Advanced; credentials stay in the server session | [connection.md](docs/features/connection.md) |
| Browse | database picker → searchable, draggable table chips | [schema-browser.md](docs/features/schema-browser.md) |
| Model | entity cards with type badges and join keys | [canvas.md](docs/features/canvas.md) |
| Relate | click-to-click links with 1:1 / 1:N / N:1 / N:M cardinality | [relationships.md](docs/features/relationships.md) |
| Tabs | Data Model tab + any number of worksheet and dashboard tabs (50 in all) | [tabs.md](docs/features/tabs.md) |
| Worksheet | Columns/Rows shelves, automatic cross-table joins, crosstab, sort, format | [worksheet.md](docs/features/worksheet.md) |
| Charts | 23 types incl. heatmap, treemap, histogram, box plot, waterfall, funnel, gauge, bullet, Sankey, small multiples, KPI; PNG/SVG/CSV export | [worksheet-charts.md](docs/features/worksheet-charts.md) |
| Encodings | Marks (Color, Size, Label, Detail, Tooltip, Shape, Path, Angle), Filters, click-to-filter, Drill, Pages | [worksheet-encodings.md](docs/features/worksheet-encodings.md) |
| Workbook | auto-saved in the browser, restored on reconnect, Export/Import as a validated file | [workbook.md](docs/features/workbook.md) |

## Start here

| If you want to… | Read |
|---|---|
| Understand the system and request flow | [ARCHITECTURE.md](ARCHITECTURE.md) |
| Know the rules before changing anything | [CLAUDE.md](CLAUDE.md) → [golden-rules.md](docs/conventions/golden-rules.md) |
| See the visual language | [DESIGN.md](DESIGN.md) |
| Know what the API accepts and returns | [api.md](docs/reference/api.md) (errors, limits) |
| Browse every topic | [docs/README.md](docs/README.md) |
| Build, run, test | [development.md](docs/operations/development.md) |
| Deploy or operate it | [deployment.md](docs/operations/deployment.md) |
| Know why a decision was made | [decisions.md](docs/reference/decisions.md) |

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

- **Not a ClickHouse admin tool.** It reads schema and runs bounded `SELECT`s; it never creates,
  alters, drops or writes anything — and ClickHouse itself enforces that on every query
  ([golden rule 1](docs/conventions/golden-rules.md#1-the-server-is-read-only-against-clickhouse)).
- **Relationships are logical, not enforced.** ClickHouse has no foreign keys; the links you draw are
  declarations the app uses for joins — the database neither creates nor validates them.
- **Not stored on a server.** No application database: your workbook lives in your browser (and in
  files you export), not shared with other users or browsers.
- **Not multi-user.** No accounts, auth, sharing or saved connections; one connection per browser
  session.
- **Not a full BI suite.** No scheduled reports, alerting or arranging worksheets on a dashboard yet — see
  the [backlog](docs/backlog/README.md).
