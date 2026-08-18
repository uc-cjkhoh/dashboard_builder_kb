# Drag-and-Drop Dashboard Builder with ClickHouse

An ASP.NET Core web app for **visually exploring a ClickHouse server**: connect to
a server, browse its databases and tables, **drag tables onto a canvas** to inspect
them as entities, **draw logical relationships** between them (one-to-one,
one-to-many, …), and organize the result into **dashboard subtabs**.

> **Status: design / specification only — no code exists yet.**
> This directory is currently a *knowledge base*, not an implementation. Every doc
> here describes the **intended** system so that the build starts from a shared,
> deliberate design. See [BUILD_PLAN.md](BUILD_PLAN.md) for the phased path from
> here to a running app.

## Project statement

Build a single-page, drag-and-drop dashboard builder for ASP.NET Core that connects
to ClickHouse:

1. One-page web app with a **left-side panel** to add a connection to a ClickHouse server.
2. When a connection is established, show a **dropdown of the available databases**.
3. After a database is selected, list its **tables**.
4. The user can **drag a table** onto the right-hand panel and drop it to display the
   table in an **entity view**.
5. The user can create **new subtabs** and build a dashboard from the dragged tables.
6. Every dragged table must have **one or more columns selected** to define
   relationships between tables (one-to-one, one-to-many, …).

## Start here

| If you want to… | Read |
|---|---|
| Understand the whole system & how a request flows | [ARCHITECTURE.md](ARCHITECTURE.md) |
| Know the rules/conventions before writing code | [CLAUDE.md](CLAUDE.md) |
| See the visual language (tokens, components) | [DESIGN.md](DESIGN.md) |
| Follow the plan from zero to running app | [BUILD_PLAN.md](BUILD_PLAN.md) |
| Browse every topic doc | [docs/README.md](docs/README.md) |
| Understand the screens/panels | [docs/app/modules.md](docs/app/modules.md) |
| Talk to ClickHouse from .NET | [docs/clickhouse-integration.md](docs/clickhouse-integration.md) |
| Model connections, entities, relationships | [docs/data-model.md](docs/data-model.md) |
| Understand the drag/drop & relationship UX | [docs/drag-and-drop.md](docs/drag-and-drop.md) |
| Know why a decision was made | [docs/project/decisions.md](docs/project/decisions.md) |

## Tech stack (intended)

| Layer | Choice | Notes |
|---|---|---|
| Runtime | **.NET 10 LTS** | AlmaLinux 9 appstream / Microsoft feed |
| Web framework | **ASP.NET Core**, Razor Pages + minimal API endpoints | single served page + JSON API |
| Language | **C#** (backend), **vanilla JS + plain CSS** (frontend) | no SPA framework — see [decisions](docs/project/decisions.md) |
| ClickHouse driver | **`ClickHouse.Client`** (ADO.NET, HTTP interface) | **TLS-only: HTTPS `8443`** (native TLS `9440` unused); plaintext `8123`/`9000` not available |
| Host OS | **AlmaLinux 9** | Kestrel behind a reverse proxy (Apache httpd, TLS on 443) + systemd; served under a path prefix. See [O5](docs/project/decisions.md) / [development.md](docs/development.md) |

See [ARCHITECTURE.md](ARCHITECTURE.md) for the full rationale and the alternatives
that were considered.

## What this is NOT (kills false assumptions)

- **Not implemented.** There is no `.csproj`, no `wwwroot/`, no C# yet. Docs describe intent.
- **Not a BI/reporting product.** No scheduled reports, no export pipeline, no alerting.
  It is an *interactive explorer + dashboard canvas*.
- **Not a ClickHouse admin tool.** It reads schema and samples data; it does not
  create/alter/drop tables or manage users, quotas, or clusters.
- **Relationships are logical, not enforced.** ClickHouse has **no foreign keys**;
  the one-to-one / one-to-many links the user draws are *declarations the app uses*
  for joins and dashboards — the database neither creates nor validates them. This is
  central; see [data-model.md](docs/data-model.md).
- **Multi-tenant / auth is out of scope for v1.** Connection credentials live in the
  user's session; there is no user database. See [decisions](docs/project/decisions.md).

## Environment

- **AlmaLinux 9.** Install the .NET SDK from the AlmaLinux appstream or Microsoft's
  package feed; run under Kestrel. See [docs/development.md](docs/development.md).
- **Build host & location (required):** the project must be built on
  **`10.168.49.20`**, under **`/unified/user/cj/web_development/prototype/dashboard_builder/`** — this is
  where `src/DashboardBuilder` and the app are created/compiled. See
  [docs/development.md](docs/development.md).
