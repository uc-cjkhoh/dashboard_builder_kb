# P22 Show Me Implementation Plan — overview

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended)
> or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax
> for tracking.

**Goal:** A Show Me card in the worksheet view bar that greys out chart types the sheet's fields can't
draw (with the reason), outlines the best one, and on a click sets the type and re-arranges Columns /
Rows into that type's layout as one undo step.

**Architecture:** All rules live in a new pure module `Features/Dashboard/show-me-rules.js` (rule table,
validity, recommendation, placement), unit-tested with `node --test`. `dashboards.js` drops its private
`chartIssue` `switch` and imports the module, so the chart hint and Show Me share one table; it adds a
`countsFor` adapter over its existing `planDims`, plus the card (same pattern as the Format / Analytics
cards).

**Tech Stack:** vanilla ES modules, no build step; `node:test` + `node:assert/strict`; CSS custom
properties from `Core/core.css`; inline-SVG icons in `Core/icons.js`. Server untouched.

**Spec:** [../p22-show-me.md](../p22-show-me.md) — read it first; this plan implements it exactly.

## Task files

| Tasks | File | Delivers |
|---|---|---|
| 1 | [plan-rules.md](plan-rules.md) | `show-me-rules.js` rule table + validity; `dashboards.js` uses it for the existing hints |
| 2 | [plan-placement.md](plan-placement.md) | recommendation + placement in the same module, with tests |
| 3 | [plan-card.md](plan-card.md) | the Show Me button + card, icon, CSS |
| 4 | [plan-card.md](plan-card.md#task-4-docs-cleanup-and-deploy) | KB docs, delete spec + plan, deploy |

## File map

| File (under the app root) | Change | Responsibility |
|---|---|---|
| `src/DashboardBuilder/Features/Dashboard/show-me-rules.js` | create | rule table, hint texts, `issueFor`, `bestType`, `showMeOptions`, `placeFor`, `samePlacement`, `roleOf` |
| `tests/js/show-me-rules.test.mjs` | create | rule table (regression vs. the old `switch`), `issueFor` precedence, `roleOf` |
| `tests/js/show-me-placement.test.mjs` | create | `bestType`, `showMeOptions`, `placeFor` invariants, `samePlacement` |
| `src/DashboardBuilder/Features/Dashboard/dashboards.js` | modify | import the rules; `showMeCounts`, `showMeToggle`, `showMePanel`; one-open-card wiring |
| `src/DashboardBuilder/Features/Dashboard/dashboard.css` | modify | `.ws-showme*` grid and tile states |
| `src/DashboardBuilder/Features/Core/icons.js` | modify | `show-me` icon |
| `tests/js/icons.test.mjs` | modify | require `show-me` |

## Global Constraints

- App root: `/unified/user/cj/web_development/prototype/dashboard_builder` (a local git repo, branch
  `main`). Work on a branch: `git checkout -b p22-show-me`. Run every command from the app root.
- JS suite: `~/.nvm/versions/node/v24.20.0/bin/node --test tests/js/*.test.mjs`; one file:
  `… --test tests/js/show-me-rules.test.mjs`. .NET suite: `dotnet test`. Syntax-check each changed
  module: `~/.nvm/versions/node/v24.20.0/bin/node --check <file>`.
- Dev run on a spare port: `cd src/DashboardBuilder && dotnet run --no-launch-profile --urls http://localhost:5180`;
  stop it with `fuser -k 5180/tcp` — **never** `pkill -f DashboardBuilder.dll` (matches the live service).
- No framework, CDN or build step; toggle visibility with `hidden` (never `style.display`); design tokens
  only (no hex); never colour alone (icon + text + colour) — [golden rules](../../conventions/golden-rules.md).
- Hint texts are copied **verbatim** from today's code; unmet mappings are hints, never errors.
- A valid Show Me click: set `s.chartType`, `s.columns`, `s.rows`, then **one** `commit(dash, s)`.
  Nothing outside Columns / Rows changes; no pill is added or dropped.
- Pure modules: header comment saying "pure, DOM-free (unit-tested under tests/js/)", named exports,
  frozen tables / `Set`s.
- Commit after each task with a message ending in the line
  `Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>`.

## Review Focus

1. **The same field on both Columns and Rows** (e.g. `region` as a dimension on Rows and on Columns) —
   placement may put both on one shelf; both must be kept and the chart still draws. Pinned in Task 2
   (`placeFor keeps a field that sits on both shelves`) and checked by hand in Task 3.
2. **Role overrides** — a numeric field turned into a dimension, or a text field used as a `count`
   measure, must be placed by its role, not its type. Pinned in Task 2 (`placement follows the pill's
   role`).
3. **Re-picking the current layout** must not add an empty undo step. Pinned in Task 2 (`samePlacement`)
   and wired in Task 3.
4. **An active drill hierarchy** — its level counts as a dimension for validity, exactly as the chart hint
   counts it, so Show Me never enables a type that then shows a hint. Checked by hand in Task 3 (the
   adapter reuses `planDims`, which already includes the drill level).
5. **Min / max of a text or date field** — only Table, Text and KPI may be enabled and Table recommended.
   Pinned in Task 1 (`issueFor` precedence) and Task 2 (`bestType`).

## Done when

All four tasks are checked; both suites pass; the hand checks in Task 3 pass on the dev port in light and
dark; the user has reviewed the card; the KB reflects the built feature and the spec + this `p22/` folder
are deleted; the live service is redeployed stop → copy → start.
