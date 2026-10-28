# Decisions — calculated fields

Continues [decisions.md](decisions.md) (D1–D25). Decisions D26–D60 and D65–D68 (D61–D64 are dashboard decisions). Behaviour: [calculated-fields.md](../features/calculated-fields.md).
Edit an entry in place when it changes.

### D26 — A calculated pill is a normal pill with an id
A calculated pill is `{ calc: id, db: "", table: "", column: <name at last save>, category, role, agg? }`;
`category` maps from the calculation's type (number → `numeric`, text → `text`, date → `temporal`,
boolean → `boolean`). The empty `db` / `table` and the fallback `column` keep the large body of code that
reads `f.db` / `f.table` / `f.column` safe; the live name always comes from the workbook's list by `calc` id,
so a rename never strands a pill. **Rejected:** a separate pill type (every reader would need a branch).

### D27 — Calculation names
Names are 1–`LIMITS.calcName` characters after trimming, unique ignoring case, and may not contain `.`, `[`
or `]` — those characters would make `[table.column]` and `[Name]` references ambiguous.

### D28 — Renaming rewrites other formulas
Renaming a calculation rewrites `[Old]` to `[New]` in every other calculation's formula text, so no
reference silently breaks. `[table.Old]` (a column that happens to share the name) is left alone.

### D29 — Deleting is guarded
Deleting a calculation another calculation refers to is refused ("Used by calculation 'B'."). One used only
by worksheets asks first, then clears those pills and any sort aimed at it. Deleting never leaves a
reference that would fail on open.

### D30 — Non-null count is a first-class aggregation
The plain non-null count is labelled `non-null <name>` (the server's `countNonNull`, `count(col)`) and is a
valid aggregation for every field category, so the same word covers a field and a calculation's `COUNT`.

### D31 — Approximate-mode Top-N is not aligned
A Top-N rank by a plain measure stays exact; a rank by a calculation uses `uniq` / scaled sums in
approximate mode, and `approx.distinct` ignores a `COUNTD` inside `topBy`. Aligning them would change plain
Top-N results or make a ranking depend on the sample; the difference is documented in
[clickhouse-integration.md](clickhouse-integration.md#calculated-fields--the-compile-path) instead.

### D32 — Save is gated; a row-level number picks its role
The dialog's Save is disabled until the draft parses, resolves, type-checks and expands without a cycle
(the same compile the worksheet uses). A row-level number may be used as a dimension or a measure; the
choice is a session-only default for newly made pills and is not saved in the workbook, so the file keeps
the `{ id, name, formula }` shape.

### D33 — Calculated fields are refused wherever a plain column is assumed
Beyond filters, Pages, drill, date range, shared filters and click selection, a calculated pill is also
refused on the Shape and Angle slots and in field-choice lists (extension of the "not where a column is
assumed" rule), and histogram / box plot show a hint instead of sending a calculated pill to their
single-table endpoints. A calculated dimension is never date-grouped, so no date part is stored or offered;
a calculated measure never offers `count` (the server refuses it). **Rejected:** teaching those endpoints
about calculations now — they are single-table and would need the whole compile path.

### D34 — Deleting a calculation used as a Top-N ranking
A Top-N filter ranked by a calculation counts as a use: the delete confirms, then keeps the filter and
clears only its ranking, so the existing "rank by the first shelf measure" default re-applies. Dropping the
filter instead would silently remove a user's setting.

### D35 — The request carries a tree, never formula text
The server never parses text: there is no text-to-SQL path to attack and one authoritative validator.

### D36 — A dimension or measure may carry `Calc`
`Calc` (a tree) replaces the column; the result keeps `k{n}` / `v{n}` aliases in request order, so pivot, sort,
Top-N and charts work unchanged.

### D37 — Aggregate or row-level, never both
A tree is **aggregate** if it contains an aggregate function, else **row-level**; a formula mixing both is a
400 (Tableau's rule; it avoids silent grain errors).

### D38 — Role follows the tree
A row-level number is a measure aggregated by the pill (default `SUM`); a row-level text, date or boolean is a
dimension (`GROUP BY` the expression); an aggregate calculation is a measure with no further aggregation.

### D39 — Division by zero is NULL
`a / b` compiles to `a / nullIf(b, 0)`, shown as a dash: one documented rule, never `inf` or `NaN` in a chart.
A plausible but wrong number is a failure: ratios of sums must not become sums of ratios, and an integer
overflow must not wrap.

### D40 — Numbers are widened to `Float64`
Every numeric field inside a calculation is wrapped `toFloat64(...)`, which avoids unsigned and integer
wrap-around and `Decimal` surprises and matches how results are read (as doubles). Values above 2^53 lose
precision.

### D41 — Workbook-level formula text
`calculations: [{ id, name, formula }]` stores formula **text**; the tree is re-derived on open, so a grammar
change leaves no stale trees. The workbook needs no format bump for this field alone.

### D42 — Reference syntax
Fields are `[table.column]`, or `[db.table.column]` when two databases share a table name; a calculation is
`[Name]` (names may not contain `.`). A two-part reference matching tables in more than one database is an
error asking for the three-part form. Columns or tables whose names contain `.`, `[` or `]` are not
supported: autocomplete does not offer them and a typed reference is an error. Spaces inside brackets are fine.

### D43 — The client expands calculation references
A calculation may reference another; the browser expands references into one tree (cycle check there) before
sending, so the server needs no calculation registry and the node cap bounds the cost.

### D44 — One aggregate compile
Plain and calculated measures share one function (aggregate name + SQL expression + `sampled` + `approximate`
→ SQL). Approximate mode scales a calculated `SUM` by `_sample_factor` and uses `uniq` for `COUNTD`, exactly as
for a plain measure ([table](clickhouse-integration.md#calculated-fields--the-compile-path)).

### D45 — `countNonNull` is a whitelisted aggregation
`count(col)` is added beside `count` (all rows), which keeps its meaning, so saved workbooks are unchanged;
`COUNT([f])` in a formula is the same aggregate.

### D46 — The server derives the role and rejects a mismatch
An aggregate tree is valid only in a `MeasureRef` with `Agg` null; a row-level tree in a `MeasureRef` needs a
value aggregation (`count` of rows is rejected, it would ignore the calculation); a row-level tree is valid in a
`ColumnRef`; an aggregate tree there is a 400 naming the field. A client bug cannot produce a wrong grain.

### D47 — A broken calculation stays
A calculation whose formula points at a field no longer in the model is kept with an error state in the field
pane and the dialog; a worksheet using it shows "Calculation 'X' can't be computed: …" and sends no query;
import reports it as an issue. Dropping it would silently change a user's charts.

### D48 — More aggregations: exact, bound, NULL for "no answer"
`median`, `stddev`, `variance`, `attr` are plain-measure aggregations and `MEDIAN`, `STDDEV`, `VARIANCE`,
`ATTR`, `PERCENTILE` calculated-field functions, all through `AggregateSql`. Quantiles are `quantileExactInclusive` (exact, linearly
interpolating like Excel `PERCENTILE.INC` and Tableau; not the reservoir `quantile`) and are never scaled on a sample; `stddev` / `variance` are sample statistics and
NULL for fewer than two values (not NaN, which JSON cannot carry); `ATTR` is `if(uniqExact(x) = 1, min(x), NULL)`
and so returns NULL where Tableau shows `*`, ignoring NULL rows. The percentile fraction is a literal in the
formula and a `p` on the `agg` node, bound as a parameter and checked 0..1 on both sides; a plain measure has no
fraction field, so a plain percentile is not offered (write `PERCENTILE([t.c], 0.9)`).

### D49 — Logic is new node kinds on the same wire; one `case` node for IF and CASE
`str`, `cmp`, `logic` (`and`/`or`), `not`, `case`, `ifnull`, `isnull` join `field | num | un | bin | agg` under the
same discriminator `k` (unknown `k` stays a 400); `IF`/`IIF` are a `case` with one arm and an else, `ZN(a)` is
`ifnull(a, 0)` and the simple `CASE x WHEN v` is a `cmp` per arm, so the server learns no more kinds than it computes.
The shared walk is `ExprTree.Children`. They count toward the same depth and node limits.

### D50 — Typing: one result type, boolean conditions, no mixed comparisons
Every THEN and the ELSE (and both sides of `IFNULL`) must be the same type, a condition must be boolean, and a
comparison takes two numbers, two texts or two dates — no implicit conversion, no boolean comparison (use the
boolean directly). The error names the offending branch (`w1.t`, `else`, `r`). An IF/CASE is an aggregate when any
part is, and the existing mixing rule applies with literals neutral.

### D51 — NULL follows SQL
A NULL condition is not true (IF takes the else, CASE the next WHEN); a comparison with NULL is NULL; `AND`/`OR`/`NOT`
are three-valued. Chosen over "NULL is false" so `x <> 'a'` does not silently include unknown values, and because
ClickHouse behaves this way natively (confirmed live). Division keeps `nullIf(r, 0)`; `IFNULL`/`ZN` is the explicit
replace-NULL tool.

### D52 — Text literals are bound, length-limited; a boolean dimension reads true/false
A text literal is a `String` parameter like every number is a `Float64`, at most 100 characters (client parser, JS
checker and server validator alike), never in SQL text. A boolean calculation is wrapped in `toBool(...)`; as a
**dimension** it groups by `toString(...)` so its keys read `true`/`false`/`null`. A plain Bool field is unchanged
(`True`/`False`), so saved filters and member colours still match.

### D53 — Text functions are one generic `fn` node with a whitelisted table
`{ k: "fn", fn, args: [...] }` carries every row-level text function; the name and its argument kinds
(`text`, `length`, `position`, `separator`) live in one table per side (`CalcCatalog.RowFunctions`, `ROW_FUNCTIONS`;
a node test ties them), so a later function (date functions) is a table row, not a new node kind. The client parses any
argument count and the checker reports arity, so the message is the same on both sides. Paths are `args.0`, `args.1`, ….

### D54 — Length, position and separator are literals, rejected out of range
`LEFT`/`RIGHT` take a whole number 0..1000, `SPLIT` a position 1..1000 and a 1..20 character separator, all written in
the formula (a number is bound as `UInt32`, a separator as `String`). A computed length would need clamp and NULL rules;
a literal needs none, so a bad one is a 400, never a clamp (golden rule 3). Fields or parameters as lengths are a backlog item.

### D55 — `CONCAT` instead of `+`; case-sensitive predicates; NULL propagates
Text `+` stays an error (arithmetic needs numbers), so `+` never changes meaning with its operand types; `CONCAT` takes 2..10
texts. `CONTAINS`/`STARTSWITH`/`ENDSWITH` are case-sensitive like `=` and Tableau (`LOWER` both sides when the case should not
matter); the case-insensitive *filter* is unchanged. Character functions are UTF-8 aware (`lowerUTF8`, `leftUTF8`,
`lengthUTF8`); `CONTAINS`/`STARTSWITH`/`ENDSWITH` compare bytes, which is exact for valid UTF-8. A NULL argument gives NULL.

### D56 — `SPLIT` is NULL past the last piece
`arrayElementOrNull(splitByString(sep, t), k)`, with a NULL `t` answered first (ClickHouse has no nullable split). A piece
that exists but is empty stays `''`, so "no such piece" (NULL) and "empty piece" differ; `''` splits to one empty piece
(confirmed live).

### D57 — Date functions are rows in the same `fn` table; units and amounts are literals
`DATEDIFF`, `DATEADD`, `YEAR`, `MONTH`, `DAY`, `QUARTER`, `WEEK`, `WEEKDAY` and `DATE` are `RowFunctions` rows (new argument kinds `date`,
`unit`, `amount`), parsed by the generic `fn` path with no grammar change. The unit is a **text literal** (`'day'`), not a bare
keyword: it needs no parser rule and reuses text-literal parsing and its 100-character cap. The unit is checked against the fixed
list `CalcCatalog.DateUnits` (a node test ties it to `DATE_UNITS`); `DATEDIFF` binds it as a `String` parameter, `DATEADD` picks a
fixed function (`addDays` …) so no unit text reaches SQL. The `DATEADD` amount is a literal -100000..100000 (a bound `Int32`; a
single leading minus is allowed), rejected out of range as in D54.

### D58 — Date arguments must be dates; text goes through `DATE()`
A date argument that is text or a number is an error that points at `DATE()`, so no function guesses a conversion. `DATE` is the one
text-to-date path and reuses the date cast's digit-only guard (`TypeCast`, one expression for both); it parses with the wide-range
parser and returns NULL outside what a `Date` holds, because ClickHouse would otherwise clamp `1850-01-01` to `1970-01-01`
silently. It returns a `Date`, dropping any time of day.
`DATEADD` is computed on `toDateTime64(d, 0)` and is NULL outside 1900-01-03..2299-12-29: ClickHouse wraps a plain `Date` past 2149 and
clamps a `DateTime` to 1970 (both pinned live), and a `Date32`/`DateTime64` result at its own edge is clamped, so the edges are excluded.

### D59 — `DATEDIFF` counts boundaries; `WEEK` is ISO; parts are numbers
`dateDiff` counts calendar boundaries crossed (31 Jan to 1 Feb is one month), the ClickHouse meaning, not elapsed time (Tableau's `DATEDIFF` also counts boundaries, but its default week starts on Sunday and
ClickHouse's on Monday, so only the boundary rule matches, not week results). `WEEK` is `toISOWeek` and `WEEKDAY` is Monday 1 to Sunday 7, while the existing week date part stays the Monday-truncated
bucket (a different thing: a date, not a number). `WEEKDAY` is ISO (Sunday is 7), unlike Tableau's Sunday-is-1. Parts return `toFloat64` like every calculation number. NULL in, NULL out.

### D60 — No `TODAY()` / `NOW()`, no `MAKEDATE` yet
A calculation is a function of the data: caching, saved workbooks and exports assume the same query gives the same answer. `TODAY`
and `NOW` would change that, so they wait for a decision (a parameter-style "as of" value). `makeDate` returns `1970-01-01` for a
month 13 or day 32 and rolls `2023-02-29` to 1 March, so it needs guards (and number-argument kinds) that are not worth building yet.


### D65 — A parameter is read as `[@Name]` and becomes a literal on the client
`[Name]` already means a calculation and `[table.column]` a field (E8, E14: names may not contain `.`), while a parameter name may hold
anything, so parameters get their own marker: `[@Name]`, not dot-split, resolved against the workbook's parameters at parse time (an unknown
one is a resolver error, so a deleted parameter reads like any other dangling reference, E15). The value is substituted into the expanded tree
**before** type-checking, as `num` / `str` / `DATE(str)`: no server change, every value stays a bound literal, the request (and so the cache key)
changes with the value, and a parameter can fill the literal-only arguments (`LEFT` length, `DATEADD` unit and amount) while keeping their range checks.
Text parameters over 100 characters are refused rather than truncated (D54's rule). **Rejected:** a `param` node on the wire (a new server
node, validation and cache story for no gain); bare `[Name]` falling back to a parameter (silent ambiguity when a calculation is later added).

### D66 — Deleting a parameter a formula reads asks; renaming rewrites the formulas
Like deleting a calculation a sheet uses, deleting a parameter that a formula mentions asks first, and afterwards the calculation shows the
E15 state with its formula untouched (so re-adding the name heals it). Refusing outright would block a legitimate clean-up; silently
rewriting would hide the damage. The scan is textual (`[@Name]` anywhere in the formula, including inside a text literal), so it can only over-ask.
A rename rewrites `[@Old]` the way a calculation rename rewrites `[Old]`. The reference line stores a parameter id (`analytics.ref.param`) and
falls back to its own value when the parameter is gone (the workbook open also unlinks it, with a note).

### D67 — Member labels are display-side, keyed by the raw value, positioned by the query's key order
A member label (`memberAliases`, a field setting) changes only the text drawn: the query, groups, sort order, filters, drill path values, selections and
member colours keep the raw value, so a label can never change what a click filters or which rows a group holds, and two members with one label stay two
marks. The one place that draws categories is `renderWorksheet`: it wraps the category formatter as `fmtCat(key, position)` (`withMemberLabels`),
where `position` is the key's index in `planDims(sheet).keyOrder`, so two fields can label the same raw value differently; callers that pass no position get
the plain format. Maps are null-prototype and read by own key (a member can be `__proto__`); the per-field cap is 200 labels, a label 80 characters, a key 100.
A selection chip's text is baked when the member is picked (like the drill label) and does not follow a later edit. **Rejected:** rewriting the result's keys before drawing
(clicks, Path sorting and the colour-split pivot would see labels; equal labels would merge rows); one global value → label map (no per-field meaning).

### D68 — A group field is a calculation whose tree is generated, not parsed
Groups are stored on a calculation (`group` beside an empty `formula`), not in `fieldMeta`: a field can have several group sets, each becomes a pill, a chip and
a value other formulas can use, and the workbook, undo, pills and query path already know calculations. `compileCalculation` builds the tree directly
(`groupTree`), so formula text (500 characters) does not bound it; the engine's 200-node limit does: 2 + 4 nodes per member = 49 members in all.
It is refused at edit time with a plain message (`checkGroupSpec`), never at query time, and the server independently refuses a larger tree. Members are `str` nodes
(bound), the OR is balanced (depth ≤ 12), and ELSE is the field itself: an ungrouped member keeps its value and NULL stays NULL (a CASE condition on NULL is false). Only text fields
(the engine compares text with text); the remainder is in the backlog. **Rejected:** generated formula text (the 500-character limit would allow about 25 members and a
round trip through quoting); a new server `in` node (no gain until groups need more than 49 members).
