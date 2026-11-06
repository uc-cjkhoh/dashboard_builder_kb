---
components: []
---
# Backlog — work not yet built

The only place for work not yet built, grouped by topic. Read it before picking up new work. Built behaviour lives in [concepts/](../../concepts/index.md). Nothing else in the KB lists to-dos.

## Files

| File | Holds |
|---|---|
| [dashboards.md](dashboards.md) | Stories remainder, dashboard layout, image and spacer widgets, actions, navigation, P38, set action |
| [calculations.md](calculations.md) | functions the engine lacks, LOD, table-calculation polish, P25 |
| [data-model.md](data-model.md) | joins, union, groups, split, cast, hierarchies, aggregate-before-join |
| [charts-and-formatting.md](charts-and-formatting.md) | chart, authoring, formatting and export gaps |
| [analytics-and-maps.md](analytics-and-maps.md) | statistics, forecasting, clustering, P42, maps |
| [platform.md](platform.md) | persistence, P45, P44, open risks, workbook additions, decisions to settle |
| [journeys-and-releases.md](journeys-and-releases.md) | journeys and acceptance scenarios, releases R1a–R3, quality targets |
| [out-of-scope.md](out-of-scope.md) | what is deliberately excluded, and why (not backlog) |
| [blocked.md](../run-logs/blocked.md) | work that could not be built, and why |

## How to read an entry

`- **name** (IDs: Txx-nn; priority P0–P3; effort S/M/L if stated) — open: nothing implements it, or partial: what exists and what is missing. Needs: dependency or none. Spec: file.`

- IDs are stable requirement IDs from an inventory of Tableau features. `T01`–`T09` are its chapters: workspace, data source, charts, calculations, table calculations, maps, statistics, dashboards, consumption.
- Entries without an ID are product phases (P24, P38 …). Do not confuse these with priorities: **priority** P0–P3 runs from P0 (most important) to P3.
- The name and the open/partial text stand alone.
- "Open" means nothing implements it; "partial" says what exists.
- Entries inside a file run by dependency, then priority.

## Recommended order

1. Calculation function remainders (logic, text, date) — the engine's tree path already exists.
2. Table-calculation polish — builds on the function set.
3. Data-model breadth (compound joins, union and split remainders, groups, hierarchies) — independent of the engine; compound joins come first.
4. Chart gaps and formatting — client-only, ordered by priority.
5. Actions, navigation, P38 and the set action (P39 remainder) — need dashboards and, for sets, P25.
6. LOD — needs the core engine and written filter-order rules.
7. Analytics and forecasting — trend models come before intervals and forecast.
8. P42 AI assist and maps — large, and need decisions on data leaving the server and bundled geography.
9. Persistence and P45 — blocked on the D2 decision.

## Spikes before committing a big design

1. **Calculation compile for LOD:** AST → ClickHouse SQL for one `FIXED` LOD, checked against a fixture (the ratio case is done; `CASE` and date parts are not).
2. **Table-calculation order:** a client engine for running total, rank and moving average with addressing and partitioning, with filter-order rules written down.
3. **Action graph:** one selection filtering two sheets with explicit field mappings (the fixed same-table form is built: [dashboards.md](../../concepts/workbook/dashboards.md#cross-widget-filtering)).
4. **Scale:** P95 latency of the aggregate path on a large and an unindexed table, with and without the result cache.

Risks are listed in [platform.md](platform.md#open-risks).

## Guards every item must keep

- Read-only against ClickHouse; every identifier validated against the live catalog and quoted; every value bound; every result bounded ([coding-standards.md](../coding-standards.md), rules 1–3).
- No server-side persistence unless [platform.md](platform.md) records a decision.
- Single user, browser-held state; ClickHouse is the only data source; no uploads, extracts, accounts or publication ([out-of-scope.md](out-of-scope.md)).
- Self-hosted, framework-free frontend, no CDN ([rule 10](../coding-standards.md#10-self-hosted-framework-free-frontend)); a new library is vendored with a written reason.
- A workbook stores specifications and metadata, never data, credentials or executable code.
- Every state-changing edit is undoable; the grain and active filters stay visible in words; everything draggable has a keyboard path; unavailable options say why.
- Not a Tableau clone: no `.twb`/`.hyper` compatibility, no Tableau branding, no claim of identical regression or forecast output.
- The design rules and golden rules 6, 7 and 9 (tokens, `hidden`, never colour alone) apply.
- Done means [review-guidelines.md](../review-guidelines.md): update the feature doc and delete the entry here.

## Known unknowns

- The inventory status was read from the code, not from a running app; a feature that exists but is broken would show as built, so runtime behaviour per requirement is unverified.
- There is no traceability matrix of requirement ID → status → test; this backlog is the status list, and the test column is still to build.

## Out of scope

[out-of-scope.md](out-of-scope.md) lists what is deliberately excluded. It is not backlog.
