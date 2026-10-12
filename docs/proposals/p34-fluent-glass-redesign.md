# P34 — Fluent glass redesign & input-validation contract

A proposal, not yet built. Two independent tracks shipped together: **(A)** a calmer visual language —
Windows 11 Fluent structure, Flat Design 2.0 surfaces, glass chrome, slate + blue, light and dark — with
less on screen at once; **(B)** a validation contract so no user input is unvalidated, no exception
goes unhandled, and no value is silently clamped, dropped or coerced. When built, the content moves into
[DESIGN.md](../../DESIGN.md), [design/](../design/tokens.md), the [features/](../features/worksheet.md)
docs and [api.md](../reference/api.md), and this file is deleted
([kb-maintenance.md](../conventions/kb-maintenance.md#when-you-make-a-change)).

## Goals

- **Pleasant, uncluttered, professional.** A first-time user sees the few controls that matter; the rest
  appears when relevant. Nothing is removed — it is disclosed progressively.
- **One accent, red only for danger.** Retire the red/black/white identity
  ([D7](../reference/decisions.md#d7--design-language-red--black--white-fixed-no-scroll-shell)) and the
  `--brand-soft` = danger-red ambiguity it created.
- **Light + dark**, following `prefers-color-scheme`.
- **Every input checked twice** — inline on the client, authoritatively on the server — with one error
  shape and honest status codes.

## Non-goals

- No change to the query model, join resolution, chart types, workbook format version or the read-only
  posture ([golden rules 1–3](../conventions/golden-rules.md)).
- No framework, build step, CDN or web font ([golden rule 10](../conventions/golden-rules.md)).
- No manual theme toggle (OS preference only) and no new features beyond the table search box.

## Approach

**Re-token, restyle, simplify — keep the structure.** The markup and the JS module graph stay; the
`:root` token block is replaced, shared components in `Core/core.css` and each feature stylesheet are
restyled, and the worksheet header gains progressive disclosure. Behaviour and existing tests stay
intact. Rejected: a from-scratch view rewrite (too much risk in the 1.8k-line `dashboards.js`) and a
colour-only reskin (doesn't address visual weight).

---

## A1 — Visual system

### Glass on chrome, solid under data

| Surface | Treatment |
|---|---|
| Sidebar, tab bar, worksheet header, menus/flyouts, dialogs, toast | **Glass:** `--glass` fill + `backdrop-filter: blur(24px) saturate(160%)` + 1px `--glass-line` stroke |
| Entity cards, chart area, crosstab, field pane list | **Solid** `--surface` — data stays crisp |
| App background | `--bg` plus a faint fixed wash (two large radial gradients: accent ~8%, teal ~6%) so glass has something to blur |

Fallback: `@supports not (backdrop-filter: blur(1px))` and `@media (prefers-reduced-transparency: reduce)`
swap `--glass` for an opaque `--surface-2`.

### Colour tokens

`--brand*`, `--side-*` and the decorative gradients (`--surface-grad`, `--head-grad`, `--side-grad`,
`--brand-grad`, `--glow-*`) are retired. Each existing `--brand` use is re-pointed by **meaning** to
`--accent*` or `--danger*`.

| Token | Light | Dark | Role |
|---|---|---|---|
| `--bg` | `#eef2f7` | `#0b1220` | app background |
| `--surface` / `--surface-2` / `--surface-3` | `#ffffff` / `#f6f8fb` / `#eef2f7` | `#111a2b` / `#162133` / `#1c2940` | cards / subtle fill / hover |
| `--glass` / `--glass-line` | `rgb(255 255 255 / .68)` / `rgb(15 23 42 / .08)` | `rgb(17 26 43 / .66)` / `rgb(255 255 255 / .08)` | chrome |
| `--ink` / `--ink-2` / `--ink-3` | `#0f172a` / `#334155` / `#64748b` | `#e2e8f0` / `#cbd5e1` / `#94a3b8` | text (all ≥ 4.5:1 on `--surface`) |
| `--line` / `--line-2` | `#e2e8f0` / `#cbd5e1` | `#1f2a3d` / `#2b3a52` | strokes |
| `--accent` / `-hover` / `-pressed` | `#2563eb` / `#1d4ed8` / `#1e40af` | same | primary fill (white text 5.2:1) |
| `--accent-ink` / `--accent-soft` / `--accent-line` | `#1d4ed8` / `#eff4ff` / `#bfd3fe` | `#93c5fd` / `rgb(59 130 246 / .16)` / `rgb(59 130 246 / .4)` | accent text / tint / stroke |
| `--ok-*` (bg/ink/line) | `#ecfdf3` / `#067647` / `#abefc6` | `rgb(23 178 106 / .14)` / `#75e0a7` / `rgb(23 178 106 / .4)` | connected / success |
| `--warn-*` | `#fffaeb` / `#93370d` / `#fedf89` | `rgb(247 144 9 / .14)` / `#fec84b` / `rgb(247 144 9 / .4)` | connecting / loading / notice |
| `--danger-*` (bg/ink/line/solid) | `#fef3f2` / `#b42318` / `#fecdca` / `#d92d20` | `rgb(240 68 56 / .14)` / `#fda29b` / `rgb(240 68 56 / .4)` / `#f04438` | error / destructive only |
| `--dim-*` | accent tints | accent tints | dimension pills |
| `--meas-*` (bg/ink/line) | `#ecfeff` / `#0e7490` / `#a5f3fc` | `rgb(6 182 212 / .14)` / `#67e8f9` / `rgb(6 182 212 / .4)` | measure pills |
| `--enc-*` (bg/ink/line) | `#f4f3ff` / `#5925dc` / `#d9d6fe` | `rgb(122 90 248 / .16)` / `#bdb4fe` / `rgb(122 90 248 / .4)` | Marks-encoding pills |

`--pend-*` is renamed `--warn-*`; `--info-*` becomes `--enc-*`. Contrast is re-checked for every
ink/background pair in both themes during the build; any pair under 4.5:1 is adjusted before ship.

### Chart tokens

`--chart-series` = `--accent`; axis/grid/label map to `--line-2` / `--line` / `--ink-2`. The 8-hue
categorical order is kept; dark-theme values are produced and checked with the dataviz skill's
validator. `chart.js` already reads tokens at render — it additionally listens to
`matchMedia('(prefers-color-scheme: dark)')` and re-renders the active chart on change.

### Type, shape, depth, motion

| Concern | Spec |
|---|---|
| Font | `"Segoe UI Variable Text", "Segoe UI", -apple-system, BlinkMacSystemFont, system-ui, sans-serif` (system only) |
| Sizes | `--fs-xs 12` · `--fs-sm 13` · `--fs-body 14` · `--fs-lead 16` · `--fs-title 20`; weights **400 / 600** only |
| Spacing | 4-pt: `--s1 4` · `--s2 8` · `--s3 12` · `--s4 16` · `--s5 20` · `--s6 24` · `--s7 32` |
| Radius | `--r-ctl 4px` (inputs, buttons, pills' inner) · `--r 8px` (cards, flyouts) · `--r-lg 12px` (dialogs) · `--r-pill 999px` |
| Control height | `--ctl-h 32px` (Fluent medium) — still one height for every toolbar control |
| Elevation | Fluent ramp, slate-tinted: `--elev-2` (cards), `--elev-8` (flyouts), `--elev-16` (dragging card), `--elev-28` (dialogs) |
| Motion | `--dur-fast 150ms` · `--dur 200ms` · `--dur-slow 250ms`; `--ease` `cubic-bezier(.33,0,.67,1)`, `--ease-out` `cubic-bezier(.1,.9,.2,1)`. Retire `--ease-back`, `sheen`, `dot-pulse`, `pulse-ring`. Reduced-motion block kept. |
| Focus | 2px `--accent` outline + 2px offset on `:focus-visible`, everywhere |

### Icons

A new `Core/icons.js` exports a small inline-SVG set (20px viewBox, 1.5px stroke, `currentColor`) —
connection, database, table, key, link, filter, colour, size, label, tooltip, detail, shape, path,
angle, drill, pages, sort, format, export, import, more, search, close, chevron, check, warning, error.
It replaces every Unicode glyph icon (◑ ◉ ⋯ ∠ ⤳ ▽ ⤵ ▦ ⤒ ⤓ ✎ ○). Self-hosted, no font.

---

## A2 — Layout & progressive disclosure

The fixed, no-scroll shell and the resizable sidebar stay
([golden rule 8](../conventions/golden-rules.md)).

| Region | Change |
|---|---|
| **Sidebar** | Glass rail, light or dark with the theme. Section titles in sentence case, `--fs-sm` 600, no uppercase tracking. |
| **Connection form** | Shows Host, Port, User, Password. TLS + "Trust self-signed certificate" move under a collapsed **Advanced** `<details>`; it opens automatically when TLS is off or the cert opt-in is on. Connected state stays the one-row summary (icon buttons for change / disconnect). |
| **Tables** | A **search box** above the list filters chips by name (client-side, case-insensitive, `Esc` clears); a "No tables match" line when empty. |
| **Tab bar** | Fluent tabs with an accent underline on the active tab. Import + Export merge into one **Workbook** overflow menu (⋯). Autosave shows as a quiet `--ink-3` "Saved" text. |
| **Worksheet view bar** | Chart-type picker stays a labelled control; Sort, Format, Export become icon buttons with tooltips and `aria-label`s. |
| **Encodings toolbar** | A visible row plus a **More** menu, by the rule in [Toolbar visibility](#toolbar-visibility). |
| **Field pane** | Each table's field group is collapsible (`<details>`), with small Dimensions / Measures labels inside; each field shows a type icon (text, number, date, bool) — not a coloured letter. |
| **Entity cards** | Flat solid card, 1px stroke, `--elev-2`. Head: table name (600) with the database muted before it; key columns get the key icon. Collapse caret kept. |
| **Pills** | Shape + text + colour ([golden rule 9](../conventions/golden-rules.md)): dimensions `--dim-*`, measures `--meas-*`, encodings `--enc-*`; invalid pills get a dashed `--danger-line` border + warning icon + tooltip. |
| **Empty states** | One sentence + one button, centred, `--ink-2`. |
| **Toast** | Glass, bottom-centre, icon + text; danger toasts stay until dismissed, others 5 s. |

### Toolbar visibility

A pure function `visibleTools(chartType, tools)` (unit-tested) decides each tool's place:

| Tool | Visible row when | Otherwise |
|---|---|---|
| Filters, Color, Label, Tooltip | always | — |
| Size, Shape | chart type is `scatter`, `square` or `circle` | More |
| Path | `line` or `area` | More |
| Angle | `pie` or `donut` | More |
| Detail, Drill, Pages | never by default | More |

**In-use override:** any tool with count > 0 is always in the visible row with its count badge, whatever
the chart type — no state is hidden behind More. Existing honesty notes (e.g. "Discrete colour needs
Bar/Line/…") are kept.

---

## B1 — Client validation

### Shared pieces

- **`Core/validate.js`** (pure, `node --test`): `host`, `port`, `int(min,max)`, `number`, `date`,
  `dateTime`, `text(maxLen, {required})`. Each returns `{ ok: true, value }` or `{ ok: false, error }`
  — a user-facing sentence. No throwing.
- **`ui.fieldError(input, msg)` / `ui.clearFieldError(input)`**: sets `aria-invalid="true"`, links an
  inline message (`.field-error`, warning icon + text) via `aria-describedby`, clears on `input`.
  Submitting/applying is blocked while any field in the form is invalid; focus moves to the first one.
- **Global handlers** in `Shell/app.js`: `window` `error` + `unhandledrejection` → danger toast
  "Something went wrong — try again" + `console.error`. A worksheet render error is caught and shown in
  the chart pane via the existing `warn()`, never a blank view.
- **`api.js`** reads `{ error }` and, defensively, ProblemDetails `title`/`errors`; a non-JSON error
  body maps to "Server error (status)".

### Per input

| Input | Rule | On failure |
|---|---|---|
| Host | required; hostname, IPv4 or bracketed/plain IPv6; ≤ 253; no scheme, port or path | inline: "Enter the host name only — put the port in Port" (when `://` or `:port` is present) |
| Port | required integer 1–65535 (blank no longer defaults) | inline |
| User / Password | user required ≤ 64; password ≤ 256 | inline |
| Tab rename | trim; 1–60 chars; `F2`/`Enter` starts rename from the keyboard | empty → revert + toast "Tab name is required."; over-length blocked by `maxlength` |
| Axis titles | ≤ 80 chars (`maxlength`) | — |
| Table drop | `db`/`table` are non-empty strings; table not already on canvas | duplicate → focus existing card + toast |
| Relationship | not a duplicate of an existing link; key categories compatible (number↔number, text↔text, date↔date) | blocked + toast naming both columns and types |
| Measure aggregation | only aggregations valid for the column's category are offered | — (server also accepts min/max on text/date, see B2) |
| Scalar filter | parsed by column category: number → strict number; date/datetime → strict ISO text (`YYYY-MM-DD[ HH:MM:SS]`, works for Date and DateTime columns); bool → `true`/`false`/`1`/`0` | invalid pill, not applied; inline message in the filter editor |
| Between filter | both bounds parse; lo ≤ hi | invalid pill + inline "From must be ≤ To" |
| In-list | values from distinct query | when the 200-value cap is hit: "Showing the first 200 values — more exist" |
| Pages | members cap 200 | same notice; load failure shows the server's message |
| Workbook import | full schema check, see below | issues dialog |
| Autosave restore | parse + same schema check | corrupt/newer entry copied to `…:backup-<ISO time>`, toast says so; never silently overwritten |

### Workbook import & restore

`workbook-model.js` validates every sheet field — pill shape (`db`, `table`, `column`, `category`),
`chartType`, `agg`, filter `op`, `sort` against their enums; `format.decimals` 0–10; `topN` in the
allowed set; `drill`, `pages`, `marks`, `selection` shapes; unique entity ids; `version` present and
numeric. Invalid parts are **reset to defaults and reported**: the import opens a dialog listing each
issue ("Sheet 'Sales': unknown chart type 'radar' — reset to Bar"). Hard failures (not JSON, wrong
`format`, missing/non-numeric `version`, newer `version`, > 5 MB) refuse the import with a specific
message.

---

## B2 — Server validation & error contract

### One error shape, honest codes

| Status | When | Body |
|---|---|---|
| 400 | invalid input — model binding, range, count, type-mismatched value | `{ "error": "<sentence>", "field": "<path>?" }` |
| 404 | unknown database/table/column on schema routes | `{ "error" }` |
| 409 | not connected | `{ "error" }` (unchanged) |
| 413 | body over the limit | `{ "error": "Request too large" }` |
| 502 | ClickHouse rejected or failed the query (`ClickHouseServerException`, network/TLS) | credential-safe `{ "error" }` (unchanged) |
| 500 | our own bug — anything else | `{ "error": "Unexpected error (ref <traceId>)" }`, logged with the trace id |

- `ApiBehaviorOptions.InvalidModelStateResponseFactory` emits the `{ error, field }` shape — first
  error only, no CLR type names or parser positions.
- `UseExceptionHandler` writes the 500 JSON for anything escaping a controller (e.g. a session read).
- `ApiControllerBase.SafeError` splits ClickHouse failures (502) from our exceptions (500).

### Limits — reject, never silently clamp or drop

| Field | Limit | Today |
|---|---|---|
| Request body (JSON APIs) | 256 KB via `[RequestSizeLimit]` | Kestrel default 30 MB |
| `ConnectRequest` host / user / password | ≤ 253 / 64 / 256, host format as B1 | no length check |
| Row + column dimensions | ≤ 12 total | unbounded |
| Measures | ≤ 10 | unbounded |
| Joins | ≤ 10 | unbounded |
| Filters | ≤ 8 → else 400 | extras silently dropped (wrong results) |
| `in` values | ≤ 500 → else 400 | silently truncated |
| `Limit` | 1–500 → else 400 | silently clamped |
| Histogram buckets / distinct limit | 1–100 / 1–1000 → else 400 | silently clamped |
| Sort alias | must be a generated `k{n}`/`v{n}` → else 400 | silently ignored |

Internal clamps stay as defence in depth but are no longer reachable from a valid request.

### Typed filter values

Before building SQL, each filter value is converted to its column's ClickHouse category (from the
`DESCRIBE` the validator already fetches): number → `decimal`/`double` invariant-culture parse,
date/datetime → ISO-8601 parse, bool → `true|false|0|1`. Failure → 400
"`'abc'` is not a number for column `amount`". The typed value is what gets bound.

### Fixes from the audit

- **min/max on text/date:** results are read by column category — non-numeric aggregates are returned as
  strings instead of `Convert.ToDouble` (which throws today → 502). `QueryResultRow.Values` becomes
  `IReadOnlyList<object?>`; the client formats by measure category.
- **Histogram / box plot filters:** `in` and `between` are applied (reusing `BuildCondition`). Filters on
  other tables can't apply to these single-table views — the client (which chooses what to send) counts
  them and shows a notice.
- **Remove** the uncalled `POST …/aggregate`, `GET …/preview` and `GET …/count` endpoints and their
  gateway methods, models and tests.

---

## Decisions this records (on ship)

- **D22 — Fluent glass design language** supersedes D7: slate + blue, glass chrome over solid data
  surfaces, light + dark by OS preference, red reserved for danger.
- **D23 — Validation contract**: validate on both sides, server authoritative; reject rather than
  silently clamp/drop; one `{ error, field? }` shape; 400/404/409/413/502/500 as above.
- Golden rule 7 is reworded: "Design tokens only — no hardcoded hex; red means danger, nothing else."

## Testing

- **xUnit:** host/port/length validators; every limit (at bound, bound + 1); typed filter conversion
  per category; model-state factory shape; `SafeError` 502 vs 500 split; min/max on text/date; removed
  endpoints return 404.
- **`node --test`:** `validate.js` (each parser, edge cases: blank, whitespace, `1e3`, `0x10`, `-0`,
  IPv6, over-length); workbook import validator (each field, repair + issue list, hard failures);
  toolbar tool-visibility rule per chart type.
- **jsdom:** `fieldError` wiring (`aria-invalid`, `aria-describedby`, clears on input); Advanced
  disclosure auto-opens; table search filtering.
- **Smoke (curl, spare dev port):** malformed JSON, empty body, wrong types, oversized body, 9 filters,
  `Limit: 0`, text value on a number column — each returns the documented status + `{ error }`.
- **Visual:** no headless browser on the build host — the user reviews light and dark on the dev port
  before deploy.

## Done when

[definition-of-done.md](../conventions/definition-of-done.md) is met, the design and feature docs
describe the new state, D22/D23 are in [decisions.md](../reference/decisions.md), this proposal is
deleted, and the live service is redeployed stop → copy → start
([deployment.md](../operations/deployment.md)).
