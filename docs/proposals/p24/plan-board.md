# P24 plan — Task 7: tab kinds and the **+** menu

Part of the [P24 plan](plan-overview.md); read its Global Constraints and Shared interfaces first. Paths are
relative to the app root. Spec: [§ Tabs](../p24-dashboards.md#tabs). Task 8 (the Board canvas) is in
[plan-board-2.md](plan-board-2.md) and [plan-board-3.md](plan-board-3.md); Task 9 (full screen, print, theme,
bookmarks) is in [plan-present.md](plan-present.md).

## Browser checks — how Tasks 7–9 use the harness

The harness is Task 1's ([plan-runtime-a.md](plan-runtime-a.md)): `$PW tests/browser/run.mjs [check …]` gives each
`tests/browser/checks/*.mjs` a fresh browser, light then dark, and calls `run(ctx)` with
`ctx = { page, errors, queries, scheme, baseUrl, shots }` (`queries`: every `/api/query` body; `errors`: page
errors, reported as a FAIL). A check returns `[{ name, ok, detail? }]`; one that throws is reported as a FAIL
with the error. The P24b checks use `node:assert/strict` (the failing assertion's message is the FAIL detail)
and return one passing result at the end. Everything they need beyond `ctx` lives in
`tests/browser/board-helpers.mjs` (below): `start` (= `openWorksheet`), `failQuery` (a later `page.route`
answering 502 for matching bodies, falling back to the mock otherwise), `reload`, `forgetErrors` (Task 8 adds those three).

### Task 7: two tab kinds in one strip, the **+** menu, the in-use confirm

**Files:**
- Modify: `src/DashboardBuilder/Features/Core/icons.js` (add `dashboard`), `tests/js/icons.test.mjs`
- Modify (replace): `src/DashboardBuilder/Features/Tabs/tabs.js`; modify `Tabs/tabs.css`
- Modify: `src/DashboardBuilder/Features/Dashboard/dashboards.js` — the `isModelActive()` guards
- Modify: `tests/browser/mock.mjs` (`openWorksheet`); create `tests/js/tab-names.test.mjs`,
  `tests/browser/board-helpers.mjs`, `tests/browser/checks/tab-kinds.mjs`

**Interfaces:**
- Consumes (Task 5 store): `tabs`, `isModelActive`, `activeTabId`, `activeWorksheet`, `showModel`,
  `createWorksheet(name)`, `createBoard(name)` (both switch to the new tab), `switchTab`, `renameTab`,
  `closeTab`, `worksheetHasContent`, `boardsUsing(sheetId)` → `[{ id, name }]`, `updateBoard`, `nextWidgetId`;
  `LIMITS.tabs` (50); `wireMenu` (Core/menu.js).
- Produces: `export function nextTabName(list, kind)` in `tabs.js`; DOM — `.tab--worksheet` / `.tab--dashboard`,
  `.tab__label[data-tab-id]` with `aria-label="<name> (<kind>)"`, `.tab__kind` icon, `.tab-add`
  (`aria-haspopup="menu"`), `[role=menuitem][data-new="worksheet" | "dashboard"]`, close button
  `aria-label="Close <kind> <name>"`; helpers `tests/browser/board-helpers.mjs` (used by Tasks 8–9).

- [ ] **Step 1: `openWorksheet` goes through the menu.** In `tests/browser/mock.mjs` `openWorksheet`, replace
  `await page.click(".tab-add");` with `await page.click(".tab-add"); await page.click('[role="menuitem"][data-new="worksheet"]');`
  (every check, P22's included, starts there; red until Step 5).

- [ ] **Step 2: Failing unit tests.** Append `"dashboard"` to `REQUIRED` in `tests/js/icons.test.mjs`. Create
  `tests/js/tab-names.test.mjs`:

```js
import { test } from "node:test";
import assert from "node:assert/strict";
import { nextTabName } from "../../src/DashboardBuilder/Features/Tabs/tabs.js";
const t = (kind, name) => ({ kind, name });
test("numbers each kind on its own, stepping past names already taken", () => {
  assert.equal(nextTabName([], "worksheet"), "Worksheet 1");
  assert.equal(nextTabName([t("worksheet", "Worksheet 1")], "dashboard"), "Dashboard 1");
  assert.equal(nextTabName([t("worksheet", "Worksheet 1"), t("dashboard", "Dashboard 1")], "worksheet"), "Worksheet 2");
  assert.equal(nextTabName([t("worksheet", "Worksheet 2")], "worksheet"), "Worksheet 3"); // after a close
  assert.equal(nextTabName([t("worksheet", "Sales"), t("dashboard", "Worksheet 2")], "worksheet"), "Worksheet 3");
});
```

  Run `node --test tests/js/icons.test.mjs tests/js/tab-names.test.mjs` — expect FAIL: `dashboard` missing;
  `nextTabName` is not exported.

- [ ] **Step 3: Failing browser check.** Create `tests/browser/board-helpers.mjs` (the one place that knows `ctx`):

```js
// Shared steps for the P24b checks (tab-kinds, board-*, board-present).
import { openWorksheet } from "./mock.mjs";
export const start = (ctx) => openWorksheet(ctx.page);   // app open, orders on the canvas, a blank worksheet
export const pass = (name) => [{ name, ok: true }];       // the assertions above it threw on any failure
export const DRAWN = ".ws-chart-canvas :is(svg, canvas)"; // ECharts draws small charts as SVG, big ones on canvas
export const storeUrl = () => new URL("../Core/store.js", document.querySelector('script[type="module"]').src).href;
export async function newTab(ctx, kind) { await ctx.page.click(".tab-add"); await ctx.page.click(`[role="menuitem"][data-new="${kind}"]`); }
export const activeName = (ctx) => ctx.page.$eval(".tab.is-active .tab__label", (e) => e.textContent.trim());
/** A new worksheet with `dim` on Columns and `measure` on Rows, drawn; returns its tab name. */
export async function sheet(ctx, dim, measure) {
  await newTab(ctx, "worksheet");
  await ctx.page.click(`.ws-field__add[aria-label="Add ${dim} to Columns"]`);
  await ctx.page.click(`.ws-field__add[aria-label="Add ${measure} to Rows"]`);
  await ctx.page.waitForSelector(`#ws-chart ${DRAWN}`);
  return activeName(ctx);
}
```

  Create `tests/browser/checks/tab-kinds.mjs`:

```js
import assert from "node:assert/strict";
import { start, pass, newTab, activeName, sheet, storeUrl } from "../board-helpers.mjs";
export async function run(ctx) {
  await start(ctx);
  const p = ctx.page, url = await p.evaluate(storeUrl);
  assert.equal(await p.getAttribute(".tab-add", "aria-haspopup"), "menu");
  await p.click(".tab-add");
  assert.deepEqual(await p.$$eval('[role="menuitem"][data-new]', (els) => els.map((e) => e.textContent.trim())), ["New worksheet", "New dashboard"]);
  await p.keyboard.press("Escape");
  const ws = await sheet(ctx, "region", "sales"); assert.match(ws, /^Worksheet \d+$/);
  assert.equal(await p.getAttribute(".tab.is-active .tab__label", "aria-label"), `${ws} (worksheet)`);
  await newTab(ctx, "dashboard"); const db = await activeName(ctx); assert.match(db, /^Dashboard \d+$/);
  assert.ok(await p.$(".tab--dashboard.is-active .tab__kind"), "dashboard tab shows its kind icon");
  assert.equal(await p.getAttribute(".tab.is-active .tab__label", "aria-label"), `${db} (dashboard)`);
  // Closing a worksheet that sits on a dashboard names the dashboard; Cancel keeps both.
  await p.evaluate(async ({ url, ws }) => {
    const s = await import(url), sh = s.tabs.find((t) => t.name === ws);
    s.updateBoard(s.activeBoard().id, [{ id: s.nextWidgetId(), kind: "sheet", sheetId: sh.id, x: 0, y: 0, w: 6, h: 4 }]);
  }, { url, ws });
  await p.click(`.tab__close[aria-label="Close worksheet ${ws}"]`);
  assert.match(await p.textContent("dialog .dialog__body"), new RegExp(`Used on: ${db}`));
  await p.click("dialog .btn:text-is('Cancel')");
  assert.ok(await p.$(`.tab__label:text-is("${ws}")`));
  // LIMITS.tabs is enforced at creation, with a toast.
  await p.evaluate(async (u) => { const s = await import(u); while (s.tabs.length < 50) s.createWorksheet("Filler"); }, url);
  await newTab(ctx, "worksheet");
  assert.match(await p.textContent("#toast"), /at most 50/);
  assert.equal(await p.$$eval(".tab:not(.tab--model)", (els) => els.length), 50);
  return pass("kinds, + menu, default names, in-use confirm, tab limit");
}
```

  Run `$PW tests/browser/run.mjs` (dev run up on `:5180`). Expect `tab-kinds` and `show-me` FAIL (threw:
  `openWorksheet` waits for a menu item the **+** doesn't open yet); `two-charts` PASS.

- [ ] **Step 4: The icon.** In `Core/icons.js` `PATHS`, after `"show-me"`:

```js
  dashboard: "M3 3.5h6v7H3zM11 3.5h6v4h-6zM11 9.5h6v7h-6zM3 12.5h6v4H3z",
```

- [ ] **Step 5: Replace `Tabs/tabs.js`.** Imports, the kind table and `nextTabName` at the top; `modelTab()`
  stays exactly as today; the rest below replaces `dashboardTab`, `addButton`, `requestClose`, `beginRename`:

```js
import {
  tabs, isModelActive, activeTabId, showModel, createWorksheet, createBoard,
  switchTab, renameTab, closeTab, worksheetHasContent, boardsUsing, bus,
} from "../Core/store.js";
import { icon } from "../Core/icons.js";
import { confirmDialog, toast } from "../Core/ui.js";
import { wireMenu } from "../Core/menu.js";
import { text, LIMITS } from "../Core/validate.js";

// The view strip: a pinned "Data Model" tab, then worksheet and dashboard tabs in one ordered list —
// each with its kind's icon and its kind in the accessible name — and a [+] menu adding either kind.
// Tabs rename on double-click / F2 and close with a confirm when they hold something; closing a worksheet
// names the dashboards it sits on (its widgets there go with it). The model tab is never closable.
const KIND = {
  worksheet: { icon: "chart-bar", label: "worksheet", base: "Worksheet", create: createWorksheet },
  dashboard: { icon: "dashboard", label: "dashboard", base: "Dashboard", create: createBoard },
};

/** "Worksheet N" / "Dashboard N": N is one past that kind's count, stepped past any name already taken. */
export function nextTabName(list, kind) {
  const names = new Set(list.map((t) => t.name));
  let n = list.filter((t) => t.kind === kind).length + 1;
  while (names.has(`${KIND[kind].base} ${n}`)) n += 1;
  return `${KIND[kind].base} ${n}`;
}

export function initTabs() {
  const strip = document.getElementById("tabs");
  if (!strip) return;
  let menuAbort = null; // the + menu is rebuilt with the strip; drop the old one's document listeners

  bus.addEventListener("tabs:changed", render);
  // Delegated on the strip, which outlives render(): the first click switches and rebuilds the tabs.
  strip.addEventListener("dblclick", (event) => {
    const label = event.target.closest?.(".tab__label[data-tab-id]");
    const tab = label && tabs.find((t) => t.id === label.dataset.tabId);
    if (tab) beginRename(tab, label);
  });
  render();

  function render() {
    menuAbort?.abort(); menuAbort = new AbortController();
    strip.replaceChildren(modelTab(), ...tabs.map(tabEl), addMenu());
  }

  // function modelTab() { … unchanged … }
  function button(cls) { const b = document.createElement("button"); b.type = "button"; b.className = cls; return b; }

  function tabEl(tab) {
    const k = KIND[tab.kind], active = activeTabId() === tab.id;
    const el = document.createElement("div");
    el.className = `tab tab--${tab.kind}${active ? " is-active" : ""}`;
    el.setAttribute("role", "tab"); el.setAttribute("aria-selected", String(active));
    if (active) el.setAttribute("aria-current", "true");

    const label = button("tab__label");
    label.dataset.tabId = tab.id;
    label.setAttribute("aria-label", `${tab.name} (${k.label})`);
    label.title = `${k.base} — click to switch, double-click to rename`;
    const glyph = icon(k.icon, { size: 14 }); glyph.classList.add("tab__kind");
    const name = document.createElement("span"); name.className = "tab__name"; name.textContent = tab.name;
    label.append(glyph, name);
    label.addEventListener("click", () => { if (activeTabId() !== tab.id) switchTab(tab.id); });

    const close = button("tab__close");
    close.setAttribute("aria-label", `Close ${k.label} ${tab.name}`);
    close.append(icon("close", { size: 14 }));
    close.addEventListener("click", (event) => { event.stopPropagation(); requestClose(tab); });

    el.addEventListener("keydown", (event) => {
      if (event.target !== label) return;
      if (event.key === "F2" || (event.key === "Enter" && active)) { event.preventDefault(); beginRename(tab, label); }
    });
    el.append(label, close);
    return el;
  }

  function addMenu() {
    const wrap = document.createElement("div");
    wrap.className = "menu tab-new";
    const add = button("tab-add");
    add.setAttribute("aria-label", "New worksheet or dashboard"); add.title = "New worksheet or dashboard";
    add.append(icon("plus"));
    const list = document.createElement("div");
    list.className = "menu__list menu__list--start"; list.setAttribute("role", "menu"); list.hidden = true;
    for (const kind of ["worksheet", "dashboard"]) {
      const item = button("menu__item");
      item.setAttribute("role", "menuitem"); item.dataset.new = kind;
      item.append(icon(KIND[kind].icon), document.createTextNode(`New ${KIND[kind].label}`));
      item.addEventListener("click", () => newTab(kind));
      list.append(item);
    }
    wireMenu(add, list, { signal: menuAbort.signal });
    wrap.append(add, list);
    return wrap;
  }

  function newTab(kind) {
    if (tabs.length >= LIMITS.tabs) { toast(`A workbook holds at most ${LIMITS.tabs} worksheets and dashboards — close one first.`, "info"); return; }
    KIND[kind].create(nextTabName(tabs, kind));
  }

  async function requestClose(tab) {
    const used = tab.kind === "worksheet" ? boardsUsing(tab.id) : [];
    const filled = tab.kind === "worksheet" ? worksheetHasContent(tab.id) : tab.widgets.length > 0;
    if (filled || used.length) {
      const usedLine = used.length ? ` Used on: ${used.map((b) => b.name).join(", ")} — its widgets there are removed too.` : "";
      const ok = await confirmDialog(`Close the ${KIND[tab.kind].label} “${tab.name}”?${usedLine}`, { danger: true, confirmText: "Close" });
      if (!ok) return;
    }
    closeTab(tab.id); // a dashboard's close never touches its worksheets (store)
  }

  function beginRename(tab, labelEl) {
    const input = document.createElement("input");
    input.className = "tab__rename"; input.value = tab.name; input.maxLength = LIMITS.tabName;
    input.setAttribute("aria-label", `Rename ${KIND[tab.kind].label}`);
    labelEl.replaceWith(input); input.focus(); input.select();
    let done = false;
    const refocusLabel = () => strip.querySelector(`.tab__label[data-tab-id="${CSS.escape(tab.id)}"]`)?.focus();
    const commit = (refocus) => {
      if (done) return;
      done = true;
      const r = text(input.value, { label: "Tab name", max: LIMITS.tabName, required: true });
      if (!r.ok) toast(r.error, "danger"); // keep the old name
      else renameTab(tab.id, r.value);
      render();
      if (refocus) refocusLabel();
    };
    input.addEventListener("blur", (event) => commit(!event.relatedTarget));
    input.addEventListener("keydown", (event) => {
      if (event.key === "Enter") { event.preventDefault(); input.blur(); }
      else if (event.key === "Escape") { done = true; render(); refocusLabel(); }
    });
  }
}
```

- [ ] **Step 6: Styles** — `Tabs/tabs.css`, after `.tab__label`:

```css
/* P24b: kind icon + name inside the label; the name ellipsises, the icon never shrinks. */
.tab__label { display: inline-flex; align-items: center; gap: var(--s1); }
.tab__name { min-width: 0; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.tab__kind { flex: none; color: var(--ink-3); }
.tab.is-active .tab__kind { color: var(--accent-ink); }
.tab-new { display: inline-flex; }
```

- [ ] **Step 7: The worksheet editor stays off dashboard tabs.** Every `isModelActive()` guard in
  `Dashboard/dashboards.js` means "not on a worksheet" now (14 at P22; `grep -n isModelActive`, and the same
  in `worksheet-view.js` if Task 3 moved a listener there). Add beside the store import
  `const onSheet = () => activeWorksheet() !== null; // P24b: false on the model and on dashboard tabs`, then
  `sed -i 's/!isModelActive()/onSheet()/g; s/isModelActive()/!onSheet()/g'` on the file and drop
  `isModelActive` from its import. `sync()` then reads `toggle(view, onSheet()); if (!onSheet()) { … }`.

- [ ] **Step 8: GREEN.** `node --check` on `tabs.js`, `icons.js`, `dashboards.js`; the JS suite (all pass,
  incl. `tab-names` and `icons`); `dotnet test`; the browser harness in light and dark — `tab-kinds` PASS and
  every earlier check still PASS. Grep the diff for `style.display` and hex colours — none.

- [ ] **Step 9: Commit.**

```bash
git add -A && git commit -m "Add worksheet and dashboard tab kinds with the + menu (P24b)

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"
```

Next: [Task 8 — the Board canvas](plan-board-2.md).
