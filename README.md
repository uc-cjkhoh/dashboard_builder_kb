# Drag-and-Drop Dashboard Builder for ClickHouse

An ASP.NET Core web app for **visually exploring a ClickHouse server**. You connect, browse databases
and tables, **drag tables onto a shared data source** and **draw logical relationships** between them.
You then build **Tableau-style worksheets**, one per worksheet tab, that chart data across the related
tables, and add dashboard tabs to arrange them. Read this page first for what the app does and where
to go next. The knowledge base is the [`docs/`](docs/README.md) folder; agents start at [CLAUDE.md](CLAUDE.md).

**Status:** built and running at `https://10.168.49.20:8443/dashboardbuilder`. This repository is docs only. The source lives at `/unified/user/cj/web_development/prototype/dashboard_builder/`
([quickstart.md](docs/getting-started/quickstart.md)). Unbuilt work: [backlog/](docs/development/backlog/index.md).

## Project statement

1. One-page web app with a **left-side panel** to add a connection to a ClickHouse server.
2. When connected, show a **dropdown of the available databases**.
3. After a database is selected, list its **tables**.
4. **Drag a table** onto the right-hand panel to display it in an **entity view**.
5. Create **new worksheet and dashboard tabs** and build from the dragged tables.
6. Every dragged table must have **one or more columns selected** to define relationships between
   tables (one-to-one, one-to-many, …).

## Start here

| If you want to… | Read |
|---|---|
| Understand the system and request flow | [architecture/overview.md](docs/architecture/overview.md) |
| Know the rules before changing anything | [CLAUDE.md](CLAUDE.md) → [coding-standards.md](docs/development/coding-standards.md) |
| What the app can do | [concepts/core-concepts.md](docs/concepts/core-concepts.md) |
| See the visual language | [reference/design/index.md](docs/reference/design/index.md) |
| Know what the API accepts and returns | [reference/api.md](docs/reference/api.md) (errors, limits) |
| Browse every topic | [docs/README.md](docs/README.md) |
| Build, run, test | [getting-started/quickstart.md](docs/getting-started/quickstart.md) |
| Deploy or operate it | [how-to/deployment.md](docs/how-to/deployment.md) · [operations/live-service.md](docs/operations/live-service.md) |
| Know why a decision was made | [decisions/README.md](docs/decisions/README.md) |
