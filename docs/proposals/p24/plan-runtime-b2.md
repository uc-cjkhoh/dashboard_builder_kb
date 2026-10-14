# P24 plan — Task 3 (part 2): `worksheet-view.js`, editor wiring, checkpoint 24a

Part of the [P24 plan](plan-overview.md). Continues Task 3 from [plan-runtime-b.md](plan-runtime-b.md) — read
its Interfaces, inventory and Steps 1–4 first (they define `$N`, `$S`, `$D`, `blocks.py` and the tests).

#### two-views

`tests/browser/checks/two-views.mjs` (Step 1 creates it; Review Focus #2 — one view's gate must not abort
another's query):

```js
// P24a (Review Focus #2): two view-only worksheet-views in one scope render side by side — neither view's
// latest-wins gate aborts the other's query; the same sheet twice also draws twice.
export async function run({ page, baseUrl, queries }) {
  const aborted = [];
  page.on("requestfailed", (r) => { if (r.url().includes("/api/query")) aborted.push(r.failure()?.errorText ?? "failed"); });
  await page.goto(`${baseUrl}/`);
  await page.waitForTimeout(1200);
  const before = queries.length;
  const r = await page.evaluate(async () => {
    const { createWorksheetView } = await import("/features/Dashboard/worksheet-view.js");
    const { hasChartInstance } = await import("/features/Dashboard/chart.js");
    const { emptySheet } = await import("/features/Core/store.js");
    const box = (left) => {
      const chart = document.createElement("div"), notice = document.createElement("div");
      chart.style.cssText = `position:fixed;top:0;left:${left}px;width:480px;height:320px`;
      document.body.append(notice, chart);
      return { chartEl: chart, noticeEl: notice };
    };
    const f = (column, category, extra = {}) => ({ db: "shop", table: "orders", column, category, ...extra });
    const a = box(0), b = box(500);
    const sheetA = { ...emptySheet(), chartType: "bar", columns: [f("region", "text")], rows: [f("sales", "numeric", { agg: "sum" })] };
    const sheetB = { ...emptySheet(), chartType: "line", columns: [f("city", "text")], rows: [f("profit", "numeric", { agg: "sum" })] };
    const va = createWorksheetView({ ...a, interactive: false }), vb = createWorksheetView({ ...b, interactive: false });
    await Promise.all([va.run(sheetA, "ws#901"), vb.run(sheetB, "ws#901")]); // started together, one scope
    const drawn = [hasChartInstance(a.chartEl), hasChartInstance(b.chartEl)];
    await Promise.all([va.run(sheetB, "ws#902"), vb.run(sheetB, "ws#902")]); // the same sheet twice
    const same = [hasChartInstance(a.chartEl), hasChartInstance(b.chartEl)];
    va.dispose();
    const afterDispose = [hasChartInstance(a.chartEl), hasChartInstance(b.chartEl)];
    vb.dispose(); a.chartEl.remove(); b.chartEl.remove(); a.noticeEl.remove(); b.noticeEl.remove();
    return { drawn, same, afterDispose };
  });
  const sent = queries.length - before;
  return [
    { name: "two views in one scope both draw", ok: r.drawn.join() === "true,true", detail: JSON.stringify(r) },
    { name: "each view sent its own /api/query and none was aborted", ok: sent >= 2 && aborted.length === 0, detail: `sent ${sent}, aborted ${aborted.join(", ")}` },
    { name: "the same sheet in two views draws in both", ok: r.same.join() === "true,true", detail: JSON.stringify(r) },
    { name: "disposing one view keeps the other's chart", ok: r.afterDispose.join() === "false,true", detail: JSON.stringify(r) },
  ];
}
```

- [ ] **Step 5: Assemble `worksheet-view.js`.** Write `$S/view-head.js`:

```js
// The worksheet query-and-render path (P24a), moved out of dashboards.js: plan → bounded query (latest-wins,
// cached per scope) → chart / table / KPI into one container. The editor makes one interactive view; each
// dashboard widget makes a view-only one. Views never share a gate, a pager or per-render flags.
import { api } from "../Core/api.js";
import { icon } from "../Core/icons.js";
import { toggle, makeButton, toast } from "../Core/ui.js";
import { LIMITS } from "../Core/validate.js";
import { checkFilter, statFilters, withCategories, TEXT_VALUE_TYPES } from "./filter-rules.js";
import { roleOf, COLOR_SPLIT_TYPES, STAT_SINGLE_TABLE, chartIssue, TEXT_VALUE_HINT, COLOR_SPLIT_HINT, statFieldHint } from "./show-me-rules.js";
import { metaOf, defaultFormat } from "../Core/store.js";
import { renderChart as renderSeriesChart, disposeChart, hasChartInstance, sizeChart, focusSeries, animateNextChart } from "./chart.js";
import { makeValueFormatter, makeCategoryFormatter } from "../Core/format.js";
import { createLatestGate, createResultCache, requestKey, isAbortError, truncationNotice } from "./query-runner.js";
import { COMPARE_TYPES, resolveRange, compareRange, compareName, changeOf, toneOf, pctText, alignCompare, targetProgress } from "./period-model.js";
import { CF_TONE_CHOICES, CF_OP_CHOICES, TONE_ICON, measureKey, extentOf, scaleColors, barGeometry, matchRule, isActive, midpointOf } from "./conditional-model.js";
import { isGroupingPart, labelParts } from "./date-parts.js";
import { applyTableCalcs, isCalc } from "./table-calc.js";
import { REF_CHOICES, TREND_CHOICES, refValue, trendSeries, combine } from "./analytics-model.js";
import { withOther, bucketNotice, tableProgress, needsNextPage, OTHER_TYPES } from "./scale-model.js";
import { categoryOf, toFilter, pv, measureName, marksOf, SCATTER_TYPES, scatterSymbol, sameField, cmpValues, colorMode,
  planDims, planMeasures, P36_TYPES, MAX_PANELS, COLOR_USES, ANALYTICS_TYPES, CLICK_TYPES, primaryDim, isDrillActive,
  chartOrientation, sharedNote, periodNotice, buildPlan } from "./sheet-plan.js";

// One result cache for every view: a widget and its worksheet tab share results (scopeId = worksheet id).
export const resultCache = createResultCache();

// hooks (editor only; a widget passes none): onSelect(field, raw) — a mark click on the primary
// dimension; onDrill(raw) — the same click while a drill hierarchy is active; onLegendSelect(sheet,
// field, raw, again) — a legend click on a member (again = the second click on the same item).
export function createWorksheetView({ chartEl, noticeEl, statusEl = null, interactive = true, hooks = {} }) {
  const gate = createLatestGate();
  let tablePager = null;       // { scopeId, key, plan, rows, total, loading, ctl, first } — the table's loaded pages
  let legendFocus = null;      // P29: the highlighted legend item, or null
  let calcPercent = new Set(); // P27: result measure indexes whose values are percentages
  let extraNotice = null;      // a line the last render wants in the notice (e.g. the panel cap)
  let bucketedKey = null;      // the group key the last result bucketed by date grain (not click-filterable)

```

  and `$S/view-tail.js`:

```js
  return {
    run,
    resize() { if (hasChartInstance(chartEl)) sizeChart(chartEl, null); },
    cancel() { gate.cancel(); },
    clearFocus() { legendFocus = null; },
    dispose() {
      gate.cancel();
      tablePager?.ctl?.abort(); tablePager = null;
      legendFocus = null;
      chartEl.onscroll = null;
      disposeChart(chartEl);
    },
  };
}
```

```bash
V=src/DashboardBuilder/Features/Dashboard/worksheet-view.js
python3 $S/blocks.py $D cut "// The status bar under the chart" "// --- presentation (P41)" "// P28: rename a result's" \
  "// P27: the table-calculation editor" "// The comparison result for" "// Wire a zone as a field-only" \
  "// --- chart ---" "// Toggle the click selection" "// Pivot a Color-encoded result" "// The Format card's editor: pick" > $S/vclosure.js
python3 $S/blocks.py $D cut "function el(tag" "// --- export helpers (P13)" "// --- crosstab (pivot) helpers" "function select(options" > $S/vbottom.js
{ cat $S/view-head.js $S/vclosure.js $S/view-tail.js; echo; sed -E 's/^function (el|iconSpan|hint)\(/export function \1(/' $S/vbottom.js; } > $V
```

- [ ] **Step 6: Rebind the moved code to the view.** Edits in `$V` (the closure blocks keep their indent):
  1. `runChart`'s first three lines (`async function runChart() {` / `const dash = activeWorksheet();` /
     `if (!dash) return;`) become `async function run(sheet, scopeId, { fresh = false } = {}) {` /
     `if (!sheet) return;` / `if (fresh) { tablePager?.ctl?.abort(); tablePager = null; } // Refresh: the table starts over`.
  2. `const s = dash.sheet;` → `const s = sheet;`; delete the line `const fresh = freshNext; freshNext = false;`.
  3. `setStatusBar`: `const bar = document.getElementById("ws-statusbar");` → `const bar = statusEl;`.
  4. `renderColorSplit(type, result, format, fmtCat)` → `renderColorSplit(sheet, type, result, format, fmtCat)`
     (definition + its one call in `renderChart`); delete its line `const sheet = activeWorksheet()?.sheet;`.
  5. `selectHandler`: guard `if (!interactive || !dimField || !CLICK_TYPES.has(type) || bucketedKey === 0) return undefined;`;
     `drillDown(raw)` → `hooks.onDrill?.(raw)`; `toggleSelection(dimField, raw)` → `hooks.onSelect?.(dimField, raw)`.
  6. Replace the whole `legendHandler` with:

```js
  function legendHandler(sheet, field, rawByName) {
    return {
      focus: legendFocus,
      onLegend: (name) => {
        const again = legendFocus === name;
        legendFocus = again ? null : name;
        const raw = rawByName.get(name);
        if (interactive && field && raw !== undefined && raw !== null && bucketedKey === null) hooks.onLegendSelect?.(sheet, field, raw, again);
        else focusSeries(chartEl, legendFocus, sheet.chartType);
      },
    };
  }
```

  7. Scope renames: `sed -i -E 's/\bdash\.id\b/scopeId/g; s/\bdashId\b/scopeId/g; s/\(dash, /(scopeId, /g; s/\bresults\./resultCache./g' $V`
     (`fetchCompare`, `runTable`, `fetchCached`, `runStatChart` now take `scopeId`; the pager keys on it).

  Check: `grep -nE "\bdash\b|activeWorksheet|activeDashboard|commit\(|drillDown|toggleSelection|freshNext|getElementById" $V`
  → no output. `$N --check $V` → no output. `wc -l $V` → ≈ 1 025.

- [ ] **Step 7: Wire the editor (`$D`).**
  1. Replace the lines from `// Latest-wins queries + recent results per dashboard` through `let tablePager = null;`
     (comment, `history`, `lastSnap`, `gate`, `results`, pager comment, `tablePager`) with:

```js
  // The chart pane is one interactive worksheet-view (worksheet-view.js): it owns the latest-wins gate, the
  // table pager and the per-render flags; results are cached per worksheet in the shared resultCache.
  const history = createHistory(); // P23 undo / redo per dashboard
  const lastSnap = new Map();       // dashId → the sheet as last committed (the "before" of the next edit)
  const wsView = createWorksheetView({ chartEl, noticeEl, statusEl: document.getElementById("ws-statusbar"),
    interactive: true, hooks: { onSelect: toggleSelection, onDrill: drillDown, onLegendSelect: legendSelect } });
```

  2. `sed -i -E '/^  let (legendFocus|calcPercent|extraNotice|bucketedKey|freshResult) = /d' $D`.
  3. `sync()`: `legendFocus = null; // P29…` → `wsView.clearFocus(); // P29…`; `gate.cancel(); shownDash = null;`
     → `wsView.cancel(); shownDash = null;`. `selectionChip`'s clear: `s.selection = null; legendFocus = null;`
     → `s.selection = null; wsView.clearFocus();`. `refreshButton`: `results.clear(dash.id); tablePager?.ctl?.abort();
     tablePager = null; freshNext = true; runChart();` → `resultCache.clear(dash.id); freshNext = true; runChart();`.
  4. After the `const commitQuiet = …;` line add the editor's `runChart` (every existing call site — `sync`, the
     `worksheet:changed` / `entity:loaded` / theme / `prefers-color-scheme` / `fields:changed` /
     `parameters:changed` listeners, `refreshButton` — keeps calling `runChart()` unchanged):

```js

  // --- chart: one interactive worksheet-view runs the query and draws (worksheet-view.js) ----------
  function runChart() {
    const dash = activeWorksheet();
    if (!dash) return;
    const fresh = freshNext; freshNext = false;
    return wsView.run(dash.sheet, dash.id, { fresh });
  }
```

  5. Before `// Toggle the click selection` add (moved out of the old `legendHandler`):

```js
  // P29: a legend click on a dimension member selects it; a second click on the same item clears it.
  function legendSelect(sheet, field, raw, again) {
    const dash = activeWorksheet();
    if (!dash) return;
    if (again) sheet.selection = null;
    else {
      const fmtCat = makeCategoryFormatter(sheet.format ?? defaultFormat());
      sheet.selection = { db: field.db, table: field.table, column: field.column, value: raw,
        label: `${nameOf(field)} = ${fmtCat(raw)}`, action: null };
    }
    commit(dash, sheet);
  }

```

  6. Imports: add `import { createWorksheetView, resultCache, el, iconSpan, hint } from "./worksheet-view.js";`;
     the `sheet-plan.js` import becomes `{ categoryOf, isDateOnlyColumn, measureName, SCATTER_TYPES, sameField,
     colorMode, planDims, planMeasures, sortTargets, CHART_LIKE, NO_AXES, TARGET_TYPES, COLOR_USES,
     ANALYTICS_TYPES, CLICK_TYPES, isDrillActive, showMeCounts, keyOf, columnsCache, sharedNote, pv,
     periodNotice, buildPlan }`; delete the whole `query-runner.js` import and these names — show-me-rules:
     `COLOR_SPLIT_TYPES chartIssue TEXT_VALUE_HINT COLOR_SPLIT_HINT statFieldHint`; filter-rules: `statFilters
     TEXT_VALUE_TYPES`; chart.js: `renderChart as renderSeriesChart, disposeChart, animateNextChart, focusSeries`
     (keep `exportChart, hasChartInstance, sizeChart`); format: `makeValueFormatter`; period-model: `compareName
     changeOf toneOf pctText alignCompare targetProgress`; conditional-model: `TONE_ICON extentOf scaleColors
     barGeometry matchRule midpointOf`; date-parts: `isGroupingPart labelParts`; table-calc: `applyTableCalcs`;
     analytics-model: `refValue trendSeries combine`; scale-model: `withOther bucketNotice tableProgress
     needsNextPage OTHER_TYPES`. Unused-import check (prints names that appear only once):
     `$N -e 'const s=require("fs").readFileSync(process.argv[1],"utf8");const n=[...s.matchAll(/^import \{([^}]+)\}/gm)].flatMap(m=>m[1].split(",")).map(x=>x.trim().split(/\s+as\s+/).pop()).filter(Boolean);console.log(n.filter(x=>s.split(new RegExp("\\b"+x+"\\b")).length===2).join(" ")||"none")' $D`
     → `none`.

- [ ] **Step 8: Verify (24a done-when).** `$N --check` on `$D`, `$V`, `$P` → no output. `$N --test tests/js/*.test.mjs`
  → all pass. `dotnet test` → unchanged and green. Browser (dev server up): `NODE_PATH=<scratch>/node_modules
  $N tests/browser/run.mjs` → every line PASS in light and dark, incl. the four `two-views` lines; last line
  `N/N passed`. Nothing moved is left behind —

```bash
grep -cE "^\s*(async )?function (buildPlan|buildJoins|relationshipGraph|bfs|planDims|planMeasures|sortTargets|run|runTable|runStatChart|fetchCached|fetchCompare|loadingView|markFresh|setNotice|setStatusBar|speedNotice|invalidFilterNotice|aliasNames|renderChart|renderP36|renderColorSplit|renderHeatmap|renderTreemap|renderScatterShapes|pathOrderedRows|marksChannels|markFieldValues|selectHandler|legendHandler|kpiView|sparkline|crosstabTable|conditionalFor|cfPalette|formattedCell|conditionalLegend|periodFilters|periodNotice|sharedSkipped|sharedNote|tupleKey|uniqueTuples|expandLeaves|runs|levelSpans|el|hint|warn|iconSpan|categoryOf|isDateOnlyColumn|measureName|colorMode|cmpValues|primaryDim|isDrillActive|drillActiveDim|drillPathFilters|pagesFilter|chartOrientation|showMeCounts)\(" $D
grep -nE "^\s*(const|let) (gate|results|tablePager|legendFocus|calcPercent|extraNotice|bucketedKey|freshResult|joinNotices|pv|col|keyOf|splitKey|columnsCache|marksOf|toFilter|fieldId|SCATTER_TYPES|CHART_LIKE|COLOR_USES) " $D
```

  → `0`, then no output; `grep -n "function runChart" $D` → one line (the 6-line wrapper). Line counts
  (`wc -l $D $V $P`): `dashboards.js` ≈ 3 400 → ≈ 2 090; `worksheet-view.js` ≈ 1 025; `sheet-plan.js` ≈ 356.
  Manual spot check in the dev app: click a bar (selection chip), click a pie legend member (selects), drill a
  2-level hierarchy, page a Table by scrolling, Refresh — each behaves as before.

- [ ] **Step 9: Commit.**

```bash
git add src/DashboardBuilder/Features/Dashboard/{sheet-plan,worksheet-view,dashboards}.js tests/js/sheet-plan.test.mjs tests/browser/checks/two-views.mjs
git commit -m "Extract worksheet-view and sheet-plan from the worksheet editor (P24a)

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"
```

## Checkpoint — 24a shippable

24a is a pure refactor, so it can ship alone. From the app root on branch `p24-dashboards`:

1. `dotnet build -c Release` → `0 Error(s)`; `dotnet test` → all pass; `$N --test tests/js/*.test.mjs` → all
   pass; `NODE_PATH=<scratch>/node_modules $N tests/browser/run.mjs` → `N/N passed` (light + dark: every P22
   check, `two-charts`, `two-views`).
2. `git diff --stat main...HEAD -- '*.cs' '*.cshtml' '*.csproj'` → empty (no server change expected).
3. **STOP and ask the user:** "24a (chart.js per container, store `tabs` + worksheet renames, `worksheet-view.js`
   + `sheet-plan.js`) is green and behaves as before. Merge it into `main` and deploy it on its own now, or
   carry on to 24b on this branch?" Report the API additions (`cancel()`, `clearFocus()`, `sheet-plan.js`).
4. Only on "yes": `git checkout main && git merge --no-ff p24-dashboards`, then
   `dotnet publish src/DashboardBuilder/DashboardBuilder.csproj -c Release -o publish`. With step 2 empty, the
   asset-only deploy (no restart, no session loss) is
   `cp -r publish/Features/* /var/www/webapps-dev/dashboardbuilder/Features/`; if any `.cs` / `.cshtml` did
   change, use stop → `cp -r publish/. /var/www/webapps-dev/dashboardbuilder/` → start instead
   ([deployment.md](../../operations/deployment.md)). Verify:
   `curl -sk -o /dev/null -w '%{http_code}\n' https://127.0.0.1:8443/dashboardbuilder/` → `200` and
   `…/dashboardbuilder/features/Dashboard/worksheet-view.js` → `200`; then `git checkout p24-dashboards &&
   git merge main` and continue with Task 4 ([plan-model.md](plan-model.md)).
