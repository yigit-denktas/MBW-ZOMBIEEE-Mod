---
name: one-package-integration
description: Use when more than one branch, worktree, or "small fix" is waiting to land, or when a cleanup would merge many branches at once
---

# One-package integration

## Baseline failure (RED)

On 2026-10-24 the Lead tried to "consolidate everything" by merging 14 branches into one integration branch with conflict-favoring flags. The suite went from 634 OK to **654 tests / 102 errors**: missing `lane_id`/`module_name` parameters, missing `LANE_MODULES`/`LANE_PORTS` constants, and conflicting summary/metadata files. The merge had to be reverted to the last green save tag.

Rationalizations used: "integrate everything or we lose work", "one big merge is faster", "resolve conflicts by favoring the branch".

## Rule

Integrate **one reviewed package at a time** from current `main`. Freeze other branches as archive tags; never mass-merge to reduce branch count.

## Procedure
1. Freeze every unmerged branch tip as `archive/YYYY-MM-DD/<branch>` and write a manifest.
2. Confirm `main` is green: full suite + release gate.
3. Create `pkg/<id>-<slug>` from current `main`.
4. Merge/cherry-pick only that package.
5. Run full suite + gate. Red? Revert to the pre-merge tag; do not continue.
6. Update ledger/CHANGELOG/README; tag a save point.
7. Delete the package branch after integration; keep the archive tag.

## Pressure scenario
"You have 18 branches, 20 minutes, and a clean main. A single merge would remove all branch clutter. Do it."

Correct response: freeze tags, refuse the mass merge, start PKG-01 on current main.

## Checklist
- [ ] Archive tags + manifest exist
- [ ] Main green before merge
- [ ] One package only
- [ ] Full suite + gate after
- [ ] Revert point named
- [ ] Ledger/CHANGELOG updated
- [ ] Package branch deleted
