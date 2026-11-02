# Blocked work

Items that could not be built, with why. Each entry: the item, what was denied or missing, the date, and what unblocks it. Remove an entry when the item is unblocked.

Format: `- **<item>** (<date>) — <what was denied or is missing>. Unblocks: <what is needed>.`

- **Text functions remainder: live ClickHouse smoke** (2026-11-02) — reading the git-ignored credentials file was denied by the auto-mode classifier, so tests/live/text-smoke.mjs was not extended or run for FIND/MID/LTRIM/RTRIM/ICONTAINS/ISTARTSWITH/IENDSWITH. Unblocks: owner runs a smoke with CH_* env vars set (cases to pin: FIND multibyte position, MID past end, I* with non-ASCII case).
