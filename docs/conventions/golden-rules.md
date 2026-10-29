# Golden rules

The invariants every change must keep. [CLAUDE.md](../../CLAUDE.md#golden-rules-summary) carries the
one-line summary; this is the full text. Rules 1–4 shape every server change; 5–11 every frontend one.

## 1. The server is read-only against ClickHouse

Introspection (`SHOW`, `DESCRIBE`, `system.*`) and bounded `SELECT`s only. There is **no DDL/DML
endpoint** and there must not be one in v1. Every `CommandText` in `ClickHouseGateway.cs` is a
`SELECT`, `SHOW` or `DESCRIBE`, and every query also carries ClickHouse's own `readonly=2` unless the server refuses it at connect — never
remove the [database-level guards](../reference/clickhouse-integration.md#database-level-guards). If a feature seems to need writes, it is out of scope — see
[README § What this is not](../../README.md#what-this-is-not). Why: [D1](../reference/decisions.md#d1--read-only-against-clickhouse).

## 2. Never interpolate an identifier you haven't validated

Database, table and column names come from the client and end up inside SQL text — ClickHouse
parameters bind **values, not identifiers**. Before an identifier reaches a query:

1. **Validate** it against the live catalog for *this* connection (`SHOW DATABASES` →
   `SHOW TABLES FROM` → `DESCRIBE`). Unknown → `UnknownIdentifierException` → **404**/**400**.
2. **Quote** it with backticks, internal backticks doubled — via `ClickHouse/Identifier.cs` only.

Never hand-format an identifier at a call site. Detail and the failure it prevents:
[clickhouse-integration.md § Identifier injection](../reference/clickhouse-integration.md#identifier-injection).

## 3. Bind every value; bound every result

- Filter values, drill/page/selection pins and `in`/`between` operands are **bound typed parameters**
  (`{p0:Float64}`, `{p0:String}`, `{p0:Array(String)}`), never concatenated.
- Aggregations and operators come from **whitelists**; generated aliases (`k{n}`/`v{n}`) are
  server-validated against the request's counts.
- Every query carries a **validated `LIMIT`** (worksheet groups ≤ 5000 — Top-N **All** asks for the full
  5000; the Table pages 500 at a time with `offset` ≤ 10,000,000; CSV export ≤ 100,000 — [D24](../reference/decisions.md#d24--showing-all-data-bounded-requests-paging-other-date-grouping);
  distinct ≤ 1000, histogram bins 1..100 — out-of-range is a 400, never a silent clamp) and a
  server-side **time limit** (12 s). Never `SELECT *` without a bound — some tables are billions of rows.
- **Validate every input, on both sides:** the server's `RequestRules` is authoritative, the client's
  `validate.js` gives the inline message; reject rather than clamp, drop or coerce
  ([D23](../reference/decisions.md#d23--validation-contract-validate-on-both-sides-server-authoritative-reject-dont-clamp)).
  A grouped query that hits its limit says so (`truncated`) rather than cutting off silently.

## 4. Credentials live in the session and nowhere else

Never return the password to the client, never write it to logs or error messages, never put it in a
URL or query string. `ConnectionRegistry` is session-scoped; a new session starts with no connection.
Errors are mapped to clean messages without the connection string (`ApiControllerBase.SafeError`). Only non-secret fields (host, port, user, TLS flags) may be remembered in the
browser as recent sources — never the password or a token ([D70](../reference/decisions-connection.md#d70--recent-connection-sources-are-non-secret-and-kept-in-the-browser)).

## 5. Relationships are logical declarations, not database facts

ClickHouse enforces no foreign keys and no uniqueness — a MergeTree "primary key" is a sparse index.
The 1:1 / 1:N / N:1 / N:M links are the **user's assertions**, used for joins and layout. Never imply
the database validated them. See [data-model.md](../reference/data-model.md#relationship) and
[D5](../reference/decisions.md#d5--relationships-are-logical-declarations-not-database-constraints).

## 6. Toggle visibility with the `hidden` attribute, not `style.display`

`core.css` sets `[hidden] { display: none !important }` so one switch works everywhere (empty states,
inline errors, dropzone hints, the connect-first gate). Inline `display` fights it. Use `ui.js`
`show` / `hide` / `toggle`. See [design/layout.md](../design/layout.md#the-hidden-attribute).

## 7. Use the design tokens — never hardcode a hex

All colour/space/type values are CSS custom properties in `Features/Core/core.css` `:root`; a workbook
theme may override only the accent set and `--chart-cat-*`, from the checked values in
`Core/theme-model.js` ([tokens.md](../design/tokens.md#workbook-themes-p41)). The default accent is **crimson** (`--accent-*`); **danger is a separate vermilion** (`--danger-*`) and always
comes with an icon and words, so a red accent is never mistaken for an error. Success is `--ok-*`, notices
`--warn-*`; field pills are never red. Charts read `--chart-*` tokens. `tests/js/tokens.test.mjs` fails on a
hex outside `:root`, a retired token or a glass overlay; `tests/js/contrast.test.mjs` fails on a token text
pair under 4.5:1. See [design/tokens.md](../design/tokens.md).

## 8. Keep the shell fixed; scroll inside panels

`html, body { height: 100%; overflow: hidden }`. The sidebar, the table list, each entity card and the
worksheet scroll internally — the page itself never scrolls. See [design/layout.md](../design/layout.md).

## 9. Never colour alone

Status is **icon + text + colour** (connection pill, card status, toasts). Charts with ≥2 series carry
a legend; cardinality is **shape-coded**; Shape encodings survive greyscale. See
[design/motion-accessibility.md](../design/motion-accessibility.md).

## 10. Self-hosted, framework-free frontend

Vanilla JS ES modules + hand-written CSS, **no SPA framework, no build step, no CDN**. The one
library, ECharts, is vendored at `Features/Core/vendor/echarts.min.js`. Why:
[D4](../reference/decisions.md#d4--vanilla-js--hand-written-css-no-spa-framework),
[D13](../reference/decisions.md#d13--charting-via-self-hosted-apache-echarts-svg-renderer-themed-from-tokens).

Preferred stack for *new* projects (shadcn/ui NOVA, Lucide, Motion, dnd-kit, Zustand) is a reference
only — this app does not adopt it, because it is React-based.

## 11. Design rules

Enforced by `tests/js/tokens.test.mjs`.

1. **Optical alignment.** Align elements to what the eye reads — an icon beside text, a glyph in a
   circle, a play triangle — nudging by a pixel or two rather than trusting box edges.
2. **Space is 4 / 8 / 16 / 24 px.** Every gap, padding and margin uses `--s1` `--s2` `--s4` `--s6`; no
   other spacing token exists. A 1px border-compensation or optical nudge is the only exception, plus table Row height → Compact (0 vertical padding).
3. **One radius.** Inner and outer shapes share `--r` (8px), including chart bars and tooltip swatches
   (`tokens().radius` in `chart.js`); only `--r-pill` (pills, dots) differs.
4. **Saturation ≈ 70 %.** Token colours cap at HSL saturation 70 %; the Okabe–Ito colour-blind palette is
   a published standard and keeps its values. JS fallback colours come from `Core/theme-model.js`, never a
   second hex copy.
5. **Few font sizes.** `--fs-body` 14 / `--fs-lead` 16 for content, `--fs-title` 24 / `--fs-display` 32
   for titles and KPI numbers. No other screen `font-size`; chart text is 14px.
6. **Let the layout explain.** No secondary labels or descriptions that the layout already conveys.
