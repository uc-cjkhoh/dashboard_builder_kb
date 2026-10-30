# Motion & accessibility

## Motion

Interaction is calm: short, purposeful transitions, nothing decorative. The style follows Fluent
(WinUI 83/167/250ms steps; "fast out, slow in" for things arriving): **entrances decelerate, exits
accelerate and run quicker**, durations stay within 100–300ms (past ~400ms feels slow), and **only
`opacity` / `transform` animate** (compositor-only — no width/height/top/left). Motion marks what
changed; it never replays on routine re-renders.

Tokens: `--dur-exit` 100ms, `--dur-fast` 150ms, `--dur` 200ms, `--dur-slow` 250ms; `--ease`
`cubic-bezier(.33,0,.67,1)` (standard), `--ease-out` `cubic-bezier(.1,.9,.2,1)` (entrances), `--ease-in`
`cubic-bezier(.5,0,.75,0)` (exits). JS-driven motion goes through `Core/motion.js` (`enter` / `exit`,
same values) for what CSS can't do: animating into `hidden`, or only the *first* appearance of
something re-rendered on every edit.

| Where | Motion |
|---|---|
| Switching tabs | the incoming view fades in and rises 4px (`--dur`); also between two dashboards |
| Menus | open: scale 97%→100% + fade from the button's corner (`--dur-fast`); close: fade out (`--dur-exit`) |
| Tool panel, Format card | slide down 4px + fade, only when opened |
| Pills | a newly added pill rises in; existing pills and dashboard switches don't animate |
| Chart | fresh data from ClickHouse: ECharts entrance 300ms `cubicOut` (not its 1s default); a re-render from the cache (format tweaks, theme flip) has no animation. Table/KPI fade in |
| Loading / notice | "Loading…" fades in after 150ms (no flash on fast queries); the result notice fades in |
| Disconnect | cards and dashboard tabs fade out (`--dur-exit`) before the workspace clears |
| Entity cards | rise in on drop; collapse by animating `max-height`; no hover lift |
| Toasts / dialogs | toasts slide up from the bottom centre; dialogs scale in over a dimming scrim |
| Status | the loading pill glyph spins |
| Controls | colour / border transitions on hover (`--dur-fast`); a picker's caret flips while its menu is open |
| Pages shelf | autoplay steps every 1.5s |

**All of it is gated by `prefers-reduced-motion: reduce`** — the CSS media query zeroes every duration,
and `Core/motion.js` and the chart's motion option skip their animations. Under
reduced motion the Pages **Play** control is omitted (stepping still works). Motion is an enhancement,
never required to understand state.

## Accessibility posture

- **Never colour alone** ([golden rule 9](../conventions/golden-rules.md#9-never-colour-alone)): status
  carries an icon + label + colour; ≥2 chart series get a legend; cardinality is shape-coded (tick vs.
  crow's foot); Shape encodings give a second, non-colour channel; an invalid pill has a dashed border
  **and** a warning icon and tooltip.
- **Forms:** an invalid field gets `aria-invalid="true"`, an inline message (`.field-error`: warning
  icon + text) linked by `aria-describedby`, cleared on the next edit; applying is blocked and focus
  moves to the first invalid field (`ui.fieldError`).
- **ARIA:** `aria-current` on the active tab; `aria-label`s on every icon-only button (remove entity,
  close tab, disconnect, view-bar tools); menus are `aria-haspopup="menu"` + `aria-expanded` with
  `role="menuitem"` items (`menuitemradio` + `aria-checked` for the chart-type and sort pickers); resize
  handles are `role="separator"` with `aria-valuenow/min/max`; `aria-pressed` on toggle buttons; accessible names on the aggregation and
  filter-operator selects, and on each picker button ("Chart type: Bar", "Sort: customers.name, ascending").
- **Live regions:** one persistent visually-hidden `#toast-live` announces every toast (a `hidden`
  container is never announced); connection and save failures arrive as toasts. Danger
  toasts stay until dismissed; others close after 5 s.
- **Keyboard / non-drag paths:** a `＋` on each table chip adds it to the canvas; relationships are
  created by dragging a column onto another (no keyboard path yet); a `＋` on each field adds it to a shelf; `F2` / `Enter` renames a
  tab; `←`/`→` on a focused resize handle resizes the sidebar or field pane; menus open on click and move with `ArrowUp` / `ArrowDown`, `Esc` closes and returns focus;
  `Esc` clears the table search.
- **Contrast** is ≥ 4.5:1 for every ink/background pair in both themes (ratios in [tokens.md](tokens.md)).
- **Native `<dialog>`** for focus trapping and `Esc`-to-close.
