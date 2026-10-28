# Design System

The visual language of the Dashboard Builder and the reasoning behind it. **Source of truth:**
`Features/Core/core.css` — the `:root` token block plus shared components — loaded before each
feature's own `Features/<Feature>/<feature>.css`. Keep the docs below and the stylesheets in step.

## Concept

> **Flat 2.0 + glass · warm neutrals + crimson · light and dark · calm.**
> Glass only on chrome that has nothing but the background wash beneath it (sidebar, tab bar, worksheet
> header) · everything that floats over content — menus, popovers, toasts, dialogs — is solid · one
> crimson accent · danger is a separate vermilion that always carries an icon and words · a fixed
> full-screen shell — no page scroll; panels scroll internally.

The builder is a two-world layout: a **left glass rail** owns connection and schema browsing; the **right
canvas** holds the data model, relationships and dashboard worksheets. Windows 11 Fluent structure
(4-pt spacing, 6/10/14 px radii, 32 px controls, a soft elevation ramp) with Flat Design 2.0
surfaces: the fixed chrome is translucent and blurs a warm background wash, while entity cards, the chart
area, the crosstab and every overlay stay solid so text is never read through other text. Light or dark is the viewer's choice — a
**System / Light / Dark** toggle at the right end of the tab bar, System (follow the OS) by default
([tokens.md § Light and dark](docs/design/tokens.md#light-and-dark),
[D22](docs/reference/decisions.md#d22--fluent-glass-design-language)).

**Progressive disclosure:** a first-time user sees the few controls that matter; the rest appears when
relevant (the connection form's Advanced section, the encodings **More** menu, the Workbook menu,
collapsible field groups). Nothing is removed — an encoding that holds fields is always shown.

## Rules that never bend

- **Tokens only** — never hardcode a hex. The accent is crimson (`--accent-*`); error / destructive is
  the vermilion `--danger-*` and is never shown by colour alone; success is `--ok-*`, notices `--warn-*`.
  Field pills are blue / teal / violet — never red — so a pill never reads as an error.
- **Glass never overlaps content** — a surface that can sit on top of text (menu, popover, toast, dialog)
  is solid `--surface`, or the text beneath shows through the blur.
- **Clickable on glass = more solid than the glass.** Controls on a glass panel are a frosted tier with a
  ≥ 3:1 edge and a full hover / pressed / selected / focus / disabled ladder
  ([tokens.md](docs/design/tokens.md#controls-on-glass--three-tiers-and-a-state-ladder)).
- **`hidden` attribute** for show/hide — never `style.display`.
- **Fixed shell** — the page never scrolls.
- **Never colour alone** — status is icon + text + colour.
- **One control height** — every toolbar control is `--ctl-h`.
- **Icons are inline SVG** from `Core/icons.js` — no icon font, no Unicode glyph icons.

These are golden rules 6–9 in [golden-rules.md](docs/conventions/golden-rules.md).

## Map

| Topic | Doc |
|---|---|
| Colour, status, chart, type, spacing, elevation, glass tokens | [docs/design/tokens.md](docs/design/tokens.md) |
| Shell, sidebar, entity cards, worksheet header tiers, `hidden`, dialogs | [docs/design/layout.md](docs/design/layout.md) |
| CSS class vocabulary, shared and per feature | [docs/design/components.md](docs/design/components.md) |
| Motion tokens, reduced motion, accessibility posture | [docs/design/motion-accessibility.md](docs/design/motion-accessibility.md) |

How each screen uses the design: the [features/](docs/features/worksheet.md) docs.
