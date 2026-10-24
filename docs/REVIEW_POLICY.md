# Review policy (owner directive, 2026-10-24)

## Fixed reviewers
Only two fixed members review:
- **review-b2** — independent read-only reviewer.
- **agent-e** — claims, legal/IP, evidence and acceptance-boundary reviewer.

## Builders
- **agent-a** — AI/combat/builds
- **agent-c** — telemetry/probes/tooling
- **agent-d** — runtime/harness/seals
- **agent-f** — launcher/release/site
- **agent-g-assets** — assets/licences
- **agent-h-bannerlord** — research
- **Lead** — coordination, installs, merges; does not self-review.

## Rules
1. Builders do **not** evaluate each other's work and do not self-approve.
2. Reviewers do not build features; they review, verify claims, and report blockers.
3. Builders keep building the next small package while a previous package waits for review.
4. Every package submitted with: branch/PR + SHA, scope, acceptance criteria, tests, receipt/evidence, known gaps.
5. Lead merges only after reviewer sign-off; merge is not acceptance.
6. Reviewer comments must distinguish PASS / BLOCKED / UNKNOWN; UNKNOWN never passes.
7. No review by the author; no review by a builder on another builder's lane.
