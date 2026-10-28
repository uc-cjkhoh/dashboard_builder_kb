# Backlog: data model and data source

Today relationships are logical, inner or left, one equality pair each ([relationships.md](../features/relationships.md)). Entries are in dependency order. Format: [README.md](README.md#how-to-read-an-entry).

- **Type cast** (IDs: T02-34; priority P0) — Open: only role convert and date parts; no cast between string, number and date. Needs: server cast whitelist. Source: [gap-analysis-detail.md](../proposals/gap-analysis-detail.md).
- **Raw-record preview** (IDs: T02-05; priority P0) — partial: names, types and distinct values only; no row preview. Needs: a new bounded row-level endpoint. Source: [gap-analysis-detail.md](../proposals/gap-analysis-detail.md).
- **View data behind a mark** (IDs: T01-18, T03-31; priority P1) — Open: no view-underlying-rows action; CSV is the aggregated result. Needs: the row-level endpoint above (bounded, identifier-validated). Source: [gap-analysis.md](../proposals/gap-analysis.md).
- **Right and full joins** (IDs: T02-12, T02-13; priority P1) — Open: join type is validated to inner or left only. Needs: validation, SQL builder and dialog changes. Source: [gap-analysis-detail.md](../proposals/gap-analysis-detail.md).
- **Compound joins and key suggestion** (IDs: T02-14, T02-15; priority P2) — Open: manual single-pair equality only; no matching-name suggestion. Needs: none. Source: [gap-analysis-detail.md](../proposals/gap-analysis-detail.md).
- **Union** (IDs: T02-16; priority P1) — Open: no manual union of tables. Needs: a bounded server query shape. Source: [gap-analysis-detail.md](../proposals/gap-analysis-detail.md).
- **P43 Many-to-many and two-way relationships** (priority P1; effort M) — Open: cardinality is recorded but every link joins inner, one way. Aggregate each side to the shared key before joining so measures do not double-count; add a per-relationship filter direction. Needs: join types. Source: the former BI-parity roadmap.
- **Member aliases** (IDs: T02-29; priority P1) — Open: only a field alias exists; no value-to-label mapping. Needs: none. Source: [gap-analysis-detail.md](../proposals/gap-analysis-detail.md).
- **Groups** (IDs: T02-30; priority P1) — Open: no dimension groups (members to a label). Needs: member aliases. Source: the former roadmap.
- **Split and unpivot** (IDs: T02-31, T02-32; priority P1) — Open: no string split, no unpivot of wide columns. Needs: none. Source: [gap-analysis-detail.md](../proposals/gap-analysis-detail.md).
- **Named hierarchies** (IDs: T03-29; priority P1) — partial: an unnamed per-sheet drill path; no reusable model hierarchies or expand/collapse headers. Needs: none. Source: the former roadmap.
- **Field details and copy** (IDs: T02-33, T02-28; priority P1–P2) — Partial: type and role shown, no field-properties panel (sort, semantic role). Open: no copy of a field or values. Needs: none. Source: [gap-analysis-detail.md](../proposals/gap-analysis-detail.md).
- **Indexing and partition guidance** (IDs: T02-37; priority document only) — Open: no guidance for source tables. Needs: none. Source: [gap-analysis-detail.md](../proposals/gap-analysis-detail.md).
