---
components: [src/DashboardBuilder/Features/Calc/split-model.js, tests/live/unpivot-smoke.mjs]
---
# Decisions — parameters, groups, splits

D65–D68 and D73: parameters, member labels, group fields, split and unpivot. Lookup: [README.md](README.md#where-each-decision-lives). Behaviour: [calculated-fields.md](../concepts/worksheet/calculated-fields.md). Edit an entry in place when it changes.

### D65 — A parameter is read as `[@Name]` and becomes a literal on the client
Parameters get their own marker, `[@Name]`, which is not dot-split.
- **Why a marker:** `[Name]` already means a calculation and `[table.column]` a field ([D42](decisions-calculated-fields.md#d42--reference-syntax): names may not contain `.`),
  while a parameter name may hold anything.
- **Resolved at parse time** against the workbook's parameters. An unknown one is a resolver error, so a deleted parameter
  reads like any other dangling reference ([D47](decisions-calculated-fields.md#d47--a-broken-calculation-stays)).
- **Substituted on the client.** The value replaces the reference in the expanded tree **before** type-checking, as `num` /
  `str` / `DATE(str)`. So there is no server change, every value stays a bound literal, and the request (and so the cache key)
  changes with the value.
- A parameter can fill the literal-only arguments (`LEFT` length, `DATEADD` unit and amount) while keeping their range checks.
- Text parameters over 100 characters are refused rather than truncated (D54's rule).
- **Rejected:** a `param` node on the wire (a new server node, validation and cache story for no gain); bare `[Name]` falling
  back to a parameter (silent ambiguity when a calculation is later added).

### D66 — Deleting a parameter a formula reads asks; renaming rewrites the formulas
Like deleting a calculation a sheet uses, deleting a parameter that a formula mentions asks first. Afterwards the calculation
shows the broken-calculation state ([D47](decisions-calculated-fields.md#d47--a-broken-calculation-stays)) with its formula untouched, so re-adding the name heals it.
- **Why:** refusing outright would block a legitimate clean-up; silently rewriting would hide the damage.
- The scan is textual (`[@Name]` anywhere in the formula, including inside a text literal), so it can only over-ask.
- A rename rewrites `[@Old]` the way a calculation rename rewrites `[Old]`.
- The reference line stores a parameter id (`analytics.ref.param`) and falls back to its own value when the parameter is gone
  (the workbook open also unlinks it, with a note).

### D67 — Member labels are display-side, keyed by the raw value, positioned by the query's key order
A member label (`memberAliases`, a field setting) changes only the text drawn. The query, groups, sort order, filters, drill
path values, selections and member colours keep the raw value, so a label can never change what a click filters or which rows
a group holds.
- **Labels are unique within a field:** not equal to another member's label or raw value. `setAlias` and the dialog refuse a
  duplicate; the workbook open drops the later one and reports it. **Why:** panels, Sankey nodes and legend items key by the
  drawn text, and two members drawn alike would merge.
- CSV export carries raw values, never labels.
- **One drawing point.** `renderWorksheet` is the one place that draws categories. It wraps the category formatter as
  `fmtCat(key, position)` (`withMemberLabels`), where `position` is the key's index in `planDims(sheet).keyOrder`, so two fields
  can label the same raw value differently. Callers that pass no position get the plain format.
- **Limits:** maps are null-prototype and read by own key (a member can be `__proto__`). The per-field cap is 200 labels; a
  label is ≤ 80 characters, a key ≤ 100.
- A selection chip's text is baked when the member is picked (like the drill label) and does not follow a later edit.
- **Rejected:** rewriting the result's keys before drawing (clicks, Path sorting and the colour-split pivot would see labels;
  equal labels would merge rows); one global value → label map (no per-field meaning).

### D68 — A group field is a calculation whose tree is generated, not parsed
Groups are stored on a calculation (`group` beside an empty `formula`), not in `fieldMeta`.
- **Why:** a field can have several group sets, and each becomes a pill, a chip and a value other formulas can use. The
  workbook, undo, pills and query path already know calculations.
- **Size bound.** `compileCalculation` builds the tree directly (`groupTree`), so the 500-character formula limit does not bound
  it; the engine's 200-node limit does: 2 + 4 nodes per member = 49 members in all. It is refused at edit time with a plain
  message (`checkGroupSpec`), never at query time, and the server independently refuses a larger tree.
- **Tree shape.** Members are `str` nodes (bound), the OR is balanced (depth ≤ 12), and ELSE is the field itself: an ungrouped
  member keeps its value, and NULL stays NULL (a CASE condition on NULL is false).
- **Text fields only** (the engine compares text with text), and only those whose ClickHouse type is String-like. UUID, IPv4,
  IPv6 and enum columns fail in ClickHouse (no common type with the text branches; `toString` in the tree was not adopted), so
  they are refused up front.
- A group name equal to an ungrouped member is refused.
- **Remainder label (optional)** adds one last `WHEN NOT isnull(field)` (4 nodes, so 48 members). NULL is left empty so it stays
  distinguishable. The label must not equal a group name. The rest is in the backlog.
- **Rejected:** generated formula text (the 500-character limit would allow about 25 members, plus a round trip through
  quoting); a new server `in` node (no gain until groups need more than 49 members).

### D73 — A split is generated calculated fields; an unpivot is a bounded preview
**Split** adds nothing to the engine. The field menu's **Split…** plans one ordinary calculated field per piece
(`SPLIT([db.table.col], 'sep', k)`, `Calc/split-model.js`).
- Pills, queries, caching and the workbook already work, and the separator and position stay the literals D54 requires.
- The piece count is the user's (2–10), not discovered from the data, since a discovery query would add an unbounded read for
  a convenience.

**Unpivot** changes the row grain, which a calculated field can't, so it is a server read like Union.
- `POST /api/unpivot` builds `arrayJoin([(name, value), …])` over the chosen same-kind columns: names bound, columns quoted
  and catalog-checked, cells cut in SQL.
- ClickHouse applies the statement's `LIMIT` after the `arrayJoin` (pinned by `tests/live/unpivot-smoke.mjs`), so one
  `LIMIT limit + 1` bounds the unpivoted rows.
- Same-kind is required so the one `Value` column is comparable. Mixed kinds are refused (400), not silently cast.
- It is a preview only until a query source exists for union and unpivot together.
