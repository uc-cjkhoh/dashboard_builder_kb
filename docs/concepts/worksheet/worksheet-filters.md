---
components: [src/DashboardBuilder/Features/Core/validate.js]
---
# Worksheet filters

Filter cards: column + operator + bound typed value, calculated fields as filters, parameters and shared filters. Part of the worksheet encodings ([worksheet-encodings.md](worksheet-encodings.md)); base worksheet: [worksheet.md](worksheet.md).

## Filters

Each Filters pill is a column + operator + value. Every value is a **bound typed parameter** ([golden rule 3](../../development/coding-standards.md#3-bind-every-value-bound-every-result)).

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

### Calculated fields as filters

A **row-level calculated field** dropped on Filters is a filter on its value ([D82](../../decisions/decisions-filters.md#d82--a-calculated-field-is-a-row-filter-applied-before-grouping)): the same pill, operators (not `top`, and not `in the` for a date) and bound typed values, coerced by the calculation's type. Members for `in` / `not in` come from a one-dimension query of the calculation (≤ 200 shown). It is a `WHERE` condition, so rows are filtered **before** grouping, ranking and table calculations. An **aggregate** calculation is refused (toast and 400). It can't be shared, doesn't apply to a histogram or box plot (counted in their notice) and is left out of "View data".

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
- **Band ends:** a typed Band's **from** and **to** can each follow a number parameter (`analytics.band.fromParam` / `toParam`; the ends swap if they cross, equal ends draw nothing). Deleting a parameter (Parameters dialog) first asks, listing every reader it will unlink; it then clears every reference a worksheet or shared filter holds to it (filters, Top N, reference line, band ends, parameter action) — each keeps its own typed value, so results may change, and the delete is not an undo step. Unbinding a band end keeps the parameter's current value as the typed number, and opening a workbook drops a saved link whose parameter is missing — ids are reused after a reopen, so a stale one would otherwise bind to an unrelated new parameter.

### Filter on a measure (T03-27, [D84](../../decisions/decisions-filters.md#d84--a-filter-on-an-aggregated-measure-having-keeps-groups-after-grouping))

A row filter cuts rows before grouping; a **measure filter** cuts whole groups after their value is worked out — "only regions whose total sales are at least 1000".

- **Add it:** right-click (or the keyboard context-menu key on) a measure pill on Rows / Columns → **Keep groups where *sum amount*** → pick the condition (`equals`, `is not`, `is greater than`, `is at least`, `is less than`, `is at most`, `is between`) and type the number (two for between). **Clear** removes it. Tab reaches the condition and the number; each has an accessible name.
- **See it:** the pill gets a badge with a funnel icon and the condition (`≥ 1000`, `10 – 30`); the info line under the view says it in words with its grain — "Showing only groups where sum amount is at least 1000, per region." (no dimensions: "Showing only the total when …"). A number that isn't one is marked in the popup, the badge reads "not applied" with a warning icon, and nothing is sent for it.
- **How it composes:** `WHERE` → Top-N → group → measure filter → sort → cap or page. The cap and the table's "of N rows" count only passing groups; a Top-N ranks first, so it may show fewer than N; several measure filters are `AND`ed (at most 10); a measure filter drops the Other bucket (the request would be rejected with it). The popover *How this is computed* names it at the Aggregates stage.
- **Which measures:** the Rows / Columns shelf measures (plain or calculated, any aggregation). Not Size / Colour / Label measures; not applied to a histogram or box plot (the line says so). Saved with the workbook on the pill (`having`).
- **Range slider** ([D87](../../decisions/decisions-filters.md#d87--the-measure-filter-range-slider-reads-its-span-from-the-drawn-result)): with **is between** chosen and numbers in the drawn result, two sliders (From, To; each named) sit above the boxes over the measure's span. Dragging fills the boxes, releasing applies after a short pause; the thumbs never cross. The span is the widest seen for that measure (same field, aggregation and grouping) on that sheet, so narrowing doesn't shrink the track; a new aggregation or grouping starts afresh and is forgotten on **Clear**. No numbers drawn, or all equal: no slider, the boxes still work.
- **Not yet:** a filter on a measure that isn't on the view, a filter shared across dashboards, and one on a Top-N ranking measure.

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

They are single-table views. They apply the filters that sit on their own table and show a notice counting the rest ("2 filters on other tables or calculated fields don't apply to a box plot").
