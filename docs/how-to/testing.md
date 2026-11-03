---
components: [src/DashboardBuilder/Features/Core/, tests/js/, tests/live/]
---
# Testing

How to run the .NET and JS suites, what each covers, and the manual smoke and live checks.

## Test

```bash
cd /unified/user/cj/web_development/prototype/dashboard_builder
dotnet test                                  # .NET suite
dotnet test --filter Identifier              # one class
~/.nvm/versions/node/v24.20.0/bin/node --test tests/js/*.test.mjs   # JS unit tests (pure modules)
```

Node 24 is installed through nvm (not on the default `PATH`). Its built-in `node --test` runs the JS
tests with no packages. They import the pure modules straight from `src/DashboardBuilder/Features/`.

In the table below, `P##` tags (P28, P33 …) name the product phase whose cases a test covers, and
`D##` is a decision ID in [decisions-platform.md](../decisions/decisions-platform.md).

| Test class | Covers |
|---|---|
| `IdentifierTests` | validate/quote with hostile names — the highest-value test |
| `ClickHouseTypeTests` | type string → display category |
| `ConnectionEndpointTests`, `SchemaEndpointTests` | endpoint contracts, 409 without a connection, 404 on unknown names, removed endpoints 404 |
| `ErrorContractTests` | the `{ error, field? }` shape, 400/413/500 mapping, `SafeError` 502 vs 500 split, no credential in a body |
| `ValidationTests` | host / port / length validators and every limit at the bound and bound + 1 |
| `FilterTests`, `TypedFilterTests` | `BuildCondition` / `BuildSingleTableFilters` — scalar, `in` arrays, `between`, hostile operators; typed value conversion per category, `Date` rejects a time |
| `StatisticalTests` | histogram / box-plot shapes and filters, `ClampBuckets`, `ClampDistinct` |
| `ExportTests` | `CsvUtil` RFC-4180 quoting + formula-injection guard |
| `CertificateValidationTests` | the TLS bypass gate (D11) |
| `QueryGuardTests` | database-level guards: `readonly=2`, time limit, cancel-on-disconnect, the step-down on codes 164/452, the 504 timeout messages |
| `TruncationTests` | probe-row limit, trimming, the `truncated` flag in the JSON |
| `tests/js/richer-filters.test.mjs` | ops per field type, text-match / relative / top-N validity, relative → bound `between`, stat charts skip top-N |
| `JoinTypeTests` | inner / left accepted, anything else 400; `join_use_nulls` only with a left join and a server that takes settings |
| `RicherFilterTests` | text match bound + case-insensitive (hostile text never in SQL), text-only, top-N needs a measure and a whole number 1–1000, histograms refuse it |
| `ResultCacheTests` | P33 cache key: `fresh` ignored, no password, separate entries per user / server / request / cap |
| `ScaleTests` | `offset` / export-limit / `dateBucket` validation, grain → function whitelist, `auto` grain choice |
| `tests/js/query-runner.test.mjs` | latest-wins gate, result cache, truncation notice |
| `tests/js/workbook-model.test.mjs` | workbook round-trip, no password, hard failures, per-field repair + issue list, caps, storage key |
| `tests/js/api-base.test.mjs` | the API base path under a proxy prefix and at the root, `errorMessage` shapes |
| `tests/js/validate.test.mjs` | each parser and its edge cases (blank, `1e3`, `0x10`, IPv6, over-length), `LIMITS` |
| `tests/js/filter-rules.test.mjs`, `toolbar-rules.test.mjs` | `checkFilter` / `checkAdd` / `viewCounts`; tool visibility per chart type |
| `tests/js/viewbar-model.test.mjs`, `resizer.test.mjs` | every chart type has an icon; sort-picker summary; resize width clamping |
| `tests/js/period-model.test.mjs` | presets and calendar edges, previous / last-year comparison (29 Feb), Date vs DateTime range filter, change / tone / %, row alignment, target |
| `tests/js/parameters-model.test.mjs` | value checks by type / list / range, bound filters read the value (missing → empty), Top N from a parameter (clamped), saved-parameter checks; workbook case: round-trip and orphan references unlinked |
| `tests/js/analytics-model.test.mjs` | reference values, exact linear / quadratic / log fits and R², forecast extension, totals by aggregation |
| `tests/js/history.test.mjs` | undo / redo / redo cleared by a new edit, per-dashboard, copies, bounded; fit modes |
| `tests/js/table-calc.test.mjs` | each calculation, blanks, competition rank (Other unranked), along Columns vs Rows partitions, renamed measures, `%` suffix |
| `tests/js/date-parts.test.mjs` | part steps (Date stops at day), labels per part, only grouping parts relabel their own key |
| `DatePartTests` (.NET) | each part → one function; auto / exact untouched; hostile / unknown parts rejected (400) |
| `tests/js/action-model.test.mjs` | link templates: https-only, host required, `{value}` encoded and unable to escape its slot or change the host |
| `tests/js/workbook-model.test.mjs` (P28 case) | field settings round-trip; bad keys / aliases / aggregations dropped and counted |
| `tests/js/workbook-model.test.mjs` (P39 cases) | bookmarks round-trip with dashboard index, selection and shared filters; bad bookmarks / link actions dropped and reported |
| `tests/js/workbook-model.test.mjs` (P40 cases) | shared filters round-trip / cap 4 / bad ops dropped; field choices kept, shown field included, junk dropped |
| `tests/js/theme-model.test.mjs` | **every preset and derived custom accent passes contrast in light and dark**, refusals, palettes, saved-theme checks |
| `tests/js/p36-charts.test.mjs` | waterfall steps (incl. below zero), round maxima, small-multiples grid, fit rules and registration of the seven P36 types |
| `tests/js/gantt-model.test.mjs` | Gantt bars (number / date start, skipped rows, calendar-day lengths across a DST change), axis time, label margin, registration |
| `tests/js/conditional-model.test.mjs` | scale tints (sequential / diverging, midpoint), **every tint ≥ 4.5:1 light and dark**, data bars from zero, first-match rules |
| `tests/js/scale-model.test.mjs` | table paging plan + progress, Other row, date-grouping plan, zoom past 1,000 categories, canvas mark counts |
| `tests/js/chart-fit.test.mjs` | per-category slots (grouped, horizontal, heatmap), label rotation by pane width, no minimum for pie/scatter/treemap |
| `tests/js/relation-rules.test.mjs`, `table-filter.test.mjs`, `empty-state.test.mjs`, `icons.test.mjs`, `contrast.test.mjs`, `format.test.mjs` | the other pure modules |
| `tests/js/tokens.test.mjs` | no retired token, no hex outside `:root`, dark block redefines the surfaces, no stylesheet reads `prefers-color-scheme`, glass fallbacks cover dark |
| `tests/js/scheme.test.mjs` | System / Light / Dark resolution against the OS, unknown stored values → System, and `scheme-boot.js` agreeing with `resolveScheme` (incl. blocked storage) |

## Smoke and live checks

**Error-contract smoke test.** Each of these returns the documented status and a `{ error }` body:
malformed JSON, an empty body, wrong types, an oversized body, 17 filters, `limit: 0`, a text value on a
number column, and `POST /api/query {}` (400 "'from' is required.").

**Live checks** (the repo has no CI):

- `tests/live/calc-smoke.mjs` tests calculated fields against the shared test ClickHouse server. It
  needs credentials, so it is a manual check; re-run it before every deploy.
- `tests/live/calc-ui.mjs` needs only the dev app.
- `node tests/live/run-ui-all.mjs` starts the dev app once (a free port, or `UI_PORT` when set and free;
  `ONLY=calc,rows` filters) and runs every `tests/live/*-ui.mjs` browser check against it. It then stops
  the app by port and prints a pass / fail line per check. The full run takes more than ten minutes, so start
  it in the background. Run it from the solution root before merging a change to the worksheet; it must end
  `fail=0`.
- `tests/live/model.mjs` holds the setup the checks share. `relateTables` draws a relationship on the canvas
  and is called after two tables load, because a table card with no relationship is held out of the field
  pane once the model has two cards. `NEW_CALC`, `PAGE_CHIP`, `CALC_NAMES` and `CALC_LIST_TEXT` reach
  calculated fields, which live in the sidebar's Calculated fields dialog. They open it only while needed,
  because a dialog left open blocks real mouse and key input.
- `tests/js/calc-limits.test.mjs` keeps the three copies of the calculation limits equal.
