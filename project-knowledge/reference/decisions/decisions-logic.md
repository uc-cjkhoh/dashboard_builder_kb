# Decisions — calculation logic

Continues [decisions.md](decisions.md). This file holds D75–D77 (`NULL`, `IN` / `BETWEEN`, keyword `IF`). Behaviour:
[calculated-fields.md](../../features/worksheet/calculated-fields.md#logic-functions). Edit an entry in place when it changes.

### D75 — `NULL` has no type of its own; it takes the type of the results beside it
`NULL` is a leaf node (`{ "k": "null" }`) whose internal type is `null`. Where it may stand is the whole rule:
- **Allowed** as a `THEN` / `ELSE` result of `IF` / `CASE`, and as either side of `IFNULL`. It takes the type of the first
  non-`NULL` result (`IF c THEN 'x' ELSE NULL END` is text; `CASE WHEN c THEN NULL WHEN d THEN 1 END` is a number).
- **Refused** everywhere else, by the type table's ordinary messages (`Arithmetic needs numbers — NULL is null.`).
  A formula that is only `NULL`, or whose results are all `NULL`, has no type (`NULL needs another value to take its type
  from — use it as an IF, CASE or IFNULL result.`).
- **`x = NULL` is refused**, not answered `NULL`: it can never match, so the message points at `ISNULL(value)`.
- **Why:** a calculation's type decides its role (dimension or measure) and the checks on every consumer. An untyped value
  would leak into arithmetic and aggregates, where it has no meaning. This is the smallest rule that gives `ELSE NULL` its
  usual use (leave a row out of a group) and is checked identically on both sides.
- **Rejected:** a `NULL` that fits any slot (every consumer needs an "unknown type" branch); casting it to a chosen type
  (`CAST(NULL AS text)` syntax for a convenience).

`TRUE` / `FALSE` are boolean literals (`{ "k": "bool", "v": true }`). They compile to the fixed SQL keywords `true` / `false`,
and `NULL` to `NULL`, since nothing the user typed reaches the SQL. A boolean still can't be compared with `=`
(write the field itself), so these are for `IF` results and `AND` / `OR`.

### D76 — `IN` is a list node of bound literals, at most 50; `BETWEEN` is two comparisons
- `x IN (a, b, …)` is `{ "k": "in", arg, list }`; `NOT IN` wraps it in `not`. The list holds number or text literals (a
  negated number counts), written in the formula, 1 to `CALC_LIMITS.inList` (50, `CalcLimits.MaxInList`), all of the
  value's type; the value is a number or text. Every list value is a bound parameter. A `[@Parameter]` works because it is
  replaced by a literal first; a date parameter is not a list value.
- Anything else is a 400, never clamped: no values or more than 50 (`IN takes 1 to 50 values.`, at `….calc.list`), a field or
  expression in the list (`….calc.list.<i>`), a mixed type, a date value.
- **Why a node, not ORs:** a chain of `=` joined by `OR` nests as deep as the list is long and would hit the depth limit at
  about ten values. The list node costs one level.
- **`BETWEEN`** is parser sugar for `x >= a AND x <= b` (ends included; `NOT BETWEEN` wraps it in `not`), so it adds no wire
  node and inherits the comparison rules (number, text or date; never a mix). `x` is written twice in the tree and
  counts twice against the node limit.
- **Rejected:** `IN` over a date (there is no date literal to put in the list; compare with `BETWEEN` and `DATE()`); a list
  read from a field or a subquery (not bounded, not bindable).

### D77 — The keyword `IF` is another spelling of `CASE WHEN`
`IF c THEN a [ELSEIF d THEN b]… [ELSE e] END` parses to the same `case` node as `IF(c, a, e)`, `IIF` and `CASE WHEN`, so
the server, the compiler and the workbook see nothing new. `IF (c) THEN …` starts like the function, so the parser decides the form from the tokens, without backtracking: a comma at
depth 1 of the parentheses (or an unclosed one) is the function; anything else is the keyword form. **Rejected:** trying the
function and retrying as the keyword form on failure: it re-parses nested `IF (…) THEN` twice per level, so 22 levels took
44 s and the 500-character limit allows about 30. The cost now is one token scan per `IF (`.
- No `ELSE` gives NULL, like `CASE`. `ELSEIF` after `ELSE` is a parse error.
