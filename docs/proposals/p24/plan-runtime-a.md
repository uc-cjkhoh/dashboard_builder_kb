# P24 plan — Task 1: browser harness, `chart.js` per container

Part of the [P24 plan](plan-overview.md); read its Global Constraints first. Paths are relative to the
app root. Spec: [§ 24a](../p24-dashboards.md#24a--widget-runtime-no-visible-change). Task 1 spans two files: this one
(Steps 1–5, the harness) and [plan-runtime-a2.md](plan-runtime-a2.md) (Steps 6–11, `chart.js`); Task 2 is in
[plan-runtime-a3.md](plan-runtime-a3.md).

### Task 1: the headless harness moves into the repo; `chart.js` keeps one chart per container

**Files:**
- Create: `tests/browser/mock.mjs`, `tests/browser/run.mjs`, `tests/browser/README.md`,
  `tests/browser/checks/show-me.mjs` (the P22 hand checks, ported), `tests/browser/checks/two-charts.mjs`
- Modify: `.gitignore` (add `tests/browser/shots/`)
- Modify: `src/DashboardBuilder/Features/Dashboard/chart.js` — l.9, l.16–19, l.63–111, l.166–167, l.175,
  l.179–187, l.201–219, l.225–232, l.243, l.287–292
- Modify: `src/DashboardBuilder/Features/Dashboard/dashboards.js` — l.1042, l.1046, l.1051, l.1053, l.2154,
  l.2288, l.2660

**Interfaces:**
- Consumes: nothing from earlier tasks.
- Produces: `renderChart(container, spec)`, `disposeChart(container)`, `hasChartInstance(container)`,
  `sizeChart(container, size | null)`, `exportChart(container, kind)`, `focusSeries(container, name, type)`,
  `animateNextChart(container, on)`; the harness — `launch(colorScheme)` → `{ browser, page, errors, queries }`,
  `openWorksheet(page)`, `BASE_URL`, `SHOTS` from `tests/browser/mock.mjs`; a check is
  `export async function run({ page, errors, queries, scheme, baseUrl, shots })` → `[{ name, ok, detail? }]`.

- [ ] **Step 1: Branch and a scratch install of `playwright-core`** (never added to the repo)

```bash
git checkout -b p24-dashboards
mkdir -p ~/pw-harness && (cd ~/pw-harness && npm init -y >/dev/null && npm i playwright-core@1.55.0)
ls ~/.cache/ms-playwright/chromium_headless_shell-1234/chrome-headless-shell-linux64/chrome-headless-shell
echo "tests/browser/shots/" >> .gitignore
```

Expected: the `ls` prints the path. (Missing → `node ~/pw-harness/node_modules/playwright-core/cli.js install chromium-headless-shell`.)
Below, `PW="NODE_PATH=$HOME/pw-harness/node_modules ~/.nvm/versions/node/v24.20.0/bin/node"`.

- [ ] **Step 2: `tests/browser/mock.mjs`** — launch + mocked `/api`. `playwright-core` is loaded with
  `createRequire`: an ES `import` ignores `NODE_PATH`.

```js
// Headless Chromium + a mocked /api for the browser checks. playwright-core comes from NODE_PATH
// (README.md) — createRequire, because ESM `import` ignores NODE_PATH.
import { createRequire } from "node:module";
const { chromium } = createRequire(import.meta.url)("playwright-core");

export const BASE_URL = (process.env.BASE_URL ?? "http://localhost:5180").replace(/\/$/, "");
export const SHOTS = new URL("./shots/", import.meta.url).pathname;
const CHROME = process.env.CHROME_PATH
  ?? `${process.env.HOME}/.cache/ms-playwright/chromium_headless_shell-1234/chrome-headless-shell-linux64/chrome-headless-shell`;
const COLUMNS = [["region", "String", "text"], ["city", "String", "text"], ["day", "Date", "temporal"],
  ["sales", "Float64", "numeric"], ["profit", "Float64", "numeric"]].map(([name, type, category]) => ({ name, type, category }));
const MEMBERS = { region: ["North", "South", "East"], city: ["Ada", "Bree", "Cole"], day: ["2026-01-01", "2026-02-01", "2026-03-01"] };

function queryResult(req) {
  const rd = (req.rowDimensions ?? []).map((c) => c.column), cd = (req.columnDimensions ?? []).map((c) => c.column);
  const ms = req.measures ?? [];
  let tuples = [[]];
  for (const d of [...rd, ...cd]) tuples = tuples.flatMap((t) => (MEMBERS[d] ?? ["a", "b"]).map((v) => [...t, v]));
  const rows = tuples.map((keys, i) => ({ keys, values: ms.map((m, j) => (m.aggregation === "min" || m.aggregation === "max") && m.column === "region" ? "North" : 10 + i * 7 + j * 3) }));
  return { rowDimensions: rd, columnDimensions: cd, measures: ms.map((m) => `${m.aggregation}(${m.column})`), rows, truncated: false };
}

/** A fresh browser + page in `colorScheme`; `queries` collects every /api/query body, `errors` page errors. */
export async function launch(colorScheme = "light") {
  const browser = await chromium.launch({ executablePath: CHROME, args: ["--no-sandbox"] });
  const page = await browser.newPage({ viewport: { width: 1440, height: 900 }, colorScheme });
  const errors = [], queries = [];
  page.on("pageerror", (e) => errors.push(String(e)));
  page.on("console", (m) => { if (m.type() === "error") errors.push(m.text()); });
  await page.route("**/api/**", async (route) => {
    const p = new URL(route.request().url()).pathname.replace(/^.*\/api/, "/api");
    const json = (body) => route.fulfill({ status: 200, contentType: "application/json", body: JSON.stringify(body) });
    if (p === "/api/connection") return json({ connected: true, host: "mock", port: 8443, user: "demo", secure: true, allowInvalidCertificate: false });
    if (p === "/api/databases") return json(["shop"]);
    if (p === "/api/databases/shop/tables") return json(["orders"]);
    if (p.endsWith("/columns")) return json(COLUMNS);
    if (p.includes("/distinct")) return json(MEMBERS[p.split("/").at(-2)] ?? []);
    if (p === "/api/query") { const req = route.request().postDataJSON(); queries.push(req); return json(queryResult(req)); }
    return route.fulfill({ status: 404, contentType: "application/json", body: JSON.stringify({ error: `unmocked ${p}` }) });
  });
  return { browser, page, errors, queries };
}

/** Open the app with orders on the canvas and one worksheet tab active. */
export async function openWorksheet(page) {
  await page.goto(`${BASE_URL}/`); await page.waitForTimeout(1200);
  await page.selectOption("#db-select", "shop"); await page.waitForTimeout(500);
  await page.click('button[aria-label="Add orders to the canvas"]'); await page.waitForTimeout(400);
  await page.click(".tab-add"); await page.waitForTimeout(800);
}
```

- [ ] **Step 3: `tests/browser/run.mjs`** — every check (or those named as arguments), light then dark.

```js
// Runs every tests/browser/checks/*.mjs (or those named on the command line) in light and dark.
// Each check exports `async function run(ctx)` → [{ name, ok, detail? }]. Exit code 1 on any FAIL.
import { readdirSync, mkdirSync } from "node:fs";
import { launch, BASE_URL, SHOTS } from "./mock.mjs";

mkdirSync(SHOTS, { recursive: true });
const dir = new URL("./checks/", import.meta.url);
const only = process.argv.slice(2);
const files = readdirSync(dir).filter((f) => f.endsWith(".mjs") && (!only.length || only.includes(f.replace(/\.mjs$/, "")))).sort();
let failed = 0, total = 0;
for (const scheme of ["light", "dark"]) {
  for (const file of files) {
    const { run } = await import(new URL(file, dir));
    const ctx = { ...(await launch(scheme)), scheme, baseUrl: BASE_URL, shots: SHOTS };
    let results;
    try { results = await run(ctx); }
    catch (err) { results = [{ name: "check threw", ok: false, detail: String(err?.stack ?? err) }]; }
    finally { await ctx.browser.close(); }
    if (ctx.errors.length) results.push({ name: "no page errors", ok: false, detail: ctx.errors.join(" | ") });
    for (const r of results) {
      total += 1; if (!r.ok) failed += 1;
      console.log(`${r.ok ? "PASS" : "FAIL"} [${scheme}] ${file.replace(/\.mjs$/, "")}: ${r.name}${!r.ok && r.detail ? ` — ${r.detail}` : ""}`);
    }
  }
}
console.log(`${total - failed}/${total} passed`);
process.exit(failed ? 1 : 0);
```

- [ ] **Step 4: `tests/browser/README.md`** — exactly:

```markdown
# Browser checks

Headless Chromium against a dev server with a mocked `/api` (no ClickHouse). Each `checks/*.mjs` exports
`async function run(ctx)` and returns `[{ name, ok, detail? }]`; `run.mjs` runs them all in light and dark
and exits 1 on any FAIL. Screenshots land in `shots/` (git-ignored).

1. Once: `mkdir -p ~/pw-harness && cd ~/pw-harness && npm init -y && npm i playwright-core@1.55.0` —
   never in the repo. Chromium headless shell: `~/.cache/ms-playwright/chromium_headless_shell-1234/…`
   (override with `CHROME_PATH`).
2. Dev server on 5180: `cd src/DashboardBuilder && dotnet run --no-launch-profile --urls http://localhost:5180`
   (other port: `BASE_URL=…`). Stop it with `fuser -k 5180/tcp`.
3. `NODE_PATH=~/pw-harness/node_modules node tests/browser/run.mjs [check …]`
```

- [ ] **Step 5: `tests/browser/checks/show-me.mjs`** — the P22 checks as a module. It reads the active
  worksheet as `(st.activeWorksheet ?? st.activeDashboard)()` so it passes before and after Task 2.

```js
// P22 Show Me regression: recommendation, greyed reasons, one-click placement, undo, keyboard, layout.
import { openWorksheet } from "../mock.mjs";

export async function run({ page, scheme, shots }) {
  const results = [], check = (name, ok, detail = "") => results.push({ name, ok: Boolean(ok), detail });
  const pill = (column, category, extra = {}) => ({ db: "shop", table: "orders", column, category, ...extra });
  const R = pill("region", "text"), C = pill("city", "text"), D = pill("day", "temporal"), S = pill("sales", "numeric", { agg: "sum" });
  const drillOn = () => ({ levels: [R, C].map(({ db, table, column, category }) => ({ db, table, column, category })), depth: 0, path: [] });
  const wait = (ms) => page.waitForTimeout(ms);
  await openWorksheet(page);
  const setSheet = async (patch) => { await page.evaluate(async (patch) => {
    const st = await import("/features/Core/store.js"), d = (st.activeWorksheet ?? st.activeDashboard)();
    st.updateSheet(d.id, { ...d.sheet, ...patch });
  }, patch); await openCard(); };
  const sheet = () => page.evaluate(async () => {
    const st = await import("/features/Core/store.js"), d = (st.activeWorksheet ?? st.activeDashboard)(), n = (a) => a.map((f) => f.column);
    return { type: d.sheet.chartType, columns: n(d.sheet.columns), rows: n(d.sheet.rows) };
  });
  const openCard = async () => { if (!(await page.$(".ws-showme"))) await page.click(".ws-showme-toggle"); await wait(150); };
  const tiles = () => page.$$eval(".ws-showme__tile", (ts) => ts.map((t) => ({ type: t.dataset.type,
    disabled: t.getAttribute("aria-disabled") === "true", recommended: t.classList.contains("is-recommended"), title: t.title })));
  const recommended = async () => (await tiles()).find((t) => t.recommended)?.type;
  const pick = async (type) => { await page.click(`.ws-showme__tile[data-type="${type}"]`); await wait(350); };
  const chartHint = () => page.$eval("#ws-chart", (c) => c.querySelector(".ws-hint")?.textContent ?? null);
  const status = () => page.$eval(".ws-showme__status", (s) => s.textContent);
  const undo = async () => { await page.keyboard.press("Control+z"); await wait(350); };
  const toggleFocused = () => page.evaluate(() => document.activeElement?.classList.contains("ws-showme-toggle"));
  const SKIP_DRAW = new Set(["histogram", "boxplot"]); // own endpoints, not mocked
  const everyValidDraws = async (label) => {
    const bad = [];
    for (const t of (await tiles()).filter((t) => !t.disabled && !SKIP_DRAW.has(t.type))) {
      await pick(t.type);
      const h = await chartHint();
      if (h && !(t.type === "bullet" && /target/i.test(h))) bad.push(`${t.type}: ${h}`);
    }
    check(`${label}: every enabled tile draws without a hint`, bad.length === 0, bad.join(" | "));
  };

  // 1. Region + Sales → Bar; Scatter greyed; Pie, then one undo; every valid tile draws
  await setSheet({ chartType: "bar", columns: [R], rows: [S] });
  const badges = await page.$$eval(".ws-showme__badge", (b) => b.map((x) => x.textContent).join());
  check("1 Bar recommended", (await recommended()) === "bar" && badges === "Recommended", badges);
  const sc = (await tiles()).find((t) => t.type === "scatter");
  check("1 Scatter greyed with reason", sc.disabled && sc.title === "A point chart plots two measures (X and Y) — add a second measure.", sc.title);
  await pick("pie");
  check("1 Pie draws", (await chartHint()) === null && (await sheet()).type === "pie");
  await undo();
  const s1 = await sheet();
  check("1 one undo returns to Bar layout", s1.type === "bar" && s1.columns.join() === "region" && s1.rows.join() === "sales", JSON.stringify(s1));
  await everyValidDraws("1");
  // 2. A date dimension → Line, date first on Columns
  await setSheet({ chartType: "bar", columns: [R, D], rows: [S] });
  check("2 Line recommended", (await recommended()) === "line");
  await pick("line");
  check("2 date first on Columns", (await sheet()).columns.join() === "day,region", JSON.stringify(await sheet()));
  // 3. Two dims + one measure → Heatmap; Sankey keeps the first key on Rows
  await setSheet({ chartType: "bar", columns: [R, C], rows: [S] });
  check("3 Heatmap recommended", (await recommended()) === "heatmap");
  await pick("heatmap");
  check("3 Heatmap draws", (await chartHint()) === null);
  await pick("sankey");
  const s3 = await sheet();
  check("3 Sankey: first key on Rows", s3.rows.join() === "region" && s3.columns.join() === "city,sales" && (await chartHint()) === null, JSON.stringify(s3));
  await everyValidDraws("3");
  // 4. Min of a text field → only Table / Text / KPI
  await setSheet({ chartType: "table", columns: [], rows: [pill("region", "text", { role: "measure", agg: "min" })] });
  const enabled = (await tiles()).filter((t) => !t.disabled).map((t) => t.type).sort().join();
  check("4 only table/text/kpi enabled", enabled === "kpi,table,text", enabled);
  check("4 Table recommended", (await recommended()) === "table");
  // 5. Drill active; 6. the same field on both shelves
  await setSheet({ chartType: "bar", columns: [], rows: [S], drill: drillOn() });
  await everyValidDraws("5 drill");
  await setSheet({ drill: null, chartType: "bar", columns: [R], rows: [{ ...R }, S] });
  await pick("table");
  const s6 = await sheet();
  check("6 both region pills kept, table draws", s6.rows.filter((c) => c === "region").length === 2 && (await chartHint()) === null, JSON.stringify(s6));
  // 7. Enter on a greyed tile → status reason; Esc → closed, focus on the toggle
  await setSheet({ chartType: "bar", columns: [R], rows: [S] });
  await page.focus('.ws-showme__tile[data-type="scatter"]'); await page.keyboard.press("Enter"); await wait(100);
  check("7 status shows the reason", (await status()).startsWith("Scatter: A point chart"));
  await page.keyboard.press("Escape"); await wait(150);
  check("7 Esc closes, focus on toggle", !(await page.$(".ws-showme")) && (await toggleFocused()));
  // 8. Re-picking the current type adds no undo step
  await setSheet({ chartType: "bar", columns: [R], rows: [S] });
  await pick("pie"); await pick("bar");
  const before = (await sheet()).type;
  await undo();
  const afterOne = await sheet();
  await pick("bar"); await pick("bar"); await undo();
  check("8 double pick of the current type adds one step only", before === "bar" && afterOne.type === "pie" && (await sheet()).type === "pie", JSON.stringify(await sheet()));
  // Empty sheet; empty shelves + drill
  await setSheet({ chartType: "bar", columns: [], rows: [] });
  check("empty: hint + no recommendation", (await status()) === "Add fields to Columns or Rows to see suggestions." && !(await recommended()));
  await setSheet({ chartType: "bar", columns: [], rows: [], drill: drillOn() });
  check("empty shelves + drill: nothing outlined", !(await recommended()));
  // The toggle keeps keyboard focus when it opens / closes the card; the layout keeps the chart's room
  await setSheet({ drill: null, chartType: "bar", columns: [R], rows: [S] });
  await page.click(".ws-showme-toggle");
  await page.focus(".ws-showme-toggle"); await page.keyboard.press("Enter"); await wait(150);
  const openFocus = await toggleFocused();
  await page.keyboard.press("Enter"); await wait(150);
  check("toggle keeps focus on open and close", openFocus && (await toggleFocused()));
  await openCard();
  const geo = await page.evaluate(() => ({ tileH: Math.round(document.querySelector(".ws-showme__tile").getBoundingClientRect().height),
    chartH: Math.round(document.getElementById("ws-chart").getBoundingClientRect().height) }));
  check("layout: tiles stay compact and the chart keeps room", geo.tileH <= 90 && geo.chartH >= 200, JSON.stringify(geo));
  await page.screenshot({ path: `${shots}show-me-${scheme}.png` });
  return results;
}
```

Task 1 continues in [plan-runtime-a2.md](plan-runtime-a2.md) — Step 6, the failing two-charts check.
