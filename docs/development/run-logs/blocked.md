# Blocked work

Items that could not be built, with why. Each entry: the item, what was denied or missing, the date, and what unblocks it. Remove an entry when the item is unblocked.

Format: `- **<item>** (<date>) — <what was denied or is missing>. Unblocks: <what is needed>.`

- **Text functions remainder: live ClickHouse smoke** (2026-11-02) — reading the git-ignored credentials file was denied by the auto-mode classifier, so tests/live/text-smoke.mjs was not extended or run for FIND/MID/LTRIM/RTRIM/ICONTAINS/ISTARTSWITH/IENDSWITH. Unblocks: owner runs a smoke with CH_* env vars set (cases to pin: FIND multibyte position, MID past end, I* with non-ASCII case).
- **Filter on an aggregated measure: live ClickHouse smoke** (2026-11-06) — reading the git-ignored credentials file was denied by the auto-mode classifier, so `tests/live/having-smoke.mjs` was written (syntax-checked) but not run against test_cj. Unblocks: owner runs it with CH_* env vars set and `NODE_EXTRA_CA_CERTS` pointing at the test server's certificate, against the having-filter build on a spare port (cases: HAVING vs an oracle `SELECT … HAVING`, Top-N then HAVING, WHERE + HAVING + total, no-dimension view, 400s).
- **Aggregate before joining: live ClickHouse smoke** (2026-11-06) — the brief withholds the git-ignored credentials file, so the SQL was checked against a stub endpoint (`AggregateJoinTests`) but not run against test_cj. Unblocks: owner runs a smoke with CH_* env vars set (cases: a fan-out sum equals the per-table sum, both filter directions, avg, outer join with a filtered table, compound key).
- **Box plot live smoke** (2026-11-06) — not run: the live ClickHouse smoke needs the git-ignored credentials, which this item was told not to read. Unblocks: a run of a smoke over a two-table join with a calculated value through `POST /api/boxplot` (tests/live pattern of calc-smoke.mjs) with credentials supplied.
