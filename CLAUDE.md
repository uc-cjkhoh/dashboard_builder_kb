# CLAUDE.md — working conventions

Rules and sharp edges for anyone (human or agent) building the drag-and-drop
dashboard builder. Read [README.md](README.md) and [ARCHITECTURE.md](ARCHITECTURE.md)
first for context. **Nothing is built yet** — when you start coding, follow the layout
in [ARCHITECTURE.md](ARCHITECTURE.md) so the code and this KB stay in agreement, and
**update the relevant doc in the same change** whenever a decision shifts.

## Architecture in one screen

One ASP.NET Core app (Kestrel) serves **a single HTML page** plus a small **read-only
JSON API**. The **browser holds all builder state** — which tables are on the canvas, the
relationships drawn, the open subtabs — in vanilla-JS ES modules (`connection`, `schema`,
`canvas`, `relations`, `tabs`). The **server is a thin, stateless-per-request proxy to
ClickHouse**: it holds the active connection in a **session-scoped `ConnectionRegistry`**,
runs introspection (`SHOW`/`DESCRIBE`) and `SELECT … LIMIT` previews through
`ClickHouseGateway`, and returns JSON. **There is no application database** — ClickHouse is
the only external system; dashboards persist (if at all) as JSON. The request loop:
connect (`SELECT 1` → store) → list databases → list tables → on drop, `DESCRIBE` columns +
preview rows → relate & subtab entirely client-side. Full picture and the API table:
[ARCHITECTURE.md](ARCHITECTURE.md); the two invariants that shape every server change
(read-only, identifier-validation) are the golden rules below.

## Build, run & test — and *where*

> **This KB directory is not where the app is built.** This folder
> (`.../knowledge/web_development/dashboard_builder`) holds docs only. The
> app must be created and compiled on host **`10.168.49.20`**, under
> **`/unified/user/cj/web_development/prototype/dashboard_builder/`** — so `src/DashboardBuilder` lives at
> `/unified/user/cj/web_development/prototype/dashboard_builder/src/DashboardBuilder`. Run every `dotnet`
> command there, from that folder. Do **not** scaffold into this KB. See
> [docs/development.md](docs/development.md).

Once scaffolded (from `src/DashboardBuilder` on the build host):

```bash
dotnet run                       # serve the one page + /api (Kestrel)
dotnet build -c Release
dotnet test                      # full suite
dotnet test --filter Identifier  # a single test/class (e.g. the identifier-safety unit tests)
dotnet publish -c Release -o out # framework-dependent; deploy behind a reverse proxy + systemd
```

- **Prereq:** `.NET SDK 10 (LTS)` (`sudo dnf install -y dotnet-sdk-10.0`).
- **A ClickHouse to point at** for anything past the shell — a throwaway container is
  fastest: `podman run -d --name ch -p 8123:8123 clickhouse/clickhouse-server`.
- **Credentials** (SSH to the build host + ClickHouse login) are in the git-ignored
  [docs/project/credentials.local.md](docs/project/credentials.local.md) — never in shared docs.
- **Highest-value tests** to keep green: the `Identifier` validate/quote helper (feed it
  hostile names) and the ClickHouse-type → display-category mapper. See
  [docs/development.md](docs/development.md).

## Golden rules

1. **The server is read-only against ClickHouse.** Introspection (`SHOW`, `DESCRIBE`,
   `system.*`) and `SELECT … LIMIT` previews only. There is **no DDL/DML endpoint** and
   there must not be one in v1. If a feature seems to need writes, it's out of scope —
   check [README's "what this is NOT"](README.md#what-this-is-not-kills-false-assumptions).

2. **Never interpolate an identifier you haven't validated.** Database, table, and
   column names come from the client and end up inside SQL text — ClickHouse parameters
   bind **values, not identifiers**. Before an identifier reaches a query it must be
   (a) confirmed to exist in the live catalog for that connection, and (b) backtick-quoted
   with internal backticks escaped. Do this in one place (`ClickHouse/Identifier.cs`).
   Details + the failure it prevents: [clickhouse-integration.md](docs/clickhouse-integration.md).

3. **Credentials live in the session and nowhere else.** Never return the password to the
   client, never write it to logs or error messages, never put it in a URL/query string.
   The `ConnectionRegistry` is session-scoped; a new session starts with no connection.

4. **Relationships are logical declarations, not database facts.** ClickHouse enforces no
   foreign keys and no uniqueness — a MergeTree "primary key" is a sparse index, not a
   constraint. The one-to-one / one-to-many links are the *user's* assertions that the app
   uses for joins and layout. Do not imply the DB validated them. See
   [data-model.md](docs/data-model.md).

5. **Toggle visibility with the `hidden` attribute, not `style.display`.** The stylesheet
   sets `[hidden] { display: none !important }` precisely so one switch works everywhere
   (empty states, inline errors, dropzone hints). Setting inline `display` fights it. See
   [DESIGN.md](DESIGN.md#layout-rules).

6. **Use the design tokens — never hardcode a hex.** All color/space/type values are CSS
   custom properties in `site.css` `:root`. `--brand-soft` and `--danger-soft` are the same
   red; **never** use `--brand-soft` for a success cue. See [DESIGN.md](DESIGN.md).

7. **Keep the shell fixed; scroll inside panels.** `html, body { height:100%; overflow:hidden }`.
   The sidebar, the table list, and each entity card scroll internally — the page itself
   never scrolls.

## Common tasks (where things will live)

| Task | Touch |
|---|---|
| Add/adjust a ClickHouse query | `src/DashboardBuilder/ClickHouse/ClickHouseGateway.cs` + [clickhouse-integration.md](docs/clickhouse-integration.md) |
| Add an API endpoint | `src/DashboardBuilder/Endpoints/` + the API table in [ARCHITECTURE.md](ARCHITECTURE.md) |
| Change the connection flow | `ConnectionRegistry.cs`, sidebar JS + [modules.md](docs/app/modules.md) |
| Work on drag/drop or entity cards | `wwwroot/js/canvas.js` + [drag-and-drop.md](docs/drag-and-drop.md) |
| Work on relationships/cardinality | `wwwroot/js/relations.js` + [data-model.md](docs/data-model.md) |
| Add a subtab/dashboard feature | `wwwroot/js/tabs.js` + [modules.md](docs/app/modules.md) |
| Change any color/spacing/typography | `wwwroot/css/site.css` `:root` + [DESIGN.md](DESIGN.md) |

## Sharp edges / gotchas

- **ClickHouse has no foreign keys.** (Rule 4.) Don't reach for `system` FK metadata — it
  doesn't exist. Relationship keys are user-picked columns.
- **Identifiers aren't parameterizable.** (Rule 2.) `SHOW TABLES FROM {db}` and
  `DESCRIBE {db}.{table}` require string interpolation; only *values* (e.g. a `LIMIT` bound,
  a filter value) can use bound parameters.
- **`DESCRIBE` type strings are ClickHouse types, not SQL-92.** Expect `Nullable(...)`,
  `LowCardinality(...)`, `Array(...)`, `Enum8(...)`, `DateTime64(3)`, etc. Map for display;
  don't assume `int/varchar`. See the type-mapping section in
  [clickhouse-integration.md](docs/clickhouse-integration.md).
- **Big tables:** always `LIMIT` previews and never `SELECT *` without a bound — a preview
  must never try to stream a billion-row table into the browser.
- **Two connections, same server, different databases** is normal; scope every query to the
  connection + database the request names, not a global default.
- **Status is icon + text + color, never color alone** (accessibility). Applies to the
  connection state pill and any dashboard status. See [DESIGN.md](DESIGN.md#accessibility-posture).

## Definition of done for a change

- Read-only invariant intact; no credential leak; identifiers validated + quoted.
- Visibility via `hidden`; colors via tokens; shell doesn't scroll.
- The KB doc that describes the touched area is updated in the same change.
- If you changed a decision, record it in [docs/project/decisions.md](docs/project/decisions.md).
