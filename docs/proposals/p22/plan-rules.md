# P22 plan — Task 1: the rule table and validity

Part of the [P22 plan](plan-overview.md); read its Global Constraints first. Paths are relative to the
app root. Spec: [§ Validity](../p22-show-me.md#validity).

### Task 1: `show-me-rules.js` — rule table, hints, `issueFor`; `dashboards.js` uses it

**Files:**
- Create: `src/DashboardBuilder/Features/Dashboard/show-me-rules.js`
- Create: `tests/js/show-me-rules.test.mjs`
- Modify: `src/DashboardBuilder/Features/Dashboard/dashboards.js` — l.61 (`roleOf`), l.167 / l.172
  (`STAT_SINGLE_TABLE`, `COLOR_SPLIT_TYPES`), l.2239, l.2422, l.2440 (hint strings), l.2726–2787
  (`chartIssue`)

**Interfaces:**
- Consumes: `TEXT_VALUE_TYPES` from `./filter-rules.js` (pure, already exported).
- Produces (later tasks rely on these exact names):
  - `roleOf(field) → "dimension" | "measure"`
  - `COLOR_SPLIT_TYPES`, `STAT_SINGLE_TABLE` — `Set<string>`
  - `TEXT_VALUE_HINT`, `COLOR_SPLIT_HINT` — `string`; `statFieldHint(type) → string`
  - `CHART_NEEDS` — frozen `{ [type]: Array<{ kind: "dims"|"measures", min, max, text }> }`
  - `chartIssue(type, dimCount, measureCount) → string | null`
  - `issueFor(type, counts) → string | null`, where `counts = { dims, shelfDims, measures, hasDate,
    textValue, discreteColor, numericField }`

- [ ] **Step 1: Branch.** `git checkout -b p22-show-me`

- [ ] **Step 2: Write the failing test** — `tests/js/show-me-rules.test.mjs`. `legacyChartIssue` is a
  verbatim copy of today's `switch` (`dashboards.js` l.2729–2786) so the move is proven lossless; before
  saving, diff it against the source (the comments inside the switch may be dropped, the strings not).

```js
import { test } from "node:test";
import assert from "node:assert/strict";
import { CHART_NEEDS, chartIssue, issueFor, roleOf, TEXT_VALUE_HINT, COLOR_SPLIT_HINT, statFieldHint }
  from "../../src/DashboardBuilder/Features/Dashboard/show-me-rules.js";
import { CHART_TYPES } from "../../src/DashboardBuilder/Features/Dashboard/viewbar-model.js";

// Verbatim copy of the pre-P22 dashboards.js chartIssue() — the regression oracle.
function legacyChartIssue(type, dimCount, measureCount) {
  switch (type) {
    case "pie":
    case "donut":
      if (measureCount !== 1) return "Pie/Donut shows one measure — put exactly one measure on a shelf.";
      if (dimCount < 1) return "Pie/Donut needs a dimension to slice by — add a dimension.";
      return null;
    case "scatter":
    case "square":
    case "circle":
      if (measureCount < 2) return "A point chart plots two measures (X and Y) — add a second measure.";
      return null;
    case "combo":
      if (measureCount < 2) return "Combo (dual-axis) needs two measures — add a second measure.";
      if (dimCount < 1) return "Combo needs a dimension for the category axis — add a dimension.";
      return null;
    case "stacked":
      if (measureCount < 2) return "Stacked bar stacks two or more measures — add another measure.";
      if (dimCount < 1) return "Stacked bar needs a dimension for the category axis — add a dimension.";
      return null;
    case "heatmap":
      if (dimCount !== 2) return "Heatmap needs exactly two dimensions (the axes) — put one on Columns and one on Rows.";
      if (measureCount < 1) return "Heatmap colours by one measure — add a measure.";
      return null;
    case "treemap":
      if (dimCount < 1 || dimCount > 2) return "Treemap nests by one or two dimensions — add one or two.";
      if (measureCount < 1) return "Treemap sizes by one measure — add a measure.";
      return null;
    case "waterfall":
      if (measureCount !== 1) return "Waterfall shows one measure as a run of changes — use exactly one measure.";
      if (dimCount < 1) return "Waterfall needs a dimension for its steps (e.g. month or category) — add one.";
      return null;
    case "funnel":
      if (measureCount !== 1) return "Funnel sizes its stages by one measure — use exactly one measure.";
      if (dimCount !== 1) return "Funnel needs exactly one dimension for its stages.";
      return null;
    case "gauge":
      if (measureCount !== 1) return "Gauge shows one measure — use exactly one measure.";
      if (dimCount !== 0) return "Gauge shows a single value — remove the dimensions (or use Bullet to compare categories).";
      return null;
    case "bullet":
      if (measureCount !== 1) return "Bullet compares one measure with a target — use exactly one measure.";
      if (dimCount > 1) return "Bullet takes at most one dimension (one bar per member).";
      return null;
    case "sankey":
      if (dimCount !== 2) return "Sankey draws flows between two dimensions — put one on Columns and one on Rows.";
      if (measureCount !== 1) return "Sankey sizes each flow by one measure — use exactly one measure.";
      return null;
    case "multiples":
      if (dimCount !== 2) return "Small multiples needs two dimensions: the first makes a panel per member, the second runs along each panel.";
      if (measureCount < 1) return "Small multiples plots a measure — add one.";
      return null;
    default:
      return null;
  }
}
const counts = (o = {}) => ({ dims: 0, shelfDims: 0, measures: 0, hasDate: false, textValue: false,
  discreteColor: false, numericField: false, ...o });

test("chartIssue matches the pre-P22 switch for every type, 0–3 dims × 0–3 measures", () => {
  for (const [type] of CHART_TYPES)
    for (let d = 0; d <= 3; d++)
      for (let m = 0; m <= 3; m++)
        assert.equal(chartIssue(type, d, m), legacyChartIssue(type, d, m), `${type} d=${d} m=${m}`);
});
test("types without needs accept any mapping", () => {
  for (const t of ["bar", "line", "area", "kpi", "text", "table", "histogram", "boxplot"]) {
    assert.equal(chartIssue(t, 0, 0), null, t);
    assert.equal(chartIssue(t, 9, 9), null, t);
    assert.ok(!Object.hasOwn(CHART_NEEDS, t), t);
  }
});
test("an unknown or prototype-named type has no needs", () => {
  assert.equal(chartIssue("constructor", 0, 0), null);
  assert.equal(chartIssue("nope", 0, 0), null);
});
test("min/max of a text value wins over every other rule, except on table / text / kpi", () => {
  const c = counts({ textValue: true, measures: 1, dims: 0 });
  assert.equal(issueFor("scatter", c), TEXT_VALUE_HINT);
  assert.equal(issueFor("bar", counts({ textValue: true, discreteColor: true, measures: 2 })), TEXT_VALUE_HINT);
  for (const t of ["table", "text", "kpi"]) assert.equal(issueFor(t, c), null, t);
});
test("a discrete Colour split needs exactly one measure, on the split types only", () => {
  const two = counts({ discreteColor: true, measures: 2, dims: 2 });
  for (const t of ["bar", "stacked", "line", "area"]) assert.equal(issueFor(t, two), COLOR_SPLIT_HINT, t);
  assert.equal(issueFor("bar", counts({ discreteColor: true, measures: 1, dims: 2 })), null);
  assert.equal(issueFor("pie", two), chartIssue("pie", 2, 2)); // pie isn't a split type → its own rule
});
test("histogram and box plot need a numeric field; other tables don't block them", () => {
  assert.equal(issueFor("histogram", counts()), "A histogram needs a numeric field — add one to Columns or Rows.");
  assert.equal(issueFor("boxplot", counts()), "A box plot needs a numeric field — add one to Columns or Rows.");
  assert.equal(statFieldHint("boxplot"), "A box plot needs a numeric field — add one to Columns or Rows.");
  assert.equal(issueFor("histogram", counts({ numericField: true, dims: 5, measures: 3 })), null);
});
test("otherwise issueFor is the rule table", () => {
  assert.equal(issueFor("heatmap", counts({ dims: 1, measures: 1 })), chartIssue("heatmap", 1, 1));
  assert.equal(issueFor("heatmap", counts({ dims: 2, measures: 1 })), null);
});
test("roleOf: an explicit role wins, else numeric → measure", () => {
  assert.equal(roleOf({ category: "numeric" }), "measure");
  assert.equal(roleOf({ category: "text" }), "dimension");
  assert.equal(roleOf({ category: "numeric", role: "dimension" }), "dimension");
  assert.equal(roleOf({ category: "text", role: "measure" }), "measure");
});
```

- [ ] **Step 3: Run it — expect FAIL** (`Cannot find module …/show-me-rules.js`):
  `~/.nvm/versions/node/v24.20.0/bin/node --test tests/js/show-me-rules.test.mjs`

- [ ] **Step 4: Implement** — `src/DashboardBuilder/Features/Dashboard/show-me-rules.js`. Every `text`
  below is today's hint, verbatim (cross-check each against `legacyChartIssue`; the Step 2 test fails on
  any drift).

```js
// P22 Show Me rules — which chart types the sheet's fields can draw, which one to recommend, and how to
// lay Columns / Rows out for a picked type. Also the single home of the chart-type field rules that the
// chart hint uses. Pure, DOM-free (unit-tested under tests/js/show-me-rules.test.mjs).
import { TEXT_VALUE_TYPES } from "./filter-rules.js";

// A pill's role: an explicit role wins; otherwise numeric fields are measures, everything else dimensions.
export const roleOf = (f) => f.role ?? (f.category === "numeric" ? "measure" : "dimension");
// Discrete Colour pivots into one series per value on these types (P7) — they need exactly one measure.
export const COLOR_SPLIT_TYPES = new Set(["bar", "stacked", "line", "area"]);
// P12 statistical charts with their own single-table endpoint (they bypass buildPlan).
export const STAT_SINGLE_TABLE = new Set(["histogram", "boxplot"]);

export const TEXT_VALUE_HINT = "Min/Max of a text or date field shows as Table, Text or KPI — switch the chart type, or use Count.";
export const COLOR_SPLIT_HINT = "Colour splits a single measure across series — use exactly one measure, or remove the Colour field.";
export const statFieldHint = (type) => `${type === "histogram" ? "A histogram" : "A box plot"} needs a numeric field — add one to Columns or Rows.`;

// Field needs per type, checked in order; the first unmet need's text is the hint. Types not listed
// (bar, line, area, kpi, text, table, histogram, boxplot) accept any mapping — 0 dimensions → KPI tiles.
const ANY = Infinity;
const need = (kind, min, max, text) => Object.freeze({ kind, min, max, text });
const PIE = Object.freeze([
  need("measures", 1, 1, "Pie/Donut shows one measure — put exactly one measure on a shelf."),
  need("dims", 1, ANY, "Pie/Donut needs a dimension to slice by — add a dimension."),
]);
const POINTS = Object.freeze([need("measures", 2, ANY, "A point chart plots two measures (X and Y) — add a second measure.")]);
export const CHART_NEEDS = Object.freeze({
  pie: PIE, donut: PIE,
  scatter: POINTS, square: POINTS, circle: POINTS, // P19 point marks share the scatter mapping
  combo: Object.freeze([
    need("measures", 2, ANY, "Combo (dual-axis) needs two measures — add a second measure."),
    need("dims", 1, ANY, "Combo needs a dimension for the category axis — add a dimension.")]),
  stacked: Object.freeze([
    need("measures", 2, ANY, "Stacked bar stacks two or more measures — add another measure."),
    need("dims", 1, ANY, "Stacked bar needs a dimension for the category axis — add a dimension.")]),
  heatmap: Object.freeze([
    need("dims", 2, 2, "Heatmap needs exactly two dimensions (the axes) — put one on Columns and one on Rows."),
    need("measures", 1, ANY, "Heatmap colours by one measure — add a measure.")]),
  treemap: Object.freeze([
    need("dims", 1, 2, "Treemap nests by one or two dimensions — add one or two."),
    need("measures", 1, ANY, "Treemap sizes by one measure — add a measure.")]),
  waterfall: Object.freeze([
    need("measures", 1, 1, "Waterfall shows one measure as a run of changes — use exactly one measure."),
    need("dims", 1, ANY, "Waterfall needs a dimension for its steps (e.g. month or category) — add one.")]),
  funnel: Object.freeze([
    need("measures", 1, 1, "Funnel sizes its stages by one measure — use exactly one measure."),
    need("dims", 1, 1, "Funnel needs exactly one dimension for its stages.")]),
  gauge: Object.freeze([
    need("measures", 1, 1, "Gauge shows one measure — use exactly one measure."),
    need("dims", 0, 0, "Gauge shows a single value — remove the dimensions (or use Bullet to compare categories).")]),
  bullet: Object.freeze([
    need("measures", 1, 1, "Bullet compares one measure with a target — use exactly one measure."),
    need("dims", 0, 1, "Bullet takes at most one dimension (one bar per member).")]),
  sankey: Object.freeze([
    need("dims", 2, 2, "Sankey draws flows between two dimensions — put one on Columns and one on Rows."),
    need("measures", 1, 1, "Sankey sizes each flow by one measure — use exactly one measure.")]),
  multiples: Object.freeze([
    need("dims", 2, 2, "Small multiples needs two dimensions: the first makes a panel per member, the second runs along each panel."),
    need("measures", 1, ANY, "Small multiples plots a measure — add one.")]),
});

/** The rule-table hint for a type and its field counts, or null when it can draw them. */
export function chartIssue(type, dimCount, measureCount) {
  if (!Object.hasOwn(CHART_NEEDS, type)) return null;
  const n = { dims: dimCount, measures: measureCount };
  for (const c of CHART_NEEDS[type]) if (n[c.kind] < c.min || n[c.kind] > c.max) return c.text;
  return null;
}

/** Why `type` can't draw the sheet described by `counts` (first rule that fails), or null. */
export function issueFor(type, counts) {
  if (counts.textValue && !TEXT_VALUE_TYPES.has(type)) return TEXT_VALUE_HINT;
  if (counts.discreteColor && COLOR_SPLIT_TYPES.has(type) && counts.measures !== 1) return COLOR_SPLIT_HINT;
  if (STAT_SINGLE_TABLE.has(type) && !counts.numericField) return statFieldHint(type);
  return chartIssue(type, counts.dims, counts.measures);
}
```

- [ ] **Step 5: Run it — expect PASS** (same command as Step 3).

- [ ] **Step 6: Switch `dashboards.js` to the module** (behaviour unchanged):
  - Add to the imports: `import { roleOf, COLOR_SPLIT_TYPES, STAT_SINGLE_TABLE, chartIssue, TEXT_VALUE_HINT, COLOR_SPLIT_HINT, statFieldHint } from "./show-me-rules.js";`
  - Delete `const roleOf = …` (l.61), `const STAT_SINGLE_TABLE = …` (l.167) and
    `const COLOR_SPLIT_TYPES = …` (l.172), with the comment lines that describe only them (the module
    carries those comments); keep the lines that describe `COLOR_USES`, which stays.
  - l.2239: `chartEl.replaceChildren(hint(statFieldHint(s.chartType)));`
  - l.2422: `chartEl.replaceChildren(hint(TEXT_VALUE_HINT));`
  - l.2440: `chartEl.append(hint(COLOR_SPLIT_HINT));`
  - Delete the whole local `function chartIssue(…) { … }` and its two comment lines (l.2726–2787). The
    call at l.2448 now resolves to the import with the same signature.

- [ ] **Step 7: Verify.** `node --check src/DashboardBuilder/Features/Dashboard/dashboards.js`;
  `grep -n "function chartIssue\|const roleOf\|const COLOR_SPLIT_TYPES\|const STAT_SINGLE_TABLE" src/DashboardBuilder/Features/Dashboard/dashboards.js`
  → no output; full JS suite → all pass (213 + the new file).

- [ ] **Step 8: Commit.**

```bash
git add src/DashboardBuilder/Features/Dashboard/show-me-rules.js tests/js/show-me-rules.test.mjs \
  src/DashboardBuilder/Features/Dashboard/dashboards.js
git commit -m "Move chart-type field rules into show-me-rules.js (P22)

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"
```

Task 2 continues in [plan-placement.md](plan-placement.md).
