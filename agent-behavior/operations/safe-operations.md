# Safe operations

Rules for an agent touching the build host, the live service or credentials. Commands and layout:
[development.md](../../project-knowledge/operations/development.md),
[deployment.md](../../project-knowledge/operations/deployment.md).

- **This KB is docs only.** Never scaffold code into it; the app source is a separate local git repo on
  the same shared filesystem, built from there.
- **Never `pkill -f DashboardBuilder.dll`** — it matches the live service. Stop dev runs by port.
- **Server changes to the live service:** stop → copy → start. Never copy a DLL over the running process.
- **Credentials** (SSH + ClickHouse) live only in the git-ignored
  [credentials.local.md](../../project-knowledge/operations/credentials.local.md) — never in shared docs,
  logs or URLs.
- **Autonomous runs:** a denied permission or an item that could not be built is logged in
  [run-logs/blocked.md](../run-logs/blocked.md), and the run continues with the next item.
