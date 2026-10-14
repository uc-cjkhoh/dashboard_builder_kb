# P22 plan — Tasks 3–4: the Show Me card; docs and deploy

Part of the [P22 plan](plan-overview.md); read its Global Constraints first. Paths are relative to the
app root. Spec: [§ Behaviour](../p22-show-me.md#behaviour).

### Task 3: the Show Me button, card, icon and styles

**Files:**
- Modify: `src/DashboardBuilder/Features/Core/icons.js` (add `show-me`), `tests/js/icons.test.mjs`
- Modify: `src/DashboardBuilder/Features/Dashboard/dashboards.js` — imports; `showMeCounts` beside
  `chartOrientation` (~l.220); `showMeOpen` beside `analyticsOpen` (~l.261); `renderShelves` view bar
  (~l.531–546); `formatToggle` (~l.727); `showMeToggle` / `showMePanel` after `formatToggle`
- Modify: `src/DashboardBuilder/Features/Dashboard/dashboard.css` (after `.ws-charttypes`, ~l.304)

**Interfaces:**
- Consumes (Tasks 1–2): `showMeOptions`, `placeFor`, `samePlacement`, `roleOf`; existing `planDims`,
  `drillActiveDim`, `colorMode`, `commit`, `renderShelves`, `iconButton`, `el`, `icon`, `chartIcon`,
  `chartLabel`, `CHART_TYPES`, `headEl`.
- Produces: DOM — `.ws-showme-toggle` (button), `.ws-showme` (card), `.ws-showme__tile[data-type]`,
  `.ws-showme__status` (`aria-live`).

- [ ] **Step 1: Failing icon test.** In `tests/js/icons.test.mjs` add `"show-me"` to the end of
  `REQUIRED`. Run the file — expect FAIL `show-me`.

- [ ] **Step 2: Add the icon** to `PATHS` in `Core/icons.js`, after `analytics` (20×20 viewBox, stroked):

```js
  "show-me": "M10 2.5l1.6 4.4 4.4 1.6-4.4 1.6L10 14.5l-1.6-4.4L4 8.5l4.4-1.6zM15.5 13.5l.7 1.8 1.8.7-1.8.7-.7 1.8-.7-1.8-1.8-.7 1.8-.7z",
```

  Run `icons.test.mjs` — expect PASS.

- [ ] **Step 3: Imports + counts adapter** in `dashboards.js`. Extend the Task 1 import:
  `import { roleOf, COLOR_SPLIT_TYPES, STAT_SINGLE_TABLE, chartIssue, TEXT_VALUE_HINT, COLOR_SPLIT_HINT, statFieldHint, showMeOptions, placeFor, samePlacement } from "./show-me-rules.js";`
  Add after `chartOrientation`:

```js
// P22 Show Me: the field counts one candidate chart type sees — the same dims the chart hint counts
// (planDims with that type: drill, shelf, Detail, Shape, discrete Colour) and the shelf measures.
function showMeCounts(sheet, type) {
  const shelf = [...sheet.columns, ...sheet.rows];
  const measures = shelf.filter((f) => roleOf(f) === "measure");
  return {
    dims: planDims({ ...sheet, chartType: type }).keyOrder.length,
    shelfDims: (drillActiveDim(sheet) ? 1 : 0) + shelf.filter((f) => roleOf(f) === "dimension").length,
    measures: measures.length,
    hasDate: shelf.some((f) => roleOf(f) === "dimension" && f.category === "temporal"),
    textValue: measures.some((f) => f.category !== "numeric" && (f.agg === "min" || f.agg === "max")),
    discreteColor: colorMode(sheet) === "discrete",
    numericField: shelf.some((f) => f.category === "numeric"),
  };
}
```

- [ ] **Step 4: One-open-card wiring.**
  - After `let analyticsOpen = false; …` add `let showMeOpen = false; // P22: whether the Show Me card is open`.
  - Replace every `formatOpen = false;` with `formatOpen = false; showMeOpen = false;` (the Analytics
    toggle and the four shelf-tool openers — `grep -n "formatOpen = false;"` lists them).
  - In `formatToggle`: `if (formatOpen) { openTool = null; analyticsOpen = false; showMeOpen = false; }`.
  - In `renderShelves`: `vbLeft.append(chartTypePicker(dash, s), showMeToggle(), undoButtons(dash));`;
    `const fmtEl = showMeOpen ? showMePanel(dash, s) : formatOpen ? formatPanel(dash, s) : analyticsOpen ? analyticsPanel(dash, s) : null;`;
    `const panelKey = toolEl ? \`tool:${openTool}\` : fmtEl ? (showMeOpen ? "showme" : "format") : null;`

- [ ] **Step 5: The toggle and the card** — after `formatToggle`:

```js
  // P22 Show Me: every chart type, greyed with the reason when the sheet's fields can't draw it, the best
  // one outlined; a click sets the type and lays Columns / Rows out for it (one commit = one undo step).
  function showMeToggle() {
    const btn = iconButton("show-me", "Show Me");
    btn.className = `iconbtn ws-viewbar__btn ws-showme-toggle${showMeOpen ? " is-active" : ""}`;
    btn.append(el("span", null, "Show Me"));
    btn.setAttribute("aria-pressed", String(showMeOpen));
    btn.setAttribute("aria-expanded", String(showMeOpen));
    btn.title = "Show Me — chart types that fit these fields";
    btn.addEventListener("click", () => { showMeOpen = !showMeOpen; if (showMeOpen) { openTool = null; formatOpen = false; analyticsOpen = false; } renderShelves(); });
    return btn;
  }
  function showMePanel(dash, s) {
    const panel = el("div", "ws-format ws-showme");
    panel.append(el("span", "ws-shelf__label", "Show Me"));
    const status = el("p", "ws-shelf__note ws-showme__status");
    status.setAttribute("aria-live", "polite");
    if (!s.columns.length && !s.rows.length) status.textContent = "Add fields to Columns or Rows to see suggestions.";
    const grid = el("div", "ws-showme__grid");
    for (const o of showMeOptions(CHART_TYPES.map(([id]) => id), (type) => showMeCounts(s, type))) {
      const tile = el("button", "ws-showme__tile"); tile.type = "button"; tile.dataset.type = o.id;
      tile.append(icon(chartIcon(o.id)), el("span", "ws-showme__label", chartLabel(o.id)));
      const current = o.id === s.chartType;
      tile.setAttribute("aria-pressed", String(current));
      if (current) { const tick = icon("check", { size: 14 }); tick.classList.add("ws-showme__check"); tile.append(tick); }
      if (o.recommended) { tile.classList.add("is-recommended"); tile.append(el("span", "ws-showme__badge", "Recommended")); }
      if (o.issue) {
        tile.setAttribute("aria-disabled", "true"); tile.title = o.issue;
        const why = el("span", null, o.issue); why.id = `ws-showme-why-${o.id}`; why.hidden = true;
        tile.setAttribute("aria-describedby", why.id); tile.append(why);
        tile.addEventListener("click", () => { status.textContent = `${chartLabel(o.id)}: ${o.issue}`; });
      } else {
        tile.addEventListener("click", () => {
          const placed = placeFor(o.id, s.columns, s.rows);
          if (current && samePlacement(placed, s)) return; // already laid out — no empty undo step
          s.chartType = o.id; s.columns = placed.columns; s.rows = placed.rows;
          commit(dash, s); // re-renders the header synchronously
          headEl.querySelector(`.ws-showme__tile[data-type="${o.id}"]`)?.focus();
        });
      }
      grid.append(tile);
    }
    panel.append(grid, status);
    panel.addEventListener("keydown", (e) => {
      if (e.key !== "Escape") return;
      e.stopPropagation(); showMeOpen = false; renderShelves();
      headEl.querySelector(".ws-showme-toggle")?.focus();
    });
    return panel;
  }
```

- [ ] **Step 6: Styles** — `dashboard.css`, after `.ws-charttypes`:

```css
/* P22 Show Me: a grid of every chart type. Greyed = the fields can't draw it (reason in title + status);
   recommended = accent outline + "Recommended" text; current = soft fill + check icon (never colour alone). */
.ws-showme-toggle { display: inline-flex; align-items: center; gap: var(--s1); width: auto; padding-inline: var(--s2); font-size: var(--fs-xs); }
.ws-showme { flex-direction: column; align-items: stretch; }
.ws-showme__grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(112px, 1fr)); gap: var(--s2); }
.ws-showme__tile {
  position: relative; display: flex; flex-direction: column; align-items: center; justify-content: center; gap: var(--s1);
  min-height: calc(var(--ctl-h) * 2); padding: var(--s2); font-size: var(--fs-xs); color: var(--ink);
  background: var(--surface); border: 1px solid var(--line-2); border-radius: var(--r-ctl); cursor: pointer;
}
.ws-showme__tile:hover:not([aria-disabled="true"]) { border-color: var(--accent); }
.ws-showme__tile[aria-pressed="true"] { background: var(--accent-soft); }
.ws-showme__tile.is-recommended { border: 2px solid var(--accent); }
.ws-showme__tile[aria-disabled="true"] { color: var(--ink-3); background: var(--surface-2); cursor: not-allowed; }
.ws-showme__tile[aria-disabled="true"] svg { opacity: .5; }
.ws-showme__badge { font-weight: 600; color: var(--accent-ink); }
.ws-showme__check { position: absolute; top: var(--s1); right: var(--s1); color: var(--accent-ink); }
.ws-showme__status { margin: 0; min-height: 1lh; }
```

- [ ] **Step 7: Static checks.** `node --check` on `dashboards.js` and `icons.js`; full JS suite and
  `dotnet test` — all pass; `grep -n "style.display\|#[0-9a-fA-F]\{3,6\}\b" ` over the added CSS / JS lines
  → none.

- [ ] **Step 8: Hand checks on the dev port** (`http://localhost:5180`). No ClickHouse account is
  reachable here: drive a headless shell with `playwright-core` and mock `**/api/**` per
  [api.md](../../reference/api.md) (connection, databases, tables, columns, query) — see
  [development.md § Test](../../operations/development.md#test). Screenshot each in light and dark
  (`page.emulateMedia({ colorScheme })`):
  1. Region (text) on Columns + Sales on Rows → Bar outlined + "Recommended"; Scatter greyed with "A point
     chart plots two measures (X and Y) — add a second measure."; click Pie → pie draws, no hint; Undo once
     → back to Bar with the same layout.
  2. Add a Date dimension → Line recommended; click Line → the date is first on Columns.
  3. Two dimensions + one measure → Heatmap recommended and draws; click Sankey → flows go from the
     first group-by dimension (now on Rows).
  4. Sales as `Min` of a text field (set the agg on a text measure) → only Table, Text and KPI enabled.
  5. Drill active (two levels on the Drill tool) → every enabled tile draws without a hint.
  6. Region on both Columns and Rows → click Table → it draws; both pills kept.
  7. Keyboard only: Tab into the grid, Enter on a greyed tile → its reason in the status line; Esc →
     card closes, focus on the Show Me button.
  8. Click the current tile when already laid out → Undo stays where it was (no new step).
  Show the screenshots to the user for review before Step 9.

- [ ] **Step 9: Commit.**

```bash
git add src/DashboardBuilder/Features/Core/icons.js tests/js/icons.test.mjs \
  src/DashboardBuilder/Features/Dashboard/dashboards.js src/DashboardBuilder/Features/Dashboard/dashboard.css
git commit -m "Add the Show Me card to the worksheet view bar (P22)

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"
```

### Task 4: docs, cleanup and deploy

**Files (KB repo, `/unified/user/cj/knowledge/web_development/dashboard_builder`):**
`docs/features/worksheet-charts.md`, `docs/reference/frontend-modules.md`, `docs/proposals/roadmap.md`,
`docs/README.md`; delete `docs/proposals/p22-show-me.md` and `docs/proposals/p22/`.

- [ ] **Step 1: `worksheet-charts.md`.** In § Chart types, say the rules live in
  `Dashboard/show-me-rules.js` (`CHART_NEEDS` / `chartIssue`). Add a `### Show Me` subsection stating as
  current behaviour: the Show Me button and card, greyed tiles with reasons, the recommendation table, the
  placement table, one commit per click, and nothing outside Columns / Rows changing — the content of the
  spec's Behaviour, Validity rules 1–3, Recommendation and Placement sections, condensed. Keep the file
  ≤ 300 lines (split Analytics into its own file if needed).
- [ ] **Step 2: `frontend-modules.md`.** Add `show-me-rules.js` in the Dashboard modules list, matching the
  existing rows' style: "pure — chart-type field rules, Show Me validity / recommendation / placement".
- [ ] **Step 3: `roadmap.md`.** Delete the `## P22 — Show Me` section and its row in Recommended order
  (renumber the rest); coverage row Show Me → `Show Me card (P22) — [worksheet-charts.md](../features/worksheet-charts.md#show-me)` with gap "—".
- [ ] **Step 4: Delete the spec and plan**, and the spec's row in `docs/README.md`:
  `git rm -r docs/proposals/p22-show-me.md docs/proposals/p22`.
- [ ] **Step 5: Verify + commit the KB.** `python3 .claude/hooks/kb-verify.py --all` → "KB clean.";
  `git commit -am "Document P22 Show Me as built; retire its spec and plan"` (with the Co-Authored-By line).
- [ ] **Step 6: Merge + publish (app repo).** `git checkout main && git merge --ff-only p22-show-me`;
  `dotnet test`; JS suite; `rm -rf publish && dotnet publish src/DashboardBuilder/DashboardBuilder.csproj -c Release -o publish`.
- [ ] **Step 7: Deploy — asset-only** (P22 changes no `.cs` / `.cshtml`; confirm with
  `git diff --stat <pre-P22 main>..main`): `cp -r publish/Features/* /var/www/webapps-dev/dashboardbuilder/Features/`
  — no restart, no `sudo`, sessions kept ([deployment.md](../../operations/deployment.md#release-flow)).
- [ ] **Step 8: Verify live.** `curl -sk -o /dev/null -w '%{http_code}\n'` on
  `https://127.0.0.1:8443/dashboardbuilder/` and `…/features/Dashboard/show-me-rules.js` → `200` both;
  `cmp publish/Features/Dashboard/dashboards.js /var/www/webapps-dev/dashboardbuilder/Features/Dashboard/dashboards.js`
  → identical. Ask the user to hard-refresh.
