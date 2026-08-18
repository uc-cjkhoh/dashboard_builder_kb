# Design System

The visual language of the drag-and-drop dashboard builder, and the reasoning behind
it. **Source of truth (once built):** `wwwroot/css/site.css` — the `:root` token block
at the top. Until that file exists this doc *is* the spec; keep the two in sync
thereafter.

## Concept

> **High-contrast · RED / BLACK / WHITE · minimal.**
> Black sidebar (the "chrome") · white content canvas · one vivid red accent · a
> fixed full-screen shell — **no page scroll**; panels scroll internally.

The builder is a two-world layout: a **black left rail** that owns connection,
navigation, and the schema browser, and a **white right canvas** where entities,
relationships, and dashboard tabs live. The split makes "controls vs. workspace"
legible at a glance, and a single strong accent (red) marks the one thing that matters
in a given view — the primary action, the live relationship link, a danger. This is a
deliberate commitment to one accent rather than a palette of competing colors.

## Design tokens (CSS custom properties)

All defined in `:root` in `site.css`. **Use the variables — never hardcode a hex.**

### Surfaces & ink (the "white world" — canvas)
| Token | Value | Role |
|---|---|---|
| `--bg` | `#f4f4f5` | app canvas |
| `--surface` | `#ffffff` | cards, entity cards, panels |
| `--surface-2` | `#f4f4f5` | hover / subtle fills |
| `--ink` | `#0a0a0a` | primary text (~19:1 on white) |
| `--ink-2` | `#3f3f46` | muted text (~10:1) |
| `--ink-3` | `#71717a` | captions |
| `--line` / `--line-2` | `#e4e4e7` / `#d4d4d8` | borders |

### Sidebar (the "black world" — chrome)
| Token | Value |
|---|---|
| `--side-bg` | `#0d0d0f` |
| `--side-elev` | `#17171a` |
| `--side-ink` | `#f4f4f5` |
| `--side-muted` | `#a1a1aa` |
| `--side-line` | `#262629` |

### Brand accent — vivid red
| Token | Value | Role |
|---|---|---|
| `--brand` | `#cc0000` | primary accent; white text on it ~4.7:1 |
| `--brand-strong` | `#a10000` | hover/pressed |
| `--brand-ink` | `#a80000` | red **text** on white (~5:1) |
| `--brand-soft` | `#fce8e8` | soft red fill |

> ⚠️ **`--brand-soft` and `--danger-soft` are the same hex (`#fce8e8`).**
> **Never** reuse `--brand-soft` as a "success" cue — a soft-red flash reads as an
> *error*. Success feedback (e.g. "connection established", "table added") must use
> `--ok-bg`. This is an easy, real trap; treat it as a hard rule.

### Chart tokens (P9)
The worksheet's bar/line charts (rendered via the self-hosted ECharts library —
[D13](docs/project/decisions.md)) read these off `:root`, so charts stay inside the design
system. **Text (labels, ticks, tooltip) wears ink tokens; only the mark wears the series
color.**

| Token | Maps to | Role |
|---|---|---|
| `--chart-series` | `--brand` | the single data series (bar fill / line) |
| `--chart-axis` | `--line-2` | axis lines |
| `--chart-grid` | `--line` | value-axis gridlines (recessive) |
| `--chart-label` | `--ink-2` | primary chart text |
| `--chart-muted` | `--ink-3` | axis tick labels |

> **Series colour.** A **single** series wears the brand accent (the "one reserved accent"). With
> **multiple measures** (one series each) charts draw from `--chart-cat-1..8` — the dataviz skill's
> **validated categorical** order (colourblind-safe ΔE / contrast checked; sub-3:1 slots backed by
> the Table view), with a **legend** for ≥2 series so identity is never colour-alone. **Colour-by-
> category** (P10) colours a **single-measure bar** chart's bars by their category from the same
> validated palette — the x-axis already labels each bar, so colour restates identity (never colour-
> alone). A categorical ramp **keyed to a second dimension** across series is still future work.

### Status pills — traffic-light semantics
Green = connected/active · amber = connecting/loading · red = failed · grey = idle.
These map directly onto the builder's states: the **connection indicator**, a table
that is **loading its preview**, a **failed query**, an **unused/idle** entity.

| Token group | Values | Meaning |
|---|---|---|
| `--ok-*` | bg `#e7f5ec` / ink `#166534` / line `#b7e0c4` | Connected / Active |
| `--pend-*` | bg `#fdf1da` / ink `#9a5b00` / line `#f2d59a` | Connecting / Loading |
| `--danger-*` | soft `#fce8e8` / line `#f0b8b8` | Failed |
| (muted) | greys | Idle / not yet on canvas |

Red stays **reserved for critical** (danger + the brand accent). Status is always
communicated by **icon + text + color**, never color alone.

### Relationship / cardinality colors
Relationship links on the canvas use `--ink-2` for the line and `--brand` when a link
is **selected or being drawn**. Cardinality endpoints (the "one" vs. "many" markers)
are shape-coded, not color-coded, so they read without color — see
[drag-and-drop.md](docs/drag-and-drop.md).

### Trend colors (dashboard KPI deltas/sparklines)
`--up` = `#1e7b45` (green, ~4.8:1), `--down` = `#cc0000` (red).

### Type scale
Font: `"Segoe UI", system-ui, -apple-system, "Helvetica Neue", Arial, sans-serif`.

| Token | Size | Role |
|---|---|---|
| `--fs-title` | 20px | page / canvas `h1` |
| `--fs-lead` | 15px | lead text |
| `--fs-body` | 14px | body (base) |
| `--fs-sm` | 13px | secondary (column rows, chips) |
| `--fs-xs` | 12px | captions, type badges |
| `--fs-kpi` | 30px | dashboard KPI numbers |

A single named scale — do not set ad-hoc inline font sizes.

### Spacing, radius, shadow
- Spacing on an **8-pt system**: `--s1: 4px … --s6: 28px`.
- Radius: `--r-sm: 8px`, `--r: 12px`, `--r-lg: 16px`, `--r-pill: 999px`.
- `--sidebar-w: 260px`.
- **`--ctl-h: 34px`** — the shared control height. Inputs, selects, `.btn`, and toolbar controls
  (`.ws-toolbtn`, the sort/chart selects, shelf drop-zones) all resolve to this one height so a
  row of mixed controls aligns on a single baseline. Reach for it whenever you add a control to a
  toolbar rather than re-deriving a height from padding.

### Toolbar alignment (worksheet)
The worksheet shelves row reads **data-left / view-right**: the field shelves (Columns/Rows/Filters)
sit left; the **view controls** (Sort · Chart · Format) form a right-aligned cluster, split off by a
hairline (`.ws-sort` carries `margin-left:auto` + a `border-left`, so everything after it rides
right). Every control in the row is `--ctl-h` tall. The **Format** panel (P10) opens as a full-width
second line under a dashed divider. Keep new toolbar controls on `--ctl-h` and inside this
left/right split so the row stays aligned as features land.

### Elevation & depth (2.5D)
The UI is layered, not flat. A three-step elevation scale expresses height:
`--elev-1` (resting chrome: buttons, chips, pills), `--elev-2` (cards at rest), `--elev-3`
(lifted/hovered cards, dialogs, toasts). `--shadow` aliases `--elev-2` for back-compat.
`--glow-brand` / `--glow-brand-sm` are red-tinted glows for the primary action.
- **Gradients** give surfaces a light-from-above feel, all composed from the palette via
  `color-mix` (never new hexes): `--surface-grad` (cards), `--head-grad` (card/dialog headers,
  sticky grid header), `--side-grad` / `--side-elev-grad` (sidebar + its chips/inputs),
  `--brand-grad` (primary button).
- **Cast shadows** sell the depth: the sidebar casts onto the canvas; cards **lift** on hover
  (`translateY` + `--elev-3`) and **tilt** while dragging; the canvas is a faint dot-grid with a
  soft brand glow so cards read as floating above it.

### Motion
Interaction feels alive but never gratuitous. Tokens: `--motion: 160ms`, `--motion-slow: 280ms`,
`--ease` (standard) and `--ease-back` (slight overshoot for entrances). Applied as: entity cards
**drop in** (scale+rise) and **tilt** while dragging, toasts **slide up**, dialogs **scale in**
with a blurred backdrop, the connecting/loading pill **shimmers** and its glyph **spins**, the
brand dot **pulses**, a **light sweeps** across the primary button on hover, table chips reveal
**staggered**, buttons/chips/icons **lift on hover**, the linking connector **pulses**, and the
entity view **collapses** by animating `max-height`. **All of it is gated by
`@media (prefers-reduced-motion: reduce)`**, which zeroes every duration — motion is an
enhancement, never required to understand state (state is still icon+text+color).

## Layout rules

- `html, body { height: 100%; overflow: hidden }` — **no page scroll**. The shell is a
  fixed full-screen split: black sidebar + white canvas. Scrolling happens *inside*
  regions — the sidebar's table list, each entity card's (fixed-height) column list, the
  active view. Scrollbars are **thin + themed** (dark in the sidebar, light in content, red on hover).
- **Resizable sidebar:** the grid column is `var(--sidebar-w)`; a right-edge handle
  (`sidebar.js`) drags it between a minimum and **30% of the viewport**. The sidebar uses a
  refined, minimalist take on the RED/BLACK/WHITE language (brand mark, tight uppercase labels,
  flat chips, hairline red edge-glow), adapted from the reference admin console.
- **Entity cards are uniform height** — a `db.table` head over a scrollable column list, no data
  preview (data lives in dashboard widgets).
- **`[hidden] { display: none !important }`** — interactive regions carry an author
  `display` (flex/grid) that would otherwise beat the UA `[hidden]` rule. The
  `!important` makes the `hidden` attribute the single reliable show/hide switch
  app-wide (empty states, inline field errors, the dropzone's "drop a table here" hint,
  the "connect first" gate). **Toggle visibility via the `hidden` attribute, not
  `style.display`.** (Also a [CLAUDE.md golden rule](CLAUDE.md#golden-rules).)

## Reusable UI components (CSS class vocabulary)

The builder's actual surfaces. (This replaces the CRUD/reporting vocabulary a generic
admin template would ship with — there are no report lists or record-CRUD tables here.)

| Pattern | Key classes |
|---|---|
| Sidebar shell | `.sidebar`, `.sidebar__section`, `.sidebar__title` |
| Connection form | `.conn-form`, `.form-field`, `.form-field--wide`, `.btn--primary` (Connect) |
| Connection indicator | `.pill`, `.pill--ok` (connected), `.pill--warn` (connecting), `.pill--danger` (failed), `.pill--muted` (idle) |
| Database picker | `.select` (native `<select>` dropdown of databases) |
| Table list | `.table-list`, `.table-chip` (**`draggable="true"`**), `.table-chip__icon`, `.table-chip__name` |
| Canvas | `.canvas`, `.canvas__empty` (dropzone hint, toggled via `hidden`) |
| Entity card | `.entity`, `.entity__head`, `.entity__cols`, `.col-row`, `.col-row__key` (join-key checkbox), `.col-row__type` (type badge), `.entity__grid` (sample data), `.entity--dragging` |
| Relationship link | `.rel-link`, `.rel-link--selected`, `.rel-end--one`, `.rel-end--many`, `.rel-badge` (cardinality label) |
| Subtabs | `.tabs`, `.tab`, `.tab.is-active`, `.tab__close`, `.tab-add` (new dashboard) |
| Dashboard widget | `.widget`, `.widget__kpi` (`--fs-kpi`), `.widget__delta` (`--up`/`--down`) |
| Card / panel | `.card`, `.card--fill`, `.card__head`, `.card__body.flush`, `.card__foot` |
| Data grid (preview) | `.data`, `.num` (right-align numerics), `.mono`, `.cell-strong`, `.cell-sub` |
| Buttons | `.btn`, `.btn--primary`, `.btn--danger` |
| Icon actions | `.iconbtn`, `.iconbtn--danger` (remove entity, close tab) |
| Dialog (native `<dialog>`) | `.dialog`, `.dialog--sm`, `.dialog__head/body/foot`, `.form-grid`, `.form-field` |
| Empty state | `.empty`, `.empty-row` |
| Toast | `.toast` (generic, reused everywhere; `role="status"` + `aria-live`) |
| Inline validation | `.has-error` (on `.form-field`), `.field-error` (injected message) |
| Add/flash feedback | `.row-new` (animates with `--ok-bg`, never `--brand-soft`) |

### Entity cards and table chips are drag surfaces, not click-to-open rows
A `.table-chip` in the sidebar is **draggable onto the canvas** — dragging is its
whole purpose; it is not a link. An `.entity` on the canvas is **moved by dragging its
head**, and its rows expose explicit affordances only: a **join-key checkbox** per
column, and a **remove** (trash) icon on the card. There is deliberately no
"click the card to do something" behavior — the card body performs no hidden action,
so nothing about it should promise one. Preview data rows (`.data tbody tr`) get a
**plain** background hover; rows are not clickable.

## Accessibility posture

- `aria-current` on the active subtab; `aria-label`s on icon-only buttons (remove
  entity, close tab, connect); `role="search"` where a filter exists;
  `role="status"`/`aria-live` on the toast and the connection indicator.
- Status conveyed by **icon + text + color** (not color alone) — the connection state,
  loading, and failure all carry a label and glyph.
- Cardinality is **shape-coded** (one/many endpoint markers), readable without color.
- Contrast ratios chosen against **WCAG AA** (annotated in the token tables).
- Native `<dialog>` for modals (focus trapping, `Esc` to close); a custom confirm
  `<dialog>` instead of `window.confirm` for styled, consistent confirmations
  (e.g. removing an entity that has relationships).

## Related

- Design tokens in code → `wwwroot/css/site.css` `:root` block (built in the design-system
  phase of the [build plan](BUILD_PLAN.md)).
- Why these choices were made → [docs/project/decisions.md](docs/project/decisions.md).
- How the design renders per screen → [docs/app/modules.md](docs/app/modules.md).
- Drag/drop, entity cards, cardinality markers → [docs/drag-and-drop.md](docs/drag-and-drop.md).
