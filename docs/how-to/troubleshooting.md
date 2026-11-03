---
components: [src/DashboardBuilder/Features/]
---
# Troubleshooting

Common dev-loop failures and their fixes.

- No ClickHouse reachable → connect fails by design; check the container / `curl` first.
- New CSS/JS outside `Features/` won't be served or published.
- If the UI goes inert after rebuilding, hard-refresh once (stale ES modules).
- More: [sharp-edges.md](../development/sharp-edges.md).
