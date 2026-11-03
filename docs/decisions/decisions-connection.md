---
components: []
---
# Decisions — connection

Continues [decisions-platform.md](decisions-platform.md). Behaviour: [connection.md](../concepts/data-source/connection.md). Edit an entry in place when it changes.

### D70 — Recent connection sources are non-secret and kept in the browser
After a successful connect, the browser remembers host, port, user, Secure and the cert opt-in in
`localStorage` (max 5, one per host/port/user), following the D21 precedent. The password and any token
are never stored. Picking a source refills the form, and the user types the password again (golden rule 4).
- **Why the cert opt-in is remembered:** it is the user's earlier explicit choice for that server, so one
  click restores "Trust invalid certificate". It is not silent: Advanced opens on refill, the form shows
  its warning, and Connect is still a deliberate press with the password typed.
- **Trade-off:** not shared across browsers; cleared with site data. Entries are re-sanitised on load.
- Detail: [connection.md](../concepts/data-source/connection.md#recent-connections).
