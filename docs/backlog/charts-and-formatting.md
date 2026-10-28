# Backlog: charts, authoring and formatting

Format: [README.md](README.md#how-to-read-an-entry). Chart types are in [worksheet-charts.md](../features/worksheet-charts.md).

## Chart gaps

- **Line styles and date axis** (IDs: T03-05, T03-07; priority P1) — Open: step and jump lines (lines are always straight, on a category axis). Partial: discrete and truncated date parts exist; no continuous time axis or gap filling. Needs: none.
- **Circle heatmap** (IDs: T03-10; priority P1) — Open: the heatmap is coloured squares only. Needs: none.
- **Dual axis and axis synchronisation** (IDs: T03-16, T03-17; priority P1) — Open: synchronise axes (the combo right axis is independent). Partial: dual axis exists only as the bar-plus-line combo, not as layered marks of any type. Needs: none.
- **Bullet target from a field** (IDs: T03-12; priority P1) — partial: the bullet chart takes its target from Format, not from a field. Needs: none.
- **Gantt and Density marks** (IDs: T03-14; priority P2) — Open: no interval marks, no density surface. Needs: none.
- **Colour, size and shape beyond current marks** (IDs: T03-19, T03-20, T03-21, T01-21; priority P1) — Partial: continuous colour works on scatter, heatmap and table only, single hue, no palette or range editing; shape works on scatter only; size on scatter bubbles only. Needs: none.
- **Palette editing and diverging colour** (IDs: T03-24, T03-33 remainder; priority P1) — Open: diverging continuous colour on heatmap and scatter (diverging exists only in table scales, `scale-model`/conditional formatting); no custom palette editing, and member colours are not wired to scatter groups, treemap or funnel or settable from the legend. Needs: none.
- **Marker size and mark borders** (IDs: T01-22, T03-34; priority P1–P2) — Partial: size and shape by field and data labels exist; no fixed marker size or border setting (the heatmap border is fixed). Needs: none.
- **Filter on an aggregated measure** (IDs: T03-27; priority P1) — partial: row-level between/compare only; no filter on an aggregated measure (HAVING) and no range slider. Needs: a whitelisted bounded HAVING in the server builder.

## Authoring gaps

- **Tooltip field formats** (IDs: T01-19 remainder; priority P2) — Open: tooltip text has no per-field number/date format inside the template (values use the view's formats). Needs: none.
- **Discrete/continuous pills and double-click placement** (IDs: T01-04, T01-15; priority P1) — Partial: role convert and date part only, no explicit discrete/continuous toggle; drag and plus-button placement only, no double-click. Needs: continuous axes for the toggle.
- **Start screen and recent sources** (IDs: T01-14; priority P1) — partial: import and autosave restore; no start screen. Needs: none.
- **Analytics pane** (IDs: T07-01; priority P1) — partial: reference lines, trend and forecast sit in a toggled card of selects, not a drag-and-drop pane. Needs: none.
- **Performance recording** (IDs: T01-30; priority P2) — Open: no query or render timing capture. Needs: none.

## Formatting and presentation

- **Worksheet formatting** (IDs: T01-23; priority P1) — partial: number, date, legend, fit and theme; no font, alignment, shading or cell sizes. Needs: none.
- **PDF export** (IDs: T01-28; priority P1) — partial: export is the browser print dialog on one worksheet; there is no generated PDF. Dashboard export follows the dashboard work. Needs: [dashboards.md](dashboards.md) P24b for dashboards.
- **Phone view check** (IDs: T09-16; priority P1) — judged complete from phone and touch CSS alone; it has not been run on a device. Needs: a device run.
