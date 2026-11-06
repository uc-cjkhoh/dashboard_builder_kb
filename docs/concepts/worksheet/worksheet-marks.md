---
components: [src/DashboardBuilder/Features/Core/format.js, src/DashboardBuilder/Features/Core/icons.js, src/DashboardBuilder/Features/Dashboard/chart.js, src/DashboardBuilder/Features/Dashboard/colour-model.js, src/DashboardBuilder/Features/Dashboard/colour-scale-model.js, src/DashboardBuilder/Features/Dashboard/contrast.js, src/DashboardBuilder/Features/Dashboard/font-model.js, src/DashboardBuilder/Features/Dashboard/pill-options.js, src/DashboardBuilder/Features/Dashboard/table-style-model.js, src/DashboardBuilder/Features/Dashboard/toolbar-rules.js, src/DashboardBuilder/Features/Dashboard/tooltip-dialog.js, src/DashboardBuilder/Features/Dashboard/tooltip-model.js, src/DashboardBuilder/Features/Dashboard/tooltip-style.js]
---
# Worksheet marks — Marks card, member colours, table look

What each Marks slot accepts and how it renders, plus member colours and the palette. Part of the worksheet encodings ([worksheet-encodings.md](worksheet-encodings.md)); base worksheet: [worksheet.md](worksheet.md).

## Marks slots

The Marks group sits at the top of the field pane and collapses like the other groups. It is a grid of **three columns** of slots: Color, Size, Label, Detail, Tooltip, Shape, Path, Angle, Filters, Date range, Drill, Pages.

- **Every tool is always reachable** (there is no More menu). Tools the chart type doesn't use are **quiet** (dimmed) unless they hold fields: Size / Shape outside scatter, square, circle; Path outside line, area; Angle outside pie, donut; Detail, Drill and Pages by default.
- **A slot** is an icon over its name. It shows a **count badge** when it holds fields and is a **drop target** (drag a field straight onto it).
- **Click a slot** to open **one** editor, with its pills over a drop zone. It is a **flyout** (`.ws-toolfly`) that opens just right of the field pane, level with the slot but below the Columns and Rows lanes, so a field is one short drag away, the chart never shifts, and the lanes stay uncovered. At most one editor is open at a time.
  - Keyboard focus moves into the flyout when a slot is pressed; **Esc** or ✕ closes it and returns focus to the slot. Pressing the slot again also closes it.
  - Pressing the chart puts the flyout away (the press still reaches the chart); the field pane, lanes and the flyout itself are left alone, since fields are dragged from and to them.
  - Each editor has an **Add field** button (**Replace field** on a one-field slot that is full): a searchable list of the pane's fields, grouped by table, filtered to what the slot takes (Size numeric, Date range temporal). Choosing one goes through the slot's own drop handler, so rules and messages match a drag. It is the click and keyboard path.
  - A hairline separates what the slot holds from its own editor: **Date range** (full-width range and compare selects), **Tooltip** (the text, an **Edit tooltip…** link beside its label, a preview), and **Filters**, whose filter cards (values, bounds, checklists) are repeated in the flyout while it is open so they are never hidden behind it (the header's copy stays invisible and inert, keeping its height, so the chart does not shift).
  - The calculation and field-choices editors opened from a pill stay inline under the lanes.
- Code: `.ws-shelf--marks`; `buildTools` / `toolButton`; `markGrid` in `Dashboard/pill-options.js` chunks the slots into rows of three. `visibleTools(chartType, tools)` (`Dashboard/toolbar-rules.js`, pure) decides which are quiet. The editor panel is `toolPanel` (`.ws-toolpanel`); `fieldPicker` builds the Add field list from the field pane's chips (`data-field`). Icons come from `Core/icons.js`.

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
- **Keeping styles on their lines:** clearing the text clears the style; applying trims leading / trailing blank lines with their styles; editing the plain **Tooltip text** box keeps styles (re-aligned by line index) only while the line count is unchanged, otherwise clears them and says so. A template of more than 12 lines (from the plain textarea) opens with Apply blocked and the reason shown.
- **Field formats** (a **Field formats** group under the lines, one row per `<field>` in the template that can be formatted):
  - A measure gets a **Number format** (View format, Auto, Compact, Currency, Percent) and **Decimals** (auto, 0-10); a date group-by (its sample parses as a Date / DateTime) gets a **Date format** (View format, Date, Date and time, Month, Year). Other group-bys get no row. "View format" = today's behaviour.
  - They reuse the worksheet Format code (`makeValueFormatter` / `makeCategoryFormatter`, `Core/format.js`), starting from the view's format (a currency symbol still applies). The preview and every chart tooltip that renders the template (cartesian, pie / donut, scatter without Shape) format from the raw value through `tipLookup` (`Dashboard/tooltip-formats.js`).
  - Stored as `tooltipFormats` `{ [field]: { number?, decimals?, date? } }`, only for fields still in the template (the key exists once one is formatted). `checkTooltipFormats` on import: known values only, decimals an integer 0-10, at most `LIMITS.tooltipFormats` = 24 fields, names ≤ 200 characters; an invalid spec is dropped with an issue, never clamped; ignored without a template.
  - Not built: styling a single field token or word inside a line (style stays per line).

### Marks rules

- Extra measures never become chart series. With no marks set, the plan is byte-identical to a plain shelves plan.
- **Colour split needs one measure:** multi-measure + Colour → a hint. Types outside `COLOR_USES` (pie, donut, scatter, combo, KPI) show a note and ignore the Colour pill.
- Colour × category combinations are still capped by the query `LIMIT`.
- Every unmet mapping shows a **hint, not an error**.

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
  - **Colour scale** (`format.colorScale`, default `sequential`) — Low → high, or Diverging: warm (`--chart-div-low`, orange) below a centre, the surface at it, cool (`--chart-div-high`, blue) above; the pair is theme-stable ([tokens.md](../../reference/design/tokens.md)) and shared with the table scale. The centre is bounded to ±1e15 (a toast refuses more; a saved one is cleared on import). Switching back to Low → high keeps the centre for later. **Colour centre** (`format.colorCentre`, blank = 0 when the data straddles it, else the middle) replaces the Colour ramp control while Diverging. The scale's ends are made symmetric about the centre (the larger distance from it, after any pins) so the middle colour sits on the centre; the legend names it in words ("centre 20"). Reverse palette swaps warm and cool. **Colour from / to are hidden while Diverging** (the ends follow the centre; a stored pin is kept but ignored, and returns with Low → high), so no "beyond range" note shows.
  - **Colour ramp** (Low → high only) — Brand (accent soft → accent), Blue, Green, Amber or Violet (the surface blended 20 % toward that categorical token, up to the token). `format.colorRamp`, default `brand`.
  - **Colour from / to** (Low → high only; `format.colorMin` / `colorMax`; blank = the data's own end) pin the ends of the scale. A value beyond a pinned end takes that end's colour (it saturates; nothing is greyed out). While a pin is active the legend reads "beyond range: end colour".
  - **Steps** (`format.colorSteps`, default 0 = Continuous): 3 to 9 discrete colour steps instead of a gradient, on either scale (heatmap and scatter). The range (data span, pins, or the symmetric diverging span) is cut into equal steps; each step takes the ramp colour sampled evenly from end to end (the first and last steps equal the ramp's ends; an odd Diverging count puts a neutral on the centre step: the surface nudged 15 % toward the ink, so it reads as a swatch in both themes; stepped heatmap cells get a `--chart-axis` hairline instead of the surface one, so a pale step is not mistaken for a gap). The outer steps are open-ended, so a pinned range still saturates; a value on a boundary belongs to the step above it; flat data (one value) is widened by 1 so the steps stay distinct. The legend becomes a row of swatches labelled with their boundaries in words ("24 to 38"); the centre / "beyond range" note sits above it. A value outside 0, 3 to 9 is reset to Continuous on import and reported, never clamped.
  - The controls show on a Heatmap, and on a Scatter only while a numeric field is on Color.
  - A minimum not below the maximum is refused with a toast; a saved one is cleared on import and reported.
  - An unpinned heatmap uses its plain data span. Reverse palette still swaps the ramp's ends.
  - Table cell scales have their own conditional-formatting colours and are unaffected.
  - Code: `Dashboard/colour-scale-model.js` (`RAMP_CHOICES`, `SCALE_CHOICES`, `rampColours`, `divergingColours`, `divergingRange`, `STEP_CHOICES`, `colourStepsError`, `stepColours`, `stepBounds`, `stepPieces`, `colourCentreError`, `mixHex`, `colourRangeError`, `rangeOf`).

### Table look (T01-23)

Format → Align · Row height · Shading, in the Table and Text views only. Stored as `format.tableAlign` `auto` | `left` | `center` | `right`, `tableDensity` `standard` | `compact` | `roomy`, `tableShade` `none` | `banded` | `header` | `both`.

- **Align** sets the value cells and measure headers. Auto keeps numbers right; the "Total" header follows too.
- **Row height** sets cell padding: Compact 0 vertical (the one deliberate step outside 4 / 8 / 16 / 24, golden-rule 2), Standard 4 / 8, Roomy 8 / 16.
- **Shading:** Banded shades even body rows (subtotal and grand-total rows count in the alternation); Header shades the header cells. Both use `--surface-3`, a step that reads in light and dark.
  - Banding skips cells carrying a rule or scale (`.xt-cf`), so their tone wins. Header shading keeps each header's own ink.
- All three are classes on the table (`xt-a-*`, `xt-d-*`, `xt-s-*`; defaults add none). There is no free font, size or colour.
- Code: `Dashboard/table-style-model.js` (`tableStyleClasses`, `TABLE_*_CHOICES`).

### Worksheet font (T01-23)

Format → Font on every chart type and on Table / Text. Stored as `format.font` `default` | `serif` | `mono` (default `default`).

- A fixed list of system stacks, nothing downloaded and no font file vendored (golden-rule 10): Default is the app's `--font`; Serif is `--font-serif` (Charter, Sitka, Cambria, Georgia); Monospace is `--font-mono`. Both tokens are in `core.css`.
- It changes the family only; sizes stay on the 14 / 16 px scale.
- A chart reads the token into its text styles (axes, legend, labels, tooltip); a table takes the class `xt-f-serif` / `xt-f-mono` (the default adds none).
- KPI cards, the worksheet title and the toolbars keep the app font.
- Code: `Dashboard/font-model.js` (`FONT_CHOICES`, `fontToken`, `fontClass`); `FONTS` in `Core/sheet-schema.js`.
