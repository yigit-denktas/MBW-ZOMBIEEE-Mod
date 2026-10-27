# AGENTS_REVIEW.md — fixed-reviewer book

Load this when asked to review a package, branch/PR, test claim, runtime/evidence submission, public claim, or acceptance/IP wording. Reviewing is read-only verification, not building.

Authority: `docs/REVIEW_POLICY.md`. Only the two fixed reviewers exist — **review-b2** (independent read-only reviewer) and **agent-e** (claims, legal/IP, acceptance boundary). Builders never review themselves or each other. Lead merges only after reviewer sign-off; a merge is not acceptance.

## Scope

- Review the artifact at an exact revision: repo, base SHA, reviewed SHA/PR head. A review of a moving tree is not a review.
- You may read, diff, hash, run read-only tests/checks, create an isolated worktree, and inspect private local evidence. You may not edit, commit, push, merge, install, launch the game, or change GitHub state.
- No reviewer sign-off for your own work or for a builder you are embedded with; recuse and route to Lead.
- Findings distinguish **PASS / BLOCKED / UNKNOWN**. UNKNOWN never passes; absent proof is not a pass.

## Assumptions

- Authored sources are authority; README, Pages and generated counters are derived views.
- Every claim needs an artifact and a revision. Test counts, runtime seals, receipts, screenshots, ledger counts and release metadata are claims until verified.
- Private evidence (`local/`, sealed bundles) is referenced by path/hash; it is never published or committed.
- A gate that fails closed is doing its job; a red gate on a feature checkout is reported, not exempted.
- Builder handoffs may be honest but incomplete; verify, do not trust or accuse.

## Procedure

1. **Confirm authorization and target.** Package name, branch/PR, base SHA, reviewed SHA, scope, acceptance criteria, tests, receipt/evidence, gaps (from the builder handoff). If no pinned SHA, review is UNKNOWN.
2. **Check independence.** Author ≠ reviewer; not the builder's lane; if conflict, stop and tell Lead.
3. **Pin the artifact.** Record exact SHA(s) and file hashes; create an isolated read-only worktree when branches differ. Note if the tree moved during review (review is stale).
4. **Inspect the diff and its blast radius.** Changed files, generated files, tests, docs, release metadata. Check the diff stays inside the package's ownership and includes no binaries, personal paths, secrets or unrelated edits.
5. **Reproduce the claims read-only.** Run the claimed tests/checks at that SHA; recompute hashes/counts; open the sealed manifest/receipt; compare docs/ledger/release metadata against the measured values. Do not accept a count or PASS from prose.
6. **Audit public/claim boundaries.** Derived-only wording; no raw captures/assets served; no acceptance, visual, causal or IP claim beyond evidence; attribution/takedown; no personal paths in public files; gate fail-closed behavior.
7. **Write findings with exact evidence.** `path:line`, SHA, URL, command + result, and what remains unproven. Separate facts from interpretation.
8. **Issue per-item verdicts.** PASS/BLOCKED/UNKNOWN with one-line reason and evidence. UNKNOWN items never justify merge.
9. **Hand off to Lead.** Reviewed SHA, verdicts, blockers, unresolved UNKNOWNs, required re-review trigger (new HEAD), and explicitly: no acceptance.
10. **Re-review only the fix.** Pin the new HEAD; re-run affected checks; do not restate stale PASSes for an old SHA.

## Verdict discipline

| Verdict | Means | Evidence required | Effect |
| --- | --- | --- | --- |
| **PASS** | The claimed behavior/check was reproduced at the reviewed SHA, within stated limits | Exact SHA + artifact + reproduced check/output; no unresolved P0/P1 | May recommend merge; still not acceptance |
| **BLOCKED** | A defect, missing artifact, unsafe behavior, weakened test or failed claim in the reviewed artifact | Exact path/line or artifact hash + reproduction | Do not merge; return to builder |
| **UNKNOWN** | Not established: no artifact, stale revision, unverifiable runtime/visual/causal claim, or missing permission | What is missing and what would resolve it | Never merge as if passed; report as gap |

Rules: never promote UNKNOWN to PASS because a builder says so; never downgrade BLOCKED because Lead is waiting; no "PASS with follow-ups" for P0/P1; P2 may pass with explicit follow-up; every verdict names the SHA it applies to.

## Evidence and claim checks

- **Identity**: artifact hash/receipt/manifest present and bound to the reviewed SHA; no hash copied from an older build.
- **Tests**: claimed command and counts reproduced at that SHA; skips explained; no tests deleted/weakened/exempted to force green; new negative fixtures where a gate/guard changed. Missing runtime evidence remains UNKNOWN.
- **Release metadata**: source revision/CHANGELOG/README/ledger agreement with reviewed HEAD; a head-revision guard failing is reported, not waived; metadata-only claims verified against the actual diff.
- **Runtime/evidence**: sealed manifest (file list + hashes) + revision + attempt; `runtime_verified=false` preserved unless real acceptance exists; proxy metrics labeled proxy; no causal claim from correlation.
- **Public claims**: derived-only wording; no raw gameplay captures/assets published; no false acceptance/visual/causal/IP claims; attribution and takedown present; counts match the ledger at the reviewed revision.
- **Safety/scanning**: no personal absolute paths (including JSON-escaped/mixed-separator/UNC forms), no secrets/binaries; exemptions narrow and justified, not blanket hides.
- **Scope**: package stays in its lane; no mass merges; no edits to other lanes' files; merge is one reviewed package at a time.

## Handoff to Lead

Report: package/branch, base SHA, reviewed SHA, verdict per item (PASS/BLOCKED/UNKNOWN), blockers with exact evidence, unresolved UNKNOWNs, tests/checks run + counts, re-review condition, and "no acceptance". Keep it short enough to act on; do not bury blockers. Lead owns merge/install; reviewer owns the evidence record.

## Hard rules

- No self-review, no builder-on-builder review.
- No edits/commits/pushes/merges/installs/launches while reviewing.
- No PASS without artifact + exact revision + read-only reproduction.
- UNKNOWN never passes; a red gate is a finding, not something to exempt.
- No acceptance or "done" language; done ≠ accepted.
- Review the current artifact, not yesterday's; when HEAD moves, the old review is stale.
- If scope, acceptance, IP/publication or destructive cleanup is ambiguous, stop and ask Lead/owner.

## File map

| Path | Use in review |
| --- | --- |
| `AGENTS.md`, `AGENTS_LEAD.md`, `AGENTS_TESTING.md`, `AGENTS_TRACKER.md` | Assignment, lead/merge rules, test/gate order, tracker discipline |
| `docs/REVIEW_POLICY.md` | Fixed-reviewer authority and PASS/BLOCKED/UNKNOWN rules |
| `.agents/skills/independent-review-evidence/SKILL.md` | Review-mistake prevention skill |
| `handoffs/AGENT_*.md`, `handoffs/*CONTRACT*.md`, `handoffs/CITY_ACCEPTANCE.json` | Builder handoffs, contracts, acceptance gates |
| `progress/ledger.json`, `progress/project-record.json`, `progress/snapshots/` | Authoritative counts, acceptance state, history |
| `progress/live-status.json`, `progress/publish-meta.json` | Current status and published-ledger binding |
| `docs/release-traceability.json`, `CHANGELOG.md`, `VERSION`, `README.md` | Release claims and their revision binding (README derived) |
| `site/index.html`, gh-pages publish set | Public/derived claims, raw-asset and attribution checks |
| `reference/` | Research/evidence sources, licences, triage reports |
| `tests/`, `tools/`, `launcher/`, `installer/`, `overlay/lua/`, `telemetry/`, `builds/`, `configs/` | Code/tests/packages under review |
| `docs/` | Contracts, acceptance ledgers, runbooks, diagnostics |
| `archive/` | Frozen branch tips and archive manifests (recovery) |
| `local/`, `evidence/` | Private, gitignored evidence; verify by path/hash, never publish |
