# Architecture

How the drag-and-drop dashboard builder is put together — the intended tech stack,
the request/data flow, the API surface, and the directory map. This is a **planned**
architecture (nothing is built yet); it is the contract the [build plan](BUILD_PLAN.md)
implements.

## Shape in one paragraph

A single ASP.NET Core app serves **one HTML page** plus a small **JSON API**. The
browser holds all *builder* state (which tables are on the canvas, the relationships
drawn, the open subtabs). The server is a **thin, stateless-per-request proxy to
ClickHouse**: it holds the active connection for the session, runs read-only
introspection and preview queries, and returns JSON. There is **no application
database** in v1 — ClickHouse is the only external system, and dashboards persist
(if at all) as JSON. See [decisions](docs/project/decisions.md) for why.

```
Browser (one page, vanilla JS)                 ASP.NET Core (Kestrel)              ClickHouse
┌───────────────────────────┐   fetch JSON   ┌──────────────────────────┐  ADO.NET  ┌──────────┐
│ Sidebar: connection form  │ ─────────────▶ │ /api/connection  (POST)  │ ────────▶ │  HTTPS    │
│  db dropdown, table list  │                │ /api/databases   (GET)   │  SHOW/    │  8443 TLS │
│ Canvas: entity cards,     │ ◀───────────── │ /api/.../tables  (GET)   │  DESCRIBE │ (secure   │
│  relationship links, tabs │    JSON        │ /api/.../columns (GET)   │  SELECT   │  only)    │
└───────────────────────────┘                │ /api/.../preview (GET)   │ ◀──────── └──────────┘
      builder state lives here               │ ConnectionRegistry (session-scoped)  │
                                             └──────────────────────────┘
```

## Tech stack & why

| Concern | Choice | Rationale (short) |
|---|---|---|
| Runtime | .NET 10 LTS | Current LTS (released Nov 2025), on AlmaLinux 9 appstream / Microsoft feed. |
| Web | ASP.NET Core, Razor Pages for the shell + minimal-API endpoints for JSON | One served page; the API is a handful of read endpoints — minimal API keeps it terse. |
| Frontend | Vanilla JS (ES modules) + hand-written CSS with design tokens | The UI is bespoke (drag/drop canvas, relationship links); an SPA framework adds weight without clear payoff for one page. See [decisions](docs/project/decisions.md). |
| ClickHouse | `ClickHouse.Client` (ADO.NET provider over the HTTP interface) | Mainstream, actively maintained .NET driver; `DbConnection`/`DbCommand` semantics. Target server is **TLS-only: HTTPS on `8443`** (native TLS `9440` unused; plaintext `8123`/`9000` unavailable). |
| Drag & drop | Native HTML5 Drag and Drop API | No dependency; table chips are `draggable`, the canvas is the drop target. See [drag-and-drop.md](docs/drag-and-drop.md). |
| Persistence | None in v1 (session + browser memory); optional JSON file/store later | No user DB needed to satisfy the statement; keeps the security surface tiny. |

Considered-and-rejected (Blazor Server, a React/TS SPA, EF Core + app DB, native TCP
protocol) are recorded with reasons in [docs/project/decisions.md](docs/project/decisions.md).

## Request / data flow

1. **Connect.** Sidebar form → `POST /api/connection` with host, port (`8443`), user,
   password, `secure` flag (on — the server is TLS-only, HTTPS `8443` / native TLS `9440`).
   The server builds a `ClickHouse.Client` connection string, opens a
   connection to validate it (`SELECT 1`), and stores it in a **session-scoped
   `ConnectionRegistry`**. Credentials are never returned to the client and never logged.
2. **Browse databases.** `GET /api/databases` → `SHOW DATABASES` → JSON array → dropdown.
3. **Browse tables.** `GET /api/databases/{db}/tables` → `SHOW TABLES FROM {db}` → list of
   draggable table chips.
4. **Inspect columns.** On drop (or on demand) `GET /api/databases/{db}/tables/{table}/columns`
   → `DESCRIBE TABLE {db}.{table}` (or `system.columns`) → column name + type list, used to
   render the entity card and to offer join-key checkboxes.
5. **Preview rows.** `GET /api/databases/{db}/tables/{table}/preview?limit=50` →
   `SELECT * FROM {db}.{table} LIMIT {n}` → sample rows for the entity view's data grid.
6. **Build relationships & tabs.** Entirely client-side: the user checks join columns on
   two entity cards and picks a cardinality; the app draws a link. Subtabs are DOM the
   client manages. No server round-trip unless/until dashboards are persisted.

See [docs/clickhouse-integration.md](docs/clickhouse-integration.md) for the exact SQL,
type mapping, and the **identifier-injection** rules that govern steps 3–5 (db/table/column
names are interpolated, not parameterizable — they must be validated against the live
catalog and backtick-quoted).

## API surface (intended)

| Method & path | Purpose | ClickHouse it runs |
|---|---|---|
| `POST /api/connection` | Establish/validate & store the session connection | `SELECT 1` |
| `GET /api/connection` | Current session connection status (password-free) | — |
| `DELETE /api/connection` | Drop the session connection | — |
| `GET /api/databases` | List databases | `SHOW DATABASES` |
| `GET /api/databases/{db}/tables` | List tables in a database | `SHOW TABLES FROM {db}` |
| `GET /api/databases/{db}/tables/{table}/columns` | Column names + types | `DESCRIBE TABLE {db}.{table}` |
| `GET /api/databases/{db}/tables/{table}/preview?limit=` | Sample rows for entity view / grid widget | `SELECT * … LIMIT n` |
| `GET /api/databases/{db}/tables/{table}/count` | Row count for a KPI widget | `SELECT count() …` |
| `POST /api/databases/{db}/tables/{table}/aggregate` | Single-table chart data | `SELECT dim, agg(m) … [WHERE …] GROUP BY … LIMIT n` |
| `POST /api/query` | Worksheet chart data across **joined** tables | `SELECT dim, agg(m) FROM t0 [JOIN t1 ON …] [WHERE …] GROUP BY … LIMIT n` |

All endpoints are **read-only** against ClickHouse. There are deliberately no
write/DDL endpoints (see [what-it-is-NOT](README.md#what-this-is-not-kills-false-assumptions)).

## Directory map (target, once scaffolded)

> Nothing below exists yet — this is the layout the build plan will create so docs and
> code agree from day one.

```
drag_and_drop_dashboard_builder/
├── src/
│   └── DashboardBuilder/                 # the ASP.NET Core project
│       ├── DashboardBuilder.csproj
│       ├── Program.cs                    # host + minimal-API endpoint mapping
│       ├── Endpoints/                    # connection / schema / preview handlers
│       ├── ClickHouse/
│       │   ├── ConnectionRegistry.cs     # session-scoped connection store
│       │   ├── ClickHouseGateway.cs      # runs the introspection/preview queries
│       │   └── Identifier.cs             # validate + backtick-quote identifiers
│       ├── Pages/                        # Razor: Index.cshtml (the one page)
│       └── wwwroot/
│           ├── css/site.css              # design tokens + components (see DESIGN.md)
│           └── js/                       # ES modules: api, ui, store, sidebar, connection, schema, canvas, relations, tabs, dashboards
├── README.md  CLAUDE.md  ARCHITECTURE.md  DESIGN.md  BUILD_PLAN.md
└── docs/…                                # this knowledge base
```

The `wwwroot/css/site.css` `:root` token block referenced throughout [DESIGN.md](DESIGN.md)
is created in the design-system phase of the [build plan](BUILD_PLAN.md).

## Cross-cutting concerns

- **Security** — credential handling, identifier injection, read-only posture, TLS to
  ClickHouse: see [CLAUDE.md](CLAUDE.md) golden rules and
  [clickhouse-integration.md](docs/clickhouse-integration.md).
- **State & persistence** — where builder state lives and the persistence decision:
  [data-model.md](docs/data-model.md).
- **Design system** — tokens, layout rules, component vocabulary: [DESIGN.md](DESIGN.md).
- **Running it** — SDK install, `dotnet run`, a throwaway ClickHouse for testing:
  [docs/development.md](docs/development.md).
- **Hosting / deployment** — Kestrel behind a reverse proxy (Apache httpd, TLS on `443`),
  served either at the site root or under a **path prefix**. The app is `PathBase`-aware
  (config key `PathBase`) and the client derives the same prefix from its module URL, so the
  API keeps working under a subpath. As deployed on `10.168.49.20`: Apache proxies
  `/dashboardbuilder` → `127.0.0.1:5006`. See [O5](docs/project/decisions.md) and
  [docs/development.md](docs/development.md#as-deployed-on-the-build-host-101684920).
