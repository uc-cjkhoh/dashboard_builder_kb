# CLAUDE.md — working conventions (index)

Index for anyone (human or agent) working on the **Dashboard Builder**. This file is the map: where the
code is, setup commands, directory layout, and the golden rules in one line each. The detail lives in
[`project-knowledge/`](project-knowledge/index.md) and [`agent-behavior/`](agent-behavior/README.md) — follow the links.

> **Read first:** [README.md](project-knowledge/README.md) · [ARCHITECTURE.md](project-knowledge/ARCHITECTURE.md) · [design/overview.md](project-knowledge/design/overview.md),
> then the [`project-knowledge/`](project-knowledge/index.md) file for whatever you're touching. **Update that doc in the same
> change** — this KB tracks current state, not history ([kb-maintenance.md](agent-behavior/kb/kb-maintenance.md)).

> **This KB is docs only.** The source is at `/unified/user/cj/web_development/prototype/dashboard_builder/`
> on the build host `10.168.49.20` (same shared filesystem — build it from here). Never scaffold code
> into the KB. The app folder is a local git repo (no remote); this KB is a separate git repo.

## Golden rules

One line each; full text in [golden-rules.md](project-knowledge/engineering/golden-rules.md).
**Rules 1–3 shape every server change.**

1. **Read-only against ClickHouse** — `SELECT`/`SHOW`/`DESCRIBE` only, no DDL/DML endpoint in v1; ClickHouse's own
   `readonly=2` is set on every query as a second guard.
2. **Validate + quote every identifier** against the live catalog, in `ClickHouse/Identifier.cs` only
   (ClickHouse binds values, not identifiers).
3. **Bind every value; bound every result** — whitelisted aggs/ops, typed values, validated `LIMIT`s;
   every query is time-limited; out-of-range input is rejected (400), never silently clamped. Charts cap at 5000 groups, tables page, CSV ≤ 100k (D24).
4. **Credentials live in the session only** — never returned, logged, or put in a URL.
5. **Relationships are logical declarations**, not database facts.
6. **Toggle visibility with `hidden`**, never `style.display`.
7. **Design tokens only** — no hardcoded hex; red means danger, nothing else.
8. **Fixed shell** — the page never scrolls; panels scroll inside.
9. **Never colour alone** — icon + text + colour; legends; shape-coded cardinality.
10. **Self-hosted, framework-free frontend** — vanilla JS/CSS, no build step, no CDN.

## What this is in one screen

One ASP.NET Core MVC app (Kestrel) serves **a single page** (`GET /`, composed from feature partials)
plus a **read-only JSON API**. The **browser holds all builder state** — the shared data source
(entities + relationships) and every worksheet and dashboard tab — in vanilla-JS ES modules. The
**server is a thin, session-scoped proxy to ClickHouse**: `ConnectionRegistry` holds the session's
connection; `ClickHouseGateway` runs introspection and bounded, identifier-safe aggregate/join queries
and returns JSON. **There is no application database.** Full picture:
[ARCHITECTURE.md](project-knowledge/ARCHITECTURE.md).

## Build, run, test, deploy

From the solution root `/unified/user/cj/web_development/prototype/dashboard_builder`:

```bash
dotnet build -c Release
dotnet test                                   # .NET suite; --filter Identifier for one class
~/.nvm/versions/node/v24.20.0/bin/node --test tests/js/*.test.mjs   # JS unit tests
cd src/DashboardBuilder && dotnet run         # http://localhost:5080
dotnet run --no-launch-profile --urls http://localhost:5180   # a spare port
dotnet publish src/DashboardBuilder/DashboardBuilder.csproj -c Release -o publish
```

- **Prereqs:** .NET SDK 10 (on the host's `PATH`); a ClickHouse to point at — details and a throwaway
  container in [development.md](project-knowledge/operations/development.md).
- **Live:** `webapps-dev.dashboardbuilder.service`, Kestrel `:5105`, Apache `:8443`, path
  `/dashboardbuilder`. Stop → copy → start for server changes — never copy a DLL over the running
  process ([deployment.md](project-knowledge/operations/deployment.md)).
- **Never `pkill -f DashboardBuilder.dll`** (matches the live service) — stop dev runs by port.
- **Credentials** (SSH + ClickHouse): git-ignored
  [credentials.local.md](project-knowledge/operations/credentials.local.md) — never in shared docs. All never-do rules: [safe-operations.md](agent-behavior/operations/safe-operations.md).

## Source layout

```
src/DashboardBuilder/
├── Program.cs              # host, session, PathBase, no-cache static files, /features provider
├── ClickHouse/             # shared server infra: Gateway (all SQL), Identifier, ClickHouseType,
│                           #   RequestValidation (limits, rules, typed filter values),
│                           #   ConnectionRegistry, CsvUtil, *Models.cs
└── Features/               # one folder per feature: controller + _View.cshtml + .css + .js
    ├── ApiControllerBase.cs  ApiErrors.cs   # RunAsync / SafeError; the one { error, field? } shape
    ├── Shell/  Core/  Connection/  Schema/  Canvas/  Relations/  Rows/  Tabs/  Board/  Dashboard/  Calc/  Workbook/
tests/DashboardBuilder.Tests/   # xUnit
tests/js/                       # node --test, for the pure JS modules
```

Feature assets are served at `/features/<Feature>/<file>` (`.css`/`.js` only). Map:
[ARCHITECTURE.md § Code map](project-knowledge/ARCHITECTURE.md#code-map).

## Design rules

Full text and how they map to tokens: [golden-rules.md § 11](project-knowledge/engineering/golden-rules.md#11-design-rules).

1. **Optical alignment** on every element — align to what the eye reads, not the box edge.
2. **Gaps and spacing** are only 4 / 8 / 16 / 24 px (`--s1` `--s2` `--s4` `--s6`).
3. **One border radius** for inner and outer shapes (`--r`, 8px).
4. **Colour saturation ≈ 70 %** by default (HSL S ≤ 70 %).
5. **Few font sizes:** 14 / 16 px for content, 24 / 32 px for titles.
6. **No unnecessary secondary labels or descriptions** — let the layout do the explaining.

## Tech stack reference

Preferred stack for new projects — **reference only**: this app stays vanilla JS/CSS
([golden rule 10](project-knowledge/engineering/golden-rules.md#10-self-hosted-framework-free-frontend)).
UI: shadcn/ui NOVA · Icons: Lucide · Animation: Motion · Drag and drop: dnd-kit · State: Zustand.

## KB directory map

The one copy of the folder tree; other docs link here.

```
dashboard_builder/          (this KB)
├── CLAUDE.md  README.md    # entry index (kept at root for Claude Code) · router to the two folders
├── agent-behavior/         # how to work here
│   ├── workflow/           # definition-of-done · merge-to-main · status-dashboard
│   ├── kb/                 # kb-maintenance · hooks
│   ├── operations/         # safe-operations (never-do list)
│   └── run-logs/           # blocked work
├── project-knowledge/      # what the project is
│   ├── README.md  ARCHITECTURE.md  index.md
│   ├── engineering/        # golden-rules · sharp-edges · change-checklist
│   ├── design/             # overview · tokens · layout · components · motion-accessibility
│   ├── features/           # one file per app feature, in three groups:
│   │   ├── data-source/    #   connection · schema-browser · canvas · query-sources · relationships
│   │   ├── worksheet/      #   worksheet · worksheet-charts · worksheet-encodings · calculated-fields · field-settings
│   │   └── workbook/       #   tabs · dashboards · workbook
│   ├── reference/          # api (+ -calculated-fields) · clickhouse-integration (+ clickhouse-calculations) · data-model · frontend-modules · glossary
│   │   └── decisions/      #   decisions (D1–D25 + lookup) · -calculated-fields · -dashboards · -connection
│   ├── operations/         # development · deployment · source-table-guidance (+ git-ignored credentials.local.md)
│   ├── backlog/            # undone work by topic · recommended order · design specs
│   ├── updates/            # generated change logs
│   └── archive/            # frozen P0–P20 build plan, old debug log — not maintained
└── .claude/                # hooks (kb-verify, update-log, reap-chrome), settings, skills
```

## Where things live

| Task | Code | Doc |
|---|---|---|
| Add/adjust a ClickHouse query | `ClickHouse/ClickHouseGateway.cs` | [clickhouse-integration.md](project-knowledge/reference/clickhouse-integration.md) |
| Add an API endpoint | `Features/*/…Controller.cs` (subclass `ApiControllerBase`) | [api.md](project-knowledge/reference/api.md) (calculation trees: [api-calculated-fields.md](project-knowledge/reference/api-calculated-fields.md)) |
| Validate an input / add a limit | `ClickHouse/RequestValidation.cs` + `Features/Core/validate.js` (keep in step) | [api.md § Limits](project-knowledge/reference/api.md#limits) |
| Connection flow | `ClickHouse/ConnectionRegistry.cs`, `Features/Connection/` | [connection.md](project-knowledge/features/data-source/connection.md) |
| Drag/drop, entity cards | `Features/Canvas/canvas.js` | [canvas.md](project-knowledge/features/data-source/canvas.md) |
| Relationships / cardinality | `Features/Relations/relations.js` | [relationships.md](project-knowledge/features/data-source/relationships.md) |
| Tabs / dashboard data | `Features/Tabs/tabs.js`, `Core/store.js`, `Features/Board/board-model.js` | [tabs.md](project-knowledge/features/workbook/tabs.md) |
| Worksheet shelves / plan / crosstab | `Features/Dashboard/dashboards.js` | [worksheet.md](project-knowledge/features/worksheet/worksheet.md) |
| Chart types / rendering / export | `Features/Dashboard/chart.js` | [worksheet-charts.md](project-knowledge/features/worksheet/worksheet-charts.md) |
| Marks, filters, drill, pages | `Features/Dashboard/dashboards.js` | [worksheet-encodings.md](project-knowledge/features/worksheet/worksheet-encodings.md) |
| Query caching / latest-wins / truncation notice | `Features/Dashboard/query-runner.js` | [worksheet.md § Query lifecycle](project-knowledge/features/worksheet/worksheet.md#query-lifecycle) |
| Save / restore / export / import | `Features/Workbook/` | [workbook.md](project-knowledge/features/workbook/workbook.md) |
| Colour / spacing / type | `Features/Core/core.css` `:root` | [tokens.md](project-knowledge/design/tokens.md) |
| Motion / transitions | `Features/Core/motion.js` + `core.css` motion tokens | [motion-accessibility.md](project-knowledge/design/motion-accessibility.md#motion) |
| Gotchas before editing | — | [sharp-edges.md](project-knowledge/engineering/sharp-edges.md) |
| Definition of done | — | [definition-of-done.md](agent-behavior/workflow/definition-of-done.md) |
