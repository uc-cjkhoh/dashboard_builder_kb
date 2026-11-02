# Change checklist — safety and frontend

What every code change to the app must satisfy before it counts as done. The process side (verification,
KB upkeep, merge) is in [definition-of-done.md](../../agent-behavior/workflow/definition-of-done.md).

## Safety

- [ ] Read-only invariant intact: no new non-`SELECT`/`SHOW`/`DESCRIBE` statement
      ([rule 1](golden-rules.md#1-the-server-is-read-only-against-clickhouse)).
- [ ] Every interpolated identifier is validated against the catalog and quoted via `Identifier.cs`
      ([rule 2](golden-rules.md#2-never-interpolate-an-identifier-you-havent-validated)).
- [ ] Every value is bound and typed to its column, and every result is `LIMIT`-bounded. Out-of-range
      input is rejected (400 `{ error, field? }`), never clamped or dropped
      ([rule 3](golden-rules.md#3-bind-every-value-bound-every-result)).
- [ ] No credential in a response, log line, error message or URL
      ([rule 4](golden-rules.md#4-credentials-live-in-the-session-and-nowhere-else)).
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
