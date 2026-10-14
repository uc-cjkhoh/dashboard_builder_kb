# P24 plan — Task 10: docs, cleanup and deploy

Part of the [P24 plan](plan-overview.md); read its Global Constraints first. KB root:
`/unified/user/cj/knowledge/web_development/dashboard_builder`; app root as in the overview. Spec:
[§ Docs](../p24-dashboards.md#docs).

### Task 10: KB docs, retire the spec + plan, merge, publish, deploy

**Files (KB):** new `docs/features/dashboards.md`; modify `docs/features/tabs.md`, `docs/features/workbook.md`,
`docs/features/worksheet.md`, `docs/reference/data-model.md`, `docs/reference/frontend-modules.md`,
`docs/reference/decisions.md`, `ARCHITECTURE.md`, `docs/design/layout.md`, `docs/proposals/roadmap.md`,
`docs/README.md`, `CLAUDE.md` (source layout + "Where things live"); delete `docs/proposals/p24-dashboards.md`
and `docs/proposals/p24/`.

- [ ] **Step 1: `features/dashboards.md` (new, ≤ 300 lines).** Current behaviour, written from the built code
  (the code wins over this plan): what a dashboard tab is; the side panel; the grid (12 columns, row height,
  limits table: widgets 12, `w` 2–12, `h` 2–24 / text 1–24, 96 rows, heading 80, body 2 000); add / move /
  resize / keyboard / overlap snap-back; widget header (Edit, Remove); text widgets; view-only widgets
  (tooltips, legend highlight, table paging — no selection, drill, Pages); stale re-run and resize without
  re-query; errors inside the widget; undo / redo; full screen, print, theme; what is per worksheet only
  (export, bookmarks). Code map: `Board/board.js`, `Board/board-layout.js`, `Dashboard/worksheet-view.js`.
- [ ] **Step 2: `features/tabs.md`** — two kinds, kind icons, **+** menu, default names "Worksheet N" /
  "Dashboard N", `LIMITS.tabs` 50 enforced at creation and import, closing a used worksheet (confirm names
  its dashboards; its widgets are removed). **`features/worksheet.md`** — "a worksheet tab" wording; the
  render path now lives in `worksheet-view.js` (one renderer shared with dashboard widgets).
- [ ] **Step 3: `features/workbook.md`** — format v2 shape, v1 → v2 migration, import issues for widgets,
  autosave key v2 with the v1 fallback. **`reference/data-model.md`** — store `tabs`, widget shapes,
  `activeView` kinds, events (`worksheet:changed`, `dashboard:changed` new meaning).
- [ ] **Step 4: `reference/frontend-modules.md`** — `chart.js` (one instance per container, container-first
  API), `worksheet-view.js`, `Dashboard/sheet-plan.js`, `Board/board.js`, `Board/board-drag.js`, `Board/board-layout.js` (pure),
  `tests/browser/` harness (`NODE_PATH=~/pw-harness/node_modules node tests/browser/run.mjs`).
  **`reference/decisions.md`** — add **D26** (Tableau-style composition, 12-column snap grid, worksheet + text
  widgets, view-only widgets, one renderer via `createWorksheetView`, browser-only persistence still under
  D21); mark **O3** answered by D26; reword D16's "a dashboard is one worksheet" to "a worksheet".
- [ ] **Step 5: `ARCHITECTURE.md`** (no code blocks) — the view layer now has worksheet tabs and dashboard
  tabs; one render path instantiated per host. **`design/layout.md`** — the dashboard canvas (grid, side
  panel, scrolling inside its panel). **`CLAUDE.md`** — add `Board/` to the source layout and a "Where
  things live" row (Dashboard canvas / layout → `Features/Board/` → `dashboards.md`); add the browser
  harness command under Build, run, test. Keep `CLAUDE.md` < 200 lines.
- [ ] **Step 6: `proposals/roadmap.md`** — P24 section keeps only 24c (cross-widget filtering) and 24d
  (stories); its Recommended-order row reads "P24c/d — cross-widget filtering, stories"; coverage row
  "Sheet tabs — worksheet / dashboard / story" → built: worksheet + dashboard tabs (P24) —
  `[dashboards.md](../features/dashboards.md)`; gap: stories → **P24d**. Also the "Biggest architectural
  gap" note: delete it (closed). Update `proposals/roadmap-bi-parity.md` P38 ("needs P24's pages") to point
  at dashboards as the built target.
- [ ] **Step 7: Retire the spec + plan.** `git rm -r docs/proposals/p24-dashboards.md docs/proposals/p24`;
  remove the spec's row from `docs/README.md` and add `features/dashboards.md` to its features table.
- [ ] **Step 8: Verify + commit the KB.** `python3 .claude/hooks/kb-verify.py --all` → `KB clean.`;
  `grep -rn "p24-dashboards\|proposals/p24" --include=*.md . | grep -v archive` → no output;
  `git add -A && git commit -m "Document P24a+b dashboards as built; retire spec and plan"` (with the
  Co-Authored-By line).
- [ ] **Step 9: Merge + publish (app).** Stop and ask the user before merging. On a yes:
  `git checkout main && git merge --ff-only p24-dashboards`; `dotnet test`; JS suite; browser harness (dev
  server on 5180, light + dark) → all pass;
  `rm -rf publish && dotnet publish src/DashboardBuilder/DashboardBuilder.csproj -c Release -o publish`.
- [ ] **Step 10: Deploy — full stop → copy → start.** 24b adds `.cshtml` partials (`Board/_Board.cshtml`,
  `Shell/Index.cshtml`), which compile into the DLL, so the asset-only copy is not enough
  ([deployment.md](../../operations/deployment.md#release-flow)). `sudo` needs a password: ask the user to
  run, as one line,
  `! sudo systemctl stop webapps-dev.dashboardbuilder && cp -r /unified/user/cj/web_development/prototype/dashboard_builder/publish/. /var/www/webapps-dev/dashboardbuilder/ && sudo systemctl start webapps-dev.dashboardbuilder`
  and warn that the restart drops every session (users reconnect; autosaved workbooks stay in the browser).
- [ ] **Step 11: Verify live.** `systemctl is-active webapps-dev.dashboardbuilder` → `active`;
  `curl -sk -o /dev/null -w '%{http_code}\n'` → `200` for `https://127.0.0.1:8443/dashboardbuilder/`,
  `…/features/Board/board.js`, `…/features/Dashboard/worksheet-view.js`;
  `cmp publish/DashboardBuilder.dll /var/www/webapps-dev/dashboardbuilder/DashboardBuilder.dll` → identical;
  `find /var/www/webapps-dev/dashboardbuilder ! -user unified` → no output. Ask the user to hard-refresh and
  confirm their autosaved workbook opened as worksheets.
