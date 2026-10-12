# P34 plan — Client C: workbook import & restore (Task 8)

Part of the [P34 plan](plan-overview.md). Paths are relative to `src/DashboardBuilder/Features/` unless they
start with `tests/`. `NODE=~/.nvm/versions/node/v24.20.0/bin/node`.

### Task 8: Validate every workbook field; report, never silently drop

**Files:** Create `Core/sheet-schema.js`. Modify `Workbook/workbook-model.js`, `Workbook/workbook.js`.
Test: `tests/js/workbook-model.test.mjs` (add cases; if an existing test `deepEqual`s a whole parse result,
add `issues: []` to its expectation).

**Interfaces:**
- Consumes: `LIMITS` (Task 5), `aggsFor` (Task 7), `listDialog`, `toast` (Task 5).
- Produces: `parseWorkbook(text) → { entities, relationships, dashboards, active, issues: string[] }` (throws only
  for hard failures); `sanitizeSheet(saved, where, issues) → sheet`; `restoreSheet(saved)` kept as
  `sanitizeSheet(saved, "Sheet", [])`.

- [ ] **Step 1: Write the failing tests** (append to `tests/js/workbook-model.test.mjs`):

```js
const wbText = (patch) => JSON.stringify({ format: WORKBOOK_FORMAT, version: 1, entities: [], relationships: [], dashboards: [], ...patch });
const sheetOf = (sheet) => parseWorkbook(wbText({ dashboards: [{ name: "S", sheet }] }));
const pill = (o = {}) => ({ db: "s", table: "orders", column: "amount", category: "numeric", ...o });

test("a missing or non-numeric version is refused with the right message", () => {
  assert.throws(() => parseWorkbook(wbText({ version: undefined })), /no valid version number/);
  assert.throws(() => parseWorkbook(wbText({ version: "1" })), /no valid version number/);
  assert.throws(() => parseWorkbook(wbText({ version: 2 })), /newer version/);
});
test("a clean workbook has no issues", () => assert.deepEqual(sheetOf({ chartType: "line" }).issues, []));
test("an unknown chart type is reset to Bar and reported", () => {
  const wb = sheetOf({ chartType: "radar" });
  assert.equal(wb.dashboards[0].sheet.chartType, "bar"); assert.match(wb.issues[0], /radar/);
});
test("out-of-range format values are reset and reported", () => {
  const wb = sheetOf({ format: { decimals: 99, topN: "abc", legend: "middle" } });
  const f = wb.dashboards[0].sheet.format;
  assert.equal(f.decimals, null); assert.equal(f.topN, null); assert.equal(f.legend, "auto");
  assert.equal(wb.issues.length, 3);
});
test("a null pill is dropped and reported; a wrong aggregation is reset", () => {
  const wb = sheetOf({ rows: [null, pill({ category: "text", agg: "sum" })] });
  assert.equal(wb.dashboards[0].sheet.rows.length, 1);
  assert.equal(wb.dashboards[0].sheet.rows[0].agg, "count");
  assert.equal(wb.issues.length, 2);
});
test("a drill without a depth is cleared and reported", () => {
  const wb = sheetOf({ drill: { levels: [pill(), pill({ column: "x" })], path: [] } });
  assert.equal(wb.dashboards[0].sheet.drill, null); assert.equal(wb.issues.length, 1);
});
test("bloated files are capped with an issue", () => {
  const wb = parseWorkbook(wbText({ dashboards: Array.from({ length: 60 }, () => ({ name: "D", sheet: { rows: Array(25).fill(pill()) } })) }));
  assert.equal(wb.dashboards.length, 50); assert.equal(wb.dashboards[0].sheet.rows.length, 20);
  assert.ok(wb.issues.some((i) => /first 50 dashboards/.test(i)));
});
test("duplicate entity ids and duplicate tables are skipped and reported", () => {
  const e = { id: "a", db: "s", table: "t", x: 0, y: 0, joinKeys: [] };
  const wb = parseWorkbook(wbText({ entities: [e, { ...e }, { ...e, id: "b" }] }));
  assert.equal(wb.entities.length, 1); assert.equal(wb.issues.length, 2);
});
```

- [ ] **Step 2: Run** `$NODE --test tests/js/workbook-model.test.mjs` — expected FAIL.
- [ ] **Step 3: Implement.** `Core/sheet-schema.js`:

```js
// Allowed values for a saved worksheet — the workbook validator checks every field against these.
// Keep CHART_TYPE_IDS in step with CHART_TYPES in Dashboard/dashboards.js.
export const CHART_TYPE_IDS = new Set(["bar", "stacked", "line", "area", "pie", "donut", "scatter", "combo",
  "square", "circle", "heatmap", "treemap", "histogram", "boxplot", "kpi", "text", "table"]);
export const CATEGORIES = new Set(["numeric", "text", "temporal", "boolean", "compound", "other"]);
export const FILTER_OPS = new Set(["=", "!=", ">", ">=", "<", "<=", "in", "between"]);
export const NUMBER_FORMATS = new Set(["auto", "compact", "currency", "percent"]);
export const DATE_FORMATS = new Set(["auto", "date", "month", "year", "datetime"]);
export const LEGENDS = new Set(["auto", "hidden", "top", "bottom", "left", "right"]);
export const TOP_N = new Set([5, 10, 20, 50, 100]);
export const MAX_DECIMALS = 10;
```

`workbook-model.js` — version check and entity rules in `parseWorkbook`:

```js
if (typeof raw.version !== "number" || !Number.isInteger(raw.version) || raw.version < 1)
  throw new Error("This workbook file has no valid version number.");
if (raw.version > WORKBOOK_VERSION) throw new Error("This workbook was saved by a newer version of Dashboard Builder.");
const issues = [];
// entities: keep the first of each id and of each db.table; report the rest
const seenIds = new Set(), seenTables = new Set(); let skipped = 0;
const entities = [];
for (const e of Array.isArray(raw.entities) ? raw.entities : []) {
  if (!(e && isStr(e.id) && isStr(e.db) && isStr(e.table))) { skipped++; continue; }
  if (seenIds.has(e.id)) { issues.push(`Skipped a table with a duplicate id (${e.id}).`); continue; }
  if (seenTables.has(`${e.db}.${e.table}`)) { issues.push(`Skipped a second copy of ${e.db}.${e.table}.`); continue; }
  seenIds.add(e.id); seenTables.add(`${e.db}.${e.table}`);
  entities.push({ id: e.id, db: e.db, table: e.table, x: num(e.x), y: num(e.y), joinKeys: Array.isArray(e.joinKeys) ? e.joinKeys.filter(isStr) : [] });
}
if (skipped) issues.push(`Skipped ${skipped} table(s) with missing details.`);
```

Relationships keep today's filter and push `Skipped N relationship(s) that referenced missing tables or had an unknown cardinality.`
when any were dropped. Dashboards — cap **before** sanitising:
`if (list.length > LIMITS.dashboards) { issues.push(\`Only the first ${LIMITS.dashboards} dashboards were opened.\`); list.length = LIMITS.dashboards; }`;
names go through `text(d.name, { label: "Tab name", max: LIMITS.tabName, required: true })` — on failure use
`"Dashboard"` and report; sheets go through `sanitizeSheet(d.sheet, \`Sheet "${name}"\`, issues)`. Return
`{ entities, relationships, dashboards, active, issues: [...new Set(issues)] }`.

```js
const defAgg = (p) => (p.category === "numeric" ? "sum" : "count");
function cleanPill(raw, where, issues) {
  if (!raw || typeof raw !== "object" || !isStr(raw.db) || !isStr(raw.table) || !isStr(raw.column) || !CATEGORIES.has(raw.category)) {
    issues.push(`${where}: skipped a field with missing details.`); return null;
  }
  const p = { ...raw };
  if (p.role !== undefined && p.role !== "dimension" && p.role !== "measure") delete p.role;
  if (p.agg !== undefined && !aggsFor(p.category).includes(p.agg)) {
    issues.push(`${where}: ${p.table}.${p.column} can't use "${p.agg}" — reset to ${defAgg(p)}.`); p.agg = defAgg(p);
  }
  return p;
}
function cleanPills(list, where, issues, max = LIMITS.pillsPerShelf) {
  if (list == null) return [];
  if (!Array.isArray(list)) { issues.push(`${where}: not a list — cleared.`); return []; }
  const out = list.map((p) => cleanPill(p, where, issues)).filter(Boolean);
  if (out.length > max) { issues.push(`${where}: only the first ${max} fields were kept.`); out.length = max; }
  return out;
}
const oneOf = (set, v, fallback, where, what, issues) => {
  if (v === undefined || set.has(v)) return v ?? fallback;
  issues.push(`${where}: unknown ${what} "${v}" — reset.`); return fallback;
};
export function sanitizeSheet(saved, where, issues) {
  const base = emptySheet();
  const s = saved && typeof saved === "object" ? saved : {};
  const sheet = { ...base };
  sheet.chartType = s.chartType === undefined ? base.chartType : CHART_TYPE_IDS.has(s.chartType) ? s.chartType
    : (issues.push(`${where}: unknown chart type "${s.chartType}" — reset to Bar.`), "bar");
  for (const k of ["columns", "rows", "color"]) sheet[k] = cleanPills(s[k], `${where} ${k}`, issues);
  sheet.filters = cleanPills(s.filters, `${where} filters`, issues, LIMITS.filters).filter((f) => {
    const okShape = FILTER_OPS.has(f.op) && (f.op === "in" || f.op === "between"
      ? Array.isArray(f.values) && f.values.every((v) => typeof v === "string") : typeof (f.value ?? "") === "string");
    if (!okShape) issues.push(`${where}: skipped a filter on ${f.table}.${f.column} with an unknown operator or value.`);
    return okShape;
  });
  const m = s.marks && typeof s.marks === "object" ? s.marks : {};
  sheet.marks = { ...base.marks };
  for (const k of ["size", "label", "shape", "path", "angle"]) sheet.marks[k] = m[k] == null ? null : cleanPill(m[k], `${where} ${k}`, issues);
  for (const k of ["detail", "tooltip"]) sheet.marks[k] = cleanPills(m[k], `${where} ${k}`, issues);
  sheet.sort = s.sort == null ? null : isStr(s.sort.by) && (s.sort.dir === "asc" || s.sort.dir === "desc") ? { by: s.sort.by, dir: s.sort.dir }
    : (issues.push(`${where}: sort cleared.`), null);
  sheet.selection = null; // transient click selection — never restored
  sheet.drill = cleanDrill(s.drill, where, issues);
  sheet.pages = s.pages == null ? null : cleanPill(s.pages, `${where} pages`, issues) && Number.isInteger(s.pages.index) && s.pages.index >= 0
    ? { db: s.pages.db, table: s.pages.table, column: s.pages.column, category: s.pages.category, index: s.pages.index }
    : (issues.push(`${where}: pages cleared.`), null);
  sheet.format = cleanFormat(s.format, where, issues);
  return sheet;
}
function cleanDrill(d, where, issues) {
  if (d == null) return null;
  const levels = Array.isArray(d.levels) ? d.levels.map((p) => cleanPill(p, `${where} drill`, issues)).filter(Boolean) : [];
  const okDepth = Number.isInteger(d.depth) && d.depth >= 0 && d.depth < levels.length;
  const okPath = okDepth && Array.isArray(d.path) && d.path.length === d.depth && d.path.every((x) => x && isStr(x.column));
  if (levels.length < 2 || !okPath) { issues.push(`${where}: drill cleared.`); return null; }
  return { levels, depth: d.depth, path: d.path.map((x) => ({ column: x.column, value: x.value ?? null, label: String(x.label ?? "") })) };
}
function cleanFormat(f0, where, issues) {
  const base = defaultFormat();
  const f = f0 && typeof f0 === "object" ? f0 : {};
  const w = `${where} format`;
  const out = { ...base };
  out.numberFormat = oneOf(NUMBER_FORMATS, f.numberFormat, base.numberFormat, w, "number format", issues);
  out.dateFormat = oneOf(DATE_FORMATS, f.dateFormat, base.dateFormat, w, "date format", issues);
  out.legend = oneOf(LEGENDS, f.legend, base.legend, w, "legend position", issues);
  out.decimals = f.decimals == null ? null : Number.isInteger(f.decimals) && f.decimals >= 0 && f.decimals <= MAX_DECIMALS ? f.decimals
    : (issues.push(`${w}: decimals "${f.decimals}" — reset to Auto.`), null);
  out.topN = f.topN == null ? null : TOP_N.has(f.topN) ? f.topN : (issues.push(`${w}: Top N "${f.topN}" — reset to All.`), null);
  for (const k of ["dataLabels", "colorByDimension"]) out[k] = f[k] === undefined ? base[k] : Boolean(f[k]);
  out.currencySymbol = typeof f.currencySymbol === "string" && f.currencySymbol.length <= 8 ? f.currencySymbol : base.currencySymbol;
  for (const k of ["xTitle", "yTitle"]) {
    const r = f[k] == null ? null : text(f[k], { label: "Axis title", max: LIMITS.axisTitle });
    out[k] = r === null ? null : r.ok ? r.value || null : (issues.push(`${w}: ${r.error} — cleared.`), null);
  }
  return out;
}
```

Imports at the top of `workbook-model.js`: `emptySheet, defaultFormat` from `../Core/store.js`; `LIMITS, text` from
`../Core/validate.js`; `aggsFor` from `../Dashboard/filter-rules.js`; the sets from `../Core/sheet-schema.js`.

**`workbook.js`:**
- Import: after `openWorkbook(wb)`, `if (wb.issues.length) await listDialog(\`Opened ${file.name} with ${wb.issues.length} issue(s)\`, wb.issues.slice(0, 20).concat(wb.issues.length > 20 ? [\`…and ${wb.issues.length - 20} more.\`] : [])); else toast(\`Opened ${file.name}.\`, "ok");`
- Restore: replace the silent `catch {}` so a bad entry is kept, not overwritten:

```js
} catch (err) {
  try { localStorage.setItem(`${key}:backup-${new Date().toISOString()}`, raw); } catch { /* storage full or blocked */ }
  toast(`Couldn't restore your saved workbook (${err.message}). A backup copy was kept in this browser.`, "danger");
}
```

  and when a restored workbook has issues, `toast(\`Restored your last workbook — ${wb.issues.length} part(s) were reset.\`, "info")`.
- Wrap the body of `openWorkbook` in `try { … } catch (err) { console.error(err); toast("Part of the workbook couldn't be opened — check the dashboards.", "danger"); } finally { restoring = false; }`.

- [ ] **Step 4: Run** `$NODE --test tests/js/*.test.mjs`, `$NODE --check` on both changed modules — expected PASS.
- [ ] **Step 5: Checkpoint.**
