# P34 plan — Design A: tokens, glass, components, dark mode (Task 9)

Part of the [P34 plan](plan-overview.md). Paths are relative to `src/DashboardBuilder/Features/`.
Spec reference: [A1 — Visual system](../p34-fluent-glass-redesign.md#a1--visual-system).

### Task 9: Replace the token system; restyle shared components; light + dark

**Files:** Modify `Core/core.css` (`:root`, keyframes, shared components), every feature `*.css` (token
re-pointing), `Dashboard/dashboard.css` + `Shell/shell.css` (stray `#fff`), `Dashboard/chart.js` (fallbacks),
`Dashboard/dashboards.js` (theme re-render). Test: a token-hygiene check (Step 1).

**Interfaces:**
- Produces tokens used by every later task: `--bg --surface --surface-2 --surface-3 --glass --glass-line
  --ink --ink-2 --ink-3 --line --line-2 --accent --accent-hover --accent-pressed --accent-ink --accent-soft
  --accent-line --on-accent --on-ink --ok-* --warn-* --danger-bg --danger-ink --danger-line --danger-solid
  --dim-* --meas-* --enc-* --chart-* --font --fs-* --s1…--s7 --r-ctl --r --r-lg --r-pill --ctl-h
  --elev-2 --elev-8 --elev-16 --elev-28 --dur-fast --dur --dur-slow --ease --ease-out`; utility class `.glass`.

- [ ] **Step 1: Write the failing check** — save as `tests/js/tokens.test.mjs`:

```js
import { test } from "node:test";
import assert from "node:assert/strict";
import { readFileSync, readdirSync } from "node:fs";
const root = new URL("../../src/DashboardBuilder/Features/", import.meta.url);
const css = readdirSync(root, { recursive: true }).filter((f) => f.endsWith(".css")).map((f) => [f, readFileSync(new URL(f, root), "utf8")]);
const RETIRED = /var\(--(brand|side-|pend-|info-|glow|hi\)|surface-grad|head-grad|motion|ease-back|elev-1\)|elev-3\)|shadow\)|r-sm\)|danger-soft)/;
test("no retired token is referenced", () => { for (const [f, t] of css) assert.doesNotMatch(t, RETIRED, f); });
test("no hex colour outside the :root token blocks", () => {
  for (const [f, t] of css) {
    const outside = t.replace(/:root[^{]*\{[^}]*\}/g, "");
    assert.doesNotMatch(outside, /#[0-9a-fA-F]{3,8}\b/, f);
  }
});
test("dark mode redefines the surfaces", () => {
  const core = css.find(([f]) => f.endsWith("core.css"))[1];
  assert.match(core, /@media \(prefers-color-scheme: dark\)\s*\{\s*:root\s*\{[^}]*--surface:/);
});
```

- [ ] **Step 2: Run** `$NODE --test tests/js/tokens.test.mjs` — expected FAIL (retired tokens everywhere).

- [ ] **Step 3: Re-point every token use, by meaning.** Run this **before** replacing the `:root` block
  (old `--elev-2` becomes new `--elev-8`, so the order matters):

```bash
cd src/DashboardBuilder/Features
sed -i -E \
  -e 's/--elev-2\b/--elev-8/g' -e 's/--elev-1\b/--elev-2/g' -e 's/--elev-3\b/--elev-28/g' -e 's/var\(--shadow\)/var(--elev-8)/g' \
  -e 's/var\(--glow-brand(-sm)?\)/var(--elev-2)/g' -e 's/, var\(--hi\)//g' \
  -e 's/--brand-strong/--accent-hover/g' -e 's/--brand-ink/--accent-ink/g' -e 's/--brand-soft/--accent-soft/g' \
  -e 's/--brand-grad/--accent/g' -e 's/--brand\b/--accent/g' \
  -e 's/--danger-soft/--danger-bg/g' -e 's/--pend-/--warn-/g' -e 's/--info-(bg|ink|line)/--enc-\1/g' \
  -e 's/--side-ink/--ink/g' -e 's/--side-muted/--ink-3/g' -e 's/--side-line/--line/g' \
  -e 's/--side-elev-grad|--side-elev/--surface-2/g' -e 's/--side-grad|--side-bg/--glass/g' \
  -e 's/--surface-grad|--head-grad/--surface/g' -e 's/--motion-slow/--dur-slow/g' -e 's/--motion\b/--dur/g' \
  -e 's/--ease-back/--ease-out/g' -e 's/--r-sm\b/--r-ctl/g' \
  */*.css Dashboard/chart.js
```

  Then fix the **danger contexts** the bulk rename sent to the accent:
  `grep -n "danger" */*.css | grep -- "--accent"` — each hit (e.g. `.iconbtn--danger:hover`,
  `.toast--danger`) uses `--danger-solid` / `--danger-ink` / `--danger-bg` instead. Replace the five stray
  `#fff`: on `--accent` backgrounds use `var(--on-accent)`; on `--enc-ink`/`--warn-ink` backgrounds use
  `var(--on-ink)`. In `chart.js` change the `--chart-series` fallback `"#cc0000"` to `"#2563eb"`.

- [ ] **Step 4: Replace the `:root` block and keyframes in `core.css`** with:

```css
:root {
  color-scheme: light dark;
  /* Surfaces & ink */
  --bg: #eef2f7; --surface: #ffffff; --surface-2: #f6f8fb; --surface-3: #eef2f7;
  --glass: rgb(255 255 255 / .68); --glass-line: rgb(15 23 42 / .08);
  --ink: #0f172a; --ink-2: #334155; --ink-3: #64748b; --line: #e2e8f0; --line-2: #cbd5e1;
  /* One accent; red means danger only */
  --accent: #2563eb; --accent-hover: #1d4ed8; --accent-pressed: #1e40af; --accent-ink: #1d4ed8;
  --accent-soft: #eff4ff; --accent-line: #bfd3fe; --on-accent: #ffffff; --on-ink: var(--surface);
  --ok-bg: #ecfdf3; --ok-ink: #067647; --ok-line: #abefc6;
  --warn-bg: #fffaeb; --warn-ink: #93370d; --warn-line: #fedf89;
  --danger-bg: #fef3f2; --danger-ink: #b42318; --danger-line: #fecdca; --danger-solid: #d92d20;
  /* Field roles (pills) */
  --dim-bg: var(--accent-soft); --dim-ink: var(--accent-ink); --dim-line: var(--accent-line);
  --meas-bg: #ecfeff; --meas-ink: #0e7490; --meas-line: #a5f3fc;
  --enc-bg: #f4f3ff; --enc-ink: #5925dc; --enc-line: #d9d6fe;
  --up: var(--ok-ink); --down: var(--danger-ink);
  /* Charts */
  --chart-series: var(--accent); --chart-axis: var(--line-2); --chart-grid: var(--line);
  --chart-label: var(--ink-2); --chart-muted: var(--ink-3);
  --chart-cat-1: #2a78d6; --chart-cat-2: #008300; --chart-cat-3: #e87ba4; --chart-cat-4: #eda100;
  --chart-cat-5: #1baf7a; --chart-cat-6: #eb6834; --chart-cat-7: #4a3aa7; --chart-cat-8: #e34948;
  /* Background wash — gives the glass something to blur */
  --wash: radial-gradient(1200px 800px at 85% -10%, color-mix(in srgb, var(--accent) 8%, transparent), transparent 60%),
          radial-gradient(900px 700px at -10% 110%, color-mix(in srgb, #14b8a6 6%, transparent), transparent 60%);
  /* Type, space, shape, depth, motion */
  --font: "Segoe UI Variable Text", "Segoe UI", -apple-system, BlinkMacSystemFont, system-ui, sans-serif;
  --fs-xs: 12px; --fs-sm: 13px; --fs-body: 14px; --fs-lead: 16px; --fs-title: 20px; --fs-kpi: 30px;
  --s1: 4px; --s2: 8px; --s3: 12px; --s4: 16px; --s5: 20px; --s6: 24px; --s7: 32px;
  --r-ctl: 4px; --r: 8px; --r-lg: 12px; --r-pill: 999px; --ctl-h: 32px; --sidebar-w: 264px;
  --elev-2: 0 1px 2px rgb(15 23 42 / .06), 0 0 2px rgb(15 23 42 / .06);
  --elev-8: 0 4px 8px rgb(15 23 42 / .08), 0 0 2px rgb(15 23 42 / .06);
  --elev-16: 0 8px 16px rgb(15 23 42 / .10), 0 0 2px rgb(15 23 42 / .06);
  --elev-28: 0 14px 28px rgb(15 23 42 / .16), 0 0 8px rgb(15 23 42 / .08);
  --dur-fast: 150ms; --dur: 200ms; --dur-slow: 250ms;
  --ease: cubic-bezier(.33, 0, .67, 1); --ease-out: cubic-bezier(.1, .9, .2, 1);
}
@media (prefers-color-scheme: dark) {
  :root {
    --bg: #0b1220; --surface: #111a2b; --surface-2: #162133; --surface-3: #1c2940;
    --glass: rgb(17 26 43 / .66); --glass-line: rgb(255 255 255 / .08);
    --ink: #e2e8f0; --ink-2: #cbd5e1; --ink-3: #94a3b8; --line: #1f2a3d; --line-2: #2b3a52;
    --accent-ink: #93c5fd; --accent-soft: rgb(59 130 246 / .16); --accent-line: rgb(59 130 246 / .4);
    --ok-bg: rgb(23 178 106 / .14); --ok-ink: #75e0a7; --ok-line: rgb(23 178 106 / .4);
    --warn-bg: rgb(247 144 9 / .14); --warn-ink: #fec84b; --warn-line: rgb(247 144 9 / .4);
    --danger-bg: rgb(240 68 56 / .14); --danger-ink: #fda29b; --danger-line: rgb(240 68 56 / .4); --danger-solid: #f04438;
    --meas-bg: rgb(6 182 212 / .14); --meas-ink: #67e8f9; --meas-line: rgb(6 182 212 / .4);
    --enc-bg: rgb(122 90 248 / .16); --enc-ink: #bdb4fe; --enc-line: rgb(122 90 248 / .4);
    --chart-cat-1: #4d95ea; --chart-cat-2: #3ba55c; --chart-cat-3: #f08fb6; --chart-cat-4: #f5b83d;
    --chart-cat-5: #2ec48c; --chart-cat-6: #f2834f; --chart-cat-7: #9d8cf2; --chart-cat-8: #f26b6a;
    --elev-2: 0 1px 2px rgb(0 0 0 / .4); --elev-8: 0 4px 8px rgb(0 0 0 / .4);
    --elev-16: 0 8px 16px rgb(0 0 0 / .45); --elev-28: 0 14px 28px rgb(0 0 0 / .55);
  }
}
@supports not ((backdrop-filter: blur(1px)) or (-webkit-backdrop-filter: blur(1px))) { :root { --glass: var(--surface-2); } }
@media (prefers-reduced-transparency: reduce) { :root { --glass: var(--surface-2); } }
```

  Keep the reduced-motion block (rename `--motion*` → `--dur*`). Delete keyframes `sheen`, `shimmer`,
  `dot-pulse`, `pulse-ring`, `entity-in`; keep `fade-in`, `rise-in`, `toast-in`, `dialog-in`, `spin`.
  Load the **dataviz** skill and run its palette validator on the dark `--chart-cat-*` against `#111a2b`;
  adjust any slot it flags before moving on. Check every ink/background pair above for ≥ 4.5:1 (text) in
  both themes; adjust the ink, not the background, if one fails.

- [ ] **Step 5: Restyle the shared components** — replace the matching rules in `core.css`:

```css
body { background: var(--bg) var(--wash) fixed; color: var(--ink); font: var(--fs-body)/1.45 var(--font); }
.glass { background: var(--glass); border: 1px solid var(--glass-line);
  -webkit-backdrop-filter: blur(24px) saturate(160%); backdrop-filter: blur(24px) saturate(160%); }
:where(button, input, select, textarea, a, [tabindex]):focus-visible { outline: 2px solid var(--accent); outline-offset: 2px; }
.btn { display: inline-flex; align-items: center; gap: var(--s2); height: var(--ctl-h); padding: 0 var(--s3);
  border: 1px solid var(--line-2); border-radius: var(--r-ctl); background: var(--surface); color: var(--ink);
  font-size: var(--fs-sm); font-weight: 600; cursor: pointer; transition: background var(--dur-fast) var(--ease), border-color var(--dur-fast) var(--ease); }
.btn:hover { background: var(--surface-3); }
.btn:disabled { opacity: .5; cursor: default; }
.btn--primary { background: var(--accent); border-color: var(--accent); color: var(--on-accent); }
.btn--primary:hover { background: var(--accent-hover); border-color: var(--accent-hover); }
.btn--primary:active { background: var(--accent-pressed); }
.btn--danger { background: transparent; border-color: var(--danger-line); color: var(--danger-ink); }
.btn--danger:hover { background: var(--danger-bg); }
.iconbtn { display: inline-grid; place-items: center; width: var(--ctl-h); height: var(--ctl-h); border: 0; border-radius: var(--r-ctl);
  background: transparent; color: var(--ink-2); cursor: pointer; transition: background var(--dur-fast) var(--ease), color var(--dur-fast) var(--ease); }
.iconbtn:hover { background: var(--surface-3); color: var(--ink); }
.iconbtn--danger:hover { background: var(--danger-bg); color: var(--danger-ink); }
.input, .select { height: var(--ctl-h); padding: 0 var(--s3); border: 1px solid var(--line-2); border-radius: var(--r-ctl);
  background: var(--surface); color: var(--ink); font: inherit; font-size: var(--fs-sm); transition: border-color var(--dur-fast) var(--ease); }
.input:hover, .select:hover { border-color: var(--ink-3); }
.input:focus, .select:focus { outline: none; border-color: var(--accent); box-shadow: inset 0 -2px 0 var(--accent); }
.input[aria-invalid="true"], .select[aria-invalid="true"] { border-color: var(--danger-solid); box-shadow: inset 0 -2px 0 var(--danger-solid); }
.field-error { display: flex; gap: var(--s1); margin-top: var(--s1); color: var(--danger-ink); font-size: var(--fs-xs); }
.pill { display: inline-flex; align-items: center; gap: var(--s1); height: 22px; padding: 0 var(--s2);
  border: 1px solid transparent; border-radius: var(--r-pill); font-size: var(--fs-xs); font-weight: 600; }
.pill--muted { background: var(--surface-2); color: var(--ink-3); border-color: var(--line); }
.pill--warn { background: var(--warn-bg); color: var(--warn-ink); border-color: var(--warn-line); }
.toast { position: fixed; left: 50%; bottom: var(--s6); transform: translateX(-50%); z-index: 100; display: flex; align-items: center;
  gap: var(--s3); max-width: min(560px, calc(100vw - 2 * var(--s4))); padding: var(--s3) var(--s2) var(--s3) var(--s4);
  border-radius: var(--r); box-shadow: var(--elev-16); color: var(--ink); animation: toast-in var(--dur-slow) var(--ease-out); }
.toast, .dialog { background: var(--glass); border: 1px solid var(--glass-line);
  -webkit-backdrop-filter: blur(24px) saturate(160%); backdrop-filter: blur(24px) saturate(160%); }
.toast--ok { border-left: 3px solid var(--ok-ink); } .toast--info { border-left: 3px solid var(--accent); }
.toast--danger { border-left: 3px solid var(--danger-solid); }
.toast__close { border: 0; background: transparent; color: var(--ink-3); width: 24px; height: 24px; border-radius: var(--r-ctl); cursor: pointer; }
.toast__close:hover { background: var(--surface-3); color: var(--ink); }
.dialog { padding: 0; border-radius: var(--r-lg); color: var(--ink); box-shadow: var(--elev-28); animation: dialog-in var(--dur-slow) var(--ease-out); }
.dialog::backdrop { background: color-mix(in srgb, var(--bg) 45%, transparent); backdrop-filter: blur(4px); }
.dialog__title { padding: var(--s4) var(--s4) 0; font-size: var(--fs-lead); font-weight: 600; }
.dialog__list { margin: var(--s3) 0 0; padding: 0 var(--s4) 0 var(--s7); max-height: 50vh; overflow: auto; color: var(--ink-2); font-size: var(--fs-sm); }
.dialog__foot { border-top: 0; padding: var(--s4); }
```

  Delete `.btn--primary::after` / `:hover::after` (sheen), `.btn:hover` / `.iconbtn:hover` transforms, and
  every rule now duplicated by the block above. Keep `.pill--ok`, `.pill--danger`, scrollbar rules (their
  tokens are already re-pointed).

- [ ] **Step 6: Re-render charts on a theme change.** In `dashboards.js`, next to the `bus` listeners (~line 219):

```js
// chart.js reads colours from :root at render time — redraw when the OS theme flips (a cache hit, no query).
matchMedia("(prefers-color-scheme: dark)").addEventListener("change", () => { if (!isModelActive()) runChart(); });
```

- [ ] **Step 7: Run** `$NODE --test tests/js/*.test.mjs` (tokens test now PASSES), `dotnet build`, then start the
  dev server (overview § conventions) and fetch `/features/Core/core.css` with curl to confirm it serves.
- [ ] **Step 8: Checkpoint.** Next: [Task 10](plan-design-b.md#task-10-icon-set).
