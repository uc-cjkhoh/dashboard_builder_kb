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
| [features/workbook.md](features/workbook.md) | Auto-save in the browser, restore on connect, Export/Import |

## reference/ — contracts & rationale

| Doc | Topic |
|---|---|
| [reference/api.md](reference/api.md) | Every endpoint and status code |
| [reference/clickhouse-integration.md](reference/clickhouse-integration.md) | Driver, TLS, the exact SQL, identifier safety, type mapping |
| [reference/data-model.md](reference/data-model.md) | Server and client state shapes, incl. the worksheet `sheet` |
| [reference/frontend-modules.md](reference/frontend-modules.md) | Module map, wiring, event bus, `api.js` / `ui.js` helpers |
| [reference/decisions.md](reference/decisions.md) | Decisions D1–D21 with rationale; open questions |
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
| [proposals/roadmap.md](proposals/roadmap.md) | every phase not built yet, in recommended order, with a coverage table against Tableau, Power BI and Looker Studio |
| [proposals/roadmap-bi-parity.md](proposals/roadmap-bi-parity.md) | detail of the open phases from the Power BI / Looker Studio review (P35–P45 series) |
| [proposals/competitive-analysis.md](proposals/competitive-analysis.md) | Gap analysis vs. Tableau and GA4, ordered by difficulty |

## Not here

- **Phases P0–P20 as built, step by step** → the frozen [../archive/build-plan.md](../archive/build-plan.md)
  (not maintained).
