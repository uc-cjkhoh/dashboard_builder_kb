# Decisions — connection

Continues [decisions.md](decisions.md). Behaviour: [connection.md](../features/connection.md). Edit an entry in place when it changes.

### D70 — Recent connection sources are non-secret and kept in the browser
After a successful connect the browser remembers host, port, user, Secure and the cert opt-in in
`localStorage` (max 5, one per host/port/user), following the D21 precedent. The password and any token are
never stored; picking a source refills the form and the user types the password again (golden rule 4).
- **Cert opt-in is remembered:** it is the user's earlier explicit choice for that server, so one click
  restores "Trust invalid certificate". It is not silent: Advanced opens on refill and the form shows its
  warning, and Connect is still a deliberate press with the password typed.
- **Trade-off:** not shared across browsers; cleared with site data. Entries are re-sanitised on load.
- Detail: [connection.md](../features/connection.md#recent-connections).
