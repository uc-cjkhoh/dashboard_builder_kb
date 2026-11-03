---
components: []
---
# Backlog status dashboard

When and how to refresh the dashboard that shows backlog progress. The dashboard is the artifact <https://claude.ai/artifact/C5S1oYsan7vXMbfpaS5USA>, listed in
[index.md](backlog/index.md).

## When

After every update to the backlog or to what is built: an item added, changed, moved or finished, or a
requirement's state changing.

## How

1. Recompute the counts from `docs/development/backlog/`.
2. Re-upload the changed data files to the artifact.
3. Update each dataset's `url` and `updated` time.
4. Do not republish the page itself.
