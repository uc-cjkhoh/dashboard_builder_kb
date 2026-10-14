# Roadmap — Power BI & Looker Studio parity (open phases)

Not built yet. Their order among the other phases, and the coverage table, are in
[roadmap.md](roadmap.md#recommended-order); the same guards apply
([roadmap.md § Guards](roadmap.md#guards-for-every-phase)). From a gap review against Tableau, Power BI
and Google Looker Studio (2026-10-13). Built: P39 bookmarks + URL actions ([workbook.md](../features/workbook.md#export--import)), P40 (field choices + shared filters, built without P30 / P32 — [worksheet.md](../features/worksheet.md#shelves--pills)), P41 (themes & presentation — [tokens.md](../design/tokens.md#workbook-themes-p41), [layout.md](../design/layout.md#full-screen--print)), P36 (more chart types — [worksheet-charts.md](../features/worksheet-charts.md#chart-types)), P35 (period comparison & scorecards —
[worksheet-encodings.md](../features/worksheet-encodings.md#date-range--comparison)) and P37 (conditional
formatting — [worksheet.md](../features/worksheet.md#table-view--a-true-rows--columns-crosstab)). When a phase ships, move its description to
[features/](../features/worksheet.md) and delete it here.

## P38 — Drill-through & report tooltips

- **Drill-through:** right-click / menu on a mark → "Go to <dashboard>" opens a target dashboard with the
  mark's dimension values applied as bound filters, plus a Back button.
- **Report tooltips:** a dashboard marked as a tooltip renders, filtered to the hovered mark, inside the
  chart's tooltip (small, cached, latest-wins).
- Depends on **P24** (dashboards as pages) for a natural target.
- **Done when:** drill-through from a bar opens the target filtered and Back restores the source; a
  tooltip page shows filtered content without blocking the chart.

## P39 — Parameter & set actions

Bookmarks and URL actions are built ([workbook.md](../features/workbook.md#export--import),
[worksheet-encodings.md](../features/worksheet-encodings.md#click-to-filter)). Left:

- **Parameter action** — a click sets a [P32](../features/worksheet-encodings.md#filters) parameter (built) to the mark's value.
- **Set action** — a click adds the mark's member to a [P25](roadmap.md#p25--data-pane-authoring) set.
- Both go on the selection chip beside the link action. **Done when:** each works from a click and is saved.

## P42 — AI assist

- **Explain this point:** for a selected mark, rank which other dimensions' members most change its value
  (bounded group-by queries per candidate dimension, client-side ranking) — Tableau Explain Data /
  Power BI key influencers.
- **Decomposition tree:** drill a measure through dimensions chosen at each step, showing the top
  contributors (re-uses Drill + Other).
- **Ask in plain language:** a question box that proposes a worksheet (fields on shelves, filters, chart
  type) via a Claude model; the model only ever produces a **worksheet spec**, validated like an imported
  workbook — never SQL.
- **Guards:** read-only stays; no data leaves the server unless the user opts in per connection (schema
  names vs. values sent to the model, recorded as a decision); every proposed field is catalog-checked.
- **Done when:** explain-a-point lists the top 5 drivers with their effect; the tree drills three levels;
  a question yields an editable worksheet.

## P43 — Many-to-many & two-way relationships

- Relationships already record cardinality (`N:M` included) but always join inner, one way. Add
  **many-to-many** handling (aggregate each side to the shared key before joining, so measures don't
  double-count) and a per-relationship **filter direction** (single / both). Builds on **P31** join types.
- **Done when:** a sum across an N:M link matches the de-duplicated total, and a filter on the "many" side
  reaches the "one" side only when the link is two-way.
- **Docs to touch:** relationships.md, clickhouse-integration.md (join planner), decisions.md.

## P44 — Custom visuals

- Power BI / Tableau let users add third-party visuals. **Not recommended here as-is:** loading outside
  code breaks [golden rule 10](../conventions/golden-rules.md#10-self-hosted-framework-free-frontend) (self-hosted, no CDN) and the security model.
- If wanted, the safe form is a **vetted, self-hosted set** added to `Core/vendor/` through normal review —
  i.e. more P36-style chart types, not a marketplace.

## P45 — Report lifecycle

- **Versioned workbooks:** keep the last N saves of a workbook with restore; a readable diff of what
  changed (sheets, fields, filters).
- **Test → production:** export a workbook bound to one connection and import it against another
  (connection profiles), reporting fields that don't exist on the target; optional Git storage of
  workbook JSON.
- Needs server-side saving ([competitive-analysis.md #15](competitive-analysis.md#2-master-list--every-capability-ordered-by-difficulty)),
  which [D2](../reference/decisions.md#d2--thin-session-scoped-proxy-no-application-database) currently rules out —
  decide that first. Browser-only versions (local history) are possible without it.
