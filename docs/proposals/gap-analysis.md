# Gap analysis: Dashboard Builder vs the Tableau inventory

Benchmark of the running app against the 229 in-scope requirements in [`tableau-features.md`](tableau-features.md), as set out in the [proposal](web-application-proposal.md). Per-ID evidence is in [gap-analysis-detail.md](gap-analysis-detail.md).

**Method.** Four reviewers each read the app source (`/unified/user/cj/web_development/prototype/dashboard_builder`) for a group of chapters and recorded, per ID, whether the behaviour exists and where. Docs were used for orientation only; code decided. The lead spot-checked the contested rows (T01-12, T01-18, T01-28, T03-05, T03-13, T04-33, T05-08) against the code and changed one (T01-12, open → partial). Statuses on broad rows such as T01-19 to T01-23 are judgement calls; the detail file states the reason for each.

## Result

| | Built | Partial | Open | Total |
|---|---:|---:|---:|---:|
| **All requirements** | **68** | **52** | **109** | **229** |
| P0 | 26 | 11 | 7 | 44 |
| P1 | 40 | 30 | 37 | 107 |
| P2 | 1 | 10 | 56 | 67 |
| P3 | 1 | 1 | 8 | 10 |
| Document only | 0 | 0 | 1 | 1 |

| Chapter | Built | Partial | Open | Total |
|---|---:|---:|---:|---:|
| T01 Workspace and workbooks | 16 | 10 | 2 | 28 |
| T02 Data source and model | 12 | 2 | 12 | 26 |
| T03 Charts and encodings | 20 | 8 | 6 | 34 |
| T04 Calculations and parameters | 8 | 6 | 19 | 33 |
| T05 Table calculations and LOD | 7 | 8 | 12 | 27 |
| T06 Maps | 0 | 0 | 21 | 21 |
| T07 Statistics and forecasting | 4 | 10 | 12 | 26 |
| T08 Dashboards and actions | 0 | 7 | 23 | 30 |
| T09 Consumption and ask-data | 1 | 1 | 2 | 4 |

The authoring core (T01, T03, the data model) is largely there. The gaps cluster in four places: **expressions, dashboard composition, maps, and the advanced statistics**.

## P0: 18 of 44 not yet built

These decide the proposal's Release 0 exit (Journey A: two worksheets, a dashboard, one sheet filtering the other, a ratio calculation).

| Cluster | IDs | State |
|---|---|---|
| Dashboard composition | T08-01, 03, 09, 11, 12, 13, 19 | A dashboard tab holds **one** worksheet. No sheet list, tiling, placement, resize, or cross-sheet filter. This is the unbuilt P24 spec. |
| Calculated fields | T04-11, 13, 14 | No expression editor or engine anywhere. |
| Calculation order | T05-01 | The pipeline (server aggregate, then client table calculation) is implicit and unexplained. |
| Data-source polish | T02-05, T02-34, T04-04 | No raw-record preview, no type cast, `count` counts all rows (no non-null count). |
| Small authoring gaps | T01-11, 19, 20; T03-28 | No duplicate sheet, no tooltip text editor, no per-member colour, exclude only for one clicked value. |

## Gap clusters, in dependency order

1. **Expression engine** — the largest single block, and everything in T05-22…27 (LOD) and T04-12…27 depends on it.
   - **Missing aggregations:** median, percentiles, standard deviation, variance, ATTR (T04-03, 06, 07, 08, 09). The whitelist is count, sum, avg, min, max, countDistinct (`ClickHouseGateway.cs`).
   - **Missing functions and logic:** text, date-difference, `CASE`, `IF`, `IFNULL` (T04-15…18, 22, 24, 25, 27).
   - **Missing editor and parameter use:** the calculation editor and help (T04-11, 12), parameter-driven metrics (T04-31), and LOD (T05-22…27).
2. **Multi-worksheet dashboards (P24)** — all of T08 bar seven partial rows. Needs a layout model first (T08-06…10, 12), then actions (T08-17…24), then device preview, stories and cross-dashboard links (T08-04, 05, 25, 26, 28).
3. **Model breadth** — right and full joins (T02-12, 13), manual union (T02-16), member aliases, groups, split, unpivot (T02-29…32), type cast (T02-34), named hierarchies (T03-29), view data behind a mark (T01-18, T03-31). The last one needs a new bounded row-level endpoint.
4. **Chart gaps** — step/jump lines (T03-05), continuous date axis (T03-07), circle heatmap (T03-10), axis sync (T03-17), measure colour on more marks (T03-19), per-member legend colour and palette reverse (T03-24, 33), filter on an aggregated measure (T03-27), continuous colour scales, marker size/border and worksheet formatting (T01-21…23).
5. **Table-calculation polish** — percentile rank, growth %, per-dimension addressing and partitioning, duplicate-as-crosstab (T05-07, 11, 13…15, 17).
6. **Advanced analytics (P2)** — see below.
7. **Maps (P2/P3)** — all 21 open; no map, geo or GeoJSON code, and no bundled geography.

## Advanced analytics (T07) as built

- **Forecast** is a 3/6/12-step extrapolation of the linear, logarithmic or quadratic trend, fitted in the browser with R² only. It is not exponential smoothing: no seasonality, horizon, missing-value policy or model description (T07-18…23 are open or partial).
- **No clustering** (T07-24…26) and **no confidence or prediction intervals** (T07-09, 10, 17, 22).
- Reference lines, bands and box plots exist in part; the per-ID notes say what each lacks.

## Built, with a caveat

- **T01-28 PDF export** is the browser's print dialog on the single worksheet, not a generated PDF.
- **T03-12 bullet** takes its target from Format, not from a field. **T03-16 dual axis** exists only as the bar-plus-right-axis-line combo.
- **T03-20 size** applies to scatter bubbles only.
- **T04-10 null skipping** is native SQL behaviour with no replace option.
- **T07-01 analytics pane** is a toggled card of selects, not drag-and-drop.
- **T09-16 phone view** is judged built on the phone and touch CSS alone; it has not been run on a device.

## What this changes in the proposal

- **Release 0 is smaller than the inventory suggests:** 18 P0 items, but two of the clusters (composition, calculated fields) are the big ones. Neither can be skipped without failing Journey A.
- **P24 dashboards come before the calculation engine** for a usable demo, but the engine is the larger and riskier build; they are independent and can run in either order.
- **No server-side persistence is needed for anything in this list.** The only new server work is the expression compiler, extra join types and aggregations, a row-level detail endpoint and a column profile endpoint.

## Not audited

- Runtime behaviour: the audit reads code and does not run the app, so a feature that exists but is broken would show as built.
- Test coverage per requirement. The traceability matrix the proposal calls for (ID → status → test) is the next step.
