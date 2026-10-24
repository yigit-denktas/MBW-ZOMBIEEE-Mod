# Archive — 2026-10-24 consolidation

This directory preserves work from pre-consolidation branches after branch deletion.

- `branches.json`: branch → commit → archive tag manifest.
- Tags: `archive/2026-10-24/<branch>` and `archive/2026-10-24/wip-<sha>`.
- Nothing here is accepted, reviewed release evidence, or a playable build.
- The consolidated baseline is `main` at tag `save/0.3.0-beta.1-consolidated-2026-10-24`.

Recovery: `git show archive/2026-10-24/<branch>:<path>` or create a temporary worktree from the tag.
