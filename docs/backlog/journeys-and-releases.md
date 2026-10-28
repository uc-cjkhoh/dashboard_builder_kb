# Backlog: journeys, releases and quality targets

What "done" means for the undone work. A release exits when its journeys pass with exact fixture values. Recommended build order: [README.md](README.md#recommended-order).

## Journeys and acceptance scenarios

**A — Dashboard from ClickHouse tables (P0).** Connect → drag two tables, declare the relationship → build a bar and a line sheet with aggregates and filters → edit tooltip, labels and colours → compose a dashboard → click a mark in one sheet to filter the other (both sheets include the clicked field's table; a sheet that doesn't shows a note instead, [cross-widget filtering](../features/dashboards.md#cross-widget-filtering)) → reload → Export → Import into a fresh browser and reconnect. *Acceptance:* every displayed aggregate equals the fixture's documented totals, including null handling and duplicated source rows; the imported workbook is identical.

**B — Date and KPI analysis (P1).** Date hierarchy at month/day/hour; `SUM(success)/SUM(total)`; target line from a parameter. *Acceptance:* changing a date filter or parameter only re-queries affected sheets; the weighted rate is a ratio of sums.

**C — Joining and shaping (P1).** Join Orders, People and Returns; alias, group, split and recode fields; union two region tables. *Acceptance:* left joins keep unmatched left rows; union column alignment is explicit; source tables are untouched.

**D — Statistics (P2).** Forecast with interval band and model description; k-means with a seed; regression only where the data supports it. *Acceptance:* identical settings and data give identical output; missing-value behaviour is documented.

**E — Map dashboard (P2).** Symbol and filled maps from a geographic field or GeoJSON beside a time series. *Acceptance:* unknown locations are flagged; no request leaves the app origin.

## Releases

| Release | Contents | Exit |
|---|---|---|
| R0 | Remaining **P0** items: type cast, duplicate sheet, tooltip editor, per-member colour, exclude | Journey A passes with exact fixture values. |
| R1a | Text, date and logic functions, parameters in formulas, remaining P1 chart types, PDF export | Common book examples reproduce without code. |
| R1b | Joins and unions breadth, table-calculation polish, linked actions, floating layout, phone preview | Journeys B and C pass. |
| R2 | LOD, maps, regression, forecast, k-means, stories, chart-in-tooltip | Journeys D and E pass. |
| R3 | Pages playback, set actions, Shapefile/KML, ask-data | Each has a use case, a correctness model and an owner. |

## Quality targets

| Dimension | Target | Qualification |
|---|---|---|
| First uncached chart | P95 ≤ 5 s on a designated benchmark table | Hardware and table documented when measured; not a promise for arbitrary servers. |
| Cached filter interaction | P95 ≤ 1 s | Bounded group count. |
| Marks | Aggregate or cap beyond 10,000 marks | The cap is 5000 groups today; reconcile ([platform.md](platform.md#decisions-to-settle)). |

- **Safety additions:** parse GeoJSON defensively; make no network request except to the app origin; keep workbook files free of credentials.
- **Tests:** unit tests for operators, nulls, aggregation, date and week logic, AST validation and limits; golden fixtures with exact SQL and results (duplicates, nulls, joins, missing dates, aliases, rejected functions); `node --test` for table calculations, regression, forecast, seeded k-means and workbook upgrade; visual checks for axis scales, continuous vs discrete dates, legends, map overlap, export size and phone layout; a live smoke against a throwaway ClickHouse ([development.md](../operations/development.md)).
