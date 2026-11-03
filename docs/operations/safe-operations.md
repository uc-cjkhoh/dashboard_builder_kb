---
components: []
---
# Safe operations

Rules for an agent touching the build host, the live service or credentials. Commands and layout:
[quickstart.md](../getting-started/quickstart.md),
[live-service.md](live-service.md).

- **This KB is docs only.** Never scaffold code into it; the app source is a separate local git repo on
  the same shared filesystem, built from there.
- **Never `pkill -f DashboardBuilder.dll`** — it matches the live service. Stop dev runs by port.
- **Server changes to the live service:** stop → copy → start. Never copy a DLL over the running process.
- **Credentials** (SSH + ClickHouse) live only in the git-ignored
  [credentials.local.md](credentials.local.md) — never in shared docs,
  logs or URLs.
- **Autonomous runs:** a denied permission or an item that could not be built is logged in
  [run-logs/blocked.md](../development/run-logs/blocked.md), and the run continues with the next item.
