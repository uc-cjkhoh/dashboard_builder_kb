# P24 plan — Task 5: store dashboards and widgets

Part of the [P24 plan](plan-overview.md) (Tasks 4–6: [plan-model.md](plan-model.md) → this file →
[plan-model-3.md](plan-model-3.md)); read the overview's Global Constraints and shared interfaces first. Paths
are relative to the app root; `NODE` = `~/.nvm/versions/node/v24.20.0/bin/node`. Spec:
[§ Store](../p24-dashboards.md#store), [§ Tabs](../p24-dashboards.md#tabs).

### Task 5: store dashboards + widgets, `LIMITS.tabs`

**Files:**
- Modify: `src/DashboardBuilder/Features/Core/store.js` (the tabs block Task 2 wrote; header comment lines 3–15)
- Modify: `src/DashboardBuilder/Features/Core/validate.js:12` (`LIMITS`)
- Modify: `src/DashboardBuilder/Features/Workbook/workbook-model.js:125-127` — the **only** `LIMITS.dashboards`
  uses in the app (`grep -rn "LIMITS.dashboards" src tests` must print nothing afterwards); Task 6 rewrites them.
- Test: `tests/js/store.test.mjs` (Task 2 created it — append), `tests/js/validate.test.mjs` (append)

**Interfaces:**
- Consumes: Task 2's `tabs`, `createWorksheet`, `updateSheet`, `switchTab`, `renameTab`, `closeTab`, `showModel`;
  Task 4's `GRID` (test only).
- Produces (Tasks 6–9): the overview's "after Task 5" list. `createBoard(name)` returns the tab. Ids are never
  persisted — a workbook stores indexes and `openWorkbook` mints fresh ids — so the `ws` / `db` / `w` counters
  only climb and never need bumping on load. `updateBoard` stores the array it is given (callers pass a fresh
  one); `closeTab(worksheetId)` gives each affected dashboard a **new** filtered array, so a history snapshot
  of the old array is never rewritten (Task 8 drops snapshot widgets whose `tabById(sheetId)` is null).
  `LIMITS.tabs` is enforced by callers (Task 7 toast, Task 6 import), not by the store.

- [ ] **Step 1: Write the failing tests** — add `createBoard, updateBoard, activeBoard, boardList, boardsUsing,
  nextWidgetId` to `tests/js/store.test.mjs`'s import from `Core/store.js` (plus any of `tabs, bus, showModel,
  createWorksheet, switchTab, renameTab, closeTab, tabById, worksheetList, activeWorksheet, activeTabId` it
  lacks), then append:

```js
const reset = () => { for (const t of [...tabs]) closeTab(t.id); showModel(); };
function record(type, fn) {
  const got = [], h = (e) => got.push(e.detail);
  bus.addEventListener(type, h);
  try { fn(); } finally { bus.removeEventListener(type, h); }
  return got;
}
const sheetW = (sheetId, x = 0, y = 0) => ({ id: nextWidgetId(), kind: "sheet", sheetId, x, y, w: 6, h: 4 });

test("createBoard adds a dashboard tab at the end and makes it the active view", () => {
  reset();
  const ws = createWorksheet("Sales"), db = createBoard("Overview");
  assert.match(db.id, /^db#\d+$/); assert.equal(db.kind, "dashboard"); assert.deepEqual(db.widgets, []);
  assert.deepEqual(tabs.map((t) => t.id), [ws.id, db.id]);
  assert.equal(activeBoard(), db); assert.equal(activeWorksheet(), null); assert.equal(activeTabId(), db.id);
  assert.deepEqual(boardList(), [db]); assert.deepEqual(worksheetList(), [ws]);
  switchTab(ws.id); assert.equal(activeBoard(), null); assert.equal(activeWorksheet(), ws);
  renameTab(db.id, "Ops"); assert.equal(db.name, "Ops");
});
test("nextWidgetId mints unique w#N ids", () => {
  const a = nextWidgetId(), b = nextWidgetId();
  assert.match(a, /^w#\d+$/); assert.notEqual(a, b);
});
test("updateBoard stores the widgets and emits dashboard:changed for that dashboard only", () => {
  reset();
  const ws = createWorksheet("S"), db = createBoard("D"), widgets = [sheetW(ws.id)];
  const got = record("dashboard:changed", () => { updateBoard(db.id, widgets); updateBoard(ws.id, []); updateBoard("db#0", []); });
  assert.deepEqual(got, [{ id: db.id }]); assert.equal(tabById(db.id).widgets, widgets); assert.equal(ws.widgets, undefined);
});
test("boardsUsing lists the dashboards that show a worksheet", () => {
  reset();
  const a = createWorksheet("A"), b = createWorksheet("B"), one = createBoard("One"), two = createBoard("Two");
  updateBoard(one.id, [sheetW(a.id), sheetW(b.id, 6)]);
  updateBoard(two.id, [sheetW(a.id), { id: nextWidgetId(), kind: "text", heading: "H", body: "", x: 0, y: 4, w: 12, h: 1 }]);
  assert.deepEqual(boardsUsing(a.id), [{ id: one.id, name: "One" }, { id: two.id, name: "Two" }]);
  assert.deepEqual(boardsUsing(b.id), [{ id: one.id, name: "One" }]);
});
test("closing a worksheet removes its widgets from every dashboard, one event each (Review Focus #3)", () => {
  reset();
  const a = createWorksheet("A"), b = createWorksheet("B");
  const one = createBoard("One"), two = createBoard("Two"), three = createBoard("Three");
  const before = [sheetW(a.id), sheetW(b.id, 6)];
  updateBoard(one.id, before); updateBoard(two.id, [sheetW(a.id)]); updateBoard(three.id, [sheetW(b.id)]);
  assert.deepEqual(record("dashboard:changed", () => closeTab(a.id)), [{ id: one.id }, { id: two.id }]);
  assert.deepEqual(one.widgets.map((w) => w.sheetId), [b.id]); assert.deepEqual(two.widgets, []);
  assert.equal(before.length, 2); // a new array — an undo snapshot of the old one is not rewritten
  assert.deepEqual(boardsUsing(a.id), []); assert.equal(tabById(a.id), null);
});
test("closing a dashboard keeps its worksheets; closing the active tab activates the next one", () => {
  reset();
  const a = createWorksheet("A"), d = createBoard("D");
  updateBoard(d.id, [sheetW(a.id)]);
  const b = createWorksheet("B");
  switchTab(d.id); closeTab(d.id);
  assert.deepEqual(tabs.map((t) => t.id), [a.id, b.id]); assert.equal(activeWorksheet(), b);
  closeTab(b.id); closeTab(a.id); assert.equal(activeTabId(), null);
});
```

  and append to `tests/js/validate.test.mjs`:

```js
test("tab, widget and text-block limits (P24b) match the board grid", async () => {
  const { GRID } = await import("../../src/DashboardBuilder/Features/Board/board-layout.js");
  assert.equal(LIMITS.tabs, 50); assert.equal(LIMITS.dashboards, undefined);
  assert.equal(LIMITS.widgets, GRID.maxWidgets); assert.equal(LIMITS.heading, 80); assert.equal(LIMITS.body, 2000);
});
```

- [ ] **Step 2: Run to verify they fail** — `$NODE --test tests/js/store.test.mjs tests/js/validate.test.mjs`
  Expected: FAIL — `SyntaxError: The requested module '…/Core/store.js' does not provide an export named
  'createBoard'`; validate: `LIMITS.tabs` is `undefined`, expected `50`.

- [ ] **Step 3: Implement.** In `Core/validate.js:12` replace `inValues: 500, dashboards: 50, pillsPerShelf: 20,` with:

```js
  inValues: 500, pillsPerShelf: 20,
  tabs: 50,                           // P24b: worksheet + dashboard tabs per workbook
  widgets: 12, heading: 80, body: 2000, // P24b: per dashboard; a text widget's heading / body characters
```

  Then `sed -i 's/LIMITS\.dashboards/LIMITS.tabs/g' src/DashboardBuilder/Features/Workbook/workbook-model.js`
  (the issue text there stays "dashboards" until Task 6). In `Core/store.js`, rewrite the header comment's
  `dashboards:` / events lines (3–15) to describe `tabs` (both kinds, the widget shapes from the overview) and
  events `worksheet:changed {id}` / `dashboard:changed {id}`. Replace Task 2's `tabs` / `activeView` / sequence
  declarations and its `isModelActive`, `activeTabId`, `activeWorksheet`, `tabById`, `worksheetList` with:

```js
// Tabs: worksheets and dashboards in one ordered strip list (P24b), plus which view is active.
export const tabs = [];
let activeView = { kind: "model" }; // { kind: "model" } | { kind: "worksheet", id } | { kind: "dashboard", id }
let wsSeq = 0, dbSeq = 0, widgetSeq = 0;

export const tabById = (id) => tabs.find((t) => t.id === id) ?? null;
export const worksheetList = () => tabs.filter((t) => t.kind === "worksheet");
export const boardList = () => tabs.filter((t) => t.kind === "dashboard");
export const isModelActive = () => activeView.kind === "model";
export const activeTabId = () => (activeView.kind === "model" ? null : activeView.id);
export const activeWorksheet = () => (activeView.kind === "worksheet" ? tabById(activeView.id) : null);
export const activeBoard = () => (activeView.kind === "dashboard" ? tabById(activeView.id) : null);
export const nextWidgetId = () => `w#${++widgetSeq}`;
/** The dashboards that show this worksheet — for the close confirm ("Used on: …"). */
export const boardsUsing = (sheetId) => boardList()
  .filter((b) => b.widgets.some((w) => w.kind === "sheet" && w.sheetId === sheetId)).map(({ id, name }) => ({ id, name }));
```

  and replace Task 2's `createWorksheet`, `updateSheet`, `switchTab`, `renameTab`, `closeTab` with
  (`worksheetHasContent` stays as Task 2 left it):

```js
function openTab(tab) { tabs.push(tab); switchTab(tab.id); emit("tabs:changed"); return tab; }
export const createWorksheet = (name) => openTab({ id: `ws#${++wsSeq}`, kind: "worksheet", name: name || "Dashboard", sheet: emptySheet() });
export const createBoard = (name) => openTab({ id: `db#${++dbSeq}`, kind: "dashboard", name: name || "Dashboard", widgets: [] });

/** Persist a worksheet's shelves + notify its views. */
export function updateSheet(id, sheet) {
  const t = tabById(id);
  if (t?.kind !== "worksheet") return;
  t.sheet = sheet;
  emit("worksheet:changed", { id });
}
/** Persist a dashboard's widgets (layout / text edits) + notify the board. */
export function updateBoard(id, widgets) {
  const t = tabById(id);
  if (t?.kind !== "dashboard") return;
  t.widgets = widgets;
  emit("dashboard:changed", { id });
}
export function switchTab(id) {
  const t = tabById(id);
  if (!t) return;
  activeView = { kind: t.kind, id };
  emit("view:changed");
  emit("tabs:changed");
}
export function renameTab(id, name) {
  const t = tabById(id);
  if (t && name) { t.name = name; emit("tabs:changed"); }
}
/** Close a tab. A worksheet's widgets leave every dashboard (each gets a new array); a dashboard's
 *  worksheets stay. The active tab's neighbour (or the model) becomes active. */
export function closeTab(id) {
  const idx = tabs.findIndex((t) => t.id === id);
  if (idx < 0) return;
  const [gone] = tabs.splice(idx, 1);
  if (gone.kind === "worksheet") {
    for (const b of boardList()) {
      const kept = b.widgets.filter((w) => !(w.kind === "sheet" && w.sheetId === id));
      if (kept.length !== b.widgets.length) { b.widgets = kept; emit("dashboard:changed", { id: b.id }); }
    }
  }
  if (activeView.kind !== "model" && activeView.id === id) {
    const next = tabs[Math.min(idx, tabs.length - 1)];
    activeView = next ? { kind: next.kind, id: next.id } : { kind: "model" };
    emit("view:changed");
  }
  emit("tabs:changed");
}
```

- [ ] **Step 4: Run to verify they pass** — `$NODE --check src/DashboardBuilder/Features/Core/store.js &&
  $NODE --test tests/js/store.test.mjs tests/js/validate.test.mjs` → Expected: PASS.
- [ ] **Step 5: Full suite + browser** — `$NODE --test tests/js/*.test.mjs && dotnet test`, then the browser
  harness (overview Global Constraints) → all green; worksheet behaviour is unchanged (no dashboard UI yet).
- [ ] **Step 6: Commit** — `git add -A src/DashboardBuilder/Features/Core src/DashboardBuilder/Features/Workbook/workbook-model.js
  tests/js/store.test.mjs tests/js/validate.test.mjs && git commit` with message
  `Store dashboards and widgets beside worksheets; LIMITS.tabs (P24b)` + the Co-Authored-By line.

Next: [plan-model-3.md](plan-model-3.md) — Task 6, workbook format v2.
