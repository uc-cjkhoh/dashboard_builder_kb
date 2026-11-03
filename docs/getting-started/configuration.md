---
components: []
---
# Configuration

The settings the app reads at startup. Set them as environment variables (systemd `Environment=` or the shell) or in `appsettings.json`.

| Key | Default | Effect |
|---|---|---|
| `ASPNETCORE_URLS` | launch profile: `http://localhost:5080`; live: `http://0.0.0.0:5105` | Kestrel listen address. Avoid the live port `5105` for dev runs |
| `ASPNETCORE_ENVIRONMENT` | `Development` (launch profile) · `Production` (live) | .NET environment |
| `PathBase` | unset | URL prefix the app is served under, e.g. `/dashboardbuilder` behind Apache. With it set, `/` itself is not served |
| `DataProtection:KeyRingPath` | `keys/` under the content root | Where Data Protection keys persist so session cookies survive a restart. Keep it writable and out of git |
| `Logging:LogLevel` | `Default: Information`, `Microsoft.AspNetCore: Warning` | `appsettings.json` |
| `AllowedHosts` | `*` | `appsettings.json` |

- **No secrets on disk.** ClickHouse credentials are entered in the UI and live only in the server session ([coding-standards.md](../development/coding-standards.md#4-credentials-live-in-the-session-and-nowhere-else)).
- **Changing the public path** means changing `PathBase` in the systemd unit and the Apache conf together ([live-service.md](../operations/live-service.md)).
