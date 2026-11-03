---
components: [src/DashboardBuilder/Features/Calc/calc-types.js, src/DashboardBuilder/Features/Core/validate.js]
---
# Calculated fields — formulas

The formula language: grammar, functions, parameters, roles, types and limits. The dialog, pane group and error state: [calculated-fields.md](calculated-fields.md).

### Grammar

```text
expr      := and ("OR" and)*
and       := not ("AND" not)*
not       := "NOT" not | compare
compare   := sum [("="|"!="|"<>"|"<"|"<="|">"|">=") sum]        (no chaining)
sum       := term (("+"|"-") term)*
term      := factor (("*"|"/") factor)*
factor    := "-" factor | number | string | "(" expr ")" | aggregate | logic | ref
string    := "'" text "'"
aggregate := FN "(" expr ")" | "PERCENTILE" "(" expr "," number ")"
ref       := "[" name "]" | "[@" parameter "]"                   (a workbook parameter, see Parameters below)
```

- **Numbers** are decimals with an optional exponent (`12`, `.5`, `1e3`); no `1,000`; a non-finite `1e999` is an error.
- **Argument types:** `SUM` / `AVG` / `MEDIAN` / `STDDEV` / `VARIANCE` / `PERCENTILE` take a number. `MIN` / `MAX` take a number, date or text. `COUNT` / `COUNTD` / `ATTR` take any type. Arithmetic needs numbers.
- An aggregate inside an aggregate is refused.
- A field of a category other than numeric, text, temporal or boolean can't be used.

### What a formula can contain

- **Operators** `+ − * /`, parentheses, numbers, and the aggregates `SUM`, `AVG`, `MIN`, `MAX`, `COUNT`, `COUNTD`, `MEDIAN`, `STDDEV`, `VARIANCE`, `PERCENTILE`, `ATTR`. Function names are case-insensitive. The function table lives in `calc-types.js`.
- **Logic** ([below](#logic-functions)): comparisons, `AND` / `OR` / `NOT`, `IN`, `BETWEEN`, `IF` / `IIF` / `CASE`, `IFNULL`, `ISNULL`, `ZN`, text, `TRUE` / `FALSE` and `NULL` literals.
- **Text** ([below](#text-functions)): `TEXT` (alias `STR`), `LOWER`, `UPPER`, `TRIM`, `LTRIM`, `RTRIM`, `LEN`, `LEFT`, `RIGHT`, `MID`, `FIND`, `REPLACE`, `CONCAT`, `CONTAINS`, `STARTSWITH`, `ENDSWITH`, `ICONTAINS`, `ISTARTSWITH`, `IENDSWITH`, `SPLIT`.
- **Date** ([below](#date-functions)): `DATEDIFF`, `DATEADD`, `YEAR`, `MONTH`, `DAY`, `QUARTER`, `WEEK`, `WEEKDAY`, `ISOYEAR`, `DATENAME`, `DATETRUNC`, `MAKEDATE`, `DATE`.
- **References:** `[table.column]` (`[db.table.column]` when two databases hold the same table name), or `[Name]` for another calculation. Calculations can refer to calculations. The browser expands every reference into one tree before sending, so the server never sees a calculation name.
- **Division by zero** gives NULL, never an error. A formula with **no field references** (`1+2`) is valid but needs a field elsewhere on the sheet to group or total.

### Statistics

- **`MEDIAN([f])`** is the exact median of the non-NULL values: linear interpolation between the two middle values, like Excel `PERCENTILE.INC` (1, 2, 3, 4 gives 2.5).
- **`PERCENTILE([f], p)`** is the same interpolation at fraction `p` (p25 of 1..4 is 1.75). `p` is a **literal** number 0..1, not a field or a formula. `PERCENTILE([f], 0.5)` equals `MEDIAN`; 0 is the minimum, 1 the maximum.
- **`STDDEV` and `VARIANCE`** are the **sample** statistics (n − 1).
- **Empty results:** `STDDEV` / `VARIANCE` of fewer than two values, and `MEDIAN` / `PERCENTILE` of no value, are empty (NULL, shown as a dash), never 0 or NaN. A plain field's pill has its own `Percentile…` aggregation ([worksheet.md](worksheet.md#aggregation)); a calculated pill does not list it.
- **`ATTR([f])`** (Tableau's attribute) is the value when the group has exactly one distinct non-NULL value, else empty (NULL; Tableau shows `*`, here a dash). NULLs are ignored, so a group of `p, p, NULL` is `p`. It keeps the field's type, so a text field stays a text measure (table, text and KPI views only).

### Clean… (query-time cleaning)

A text or number field's menu **Clean…** adds ONE calculated field. The data is never changed.

- **Trim spaces** (text) → `TRIM`.
- **Replace missing (NULL) values** → `IFNULL(f, 'text')`, or `IFNULL(f, 12.5)` on a number. It replaces NULL only, not an empty string.
- **Recode values** → `old = new` lines, up to 20, each cut at the first `=`. Builds `CASE f WHEN 'old' THEN 'new' … ELSE f END`; unlisted values are kept unless unticked. The formula must stay within 500 characters.
- **Read as a date** → `DATE(f)`.
- **Naming:** `<field> (trimmed|filled|recoded|date)`, then ` 2`… when taken.
- **Not offered** on a date field (no date literal), nor on a field whose names hold `.`, `[` or `]`.

### Logic functions

- **Text literal** `'open'`: a quote inside is doubled (`'it''s'`). At most 100 characters. It is sent as data, never as SQL text. There is no date literal: write `DATE('2024-01-01')`.
- **Comparison** `= != <> < <= > >=` (`<>` is `!=`) takes two numbers, two texts or two dates — never a mix and never a boolean (`Comparison needs two values of the same type — …`). Text compares exactly (case and accents count).
- **Precedence**, loosest first: `OR`, `AND`, `NOT`, comparison, `+ -`, `* /`. So `1 + 2 > 2` works without parentheses.
- **`AND` / `OR` / `NOT`** need booleans (a comparison, `ISNULL`, a boolean field, `TRUE` / `FALSE`) and give a boolean. A boolean is never compared with `=`: write the field itself.
- **`x IN (a, b, …)`** / **`NOT IN`** ([D76](../../decisions/decisions-logic.md#d76--in-is-a-list-node-of-bound-literals-at-most-50-between-is-two-comparisons)): `x` is a number or text; the 1 to 50 values are number or text literals of the same type written in the formula (a number or text `[@Parameter]` works), each bound as data. A field, a date, a mixed type or a longer list is refused. **`x BETWEEN a AND b`** / **`NOT BETWEEN`** is `x >= a AND x <= b` (ends included; number, text or date); a large `x` is evaluated twice in the SQL and counts twice against the node limit.
- **`IF(cond, a, b)`** (also `IIF`), **`IF c THEN a [ELSEIF d THEN b]… [ELSE e] END`** and **`CASE WHEN c THEN a [WHEN …] [ELSE d] END`** (all one `case` node, [D77](../../decisions/decisions-logic.md#d77--the-keyword-if-is-another-spelling-of-case-when)):
  - The simple form `CASE [f] WHEN 'x' THEN a … END` tests `[f] = 'x'`. The subject is copied into every arm, so each arm costs its nodes again against the node limit.
  - Conditions are booleans. Every THEN and the ELSE must have **one type** (number, text, date or boolean); otherwise `All results must be the same type — … is text, not number.` shows at the offending branch.
  - The first true WHEN wins. A CASE with no ELSE is empty (NULL) when nothing matches.
- **`IFNULL(a, b)`** is `a`, or `b` when `a` is empty (same type). **`ZN(a)`** is `IFNULL(a, 0)`. **`ISNULL(a)`** is true when `a` is empty. Division by zero is still empty, so `IFNULL(a / b, 0)` repairs it.
- **NULL:**
  - A condition that is NULL counts as not true: `IF` takes its else, `CASE` tries the next WHEN. A comparison or `IN` with a NULL value is NULL (shown as a NULL group, not `false`).
  - **`NULL` literal** ([D75](../../decisions/decisions-logic.md#d75--null-has-no-type-of-its-own-it-takes-the-type-of-the-results-beside-it)) is only an `IF` / `CASE` result or an `IFNULL` side, and takes the type of the other results (`IF c THEN 'x' ELSE NULL END` is text). Anywhere else it is refused; `x = NULL` points at `ISNULL(x)`, and a formula with no non-NULL result has no type.
  - `AND` / `OR` / `NOT` are three-valued: `NULL AND false` is `false`, `NULL OR true` is `true`, `NOT NULL` is NULL. Aggregates still skip NULLs.
- **Aggregate or row-level:** an `IF`, `CASE`, comparison or `IFNULL` is an aggregate calculation when any part is an aggregate and every other part is an aggregate or a constant (`IF(SUM([a]) > 100, 'high', 'low')`). A row-level part beside an aggregate is the usual mixing error. `SUM(IF([s] = 'open', [amount], 0))` is a conditional sum.

### Text functions

Row-level functions over text. Names are case-insensitive; the table is `ROW_FUNCTIONS` in `calc-types.js`.

- Each argument that is text may be any text expression: a field, a literal, or another function.
- Every other argument is a **literal written in the formula**, never a field or a computed value.

| Function | Result | Meaning |
|---|---|---|
| `TEXT(x)` / `STR(x)` | text | A number, date or text as text. `STR` is the same function. Unlike the rows below, the argument is not limited to text: it may be any number, date or text expression. A condition is refused: `TEXT (or STR) needs a number, date or text — that value is boolean.` Numbers print as ClickHouse prints a Float64 (`10`, `2.5`, `0.30000000000000004`, `1e21`; no thousands separator). A date reads `YYYY-MM-DD`; any value with a time (a `DATETIME` column, a `DATEADD` result) reads `YYYY-MM-DD hh:mm:ss`. NULL gives NULL; text is unchanged. `CONCAT('#', TEXT([o.id]))` builds a label |
| `LOWER(t)` / `UPPER(t)` | text | change case, accents and non-Latin letters included (`UPPER('straße')` is `STRASSE`) |
| `TRIM(t)` / `LTRIM(t)` / `RTRIM(t)` | text | remove spaces at both ends / the start / the end (the space character only; tabs and line breaks stay) |
| `LEN(t)` / `FIND(t, s)` | number | `LEN`: length in **characters**, not bytes (`LEN('日本語')` is 3). `FIND`: 1-based character position of the first `s` in `t`, 0 when absent, case-sensitive, 1 for an empty `s` |
| `LEFT(t, n)` / `RIGHT(t, n)` | text | The first / last `n` characters. `n` is a whole number 0 to 1000. Longer than the text gives the whole text; 0 gives an empty text. `MID(t, start, n)` takes `n` characters from `start` (1 to 1000, 1 is the first); `start` and `n` are literals |
| `REPLACE(t, from, to)` | text | Every occurrence of `from` replaced by `to`. Case-sensitive. An empty `from` changes nothing. `from` and `to` may be fields (pinned live) |
| `CONCAT(a, b, …)` | text | Two to ten texts joined. Empty if any is empty (wrap a part in `IFNULL(x, '')` to keep the rest) |
| `CONTAINS(t, s)` / `STARTSWITH(t, s)` / `ENDSWITH(t, s)` | boolean | **case-sensitive** match; `ICONTAINS` / `ISTARTSWITH` / `IENDSWITH` are the case-insensitive twins (separate names, no flag); an empty `s` is always true |
| `SPLIT(t, sep, k)` | text | The `k`-th piece (1 is the first) of `t` cut at `sep`. `sep` is text of 1 to 20 characters; `k` a whole number 1 to 1000. Empty when there is no `k`-th piece. An empty text has one empty piece; two neighbouring separators leave an empty piece |

- **Split… menu.** A text field's menu **Split…** asks for a separator (1–20 characters) and 2–10 pieces, then adds one calculated field per piece (`tags 1`, `tags 2`, … = `SPLIT([db.table.tags], ',', k)`). It stops at the 20-field limit. A field whose names hold `.`, `[` or `]` can't be split.
- **Empty in, empty out:** a NULL text gives NULL from every function (`LEN`, `CONTAINS` too), so use `IFNULL(x, …)` first when a default is wanted.
- **No `+` on text;** use `CONCAT`.
- **Lengths and positions are checked, not clamped.** A negative, fractional, field-valued or over-limit length or position is an error naming the function (`LEFT's length must be a whole number from 0 to 1000 written in the formula.`).
- **Type errors:** a number or boolean where text is needed reads `LOWER needs a text — orders.amount is number.` at the argument. A wrong argument count reads `LEFT takes 2 arguments.` (`CONCAT takes 2 to 10 arguments.`).
- **Row-level, aggregates as usual:**
  - `COUNTD(LOWER([c.name]))` and `SUM(IF(CONTAINS([c.name], 'x'), 1, 0))` work.
  - A text function over an aggregate (`LOWER(MAX([c.name]))`) is an aggregate. Mixing with a bare row-level field is the usual error.
  - A row-level text or boolean result (`LOWER`, `CONTAINS`) is a **dimension**. `LEN` is a row-level number (measure or dimension).

### Date functions

Row-level functions over dates (same `ROW_FUNCTIONS` table and generic `fn` node as text).

- A *date* argument is any date or date-time expression: a field, `DATEADD(…)`, `DATE(…)`.
- A text argument is refused (`YEAR needs a date — orders.status is text. Use DATE() to turn text into a date.`); so is a number.
- A NULL date gives NULL from every function.

| Function | Result | Meaning |
|---|---|---|
| `DATEDIFF(unit, d1, d2)` | number | `d2` minus `d1`, in whole `unit`s, counted as **calendar boundaries crossed**: `DATEDIFF('month', 31 Jan, 1 Feb)` is 1 and `DATEDIFF('year', 31 Dec, 1 Jan)` is 1. Negative when `d2` is earlier. Weeks start on Monday (Tableau's default week starts on Sunday, so a `'week'` difference can differ from Tableau's by one around a Sunday) |
| `DATEADD(unit, n, d)` | date | `d` moved by `n` units. A month or year step past the end of a shorter month lands on its last day (31 Jan + 1 month is 29 Feb 2024; 29 Feb 2024 + 1 year is 28 Feb 2025). The result may be later than a `Date` column's own 2149 limit. It is **NULL** when it falls outside 1900-01-03 to 2299-12-29 (never a wrapped or clamped date) |
| `YEAR(d)` / `MONTH(d)` / `DAY(d)` / `QUARTER(d)` | number | the calendar year, month 1-12, day of the month 1-31, quarter 1-4 |
| `WEEK(d)` / `ISOYEAR(d)` | number | the **ISO 8601 week** 1-53 (weeks start Monday; week 1 holds the year's first Thursday, so 31 Dec 2020 and 1 Jan 2021 are week 53 and 30 Dec 2024 is week 1) / the year that owns that week (30 Dec 2024 is 2025, 3 Jan 2021 is 2020) |
| `WEEKDAY(d)` | number | ISO day of the week: **Monday 1 to Sunday 7** (Tableau's `DATEPART('weekday')` counts Sunday as 1, so `WEEKDAY(d) = 7` is a Sunday here) |
| `DATENAME(part, d)` | text | the **English** name: `'weekday'` gives Monday to Sunday, `'month'` January to December (fixed, never the server's locale); the part is a text literal, any case, and any other word is an error |
| `DATETRUNC(unit, d)` | date | `d` cut back to the start of its `unit` (same units as `DATEDIFF`; weeks start Monday): `DATETRUNC('month', 5 Mar 2024)` is 1 Mar 2024. A calculated date dimension to group by month, quarter or year |
| `MAKEDATE(y, m, d)` | date | the date with that year, month and day; each argument is any number expression. **NULL, never a guessed date,** unless all three are whole numbers, the year is 1901 to 2298, the month 1 to 12 and the day exists in that month (30 Feb, 29 Feb 2023 and 29 Feb 2100 are NULL; the engine itself would answer 1 Mar or 1970-01-01). A NULL part gives NULL |
| `DATE(t)` | date | the text `t` read as a calendar date (`2024-03-05`, `20240229`, `2024-03-05 10:30:00`); NULL when it is not one. The time of day is dropped |

- **Unit and amount are literals written in the formula.**
  - The unit (`DATEDIFF`, `DATEADD`, `DATETRUNC`) is a **text literal** (`'day'`, any case) from `year`, `quarter`, `month`, `week`, `day`, `hour`, `minute`, `second`. Anything else (a field, a number, another word) is an error listing them.
  - The `DATEADD` amount is a whole number from -100000 to 100000 (`-7` is fine), never a field or computed value. Out of range is an error, not a clamp (as `LEFT`'s length, [D54](../../decisions/decisions-calculation-functions.md#d54--length-position-and-separator-are-literals-rejected-out-of-range)).
- **Date versus date-time:** the engine's *date* type covers both.
  - On a date-time column, `DATEDIFF('hour', …)` counts hour boundaries (22:30 to 01:00 next day is 3) and `DATEADD('hour', …)` keeps the time of day. On a plain date column, a time unit reads midnight to midnight (`DATEDIFF('hour', 1 Jan, 2 Jan)` is 24), and `DATEADD('hour', 5, d)` becomes a date-time at 05:00.
  - A date-time at midnight displays as a date, as everywhere in the app. The server's own time zone applies to date-time columns without one.
- **`DATE(t)` rules** — the same guard as the date type cast:
  - Text made only of digits, spaces, signs, commas and dots is NULL unless it is `YYYYMMDD` (`'12345'` is NULL, not the 5th of this month). An impossible day (`2024-02-30`), a word, and a year outside 1970 to 2148 are NULL, never a clamped date.
- **`WEEK` is not the week date part.** The date part and bucket "week" on a plain date field is the **Monday that starts the week** (a date); `WEEK(d)` is the ISO week *number*. Weeks 52/53 and 1 can belong to the neighbouring ISO year, so group by `ISOYEAR` plus `WEEK`, not `YEAR` plus `WEEK`, across the year turn.
- **Bucketing a calculated date:** a calculated `DATEADD` / `DATETRUNC` / `MAKEDATE` / `DATE` dimension groups **per distinct value**. It is never date-bucketed or given a date part (a calculated dimension takes no `datePart` or `dateBucket`; [D33](../../decisions/decisions-calculated-fields.md#d33--calculated-fields-are-refused-wherever-a-plain-column-is-assumed)). To group by month or year, use `DATETRUNC` or `YEAR` / `MONTH` / `QUARTER` of it. **Roles:** the number functions give a row-level number (`SUM(WEEK([o.placed]))` works); `DATEADD`, `DATETRUNC`, `MAKEDATE` and `DATE` give a date dimension (`MIN` / `MAX` take it); `DATENAME` a text dimension.

### Parameters

A formula reads a workbook parameter ([worksheet-filters.md](worksheet-filters.md#filters)) as **`[@Name]`**: `SUM([orders.amount]) * [@Tax rate]`.

- **Names.** The `@` is the parameter namespace, so `[Name]` still means a calculation and `[table.column]` a field.
  - A parameter name may hold dots (`[@Tax.rate]` is one name) but not `[` or `]` (refused in the dialog and skipped on open).
  - A calculation name may not start with `@` (the name rule; an imported one is skipped with a note).
  - A number parameter read from a hand-edited workbook must be a plain decimal (`0x10`, `1e400` are refused).
- **Substitution is client-side, at compile.** `compileCalculation` parses `[@Name]` to `{ k: "param", name }`, expands calculation references, then replaces each `param` node by a literal before type-checking:
  - a number → `num` (a negative is `-` over its magnitude, the parser's own shape);
  - a text → `str` (**at most 100 characters**, the text-literal limit);
  - a date → `DATE('YYYY-MM-DD')` (a `fn date` over a `str`, so the date rules of `DATE` apply).

  The checked tree, the cache key and the wire hold only literals; the server never sees a parameter and its limits are unchanged. Because the substitution comes before the check, a parameter can supply the literal-only arguments: `LEFT([c.name], [@N])`, `DATEADD([@Unit], [@Days], d)`. These are still range-checked, so 2.5 or `'fortnight'` is refused as a literal would be.
- **Type errors:** a text parameter in arithmetic reads `Arithmetic needs numbers — that value is text.`; `YEAR([@Region])` is `YEAR needs a date`. A number parameter that isn't finite, a date that isn't a date, or a text over 100 characters reads `Parameter [@X] isn't a usable number.` / `isn't a date.` / `can be at most 100 characters in a formula.`
- **Autocomplete:** typing `[@` offers only the workbook's parameters (`parameter · number`), narrowed by what follows.
- **Changing a value** re-plans the open worksheet and every dashboard widget. The request carries the new literal — a different request key, so a fresh query, not a cached one. The sheet shows a control for each parameter its calculated pills read (the same controls as for filters). Calculated pills are re-typed when a parameter's type changes.
- **Rename:** renaming a parameter rewrites `[@Old]` in every formula, and renaming a calculation rewrites `[Old]`, both outside text literals (`'[@Old]'` stays text).
- **Delete:** deleting a parameter that a formula mentions **asks first**, naming the calculations. If confirmed, the calculation keeps its formula and shows the broken-calculation [error state](calculated-fields.md#error-state) `Calculation 'X' can't be computed: Parameter [@Y] was deleted or doesn't exist.` (no query is sent) until a parameter with that name exists again.
- The workbook saves formula text only (format unchanged).

### Roles and types

The check yields a type (number, text, date, boolean) and whether the formula is an **aggregate**:

| Formula | Role | Used as |
|---|---|---|
| contains an aggregate (`SUM([a]) / SUM([b])`) | measure | aggregated by the server, no further aggregation |
| row-level text, date or boolean (`[status] = 'open'`, `CASE … 'big' …`) | dimension | a group key; a boolean calculation shows `true` / `false` (a plain Bool field keeps `True` / `False`) |
| row-level number | measure **or** dimension | measure sums it per row (`SUM([price] * [qty])`); dimension groups by it |

- Mixing an aggregate with a bare row-level field in one formula is refused by the checker with a message.
- An aggregate text or boolean calculation is a measure and shows in tables and KPIs.

### Limits

Formula length, tree depth, node count, name length, literal and text-function argument limits live in `Core/validate.js` `LIMITS` and `CALC_LIMITS` in `calc-types.js`, mirrored by the server's `CalcLimits` ([api.md § Limits](../../reference/api.md#limits)). A `CASE` counts one node plus every condition and result; an `IN` one plus its value and each list value (at most `inList`, 50). Anything over a limit is refused with a message, never clamped.
