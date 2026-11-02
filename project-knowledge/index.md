# Project knowledge — topic index

Deep dives for the Dashboard Builder. Start from [README.md](README.md) /
[ARCHITECTURE.md](ARCHITECTURE.md) / [CLAUDE.md](../CLAUDE.md) for the big picture, then the file
matching whatever you're touching.

> **Shorthand used across the KB:** `D##` = a decision ([lookup](reference/decisions/decisions.md#where-each-decision-lives)) ·
> `P##` = a product phase, built or planned ([backlog](backlog/README.md)) · `R1a`–`R3` = planned releases
> ([journeys-and-releases.md](backlog/journeys-and-releases.md#releases)) · `T01`–`T09` = Tableau-inventory requirement areas ([backlog](backlog/README.md#how-to-read-an-entry)).

## engineering/ — the rules (read before changing behaviour)

| Doc | Topic |
|---|---|
| [engineering/golden-rules.md](engineering/golden-rules.md) | The 10 golden rules in full |
| [engineering/sharp-edges.md](engineering/sharp-edges.md) | Gotchas: ClickHouse quirks, proxy/deploy landmines, frontend traps |
| [engineering/change-checklist.md](engineering/change-checklist.md) | Safety and frontend gates every code change meets |

## features/ — one file per app feature, grouped by where it lives in the app

### features/data-source/ — the Data Source tab: connect, pick tables, model them

| Doc | Topic |
|---|---|
| [connection.md](features/data-source/connection.md) | Connection form, TLS + cert opt-in, summary, gating |
| [schema-browser.md](features/data-source/schema-browser.md) | Database picker and draggable table chips |
| [canvas.md](features/data-source/canvas.md) | Drag/drop onto the Data Source, entity cards, union / unpivot cards |
| [query-sources.md](features/data-source/query-sources.md) | A union or unpivot as a data source: adding, columns, reading, saving, SQL shape |
| [relationships.md](features/data-source/relationships.md) | Drawing links, cardinality, shape-coded endpoints |

### features/worksheet/ — a worksheet tab: shelves, charts, encodings, calculations

| Doc | Topic |
|---|---|
| [worksheet.md](features/worksheet/worksheet.md) | Field pane, shelves, query lifecycle (latest-wins, cache, truncation), joins, crosstab, sort, format |
| [worksheet-charts.md](features/worksheet/worksheet-charts.md) | Chart types, orientation, ECharts adapter, export |
| [worksheet-encodings.md](features/worksheet/worksheet-encodings.md) | Marks, Filters, click-to-filter, Drill, Pages, date range |
| [calculated-fields.md](features/worksheet/calculated-fields.md) | Formulas, dialog, field-pane group, roles, refusals, error state, the explainer |
| [field-settings.md](features/worksheet/field-settings.md) | Per-field data type cast and member labels |

### features/workbook/ — tabs, dashboards, and saving the whole workbook

| Doc | Topic |
|---|---|
| [tabs.md](features/workbook/tabs.md) | Data Source tab + worksheet and dashboard tabs |
| [dashboards.md](features/workbook/dashboards.md) | The dashboard board: grid, side panel, widgets, lifecycle |
| [workbook.md](features/workbook/workbook.md) | Auto-save in the browser, restore on connect, Export/Import |

## reference/ — contracts & rationale

| Doc | Topic |
|---|---|
| [api.md](reference/api.md) | Every endpoint, status code and limit |
| [api-calculated-fields.md](reference/api-calculated-fields.md) | The `calc` tree: nodes, role and typing rules |
| [clickhouse-integration.md](reference/clickhouse-integration.md) | Driver, TLS, the exact SQL, identifier safety, type mapping |
| [clickhouse-calculations.md](reference/clickhouse-calculations.md) | How a `calc` tree compiles; exact vs approximate aggregates |
| [data-model.md](reference/data-model.md) | Server and client state shapes, incl. the worksheet `sheet` |
| [frontend-modules.md](reference/frontend-modules.md) | Module map, wiring, event bus, `api.js` / `ui.js` helpers |
| [glossary.md](reference/glossary.md) | Domain terms |

### reference/decisions/ — why things are the way they are

| Doc | Topic |
|---|---|
| [decisions.md](reference/decisions/decisions.md) | D1–D25 (platform, frontend, worksheet, hosting), the D-number → file lookup, open questions |
| [decisions-calculated-fields.md](reference/decisions/decisions-calculated-fields.md) | D26–D60, D65–D68, D73: calculations, parameters, groups, split / unpivot |
| [decisions-dashboards.md](reference/decisions/decisions-dashboards.md) | D61–D64, D69, D71–D72: dashboards, hierarchies, option controls |
| [decisions-connection.md](reference/decisions/decisions-connection.md) | D70: recent connection sources |
| [decisions-logic.md](reference/decisions/decisions-logic.md) | D75–D77: `NULL`, `IN` / `BETWEEN`, keyword `IF` |

## operations/ — build, run, deploy

| Doc | Topic |
|---|---|
| [operations/development.md](operations/development.md) | Where the code is, build / run / test, throwaway ClickHouse |
| [operations/deployment.md](operations/deployment.md) | Live service, Apache proxy, release flow, ops commands |
| [operations/source-table-guidance.md](operations/source-table-guidance.md) | Sorting key, partitioning, types, join keys and sampling for the ClickHouse tables the app reads |
| `operations/credentials.local.md` | SSH + ClickHouse logins — git-ignored, local only |

## design/ — the design system

Overview: [design/overview.md](design/overview.md).

| Doc | Topic |
|---|---|
| [design/tokens.md](design/tokens.md) | Colour, status, chart, type, spacing, elevation tokens |
| [design/layout.md](design/layout.md) | Fixed shell, sidebar, worksheet header tiers, `hidden` |
| [design/components.md](design/components.md) | CSS class vocabulary |
| [design/motion-accessibility.md](design/motion-accessibility.md) | Motion and accessibility posture |

## backlog/ — not built yet

| Doc | Topic |
|---|---|
| [backlog/README.md](backlog/README.md) | the only to-do list: how to read it, recommended order, spikes, guards, known unknowns |
| [backlog/dashboards.md](backlog/dashboards.md) | P24a–d, layout, actions, navigation, P38, P39 remainder |
| [backlog/calculations.md](backlog/calculations.md) | functions, LOD, table-calculation polish, P25 |
| [backlog/data-model.md](backlog/data-model.md) | joins, union, groups, split, cast, hierarchies, P43 |
| [backlog/charts-and-formatting.md](backlog/charts-and-formatting.md) | chart, authoring, formatting and export gaps |
| [backlog/analytics-and-maps.md](backlog/analytics-and-maps.md) | statistics, forecasting, clustering, P42, maps |
| [backlog/platform.md](backlog/platform.md) | persistence, P45, P44, risks, workbook additions, decisions to settle |
| [backlog/journeys-and-releases.md](backlog/journeys-and-releases.md) | journeys, acceptance scenarios, releases R1a–R3, quality targets |
| [backlog/out-of-scope.md](backlog/out-of-scope.md) | deliberately excluded topics and why |

## updates/ — what changed, by date

| Doc | Topic |
|---|---|
| [updates/ui_updates.md](updates/ui_updates.md) | visual and interaction changes, grouped by date (generated) |
| [updates/feature_updates.md](updates/feature_updates.md) | functional changes, grouped by date (generated) |

## Not here

- **Phases P0–P20 as built, step by step, and old run logs** → the frozen [archive/](archive/README.md)
  (not maintained).

## Agent behavior

How to work on this project (definition of done, KB upkeep, hooks, safe operation, run logs) →
[../agent-behavior/](../agent-behavior/README.md).
