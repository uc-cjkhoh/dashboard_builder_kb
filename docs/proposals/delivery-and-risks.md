# Delivery order and risks

Part of the [proposal](web-application-proposal.md#9-delivery-and-risks).

## Delivery

Order by dependency, not by chapter. The effort estimates in the previous draft assumed a multi-engineer team building a new product and no longer apply; sizing follows the gap analysis.

```text
Gap analysis (done: gap-analysis.md)
  └─ Calculation engine: AST, validation, compiler, function catalog   (T04)
       ├─ Table calculations (client)                                  (T05-02 … 21)
       ├─ LOD compiler                                                 (T05-22 … 27)
       └─ Parameters everywhere, search box                            (T04-28 … 33)
  └─ Model breadth: join types, unions, groups, hierarchies, metadata  (T02, T03-29)
  └─ Charts and encodings gaps                                         (T03)
  └─ Dashboards: layout, actions, navigation, stories                  (T08)
  └─ Analytics: reference, trend, forecast, k-means                    (T07)
  └─ Maps                                                              (T06)
  └─ Export/presentation, ask-data                                     (T01-24/28/29, T09)
```

Suggested releases, to be confirmed after the gap analysis:

| Release | Contents | Exit |
|---|---|---|
| R0 | Remaining **P0** items (18 of 44; composition and calculated fields are the large ones) | Journey A passes with exact fixture values. |
| R1a | Calculation editor, text/date/logic functions, parameters, remaining P1 chart types, PDF export | Common book examples reproduce without code. |
| R1b | Joins/unions breadth, table calculations, linked actions, floating layout, phone preview | Journeys B and C pass. |
| R2 | LOD, maps, regression, forecast, k-means, stories, chart-in-tooltip | Journeys D and E pass. |
| R3 | Pages playback, set actions, Shapefile/KML, ask-data | Each has a use case, a correctness model and an owner. |

**Four spikes before committing the engine design:**
1. **Calculation compile:** AST → ClickHouse SQL for ratio, `CASE`, date parts and one `FIXED` LOD, checked against a fixture.
2. **Table-calc order:** a client engine for running total, rank and moving average with addressing/partitioning, with filter-order rules written down.
3. **Action graph:** one selection filtering two sheets with explicit field mappings.
4. **Scale:** P95 latency of the aggregate path on a large and an unindexed table, with and without the result cache.

---

## Risks and trade-offs

| Risk | Why it matters | Mitigation |
|---|---|---|
| Wrong aggregation grain | Plausible but wrong numbers. | Typed AST, grain descriptor, golden tests. |
| LOD and filter-order semantics | Subtle interactions between filter classes. | Build after the core engine; conformance fixtures; document differences. |
| Breaking the golden rules | An expression feature that interpolates text breaks injection safety. | AST-only compilation; identifier validation in one place; review every Gateway change against rules 1–3. |
| Workbook growth | Calculations, actions, stories and GeoJSON enlarge `localStorage` entries. | Size limits with a clear error; version and upgrade path; GeoJSON size cap. |
| Client-side analytics on truncated data | Forecasts over a capped result mislead. | Show the truncation notice; refuse a model when the data is truncated. |
| Large dashboards in the browser | Too many live sheets. | Latest-wins query runner, cache, lazy sheets, mark caps. |
| ClickHouse dialect coverage | Percentiles, week rules and nulls differ by function. | One whitelist table; integration tests against a real server. |
| Map data licensing | Basemaps are external by default. | Bundle licensed local data; no service calls. |
| Statistical parity | Output may differ from Tableau. | Publish methods and parameters; fixtures; no parity claim. |
| Scope creep | 229 items is a multi-release product. | Gap analysis first; P0 before P1; written reason for every new library. |

---
