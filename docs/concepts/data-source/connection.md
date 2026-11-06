---
components: [src/DashboardBuilder/ClickHouse/ConnectionRegistry.cs, src/DashboardBuilder/Features/Connection/, src/DashboardBuilder/Features/Core/validate.js]
---
# Connection panel

The connection panel sits at the top of the sidebar. It adds the session's ClickHouse connection and gates the rest of the UI until it exists.

**Code:**

- `Features/Connection/` — `ConnectionController.cs`, `_Connection.cshtml`, `connection.js`, `connection-rules.js`, `connection.css`
- `ClickHouse/ConnectionRegistry.cs` — holds the session's connection

## The form

Layout (`form#conn-form`): the four fields are **one filled block** — a row each (Host, Port, User, Password), the labels in one shared lane (a subgrid: as wide as the longest label plus an 8px gap, so values align and no label touches its value),
every row exactly 32px (the hairline between rows is an inset shadow, not a border); focus deepens the row's fill and an invalid row gets a 1px danger ring with its message under the value.
Motion: rows enter in a 30ms stagger (fields, recent sources), the status dot settles / breathes / pops per state, the lost row rises in, the chevrons
and switch thumbs ease, and **Connect** shows a spinner while it runs; all of it collapses under reduced motion. The open form is one rhythm: recent sources, the fields block, **Advanced** and the actions are stacked 8px apart; the fields and the options (switches + certificate
warning) are two blocks with the same fill, radius and 8px side inset, and **Connect** / **Cancel** are two equal columns (Connect alone spans the row). Under the fields, **Advanced** is a quiet chevron row whose options are **switch rows** (still checkboxes; on = ink, never a hue), then a full-width **Connect**.

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
| Trust invalid / self-signed certificate | **on** | shown only while Secure is on; a warning (`.form-warn`) shows while ticked; untick it to verify the certificate ([D11](../../decisions/decisions-platform.md#d11--tls-certificate-trust-self-signed-is-accepted-by-default-untick-to-verify)) |

- The Advanced section opens by itself when TLS is off or the certificate trust is on, so on a new form it is open and shows the warning
  (`advancedShouldOpen` in `connection-rules.js`).
- Inputs are read by element id (`conn-host`, `conn-port`, `conn-user`, `conn-password`, `conn-secure`,
  `conn-allowcert`), not by `form.host` named access.

## Recent connections

After each successful connect, the source is remembered in this browser so it can be picked again.

- **What is kept:** host, port, user, Secure and the certificate opt-in, in `localStorage` key `dashboardbuilder.recent-sources`.
  The list is most recent first, at most 5, one per host/port/user.
- **The password is never stored** (golden rule 4). `recent-sources.js` copies only the fields above, and `sanitize` drops anything else on load
  ([D70](../../decisions/decisions-connection.md#d70--recent-connection-sources-are-non-secret-and-kept-in-the-browser)).
- **Where it shows:** the list (`#conn-recent`) sits above the form while the form is open, set off from it by one hairline.
  Each row is one flat line: the host (ellipsised) and the user in grey (full `host · user · :port` in the tooltip). Hover or focus washes the row and reveals the × (`.conn-recent__remove`).
  It is hidden when there are none or while the summary shows.
- **Picking one** refills the fields, opens Advanced if needed, clears the password and focuses it.
  The host is refilled exactly as it was entered (`formValues`), because a recent source is stored from the entered value, never a derived one.
- **Certificate opt-in:** it is remembered too. Picking such a source reopens Advanced with the certificate warning showing; the password is still typed.
- The × on a row forgets that source (shown on hover and on keyboard focus).
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
   a **single status row** — status slot, host (as entered; no certificate icon — the opt-in is shown in Advanced and the tooltip), then one right-aligned group (`.conn-row__actions`) of two icon buttons:
   **Change connection** (edit) and **Disconnect** (power). There is no menu and no manual "check connection" button; liveness is probed automatically
   (and **Retry** appears when lost). Above the tile sits a visible group title, **Connections** (`.sidebar__title`; **Databases & Tables** titles the lower group, shown once connected), flush with the tile edge. Below the tile, a full-width hairline divider (`#sidebar-divider`, shown once connected) separates Connection from
   Databases & Tables; its gap flexes 24px → 8px as the table list needs height. Connected, the tile is inset 4px so the dot sits on the
   12px icon lane of the rows below and the host on their 36px text lane.
   - **The status slot is the panel's only coloured element, and it shows liveness, not "connected once".**
     Filled green dot = the last probe reached ClickHouse; hollow grey pulsing ring = checking (one failed probe);
     red cross-in-circle = **lost** (two failed probes in a row, or the browser went offline). Lost also dims the host and adds a row
     under the summary — "Connection lost" in danger ink plus **Retry**. A screen-reader status (`#conn-health-text`) mirrors it.
     Rules: `Connection/connection-health.js` (pure, unit-tested).
   - **Probes:** `GET /api/connection/ping` every 30 s while the tab is visible, on returning to the tab, on `online`, and on Retry.
     It is silent (no activity-bar entry). If the server answers `connected:false` the session ended (2 h idle, restart), so the UI
     returns to the form with a toast instead of showing a stale dot. Cancel from "change" keeps the last probe's state.
   - The summary's actions:
     - **Change connection** (menu) opens the form (with **Cancel**); Cancel returns to the row.
       The existing connection stays active until a new connect succeeds.
       The form always holds the active connection's host, port and user (`formFromView`), also after a page reload.
     - **Disconnect** (in the menu) sends `POST /api/connection/disconnect` with `{}` (the proxy blocks `DELETE`).
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
