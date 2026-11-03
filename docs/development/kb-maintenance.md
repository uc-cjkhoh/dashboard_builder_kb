---
components: []
---
# Maintaining this knowledge base

The rules that apply every time you edit these docs. Read this before adding or changing anything here.

The structure follows the organisation-wide standard `/unified/user/cj/knowledge/general/knowledge_base_structure.md`,
which is the source of truth. The sibling MNP Web Portal KB uses the same rules
(`../mnp_web_portal/docs/conventions/kb-maintenance.md`).

## Core rules

- **Current state, not history.** Overwrite existing lines. Do not append changelog entries
  ("shipped 2026-…", "Correction, same day", "Nth build pass", "was X, now Y", "✅ Shipped"). Keep the
  facts and the *why* behind a decision; drop the journey. History lives only in the generated
  [update logs](../../CHANGELOG.md).
- **Atomic, MECE chunks.** Small, self-contained sections with precise titles. No two files overlap or
  contradict; each markdown file is the single source of truth for its topic. When you find a
  contradiction, reconcile to the single current truth — when docs and code disagree, the code wins.
- **Explicit, actionable logic.** Dense bulleted specifications and numbered steps, natural wording over
  internal jargon, no filler or preamble.
- **Same-change rule** ([golden rule 11](coding-standards.md#11-update-the-kb-after-every-prompt)). Update the doc for what you touched in the same turn and the same commit, before reporting the work done. When moving a heading or
  file, fix inbound links (file and `#anchor`).

## Layout

The KB is the root `README.md`, `CLAUDE.md`, `CHANGELOG.md` and the `docs/` tree. The folder tree is kept
in one place only: the [KB directory map in CLAUDE.md](../../CLAUDE.md#kb-directory-map). Update it when
you add, move or remove a folder.

| Folder | Put here |
|---|---|
| `getting-started/` | installation, setup, first run |
| `architecture/` | shape, data flow, components, module maps |
| `concepts/` | domain knowledge and feature behaviour: what it does and why |
| `how-to/` | task-oriented steps |
| `reference/` | APIs, SQL, state shapes, configuration, glossary, design system |
| `decisions/` | decision records, one topic per file, `README.md` holds the lookup |
| `operations/` | running the live service, safe operation, credentials |
| `development/` | engineering standards, review gates, git workflow, KB upkeep, backlog, run logs, generated change logs |
| `archive/` | frozen history, not maintained (exempt from the checks) |

A topic lives in exactly one folder. Never scaffold app code into the KB.

## Size and file rules

- **Every doc is under 300 lines; indexes (`CLAUDE.md`, `README.md`, `index.md`) under 200.** When an edit
  pushes a doc past the limit, extract its most self-contained sub-topic into a new file in the same folder
  and link it.
- **`architecture/overview.md` is high level only.** No code blocks (an untagged plain-text diagram is fine).
- **kebab-case filenames** under `docs/`.
- **An `index.md` in every folder with more than one doc**, so an agent loads the index, not every file.
  `docs/decisions/` and `docs/` use `README.md`.
- **Front-matter on every doc under `docs/`**, declaring the code it describes, so an agent modifying a
  module reads only the docs tied to it:

  ```yaml
  ---
  components: [src/DashboardBuilder/Features/Canvas/canvas.js, src/DashboardBuilder/ClickHouse/Identifier.cs]
  ---
  ```

  Paths are relative to the app's solution root; an empty list (`components: []`) means no single module.

## When you make a change

1. Update the doc for the touched area **in the same change** (see
   [review-guidelines.md](review-guidelines.md)).
2. Edit in place — no dated note and no "Built (Pn)" callout at the bottom.
3. If you add or move a source file a doc describes, update that doc's `components:` list.
4. If a section outgrew the limit, split it and link.
5. If you moved or renamed a file or heading, fix inbound links.
6. When a backlog item is built, move its description out of `backlog/<file>` into the matching
   `concepts/` doc as current behaviour and delete the entry (and any spec or plan file) from the
   [backlog](backlog/index.md): the backlog is the only to-do list.

## Enforcement

Hooks check every KB edit and generate the update logs: [hooks.md](hooks.md). Fix what `kb-verify.py`
reports in the same change. Check everything by hand with `python3 .claude/hooks/kb-verify.py --all`.

## Related

- [coding-standards.md](coding-standards.md) · [review-guidelines.md](review-guidelines.md) · [docs index](../README.md)
