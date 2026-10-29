# Worksheet encodings — Marks, Filters, click-to-filter, Drill, Pages

Everything beyond the Columns/Rows shelves. All of it rides the **existing** bounded aggregate/join
query and the bound-parameter filter path — no encoding adds a server query shape
([D18](../reference/decisions.md#d18--marks-card-and-pages-shelf-are-client-encodings-on-the-existing-query-shape)).
Base worksheet: [worksheet.md](worksheet.md). State shapes:
[data-model.md](../reference/data-model.md#marks-pages-selection-drill).

## Encodings toolbar

One wrapping row of compact **icon + text** buttons (`buildTools` / `toolButton`, `.ws-toolbar`) plus a
**More** menu. `visibleTools(chartType, tools)` (`Dashboard/toolbar-rules.js`, pure) decides where each
tool sits:

| Tool | In the visible row when | Otherwise |
|---|---|---|
| Filters, Date range, Color, Label, Tooltip | always | — |
| Size, Shape | chart type is `scatter`, `square` or `circle` | More |
| Path | `line` or `area` | More |
| Angle | `pie` or `donut` | More |
| Detail, Drill, Pages | never by default | More |

**In-use override:** a tool that holds fields (count > 0) is always in the visible row with its count
badge, whatever the chart type — no state hides behind More. Choosing a tool from More opens its
editor like any other tool. Icons come from `Core/icons.js`.

Each visible button shows a **count badge** when it holds fields, is a **drop target** (drag a field straight
onto it), and on click opens **one** editor panel (`toolPanel`, `.ws-toolpanel`) with its pills over a
drop zone. At most one editor is open at a time.

## Marks

How each encoding reaches the query (`planDims` / `planMeasures`):

| Encoding | Accepts | Query effect | Renders as |
|---|---|---|---|
| **Color** (categorical) | 1 dimension | extra group-by, appended last | one coloured series per value: bar → grouped, stacked → stacked, line/area → one line each; Table → extra header level |
| **Color** (numeric) | 1 measure | extra measure | continuous token gradient (`visualMap`) — scatter and heatmap; hue and range in Format |
| **Size** | 1 measure | extra measure | scatter bubble size |
| **Label** | 1 field | numeric → extra measure; categorical reads an existing key | the value drawn on each mark |
| **Detail** | dimensions | extra group-by | more marks, no visual channel |
| **Tooltip** | fields | numeric → extra measures | custom tooltip lines (`extraTooltip`); with a tooltip text set, the template replaces them (below) |
| **Shape** | 1 dimension | extra group-by (scatter family) | one series per value with a distinct symbol + legend |
| **Path** | 1 field | numeric → extra measure | orders line/area vertices (`pathOrderedRows`) |
| **Angle** | 1 measure | — | acknowledged for pie/donut (already measure → angle); a hint elsewhere |

### Tooltip text (T01-19)

The Tooltip tool panel also holds a **Tooltip text** editor: free text with `<Field>` placeholders for the
view's fields — group-by / Tooltip fields as `table.column`, measures as named in the view — plus literal text
(Enter = new line, max `LIMITS.tooltipText` = 300 characters, client-side only). Field chips insert a
placeholder at the cursor; a live preview fills them from the first mark, and a note lists placeholders not in
the view. It is stored on the sheet as `tooltipText` (`null` = the automatic tooltip) and saved with the workbook
(`sanitizeSheet` drops over-long / non-text values with an import issue). `chart.js` `customTip` renders it for
bar / line / area / combo (axis tooltip: every series in the hover), pie / donut and scatter-family charts;
unknown placeholders show as literal text, values use the existing value / category formatters. All HTML is built
in `Dashboard/tooltip-model.js` from escaped parts only (`<script>`, quotes, `&` are escaped — user text never
becomes markup). The automatic tooltip is kept on Table, Text, KPI, Heatmap, Treemap, discrete-colour splits, Scatter with a Shape field and the P36 chart types. The chips offer only fields that resolve: group-by / Tooltip fields and the shelf measures (not Size / continuous-Colour measures).

- Extra measures never become chart series; with no marks set the plan is byte-identical to a plain
  shelves plan.
- **Colour split needs one measure** — multi-measure + Colour → a hint. Types outside `COLOR_USES`
  (pie, donut, scatter, combo, KPI) show a note and ignore the Colour pill.
- Colour × category combinations are still capped by the query `LIMIT`.
- Every unmet mapping shows a **hint, not an error**.

## Filters

Each Filters pill is a column + operator + value; every value is a **bound typed parameter**
([golden rule 3](../conventions/golden-rules.md#3-bind-every-value-bound-every-result)).

| Operator | Control | Binding |
|---|---|---|
| `= != > >= < <=` | single value, ≤ 1000 characters | bound as the **column's type** (below) |
| `in` | multi-select from a **bounded distinct-values** query (`GET …/columns/{col}/distinct`; the editor asks for 201 and shows 200) | `Array(Float64)` / `Array(String)` / `Array(UInt8)` by type; ≤ 500 values |
| `not in` (Exclude) | the same multi-select as `in` | `(col NOT IN {p:Array(…)} OR isNull(col))` — same arrays and ≤ 500 limit. **Rows where the column is NULL are kept** (a bare `NOT IN` would drop them, three-valued logic); single-value `!=` still drops NULLs |
| `between` | two bounds, From ≤ To | two typed parameters |
| `contains` / `starts with` / `ends with` (P30, text fields) | text, ≤ 1000 characters | bound `String`: `positionCaseInsensitiveUTF8(col, p) > 0` / `startsWith(lowerUTF8(col), lowerUTF8(p))` / `endsWith(…)` — case-insensitive, no LIKE pattern, nothing to escape |
| `in the` — relative date (P30, date fields) | a period preset (last 7 / 28 / 30 / 90 days, this / last month, quarter, year) | resolved in the browser to a bound `between` over whole days (`serverFilter`) |
| `top` — top-N (P30, dimensions) | top / bottom, n (1–1000), by a shelf measure | `col IN (SELECT col … same joins + other filters … GROUP BY col ORDER BY agg DESC LIMIT n)` — column and measure catalog-validated, aggregation whitelisted, n a validated integer |

**Values are parsed by the column's category** (`filterValue` / `range` in `Core/validate.js`, mirrored
by the server's `FilterValues.Coerce`):

| Category | Accepted |
|---|---|
| number | plain decimal or exponent (`12`, `-3.5`, `1e3`) — not `1,000`, `0x10`, `NaN` |
| date / datetime | ISO `YYYY-MM-DD` or `YYYY-MM-DD HH:MM:SS` (`T` allowed, seconds optional). A `Date` / `Date32` column rejects a time part |
| boolean | `true`, `false`, `1`, `0` |
| text | any |
| compound / other | can't be filtered |

A value that doesn't fit makes the pill **invalid** (dashed border, warning icon, tooltip) with the
reason inline in the filter editor ("'abc' is not a number for column amount."); an inverted range says
"From must be less than or equal to To". An invalid filter is **not applied** — it is never sent.
An empty `in` / `not in` or a blank filter is a no-op (never `IN ()`); a half-filled range is invalid. When the
distinct list has more than 200 values the editor says "Showing the first 200 values — more exist."
Filters are worksheet-scoped unless **shared**. At most **8** user filters; the server accepts up to 20 per query.

**Parameters** (P32). A scalar, text-match or top-N filter's **{ }** button binds its value to a
workbook parameter of the field's type (number for numeric fields and top-N counts, date for dates,
text for text); the value editor becomes a parameter picker, and **{ }** again unbinds it (keeping the
current value). The bound value is filled in at plan time (`withParamValue`) and sent as an ordinary
bound filter value. Every parameter a sheet uses — its filters, the shared filters, Format → Top N, calculated fields, a bound reference line — gets
a control above the filter cards (also each parameter a calculated pill reads as `[@Name]`, and a bound reference line): a select for a list, a slider + box for a number range (the slider moves by the parameter's **step size** when it has one), else a typed
input; a value outside the allowed ones is refused with the reason, and a change re-runs the view (and every dashboard widget).
The Parameters dialog's number **range** has min, max and an optional **step size** (a positive number; empty is none; saved and shown again on edit).
Deleting a parameter that a calculation reads asks first. Analytics → Reference line **Constant** can follow a number parameter instead of a typed value
(`analytics.ref.param`); a deleted parameter falls back to the line's own value.

**Filter cards** (P30). Under the title, each of the sheet's filters — and the shared ones — shows as a
card: a **checkbox list** for `in` / `not in` (the bounded distinct values; a `not in` card is labelled "not in"), the filter's own editor otherwise. Cards
and the Filters tool edit the same objects, so they always agree; ⋯ → **Show filter cards** hides them
(`sheet.showFilterCards`). The operator list follows the field type (`opsFor`).

**Shared filters** (P40). A filter pill's **link** button moves it to the workbook's shared list
(`sharedFilters`, at most **4**) — it then shows on every dashboard's Filters tool with an **All
dashboards** badge, and editing it anywhere changes it everywhere; the link button again moves it back to
this dashboard. A shared filter applies wherever **its table is already in the view** (it never forces a
join); where it isn't, the tool and the chart card's info line say so ("customers.country: shared, but not
applied here — its table isn't in this view."). Histogram and box plot don't apply shared filters.

**Histogram and box plot** are single-table views: they apply the filters that sit on their own table
and show a notice counting the rest ("2 filters on other tables don't apply to a box plot").

## Click-to-filter

Clicking a chart mark **selects** its primary-dimension value (`chart.js` forwards the ECharts click;
`selectHandler` / `toggleSelection` map `dataIndex` → the raw value) into `sheet.selection`. A
**selection chip** (`.ws-select`) offers:

- **Keep only** → `col = value` · **Exclude** → `col != value` · **✕** clear.
- **Legend clicks** (P29) — clicking a legend item **highlights** that series (the others dim, via
  ECharts `emphasis.focus: "series"`); clicking it again clears. When the legend lists a dimension's
  members — a Colour split, a Shape split, or a pie / donut's slices — the click also **selects** that
  member, so this bar offers Keep only / Exclude exactly as a mark click does. A legend of measures only
  highlights. The legend no longer hides series on click (ECharts' toggle is undone at once and the click
  handed to the worksheet, a tick later so a re-render never disposes the chart mid-event).
- **Link action** (P39) — when the sheet has one (Format → **Link action**: a label and an `https://`
  address with `{value}`), an **"<label> ↗"** button opens that address with the selected value
  URL-encoded into `{value}`, in a new tab with `noopener`. Only `https:` links with a host are accepted
  (`http:`, `javascript:`, `data:` and the like are refused with the reason); a value can't change the
  host or break out of its slot. Nothing opens without that click. Rules: `Dashboard/action-model.js`
  (unit-tested). One link action per sheet (`sheet.urlAction`).

The action is a bound-parameter filter appended in `buildPlan` **only when the column's table is
already in the query** — a click never forces a join. Exclude is a single-value `!=`; to exclude several members use a `not in` filter. Clicking the same mark again clears it. Works on
bar, stacked, line, area, combo, pie, donut and scatter (incl. colour-split); other types and null
values are no-ops. On a dashboard the same click filters the other widgets at once ([dashboards.md](dashboards.md#cross-widget-filtering)). Why select-then-act:
[D16](../reference/decisions.md#d16--click-to-filter-is-a-select-then-act-worksheet-selection).

## Drill-down

The **Drill** tool takes ≥2 dimension fields **from one table** as an ordered hierarchy
(year → quarter → month) on `sheet.drill`:

1. The **current level leads the group-by** — `buildPlan` prepends it as the first row dimension, so
   it drives the category axis.
2. Clicking a mark **drills one level finer**, pinning the clicked value; every pinned ancestor is a
   bound `=` filter on the drill table (same table → never a join). An active drill takes clicks
   instead of selection.
3. A **breadcrumb** (`.ws-drill`, `--warn` tint) shows `All › 2023 › Q2`; each crumb jumps up, **Up** goes up
   one level. Clicking at the finest level does nothing.

A hierarchy holds at most **6** levels (a further add is refused with a toast). Editing the levels
resets the descent. A hierarchy with no shelf fields renders an implicit-count
chart of the current level. Why one table:
[D17](../reference/decisions.md#d17--drill-down-is-a-single-table-hierarchy-on-the-bound-param-path).

### Named hierarchies

A **named hierarchy** (T03-29) is a reusable drill path kept on the workbook:
`{ id, name, levels: [{ db, table, column }] }` — 2–6 levels, all from one table, no repeated column (the same rules as
the Drill tool), at most **20** per workbook, a name of 1–60 characters unique case-insensitively. A calculated field or a
field with a type cast can't be a level (the calc refusal text, or "A field with a type cast can't be a hierarchy level").
They are managed in the field pane's **Hierarchies** group (above the tables): **New hierarchy** and **Hierarchies…** open the
dialog (`Dashboard/hierarchy-dialog.js`) — a name, a table, and an ordered level list built with an "Add a level" picker and
per-level **Up / Down / Remove** buttons (labelled, keyboard-operable; focus stays on the control just used), plus
Edit / Delete (Delete confirms). Each hierarchy is a chip with its level count.

Dragging a chip onto the **Drill** tool (its button, its open panel, or **More** while Drill is empty) — or its plus button —
**replaces the sheet's drill** with `{ levels, depth: 0, path: [] }`, the structure a hand-built drill has (each level carries
its column's category), so the chart, breadcrumb and click-to-drill behave identically. The sheet gets a **copy** of the levels:
renaming, editing or deleting the hierarchy later never changes a sheet that already used it. A chip whose table isn't in the
Data Model or whose column no longer exists is shown with a "No table" / "Missing field" badge and can't be applied; a column
cast after the hierarchy was made refuses with the cast message. The dialog's Edit keeps a level whose column has vanished (the chip shows "Missing field" until it is removed or replaced). Hierarchies are client-side only (the server never sees one)
and save with the workbook ([workbook.md](workbook.md)). Expand / collapse headers on a crosstab are not built
([roadmap](../backlog/data-model.md)).

## Pages

The **Pages** tool takes one dimension (`sheet.pages`). A page control (`.ws-pages`) below the shelves
shows the current member and count, with previous / next stepping (wrapping) and **Play / Pause**
autoplay every 1.5s — **omitted under `prefers-reduced-motion`**. Each page applies the current member
as a bound `=` filter, only when its table is already in the query. Members come from the bounded
distinct-values query (shared with `in`; capped at 200, with the same "more exist" notice, and a load
failure shows the server's message). The autoplay timer is cleared on view switch.

## Date range & comparison

The **Date range** tool (calendar icon, P35) takes one date / date-time field (`sheet.period`; anything
else is refused with a toast). Its panel (`periodEditor`) picks:

- **Range** — Last 7 / 28 / 30 / 90 days (ending today), This / Last month, quarter, year, or **Custom**
  (two day pickers). Whole days, inclusive, in the browser's calendar.
- **Compare to** — No comparison, **Previous period** (the same number of days just before), **Same period
  last year** (29 Feb → 28 Feb) or **Custom**.

The panel and the chart card's notice line show the resolved days ("1 Sept – 30 Sept 2026 vs 2 Aug – 31 Aug
2026"); an incomplete custom range says so and isn't applied. The range is one bound `between` filter on
the field (days for `Date`, `00:00:00`–`23:59:59` for `DateTime`) and, like a filter, may bring its table
into the query. A new range defaults to **Last 30 days vs previous period**.

The **comparison** is the same query over the comparison range (cached like any result; a failure toasts
and the chart still draws). It shows on:

| View | Shows |
|---|---|
| **KPI** (no dimensions) — the scorecard | under each value: ▲ / ▼ / ■ + signed % + "vs previous period", coloured `--up` / `--down` (good / bad) with an `aria-label`; the previous value in its tooltip. Format → **A fall is good** flips the tone. Format → **Target** (KPI) adds a progress bar and "78% of 40,000" under the first measure (✓ when met) |
| **Line / Area** | a dashed, faded line per measure, named "<measure> (previous period)" in the legend |
| **Bar** | a hatched, muted bar beside each bar, named in the legend |

Rows line up **by position** when the first group key is the range's own date field (day 1 with day 1),
otherwise **by the same keys** (e.g. the same country). Other chart types apply the range only and the
panel says so. Rules: `Dashboard/period-model.js` (unit-tested).

## Member colours and palette order (T01-20, T03-33)

- **Member colours.** Format → **Edit member colours** lists the members the drawn chart colours by a discrete
  field — Colour-shelf members on bar/stacked/line/area, pie / donut slices, and the categories of a
  single-measure bar with *Colour by category*. Each row offers 24 fixed swatches (the three workbook palettes'
  light colours) and **Reset**, with **Reset all for this field** below the list (it also removes colours of members no longer in the view, which still count toward the cap); the list stays open across redraws and is disabled until such a chart is drawn.
  Legend clicks are unchanged (highlight / select).
- **Stored** as `sheet.memberColors = { "<table>.<column>": { "<member>": "#rrggbb" } }` — workbook data, so a
  validated hex, not a token. The member key is the raw value as text (`null` has its own key), so a colour
  survives a change of number/date format. Limits ([api.md](../reference/api.md#limits), client-side only):
  100 members per field, 20 fields, member key ≤ 100 chars, field key ≤ 200 (maps are null-prototype, so a member named `constructor` or `__proto__` is an ordinary key; an imported `__proto__` is dropped and reported); invalid entries are dropped on import and reported.
  Old workbooks load with `{}`. A calculated field cannot be member-coloured; scatter groups and treemap / funnel
  are not yet wired.
- **Contrast.** User colours are not adjusted; label inks still come from `Dashboard/contrast.js` (`pickInk`), which picks the higher-contrast ink for any hex.
- **Reverse palette** (`format.paletteReverse`, boolean, default off) reverses the eight categorical colours' order
  and swaps the continuous ramp's ends (heatmap and scatter colour). Member colours are unaffected.
- **Continuous colour scale** (T03-19; Format, on Scatter and Heatmap): **Colour ramp** Brand (accent soft → accent),
  Blue, Green, Amber or Violet (the surface blended 20 % toward that categorical token, up to the token) —
  `format.colorRamp`, default `brand`; **Colour from / to** (`format.colorMin` / `colorMax`, blank = the data's own
  end) pin the ends of the scale, and values outside a pinned end draw in the neutral axis grey while the legend
  shows the pinned span. A minimum not below the maximum is refused with a toast; a saved one is cleared on import and
  reported. Reverse palette still swaps the ramp's ends. Table cell scales have their own
  conditional-formatting colours and are unaffected. Pure logic: `Dashboard/colour-scale-model.js`
  (`RAMP_CHOICES`, `rampColours`, `mixHex`, `colourRangeError`, `rangeOf`).
- Pure logic: `Dashboard/colour-model.js` (`setMemberColor`, `cleanMemberColors`, `colorsByName`,
  `orderedPalette`, `rampStops`, `SWATCHES`).

