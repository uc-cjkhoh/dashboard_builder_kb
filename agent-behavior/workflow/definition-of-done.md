# Definition of done

The process checklist to go through before calling a change finished. A change is done only when every
box holds. The code-level gates (safety, frontend) are in
[change-checklist.md](../../project-knowledge/engineering/change-checklist.md).

## Verification

- [ ] `dotnet build` clean and `dotnet test` green from the solution root
      ([development.md](../../project-knowledge/operations/development.md#test)).
- [ ] `node --test tests/js/*.test.mjs` green; new logic lives in a pure module with a test.
- [ ] Changed JS modules pass `node --check`; the page and changed assets serve `200` from a local
      `dotnet run`.

## Knowledge base

- [ ] The doc for the touched area is updated **in the same change**, edited in place
      ([kb-maintenance.md](../kb/kb-maintenance.md)).
- [ ] A changed decision is updated in [decisions.md](../../project-knowledge/reference/decisions/decisions.md).
- [ ] A built backlog item moves from `backlog/<file>` into its `features/` doc
      ([backlog](../../project-knowledge/backlog/README.md)).

## Integration

- [ ] Suites green → merge per [merge-to-main.md](merge-to-main.md).

## Status dashboard

- [ ] Backlog or built-state changed → refresh the dashboard per [status-dashboard.md](status-dashboard.md).
