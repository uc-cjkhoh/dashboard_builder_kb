# Agent behavior

How an agent (or human) works on the Dashboard Builder: process, upkeep, safe operation. What the
project *is* lives in [../project-knowledge/](../project-knowledge/index.md).

| Topic | Doc | Holds |
|---|---|---|
| Workflow | [workflow/definition-of-done.md](workflow/definition-of-done.md) | The process gates: verification, KB upkeep, integration, dashboard |
| Workflow | [workflow/merge-to-main.md](workflow/merge-to-main.md) | The standing merge grant for the app repo, and when to stop and ask |
| Workflow | [workflow/status-dashboard.md](workflow/status-dashboard.md) | When and how to refresh the backlog status dashboard |
| KB upkeep | [kb/kb-maintenance.md](kb/kb-maintenance.md) | Current state not history, MECE, size limits, layout |
| KB upkeep | [kb/hooks.md](kb/hooks.md) | The three hooks: KB verify, update logs, Chrome reaper |
| Safe operation | [operations/safe-operations.md](operations/safe-operations.md) | Never-do list for the build host, live service and credentials |
| Run logs | [run-logs/blocked.md](run-logs/blocked.md) | Work that could not be built, and why |

Code-level gates (safety, frontend) that every change must meet are project knowledge:
[change-checklist.md](../project-knowledge/engineering/change-checklist.md).
