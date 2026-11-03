---
components: [src/DashboardBuilder/Features/Shell/app.js]
---
# Local development

Checking a change by hand before it is merged. Start the app with the [quickstart](../getting-started/quickstart.md); run the suites from [testing.md](testing.md).

## Visual review and DOM behaviour

**Visual review:** there is no headless browser on the build host. Look at light **and** dark (the tab
bar's appearance toggle) on a spare dev port before deploying a UI change.

**DOM behaviour:** there's no headless browser (Chromium can't launch here), but the real modules can be
driven in **jsdom** against the rendered page and a fake API.

1. Install jsdom into a scratch directory, not the repo.
2. Import `Features/Shell/app.js` with jsdom's window objects exposed as globals. Include `CustomEvent`
   and `EventTarget`, so the store's bus and `document` share one realm.
3. Syntax-check changed modules (`node --check <file>`) and run the smoke test above.
4. Do a manual pass: connect → drag a table → tick keys → draw a 1:N link → add a dashboard → build a
   chart → reload (the workbook restores).

A live-ClickHouse run is manual, because the only account in `credentials.local.md` is localhost-only.
