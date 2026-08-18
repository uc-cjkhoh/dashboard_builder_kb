# docs/ — topic index

Deep-dive docs for the drag-and-drop dashboard builder. Start at the repo-root
[README.md](../README.md); come here for detail on a specific area.

| Doc | What it covers |
|---|---|
| [app/modules.md](app/modules.md) | The screens/panels: connection panel, schema browser, canvas, entity view, relationship builder, subtabs, widgets |
| [data-model.md](data-model.md) | Client & server data shapes: connection, entity, relationship (cardinality), dashboard/tab; and the "relationships are logical" rule |
| [clickhouse-integration.md](clickhouse-integration.md) | Driver, connection string, the exact introspection/preview SQL, type mapping, identifier-injection rules |
| [drag-and-drop.md](drag-and-drop.md) | HTML5 drag/drop model, entity cards, drawing relationships, cardinality markers |
| [frontend-patterns.md](frontend-patterns.md) | Vanilla-JS module layout, fetch helpers, the `hidden`-attribute toggle, tab management |
| [development.md](development.md) | Run/build on AlmaLinux 9: .NET SDK, `dotnet run`, a throwaway ClickHouse for testing |
| [deployment.md](deployment.md) | **Live production deployment**: the `dashboardbuilder` systemd service, Apache TLS reverse proxy, release flow, ops commands |
| [glossary.md](glossary.md) | Domain terms (entity, cardinality, join key, subtab, preview, …) |
| [project/decisions.md](project/decisions.md) | Architecture & design decisions with rationale; open questions |
| [project/competitive-analysis.md](project/competitive-analysis.md) | Gap analysis vs. Tableau & Google Analytics 4; every capability to compete, ordered by difficulty, with tools required |

See also the root docs: [ARCHITECTURE.md](../ARCHITECTURE.md), [DESIGN.md](../DESIGN.md),
[CLAUDE.md](../CLAUDE.md), [BUILD_PLAN.md](../BUILD_PLAN.md).
