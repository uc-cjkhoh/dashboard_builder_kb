# P24 plan — Task 1 (continued): the two-charts check, `chart.js` per container

Part of the [P24 plan](plan-overview.md); read its Global Constraints first. Paths are relative to the
app root. Task 1's **Files** / **Interfaces** and Steps 1–5 (the harness: `tests/browser/mock.mjs`,
`run.mjs`, `README.md`, `checks/show-me.mjs`) are in [plan-runtime-a.md](plan-runtime-a.md); do those first.
`$PW` is defined there in Step 1.

- [ ] **Step 6: Write the failing check** — `tests/browser/checks/two-charts.mjs`

```js
// P24a: two containers hold two live charts at once; disposing one leaves the other.
export async function run({ page, baseUrl }) {
  await page.goto(`${baseUrl}/`); await page.waitForTimeout(1200);
  const r = await page.evaluate(async () => {
    const c = await import("/features/Dashboard/chart.js");
    const box = (left) => document.body.appendChild(Object.assign(document.createElement("div"),
      { style: `position:fixed;top:0;left:${left}px;width:480px;height:320px` }));
    const live = (el) => {
      const host = el.querySelector(".ws-chart-canvas");
      const inst = host && window.echarts.getInstanceByDom(host);
      return Boolean(inst && !inst.isDisposed() && host.querySelector("svg"));
    };
    const a = box(0), b = box(500);
    const spec = { type: "bar", categories: ["North", "South"], series: [{ name: "sales", data: [3, 5] }] };
    c.renderChart(a, spec);
    c.renderChart(b, { ...spec, type: "line" });
    const both = [live(a), live(b)], has = [c.hasChartInstance(a), c.hasChartInstance(b)];
    c.disposeChart(a);
    const after = [live(a), live(b)], hasAfter = [c.hasChartInstance(a), c.hasChartInstance(b)];
    c.disposeChart(b); a.remove(); b.remove();
    return { both, has, after, hasAfter };
  });
  return [
    { name: "two containers hold two live charts", ok: r.both.join() === "true,true" && r.has.join() === "true,true", detail: JSON.stringify(r) },
    { name: "disposing one container keeps the other", ok: r.after.join() === "false,true" && r.hasAfter.join() === "false,true", detail: JSON.stringify(r) },
  ];
}
```

- [ ] **Step 7: Run the harness — show-me green, two-charts red.** Start the dev server (Global Constraints), then
  `eval "$PW tests/browser/run.mjs"`.
  Expected: 22 `PASS … show-me` per scheme; `FAIL [light] two-charts: two containers hold two live charts —
  {"both":[false,true],…}` and `FAIL … disposing one container keeps the other`, same in dark; last line
  `44/48 passed`; exit code 1.

- [ ] **Step 8: `chart.js` — per-container state.** Replace the module lets (l.16–19) with:

```js
// Per-container chart state. `lastOption` is the option on screen — re-drawn as SVG for export when the
// chart is on canvas. `animateNext` survives disposeChart (the worksheet sets it before each render).
const charts = new WeakMap(); // container → { instance, resizeObserver, lastOption, onCanvas, animateNext }
function stateOf(container) {
  let st = charts.get(container);
  if (!st) {
    st = { instance: null, resizeObserver: null, lastOption: null, onCanvas: false, animateNext: true };
    charts.set(container, st);
  }
  return st;
}
```

  Then change exactly these lines (bodies otherwise untouched; `instance` is now a local in each function):

| Line(s) | Now | Becomes |
|---|---|---|
| 9 | `… One live instance at a time; call disposeChart() before re-rendering.` | `… One live instance per container (P24a): renderChart(container, …) replaces that container's chart only.` |
| 64 | `disposeChart();` | `disposeChart(container);` then a new line `const st = stateOf(container);` |
| 81–82 | `onCanvas = …;` / `instance = window.echarts.init(host, null, { renderer: onCanvas ? … });` | `st.onCanvas = …;` / `const instance = window.echarts.init(host, null, { renderer: st.onCanvas ? … });` + new line `st.instance = instance;` |
| 86–88 | `if (onCanvas) …` / `lastOption = option;` / `motionOption(animateNext && !onCanvas)` | `if (st.onCanvas) …` / `st.lastOption = option;` / `motionOption(st.animateNext && !st.onCanvas)` |
| 99 | `focusSeries(spec.focus, spec.type)` | `focusSeries(container, spec.focus, spec.type)` |
| 101–102 | `resizeObserver = new ResizeObserver(() => {` / `if (!instance) return;` | `st.resizeObserver = new ResizeObserver(() => {` / `if (st.instance !== instance) return;` |
| 110 | `resizeObserver.observe(host);` | `st.resizeObserver.observe(host);` |
| 166–167 | `export function focusSeries(name, type) {` / `if (!instance) return;` | `export function focusSeries(container, name, type) {` / `const instance = charts.get(container)?.instance;` / `if (!instance) return;` |
| 175 | `export function hasChartInstance() { return instance !== null; }` | `export function hasChartInstance(container) { return Boolean(charts.get(container)?.instance); }` |
| 179 | `let animateNext = true;` | delete (now per container) |
| 181–182 | `export function sizeChart(size) {` / `if (!instance) return;` | `export function sizeChart(container, size) {` / `const instance = charts.get(container)?.instance;` / `if (!instance) return;` |
| 187 | `export function animateNextChart(on) { animateNext = Boolean(on); }` | `export function animateNextChart(container, on) { stateOf(container).animateNext = Boolean(on); }` |
| 201–202 | `export async function exportChart(kind) {` / `if (!instance) return null;` | `export async function exportChart(container, kind) {` / `const st = charts.get(container);` / `const instance = st?.instance;` / `if (!instance) return null;` |
| 207, 213, 217 | `if (onCanvas) {` · `offscreenSvg(w, h)` · `currentSvgString(w, h)` | `if (st.onCanvas) {` · `offscreenSvg(st.lastOption, w, h)` · `currentSvgString(instance, w, h)` |
| 225–226, 232 | `function offscreenSvg(w, h) {` / `if (!lastOption) …` / `{ ...lastOption, …}` | `function offscreenSvg(option, w, h) {` / `if (!option) …` / `{ ...option, …}` |
| 243 | `function currentSvgString(w, h) {` | `function currentSvgString(instance, w, h) {` |

  And `disposeChart` (l.287–292) becomes:

```js
// Tear down `container`'s instance + its observer. Safe to call when nothing is rendered there.
export function disposeChart(container) {
  const st = charts.get(container);
  if (!st) return;
  if (st.resizeObserver) { st.resizeObserver.disconnect(); st.resizeObserver = null; }
  if (st.instance) { st.instance.dispose(); st.instance = null; }
  st.lastOption = null; st.onCanvas = false;
}
```

  Check: `grep -nE "^(let|var) " src/DashboardBuilder/Features/Dashboard/chart.js` → no output.

- [ ] **Step 9: `dashboards.js` passes its `chartEl`** (the only importer; l.12 import line unchanged). The
  twelve `renderSeriesChart(chartEl, …)` calls (l.2325 … l.2866) are already container-first.

| Line | Now | Becomes |
|---|---|---|
| 1042 | `sizeChart({ width: 1000, height: 560 });` | `sizeChart(chartEl, { width: 1000, height: 560 });` |
| 1046 | `sizeChart(null);` | `sizeChart(chartEl, null);` |
| 1051 | `if (!hasChartInstance()) {` | `if (!hasChartInstance(chartEl)) {` |
| 1053 | `await exportChart(kind);` | `await exportChart(chartEl, kind);` |
| 2154 | `disposeChart(); // tear down …` | `disposeChart(chartEl); // tear down …` |
| 2288 | `animateNextChart(fresh);` | `animateNextChart(chartEl, fresh);` |
| 2660 | `focusSeries(legendFocus, sheet.chartType);` | `focusSeries(chartEl, legendFocus, sheet.chartType);` |

- [ ] **Step 10: Verify** — `node --check` both files; `grep -rnE "(sizeChart|hasChartInstance|exportChart|disposeChart|animateNextChart|focusSeries)\(\)" src/` → no output;
  the JS suite (Expected: `# fail 0`; `p36-charts.test.mjs` still imports `waterfallSteps`/`niceMax`/`multiplesGrid`);
  restart the dev server; `eval "$PW tests/browser/run.mjs"` → Expected: no FAIL lines, `48/48 passed`, exit 0.
  By hand in light and dark: a chart's PNG and SVG export, Print preview of a bar chart, legend click highlight.

- [ ] **Step 11: Commit**

```bash
git add .gitignore tests/browser src/DashboardBuilder/Features/Dashboard/chart.js src/DashboardBuilder/Features/Dashboard/dashboards.js
git commit -m "Keep one chart per container; add the headless browser harness (P24a)

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"
```

Next: [Task 2 — store `tabs` and worksheet renames](plan-runtime-a3.md).
