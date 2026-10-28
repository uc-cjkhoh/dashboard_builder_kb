# P24c Implementation Plan — cross-widget filtering

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** On a dashboard, a click on a mark in one worksheet widget filters the other worksheet widgets to that value, with the source dimmed to the selected mark and a chip showing the filter.

**Architecture:** A pure module `dashboard-select.js` owns the selection model. `sheet-plan.js` gains a `crossFilter` option on `buildPlan` that replaces the worksheet's own click selection. `worksheet-view.js` gains a select-only mode and a `selected` option; `chart.js` gains one pure dimming helper. `Features/Board/board.js` holds the per-dashboard selection and re-runs the targets. No server, store-shape or workbook-format change.

**Tech Stack:** vanilla ES modules, ECharts (self-hosted), `node:test`, the headless-Chromium harness in `tests/browser/` built by 24a Task 1.

**Spec:** [p24c-cross-widget-filtering.md](p24c-cross-widget-filtering.md). Builds on the built board ([dashboards.md](../features/dashboards.md), [D61](../reference/decisions-dashboards.md)); **24a and 24b are built** (`Features/Board/`, `sheet-plan.js`, `worksheet-view.js` exist).

## Global Constraints

- App root `/unified/user/cj/web_development/prototype/dashboard_builder` (local git repo); branch `p24c-cross-filter` from `main` after 24a + 24b is merged; run commands from the app root.
- JS suite: `~/.nvm/versions/node/v24.20.0/bin/node --test tests/js/*.test.mjs`; .NET: `dotnet test` (must stay green, untouched); browser: `NODE_PATH=~/pw-harness/node_modules ~/.nvm/versions/node/v24.20.0/bin/node tests/browser/run.mjs`. `node --check` every changed module.
- Dev run: `cd src/DashboardBuilder && dotnet run --no-launch-profile --urls http://localhost:5180`; stop with `fuser -k 5180/tcp` — **never** `pkill -f DashboardBuilder.dll`.
- No server change, no new endpoint, **no workbook format change**; the cross-filter is transient and never saved. No framework, CDN or build step; `hidden` for visibility; design tokens only (no hex); never colour alone; the page never scrolls.
- A selection filters a target **only if the selected column's table is already in that widget's query**; it never forces a join (spec C3, decided).
- Server limit: ≤ 20 filters per query. A target's worst case is 8 own + 4 shared + 5 drill + 1 page + 1 period + 1 selection = 20.
- Commit at the end of each task; message ends `Co-Authored-By: Claude Sonnet 5.5 <noreply@anthropic.com>`.

## Review Focus

1. **Two copies of one worksheet on a dashboard** — a click in copy A filters copy B; A is unfiltered. Pinned in Task 5.
2. **The selected value disappears from the source** (its data changed under it) — no dimming, no crash, the chip stays and clears normally. Pinned in Task 1 (`selectedIndexOf` → -1).
3. **A click on a date-grouped chart or on a null mark** — no selection, no chip (D16's rule, kept). Pinned in Task 5.
4. **A target's query fails (502) while a selection is active** — that widget shows its own error, the others still filter, clearing recovers. Pinned in Task 5.
5. **Two clicks in quick succession** — only the second selection's results are drawn in each target (per-view latest-wins). Pinned in Task 5.

---

### Task 0: Amend the 24a + 24b plan (before its Task 3)

The archived plan is frozen, so apply these in the working branch when you reach the named task.

- [ ] **Step 1 (Task 3, `worksheet-view`/editor):** wherever the archived plan re-renders from cache on `theme:changed`, also listen for `scheme:changed` (emitted by `Core/scheme.js`; the editor already does in `dashboards.js`).
- [ ] **Step 2 (Task 3):** locate every code reference in the archived plan by **function name**, not line number: `dashboards.js` has uncommitted scheme-toggle changes after commit `568e3c8`. Run `git status` first; if the app tree is still dirty, ask the owner to commit or stash it.
- [ ] **Step 3 (Task 7):** `Core/icons.js` and `tests/js/icons.test.mjs` also carry the scheme-toggle changes; add the `dashboard` icon on top of them without reverting those.

### Task 1: The selection model (pure)

**Files:**
- Create: `src/DashboardBuilder/Features/Dashboard/dashboard-select.js`
- Test: `tests/js/dashboard-select.test.mjs`

**Interfaces:**
- Consumes: `keyOf(db, table)` from `Dashboard/sheet-plan.js`.
- Produces (all pure):
  - `nextSelection(cur, field, raw, fmtCat, sourceWidgetId)` → selection `{ db, table, column, value, label, sourceWidgetId }`, `null` (same value clicked again), or `cur` unchanged (when `raw` is `null` or `undefined`).
  - `crossFilterOf(sel)` → `{ db, table, column, op: "=", value: String(sel.value), values: null }`.
  - `appliesTo(involvedKeys, sel)` → boolean.
  - `selectedIndexOf(rawByIndex, sel)` → index or `-1`.
  - `chipText(sel)`, `notAppliedNote(sel)` → strings.

- [ ] **Step 1: Write the failing tests** with `field = { db: "shop", table: "customers", column: "country" }`, `fmtCat = String`:
  - `nextSelection(null, field, "DE", String, "w#1")` deep-equals `{ db: "shop", table: "customers", column: "country", value: "DE", label: "customers.country = DE", sourceWidgetId: "w#1" }`.
  - Clicking `"DE"` again with that selection returns `null`; clicking `"FR"` returns a selection with `value: "FR"`; `raw` `null` and `undefined` return the same `cur` object (`assert.equal`).
  - `crossFilterOf(sel)` deep-equals `{ db: "shop", table: "customers", column: "country", op: "=", value: "DE", values: null }`.
  - `appliesTo([keyOf("shop","customers"), keyOf("shop","orders")], sel)` is `true`; with only `orders` it is `false`.
  - `selectedIndexOf(["DE","FR",null], sel)` is `0`; with a numeric selection value `2` and raws `[1, 2]` it is `1` (compared as strings); a missing value or a `null` selection gives `-1`.
  - `chipText(sel)` is `"Filtering by customers.country = DE"`; `notAppliedNote(sel)` is `"customers.country: selected on another sheet, not applied here — its table isn't in this view."`.
- [ ] **Step 2: Run** `node --test tests/js/dashboard-select.test.mjs` → FAIL (module missing).
- [ ] **Step 3: Implement** the six functions in `dashboard-select.js` (no DOM, no store imports).
- [ ] **Step 4: Run** the same command → PASS.
- [ ] **Step 5: Commit** `feat: dashboard selection model (P24c)`.

### Task 2: `buildPlan` takes a cross-filter

**Files:**
- Modify: `src/DashboardBuilder/Features/Dashboard/sheet-plan.js`
- Test: `tests/js/sheet-plan.test.mjs` (from 24a Task 3; reuse its fixture helpers)

**Interfaces:**
- Consumes: `crossFilterOf`, `appliesTo` from Task 1.
- Produces: `involvedTables(sheet, periodRange?)` → `string[]` of `keyOf` keys in query order (the list `buildPlan` already builds as `involved`; extract it so both use one implementation); `buildPlan(sheet, periodRange?, { crossFilter } = {})`.

- [ ] **Step 1: Write the failing tests:**
  - `involvedTables` of a sheet with `orders.amount` and `customers.country` returns both keys, `orders` first.
  - `buildPlan(sheet, undefined, { crossFilter: sel })` with `customers` in the query has the `crossFilterOf(sel)` filter in `plan.filters`; with `customers` not in the query it has none and the plan is otherwise `deepEqual` to `buildPlan(sheet)`.
  - A sheet with `selection: { …, action: "keep", value: "FR" }` plus a `crossFilter` has the cross filter and **not** the sheet's own selection filter.
  - A sheet filled to every slot (8 filters, 4 shared, a 5-level drill path, a page, a period) plus a cross filter yields `plan.filters.length === 20`.
  - Existing 24a oracle tests still pass unchanged.
- [ ] **Step 2: Run** `node --test tests/js/sheet-plan.test.mjs` → the new cases FAIL.
- [ ] **Step 3: Implement** `involvedTables` and the `crossFilter` option; when `crossFilter` is given, skip the sheet's own `selFilters` and append `crossFilterOf` only if `appliesTo(involved, crossFilter)`.
- [ ] **Step 4: Run** the full JS suite → PASS.
- [ ] **Step 5: Commit** `feat: buildPlan cross-filter option (P24c)`.

### Task 3: Dimming the selected mark

**Files:**
- Modify: `src/DashboardBuilder/Features/Dashboard/chart.js`
- Test: `tests/js/chart-dim.test.mjs`

**Interfaces:**
- Produces: `export const DIM_OPACITY = 0.35`; `export function applySelectionDim(option, type, selectedIndex)` → `option`. `renderChart(container, spec)` calls it after `buildOption` when `spec.selectedIndex >= 0`.

- [ ] **Step 1: Write the failing tests** (hand-built option objects):
  - `type "bar"`, `series: [{ type: "bar", data: [1, 2, 3] }]`, index `1` → items 0 and 2 become `{ value, itemStyle: { opacity: DIM_OPACITY } }`; item 1 is still `2`.
  - `type "stacked"` with two series: every series dims items at the non-selected indices.
  - `type "pie"`, `data: [{ name: "A", value: 1, itemStyle: { color: "x" } }, { name: "B", value: 2 }]`, index `1` → A keeps `color: "x"` and gains the opacity; B unchanged.
  - A `null` item stays `null`-valued (`value: null`) and does not throw.
  - `type "line"`, `-1`, and `null` index return an option `deepEqual` to the input.
- [ ] **Step 2: Run** `node --test tests/js/chart-dim.test.mjs` → FAIL.
- [ ] **Step 3: Implement** `applySelectionDim` for `bar`, `stacked`, `pie`, `donut` only (other types: chip only, by spec); wire it into `renderChart`. Do not mutate the input option's shared objects.
- [ ] **Step 4: Run** the full JS suite → PASS.
- [ ] **Step 5: Commit** `feat: dim unselected marks (P24c)`.

### Task 4: The view's select mode

**Files:**
- Modify: `src/DashboardBuilder/Features/Dashboard/worksheet-view.js`

**Interfaces:**
- Consumes: `buildPlan(…, { crossFilter })`, `involvedTables`, `appliesTo`, `notAppliedNote`, `selectedIndexOf`, `renderChart` with `spec.selectedIndex`.
- Produces: `createWorksheetView({ …, interactive: false | true | "select", hooks })`; `view.run(sheet, scopeId, { fresh, crossFilter = null, selected = null })`.

- [ ] **Step 1: Implement** (browser-verified in Task 5; no DOM-free seam beyond Tasks 1–3):
  - `interactive: "select"` builds the existing click handler but never treats a click as a drill, and calls `hooks.onSelect(dimField, raw)`; everything else stays as `interactive: false` (no drill chip, no Pages, no legend selection).
  - `run(…, { crossFilter })` passes it to `buildPlan`; when `crossFilter` is set and `appliesTo(involvedTables(sheet, period), crossFilter)` is false, put `notAppliedNote(crossFilter)` in `noticeEl` and run the plan **without** the filter.
  - `run(…, { selected })` computes `selectedIndexOf(rawByIndex, selected)` and passes it as `spec.selectedIndex`.
  - The existing rule stays: no handler when the date axis is bucketed (`bucketedKey === 0`) or the chart type is outside `CLICK_TYPES`.
- [ ] **Step 2: Run** the full JS suite and `node --check` → PASS (editor behaviour unchanged: `interactive: true` and `false` paths are untouched).
- [ ] **Step 3: Commit** `feat: worksheet view select mode and cross-filter option (P24c)`.

### Task 5: Board wiring, chip, and browser checks

**Files:**
- Modify: `src/DashboardBuilder/Features/Board/board.js`, `_Board.cshtml`, `board.css`
- Create: `tests/browser/checks/cross-filter.mjs` (same shape as the 24b board checks: `export async function run(ctx)`; register it where those are listed in `tests/browser/run.mjs`)

**Interfaces:**
- Consumes: `nextSelection`, `chipText`, `crossFilterOf`; `view.run` options from Task 4; `primaryDim` from `sheet-plan.js`; the Board's `live` map and `rerun(pred)` / `run(it)` helpers.
- Produces: in `board.js`, `let selection = null` per active dashboard (a `Map` keyed by dashboard id), and a chip element `#bd-filter` (`class="bd-chip"`, `hidden` when none) beside the status line.

- [ ] **Step 1: Write the browser check** against the mocked API with `shop.customers` and `shop.orders` related; two worksheets, **both including `customers.country`**, on one dashboard. Assertions, each in light and dark:
  - Click the `DE` bar in widget A → exactly one new `/api/query` is sent, for widget B, whose body contains a filter `{ table: "customers", column: "country", op: "=", value: "DE" }`; none for A. The chip reads "Filtering by customers.country = DE". A's `DE` mark is full opacity and the others are at `DIM_OPACITY` (read the chart's option in the page with `window.echarts.getInstanceByDom(chartEl).getOption()`).
  - Click `DE` again → the chip hides and B re-queries without the filter.
  - A third widget on orders only (no `customers`) shows "customers.country: selected on another sheet, not applied here — its table isn't in this view." and keeps its data; the filter is absent from its query.
  - Same worksheet added twice: a click in copy A filters copy B, not A. *(Review Focus 1.)*
  - Date-grouped chart and a `null` mark: clicking does nothing, no chip. *(Review Focus 3.)*
  - Fail B's query with 502 (`failQuery`), click: B shows its error, the other widget still filters; clear, B recovers. *(Review Focus 4.)*
  - Two clicks 50 ms apart with the first response delayed: the final DOM reflects the second selection only. *(Review Focus 5.)*
  - Leaving the dashboard tab and returning shows no chip; removing the source widget clears it; changing the source worksheet's primary dimension clears it; opening a workbook clears it.
- [ ] **Step 2: Run** the browser harness → the new check FAILS, earlier checks PASS.
- [ ] **Step 3: Implement** in `board.js`: build each widget's view with `interactive: "select"` and `fmtCat` is `makeCategoryFormatter(sourceSheet.format ?? defaultFormat())` (import both from wherever 24a left them; grep for the names); `hooks.onSelect = (field, raw) => { selection = nextSelection(selection, field, raw, fmtCat, it.id); renderChip(); rerunAll(); }`; `run(it)` passes `{ selected: selection }` when `it.id === selection?.sourceWidgetId`, else `{ crossFilter: selection }`; the chip's ✕ sets `selection = null` and re-runs; clear on `disposeAll`, on removal of the source widget, on `worksheet:changed` when `primaryDim` of the source sheet no longer matches the selection's table and column, and on `view:changed` / `tabs:changed`. Style the chip and dimmed source from tokens only; the chip carries an icon and text.
- [ ] **Step 4: Run** the browser harness, the JS suite and `dotnet test` → all PASS.
- [ ] **Step 5: Commit** `feat: cross-widget filtering on dashboards (P24c)`.

### Task 6: Docs and finish

**Files:**
- Modify (KB repo `/unified/user/cj/knowledge/web_development/dashboard_builder`): `docs/features/dashboards.md` (add "Cross-widget filtering"), `docs/reference/decisions.md` (D27; reword D16's last bullet), `docs/reference/data-model.md` (the dashboard selection is transient, never saved), `docs/reference/frontend-modules.md` (`dashboard-select.js`).
- Delete: `docs/backlog/p24c-cross-widget-filtering.md`, `docs/backlog/p24c-plan.md`.

- [ ] **Step 1:** Write the doc changes as current behaviour (no "was/now" wording); remove the P24c entry from `docs/backlog/dashboards.md` and update the Journey A link in `docs/backlog/journeys-and-releases.md`.
- [ ] **Step 2:** Run `python3 .claude/hooks/kb-verify.py --all` in the KB repo; fix anything it reports for the touched files.
- [ ] **Step 3:** Run all three suites once more and attach the browser screenshots (light + dark) for review.
- [ ] **Step 4:** Stop and ask the owner before merging or deploying: the live service `webapps-dev.dashboardbuilder` is stop → copy → start only ([deployment.md](../operations/deployment.md)).
- [ ] **Step 5: Commit** `docs: document P24c, retire its spec and plan` in the KB repo.
