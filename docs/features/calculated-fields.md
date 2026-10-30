# Calculated fields

A **calculated field** is a named formula over fields of the data model, used like a field:
`SUM([orders.amount]) / SUM([orders.qty])` on a shelf, in a mark slot, in a Top-N rank. The browser keeps
the formula text; before a query it expands and type-checks the formula into a tree that ClickHouse
computes on the read-only, bounded path ([clickhouse-integration.md](../reference/clickhouse-integration.md#calculated-fields--the-compile-path),
wire shape in [api.md](../reference/api.md#calculated-fields-calc)). Code: `Features/Calc/`
([frontend-modules.md](../reference/frontend-modules.md)); the dialog and pane group are wired from
`Dashboard/dashboards.js`. Rationale: [decisions.md](../reference/decisions.md) D26–D47.

## Formulas

- Grammar: `expr := and ("OR" and)*`; `and := not ("AND" not)*`; `not := "NOT" not | compare`;
  `compare := sum [("="|"!="|"<>"|"<"|"<="|">"|">=") sum]` (no chaining); `sum := term (("+"|"-") term)*`;
  `term := factor (("*"|"/") factor)*`;
  `factor := "-" factor | number | string | "(" expr ")" | aggregate | logic | ref`; `string := "'" text "'"`; `aggregate := FN "(" expr ")" | "PERCENTILE" "(" expr "," number ")"`;
  `ref := "[" name "]" | "[@" parameter "]"` (a workbook parameter, see Parameters below). Numbers are decimals with an optional exponent (`12`, `1.5`, `.5`, `1.`, `1e3`; no
  `1,000`; a non-finite `1e999` is an error). `SUM`/`AVG`/`MEDIAN`/`STDDEV`/`VARIANCE`/`PERCENTILE` take a number; `MIN`/`MAX` a number, date or text;
  `COUNT`/`COUNTD`/`ATTR` any type; arithmetic needs numbers; an aggregate inside an aggregate is refused. A field of
  a category other than numeric, text, temporal or boolean can't be used.
- **Logic** ([below](#logic-functions)): comparisons, `AND` / `OR` / `NOT`, `IF` / `IIF` / `CASE`, `IFNULL`, `ISNULL`, `ZN`, text literals.
- **Text** ([below](#text-functions)): `LOWER`, `UPPER`, `TRIM`, `LEN`, `LEFT`, `RIGHT`, `REPLACE`, `CONCAT`, `CONTAINS`, `STARTSWITH`, `ENDSWITH`, `SPLIT`. A text or number field's menu **Clean…** (query-time cleaning; the data is never changed) adds ONE calculated field: text **Trim spaces** (`TRIM`), **Replace missing (NULL) values** (`IFNULL(f, 'text')`, or `IFNULL(f, 12.5)` on a number; it replaces NULL only, not an empty string), **Recode values** (`old = new` lines, up to 20, cut at the first `=`; `CASE f WHEN 'old' THEN 'new' … ELSE f END`, unlisted values kept unless unticked, the formula within 500 characters) and **Read as a date** (`DATE(f)`); named `<field> (trimmed|filled|recoded|date)`, then ` 2`… when taken; a date field has no Clean… (no date literal), nor does a field whose names hold `.`, `[` or `]`.
- **Date** ([below](#date-functions)): `DATEDIFF`, `DATEADD`, `YEAR`, `MONTH`, `DAY`, `QUARTER`, `WEEK`, `WEEKDAY`, `DATE`.
- Operators `+ − * /`, parentheses, numbers, and the aggregates `SUM`, `AVG`, `MIN`, `MAX`, `COUNT`,
  `COUNTD`, `MEDIAN`, `STDDEV`, `VARIANCE`, `PERCENTILE`, `ATTR` (function names are case-insensitive). The
  function table lives in `calc-types.js`.
- **Statistics:** `MEDIAN([f])` is the exact median of the non-NULL values (linear interpolation between the two
  middle values, like Excel `PERCENTILE.INC`: 1, 2, 3, 4 gives 2.5); `PERCENTILE([f], p)` is the same interpolation at fraction `p` (p25 of 1..4 is 1.75)
  (a **literal** number 0..1, not a field or a formula; `PERCENTILE([f], 0.5)` equals `MEDIAN`, 0 the minimum, 1
  the maximum); `STDDEV` and `VARIANCE` are the **sample** statistics (n − 1). `STDDEV`/`VARIANCE` of fewer than
  two values, and `MEDIAN`/`PERCENTILE` of no value, are empty (NULL, shown as a dash), never 0 or NaN. A percentile of a plain
  field needs no formula: the pill's `Percentile…` aggregation ([worksheet.md](worksheet.md#shelves--pills)) runs the same SQL; a calculated pill does not list it.
- **`ATTR([f])`** (Tableau's attribute) is the value when the group has exactly one distinct non-NULL value,
  else empty (NULL — Tableau shows `*`; here a dash). NULLs are ignored, so a group of `p, p, NULL` is `p`.
  It keeps the field's type, so a text field stays a text measure (table, text and KPI views only).
- A **reference** is `[table.column]` (`[db.table.column]` when two databases hold the same table name) or
  `[Name]` for another calculation. Calculations can refer to calculations; the browser expands every
  reference into one tree before sending, so the server never sees a calculation name.
- Division by zero gives an empty (NULL) value, never an error.
- A formula with no field references (`1+2`) is valid. It needs a field from a table elsewhere on the sheet
  to have anything to group or total.

### Logic functions

- **Text literal** `'open'`: a quote inside is doubled (`'it''s'`); at most 100 characters; it is sent as data, never
  as SQL text. There are no date or boolean literals (compare two date fields; use a boolean field as a condition).
- **Comparison** `= != <> < <= > >=` (`<>` is `!=`) takes two numbers, two texts or two dates, never a mix and never a
  boolean (`Comparison needs two values of the same type — …`). Text compares exactly (case and accents count).
  Precedence, loosest first: `OR`, `AND`, `NOT`, comparison, `+ -`, `* /`; `1 + 2 > 2` works unparenthesised.
- **`AND` / `OR` / `NOT`** need booleans (a comparison, `ISNULL`, a boolean field) and give a boolean.
- **`IF(cond, a, b)`** (also `IIF`) and **`CASE WHEN c THEN a [WHEN …] [ELSE d] END`**; the simple form
  `CASE [f] WHEN 'x' THEN a … END` tests `[f] = 'x'` (the subject is copied into every arm, so each arm costs its nodes
  again against the node limit). Conditions are booleans; every THEN and the ELSE must have
  **one type** (number, text, date or boolean), else `All results must be the same type — … is text, not number.` at the
  offending branch. The first true WHEN wins. A CASE with no ELSE is empty (NULL) when nothing matches.
- **`IFNULL(a, b)`** is `a`, or `b` when `a` is empty (same type); **`ZN(a)`** is `IFNULL(a, 0)`; **`ISNULL(a)`** is true
  when `a` is empty. Division by zero is still empty, so `IFNULL(a / b, 0)` repairs it.
- **NULL:** a condition that is NULL counts as not true — `IF` takes its else, `CASE` tries the next WHEN. A comparison
  with NULL is NULL (shown as a NULL group, not `false`), `AND`/`OR`/`NOT` are three-valued (`NULL AND false` is
  `false`, `NULL OR true` is `true`, `NOT NULL` is NULL). Aggregates still skip NULLs.
- **Aggregate or row-level:** an `IF`, `CASE`, comparison or `IFNULL` is an aggregate calculation when any part is an
  aggregate and every other part is an aggregate or a constant (`IF(SUM([a]) > 100, 'high', 'low')`); a row-level
  part beside an aggregate is the usual mixing error. `SUM(IF([s] = 'open', [amount], 0))` is a conditional sum.
- Not built: the keyword form `IF c THEN a ELSEIF … END` (write `IF(…)` or `CASE`), date and boolean literals, `NULL`
  as a word (use `ISNULL`), `IN`, `BETWEEN`.

### Text functions

Row-level functions over text (names are case-insensitive; the table is `ROW_FUNCTIONS` in `calc-types.js`). Each argument
that is text may be any text expression: a field, a literal, or another function. Every other argument is a **literal written
in the formula**, never a field or a computed value.

| Function | Result | Meaning |
|---|---|---|
| `LOWER(t)` / `UPPER(t)` | text | change case, accents and non-Latin letters included (`UPPER('straße')` is `STRASSE`) |
| `TRIM(t)` | text | remove leading and trailing spaces (the space character only; tabs and line breaks stay) |
| `LEN(t)` | number | length in **characters**, not bytes (`LEN('日本語')` is 3) |
| `LEFT(t, n)` / `RIGHT(t, n)` | text | the first / last `n` characters; `n` is a whole number 0 to 1000; longer than the text gives the whole text, 0 gives an empty text |
| `REPLACE(t, from, to)` | text | every occurrence of `from` replaced by `to`; case-sensitive; an empty `from` changes nothing; `from` and `to` may be fields (pinned live) |
| `CONCAT(a, b, …)` | text | two to ten texts joined; empty if any is empty (wrap a part in `IFNULL(x, '')` to keep the rest) |
| `CONTAINS(t, s)` / `STARTSWITH(t, s)` / `ENDSWITH(t, s)` | boolean | **case-sensitive** match (`LOWER` both sides for a case-insensitive one); an empty `s` is always true |
| `SPLIT(t, sep, k)` | text | the `k`-th piece (1 is the first) of `t` cut at `sep`; `sep` is text of 1 to 20 characters, `k` a whole number 1 to 1000; empty when there is no `k`-th piece; an empty text has one empty piece; two neighbouring separators leave an empty piece. A text field's menu **Split…** asks for a separator (1–20 characters) and 2–10 pieces, then adds one calculated field per piece (`tags 1`, `tags 2`, … = `SPLIT([db.table.tags], ',', k)`), stopping at the 20-field limit; a field whose names hold `.`, `[` or `]` can't be split |

- **Empty in, empty out:** a NULL text gives NULL from every function (`LEN`, `CONTAINS` too), so `IFNULL(x, …)` first when a
  default is wanted. There is no `+` on text; use `CONCAT`. A negative, fractional, field-valued or over-limit length or
  position is an error naming the function, not a silent clamp (`LEFT's length must be a whole number from 0 to 1000 written in the formula.`).
- **Types:** a number or boolean where text is needed reads `LOWER needs a text — orders.amount is number.` at the argument; a wrong
  argument count reads `LEFT takes 2 arguments.` (`CONCAT takes 2 to 10 arguments.`).
- **Row-level, aggregates as usual:** `COUNTD(LOWER([c.name]))` and `SUM(IF(CONTAINS([c.name], 'x'), 1, 0))` work; a text
  function over an aggregate (`LOWER(MAX([c.name]))`) is an aggregate; mixing with a bare row-level field is the usual error. A row-level text
  or boolean result (`LOWER`, `CONTAINS`) is a **dimension**; `LEN` is a row-level number (measure or dimension).
- Not built: regular expressions, `FIND` / `POSITION`, `MID` / `SUBSTRING`, `LTRIM` / `RTRIM`, `STARTSWITH`/`CONTAINS` ignoring case, a length, position or separator
  that is a field or computed value (a `[@Parameter]` works, see Parameters).

### Date functions

Row-level functions over dates (same `ROW_FUNCTIONS` table and generic `fn` node as text). A *date* argument is any date or
date-time expression: a field, `DATEADD(…)`, `DATE(…)`. A text argument is refused (`YEAR needs a date — orders.status is text.
Use DATE() to turn text into a date.`); so is a number. A NULL date gives NULL from every function.

| Function | Result | Meaning |
|---|---|---|
| `DATEDIFF(unit, d1, d2)` | number | `d2` minus `d1`, in whole `unit`s, counted as **calendar boundaries crossed**: `DATEDIFF('month', 31 Jan, 1 Feb)` is 1 and `DATEDIFF('year', 31 Dec, 1 Jan)` is 1; negative when `d2` is earlier; weeks start on Monday (Tableau's default week starts on Sunday, so a `'week'` difference can differ from Tableau's by one around a Sunday) |
| `DATEADD(unit, n, d)` | date | `d` moved by `n` units; a month or year step past the end of a shorter month lands on its last day (31 Jan + 1 month is 29 Feb 2024; 29 Feb 2024 + 1 year is 28 Feb 2025). The result may be later than a `Date` column's own 2149 limit; it is **NULL** when it falls outside 1900-01-03 to 2299-12-29 (never a wrapped or clamped date) |
| `YEAR(d)` / `MONTH(d)` / `DAY(d)` / `QUARTER(d)` | number | the calendar year, month 1-12, day of the month 1-31, quarter 1-4 |
| `WEEK(d)` | number | the **ISO 8601 week** 1-53 (weeks start Monday; week 1 holds the year's first Thursday, so 31 Dec 2020 and 1 Jan 2021 are week 53 and 30 Dec 2024 is week 1) |
| `WEEKDAY(d)` | number | ISO day of the week: **Monday 1 to Sunday 7** (Tableau's `DATEPART('weekday')` counts Sunday as 1, so `WEEKDAY(d) = 7` is a Sunday here) |
| `DATE(t)` | date | the text `t` read as a calendar date (`2024-03-05`, `20240229`, `2024-03-05 10:30:00`); NULL when it is not one. The time of day is dropped |

- **Unit and amount are literals written in the formula.** The unit is a **text literal** (`'day'`, any case) from `year`, `quarter`,
  `month`, `week`, `day`, `hour`, `minute`, `second`; anything else (a field, a number, another word) is an error listing them. The
  `DATEADD` amount is a whole number from -100000 to 100000 (`-7` is fine), never a field or computed value; out of range is an
  error, not a clamp (as `LEFT`'s length, [D54](../reference/decisions-calculated-fields.md#d54--length-position-and-separator-are-literals-rejected-out-of-range)).
- **Date versus date-time:** the engine's *date* type covers both. On a date-time column `DATEDIFF('hour', …)` counts hour
  boundaries (22:30 to 01:00 next day is 3) and `DATEADD('hour', …)` keeps the time of day. On a plain date column a time unit
  reads midnight to midnight (`DATEDIFF('hour', 1 Jan, 2 Jan)` is 24) and `DATEADD('hour', 5, d)` becomes a date-time at 05:00. A
  date-time at midnight displays as a date, as everywhere in the app. The server's own time zone applies to date-time columns
  without one.
- **`DATE(t)` rules:** the same guard as the date type cast: text made only of digits, spaces, signs, commas and dots is NULL unless it is
  `YYYYMMDD` (`'12345'` is NULL, not the 5th of this month); an impossible day (`2024-02-30`), a word, and a year outside 1970 to
  2148 are NULL, never a clamped date.
- **`WEEK` is not the week date part:** the date part and bucket "week" on a plain date field is the **Monday that starts the week**
  (a date); `WEEK(d)` is the ISO week *number*. Weeks 52/53 and 1 can belong to the neighbouring ISO year, and there is no `ISOYEAR`
  yet, so group by `YEAR` plus `WEEK` only away from the year turn.
- **Bucketing a calculated date:** a calculated `DATEADD` / `DATE` dimension groups **per distinct value**; it is never date-bucketed or given a date part
  (a calculated dimension takes no `datePart` or `dateBucket`, E12). To group by month or year, use `YEAR` / `MONTH` / `QUARTER` of it (a number dimension).
- **Roles:** the number functions give a row-level number (a measure or dimension, `SUM(WEEK([o.placed]))` works); `DATEADD` and `DATE`
  give a date dimension (`MIN`/`MAX` take it); `IF(MONTH([o.placed]) = 12, …)` and `DATEDIFF(…) > 30` work.
- Not built: `TODAY()` / `NOW()` (a result would change between runs, which breaks caching), `MAKEDATE`, fiscal calendars and fiscal year start,
  `ISOYEAR`, date-part bucketing of a calculated date, `DATENAME` / `DATETRUNC`, a unit, amount or part that is a field (a `[@Parameter]` works), `DATEPARSE` with a format, time zones.

### Parameters

A formula reads a workbook parameter ([worksheet-encodings.md](worksheet-encodings.md#filters)) as **`[@Name]`**: `SUM([orders.amount]) * [@Tax rate]`.
The `@` is the parameter namespace, so `[Name]` still means a calculation and `[table.column]` a field; a parameter name may hold dots
(`[@Tax.rate]` is one name) but not `[` or `]` (refused in the dialog and skipped on open), and a calculation name may not start with `@` (the name rule; an imported one is skipped with a note). A number parameter read from a hand-edited workbook must be a plain decimal (`0x10`, `1e400` are refused).
- **Substitution is client-side, at compile.** `compileCalculation` parses `[@Name]` to `{ k: "param", name }`, expands calculation references,
  then replaces each `param` node by a literal before type-checking: a number is `num` (a negative is `-` over its magnitude, the parser's own
  shape), a text is `str` (**at most 100 characters**, the text-literal limit), a date is `DATE('YYYY-MM-DD')` (a `fn date` over a `str`, so the date rules of
  `DATE` apply). The checked tree, the cache key and the wire hold only literals; the server never sees a parameter and its
  limits are unchanged. Because the substitution comes before the check, a parameter can supply the literal-only arguments: `LEFT([c.name], [@N])`,
  `DATEADD([@Unit], [@Days], d)` (still range-checked, so 2.5 or `'fortnight'` is refused as a literal would be).
- **Types:** a text parameter in arithmetic reads `Arithmetic needs numbers — that value is text.`; `YEAR([@Region])` is `YEAR needs a date`.
  A number parameter that isn't finite, a date that isn't a date, or a text over 100 characters is `Parameter [@X] isn't a usable number.` /
  `isn't a date.` / `can be at most 100 characters in a formula.`
- **Autocomplete:** typing `[@` offers only the workbook's parameters (`parameter · number`), narrowed by what follows.
- **Changing a value** re-plans the open worksheet and every dashboard widget: the request now carries the new literal (a different request key, so a
  fresh query, not a cached one); the sheet shows a control for each parameter its calculated pills read (the same controls as for filters).
  Calculated pills are re-typed when a parameter's type changes.
- **Rename and delete:** renaming a parameter rewrites `[@Old]` in every formula, and renaming a calculation `[Old]`, both outside text literals (`'[@Old]'` stays text). Deleting one that a formula mentions **asks first** (naming the
  calculations); if confirmed, the calculation keeps its formula and shows the E15 state `Calculation 'X' can't be computed: Parameter [@Y] was
  deleted or doesn't exist.` (no query is sent) until a parameter with that name exists again. The workbook saves formula text only (format unchanged).

### Roles and types

The check yields a type (number, text, date, boolean) and whether the formula is an **aggregate**:

| Formula | Role | Used as |
|---|---|---|
| contains an aggregate (`SUM([a]) / SUM([b])`) | measure | aggregated by the server, no further aggregation |
| row-level text, date or boolean (`[status] = 'open'`, `CASE … 'big' …`) | dimension | a group key; a boolean calculation shows `true` / `false` (a plain Bool field keeps `True` / `False`) |
| row-level number | measure **or** dimension | measure sums it per row (`SUM([price] * [qty])`); dimension groups by it |

Mixing an aggregate with a bare row-level field in one formula is refused by the checker with a message. An aggregate
text or boolean calculation is a measure and shows in tables and KPIs.

### Limits

Read from `Core/validate.js` `LIMITS` (`calculations`, `calcFormula`, `calcName`) and `CALC_LIMITS` in
`calc-types.js` (formula length, depth, nodes, text literal length 100, text-function length/position 1000, separator 20, `CONCAT` arguments 10) — the server mirrors depth, nodes, name length,
literal length and these in `CalcLimits`. A `CASE` counts one node plus every condition and result. A formula over the length limit, a tree over the depth or node limit, a name over the length
limit and a workbook over the calculation count are refused with a message; none is clamped.

## The dialog

**New calculated field** (field pane) and **Edit…** open one dialog (`calc-dialog.js`; all logic in
`calc-dialog-model.js`):

- **Name** — 1 to `LIMITS.calcName` characters after trimming, no `.`, `[` or `]`, unique ignoring case.
  A name problem shows only after the box was touched and never hides the formula's own message.
- **Formula** — a text box. Typing `[` opens an autocomplete of fields and other calculations (a
  calculation never offers itself); arrow keys move, Enter or Tab (after arrowing) accepts, Esc closes the
  list and not the dialog. A fresh formula text is always a string: CRLF is normalised, control characters
  and over-long text give a message, never an exception.
  Typing the start of a **function name** (a letter prefix outside `[ ]` and outside a text literal, e.g. `LO`) offers up to 12
  matching functions in the same list (not when the caret is inside a word; before an existing `(` no second one is added), each with its signature (`LOWER(text)`); accepting inserts `LOWER(` with the caret
  after the bracket (`AND`, `OR`, `NOT` and `CASE` insert the word and a space). Field suggestions after `[` are unchanged.
- **Functions** — a button under the formula opens a help panel (`aria-expanded`, Esc closes the panel and not the dialog).
  A search box filters the glossary (name, group, plain-words sentence, signature); the list is grouped Aggregate, Logic,
  Text, Date. Hovering or focusing a row shows its detail: signature, what it does, what it takes, what it gives, one
  example formula and the empty-value (NULL) rule. Clicking a row inserts its signature at the caret (replacing a
  selection); **Insert example** inserts the example of the function last focused with the keyboard or clicked (hovering only previews). After an insert, focus returns to the formula box, so Esc then closes the dialog. The dialog body scrolls so Cancel / Save stay visible. The
  glossary (`function-help.js`) derives names, arity and result types from `calc-types.js`; a test fails when a function
  has no entry or an entry has no function, and that every example formula parses and type-checks. Operators
  (`+ - * / = != < <= > >=`) are not listed as functions.
- **Live message** — the first problem, in plain words, with `(at character N)` and a caret mark when the
  parser knows the position. Unknown field and cycle messages name the cause.
- **Role chip** — icon plus text, never colour alone: `Aggregate · number`, `Row-level · text`, `Row-level · boolean`, "No
  formula yet", or "Can't be saved".
- **Use as** — a Measure / Dimension choice, shown only for a **row-level number**. It is a session-only
  default for chips dragged afterwards; it is not saved in the workbook. A pill already placed keeps its
  own role.
- **Save** is disabled until the draft names, parses, resolves, type-checks and expands without a cycle.
  Cancel and Esc discard. Saving an edit under a new name rewrites `[Old]` to `[New]` in every other
  calculation's formula, so no reference breaks (`[table.Old]` is left alone).

## Field pane group

A **Calculated fields** group sits above the tables: a **New calculated field** button (disabled at the
count limit) and one chip per calculation showing its name, role chip (`Aggregate · number` …) and a
**⋯** menu:

| Action | Behaviour |
|---|---|
| Edit… | opens the dialog (a group field: the Group dialog, [below](#group-fields)) |
| Duplicate | adds `<name> copy` (`copy 2` … when taken) with the same formula (or groups) and Use-as choice |
| Delete… | refused with a toast `Used by calculation 'B'.` while another calculation refers to it; when worksheets or shared Top-N filters use it, a confirm says how many, and Delete clears its pills (and a sort or Top-N ranking aimed at it) from them; otherwise it deletes at once |

A calculation that can't be computed (its field left the model, an imported cycle) shows an **Error**
badge instead of the role chip, its message as the tooltip, and cannot be dragged or added. The search
box filters the group by name. Chips drag or **+** onto shelves like fields; the **+** goes to Rows for a
measure and Columns for a dimension.

## What a calculated pill is

A pill `{ calc: id, db: "", table: "", column: <name at last save>, category, role, agg? }`.
`category` follows the type (`numeric`, `text`, `temporal`, `boolean`); the empty `db` / `table` keep every
reader of `f.db` / `f.table` / `f.column` safe, and the **live name** always comes from the workbook's list
by `calc` id. A row-level number used as a measure carries `agg: "sum"`. After any calculation change every
sheet's pills refresh their category, role and name (`syncCalcPills`).

Calculated pills go on Rows, Columns, Color, and the Size, Label, Path and Detail / Tooltip slots, and may be
a Top-N ranking measure and a sort target. A calculated dimension is never date-grouped: its pill shows no
date-part picker or step buttons, and a saved `datePart` is removed (on sync and on open).

A calculated **measure's** aggregation menu offers only sum, avg, min, max, distinct count and non-null count
(`CALC_AGGS`, mirroring the server's `CalcCatalog.RowLevelAggregations`) — never `count`, which the server
refuses for a calculation; a saved `count` resets to sum on open. After undo, redo, applying a bookmark or
opening a workbook, the sheet's calculated pills re-read the live calculation's type and role.

**Top-N by a calculation.** A Top-N filter ranked by a calculation stores `topBy: { db: "", table: "", column,
calc: id, agg? }` and is saved and restored like any other. Deleting the calculation counts that filter as a
use (the confirm appears); confirming keeps the filter but clears its ranking, and the filter panel ranks by
the first shelf measure again (until then the filter reports "Pick a measure to rank by." and is not sent).
The same holds for a **shared** Top-N filter: it counts as a use ("… and 1 shared Top N filter"), and its ranking
is cleared. A Top-N whose calculation can no longer be computed stops the view with the usual
`Calculation 'X' can't be computed: …` message; a ranking that cannot be wired is never sent as `topBy: null`.
A Top-N whose calculation can't be computed is refused like a pill (below).

### Where a calculated field is refused

Dropping one on any of these shows the toast **`Calculated fields can't be used here yet.`**, adds no pill:
a filter, Pages, drill-down, the date range, a shared filter, a click selection, the Shape and Angle slots,
and a field-choice list (a calculated pill has no field choices). Click-to-filter is **off** when the
primary dimension (the drill level, else the first Rows / Columns dimension) is a calculation; the legend
still highlights.

**Histogram and box plot** run single-table endpoints that know nothing of calculations: with a calculated
pill on Columns or Rows they show **`Histogram and box plot don't use calculated fields yet.`** in the chart
slot and send no query.

## Error state

A calculation that can't be computed (unknown or removed field, missing table, cycle, a calculation that
no longer exists) is kept, not dropped. Any sheet that uses it (a pill, or a Top-N ranked by it) sends **no query** and shows, in the chart
slot and for CSV export, `Calculation 'X' can't be computed: <reason>`. Fix or delete the calculation and
the view recomputes. A sheet whose only pills are field-less calculations shows the hint "Add a field from
a table — a calculation with no field in it has nothing to group or total." (no query).

## Group fields

A field's **⋯** menu has **Group…** (T02-30): a text column's members go into named groups, saved as a **group calculation**
(`{ id, name: "region (groups)", formula: "", group: { field, groups: [{ name, members }] } }`). The dialog (`group-dialog.js`;
rules in `group-model.js`) names the field, adds groups (≤ 50, 1–80 characters, unique) and puts each member (the field's top 200,
from the distinct-values read; NULL is skipped) in a group or leaves it **not grouped**. **Label ungrouped members** (optional, default "Other", ≤ 80 characters — a client-side cap like group names, the server accepts up to 100; not a group's name or an ungrouped member) folds every ungrouped non-NULL member into that one label; NULL stays NULL. It is an ordinary calculated dimension afterwards: a
chip in the pane (Edit… reopens this dialog, Duplicate copies the groups), a pill, a text value in formulas (`[region (groups)]`). Number, date and true/false fields, and UUID, IP address and enum columns, are refused (the engine compares text only; ClickHouse has no common type for those, pinned by `tests/live/group-smoke.mjs`). A group name equal to a member that stays ungrouped is refused (it would merge their rows). Compile: `compileCalculation` takes the tree straight from `groupTree`, never formula text, so
the 500-character limit does not apply: `CASE WHEN member = 'a' OR … THEN 'Group' … ELSE <the field> END`, one WHEN per group, an
OR (balanced, so shallow) of `=` against `str` literals — bound parameters, nothing quoted into SQL, plus a last `WHEN NOT isnull(field) THEN '<label>'` when the label is on. A member in no group keeps its own value (without the label);
NULL stays NULL. The **node limit (200)** bounds it: 2 + 4 nodes per member, so **49 members across all groups**, **48** with the remainder label (`maxMembersFor`; the dialog says
so and disables Save, and the server refuses a bigger tree too). A group-calculation pill takes no click-selection (E12), and member labels do not apply to it. Code: `Calc/group-model.js`.

## Non-null count

**Non-null count** is a valid aggregation for every field category (`aggsFor`), shown as `non-null <name>` everywhere: the server names the
result column that way (`countNonNull`, `count(col)`), so the chart, the CSV header and a compare result agree. A
calculation's `COUNT(...)` is the same aggregate.

## How this is computed

A view-bar button opens a popover (`explain-popover.js`, text only; Esc or an outside click closes it and
returns focus) listing, for the current sheet, the six stages in the order they run:

1. **Filters** — own, shared, drill, page, selection, date range and Top-N filter that ClickHouse applies.
2. **Row-level calculations** — worked out for each remaining row.
3. **Group by** — the dimensions, or a single group when there are none.
4. **Aggregates** — including aggregate calculations.
5. **Cap and Other** — the display cap (Top-N "All" = 5000 groups) and the Other bucket when the chart folds one.
6. **Table calculations** — run in the browser on the returned groups.

The text is generated from the live sheet (`eval-order.js`), so it is current whenever it opens.
