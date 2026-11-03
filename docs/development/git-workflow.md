---
components: []
---
# Merge to `main`

A standing authorisation to merge finished work into `main` without asking. It applies to the
Dashboard Builder **app repo only** and does not carry over to any other repo, including this KB repo.

## Do

1. Wait until the suites in [review-guidelines.md](review-guidelines.md#verification) are green (or a
   failing test or error has been fixed and they are green again).
2. Merge the work branch into `main` locally, with no separate go-ahead.
3. Run the suites again on the merged result.
4. Remove the worktree and delete the merged branch.

## Stop and ask instead

- The main tree has uncommitted changes that overlap the merge — never stash or commit the user's work
  without asking.
- The branch is protected, or a remote or team flow exists.
- The change goes beyond what the branch was for.

**Never push.**
