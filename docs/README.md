# docs/ — topic index

Deep dives for the Dashboard Builder. Start from the root [README.md](../README.md) /
[ARCHITECTURE.md](../ARCHITECTURE.md) / [CLAUDE.md](../CLAUDE.md) for the big picture, then the file
matching whatever you're touching.

## conventions/ — the rules (read before changing behaviour)

| Doc | Topic |
|---|---|
| [conventions/golden-rules.md](conventions/golden-rules.md) | The 10 golden rules in full |
| [conventions/sharp-edges.md](conventions/sharp-edges.md) | Gotchas: ClickHouse quirks, proxy/deploy landmines, frontend traps |
| [conventions/definition-of-done.md](conventions/definition-of-done.md) | The done checklist |
| [conventions/kb-maintenance.md](conventions/kb-maintenance.md) | How to maintain this KB — current state, size limits, layout, enforcement hook |

## features/ — one file per app feature

| Doc | Topic |
|---|---|
| [features/connection.md](features/connection.md) | Connection form, TLS + cert opt-in, summary, gating |
| [features/schema-browser.md](features/schema-browser.md) | Database picker and draggable table chips |
| [features/canvas.md](features/canvas.md) | Drag/drop onto the Data Model, entity cards, join keys |
| [features/relationships.md](features/relationships.md) | Drawing links, cardinality, shape-coded endpoints |
| [features/tabs.md](features/tabs.md) | Data Model tab + worksheet and dashboard tabs |
| [features/dashboards.md](features/dashboards.md) | the dashboard board: grid, side panel, widgets, lifecycle |
| [features/worksheet.md](features/worksheet.md) | Field pane, shelves, query lifecycle (latest-wins, cache, truncation), joins, crosstab, sort, format |
| [features/worksheet-charts.md](features/worksheet-charts.md) | Chart types, orientation, ECharts adapter, export |
| [features/worksheet-encodings.md](features/worksheet-encodings.md) | Encodings toolbar: Marks, Filters, click-to-filter, Drill, Pages |
| [features/calculated-fields.md](features/calculated-fields.md) | Calculated fields: dialog, field-pane group, roles, refusals, error state, the explainer |
| [features/workbook.md](features/workbook.md) | Auto-save in the browser, restore on connect, Export/Import |

## reference/ — contracts & rationale

| Doc | Topic |
|---|---|
| [reference/api.md](reference/api.md) | Every endpoint and status code |
| [reference/clickhouse-integration.md](reference/clickhouse-integration.md) | Driver, TLS, the exact SQL, identifier safety, type mapping |
| [reference/data-model.md](reference/data-model.md) | Server and client state shapes, incl. the worksheet `sheet` |
| [reference/frontend-modules.md](reference/frontend-modules.md) | Module map, wiring, event bus, `api.js` / `ui.js` helpers |
| [reference/decisions.md](reference/decisions.md) | Decisions D1–D25 with rationale; [connection D70](reference/decisions-connection.md); [calculated fields D26–D60 and D65–D66](reference/decisions-calculated-fields.md); [dashboards D61–D64](reference/decisions-dashboards.md); open questions |
| [reference/glossary.md](reference/glossary.md) | Domain terms |

## operations/ — build, run, deploy

| Doc | Topic |
|---|---|
| [operations/development.md](operations/development.md) | Where the code is, build / run / test, throwaway ClickHouse |
| [operations/deployment.md](operations/deployment.md) | Live service, Apache proxy, release flow, ops commands |
| [operations/source-table-guidance.md](operations/source-table-guidance.md) | Sorting key, partitioning, types, join keys and sampling for the ClickHouse tables the app reads |
| `operations/credentials.local.md` | SSH + ClickHouse logins — git-ignored, local only |

## design/ — the design system

Overview: [../DESIGN.md](../DESIGN.md).

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
| [backlog/journeys-and-releases.md](backlog/journeys-and-releases.md) | journeys, acceptance scenarios, releases R0–R3, quality targets |
| [backlog/out-of-scope.md](backlog/out-of-scope.md) | deliberately excluded topics and why |

## Not here

- **Phases P0–P20 as built, step by step** → the frozen [../archive/build-plan.md](../archive/build-plan.md)
  (not maintained).
