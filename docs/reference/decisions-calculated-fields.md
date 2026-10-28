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
