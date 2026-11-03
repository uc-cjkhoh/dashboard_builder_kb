---
components: [src/DashboardBuilder/ClickHouse/TypeCast.cs, src/DashboardBuilder/Features/Dashboard/cast-model.js, src/DashboardBuilder/Features/Dashboard/member-labels.js]
---
# Field settings: data type cast and member labels

Per-field settings from a field's context popup in the worksheet field pane ([worksheet.md](worksheet.md#field-pane-basics-p28)). Both are stored per workbook in `fields` (store `fieldMeta`).

## Data type cast (T02-34)

The popup also has **Data type**: *Original*, or the casts that make sense for the column (`castChoices`) — text → Number / Date; number or date → Text; boolean → Text / Number; anything else → Text. The setting is `cast`: `text` | `number` | `date`.

- **The server converts in the query**, so the field groups, aggregates, filters and ranks (Top-N) as its new type.
- **A value that doesn't fit becomes empty (NULL)**, never an error. Filters on it therefore drop it (`notin` keeps it).
- **The field takes the new category everywhere.** It moves to Dimensions / Measures, offers that type's aggregations, operators and date parts, and shows an **as Number** tag (icon + text) on its chip and pills. Changing a cast re-categorises the pills, filters, drill levels and shared filters that read the field (`syncCastCategories`).
- **Not supported:** calculated fields have their own type and take no cast. Histogram and box plot don't support a cast field yet (a hint, no request).
- **Stored values still show in places:** the filter value picker lists the stored text. View data leaves out filters and a selected mark on a cast field (it reads stored values) and says so.
- Code: `Dashboard/cast-model.js`, `ClickHouse/TypeCast.cs`.

## Member labels (T02-29)

**Edit member labels…** (not offered on date fields) opens a dialog listing the field's top members — the bounded distinct-values read, first 200 — with one label input each.

- **Input rules:**
  - A label is ≤ 80 characters. Blank, or equal to the value, means no label.
  - Labels are **unique within a field**. A label equal to another member's label or raw value is refused, naming that member. A file with such labels opens with the first kept and the rest dropped and reported.
  - A value over 100 characters can't be labelled.
  - **Reset all** clears them. Enter moves down the list; Esc discards.
- **Stored** as the field setting `memberAliases` (`{ [rawValue]: label }`, ≤ 200 entries, key ≤ 100 characters; `Dashboard/member-labels.js`).
- **Display only.** Queries, grouping, sorting, filters, drill and selections keep the raw value.
- **Where a label shows**, each **by key position** (`withMemberLabels`: two fields may label the same raw value differently):
  - category axes, pie slices and legends, colour-split series;
  - heatmap / treemap / Sankey / small-multiples labels;
  - tooltips — the default head, the template's `<table.column>` field and Tooltip fields, all still HTML-escaped;
  - crosstab headers and the Label mark.
- **Filters:** a filter card / `in` picker shows the label with the raw value as secondary text and title. Ticking a member stores the raw value.
- **Chips:** a click-selection chip, the legend selection chip, the drill breadcrumb and the dashboard filter chip name the member by its label when it is picked. The stored label text does not follow a later edit.
- **Unaffected:** member colours stay keyed by the raw member. CSV export and View data carry raw values (and group names), never labels.
- **Not labelled:** calculated or group dimensions, date-part keys, bucketed numeric keys, NULL, Pages.
- Maps are null-prototype objects read with own-key checks, so a member called `constructor` or `__proto__` is an ordinary member.
