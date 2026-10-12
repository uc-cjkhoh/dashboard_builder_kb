# P34 plan — Design C: tabs, worksheet header, cards; docs & deploy (Tasks 12–13)

Part of the [P34 plan](plan-overview.md). Paths are relative to `src/DashboardBuilder/Features/` unless they
start with `tests/`. `NODE=~/.nvm/versions/node/v24.20.0/bin/node`.

### Task 12: Tabs, workbook menu, worksheet header, cards

**Files:** Create `Core/menu.js`, `Dashboard/toolbar-rules.js`, test `tests/js/toolbar-rules.test.mjs`. Modify
`Tabs/tabs.js`, `Tabs/tabs.css`, `Workbook/_Workbook.cshtml`, `Workbook/workbook.js`, `Workbook/workbook.css`,
`Dashboard/dashboards.js`, `Dashboard/dashboard.css`, `Canvas/canvas.js`, `Canvas/canvas.css`, `Relations/relations.css`.

**Interfaces:**
- Consumes: `icon` (Task 10); tokens (Task 9); `checkFilter` (Task 7).
- Produces: `visibleTools(chartType, tools: { key, count }[]) → { visible, more }` (input order kept);
  `wireMenu(button, list, { signal } = {}) → { close() }`.

- [ ] **Step 1: Write the failing test** — `tests/js/toolbar-rules.test.mjs`:

```js
import { test } from "node:test";
import assert from "node:assert/strict";
import { visibleTools } from "../../src/DashboardBuilder/Features/Dashboard/toolbar-rules.js";
const KEYS = ["color", "size", "label", "detail", "tooltip", "shape", "path", "angle", "filters", "drill", "pages"];
const tools = (counts = {}) => KEYS.map((key) => ({ key, count: counts[key] ?? 0 }));
const keys = (list) => list.map((t) => t.key);
test("a bar chart shows the four everyday tools", () => {
  const r = visibleTools("bar", tools());
  assert.deepEqual(keys(r.visible), ["color", "label", "tooltip", "filters"]);
  assert.deepEqual(keys(r.more), ["size", "detail", "shape", "path", "angle", "drill", "pages"]);
});
test("chart-specific tools surface for their chart types", () => {
  assert.ok(keys(visibleTools("scatter", tools()).visible).includes("size"));
  assert.ok(keys(visibleTools("square", tools()).visible).includes("shape"));
  assert.ok(keys(visibleTools("area", tools()).visible).includes("path"));
  assert.ok(keys(visibleTools("donut", tools()).visible).includes("angle"));
});
test("a tool in use is never hidden behind More", () => {
  const r = visibleTools("bar", tools({ detail: 1, pages: 1 }));
  assert.ok(keys(r.visible).includes("detail")); assert.ok(keys(r.visible).includes("pages"));
});
```

- [ ] **Step 2: Run** — expected FAIL (module missing).
- [ ] **Step 3: Implement.**

```js
// Dashboard/toolbar-rules.js — which encoding tools sit in the visible row vs. the More menu (pure).
const ALWAYS = new Set(["filters", "color", "label", "tooltip"]);
const POINTS = new Set(["scatter", "square", "circle"]);
const WHEN = { size: POINTS, shape: POINTS, path: new Set(["line", "area"]), angle: new Set(["pie", "donut"]) };
export function visibleTools(chartType, tools) {
  const visible = [], more = [];
  for (const t of tools) (t.count > 0 || ALWAYS.has(t.key) || WHEN[t.key]?.has(chartType) ? visible : more).push(t);
  return { visible, more };
}
```

```js
// Core/menu.js — a button toggling a [role=menu] list. Esc, outside click and item click close it;
// ArrowUp/ArrowDown move focus. Visibility via `hidden` only. Pass an AbortSignal for menus that are re-rendered.
export function wireMenu(button, list, { signal } = {}) {
  const items = () => [...list.querySelectorAll('[role="menuitem"]')];
  const setOpen = (open) => {
    list.hidden = !open; button.setAttribute("aria-expanded", String(open));
    if (open) items()[0]?.focus();
  };
  button.setAttribute("aria-haspopup", "menu"); button.setAttribute("aria-expanded", "false");
  button.addEventListener("click", (e) => { e.stopPropagation(); setOpen(list.hidden); }, { signal });
  list.addEventListener("click", (e) => { if (e.target.closest('[role="menuitem"]')) setOpen(false); }, { signal });
  list.addEventListener("keydown", (e) => {
    const all = items(), i = all.indexOf(document.activeElement);
    if (e.key === "ArrowDown") { e.preventDefault(); all[(i + 1) % all.length]?.focus(); }
    else if (e.key === "ArrowUp") { e.preventDefault(); all[(i - 1 + all.length) % all.length]?.focus(); }
    else if (e.key === "Escape") { setOpen(false); button.focus(); }
  }, { signal });
  document.addEventListener("click", (e) => { if (!list.hidden && !list.contains(e.target)) setOpen(false); }, { signal });
  return { close: () => setOpen(false) };
}
```

  **Tabs.** `tabs.css`: `.tab { background: transparent; border: 0; border-radius: var(--r-ctl) var(--r-ctl) 0 0; color: var(--ink-2); height: var(--ctl-h); padding: 0 var(--s3); }`,
  `.tab:hover { background: var(--surface-3); color: var(--ink); }`, `.tab[aria-selected="true"] { color: var(--ink); font-weight: 600; box-shadow: inset 0 -2px 0 var(--accent); }`.
  Close and add buttons use `icon("close", { size: 14 })` / `icon("plus")` (Task 10).

  **Workbook menu.** `_Workbook.cshtml` replaces the two buttons with:

```html
<span class="workbook__status" id="wb-status" role="status" aria-live="polite" title="Saved in this browser" hidden></span>
<div class="menu">
    <button type="button" class="iconbtn" id="wb-menu-btn" aria-controls="wb-menu-list" aria-label="Workbook" title="Workbook"><span data-icon="more"></span></button>
    <div class="menu__list glass" id="wb-menu-list" role="menu" hidden>
        <button type="button" class="menu__item" role="menuitem" id="wb-import"><span data-icon="import"></span>Import workbook…</button>
        <button type="button" class="menu__item" role="menuitem" id="wb-export"><span data-icon="export"></span>Export workbook</button>
    </div>
</div>
<input type="file" id="wb-file" accept="application/json,.json" hidden />
```

  `workbook.js`: `wireMenu(document.getElementById("wb-menu-btn"), document.getElementById("wb-menu-list"))`; the
  saved status text becomes `"Saved"` (`--ink-3`, `--fs-xs`); the storage failure keeps its sentence with class
  `workbook__status--warn` (`--warn-ink` + `icon("warning")`). Menu CSS (in `core.css`, shared):
  `.menu { position: relative; } .menu__list { position: absolute; right: 0; top: calc(100% + var(--s1)); z-index: 50; min-width: 200px; padding: var(--s1); border-radius: var(--r); box-shadow: var(--elev-8); display: grid; }`
  `.menu__item { display: flex; align-items: center; gap: var(--s2); height: var(--ctl-h); padding: 0 var(--s3); border: 0; border-radius: var(--r-ctl); background: transparent; color: var(--ink); text-align: left; cursor: pointer; }`
  `.menu__item:hover, .menu__item:focus-visible { background: var(--surface-3); }`.

  **Worksheet header** (`dashboards.js` `renderShelves`):
  1. `buildTools` `icon:` values become icon names: color→`color`, size→`size`, label→`label`, detail→`detail`,
     tooltip→`tooltip`, shape→`shape`, path→`path`, angle→`angle`, filters→`filter`, drill→`drill`, pages→`pages`;
     `toolButton` renders `icon(tool.icon)` + `el("span", "ws-tool__text", tool.label)` + the count badge.
  2. Replace the toolbar loop (drop the "Marks" label and the separators):

```js
let headerAbort = null; // module scope: menus wired during the previous render
// in renderShelves:
headerAbort?.abort(); headerAbort = new AbortController();
const { visible, more } = visibleTools(s.chartType, tools);
const toolbar = el("div", "ws-toolbar");
for (const t of visible) toolbar.append(toolButton(dash, s, t));
if (more.length) {
  const wrap = el("div", "menu ws-more");
  const btn = el("button", "ws-tool"); btn.type = "button";
  btn.append(icon("more"), el("span", "ws-tool__text", "More"));
  const list = el("div", "menu__list glass"); list.setAttribute("role", "menu"); list.hidden = true;
  for (const t of more) {
    const item = el("button", "menu__item"); item.type = "button"; item.setAttribute("role", "menuitem");
    item.append(icon(t.icon), document.createTextNode(t.label));
    item.addEventListener("click", () => { openTool = t.key; renderShelves(); });
    list.append(item);
  }
  wrap.append(btn, list); toolbar.append(wrap);
  wireMenu(btn, list, { signal: headerAbort.signal });
}
```

  3. View bar: Format → `iconButton("format", "Format")`, refresh → `iconButton("refresh", "Refresh")`, export →
     `iconButton("export", "Export")` (keep its existing menu/handler), sort direction → `iconButton("sort", …)`.
     Keep the Chart select labelled.
  4. Invalid filter pills (Task 7) prepend `icon("warning", { size: 14 })`.
  5. Field pane: each table group becomes `<details class="ws-fieldset" open>` with `<summary>` = table name;
     "Dimensions"/"Measures" stay as small labels; each chip starts with an `icon()` by category —
     numeric→`type-number`, text→`type-text`, temporal→`type-date`, boolean→`type-bool`, else `type-other`; `＋` → `icon("plus")`.

  **`dashboard.css`:** `.ws-shelves { background: var(--glass); border-bottom: 1px solid var(--glass-line); backdrop-filter: blur(24px) saturate(160%); padding: var(--s3) var(--s5); display: grid; gap: var(--s2); }`;
  `.ws-tool { display: inline-flex; align-items: center; gap: var(--s1); height: var(--ctl-h); padding: 0 var(--s2); border: 0; border-radius: var(--r-ctl); background: transparent; color: var(--ink-2); font-size: var(--fs-sm); cursor: pointer; }`
  `.ws-tool:hover, .ws-tool.is-active { background: var(--surface-3); color: var(--ink); }`; `.ws-tool.is-set { color: var(--accent-ink); }`;
  count badge `background: var(--accent); color: var(--on-accent); border-radius: var(--r-pill); min-width: 16px; font-size: 11px;`;
  pills `.ws-pill--dimension` → `--dim-*`, `.ws-pill--measure` → `--meas-*`, marks/colour pills → `--enc-*`,
  `.ws-pill--invalid { border-style: dashed; border-color: var(--danger-line); color: var(--danger-ink); }`; `.ws-chart` and the crosstab sit on
  `var(--surface)` with `border: 1px solid var(--line); border-radius: var(--r); box-shadow: var(--elev-2); margin: var(--s4) var(--s5);`.

  **Entity cards** (`canvas.js` `renderCard`, `canvas.css`): title becomes `<span class="entity__db">db.</span><span class="entity__table">table</span>`;
  `▾`/`✕` are already icons (Task 10); a key column's row gets `icon("key", { size: 14 })` before its name.
  `.entity { background: var(--surface); border: 1px solid var(--line); border-radius: var(--r); box-shadow: var(--elev-2); }`,
  `.entity:hover { box-shadow: var(--elev-8); }`, `.entity.is-dragging { box-shadow: var(--elev-16); }`,
  `.entity__head { background: transparent; border-bottom: 1px solid var(--line); }`, `.entity__db { color: var(--ink-3); font-weight: 400; }`,
  `.entity__table { font-weight: 600; }`, `.entity.is-flash { outline: 2px solid var(--accent); outline-offset: 2px; }`.
  `relations.css`: resting links `var(--ink-3)`, selected/drawing `var(--accent)`; cardinality glyphs unchanged (shape-coded).

  **Empty states — one sentence + one button.** `_Canvas.cshtml`: replace the title + sub-line with one
  `<p class="empty__title" id="canvas-empty-title">` and one `<button type="button" class="btn btn--primary" id="canvas-empty-action">`.
  `canvas.js` `refreshEmpty` sets them by state — disconnected: "Connect to a ClickHouse server to begin." / **Connect**
  (focuses `#conn-host`); connected, no tables: "Drag a table here from the sidebar to start your data model." / **Find a table**
  (focuses `#table-search`). `.canvas__empty { display: grid; place-items: center; gap: var(--s3); color: var(--ink-2); text-align: center; }`.

- [ ] **Step 4: Run** the JS suite + `$NODE --check` on every changed module — PASS. jsdom check: a bar sheet renders 4 tools + More;
  switching to scatter shows Size and Shape; dropping a Detail field keeps Detail visible on bar; More opens/closes with click and Esc.
- [ ] **Step 5: Checkpoint.**

### Task 13: Review, docs, deploy

- [ ] **Step 1: Full verification.** `dotnet build -c Release && dotnet test` and `$NODE --test tests/js/*.test.mjs` — all
  PASS; re-run the Task 4 smoke script; `grep -rn "#[0-9a-fA-F]\{3,6\}\b" src/DashboardBuilder/Features --include=*.css | grep -v core.css` → empty.
- [ ] **Step 2: Whole-change review** with superpowers:requesting-code-review against the spec; fix findings; re-run Step 1.
- [ ] **Step 3: User visual review.** Run on `ASPNETCORE_URLS=http://0.0.0.0:5180`; ask the user to check light **and** dark
  (OS setting) at `http://10.168.49.20:5180/` — connect, drag tables, relate, build bar/scatter/pie, open More, import a bad
  workbook. Apply their feedback before continuing.
- [ ] **Step 4: Docs (KB repo), same change.** Update to the new current state: `DESIGN.md`; `docs/design/tokens.md`,
  `layout.md`, `components.md`, `motion-accessibility.md`; `docs/features/connection.md`, `schema-browser.md`, `canvas.md`,
  `relationships.md`, `tabs.md`, `worksheet.md`, `worksheet-encodings.md`, `worksheet-charts.md`, `workbook.md`;
  `docs/reference/api.md` (error contract, limits, removed endpoints, `values` may be string/null),
  `clickhouse-integration.md` (typed filters), `data-model.md`, `frontend-modules.md` (new modules); `decisions.md` (add D22, D23;
  D7 marked superseded by D22); `golden-rules.md` rule 7 and its `CLAUDE.md` summary line → "red means danger, nothing else";
  `sharp-edges.md` (drop the `--brand-soft` note; add "measure values can be a string or null"). Delete
  `docs/proposals/p34-fluent-glass-redesign.md` and `docs/proposals/p34/`; remove their row from `docs/README.md`. Run
  `python3 .claude/hooks/kb-verify.py --all` → "KB clean." Commit the KB.
- [ ] **Step 5: Deploy — ask the user first** (live service, every session reconnects). Then follow
  [deployment.md § Release flow](../../operations/deployment.md#release-flow): publish, **stop** the service, copy, **start**,
  `curl -sk -o /dev/null -w '%{http_code}' https://10.168.49.20:8443/dashboardbuilder/` → `200`.
