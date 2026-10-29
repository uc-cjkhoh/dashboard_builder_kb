# Backlog: charts, authoring and formatting

Format: [README.md](README.md#how-to-read-an-entry). Chart types are in [worksheet-charts.md](../features/worksheet-charts.md).

## Chart gaps

- **Continuous time axis, gap filling and true jump lines** (IDs: T03-05 remainder, T03-07; priority P1) — Open: a true jump line (disconnected horizontal segments with no risers, as in Tableau; the current Step (centred) is a connected step); lines sit on a category axis, so unevenly spaced dates are drawn evenly and missing periods are not filled. Partial: discrete and truncated date parts exist; no continuous time axis or gap filling. Needs: none.
- **Layered marks and dual axis beyond the combo** (IDs: T03-16 remainder, T03-17 remainder; priority P2) — Partial: the combo has Synchronise axes and a right-axis mark of line, bar or area. Open: a dual axis on other chart types (line, area, scatter) by dropping a second measure on the right; independent mark types per measure (all right-axis measures share one type); a user-set axis range or a synchronise that spans a field the combo does not plot. Needs: none.
- **Gantt and Density marks** (IDs: T03-14; priority P2) — Open: no interval marks, no density surface. Needs: none.
- **Colour, size and shape beyond current marks** (IDs: T03-19, T03-20, T03-21, T01-21; priority P1) — Partial: continuous colour works on scatter, heatmap and table only, single hue, no palette or range editing; shape works on scatter only; size on scatter bubbles only. Needs: none.
- **Palette editing, diverging colour and member-colour gaps** (IDs: T01-20 and T03-24 remainder, T03-33 remainder; priority P1) — Open: diverging continuous colour on heatmap and scatter (diverging exists only in table scales); custom palette editing and a free-hex picker (only 24 fixed swatches); member colours cannot be set from the legend (a legend click highlights), cannot be assigned to scatter groups, treemap or funnel members, and are unsupported for calculated fields; no stepped or reversed-per-field ramps. Needs: none.
- **Marker and border refinements** (IDs: T01-22 remainder, T03-34 remainder; priority P2) — Partial: Format has a fixed marker size (4–40 px) and a none / thin / thick mark border for scatter, line markers, circle heatmap, bars and cells. Open: border on the treemap, pie, funnel and the P36 types; a border colour or width of the user's choosing; per-series marker size; marker shape on line charts. Needs: none.
- **Filter on an aggregated measure** (IDs: T03-27; priority P1) — partial: row-level between/compare only; no filter on an aggregated measure (HAVING) and no range slider. Needs: a whitelisted bounded HAVING in the server builder.

## Authoring gaps

- **Tooltip field formats** (IDs: T01-19 remainder; priority P2) — Open: tooltip text has no per-field number/date format inside the template (values use the view's formats). Needs: none.
- **Discrete/continuous pills and double-click placement** (IDs: T01-04, T01-15; priority P1) — Partial: role convert and date part only, no explicit discrete/continuous toggle; drag and plus-button placement only, no double-click. Needs: continuous axes for the toggle.
- **Start screen and recent sources** (IDs: T01-14; priority P1) — partial: import, autosave restore and recent connections (host, port, user; no password) exist; no start screen listing recent workbooks or sample data. Needs: none.
- **Analytics pane** (IDs: T07-01; priority P1) — partial: reference lines, trend and forecast sit in a toggled card of selects, not a drag-and-drop pane. Needs: none.
- **Performance recording** (IDs: T01-30; priority P2) — Open: no query or render timing capture. Needs: none.

## Formatting and presentation

- **Worksheet formatting** (IDs: T01-23; priority P1) — partial: number, date, legend, fit and theme; no font, alignment, shading or cell sizes. Needs: none.
- **PDF export** (IDs: T01-28; priority P1) — partial: export is the browser print dialog on one worksheet; there is no generated PDF. A dashboard prints through the browser too (whole canvas); a generated PDF is not built. Needs: none.
- **Phone view check** (IDs: T09-16; priority P1) — judged complete from phone and touch CSS alone; it has not been run on a device. Needs: a device run.
