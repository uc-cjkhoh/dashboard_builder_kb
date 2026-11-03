---
components: []
---
# Prerequisites

What you need before building or running the app.

- **.NET SDK 10** — already on the host's global `PATH` (`/usr/lib64/dotnet`, `dotnet --version` →
  `10.0.108`). A 9.0 SDK is also present but unused. Elsewhere: `sudo dnf install -y dotnet-sdk-10.0`.
- **A ClickHouse to point at.** The real target is TLS-only on `8443` with a self-signed cert. Tick
  Secure and the cert opt-in, and use a network-enabled account
  ([sharp edges](../development/sharp-edges.md#clickhouse)). For quick local testing, a throwaway
  container on plain HTTP works (connect with Secure off, port `8123`):

  ```bash
  podman run -d --name ch -p 8123:8123 -p 9000:9000 clickhouse/clickhouse-server
  curl 'http://localhost:8123/' --data 'SELECT 1'
  ```

  Load a couple of related tables so drag/drop, relationships and joins have something to show.
