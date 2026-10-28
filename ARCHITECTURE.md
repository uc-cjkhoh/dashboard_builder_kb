# Architecture

How the Dashboard Builder is put together — the shape, the request/data flow, and where each piece of
code lives. High level only: SQL, endpoints and state shapes are in the [`docs/reference/`](docs/README.md)
files linked below.

## Shape in one paragraph

A single ASP.NET Core MVC app serves **one HTML page** plus a small **read-only JSON API**. The
**browser holds all builder state**: the one shared data model (tables dragged onto the canvas + the
relationships drawn between them) and one worksheet per dashboard tab. The **server is a thin,
session-scoped proxy to ClickHouse**: it keeps the session's connection, validates every identifier
against the live catalog, runs introspection and bounded aggregate/join queries, and returns JSON.
**There is no application database** — ClickHouse is the only external system
([D2](docs/reference/decisions.md#d2--thin-session-scoped-proxy-no-application-database)); the builder
state auto-saves as a **workbook** in the browser
([D21](docs/reference/decisions.md#d21--workbooks-persist-in-the-browser-not-on-the-server)).

```
Browser — one page, vanilla JS ES modules          ASP.NET Core MVC (Kestrel)               ClickHouse
┌──────────────────────────────────────┐  JSON   ┌───────────────────────────────┐  HTTPS  ┌──────────┐
│ Sidebar: connection · db · tables    │ ──────▶ │ Connection / Schema / Query   │ ──────▶ │ 8443 TLS │
│ Data Model: entities + relationships │         │   API controllers             │  SHOW   │ read-only│
│ Dashboards: one worksheet each       │ ◀────── │ ClickHouseGateway + Identifier│ DESCRIBE│          │
│   (field pane · shelves · chart)     │         │ ConnectionRegistry (session)  │ SELECT  │          │
└──────────────────────────────────────┘         └───────────────────────────────┘ ◀────── └──────────┘
   all builder state lives here                    holds only the session connection
```

In production Apache httpd terminates TLS and proxies `/dashboardbuilder` to Kestrel
([deployment.md](docs/operations/deployment.md)).

## Request / data flow

1. **Connect.** The sidebar form posts host, port, user, password, TLS and the cert opt-in. The server
   builds a `ClickHouse.Client` connection, validates it with `SELECT 1`, and stores it in the
   session's `ConnectionRegistry`. Credentials never return to the client and are never logged.
   → [connection.md](docs/features/connection.md)
2. **Browse.** List databases, then a database's tables (the database name is validated before it is
   quoted into SQL); tables render as draggable chips. → [schema-browser.md](docs/features/schema-browser.md)
3. **Model.** Dropping a chip fetches the table's columns (`DESCRIBE`, type-categorised) and renders an
   entity card. Ticking join keys and linking them declares a relationship with a cardinality —
   entirely client-side. → [canvas.md](docs/features/canvas.md), [relationships.md](docs/features/relationships.md)
4. **Build a worksheet.** On a dashboard tab, fields dragged onto shelves and encodings become one plan:
   dimensions, measures, filters, sort, limit. The client resolves a **join path** over the drawn
   relationships. → [worksheet.md](docs/features/worksheet.md)
5. **Query.** Unless the result is already cached for this dashboard, the client sends the plan
   (aborting any query it supersedes). The server first validates the request's shape and limits
   (rejecting, never clamping), then every table and column against the catalog, quotes them, converts
   and binds every value by its column's type, applies the limit (+1 probe row to detect truncation), builds the
   `JOIN`s, and runs one bounded `GROUP BY` under ClickHouse's `readonly=2` and a 12 s time limit.
   Histogram and box plot use their own single-table endpoints.
   → [worksheet.md § Query lifecycle](docs/features/worksheet.md#query-lifecycle),
   [clickhouse-integration.md](docs/reference/clickhouse-integration.md)
6. **Render.** The client pivots the flat result into a crosstab or hands it to the ECharts adapter;
   clicks feed back into the plan as bound filters (click-to-filter, drill, pages).
7. **Persist.** Every change auto-saves the workbook to the browser; reconnecting restores it.
   → [workbook.md](docs/features/workbook.md)
   → [worksheet-charts.md](docs/features/worksheet-charts.md), [worksheet-encodings.md](docs/features/worksheet-encodings.md)

Every endpoint and status code: [api.md](docs/reference/api.md). State shapes:
[data-model.md](docs/reference/data-model.md).

## Code map

The app is **MVC in feature folders** ([D19](docs/reference/decisions.md#d19--mvc-in-feature-folders)):
each feature owns its controller, view partial, CSS and JS in one folder. Source root:
`/unified/user/cj/web_development/prototype/dashboard_builder/src/DashboardBuilder/`.

| Path | Role |
|---|---|
| `Program.cs` | host, session (in-memory, 2h idle), persisted Data Protection keys, `PathBase`, `no-cache` static files, the `/features` asset provider, controllers |
| `ClickHouse/ClickHouseGateway.cs` | every SQL statement; the pure query builders |
| `ClickHouse/RequestValidation.cs` | `ApiLimits`, `RequestRules` (every input rule), `FilterValues` (typed filter values) |
| `ClickHouse/Identifier.cs` | validate-against-catalog + backtick-quote |
| `ClickHouse/ClickHouseType.cs`, `CsvUtil.cs` | type → display category; safe CSV |
| `ClickHouse/ConnectionRegistry.cs`, `*Models.cs` | session connection store; request/response records |
| `Features/ApiControllerBase.cs`, `ApiErrors.cs` | shared `[ApiController]` base — `RunAsync` maps 409 / 400 / 502 / 504 / 500; the one `{ error, field? }` body, body-size limit, exception handler |
| `Features/Shell/` | `ShellController` (`GET /`), `Index.cshtml` composing the partials, `app.js` bootstrap, `sidebar.js`, `scheme-toggle.js` |
| `Features/Core/` | `core.css` (tokens + shared components), `api.js`, `ui.js`, `validate.js`, `icons.js`, `menu.js`, `store.js`, `format.js`, `sheet-schema.js`, vendored ECharts |
| `Features/Connection/`, `Schema/` | sidebar features, each with its API controller |
| `Features/Canvas/`, `Relations/`, `Tabs/` | client-only features (no controller); pure rule modules `empty-state.js`, `relation-rules.js` |
| `Features/Dashboard/` | the worksheet editor (`dashboards.js`), the instantiable query-and-render lifecycle (`worksheet-view.js`), the drawing of a result (`worksheet-render.js` + `render-*.js`, no editor state), the pure query plan (`sheet-plan.js`) and result shaping (`result-model.js`), pure rules (`filter-rules.js`, `toolbar-rules.js`, `contrast.js`), query gate + cache (`query-runner.js`), ECharts adapter (`chart.js`), `QueryController` |
| `Features/Workbook/` | auto-save, restore, Export/Import (`workbook.js`) + the file format and its validation (`workbook-model.js`) |
| `tests/DashboardBuilder.Tests/`, `tests/js/` | xUnit suite; `node --test` suite for the pure JS modules |

Feature CSS/JS are served at `/features/<Feature>/<file>`; only `.css` and `.js` are mapped, so the
co-located `.cs`/`.cshtml` return 404. Module responsibilities and wiring:
[frontend-modules.md](docs/reference/frontend-modules.md).

## Cross-cutting concerns

- **Security** — read-only posture, identifier validation, bound values, credential handling, TLS to
  ClickHouse: [golden-rules.md](docs/conventions/golden-rules.md).
- **State & persistence** — all in the browser, reset on reload: [data-model.md](docs/reference/data-model.md).
- **Design system** — tokens, layout, components: [DESIGN.md](DESIGN.md).
- **Hosting** — `PathBase`-aware app behind Apache + systemd: [deployment.md](docs/operations/deployment.md).
- **Why** each choice was made, and what was rejected: [decisions.md](docs/reference/decisions.md).
