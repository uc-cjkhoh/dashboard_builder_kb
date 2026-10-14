# Sharp edges

Gotchas that have bitten (or will bite) this app. Read before touching the area named in each heading.

## ClickHouse

- **No foreign keys exist.** Don't look for `system` FK metadata. Relationship keys are user-picked
  columns ([golden rule 5](golden-rules.md#5-relationships-are-logical-declarations-not-database-facts)).
- **Identifiers aren't parameterizable.** `SHOW TABLES FROM {db}` and `DESCRIBE {db}.{table}` need
  string interpolation; only *values* can be bound
  ([golden rule 2](golden-rules.md#2-never-interpolate-an-identifier-you-havent-validated)).
- **`DESCRIBE` returns ClickHouse types, not SQL-92.** Expect `Nullable(...)`, `LowCardinality(...)`,
  `Array(...)`, `Enum8(...)`, `DateTime64(3)`. Map through `ClickHouseType.Categorize`; don't assume
  `int`/`varchar` ([type mapping](../reference/clickhouse-integration.md#type-mapping)).
- **A "wrong password" can be a source-IP restriction.** A user limited by `<networks>` gets
  `Code: 194 … REQUIRED_PASSWORD` (HTTP 401) from a disallowed IP even with the right password. The
  `default` user on `10.168.49.13` is localhost-only — connect from the app host with a
  network-enabled account ([detail](../reference/clickhouse-integration.md#a-wrong-password-can-be-a-network-restriction)).
- **The target cert is self-signed.** Validation is on by default, so connecting needs the
  "Trust invalid / self-signed certificate" box ticked
  ([D11](../reference/decisions.md#d11--tls-certificate-validation-safe-by-default-explicit-per-connection-opt-in)).
- **A hand-built `HttpClient` must set `AutomaticDecompression`**, or ClickHouse.Client throws
  "server returned compressed result but HttpClient did not decompress it".
- **Two connections, same server, different databases is normal.** Scope every query to the
  connection + database the request names, never a global default.

## Hosting & deploy

- **The Apache proxy 403s `DELETE` and body-less `POST`/`GET`** before Kestrel sees them. Every
  state-changing call is a `POST` with a JSON body — Disconnect is `POST /api/connection/disconnect`
  with `{}`. A feature can pass tests and direct `curl :5105` yet fail in the browser.
- **Never copy a DLL over the running process.** Overwriting the live mmap'd `DashboardBuilder.dll`
  throws `BadImageFormatException`, systemd crash-restarts, and every session's in-memory connection
  is lost. Stop → copy → start ([deployment.md § Release flow](../operations/deployment.md#release-flow)).
- **Never `pkill -f DashboardBuilder.dll`** — it matches the live service too. Kill dev runs by port.
- **A restart resets every session** (in-memory session store) — users must reconnect; their workbook
  restores from the browser on reconnect.
- **Stale ES modules.** Imports aren't version-stamped; static files are served `Cache-Control:
  no-cache` so browsers revalidate. Keep that header. If the UI goes inert after a deploy,
  hard-refresh once.

## Frontend

- **Measure values can be a string or `null`, not just a number.** `min` / `max` of a text or date column
  return strings; an aggregate over no rows (or `NaN` / `∞`) returns `null`. Anything that reads
  `row.values[i]` must handle both — only Table, Text and KPI can show a string. A numeric-looking text
  value (`"01234"`) still gets number formatting (no measure-type signal reaches the client).
- **Temporal values are ISO text, and midnight `DateTime` renders date-only.** Keys, distinct values and
  box labels are `YYYY-MM-DD` or `YYYY-MM-DD HH:MM:SS`; a `DateTime` at exactly `00:00:00` prints as
  `YYYY-MM-DD`. A `Date` / `Date32` column rejects a filter value with a time part (400). `DateTime64`
  keys lose their milliseconds, and filter values with fractional seconds are rejected.
- **Server filter cap (20) ≠ client cap (8).** The worksheet appends the shared filters (≤ 4), drill path,
  page, selection and date range to the user's filters; raise one side only with the other in mind ([api.md § Limits](../reference/api.md#limits)).
- **Approximate SAMPLE is untested against a live ClickHouse.** The SQL (`SAMPLE 0.1`, `_sample_factor`)
  follows the ClickHouse docs; a refusal falls back to an unsampled query, so the worst case is no speed-up.
- **The result cache is per process.** Two app instances keep separate caches; a restart empties it.
- **Drop-time caps ignore the chart type.** Dimension / measure counts include encodings the current
  chart doesn't use, so a drop exactly at the cap can be refused until the stale encoding is removed.
- **`POST /api/query {}` is a 400, not a 409** — model binding runs before the connection check.
- **An unmatched `/api/*` route returns an empty-body 404** (no `{ error }`); a client that parses the
  body must tolerate it.
- **An unreadable stored workbook is backed up, never overwritten.** Autosave is blocked for a key only
  when no backup could be kept ([workbook.md](../features/workbook.md#restore-on-connect)).
- **The worksheet's column cache is never invalidated on reconnect** to a different server; filters can
  read "can't be compared" until a reload.
- **New feature CSS/JS must sit under `Features/`.** Only `.css`/`.js` are served from there
  (`/features/<Feature>/<file>`) and only those globs are copied on publish; anything else 404s.
- **Init order matters.** `app.js` registers listeners (`schema.js`'s `connection:changed`) before
  `connection.js` fires its initial status check.
- **`api.js` derives the API base from its own URL** by stripping `/features/Core/`. Move the file and
  every API call 404s — the page still loads, so only a click reveals it.
- **No headless browser on the build host**, but Node 24 is (via nvm): unit-test pure modules with
  `node --test` and drive the DOM in jsdom ([development.md](../operations/development.md#test)).
- **Ports 5080 and 5199 are taken** (the launch profile pins 5080, and a long-running dev process holds
  5199). Smoke-test with `dotnet run --no-launch-profile --urls http://localhost:5180` — an
  `ASPNETCORE_URLS` / launch-profile setting otherwise wins.
- **A cache hit means no query.** Presentation-only changes re-render from the worksheet's result
  cache; if a change *should* re-query, it must change the plan (see
  [worksheet.md § Query lifecycle](../features/worksheet.md#query-lifecycle)).
