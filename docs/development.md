# Development — run, build, test on AlmaLinux 9

How to work on the app during development. Environment is **AlmaLinux 9**. The app is
built and **deployed live** as a systemd service — for the production deployment (unit,
Apache proxy, release flow, ops) see [deployment.md](deployment.md); this doc covers the
dev inner loop (`dotnet run`, throwaway ClickHouse, tests).

## Build host & location (required)

The project must be built on host **`10.168.49.20`**, under
**`/unified/user/cj/web_development/prototype/dashboard_builder/`**. Create and compile the app there — i.e.
`src/DashboardBuilder` lives at
`/unified/user/cj/web_development/prototype/dashboard_builder/src/DashboardBuilder`. Run the scaffold, `dotnet
run`, `dotnet build`, and `dotnet test` on that host, from that folder. (This KB lives
separately under `.../knowledge/web_development/drag_and_drop_dashboard_builder`; keep the
built app in the prototype folder above.)

**Credentials** (SSH to the build host, and the ClickHouse login) are in the local,
git-ignored file [project/credentials.local.md](project/credentials.local.md) — not in the
shared docs. Supply the ClickHouse password to the app at runtime, never in committed config.

## Prerequisites

- **.NET SDK 10 (LTS)** ([decision D8](project/decisions.md)).
  From the AlmaLinux appstream:
  ```bash
  sudo dnf install -y dotnet-sdk-10.0
  dotnet --info
  ```
  (Or use Microsoft's package feed / the `dotnet-install` script if the appstream lags.)
  > **As actually installed on the build host (`10.168.49.20`):** the SDK is already on the
  > global `PATH` from the distro packages — `dotnet --version` reports `10.0.108` and
  > `dotnet --list-sdks` shows it under `/usr/lib64/dotnet/sdk` (a 9.0.x SDK is also present but
  > unused). No `~/.dotnet` install or `PATH` prefix is needed here — just run `dotnet` directly.
- **A ClickHouse server to point at.** The **real/target server is TLS-only** — HTTPS on
  **`8443`** (native TLS `9440`), no plaintext `8123`/`9000` ([decision D10](project/decisions.md));
  connect to it with the `secure` flag on and port `8443`. For quick *local* testing a
  throwaway container exposing plain HTTP on 8123 is fine (connect with `secure` off):
  ```bash
  # podman is the AlmaLinux 9 default; docker works the same
  podman run -d --name ch -p 8123:8123 -p 9000:9000 clickhouse/clickhouse-server
  # sanity check the HTTP interface
  curl 'http://localhost:8123/' --data 'SELECT 1'
  ```
  Load a little sample data (e.g. a couple of related tables) so drag/drop and
  relationships have something to show.

## Run

```bash
cd src/DashboardBuilder
dotnet run
# Kestrel serves the one page + /api on the launch profile's URL (see launchSettings.json)
```

Open the page, add a connection pointing at your ClickHouse (host `localhost`, port
`8123`, default user), and you should see databases populate.

## Build & publish

```bash
dotnet build -c Release
dotnet publish -c Release -o out     # framework-dependent; deploy behind a reverse proxy + systemd
```

Keep ClickHouse credentials out of source and logs; supply any server-side config via
environment/secret store, not committed files.

### Hosting under a path prefix (reverse proxy)

The app can be served at the site root **or** under a path prefix. Set the `PathBase`
config value (e.g. env `PathBase=/dashboardbuilder`) and it applies the prefix to routing,
`~/` asset links, and the JSON API — the client derives the same prefix from its own module
URL, so nothing else needs configuring. Empty/unset = served at root (the default; local dev
and tests are unaffected).

```bash
PathBase=/dashboardbuilder ASPNETCORE_URLS=http://127.0.0.1:5006 dotnet run --no-launch-profile
# → http://127.0.0.1:5006/dashboardbuilder/  (root "/" is not served in this mode)
```

### As deployed on the build host (`10.168.49.20`)

This host fronts every .NET app with **Apache httpd** on **443** (the firewall exposes only
443, not the app ports), proxying a path prefix to a localhost Kestrel port. The Dashboard
Builder follows that convention:

- **URL:** `https://10.168.49.20/dashboardbuilder/` (Apache terminates TLS with a
  self-signed cert — browsers show a one-time warning).
- **Apache conf:** `/etc/httpd/conf.d/webapps/5006-dashboardbuilder.conf` —
  `ProxyPass /dashboardbuilder http://127.0.0.1:5006/dashboardbuilder` (+ `ProxyPassReverse`).
  Reload with `sudo systemctl reload httpd` after edits.
- **App:** Kestrel on `127.0.0.1:5006` with `PathBase=/dashboardbuilder`, run as a
  **systemd** service (`dashboardbuilder.service`) off a `dotnet publish` in
  `/var/www/webapps/dashboardbuilder/` — the same pattern as the neighboring apps. This
  durable deploy is already in place; see [deployment.md](deployment.md) for the unit,
  release flow, and ops commands.

## Test

Target coverage (to add as code lands):
- **Unit** — the identifier validate/quote helper ([clickhouse-integration.md](clickhouse-integration.md)):
  the highest-value test; feed it hostile db/table/column names and assert rejection/quoting.
- **Unit** — the ClickHouse type → display-category mapper.
- **Integration** — the introspection/preview endpoints against the throwaway ClickHouse
  (databases/tables/columns/preview round-trip; read-only invariant).
- **Manual/UX** — drag a table → entity renders; select join keys → draw a 1:N link;
  add a subtab → independent canvas; refresh → (v1) state resets, as expected.

```bash
dotnet test
```

## Gotchas while developing

- No ClickHouse running → connection fails by design; check the container/`curl` first.
- `DESCRIBE` returns ClickHouse types, not `int/varchar` — see the type-mapping table.
- Always `LIMIT` previews; don't `SELECT *` a big table into the browser.
- Toggle visibility with the `hidden` attribute, not `style.display`.
- **Stale ES modules:** the frontend is many interdependent ES modules, but only the entry
  `<script>` is version-stamped — `import`s are not. `Program.cs` serves static files with
  `Cache-Control: no-cache` so browsers revalidate; without it, a browser can run a *mix* of old
  and new modules, and a missing/renamed export fails the whole graph silently (symptom: the UI
  does nothing on click). After a deploy, if the UI seems inert, **hard-refresh** (Ctrl/Cmd+Shift+R)
  once — and keep the no-cache header.
