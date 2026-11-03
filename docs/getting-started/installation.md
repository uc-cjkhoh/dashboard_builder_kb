---
components: [tests/DashboardBuilder.Tests/]
---
# Installation

Where the code lives and how to build and publish it.

## Where the code lives

| What | Path |
|---|---|
| Solution root (run `dotnet` here) | `/unified/user/cj/web_development/prototype/dashboard_builder/` (`DashboardBuilder.slnx`) |
| App project | `…/src/DashboardBuilder/` |
| Tests | `…/tests/DashboardBuilder.Tests/` (xUnit) |
| This KB (docs only) | `/unified/user/cj/knowledge/web_development/dashboard_builder/` |

- The build host is **`10.168.49.20`** (`dataweb`). The KB and the app share its filesystem, so a KB
  session can build and test the app directly, with no SSH needed (decision
  [D9](../decisions/decisions-platform.md#d9--app-source-lives-outside-the-kb-on-the-build-host)).
- The app folder is a **local git repo** (no remote; keep `keys/` ignored), so changes can be reviewed as
  diffs. The KB is a separate git repo. Never scaffold code into the KB.
- SSH and ClickHouse credentials are in the git-ignored [credentials.local.md](../operations/credentials.local.md).

## Build & publish

```bash
cd /unified/user/cj/web_development/prototype/dashboard_builder
dotnet build -c Release
dotnet publish src/DashboardBuilder/DashboardBuilder.csproj -c Release -o publish
```

Publish is framework-dependent. `Features/**/*.css|js` are copied as content alongside the DLL. Keep
ClickHouse credentials out of source, config and logs.
