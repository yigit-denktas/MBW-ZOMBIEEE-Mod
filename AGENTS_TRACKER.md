# AGENTS_TRACKER.md

Load for ledger, issue, PR, milestone, snapshot, README/Pages, or release-metadata work.

## Authoritative vs derived
- Authoritative: `progress/ledger.json`, `progress/project-record.json`, snapshots in `progress/snapshots/`.
- Derived: README/Pages, generated counters, release-traceability metadata.
- Never hand-edit generated percentages. Preserve snapshots before scope changes.

## Required discipline
1. Every real fix gets a card, even small ones. Add evidence (revision/artifact/result/gap).
2. Distinguish **done** from **accepted**. Required outcomes stay 8/23 until real acceptance; accepted milestones 0/5.
3. Keep stable IDs; never recycle. Active/review earns no partial credit.
4. Scope growth uses `govern-project-scope`; preserve previous source file/history.
5. Run `project_record check/build/readme` before claiming tracker health.
6. Snapshot the ledger before structural changes.
7. Publish only `site/index.html`, `progress/ledger.json`, `progress/live-status.json`, `progress/publish-meta.json` to gh-pages; never README/CHANGELOG.
8. `progress/publish-meta.json` must match the published ledger hash/count and source SHA. Staleness must be visible.
9. Issue/PR hygiene: close completed issues with exact evidence; archive branch tips as tags before branch deletion; no orphan PRs.

## Installed project-record block

<!-- project-record:agents:start -->
## Project tracking agent rules

Read the matching skill before tracking work. Discover project purpose, scope, existing authority and local instructions first. Use the project’s terminology aliases and brand.

| Workflow skill | Instructions |
| --- | --- |
| establish-project-tracking | `.agents/skills/establish-project-tracking/SKILL.md` |
| adapt-project-tracking | `.agents/skills/adapt-project-tracking/SKILL.md` |
| update-project-progress | `.agents/skills/update-project-progress/SKILL.md` |
| answer-project-status | `.agents/skills/answer-project-status/SKILL.md` |
| govern-project-scope | `.agents/skills/govern-project-scope/SKILL.md` |
| connect-github-tracking | `.agents/skills/connect-github-tracking/SKILL.md` |
| prepare-project-delivery | `.agents/skills/prepare-project-delivery/SKILL.md` |
| present-project-tracking | `.agents/skills/present-project-tracking/SKILL.md` |
| operate-project-tracking | `.agents/skills/operate-project-tracking/SKILL.md` |
| use-project-records | `.agents/skills/use-project-records/SKILL.md` |
| verify-project-accessibility | `.agents/skills/verify-project-accessibility/SKILL.md` |

Treat authored sources as authority and README/Pages as derived views. Scout docs, issues, PRs, branches, releases and existing trackers before planning a setup or scope expansion. Record inaccessible sources and observation dates.
Keep stable IDs and one accounting owner per leaf. Use named fractions and the toolkit calculators. Preserve snapshots when scope grows. A rebuild does not refresh source observation or award acceptance.
Run record checks and relevant project checks before reporting completion. Preserve evidence subject and revision. Keep unavailable acceptance tests pending. Review public output and protect project-owned files.
Tracking work alone does not authorize deployment, credentials, GitHub changes or changes to another repository. Follow authorization already provided for the task.

Skill suite identity: `6fc2a9f5a89f9163ea3a2e744a01c3e838b85894e0aa374173a6230986520405`. Installation ownership: `.project-record/agent-installation.json`.
<!-- project-record:agents:end -->
