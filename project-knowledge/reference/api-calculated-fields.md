# API: calculated-field trees (`calc`)

The `calc` expression tree a dimension, measure or Top-N `topBy` may carry on `/api/query`: nodes, role and typing rules, error wording. The rest of the API: [api.md](api.md). How a tree compiles to SQL: [clickhouse-calculations.md](clickhouse-calculations.md).


A row or column dimension (`ColumnRef`), a measure (`MeasureRef`) and a Top-N `topBy` may carry a
`calc` expression tree; the browser parses the formula and sends only the tree — no formula text
reaches the server or SQL.

```json
{ "db": "shop", "table": "orders", "column": "Margin", "agg": null,
  "calc": { "k": "bin", "op": "/",
    "l": { "k": "agg", "fn": "sum", "arg": { "k": "field", "db": "shop", "table": "orders", "column": "amount" } },
    "r": { "k": "agg", "fn": "sum", "arg": { "k": "field", "db": "shop", "table": "orders", "column": "qty" } } } }
```

## Nodes (discriminator `k`)

| `k` | Members |
|---|---|
| `field` | `db`, `table`, `column` |
| `num` | `v`, finite |
| `un` / `bin` | `op: "-"` / `op` ∈ `+ - * /` |
| `str` | `v`, ≤ 100 characters, bound as a `String` parameter |
| `cmp` | `op` ∈ `= != < <= > >=`, `l`, `r` |
| `logic` | `op` ∈ `and or`, `l`, `r` |
| `ifnull` | `l`, `r` |
| `case` | `whens`: `[{ "c": cond, "t": result }]` (at least one) and an optional `else`. `IF`/`IIF` are one arm plus `else` |
| `not` / `isnull` | `arg` |
| `fn` | `fn` ∈ `text lower upper trim ltrim rtrim len left right mid find replace concat contains startswith endswith icontains istartswith iendswith split datediff dateadd year month day quarter week weekday date`, `args`: array |
| `agg` | `fn` ∈ `sum avg min max count countd median stddev variance percentile attr`, `arg`, and `p` for `percentile` |

- In `agg`, `count` counts non-NULL values (as `countNonNull`) and `countd` counts distinct values.
- `p` is a finite number 0..1, required for `percentile` and refused on every other function (400 at
  `….calc.p`, "PERCENTILE needs a fraction between 0 and 1." / "SUM takes no fraction."). It is bound as a
  `Float64` parameter.
- Every referenced table must already be in the query (`from` or a join). Otherwise it is the usual 400
  "Field references a table not in the query."

## Rules

- **With `calc` set**, `db` / `table` / `column` are not used in SQL, but they must still be present.
  An absent `column` is a binding 400, "'measures[0].column' is required."; send empty strings when there
  is no label.
- **`column` is only the display label** (≤ 60 characters; longer is a 400 at `….column`). It is
  echoed in the result's `rowDimensions` / `measures`. An empty `column` falls back to `"calculation"`.
- **Role rules** (400, field `….calc`):
  - An **aggregate** tree (one that contains an `agg` node) is valid only as a measure or `topBy` with
    `agg` absent or `null`. As a dimension it is a 400.
  - A **row-level** tree as a measure / `topBy` needs `agg` ∈ `sum`, `avg`, `min`, `max`,
    `countDistinct`, `countNonNull`, `median`, `stddev`, `variance`, `attr`. `count` of rows is rejected
    because it would ignore the calculation. `percentile` has no row-level form. `sum` / `avg` / `median` /
    `stddev` / `variance` need a number.
  - A row-level tree is valid as a dimension. A calculated dimension takes no `datePart` (`….datePart`) and is never date-grouped by `dateBucket`.
- **Text-function typing** (400 at `….calc.args.<i>` or the call):
  - A text argument must be text ("LOWER needs a text — orders.amount is number.").
  - The argument count is fixed ("LEFT takes 2 arguments.", "CONCAT takes 2 to 10 arguments."). The `LEFT`/`RIGHT` length is a number literal 0..1000. The `SPLIT` position is a literal 1..1000 and its
    separator a text literal of 1..20 characters ("SPLIT's separator must be text written in the formula, 1 to 20 characters.").
  - An unknown name is "Unknown function x.". Limits: `CalcLimits.MaxCount` / `MaxSeparator` / `MaxConcat`, mirrored in `CALC_LIMITS`.
- **Date-function typing** (400 at `….calc.args.<i>`; arity is fixed, "DATEDIFF takes 3 arguments."):
  - A date argument must be a date ("YEAR needs a date — orders.status is text. Use DATE() to turn text into a date."). `DATE` takes text.
  - The `DATEDIFF`/`DATEADD` unit is a `str` node from `year quarter month week day hour minute second`, any case
    ("DATEDIFF's unit must be one of 'year', … written in the formula as text.").
  - The `DATEADD` amount is a `num` node, or `un` `-` over one: a whole number within ±100000 ("DATEADD's amount must be a
    whole number from -100000 to 100000 written in the formula."; `CalcLimits.MaxDateAmount`, `CALC_LIMITS.dateAmount`).
- **Logic typing** (400 at the node path; `w0.c` is the first WHEN's condition, `w1.t` the second's result, `else`):
  - A condition must be boolean ("A condition needs a boolean — orders.amount is number.").
  - Every result has one type ("All results must be the same type — …"). A comparison takes two values of one type, never boolean ("Comparison needs two values of the same type — …").
  - `AND`/`OR`/`NOT` take booleans. A text literal is ≤ 100 characters ("A text value can be at most 100 characters.").
    A `case` needs an arm ("A CASE needs at least one WHEN.").
  - A boolean calculation is a dimension (keys `true` / `false` / `null`) or, when it aggregates, a measure. It takes no `sum`/`avg`.
- **Tree errors** name the node (`measures[0].calc.arg`, `rowDimensions[1].calc.l.r`). Examples: "SUM needs a
  number — orders.region is text.", "Unknown field orders.nope.", "Can't mix an aggregate with a
  row-level value in one formula.", "An aggregate can't contain another aggregate.", "That formula is too
  deep." / "too large.".
- **Results:** a number-typed calculation's values are numbers (division by zero → `null`). `min` / `max`
  of a text or date calculation are strings. A calculated dimension's keys are strings like any key:
  numbers in invariant form (`"0.3333333333333333"`, `"20"`), `null` for a NULL key.
