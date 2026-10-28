# P24c — Cross-widget filtering on dashboards

A proposal, not yet built. Third phase of P24, after 24a + 24b ([dashboards.md](../features/dashboards.md): worksheet views and
multi-worksheet dashboards). It closes
inventory item **T08-19** (use a sheet as a filter), the last P0 dashboard gap
([dashboards.md](dashboards.md)).

## Goal

On a dashboard, clicking a mark in one worksheet widget filters the other worksheet widgets to that value —
the "one sheet filters the other" step of Journey A in the [journeys](journeys-and-releases.md#journeys-and-acceptance-scenarios).

## Non-goals

- No configurable actions (source/target pickers, linking fields — T08-20), no hover or menu triggers (T08-22), no
  highlight action across widgets (T08-21), no multi-mark selection (T08-23), no clear-behaviour options (T08-24).
  Each is a later increment on this one.
- No drill or Pages inside a widget; no filter controls on the dashboard; no cross-dashboard actions.
- No server change, no new endpoint, no workbook format change: the cross-filter is **transient** and is never
  saved, exactly like `sheet.selection` today.
- No mark picking by keyboard. ECharts marks are pointer-only today; this phase does not change that.

## Decisions

| # | Decision | Why |
|---|---|---|
| C1 | Clicking a mark in a **source** widget sets a **dashboard selection** `{ db, table, column, value, label, sourceWidgetId }` taken from the widget's primary dimension, by the same `selectHandler` rules and chart types as [D16](../reference/decisions.md#d16--click-to-filter-is-a-select-then-act-worksheet-selection). Legend-member clicks are **not** sources. Only the widget that was clicked is exempt from the filter, so a second copy of the same worksheet on the dashboard is a target like any other. | One selection model for worksheet and dashboard; the widget id makes C2 and C6 well defined. |
| C2 | The selection **filters the other widgets immediately** (`column = value`); the source widget is **not** filtered and shows the selected mark with the others dimmed. **Dimming is new rendering work** (today a selection shows only as a chip): a render-only restyle of the cached chart, no re-query, for the D16 chart types where ECharts can style one datum; where it can't, the chip alone marks the selection. | D16 chose select-then-act because on a single view self-filtering collapses the chart. With other widgets as targets, acting at once is what the user expects, and the source keeps its context. |
| C3 (decided 28 Oct 2026: keep the narrow rule) | A target applies the filter **only if the column's table is already in that widget's query** — the shared-filter rule ([worksheet-encodings.md § Shared filters](../features/worksheet-encodings.md#filters)); it never forces a join. **Consequence:** the sheets that should react to each other must share the field's table (Tableau's filter actions also need a shared field). A bar by `customers.country` does not filter a line of orders by month that never uses `customers`; that widget shows the note. A widget it can't reach says so inside the widget ("customers.country: selected on another sheet, not applied here — its table isn't in this view."). | Golden rule 3 (no accidental joins or fan-out) and one familiar explanation. |
| C4 | **One selection per dashboard.** A click elsewhere replaces it; clicking the selected mark again clears it. | Smallest model that satisfies T08-19; multi-select comes with T08-23. |
| C5 | A **chip** in the dashboard header shows `Filtering by customers.country = DE — ✕`. ✕ clears it. | State must be visible and escapable; never colour alone ([golden rule 9](../conventions/golden-rules.md#9-never-colour-alone)). |
| C6 | The selection lives in the Board's in-memory state keyed by dashboard id. It **clears** when the dashboard tab is left, when its source widget is removed, when the source worksheet's primary dimension changes, and on a workbook open. | Transient by design; avoids a stale filter nobody can see. |
| C7 | Widgets **lift only B4's selection ban**, as a view mode that selects but never drills (`interactive: "select"`; a click selects the current primary dimension even if the worksheet has a drill). In a **target**, the dashboard selection **replaces** the worksheet's own click selection in the plan; drill path and page still apply as in its tab. | Keeps the 24b contract (a widget draws its worksheet as the tab does) and keeps the filter count inside the server's 20: 8 own + 4 shared + 5 drill + 1 page + 1 period + 1 selection. |
| C8 | A null or unmappable mark (types D16 excludes) is a no-op. Table widgets don't select. | Same as D16. |

## Behaviour

1. Click a bar in widget A. A's mark is selected (others dim) and the chip appears.
2. Every other worksheet widget re-queries with the extra bound filter and redraws; widgets that can't apply it
   show their **unfiltered** data and the note — never a result left over from an earlier selection. Each widget queries independently, so one failure doesn't affect
   another.
3. Changing the selection re-queries only the targets, never the source; clearing re-queries the targets to
   their unfiltered state (a cache hit when the unfiltered result is still cached).
4. Switching to the worksheet tab (Edit) shows the worksheet unchanged; the dashboard selection is not applied
   there.

## Sequencing

24c is **its own plan**, built after the 24a + 24b checkpoint (Task 10 of the archived plan) on a separate branch so it can be reviewed alone. It relies on `hooks.onSelect` and `createWorksheetView` exactly as the archived plan defines them. The three amendments below are written out as **Task 0** of the [P24c plan](p24c-plan.md) and applied to the 24a + 24b plan before its Task 3.

## Code

| File | Change |
|---|---|
| `Features/Dashboard/dashboard-select.js` | **new, pure** — build a selection from a click, decide applicability for a plan, build the chip label and the not-applied note. |
| `Features/Dashboard/sheet-plan.js` | `buildPlan(sheet, period, { crossFilter })` appends the bound filter when its table is in `involved`; reports `notApplied`. |
| `Features/Dashboard/worksheet-view.js` | `run(sheet, scopeId, { fresh, crossFilter })`; `setSelected(selection \| null)` restyles from the cached option; shows the note; emits `onSelect`. |
| `Features/Dashboard/chart.js` | per-datum dimming for a selected value (new). |
| `Features/Board/board.js` | holds the selection per dashboard, passes `onSelect`, re-runs the targets, renders the chip, applies C6 clears. |
| `Features/Board/board.css` | chip and dimmed-source styles from tokens only. |
| tests | `tests/js/dashboard-select.test.mjs` (new); `sheet-plan` cases; browser checks below. |

## Testing

- **Pure:** selection from each supported chart type; null and unmappable no-ops; applicable vs not applicable by
  table; chip label; filter count stays ≤ 20 with every worksheet filter, shared filter and period in use.
- **Browser (headless, mocked API, light and dark):** click in A sends B's query with the extra filter and not
  A's; the chip appears and clears; a widget on an unrelated table shows the note and keeps its data; a second
  click replaces; leaving and returning clears; removing the source widget clears; every 24a/24b check still passes.
- `dotnet test` unchanged and green.

## Changes the archived P24a + 24b plan needs

- **Re-render events.** The app now has a light/dark toggle (`Core/scheme.js`, event `scheme:changed`). Wherever the plan
  re-renders live views on `theme:changed`, also re-render on `scheme:changed`.
- **`dashboards.js` drift.** The plan's line references predate the uncommitted scheme changes in the app tree
  (`dashboards.js` now listens to `scheme:changed`); re-anchor by function name, not line number, before Task 3.
- **Icons.** Task 7 adds the `dashboard` icon; `icons.js` and `tests/js/icons.test.mjs` also carry the scheme-toggle
  changes, so rebase on them.

## Plan

[p24c-plan.md](p24c-plan.md).

## Docs

`features/dashboards.md` (from 24b) gains a "Cross-widget filtering" section; `reference/decisions.md` gets D27 and
D16's "same selection is the basis for cross-worksheet filtering" is answered; `reference/data-model.md` notes the
selection is transient; `backlog/` loses this file and the plan.

## Done when

Two worksheet widgets on a dashboard: a click in one filters the other with the source unchanged and the chip
showing the filter; a widget that can't apply it says why; clearing restores it; nothing is saved to the
workbook; all earlier suites and checks green; the KB updated and this file deleted.
