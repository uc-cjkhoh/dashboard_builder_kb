# Schema browser — database picker & table list

Sidebar, below the connection panel. Code: `Features/Schema/` (`SchemaController.cs`,
`_Schema.cshtml`, `schema.js`, `table-filter.js`, `schema.css`).

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

## Safety

`{db}` is validated against `SHOW DATABASES` (ordinal match) before it is quoted into `SHOW TABLES
FROM`; an unknown or hostile name → **404** before any SQL is built
([golden rule 2](../conventions/golden-rules.md#2-never-interpolate-an-identifier-you-havent-validated)).
