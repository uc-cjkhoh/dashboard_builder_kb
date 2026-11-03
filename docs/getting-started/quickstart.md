---
components: []
---
# Quickstart

Run the app locally and confirm it answers.

```bash
cd /unified/user/cj/web_development/prototype/dashboard_builder/src/DashboardBuilder
dotnet run                                   # launch profile → http://localhost:5080
```

To run on a spare port, skip the launch profile and pass the URL explicitly. Avoid the live port
`5105`, and note that 5080 may already be in use. Otherwise an `ASPNETCORE_URLS` environment variable
or the launch profile pins the port:

```bash
dotnet run --no-launch-profile --urls http://localhost:5180
```

To smoke-test under the proxy prefix:

```bash
PathBase=/dashboardbuilder dotnet run --no-launch-profile --urls http://127.0.0.1:5180
curl -s -o /dev/null -w '%{http_code}\n' http://127.0.0.1:5180/dashboardbuilder/
curl -s -o /dev/null -w '%{http_code}\n' http://127.0.0.1:5180/dashboardbuilder/features/Dashboard/dashboards.js
```

With `PathBase` set, `/` itself is not served. Stop a dev run **by port** (`fuser -k 5180/tcp`). Never
use `pkill -f DashboardBuilder.dll`, which also matches the live service.
