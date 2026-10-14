# P24 plan — Task 8 (part 2): `board.css`, `board.js`

Part of the [P24 plan](plan-overview.md); read its Global Constraints first, the harness contract in
[plan-board.md](plan-board.md) and Task 8's Files / Interfaces / Steps 1–6 in [plan-board-2.md](plan-board-2.md).
Spec: [§ Canvas](../p24-dashboards.md#canvas), [§ Rendering and data](../p24-dashboards.md#rendering-and-data).

### Task 8 (continued)

- [ ] **Step 7: `Features/Board/board.css`** — tokens only; visibility by `hidden`:

```css
/* Board — a dashboard tab (P24b): the worksheet list beside a 12-column snap grid of widgets. The canvas
   grows downward and scrolls inside .bd-scroll (the page never scrolls). */
.view--board { padding: 0; }
.board { display: grid; grid-template-columns: 220px 1fr; height: 100%; min-height: 0; }
.bd-side { display: flex; flex-direction: column; gap: var(--s3); min-height: 0; overflow: auto; padding: var(--s3) var(--s4);
  border-right: 1px solid var(--line); background: color-mix(in srgb, var(--surface), var(--ink) 2%); }
.bd-side__title { margin: 0; font-size: var(--fs-xs); font-weight: 700; color: var(--ink-2); }
.bd-side__hint, .bd-sheets__none { margin: 0; font-size: var(--fs-xs); color: var(--ink-3); }
.bd-sheets { display: grid; gap: var(--s1); margin: 0; padding: 0; list-style: none; }
.bd-sheet { display: flex; align-items: center; gap: var(--s2); padding: var(--s1) var(--s2); border-radius: var(--r-ctl); font-size: var(--fs-sm); cursor: grab; }
.bd-sheet:hover { background: var(--surface-3); } .bd-sheet__name { flex: 1; min-width: 0; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.bd-sheet__add { height: 28px; padding: 0 var(--s2); font-size: var(--fs-xs); }
.bd-main { display: flex; flex-direction: column; min-width: 0; min-height: 0; }
.bd-bar { flex: none; display: flex; align-items: center; gap: var(--s2); padding: var(--s2) var(--s5); border-bottom: 1px solid var(--line); }
.bd-status { flex: 1; min-width: 0; margin: 0; font-size: var(--fs-xs); color: var(--ink-2); }
.bd-scroll { position: relative; flex: 1; min-height: 0; overflow: auto; padding: var(--s5); }
.bd-canvas { --bd-row: calc(var(--ctl-h) * 2); position: relative; display: grid; grid-template-columns: repeat(12, minmax(0, 1fr));
  grid-auto-rows: var(--bd-row); gap: var(--s3); min-height: calc(var(--bd-rows, 8) * (var(--bd-row) + var(--s3))); }
.bd-empty { position: absolute; inset: var(--s5); display: grid; place-content: center; gap: var(--s2); text-align: center;
  color: var(--ink-2); border: 1px dashed var(--line-2); border-radius: var(--r); pointer-events: none; }
.bd-widget { position: relative; display: flex; flex-direction: column; min-width: 0; min-height: 0; background: var(--surface);
  border: 1px solid var(--line); border-radius: var(--r); box-shadow: var(--elev-2); }
.bd-widget.is-dragging { z-index: 2; opacity: .85; box-shadow: var(--elev-16); }
.bd-widget__head { flex: none; display: flex; align-items: center; gap: var(--s2); min-height: var(--ctl-h);
  padding: 0 var(--s1) 0 var(--s3); border-bottom: 1px solid var(--line); color: var(--ink-3); cursor: grab; touch-action: none; }
.bd-widget__title { flex: 1; min-width: 0; margin: 0; overflow: hidden; text-overflow: ellipsis; white-space: nowrap;
  font-size: var(--fs-sm); font-weight: 600; color: var(--ink); }
.bd-widget__actions { display: flex; gap: 2px; } .bd-widget__btn { width: 28px; height: 28px; color: var(--ink-3); }
.bd-widget__body { position: relative; flex: 1; min-height: 0; display: flex; flex-direction: column; overflow: auto; }
.bd-widget__chart { padding: var(--s2); }  /* .ws-chart supplies flex, positioning and the table styles */
.bd-widget__notice { margin: var(--s2) var(--s2) 0; }
.bd-widget__resize { position: absolute; right: 0; bottom: 0; width: 16px; height: 16px; cursor: nwse-resize; touch-action: none;
  border-bottom-right-radius: var(--r); background: linear-gradient(135deg, transparent 50%, var(--line-2) 50%); }
.bd-text { margin: 0; padding: var(--s2) var(--s3); white-space: pre-wrap; overflow-wrap: anywhere; color: var(--ink); }
.bd-text.is-empty { color: var(--ink-3); font-style: italic; }
.bd-textedit { display: grid; gap: var(--s2); padding: var(--s2) var(--s3); }
.bd-textedit__body { min-height: 72px; resize: vertical; } .bd-textedit__foot { display: flex; justify-content: flex-end; gap: var(--s2); }
.bd-ghost { z-index: 1; display: flex; align-items: center; justify-content: center; gap: var(--s1); pointer-events: none;
  border: 2px dashed var(--accent); border-radius: var(--r); background: var(--accent-soft); color: var(--accent-ink); font-size: var(--fs-xs); font-weight: 600; }
.bd-ghost.is-invalid { border-color: var(--danger-line); background: var(--danger-bg); color: var(--danger-ink); }
.bd-ghost:not(.is-invalid) .bd-ghost__icon { display: none; }
@media (pointer: coarse) { .bd-widget__btn { min-width: 44px; min-height: 44px; } .bd-widget__resize { width: 28px; height: 28px; } }
@media (max-width: 760px) { .board { grid-template-columns: 1fr; grid-template-rows: auto 1fr; }
  .bd-side { max-height: 30vh; border-right: 0; border-bottom: 1px solid var(--line); } }
```

  The core `[tabindex]:focus-visible` ring marks a focused widget.

- [ ] **Step 8: `Features/Board/board.js`.**

```js
// Board/board.js — a dashboard tab (P24b): the worksheet list and a 12-column snap grid of worksheet and text
// widgets (move / resize by pointer or keys; undo / redo per dashboard). Only the active dashboard renders;
// leaving it disposes every widget's view, so showing it again runs each worksheet's current sheet (Review
// Focus #1). Grid math: board-layout.js; pointer work: board-drag.js; drawing: Dashboard/worksheet-view.js.
import { bus, activeBoard, tabById, worksheetList, updateBoard, switchTab, nextWidgetId } from "../Core/store.js";
import { GRID, DEFAULT_SIZE, firstFree, moveBy, resizeBy } from "./board-layout.js";
import { wireDrag, keyStep, gridArea } from "./board-drag.js";
import { createWorksheetView } from "../Dashboard/worksheet-view.js";
import { createHistory } from "../Dashboard/history.js";
import { icon } from "../Core/icons.js";
import { toast, checkField, makeButton } from "../Core/ui.js";
import { text, LIMITS } from "../Core/validate.js";
import { enter, MOTION } from "../Core/motion.js";

const SHEET_MIME = "application/x-dashboardbuilder-sheet";
const el = (tag, cls, txt) => { const e = document.createElement(tag); if (cls) e.className = cls; if (txt != null) e.textContent = txt; return e; };

export function initBoard() {
  const view = document.getElementById("board-view");
  if (!view) return;
  const $ = (id) => document.getElementById(id);
  const listEl = $("bd-sheets"), canvas = $("bd-canvas"), ghost = $("bd-ghost"), emptyEl = $("bd-empty");
  const statusEl = $("bd-status"), undoBtn = $("bd-undo"), redoBtn = $("bd-redo"), scroller = $("bd-scroll");
  const history = createHistory(); // dashboard id → snapshots of its widgets
  const live = new Map();          // widget id → { el, head, title, body, edit, remove, kind, sheetId?, view?, chartEl?, ro? }
  let shown = null;                // the dashboard on screen
  let editing = null;              // the text widget whose editor is open

  bus.addEventListener("view:changed", sync);
  bus.addEventListener("dashboard:changed", (e) => { if (e.detail?.id === shown) render(); });
  bus.addEventListener("tabs:changed", () => { if (shown) { renderList(); render(); } }); // renames
  bus.addEventListener("worksheet:changed", (e) => rerun((it) => it.sheetId === e.detail?.id));
  for (const type of ["fields:changed", "parameters:changed"]) bus.addEventListener(type, () => rerun(() => true));
  undoBtn.addEventListener("click", () => step("undo"));
  redoBtn.addEventListener("click", () => step("redo"));
  document.addEventListener("keydown", (e) => {
    if (!(e.ctrlKey || e.metaKey) || view.hidden) return;
    if (e.target.closest?.("input, textarea, select, [contenteditable='true'], dialog")) return; // the field's own undo
    const k = e.key.toLowerCase();
    if (k === "z" && !e.shiftKey) { e.preventDefault(); step("undo"); }
    else if ((k === "z" && e.shiftKey) || k === "y") { e.preventDefault(); step("redo"); }
  });
  $("bd-add-text").addEventListener("click", () => addWidget({ kind: "text", heading: "Heading", body: "" }, true));
  scroller.addEventListener("dragover", (e) => { if (e.dataTransfer.types.includes(SHEET_MIME)) { e.preventDefault(); e.dataTransfer.dropEffect = "copy"; } });
  scroller.addEventListener("drop", (e) => { const id = e.dataTransfer.getData(SHEET_MIME); if (id) { e.preventDefault(); addWidget({ kind: "sheet", sheetId: id }); } });
  // (Task 9: presentation — full screen, print, theme)
  sync();

  function sync() {
    const board = activeBoard(), was = shown;
    view.hidden = !board;
    if (!board || board.id !== shown) disposeAll();
    shown = board?.id ?? null;
    if (!board) return;
    renderList(); render();
    if (was && was !== shown) enter(canvas, { y: 4, duration: MOTION.view }); // dashboard → dashboard
  }
  function disposeAll() { for (const it of live.values()) drop(it); live.clear(); editing = null; ghost.hidden = true; statusEl.textContent = ""; }
  function drop(it) { it.ro?.disconnect(); it.view?.dispose(); it.el.remove(); }
  function rerun(pred) { if (shown) for (const it of live.values()) if (it.view && pred(it)) run(it); }
  function run(it) { const ws = tabById(it.sheetId); if (ws?.kind === "worksheet") it.view.run(ws.sheet, ws.id); }
  function say(msg) { statusEl.textContent = msg; }
  function widgetOf(id) { return activeBoard()?.widgets.find((w) => w.id === id) ?? null; }

  // Keyed: new widgets are built (a worksheet one runs its view), gone ones disposed, kept ones only re-placed.
  function render() {
    const board = activeBoard();
    if (!board || board.id !== shown) return;
    const ids = new Set(board.widgets.map((w) => w.id));
    for (const [id, it] of live) if (!ids.has(id)) { drop(it); live.delete(id); }
    const used = Math.max(0, ...board.widgets.map((w) => w.y + w.h));
    canvas.style.setProperty("--bd-rows", String(Math.min(GRID.maxRows, Math.max(8, used + 4)))); // room below to drop
    for (const w of board.widgets) {
      let it = live.get(w.id);
      if (!it) { it = build(w); live.set(w.id, it); canvas.append(it.el); if (it.view) run(it); }
      it.el.style.gridArea = gridArea(w);
      label(it, w);
      if (w.kind === "text" && editing !== w.id) showText(it, w);
    }
    emptyEl.hidden = board.widgets.length > 0;
    undoBtn.disabled = !history.canUndo(board.id); redoBtn.disabled = !history.canRedo(board.id);
  }

  function build(w) {
    const node = el("section", `bd-widget bd-widget--${w.kind}`);
    node.tabIndex = 0; node.setAttribute("role", "group"); node.dataset.id = w.id;
    const head = el("header", "bd-widget__head"), title = el("h2", "bd-widget__title"), actions = el("div", "bd-widget__actions");
    const edit = iconBtn("edit"), remove = iconBtn("close");
    actions.append(edit, remove);
    head.append(icon(w.kind === "text" ? "label" : "chart-bar", { size: 14 }), title, actions);
    const body = el("div", "bd-widget__body"), handle = el("span", "bd-widget__resize");
    handle.title = "Drag to resize (or Shift+arrow keys with the widget focused)";
    node.append(head, body, handle);
    const it = { el: node, head, title, body, edit, remove, kind: w.kind };
    edit.addEventListener("click", () => { const cur = widgetOf(w.id); if (cur?.kind === "sheet") switchTab(cur.sheetId); else if (cur) openEditor(it, cur); });
    remove.addEventListener("click", () => commit((ws) => ws.filter((x) => x.id !== w.id), `${title.textContent} removed.`));
    node.addEventListener("keydown", (e) => onKey(e, w.id));
    wireDrag({ node, head, handle, canvas, ghost, id: w.id, widgets: () => activeBoard()?.widgets ?? [],
      onCommit: (rect) => commitRect(w.id, rect), onReject: refuse });
    if (w.kind === "sheet") {
      // The worksheet's own failure / hint text renders in this pane — inside the widget, siblings untouched.
      const notice = el("p", "ws-chart-notice bd-widget__notice"), chart = el("div", "ws-chart bd-widget__chart");
      notice.hidden = true; notice.setAttribute("role", "status");
      body.append(notice, chart);
      Object.assign(it, { sheetId: w.sheetId, chartEl: chart, view: createWorksheetView({ chartEl: chart, noticeEl: notice, interactive: false }) });
      let frame = 0; // the chart follows its cell box without re-querying (Review Focus #5)
      it.ro = new ResizeObserver(() => { cancelAnimationFrame(frame); frame = requestAnimationFrame(() => it.view?.resize()); });
      it.ro.observe(chart);
    }
    return it;
  }
  function iconBtn(name) { const b = makeButton("", "iconbtn bd-widget__btn"); b.append(icon(name, { size: 14 })); return b; }

  function label(it, w) {
    const name = w.kind === "sheet" ? tabById(w.sheetId)?.name ?? "Missing worksheet" : w.heading || "Text";
    const kind = w.kind === "sheet" ? "worksheet" : "text";
    it.title.textContent = name;
    it.edit.setAttribute("aria-label", `Edit ${kind} ${name}`); it.edit.title = w.kind === "sheet" ? "Edit — open the worksheet" : "Edit text";
    it.remove.setAttribute("aria-label", `Remove ${name} from the dashboard`); it.remove.title = "Remove from the dashboard";
    it.el.setAttribute("aria-label", `${name} (${kind}), columns ${w.x + 1}–${w.x + w.w}, rows ${w.y + 1}–${w.y + w.h}. Arrows move, Shift+arrows resize.`);
  }
  function showText(it, w) {
    it.body.replaceChildren(el("p", `bd-text${w.body ? "" : " is-empty"}`, w.body || "No text yet — choose Edit to write some."));
  }

  // Inline text editor. No maxLength: an over-long entry is reported under its field, never cut (rule 3).
  function openEditor(it, w) {
    editing = w.id;
    const form = el("form", "bd-textedit"), foot = el("div", "bd-textedit__foot");
    const heading = el("input", "input"); heading.value = w.heading; heading.setAttribute("aria-label", "Heading");
    const body = el("textarea", "input bd-textedit__body"); body.value = w.body; body.setAttribute("aria-label", "Text");
    const cancel = makeButton("Cancel", "btn"), save = makeButton("Save", "btn btn--primary"); save.type = "submit";
    foot.append(cancel, save); form.append(heading, body, foot);
    it.body.replaceChildren(form); heading.focus();
    const close = () => { editing = null; render(); it.el.focus(); };
    cancel.addEventListener("click", close);
    form.addEventListener("keydown", (e) => { if (e.key === "Escape") { e.preventDefault(); close(); } });
    form.addEventListener("submit", (e) => {
      e.preventDefault();
      const h = checkField(heading, text(heading.value, { label: "Heading", max: LIMITS.heading }));
      const b = checkField(body, text(body.value, { label: "Text", max: LIMITS.body, trim: false }));
      if (h === undefined || b === undefined) return;
      const cur = widgetOf(w.id);
      editing = null;
      if (cur && (cur.heading !== h || cur.body !== b)) commit((ws) => ws.map((x) => (x.id === w.id ? { ...x, heading: h, body: b } : x)));
      else render();
      it.el.focus();
    });
  }

  // Every layout / text change: one undo step, then updateBoard → dashboard:changed → render().
  function commit(change, msg) {
    const board = activeBoard();
    if (!board) return;
    history.record(board.id, board.widgets);
    updateBoard(board.id, change(structuredClone(board.widgets)));
    if (msg) say(msg);
  }
  function commitRect(id, r) { commit((ws) => ws.map((x) => (x.id === id ? { ...x, x: r.x, y: r.y, w: r.w, h: r.h } : x))); }
  function refuse(mode) { say(`Can't ${mode} there — it would overlap another widget or leave the grid, so it stayed put.`); }
  function onKey(e, id) {
    if (e.target !== e.currentTarget) return; // keys typed in the text editor
    const s = keyStep(e), board = activeBoard();
    if (!s || !board) return;
    e.preventDefault();
    const r = s.resize ? resizeBy(board.widgets, id, s.dx, s.dy) : moveBy(board.widgets, id, s.dx, s.dy);
    if (r) commitRect(id, r); else refuse(s.resize ? "resize" : "move");
  }
  function step(which) {
    const board = activeBoard();
    const target = board && history[which](board.id, board.widgets);
    if (!target) return;
    // Review Focus #3: a worksheet closed since that snapshot is gone — never resurrect a widget onto it.
    const kept = target.filter((w) => w.kind !== "sheet" || tabById(w.sheetId)?.kind === "worksheet");
    if (kept.length < target.length) say("A widget whose worksheet was closed can't come back.");
    updateBoard(board.id, kept);
  }

  function addWidget(spec, openText = false) {
    const board = activeBoard();
    if (!board || (spec.kind === "sheet" && tabById(spec.sheetId)?.kind !== "worksheet")) return;
    if (board.widgets.length >= GRID.maxWidgets) { toast(`A dashboard holds at most ${GRID.maxWidgets} widgets — remove one first.`, "info"); return; }
    const { w, h } = DEFAULT_SIZE[spec.kind], at = firstFree(board.widgets, w, h);
    if (!at) { toast("The canvas is full — remove or shrink a widget to make room.", "info"); return; }
    const id = nextWidgetId();
    commit((ws) => [...ws, { id, ...spec, x: at.x, y: at.y, w, h }], `${spec.kind === "sheet" ? tabById(spec.sheetId).name : "Text"} added.`);
    const it = live.get(id);
    if (!it) return;
    enter(it.el, { y: 4 });
    if (openText) openEditor(it, widgetOf(id)); else it.el.focus();
  }

  function renderList() {
    const sheets = worksheetList();
    listEl.replaceChildren(...(sheets.length ? [] : [el("li", "bd-sheets__none", "No worksheets yet — add one with + in the tab bar.")]));
    for (const ws of sheets) {
      const li = el("li", "bd-sheet"), add = makeButton("Add", "btn bd-sheet__add");
      li.draggable = true;
      add.prepend(icon("plus", { size: 14 }));
      add.setAttribute("aria-label", `Add ${ws.name} to the dashboard`);
      add.addEventListener("click", () => addWidget({ kind: "sheet", sheetId: ws.id }));
      li.addEventListener("dragstart", (e) => { e.dataTransfer.setData(SHEET_MIME, ws.id); e.dataTransfer.effectAllowed = "copy"; });
      li.append(icon("chart-bar", { size: 14 }), el("span", "bd-sheet__name", ws.name), add);
      listEl.append(li);
    }
  }
}
```

- [ ] **Step 9: GREEN.** `node --check` on `board.js`, `board-drag.js`, `app.js`; the JS suite; `dotnet test`;
  the harness in light and dark — `board-render`, `board-edit`, `tab-kinds` and every earlier check PASS.
  `grep -n "style.display\|#[0-9a-fA-F]\{3,6\}\b" src/DashboardBuilder/Features/Board/*` → none. Screenshot an
  arranged dashboard (two charts + a heading) in light and dark for the user.

- [ ] **Step 10: Commit.** `git add -A && git commit` — message `Add the Board: dashboards of worksheet and text
  widgets on a snap grid (P24b)`, ending with the `Co-Authored-By` line.

Next: [Task 9 — full screen, print, theme, bookmarks](plan-present.md).
