# Schema browser — database picker & table list

Sidebar, below the connection panel. Code: `Features/Schema/` (`SchemaController.cs`,
`_Schema.cshtml`, `schema.js`, `table-filter.js`, `schema.css`); the preview dialog is `Features/Rows/`.

## Database picker

- On `connection:changed` (connected), `schema.js` fills a native `<select>` from
  `GET /api/databases` (`SHOW DATABASES`), with a disabled "Select a database…" placeholder. On
  disconnect it clears.
- Choosing a database loads its tables. Switching databases replaces the table list but leaves the
  canvas untouched — an entity keeps the `db.table` it was dropped from.

## Table list

- `GET /api/databases/{db}/tables` (`SHOW TABLES FROM {db}`) renders one **table chip** per table
  (icon + name). The list scrolls internally.
- Each chip is `draggable="true"` and writes the `application/x-ch-table` payload `{db, table}` on
  `dragstart` — the drop side is in [canvas.md](canvas.md#dragging-a-table-onto-the-canvas).
- A **`＋` button** on each chip is the non-drag fallback: it dispatches `table:add` `{db, table}`,
  which `canvas.js` consumes exactly like a drop.
- A **search box** (`#table-search`, `maxlength` 100) above the list filters the chips by name —
  client-side, case-insensitive substring match (`matchTables` in `table-filter.js`). `Esc` clears it.
  When nothing matches, "No tables match." shows. The filter resets when the table list reloads.
- Chip icons are inline SVG (`Core/icons.js`). A **grip** (`.table-chip__grip`) appears on hover / focus
  (always on touch) as the drag affordance; the chip's tooltip says "Drag <table> onto the canvas" and
  the `＋` button's says "Add to the canvas (or drag the table)". Chips are tier-2 glass controls
  ([tokens.md](../design/tokens.md#controls-on-glass--three-tiers-and-a-state-ladder)).

## Row preview

- A **preview button** (eye icon, `.table-chip__peek`, `aria-label` "Preview rows of <table>") sits on each chip, shown
  on hover / focus like the grip. It opens the **rows dialog** (`Rows/rows-dialog.js`): the first **20** rows of the
  table (`tableRowsRequest` in `Rows/rows-model.js` → `POST /api/rows`,
  [api.md § Rows](../reference/api.md#rows)), with each column's **name and raw ClickHouse type** in a sticky
  header, then the rows. Read-only; no ordering (the first rows in storage order).
- The dialog is a native `<dialog>` labelled by its title ("<table> — first rows", the `db.table` beneath),
  closed by **Esc**, the X or Close (which also cancels a request still in flight). The table scrolls inside the
  dialog (max 80vh); the page never scrolls. A SQL `NULL` cell reads *NULL* in italic muted text, distinct from an
  empty string. A cell longer than 1000 characters is cut with an ellipsis; at most the table's first 200 columns
  show (the footer says "first N columns"). The footer states "N rows" or "First N rows — more exist".
- When any cell was cut, the dialog says so ("Some cells were cut at 1000 characters; the CSV export has the cut text too").
- **Export CSV** saves the rows shown (RFC 4180 quoting; a cell starting `= + - @` is prefixed with `'`, like the
  server's `CsvUtil`). A failure (a 400 / 502 / 504) shows its message in the dialog and a toast; the export stays disabled.
- The same dialog serves the worksheet's *View data* ([worksheet.md](worksheet.md#view-data)). Canvas entity cards
  still show no rows ([canvas.md](canvas.md)).

## Column profile / field details

- Each field row on a canvas entity card has a **Profile button** (`.col-row__profile`, analytics icon, `aria-label`
  "Profile <column>"; shown on hover / focus, always on touch; it does not toggle the join key). It opens the **profile
  dialog** (`Schema/column-profile-dialog.js`, rules in `column-profile-model.js`): `POST /api/databases/{db}/tables/{table}/profile`
  ([api.md](../reference/api.md)), read-only.
- **Field details:** Name, Type (raw ClickHouse type), Kind (the display category) and Role (*measure* for numeric,
  else *dimension* — the worksheet's rule). **Tiles:** Rows, Distinct (approx.), Null share (percent and "n of N rows"),
  and Min / Max for numeric and date columns. **Most frequent values:** up to 10, each a text label, an in-cell bar,
  the count and its share of the rows read; NULL reads *(NULL)* and an empty string *(empty)* (italic, so neither is mistaken for the text "NULL"), a value over 100
  characters is cut with an ellipsis. Bars are neutral (red means danger); the text carries every figure.
- Honesty: only the **first 1,000,000 rows ClickHouse returns, in no particular order** are read — not a statistical
  sample; when the table has at least that many a warning band says the figures describe those rows, not the table.
  Values are compared by their first 100 characters (a note says so when one was cut), so values differing only later
  count together. Distinct is an estimate. A share never rounds a partial share up to 100%
  and tiny ones read "<0.1%".
- **Copy name** copies the column name; **Copy values** copies the plain top values, one per line (NULL, empty and cut
  values left out). Both use `navigator.clipboard` and say so in a toast, or report that the browser blocked it.
- States: "Profiling…" while loading (closing cancels the request); a failure (404 / 502 / 504) shows icon + message
  in the dialog and a toast. **Esc**, X or Close close it. Not yet: sort order and semantic-role editing (see the backlog).

## Safety

`{db}` is validated against `SHOW DATABASES` (ordinal match) before it is quoted into `SHOW TABLES
FROM`; an unknown or hostile name → **404** before any SQL is built
([golden rule 2](../conventions/golden-rules.md#2-never-interpolate-an-identifier-you-havent-validated)).

## Union

The **Union** button beside the Tables heading opens a dialog listing the database's tables as checkboxes. **Show rows** is
enabled for 2–5 ticked tables (a sixth can't be ticked; the hint reads "Pick 2 to 5 tables."). It opens the rows dialog on
`POST /api/union` ([api.md § Union](../reference/api.md#union)): the first 20 rows of the tables stacked over their shared
columns, `Source table` first. A refusal (no shared column, …) shows in the dialog. Union is a preview only; it is not a
table on the canvas and no sheet can use it yet ([data-model.md](../backlog/data-model.md)).

## Unpivot

The **Unpivot** button beside **Union** opens a dialog: pick a table of the database, then tick the columns to **turn into rows** (2–50, all
of one kind: all numbers, all text, …) and, optionally, up to 5 columns to **keep** beside them. A column ticked on one side is disabled on
the other; the hint under the lists says what is missing. **Show rows** opens the rows dialog on `POST /api/unpivot`
([api.md § Unpivot](../reference/api.md#unpivot)): the first 20 rows, the kept columns then `Field` (the column's name) and `Value`, one
row per source row per chosen column; NULL stays empty and 0 stays 0. A refusal shows in the dialog. Unpivot is a preview only, like Union: it is not a
table on the canvas and no sheet can use it yet ([data-model.md](../backlog/data-model.md)). Splitting a text field is in
[calculated-fields.md § Text functions](calculated-fields.md#text-functions).
