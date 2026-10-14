# P24 plan — Task 4: grid layout

Part of the [P24 plan](plan-overview.md); read its Global Constraints and shared interfaces first. Paths are
relative to the app root; `NODE` = `~/.nvm/versions/node/v24.20.0/bin/node`. Tasks 4–6 span three files:
this one, [plan-model-2.md](plan-model-2.md) (Task 5, store) and [plan-model-3.md](plan-model-3.md) (Task 6,
workbook v2). Spec: [§ Canvas](../p24-dashboards.md#canvas).

### Task 4: `Board/board-layout.js` — pure grid math

**Files:**
- Create: `src/DashboardBuilder/Features/Board/board-layout.js`
- Create: `tests/js/board-layout.test.mjs`

**Interfaces:**
- Consumes: nothing (no imports).
- Produces (Tasks 6 and 8): exactly the overview's list. A rect is `{ x, y, w, h }` in whole cells; a widget is
  a rect plus `id` and `kind` (`"sheet"` | `"text"`). `firstFree` is geometry only — the 12-widget cap is the
  caller's check (Board add, `normaliseLayout`). `moveBy` / `resizeBy` return `null`, never a clamped rect.
  `normaliseLayout` (import only) keeps every non-rect property, input order, and returns issue sentences
  that start lower-case — the caller prefixes `Dashboard "<name>": `.

- [ ] **Step 1: Write the failing test** — `tests/js/board-layout.test.mjs`:

```js
import { test } from "node:test";
import assert from "node:assert/strict";
import { GRID, SIZE_LIMITS, DEFAULT_SIZE, overlaps, fits, firstFree, clampRect, cellsFromPixels, moveBy, resizeBy,
  normaliseLayout } from "../../src/DashboardBuilder/Features/Board/board-layout.js";

const wd = (id, x, y, w = 6, h = 4, kind = "sheet") => ({ id, kind, x, y, w, h });
const rect = ({ x, y, w, h }) => ({ x, y, w, h });
const stack = (n, h) => Array.from({ length: n }, (_, i) => wd(`f#${i}`, 0, i * h, 12, h));

test("grid, size limits and default sizes match the spec", () => {
  assert.deepEqual(GRID, { cols: 12, maxRows: 96, maxWidgets: 12 });
  assert.deepEqual(SIZE_LIMITS, { sheet: { minW: 2, minH: 2 }, text: { minW: 2, minH: 1 }, maxW: 12, maxH: 24 });
  assert.deepEqual(DEFAULT_SIZE, { sheet: { w: 6, h: 4 }, text: { w: 12, h: 1 } });
});
test("rects overlap only when they share a cell — touching edges do not", () => {
  const a = { x: 0, y: 0, w: 6, h: 4 };
  assert.equal(overlaps(a, { x: 5, y: 3, w: 2, h: 2 }), true);
  assert.equal(overlaps(a, { x: 2, y: 1, w: 1, h: 1 }), true); // contained
  for (const b of [{ x: 6, y: 0, w: 6, h: 4 }, { x: 0, y: 4, w: 6, h: 4 }, { x: 6, y: 4, w: 1, h: 1 }])
    assert.equal(overlaps(a, b), false, JSON.stringify(b));
});
test("fits: whole cells inside 12 × 96, clear of every other widget except ignoreId", () => {
  const ws = [wd("w#1", 0, 0)];
  assert.equal(fits(ws, { x: 6, y: 0, w: 6, h: 4 }), true);
  assert.equal(fits(ws, { x: 4, y: 0, w: 4, h: 2 }), false);
  assert.equal(fits(ws, { x: 0, y: 0, w: 6, h: 4 }, "w#1"), true);
  assert.equal(fits([], { x: 0, y: 92, w: 2, h: 4 }), true); // y + h = 96
  for (const r of [{ x: 7, y: 0, w: 6, h: 4 }, { x: -1, y: 0, w: 2, h: 2 }, { x: 0, y: 93, w: 2, h: 4 }, { x: 0.5, y: 0, w: 2, h: 2 }])
    assert.equal(fits([], r), false, JSON.stringify(r));
});
test("firstFree scans rows top to bottom, each row left to right", () => {
  assert.deepEqual(firstFree([], 6, 4), { x: 0, y: 0 });
  assert.deepEqual(firstFree([wd("a", 0, 0)], 6, 4), { x: 6, y: 0 });
  assert.deepEqual(firstFree([wd("a", 0, 0), wd("b", 6, 0)], 6, 4), { x: 0, y: 4 });
  assert.deepEqual(firstFree([wd("a", 0, 0, 6, 2), wd("b", 6, 0)], 6, 4), { x: 0, y: 2 });
  assert.deepEqual(firstFree([wd("t", 0, 0, 12, 1, "text")], 12, 1), { x: 0, y: 1 });
});
test("firstFree returns null when nothing fits under the row limit", () => {
  assert.equal(firstFree(stack(4, 24), 2, 2), null);
  assert.deepEqual(firstFree(stack(3, 24), 12, 24), { x: 0, y: 72 });
  assert.equal(firstFree([], 13, 1), null);
});
test("clampRect pulls a rect into the grid and its kind's size limits, in whole cells", () => {
  assert.deepEqual(clampRect("sheet", { x: 10, y: -3, w: 6, h: 1 }), { x: 6, y: 0, w: 6, h: 2 });
  assert.deepEqual(clampRect("text", { x: 0, y: 0, w: 1, h: 1 }), { x: 0, y: 0, w: 2, h: 1 });
  assert.deepEqual(clampRect("sheet", { x: 0, y: 95, w: 20, h: 30 }), { x: 0, y: 72, w: 12, h: 24 });
  assert.deepEqual(clampRect("sheet", { x: 1.6, y: "a", w: null, h: 3.4 }), { x: 2, y: 0, w: 6, h: 3 });
});
test("cellsFromPixels rounds a drag to the nearest cell, gap included, never -0", () => {
  for (const [px, want] of [[0, 0], [45, 0], [47, 1], [184, 2], [-47, -1], [-40, 0]])
    assert.equal(cellsFromPixels(px, 80, 12), want, String(px));
  assert.equal(cellsFromPixels(50, 0, 0), 0);
});
test("moveBy returns the target rect, or null for a step that overlaps or leaves the grid", () => {
  const ws = [wd("a", 0, 0), wd("b", 6, 4)];
  assert.deepEqual(moveBy(ws, "a", 0, 1), { x: 0, y: 1, w: 6, h: 4 });
  assert.deepEqual(moveBy(ws, "b", 0, 88), { x: 6, y: 92, w: 6, h: 4 });
  for (const [id, dx, dy] of [["a", 1, 1], ["a", -1, 0], ["b", 1, 0], ["b", 0, 89], ["nope", 0, 1]])
    assert.equal(moveBy(ws, id, dx, dy), null, `${id} ${dx},${dy}`);
  assert.deepEqual(ws[0], wd("a", 0, 0)); // never mutates
});
test("resizeBy keeps each kind's size limits and never overlaps", () => {
  const ws = [wd("a", 0, 0), wd("b", 6, 0), wd("t", 0, 4, 12, 1, "text")];
  assert.deepEqual(resizeBy(ws, "a", 0, -2), { x: 0, y: 0, w: 6, h: 2 });
  assert.deepEqual(resizeBy(ws, "t", -10, 0), { x: 0, y: 4, w: 2, h: 1 });
  for (const [dw, dh] of [[0, -3], [1, 0], [-5, 0], [0, 1]]) assert.equal(resizeBy(ws, "a", dw, dh), null, `${dw},${dh}`);
  assert.equal(resizeBy([wd("a", 0, 0, 6, 24)], "a", 0, 1), null); // h ≤ 24
});
test("a clean layout passes through normaliseLayout unchanged", () => {
  const ws = [wd("a", 0, 0), wd("b", 6, 0)];
  assert.deepEqual(normaliseLayout(ws), { widgets: ws, issues: [] });
});
test("normaliseLayout clamps, then moves overlaps to the first free spot, each reported in order", () => {
  const { widgets, issues } = normaliseLayout([
    { kind: "text", heading: "Q3", body: "", x: 0, y: 0, w: 14, h: 1 },
    { kind: "sheet", sheet: 0, x: 0, y: 0, w: 6, h: 4 }, { kind: "sheet", sheet: 1, x: 0, y: 1, w: 6, h: 4 }]);
  assert.deepEqual(widgets.map(rect), [{ x: 0, y: 0, w: 12, h: 1 }, { x: 0, y: 1, w: 6, h: 4 }, { x: 6, y: 1, w: 6, h: 4 }]);
  assert.equal(widgets[0].heading, "Q3"); assert.equal(widgets[2].sheet, 1);
  assert.deepEqual(issues, ["widget 1 was off the grid or the wrong size — resized to fit.",
    "widget 2 overlapped another — moved to the first free spot.", "widget 3 overlapped another — moved to the first free spot."]);
});
test("normaliseLayout keeps the first 12 widgets and drops one with no free spot", () => {
  const capped = normaliseLayout(stack(13, 4));
  assert.equal(capped.widgets.length, 12); assert.deepEqual(capped.issues, ["only the first 12 widgets were opened."]);
  const full = normaliseLayout([...stack(4, 24), wd("x", 0, 0, 2, 2)]);
  assert.equal(full.widgets.length, 4);
  assert.deepEqual(full.issues, ["widget 5 overlapped another and there was no free spot — dropped."]);
});
```

- [ ] **Step 2: Run it to verify it fails** — `$NODE --test tests/js/board-layout.test.mjs`
  Expected: FAIL — `ERR_MODULE_NOT_FOUND` for `Features/Board/board-layout.js`.

- [ ] **Step 3: Implement** — `src/DashboardBuilder/Features/Board/board-layout.js`:

```js
// Dashboard grid math (P24b) — pure, no imports, unit-tested. A rect is { x, y, w, h } in whole cells of a
// 12-column grid; a widget is a rect plus `id` and `kind` ("sheet" | "text"). Nothing here clamps
// silently: moveBy / resizeBy return null for a step that would overlap, leave the grid or break a size
// limit. Only normaliseLayout (workbook import) clamps or moves, and it reports every change.
export const GRID = Object.freeze({ cols: 12, maxRows: 96, maxWidgets: 12 });
export const SIZE_LIMITS = Object.freeze({ sheet: { minW: 2, minH: 2 }, text: { minW: 2, minH: 1 }, maxW: 12, maxH: 24 });
export const DEFAULT_SIZE = Object.freeze({ sheet: { w: 6, h: 4 }, text: { w: 12, h: 1 } });

/** True when a and b share at least one cell; touching edges don't count. */
export const overlaps = (a, b) => a.x < b.x + b.w && b.x < a.x + a.w && a.y < b.y + b.h && b.y < a.y + a.h;

const inGrid = (r) => [r.x, r.y, r.w, r.h].every(Number.isInteger) && r.x >= 0 && r.y >= 0 && r.w >= 1 && r.h >= 1
  && r.x + r.w <= GRID.cols && r.y + r.h <= GRID.maxRows;
const sizeOk = (kind, r) => {
  const m = SIZE_LIMITS[kind] ?? SIZE_LIMITS.sheet;
  return r.w >= m.minW && r.w <= SIZE_LIMITS.maxW && r.h >= m.minH && r.h <= SIZE_LIMITS.maxH;
};

/** The rect lies inside the grid and overlaps no widget (bar the one with id `ignoreId`). */
export function fits(widgets, rect, ignoreId = null) {
  return inGrid(rect) && !widgets.some((o) => o.id !== ignoreId && overlaps(o, rect));
}

/** The first spot a w × h rect fits, scanning rows top to bottom and each row left to right; null if none. */
export function firstFree(widgets, w, h) {
  for (let y = 0; y + h <= GRID.maxRows; y++)
    for (let x = 0; x + w <= GRID.cols; x++) if (fits(widgets, { x, y, w, h })) return { x, y };
  return null;
}

const whole = (v, fallback) => (Number.isFinite(v) ? Math.round(v) : fallback);
const within = (v, lo, hi) => Math.min(hi, Math.max(lo, v));
/** The nearest legal rect for this kind: whole cells, size limits, inside the grid. Import only. */
export function clampRect(kind, rect) {
  const m = SIZE_LIMITS[kind] ?? SIZE_LIMITS.sheet, d = DEFAULT_SIZE[kind] ?? DEFAULT_SIZE.sheet;
  const w = within(whole(rect.w, d.w), m.minW, SIZE_LIMITS.maxW), h = within(whole(rect.h, d.h), m.minH, SIZE_LIMITS.maxH);
  return { x: within(whole(rect.x, 0), 0, GRID.cols - w), y: within(whole(rect.y, 0), 0, GRID.maxRows - h), w, h };
}

/** A pixel drag → whole cells: one cell step is a cell plus one gap. */
export const cellsFromPixels = (px, cellPx, gapPx) => (cellPx + gapPx > 0 ? Math.round(px / (cellPx + gapPx)) || 0 : 0);

export function moveBy(widgets, id, dx, dy) {
  const wd = widgets.find((o) => o.id === id);
  if (!wd) return null;
  const r = { x: wd.x + dx, y: wd.y + dy, w: wd.w, h: wd.h };
  return fits(widgets, r, id) ? r : null;
}
export function resizeBy(widgets, id, dw, dh) {
  const wd = widgets.find((o) => o.id === id);
  if (!wd) return null;
  const r = { x: wd.x, y: wd.y, w: wd.w + dw, h: wd.h + dh };
  return sizeOk(wd.kind, r) && fits(widgets, r, id) ? r : null;
}

/** Imported widgets → a legal layout, in input order: the first 12 kept; each clamped; one that then
 *  overlaps an earlier one moves to the first free spot, or is dropped when there is none. */
export function normaliseLayout(widgets) {
  const issues = [], placed = [];
  if (widgets.length > GRID.maxWidgets) issues.push(`only the first ${GRID.maxWidgets} widgets were opened.`);
  widgets.slice(0, GRID.maxWidgets).forEach((wd, i) => {
    let r = clampRect(wd.kind, wd);
    if (["x", "y", "w", "h"].some((k) => r[k] !== wd[k])) issues.push(`widget ${i + 1} was off the grid or the wrong size — resized to fit.`);
    if (!fits(placed, r)) {
      const spot = firstFree(placed, r.w, r.h);
      if (!spot) { issues.push(`widget ${i + 1} overlapped another and there was no free spot — dropped.`); return; }
      r = { ...r, ...spot };
      issues.push(`widget ${i + 1} overlapped another — moved to the first free spot.`);
    }
    placed.push({ ...wd, ...r });
  });
  return { widgets: placed, issues };
}
```

- [ ] **Step 4: Run to verify it passes** — `$NODE --check src/DashboardBuilder/Features/Board/board-layout.js &&
  $NODE --test tests/js/board-layout.test.mjs` → Expected: PASS (12 tests).
- [ ] **Step 5: Full suite** — `$NODE --test tests/js/*.test.mjs && dotnet test` → all green.
- [ ] **Step 6: Commit** — `git add src/DashboardBuilder/Features/Board/board-layout.js tests/js/board-layout.test.mjs &&
  git commit` with message `Add pure dashboard grid layout: fit, first free, clamp, move, resize (P24b)` + the
  Co-Authored-By line.

Next: [plan-model-2.md](plan-model-2.md) — Task 5, store dashboards and widgets.
