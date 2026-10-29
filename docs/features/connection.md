# Connection panel

Sidebar top. Adds the session's ClickHouse connection and gates the rest of the UI until it exists.
Code: `Features/Connection/` (`ConnectionController.cs`, `_Connection.cshtml`, `connection.js`,
`connection-rules.js`, `connection.css`) + `ClickHouse/ConnectionRegistry.cs`.

## The form

| Field | Default | Notes |
|---|---|---|
| Host | — | required, ≤ 253; a host name, IPv4 or (bracketed) IPv6 — no scheme, port or path |
| Port | `8443` | required whole number 1–65535 (blank is rejected, not defaulted); the HTTPS interface — the target server is TLS-only ([D10](../reference/decisions.md#d10--connect-over-tls-only-https-port-8443)) |
| User | `default` | required, ≤ 64; on the known target, `default` is localhost-only — use a network-enabled account ([sharp edges](../conventions/sharp-edges.md#clickhouse)) |
| Password | — | ≤ 256; sent once to the server session; never echoed back |

**Advanced** (a collapsed `<details>`, `#conn-advanced`) holds the rest:

| Field | Default | Notes |
|---|---|---|
| Secure (TLS) | on | |
| Trust invalid / self-signed certificate | off | shown only while Secure is on; a warning (`.form-warn`) shows while ticked ([D11](../reference/decisions.md#d11--tls-certificate-validation-safe-by-default-explicit-per-connection-opt-in)) |

The section opens by itself when TLS is off or the certificate opt-in is on
(`advancedShouldOpen` in `connection-rules.js`).

Inputs are read by element id (`conn-host`, `conn-port`, `conn-user`, `conn-password`, `conn-secure`,
`conn-allowcert`), not `form.host` named access.

## Recent connections

After each successful connect the source (host, port, user, Secure, cert opt-in) is remembered in this
browser (`localStorage` key `dashboardbuilder.recent-sources`, most recent first, max 5, one per
host/port/user). **The password is never stored** (golden rule 4) — `recent-sources.js` copies only
those fields and `sanitize` drops anything else on load. While the form is open the list (`#conn-recent`)
sits above it; it is hidden when there are none or while the summary shows. Picking one refills the
fields (opening Advanced if needed), clears the password and focuses it; the × on a row forgets it.
Blocked storage just means nothing is remembered.

## Validation

Submit validates every field with `Core/validate.js` (`host`, `port`, `text`) before any request. A failing
field gets an inline message (`aria-invalid` + `.field-error`), the request is not sent, and focus moves
to the first invalid field. A host that carries a scheme or port says so ("Enter the host name only — put
the port in Port."). The server re-checks the same rules (`RequestRules.ValidateConnect`, identical host
messages) and answers `400 { error, field }` — [api.md](../reference/api.md#errors).

## Flow

1. **Connect** → `POST /api/connection`. The server builds a `ClickHouse.Client` connection string,
   runs `SELECT 1`, and on success stores the connection in the session's `ConnectionRegistry`.
2. The **indicator pill** moves idle → connecting → connected / failed (icon + label + colour), with a
   toast. Failure messages carry no credentials.
3. Once connected the form is replaced by a **compact summary** (`.conn-summary`): host +
   `user · TLS · :port`, flagged `TLS ⚠ cert unverified` when the cert opt-in is on. Two icon actions:
   - **change** (edit icon) — reopens the form with **Cancel**; the existing connection stays active
     until a new connect succeeds.
   - **disconnect** (power icon) — `POST /api/connection/disconnect` with `{}` (the proxy blocks `DELETE`). The
     form returns and the workspace is cleared — cards and tabs fade out; reconnecting to the
     same server reopens them from the autosaved workbook ([workbook.md](workbook.md#auto-save)).
4. On page load `GET /api/connection` restores the summary for an existing session (password-free
   view).

## Gating & events

- Until connected, the database picker, table list and canvas dropzone are hidden via the `hidden`
  attribute.
- Every state change dispatches **`connection:changed`** on `document` (detail = the connection view,
  or `{connected:false}`). [schema-browser.md](schema-browser.md) listens to load or clear databases.

## Server side

- `ConnectionRegistry` is session-scoped (cookie `DashboardBuilder.Session`, HttpOnly, 2h idle
  timeout, in-memory store). A new session — or a service restart — starts with no connection.
- Endpoints without a connection return **409** (`ApiControllerBase.NotConnected`).
- Endpoint contract: [api.md](../reference/api.md#connection).
