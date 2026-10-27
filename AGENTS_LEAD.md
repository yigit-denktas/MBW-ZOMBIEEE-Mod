# AGENTS_LEAD.md — operator book

Load this only when coordinating. Testing details: `AGENTS_TESTING.md`. Tracking: `AGENTS_TRACKER.md`.

## Session start
1. `git status`, branch/worktree inventory, `progress/live-status.json`, ledger counts.
2. Check active WSE2 processes before any install/kill.
3. Read the current package's target, tests, reviewer, and stop condition before touching main.
4. No mass branch merges. If several branches exist, archive them as tags first, then integrate one reviewed package.

## Operating loop
1. Write the package target and acceptance criteria.
2. A builder implements on `pkg/<id>-<slug>` from current `main`.
3. Run targeted tests; then full suite + release gate.
4. Fixed reviewer checks artifact/revision/evidence; PASS/BLOCKED/UNKNOWN.
5. Lead integrates only after sign-off; update ledger/CHANGELOG/README; tag save point.
6. Delete the package branch after integration; work remains recoverable by tag.

## Hard rules
- Never install while a WSE2 session is active.
- Never merge all branches to "clean up"; that is how the 102-error integration happened.
- Never label done as accepted.
- Never edit generated percentages by hand.
- If a suite goes red after a merge, revert to the last green save tag before further edits.
- Archive before deleting: `archive/YYYY-MM-DD/<branch>` tags + manifest.

## Handoffs
Builders hand reviewer: branch/SHA, scope, tests, receipt/evidence, gaps. Reviewer hands Lead: PASS/BLOCKED/UNKNOWN + exact artifact. Lead hands owner: what works, what is unverified, what decision is needed.

## When to stop
Stop and ask the owner when scope, acceptance, IP/publication, or destructive cleanup is ambiguous. Do not invent acceptance or durations.

## Recovery
Last green baseline: `save/0.3.0-beta.1-consolidated-2026-10-24`. Archived branches: `archive/2026-10-24/*` (manifest in `archive/2026-10-24/branches.json`). Recovery: create a temporary worktree from the archive tag; never resurrect all branches.
