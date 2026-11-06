---
components: [src/DashboardBuilder/Features/Board/]
---
# Dashboard data notes, full screen and print

Part of [dashboards.md](dashboards.md): the free-text note, full screen, and the printed header.

## Data notes

- **Notes** (bar) opens an inline editor under the bar: a labelled textarea, a count ("n / 1000"), **Save** and **Cancel**. Ctrl+Enter saves, Esc cancels.
- **Limit:** at most **1000** characters after trimming (`LIMITS.dashboardNotes`, client-side only). Over it, the editor shows an alert, sets `aria-invalid` and keeps the text — rejected, never cut. Saving blanks clears the note.
- **Shown** under the bar as plain text (`textContent`, line breaks kept); hidden when there is none. Switching dashboards closes an open editor.
- **Saved** as an optional `notes` string on the dashboard (absent when empty); on import a non-string or over-long note is dropped with an issue. Not part of undo / redo. Specification text only — no data.

## Full screen and print

- **Full screen** shows the bar and canvas (the whole board) full screen, using the Fullscreen API with a fallback to a fixed overlay.
  The button's text changes to "Exit full screen". Esc or the button exits.
- **Print** prints a header and the canvas. The side panel, bar buttons, widget buttons, bar title and on-screen note are hidden (`@media print` in `board.css`).
  - **Header** (`.ws-print-head`, built on `beforeprint`, removed after): the name, then only the lines that apply: "Worksheets: …" (the worksheet widgets' names), "Filtered by …" (the dashboard selection chip), "Printed <time> (<offset>)", and the note.
  - **Automatic size:** on `beforeprint` the board lays itself out **stacked at a fixed 1000px page width** (`layoutBoard(…, { stack: true })`),
    and the widgets print **in flow, one column** (`position: relative`, `break-inside: avoid`).
    This is because an absolutely positioned widget could be split or cropped across pages.
    The on-screen arrangement (side by side) is not kept on paper.
  - **Chart size:** each worksheet widget's chart is sized to its printed cell (`sizeChart(body, { width, height })`, from the cell box less header and padding).
    This overrides the worksheet print rule that fixes every chart canvas at 1000 × 560. `afterprint` restores the screen layout and chart sizes.
  - **Fixed size:** a **fixed-size** dashboard instead prints its box with the on-screen arrangement kept, absolutely positioned and
    scaled down proportionally to the 1000px page width (never up).
- Image and CSV export stay per worksheet (reach them with **Edit**).

## Tests

**Data notes**

- `tests/js/board-notes.test.mjs` — the limit, trimming, import cleaning, saved form, print lines, workbook parse.
- `tests/live/dashboard-notes-ui.mjs` — editor and count, over-limit refused, Esc, `<b>` stays literal text, autosave and reload, print header under print media, clearing; light and dark screenshots.

Print layout of the widgets is also covered by `tests/live/board-ui.mjs` (see [dashboards.md](dashboards.md#tests)). Not verified: the browser's real print dialog and PDF pages.
