# P24 plan — Task 2: store `tabs` and worksheet renames

Part of the [P24 plan](plan-overview.md); read its Global Constraints first. Paths are relative to the
app root. Spec: [§ 24a](../p24-dashboards.md#24a--widget-runtime-no-visible-change) (store rename). Needs
Task 1 ([plan-runtime-a.md](plan-runtime-a.md), [plan-runtime-a2.md](plan-runtime-a2.md)) done; `$PW` is
defined in Task 1 Step 1.

### Task 2: one ordered `tabs` list of worksheets; `dashboard` → `worksheet` in code (no visible change)

**Files:**
- Create: `tests/js/store.test.mjs`
- Modify: `src/DashboardBuilder/Features/Core/store.js` — l.13–15 (header), l.90–102, l.191–241
- Modify: `src/DashboardBuilder/Features/Tabs/tabs.js` — l.2–3, 20–21, 29, 53, 64, 67, 92, 97, 104, 123, 129
- Modify: `src/DashboardBuilder/Features/Workbook/workbook.js` — l.2–3, 27, 92, 161, 178, 184, 233–234, 237
- Modify: `src/DashboardBuilder/Features/Workbook/bookmarks-dialog.js` — l.5–6, 13, 62, 84, 85, 88
- Modify: `src/DashboardBuilder/Features/Dashboard/dashboards.js` — l.9, 284, 2138 and the 14 `activeDashboard()` calls
- Modify: `tests/browser/checks/show-me.mjs` — drop the `activeDashboard` fallback

**Interfaces:**
- Consumes: Task 1's harness (`tests/browser/run.mjs`, `checks/show-me.mjs`, `checks/two-charts.mjs`).
- Produces (`Core/store.js`): `tabs` — `[{ id: "ws#N", kind: "worksheet", name, sheet }]`; `worksheetList()`,
  `tabById(id)` → tab | null, `isModelActive()`, `activeTabId()` → id | null, `activeWorksheet()` → tab | null;
  `createWorksheet(name)` → tab, `updateSheet(id, sheet)` → emits `worksheet:changed { id }`,
  `worksheetHasContent(id)`, `switchTab(id)`, `renameTab(id, name)`, `closeTab(id)`; `activeView` is
  `{ kind: "model" } | { kind: "worksheet", id }`. Removed: `dashboards`, `activeDashboard`, `activeDashboardId`,
  `createDashboard`, `switchDashboard`, `renameDashboard`, `closeDashboard`, `dashboardHasContent`, `dashboard:changed`.
- Unchanged on purpose: `Workbook/workbook-model.js` (v1 file: `serializeWorkbook({ dashboards, active })` with
  `active.kind === "dashboard"`, `parseWorkbook` → `wb.dashboards`) — Task 6 owns it; bookmark fields
  `dashId` / `dashName` (saved data); `LIMITS.dashboards` in `validate.js` (renamed `LIMITS.tabs` in Task 5);
  every user-visible "dashboard" string (tab tooltip / aria-labels, "All dashboards" badges, toasts, dialogs).

`store.js` has no imports (only `EventTarget` / `CustomEvent`, both global in Node 24), so it is tested under `node --test`.

- [ ] **Step 1: Write the failing test** — `tests/js/store.test.mjs`

```js
import { test, beforeEach } from "node:test";
import assert from "node:assert/strict";
import * as store from "../../src/DashboardBuilder/Features/Core/store.js";

const { tabs, bus, emptySheet } = store;
const seen = [];
for (const type of ["worksheet:changed", "view:changed", "tabs:changed"])
  bus.addEventListener(type, (e) => seen.push([type, e.detail?.id ?? null]));
beforeEach(() => { for (const t of [...tabs]) store.closeTab(t.id); store.showModel(); seen.length = 0; });

test("createWorksheet adds a worksheet tab, makes it active and keeps the default name", () => {
  const ws = store.createWorksheet();
  assert.match(ws.id, /^ws#\d+$/);
  assert.equal(ws.kind, "worksheet");
  assert.equal(ws.name, "Dashboard");
  assert.deepEqual(ws.sheet, emptySheet());
  assert.deepEqual(tabs, [ws]);
  assert.deepEqual(store.worksheetList(), [ws]);
  assert.equal(store.tabById(ws.id), ws);
  assert.equal(store.activeTabId(), ws.id);
  assert.equal(store.activeWorksheet(), ws);
  assert.equal(store.isModelActive(), false);
  assert.equal(store.createWorksheet("Sales").name, "Sales");
  assert.notEqual(tabs[1].id, ws.id);
});
test("updateSheet stores the sheet and emits worksheet:changed with the id", () => {
  const ws = store.createWorksheet();
  seen.length = 0;
  const sheet = { ...emptySheet(), chartType: "line" };
  store.updateSheet(ws.id, sheet);
  assert.equal(ws.sheet, sheet);
  assert.deepEqual(seen, [["worksheet:changed", ws.id]]);
  store.updateSheet("ws#999", emptySheet());
  assert.equal(seen.length, 1);
});
test("worksheetHasContent is false for an empty sheet and true once a shelf holds a field", () => {
  const ws = store.createWorksheet();
  assert.equal(store.worksheetHasContent(ws.id), false);
  store.updateSheet(ws.id, { ...emptySheet(), columns: [{ db: "d", table: "t", column: "c", category: "text" }] });
  assert.equal(store.worksheetHasContent(ws.id), true);
  assert.equal(store.worksheetHasContent("ws#999"), false);
});
test("switchTab and renameTab act on a known id only", () => {
  const a = store.createWorksheet("A"), b = store.createWorksheet("B");
  assert.equal(store.activeTabId(), b.id);
  store.switchTab(a.id);
  assert.equal(store.activeWorksheet(), a);
  store.switchTab("ws#999");
  assert.equal(store.activeWorksheet(), a);
  store.renameTab(b.id, "Bee");
  store.renameTab(b.id, "");
  assert.equal(b.name, "Bee");
});
test("closeTab activates the next neighbour, then the model when none is left", () => {
  const a = store.createWorksheet("A"), b = store.createWorksheet("B"), c = store.createWorksheet("C");
  store.switchTab(b.id);
  store.closeTab(b.id);
  assert.equal(store.activeTabId(), c.id);
  store.closeTab(a.id);
  assert.equal(store.activeTabId(), c.id);
  store.closeTab(c.id);
  assert.equal(store.isModelActive(), true);
  assert.equal(store.activeTabId(), null);
  assert.equal(store.activeWorksheet(), null);
  assert.equal(tabs.length, 0);
});
test("the pre-P24 names are gone", () => {
  for (const n of ["dashboards", "activeDashboard", "activeDashboardId", "createDashboard", "switchDashboard",
    "renameDashboard", "closeDashboard", "dashboardHasContent"]) assert.equal(store[n], undefined, n);
});
```

- [ ] **Step 2: Run it to verify it fails** — `~/.nvm/versions/node/v24.20.0/bin/node --test tests/js/store.test.mjs`
  Expected: `ℹ fail 6`, each with `TypeError: tabs is not iterable`.

- [ ] **Step 3: `store.js`.** Header l.13–15 becomes:

```js
// tabs:          [ { id: "ws#N", kind: "worksheet", name, sheet } ]  (strip order)
// bus events:    entity:moved / entity:removed / joinkey:changed / rel:changed  (model),
//                view:changed / tabs:changed / worksheet:changed {id}          (views)
```

  Lines 90–102 (from `// Dashboards + which view is active.` to the end of `activeDashboard`) become:

```js
// The tab strip after the pinned Data Model, in order, + which view is active. P24a: every tab is a
// worksheet { id: "ws#N", kind: "worksheet", name, sheet } (P24b adds dashboards).
export const tabs = [];
let activeView = { kind: "model" };   // { kind: "model" } | { kind: "worksheet", id }
let wsSeq = 0;

export function emit(type, detail) {
  bus.dispatchEvent(new CustomEvent(type, { detail }));
}

export const isModelActive = () => activeView.kind === "model";
export const activeTabId = () => (activeView.kind === "model" ? null : activeView.id);
export const tabById = (id) => tabs.find((t) => t.id === id) ?? null;
export const worksheetList = () => tabs.filter((t) => t.kind === "worksheet");
export const activeWorksheet = () => (activeView.kind === "worksheet" ? tabById(activeView.id) : null);
```

  `showModel`, `emptySheet`, `defaultMarks`, `defaultFormat` (l.104–189) stay. Lines 191–241 (`createDashboard`
  … `closeDashboard`) become:

```js
export function createWorksheet(name) {
  wsSeq += 1;
  // All new worksheets share the same default name (the id stays unique) until P24b numbers them.
  const ws = { id: `ws#${wsSeq}`, kind: "worksheet", name: name || "Dashboard", sheet: emptySheet() };
  tabs.push(ws);
  switchTab(ws.id);
  emit("tabs:changed");
  return ws;
}

/** Persist a worksheet's shelves + notify the view. */
export function updateSheet(id, sheet) {
  const ws = tabById(id);
  if (ws?.kind !== "worksheet") return;
  ws.sheet = sheet;
  emit("worksheet:changed", { id });
}

/** A worksheet has content if any shelf holds a field. */
export function worksheetHasContent(id) {
  const s = tabById(id)?.sheet;
  const m = s?.marks;
  const hasMarks = Boolean(m && (m.size || m.label || (m.detail?.length ?? 0) > 0 || (m.tooltip?.length ?? 0) > 0 || m.shape || m.path || m.angle));
  return Boolean(s && ((s.columns?.length ?? 0) > 0 || (s.rows?.length ?? 0) > 0 || (s.color?.length ?? 0) > 0 || (s.filters?.length ?? 0) > 0 || ((s.drill?.levels?.length ?? 0) > 0) || hasMarks || s.pages || s.period));
}

export function switchTab(id) {
  const tab = tabById(id);
  if (!tab) return;
  activeView = { kind: tab.kind, id };
  emit("view:changed");
  emit("tabs:changed");
}

export function renameTab(id, name) {
  const tab = tabById(id);
  if (tab && name) { tab.name = name; emit("tabs:changed"); }
}

export function closeTab(id) {
  const idx = tabs.findIndex((t) => t.id === id);
  if (idx < 0) return;
  const wasActive = activeTabId() === id;
  tabs.splice(idx, 1);
  if (wasActive) {
    const next = tabs[Math.min(idx, tabs.length - 1)];
    activeView = next ? { kind: next.kind, id: next.id } : { kind: "model" };
    emit("view:changed");
  }
  emit("tabs:changed");
}
```

- [ ] **Step 4: Run the test** — same command. Expected: `ℹ pass 6`, `ℹ fail 0`.

- [ ] **Step 5: Callers.** Rename table: `dashboards` → `tabs` (iteration / index) or `tabById(id)` (lookup);
  `activeDashboard` → `activeWorksheet`; `activeDashboardId` → `activeTabId`; `createDashboard` → `createWorksheet`;
  `switchDashboard` → `switchTab`; `renameDashboard` → `renameTab`; `closeDashboard` → `closeTab`;
  `dashboardHasContent` → `worksheetHasContent`; event `"dashboard:changed"` → `"worksheet:changed"`; id `dash#N` → `ws#N`.

| File:line | Now | Becomes |
|---|---|---|
| tabs.js:2–3 | `dashboards, isModelActive, activeDashboardId, showModel, createDashboard,` / `switchDashboard, renameDashboard, closeDashboard, dashboardHasContent, bus,` | `tabs, tabById, isModelActive, activeTabId, showModel, createWorksheet,` / `switchTab, renameTab, closeTab, worksheetHasContent, bus,` |
| tabs.js:20 | `".tab__label[data-dash-id]"` | `".tab__label[data-tab-id]"` |
| tabs.js:21 | `dashboards.find((d) => d.id === label.dataset.dashId)` | `tabById(label.dataset.tabId)` |
| tabs.js:29 | `for (const dash of dashboards)` | `for (const dash of tabs)` |
| tabs.js:53 | `activeDashboardId() === dash.id` | `activeTabId() === dash.id` |
| tabs.js:64 | `label.dataset.dashId = dash.id;` | `label.dataset.tabId = dash.id;` |
| tabs.js:67 | `if (activeDashboardId() !== dash.id) switchDashboard(dash.id);` | `if (activeTabId() !== dash.id) switchTab(dash.id);` |
| tabs.js:92 / 97 / 104 / 123 | `createDashboard()` / `dashboardHasContent(dash.id)` / `closeDashboard(dash.id)` / `renameDashboard(dash.id, r.value)` | `createWorksheet()` / `worksheetHasContent(dash.id)` / `closeTab(dash.id)` / `renameTab(dash.id, r.value)` |
| tabs.js:129 | `dashboards.findIndex(…)` | `tabs.findIndex(…)` |
| bookmarks-dialog.js:5–6 | `activeDashboard, isModelActive, dashboards, …, createDashboard,` / `updateSheet, switchDashboard, …` | `activeWorksheet, isModelActive, tabById, …, createWorksheet,` / `updateSheet, switchTab, …` |
| bookmarks-dialog.js:13 | `activeDashboard()` | `activeWorksheet()` |
| bookmarks-dialog.js:62, 84 | `dashboards.find((d) => d.id === b.dashId)` | `tabById(b.dashId)` |
| bookmarks-dialog.js:85 / 88 | `createDashboard(b.dashName)` / `switchDashboard(dash.id)` | `createWorksheet(b.dashName)` / `switchTab(dash.id)` |
| workbook.js:2–3 | `…, dashboards, bus, activeDashboardId,` / `createDashboard, updateSheet, closeDashboard, showModel, switchDashboard, …` | `…, tabs, worksheetList, bus, activeTabId,` / `createWorksheet, updateSheet, closeTab, showModel, switchTab, …` |
| workbook.js:27 | `"dashboard:changed"` | `"worksheet:changed"` |
| workbook.js:92, 161 | `for (const d of [...dashboards]) closeDashboard(d.id);` | `for (const t of [...tabs]) closeTab(t.id);` |
| workbook.js:178 / 184 | `createDashboard(d.name)` / `switchDashboard(opened[wb.active].id)` | `createWorksheet(d.name)` / `switchTab(opened[wb.active].id)` |
| workbook.js:233–234 | `const id = activeDashboardId();` / `… dashboards, active: id ? { kind: "dashboard", id } …` | `const id = activeTabId(); // the v1 file still calls the active worksheet a "dashboard" (until P24b)` / `… dashboards: worksheetList(), active: id ? { kind: "dashboard", id } …` |
| workbook.js:237 | `dashboards.length === 0` | `tabs.length === 0` |
| dashboards.js:9 + 14 calls | `activeDashboard` | `activeWorksheet` (`sed -i 's/\bactiveDashboard\b/activeWorksheet/g'`) |
| dashboards.js:284 | `bus.addEventListener("dashboard:changed", …` | `bus.addEventListener("worksheet:changed", …` |
| dashboards.js:2138 | `// Every edit goes through commit() → dashboard:changed → …` | `// Every edit goes through commit() → worksheet:changed → …` |

  `wb.dashboards` in workbook.js (l.71, 73, 177) is the parsed v1 file — unchanged. The harness:
  `sed -i 's/(st.activeWorksheet ?? st.activeDashboard)()/st.activeWorksheet()/' tests/browser/checks/show-me.mjs`.

- [ ] **Step 6: Verify** — `node --check` the five changed modules, then:

```bash
grep -rnE "\b(dashboards|activeDashboard|activeDashboardId|createDashboard|switchDashboard|renameDashboard|closeDashboard|dashboardHasContent|dashSeq)\b|dashboard:changed|dash#|dashId\b" \
  src/DashboardBuilder/Features --include=*.js | grep -vE "workbook-model.js|//|wb\.dashboards|\"[^\"]*dashboards[^\"]*\"|b\.dashId|dashId: |tablePager|history.js"
```

  Expected: exactly two lines — `workbook.js:234` (`dashboards: worksheetList()`, the v1 serialiser's argument)
  and `validate.js:12` (`dashboards: 50`, renamed in Task 7). Then the JS suite
  (Expected: `# fail 0`, `store.test.mjs` included), `dotnet test` (Expected: `Failed: 0`), restart the dev server
  and `eval "$PW tests/browser/run.mjs"` (Expected: `48/48 passed`). By hand: add / rename (double-click, F2) /
  close a tab; save a bookmark, close its tab, apply it (reopens as "Dashboard"); reload — autosave restores the
  same tabs and active tab.

- [ ] **Step 7: Commit**

```bash
git add tests/js/store.test.mjs tests/browser/checks/show-me.mjs src/DashboardBuilder/Features/Core/store.js \
  src/DashboardBuilder/Features/Tabs/tabs.js src/DashboardBuilder/Features/Workbook/workbook.js \
  src/DashboardBuilder/Features/Workbook/bookmarks-dialog.js src/DashboardBuilder/Features/Dashboard/dashboards.js
git commit -m "Hold worksheets in one ordered tabs list; rename dashboard to worksheet in code (P24a)

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"
```

Next: [Task 3 — `worksheet-view.js`](plan-runtime-b.md).
