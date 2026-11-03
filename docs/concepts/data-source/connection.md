---
components: [src/DashboardBuilder/ClickHouse/ConnectionRegistry.cs, src/DashboardBuilder/Features/Connection/, src/DashboardBuilder/Features/Core/validate.js]
---
# Connection panel

The connection panel sits at the top of the sidebar. It adds the session's ClickHouse connection and gates the rest of the UI until it exists.

**Code:**

- `Features/Connection/` — `ConnectionController.cs`, `_Connection.cshtml`, `connection.js`, `connection-rules.js`, `connection.css`
- `ClickHouse/ConnectionRegistry.cs` — holds the session's connection

## The form

| Field | Default | Notes |
|---|---|---|
| Host | — | required, ≤ 253; a host name, IPv4 or (bracketed) IPv6 — no scheme, port or path |
| Port | `8443` | required whole number 1–65535 (blank is rejected, not defaulted); the HTTPS interface — the target server is TLS-only ([D10](../../decisions/decisions-platform.md#d10--connect-over-tls-only-https-port-8443)) |
| User | `default` | required, ≤ 64; on the known target, `default` is localhost-only — use a network-enabled account ([sharp edges](../../development/sharp-edges.md#clickhouse)) |
| Password | — | ≤ 256; sent once to the server session; never echoed back |

**Advanced** (a collapsed `<details>`, `#conn-advanced`) holds the rest:

| Field | Default | Notes |
|---|---|---|
| Secure (TLS) | on | |
| Trust invalid / self-signed certificate | off | shown only while Secure is on; a warning (`.form-warn`) shows while ticked ([D11](../../decisions/decisions-platform.md#d11--tls-certificate-validation-safe-by-default-explicit-per-connection-opt-in)) |

- The Advanced section opens by itself when TLS is off or the certificate opt-in is on
  (`advancedShouldOpen` in `connection-rules.js`).
- Inputs are read by element id (`conn-host`, `conn-port`, `conn-user`, `conn-password`, `conn-secure`,
  `conn-allowcert`), not by `form.host` named access.

## Recent connections

After each successful connect, the source is remembered in this browser so it can be picked again.

- **What is kept:** host, port, user, Secure and the certificate opt-in, in `localStorage` key `dashboardbuilder.recent-sources`.
  The list is most recent first, at most 5, one per host/port/user.
- **The password is never stored** (golden rule 4). `recent-sources.js` copies only the fields above, and `sanitize` drops anything else on load
  ([D70](../../decisions/decisions-connection.md#d70--recent-connection-sources-are-non-secret-and-kept-in-the-browser)).
- **Where it shows:** the list (`#conn-recent`) sits above the form while the form is open.
  It is hidden when there are none or while the summary shows.
- **Picking one** refills the fields, opens Advanced if needed, clears the password and focuses it.
  The host is refilled exactly as it was entered (`formValues`), because a recent source is stored from the entered value, never a derived one.
- **Certificate opt-in:** it is remembered too. Picking such a source reopens Advanced with the certificate warning showing; the password is still typed.
- The × on a row forgets that source.
- If browser storage is blocked, nothing is remembered.

## Validation

1. On submit, every field is validated with `Core/validate.js` (`host`, `port`, `text`) before any request.
2. A failing field gets an inline message (`aria-invalid` + `.field-error`), the request is not sent, and focus moves to the first invalid field.
3. A host that carries a scheme or port says so: "Enter the host name only — put the port in Port."
4. The server re-checks the same rules (`RequestRules.ValidateConnect`, with identical host messages) and answers `400 { error, field }` —
   [api.md](../../reference/api.md#errors).

## Flow

1. **Connect** → `POST /api/connection`. The server builds a `ClickHouse.Client` connection string and runs `SELECT 1`.
   On success it stores the connection in the session's `ConnectionRegistry`.
2. **While it runs and after:** there is no status pill.
   - **Connect** is disabled and `aria-busy` while the request runs.
   - Success shows a toast.
   - Failure shows the field error (when the server names a field) or a danger toast. Failure messages carry no credentials.
3. **Once connected**, the form is **collapsed by default** into a one-line **compact summary** (`.conn-summary`, control height):
   a dot and the host, as entered.
   - The host's tooltip is `user · TLS · :port` (`summaryTitle`).
   - A bypassed certificate check adds a warning icon (`#conn-warn`, "Certificate not verified").
   - The summary has two icon actions:
     - **change** (edit icon, `aria-expanded`) toggles the form open (with **Cancel**) and closed again.
       The existing connection stays active until a new connect succeeds.
       The form always holds the active connection's host, port and user (`formFromView`), also after a page reload.
     - **disconnect** (power icon) sends `POST /api/connection/disconnect` with `{}` (the proxy blocks `DELETE`).
       The form returns and the workspace is cleared: cards and tabs fade out.
       Reconnecting to the same server reopens them from the autosaved workbook ([workbook.md](../workbook/workbook.md#auto-save)).
4. **On page load**, `GET /api/connection` restores the summary for an existing session (a password-free view).

## Gating & events

- Until connected, the database picker, table list and canvas dropzone are hidden via the `hidden` attribute.
- Every state change dispatches **`connection:changed`** on `document`. Its detail is the connection view, or `{connected:false}`.
  [schema-browser.md](schema-browser.md) listens to load or clear databases.

## Server side

- `ConnectionRegistry` is session-scoped: cookie `DashboardBuilder.Session`, HttpOnly, 2h idle timeout, in-memory store.
  A new session, or a service restart, starts with no connection.
- Endpoints called without a connection return **409** (`ApiControllerBase.NotConnected`).
- Endpoint contract: [api.md](../../reference/api.md#connection).
