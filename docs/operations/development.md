# Development — build, run, test

The dev inner loop on AlmaLinux 9. Production hosting is [deployment.md](deployment.md).

## Where the code lives

| What | Path |
|---|---|
| Solution root (run `dotnet` here) | `/unified/user/cj/web_development/prototype/dashboard_builder/` (`DashboardBuilder.slnx`) |
| App project | `…/src/DashboardBuilder/` |
| Tests | `…/tests/DashboardBuilder.Tests/` (xUnit) |
| This KB (docs only) | `/unified/user/cj/knowledge/web_development/dashboard_builder/` |

Build host is **`10.168.49.20`** (`dataweb`); KB and app share its filesystem, so a KB session can build
and test the app directly — no SSH needed ([D9](../reference/decisions.md#d9--app-source-lives-outside-the-kb-on-the-build-host)).
The app folder is a **local git repo** (no remote; keep `keys/` ignored), so changes can be reviewed as
diffs; the KB is a separate git repo. Never scaffold code into the KB. SSH and ClickHouse credentials
are in the git-ignored [credentials.local.md](credentials.local.md).

## Prerequisites

- **.NET SDK 10** — already on the host's global `PATH` (`/usr/lib64/dotnet`, `dotnet --version` →
  `10.0.108`; a 9.0 SDK is also present but unused). Elsewhere: `sudo dnf install -y dotnet-sdk-10.0`.
- **A ClickHouse to point at.** The real target is TLS-only on `8443` with a self-signed cert — tick
  Secure and the cert opt-in, and use a network-enabled account
  ([sharp edges](../conventions/sharp-edges.md#clickhouse)). For quick local testing a throwaway
  container on plain HTTP works (connect with Secure off, port `8123`):

  ```bash
  podman run -d --name ch -p 8123:8123 -p 9000:9000 clickhouse/clickhouse-server
  curl 'http://localhost:8123/' --data 'SELECT 1'
  ```

  Load a couple of related tables so drag/drop, relationships and joins have something to show.

## Run

```bash
cd /unified/user/cj/web_development/prototype/dashboard_builder/src/DashboardBuilder
dotnet run                                   # launch profile → http://localhost:5080
```

To run on a spare port (avoid the live port `5105`, and note 5080 may already be in use), skip the
launch profile and pass the URL explicitly — an `ASPNETCORE_URLS` environment variable or the launch
profile otherwise pins the port:

```bash
dotnet run --no-launch-profile --urls http://localhost:5180
```

To smoke-test under the proxy prefix:

```bash
PathBase=/dashboardbuilder dotnet run --no-launch-profile --urls http://127.0.0.1:5180
curl -s -o /dev/null -w '%{http_code}\n' http://127.0.0.1:5180/dashboardbuilder/
curl -s -o /dev/null -w '%{http_code}\n' http://127.0.0.1:5180/dashboardbuilder/features/Dashboard/dashboards.js
```

With `PathBase` set, `/` itself is not served. Stop a dev run **by port**
(`fuser -k 5180/tcp`) — never `pkill -f DashboardBuilder.dll`, which also matches the live service.

Error-contract smoke test (each returns the documented status and a `{ error }` body): malformed JSON,
an empty body, wrong types, an oversized body, 17 filters, `limit: 0`, a text value on a number column,
`POST /api/query {}` (400 "'from' is required.").

## Build & publish

```bash
cd /unified/user/cj/web_development/prototype/dashboard_builder
dotnet build -c Release
dotnet publish src/DashboardBuilder/DashboardBuilder.csproj -c Release -o publish
```

Publish is framework-dependent; `Features/**/*.css|js` are copied as content alongside the DLL. Keep
ClickHouse credentials out of source, config and logs.

## Test

```bash
cd /unified/user/cj/web_development/prototype/dashboard_builder
dotnet test                                  # .NET suite
dotnet test --filter Identifier              # one class
~/.nvm/versions/node/v24.20.0/bin/node --test tests/js/*.test.mjs   # JS unit tests (pure modules)
```

Node 24 is installed through nvm (not on the default `PATH`); its built-in `node --test` runs the JS
tests with no packages. They import the pure modules straight from `src/DashboardBuilder/Features/`.

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
| `tests/js/p36-charts.test.mjs` | waterfall steps (incl. below zero), round maxima, small-multiples grid, fit rules and registration of the six P36 types |
| `tests/js/conditional-model.test.mjs` | scale tints (sequential / diverging, midpoint), **every tint ≥ 4.5:1 light and dark**, data bars from zero, first-match rules |
| `tests/js/scale-model.test.mjs` | table paging plan + progress, Other row, date-grouping plan, zoom past 1,000 categories, canvas mark counts |
| `tests/js/chart-fit.test.mjs` | per-category slots (grouped, horizontal, heatmap), label rotation by pane width, no minimum for pie/scatter/treemap |
| `tests/js/relation-rules.test.mjs`, `table-filter.test.mjs`, `empty-state.test.mjs`, `icons.test.mjs`, `contrast.test.mjs`, `format.test.mjs` | the other pure modules |
| `tests/js/tokens.test.mjs` | no retired token, no hex outside `:root`, dark block redefines the surfaces |

**Visual review:** there is no headless browser on the build host, so look at light **and** dark (switch
the OS / browser colour scheme) on a spare dev port before deploying a UI change.

**DOM behaviour:** there's no headless browser (Chromium can't launch here), but the real modules can be
driven in **jsdom** against the rendered page and a fake API. Install jsdom into a scratch directory (not
the repo) and import `Features/Shell/app.js` with jsdom's window objects exposed as globals — including
`CustomEvent` and `EventTarget`, so the store's bus and `document` share one realm. Also syntax-check
changed modules (`node --check <file>`), run the smoke test above, and do a manual pass: connect → drag a
table → tick keys → draw a 1:N link → add a dashboard → build a chart → reload (the workbook restores).
A live-ClickHouse run is manual: the only account in `credentials.local.md` is localhost-only.

## Gotchas

- No ClickHouse reachable → connect fails by design; check the container / `curl` first.
- New CSS/JS outside `Features/` won't be served or published.
- If the UI goes inert after rebuilding, hard-refresh once (stale ES modules).
- More: [sharp-edges.md](../conventions/sharp-edges.md).
