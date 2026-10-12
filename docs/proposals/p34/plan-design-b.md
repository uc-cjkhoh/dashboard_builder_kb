# P34 plan — Design B: icons, sidebar & connection (Tasks 10–11)

Part of the [P34 plan](plan-overview.md). Paths are relative to `src/DashboardBuilder/Features/` unless they
start with `tests/`. `NODE=~/.nvm/versions/node/v24.20.0/bin/node`.

### Task 10: Icon set

**Files:** Create `Core/icons.js`, test `tests/js/icons.test.mjs`. Modify `Shell/app.js` (hydrate
`[data-icon]`), `Core/ui.js` (status-pill + field-error glyphs), every `.cshtml`/`.js` that renders a Unicode
glyph icon (find them: `grep -rn "[◑◉⋯∠⤳▽⤵▦⤒⤓✎○●◐✕⚠ⓘ◇◎▾✓＋]" --include=*.js --include=*.cshtml .`).

**Interfaces:**
- Produces: `icon(name, { size = 16, label } = {}) → SVGElement` (class `icon`, `aria-hidden` unless `label`);
  `PATHS` (name → path `d`); `ICON_NAMES`. Static markup uses `<span data-icon="name"></span>`, hydrated once by `app.js`.

- [ ] **Step 1: Write the failing test** — `tests/js/icons.test.mjs`:

```js
import { test } from "node:test";
import assert from "node:assert/strict";
import { PATHS } from "../../src/DashboardBuilder/Features/Core/icons.js";
const REQUIRED = ["connection", "database", "table", "key", "link", "filter", "color", "size", "label", "tooltip", "detail",
  "shape", "path", "angle", "drill", "pages", "sort", "format", "export", "import", "more", "search", "close", "chevron",
  "check", "warning", "error", "info", "refresh", "edit", "power", "plus", "dot",
  "type-number", "type-text", "type-date", "type-bool", "type-other"];
test("every icon the UI needs exists", () => { for (const n of REQUIRED) assert.ok(PATHS[n], n); });
test("paths are plain SVG path data", () => { for (const [n, d] of Object.entries(PATHS)) assert.match(d, /^[MmLlHhVvCcSsQqTtAaZz0-9.,\s-]+$/, n); });
```

- [ ] **Step 2: Run** `$NODE --test tests/js/icons.test.mjs` — expected FAIL (module missing).
- [ ] **Step 3: Implement `Core/icons.js`:**

```js
// Self-hosted inline-SVG icons: 20px grid, 1.5px round stroke, currentColor. No icon font, no CDN.
export const PATHS = Object.freeze({
  connection: "M6 8V4M14 8V4M4 8h12v3a6 6 0 0 1-12 0zM10 17v-2",
  database: "M4 5c0-1.1 2.7-2 6-2s6 .9 6 2-2.7 2-6 2-6-.9-6-2zM4 5v10c0 1.1 2.7 2 6 2s6-.9 6-2V5M4 10c0 1.1 2.7 2 6 2s6-.9 6-2",
  table: "M3 4h14v12H3zM3 8h14M8 8v8",
  key: "M12.5 3.5a4 4 0 1 1-3.2 6.4L3.5 15.7V17H6v-1.5h1.5V14l1.8-1.8M13.5 6.5h.01",
  link: "M8.5 11.5l3-3M7 9.5L5.5 11a2.5 2.5 0 0 0 3.5 3.5l1.5-1.5M13 10.5l1.5-1.5A2.5 2.5 0 0 0 11 5.5L9.5 7",
  filter: "M3 4h14l-5.5 6.5V16l-3-1.5v-4z",
  color: "M10 3s5 5.2 5 8.5a5 5 0 0 1-10 0C5 8.2 10 3 10 3z",
  size: "M4 10a6 6 0 1 0 12 0 6 6 0 1 0-12 0M7.5 10a2.5 2.5 0 1 0 5 0 2.5 2.5 0 1 0-5 0",
  label: "M4.5 16L9.5 4h1l5 12M6.3 12h7.4",
  tooltip: "M4 4h12v9H9l-3 3v-3H4z",
  detail: "M4 6h12M4 10h12M4 14h8",
  shape: "M3 8a2.5 2.5 0 1 0 5 0 2.5 2.5 0 1 0-5 0M12 5.5h5v5h-5zM7.5 17l3-5 3 5z",
  path: "M3 15c3 0 3-10 7-10s4 10 7 10",
  angle: "M4 16h12M4 16l9-10M8.5 16a4.5 4.5 0 0 0-1.4-3.3",
  drill: "M5 4v6a3 3 0 0 0 3 3h7M12 10l3 3-3 3",
  pages: "M6 3h8v14H6zM3 5v10M17 5v10",
  sort: "M6 4v12M3 13l3 3 3-3M14 16V4M11 7l3-3 3 3",
  format: "M4 6h8M15 6h1M4 14h2M9 14h7M12 4v4M7 12v4",
  export: "M10 3v9M6 8.5l4 4 4-4M4 15v2h12v-2",
  import: "M10 13V4M6 7.5l4-4 4 4M4 15v2h12v-2",
  more: "M5 10h.01M10 10h.01M15 10h.01",
  search: "M9 4a5 5 0 1 0 0 10 5 5 0 0 0 0-10zM16 16l-3.5-3.5",
  close: "M5 5l10 10M15 5L5 15",
  chevron: "M7 8l3 3 3-3",
  check: "M4 10.5l4 4 8-9",
  warning: "M10 3l8 14H2zM10 8v4M10 14.5h.01",
  error: "M10 3a7 7 0 1 0 0 14 7 7 0 0 0 0-14zM7.5 7.5l5 5M12.5 7.5l-5 5",
  info: "M10 3a7 7 0 1 0 0 14 7 7 0 0 0 0-14zM10 9v5M10 6.5h.01",
  refresh: "M16 10a6 6 0 1 1-1.8-4.3M16 4v3.5h-3.5",
  edit: "M4 16l1-4 8-8 3 3-8 8zM11.5 5.5l3 3",
  power: "M10 3v6M6.2 5.4a5.2 5.2 0 1 0 7.6 0",
  plus: "M10 4v12M4 10h12",
  dot: "M10 6.5a3.5 3.5 0 1 0 0 7 3.5 3.5 0 0 0 0-7z",
  "type-number": "M7.5 4L6 16M14 4l-1.5 12M4 8h13M3.5 12h13",
  "type-text": "M5 5h10M10 5v11",
  "type-date": "M4 5h12v11H4zM4 8.5h12M7 3v3M13 3v3",
  "type-bool": "M3 10a4 4 0 0 1 4-4h6a4 4 0 0 1 0 8H7a4 4 0 0 1-4-4zM13 10h.01",
  "type-other": "M5 10h10",
});
export const ICON_NAMES = Object.freeze(Object.keys(PATHS));
const NS = "http://www.w3.org/2000/svg";
export function icon(name, { size = 16, label } = {}) {
  const d = PATHS[name];
  if (!d) throw new Error(`Unknown icon: ${name}`);
  const svg = document.createElementNS(NS, "svg");
  for (const [k, v] of Object.entries({ viewBox: "0 0 20 20", width: size, height: size, fill: "none", stroke: "currentColor",
    "stroke-width": "1.5", "stroke-linecap": "round", "stroke-linejoin": "round" })) svg.setAttribute(k, String(v));
  svg.classList.add("icon");
  if (label) { svg.setAttribute("role", "img"); svg.setAttribute("aria-label", label); } else svg.setAttribute("aria-hidden", "true");
  const p = document.createElementNS(NS, "path");
  p.setAttribute("d", d);
  svg.append(p);
  return svg;
}
```

  `Shell/app.js` (after the global handlers): `for (const el of document.querySelectorAll("[data-icon]")) el.replaceChildren(icon(el.dataset.icon));`.
  `Core/ui.js`: the status pill uses `icon()` — `idle: "dot"`, `connecting: "refresh"` (keeps the spin class),
  `connected: "check"`, `failed: "error"`; `fieldError` uses `icon("warning", { size: 14 })` instead of `⚠`; the toast
  close button uses `icon("close", { size: 14 })`. Replace every glyph found by the grep with `icon(name)` in JS
  or `<span data-icon="name"></span>` in markup (`✎` → `edit`, `▾` → `chevron`, `✕`/`×` → `close`, `＋`/`+` → `plus`,
  `ⓘ` → `info`). `Dashboard/dashboards.js` `iconButton(glyph, label)`: use `icon(glyph)` when `PATHS[glyph]` exists,
  else the text (keeps the conventional `#` / `Σ` role toggles). Add to `core.css`: `.icon { flex: none; display: block; }`.

- [ ] **Step 4: Run** the JS suite + `$NODE --check` on changed modules — PASS. Re-run the glyph grep — no output.
- [ ] **Step 5: Checkpoint.**

### Task 11: Glass sidebar, Advanced connection options, table search

**Files:** Modify `Shell/Index.cshtml`, `Shell/shell.css`, `Connection/_Connection.cshtml`, `Connection/connection.js`,
`Connection/connection.css`, `Schema/_Schema.cshtml`, `Schema/schema.js`, `Schema/schema.css`. Create
`Schema/table-filter.js`, test `tests/js/table-filter.test.mjs`.

**Interfaces:** Produces `matchTables(names: string[], query: string) → string[]` (`Schema/table-filter.js`) and
`advancedShouldOpen({ secure, allowInvalidCert }) → boolean` (`Connection/connection-rules.js`, created here).

- [ ] **Step 1: Write the failing tests** — `tests/js/table-filter.test.mjs`:

```js
import { test } from "node:test";
import assert from "node:assert/strict";
import { matchTables } from "../../src/DashboardBuilder/Features/Schema/table-filter.js";
import { advancedShouldOpen } from "../../src/DashboardBuilder/Features/Connection/connection-rules.js";
test("search is case-insensitive and trimmed; blank shows all", () => {
  const t = ["orders", "Order_items", "customers"];
  assert.deepEqual(matchTables(t, "  ORDER "), ["orders", "Order_items"]);
  assert.deepEqual(matchTables(t, "   "), t);
  assert.deepEqual(matchTables(t, "zzz"), []);
});
test("Advanced opens when TLS is off or the certificate opt-in is on", () => {
  assert.equal(advancedShouldOpen({ secure: true, allowInvalidCert: false }), false);
  assert.equal(advancedShouldOpen({ secure: false, allowInvalidCert: false }), true);
  assert.equal(advancedShouldOpen({ secure: true, allowInvalidCert: true }), true);
});
```

- [ ] **Step 2: Run** — expected FAIL (modules missing).
- [ ] **Step 3: Implement.**

```js
// Schema/table-filter.js — pure table search (no DOM).
export function matchTables(names, query) {
  const q = String(query ?? "").trim().toLowerCase();
  return q ? names.filter((n) => n.toLowerCase().includes(q)) : names;
}
```

```js
// Connection/connection-rules.js — pure (no DOM).
export const advancedShouldOpen = ({ secure, allowInvalidCert }) => !secure || Boolean(allowInvalidCert);
```

  **Shell.** `Index.cshtml`: `<aside class="sidebar glass">`, `<div class="canvas__bar glass">`. `shell.css`:
  `.sidebar { background: var(--glass); color: var(--ink); border-right: 1px solid var(--glass-line); box-shadow: none; }`
  (drop the old dark gradient/edge glow); `.sidebar__mark { background: var(--accent); color: var(--on-accent); border-radius: var(--r); }`;
  `.sidebar__title { text-transform: none; letter-spacing: 0; font-size: var(--fs-sm); font-weight: 600; color: var(--ink-2); }`;
  `.sidebar__section { padding: var(--s4) var(--s5); border-bottom: 1px solid var(--glass-line); }`;
  `.canvas__bar { border-width: 0 0 1px; border-radius: 0; }`; `.view--model, .view--dashboard { background: transparent; }`
  (the body wash shows through); keep the resizer, its active state uses `var(--accent)`.

  **Connection.** In `_Connection.cshtml`, wrap the two TLS checkboxes and the warning in
  `<details class="conn-advanced" id="conn-advanced"><summary>Advanced</summary> … </details>`. In
  `connection.js`, set `advancedEl.open = advancedShouldOpen({ secure: secureEl.checked, allowInvalidCert: allowCertEl.checked })`
  whenever the form is shown. `connection.css`: `.conn-form { display: grid; gap: var(--s3); }`,
  `.conn-advanced > summary { cursor: pointer; color: var(--ink-2); font-size: var(--fs-sm); }`,
  `.conn-summary { padding: var(--s3); border: 1px solid var(--line); border-radius: var(--r); background: var(--surface); }`.

  **Table search.** `_Schema.cshtml`, top of `#tables-section`:

```html
<label class="table-search">
    <span data-icon="search" aria-hidden="true"></span>
    <input type="search" class="input" id="table-search" placeholder="Search tables" aria-label="Search tables"
           maxlength="100" autocomplete="off" spellcheck="false" />
</label>
<p class="table-list__empty" id="table-empty" hidden>No tables match.</p>
```

  `schema.js`: keep the loaded table names; on `input`, `const shown = new Set(matchTables(names, searchEl.value))`
  then toggle each chip's `hidden` by `shown.has(chip.dataset.table)` (set `data-table` when rendering a chip) and
  `toggle(emptyEl, names.length > 0 && shown.size === 0)`. `keydown` `Escape` clears the box and re-filters.
  Clear the box whenever the database changes. `schema.css`: `.table-search { position: relative; display: block; margin-bottom: var(--s2); }`,
  `.table-search .icon { position: absolute; left: var(--s2); top: 50%; transform: translateY(-50%); color: var(--ink-3); }`,
  `.table-search .input { width: 100%; padding-left: calc(var(--s2) + 20px); }`, `.table-list__empty { color: var(--ink-3); font-size: var(--fs-sm); padding: var(--s2) 0; }`;
  table chips: `background: var(--surface); border: 1px solid var(--line); border-radius: var(--r-ctl);` hover `var(--surface-3)`.

- [ ] **Step 4: Run** the JS suite and `$NODE --check` on changed modules — PASS. jsdom check (development.md § Test):
  load the page with a fake API listing 3 tables; type "ord" → 2 chips visible; type "zzz" → "No tables match." visible.
- [ ] **Step 5: Checkpoint.** Next: [Task 12](plan-design-c.md#task-12-tabs-workbook-menu-worksheet-header-cards).
