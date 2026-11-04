---
components: [src/DashboardBuilder/Features/Shell/AppTimeZone.cs, src/DashboardBuilder/Features/Core/timezone.js, src/DashboardBuilder/Features/Shell/Index.cshtml, tests/js/timezone.test.mjs, tests/DashboardBuilder.Tests/AppTimeZoneTests.cs]
---
# Time zone

Clock times in the UI, and "today" for date ranges, use one **app time zone** — not the browser's.

## Which zone

The server picks it once per page load (`AppTimeZone.Resolve`) and writes its IANA id into
`<meta name="app-timezone">` on the shell page:

1. `Display:TimeZone` (setting or `Display__TimeZone` environment variable), when it names a known zone. `UTC` here really means UTC.
2. Else the zone of the **machine hosting the app** (`TimeZoneInfo.Local`) — unless it reports plain UTC (`UTC`, `Etc/UTC`, `GMT` …), which is treated as "unset" because it is usually a container default.
3. Else **Malaysia time**, `Asia/Kuala_Lumpur` (UTC+8).

The live host is `Asia/Kuala_Lumpur`, so it shows UTC+8 with no setting. If the browser does not know the id, `Core/timezone.js` falls back to Malaysia time.

## Where it applies

| Place | Behaviour |
|---|---|
| Status bar | `Updated hh:mm:ss` is the query time in the app zone |
| Performance timings | the Time column is in the app zone; its header names the offset, e.g. `Time (UTC+8)`; Copy as text uses the same clock |
| Date range presets | "today" is the app zone's calendar date (Last 30 days, This month …), so a range does not flip at 08:00 for a UTC+8 user |
| Print header | `Printed yyyy-mm-dd hh:mm:ss (UTC+8)` |
| Workbook export | the file name's date (`workbook-yyyy-mm-dd.json`) |

It does **not** change how ClickHouse values are shown (a `DateTime` string is shown as stored) and not the ISO timestamps kept inside a saved workbook.

## Code

`Core/timezone.js` is pure and takes the zone as an argument: `clockIn`, `dateIn`, `dateTimeIn`, `todayIn`, `offsetLabel`, `appTimeZone`.
Tests: `tests/js/timezone.test.mjs`, `AppTimeZoneTests.cs`.
