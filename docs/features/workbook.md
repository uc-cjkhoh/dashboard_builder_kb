# Workbook — save, restore, export, import

The whole builder state — the Data Model and every dashboard worksheet — survives a page reload and can
be moved between browsers as a file. Everything stays **in the browser**; there is still no server-side
database ([D21](../reference/decisions.md#d21--workbooks-persist-in-the-browser-not-on-the-server)).
Code: `Features/Workbook/` (`workbook.js`, `workbook-model.js`, `_Workbook.cshtml`, `workbook.css`);
the allowed values it checks against are in `Core/sheet-schema.js`, the caps in `Core/validate.js` `LIMITS`.

## What a workbook holds

| Kept | Left out |
|---|---|
| each table: `db`, `table`, canvas position, ticked join keys | DOM nodes, fetched column lists (re-fetched on open) |
| each relationship: endpoints + cardinality | loaded Pages members (re-fetched on demand) |
| each dashboard: name + full worksheet `sheet` | the connection, host credentials, **any password** |
| which dashboard was open | |

Format: JSON with `"format": "dashboard-builder-workbook"` and an integer `version` (currently 1). Shapes are in
[data-model.md](../reference/data-model.md#workbook-file).

## Auto-save

- Any model or worksheet change (`entity:added/moved/removed`, `joinkey:changed`, `rel:changed`,
  `tabs:changed`, `dashboard:changed`) schedules a save **500 ms** later to `localStorage`.
- One workbook per **server + user**: key `dashboardbuilder.workbook.v1|<host>|<port>|<user>`. Nothing is
  saved while disconnected; a pending save is flushed under the old key when the connection changes.
- **Disconnect clears the screen, not the save.** After the flush, the cards and dashboard tabs fade
  out (~100ms) and the model and every dashboard are cleared (`clearWorkspace`); the stored workbook is
  untouched, so reconnecting to the same server + user restores it. Reconnecting mid-fade keeps the
  workspace as it was.
- The tab bar shows a quiet **Saved** text, or "Not saved — browser storage is unavailable. Use Export to
  keep a copy." (private window, blocked storage).
- **Autosave never overwrites a stored workbook it couldn't read.** It is blocked for that key only when
  no backup copy could be kept (see below); the status then says "Not saved — your previous workbook
  couldn't be read and has been left untouched. Use Export to keep a copy." A deliberate Import replaces
  the stored entry and lifts the block.

## Restore on connect

When a connection is established **and the canvas is empty**, the saved workbook for that server + user
reopens and a toast says `Restored your last workbook (N tables, M dashboards).` Tables re-fetch their
columns; join keys are re-ticked once the columns arrive; relationships draw as soon as both key rows
exist; the previously open dashboard becomes active and re-runs its query. A table that no longer exists
shows its card's **failed** state with Retry, and keeps its saved keys.

- **Repairs are reported.** If validation reset or dropped anything, the toast adds "N part(s) were
  reset" and an issues dialog lists each one (first 20, then "…and N more").
- **An unreadable or newer-format entry** is copied to `<key>:backup-<ISO time>` (an identical backup is
  not duplicated) and a danger toast says so; saving then continues normally. If storage is full and no
  backup can be kept, the entry is left untouched and autosave is blocked for it.
- **A partial open** (a table or dashboard failed to rebuild) is never autosaved over the stored entry.

## Export & Import

Both live in the **Workbook** overflow menu (an icon button at the right end of the tab bar,
`_Workbook.cshtml`):

- **Export workbook** downloads `workbook-YYYY-MM-DD.json` of the current state ("Nothing to export yet"
  when the canvas is empty).
- **Save view as bookmark…** names and saves the open dashboard's view — its whole sheet (filters, date
  range, click selection, drill level, page, chart type, format) plus the shared filters — at most **30**
  per workbook. **Bookmarks…** lists them (dashboard and time saved) with **Apply** and **Delete**.
  Applying restores the shared filters and that dashboard's sheet and switches to it; if the dashboard was
  closed it is recreated under its saved name. Bookmarks save with the workbook (`Workbook/bookmarks-dialog.js`).
- **Parameters…** (P32) lists the workbook's parameters (at most 20) with **New**, **Edit** and **Delete**:
  a name (unique, 1–60 characters), a type (number / text / date), the allowed values (any, a list of ≤ 50,
  or a number range) and the current value — each checked before it is kept (`Core/parameters-model.js`).
  Parameters save with the workbook; disconnecting clears them from the screen.
- **Theme…** opens the theme dialog: an accent (Crimson, Blue, Teal, Violet, Graphite or a custom colour,
  refused with the reason if it can't carry white text) and chart colours (Default, Colour-blind safe,
  Muted), as labelled swatches. Choices apply live and save with the workbook; disconnecting returns the
  screen to the default theme until the workbook reopens ([tokens.md](../design/tokens.md#workbook-themes-p41)).
- **Import workbook…** opens a `.json` file. It needs a connection — a workbook opens against the
  connected server. If the canvas isn't empty, a confirm dialog asks before **replacing** it. The file
  is validated in full (below); anything repaired is listed in an issues dialog ("Opened <file> with N
  issue(s)"), otherwise a toast says "Opened <file>.".

## Validation (`parseWorkbook`)

**Hard failures** refuse the file with a specific toast and change nothing: not JSON or not a workbook
(`format` mismatch), a missing / non-integer / < 1 `version`, a `version` newer than this build, or a file
over 5 MB.

**Everything else is repaired and reported — never silently coerced.** Each issue is one sentence
naming the sheet and field ("Sheet "Sales": unknown chart type "radar" — reset to Bar."). Checked:

| Part | Rule |
|---|---|
| Tables | `id`, `db`, `table` non-empty text; ids and `db.table` unique (first kept); position finite and ≥ 0 else reset to 0; join keys a list of column names; at most **100** tables |
| Relationships | both endpoints reference a kept table; cardinality one of `1:1`, `1:N`, `N:1`, `N:M`; `joinType` left, else inner; at most **200** |
| Dashboards | each an object; name 1–60 characters (else reset to "Dashboard"); at most **50** |
| Sheet | `chartType` one of the 23 types; pills carry `db`, `table`, `column`, `category`; `role` and `agg` valid for the column's category (a bad `agg` resets to sum / count); at most 20 pills per shelf; at most 8 filters |
| Filters | known `op` (incl. P30 `contains` / `startsWith` / `endsWith` / `relative` / `top`; a `top` must carry its `topBy` measure); single value text (a non-text value resets to empty); `in` / `between` carry a text list; the `category` may be absent (back-filled from the catalog at runtime) |
| Marks, sort, pages, drill | shapes checked; drill needs ≥ 2 levels (≤ 6) and a path matching its depth; `selection` is never restored |
| Format | `numberFormat`, `dateFormat`, `dateBucket`, `legend` in their sets; `decimals` integer 0–10; `topN` in 5 / 10 / 20 / 50 / 100; `target` a finite number; booleans must be booleans; currency symbol ≤ 8 characters; axis titles ≤ 80 |
| Conditional formatting | ≤ 20 measures; `mode` / `scale` in their sets, `mid` a number or null; ≤ 5 rules each with a known `op` and `tone` and a numeric `value` — bad entries / rules dropped and reported |
| Date range | a temporal field; `preset` and `compare` in their sets; custom days `YYYY-MM-DD`; else cleared and reported |
| Shared filters | as sheet filters; at most **4** |
| Analytics | reference kind in its set (a constant needs a number), band two numbers (ordered), trend none / linear / log / poly2, forecast 0 / 3 / 6 / 12, totals booleans; a bad part is reset and reported |
| Title / caption | text ≤ 80 / ≤ 300 or null; `showTitle` a boolean; `format.fit` standard / width / height / entire |
| Table calculation | a known type, `along` auto / columns / rows, `window` an integer 2–30; else removed and reported |
| Date part | a known part on a date pill only; else reset to Auto and reported |
| Field choices | each a full field (db / table / column / category); ≤ 8; the shown field is added if missing; fewer than 2 → dropped |
| Parameters | ≤ 20; id `prm<n>`, a name, a known type; allowed list / range checked; a value outside them reset and reported. A filter or Top N pointing at a parameter the file doesn't have is unlinked and reported |
| Field settings | keys `db.table.column`; `alias` 1–60 characters, `agg` a known aggregation, `hidden` true; ≤ 2000; bad ones dropped and counted |
| Bookmarks | at most 30; a name 1–60 characters and a sheet (validated like any sheet; a well-formed click selection is kept, unlike a dashboard's); shared filters as above; a dashboard index in range, else "closed" (recreated when applied) |
| Link action | `https://` with a host and `{value}`, ≤ 500 characters; else removed and reported |
| Theme | `accent` a preset id or a valid custom `#rrggbb`, `palette` a known id; absent = default; else reset and reported |
| `active` | an integer index into the kept dashboards, else the Data Model opens |

Repaired settings never abort the import; an `entities` / `relationships` / `dashboards` value that
isn't a list means none of that part is opened.

## How opening works

`openWorkbook` (in `workbook.js`) clears the model (`canvas.clearModel()`) and closes every dashboard, then
re-adds each table through `canvas.addEntity(db, table, x, y, { joinKeys })`, maps saved entity ids to the
new ones, recreates relationships via `relations.restoreRelationship`, and recreates dashboards with
`createDashboard` + `updateSheet`. Saved sheets are validated over today's defaults (`sanitizeSheet`;
`restoreSheet` is the same without the report), so workbooks from older builds gain new fields.
Auto-save is paused while this runs. If a part fails to open, a danger toast says so and no success toast
or autosave follows.
