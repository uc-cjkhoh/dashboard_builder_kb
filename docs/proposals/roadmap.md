# Roadmap — what is not built yet

What is **not built yet**, in build order. Built behaviour lives in [features/](../features/worksheet.md);
when a phase ships, move its description there and delete it here
([kb-maintenance.md](../conventions/kb-maintenance.md#when-you-make-a-change)). The longer-range,
platform-level gaps (server-side persistence, auth, event pipeline) are in
[competitive-analysis.md](competitive-analysis.md). P35–P45 came from a gap review against Tableau, Power BI
and Google Looker Studio (2026-10-13) — the ones still open are detailed in [roadmap-bi-parity.md](roadmap-bi-parity.md). Phases P0–P20 are frozen in
[archive/build-plan.md](../../archive/build-plan.md).

## Recommended order

Ranked by how much closer each makes the builder feel to Tableau, per unit of effort. Effort: S = days,
M = 1–2 weeks, L = 3+ weeks.

| # | Phase | Effort | Why this position |
|---|---|---|---|
| 1 | [P22 Show Me](#p22--show-me) | M | recommend-and-place |
| 2 | [P24 Multi-worksheet dashboards](#p24--multi-worksheet-dashboards--stories) | L | the biggest structural gap |
| 3 | [P25 Data-pane authoring](#p25--data-pane-authoring) | L | calculated fields — needs a safe expression whitelist |
| 4 | [P39 Parameter & set actions](roadmap-bi-parity.md#p39--parameter--set-actions) | S | the rest of P39 — parameters exist (P32); set actions wait for P25 sets |
| 5 | [P43 Many-to-many & two-way relationships](roadmap-bi-parity.md#p43--many-to-many--two-way-relationships) | M | after P31 |
| 6 | [P38 Drill-through & report tooltips](roadmap-bi-parity.md#p38--drill-through--report-tooltips) | M | needs P24's pages |
| 7 | [P42 AI assist](roadmap-bi-parity.md#p42--ai-assist) | L | explain a point, key influencers, ask in plain language |
| 8 | [P45 Report lifecycle](roadmap-bi-parity.md#p45--report-lifecycle) | L | versioned workbooks, test → production — needs server-side saving |
| — | [P44 Custom visuals](roadmap-bi-parity.md#p44--custom-visuals) | — | **not recommended** as specified: conflicts with golden rule 10 |

## Guards for every phase

- **Read-only, bounded, identifier-safe** — new values bound, new identifiers catalog-validated + quoted,
  every result clamped ([golden rules 1–3](../conventions/golden-rules.md)).
- `hidden` visibility, design tokens, `--ctl-h` controls, never colour alone.
- Unmet mappings show a **hint**, never an error. Each phase independently shippable.
- Done = [definition-of-done.md](../conventions/definition-of-done.md).

## Coverage vs. Tableau's worksheet workspace

Audited against Tableau Desktop's [workspace anatomy](https://help.tableau.com/current/pro/desktop/en-us/environment_workspace.htm#workspace-area).

| Tableau part | Builder today | Gap |
|---|---|---|
| Data pane (Dimensions / Measures) | field pane with search, rename (display name), default aggregation, hide (P28) | authoring extras → **P25** |
| Date fields | per-pill date part (year … hour, discrete parts) with + / − steps, else Format → Group dates (P26) | — |
| Columns / Rows shelves | multi-pill, reorder, role-convert, agg picker | — |
| Filters shelf | scalar / `in` / `between` / text match / relative date / top-N, bound, plus filter cards (P30) | a range slider (needs a min / max query) |
| Table calculations | quick table calculations on measure pills (P27) — [worksheet.md](../features/worksheet.md#shelves--pills) | custom table-calc formulas → P25 |
| Parameters | workbook parameters (number / text / date; any, list, range) driving filter values, top-N filters and Top N, with controls on the card (P32) | parameter actions → P39 remainder |
| Joins / relationships | inner or left join per drawn link (P31) | many-to-many handling → **P43** |
| Marks card — Color, Size, Label, Detail, Tooltip, Shape, Path, Angle | encodings toolbar | continuous Colour beyond scatter; Size/Shape beyond scatter |
| Mark types | 23 types incl. Square/Circle/Text and the P36 types | Gantt, Density not built; Map out of scope ([D18](../reference/decisions.md#d18--marks-card-and-pages-shelf-are-client-encodings-on-the-existing-query-shape)) |
| Pages shelf | step + autoplay | — |
| Drill-down / hierarchies | single-table Drill tool + breadcrumb | reusable Data-pane hierarchies → **P25** |
| Analytics pane | reference line / band, trend + forecast, totals / subtotals (P21) | clustering; trend on more chart types |
| Show Me | chart-type dropdown + hints | recommend-and-place → **P22** |
| Legends | colour / shape legend + position; click to highlight, select a member, Keep only / Exclude (P29) | — |
| Title / caption / field labels / toolbar / status bar | editable title + caption, status bar, undo / redo, swap, clear, fit (P23) | highlight mode (click-to-select covers it) |
| Sheet tabs — worksheet / dashboard / story | Data Model + one worksheet per tab | multi-worksheet dashboards, stories → **P24** |

### Beyond Tableau's worksheet — Power BI & Looker Studio

| Their feature | Builder today | Gap |
|---|---|---|
| Scorecards with comparison, date range + compare period | built (P35) — [Date range tool](../features/worksheet-encodings.md#date-range--comparison) | — |
| Waterfall, funnel, gauge, bullet, Sankey, small multiples | built (P36) — [chart types](../features/worksheet-charts.md#chart-types) | — |
| Conditional formatting (colour scale, data bars, rules) in tables | built (P37) — [Table view](../features/worksheet.md#table-view--a-true-rows--columns-crosstab) | — |
| Drill-through pages, report-page tooltips | single-table Drill tool | **P38** |
| Bookmarks; URL / parameter / set actions | built (P39): bookmarks + URL actions — [workbook.md](../features/workbook.md#export--import), [worksheet-encodings.md](../features/worksheet-encodings.md#click-to-filter) | parameter / set actions → **P39** remainder (needs P32, P25) |
| Field parameters, synced slicers | built (P40) as pill **field choices** + **shared filters** — [worksheet.md](../features/worksheet.md#shelves--pills), [worksheet-encodings.md](../features/worksheet-encodings.md#filters) | P30 filter cards would give shared filters a card form |
| Report themes, phone layout, full screen, print / PDF | built (P41) — [themes](../design/tokens.md#workbook-themes-p41), [presentation](../design/layout.md#full-screen--print) | — |
| Explain data, key influencers, decomposition tree, Q&A / Copilot / Gemini | — | **P42** |
| Many-to-many and bidirectional relationships | inner join along drawn links | **P43** |
| Custom visuals marketplace | — | **P44** (not recommended) |
| Git integration, deployment pipelines | file Export / Import | **P45** |

> **Biggest architectural gap:** in Tableau a dashboard *composes several worksheets*; here a dashboard
> tab **is** one worksheet (one `sheet`, one chart host). P24 closes it; the others enrich the single
> worksheet.

## P22 — Show Me

Recommend the view types that fit the fields in play and build one in a click.
Spec: [p22-show-me.md](p22-show-me.md).

- A panel lists chart types with the valid ones enabled for the current selection (reusing
  `chartIssue()`), and on pick **auto-places** fields on shelves/encodings.
- **Done when:** with fields selected, applicable types highlight, one click yields the chart with
  sensible placement, and inapplicable types are greyed with the reason.
- Depends on P11-era chart types and the Marks toolbar (both built).

## P24 — Multi-worksheet dashboards & stories

- A dashboard-composition view hosting **several worksheet widgets** (charts, crosstabs, KPI tiles) with
  per-widget size/placement over the one data model; optional **story** points (ordered, captioned
  snapshots).
- Cross-widget filtering reuses the existing `sheet.selection` / filter machinery
  ([D16](../reference/decisions.md#d16--click-to-filter-is-a-select-then-act-worksheet-selection)) via an
  event-bus fan-out.
- Revisit [O1](../reference/decisions.md#open-questions) persistence and O3 composition.
- **Done when:** ≥2 worksheets sit on one canvas, can be arranged/resized and re-query independently, and
  a click in one filters the others; a story sequences views with captions.

## P25 — Data-pane authoring

- **Calculated fields** (a computed SELECT expression), **groups** (members → label), **sets** (named
  member subsets), **bins** (numeric bucketing — the histogram shape), **folders**, and reusable
  **hierarchies** (feeding the Drill tool).
- **Guards (critical):** this is the one phase that lets user text into a SQL *expression*. Evaluate only
  a **whitelisted** set of scalar functions/operators; forbid subqueries, semicolons and any DDL/DML;
  validate every identifier against the live catalog; bind every literal. Record the approach as a new
  decision before building.
- **Done when:** a calculated field works on a shelf; a group and a bin render; a hierarchy feeds Drill.
- **Docs to touch:** clickhouse-integration.md (expression whitelist), data-model.md, decisions.md.

