# Worksheet encodings — Marks, Filters, click-to-filter, Drill, Pages

Everything beyond the Columns / Rows shelves. All of it rides the **existing** bounded aggregate/join query and the bound-parameter filter path; no encoding adds a server query shape ([D18](../../reference/decisions/decisions.md#d18--marks-card-and-pages-shelf-are-client-encodings-on-the-existing-query-shape)).

Base worksheet: [worksheet.md](worksheet.md). State shapes: [data-model.md](../../reference/data-model.md#marks-pages-selection-drill).

## At a glance

- **No new query shapes:** every encoding is a client-side layer over the one aggregate/join query and the bound-parameter filter path.
- **Marks** (Color, Size, Label, Detail, Tooltip, Shape, Path, Angle) add group-bys or labels. The table under *Marks* says what each accepts and how it renders.
- **Filters** are column + operator + bound typed value. **Date range** is a filter with an optional comparison period.
- **Click-to-filter** selects a mark's primary-dimension value, then offers Keep only / Exclude / View data.
- **Drill** walks an ordered same-table hierarchy. **Pages** steps one dimension one member at a time.
- **Member colours** are display-side overrides keyed by the raw value.

**Sections:** Marks slots · Marks · Filters · Click-to-filter · Drill-down · Pages · Date range & comparison · Member colours and palette order

## Marks slots

The Marks group sits at the top of the field pane and collapses like the other groups. It is a grid of **three columns** of slots: Color, Size, Label, Detail, Tooltip, Shape, Path, Angle, Filters, Date range, Drill, Pages.

- **Every tool is always reachable** (there is no More menu). Tools the chart type doesn't use are **quiet** (dimmed) unless they hold fields: Size / Shape outside scatter, square, circle; Path outside line, area; Angle outside pie, donut; Detail, Drill and Pages by default.
- **A slot** is an icon over its name. It shows a **count badge** when it holds fields and is a **drop target** (drag a field straight onto it).
- **Click a slot** to open **one** editor panel in the data header, with its pills over a drop zone. At most one editor is open at a time.
- Code: `.ws-shelf--marks`; `buildTools` / `toolButton`; `markGrid` in `Dashboard/pill-options.js` chunks the slots into rows of three. `visibleTools(chartType, tools)` (`Dashboard/toolbar-rules.js`, pure) decides which are quiet. The editor panel is `toolPanel` (`.ws-toolpanel`). Icons come from `Core/icons.js`.

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

### Tooltip text (T01-19) and the tooltip modal

#### Tooltip text box

The Tooltip tool panel also holds a **Tooltip text** editor: free text with `<Field>` placeholders for the view's fields, plus literal text.

- **Placeholders:** group-by / Tooltip fields as `table.column`; measures as named in the view. Field chips insert a placeholder at the cursor. The chips offer only fields that resolve: group-by / Tooltip fields and the shelf measures (not Size / continuous-Colour measures).
- **Editing:** Enter = new line. At most `LIMITS.tooltipText` = 300 characters (client-side only).
- **Feedback:** a live preview fills the placeholders from the first mark, and a note lists placeholders not in the view.
- **Stored** on the sheet as `tooltipText` (`null` = the automatic tooltip) and saved with the workbook. `sanitizeSheet` drops over-long / non-text values with an import issue.
- **Where it applies:** `chart.js` `customTip` renders it for bar / line / area / combo (axis tooltip: every series in the hover), pie / donut and scatter-family charts. The automatic tooltip is kept on Table, Text, KPI, Heatmap, Treemap, discrete-colour splits, Scatter with a Shape field and the P36 chart types.
- **Rendering:** unknown placeholders show as literal text; values use the existing value / category formatters.
- **Safety:** all HTML is built in `Dashboard/tooltip-model.js` from escaped parts only (`<script>`, quotes, `&` are escaped). User text never becomes markup.

#### Edit tooltip… modal

**Edit tooltip…** (a button in the panel) opens a modal (`Dashboard/tooltip-dialog.js`). Focus goes to the first line on open; after Apply, Cancel or Esc it returns to **Edit tooltip…**.

- **Left — the template as a list of lines:** one text input each, at most `LIMITS.tooltipLines` = 12. The 300-character total still applies and blocks Apply.
  - Field chips insert `<field>` into the selected line. **Add line** adds one.
  - Per line: **move up / down** (buttons, or Alt+Up / Alt+Down in the line's input; the style travels with the line) and **remove**.
  - Per line style: **size** (Auto, 14, 16 or 24 px), **bold**, **italic** and **colour** (Auto or a token palette: text, muted, accent, green, amber, blue, teal, violet).
- **Right — a live preview** rendered by the same `tooltipHtml` the chart hover uses, filled with the chart's first-mark sample values.
- **Draft until applied:** **Apply** commits once (one undo step); **Cancel** / Esc discard; **Automatic** clears the template.
- **Stored** as `tooltipStyle` on the sheet: a list aligned to the template's lines of `{ size?, bold?, italic?, color? }` (`null` / absent = default). The key exists only once a line is styled, so files without styles round-trip unchanged.
- **Validated on import** by `checkTooltipStyle` (`Dashboard/tooltip-style.js`):
  - sizes only from the type scale; colours only palette keys, mapped to `var(--ink)`, `var(--accent-ink)`…, so they follow the theme. No hex; nothing user-typed reaches a `style` attribute;
  - at most 12 lines;
  - an invalid style is dropped with an issue; a style without a template is ignored.
- **Keeping styles on their lines:**
  - Clearing the text clears the style.
  - Applying trims leading / trailing blank lines together with their styles.
  - Editing the plain **Tooltip text** box keeps the styles (re-aligned by line index) only while the line count is unchanged. If it changes, the styles are cleared and the note says so.
  - A template of more than 12 lines (possible from the plain textarea) opens in the modal with Apply blocked and the reason shown until lines are removed.

### Marks rules

- Extra measures never become chart series. With no marks set, the plan is byte-identical to a plain shelves plan.
- **Colour split needs one measure:** multi-measure + Colour → a hint. Types outside `COLOR_USES` (pie, donut, scatter, combo, KPI) show a note and ignore the Colour pill.
- Colour × category combinations are still capped by the query `LIMIT`.
- Every unmet mapping shows a **hint, not an error**.

## Filters

Each Filters pill is a column + operator + value. Every value is a **bound typed parameter** ([golden rule 3](../../engineering/golden-rules.md#3-bind-every-value-bound-every-result)).

| Operator | Control | Binding |
|---|---|---|
| `= != > >= < <=` | single value, ≤ 1000 characters | bound as the **column's type** (below) |
| `in` | multi-select from a **bounded distinct-values** query (`GET …/columns/{col}/distinct`; the editor asks for 201 and shows 200) | `Array(Float64)` / `Array(String)` / `Array(UInt8)` by type; ≤ 500 values |
| `not in` (Exclude) | the same multi-select as `in` | `(col NOT IN {p:Array(…)} OR isNull(col))` — same arrays and ≤ 500 limit. **Rows where the column is NULL are kept** (a bare `NOT IN` would drop them, three-valued logic). Single-value `!=` still drops NULLs |
| `between` | two bounds, From ≤ To | two typed parameters |
| `contains` / `starts with` / `ends with` (P30, text fields) | text, ≤ 1000 characters | bound `String`: `positionCaseInsensitiveUTF8(col, p) > 0` / `startsWith(lowerUTF8(col), lowerUTF8(p))` / `endsWith(…)` — case-insensitive, no LIKE pattern, nothing to escape |
| `in the` — relative date (P30, date fields) | a period preset (last 7 / 28 / 30 / 90 days, this / last month, quarter, year) | resolved in the browser to a bound `between` over whole days (`serverFilter`) |
| `top` — top-N (P30, dimensions) | top / bottom, n (1–1000), by a shelf measure | `col IN (SELECT col … same joins + other filters … GROUP BY col ORDER BY agg DESC LIMIT n)` — column and measure catalog-validated, aggregation whitelisted, n a validated integer |

**Values are parsed by the column's category** (`filterValue` / `range` in `Core/validate.js`, mirrored by the server's `FilterValues.Coerce`):

| Category | Accepted |
|---|---|
| number | plain decimal or exponent (`12`, `-3.5`, `1e3`) — not `1,000`, `0x10`, `NaN` |
| date / datetime | ISO `YYYY-MM-DD` or `YYYY-MM-DD HH:MM:SS` (`T` allowed, seconds optional). A `Date` / `Date32` column rejects a time part |
| boolean | `true`, `false`, `1`, `0` |
| text | any |
| compound / other | can't be filtered |

### Invalid and empty filters

- **A value that doesn't fit** makes the pill **invalid** (dashed border, warning icon, tooltip). The reason shows inline in the filter's value editor, in its context popup: "'abc' is not a number for column amount."
- **An inverted range** says "From must be less than or equal to To".
- **An invalid filter is not applied** — it is never sent.
- **An empty `in` / `not in` or a blank filter** is a no-op (never `IN ()`). A half-filled range is invalid.
- **A long distinct list:** with more than 200 values the editor says "Showing the first 200 values — more exist."
- **Scope and caps:** filters are worksheet-scoped unless **shared**. At most **8** user filters; the server accepts up to 20 per query.

### Parameters (P32)

- **Binding a filter.** A scalar, text-match or top-N filter's **{ }** button binds its value to a workbook parameter of the field's type: number for numeric fields and top-N counts, date for dates, text for text. The value editor becomes a parameter picker. **{ }** again unbinds it, keeping the current value.
- **At plan time** the bound value is filled in (`withParamValue`) and sent as an ordinary bound filter value.
- **Controls above the filter cards.** Every parameter a sheet uses gets a control: its filters, the shared filters, Format → Top N, calculated fields (each parameter a calculated pill reads as `[@Name]`) and a bound reference line.
  - A list → a select. A number range → a slider + box; the slider moves by the parameter's **step size** when it has one. Otherwise a typed input.
  - A value outside the allowed ones is refused with the reason.
  - A change re-runs the view (and every dashboard widget).
- **The Parameters dialog's number range** has min, max and an optional **step size** (a positive number; empty is none; saved and shown again on edit).
- **Deleting** a parameter that a calculation reads asks first.
- **Reference line:** Analytics → Reference line **Constant** can follow a number parameter instead of a typed value (`analytics.ref.param`). A deleted parameter falls back to the line's own value.

### Filter cards (P30)

- Under the title, each of the sheet's filters — and the shared ones — shows as a card.
- An `in` / `not in` filter is a **checkbox list** of the bounded distinct values (a `not in` card is labelled "not in"). Other filters show their own editor.
- Cards and the Filters tool edit the same objects, so they always agree.
- ⋯ → **Show filter cards** hides them (`sheet.showFilterCards`).
- The operator list follows the field type (`opsFor`).

### Shared filters (P40)

- **Sharing.** A filter's **Apply on every dashboard** tick (in its context popup) moves it to the workbook's shared list (`sharedFilters`, at most **4**). Unticking moves it back to this dashboard.
- **Everywhere at once.** A shared filter shows on every dashboard's Filters tool with an **All dashboards** badge; editing it anywhere changes it everywhere.
- **Applied only where its table is already in the view** — it never forces a join. Where it isn't, the tool and the chart card's info line say so ("customers.country: shared, but not applied here — its table isn't in this view.").
- Histogram and box plot don't apply shared filters.

### Histogram and box plot

They are single-table views. They apply the filters that sit on their own table and show a notice counting the rest ("2 filters on other tables don't apply to a box plot").

## Click-to-filter

Clicking a chart mark **selects** its primary-dimension value into `sheet.selection`. Code: `chart.js` forwards the ECharts click; `selectHandler` / `toggleSelection` map `dataIndex` → the raw value.

A **selection chip** (`.ws-select`) offers:

- **Keep only** → `col = value` · **Exclude** → `col != value` · **✕** clear.
- **Legend clicks** (P29):
  - Clicking a legend item **highlights** that series; the others dim (ECharts `emphasis.focus: "series"`). Clicking it again clears.
  - When the legend lists a dimension's members — a Colour split, a Shape split, or a pie / donut's slices — the click also **selects** that member. The bar then offers Keep only / Exclude exactly as a mark click does.
  - A legend of measures only highlights.
  - The legend never hides series on click. ECharts' toggle is undone at once and the click is handed to the worksheet a tick later, so a re-render never disposes the chart mid-event.
- **Link action** (P39) — when the sheet has one (Format → **Link action**: a label and an `https://` address with `{value}`):
  - An **"<label> ↗"** button opens that address with the selected value URL-encoded into `{value}`, in a new tab with `noopener`. Nothing opens without that click.
  - Only `https:` links with a host are accepted. `http:`, `javascript:`, `data:` and the like are refused with the reason. A value can't change the host or break out of its slot.
  - One link action per sheet (`sheet.urlAction`). Rules: `Dashboard/action-model.js` (unit-tested).

How the action applies:

- It is a bound-parameter filter appended in `buildPlan` **only when the column's table is already in the query** — a click never forces a join.
- Exclude is a single-value `!=`. To exclude several members, use a `not in` filter.
- Clicking the same mark again clears it.
- Works on bar, stacked, line, area, combo, pie, donut and scatter (incl. colour-split). Other types and null values are no-ops.
- On a dashboard the same click filters the other widgets at once ([dashboards.md](../workbook/dashboards.md#cross-widget-filtering)).
- Why select-then-act: [D16](../../reference/decisions/decisions.md#d16--click-to-filter-is-a-select-then-act-worksheet-selection).

## Drill-down

The **Drill** tool takes ≥2 dimension fields **from one table** as an ordered hierarchy (year → quarter → month) on `sheet.drill`:

1. The **current level leads the group-by.** `buildPlan` prepends it as the first row dimension, so it drives the category axis.
2. Clicking a mark **drills one level finer**, pinning the clicked value. Every pinned ancestor is a bound `=` filter on the drill table (same table → never a join). An active drill takes clicks instead of selection.
3. A **breadcrumb** shows `All › 2023 › Q2`. Each crumb jumps up; **Up** goes up one level. Clicking at the finest level does nothing. Style: `.ws-drill`, `--warn` tint.

- A hierarchy holds at most **6** levels; a further add is refused with a toast.
- Editing the levels resets the descent.
- A hierarchy with no shelf fields renders an implicit-count chart of the current level.
- Why one table: [D17](../../reference/decisions/decisions.md#d17--drill-down-is-a-single-table-hierarchy-on-the-bound-param-path).

### Named hierarchies

A **named hierarchy** (T03-29) is a reusable drill path kept on the workbook: `{ id, name, levels: [{ db, table, column }] }`.

- **Rules:** 2–6 levels, all from one table, no repeated column (the same rules as the Drill tool). At most **20** per workbook. A name of 1–60 characters, unique case-insensitively.
- **Not allowed as a level:** a calculated field (the calc refusal text) or a field with a type cast ("A field with a type cast can't be a hierarchy level").
- **Managing them.** The sidebar's drill icon on a worksheet tab opens the Hierarchies dialog (`Dashboard/hierarchy-dialog.js`). Its own **+ New hierarchy** button starts a new one.
  - Each row has **Use** (sets the worksheet's drill levels), **Edit** and **Delete** (Delete confirms).
  - Editing: a name, a table, and an ordered level list built with an "Add a level" picker and per-level **Up / Down / Remove** buttons (labelled, keyboard-operable; focus stays on the control just used).
- **Applying.** **Use** on a dialog row **replaces the sheet's drill** with `{ levels, depth: 0, path: [] }` — the structure a hand-built drill has, each level carrying its column's category — so the chart, breadcrumb and click-to-drill behave identically.
- **The sheet gets a copy** of the levels. Renaming, editing or deleting the hierarchy later never changes a sheet that already used it.
- **Refusals.** A column cast after the hierarchy was made refuses with the cast message, and a column no longer in the table refuses too. The dialog's Edit keeps a level whose column has vanished until it is removed or replaced.
- Hierarchies are client-side only (the server never sees one) and save with the workbook ([workbook.md](../workbook/workbook.md)).

### Expand / collapse headers

In the Table and Text views, a Rows or Columns header that has a next level below it (every dimension but the last on its shelf) carries a **+ / −** button before its label.

- **Collapsing** hides every level below that header. The header stands for them as one row (or column, spanning the remaining header levels). The outermost collapsed header wins.
- **No button** on a last-level header or the measure band. The Dashboard widget draws a sheet's saved collapsed state but has no buttons — only the editor toggles.
- **Accessibility:** a real `<button>` with `aria-expanded` and an `aria-label` of "Collapse <header> (rows)" / "Expand <header> (columns)". The icon changes with the state, the header text beside it names the member, and focus returns to the button after the redraw.
- Code: `Dashboard/collapse-model.js`, drawn by `crosstabTable`.

- **Values stay correct.** A collapsed header's cells are its children's cells combined by the measure's own aggregation (`combine`, the rule the subtotals and grand totals use): sums and counts add; min / max take min / max.
  - An average, median, distinct count, percentile or table calculation cannot be rebuilt from its parts, so it shows "—". Nothing is re-aggregated in the browser.
  - Totals and the subtotal row read the full data, so they don't change. A first-level subtotal row is not drawn under a collapsed first-level header (the header's own row is that total).
- **No query.** Collapsing is presentation only: it redraws from the cached result (like a format change).
  - While the table is still paging, or the result was cut at its group limit, a collapsed cell (and a collapsed row's or column's total) reads "—" rather than a partial sum.
  - Colour scales and data bars are measured on the values shown, collapsed sums included.
- **State** is `sheet.collapsed = { rows: [key…], cols: [key…] }` (absent until a header is collapsed). It is saved with the workbook and restored on load ([workbook.md](../workbook/workbook.md)).
  - A key names the dimensions down to the header plus its member path, so re-ordering the shelves never collapses other members. A key whose members no longer exist is ignored.
  - Import keeps only string keys (≤ 200 per axis, each ≤ 600 characters) and reports the rest.
  - A click first prunes keys that match no current header. At 200 collapsed headers a further collapse is refused with a toast and nothing changes.
  - Undo / redo cover it (the sheet snapshot). Client-side only: the server never sees it.

## Pages

The **Pages** tool takes one dimension (`sheet.pages`).

- **Page control** (`.ws-pages`) below the shelves: shows the current member and count, with previous / next stepping (wrapping).
- **Play / Pause** autoplays every 1.5s — **omitted under `prefers-reduced-motion`**. The autoplay timer is cleared on view switch.
- **Filtering:** each page applies the current member as a bound `=` filter, only when its table is already in the query.
- **Members** come from the bounded distinct-values query (shared with `in`), capped at 200 with the same "more exist" notice. A load failure shows the server's message.

## Date range & comparison

The **Date range** tool (calendar icon, P35) takes one date / date-time field (`sheet.period`); anything else is refused with a toast. Its panel (`periodEditor`) picks:

- **Range** — Last 7 / 28 / 30 / 90 days (ending today), This / Last month, quarter, year, or **Custom** (two day pickers). Whole days, inclusive, in the browser's calendar.
- **Compare to** — No comparison, **Previous period** (the same number of days just before), **Same period last year** (29 Feb → 28 Feb) or **Custom**.

- **Default:** a new range is **Last 30 days vs previous period**.
- **Resolved days** show in the panel and the chart card's notice line ("1 Sept – 30 Sept 2026 vs 2 Aug – 31 Aug 2026"). An incomplete custom range says so and isn't applied.
- **Query:** the range is one bound `between` filter on the field (days for `Date`, `00:00:00`–`23:59:59` for `DateTime`). Like a filter, it may bring its table into the query.

### The comparison

The comparison is the same query over the comparison range. It is cached like any result; a failure toasts and the chart still draws. It shows on:

| View | Shows |
|---|---|
| **KPI** (no dimensions) — the scorecard | Under each value: ▲ / ▼ / ■ + signed % + "vs previous period", coloured `--up` / `--down` (good / bad) with an `aria-label`; the previous value in its tooltip. Format → **A fall is good** flips the tone. Format → **Target** (KPI) adds a progress bar and "78% of 40,000" under the first measure (✓ when met) |
| **Line / Area** | a dashed, faded line per measure, named "<measure> (previous period)" in the legend |
| **Bar** | a hatched, muted bar beside each bar, named in the legend |

- **Matching rows:** rows line up **by position** when the first group key is the range's own date field (day 1 with day 1). Otherwise they line up **by the same keys** (e.g. the same country).
- Other chart types apply the range only, and the panel says so.
- Rules: `Dashboard/period-model.js` (unit-tested).

## Member colours and palette order (T01-20, T03-33)

### Member colours

- **Editing.** Format → **Edit member colours** lists the members the drawn chart colours by a discrete field: Colour-shelf members on bar / stacked / line / area, pie / donut slices, and the categories of a single-measure bar with *Colour by category*.
  - Each row offers 24 fixed swatches (the three workbook palettes' light colours) and **Reset**.
  - **Reset all for this field** below the list also removes colours of members no longer in the view (which still count toward the cap).
  - The list stays open across redraws and is disabled until such a chart is drawn.
  - Legend clicks are unchanged (highlight / select).
- **Stored** as `sheet.memberColors = { "<table>.<column>": { "<member>": "#rrggbb" } }`. This is workbook data, so a validated hex, not a token. The member key is the raw value as text (`null` has its own key), so a colour survives a change of number / date format.
- **Limits** ([api.md](../../reference/api.md#limits), client-side only): 100 members per field, 20 fields, member key ≤ 100 chars, field key ≤ 200.
  - Maps are null-prototype, so a member named `constructor` or `__proto__` is an ordinary key; an imported `__proto__` is dropped and reported.
  - Invalid entries are dropped on import and reported. Workbooks without the key load with `{}`.
- **Not covered:** a calculated field cannot be member-coloured; scatter groups and treemap / funnel are not yet wired.
- **Contrast.** User colours are not adjusted. Label inks still come from `Dashboard/contrast.js` (`pickInk`), which picks the higher-contrast ink for any hex.
- Code: `Dashboard/colour-model.js` (`setMemberColor`, `cleanMemberColors`, `colorsByName`, `orderedPalette`, `rampStops`, `SWATCHES`).

### Palette and colour scale

- **Reverse palette** (`format.paletteReverse`, boolean, default off) reverses the eight categorical colours' order and swaps the continuous ramp's ends (heatmap and scatter colour). Member colours are unaffected.
- **Continuous colour scale** (T03-19; Format, on Scatter and Heatmap):
  - **Colour ramp** — Brand (accent soft → accent), Blue, Green, Amber or Violet (the surface blended 20 % toward that categorical token, up to the token). `format.colorRamp`, default `brand`.
  - **Colour from / to** (`format.colorMin` / `colorMax`; blank = the data's own end) pin the ends of the scale. A value beyond a pinned end takes that end's colour (it saturates; nothing is greyed out). While a pin is active the legend reads "beyond range: end colour".
  - The controls show on a Heatmap, and on a Scatter only while a numeric field is on Color.
  - A minimum not below the maximum is refused with a toast; a saved one is cleared on import and reported.
  - An unpinned heatmap uses its plain data span. Reverse palette still swaps the ramp's ends.
  - Table cell scales have their own conditional-formatting colours and are unaffected.
  - Code: `Dashboard/colour-scale-model.js` (`RAMP_CHOICES`, `rampColours`, `mixHex`, `colourRangeError`, `rangeOf`).

### Table look (T01-23)

Format → Align · Row height · Shading, in the Table and Text views only. Stored as `format.tableAlign` `auto` | `left` | `center` | `right`, `tableDensity` `standard` | `compact` | `roomy`, `tableShade` `none` | `banded` | `header` | `both`.

- **Align** sets the value cells and measure headers. Auto keeps numbers right; the "Total" header follows too.
- **Row height** sets cell padding: Compact 0 vertical (the one deliberate step outside 4 / 8 / 16 / 24, golden-rule 2), Standard 4 / 8, Roomy 8 / 16.
- **Shading:** Banded shades even body rows (subtotal and grand-total rows count in the alternation); Header shades the header cells. Both use `--surface-3`, a step that reads in light and dark.
  - Banding skips cells carrying a rule or scale (`.xt-cf`), so their tone wins. Header shading keeps each header's own ink.
- All three are classes on the table (`xt-a-*`, `xt-d-*`, `xt-s-*`; defaults add none). There is no free font, size or colour.
- Code: `Dashboard/table-style-model.js` (`tableStyleClasses`, `TABLE_*_CHOICES`).
