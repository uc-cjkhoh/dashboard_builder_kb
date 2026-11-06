---
components: []
---
# Backlog: calculations and table calculations

Calculation work not yet built. Entries are in dependency order. Format: [index.md](index.md#how-to-read-an-entry).

Built behaviour (functions, parameters, statistics on plain measures): [calculated-fields.md](../../concepts/worksheet/calculated-fields.md).

Rules for new work:

- Every new function goes through the whitelisted expression tree, never formula text on the server.
- LOD (level of detail) terms and any new function whitelist entry keep the endpoint's limits and response shape. The endpoint never accepts SQL text.

- **Logic functions remainder** — Open: a date literal (`DATE('2024-01-01')` works today; a bare literal would need a type and a bound `Date` parameter), `IN` over a date (needs the date literal), a boolean compared with `=`, and an `IN` list read from a field or another source. Needs: none.
- **Text functions remainder** — Open: regular expressions, a `FIND` start position, a `MID` start or length that is optional, and a `LEFT` / `RIGHT` / `MID` length or `SPLIT` position or separator that is a field or computed value (a `[@Parameter]` works). Needs: none.
- **Date functions remainder** — Open: `TODAY()` / `NOW()` (non-deterministic; need an owner decision, [D60](../../decisions/decisions-calculation-functions.md#d60--no-today--now)), fiscal calendars and a fiscal year start, date-part bucketing of a calculated date (a calculated date dimension groups per distinct value; `DATETRUNC` is the workaround), `DATEPARSE` with a format, time zones, a unit, amount or part that is a field (a `[@Parameter]` works), and further `DATENAME` parts (year, quarter). Needs: none.
- **Parameters remainder** (IDs: T04-31, T04-32; priority P2) — Open: analytics band bounds, the moving-average window and a trend forecast cannot bind a parameter (only a Constant reference line can); a step size exists only for a number range (not for "any value"); a calculated field reads a parameter only through `[@Name]` (no parameter picker in the pill menu). Needs: none.
- **Filters on calculated fields remainder** — Built: a row-level calculation as a Filters field ([D82](../../decisions/decisions-filters.md#d82--a-calculated-field-is-a-row-filter-applied-before-grouping)). Open: an aggregate calculation as a filter (`HAVING`; waits for level of detail), a calculated filter shared across dashboards, `in the` (relative date) and Top-N on a calculation, a calculated Pages field, drill level or date-range field; the histogram and box-plot views cannot use a calculation (their filters skip a calculated one); click-to-filter is off when the primary dimension is a calculation; "View data" leaves a calculated filter out. Needs: none.
- **Table-calculation polish** (IDs: T05-07, T05-09, T05-10, T05-11, T05-12, T05-13, T05-14, T05-15, T05-16, T05-17, T05-19, T05-21; priority P1–P2) — Built: percentile rank (T05-09 partly), compound growth rate (per period since the group's first value), compute-using a chosen set of dimensions (the rest restart). Open: YTD total and YTD growth (need a restart at a date-hierarchy level, listed below), assistance overlay. Partial: year-over-year is a comparison series only; no per-dimension restart interval (restart at a level of a date hierarchy), no addressing by specific members, no scope/at-level options; no duplicate-as-crosstab; no bump preset; the moving-average window is not parameter-bindable. Needs: none.
- **Table-calculation engine order** — table calculations run in the browser on the bounded result, after the server aggregate; filter-order rules between filter classes are written down before more calculations are added (the evaluation-order popover already lists the six stages). Needs: none.
- **Table-calculation formulas** (IDs: T05-18; priority P2) — Open: only the fixed quick-calculation list exists; no custom table functions. Needs: table-calculation polish.
- **Level of detail** (IDs: T05-22, T05-23, T05-24, T05-25, T05-26, T05-27; priority P2) — Open: `FIXED`, `INCLUDE`, `EXCLUDE`, first-event cohort, aggregate-per-entity-then-average, higher-level benchmark. Needs: filter-order rules written down first. LOD compiles to SQL; whether it is a subquery or a window is settled in [platform.md](platform.md).
- **P25 data-pane authoring** (priority P1; effort L) — Open: sets (named member subsets), bins (numeric buckets), folders. Groups and reusable hierarchies are in [data-model.md](data-model.md). Needs: calculated fields (built); a decision recorded before building.
