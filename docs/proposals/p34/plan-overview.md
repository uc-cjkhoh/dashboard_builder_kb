# P34 Implementation Plan — overview

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended)
> or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax
> for tracking.

**Goal:** Ship the Fluent glass redesign and the input-validation contract described in the spec.

**Architecture:** Keep the existing MVC feature folders and the JS module graph. The server gains a
single validation layer (`ClickHouse/RequestValidation.cs`) and one error contract (`Features/ApiErrors.cs`,
`ApiControllerBase.RunAsync`). The client gains pure, unit-tested rule modules (`Core/validate.js`,
`Dashboard/filter-rules.js`, `Dashboard/toolbar-rules.js`, `Relations/relation-rules.js`) wired into the
existing UI. The redesign replaces the `:root` tokens, restyles components, and adds `Core/icons.js`.

**Tech Stack:** ASP.NET Core 10 MVC (C#), xUnit + `WebApplicationFactory`, vanilla JS ES modules,
`node --test` (Node 24), ClickHouse.Client, vendored ECharts. No framework, build step or CDN.

**Spec:** [../p34-fluent-glass-redesign.md](../p34-fluent-glass-redesign.md) — read it first; this plan
argues from it.

## Plan files (execute in this order)

| Part | Tasks | File |
|---|---|---|
| Server — error contract (Task 1), Task 2 outline | 1–2 | [plan-server-a.md](plan-server-a.md) |
| Server — Task 2 code, typed filters & results tests | 2–3 | [plan-server-b.md](plan-server-b.md) |
| Server — Task 3 implementation, endpoint removal + smoke | 3–4 | [plan-server-c.md](plan-server-c.md) |
| Client — validation primitives, connection form | 5 | [plan-client-a.md](plan-client-a.md) |
| Client — data-model inputs, worksheet rules | 6–7 | [plan-client-b.md](plan-client-b.md) |
| Client — workbook import & restore | 8 | [plan-client-c.md](plan-client-c.md) |
| Design — tokens, glass, components, dark mode | 9 | [plan-design-a.md](plan-design-a.md) |
| Design — icons, sidebar, connection, table search | 10–11 | [plan-design-b.md](plan-design-b.md) |
| Design — tabs, worksheet header, cards; docs & deploy | 12–13 | [plan-design-c.md](plan-design-c.md) |

Server tasks come first: the client tasks rely on the server's `{ error, field }` shape and the
`object?` result values.

## Global Constraints

- Read-only against ClickHouse; validate + quote every identifier in `ClickHouse/Identifier.cs` only;
  bind every value; bound every result (golden rules 1–3).
- Credentials never returned, logged, or put in a URL (golden rule 4).
- Toggle visibility with `hidden`, never `style.display` (golden rule 6).
- Design tokens only — no hardcoded hex outside the `:root` blocks in `Core/core.css` (golden rule 7).
- The page never scrolls; panels scroll inside (golden rule 8).
- Never colour alone — icon + text + colour (golden rule 9).
- Self-hosted, framework-free frontend — no CDN, no web font, no build step (golden rule 10).
- Error body is always `{ "error": "<sentence>", "field": "<path>?" }`. Status codes: 400 invalid input,
  404 unknown schema identifier on schema routes, 409 not connected, 413 body too large, 502 ClickHouse
  failure, 504 timeout (unchanged), 500 our bug with `Unexpected error (ref <traceId>).`
- Limits (server constants in `ApiLimits`, mirrored in `Core/validate.js` `LIMITS`): body 256 KB; host 253,
  user 64, password 256 chars; dimensions ≤ 12 total, measures ≤ 10, joins ≤ 10, filters ≤ 8, `in`
  values ≤ 500, filter value ≤ 1000 chars; row limit 1–500; buckets 1–100; distinct 1–1000; tab name
  1–60; axis title ≤ 80.
- User-facing messages are full sentences, name the field/column, and never contain CLR type names.
- Host-validation messages are identical on client and server (copied verbatim in both tasks).
- New feature CSS/JS lives under `Features/` (only `.css`/`.js` are served from there).

## Review Focus

Inputs the spec implies but no task's main tests exercise — each now has a pinning test in its task:

1. **An aggregate over zero matching rows** (avg → `nan`, division → `inf`) must render "—", not crash
   JSON serialisation with a 500 → Task 3 `ToResultValue` tests.
2. **Locale-formatted numbers** ("1,5", "1,000", "1 000", "0x10", "1e3" accepted as scientific) must be
   rejected with a message, never parsed as a different number → Task 3 `Coerce` and Task 5 `number` tests.
3. **Whitespace-only input** (host "   ", tab name "  ", filter value " ") counts as empty → Task 5 tests.
4. **A hostile or bloated workbook file** (thousands of dashboards/pills, nested junk) must be capped
   with reported issues, not freeze the tab → Task 8 caps tests (≤ 50 dashboards, ≤ 20 pills per shelf).
5. **A host pasted with brackets and a port** (`[::1]:8443`, `host:8443`) gets the "put the port in Port"
   message on both sides → Task 2 and Task 5 host tests.

## File map

| File | Status | Responsibility |
|---|---|---|
| `src/DashboardBuilder/ClickHouse/RequestValidation.cs` | create | `RequestValidationException`, `ApiLimits`, `RequestRules`, `FilterValues` |
| `src/DashboardBuilder/Features/ApiErrors.cs` | create | model-state factory, body-limit middleware, unhandled-exception writer |
| `src/DashboardBuilder/Features/ApiControllerBase.cs` | modify | `RunAsync`, `Invalid`, 500 vs 502 split |
| `src/DashboardBuilder/Program.cs` | modify | register factory, exception handler, body limit |
| `src/DashboardBuilder/ClickHouse/ClickHouseGateway.cs` | modify | typed `BuildCondition`, `object?` values, stat filters; remove aggregate/preview/count |
| `src/DashboardBuilder/ClickHouse/QueryModels.cs`, `StatisticalModels.cs`, `SchemaModels.cs`, `CsvUtil.cs` | modify | `object?` values, `StatFilter`, drop `PreviewResult` |
| `src/DashboardBuilder/ClickHouse/AggregateModels.cs` | delete | endpoint removed |
| `Features/Connection/ConnectionController.cs`, `Schema/SchemaController.cs`, `Dashboard/QueryController.cs` | modify | use `RunAsync` + rules |
| `Features/Core/validate.js` | create | pure parsers + `LIMITS` |
| `Features/Core/ui.js` | modify | `fieldError`, `clearFieldError`, `listDialog`, dismissible danger toast |
| `Features/Core/api.js` | modify | `errorMessage`, drop removed endpoints |
| `Features/Core/format.js` | modify | string measure values pass through |
| `Features/Core/icons.js` | create | inline-SVG icon set |
| `Features/Core/core.css` | modify | new tokens (light + dark), components, glass |
| `Features/Shell/app.js`, `Index.cshtml`, `shell.css` | modify | global error handlers, glass shell, wash |
| `Features/Connection/*` | modify | validation, Advanced disclosure |
| `Features/Schema/*` | modify | table search |
| `Features/Canvas/canvas.js`, `Relations/relations.js`, `Relations/relation-rules.js` (create) | modify | duplicate/type checks |
| `Features/Tabs/tabs.js`, `tabs.css` | modify | rename rules, keyboard rename, Fluent tabs |
| `Features/Dashboard/filter-rules.js`, `toolbar-rules.js` | create | pure worksheet rules |
| `Features/Dashboard/dashboards.js`, `chart.js`, `dashboard.css` | modify | wire rules, icons, More menu, theme re-render |
| `Features/Workbook/workbook-model.js`, `workbook.js`, `_Workbook.cshtml`, `workbook.css` | modify | full sheet validation, issues, backup, menu |
| `Features/Core/sheet-schema.js`, `Core/menu.js` | create | allowed saved-sheet values; shared accessible menu |
| `Features/Schema/table-filter.js`, `Connection/connection-rules.js` | create | pure table search; Advanced-open rule |
| `tests/DashboardBuilder.Tests/ErrorContractTests.cs`, `ValidationTests.cs`, `TypedFilterTests.cs` | create | server tests |
| `tests/js/validate.test.mjs`, `relation-rules.test.mjs`, `filter-rules.test.mjs`, `format.test.mjs`, `tokens.test.mjs`, `icons.test.mjs`, `table-filter.test.mjs`, `toolbar-rules.test.mjs` | create | client tests |

All source paths are under `/unified/user/cj/web_development/prototype/dashboard_builder/` (the
**app root**). Run every command from there unless a step says otherwise.

## Working conventions for every task

- **The app folder is not a git repo.** Before Task 1, take a backup:
  `tar czf ~/dashboard_builder-pre-p34-$(date +%F).tgz src tests` — then "commit" steps in this
  plan mean **checkpoint**: run both suites green and note the task done. KB doc changes are committed
  in the KB repo (Task 13).
- .NET suite: `dotnet test` (one class: `dotnet test --filter ValidationTests`).
- JS suite: `~/.nvm/versions/node/v24.20.0/bin/node --test tests/js/*.test.mjs`.
- Syntax-check every changed JS module: `~/.nvm/versions/node/v24.20.0/bin/node --check <file>`.
- Dev run on a spare port (5199 is taken): `cd src/DashboardBuilder && ASPNETCORE_URLS=http://localhost:5180 dotnet run`.
  Stop it by port (`fuser -k 5180/tcp`) — **never** `pkill -f DashboardBuilder.dll` (matches the live service).
- There is no headless browser on the host. DOM behaviour is checked with jsdom installed in a scratch
  dir ([development.md](../../operations/development.md#test)); the user does the visual review.

## Done when

All 13 tasks are checked, both suites pass, the smoke script in Task 4 returns the documented statuses,
the user has reviewed light + dark on the dev port, the KB reflects the new state and this `p34/`
folder plus the spec are deleted (Task 13), and the live service is redeployed stop → copy → start.
