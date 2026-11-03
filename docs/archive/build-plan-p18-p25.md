# Tableau worksheet parity — gap analysis (P18–P25)

Verified the builder's worksheet against Tableau Desktop's **worksheet workspace** anatomy
([help.tableau.com › environment_workspace](https://help.tableau.com/current/pro/desktop/en-us/environment_workspace.htm#workspace-area)):
the numbered workspace parts (Data pane, Analytics pane, Columns/Rows/Pages/Filters shelves, the
**Marks card** + its encoding targets, Show Me, legends, sheet tabs incl. worksheet/dashboard/story,
title/caption, field labels, toolbar, status bar). Below: what we **have**, what is **already on the
roadmap** (P12–P16), and the **still-missing** parts, which become **P18–P25**. Same guards as the
uplift track: **read-only, bounded, identifier-safe** ([D1](../../archive/docs/project/decisions.md)/[D6](../../archive/docs/project/decisions.md)),
`hidden` visibility, tokens; each phase independently shippable.

### Coverage matrix

| Tableau workspace part | Builder today | Verdict |
|---|---|---|
| **Data pane** — fields split Dimensions/Measures | field pane per model table ✓ | **Have** (authoring extras missing → P25) |
| **Columns / Rows shelves** | ✓ multi-pill, role-convert, agg picker | **Have** |
| **Filters shelf** | op + typed value pill | **Partial** — no range / relative-date / top-N / multi-select **list** filter; interactive **filter cards** = **P14** |
| **Marks card — Color** | Colour shelf (discrete series) + continuous gradient on scatter (P18) + colour-by-category (P10) | **Have** (bar-gradient deferred, [D18](../../archive/docs/project/decisions.md)) |
| **Marks card — Size** | Size lane → scatter bubbles (P18) | **Have (scatter)** |
| **Marks card — Label / Text** | field-on-Label (P18) + Text mark → crosstab (P19) | **Have** |
| **Marks card — Detail** | Detail lane → group-by granularity (P18) | **Have** |
| **Marks card — Tooltip** | custom field-driven tooltip lines (P18) | **Have** |
| **Marks card — Shape** | Shape lane → per-value symbols + legend on scatter (P19) | **Have (scatter)** |
| **Marks card — Path** | Path lane → orders line/area vertices (P19) | **Have** |
| **Marks card — Angle** | pie maps measure→slice implicitly; Angle lane acknowledges it (P19) | **Covered (pie)** |
| **Mark-type dropdown** | bar/stacked/line/area/pie/donut/scatter/combo/**square/circle/text**/heatmap/treemap/histogram/boxplot/KPI/table | **Have** — Gantt/Density **deferred**, Map **out of scope** ([D18](../../archive/docs/project/decisions.md)) |
| **Pages shelf** | Pages lane + step/animate control (P20) | **Have** |
| **Analytics pane** — reference/constant/average lines & bands, trend line, forecast, totals/subtotals | — | **Missing → P21** (box plot / statistical marks already = **P12**) |
| **Show Me** | chart-type dropdown + invalid-mapping hints | **Partial** — no recommend-and-auto-place panel → **P22** |
| **Legends** (colour/size/shape) | ECharts colour legend + position toggle | **Partial** — display-only; size/shape legends need P18/P19; interactive **highlight/​filter on legend** = **P15** |
| **Worksheet Title / Caption** | — | **Missing → P23** |
| **Field labels** (row/column) | crosstab corner + axis titles | **Partial → P23** |
| **Toolbar** — undo/redo, swap rows↔cols, clear sheet, fit, highlight | scattered inline controls only | **Missing → P23** |
| **Status bar** — marks count, rows×cols, aggregate of selection | — | **Missing → P23** |
| **Sheet tabs** — worksheet **/ dashboard / story** | Data-Model tab + subtabs, **each = one worksheet** | **Partial** — no multi-worksheet **dashboard** composition, no **story** → **P24** |
| **Drill-down / hierarchies** | Drill-down lane (single-table hierarchy) + breadcrumb ✓ (P16) | **Have (single-table)**; Data-pane-authored reusable hierarchies → P25 |
| Side bar / Data Source / Start page | connection sidebar + schema browser | **Have (equivalent)** |

> **Biggest architectural gap:** in Tableau a **dashboard** *composes several worksheets* on one canvas;
> in the builder a "dashboard" subtab **is a single worksheet** (one `sheet`, one `#ws-chart`). True
> multi-view dashboards are **P24** — the others (P18–P23, P25) enrich the single worksheet.

### New phases at a glance

| Phase | Outcome | Depends on |
|---|---|---|
| P18 ✅ | **Marks card I** — Size, Label/Text, Detail, Tooltip; continuous Color (generalises the P7 Color shelf) | P7 |
| P19 ✅ | **Marks card II** — Shape, Path, Angle + mark-type expansion (square/circle/text; gantt/density deferred, map out of scope) | P18 |
| P20 ✅ | **Pages shelf** — page/animate the view through a dimension | P7 |
| P21 | **Analytics pane** — reference/average/constant lines & bands, trend line, forecast, totals/subtotals | P7 |
| P22 | **Show Me** — recommend valid viz types for the current fields & auto-place | P11, P18 |
| P23 | **Worksheet chrome & toolbar** — Title, Caption, field labels, status bar; undo/redo, swap rows↔cols, clear, fit, highlight | P7 |
| P24 | **Multi-worksheet dashboards & stories** — compose many worksheets/KPIs on one canvas + story points | P7, P14 |
| P25 | **Data-pane authoring** — calculated fields, groups, sets, bins, folders, hierarchies | P4 |

---

## P18 — Marks card I: Size · Label · Detail · Tooltip (+ continuous Colour)
**Goal:** turn the P7 Color shelf into a proper **Marks card** — a cluster of encoding targets that
map a field onto a mark property, all on the **existing bounded aggregate/join query**.
- **Size** — a measure → mark size (bubble scatter, variable bar/line width); a size legend.
- **Label / Text** — drop a **field** on Label (not just the P10 on/off toggle); a **Text/table mark**
  writing the field value into the mark.
- **Detail** — a dimension that **adds group-by granularity without a visual channel** (like Color's
  query treatment, minus the colour) — more marks, same encodings.
- **Tooltip** — a **custom tooltip** template with chosen fields (ECharts formatter driven by the
  sheet's tooltip field list), replacing the fixed default.
- **Continuous Colour** — a **measure** on Colour → a sequential token-derived gradient (today Colour
  is discrete only); keep a colour legend, never colour-alone.
- **Done when:** a bubble chart (Size = measure), a labelled chart (Label = field), an added-detail
  chart, and a custom tooltip each render from a valid mapping; invalid mappings show a **hint**, not
  an error (P11 rule). Marks-card encodings persist per session ([O1](../../archive/docs/project/decisions.md)).
- **Guards:** Size/Detail that add a group-by go through the **same validated, bounded** query path as
  Color ([D14](../../archive/docs/project/decisions.md)); no new query shape beyond an extra dimension/measure.
- **Doc:** [modules.md](../../archive/docs/app/modules.md) §7 (Marks card), [data-model.md](../../archive/docs/data-model.md)
  (encoding model), [frontend-patterns.md](../../archive/docs/frontend-patterns.md) (chart adapter).
- **✅ Shipped 2026-08-18:** the P7 Colour shelf became a **Marks card** (`marksCard` in `dashboards.js`,
  `sheet.marks`) grouping **Color / Size / Label / Detail / Tooltip** lanes. The canonical query shape
  moved into shared `planDims`/`planMeasures` (buildPlan sends them, `renderChart` re-derives the same
  ordering), so marks-only measures never become spurious series and **a sheet with no marks emits a
  byte-identical plan** (no regression). **Size** → scatter bubbles (`sizeScaler`); **continuous Colour**
  (a numeric Colour field) → a token gradient `visualMap` on scatter; **Detail** → extra group-by
  granularity; **Label** → a field's value on each mark (numeric rides along as an aux measure,
  categorical reads its group-by key); **Tooltip** → custom field lines (`extraTooltip`). Every unmet
  mapping is a **hint, not an error** ([D18](../../archive/docs/project/decisions.md)). Pure client — build clean,
  **100 tests**, JS syntax-checked; deployed live. *(In-browser render check pending — no headless
  browser on the host, per P9's note.)*

## P19 — Marks card II: Shape · Path · Angle + mark types
**Goal:** the remaining Marks-card encodings and mark vocabulary.
- **Shape** — a dimension → distinct point shapes (scatter / shape charts); a shape legend
  (shape is a second non-colour channel, so identity survives greyscale).
- **Path** — a field that **orders** the vertices of a line/polygon mark (connected scatter, custom
  line order) rather than the default category order.
- **Angle** — explicit for pie (already implicit); expose it where a radial mark needs it.
- **Mark types** — extend the mark-type dropdown with **Square, Circle, Text, Gantt Bar, Density**
  (heatmap-ish) marks. **Map is out of scope** (no geospatial in v1 — record in
  [decisions.md](../../archive/docs/project/decisions.md)).
- **Done when:** shape-encoded scatter, a path-ordered line, and at least the Square/Circle/Text marks
  render; each unmet mapping shows a hint.
- **Doc:** [modules.md](../../archive/docs/app/modules.md) §7, [DESIGN.md](../../archive/DESIGN.md) (shape vocabulary / a11y —
  never colour-alone).
- **✅ Shipped 2026-08-18:** **Shape** (`addShape`) → on the scatter family, splits points into one
  series per value with a distinct symbol + legend (`renderScatterShapes`/`buildScatterShapes`; identity
  survives greyscale). **Path** (`pathOrderedRows`) → orders a line/area's vertices by the Path field's
  value (a group-by key or numeric measure). **Angle** → acknowledged for pie/donut (which already map
  the measure to slice angle), a hint elsewhere. **Mark types:** the dropdown gained **Square** and
  **Circle** (scatter builder + symbol override) and **Text** (→ the crosstab text grid). **Gantt Bar /
  Density deferred; Map out of scope** ([D18](../../archive/docs/project/decisions.md)). Unmet mappings show hints.
  Pure client — build clean, **100 tests**, JS syntax-checked; deployed live. *(In-browser render check
  pending.)*

## P20 — Pages shelf
**Goal:** Tableau's **Pages** — step or animate the view through the members of a dimension.
- A **Pages** shelf takes one dimension; a page **control** (play/step/loop + current-member label)
  filters the view to one member at a time via the existing **bound-parameter** filter path.
- **Done when:** dropping a dimension on Pages yields a control that pages through its members,
  re-rendering the chart per member; respects `prefers-reduced-motion` (no autoplay when set).
- **Guards:** each page is one **bound** filter value ([D6](../../archive/docs/project/decisions.md)); members list
  comes from a **bounded distinct-values** query (shared with P14).
- **Doc:** [modules.md](../../archive/docs/app/modules.md) §7, [clickhouse-integration.md](../../archive/docs/clickhouse-integration.md).
- **✅ Shipped 2026-08-18:** a **Pages lane** (`addPages`, `sheet.pages`) takes one dimension; a **page
  control** below the shelves (`pagesControl`) shows the current member + count with **◀ ▶** stepping
  (wrapping) and **▶ Play / ❚❚ Pause** autoplay (a 1.5s timer). Each page applies the current member as a
  **bound-parameter `=` filter** (`pagesFilter`, appended in `buildPlan`), only when its table is already
  in the query — never forcing a join. Members come from the **bounded distinct-values** query (shared
  with the P14 `in` filter). **Autoplay is omitted under `prefers-reduced-motion`** (done-when); the timer
  is transient and cleared on view switch. Pure client — build clean, **100 tests**, JS syntax-checked;
  deployed live. *(In-browser animation check pending.)*

## P21 — Analytics pane
**Goal:** the second side-bar tab — drop-on analytics that overlay the view.
- **Reference lines / bands** (constant, or from an aggregate: average/median/min/max), **constant
  line**, **average line**; **trend line** (linear/log/poly, computed client-side over returned rows),
  **forecast** (simple), and **Totals** — grand totals + **subtotals** in the crosstab.
- **Done when:** a user adds an average reference line, a linear trend line, and column grand totals,
  and they render/update with the query; all overlays are **client-side over the bounded result**
  (no new server aggregate beyond optional totals rows).
- **Guards:** totals stay within the read-only aggregate path; no unbounded scans.
- **Doc:** [modules.md](../../archive/docs/app/modules.md) §7 (analytics overlays), [DESIGN.md](../../archive/DESIGN.md)
  (reference-line styling tokens).

## P22 — Show Me
**Goal:** Tableau's **Show Me** — recommend the view types that fit the fields in play and build one
in a click.
- A **Show Me** panel lists chart types with the **valid ones enabled** for the current
  dimension/measure selection (reusing `chartIssue()` logic) and, on pick, **auto-places** fields on
  the right shelves/encodings.
- **Done when:** with fields selected, Show Me highlights the applicable types and one click produces
  the chart with sensible shelf placement; inapplicable types are greyed with the reason.
- **Doc:** [modules.md](../../archive/docs/app/modules.md) §7 (Show Me), [frontend-patterns.md](../../archive/docs/frontend-patterns.md).

## P23 — Worksheet chrome & toolbar
**Goal:** the worksheet's framing UI and editing actions.
- **Title** (editable, defaulting to the sheet name) and **Caption** (auto-generated summary,
  editable); **field labels** for rows/columns in the view; a **status bar** (marks count, rows×cols,
  aggregate of the current selection).
- **Toolbar** actions: **undo/redo** (a worksheet-state history stack), **swap rows↔columns**,
  **clear sheet**, **fit** (standard / fit-width / fit-height / entire view), **highlight**.
- **Done when:** title/caption render and edit; undo/redo traverse shelf/format changes; swap
  transposes Columns↔Rows; clear empties the sheet (with confirm if non-empty); fit modes change the
  chart sizing.
- **Doc:** [modules.md](../../archive/docs/app/modules.md) §7, [DESIGN.md](../../archive/DESIGN.md) (toolbar, `--ctl-h`).

## P24 — Multi-worksheet dashboards & stories
**Goal:** close the **biggest** architectural gap — a Tableau **dashboard** *composes several
worksheets*; today a subtab is a single worksheet.
- Introduce a **dashboard-composition** view: a grid/free canvas that hosts **multiple worksheet
  widgets** (charts, crosstabs, KPI tiles) with per-widget sizing/placement, sharing the one data
  model. Optionally **story** points (ordered, captioned snapshots). Revisit
  [O1](../../archive/docs/project/decisions.md) persistence and [O3](../../archive/docs/project/decisions.md) widget richness.
- **Done when:** a user places ≥2 worksheets on one dashboard canvas, arranges/resizes them, and each
  re-queries independently; a story sequences several views with captions.
- **Depends on:** P14 (dashboard-level filters make multi-widget composition worthwhile).
- **Doc:** [ARCHITECTURE.md](../../archive/ARCHITECTURE.md), [data-model.md](../../archive/docs/data-model.md) (dashboard vs
  worksheet), [modules.md](../../archive/docs/app/modules.md).

## P25 — Data-pane authoring
**Goal:** author derived fields in the Data pane, like Tableau.
- **Calculated fields** (a computed **SELECT expression**), **groups** (map members → a label),
  **sets** (a named member subset), **bins** (numeric bucketing — overlaps the **P12** histogram
  shape), **folders**, and **hierarchies** (ordered levels — the drill metadata of **P16**).
- **Done when:** a user defines a calculated field and uses it on a shelf; a group and a bin render;
  hierarchy/drill reuses P16.
- **Guards (critical):** calculated fields are **read-only** ([D1](../../archive/docs/project/decisions.md)) and
  **injection-safe** — evaluate only a **whitelisted set of scalar functions/operators**, forbid
  subqueries, semicolons, and any DDL/DML; validate every identifier against the live catalog
  ([D6](../../archive/docs/project/decisions.md)). This is the one phase that lets user text into a SQL *expression*,
  so treat the whitelist as a golden-rule surface. Record the approach in
  [decisions.md](../../archive/docs/project/decisions.md).
- **Doc:** [clickhouse-integration.md](../../archive/docs/clickhouse-integration.md) (calc-expression whitelist),
  [data-model.md](../../archive/docs/data-model.md).

---

## Cross-phase definition of done
Every phase closes only when: read-only invariant intact; no credential leak; identifiers
validated + quoted where interpolated; visibility via `hidden`; colors via tokens; the
touched KB doc updated in the same change ([CLAUDE.md](../../archive/CLAUDE.md#definition-of-done-for-a-change)).

## Open questions to resolve along the way
[O1](../../archive/docs/project/decisions.md) persistence (before P6 ships beyond in-memory) ·
[O2](../../archive/docs/project/decisions.md) saved connections · [O3](../../archive/docs/project/decisions.md) widget
richness (before P7) · [O4](../../archive/docs/project/decisions.md) execute joins? (before join-backed
widgets) · [O5](../../archive/docs/project/decisions.md) prod proxy/TLS (**resolved** — Apache httpd + PathBase on `10.168.49.20`).

## Suggested first step
Start **P0 + P1 together**: scaffold the project and stand up the safe gateway with the
identifier tests. That front-loads the one genuinely risky part (SQL-identifier safety) and
gives every later phase a trustworthy foundation. **Do not** begin until you're ready to
build — this plan and the KB are the current deliverable.
