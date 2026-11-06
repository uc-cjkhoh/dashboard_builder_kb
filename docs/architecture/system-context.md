---
components: []
---
# System context

The stack the app runs on and the boundaries of what it does.

## Tech stack

| Layer | Choice |
|---|---|
| Runtime | .NET 10 LTS on AlmaLinux 9 |
| Web | ASP.NET Core MVC in **feature folders** — one Shell page + attribute-routed JSON API controllers |
| Frontend | vanilla JS ES modules + hand-written CSS with design tokens (Flat 2.0 + glass chrome, Signal accent (near-black / neon lime), light/dark: System / Light / Dark toggle); no framework, no build step |
| Charts | Apache ECharts, self-hosted (SVG renderer) |
| ClickHouse driver | `ClickHouse.Client` (ADO.NET over HTTPS, port `8443`) |
| Hosting | Kestrel under systemd, behind Apache httpd TLS at path `/dashboardbuilder` |
| Persistence | browser only — the workbook auto-saves to `localStorage`; no server database |

## What this is not

- **Not a ClickHouse admin tool.** It reads schema and runs bounded `SELECT`s. It never creates,
  alters, drops or writes anything, and ClickHouse itself enforces that on every query
  ([golden rule 1](../development/coding-standards.md#1-the-server-is-read-only-against-clickhouse)).
- **Relationships are logical, not enforced.** ClickHouse has no foreign keys. The links you draw are
  declarations the app uses for joins; the database neither creates nor validates them.
- **Not stored on a server.** There is no application database. Your workbook lives in your browser
  and in files you export; it is not shared with other users or browsers.
- **Not multi-user.** No accounts, auth, sharing or saved connections; one connection per browser
  session.
- **Not a full BI suite.** No scheduled reports or alerting — see the [backlog](../development/backlog/index.md).
