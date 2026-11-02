# Hooks

What the three KB hooks check or generate, and how to run them by hand. The hooks are wired in
`.claude/settings.json`; the scripts live in `.claude/hooks/`.

| Hook | Fires | Does |
|---|---|---|
| `kb-verify.py` | after Write/Edit of a KB markdown file | Reports line-limit breaches, code blocks in `ARCHITECTURE.md`, non-kebab-case filenames, changelog phrasing, and broken file/anchor links (inbound too) back to the agent. Rules: [kb-maintenance.md](kb-maintenance.md). |
| `update-log.py` | after a Bash call that runs `git merge` or `git commit` | Rebuilds [ui_updates.md](../../project-knowledge/updates/ui_updates.md) and [feature_updates.md](../../project-knowledge/updates/feature_updates.md) from the app repo's `main` history. |
| `reap-chrome.sh` | after Bash, and on Stop | Kills orphaned headless-Chrome processes and removes their `calc-ui-*` profile dirs. |

## By hand

- Check the whole KB: `python3 .claude/hooks/kb-verify.py --all` (exit 1 if any finding).
- Rebuild the update logs: `python3 .claude/hooks/update-log.py --rebuild`.

## Exemptions

`kb-verify.py` skips `project-knowledge/archive/`, `project-knowledge/updates/`, `agent-behavior/run-logs/`
and `*.local.md`. These are either history by design or git-ignored.

The update logs are generated, never hand-edited:

- One section per commit date, newest first.
- Each commit lands in exactly one file. UI covers styles, markup and visual wording; feature covers
  server, models and behaviour.
- Test-only and docs-only commits are skipped.
- Commits from the same date that open with the same four words collapse to one bullet.
