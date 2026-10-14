# Tabs — Data Model + dashboards

The view strip across the top of the content area. Code: `Features/Tabs/` (`tabs.js`, `tabs.css`) over
the shared state in `Core/store.js`. Why one shared model:
[D12](../reference/decisions.md#d12--subtabs-are-dashboards-over-one-shared-data-model).

## The strip

- Tabs are frosted pills (tier-2 glass controls): the active tab has an accent fill, edge and underline and bold text. A pinned **Data Model** tab (`.tab--model`) — the shared entity canvas ([canvas.md](canvas.md) +
  [relationships.md](relationships.md)). It cannot be closed.
- One tab per **dashboard**; each dashboard **is one worksheet** ([worksheet.md](worksheet.md)).
- `[+]` (`.tab-add`) adds a dashboard.
- **Rename:** double-click a dashboard label, or focus it and press `F2` (or `Enter` on the active
  tab), to edit inline (`.tab__rename`, `maxlength` 60). The name is trimmed and must be 1–60
  characters; an empty name reverts and toasts "Tab name is required." Keyboard focus returns to the
  tab's label afterwards. Clicking the tab that is already open does nothing, and the double-click
  listener sits on the strip (`#tabs`), not the label — every switch rebuilds the strip, so a label-level
  listener would lose the double-click.
- The close icon (`.tab__close`, `aria-label` "Close <name>") closes a dashboard — with a confirm dialog when it holds content.
- The active tab carries `aria-current`.

## How views switch

- `store.activeView` is the model or a dashboard id. `canvas.js` / `relations.js` render `#model-view`
  when the model is active; `dashboards.js` renders the active dashboard into `#dashboard-view`.
- Each module shows/hides its own view on `view:changed`; the strip redraws on `tabs:changed`.
- All dashboards build from the **same** entities and relationships — a table added while on a
  dashboard still lands in the shared model.

## Persistence

Tabs, entities, relationships and worksheets are saved as the browser **workbook** and restored on
reconnect. The strip's right end holds the quiet autosave text and one **Workbook** overflow menu
(Import / Export) — [workbook.md](workbook.md).
