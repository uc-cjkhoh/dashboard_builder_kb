# Decisions — calculated fields

Continues [decisions.md](decisions.md) (D1–D25). Behaviour: [calculated-fields.md](../features/calculated-fields.md).
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
