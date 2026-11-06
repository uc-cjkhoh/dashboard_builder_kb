---
components: [src/DashboardBuilder/Features/Core/icons.js]
---
# Icons

The icon set is one file, `Features/Core/icons.js`: self-hosted inline SVG, no icon font and no CDN
([golden rule 10](../../development/coding-standards.md#10-self-hosted-framework-free-frontend)).
Look an icon up here before drawing a new one; reuse beats adding.

## Rules

- **Grid:** a 20 × 20 viewBox, a 1.5px round stroke, `currentColor` — so an icon takes its button's ink in every theme.
- **API:** `icon(name, { size = 16, label })` returns an `<svg class="icon">`. Without `label` it is `aria-hidden`;
  with one it is `role="img"`. An unknown name throws. `ICON_NAMES` lists them all.
- **Markup:** `<span data-icon="name"></span>` in a view is filled with the same glyph at start-up.
- **Never colour alone** ([golden rule 9](../../development/coding-standards.md#9-never-colour-alone)): an icon
  that carries meaning sits beside words or in a button with an `aria-label` and tooltip.
- **Adding one:** draw it on the 20px grid, add it to `PATHS`, and list it below. `tests/js/icons.test.mjs` checks that
  every required name exists, that each path is plain SVG path data, and that no icon copies the Analytics glyph.

## Where the notable ones are used

| Icon | Used for |
|---|---|
| `settings` | the **Settings** menu in the tab bar's right-most slot — three sliders (it was a sun-like gear, too close to `sun`) |
| `hierarchy` | the **Hierarchies** tool in the worksheet sidebar — a parent over two children |
| `calc`, `param` | the **Calculated fields** and **Parameters** sidebar tools |
| `chart-gauge` | the **Performance timings** tile at the bottom of the sidebar body. It is also the Gauge chart type's glyph, so the two share a drawing |
| `monitor`, `sun`, `moon` | the **Appearance** toggle: System, Light, Dark |
| `drill` | the **Drill** Marks slot and the drill breadcrumb (no longer the Hierarchies icon) |
| `edit` | the pencil **Edit** button built into each row of the Calculated fields dialog, and field renaming |
| `export`, `import` | **Export** and **Import workbook…** in the worksheet view bar |
| `more` | the ⋯ **Sheet actions** menu |
| `sidebar` | collapse / expand the sidebar and the field pane |
| `plus`, `minus`, `close`, `check`, `chevron` | add, remove, dismiss, tick, disclosure |
| `warning`, `error`, `info` | notices and field errors, always with words |
| `type-number`, `type-text`, `type-date`, `type-bool`, `type-other` | the field type on a field row |

Removed: `bookmark` and `bookmarks` (the Bookmarks feature was removed).

## All names

- **Data source:** `connection`, `database`, `table`, `key`, `link`, `swap`, `story`, `dashboard`.
- **Marks slots:** `color`, `size`, `label`, `tooltip`, `detail`, `shape`, `path`, `angle`, `pages`, `filter`, `calendar`.
- **Analytics:** `insights`, `analytics`, `profile` (a histogram: the Data Source field row's Profile button), `ref-line`, `band`, `trend`, `forecast`, `show-me`.
- **Actions:** `undo`, `redo`, `expand`, `collapse`, `print`, `sort`, `sort-asc`, `sort-desc`, `format`, `eye`, `refresh`, `power`, `duplicate`, `grip`, `search`, `stroke-width`, `arrow-left`, `arrow-right`.
- **Chart types:** `chart-bar`, `chart-stacked`, `chart-line`, `chart-area`, `chart-pie`, `chart-donut`, `chart-scatter`, `chart-combo`, `chart-square`, `chart-circle`, `chart-heatmap`, `chart-treemap`, `chart-histogram`, `chart-boxplot`, `chart-waterfall`, `chart-funnel`, `chart-gauge`, `chart-gantt`, `chart-bullet`, `chart-sankey`, `chart-multiples`, `chart-kpi`, `chart-text` (Table reuses `table`).

## Favicon

The tab icon is the sidebar's four-square brand mark in the lime (`#a9c43c`, a mid tone that reads on light and dark tabs), an inline SVG data URI in the
`<link rel="icon">` in `Shell/Index.cshtml`. Inline means no extra request, no static-file mapping (the `/features` provider serves only `.css` / `.js`)
and no path-prefix problem behind Apache; the browser never asks for `/favicon.ico`. An SVG cannot read the CSS tokens, so if `--accent` changes, change the hex there too.

