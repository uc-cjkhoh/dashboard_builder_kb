---
components: [src/DashboardBuilder/ClickHouse/Identifier.cs, src/DashboardBuilder/Features/Core/icons.js, src/DashboardBuilder/Features/Core/validate.js, tests/js/calc-limits.test.mjs, tests/js/card-width.test.mjs, tests/js/dashboard-select.test.mjs, tests/js/result-model.test.mjs, tests/js/store-tabs.test.mjs, tests/js/worksheet-view.test.mjs]
---
# Review guidelines

What every change must satisfy before it counts as done and merges: verification, safety, frontend, knowledge base, integration. A change is done only when every box holds.

## Verification

- [ ] `dotnet build` clean and `dotnet test` green from the solution root
      ([testing.md](../how-to/testing.md#test)).
- [ ] `node --test tests/js/*.test.mjs` green; new logic lives in a pure module with a test.
- [ ] Changed JS modules pass `node --check`; the page and changed assets serve `200` from a local
      `dotnet run`.

## Safety

- [ ] Read-only invariant intact: no new non-`SELECT`/`SHOW`/`DESCRIBE` statement
      ([rule 1](coding-standards.md#1-the-server-is-read-only-against-clickhouse)).
- [ ] Every interpolated identifier is validated against the catalog and quoted via `Identifier.cs`
      ([rule 2](coding-standards.md#2-never-interpolate-an-identifier-you-havent-validated)).
- [ ] Every value is bound and typed to its column, and every result is `LIMIT`-bounded. Out-of-range
      input is rejected (400 `{ error, field? }`), never clamped or dropped
      ([rule 3](coding-standards.md#3-bind-every-value-bound-every-result)).
- [ ] No credential in a response, log line, error message or URL
      ([rule 4](coding-standards.md#4-credentials-live-in-the-session-and-nowhere-else)).
- [ ] State-changing calls are `POST` with a JSON body, because of the proxy
      ([sharp edges](sharp-edges.md#hosting--deploy)).

## Frontend

- [ ] Visibility is toggled with `hidden`.
- [ ] Colours come from tokens, with red only for danger.
- [ ] Icons come from `Core/icons.js`.
- [ ] The shell doesn't scroll, and the change looks right in light and dark.
- [ ] Every new input is validated on the client (`Core/validate.js` + `ui.fieldError`) **and** the server
      (`RequestRules`), with the same message and limit.
- [ ] Status is icon + text + colour; new controls sit on `--ctl-h`.
- [ ] Unmet chart mappings show a **hint**, never an error.

## Knowledge base

- [ ] The doc for the touched area is updated **in the same change**, edited in place
      ([kb-maintenance.md](kb-maintenance.md)).
- [ ] A changed decision is updated in [decisions-platform.md](../decisions/decisions-platform.md).
- [ ] A built backlog item moves from `backlog/<file>` into its `features/` doc
      ([backlog](backlog/index.md)).

## Integration

- [ ] Suites green → merge per [git-workflow.md](git-workflow.md).
