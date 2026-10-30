# Components — CSS class vocabulary

The builder's surfaces and the classes that style them. Shared components live in
`Features/Core/core.css`; feature-specific ones in `Features/<Feature>/<feature>.css`. There are no
report lists or record-CRUD tables here — this is an explorer, not an admin template.

## Shared (`Core/core.css`)

| Pattern | Key classes |
|---|---|
| Buttons | `.btn`, `.btn--primary`, `.btn--danger` |
| Icon actions | `.iconbtn`, `.iconbtn--danger` (remove entity, close tab, disconnect) |
| Icons | `Core/icons.js` `icon(name, {size, label})` → inline `<svg class="icon">`; static markup uses `<span data-icon="name">`, hydrated once by `Shell/app.js` |
| Menu | `.menu`, `.menu__list` (solid `--surface`, never glass; `--start` anchors left), `.menu__item` (`[aria-checked]` radio items with `.menu__check`), `.menu__label`, `.menu__heading`, `.menu__sep` — wired by `Core/menu.js` |
| Glass | `.glass` (tint + `--glass-blur` + 1px stroke + top rim) — only on chrome over the wash: sidebar, `.canvas__bar`; `.ws-shelves` uses the same tokens |
| Inline field error | `.field-error`, `.field-error__icon` (via `ui.fieldError`) |
| Status pill | `.pill`, `.pill--warn` (loading), `.pill--danger` (failed) — the schema browser's table-load status |
| Card / panel | `.card`, `.card--fill`, `.card__head`, `.card__body.flush`, `.card__foot` |
| Dialog | `.dialog`, `.dialog--sm`, `.dialog__head/body/foot`, `.form-grid`, `.form-field` |
| Cardinality picker | `.card-choice` |
| Select | `.select`, `.select--light`; in the sidebar (`.sidebar .select`) it matches the text inputs — control height, edge, radius, padding, focus underline — with a token-coloured gradient chevron instead of the UA arrow; `.select option` takes `--surface`/`--ink` so the open list follows the theme |
| Data grid | `.data`, `.num` (right-aligned numerics), `.mono`, `.cell-strong`, `.cell-sub` |
| Empty state | `.empty` |
| Toast | `.toast` (`.toast--ok` / `--info` / `--danger`, a coloured left rule), `.toast__text`, `.toast__close`; announced through `#toast-live` |
| Issue list | `.dialog__list` (`ui.listDialog`) |
| Bookmarks dialog | `.bookmark-list`, `.bookmark` (`__info`, `__name`, `__meta`), `.bookmark-note` |
| Theme dialog | `.theme-dialog` (`__body`), `.theme-group` (`__title`), `.theme-options`, `.theme-option` (`--custom`, `__label`), `.theme-swatches`, `.theme-swatch`, `.theme-picker`, `.theme-hex`, `.theme-error` |

## Per feature

| Feature | Key classes |
|---|---|
| Shell | `.sidebar`, `.sidebar__section`, `.sidebar__title`, `.sidebar__resizer` (+ shared `.resizer`) |
| Connection | `.conn-form`, `.conn-advanced` (collapsed `<details>`), `.form-field`, `.form-check`, `.form-warn` (cert warning), `.conn-summary` |
| Schema | `.table-search`, `.table-list`, `.table-list__empty`, `.table-chip` (`draggable="true"`; `--dragging`), `.table-chip__grip`, `.table-chip__icon`, `.table-chip__name` |
| Canvas | `.canvas`, `.canvas__bar` (glass tab bar), `.canvas__empty` (`.empty__model` ghost model: `.empty__card`, `.empty__row`, `.empty__link`, `.empty__end`), `.entity`, `.entity__head`, `.entity__title`, `.entity__toggle`, `.entity__status`, `.entity__cols`, `.entity--collapsed`, `.entity--dragging`, `.col-row`, `.col-row__key`, `.col-row__type` |
| Relations | `.rel-svg` (`--labels`), `.rel-link` (`--selected`, `--hover`, `--label`), `.rel-link__line`, `.rel-link__hit`, `.col-row--linked`, `.rel-end`, `.rel-badge`, `.rel-connector` |
| Tabs | `.tabs`, `.tab`, `.tab--model`, `.tab.is-active`, `.tab__label`, `.tab__rename`, `.tab__close`, `.tab-add` (a `.menu`: `.tab-menu`, `.tab-menu__list`), `.tab--worksheet`, `.tab--dashboard`, `.tab__kind`, `.view--model`, `.view--worksheet`, `.view--board` |
| Workbook | `.workbook` (right end of `.canvas__bar`), `.workbook__status` (quiet autosave text), the Workbook `.menu` |
| Worksheet | see below |

## Worksheet (`Dashboard/dashboard.css`)

| Part | Key classes |
|---|---|
| Frame | `.ws-fieldtools` (`__search`, `__hidden`), `.ws-field__rename`; `.ws-group` (`__head`, `__name`; the shared collapsible group), `.ws-fields-collapse`, `.ctx-menu` (the context popup; `__custom` rows), `.ws-field.is-renamed` / `.is-hidden`; `.worksheet` (`--ws-fields-w`; `.is-fields-open` on phones), `.ws-fields-toggle`, `.ws-print-head` (`__title`, `__line`), `.ws-chart-card.is-presenting`, `.ws-fields`, `.ws-fields__resizer`, `.ws-fieldset` (collapsible `<details>` per table), `.ws-field`, `.ws-chart-card` (solid card: `.ws-chart-head` view bar, notice, `.ws-chart` pane; `.is-fresh` fades a new result in), `.ws-chart-notice` (result notice at the card's top — info icon + muted `--fs-xs` text), `.ws-note` (inline editor note) |
| View bar | `.ws-undo` (undo / redo), `.ws-actions` (⋯ sheet actions), `.ws-titleblock` (`__btn`, `__title`, `__caption`, `__input`; `.is-auto`), `.ws-statusbar`; `.ws-viewbar`, `.ws-viewbar__group--right`, `.ws-viewbar__icons` (Format / Export / Refresh icon buttons), `.ws-pick` (`--chart` / `--sort`; `__btn`, `__text`, `__caret`) — pickers open a `.menu__list` of `menuitemradio`s; `.ws-charttypes` (two-column type grid), `.ws-format`, `.ws-export` |
| Shelves | `.ws-shelf` (`--columns` / `--rows` / `--marks`), `.ws-shelf__label`, `.ws-shelf__zone`, `.ws-shelf__note` |
| Pills | `.ws-calc` (table-calculation editor), `.ws-pill--shared`, `.ws-pill__badge`; `.ws-choices` (the Choices editor), `.ws-switchers` (chart-card switchers); `.ws-pill`, `.ws-pill--dimension` (blue `--dim-*`), `.ws-pill--measure` (teal `--meas-*`), `.ws-pill--color` / `.ws-pill--mark` (violet `--enc-*`), `.ws-pill--invalid` (dashed `--danger-line` + warning icon), `.ws-pill--drill`, `.ws-pill__grip`, `.ws-pill.is-dragging`, `.is-drop-target`, `.ws-pill__in`, `.ws-pill__range` |
| Marks slots | `.ws-marks__grid` / `__row` / `__gap` (three columns, in the field pane), `.ws-tool` (`.is-quiet`; (`__icon` / `__text` / `__badge`; `.is-set` / `.is-active` / `.is-over`), `.ws-toolpanel` (`__head` / `__title` / `__zone`), `.ws-period` (`__row`; the Date range editor), `.ws-shelf__note--warn` |
| Parameters | controls `.ws-params`, `.ws-param` (`__name`, `__range`, `__num`); bound filter `.ws-pill__param` (`aria-pressed`), `.ws-pill__paramsel`, `.ws-pill__pwrap`; dialog `.params-dialog`, `.params-edit`, `.params-form`, `.params-field`, `.params-actions` |
| Filter cards | `.ws-filtercards`, `.ws-fcard` (`__head`, `__name`, `__body`, `__op`, `__list`, `__item`; `.is-invalid`); top-N editor `.ws-pill__top` (`__topn`, `__topby`, `__topdir`), `.ws-pill__rel` |
| Interaction chips | selection `.ws-select` (`.ws-select__btn`, `.ws-select__link` — the link action); link editor `.ws-link` (`__tpl`); drill breadcrumb `.ws-drill` (`__crumb`, `.is-current`, `__up`, `__level`); pages `.ws-pages` (`__btn`, `__member`) |
| Output | `.widget`, `.widget__head`, `.widget__body` (`--loading` / `--error`), `.widget__chart`, `.widget__grid`, `.widget__kpi` (`-num` / `-sub`), `.ws-kpi-row`, `.ws-spark`, scorecard `.ws-kpi__change` (`--good` / `--bad` / `--neutral`, `__arrow`), `.ws-kpi__target` (`-fill`, `.is-met`) |
| Crosstab | totals `.xt-total` (`.xt-grand`, `.xt-subtotal`); Analytics card `.ws-analytics`; `.xtab`, `.xt-wrap`, `.xt-corner`, `.xt-colhdr`, `.xt-rowhdr`, `.xt-meas`; conditional formatting `.xt-cf` (`__num`, `__icon`), `.xt-bar` (`--neg`), `.xt-rule--good` / `--bad` / `--warn` / `--info`, key `.xt-legend` (`__item`, `__rule`, `__name`, `__scale`, `__note`); editor `.ws-cf` (`__title`, `__row`, `__rule`, `__num`, `__add`) |

## Drag surfaces are not click targets

A `.table-chip` exists to be **dragged** onto the canvas (its `＋` button is the non-drag fallback);
it is not a link. An `.entity` is **moved by dragging its head**; its rows expose explicit affordances
only — a join-key checkbox per column and a remove icon on the card. The card body performs no hidden
action, so nothing about it should promise one. Grid rows get a plain hover; they are not clickable.
