# P34 plan — Client A: validation primitives, connection, data model (Tasks 5–6)

Part of the [P34 plan](plan-overview.md). Paths are relative to `src/DashboardBuilder/Features/` unless they
start with `tests/`. `NODE=~/.nvm/versions/node/v24.20.0/bin/node`.

### Task 5: Validation primitives, error plumbing, connection form

**Files:**
- Create: `Core/validate.js`; Test: `tests/js/validate.test.mjs`
- Modify: `Core/ui.js` (`fieldError`, `clearFieldError`, `checkField`, `listDialog`, dismissible danger toast),
  `Core/api.js` (`errorMessage`, `.status`/`.field` on thrown errors, network failure message),
  `Shell/app.js` (global handlers), `Connection/_Connection.cshtml`, `Connection/connection.js`
- Test: `tests/js/api-base.test.mjs` (add `errorMessage` cases)

**Interfaces:**
- Produces (`Core/validate.js`): `LIMITS`, `HOST_MESSAGES`, `host(raw)`, `port(raw)`,
  `text(raw, { label, max, required = false, trim = true })`, `number(raw)`, `dateTime(raw)`,
  `filterValue(category, raw, column)`, `range(category, lo, hi, column)` — each returns
  `{ ok: true, value } | { ok: false, error }`.
- Produces (`Core/ui.js`): `fieldError(input, message)`, `clearFieldError(input)`, `checkField(input, result) → value | undefined`,
  `listDialog(title, items: string[]) → Promise<void>`. `toast(message, "danger")` now stays until dismissed.
- Produces (`Core/api.js`): `errorMessage(status, data) → string`; thrown errors carry `.status` and `.field`.

- [ ] **Step 1: Write the failing tests** — `tests/js/validate.test.mjs`:

```js
import { test } from "node:test";
import assert from "node:assert/strict";
import { host, port, text, number, dateTime, filterValue, range, HOST_MESSAGES, LIMITS }
  from "../../src/DashboardBuilder/Features/Core/validate.js";

const err = (r) => (assert.equal(r.ok, false), r.error);
test("valid hosts pass trimmed", () => {
  for (const h of ["clickhouse.example.com", "10.168.49.13", "localhost", "::1", "[::1]", "ch_1.internal"]) assert.equal(host(h).ok, true, h);
  assert.equal(host("  padded.host ").value, "padded.host");
});
test("invalid hosts say why, with the server's wording", () => {
  assert.equal(err(host("https://h")), HOST_MESSAGES.scheme);
  assert.equal(err(host("h:8443")), HOST_MESSAGES.port);
  assert.equal(err(host("[::1]:8443")), HOST_MESSAGES.port);
  assert.equal(err(host("h/db")), HOST_MESSAGES.path);
  assert.equal(err(host("bad host")), HOST_MESSAGES.invalid);
  assert.equal(err(host("   ")), "Host is required.");
  assert.equal(err(host("a".repeat(LIMITS.host + 1))), "Host must be at most 253 characters.");
});
test("port is a required whole number 1–65535", () => {
  assert.equal(port(" 8443 ").value, 8443);
  assert.equal(err(port("")), "Port is required.");
  for (const p of ["0", "65536", "84.5", "abc", "-1", "1e3"]) assert.equal(err(port(p)), "Port must be a whole number from 1 to 65535.", p);
});
test("text trims, requires and caps", () => {
  assert.equal(text("  Sales ", { label: "Tab name", max: 60, required: true }).value, "Sales");
  assert.equal(err(text("   ", { label: "Tab name", max: 60, required: true })), "Tab name is required.");
  assert.equal(err(text("x".repeat(61), { label: "Tab name", max: 60 })), "Tab name must be at most 60 characters.");
  assert.equal(text(" p ", { label: "Password", max: 256, trim: false }).value, " p ");
});
test("numbers are plain — no locale separators, hex or words", () => {
  assert.equal(number(" -1.5 ").value, -1.5);
  assert.equal(number("1e3").value, 1000);
  for (const n of ["1,5", "1,000", "1 000", "0x10", "NaN", "Infinity", "", "  "]) assert.equal(number(n).ok, false, n);
});
test("dates are ISO and real calendar days", () => {
  assert.equal(dateTime("2024-02-29").value, "2024-02-29");
  assert.equal(dateTime("2024-01-31T10:20").value, "2024-01-31 10:20:00");
  for (const d of ["2023-02-29", "31/01/2024", "2024-13-01", "2024-01-01 25:00"]) assert.equal(dateTime(d).ok, false, d);
});
test("filter values are checked by column category, naming the column", () => {
  assert.match(err(filterValue("numeric", "abc", "amount")), /amount/);
  assert.equal(filterValue("boolean", "TRUE", "flag").value, "true");
  assert.equal(filterValue("text", " a ", "name").value, " a ");
  assert.equal(filterValue("compound", "x", "tags").ok, false);
  assert.equal(filterValue("text", " ", "name").ok, false); // whitespace-only counts as empty
});
test("a range needs From ≤ To", () => {
  assert.match(err(range("numeric", "9", "1", "amount")), /From must be less than or equal to To/);
  assert.deepEqual(range("temporal", "2024-01-01", "2024-02-01", "d").value, ["2024-01-01", "2024-02-01"]);
});
```

Add to `tests/js/api-base.test.mjs`:

```js
import { errorMessage } from "../../src/DashboardBuilder/Features/Core/api.js";
test("errorMessage prefers {error}, then ProblemDetails title, then a status line", () => {
  assert.equal(errorMessage(400, { error: "Port is required.", field: "port" }), "Port is required.");
  assert.equal(errorMessage(400, { title: "One or more validation errors occurred." }), "One or more validation errors occurred.");
  assert.equal(errorMessage(502, null), "Server error (502).");
  assert.equal(errorMessage(404, null), "Request failed (404).");
});
```

- [ ] **Step 2: Run** `$NODE --test tests/js/*.test.mjs` — expected FAIL (module/exports missing).

- [ ] **Step 3: Implement `Core/validate.js`:**

```js
// Pure input parsers (no DOM) shared by every form. Each returns { ok: true, value } or
// { ok: false, error } — a user-facing sentence. Mirrors ClickHouse/RequestValidation.cs: keep LIMITS and
// the host messages identical on both sides.
export const LIMITS = Object.freeze({
  host: 253, user: 64, password: 256, tabName: 60, axisTitle: 80, filterValue: 1000,
  filters: 8, inValues: 500, dashboards: 50, pillsPerShelf: 20,
});
export const HOST_MESSAGES = Object.freeze({
  scheme: "Enter the host name only — no http:// or https://.",
  port: "Enter the host name only — put the port in Port.",
  path: "Enter the host name only — no path.",
  invalid: "Enter a valid host name or IP address.",
});
const ok = (value) => ({ ok: true, value });
const fail = (error) => ({ ok: false, error });
const HOSTNAME = /^[A-Za-z0-9_]([A-Za-z0-9_-]{0,61}[A-Za-z0-9_])?(\.[A-Za-z0-9_]([A-Za-z0-9_-]{0,61}[A-Za-z0-9_])?)*\.?$/;
const PLAIN_NUMBER = /^[+-]?(\d+\.?\d*|\.\d+)([eE][+-]?\d+)?$/;
const ISO = /^(\d{4})-(\d{2})-(\d{2})(?:[ T](\d{2}):(\d{2})(?::(\d{2}))?)?$/;
const isIPv6 = (s) => /^[0-9A-Fa-f:.]+$/.test(s) && (() => { try { new URL(`http://[${s}]/`); return true; } catch { return false; } })();

export function host(raw) {
  const h = String(raw ?? "").trim();
  if (!h) return fail("Host is required.");
  if (h.length > LIMITS.host) return fail(`Host must be at most ${LIMITS.host} characters.`);
  if (h.includes("://")) return fail(HOST_MESSAGES.scheme);
  if (h.includes("/")) return fail(HOST_MESSAGES.path);
  if (h.startsWith("[")) {
    const close = h.indexOf("]");
    if (close < 0) return fail(HOST_MESSAGES.invalid);
    if (close !== h.length - 1) return fail(HOST_MESSAGES.port);
    return isIPv6(h.slice(1, close)) ? ok(h) : fail(HOST_MESSAGES.invalid);
  }
  if ((h.match(/:/g) ?? []).length >= 2) return isIPv6(h) ? ok(h) : fail(HOST_MESSAGES.invalid);
  if (h.includes(":")) return fail(HOST_MESSAGES.port);
  return HOSTNAME.test(h) ? ok(h) : fail(HOST_MESSAGES.invalid);
}
export function port(raw) {
  const p = String(raw ?? "").trim();
  if (!p) return fail("Port is required.");
  const n = /^\d{1,5}$/.test(p) ? Number(p) : NaN;
  return n >= 1 && n <= 65535 ? ok(n) : fail("Port must be a whole number from 1 to 65535.");
}
export function text(raw, { label, max, required = false, trim = true }) {
  const s = String(raw ?? "");
  const v = trim ? s.trim() : s;
  if (required && !v.trim()) return fail(`${label} is required.`);
  if (v.length > max) return fail(`${label} must be at most ${max} characters.`);
  return ok(v);
}
export function number(raw) {
  const s = String(raw ?? "").trim();
  const n = PLAIN_NUMBER.test(s) ? Number(s) : NaN;
  return Number.isFinite(n) ? ok(n) : fail(`'${raw}' is not a number.`);
}
export function dateTime(raw) {
  const m = ISO.exec(String(raw ?? "").trim());
  if (m) {
    const [, y, mo, d, h = "00", mi = "00", se = "00"] = m;
    const t = new Date(Date.UTC(+y, +mo - 1, +d, +h, +mi, +se));
    const real = t.getUTCFullYear() === +y && t.getUTCMonth() === +mo - 1 && t.getUTCDate() === +d && t.getUTCHours() === +h && t.getUTCMinutes() === +mi;
    if (real) return ok(m[4] === undefined ? `${y}-${mo}-${d}` : `${y}-${mo}-${d} ${h}:${mi}:${se}`);
  }
  return fail(`'${raw}' is not a date (YYYY-MM-DD or YYYY-MM-DD HH:MM:SS).`);
}
export function filterValue(category, raw, column) {
  const s = String(raw ?? "");
  if (!s.trim()) return fail(`Enter a value for ${column}.`);
  if (s.length > LIMITS.filterValue) return fail(`A filter value must be at most ${LIMITS.filterValue} characters.`);
  switch (category) {
    case "numeric": { const r = number(s); return r.ok ? r : fail(`'${s}' is not a number for column ${column}.`); }
    case "temporal": { const r = dateTime(s); return r.ok ? r : fail(`'${s}' is not a date (YYYY-MM-DD or YYYY-MM-DD HH:MM:SS) for column ${column}.`); }
    case "boolean": {
      const b = s.trim().toLowerCase();
      if (b === "true" || b === "1") return ok("true");
      if (b === "false" || b === "0") return ok("false");
      return fail(`'${s}' is not true or false for column ${column}.`);
    }
    case "text": return ok(s);
    default: return fail(`Column ${column} can't be filtered — its type can't be compared.`);
  }
}
export function range(category, lo, hi, column) {
  const a = filterValue(category, lo, column);
  if (!a.ok) return a;
  const b = filterValue(category, hi, column);
  if (!b.ok) return b;
  const inverted = category === "numeric" ? a.value > b.value : category === "temporal" ? a.value > b.value : false;
  return inverted ? fail(`From must be less than or equal to To for column ${column}.`) : ok([a.value, b.value]);
}
```

**`Core/api.js`** — export `errorMessage` and use it in `request` and `exportCsv`:

```js
export function errorMessage(status, data) {
  if (data && typeof data.error === "string" && data.error) return data.error;
  if (data && typeof data.title === "string" && data.title) return data.title;
  return status >= 500 ? `Server error (${status}).` : `Request failed (${status}).`;
}
function httpError(status, data) {
  const e = new Error(errorMessage(status, data));
  e.status = status; e.field = data?.field ?? null;
  return e;
}
```

In `request`, wrap the fetch: `try { res = await fetch(BASE + url, opts); } catch (e) { if (e?.name === "AbortError") throw e; throw new Error("Can't reach the server — check your network and try again."); }`
and on `!res.ok` `throw httpError(res.status, data);`. `exportCsv` does the same.

**`Core/ui.js`** — the toast gets a text span + close button; only non-danger toasts auto-hide:

```js
export function toast(message, kind = "info") {
  const el = document.getElementById("toast");
  if (!el) return;
  const text = document.createElement("span");
  text.className = "toast__text"; text.textContent = message;
  const close = makeButton("×", "toast__close");
  close.setAttribute("aria-label", "Dismiss");
  close.addEventListener("click", () => hide(el));
  el.replaceChildren(text, close);
  el.className = `toast toast--${kind}`;
  show(el);
  clearTimeout(toastTimer);
  if (kind !== "danger") toastTimer = setTimeout(() => hide(el), 5000);
}
let fieldErrorSeq = 0;
/** Mark a field invalid with an inline message under it; cleared on the next edit. */
export function fieldError(input, message) {
  clearFieldError(input);
  const msg = document.createElement("p");
  msg.className = "field-error"; msg.id = `field-error-${++fieldErrorSeq}`;
  const glyph = document.createElement("span");
  glyph.className = "field-error__icon"; glyph.setAttribute("aria-hidden", "true"); glyph.textContent = "⚠";
  msg.append(glyph, document.createTextNode(" " + message));
  input.setAttribute("aria-invalid", "true");
  input.setAttribute("aria-describedby", msg.id);
  input.insertAdjacentElement("afterend", msg);
  input.addEventListener("input", () => clearFieldError(input), { once: true });
}
export function clearFieldError(input) {
  const id = input.getAttribute("aria-describedby");
  if (id) document.getElementById(id)?.remove();
  input.removeAttribute("aria-invalid"); input.removeAttribute("aria-describedby");
}
/** Apply a validate.js result to a field: the value when ok, else undefined (and the field is marked). */
export function checkField(input, result) {
  if (result.ok) { clearFieldError(input); return result.value; }
  fieldError(input, result.error);
  return undefined;
}
/** A titled list of issues with one OK button. */
export function listDialog(title, items) {
  return new Promise((resolve) => {
    const dlg = document.createElement("dialog");
    dlg.className = "dialog dialog--sm";
    const h = document.createElement("h2"); h.className = "dialog__title"; h.textContent = title;
    const ul = document.createElement("ul"); ul.className = "dialog__list";
    for (const it of items) { const li = document.createElement("li"); li.textContent = it; ul.append(li); }
    const foot = document.createElement("div"); foot.className = "dialog__foot";
    const okBtn = makeButton("OK", "btn btn--primary"); foot.append(okBtn);
    dlg.append(h, ul, foot); document.body.append(dlg);
    const finish = () => { closeDialog(dlg); resolve(); };
    okBtn.addEventListener("click", finish);
    dlg.addEventListener("cancel", (e) => { e.preventDefault(); finish(); });
    openDialog(dlg);
  });
}
```

**`Shell/app.js`** — first lines after the imports (import `toast` from `../Core/ui.js`):

```js
// Last-resort handlers: an unexpected error is told to the user, never only logged. Aborted queries are normal.
window.addEventListener("error", (e) => { console.error(e.error ?? e.message); toast("Something went wrong — try again.", "danger"); });
window.addEventListener("unhandledrejection", (e) => {
  if (e.reason?.name === "AbortError") return;
  console.error(e.reason); toast("Something went wrong — try again.", "danger");
});
```

**Connection form.** `_Connection.cshtml`: Port becomes `type="text" inputmode="numeric" maxlength="5"`;
add `maxlength="253"` (host), `"64"` (user), `"256"` (password). `connection.js` submit handler:

```js
const fields = { host: hostEl, port: portEl, user: userEl, password: passEl };
const values = {
  host: checkField(hostEl, host(hostEl.value)),
  port: checkField(portEl, port(portEl.value)),
  user: checkField(userEl, text(userEl.value, { label: "User", max: LIMITS.user, required: true })),
  password: checkField(passEl, text(passEl.value, { label: "Password", max: LIMITS.password, trim: false })),
};
const firstBad = Object.values(fields).find((i) => i.getAttribute("aria-invalid") === "true");
if (firstBad) { firstBad.focus(); return; }
const payload = { ...values, secure: secureEl.checked, allowInvalidCert: secureEl.checked && allowCertEl.checked };
```

In its `catch`, show a server field error at the field: `if (err.field && fields[err.field]) fieldError(fields[err.field], err.message); else toast(err.message, "danger");`.
Delete the old "Host and user are required." toast. Import `host, port, text, LIMITS` from `../Core/validate.js`.

- [ ] **Step 4: Run** `$NODE --test tests/js/*.test.mjs` and `$NODE --check` on each changed module — expected PASS. jsdom: submit with host `h:8443` → `#conn-host` has `aria-invalid="true"` and a linked `.field-error`; typing clears it.
- [ ] **Step 5: Checkpoint.** Next: [Task 6](plan-client-b.md#task-6-data-model-inputs-and-tab-names).
