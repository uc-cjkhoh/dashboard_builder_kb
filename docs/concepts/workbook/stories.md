---
components: [src/DashboardBuilder/Features/Core/store.js, src/DashboardBuilder/Features/Dashboard/dashboard.css, src/DashboardBuilder/Features/Story/]
---
# Stories — ordered, captioned steps

A **story** tab walks a reader through worksheets and dashboards, one captioned step at a time.
It is a third tab kind beside worksheets and dashboards ([tabs.md](tabs.md)); it adds no server endpoint.

- Why steps point at tabs and not at copies: [D81](../../decisions/decisions-dashboards.md#d81--a-story-is-a-tab-of-captioned-steps-that-point-at-worksheets-and-dashboards).

**Code:** `Features/Story/` — `story-model.js` (pure, node-tested), `story.js`, `story.css`, `_Story.cshtml`.
`Core/store.js` holds the data (`createStory`, `setSteps`, `stories()`, `activeStory()`).

## The tab

`[+]` → **New story** makes "Story N" (icon `story`, accessible name "Story 1 (story)"). It counts toward the 50-tab limit.
Its view is `#story-view`, shown only while a story is active.

| Part | What it does |
|---|---|
| Bar | the story's name, "N of 20 steps", a polite status line, **Print step** |
| Add row | **Step shows** (a select of every worksheet and dashboard), a caption field (≤ 300), **Add step**. The new step is appended and becomes current. A refusal (caption too long, 20 steps already, no tab chosen) is written under the row and nothing is added. |
| Step strip | one button per step: number, caption start (else the tab's name), and an icon for the kind. The current step is filled and bold, and has `aria-selected`; the strip is a `tablist`. |
| Current step | "Step N of M · <tab name>", the caption (plain text), and the step's tools |
| Stage | a **worksheet** step draws that worksheet as a static view (no selection or drill) through the shared result cache; a **dashboard** step shows a card with **Open dashboard** |
| Previous / Next | one step each; disabled at the ends (no wrap); "N / M" between them |

## Step tools

Each is a labelled icon button ("Edit the caption of step 2", "Move step 2 earlier", "Move step 2 later", "Remove step 2"),
plus **Open tab** (goes to the step's worksheet or dashboard, where the usual export and CSV live).

- **Edit caption** opens a labelled textarea with a count (the length is measured after trimming, on save and on import). Save (or Ctrl+Enter) stores it. An over-long caption is refused with an alert and
  `aria-invalid`, never cut. Esc or Cancel keeps the old caption and returns focus to Edit.
- **Move earlier / later** swaps with the neighbour and keeps the moved step current; focus stays on the same tool. Disabled at the ends.
- **Remove** drops the step; the step after it (else the one before) becomes current and focus goes to the strip, or to the Add row when none are left.

## Keyboard

Tab reaches the strip once (roving `tabindex`). Left / Right move to the previous / next step, Home / End to the first / last,
and focus follows the selection. Arrows never wrap. Focus stays on a live control after Previous / Next (the other button when the end is reached), after a strip click, and after a move (the same tool, or the other direction when that end is reached). Every control has an accessible name, and each move is announced in the status line ("Step 2 of 3.").

## Print

**Print step** prints the current step only: the story's name, the step line, the caption and the chart at page width (the
worksheet print rules of `dashboard.css` size the chart). The chart is drawn at 1000 × 560 for the page, as the worksheet print does, and restored afterwards. Strip, controls and sidebar are hidden. A dashboard step prints its card.

## Lifecycle

- **The step on screen** is transient (per story, in memory); steps are saved.
- Only the active story renders; leaving it destroys the worksheet view (queries aborted). A worksheet edit, a theme or light / dark flip,
  or a parameter change re-runs the stage from the cache when it shows that worksheet.
- **Closing a worksheet or dashboard removes every step that showed it** (each story notified with `story:changed`). The close confirm names the stories ("Its steps will be removed from the story: Tour."), also for a worksheet that is on no dashboard. Closing a story touches nothing else; a story with steps confirms first.
- **No undo** for story edits (add, remove, move, caption) — unlike dashboards, there is no history.
- **Reconnect:** a stage that showed a hint while its tables' columns were loading runs again once they arrive (`entity:loaded`).
- An open caption editor keeps what was typed through other redraws (rename, tab changes).
- A navigation button on a dashboard never offers a story as its target.

## Limits

`LIMITS.storySteps` **20** per story, `LIMITS.stepCaption` **300** characters. Client-side only; out-of-range input is rejected, never clamped.
Save and open: [data-model.md](../../reference/data-model.md#workbook-file) and [workbook.md](workbook.md#validation-parseworkbook).

## Not built

A dashboard drawn inside the stage, step-level filters and
selections, and a presentation mode — see the [backlog](../../development/backlog/dashboards.md).
