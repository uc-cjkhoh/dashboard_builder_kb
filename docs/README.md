---
components: []
---
# Dashboard Builder — knowledge base index

Navigation for the whole KB. Start at the [project README](../README.md) for what the app is, then pick
the folder that matches your task. Agents: [CLAUDE.md](../CLAUDE.md) is loaded automatically and holds
the golden rules.

> **Shorthand used across the KB:** `D##` = a decision ([lookup](decisions/README.md#where-each-decision-lives)) ·
> `P##` = a product phase, built or planned ([backlog](development/backlog/index.md)) · `R1a`–`R3` = planned releases
> ([journeys-and-releases.md](development/backlog/journeys-and-releases.md#releases)) · `T01`–`T09` = Tableau-inventory requirement areas ([backlog](development/backlog/index.md#how-to-read-an-entry)).

## Folders

| Folder | Holds | Index |
|---|---|---|
| `getting-started/` | prerequisites, installation, configuration, quickstart | [index](getting-started/index.md) |
| `architecture/` | system context, shape, data flow, code map, frontend modules | [index](architecture/index.md) |
| `concepts/` | what the app does: core concepts, data source, worksheet, workbook | [index](concepts/index.md) |
| `how-to/` | task steps: local development, testing, deploying, troubleshooting | [index](how-to/index.md) |
| `reference/` | API, ClickHouse SQL, state shapes, glossary, design system, source-table guidance | [index](reference/index.md) |
| `decisions/` | why things are the way they are (D1–D84) | [README](decisions/README.md) |
| `operations/` | the live service, safe operation, credentials | [index](operations/index.md) |
| `development/` | engineering rules, review gates, git workflow, KB upkeep, backlog, change logs | [index](development/index.md) |
| `archive/` | frozen build plan and old run log, not maintained | [index](archive/index.md) |

## Find a topic

| If you want to… | Read |
|---|---|
| Understand the system and its request flow | [architecture/overview.md](architecture/overview.md) · [data-flow.md](architecture/data-flow.md) |
| Know the rules before changing anything | [development/coding-standards.md](development/coding-standards.md) |
| Avoid known traps | [development/sharp-edges.md](development/sharp-edges.md) |
| Build, run, test | [quickstart](getting-started/quickstart.md) · [testing](how-to/testing.md) |
| Deploy or operate the live service | [how-to/deployment.md](how-to/deployment.md) · [operations/live-service.md](operations/live-service.md) |
| Know what the API accepts and returns | [reference/api.md](reference/api.md) |
| See the visual language | [reference/design/index.md](reference/design/index.md) |
| Find work not yet built | [development/backlog/index.md](development/backlog/index.md) |
| See what changed and when | [CHANGELOG.md](../CHANGELOG.md) |
