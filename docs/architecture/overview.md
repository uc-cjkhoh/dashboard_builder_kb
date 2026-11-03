---
components: []
---
# Architecture overview

How the Dashboard Builder is put together: the shape, the request/data flow, and where each piece of
code lives. It is high level only: the step-by-step flow is [data-flow.md](data-flow.md), the code map is [components.md](components.md), and SQL, endpoints and
state shapes are in the [`reference/`](../reference/index.md) files. Decisions are
cited by ID (D2, D19 …), each a heading in [decisions-platform.md](../decisions/decisions-platform.md).

## Shape in one paragraph

A single ASP.NET Core MVC app serves **one HTML page** plus a small **read-only JSON API**.

- The **browser holds all builder state**: the one shared data source (tables dragged onto the canvas
  plus the relationships drawn between them), one worksheet per worksheet tab, and a board of widgets
  per dashboard tab.
- The **server is a thin, session-scoped proxy to ClickHouse**. It keeps the session's connection,
  validates every identifier against the live catalog, runs introspection and bounded aggregate/join
  queries, and returns JSON.
- **There is no application database.** ClickHouse is the only external system
  ([D2](../decisions/decisions-platform.md#d2--thin-session-scoped-proxy-no-application-database)). The
  builder state auto-saves as a **workbook** in the browser
  ([D21](../decisions/decisions-platform.md#d21--workbooks-persist-in-the-browser-not-on-the-server)).

```
Browser — one page, vanilla JS ES modules          ASP.NET Core MVC (Kestrel)               ClickHouse
┌──────────────────────────────────────┐  JSON   ┌───────────────────────────────┐  HTTPS  ┌──────────┐
│ Sidebar: connection · db · tables    │ ──────▶ │ Connection / Schema / Query   │ ──────▶ │ 8443 TLS │
│ Data Source: entities + relationships│         │   API controllers             │  SHOW   │ read-only│
│ Worksheets (+ dashboards, a board)   │ ◀────── │ ClickHouseGateway + Identifier│ DESCRIBE│          │
│   (field pane · shelves · chart)     │         │ ConnectionRegistry (session)  │ SELECT  │          │
└──────────────────────────────────────┘         └───────────────────────────────┘ ◀────── └──────────┘
   all builder state lives here                    holds only the session connection
```

In production Apache httpd terminates TLS and proxies `/dashboardbuilder` to Kestrel
([live-service.md](../operations/live-service.md)).

## Cross-cutting concerns

- **Security** — read-only posture, identifier validation, bound values, credential handling, TLS to
  ClickHouse: [coding-standards.md](../development/coding-standards.md).
- **State & persistence** — all in the browser; the workbook auto-saves to `localStorage` and is restored on connect ([workbook.md](../concepts/workbook/workbook.md)). Shapes: [data-model.md](../reference/data-model.md).
- **Design system** — tokens, layout, components: [design/index.md](../reference/design/index.md).
- **Hosting** — `PathBase`-aware app behind Apache + systemd: [live-service.md](../operations/live-service.md).
- **Why** each choice was made, and what was rejected: [decisions-platform.md](../decisions/decisions-platform.md).
