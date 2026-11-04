---
components: [src/DashboardBuilder/]
---
# Components and code map

Where each piece of code lives. Read it before touching code you don't know.

The app is **MVC in feature folders** ([D19](../decisions/decisions-platform.md#d19--mvc-in-feature-folders)):
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
| `Features/Shell/` | `ShellController` (`GET /`), `Index.cshtml` composing the partials, `app.js` bootstrap, `sidebar.js`, `scheme-toggle.js`, `activity-bar.js` |
| `Features/Core/` | `core.css` (tokens + shared components), `api.js`, `activity-model.js`, `ui.js`, `validate.js`, `icons.js`, `menu.js`, `store.js`, `format.js`, `sheet-schema.js`, vendored ECharts |
| `Features/Connection/`, `Schema/` | sidebar features, each with its API controller |
| `Features/Canvas/`, `Relations/`, `Tabs/`, `Board/` | client-only features (no controller); `Board/` holds the dashboard tab's body (`board.js`, `board-widget.js`, `board-panel.js`) with the pure `board-model.js` (widget rules) and `board-layout.js` (geometry); pure rule modules `empty-state.js`, `relation-rules.js` |
| `Features/Rows/`, `Calc/` | row previews, union / unpivot and source columns (controllers + dialogs); calculated fields (parser, type check, dialog, groups) |
| `Features/Dashboard/` | the worksheet editor (`dashboards.js`), the instantiable query-and-render lifecycle (`worksheet-view.js`), the drawing of a result (`worksheet-render.js` + `render-*.js`, no editor state), the pure query plan (`sheet-plan.js`) and result shaping (`result-model.js`), pure rules (`filter-rules.js`, `toolbar-rules.js`, `contrast.js`), query gate + cache (`query-runner.js`), ECharts adapter (`chart.js`), `QueryController` |
| `Features/Workbook/` | auto-save, restore, Export/Import (`workbook.js`) + the file format and its validation (`workbook-model.js`) |
| `tests/DashboardBuilder.Tests/`, `tests/js/` | xUnit suite; `node --test` suite for the pure JS modules |

Feature CSS/JS are served at `/features/<Feature>/<file>`; only `.css` and `.js` are mapped, so the
co-located `.cs`/`.cshtml` return 404. Module responsibilities and wiring:
[frontend-modules.md](frontend-modules.md).
