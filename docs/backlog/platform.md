# Backlog: platform decisions and risks

Items here need a decision before work. Format: [README.md](README.md#how-to-read-an-entry).

- **Server-side persistence, accounts and sharing** (priority P3) — work is saved only in the browser and exported files; there are no users, roles, shared workbooks or server-side saved work. [D2](../reference/decisions.md#d2--thin-session-scoped-proxy-no-application-database) currently rules it out; decide that first. Needs: a decision, then an app store and auth.
- **P45 Report lifecycle** (priority P3; effort L) — Open: keep the last N saves with restore and a readable diff; export a workbook bound to one connection and import it against another, reporting missing fields; optional Git storage. Browser-only local history is possible without the decision above. Needs: server-side saving for the full form.
- **P44 Custom visuals** (priority none) — recommended against: loading outside code breaks golden rule 10. The safe form is more vetted, self-hosted chart types, not a marketplace. Needs: a decision to drop or narrow.

## Open risks

- **Wrong aggregation grain** — plausible but wrong numbers; use a typed tree, a grain descriptor and golden tests.
- **LOD and filter-order semantics** — build after the core engine; write conformance fixtures.
- **Breaking the golden rules** — an expression feature that interpolates text breaks injection safety; review every Gateway change against rules 1–3.
- **Workbook growth** — calculations, actions, stories and GeoJSON enlarge `localStorage` entries; set size limits with a clear error.
- **Client analytics on truncated data** — show the truncation notice and refuse a model on truncated data.
- **Large dashboards** — too many live sheets; keep latest-wins runner, cache, lazy sheets and mark caps.
- **ClickHouse dialect coverage** — percentiles, week rules and nulls differ; one whitelist table plus integration tests against a real server.
- **Map data licensing** — bundle licensed local data; no service calls.
- **Statistical parity** — publish methods and parameters; fixtures; make no parity claim with Tableau.
- **Scope creep** — 229 inventory items is a multi-release product; P0 before P1 and a written reason for every new library.

## Workbook additions

New features add fields to the workbook JSON under a new `version` with an upgrade path from the old one; each needs a schema, limits and a migration. On open, a stored reference to a column that no longer exists is reported, not dropped.

| Field | Holds |
|---|---|
| `groups`, `hierarchies`, `sets` | dimension groups, named drill hierarchies, sets |
| `actions` | the dashboard action graph |
| `stories` | ordered steps |
| `clusters` | model settings and seed; labels are recomputed, not stored |

## Decisions to settle

- The workbook version bump and the limits for the fields above.
- Whether LOD compiles to a subquery or a window.
- The mark cap: 5000 groups today, 10,000 proposed ([D24](../reference/decisions.md#d24--showing-all-data-bounded-requests-paging-other-date-grouping)); reconcile.
- Charting additions that need ECharts extensions or a vendored library; new libraries are vendored, each with a written reason (golden rule 10).
