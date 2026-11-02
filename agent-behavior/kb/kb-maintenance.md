# Maintaining this knowledge base

The rules that apply every time you edit these docs. Read this before adding or changing anything here.

This KB follows the organisation-wide standard at
`/unified/user/cj/knowledge/general/knowledge_base_best_practice.md`, which is the source of truth.
The rules here mirror those of the sibling MNP Web Portal KB
(`../mnp_web_portal/docs/conventions/kb-maintenance.md`). **Keep to them when adding or changing
anything here.**

## Core rules

- **Current state, not history.** Overwrite existing lines. Do not append changelog entries
  ("shipped 2026-…", "Correction, same day", "Nth build pass", "was X, now Y", "✅ Shipped"). Keep the
  facts and the *why* behind a decision, and drop the journey that got there. The KB represents what
  the system is now, not its commit history.
- **Atomic, MECE chunks.** Break content into small, self-contained sections with precise,
  descriptive titles. Organise into Mutually Exclusive, Collectively Exhaustive categories so no two
  files overlap or contradict. When you find a contradiction, reconcile to the single current truth —
  and when docs and code disagree, the code wins.
- **Explicit, actionable logic.** Prefer clear steps and rules over prose (e.g. a validate-then-quote
  sequence, an invariant), and natural phrasing over internal jargon.

## Size limits & file architecture

- **`CLAUDE.md` / `README.md` — under 200 lines.** They are indexes: setup/run/deploy commands, tech
  stack, directory map, and the golden-rules summary. Detail lives in the topic files.
- **`ARCHITECTURE.md` — high-level flow only.** No code blocks (an untagged plain-text diagram is
  fine); point to the source and to topic files.
- **The 350-line rule.** If an edit pushes any doc past ~350 lines, extract its most self-contained
  sub-topic into a new file in the same subfolder and leave a short markdown link to it.
- **Two top-level folders, kebab-case filenames.** `agent-behavior/` holds how agents work on this
  project; `project-knowledge/` holds what the project is. A topic lives in exactly one of them, in a
  subfolder per concern:
  - [agent-behavior/](../README.md): `workflow/`, `kb/`, `operations/`, `run-logs/`.
  - [project-knowledge/](../../project-knowledge/index.md): `engineering/`, `design/`, `features/`,
    `reference/`, `operations/`, `backlog/`, `updates/`, `archive/`. Feature docs group into
    `data-source/`, `worksheet/` and `workbook/`; decisions live in `reference/decisions/`.
  - `archive/` is the exception. It holds the frozen build plan for phases P0–P20 (the original
    build phases), a historical artifact kept as-is and not maintained.

## When you make a change

1. Update the doc for the touched area **in the same change** (see
   [definition-of-done.md](../workflow/definition-of-done.md)).
2. Edit in place — don't add a dated note or a "Built (Pn)" callout at the bottom.
3. If a section outgrew 350 lines, split it and link.
4. If you moved or renamed a file or heading, fix inbound links (file-level and `#anchor`-level).
5. When a backlog item is built, move its description out of `backlog/<file>` into the matching
   `features/` doc as current behaviour, and delete the entry (and any spec or plan file) from
   [backlog/](../../project-knowledge/backlog/README.md): the backlog is the only to-do list.

## Enforcement

Hooks check every KB edit and generate the update logs: [hooks.md](hooks.md). Fix what `kb-verify.py`
reports in the same change.

## Related

- The full standard → `/unified/user/cj/knowledge/general/knowledge_base_best_practice.md`
- [golden-rules.md](../../project-knowledge/engineering/golden-rules.md) · [definition-of-done.md](../workflow/definition-of-done.md) ·
  [project-knowledge index](../../project-knowledge/index.md)
