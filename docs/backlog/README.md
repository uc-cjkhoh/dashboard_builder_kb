# Backlog — work not yet built

The only place for work not yet built, grouped by topic. Built behaviour lives in [../features/](../features/worksheet.md). Nothing else in the KB lists to-dos.

## Files

| File | Holds |
|---|---|
| [dashboards.md](dashboards.md) | P24a–d, dashboard layout, actions, navigation, P38, P39 remainder |
| [calculations.md](calculations.md) | functions the engine lacks, parameters in formulas, LOD, table-calculation polish, P25 |
| [data-model.md](data-model.md) | joins, union, groups, split, cast, row preview, hierarchies, P43 |
| [charts-and-formatting.md](charts-and-formatting.md) | chart, authoring, formatting and export gaps |
| [analytics-and-maps.md](analytics-and-maps.md) | statistics, forecasting, clustering, P42, maps |
| [platform.md](platform.md) | persistence, P45, P44, open risks, workbook additions, decisions to settle |
| [journeys-and-releases.md](journeys-and-releases.md) | journeys and acceptance scenarios, releases R0–R3, quality targets |
| [out-of-scope.md](out-of-scope.md) | what is deliberately excluded, and why (not backlog) |
| [p24-dashboards-spec.md](p24-dashboards-spec.md) | design spec for P24a and P24b |
| [p24c-cross-widget-filtering.md](p24c-cross-widget-filtering.md), [p24c-plan.md](p24c-plan.md) | design spec and task plan for P24c |

Status at a glance: the [backlog status dashboard](https://claude.ai/artifact/C5S1oYsan7vXMbfpaS5USA). Update it after every backlog update ([definition-of-done.md](../conventions/definition-of-done.md#status-dashboard)).

## How to read an entry

`- **name** (IDs: Txx-nn; priority P0–P3; effort S/M/L if stated) — open: nothing implements it, or partial: what exists and what is missing. Needs: dependency or none. Spec: file.`

- IDs are stable Tableau-inventory requirement IDs (`T01`–`T09`: workspace, data model, charts, calculations, table calculations, maps, statistics, dashboards, consumption); entries without an ID are product phases (P24, P38 …). The name and the open/partial text stand alone.
- "Open" means nothing implements it; "partial" says what exists.
- Entries inside a file run by dependency, then priority.

## Recommended order

1. Dashboard runtime (P24a) — every dashboard item needs an instantiable worksheet view.
2. Dashboards as a tab kind (P24b) — the largest structural gap and the Release 0 exit.
3. Cross-widget filtering (P24c) — the last Release 0 dashboard gap, and it needs widgets.
4. Small P0 gaps (cast, row preview, duplicate sheet, tooltip editor, per-member colour, exclude) — each is independent and closes Release 0.
5. Calculation aggregations, logic, text and date functions — the engine's tree path already exists.
6. Parameters in formulas and table-calculation polish — both build on the function set.
7. Data-model breadth (joins, union, groups, split, hierarchies) — independent of the engine; join types come before P43.
8. Chart gaps and formatting — client-only, ordered by priority.
9. Actions, navigation, P38 and P39 remainder — need dashboards and, for sets, P25.
10. LOD — needs the core engine and written filter-order rules.
11. Analytics and forecasting — trend models come before intervals and forecast.
12. P42 AI assist and maps — large, and need decisions on data leaving the server and bundled geography.
13. Persistence and P45 — blocked on the D2 decision.

## Spikes before committing a big design

1. **Calculation compile for LOD:** AST → ClickHouse SQL for one `FIXED` LOD, checked against a fixture (the ratio case is done; `CASE` and date parts are not).
2. **Table-calculation order:** a client engine for running total, rank and moving average with addressing and partitioning, with filter-order rules written down.
3. **Action graph:** one selection filtering two sheets with explicit field mappings ([p24c-cross-widget-filtering.md](p24c-cross-widget-filtering.md)).
4. **Scale:** P95 latency of the aggregate path on a large and an unindexed table, with and without the result cache.

Risks are listed in [platform.md](platform.md#open-risks).

## Guards every item must keep

- Read-only against ClickHouse; every identifier validated against the live catalog and quoted; every value bound; every result bounded ([golden-rules.md](../conventions/golden-rules.md), rules 1–3).
- No server-side persistence unless [platform.md](platform.md) records a decision.
- Single user, browser-held state; ClickHouse is the only data source; no uploads, extracts, accounts or publication ([out-of-scope.md](out-of-scope.md)).
- Self-hosted, framework-free frontend, no CDN; a new library is vendored with a written reason.
- A workbook stores specifications and metadata, never data, credentials or executable code.
- Every state-changing edit is undoable; the grain and active filters stay visible in words; everything draggable has a keyboard path; unavailable options say why.
- Not a Tableau clone: no `.twb`/`.hyper` compatibility, no Tableau branding, no claim of identical regression or forecast output.
- Design tokens only, `hidden` for visibility, never colour alone.
- Done means [definition-of-done.md](../conventions/definition-of-done.md): update the feature doc and delete the entry here.

## Known unknowns

- The inventory status was read from the code, not from a running app; a feature that exists but is broken would show as built, so runtime behaviour per requirement is unverified.
- There is no traceability matrix of requirement ID → status → test; this backlog is the status list, and the test column is still to build.

## Out of scope

[out-of-scope.md](out-of-scope.md) lists what is deliberately excluded. It is not backlog.
