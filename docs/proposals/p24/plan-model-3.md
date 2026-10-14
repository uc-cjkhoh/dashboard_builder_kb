# P24 plan — Task 6: workbook format v2

Part of the [P24 plan](plan-overview.md) (Tasks 4–6: [plan-model.md](plan-model.md) →
[plan-model-2.md](plan-model-2.md) → this file); read the overview's Global Constraints and shared interfaces
first. Paths are relative to the app root; `NODE` = `~/.nvm/versions/node/v24.20.0/bin/node`. Spec:
[§ Workbook format v2](../p24-dashboards.md#workbook-format-v2). Line numbers are from `main` before Task 2 —
find each function by name if Task 2 shifted them.

### Task 6: v2 serialiser, `migrateV1`, widget validation, v2 autosave key

**Files:**
- Modify: `src/DashboardBuilder/Features/Workbook/workbook-model.js` — `WORKBOOK_VERSION` (17), `migrateV1`
  (new, after 19), `serializeWorkbook` (21–54), `parseWorkbook` (65–152), new helpers after `isStr` (154),
  `cleanBookmarks` (335–357), `storageKey` (429–433 → three key functions)
- Modify: `src/DashboardBuilder/Features/Workbook/workbook.js` — imports (1–5, 16), `CHANGE_EVENTS` (25–28),
  `onConnection` (62–79), `clearWorkspace` (92), `openWorkbook` (160–189), `importFile` (219), helpers (232–237)
- Test: `tests/js/workbook-model.test.mjs` (edit existing tests + append)

**Interfaces:**
- Consumes: Task 4 `normaliseLayout`; Task 5 `tabs`, `tabById`, `activeTabId`, `createWorksheet`, `updateSheet`,
  `createBoard`, `updateBoard`, `nextWidgetId`, `closeTab`, `switchTab`, `LIMITS.tabs / widgets / heading / body`.
- Produces: `migrateV1(raw)`; `serializeWorkbook({ entities, relationships, tabs, active: { kind: "model" } | { kind, id }, … })`;
  `parseWorkbook(text)` → `{ entities, relationships, worksheets: [{ name, sheet }], dashboards: [{ name, widgets }],
  tabs: [{ kind, index }], active: { kind, index } | null, theme, sharedFilters, bookmarks, fields, parameters, issues }`
  (widgets as in the spec's v2 shape; every index points into the returned lists; `tabs` names each tab once;
  bookmark `dashboard` = a worksheet index or null); `autosaveKey`, `legacyAutosaveKey`, `savedWorkbookText(view, read)`.

- [ ] **Step 1: Update the existing tests to v2, then append the new ones.** In `tests/js/workbook-model.test.mjs`:
  1. Import line 5: `serializeWorkbook, parseWorkbook, migrateV1, autosaveKey, legacyAutosaveKey, savedWorkbookText, WORKBOOK_FORMAT,`.
  2. `sampleState()` lines 22–23: `const tabs = [{ id: "ws#1", kind: "worksheet", name: "Revenue", sheet }];` and
     `return { entities, relationships, tabs, active: { kind: "worksheet", id: "ws#1" } };`.
  3. Run `sed -i -e 's/st\.dashboards\[0\]/st.tabs[0]/g' -e 's/\.dashboards\[0\]/.worksheets[0]/g' -e 's/wb\.dashboards\.length/wb.worksheets.length/g' tests/js/workbook-model.test.mjs`
     (`wbText` / `sheetOf` stay v1 — they now exercise the migration).
  4. Line 35: `assert.deepEqual(wb.active, { kind: "worksheet", index: 0 });`. Lines 88–97: `storageKey` → `autosaveKey`.
     Line 115: `version: 2` → `version: 3`. Line 155: `assert.ok(wb.issues.includes("Only the first 50 tabs were opened."));`.
     Lines 182 and 199: expected name `"Worksheet"`; 187: `/not a dashboard/i` → `/not a worksheet/i`;
     207: `/worksheets weren't a list/`; 213: `/active tab was invalid/`; 291–292: `dashId: "ws#1"`.

  Append:
```js
const v2 = (patch) => JSON.stringify({ format: WORKBOOK_FORMAT, version: 2, entities: [], relationships: [], worksheets: [], dashboards: [], ...patch });
const ws = (name) => ({ name, sheet: {} }), sw = (sheet, x, y, w = 6, h = 4) => ({ kind: "sheet", sheet, x, y, w, h });
const rectOf = ({ x, y, w, h }) => ({ x, y, w, h });
const open = (widgets, sheets = [ws("A")]) => parseWorkbook(v2({ worksheets: sheets, dashboards: [{ name: "Board", widgets }],
  tabs: [...sheets.map((_, index) => ({ kind: "worksheet", index })), { kind: "dashboard", index: 0 }] }));

test("v2 round-trips worksheets, dashboards, widgets, strip order and the active dashboard", () => {
  const a = { id: "ws#1", kind: "worksheet", name: "Sales", sheet: emptySheet() }, b = { ...a, id: "ws#2", name: "Ops", sheet: emptySheet() };
  const d = { id: "db#1", kind: "dashboard", name: "Overview", widgets: [
    { id: "w#1", kind: "text", heading: "Q3", body: "Notes", x: 0, y: 0, w: 12, h: 1 },
    { id: "w#2", kind: "sheet", sheetId: "ws#2", x: 0, y: 1, w: 6, h: 4 }, { id: "w#3", kind: "sheet", sheetId: "ws#2", x: 6, y: 1, w: 6, h: 4 }] };
  const saved = serializeWorkbook({ entities: new Map(), relationships: new Map(), tabs: [a, d, b], active: { kind: "dashboard", id: "db#1" } });
  assert.equal(saved.version, 2);
  assert.deepEqual(saved.tabs, [{ kind: "worksheet", index: 0 }, { kind: "dashboard", index: 0 }, { kind: "worksheet", index: 1 }]);
  assert.deepEqual(saved.dashboards[0].widgets[1], { kind: "sheet", sheet: 1, x: 0, y: 1, w: 6, h: 4 });
  const wb = parseWorkbook(JSON.stringify(saved)); assert.deepEqual(wb.issues, []);
  assert.deepEqual(wb.worksheets.map((w) => w.name), ["Sales", "Ops"]);
  assert.deepEqual(wb.dashboards[0].widgets, saved.dashboards[0].widgets);
  assert.deepEqual(wb.tabs, saved.tabs); assert.deepEqual(wb.active, { kind: "dashboard", index: 0 });
});
test("a widget on a closed worksheet is not saved", () => {
  const d = { id: "db#1", kind: "dashboard", name: "D", widgets: [{ id: "w#1", kind: "sheet", sheetId: "ws#9", x: 0, y: 0, w: 6, h: 4 }] };
  assert.deepEqual(serializeWorkbook({ entities: new Map(), relationships: new Map(), tabs: [d], active: { kind: "model" } }).dashboards[0].widgets, []);
});
test("migrateV1 turns every v1 dashboard into a worksheet, in order", () => {
  const m = migrateV1({ format: WORKBOOK_FORMAT, version: 1, dashboards: [ws("A"), 5, ws("B")], active: 2, bookmarks: [] });
  assert.equal(m.version, 2); assert.deepEqual(m.worksheets, [ws("A"), 5, ws("B")]); assert.deepEqual(m.dashboards, []);
  assert.deepEqual(m.tabs, [{ kind: "worksheet", index: 0 }, { kind: "worksheet", index: 2 }]);
  assert.deepEqual(m.active, { kind: "worksheet", index: 2 });
  assert.equal(migrateV1({ format: WORKBOOK_FORMAT, version: 1 }).active, null);
});
test("a v1 autosave with bookmarks and an active tab keeps both on the same worksheet (Review Focus #4)", () => {
  const wb = parseWorkbook(wbText({ dashboards: [5, ws("A"), ws("B")], active: 2,
    bookmarks: [{ name: "On B", dashboard: 2, sheet: {} }, { name: "On A", dashboard: 1, sheet: {} }, { name: "Gone", dashboard: 0, sheet: {} }] }));
  assert.deepEqual(wb.worksheets.map((w) => w.name), ["A", "B"]);
  assert.deepEqual(wb.tabs, [{ kind: "worksheet", index: 0 }, { kind: "worksheet", index: 1 }]);
  assert.deepEqual(wb.active, { kind: "worksheet", index: 1 });
  assert.deepEqual(wb.bookmarks.map((b) => b.dashboard), [1, 0, null]);
});
test("a widget whose worksheet is missing, or of an unknown kind, is dropped and reported", () => {
  const wb = open([sw(0, 0, 0), sw(4, 6, 0), { kind: "image", x: 0, y: 4, w: 2, h: 2 }]);
  assert.equal(wb.dashboards[0].widgets.length, 1);
  assert.ok(wb.issues.includes('Dashboard "Board": skipped a worksheet widget whose worksheet is missing.'));
  assert.ok(wb.issues.includes('Dashboard "Board": skipped a widget of an unknown kind.'));
});
test("an off-grid or undersized widget is clamped; an overlapping one moves; both reported", () => {
  const wb = open([sw(0, 10, 0, 6, 1), sw(0, 6, 0)]);
  assert.deepEqual(wb.dashboards[0].widgets.map(rectOf), [{ x: 6, y: 0, w: 6, h: 2 }, { x: 0, y: 0, w: 6, h: 4 }]);
  assert.ok(wb.issues.includes('Dashboard "Board": widget 1 was off the grid or the wrong size — resized to fit.'));
  assert.ok(wb.issues.includes('Dashboard "Board": widget 2 overlapped another — moved to the first free spot.'));
});
test("text past its limits is shortened, and non-text cleared, each reported", () => {
  const wb = open([{ kind: "text", heading: "h".repeat(81), body: 7, x: 0, y: 0, w: 12, h: 1 }]);
  const t = wb.dashboards[0].widgets[0];
  assert.equal(t.heading.length, 80); assert.equal(t.body, "");
  assert.ok(wb.issues.includes(`Dashboard "Board": a text block's heading was longer than 80 characters — shortened.`));
  assert.ok(wb.issues.includes(`Dashboard "Board": a text block's text wasn't text — cleared.`));
});
test("widgets past 12 and tabs past 50 are dropped and reported", () => {
  const wb = open(Array.from({ length: 14 }, (_, i) => sw(0, (i % 2) * 6, Math.floor(i / 2) * 4)));
  assert.equal(wb.dashboards[0].widgets.length, 12);
  assert.ok(wb.issues.includes('Dashboard "Board": only the first 12 widgets were opened.'));
  const many = parseWorkbook(v2({ worksheets: Array.from({ length: 51 }, (_, i) => ws(`S${i}`)), dashboards: [{ name: "D", widgets: [sw(50, 0, 0)] }],
    tabs: [{ kind: "dashboard", index: 0 }, ...Array.from({ length: 51 }, (_, index) => ({ kind: "worksheet", index }))] }));
  assert.equal(many.tabs.length, 50); assert.equal(many.worksheets.length, 49); assert.ok(many.issues.includes("Only the first 50 tabs were opened."));
  assert.deepEqual(many.dashboards[0].widgets, []); // its worksheet was past the cap
});
test("a bad tab order is repaired and a bad active tab reported", () => {
  const wb = parseWorkbook(v2({ worksheets: [ws("A"), ws("B")], tabs: [{ kind: "worksheet", index: 1 }, { kind: "chart", index: 0 }],
    active: { kind: "dashboard", index: 3 } }));
  assert.deepEqual(wb.worksheets.map((w) => w.name), ["B", "A"]);
  assert.ok(wb.issues.includes("The saved tab order was incomplete or invalid — the remaining tabs were added at the end."));
  assert.ok(wb.issues.includes("The saved active tab was invalid — the data model view was opened."));
  assert.equal(wb.active, null);
});
test("autosave writes the v2 key and reads the v1 key only as a fallback", () => {
  const view = { connected: true, host: "ch", port: 8443, user: "u" };
  assert.equal(autosaveKey(view), "dashboardbuilder.workbook.v2|ch|8443|u");
  assert.equal(legacyAutosaveKey(view), "dashboardbuilder.workbook.v1|ch|8443|u");
  const stored = new Map([[legacyAutosaveKey(view), "old"]]), read = (k) => stored.get(k) ?? null;
  assert.equal(savedWorkbookText(view, read), "old");
  stored.set(autosaveKey(view), "new"); assert.equal(savedWorkbookText(view, read), "new");
  assert.equal(savedWorkbookText({ connected: false }, read), null); assert.equal(legacyAutosaveKey({ connected: false }), null);
});
```
- [ ] **Step 2: Run to verify it fails** — `$NODE --test tests/js/workbook-model.test.mjs`
  Expected: FAIL — `SyntaxError: The requested module '…/workbook-model.js' does not provide an export named 'migrateV1'`.

- [ ] **Step 3: Implement `workbook-model.js`.** Add `import { normaliseLayout } from "../Board/board-layout.js";`
  to the imports; line 17 → `export const WORKBOOK_VERSION = 2;`; after line 19 add:
```js
/** A v1 workbook (every tab a worksheet, saved as "dashboards") → the v2 shape: the same worksheets in the
 *  same order, no dashboards; `active` and bookmark `dashboard` indexes carry over as worksheet indexes. */
export function migrateV1(raw) {
  const { dashboards, active, ...rest } = raw;
  const tabs = Array.isArray(dashboards) ? dashboards.flatMap((d, index) => (d && typeof d === "object" ? [{ kind: "worksheet", index }] : [])) : [];
  return { ...rest, version: 2, worksheets: dashboards, dashboards: [], tabs, active: active == null ? null : { kind: "worksheet", index: active } };
}
```
  `serializeWorkbook` (21–54): the signature takes `tabs` in place of `dashboards`; the first lines of the body are:
```js
  const sheets = tabs.filter((t) => t.kind === "worksheet"), boards = tabs.filter((t) => t.kind === "dashboard");
  const indexOf = (t) => (t.kind === "worksheet" ? sheets : boards).indexOf(t);
  const sheetIndex = (id) => sheets.findIndex((s) => s.id === id);
  const rect = (w) => ({ x: w.x, y: w.y, w: w.w, h: w.h });
  const activeTab = active && active.kind !== "model" ? tabs.find((t) => t.id === active.id) : null;
```
  Delete line 24 (`activeIndex`). Keep the entity/relationship/theme/filter/field/parameter lines (29–40, 43–46)
  as they are. Replace lines 41–42 with:
```js
    worksheets: sheets.map((s) => ({ name: s.name, sheet: savedSheet(s.sheet) })),
    dashboards: boards.map((b) => ({ name: b.name, widgets: b.widgets.flatMap((w) => (w.kind === "text"
      ? [{ kind: "text", heading: w.heading, body: w.body, ...rect(w) }]
      : sheetIndex(w.sheetId) >= 0 ? [{ kind: "sheet", sheet: sheetIndex(w.sheetId), ...rect(w) }] : [])) })),
    tabs: tabs.map((t) => ({ kind: t.kind, index: indexOf(t) })),
    active: activeTab ? { kind: activeTab.kind, index: indexOf(activeTab) } : null,
```
  and in the bookmark map (47–52) make the comment "each bookmark points at its worksheet by index" and line 49
  `const i = sheetIndex(b.dashId);`. In `parseWorkbook`, after line 72 add `if (raw.version === 1) raw = migrateV1(raw);`
  and replace lines 121–141 with:
```js
  // Worksheets and dashboards: each kind's objects, then the strip order (≤ 50 tabs), then renumber what
  // survived so every index below — tabs, active, widgets, bookmarks — points into the final lists.
  const wsK = keptItems(raw.worksheets, "worksheet", issues), dbK = keptItems(raw.dashboards, "dashboard", issues);
  let order = tabOrder(raw.tabs, wsK, dbK, issues);
  if (order.length > LIMITS.tabs) { issues.push(`Only the first ${LIMITS.tabs} tabs were opened.`); order = order.slice(0, LIMITS.tabs); }
  const wsNew = new Map(), dbNew = new Map(); // kept index → final index, in strip order
  for (const t of order) { const m = t.kind === "worksheet" ? wsNew : dbNew; m.set(t.index, m.size); }
  const sheetAt = (i) => wsNew.get(wsK.at.get(i)); // file worksheet index → final index | undefined
  const worksheets = [...wsNew.keys()].map((i) => {
    const name = tabName(wsK.items[i], "worksheet", "Worksheet", issues);
    return { name, sheet: sanitizeSheet(wsK.items[i].sheet, `Sheet "${name}"`, issues) };
  });
  const dashboards = [...dbNew.keys()].map((i) => {
    const name = tabName(dbK.items[i], "dashboard", "Dashboard", issues);
    return { name, widgets: cleanWidgets(dbK.items[i].widgets, sheetAt, `Dashboard "${name}"`, issues) };
  });
  const tabs = order.map((t) => ({ kind: t.kind, index: (t.kind === "worksheet" ? wsNew : dbNew).get(t.index) }));
  const a = raw.active, [aK, aNew] = a?.kind === "worksheet" ? [wsK, wsNew] : a?.kind === "dashboard" ? [dbK, dbNew] : [];
  const activeIndex = aK ? aNew.get(aK.at.get(a.index)) : undefined;
  if (a != null && activeIndex === undefined) issues.push("The saved active tab was invalid — the data model view was opened.");
  const active = activeIndex === undefined ? null : { kind: a.kind, index: activeIndex };
```
  Line 144 → `cleanBookmarks(raw.bookmarks, sheetAt, issues)`; line 149 → `for (const d of worksheets)`; line 151
  returns `{ entities, relationships, worksheets, dashboards, tabs, active, theme, sharedFilters, bookmarks, fields,
  parameters, issues: [...new Set(issues)] }`. After `isStr` (154) add:
```js
// One kind of tab from the file: the objects kept, and each file index → its kept index.
function keptItems(list, noun, issues) {
  if (list !== undefined && !Array.isArray(list)) issues.push(`The ${noun}s weren't a list — none were opened.`);
  const all = Array.isArray(list) ? list : [], items = [], at = new Map();
  all.forEach((d, i) => { if (d && typeof d === "object") { at.set(i, items.length); items.push(d); } });
  if (items.length < all.length) issues.push(`Skipped ${all.length - items.length} entry(ies) that were not a ${noun}.`);
  return { items, at };
}
// The strip order: valid, distinct { kind, index } entries; any tab it leaves out goes at the end.
function tabOrder(list, wsK, dbK, issues) {
  const seen = new Set(), order = [];
  let bad = list !== undefined && !Array.isArray(list);
  for (const t of Array.isArray(list) ? list : []) {
    const i = (t?.kind === "worksheet" ? wsK : t?.kind === "dashboard" ? dbK : null)?.at.get(t.index);
    if (i === undefined || seen.has(`${t.kind}:${i}`)) { bad = true; continue; }
    seen.add(`${t.kind}:${i}`); order.push({ kind: t.kind, index: i });
  }
  for (const [kind, k] of [["worksheet", wsK], ["dashboard", dbK]])
    k.items.forEach((_, i) => { if (!seen.has(`${kind}:${i}`)) { bad = true; order.push({ kind, index: i }); } });
  if (bad) issues.push("The saved tab order was incomplete or invalid — the remaining tabs were added at the end.");
  return order;
}
function tabName(d, noun, fallback, issues) {
  const r = d.name == null || typeof d.name === "string"
    ? text(d.name, { label: "Tab name", max: LIMITS.tabName, required: true }) : { ok: false, error: `The ${noun} name must be text.` };
  if (r.ok) return r.value; issues.push(`A ${noun} name was reset to "${fallback}": ${r.error}`);
  return fallback;
}
// A dashboard's widgets: a known kind, a worksheet that was opened, text within its limits, then a legal layout.
function cleanWidgets(list, sheetAt, where, issues) {
  if (list == null) return [];
  if (!Array.isArray(list)) { issues.push(`${where}: its widgets weren't a list — none were opened.`); return []; }
  const kept = [];
  for (const w of list) {
    const rect = { x: w?.x, y: w?.y, w: w?.w, h: w?.h };
    if (w?.kind === "sheet") {
      const sheet = sheetAt(w.sheet);
      if (sheet === undefined) issues.push(`${where}: skipped a worksheet widget whose worksheet is missing.`);
      else kept.push({ kind: "sheet", sheet, ...rect });
    } else if (w?.kind === "text") {
      kept.push({ kind: "text", heading: widgetText(w.heading, "heading", LIMITS.heading, where, issues),
        body: widgetText(w.body, "text", LIMITS.body, where, issues), ...rect });
    } else issues.push(`${where}: skipped a widget of an unknown kind.`);
  }
  const layout = normaliseLayout(kept);
  for (const i of layout.issues) issues.push(`${where}: ${i}`);
  return layout.widgets;
}
function widgetText(v, what, max, where, issues) {
  if (v == null) return ""; if (typeof v !== "string") { issues.push(`${where}: a text block's ${what} wasn't text — cleared.`); return ""; }
  if (v.length <= max) return v; issues.push(`${where}: a text block's ${what} was longer than ${max} characters — shortened.`);
  return v.slice(0, max);
}
```
  `cleanBookmarks(list, sheetAt, issues)`: comment line 336 says "a worksheet index (null if that worksheet
  wasn't opened)"; line 351 → `const dashboard = Number.isInteger(b.dashboard) ? sheetAt(b.dashboard) ?? null : null;`.
  Replace `storageKey` (429–433) with:
```js
/** Autosave keys for the session's server + user (null while disconnected). v2 is written; the v1 key is
 *  only read as a fallback, and left in place. */
const keyFor = (v, view) => (view?.connected ? `dashboardbuilder.workbook.v${v}|${view.host}|${view.port}|${view.user}` : null);
export const autosaveKey = (view) => keyFor(WORKBOOK_VERSION, view);
export const legacyAutosaveKey = (view) => keyFor(1, view);
export const savedWorkbookText = (view, read) => (view?.connected ? read(autosaveKey(view)) ?? read(legacyAutosaveKey(view)) : null);
```
- [ ] **Step 4: Run to verify it passes** — `$NODE --check src/DashboardBuilder/Features/Workbook/workbook-model.js &&
  $NODE --test tests/js/workbook-model.test.mjs` → Expected: PASS.

- [ ] **Step 5: Wire `workbook.js`.** Store import (1–5): `entities, relationships, tabs, bus, activeTabId, tabById,
  createWorksheet, updateSheet, createBoard, updateBoard, nextWidgetId, closeTab, showModel, switchTab,
  currentTheme, setTheme,` + the unchanged third line; line 16 imports `serializeWorkbook, parseWorkbook,
  autosaveKey, savedWorkbookText`. `CHANGE_EVENTS` lists both `"worksheet:changed"` and `"dashboard:changed"`.
  In `onConnection`: `key = autosaveKey(view);`; `const saved = savedWorkbookText(view, readStorage); // a v1 autosave is migrated and left in place`;
  the empty check is `if (!wb.entities.length && !wb.tabs.length) return;`; and
  `const restored = \`Restored your last workbook (${[count(wb.entities.length, "table"), count(wb.worksheets.length, "worksheet"), ...(wb.dashboards.length ? [count(wb.dashboards.length, "dashboard")] : [])].join(", ")}).\`;`.
  Lines 92 and 161 → `for (const t of [...tabs]) closeTab(t.id);`. Replace 177–185 of `openWorkbook` with:
```js
    // Tabs in strip order. Dashboards open empty: their widgets name worksheets by index, so they are
    // filled once every worksheet has its new id.
    const made = { worksheet: [], dashboard: [] };
    for (const t of wb.tabs) {
      if (t.kind === "worksheet") {
        const w = wb.worksheets[t.index], tab = createWorksheet(w.name);
        updateSheet(tab.id, w.sheet);
        made.worksheet[t.index] = tab;
      } else made.dashboard[t.index] = createBoard(wb.dashboards[t.index].name);
    }
    wb.dashboards.forEach((d, i) => updateBoard(made.dashboard[i].id, d.widgets.map(({ sheet, ...w }) =>
      ({ id: nextWidgetId(), ...w, ...(w.kind === "sheet" ? { sheetId: made.worksheet[sheet].id } : {}) }))));
    // P39: bookmarks point at their worksheet by index; a missing one is recreated when applied.
    setBookmarks((wb.bookmarks ?? []).map((b) => ({ ...b, dashId: b.dashboard !== null ? made.worksheet[b.dashboard]?.id ?? null : null })));
    const act = wb.active && made[wb.active.kind][wb.active.index];
    if (act) switchTab(act.id); else showModel();
```
  Line 189 toast → "…check the worksheets and dashboards."; line 219 → "Its tables, relationships, worksheets and
  dashboards will be removed."; lines 232–237:
```js
function currentState() {
  const id = activeTabId();
  return { entities, relationships, tabs, active: id ? { kind: tabById(id).kind, id } : { kind: "model" },
    theme: currentTheme(), sharedFilters, bookmarks, fieldMeta, parameters };
}
const isEmpty = () => entities.size === 0 && tabs.length === 0;
```
- [ ] **Step 6: Full suite + browser** — `$NODE --check src/DashboardBuilder/Features/Workbook/workbook.js &&
  $NODE --test tests/js/*.test.mjs && dotnet test`, then the browser harness → all green (the P22 checks reload
  a v2 autosave; Task 8 adds "a v1 autosave opens as worksheets").
- [ ] **Step 7: Commit** — `git add src/DashboardBuilder/Features/Workbook tests/js/workbook-model.test.mjs &&
  git commit` with message `Workbook format v2: dashboards, widgets, tab order; migrate v1 files and autosaves (P24b)`
  + the Co-Authored-By line.

Next: [plan-board.md](plan-board.md) — Task 7, tab kinds and the **+** menu.
