---
components: [src/DashboardBuilder/DashboardBuilder.csproj]
---
# Deploy a release

Build, copy and verify a release on the live host. The service itself (unit, proxy, runtime) is described in [live-service.md](../operations/live-service.md).

From the solution root (`/unified/user/cj/web_development/prototype/dashboard_builder`):

1. **Build and test:** `dotnet test`, then
   `dotnet publish src/DashboardBuilder/DashboardBuilder.csproj -c Release -o publish`.
2. **Server code changed (any `.cs`, `.cshtml`, csproj):** stop, copy, start. Never copy a DLL over
   the running process; the mmap'd image corrupts (`BadImageFormatException`) and systemd crash-restarts.

   ```bash
   sudo systemctl stop webapps-dev.dashboardbuilder
   cp -r publish/. /var/www/webapps-dev/dashboardbuilder/      # contents, not the folder; leaves keys/ intact
   sudo systemctl start webapps-dev.dashboardbuilder
   ```

   Copy as `unified`, never `sudo cp`; root-owned files in the deploy dir break the next deploy.
   `cp -r publish /var/www/…/` (no `/.`) nests a `publish/` folder and the old DLL keeps running.

3. **Only `Features/**/*.css|js` changed** (and the deployed bundle already has `Features/`): copy the
   assets alone, with no restart and no session loss:

   ```bash
   cp -r publish/Features/* /var/www/webapps-dev/dashboardbuilder/Features/
   ```

4. **Verify:** `curl -sk -o /dev/null -w '%{http_code}\n' https://127.0.0.1:8443/dashboardbuilder/`
   → `200`, **and** a feature asset (`…/features/Core/api.js`) → `200`. Check both, because the page
   alone also answers 200 on a stale build. Then hard-refresh the browser once.
