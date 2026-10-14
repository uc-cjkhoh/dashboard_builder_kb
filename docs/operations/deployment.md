# Deployment — live on `10.168.49.20`

The Dashboard Builder runs as a permanent **systemd** service behind **Apache httpd**, following the
host's per-webapp convention ([D20](../reference/decisions.md#d20--apache-reverse-proxy--pathbase--systemd)).
For the dev loop see [development.md](development.md).

## At a glance

| Item | Value |
|---|---|
| Public URL | `https://10.168.49.20:8443/dashboardbuilder` (self-signed TLS → one-time browser warning) |
| Apache vhost | `:8443` dev/test vhost (`/etc/httpd/conf.d/webui-dev.conf`), which includes `conf.d/webapps-dev/*.conf` |
| Proxy conf | `/etc/httpd/conf.d/webapps-dev/5105-dashboardbuilder.conf` |
| systemd unit | `webapps-dev.dashboardbuilder.service` (`/etc/systemd/system/`) |
| Kestrel | `0.0.0.0:5105`, `PathBase=/dashboardbuilder`, `ASPNETCORE_ENVIRONMENT=Production` |
| Deploy dir | `/var/www/webapps-dev/dashboardbuilder/` (owned by `unified`) |
| Logs | `journalctl -u webapps-dev.dashboardbuilder` (`SyslogIdentifier=dashboardbuilder`) |

Port `5105` is this app's slot in the host convention (`5100-ucbizview` … `5105-dashboardbuilder`,
`5106-mnpwebportal`, …; one Apache conf + one Kestrel port each). The firewall exposes only the Apache
ports. The production `:443` vhost (`conf.d/webapps/`) does **not** serve this app.

## Topology

```
Browser ── https://10.168.49.20:8443/dashboardbuilder
  ▼
Apache httpd :8443 (TLS) ── 5105-dashboardbuilder.conf
  │  ProxyPass /dashboardbuilder → http://127.0.0.1:5105/dashboardbuilder
  ▼
Kestrel: dotnet DashboardBuilder.dll ── webapps-dev.dashboardbuilder.service
  ▼
ClickHouse (HTTPS 8443) — per-session connection; credentials only in session state
```

## systemd unit

```ini
[Unit]
Description=ASP.NET Core Web App - DashboardBuilder
After=network.target

[Service]
WorkingDirectory=/var/www/webapps-dev/dashboardbuilder
ExecStart=/usr/bin/dotnet /var/www/webapps-dev/dashboardbuilder/DashboardBuilder.dll
Restart=always
RestartSec=10
KillSignal=SIGINT
SyslogIdentifier=dashboardbuilder
User=unified
Environment=ASPNETCORE_ENVIRONMENT=Production
Environment=ASPNETCORE_URLS=http://0.0.0.0:5105
Environment=PathBase=/dashboardbuilder

[Install]
WantedBy=multi-user.target
```

To change the public path, change it in **both** the unit's `PathBase` and the Apache conf.

## Apache proxy conf

```apache
ProxyPreserveHost On

ProxyPass /dashboardbuilder http://127.0.0.1:5105/dashboardbuilder
ProxyPassReverse /dashboardbuilder http://127.0.0.1:5105/dashboardbuilder

<Location /dashboardbuilder>
   Require all granted
</Location>
```

Reload with `sudo systemctl reload httpd` after edits (root-owned; `sudo` needs a password).

**The proxy 403s `DELETE` and any request without a body** before Kestrel sees it — every
state-changing call must be a `POST` with JSON ([sharp edges](../conventions/sharp-edges.md#hosting--deploy)).

## Runtime

- **.NET 10**, framework-dependent (`net10.0`), Kestrel launched directly by systemd. The `web.config` in
  the deploy dir is for IIS and unused here.
- **Config:** `appsettings.json` (logging, `AllowedHosts: *`). No secrets on disk.
- **Sessions:** in-memory (`AddDistributedMemoryCache`), so **every restart drops every session's
  ClickHouse connection** — users must reconnect.
- **Data Protection keys** persist to `keys/` under the content root
  (`/var/www/webapps-dev/dashboardbuilder/keys/`; override with `DataProtection:KeyRingPath`) with
  `SetApplicationName("DashboardBuilder")`, so session cookies from before a restart decrypt cleanly
  instead of logging `CryptographicException`. The dir must stay writable by `unified` and survive
  redeploys — don't delete it (and keep it out of git).
- **Static assets** are served `Cache-Control: no-cache` so browsers revalidate changed ES modules.

## Deployed build vs. source

The live bundle matches the source: MVC feature folders
([D19](../reference/decisions.md#d19--mvc-in-feature-folders)) with assets under `Features/`, the
database-level query guards with their step-down, the truncation notice, the query cache and the browser
workbook. Asset-only changes can now use the no-restart copy (step 3 below).

## Release flow

From the solution root (`/unified/user/cj/web_development/prototype/dashboard_builder`):

1. **Build and test:** `dotnet test`, then
   `dotnet publish src/DashboardBuilder/DashboardBuilder.csproj -c Release -o publish`.
2. **Server code changed (any `.cs`, `.cshtml`, csproj)** — stop, copy, start. Never copy a DLL over
   the running process: the mmap'd image corrupts (`BadImageFormatException`) and systemd crash-restarts.

   ```bash
   sudo systemctl stop webapps-dev.dashboardbuilder
   cp -r publish/. /var/www/webapps-dev/dashboardbuilder/      # contents, not the folder; leaves keys/ intact
   sudo systemctl start webapps-dev.dashboardbuilder
   ```

   Copy as `unified`, never `sudo cp` — root-owned files in the deploy dir break the next deploy.
   `cp -r publish /var/www/…/` (no `/.`) nests a `publish/` folder and the old DLL keeps running.

3. **Only `Features/**/*.css|js` changed** (and the deployed bundle already has `Features/`) — copy the
   assets alone; no restart, no session loss:

   ```bash
   cp -r publish/Features/* /var/www/webapps-dev/dashboardbuilder/Features/
   ```

4. **Verify:** `curl -sk -o /dev/null -w '%{http_code}\n' https://127.0.0.1:8443/dashboardbuilder/`
   → `200`, **and** a feature asset (`…/features/Core/api.js`) → `200` — the page alone also answers 200
   on a stale build. Then hard-refresh the browser once.

## Operations

```bash
systemctl status webapps-dev.dashboardbuilder
sudo systemctl restart webapps-dev.dashboardbuilder     # drops all sessions
journalctl -u webapps-dev.dashboardbuilder -f
ss -ltnp | grep 5105                                    # Kestrel bound?
```
