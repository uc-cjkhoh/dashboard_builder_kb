# Deployment — live on the build host (`10.168.49.20` / `dataweb`)

The Dashboard Builder is **deployed and running as a permanent systemd service**.
This is the "durable deploy" pattern that [development.md](development.md) says to
match — it is now in place. For how to *run/build during development*, see
[development.md](development.md); this doc describes the **production deployment**.

> Snapshot verified 2026-08-17. `dashboardbuilder.service` has been
> `active (running)` since 2026-08-14 (deployed 10:54 +08) and is enabled at boot.

## Topology

```
Browser
  │  https://10.168.49.20/dashboardbuilder/   (self-signed TLS → one-time warning)
  ▼
Apache httpd  ── listens :443, terminates TLS (VirtualHost in webui.conf)
  │  /etc/httpd/conf.d/webapps/5006-dashboardbuilder.conf
  │  ProxyPass /dashboardbuilder → http://127.0.0.1:5006/dashboardbuilder
  ▼
Kestrel  (dotnet DashboardBuilder.dll)  ── systemd: dashboardbuilder.service
  listening 0.0.0.0:5006,  PathBase=/dashboardbuilder,  ASPNETCORE_ENVIRONMENT=Production
  ▼
ClickHouse (HTTPS interface, per-session read-only connection — creds live only in session state)
```

The firewall exposes only **443**, not the app ports. Port `5006` is this app's
slot in the host's per-webapp convention (`5000-ucbizview` … `5006-dashboardbuilder`,
one Apache conf + one Kestrel port each under `/etc/httpd/conf.d/webapps/`).

## systemd service

- **Unit:** `/etc/systemd/system/dashboardbuilder.service`
- **Enabled at boot**, runs as user `unified`
- **Restart policy:** `Restart=always`, `RestartSec=10`
- **Shutdown:** `KillSignal=SIGINT` (graceful Kestrel shutdown)

```ini
[Unit]
Description=ASP.NET Core Web App - DashboardBuilder
After=network.target

[Service]
WorkingDirectory=/var/www/webapps/dashboardbuilder
ExecStart=/usr/bin/dotnet /var/www/webapps/dashboardbuilder/DashboardBuilder.dll
Restart=always
RestartSec=10
KillSignal=SIGINT
SyslogIdentifier=dashboardbuilder
User=unified
Environment=ASPNETCORE_ENVIRONMENT=Production
Environment=ASPNETCORE_URLS=http://0.0.0.0:5006
Environment=PathBase=/dashboardbuilder

[Install]
WantedBy=multi-user.target
```

`PathBase=/dashboardbuilder` is what makes routing, `~/` asset links, and the
`/api` group resolve under the proxy prefix (see `Program.cs` `UsePathBase`, and
[development.md § Hosting under a path prefix](development.md)). If you change the
public path, change it in **both** the unit's `PathBase` env **and** the Apache conf.

## Apache reverse proxy

`/etc/httpd/conf.d/webapps/5006-dashboardbuilder.conf` (Included into the `:443`
TLS VirtualHost):

```apache
ProxyPreserveHost On

ProxyPass /dashboardbuilder http://127.0.0.1:5006/dashboardbuilder
ProxyPassReverse /dashboardbuilder http://127.0.0.1:5006/dashboardbuilder

<Location /dashboardbuilder>
   Require all granted
</Location>
```

Reload with `sudo systemctl reload httpd` after edits.

## Runtime

- **Framework:** .NET 10 (`net10.0`), framework-dependent — uses the host's
  `Microsoft.NETCore.App` / `Microsoft.AspNetCore.App` 10.0 shared frameworks
  (`dotnet --version` → `10.0.108`).
- **Hosting:** Kestrel, launched directly by systemd via `/usr/bin/dotnet`. The
  `web.config` in the deploy dir describes IIS in-process hosting and is **not used**
  in this Linux/systemd deployment.
- **Config:** `appsettings.json` (Logging + `AllowedHosts: *`). No secrets on disk —
  ClickHouse credentials live only in server-side session state (CLAUDE.md golden rule).

## Deploy directory

`/var/www/webapps/dashboardbuilder/` — owned by `unified`, a copy of a
`dotnet publish` bundle. Key files:

| File | Purpose |
|------|---------|
| `DashboardBuilder.dll` | app entry assembly (run by `dotnet`) |
| `DashboardBuilder.runtimeconfig.json` | targets `net10.0`, server GC, invariant globalization |
| `appsettings.json` | logging / AllowedHosts |
| `wwwroot/` | static assets (JS ES-module graph, css, ECharts vendor) |
| `ClickHouse.Client.dll`, `NodaTime.dll`, `Microsoft.IO.RecyclableMemoryStream.dll` | dependencies |

## Build & release flow

Build in the prototype folder (`/unified/user/cj/web_development/prototype/dashboard_builder/`,
see [development.md](development.md)), then copy the publish bundle into the deploy dir:

```bash
# from the repo root on the build host
dotnet publish src/DashboardBuilder/DashboardBuilder.csproj -c Release -o publish

# copy the bundle into place (needs write access to the deploy dir)
cp -r publish/* /var/www/webapps/dashboardbuilder/

# restart to pick up the new build
sudo systemctl restart dashboardbuilder
```

> Static JS modules are served with `Cache-Control: no-cache` (see `Program.cs` and
> [development.md § Stale ES modules](development.md)) so browsers always re-fetch
> changed modules after a deploy — no manual cache-busting needed.

## Operations

```bash
# status / health
systemctl status dashboardbuilder
sudo systemctl restart dashboardbuilder
sudo systemctl stop dashboardbuilder

# follow logs (SyslogIdentifier=dashboardbuilder)
journalctl -u dashboardbuilder -f

# confirm Kestrel is bound
ss -ltnp | grep 5006
```

### Session cookie warnings (fixed)

Older deploys logged this repeatedly after a restart/redeploy:

```
warn: Microsoft.AspNetCore.Session.SessionMiddleware
      Error unprotecting the session cookie.
      CryptographicException: The payload was invalid.
```

**Cause:** ASP.NET Core Data Protection keys were ephemeral, so each process start
generated new keys and could no longer decrypt cookies issued by the previous run.

**Fix (in `Program.cs`):** the Data Protection key ring is now persisted to disk with
`AddDataProtection().PersistKeysToFileSystem(...).SetApplicationName("DashboardBuilder")`.
After a restart the cookie decrypts cleanly (resolving to a fresh session) instead of
throwing.

- **Key ring location:** defaults to a `keys/` folder under the content root — i.e.
  `/var/www/webapps/dashboardbuilder/keys/` in production. Override with config key
  `DataProtection:KeyRingPath` (env `DataProtection__KeyRingPath`).
- The `keys/` dir must be **writable by the service user (`unified`)** and must
  **persist across redeploys** — it lives outside the `publish` bundle, so the
  `cp -r publish/*` release step leaves it intact. Don't delete it, and don't commit it.
- **Note:** this removes the crypto error only. Session *contents* still reset on restart
  because the session store is in-memory (`AddDistributedMemoryCache`); to preserve session
  state across restarts you'd also need a persistent distributed cache (e.g. Redis).
