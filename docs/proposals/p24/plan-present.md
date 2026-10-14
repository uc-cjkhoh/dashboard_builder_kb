# P24 plan — Task 9: dashboard full screen, print, theme, bookmarks

Part of the [P24 plan](plan-overview.md); read its Global Constraints first, the harness contract in
[plan-board.md](plan-board.md) and Task 8 ([plan-board-2.md](plan-board-2.md), [plan-board-3.md](plan-board-3.md)).
Paths are relative to the app root. Spec:
[§ Full screen, print, export, bookmarks](../p24-dashboards.md#full-screen-print-export-bookmarks),
[§ Rendering and data](../p24-dashboards.md#rendering-and-data) (theme).

### Task 9: dashboard full screen, print, theme, bookmarks

**Files:** modify `Features/Board/_Board.cshtml`, `board.js`, `board.css`; `Features/Workbook/workbook.js`;
`Features/Core/menu.js`; create `tests/browser/checks/board-present.mjs`.

**Interfaces:** consumes `sizeChart(container, size | null)` (Task 1), `gridMetrics` (Task 8), `activeBoard()`,
`setTheme` / `currentTheme`. Produces `#bd-full` (`aria-pressed`), `#bd-print`, `.bd-print-head`.

- [ ] **Step 1: Failing check** — `tests/browser/checks/board-present.mjs`:

```js
import assert from "node:assert/strict";
import { start, pass, sheet, board, addSheet, drawnCount, storeUrl } from "../board-helpers.mjs";
// P24b presentation: bookmarks / export not offered, full screen, theme redraw from cache, print sizing.
export async function run(ctx) {
  await start(ctx);
  const p = ctx.page, url = await p.evaluate(storeUrl);
  const a = await sheet(ctx, "region", "sales");
  await p.click("#wb-menu-btn"); assert.ok(await p.isVisible("#wb-bookmark-add")); await p.keyboard.press("Escape");
  await board(ctx); await addSheet(ctx, a); await addSheet(ctx, a); await drawnCount(ctx, 2);
  await p.click("#wb-menu-btn"); assert.ok(await p.isHidden("#wb-bookmark-add"), "no bookmark action on a dashboard");
  await p.keyboard.press("Escape");
  assert.equal(await p.locator(".ws-export:visible").count(), 0, "image / CSV export not offered on a dashboard");
  await p.click("#bd-full");
  assert.equal(await p.getAttribute("#bd-full", "aria-pressed"), "true");
  assert.ok(await p.evaluate(() => document.fullscreenElement?.id === "bd-main" || document.getElementById("bd-main").classList.contains("is-presenting")));
  await p.click("#bd-full"); assert.equal(await p.getAttribute("#bd-full", "aria-pressed"), "false");
  await p.$$eval(".bd-widget .ws-chart-canvas", (hs) => hs.forEach((h) => { h.dataset.old = "1"; }));
  const n = ctx.queries.length;
  await p.evaluate(async (u) => { const s = await import(u); s.setTheme({ ...s.currentTheme(), accent: "#2255aa" }); }, url);
  await p.waitForFunction(() => !document.querySelector(".bd-widget .ws-chart-canvas[data-old]") && document.querySelectorAll(".bd-widget .ws-chart-canvas").length === 2);
  assert.equal(ctx.queries.length, n, "a theme change redraws from cache");
  await p.evaluate(() => window.dispatchEvent(new Event("beforeprint")));
  const gap = await p.$eval("#bd-canvas", (c) => parseFloat(getComputedStyle(c).columnGap));
  const want = Math.floor(6 * ((1000 - 11 * gap) / 12) + 5 * gap) - 2; // 6 of 12 columns on the 1000px page
  for (const w of await p.$$eval(".bd-widget .ws-chart-canvas", (hs) => hs.map((h) => h.firstElementChild.getBoundingClientRect().width)))
    assert.ok(Math.abs(w - want) <= 2, `printed chart ${w}px ≈ ${want}px`);
  await p.emulateMedia({ media: "print" });
  assert.ok(await p.isHidden(".bd-side") && await p.isVisible("#bd-print-title"));
  await p.emulateMedia({ media: "screen" }); await p.evaluate(() => window.dispatchEvent(new Event("afterprint")));
  return pass("no bookmark / export on a dashboard, full screen, theme redraw from cache, print sizing");
}
```

  `$PW tests/browser/run.mjs board-present` — expect FAIL (`#wb-bookmark-add` still visible on the dashboard).

- [ ] **Step 2: Markup.** In `_Board.cshtml`, after `#bd-redo`:
  `<button type="button" class="iconbtn" id="bd-full" aria-label="Full screen" title="Full screen" aria-pressed="false"><span data-icon="expand"></span></button>`
  and `<button type="button" class="iconbtn" id="bd-print" aria-label="Print / PDF" title="Print / PDF…"><span data-icon="print"></span></button>`;
  first child of `#bd-scroll`: `<div class="bd-print-head"><h1 class="bd-print-head__title" id="bd-print-title"></h1><p class="bd-print-head__line" id="bd-print-line"></p></div>`.

- [ ] **Step 3: `board.js`.** Add `import { sizeChart } from "../Dashboard/chart.js";`, `gridMetrics` to the
  `board-drag.js` import, and replace the `// (Task 9: …)` line with:

```js
  // Presentation: full screen and print take the whole canvas; a theme flip redraws every widget from cache.
  const main = $("bd-main"), fullBtn = $("bd-full"), PRINT_W = 1000; // px, as the worksheet's printed chart
  const isFull = () => document.fullscreenElement === main || main.classList.contains("is-presenting");
  const paintFull = () => {
    const on = isFull(), t = on ? "Exit full screen (Esc)" : "Full screen";
    fullBtn.replaceChildren(icon(on ? "collapse" : "expand"));
    fullBtn.setAttribute("aria-pressed", String(on)); fullBtn.setAttribute("aria-label", t); fullBtn.title = t;
  };
  fullBtn.addEventListener("click", async () => {
    if (isFull()) { if (document.fullscreenElement) await document.exitFullscreen().catch(() => {}); main.classList.remove("is-presenting"); }
    else { try { await main.requestFullscreen(); } catch { main.classList.add("is-presenting"); } }
    paintFull();
  });
  document.addEventListener("fullscreenchange", paintFull);
  document.addEventListener("keydown", (e) => { if (e.key === "Escape" && main.classList.contains("is-presenting") && !e.defaultPrevented) { main.classList.remove("is-presenting"); paintFull(); } });
  bus.addEventListener("view:changed", () => { main.classList.remove("is-presenting"); if (document.fullscreenElement === main) document.exitFullscreen().catch(() => {}); paintFull(); });
  $("bd-print").addEventListener("click", () => window.print());
  let printing = false;
  window.addEventListener("beforeprint", () => {
    const board = activeBoard();
    if (!board || view.hidden) return;
    printing = true;
    $("bd-print-title").textContent = board.name;
    $("bd-print-line").textContent = `Printed ${new Date().toLocaleString()}`;
    const { row, gap } = gridMetrics(canvas), col = (PRINT_W - gap * (GRID.cols - 1)) / GRID.cols;
    for (const w of board.widgets) { // print CSS drops the pane padding + notice: the chart fills its cell box under the header
      const it = live.get(w.id);
      if (it?.chartEl) sizeChart(it.chartEl, { width: Math.floor(w.w * col + (w.w - 1) * gap) - 2, height: Math.floor(w.h * row + (w.h - 1) * gap) - it.head.offsetHeight - 2 });
    }
  });
  window.addEventListener("afterprint", () => { if (!printing) return; printing = false; for (const it of live.values()) if (it.chartEl) sizeChart(it.chartEl, null); });
  const redraw = () => rerun(() => true); // same plans → the shared cache, no query
  bus.addEventListener("theme:changed", redraw);
  matchMedia("(prefers-color-scheme: dark)").addEventListener("change", redraw);
```

- [ ] **Step 4: `board.css`** (append):

```css
/* Full screen: the bar + canvas alone, without the edit affordances. Print: the whole canvas at 1000px. */
.bd-print-head { display: none; }
.bd-main:fullscreen, .bd-main.is-presenting { background: var(--bg); }
.bd-main.is-presenting { position: fixed; inset: 0; z-index: 50; }
.bd-main:is(:fullscreen, .is-presenting) :is(.bd-widget__actions, .bd-widget__resize) { display: none; }
@media print {
  .view--board, .board, .bd-main, .bd-scroll { display: block; height: auto; overflow: visible; padding: 0; }
  .bd-side, .bd-bar, .bd-widget__actions, .bd-widget__resize, .bd-ghost, .bd-empty { display: none !important; }
  .bd-print-head { display: block; margin-bottom: 6mm; color: var(--print-ink); }
  .bd-print-head__title { margin: 0 0 2mm; font-size: 18pt; } .bd-print-head__line { margin: 0; font-size: 9pt; }
  .bd-canvas { width: 1000px; min-height: 0; }
  .bd-widget { box-shadow: none; break-inside: avoid; background: var(--print-paper); border-color: var(--line-2); }
  .bd-widget__body { overflow: visible; }
  .bd-widget .ws-chart-canvas { position: relative; inset: auto; width: auto; height: auto; } /* not the worksheet's 1000 × 560 */
}
```

- [ ] **Step 5: Bookmarks on worksheets only.** `workbook.js` (import `activeBoard`), after the
  `wb-bookmark-add` listener: `const bmAdd = document.getElementById("wb-bookmark-add");`
  `const syncBookmark = () => { if (bmAdd) bmAdd.hidden = activeBoard() !== null; };`
  `bus.addEventListener("view:changed", syncBookmark); syncBookmark();`. `Core/menu.js`: arrow keys skip hidden
  items — `const items = () => [...list.querySelectorAll('[role^="menuitem"]')].filter((i) => !i.hidden);`.

- [ ] **Step 6: GREEN.** `node --check` the four changed modules; JS suite; `dotnet test`; harness light + dark —
  all PASS. Print-preview a dashboard by hand (Chromium, landscape) and screenshot it for the user.

- [ ] **Step 6b: v1 autosave opens as worksheets** (spec § Testing; Task 6 covers the file path in node).
  Create `tests/browser/checks/v1-autosave.mjs` — it seeds the **v1** key before the app loads, then
  checks the migrated tabs and that the v1 key is left in place and a v2 key is written:

```js
import assert from "node:assert/strict";
const V1 = "dashboardbuilder.workbook.v1|mock|8443|demo", V2 = "dashboardbuilder.workbook.v2|mock|8443|demo";
const v1 = { format: "dashboard-builder-workbook", version: 1, savedAt: "2026-10-01T00:00:00Z", entities: [], relationships: [],
  dashboards: [{ name: "Old sales", sheet: { columns: [], rows: [], chartType: "bar" } },
               { name: "Old trend", sheet: { columns: [], rows: [], chartType: "line" } }], active: 1 };
export async function run({ browser, baseUrl }) {
  const page = await browser.newPage();
  await page.addInitScript(([k, v]) => { if (!sessionStorage.getItem("seeded")) { localStorage.clear(); localStorage.setItem(k, v); sessionStorage.setItem("seeded", "1"); } }, [V1, JSON.stringify(v1)]);
  await page.route("**/api/connection", (r) => r.fulfill({ status: 200, contentType: "application/json",
    body: JSON.stringify({ connected: true, host: "mock", port: 8443, user: "demo", secure: true, allowInvalidCertificate: false }) }));
  await page.goto(`${baseUrl}/`); await page.waitForTimeout(1500);
  const tabs = await page.$$eval(".tab", (ts) => ts.filter((t) => t.querySelector(".tab__label[data-tab-id]")).map((t) => ({
    name: t.querySelector(".tab__label").textContent.trim(), kind: t.classList.contains("tab--dashboard") ? "dashboard" : "worksheet",
    active: t.classList.contains("is-active") })));
  assert.deepEqual(tabs.map((t) => [t.name, t.kind]), [["Old sales", "worksheet"], ["Old trend", "worksheet"]], JSON.stringify(tabs));
  assert.equal(tabs.find((t) => t.active)?.name, "Old trend");
  await page.waitForTimeout(800); // autosave debounce
  const keys = await page.evaluate(([a, b]) => [Boolean(localStorage.getItem(a)), Boolean(localStorage.getItem(b))], [V1, V2]);
  assert.deepEqual(keys, [true, true], "v1 kept, v2 written");
  await page.close();
  return [{ name: "v1 autosave opens as worksheets (active tab kept); v1 key kept, v2 written", ok: true }];
}
```

  Selectors are Task 7's tab markup (`.tab__label[data-tab-id]`, `.tab--dashboard`, `.is-active`). Run the
  harness → this check passes in light + dark.

- [ ] **Step 7: Commit** — `Dashboard full screen, print, theme redraw; bookmarks on worksheets only (P24b)`,
  ending with the `Co-Authored-By` line.

Next: [Task 10 — docs, merge, deploy](plan-finish.md).
