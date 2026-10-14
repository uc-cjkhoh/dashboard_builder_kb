# P22 — Show Me

A proposal, not yet built. A **Show Me** card lists every chart type, enables the ones the fields on the
sheet can draw, outlines the best one, and on a click sets the type **and** re-arranges the fields on
Columns / Rows into that type's natural layout. When built, the behaviour moves into
[worksheet-charts.md](../features/worksheet-charts.md#chart-types) and
[frontend-modules.md](../reference/frontend-modules.md), P22 leaves [roadmap.md](roadmap.md), and this file
and its plan are deleted ([kb-maintenance.md](../conventions/kb-maintenance.md#when-you-make-a-change)).

## Goals

- From any set of fields on the sheet, one click yields a chart that draws — no hint screen.
- Inapplicable types are greyed **with the reason**, in the same words the chart hint already uses.
- One source of truth for "can this type draw these fields": the chart hint and Show Me never disagree.

## Non-goals

- **No field selection.** Show Me reads the fields already on the sheet (Columns, Rows, Colour, Marks,
  drill). The field pane keeps its drag / "+" flow; there is no Ctrl/Shift-click multi-select.
- **Nothing added or dropped.** A click moves pills between Columns and Rows only. Colour, Size, Label,
  Detail, Tooltip, Shape, Path, Angle, filters, sort, format and analytics are untouched.
- No new chart types, no server change, no query-shape change, no workbook format change (`chartType`,
  `columns`, `rows` already exist).
- The chart-type dropdown stays as it is: the quick "set the type only" control.

## Decisions

| # | Decision | Why |
|---|---|---|
| S1 | Input = fields already on the sheet | the builder has no field-selection concept; adding one is its own phase |
| S2 | A click re-arranges Columns / Rows to fit | "one click yields the chart" (roadmap done-when); fields are never lost |
| S3 | A separate Show Me card beside the dropdown | the dropdown keeps a way to change type without moving fields |
| S4 | Rules move to a pure, tested module | `chartIssue()` is today a closure-local `switch` in `dashboards.js` with no tests |
| S5 | Placement keeps dimension and measure **order** | heatmap, Sankey and small multiples read the first group-by key as the source / panel; a click must never swap them |

## Behaviour

### The card

- A **Show Me** button sits in the view bar's left group, after the chart-type dropdown. It toggles a
  card below the view bar — the Format / Analytics card pattern: one card open at a time, `hidden`
  visibility, `enter()` motion, `aria-expanded` on the button.
- The card is a grid of all 23 `CHART_TYPES` tiles (icon from `chartIcon` + label), in `CHART_TYPES`
  order.
- **Valid** tile — a normal button. **Invalid** tile — muted, `aria-disabled="true"` (still focusable),
  its reason as `aria-describedby`; activating it shows the reason in the card's status line instead of
  acting.
- **Recommended** tile — accent outline **plus** a "Recommended" text badge (never colour alone).
- **Current** type — `aria-pressed="true"` and a check icon.
- No fields on Columns / Rows: every tile stays listed; the status line reads "Add fields to Columns or
  Rows to see suggestions." and nothing is outlined.
- The card stays open after a pick so the user can try another. The header re-renders on every commit,
  so the card is rebuilt from the current sheet and focus is restored to the tile that was picked.
- `Esc` closes the card and returns focus to the Show Me button.

### A click on a valid tile

`next = { ...sheet, chartType: id, ...placeFor(id, sheet.columns, sheet.rows) }`, then **one** `commit`
— one undo step, one query. Picking the current type re-applies its layout (a no-op if already in it).

## Validity

A type is valid when `issueFor(id, counts)` returns `null`. `counts` is computed **per candidate type**
(the Shape and discrete-Colour dimensions count only for some types) by a callback from `dashboards.js`:

| Field of `counts` | Source in `dashboards.js` |
|---|---|
| `dims` | `planDims({ ...sheet, chartType: id }).keyOrder.length` (drill, shelf, Detail, Shape, discrete Colour) |
| `measures` | shelf measures from `planMeasures` (role `"shelf"`) |
| `hasDate` | a `temporal` dimension on Columns / Rows |
| `textValue` | a shelf measure with `min` / `max` on a non-`numeric` field |
| `discreteColor` | `colorMode(sheet) === "discrete"` |
| `numericField` | a `numeric` field on Columns / Rows |
| `singleTable` | every Columns / Rows field from one `db.table` |

Rules, checked in this order (first hit is the reason):

1. `textValue` and type ∉ {table, text, kpi} → "Min/Max of a text or date field shows as Table, Text or
   KPI — switch the chart type, or use Count."
2. `discreteColor`, type ∈ {bar, stacked, line, area}, `measures ≠ 1` → "Colour splits a single measure
   across series — use exactly one measure, or remove the Colour field."
3. histogram / boxplot without `numericField` → "A histogram needs a numeric field — add one to Columns
   or Rows." (box plot: "A box plot needs …"); without `singleTable` → "Histogram and box plot read one
   table — keep Columns and Rows to fields from one table."
4. The `CHART_NEEDS` table (today's `chartIssue` `switch`, unchanged):

| Type | dims | measures |
|---|---|---|
| pie, donut | ≥ 1 | = 1 |
| scatter, square, circle | any | ≥ 2 |
| combo, stacked | ≥ 1 | ≥ 2 |
| heatmap | = 2 | ≥ 1 |
| treemap | 1–2 | ≥ 1 |
| waterfall | ≥ 1 | = 1 |
| funnel | = 1 | = 1 |
| gauge | = 0 | = 1 |
| bullet | ≤ 1 | = 1 |
| sankey | = 2 | = 1 |
| multiples | = 2 | ≥ 1 |
| bar, line, area, kpi, text, table, histogram, boxplot | any | any |

Each row keeps today's hint text verbatim. A bullet without a Format target stays valid — the chart
already hints for the target.

## Recommendation — `bestType(counts)`

First matching row wins; the result is outlined only if it is itself valid, else nothing is outlined.

| Fields in play | Recommended |
|---|---|
| no dims, no measures | none |
| `textValue` | table |
| dims ≥ 3 | table |
| dims = 0, measures = 2 | scatter |
| dims = 0, measures ≥ 1 | kpi |
| `hasDate`, measures ≥ 1 | line |
| dims = 1, measures ≥ 1 | bar |
| dims = 2, measures = 1 | heatmap |
| anything else | table |

## Placement — `placeFor(type, columns, rows)`

Let **D** be the dimensions in group-by key order (Rows dimensions, then Columns dimensions) and **M** the
measures in series order (Columns measures, then Rows measures) — the orders `planDims` / `planMeasures`
already use. Pills are moved as-is (role, agg, date part, table calc kept). Returns `{ columns, rows }`.

| Family | Types | columns | rows |
|---|---|---|---|
| Horizontal bars | bar, stacked — only when today Rows holds a dimension and Columns none | M | D |
| Category × measure | bar, stacked, waterfall, funnel, bullet, kpi, pie, donut, treemap, gauge, histogram, boxplot | D | M |
| Time series | line, area, combo | D with temporal dims first (stable) | M |
| Measure × measure | scatter, square, circle | D, then M[0] | M[1…] |
| Two dimensions | heatmap, sankey, multiples | D[1…], then M | D[0] |
| Text table | table, text | M | D |

Invariants (tested): the multiset of pills on Columns + Rows is unchanged; the relative order of D and of
M is unchanged; the result passes `normaliseShelf` unchanged (dimensions ahead of measures). Each
family's layout is confirmed against its renderer while planning, so a click on a valid tile always
draws.

## Code

| File | Change |
|---|---|
| `Features/Dashboard/show-me-rules.js` | **new**, pure, no imports: `CHART_NEEDS`, `issueFor(type, counts)`, `chartIssue(type, dims, measures)` (the table rule only, for the existing hint), `showMeOptions(types, countsFor)` → `[{ id, issue, recommended }]`, `bestType(counts)`, `placeFor(type, columns, rows)` |
| `Features/Dashboard/dashboards.js` | delete the local `chartIssue`; import it; add `countsFor(sheet)`, the Show Me button + card (`showMeToggle` / `showMePanel`, beside `formatToggle` / `formatPanel`), one-open-card wiring |
| `Features/Dashboard/dashboard.css` | the card grid, tile states (muted, recommended outline + badge, pressed) — tokens only, `--ctl-h` |
| `Features/Core/icons.js` | a Show Me icon if no existing one fits (inline SVG, covered by `icons.test.mjs`) |
| `tests/js/show-me-rules.test.mjs` | **new** |

## Testing

- `show-me-rules.test.mjs`: every `CHART_NEEDS` row at, below and above its bounds with today's hint
  text (regression for the moved `chartIssue`); rules 1–3 and their precedence; every `bestType` row;
  `placeFor` for each family incl. horizontal bars kept horizontal, temporal-first on line, D[0] on Rows
  for the two-dimension types, and the three invariants over generated shelves.
- Both suites stay green; `node --check` on changed modules.
- Manual on the dev port: each recommended type draws without a hint from a bar sheet with 1, 2 and 3
  dimensions; undo restores the prior layout in one step; keyboard-only use of the card; light + dark.

## Done when

With fields on the sheet, applicable types are enabled and the best one outlined; one click yields the
chart with sensible placement in one undo step; inapplicable types are greyed with the reason; the chart
hint and Show Me share one rule table; the KB is updated and this file deleted.
