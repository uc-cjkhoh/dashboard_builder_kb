# Definition of done

A change is done only when every box holds.

## Safety

- [ ] Read-only invariant intact — no new non-`SELECT`/`SHOW`/`DESCRIBE` statement
      ([rule 1](golden-rules.md#1-the-server-is-read-only-against-clickhouse)).
- [ ] Every interpolated identifier catalog-validated + quoted via `Identifier.cs`
      ([rule 2](golden-rules.md#2-never-interpolate-an-identifier-you-havent-validated)).
- [ ] Every value bound and typed to its column; every result `LIMIT`-bounded; out-of-range input is
      rejected (400 `{ error, field? }`), never clamped or dropped
      ([rule 3](golden-rules.md#3-bind-every-value-bound-every-result)).
- [ ] No credential in a response, log line, error message or URL
      ([rule 4](golden-rules.md#4-credentials-live-in-the-session-and-nowhere-else)).
- [ ] State-changing calls are `POST` + JSON body (proxy rule — [sharp edges](sharp-edges.md#hosting--deploy)).

## Frontend

- [ ] Visibility via `hidden`; colours via tokens (red only for danger); icons from `Core/icons.js`; the
      shell doesn't scroll; looks right in light and dark.
- [ ] Every new input is validated on the client (`Core/validate.js` + `ui.fieldError`) **and** the server
      (`RequestRules`), with the same message and limit.
- [ ] Status is icon + text + colour; new controls sit on `--ctl-h`.
- [ ] Unmet chart mappings show a **hint**, never an error.

## Verification

- [ ] `dotnet build` clean and `dotnet test` green from the solution root
      ([development.md](../operations/development.md#test)).
- [ ] `node --test tests/js/*.test.mjs` green; new logic lives in a pure module with a test.
- [ ] Changed JS modules pass `node --check`; the page and changed assets serve `200` from a local
      `dotnet run`.

## Knowledge base

- [ ] The doc for the touched area is updated **in the same change**, edited in place
      ([kb-maintenance.md](kb-maintenance.md)).
- [ ] A changed decision is updated in [decisions.md](../reference/decisions.md); a built roadmap item
      moves from [delivery-and-risks.md](../proposals/delivery-and-risks.md) into its `features/` doc.

## Integration

- [ ] **Always merge to `main` after tests pass or an error is fixed.** Once the suites above are green
      (or a failing test or error has been fixed and they are green again), merge the work branch into
      `main` locally — no waiting for a separate go-ahead — then run the suites again on the merged result.
