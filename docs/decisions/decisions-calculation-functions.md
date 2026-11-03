---
components: []
---
# Decisions — calculation functions

D48–D60: aggregations, logic, text and date functions. Lookup: [README.md](README.md#where-each-decision-lives). Behaviour: [calculated-fields-formulas.md](../concepts/worksheet/calculated-fields-formulas.md). Edit an entry in place when it changes.

### D48 — More aggregations: exact, bound, NULL for "no answer"
`median`, `stddev`, `variance` and `attr` are plain-measure aggregations. `MEDIAN`, `STDDEV`, `VARIANCE`, `ATTR` and
`PERCENTILE` are calculated-field functions. All go through `AggregateSql`.
- **Quantiles** are `quantileExactInclusive`: exact, linearly interpolating like Excel `PERCENTILE.INC` and Tableau (not the
  reservoir `quantile`). They are never scaled on a sample.
- **`stddev` / `variance`** are sample statistics and are NULL for fewer than two values (not NaN, which JSON cannot carry).
- **`ATTR`** is `if(uniqExact(x) = 1, min(x), NULL)`, so it returns NULL where Tableau shows `*`, ignoring NULL rows.
- **The percentile fraction in a formula** is a literal, carried as `p` on the `agg` node, bound as a parameter and checked 0..1
  on both sides.
- **A plain measure's fraction** is `MeasureRef.P` (the pill's `p`, stored 0..1, typed as a percent 0–100). It is required
  exactly when `agg` is `percentile`; otherwise it is a 400 at `measures[i].p` / `filters[i].topBy.p`. It is bound as `mp{n}` /
  `tp{i}`.
- **Label:** `p<percent> <column>` (`p90 amount`; percent to six decimals, no exponent). `PercentLabel` and `percentLabel` write
  the same text.
- Percentile stays out of a field's default-aggregation menu (it would need a default fraction) and out of a calculated pill's
  list. An invalid or missing `p` on an opened workbook resets the pill's aggregation, with an import issue.

### D49 — Logic is new node kinds on the same wire; one `case` node for IF and CASE
`str`, `cmp`, `logic` (`and`/`or`), `not`, `case`, `ifnull` and `isnull` join `field | num | un | bin | agg` under the same
discriminator `k`. An unknown `k` stays a 400.
- `IF`/`IIF` are a `case` with one arm and an else; `ZN(a)` is `ifnull(a, 0)`; the simple `CASE x WHEN v` is a `cmp` per arm.
- **Why:** the server learns no more kinds than it computes.
- The shared walk is `ExprTree.Children`. The new kinds count toward the same depth and node limits.

### D50 — Typing: one result type, boolean conditions, no mixed comparisons
- Every THEN and the ELSE (and both sides of `IFNULL`) must be the same type.
- A condition must be boolean.
- A comparison takes two numbers, two texts or two dates — no implicit conversion and no boolean comparison (use the boolean
  directly).
- The error names the offending branch (`w1.t`, `else`, `r`).
- An IF/CASE is an aggregate when any part is, and the existing mixing rule applies, with literals neutral.

### D51 — NULL follows SQL
A NULL condition is not true (IF takes the else, CASE the next WHEN). A comparison with NULL is NULL. `AND`/`OR`/`NOT` are
three-valued.
- **Why:** chosen over "NULL is false" so `x <> 'a'` does not silently include unknown values, and because ClickHouse behaves
  this way natively (confirmed live).
- Division keeps `nullIf(r, 0)`. `IFNULL`/`ZN` is the explicit replace-NULL tool.

### D52 — Text literals are bound, length-limited; a boolean dimension reads true/false
- A text literal is a `String` parameter, just as every number is a `Float64`. It is at most 100 characters (client parser, JS
  checker and server validator alike) and never appears in SQL text.
- A boolean calculation is wrapped in `toBool(...)`. As a **dimension** it groups by `toString(...)`, so its keys read
  `true`/`false`/`null`.
- A plain Bool field is unchanged (`True`/`False`), so saved filters and member colours still match.

### D53 — Text functions are one generic `fn` node with a whitelisted table
`{ k: "fn", fn, args: [...] }` carries every row-level text function. The name and its argument kinds (`text`, `length`,
`position`, `separator`) live in one table per side (`CalcCatalog.RowFunctions`, `ROW_FUNCTIONS`; a node test ties them).
- **Why:** a later function (date functions) is a table row, not a new node kind.
- The client parses any argument count and the checker reports arity, so the message is the same on both sides.
- Paths are `args.0`, `args.1`, ….

### D54 — Length, position and separator are literals, rejected out of range
`LEFT`/`RIGHT` take a whole number 0..1000, and `SPLIT` takes a position 1..1000 and a 1..20 character separator, all written
in the formula. A number is bound as `UInt32`, a separator as `String`.
- **Why:** a computed length would need clamp and NULL rules; a literal needs none. So a bad one is a 400, never a clamp
  (golden rule 3).
- Fields or parameters as lengths are a backlog item.

### D55 — `CONCAT` instead of `+`; case-sensitive predicates; NULL propagates
- **Text `+` stays an error** (arithmetic needs numbers), so `+` never changes meaning with its operand types. `CONCAT` takes
  2..10 texts.
- **`CONTAINS`/`STARTSWITH`/`ENDSWITH` are case-sensitive**, like `=` and Tableau (`LOWER` both sides when case should not
  matter). The case-insensitive *filter* is unchanged.
- **Character functions are UTF-8 aware** (`lowerUTF8`, `leftUTF8`, `lengthUTF8`). `CONTAINS`/`STARTSWITH`/`ENDSWITH` compare
  bytes, which is exact for valid UTF-8.
- A NULL argument gives NULL.

### D56 — `SPLIT` is NULL past the last piece
`SPLIT` compiles to `arrayElementOrNull(splitByString(sep, t), k)`, with a NULL `t` answered first (ClickHouse has no nullable
split).
- A piece that exists but is empty stays `''`, so "no such piece" (NULL) and "empty piece" differ.
- `''` splits to one empty piece (confirmed live).

### D57 — Date functions are rows in the same `fn` table; units and amounts are literals
`DATEDIFF`, `DATEADD`, `YEAR`, `MONTH`, `DAY`, `QUARTER`, `WEEK`, `WEEKDAY` and `DATE` are `RowFunctions` rows (new argument
kinds `date`, `unit`, `amount`), parsed by the generic `fn` path with no grammar change.
- **The unit is a text literal** (`'day'`), not a bare keyword. It needs no parser rule and reuses text-literal parsing and its
  100-character cap.
- The unit is checked against the fixed list `CalcCatalog.DateUnits` (a node test ties it to `DATE_UNITS`). `DATEDIFF` binds it
  as a `String` parameter; `DATEADD` picks a fixed function (`addDays` …), so no unit text reaches SQL.
- **The `DATEADD` amount** is a literal -100000..100000 (a bound `Int32`; a single leading minus is allowed), rejected out of
  range as in D54.

### D58 — Date arguments must be dates; text goes through `DATE()`
A date argument that is text or a number is an error that points at `DATE()`, so no function guesses a conversion.
- **`DATE` is the one text-to-date path.** It reuses the date cast's digit-only guard (`TypeCast`, one expression for both).
  It parses with the wide-range parser and returns NULL outside what a `Date` holds, because ClickHouse would otherwise clamp
  `1850-01-01` to `1970-01-01` silently. It returns a `Date`, dropping any time of day.
- **`DATEADD`** is computed on `toDateTime64(d, 0)` and is NULL outside 1900-01-03..2299-12-29. ClickHouse wraps a plain
  `Date` past 2149 and clamps a `DateTime` to 1970 (both pinned live), and a `Date32`/`DateTime64` result at its own edge is
  clamped, so the edges are excluded.

### D59 — `DATEDIFF` counts boundaries; `WEEK` is ISO; parts are numbers
- **`dateDiff` counts calendar boundaries crossed** (31 Jan to 1 Feb is one month) — the ClickHouse meaning, not elapsed time.
  Tableau's `DATEDIFF` also counts boundaries, but its default week starts on Sunday and ClickHouse's on Monday, so only the
  boundary rule matches, not week results.
- **`WEEK` is `toISOWeek`.** The existing week date part stays the Monday-truncated bucket — a different thing: a date, not a
  number.
- **`WEEKDAY` is ISO:** Monday 1 to Sunday 7, unlike Tableau's Sunday-is-1.
- Parts return `toFloat64`, like every calculation number. NULL in, NULL out.

### D60 — No `TODAY()` / `NOW()`
- **No `TODAY` / `NOW`:** a calculation is a function of the data. Caching, saved workbooks and exports assume the same query
  gives the same answer, and `TODAY` / `NOW` would change that. They wait for a decision (a parameter-style "as of" value).
- `MAKEDATE` is built, guarded ([D78](decisions-logic.md#d78--makedate-is-null-unless-the-date-exists-datename-is-english)).
