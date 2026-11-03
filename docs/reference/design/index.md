---
components: []
---
# Design System

The visual language of the Dashboard Builder and the reasoning behind it. Read this before any UI
change, then the topic file from the [map](#map). **Source of truth:** `Features/Core/core.css` (the
`:root` token block plus shared components), loaded before each feature's own
`Features/<Feature>/<feature>.css`. Keep the docs below and the stylesheets in step.

## Concept

> **Flat 2.0 + glass · warm neutrals + crimson · light and dark · calm.**
> Glass only on chrome that has nothing but the background wash beneath it (sidebar, tab bar, worksheet
> header) · everything that floats over content — menus, popovers, toasts, dialogs — is solid · one
> crimson accent · danger is a separate vermilion that always carries an icon and words · a fixed
> full-screen shell — no page scroll; panels scroll internally.

The builder is a two-world layout. A **left glass rail** owns connection and schema browsing; the
**right canvas** holds the data source, relationships and dashboard worksheets.

- **Structure** follows Windows 11 Fluent: 4/8/16/24 px spacing, one 8 px radius, 32 px controls and a
  soft elevation ramp.
- **Surfaces** follow Flat Design 2.0. The fixed chrome is translucent and blurs a warm background wash.
  Entity cards, the chart area, the crosstab and every overlay stay solid, so text is never read
  through other text.
- **Light or dark** is the viewer's choice: a **System / Light / Dark** toggle at the right end of the
  tab bar, with System (follow the OS) as the default
  ([tokens.md § Light and dark](tokens.md#light-and-dark), design decision
  [D22](../../decisions/decisions-platform.md#d22--fluent-glass-design-language)).

**Progressive disclosure:** a first-time user sees the few controls that matter. The rest appears when
relevant, such as the connection form's Advanced section, the Workbook menu and collapsible field
groups. Nothing is removed: an encoding that holds fields is always shown.

## Rules that never bend

- **Tokens only** — never hardcode a hex. The accent is crimson (`--accent-*`). Error / destructive is
  the vermilion `--danger-*` and is never shown by colour alone. Success is `--ok-*`, notices `--warn-*`.
  Field pills are blue / teal / violet, never red, so a pill never reads as an error.
- **Glass never overlaps content** — a surface that can sit on top of text (menu, popover, toast, dialog)
  is solid `--surface`; otherwise the text beneath shows through the blur.
- **Clickable on glass = more solid than the glass.** Controls on a glass panel are a frosted tier with a
  ≥ 3:1 edge and a full hover / pressed / selected / focus / disabled ladder
  ([tokens.md](tokens.md#controls-on-glass--three-tiers-and-a-state-ladder)).
- **Design rules** — optical alignment; space only 4 / 8 / 16 / 24 px; one radius for inner and outer
  shapes; saturation ≈ 70 %; font sizes 14 / 16 (content) and 24 / 32 (titles); the layout explains, not
  extra labels ([coding-standards.md § 11](../../development/coding-standards.md#11-design-rules)).
- **`hidden` attribute** for show/hide — never `style.display`.
- **Fixed shell** — the page never scrolls.
- **Never colour alone** — status is icon + text + colour.
- **One control height** — every toolbar control is `--ctl-h`.
- **Icons are inline SVG** from `Core/icons.js` — no icon font, no Unicode glyph icons.

These are golden rules 6–9 in [coding-standards.md](../../development/coding-standards.md).

## Map

| Topic | Doc |
|---|---|
| Colour, status, chart, type, spacing, elevation, glass tokens | [design/tokens.md](tokens.md) |
| Shell, sidebar, entity cards, worksheet header tiers, `hidden`, dialogs | [design/layout.md](layout.md) |
| CSS class vocabulary, shared and per feature | [design/components.md](components.md) |
| Motion tokens, reduced motion, accessibility posture | [design/motion-accessibility.md](motion-accessibility.md) |

How each screen uses the design: the [features/](../../concepts/worksheet/worksheet.md) docs.
