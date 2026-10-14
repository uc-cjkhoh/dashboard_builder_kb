# Maintaining this knowledge base

This KB follows the organisation-wide standard at
`/unified/user/cj/knowledge/general/knowledge_base_best_practice.md` — that file is the source of
truth; this page records the rules that apply every time you edit these docs. It mirrors the rules of
the sibling MNP Web Portal KB (`../mnp_web_portal/docs/conventions/kb-maintenance.md`). **Keep to them
when adding or changing anything here.**

## Core rules

- **Current state, not history.** Overwrite existing lines; do not append changelog entries
  ("shipped 2026-…", "Correction, same day", "Nth build pass", "was X, now Y", "✅ Shipped"). Keep the
  facts and the *why* behind a decision; drop the journey that got there. The KB represents what the
  system is now, not its commit history.
- **Atomic, MECE chunks.** Break content into small, self-contained sections with precise,
  descriptive titles. Organise into Mutually Exclusive, Collectively Exhaustive categories so no two
  files overlap or contradict. When you find a contradiction, reconcile to the single current truth —
  and when docs and code disagree, the code wins.
- **Explicit, actionable logic.** Prefer clear steps and rules over prose (e.g. a validate-then-quote
  sequence, an invariant), and natural phrasing over internal jargon.

## Size limits & file architecture

- **`CLAUDE.md` / `README.md` — under 200 lines.** They are indexes: setup/run/deploy commands, tech
  stack, directory map, and the golden-rules summary. Detail lives in `docs/`.
- **`ARCHITECTURE.md` — high-level flow only.** No code blocks (an untagged plain-text diagram is
  fine); point to the source and to `docs/` sub-files.
- **The 300-line rule.** If an edit pushes any doc past ~300 lines, extract its most self-contained
  sub-topic into a new file in the same `docs/` subfolder and leave a short markdown link to it.
- **Componentized `docs/`, kebab-case filenames.** Group by concern:
  [conventions/](golden-rules.md), [design/](../design/tokens.md), [features/](../features/worksheet.md)
  (one file per app feature folder), [reference/](../reference/data-model.md),
  [operations/](../operations/deployment.md), [proposals/](../proposals/roadmap.md).
  `archive/` (the frozen P0–P20 build plan) is the exception — a historical artifact, kept as-is and
  not maintained.

## When you make a change

1. Update the doc for the touched area **in the same change** (see
   [definition-of-done.md](definition-of-done.md)).
2. Edit in place — don't add a dated note or a "Built (Pn)" callout at the bottom.
3. If a section outgrew 300 lines, split it and link.
4. If you moved or renamed a file or heading, fix inbound links (file-level and `#anchor`-level).
5. When a roadmap item is built, move its description out of
   [proposals/roadmap.md](../proposals/roadmap.md) into the matching `features/` doc as current
   behaviour.

## Enforcement

`.claude/hooks/kb-verify.py` runs after every Write/Edit of a KB markdown file and reports (to the
agent) line-limit breaches, code blocks in `ARCHITECTURE.md`, non-kebab-case `docs/` filenames,
changelog phrasing, and broken file/anchor links — inbound ones included. `archive/` and
`*.local.md` are exempt. Fix what it reports in the same change.

## Related

- The full standard → `/unified/user/cj/knowledge/general/knowledge_base_best_practice.md`
- [golden-rules.md](golden-rules.md) · [definition-of-done.md](definition-of-done.md) ·
  [../README.md](../README.md)
