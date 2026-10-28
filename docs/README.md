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
| [features/tabs.md](features/tabs.md) | Data Model tab + dashboard tabs |
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
| [reference/decisions.md](reference/decisions.md) | Decisions D1–D25 with rationale; [calculated fields D26–D32](reference/decisions-calculated-fields.md); open questions |
| [reference/glossary.md](reference/glossary.md) | Domain terms |

## operations/ — build, run, deploy

| Doc | Topic |
|---|---|
| [operations/development.md](operations/development.md) | Where the code is, build / run / test, throwaway ClickHouse |
| [operations/deployment.md](operations/deployment.md) | Live service, Apache proxy, release flow, ops commands |
| `operations/credentials.local.md` | SSH + ClickHouse logins — git-ignored, local only |

## design/ — the design system

Overview: [../DESIGN.md](../DESIGN.md).

| Doc | Topic |
|---|---|
| [design/tokens.md](design/tokens.md) | Colour, status, chart, type, spacing, elevation tokens |
| [design/layout.md](design/layout.md) | Fixed shell, sidebar, worksheet header tiers, `hidden` |
| [design/components.md](design/components.md) | CSS class vocabulary |
| [design/motion-accessibility.md](design/motion-accessibility.md) | Motion and accessibility posture |

## proposals/ — not built yet

| Doc | Topic |
|---|---|
| [proposals/web-application-proposal.md](proposals/web-application-proposal.md) | the product proposal: scope, architecture, journeys, acceptance scenarios |
| [proposals/tableau-features.md](proposals/tableau-features.md) | the 229-requirement Tableau inventory the proposal traces to; [excluded topics](proposals/tableau-features-excluded.md) |
| [proposals/gap-analysis.md](proposals/gap-analysis.md) | the running app benchmarked against the inventory; [per-ID detail](proposals/gap-analysis-detail.md) |
| [proposals/delivery-and-risks.md](proposals/delivery-and-risks.md) | delivery order by dependency, and risks |
| [proposals/calculation-engine.md](proposals/calculation-engine.md) | calculated fields spec (built, not deployed) |
| [proposals/p24c-cross-widget-filtering.md](proposals/p24c-cross-widget-filtering.md) | P24c: cross-widget filtering on dashboards; [plan](proposals/p24c-plan.md) |
| [backlog/README.md](backlog/README.md) | the undone work in one place, grouped by topic with a recommended order |
| [proposals/archive/](proposals/archive/) | retired specs and plans (P24a+b, P24 plans, old roadmaps) — not maintained |

## Not here

- **Phases P0–P20 as built, step by step** → the frozen [../archive/build-plan.md](../archive/build-plan.md)
  (not maintained).
