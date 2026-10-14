# P24 plan — Task 8 (part 1): the Board canvas — checks, markup, drag

Part of the [P24 plan](plan-overview.md); read its Global Constraints and Shared interfaces first, and the
harness contract at the top of [plan-board.md](plan-board.md). Paths are relative to the app root. Spec:
[§ Canvas](../p24-dashboards.md#canvas), [§ Rendering and data](../p24-dashboards.md#rendering-and-data).
Task 8 continues in [plan-board-3.md](plan-board-3.md) (`board.css`, `board.js`, GREEN, commit).

### Task 8: the Board feature

**Files:**
- Create: `src/DashboardBuilder/Features/Board/_Board.cshtml`, `board-drag.js`; `board.css`, `board.js` (part 2)
- Modify: `src/DashboardBuilder/Features/Shell/Index.cshtml`, `Shell/app.js` (mount, like every feature)
- Modify: `tests/browser/board-helpers.mjs`; create `tests/browser/checks/board-render.mjs`, `board-edit.mjs`

**Interfaces:**
- Consumes: store (Task 5) `bus`, `activeBoard()`, `boardList()`, `tabById(id)`, `worksheetList()`,
  `updateBoard(id, widgets)`, `switchTab(id)`, `nextWidgetId()`; events `view:changed`, `tabs:changed`,
  `dashboard:changed { id }`, `worksheet:changed { id }`; `board-layout.js` (Task 4) `GRID`, `DEFAULT_SIZE`,
  `firstFree`, `cellsFromPixels`, `moveBy`, `resizeBy`; `createWorksheetView` (Task 3); `createHistory`
  (`Dashboard/history.js`); `LIMITS.heading` (80), `LIMITS.body` (2000) (Task 5); `text`, `checkField`, `toast`.
- Produces: `export function initBoard()` (`board.js`); `board-drag.js` — `keyStep(e)` → `{ dx, dy, resize } | null`,
  `gridMetrics(canvas)` → `{ col, row, gap }` px, `wireDrag({ node, head, handle, canvas, ghost, widgets, id, onCommit, onReject })`.
  DOM used by Task 9: `#board-view`, `#bd-main`, `#bd-bar`, `#bd-canvas`, `.bd-widget`, `.bd-widget__chart`
  (`ws-chart`), `#bd-status`. `live` map in `board.js`: widget id → `{ el, kind, sheetId?, view?, chartEl?, ro? }`.

**How it fits together** (read before coding):
- **Keyed render.** `render()` reconciles `live` against the active board's widgets: new ids get a node (and,
  for a worksheet, one `createWorksheetView({ interactive: false })` run with `scopeId = sheetId`); gone ids are
  disposed; kept ids only get their grid area and header updated — a move never re-queries or redraws.
- **Stale = rebuilt on show (Review Focus #1).** Leaving a dashboard disposes every view; showing it again
  builds every widget, which runs its worksheet's *current* sheet (an edited plan misses the cache → new
  query; an unchanged one is a cache hit). While a dashboard is on screen, `worksheet:changed { id }` re-runs
  that sheet's widgets in place.
- **Resize (Review Focus #5)** — a `ResizeObserver` per chart calls `view.resize()`; nothing re-queries.
- **Undo (Review Focus #3)** — `createHistory()` keyed by dashboard id, snapshots of `widgets`; only Board
  commits record. Undo / redo drop any sheet widget whose worksheet no longer exists, and say so.

- [ ] **Step 1: Board helpers.** Append to `tests/browser/board-helpers.mjs`:

```js
export async function board(ctx) { await newTab(ctx, "dashboard"); await ctx.page.waitForSelector("#board-view:not([hidden])"); return activeName(ctx); }
export const tab = (ctx, name) => ctx.page.click(`.tab__label:text-is("${name}")`);
export const addSheet = (ctx, name) => ctx.page.click(`.bd-sheet__add[aria-label="Add ${name} to the dashboard"]`);
export const widget = (ctx, title) => ctx.page.locator(".bd-widget", { has: ctx.page.locator(`.bd-widget__title:text-is("${title}")`) });
export const area = (loc) => loc.first().evaluate((e) => e.style.gridArea);
export const drawnCount = (ctx, n) => ctx.page.waitForFunction(
  ([sel, k]) => document.querySelectorAll(`.bd-widget ${sel}`).length === k, [DRAWN, n]);
/** Series in a widget's live chart (ECharts is global; the instance sits on .ws-chart-canvas). */
export const seriesOf = (loc) => loc.first().locator(".ws-chart-canvas").evaluate((h) => window.echarts.getInstanceByDom(h)?.getOption().series.length ?? 0);
export const queriesWith = (ctx, from, ...cols) =>
  ctx.queries.slice(from).filter((b) => cols.every((c) => JSON.stringify(b).includes(`"${c}"`))).length;
export const settle = (ctx) => ctx.page.waitForLoadState("networkidle");
export async function reload(ctx) { await ctx.page.reload(); await ctx.page.waitForTimeout(1500); } // autosave restores
/** From now on a query whose body matches `pred` answers 502; returns the function that clears it. */
export async function failQuery(ctx, pred) {
  const h = (route) => (pred(route.request().postDataJSON())
    ? route.fulfill({ status: 502, contentType: "application/json", body: JSON.stringify({ error: "Query failed (mock)." }) })
    : route.fallback());
  await ctx.page.route("**/api/query", h);
  return () => ctx.page.unroute("**/api/query", h);
}
/** Drop expected console errors (the browser logs a failed 502 request) so they don't fail the run. */
export const forgetErrors = (ctx, re) => { for (let i = ctx.errors.length - 1; i >= 0; i--) if (re.test(ctx.errors[i])) ctx.errors.splice(i, 1); };
/** Let the 500 ms autosave land, then reload. */
export async function reloadSaved(ctx) { await ctx.page.waitForTimeout(800); await reload(ctx); }
```

- [ ] **Step 2: Failing check — rendering.** `tests/browser/checks/board-render.mjs`:

```js
import assert from "node:assert/strict";
import { start, pass, sheet, board, addSheet, widget, drawnCount, seriesOf, queriesWith, settle, tab, reload, reloadSaved, failQuery, forgetErrors } from "../board-helpers.mjs";
// P24b: own query per worksheet, failure stays in its widget, same sheet twice (RF#2), edit → re-run (RF#1), resize (RF#5).
export async function run(ctx) {
  await start(ctx);
  const p = ctx.page;
  const a = await sheet(ctx, "region", "sales"), b = await sheet(ctx, "city", "profit");
  const db = await board(ctx);
  assert.match(await p.textContent("#bd-empty"), /Add a worksheet from the list/);
  await addSheet(ctx, a); await addSheet(ctx, b); await addSheet(ctx, a);
  await drawnCount(ctx, 3);
  let n = ctx.queries.length;
  await reloadSaved(ctx); await tab(ctx, db); await drawnCount(ctx, 3); // empty cache: each sheet queries
  assert.ok(queriesWith(ctx, n, "region", "sales") >= 1, "worksheet A sent its query");
  assert.ok(queriesWith(ctx, n, "city", "profit") >= 1, "worksheet B sent its query");
  const clear = await failQuery(ctx, (body) => JSON.stringify(body).includes('"city"'));
  await reload(ctx); await tab(ctx, db);
  await widget(ctx, b).locator(".bd-widget__body", { hasText: /failed/i }).waitFor();
  await drawnCount(ctx, 2);                                             // both A widgets still drawn
  await clear(); forgetErrors(ctx, /502|Failed to load resource/);
  await reload(ctx); await tab(ctx, db); await drawnCount(ctx, 3);
  assert.equal(await seriesOf(widget(ctx, b)), 1);
  await widget(ctx, b).locator(`.bd-widget__btn[aria-label="Edit worksheet ${b}"]`).click();
  assert.ok(await p.isVisible("#dashboard-view") && await p.isHidden("#board-view"), "Edit opens the worksheet");
  await p.click('.ws-field__add[aria-label="Add sales to Rows"]'); await settle(ctx);
  await tab(ctx, db); await drawnCount(ctx, 3);
  assert.equal(await seriesOf(widget(ctx, b)), 2, "the hidden dashboard shows the edit");
  const width = () => widget(ctx, a).first().locator(".ws-chart-canvas").evaluate((h) => h.firstElementChild.getBoundingClientRect().width);
  const w0 = await width(); n = ctx.queries.length;
  const vp = p.viewportSize(); await p.setViewportSize({ width: vp.width - 300, height: vp.height });
  for (let i = 0; i < 30 && (await width()) === w0; i++) await p.waitForTimeout(100);
  assert.notEqual(await width(), w0, "the chart follows the column width");
  assert.equal(ctx.queries.length, n, "a resize never re-queries");
  await p.screenshot({ path: `${ctx.shots}/board-${ctx.scheme}.png` });
  return pass("own queries, failure inside its widget, same sheet twice, edit re-runs, resize without query");
}
```

- [ ] **Step 3: Failing check — editing.** `tests/browser/checks/board-edit.mjs`:

```js
import assert from "node:assert/strict";
import { start, pass, sheet, board, addSheet, widget, area, tab, reloadSaved } from "../board-helpers.mjs";
// P24b: text edit + limit + undo/redo, pointer move/resize, keys, overlap snap-back, persistence, undo after close (RF#3).
export async function run(ctx) {
  await start(ctx);
  const p = ctx.page, a = await sheet(ctx, "region", "sales"), db = await board(ctx);
  await addSheet(ctx, a);                          // 6 × 4 at (0, 0)
  await p.click("#bd-add-text");                   // 12 × 1 at row 4 (first free), editor open
  await p.fill(".bd-textedit input", "x".repeat(81)); await p.click(".bd-textedit .btn--primary");
  assert.match(await p.textContent(".bd-textedit .field-error"), /at most 80/);
  await p.fill(".bd-textedit input", "Sales overview"); await p.fill(".bd-textedit textarea", "Q3 by region");
  await p.click(".bd-textedit .btn--primary");
  assert.equal(await widget(ctx, "Sales overview").locator(".bd-text").textContent(), "Q3 by region");
  await p.keyboard.press("Control+z"); await widget(ctx, "Heading").waitFor();
  await p.keyboard.press("Control+Shift+z"); await widget(ctx, "Sales overview").waitFor();
  const w = widget(ctx, a);
  const m = await p.$eval("#bd-canvas", (c) => { const cs = getComputedStyle(c), g = parseFloat(cs.columnGap);
    return { col: (c.clientWidth - g * 11) / 12 + g, row: parseFloat(cs.gridAutoRows) + g }; });
  const drag = async (sel, dx, dy) => {
    const r = await w.locator(sel).boundingBox(), x = r.x + Math.min(20, r.width / 2), y = r.y + r.height / 2;
    await p.mouse.move(x, y); await p.mouse.down(); await p.mouse.move(x + dx, y + dy, { steps: 6 }); await p.mouse.up();
  };
  await drag(".bd-widget__head", 3 * m.col, 0);   assert.equal(await area(w), "1 / 4 / span 4 / span 6");
  await drag(".bd-widget__resize", m.col, 0);     assert.equal(await area(w), "1 / 4 / span 4 / span 7");
  await w.focus(); await p.keyboard.press("ArrowLeft");  assert.equal(await area(w), "1 / 3 / span 4 / span 7");
  await p.keyboard.press("Shift+ArrowLeft");             assert.equal(await area(w), "1 / 3 / span 4 / span 6");
  await drag(".bd-widget__head", 0, 2 * m.row);   // onto the text widget
  assert.equal(await area(w), "1 / 3 / span 4 / span 6", "an overlapping drop snaps back");
  await p.waitForFunction(() => /overlap/i.test(document.getElementById("bd-status").textContent));
  assert.ok(await p.isHidden("#bd-ghost"));
  await reloadSaved(ctx); await tab(ctx, db);
  assert.equal(await area(widget(ctx, a)), "1 / 3 / span 4 / span 6");
  assert.equal(await area(widget(ctx, "Sales overview")), "5 / 1 / span 1 / span 12");
  await widget(ctx, a).focus(); await p.keyboard.press("ArrowRight");   // one undo step that still holds A
  await p.click(`.tab__close[aria-label="Close worksheet ${a}"]`);
  assert.match(await p.textContent("dialog .dialog__body"), new RegExp(`Used on: ${db}`));
  await p.click("dialog .btn--danger");
  assert.equal(await widget(ctx, a).count(), 0);
  await p.focus(".bd-widget"); await p.keyboard.press("Control+z");          // RF#3
  assert.equal(await widget(ctx, a).count(), 0, "undo never brings back a closed worksheet's widget");
  assert.match(await p.textContent("#bd-status"), /can't come back/);
  return pass("text edit + limit + undo, move / resize / keys, overlap snap-back, persistence, undo after close");
}
```

- [ ] **Step 4: RED.** `$PW tests/browser/run.mjs`. Expect `board-render` and `board-edit` FAIL (`#board-view` never
  appears — the Board isn't mounted); every other check PASS.

- [ ] **Step 5: Markup and mount.** `Features/Board/_Board.cshtml`:

```html
@* Dashboard tab (P24b): worksheets and text laid out on a 12-column snap grid. Driven by Board/board.js
   (+ board-drag.js; grid math in the pure board-layout.js); each worksheet widget draws through
   Dashboard/worksheet-view.js. *@
<section class="view view--board" id="board-view" aria-label="Dashboard" hidden>
    <div class="board">
        <aside class="bd-side" aria-label="Worksheets">
            <h2 class="bd-side__title">Worksheets</h2>
            <ul class="bd-sheets" id="bd-sheets"></ul>
            <button type="button" class="btn" id="bd-add-text"><span data-icon="label"></span>Add text</button>
            <p class="bd-side__hint">Add a worksheet, or drag it onto the canvas.</p>
        </aside>
        <div class="bd-main" id="bd-main">
            <div class="bd-bar" id="bd-bar">
                <button type="button" class="iconbtn" id="bd-undo" aria-label="Undo (Ctrl+Z)" title="Undo (Ctrl+Z)" disabled><span data-icon="undo"></span></button>
                <button type="button" class="iconbtn" id="bd-redo" aria-label="Redo (Ctrl+Shift+Z)" title="Redo (Ctrl+Shift+Z)" disabled><span data-icon="redo"></span></button>
                <p class="bd-status" id="bd-status" role="status" aria-live="polite"></p>
            </div>
            <div class="bd-scroll" id="bd-scroll">
                <div class="bd-canvas" id="bd-canvas">
                    <div class="bd-ghost" id="bd-ghost" aria-hidden="true" hidden><span class="bd-ghost__icon" data-icon="warning"></span><span class="bd-ghost__text"></span></div>
                </div>
                <div class="bd-empty" id="bd-empty" hidden>
                    <p class="empty__title">This dashboard is empty</p>
                    <p>Add a worksheet from the list.</p>
                </div>
            </div>
        </div>
    </div>
</section>
```

  `Shell/Index.cshtml`: `<link rel="stylesheet" href="~/features/Board/board.css" />` after `dashboard.css`;
  `<partial name="~/Features/Board/_Board.cshtml" />` after the `_Dashboard` partial. `Shell/app.js`:
  `import { initBoard } from "../Board/board.js";` after the Dashboard import, and `initBoard();` after
  `initDashboards();` (static `data-icon` spans hydrate as today).

- [ ] **Step 6: `Features/Board/board-drag.js`.**

```js
// Board/board-drag.js — pointer move (drag a widget's header) and resize (drag its corner) on the board
// grid, plus the arrow-key step. Snaps through board-layout; a ghost shows the target cells, marked (icon +
// text + colour) when the drop is refused; a refused drop snaps back and the caller says why. No store access.
import { cellsFromPixels, moveBy, resizeBy, GRID } from "./board-layout.js";

const KEYS = { ArrowLeft: [-1, 0], ArrowRight: [1, 0], ArrowUp: [0, -1], ArrowDown: [0, 1] };
/** An arrow is a one-cell step; Shift resizes. null for any other key, or with Ctrl / Meta / Alt. */
export function keyStep(e) {
  const d = KEYS[e.key];
  return !d || e.ctrlKey || e.metaKey || e.altKey ? null : { dx: d[0], dy: d[1], resize: e.shiftKey };
}

/** Cell metrics in px from the live canvas — the column width follows the panel. */
export function gridMetrics(canvas) {
  const cs = getComputedStyle(canvas), gap = parseFloat(cs.columnGap) || 0;
  return { col: (canvas.clientWidth - gap * (GRID.cols - 1)) / GRID.cols, row: parseFloat(cs.gridAutoRows) || 0, gap };
}

export const gridArea = (r) => `${r.y + 1} / ${r.x + 1} / span ${r.h} / span ${r.w}`;

function showGhost(ghost, r, ok) {
  const w = Math.min(GRID.cols, Math.max(1, r.w)), h = Math.max(1, r.h); // a refused target is drawn inside the grid
  ghost.style.gridArea = gridArea({ x: Math.min(Math.max(0, r.x), GRID.cols - w), y: Math.max(0, r.y), w, h });
  ghost.classList.toggle("is-invalid", !ok);
  ghost.querySelector(".bd-ghost__text").textContent = ok ? "Drop here" : "Can't drop here";
  ghost.hidden = false;
}

export function wireDrag({ node, head, handle, canvas, ghost, widgets, id, onCommit, onReject }) {
  const start = (e, mode) => {
    if (e.button !== 0 || e.target.closest("button, input, textarea")) return;
    e.preventDefault();
    const target = e.currentTarget, m = gridMetrics(canvas), x0 = e.clientX, y0 = e.clientY;
    const cur = widgets().find((w) => w.id === id); if (!cur) return;
    target.setPointerCapture(e.pointerId); node.classList.add("is-dragging");
    let dx = 0, dy = 0, rect = cur;
    const move = (ev) => {
      const px = ev.clientX - x0, py = ev.clientY - y0;
      dx = cellsFromPixels(px, m.col, m.gap); dy = cellsFromPixels(py, m.row, m.gap);
      const cand = mode === "move" ? { ...cur, x: cur.x + dx, y: cur.y + dy } : { ...cur, w: cur.w + dx, h: cur.h + dy };
      rect = mode === "move" ? moveBy(widgets(), id, dx, dy) : resizeBy(widgets(), id, dx, dy);
      if (mode === "move") node.style.translate = `${px}px ${py}px`;
      showGhost(ghost, rect ?? cand, Boolean(rect));
    };
    const end = (ev) => {
      target.removeEventListener("pointermove", move); target.removeEventListener("pointerup", end); target.removeEventListener("pointercancel", end);
      node.style.translate = ""; node.classList.remove("is-dragging"); ghost.hidden = true;
      if (ev.type === "pointercancel" || (!dx && !dy)) return;
      if (rect) onCommit(rect); else onReject(mode);
    };
    target.addEventListener("pointermove", move); target.addEventListener("pointerup", end); target.addEventListener("pointercancel", end);
  };
  head.addEventListener("pointerdown", (e) => start(e, "move"));
  handle.addEventListener("pointerdown", (e) => start(e, "resize"));
}
```

Continue with the styles and `board.js`: [plan-board-3.md](plan-board-3.md).
