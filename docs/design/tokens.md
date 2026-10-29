# Design tokens

Every colour, size and depth value is a CSS custom property in the `:root` block of
`Features/Core/core.css` (loaded before every feature stylesheet). **Use the variables — never
hardcode a hex** ([golden rule 7](../conventions/golden-rules.md#7-use-the-design-tokens--never-hardcode-a-hex)).
The block defines the **light** theme; `:root[data-scheme="dark"]` overrides the colour and
elevation tokens ([Light and dark](#light-and-dark)). Ink/background pairs are chosen for ≥ 4.5:1
(WCAG AA) in both themes. `tests/js/tokens.test.mjs` fails on a retired token, a hex outside `:root`, or a
dark block that stops redefining the surfaces, or a menu / popover / toast / dialog styled as glass;
`tests/js/contrast.test.mjs` fails on any token text pair below 4.5:1 in either theme.

## Light and dark

The viewer picks **System** (default — follow the OS `prefers-color-scheme`), **Light** or **Dark** from
the toggle at the right end of the tab bar ([layout.md § Tab bar](layout.md#tab-bar)). The choice is a
per-browser preference (`localStorage` `dashboardbuilder.scheme`), never saved in the workbook.

- **One switch:** `<html data-scheme="light|dark">` is the only thing the stylesheets key off; no
  stylesheet reads `prefers-color-scheme` (`tokens.test.mjs` enforces it). `color-scheme` follows the
  attribute, so native controls and scrollbars match.
- **No flash:** `Core/scheme-boot.js`, a classic script in `<head>`, sets the attribute before first paint.
  It repeats `resolveScheme` from `Core/scheme-model.js` (pure; `tests/js/scheme.test.mjs` runs the boot
  script against it for every stored value × OS setting). Blocked storage → System.
- **Runtime:** `Core/scheme.js` owns the attribute — `isDark()`, `schemePref()`, `setSchemePref()`. It follows
  OS changes only while the choice is System, and emits `scheme:changed` on the bus when the painted
  scheme flips; the workbook theme (`Core/theme.js`) and the active chart (`dashboards.js`) re-apply on it.
- **Specificity:** `:root[data-scheme="dark"]` outweighs a bare `:root`, so the opaque-glass fallbacks
  (`@supports not (backdrop-filter…)`, `prefers-reduced-transparency`) also list `:root[data-scheme]`.

Colours below are capped at HSL saturation 70 %.

## Surfaces & ink

| Token | Light | Dark | Role |
|---|---|---|---|
| `--bg` | `#f6f3f3` | `#141113` | app background (under the wash) |
| `--surface` / `--surface-2` / `--surface-3` | `#ffffff` / `#faf7f7` / `#f2eded` | `#1c181b` / `#221d21` / `#2b2529` | cards, overlays and data / subtle fill / hover |
| `--ink` / `--ink-2` / `--ink-3` | `#1c1719` / `#423a3d` / `#6b6165` | `#f3eeef` / `#d8cfd2` / `#a89ea2` | primary / muted / caption text |
| `--line` / `--line-2` | `#ebe4e5` / `#d9cfd1` | `#2e282c` / `#42393e` | strokes |
| `--scrim` | `rgb(28 23 25 / .38)` | `rgb(0 0 0 / .55)` | dialog backdrop (plain dim, no blur) |

Warm neutrals (a faint red cast) so the crimson accent sits naturally. Captions (`--ink-3`) reach ≥ 5.1:1
on every surface in both themes.

`--wash` is the app background: three large, soft radial gradients (accent ~13 %, amber ~9 %, rose ~4 %)
on `--bg`. It is set as `background-color` + `background-image` (a colour cannot sit in the first layer of a
multi-layer `background` shorthand — the whole declaration would be dropped).

## Glass

| Token | Light | Dark | Role |
|---|---|---|---|
| `--glass` | `rgb(255 255 255 / .72)` | `rgb(28 24 27 / .70)` | tint |
| `--glass-line` | `rgb(60 20 28 / .10)` | `rgb(255 170 180 / .10)` | 1px stroke |
| `--glass-rim` | `rgb(255 255 255 / .9)` | `rgb(255 190 198 / .08)` | inset top highlight (tinted, never pure white, in dark) |
| `--glass-blur` | `blur(20px) saturate(150%)` | same | backdrop filter |
| `--glass-ctl` | `rgb(255 255 255 / .80)` | `rgb(43 37 41 / .85)` | fill of a control on glass (tier 2) |
| `--glass-ctl-hover` | `#fbf1f2` | `rgb(56 48 53 / .96)` | its hover fill (light is rose-tinted: white on near-white glass would not show) |
| `--ctl-edge` | `#8f8487` | `#7d7377` | outline of a control on glass — ≥ 3:1 against the panel and the control fill (WCAG 1.4.11) |

**Where glass is allowed — only where nothing but the wash is beneath it:** the sidebar, the tab bar
(`.canvas__bar`) and the worksheet header (`.ws-shelves`). **Never** on menus, popovers (Export, the context popup),
toasts or dialogs: they float over content, and blurred text behind would read through the text on top.
The tint stays ≥ 70 % so text on glass keeps AA contrast whatever the wash does beneath it. No
`backdrop-filter`, or `prefers-reduced-transparency: reduce` → `--glass` becomes the opaque `--surface-2`
and `--glass-ctl` the opaque `--surface`.

### Controls on glass — three tiers and a state ladder

Blur does not signal "clickable", so interactivity is carried by solidity, edge and feedback:

| Tier | What | Look |
|---|---|---|
| 1 · panel | sidebar, tab bar, worksheet header | `--glass` + `--glass-line` |
| 2 · control on glass | tabs, table chips, inputs / selects on glass | `--glass-ctl` + `--ctl-edge` border + `--glass-rim` + `--elev-2` |
| 3 · primary action | Connect, Apply | solid `--accent`, never glass |

Ghost controls on glass (`.ws-tool` encoding tools, `.iconbtn`) have no fill at rest — the icon + label
identify them — and become a tier-2 frosted pill on hover. Every state changes at least two of fill /
edge / shadow / ink / weight:

| State | Treatment |
|---|---|
| hover | `--glass-ctl-hover`, edge darkens to `--ink-3`, `--elev-8` (ghost: gains fill + edge + `--elev-2`), icon turns accent |
| pressed | `scale(.96–.98)`, shadow drops to the rim only |
| selected (active tab, open tool, Format on) | `--accent-soft` fill + `--accent` edge + 2px accent underline + weight 600 |
| focus | the 2px `--focus` ring (inset where the control sits near an edge, e.g. a chip's `＋`) |
| dragging (table chip) | `--accent` edge + `--elev-16`, grip shown |
| disabled | `opacity .5`, no shadow, `not-allowed`, no hover change |

Only `background`, `border-color`, `box-shadow`, `color` and `transform` transition (`--dur-fast`); the
blur is never animated. Under `@media (pointer: coarse)` glass controls grow to a 44px target.
`tests/js/contrast.test.mjs` pins `--ctl-edge` at ≥ 3:1 against the glass over the base and the strongest
wash tint, in both themes.

## Accent — one crimson

| Token | Light | Dark | Role |
|---|---|---|---|
| `--accent` / `-hover` / `-pressed` | `#b82035` / `#9c1c32` / `#821729` | `#d42a3c` / `#b72031` / `#991b2a` | primary fill (white `--on-accent` ≥ 4.5:1 in every state); active tab underline, selected relationship, single chart series |
| `--accent-ink` | `#a51d31` | `#eea0a7` | accent **text** |
| `--accent-soft` / `--accent-line` | `#fcf0f2` / `#f3c3ca` | `#3a1a20` / `#6b2a33` | tint / stroke |
| `--focus` | `--ink` | `--ink` | focus ring — neutral, so focus never looks like an error |

Inputs on focus keep a neutral `--ink-3` border plus a 2px `--accent` underline; an invalid input uses
`--danger-solid` and always has its icon + message below.

### Workbook themes (P41)

A workbook may carry a **theme** (`{ accent, palette }`, Workbook → **Theme…**) that overrides the accent
set above and `--chart-cat-1…8` — set inline on `:root` by `Core/theme.js`, re-applied on `scheme:changed`; the default theme sets nothing. The values live in `Core/theme-model.js`, the second token
source after `core.css :root`:

- **Accents:** Crimson (default — the values above), Blue, Teal, Violet, Graphite, each with light and dark
  sets; or a **custom** `#rrggbb`. Every set keeps white `--on-accent` ≥ 4.5:1 on the accent and hover,
  `--accent-ink` ≥ 4.5:1 on the surface **and** on `--accent-soft`, and the accent ≥ 3:1 against the
  surface (unit-tested for every preset and for derived custom colours). A custom colour too light for
  white text is refused with the reason; in dark mode it is lifted until it stands 3:1 off the surface.
- **Palettes:** Default, **Colour-blind safe** (Okabe–Ito), Muted — eight distinct colours per scheme.
- Surfaces, ink, status colours and glass never change with the theme.

`--print-paper` / `--print-ink` (`#ffffff` / `#000000`) are the print stylesheet's colours in every scheme.

## Status & field roles

Green = connected / success · amber = connecting / loading / notice · **vermilion = error or destructive**
· grey = idle. Status is always **icon + text + colour**
([golden rule 9](../conventions/golden-rules.md#9-never-colour-alone)) — which is what keeps danger apart
from the crimson accent.

| Token group | Light (bg / ink / line) | Dark (bg / ink / line) | Meaning |
|---|---|---|---|
| `--ok-*` | `#edfcf3` / `#136945` / `#abefc6` | `#112a1d` / `#75e0a7` / `#1f5c3c` | connected, success |
| `--warn-*` | `#fbf5ea` / `#7e3d16` / `#edcf9b` | `#2d2210` / `#e9c080` / `#6a4a13` | connecting, loading, notices; drill breadcrumb |
| `--danger-*` | `#fcf3f1` / `#95221a` / `#f3c9be`, `--danger-solid` `#af491f` | `#341a14` / `#eeae9d` / `#7a3322`, solid `#e47f65` | failed, invalid, destructive |
| `--dim-*` | `#eef4fc` / `#205fb7` / `#bfd5f4` | `#172235` / `#9dbfee` / `#2c4a78` | dimension pills (blue) |
| `--meas-*` | `#e9f8f8` / `#13676d` / `#a6e3e6` | `#10292b` / `#6fdde3` / `#1d5a5e` | measure pills (teal) |
| `--enc-*` | `#f4f1fd` / `#5b2fc9` / `#d9d2f7` | `#231d3a` / `#cac0f4` / `#4b3c8a` | Marks-encoding pills (violet; an encoding tint, not a status) |

Dark status tints are opaque (not translucent) so their contrast is fixed. `--up` = `--ok-ink` and
`--down` = `--danger-ink` colour KPI deltas and sparklines.

## Chart tokens

`chart.js` reads these off `:root` (resolving one level of `var()`) at render, and re-renders the active
chart on `scheme:changed` (a cache hit, no query), so charts follow light / dark. **Text wears ink tokens; only the
mark wears the series colour.**

| Token | Maps to | Role |
|---|---|---|
| `--chart-series` | `--accent` | a single data series (crimson) |
| `--chart-axis` | `--line-2` | axis lines |
| `--chart-grid` | `--line` | value-axis gridlines |
| `--chart-label` | `--ink-2` | primary chart text |
| `--chart-muted` | `--ink-3` | tick labels |
| `--chart-cat-1..8` | light `#2a78d6` `#146f14` `#e87ba4` `#c99424` `#1eac79` `#de6e41` `#4a3aa7` `#df4d4c`; dark `#5696e1` `#3ba55c` `#ec93b7` `#e0b152` `#2ec48c` `#e3895e` `#a192ec` `#e77675` | categorical ramp, fixed order |

- **One series** wears the accent. **≥2 series** (multiple measures, or a Colour split) draw
  `--chart-cat-*` in order, with a legend. Beyond 8 values the ramp repeats; the legend disambiguates.
- **Colour-by-category** (Format panel) colours a single-measure bar chart's bars from the same ramp.
- **Heatmap** and **continuous Colour** use a single-hue `--accent-soft` → `--accent` scale.
- **Treemap tile labels** pick black or white per tile with `Dashboard/contrast.js` (`pickInk`) so the
  label meets contrast on every `--chart-cat-*` fill.

## Type scale

Font (`--font`): `"Segoe UI Variable Text", "Segoe UI", -apple-system, BlinkMacSystemFont, system-ui,
sans-serif` — system fonts only. UI text is weight **400 / 600**. Two content sizes and two title sizes; no ad-hoc sizes.

| Token | Size | Role |
|---|---|---|
| `--fs-title` | 24px | dashboard and worksheet titles, dialog titles |
| `--fs-lead` | 16px | lead text |
| `--fs-body` | 14px | everything else: body, rows, chips, captions, badges, chart text |
| `--fs-display` | 32px | KPI numbers |

## Spacing, radius, sizing

- Spacing: `--s1` 4 · `--s2` 8 · `--s4` 16 · `--s6` 24 — nothing between ([golden rule 11](../conventions/golden-rules.md#11-design-rules)).
- Radius: one `--r` 8px for every shape, inner or outer · `--r-pill` 999px.
- `--sidebar-w`: 264px default (resizable — [layout.md](layout.md#sidebar)).
- `--topbar-h`: 60px — the shared `min-height` of the sidebar brand (`.sidebar__brand`) and the tab bar
  (`.canvas__bar`), so their bottom borders form one continuous line ([layout.md](layout.md#tab-bar)).
- **`--ctl-h`: 32px** — the shared control height for inputs, selects, `.btn`, toolbar buttons, icon buttons, the brand mark and
  shelf drop zones, so a row of mixed controls aligns on one baseline.

## Elevation & focus

- **Elevation (warm-tinted ramp):** `--elev-2` cards at rest · `--elev-8` hovered cards · `--elev-16`
  menus, popovers, toast and the card being dragged · `--elev-28` dialogs. Flat 2.0: shadows are soft and
  short; there are no hover-lift transforms.
- **Glass:** see [Glass](#glass) — chrome only.
- **Focus:** a 2px `--focus` (ink) outline with a 2px offset on `:focus-visible`, everywhere (inset on menu
  items).
- **Motion tokens** live with the motion rules: [motion-accessibility.md](motion-accessibility.md).
