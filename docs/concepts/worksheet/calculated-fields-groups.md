---
components: [src/DashboardBuilder/Features/Calc/group-dialog.js, src/DashboardBuilder/Features/Calc/group-model.js, tests/live/group-smoke.mjs]
---
# Calculated fields — group fields

A group field is a calculation whose tree is generated, not parsed. The rest of the feature: [calculated-fields.md](calculated-fields.md).

A field's **⋯** menu has **Group…** (T02-30). It puts a text column's members into named groups, saved as a **group calculation**: `{ id, name: "region (groups)", formula: "", group: { field, groups: [{ name, members }] } }`.

### The Group dialog

Code: `group-dialog.js`; rules in `group-model.js`.

- It names the field and adds groups (≤ 50, 1–80 characters, unique).
- Each member (the field's top 200, from the distinct-values read; NULL is skipped) goes in a group or stays **not grouped**.
- **Label ungrouped members** (optional, default "Other", ≤ 80 characters) folds every ungrouped non-NULL member into that one label; NULL stays NULL. The 80-character cap is client-side, like group names; the server accepts up to 100. The label may not be a group's name or an ungrouped member.
- **Refused:**
  - number, date and true/false fields, and UUID, IP address and enum columns (the engine compares text only; ClickHouse has no common type for those, pinned by `tests/live/group-smoke.mjs`);
  - a group name equal to a member that stays ungrouped (it would merge their rows).

### Using a group field

It is an ordinary calculated dimension afterwards: a chip in the pane (Edit… reopens this dialog, Duplicate copies the groups), a pill, and a text value in formulas (`[region (groups)]`).

- A member in no group keeps its own value (without the label). NULL stays NULL.
- A group-calculation pill takes no click-selection ([D33](../../decisions/decisions-calculated-fields.md#d33--calculated-fields-are-refused-wherever-a-plain-column-is-assumed)), and member labels do not apply to it.

### How it compiles

- `compileCalculation` takes the tree straight from `groupTree`, never formula text, so the 500-character limit does not apply.
- The tree is `CASE WHEN member = 'a' OR … THEN 'Group' … ELSE <the field> END`: one WHEN per group, each an OR (balanced, so shallow) of `=` against `str` literals. These are bound parameters; nothing is quoted into SQL.
- With the label on, a last `WHEN NOT isnull(field) THEN '<label>'` is added.
- **Size limit:** the **node limit (200)** bounds it at 2 + 4 nodes per member — **49 members across all groups**, **48** with the remainder label (`maxMembersFor`). The dialog says so and disables Save, and the server refuses a bigger tree too.
- Code: `Calc/group-model.js`.
