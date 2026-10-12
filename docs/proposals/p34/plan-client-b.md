# P34 plan — Client B: data-model inputs, worksheet rules (Tasks 6–7)

Part of the [P34 plan](plan-overview.md). Paths are relative to `src/DashboardBuilder/Features/` unless they
start with `tests/`. `NODE=~/.nvm/versions/node/v24.20.0/bin/node`.

### Task 6: Data-model inputs and tab names

**Files:** Create `Relations/relation-rules.js`, test `tests/js/relation-rules.test.mjs`. Modify `Relations/relations.js`
(`onConnectorClick`), `Canvas/canvas.js` (drop + `table:add`), `Tabs/tabs.js` (`beginRename`, tab keydown).

**Interfaces:**
- Consumes: `text`, `LIMITS` (`Core/validate.js`); `toast` (`Core/ui.js`).
- Produces: `keysCompatible(catA, catB) → boolean`; `findDuplicate(relationships: Iterable, from, to) → rel | null`;
  `linkProblem({ relationships, from, to, fromCategory, toCategory, fromLabel, toLabel }) → string | null`.

- [ ] **Step 1: Write the failing test** — `tests/js/relation-rules.test.mjs`:

```js
import { test } from "node:test";
import assert from "node:assert/strict";
import { keysCompatible, findDuplicate, linkProblem } from "../../src/DashboardBuilder/Features/Relations/relation-rules.js";
const a = { entityId: "e1", column: "customer_id" }, b = { entityId: "e2", column: "id" };
const base = { relationships: [], from: a, to: b, fromCategory: "numeric", toCategory: "numeric", fromLabel: "orders.customer_id", toLabel: "customers.id" };
test("same-kind keys relate", () => assert.equal(linkProblem(base), null));
test("a key can't relate to its own table", () => assert.match(linkProblem({ ...base, to: { entityId: "e1", column: "x" } }), /different table/));
test("a duplicate link is blocked in either direction", () => {
  const rel = { from: b, to: a, cardinality: "1:N" };
  assert.equal(findDuplicate([rel], a, b), rel);
  assert.match(linkProblem({ ...base, relationships: [rel] }), /already related/);
});
test("number-to-text keys are blocked, naming both", () => {
  const msg = linkProblem({ ...base, toCategory: "text" });
  assert.match(msg, /orders\.customer_id \(numeric\)/); assert.match(msg, /customers\.id \(text\)/);
});
test("compound and other keys never relate", () => {
  assert.equal(keysCompatible("compound", "compound"), false);
  assert.equal(keysCompatible("other", "other"), false);
  assert.equal(keysCompatible("temporal", "temporal"), true);
});
```

- [ ] **Step 2: Run** `$NODE --test tests/js/relation-rules.test.mjs` — expected FAIL (module missing).
- [ ] **Step 3: Implement** `Relations/relation-rules.js`:

```js
// Pure rules for drawing a relationship (no DOM). Unit-tested in tests/js/relation-rules.test.mjs.
const KIND = { numeric: "number", text: "text", temporal: "date", boolean: "boolean" };
export const keysCompatible = (a, b) => Boolean(KIND[a]) && KIND[a] === KIND[b];
const sameEnd = (p, q) => p.entityId === q.entityId && p.column === q.column;
export function findDuplicate(relationships, from, to) {
  for (const r of relationships)
    if ((sameEnd(r.from, from) && sameEnd(r.to, to)) || (sameEnd(r.from, to) && sameEnd(r.to, from))) return r;
  return null;
}
export function linkProblem({ relationships, from, to, fromCategory, toCategory, fromLabel, toLabel }) {
  if (from.entityId === to.entityId) return "Pick a key on a different table.";
  if (findDuplicate(relationships, from, to)) return `${fromLabel} and ${toLabel} are already related.`;
  if (!keysCompatible(fromCategory, toCategory))
    return `Can't relate ${fromLabel} (${fromCategory}) to ${toLabel} (${toCategory}) — join keys must hold the same kind of value.`;
  return null;
}
```

Wire it. In `relations.js` `onConnectorClick`, replace the same-entity check with:

```js
const end = (id, col) => { const e = entities.get(id); return { cat: e?.columns.find((c) => c.name === col)?.category, label: `${e?.table}.${col}` }; };
const p = end(pending.entityId, pending.column), q = end(entityId, column);
const problem = linkProblem({ relationships: relationships.values(), from: { entityId: pending.entityId, column: pending.column },
  to: { entityId, column }, fromCategory: p.cat, toCategory: q.cat, fromLabel: p.label, toLabel: q.label });
if (problem) { clearPending(); toast(problem, "danger"); return; }
```

In `canvas.js`, route both the drop handler and the `table:add` listener through one guard (workbook open
keeps calling `createEntity` directly):

```js
function addTableFromUser(db, table, x, y) {
  if (typeof db !== "string" || !db || typeof table !== "string" || !table) return; // malformed drag payload
  const existing = [...entities.values()].find((e) => e.db === db && e.table === table);
  if (existing) {
    existing.el.scrollIntoView({ block: "nearest", inline: "nearest" });
    existing.el.classList.add("is-flash");
    setTimeout(() => existing.el.classList.remove("is-flash"), 1200);
    toast(`${db}.${table} is already on the canvas.`, "info");
    return;
  }
  createEntity(db, table, x, y);
}
```

In `tabs.js` `beginRename`: `input.maxLength = LIMITS.tabName;` and on commit
`const r = text(input.value, { label: "Tab name", max: LIMITS.tabName, required: true }); if (!r.ok) { toast(r.error, "danger"); /* revert to dash.name */ } else /* rename to r.value */`.
Add a `keydown` on each tab element: `if (e.key === "F2" || (e.key === "Enter" && isActive)) { e.preventDefault(); beginRename(dash, label); }`.

- [ ] **Step 4: Run** `$NODE --test tests/js/*.test.mjs` + `$NODE --check` on the three changed files — expected PASS.
- [ ] **Step 5: Checkpoint.**

### Task 7: Worksheet rules — aggregations, typed filters, honest notices

**Files:** Create `Dashboard/filter-rules.js`, tests `tests/js/filter-rules.test.mjs`, `tests/js/format.test.mjs`.
Modify `Dashboard/dashboards.js`, `Core/format.js`.

**Interfaces:**
- Consumes: `filterValue`, `range`, `LIMITS` (Task 5); `fieldError` (Task 5); server `object?` values (Task 3).
- Produces: `AGGS`, `aggsFor(category) → string[]`; `checkFilter(f) → { state: "empty" | "ok" } | { state: "invalid", error }`;
  `statFilters(filters, db, table) → { apply: StatFilter[], ignored: number }`; `TEXT_VALUE_TYPES: Set`.

- [ ] **Step 1: Write the failing tests** — `tests/js/filter-rules.test.mjs`:

```js
import { test } from "node:test";
import assert from "node:assert/strict";
import { aggsFor, checkFilter, statFilters } from "../../src/DashboardBuilder/Features/Dashboard/filter-rules.js";
const F = (o) => ({ db: "s", table: "orders", column: "amount", category: "numeric", op: "=", value: "", values: null, ...o });
test("aggregations match the column category", () => {
  assert.ok(aggsFor("numeric").includes("sum"));
  assert.deepEqual(aggsFor("temporal"), ["count", "countDistinct", "min", "max"]);
  assert.deepEqual(aggsFor("boolean"), ["count", "countDistinct"]);
});
test("an untouched filter is empty, not an error", () => {
  assert.equal(checkFilter(F({})).state, "empty");
  assert.equal(checkFilter(F({ value: "   " })).state, "empty");
  assert.equal(checkFilter(F({ op: "between", values: ["", ""] })).state, "empty");
});
test("a non-number on a numeric column is invalid and says so", () => {
  const r = checkFilter(F({ value: "1,000" }));
  assert.equal(r.state, "invalid"); assert.match(r.error, /not a number for column orders\.amount/);
});
test("a half range or inverted range is invalid", () => {
  assert.match(checkFilter(F({ op: "between", values: ["5", ""] })).error, /both From and To/);
  assert.match(checkFilter(F({ op: "between", values: ["9", "1"] })).error, /From must be less than or equal to To/);
});
test("a valid date filter is ok", () => assert.equal(checkFilter(F({ category: "temporal", value: "2024-01-31" })).state, "ok"));
test("stat charts apply same-table ok filters and count the rest", () => {
  const r = statFilters([F({ value: "5" }), F({ table: "customers", value: "1" }), F({ value: "x" }), F({ op: "in", values: ["1", "2"] })], "s", "orders");
  assert.deepEqual(r.apply, [{ column: "amount", op: "=", value: "5", values: null }, { column: "amount", op: "in", value: "", values: ["1", "2"] }]);
  assert.equal(r.ignored, 1);
});
```

`tests/js/format.test.mjs`:

```js
import { test } from "node:test";
import assert from "node:assert/strict";
import { makeValueFormatter } from "../../src/DashboardBuilder/Features/Core/format.js";
test("text measure values (min/max of a date or text field) show as-is", () => {
  const f = makeValueFormatter({});
  assert.equal(f("2024-01-02"), "2024-01-02"); assert.equal(f(null), "—"); assert.equal(f(1234.5), (1234.5).toLocaleString(undefined, { maximumFractionDigits: 2 }));
});
```

- [ ] **Step 2: Run** `$NODE --test tests/js/*.test.mjs` — expected FAIL.
- [ ] **Step 3: Implement** `Dashboard/filter-rules.js`:

```js
// Pure worksheet rules (no DOM): aggregations per field, filter usability, stat-chart filter mapping.
import { filterValue, range, LIMITS } from "../Core/validate.js";
export const AGGS = Object.freeze({
  numeric: ["sum", "avg", "min", "max", "count", "countDistinct"],
  ordered: ["count", "countDistinct", "min", "max"], // text + temporal: min/max come back as text
  other: ["count", "countDistinct"],                  // boolean, compound, other
});
export const aggsFor = (category) =>
  category === "numeric" ? AGGS.numeric : category === "text" || category === "temporal" ? AGGS.ordered : AGGS.other;
// Chart types that can show a text measure value (min/max of a text or date field).
export const TEXT_VALUE_TYPES = new Set(["table", "text", "kpi"]);
const blank = (v) => v == null || !String(v).trim();
export function checkFilter(f) {
  const col = `${f.table}.${f.column}`;
  if (f.op === "in") {
    const vals = Array.isArray(f.values) ? f.values : [];
    if (!vals.length) return { state: "empty" };
    return vals.length > LIMITS.inValues
      ? { state: "invalid", error: `An 'in' filter can list at most ${LIMITS.inValues} values.` } : { state: "ok" };
  }
  if (f.op === "between") {
    const [lo, hi] = Array.isArray(f.values) ? f.values : [];
    if (blank(lo) && blank(hi)) return { state: "empty" };
    if (blank(lo) || blank(hi)) return { state: "invalid", error: `Enter both From and To for ${col}.` };
    const r = range(f.category, lo, hi, col);
    return r.ok ? { state: "ok" } : { state: "invalid", error: r.error };
  }
  if (blank(f.value)) return { state: "empty" };
  const r = filterValue(f.category, f.value, col);
  return r.ok ? { state: "ok" } : { state: "invalid", error: r.error };
}
export function statFilters(filters, db, table) {
  const usable = filters.filter((f) => checkFilter(f).state === "ok");
  const mine = usable.filter((f) => f.db === db && f.table === table);
  return {
    apply: mine.map((f) => ({ column: f.column, op: f.op, value: f.value ?? "", values: f.values ?? null })),
    ignored: usable.length - mine.length,
  };
}
```

`Core/format.js` `makeValueFormatter`: change `if (Number.isNaN(v)) return "—";` to
`if (Number.isNaN(v)) return typeof n === "string" && n ? n : "—";`.

**`dashboards.js` wiring** (import from `./filter-rules.js` and `../Core/validate.js` / `../Core/ui.js`):
1. Delete `AGGS_NUMERIC`, `AGGS_TEXT`, local `aggsFor`, `isActiveFilter`; every `aggsFor(f)` → `aggsFor(f.category)`;
   every `isActiveFilter(f)` → `checkFilter(f).state === "ok"`.
2. `filterPill`: after `cfg.append(op, filterValueControl(dash, s, f))`, add
   `const chk = checkFilter(f); if (chk.state === "invalid") { const inp = cfg.querySelector("input"); if (inp) fieldError(inp, chk.error); }`
   and on the returned pill `p.classList.toggle("ws-pill--invalid", chk.state === "invalid")`.
3. `filterValueControl`: each text input gets `maxLength = LIMITS.filterValue` and a placeholder by category —
   `numeric: "number"` (+ `inputMode = "decimal"`), `temporal: "YYYY-MM-DD"`, `boolean: "true or false"`, else `"value"`.
4. `addFilter`: `if (s.filters.length >= LIMITS.filters) { toast(\`A view can have at most ${LIMITS.filters} filters.\`, "info"); return; }`.
5. When rendering, if any filter is invalid, `setNotice` adds: `"N filter(s) not applied — fix the highlighted value."`
   (joined with other notices by `" · "`).
6. `populateDistinct`: wrap the select in a `span`; when `vals.length >= 200` append
   `el("p", "ws-note", "Showing the first 200 values — more exist.")`. In the pages members loader, show
   `Couldn't load members: ${err.message}` and the same 200-cap note.
7. `runStatChart`: replace the `filters` computation with `const { apply: filters, ignored } = statFilters(s.filters, db, table);`
   and after rendering add the notice `${ignored} filter(s) on other tables don't apply to a ${histogram|box plot}.` when `ignored > 0`.
8. Format panel: label the Top-N select `s.chartType === "histogram" ? "Bins" : "Top N"`; `fmtText` inputs get `maxLength = LIMITS.axisTitle`.
9. In the function that calls `chartIssue(` (~line 1235), before rendering a chart:
   `if (!TEXT_VALUE_TYPES.has(type) && result.rows.some((r) => r.values.some((v) => typeof v === "string"))) { chartEl.replaceChildren(hint("Min/Max of a text or date field shows as Table, Text or KPI — switch the chart type, or use Count.")); return; }`
10. Never a blank view: wrap the rendering part of `runChart` (after the result arrives) in
   `try { … } catch (err) { console.error(err); chartEl.replaceChildren(warn("This view couldn't be drawn — try another chart type or remove a field.")); }`.

- [ ] **Step 4: Run** `$NODE --test tests/js/*.test.mjs`, `$NODE --check Dashboard/dashboards.js` — expected PASS.
- [ ] **Step 5: Checkpoint.**
