# Backlog: charts, authoring and formatting

Format: [README.md](README.md#how-to-read-an-entry). Chart types are in [worksheet-charts.md](../features/worksheet-charts.md).

## Chart gaps

- **Line styles and date axis** (IDs: T03-05, T03-07; priority P1) — Open: step and jump lines (lines are always straight, on a category axis). Partial: discrete and truncated date parts exist; no continuous time axis or gap filling. Needs: none. Source: [gap-analysis-detail.md](../proposals/gap-analysis-detail.md).
- **Circle heatmap** (IDs: T03-10; priority P1) — Open: the heatmap is coloured squares only. Needs: none. Source: [gap-analysis-detail.md](../proposals/gap-analysis-detail.md).
- **Axis synchronisation** (IDs: T03-17; priority P1) — Open: the combo right axis is independent. Dual axis exists only as bar plus line. Needs: none. Source: [gap-analysis-detail.md](../proposals/gap-analysis-detail.md).
- **Gantt and Density marks** (IDs: T03-14; priority P2) — Open: no interval marks, no density surface. Needs: none. Source: the former roadmap.
- **Colour, size and shape beyond current marks** (IDs: T03-19, T03-21, T01-21; priority P1) — Partial: continuous colour works on scatter, heatmap and table only, single hue, no palette or range editing; shape works on scatter only; size on scatter bubbles only. Needs: none. Source: [gap-analysis-detail.md](../proposals/gap-analysis-detail.md).
- **Per-member colour and palettes** (IDs: T01-20, T03-24, T03-33; priority P0–P1) — Partial: three workbook palettes, legend position and highlight; no per-member colour assignment, no palette reverse, diverging only in table scales. Needs: none. Source: [gap-analysis-detail.md](../proposals/gap-analysis-detail.md).
- **Marker size and mark borders** (IDs: T01-22, T03-34; priority P1–P2) — Partial: size and shape by field and data labels exist; no fixed marker size or border setting (the heatmap border is fixed). Needs: none. Source: [gap-analysis-detail.md](../proposals/gap-analysis-detail.md).
- **Filter on an aggregated measure** (IDs: T03-27; priority P1) — partial: row-level between/compare only; no filter on an aggregated measure (HAVING) and no range slider. Needs: a whitelisted bounded HAVING in the server builder. Source: [gap-analysis-detail.md](../proposals/gap-analysis-detail.md).
- **Exclude** (IDs: T03-28; priority P0) — partial: multi-select `in` works; Exclude applies to one clicked value only, with no NOT IN. Needs: a validated NOT IN op. Source: [gap-analysis-detail.md](../proposals/gap-analysis-detail.md).

## Authoring gaps

- **Duplicate sheet** (IDs: T01-11; priority P0) — partial: create, rename, switch and close exist. Needs: none. Source: [gap-analysis-detail.md](../proposals/gap-analysis-detail.md).
- **Tooltip text editor** (IDs: T01-19; priority P0) — partial: extra tooltip fields show on hover; no tooltip text or format editor. Needs: none. Source: [gap-analysis-detail.md](../proposals/gap-analysis-detail.md).
- **Discrete/continuous pills and double-click placement** (IDs: T01-04, T01-15; priority P1) — Partial: role convert and date part only, no explicit discrete/continuous toggle; drag and plus-button placement only, no double-click. Needs: continuous axes for the toggle. Source: [gap-analysis-detail.md](../proposals/gap-analysis-detail.md).
- **Start screen and recent sources** (IDs: T01-14; priority P1) — partial: import and autosave restore; no start screen. Needs: none. Source: [gap-analysis-detail.md](../proposals/gap-analysis-detail.md).
- **Performance recording** (IDs: T01-30; priority P2) — Open: no query or render timing capture. Needs: none. Source: [gap-analysis-detail.md](../proposals/gap-analysis-detail.md).

## Formatting and presentation

- **Worksheet formatting** (IDs: T01-23; priority P1) — partial: number, date, legend, fit and theme; no font, alignment, shading or cell sizes. Needs: none. Source: [gap-analysis-detail.md](../proposals/gap-analysis-detail.md).
- **PDF export** — export is the browser print dialog on one worksheet; there is no generated PDF. Dashboard export follows the dashboard work. Needs: [dashboards.md](dashboards.md) P24b for dashboards. Source: [gap-analysis.md](../proposals/gap-analysis.md).
- **Phone view check** — judged complete from phone and touch CSS alone; it has not been run on a device. Needs: a device run. Source: [gap-analysis.md](../proposals/gap-analysis.md).
