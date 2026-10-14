# P24 plan — Task 3 (part 1): inventory, failing tests, `sheet-plan.js`

Part of the [P24 plan](plan-overview.md); read its Global Constraints first. Paths are relative to the app
root. Spec: [§ 24a](../p24-dashboards.md#24a--widget-runtime-no-visible-change). Task 3 is long, so it spans
two files: this one (Steps 1–4) and [plan-runtime-b2.md](plan-runtime-b2.md) (Steps 5–9 + the 24a checkpoint).

### Task 3: extract `Dashboard/worksheet-view.js` (and its pure half, `Dashboard/sheet-plan.js`)

**Files:**
- Create: `src/DashboardBuilder/Features/Dashboard/sheet-plan.js` — the query shape (DOM-free; reads the store)
- Create: `src/DashboardBuilder/Features/Dashboard/worksheet-view.js` — the query-and-render path
- Create: `tests/js/sheet-plan.test.mjs`, `tests/browser/checks/two-views.mjs`
- Modify: `src/DashboardBuilder/Features/Dashboard/dashboards.js` — loses ≈ 1 300 lines; creates one view

**Interfaces:**
- Consumes (Tasks 1–2): `chart.js` container-first exports — `renderChart(container, spec)`,
  `disposeChart(container)`, `hasChartInstance(container)`, `sizeChart(container, size | null)`,
  `focusSeries(container, name, type)`, `animateNextChart(container, fresh)`; `store.js` `activeWorksheet()`,
  `worksheet:changed`; the harness `tests/browser/run.mjs` whose checks get `ctx = { browser, page, errors,
  queries, scheme, baseUrl, shots }` (`queries` = every `/api/query` body) and return `[{ name, ok, detail }]`.
- Produces (Tasks 7–9 rely on these exact names):
  - `worksheet-view.js`: `export const resultCache` (the one `createResultCache()`);
    `createWorksheetView({ chartEl, noticeEl, statusEl = null, interactive = true, hooks = {} })` →
    `{ run(sheet, scopeId, { fresh = false } = {}) → Promise, resize(), dispose(), cancel(), clearFocus() }`;
    `hooks = { onSelect(field, raw), onDrill(raw), onLegendSelect(sheet, field, raw, again) }`, every hook
    optional. `interactive: false` → no click handler on marks (no selection / drill) and a legend click only
    highlights; tooltips, legend highlight and table paging stay. Also exports the DOM helpers `el`, `iconSpan`, `hint`.
  - `sheet-plan.js`: `buildPlan(sheet, periodRange?)`, `planDims`, `planMeasures`, `sortTargets`, `sharedNote`,
    `periodNotice`, `pv`, `categoryOf`, `keyOf`, `columnsCache`, the type sets — every name in the inventory below.
- **Additions to the overview's API** (report at the checkpoint): `cancel()` (the editor stops an in-flight
  query when the Data Model opens, without dropping the table's loaded pages — `dispose()` drops them) and
  `clearFocus()` (the editor clears the legend highlight on a tab switch and on "Clear selection"); and the
  new module `sheet-plan.js`, so `buildPlan` is node-testable and neither module imports the other's internals.

**Behaviour notes (24a = no visible change).** A view runs the sheet as stored: its saved selection, drill
depth and Pages member still filter a view-only widget — only *changing* them needs `interactive`. The editor
now consumes its Refresh flag (`freshNext`) on every run; before, a Table / histogram / box-plot run left it
pending for the next chart query — a no-op difference users cannot see.

#### Inventory (line numbers at app commit `568e3c8`; Tasks 1–2 shift them slightly — the steps cut by anchor text)

| Lines | What | Goes to |
|---|---|---|
| 34–51 | `categoryOf`, `isDateOnlyColumn` | `sheet-plan.js` |
| 52–53 | `FILTER_PLACEHOLDER`, `OPS` (dead, left alone) | stays |
| 54–239 | `toFilter`, `measureName`, `fieldId`, `EMPTY_MARKS`, `marksOf`, `SCATTER_TYPES`, `scatterSymbol`, `isNumericField`, `sameField`, `cmpValues`, `colorMode`, `planDims`, `planMeasures`, `sortTargets`, `CHART_LIKE`, `P36_TYPES`, `NO_AXES`, `TARGET_TYPES`, `MAX_PANELS`, `COLOR_USES`, `ANALYTICS_TYPES`, `CLICK_TYPES`, `primaryDim`, `isDrillActive`, `drillActiveDim`, `drillPathFilters`, `pagesFilter`, `chartOrientation`, `showMeCounts`, `keyOf`, `splitKey`, `columnsCache` | `sheet-plan.js` (all exported) |
| 140 | `shelfMeasureCount` — never called | deleted |
| 240–241 | `headerAbort`, `TYPE_ICONS` | stays |
| 1427–1438, 1550, 1988–1993, 2013–2018, 2341–2455 | closure: `sharedSkipped`, `sharedNote`, `pv`, `periodFilters`, `periodNotice`, `buildPlan`, `buildJoins`, `relationshipGraph`, `bfs`, `col` | `sheet-plan.js` (dedented, exported) |
| 964–979 | `setStatusBar` | view factory |
| 1439–1454 | `aliasNames` | view factory |
| 1994–2012 | `fetchCompare` | view factory |
| 2149–2339 | `runChart` (→ `run`), `runTable` + its pager, `speedNotice`, `joinNotices`, `invalidFilterNotice`, `fetchCached`, `loadingView`, `markFresh`, `setNotice`, `runStatChart` | view factory |
| 2457–2773 | `renderChart`, `renderP36`, `legendHandler`, `pathOrderedRows`, `renderScatterShapes`, `marksChannels`, `markFieldValues`, `selectHandler` | view factory |
| 2775–2793 | `toggleSelection` | stays (becomes `hooks.onSelect`) |
| 2795–3162 | `renderColorSplit`, `renderHeatmap`, `renderTreemap`, `kpiView`, `sparkline`, `crosstabTable`, `conditionalFor`, `cfPalette`, `formattedCell`, `conditionalLegend` | view factory |
| 3294–3302 | `el`, `iconSpan`, `hint`, `warn` | view module level (`el`, `iconSpan`, `hint` exported) |
| 3322–3364 | `tupleKey`, `uniqueTuples`, `expandLeaves`, `runs`, `levelSpans` | view module level |

Everything else stays in the editor: field pane, shelves, pills, Marks / Filters / Drill / Pages tools,
`drillDown` (680–692, becomes `hooks.onDrill`), `selectionChip`, view bar, Show Me, Format / Analytics /
conditional-formatting *editors*, undo / redo, full screen, print, `exportImage`, `exportCsvRows`, the bottom
DnD / `select` / `fmt*` / download helpers. The moved factory blocks keep their two-space indent and their
closure names, so they bind to the factory's own variables with only the edits in Step 6.

**Closure state (l.256–281):** `gate`, `tablePager`, `legendFocus`, `calcPercent`, `extraNotice`,
`bucketedKey` → per view, inside `createWorksheetView`. `results` → `export const resultCache`. `freshNext` stays
(→ `run(…, { fresh })`). `freshResult` is never read → deleted. `history`, `lastSnap`, `calcFor`,
`choicesFor`, `cfMeasure`, the `*Open`/`shown*` flags, `openTool`, `pageTimer` stay. `commit` is reached only
through the hooks.

- [ ] **Step 1: Write the failing tests.** `tests/js/sheet-plan.test.mjs` — oracles captured by running the
  pre-move `buildPlan` (commit `568e3c8`); the move must not change one field:

```js
import { test, beforeEach } from "node:test";
import assert from "node:assert/strict";
import { buildPlan, planDims, planMeasures, sortTargets } from "../../src/DashboardBuilder/Features/Dashboard/sheet-plan.js";
import { emptySheet, defaultMarks, entities, relationships } from "../../src/DashboardBuilder/Features/Core/store.js";

// Oracles captured from the pre-P24 dashboards.js buildPlan (commit 568e3c8) — the move must not change them.
const pill = (table, column, category, extra = {}) => ({ db: "shop", table, column, category, ...extra });
const R = pill("orders", "region", "text"), C = pill("orders", "city", "text"), S = pill("orders", "sales", "numeric", { agg: "sum" });
const SEG = pill("customers", "segment", "text");
const sheet = (o) => ({ ...emptySheet(), ...o });
const col = (table, column) => ({ db: "shop", table, column });
const TAIL = { limit: 5000, otherBucket: true, dateBucket: "auto" };
beforeEach(() => { entities.clear(); relationships.clear(); });

test("one table: dimension on Columns, measure on Rows", () => {
  assert.deepEqual(buildPlan(sheet({ columns: [R], rows: [S] })), {
    from: { db: "shop", table: "orders" }, joins: [], rowDimensions: [], columnDimensions: [col("orders", "region")],
    measures: [{ ...col("orders", "sales"), agg: "sum" }], filters: [], ...TAIL, sort: { column: "k0", desc: false } });
});
test("two tables join along a left relationship; a filter binds; sort by the measure, descending", () => {
  entities.set("e1", { id: "e1", db: "shop", table: "orders", columns: [] });
  entities.set("e2", { id: "e2", db: "shop", table: "customers", columns: [] });
  relationships.set("r1", { id: "r1", from: { entityId: "e1", column: "cust_id" }, to: { entityId: "e2", column: "id" }, joinType: "left" });
  const plan = buildPlan(sheet({ columns: [SEG], rows: [S], filters: [{ ...R, op: "=", value: "North" }],
    sort: { by: "measure:shop.orders.sales:sum", dir: "desc" } }));
  assert.deepEqual(plan, {
    from: { db: "shop", table: "customers" },
    joins: [{ left: col("customers", "id"), right: col("orders", "cust_id"), type: "left" }],
    rowDimensions: [], columnDimensions: [col("customers", "segment")], measures: [{ ...col("orders", "sales"), agg: "sum" }],
    filters: [{ ...col("orders", "region"), op: "=", value: "North", values: null }], ...TAIL, sort: { column: "v0", desc: true } });
});
test("no relationship between the tables → null", () => {
  assert.equal(buildPlan(sheet({ columns: [SEG], rows: [S] })), null);
});
test("drill level leads; selection, drill path and page filters follow in that order", () => {
  const drill = { levels: [R, C].map(({ db, table, column, category }) => ({ db, table, column, category })), depth: 1,
    path: [{ column: "region", value: "North", label: "North" }] };
  const plan = buildPlan(sheet({ rows: [S], drill, pages: { ...col("orders", "city"), members: ["Ada", "Bree"], index: 1 },
    selection: { ...col("orders", "city"), value: "Ada", action: "exclude" } }));
  assert.deepEqual(plan.rowDimensions, [col("orders", "city")]);
  assert.deepEqual(plan.filters, [
    { ...col("orders", "city"), op: "!=", value: "Ada", values: null },
    { ...col("orders", "region"), op: "=", value: "North", values: null },
    { ...col("orders", "city"), op: "=", value: "Bree", values: null }]);
});
test("planDims keeps discrete Colour last; planMeasures puts shelf measures before Size", () => {
  const dims = planDims(sheet({ columns: [R], rows: [S], color: [C], marks: { ...defaultMarks(), detail: [pill("orders", "day", "temporal")] } }));
  assert.deepEqual(dims.keyOrder.map((f) => f.column), ["region", "day", "city"]);
  const ms = planMeasures(sheet({ chartType: "scatter", rows: [S, pill("orders", "profit", "numeric", { agg: "avg" })],
    marks: { ...defaultMarks(), size: pill("orders", "qty", "numeric", { agg: "sum" }) } }));
  assert.deepEqual(ms.map((e) => `${e.role}:${e.field.column}:${e.agg}`), ["shelf:sales:sum", "shelf:profit:avg", "size:qty:sum"]);
  assert.deepEqual(sortTargets(sheet({ columns: [R], rows: [S] })).map((t) => t.alias), ["k0", "v0"]);
});
```

  Then `tests/browser/checks/two-views.mjs` — the code is in [plan-runtime-b2.md § two-views](plan-runtime-b2.md#two-views)
  (Review Focus #2); create it now, exactly as printed there.

- [ ] **Step 2: Run both — expect FAIL.** `N=~/.nvm/versions/node/v24.20.0/bin/node`;
  `$N --test tests/js/sheet-plan.test.mjs` → `Cannot find module …/Dashboard/sheet-plan.js`. Start the dev
  server (Global Constraints), then `NODE_PATH=<scratch>/node_modules $N tests/browser/run.mjs two-views` →
  `FAIL [light] two-views: check threw — … Failed to fetch dynamically imported module …` (and `[dark]`).

- [ ] **Step 3: Move the query shape into `sheet-plan.js`.** Save the block tool (prints the cut text):

```python
# <scratch>/blocks.py — print (show) or remove-and-print (cut) blocks of FILE: each runs from the first line
# containing START up to the line before the next line containing STOP.  python3 blocks.py FILE show|cut START STOP …
import sys
path, mode, *pairs = sys.argv[1:]
lines = open(path).read().split("\n")
def find(text, after=0):
    hits = [i for i, l in enumerate(lines) if text in l and i >= after]
    if not hits: sys.exit(f"anchor not found: {text!r}")
    return hits[0]
spans = [(a, find(stop, a + 1)) for start, stop in zip(pairs[::2], pairs[1::2]) for a in [find(start)]]
print("\n".join(l for a, b in spans for l in lines[a:b]))
if mode == "cut":
    drop = {i for a, b in spans for i in range(a, b)}
    open(path, "w").write("\n".join(l for i, l in enumerate(lines) if i not in drop))
```

  Write `<scratch>/plan-head.js` (the new file's header), then cut and assemble:

```js
// A worksheet's query shape (moved out of dashboards.js in P24a): plan helpers, joins over the Data Model's
// relationships, buildPlan. DOM-free — reads the store's model, shared filters, parameters and field
// settings when called. Used by the worksheet editor (dashboards.js) and every worksheet-view.
import { entities, relationships, sharedFilters, parameters, metaOf, nameOf } from "../Core/store.js";
import { roleOf } from "./show-me-rules.js";
import { checkFilter, serverFilter } from "./filter-rules.js";
import { resolveRange, rangeFilter, rangeLabel } from "./period-model.js";
import { scalePlan } from "./scale-model.js";
import { withParamValue, effectiveTopN } from "../Core/parameters-model.js";
import { LIMITS } from "../Core/validate.js";

```

```bash
S=<scratch>; D=src/DashboardBuilder/Features/Dashboard/dashboards.js; P=src/DashboardBuilder/Features/Dashboard/sheet-plan.js
python3 $S/blocks.py $D cut "// Column category from" "const FILTER_PLACEHOLDER" "// A filter contributes" "let headerAbort" > $S/top.js
python3 $S/blocks.py $D cut "// Shared filters whose table" "// P28: rename a result's" "  const pv = (f)" "  const PARAMABLE" \
  "// The period's range filter" "// The comparison result for" "// The range line for the notice" "// Wire a zone as a field-only" \
  "  function buildPlan(sheet, periodRange)" "  // result = { rowDimensions:" > $S/closure.js
{ cat $S/plan-head.js $S/top.js; sed -E 's/^  //' $S/closure.js; } | sed -E 's/^(const|function) /export \1 /' \
  | grep -v '^export const shelfMeasureCount' > $P
```

  In `dashboards.js`, after `import { createHistory } from "./history.js";` add:

```js
import { categoryOf, isDateOnlyColumn, toFilter, pv, measureName, marksOf, SCATTER_TYPES, scatterSymbol, sameField, cmpValues,
  colorMode, planDims, planMeasures, sortTargets, CHART_LIKE, P36_TYPES, NO_AXES, TARGET_TYPES, MAX_PANELS, COLOR_USES,
  ANALYTICS_TYPES, CLICK_TYPES, primaryDim, isDrillActive, chartOrientation, showMeCounts, keyOf, columnsCache,
  sharedNote, periodNotice, buildPlan } from "./sheet-plan.js";
```

  and delete the now-unused imports `serverFilter` (filter-rules), `relationships` (store), `withParamValue`,
  `effectiveTopN` (parameters-model), `rangeFilter` (period-model), `scalePlan` (scale-model).

- [ ] **Step 4: Verify the half-move.** `$N --check $P && $N --check $D` → no output. `wc -l $P` → ≈ 356.
  `grep -c '^export ' $P` → `44`. `$N --test tests/js/*.test.mjs` → all pass, `sheet-plan` 5/5. Browser:
  `run.mjs` → every pre-existing check PASS; `two-views` still FAIL (no view yet). Commit nothing yet —
  Task 3 commits once, at Step 9 in [plan-runtime-b2.md](plan-runtime-b2.md).
