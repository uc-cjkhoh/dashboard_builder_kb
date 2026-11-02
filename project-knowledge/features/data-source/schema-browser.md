# Schema browser — database picker & table list

The schema browser sits in the sidebar, below the connection panel. It lists the connected server's databases and tables,
previews rows, and profiles columns.

**Code:**

- `Features/Schema/` — `SchemaController.cs`, `_Schema.cshtml`, `schema.js`, `table-filter.js`, `schema.css`
- `Features/Rows/` — the preview dialog

## At a glance

- **Pick a database**, then drag a table chip onto the canvas (or press its `＋`); a search box filters the chips.
- **Preview rows:** the eye button shows a table's first 20 rows, read-only, with CSV export.
- **Profile a column:** a card row's Profile button summarises the first 1,000,000 rows ClickHouse returns.
- **Union / Unpivot** dialogs preview a combined source and can add it to the model.
- **Safety:** a database name is checked against `SHOW DATABASES` before it is used in SQL.

## Database picker

- **Filling it.** On `connection:changed` (connected), `schema.js` fills a native `<select>` from `GET /api/databases` (`SHOW DATABASES`).
  It has a disabled "Select a database…" placeholder. On disconnect it clears.
- **Open list.** Where the browser supports customizable selects, the open list takes the table rows' design
  (`appearance: base-select`, `@supports` in `schema.css`):
  - a solid panel (`--surface`, one stroke, `--elev-16`, 8px radius) of flat 32px rows;
  - names start on the closed control's text lane;
  - an ink wash on hover / focus;
  - the current database bold, with an accent tick at the right;
  - the app's chevron (flipped while open) in place of the browser's built-in (user-agent) triangle;
  - the placeholder is not listed.

  Other browsers keep the native list, themed by `core.css`.
- **Choosing a database** loads its tables. Switching databases replaces the table list but leaves the canvas untouched:
  an entity keeps the `db.table` it was dropped from.

## Table list

- **Chips.** `GET /api/databases/{db}/tables` (`SHOW TABLES FROM {db}`) renders one **table chip** per table (icon + name).
  The list scrolls internally.
- **Drag.** Each chip is `draggable="true"` and writes the `application/x-ch-table` payload `{db, table}` on `dragstart`.
  The drop side is in [canvas.md](canvas.md#dragging-a-table-onto-the-canvas).
- **`＋` button.** The non-drag fallback on each chip. It dispatches `table:add` `{db, table}`, which `canvas.js` consumes exactly like a drop.
- **Search.** A search box (`#table-search`, `maxlength` 100) above the list filters the chips by name.
  - It is a client-side, case-insensitive substring match (`matchTables` in `table-filter.js`).
  - `Esc` clears it.
  - When nothing matches, "No tables match." shows.
  - The filter resets when the table list reloads.
- **Look and tooltips.**
  - Chip icons are inline SVG (`Core/icons.js`).
  - A **grip** (`.table-chip__grip`) appears on hover / focus as the drag affordance.
  - The chip's tooltip says "Drag <table> onto the canvas"; the `＋` button's says "Add to the canvas (or drag the table)".
  - Chips are tier-2 glass controls ([tokens.md](../../design/tokens.md#controls-on-glass--three-tiers-and-a-state-ladder)).

## Row preview

- **Opening it.** A **preview button** (eye icon, `.table-chip__peek`, `aria-label` "Preview rows of <table>") sits on each chip,
  shown on hover / focus like the grip. It opens the **rows dialog** (`Rows/rows-dialog.js`).
- **What it shows:** the first **20** rows of the table, read-only, with no ordering (the first rows in storage order).
  - Request: `tableRowsRequest` in `Rows/rows-model.js` → `POST /api/rows` ([api.md § Rows](../../reference/api.md#rows)).
  - A sticky header shows each column's **name and raw ClickHouse type**, then the rows follow.
- **The dialog** is a native `<dialog>` labelled by its title ("<table> — first rows", with the `db.table` beneath).
  - **Esc**, the X or Close closes it. Closing also cancels a request still in flight.
  - The table scrolls inside the dialog (max 80vh); the page never scrolls.
- **Cells and limits:**
  - A SQL `NULL` cell reads *NULL* in italic muted text, distinct from an empty string.
  - A cell longer than 1000 characters is cut with an ellipsis. When any cell was cut, the dialog says so
    ("Some cells were cut at 1000 characters; the CSV export has the cut text too").
  - At most the table's first 200 columns show (the footer says "first N columns").
  - The footer states "N rows" or "First N rows — more exist".
- **Export CSV** saves the rows shown, with RFC 4180 quoting. A cell starting `= + - @` is prefixed with `'`, like the server's `CsvUtil`.
- **Failure:** a 400 / 502 / 504 shows its message in the dialog and a toast; the export stays disabled.
- **Reuse:** the same dialog serves the worksheet's *View data* ([worksheet.md](../worksheet/worksheet.md#view-data)).
  Canvas entity cards still show no rows ([canvas.md](canvas.md)).

## Column profile / field details

- **Opening it.** Each field row on a canvas entity card has a **Profile button** (`.col-row__profile`, analytics icon,
  `aria-label` "Profile <column>"; shown on hover / focus).
  It opens the **profile dialog** (`Schema/column-profile-dialog.js`, rules in `column-profile-model.js`).
  The request is `POST /api/databases/{db}/tables/{table}/profile` ([api.md](../../reference/api.md)), read-only.
- **Field details:** Name, Type (raw ClickHouse type), Kind (the display category) and Role
  (*measure* for numeric, else *dimension* — the worksheet's rule).
- **Tiles:** Rows, Distinct (approx.), Null share (percent and "n of N rows"), and Min / Max for numeric and date columns.
- **Most frequent values:** up to 10. Each has a text label, an in-cell bar, the count and its share of the rows read.
  - NULL reads *(NULL)* and an empty string reads *(empty)*, in italic, so neither is mistaken for the text "NULL".
  - A value over 100 characters is cut with an ellipsis.
  - Bars are neutral (red means danger); the text carries every figure.
- **Honesty about what was read:**
  - Only the **first 1,000,000 rows ClickHouse returns, in no particular order** are read. This is not a statistical sample.
    When the table has at least that many, a warning band says the figures describe those rows, not the table.
  - Values are compared by their first 100 characters (a note says so when one was cut), so values differing only later count together.
  - Distinct is an estimate.
  - A share never rounds a partial share up to 100%, and tiny ones read "<0.1%".
- **Copy name** copies the column name. **Copy values** copies the plain top values, one per line (NULL, empty and cut values left out).
  Both use `navigator.clipboard` and say so in a toast, or report that the browser blocked it.
- **States:** "Profiling…" while loading (closing cancels the request).
  A failure (404 / 502 / 504) shows icon + message in the dialog and a toast. **Esc**, X or Close close it.
- Not yet: sort order and semantic-role editing (see the backlog).

## Safety

`{db}` is validated against `SHOW DATABASES` (ordinal match) before it is quoted into `SHOW TABLES FROM`.
An unknown or hostile name → **404** before any SQL is built
([golden rule 2](../../engineering/golden-rules.md#2-never-interpolate-an-identifier-you-havent-validated)).

## Union

The **Union** button beside the Tables heading opens a dialog listing the database's tables as checkboxes.

- **Picking:** 2–5 tables. A sixth can't be ticked; the hint reads "Pick 2 to 5 tables."
- **Show rows** is enabled for 2–5 ticked tables. It opens the rows dialog on `POST /api/union` ([api.md § Union](../../reference/api.md#union)):
  the first 20 rows of the tables stacked over their shared columns, `Source table` first.
- A refusal (no shared column, …) shows in the dialog.
- **Add to model** (primary, same pick rule) puts the union on the Data Source as a card worksheets can read ([query-sources.md](query-sources.md)).

## Unpivot

The **Unpivot** button beside **Union** opens a dialog.

- **Picking:**
  1. Pick a table of the database.
  2. Tick the columns to **turn into rows**: 2–50, all of one kind (all numbers, all text, …).
  3. Optionally tick up to 5 columns to **keep** beside them.

  A column ticked on one side is disabled on the other. The hint under the lists says what is missing.
- **Show rows** opens the rows dialog on `POST /api/unpivot` ([api.md § Unpivot](../../reference/api.md#unpivot)).
  It shows the first 20 rows: the kept columns, then `Field` (the column's name) and `Value`, one row per source row per chosen column.
  NULL stays empty and 0 stays 0.
- A refusal shows in the dialog.
- **Add to model** (primary, same pick rule) puts the unpivot on the Data Source as a card worksheets can read ([query-sources.md](query-sources.md)).
  There, `Value` keeps the columns' kind.

Splitting a text field is in [calculated-fields.md § Text functions](../worksheet/calculated-fields.md#text-functions).
