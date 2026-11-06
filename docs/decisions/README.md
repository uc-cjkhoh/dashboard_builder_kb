---
components: []
---
# Decisions & rationale

The "why" record: each architecture or design decision, its reason, and what was rejected. When a
decision changes, **edit its entry in place** (and the doc it affects) in the same change. To resolve an
open question, promote it to a decision.

## Where each decision lives

| Decisions | File |
|---|---|
| D1–D25 | this file |
| D26–D60, D65–D68, D73 (calculated fields, parameters, member labels, groups, split / unpivot) | [decisions-calculated-fields.md](decisions-calculated-fields.md) |
| D61–D64, D69, D71–D72, D74, D79–D81 (dashboards, hierarchies, option controls, desktop-only, compound join keys, Gantt, stories) | [decisions-dashboards.md](decisions-dashboards.md) |
| D70 (recent connection sources) | [decisions-connection.md](decisions-connection.md) |
| D82 (calculated fields as row filters), D84 (a filter on an aggregated measure, `HAVING`) | [decisions-filters.md](decisions-filters.md) |
| D83 (groups on whole-number and true/false fields) | [decisions-calculated-fields.md](decisions-calculated-fields.md) |
| D75–D77 (`NULL`, `IN` / `BETWEEN`, keyword `IF`), D78 (`MAKEDATE`, `DATENAME`) | [decisions-logic.md](decisions-logic.md) |

## Open questions

| # | Question | Leaning |
|---|---|---|
| **O1** | Should workbooks persist on the server (shared across browsers/users)? | Browser persistence is decided ([D21](decisions-platform.md#d21--workbooks-persist-in-the-browser-not-on-the-server)). Server-side storage only with accounts — see [platform.md](../development/backlog/platform.md). |
| **O2** | Where are multiple saved connections stored? | One active connection per session, not saved. Later: named profiles **without** persisting passwords server-side. |
| **O3** | How far does dashboard composition go? | Worksheets and dashboards are separate tab kinds and a dashboard's data is built ([D61](decisions-dashboards.md)); the board canvas and its editing are built ([D62](decisions-dashboards.md), [D63](decisions-dashboards.md)); composition would revisit O1 only if dashboards were shared. |
