# Debug log — fine-tuning run 2026-10-29

Warnings, errors, bugs, permission denials and anything that stopped development during the fine-tuning run. Append-only.

- **ft-connection** (2026-10-29) — setPill/PILL in Core/ui.js are now unused dead code (out of scope: Core); left in place. Task 6: server returns the entered (trimmed) host, so the only host loss found was the blank form after a reload/change; fixed via formFromView, recent stored from the entered host. No other errors.
- **ft-canvas / tabs-ui** (15:54) — tests/live/tabs-ui.mjs 'empty-board message' check fails on the ft-canvas worktree; the change touches no board code (likely pre-existing or from another branch); not investigated, left as is.
- **ft-canvas / date labels** (15:54) — default 'thin' now fits the date axis to the pane (no per-category scroll) for date charts; existing date/charts/labels live checks still pass; no errors otherwise.
- **tabs-ui empty-board check** (15:55) — fails after ft-canvas merge; cause unverified (my attempt to run it on the pre-change commit timed out at 'app loaded'). Assigned to ft-worksheet to confirm on main.
- **tabs-ui empty-board** (15:56) — confirmed on main: failure was a stale test expectation ('This dashboard is empty'); _Board.cshtml text was shortened to 'Empty dashboard' by an earlier fine-tuning commit; test updated, passes.
- **baseline UI suite on main** (16:12) — board-edit-ui (8 fail), board-ui (1), ref-lines-ui (2) already fail on main (checked in a throwaway worktree ft-worksheet-base): ghost y offsets / chart option undefined; unrelated to this batch; left as is.
- **ft-worksheet / chart-type** (16:28) — merging Show Me into the picker with a re-layout (placeFor) broke ~6 UI checks (types picked with a dimension on Rows moved it); dropped the re-layout, removed placeFor/samePlacement and their tests; picker only sets the type.
- **ft-worksheet / cast chip** — removing the field-row ⋯ button let the cast tag fit on the name's line (name clipped to 4px); fixed with `.ws-field.is-cast .ws-field__name { min-width: 96px }`.
- **ft-worksheet / my pgrep monitors** — `pgrep -f run-ui-all` matched its own watcher command (never ended); stopped them and waited on the PID instead.
- **ft-worksheet / design audit** — fonts and radii clean; fixed native checkbox 3px margins and toast-close padding; left: search/select 28px icon gutters, HSL saturation of pill/accent tokens at 70.2-70.8% (the "≈70%" rule), member-label placeholders that echo raw data.
