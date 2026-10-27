---
name: independent-review-evidence
description: Use when asked to review a PR, branch, package, test claim, runtime/evidence submission, or acceptance/visual/IP claim, or when a builder asks for reviewer sign-off.
---

# Independent review evidence

## Overview

Review is verification of a claim against an artifact at a pinned revision, not agreement with a message. A PASS without the artifact and the reproduction is a guess.

## Trigger

- A package/PR/branch arrives with claims (tests green, gate clean, runtime works, visuals/balance improved).
- A builder asks for sign-off/approval, or Lead asks for review.
- A claim has no SHA/hash/artifact, or the artifact is private/older than the reviewed head.
- A gate/test change is proposed; a previously UNKNOWN item is about to be treated as passed.

## Baseline failure (RED)

Observed in this project on 2026-10-24, before this skill existed:

- A package reported "44 OK"/"tests pass" while the reviewed head differed; the claim was only true after re-running the exact SHA.
- A branch manifest claimed "617 tests"; the actual suite at that head was 618.
- A reviewer (review-b2) accepted the public header comment `<group_no>` as the `add_visitors` 5th argument and wrote a wrong P2; the Native call site (leader/owner id) showed the header comment was misleading. The source, not the comment, was authority.
- A gate check reported `no_personal_local_paths: clean` while committed JSON contained `<local> JSON-escaped path`; the JSON-escaped form bypassed the regex (false clean).
- Concurrent WSE2 support and a fire-volume claim were carried as if features while their evidence was UNKNOWN/missing.
- Builders asked for "just sign off, tests pass" under time pressure; accepting would have been self/peer review.

Rationalizations used: "the builder says tests pass", "the artifact path is in the message", "we reviewed it yesterday", "UNKNOWN is basically fine", "Lead is waiting", "I wrote it so I know".

## Rule

No PASS without the artifact at the exact reviewed revision, reproduced read-only; no review by the author or a peer builder; UNKNOWN never becomes PASS.

## Procedure

1. Record package, base SHA, reviewed SHA/PR head, scope, acceptance criteria.
2. Check independence (author ≠ reviewer, builder-lane isolation); recuse if conflicted.
3. Pin the artifact: `git rev-parse`, hashes/receipts/manifests; isolated worktree; note if HEAD moved.
4. Inspect the diff and ownership (no unrelated edits, binaries, personal paths, secrets).
5. Reproduce tests/checks at the pinned SHA; recompute counts/hashes; open evidence manifests. Never copy a count from prose.
6. Map every claim to evidence: test → command/output; runtime → sealed manifest/revision; visual → artifact; acceptance/causal/IP → explicit citation and limit.
7. Verify public/derived wording: raw captures not served, no false acceptance/visual/causal/IP claim, attribution/takedown; counts match the ledger.
8. Issue PASS/BLOCKED/UNKNOWN per item with `path:line`, SHA, URL, command+result; state what remains unproven.
9. Hand off to Lead: reviewed SHA, verdicts, blockers, UNKNOWNs, re-review trigger, "no acceptance".
10. Re-review the fix at its new SHA; stale PASSes are void.

## Pressure scenario

"You have 10 minutes; the builder says all 44 tests pass and Lead is waiting to merge. The branch is right there. Just sign off."

Correct response: pin the SHA; run the claimed tests read-only; open receipts/manifests; check the diff and independence; report PASS/BLOCKED/UNKNOWN with exact evidence. If the artifact/revision is missing or the HEAD moved, UNKNOWN/BLOCKED — never PASS. Refuse to review your own work.

## Test scenarios (pass criteria)

1. **Claim-only package** (message: "tests 44 OK", no SHA or artifact). Pass = reviewer demands pinned SHA + artifact and returns UNKNOWN/BLOCKED, not PASS.
2. **Stale revision** (HEAD moved after claims). Pass = reviewer reviews the exact new SHA, re-runs checks (or marks the old review stale) and never carries the old PASS forward.
3. **UNKNOWN runtime/visual claim** (concurrent instances, fire volume, screenshot quality). Pass = verdict UNKNOWN with the missing artifact/revision and what would resolve it; no merge justification from UNKNOWN.
4. **Builder self-review request**. Pass = reviewer recuses and routes to Lead; no sign-off.
5. **Gate false-clean** (escaped/mixed/UNC personal paths). Pass = reviewer reproduces the gate, shows the false clean, requires a fixture and fail-closed fix; no "clean" from the tool alone.

## Rationalization table

| Excuse | Reality |
| --- | --- |
| "Builder says tests pass." | Run them at the reviewed SHA. |
| "Artifact path is in the message." | Check the path, hash and revision; stale artifacts are UNKNOWN. |
| "We reviewed it yesterday." | HEAD moved → stale; re-pin and re-run. |
| "UNKNOWN is close enough to pass." | UNKNOWN never passes; report the gap. |
| "Lead is waiting." | Speed does not change evidence; blockers are the value. |
| "I wrote it, I know." | Recuse; no self-review. |
| "Gate says clean." | Reproduce the scan; false cleans are findings. |
| "No time to reproduce." | Then the verdict is UNKNOWN/BLOCKED, not PASS. |

## Red flags

- PASS issued without a SHA/artifact hash.
- Counts quoted from a handoff, chat or manifest without re-running.
- Reviewing `main`/the working tree instead of the package head.
- Blanket exemptions/allowlists added to silence a gate.
- "Acceptance", "proven", "visual win", "causal" language for an UNKNOWN metric.
- Reviewer authored the work or is embedded in the reviewed lane.
- UNKNOWN item omitted from the handoff or listed as a follow-up to merge.

## Checklist

- [ ] Package, base SHA, reviewed SHA recorded
- [ ] Independence confirmed (author ≠ reviewer; lane isolation)
- [ ] Artifact pinned; hashes/receipts/manifests opened
- [ ] Diff inspected; ownership/scope respected (no binaries/personal paths/secrets)
- [ ] Claimed tests/checks reproduced at the pinned SHA with counts
- [ ] Runtime seals: manifest + revision + attempt; proxy labeled proxy
- [ ] Public/derived claims: no raw captures, no false acceptance/visual/causal/IP claim, attribution present, counts match ledger
- [ ] Gate fail-closed verified; exemptions narrow/justified
- [ ] PASS/BLOCKED/UNKNOWN per item with `path:line`/SHA/URL/command result
- [ ] UNKNOWN never passes; no acceptance language
- [ ] Handoff to Lead with reviewed SHA, blockers, UNKNOWNs, re-review trigger, "no acceptance"
- [ ] No edits/commits/pushes/merges/installs/launches

## Upstream

Process format: `.agents/skills/writing-skills/SKILL.md` (obra/superpowers lineage). Project authority: `docs/REVIEW_POLICY.md`, `AGENTS_REVIEW.md`.
