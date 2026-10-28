# Backlog — work not yet built

One place for the undone work, grouped by topic. Built behaviour lives in [../features/](../features/worksheet.md); the remaining source material (requirements, gap analysis, proposal, specs) stays in [../proposals/](../proposals/delivery-and-risks.md).

## Files

| File | Holds |
|---|---|
| [dashboards.md](dashboards.md) | P24a–d, dashboard layout, actions, navigation, P38, P39 remainder |
| [calculations.md](calculations.md) | functions the engine lacks, parameters in formulas, LOD, table-calculation polish, P25 |
| [data-model.md](data-model.md) | joins, union, groups, split, cast, row preview, hierarchies, P43 |
| [charts-and-formatting.md](charts-and-formatting.md) | chart, authoring, formatting and export gaps |
| [analytics-and-maps.md](analytics-and-maps.md) | statistics, forecasting, clustering, P42, maps |
| [platform.md](platform.md) | persistence, P45, P44, open risks |

## How to read an entry

`- **name** (IDs: Txx-nn; priority P0–P3; effort S/M/L if a source states it) — what is missing. Needs: dependency or none. Source: file.`

- IDs are the requirement IDs in [../proposals/tableau-features.md](../proposals/tableau-features.md); entries without an ID come from the roadmaps.
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

## Guards every item must keep

- Read-only against ClickHouse; every identifier validated against the live catalog and quoted; every value bound; every result bounded ([golden-rules.md](../conventions/golden-rules.md), rules 1–3).
- No server-side persistence unless [platform.md](platform.md) records a decision.
- Design tokens only, `hidden` for visibility, never colour alone.
- Done means [definition-of-done.md](../conventions/definition-of-done.md): update the feature doc and delete the entry here.

## Out of scope

[../proposals/tableau-features-excluded.md](../proposals/tableau-features-excluded.md) lists what is deliberately excluded. It is not backlog.
