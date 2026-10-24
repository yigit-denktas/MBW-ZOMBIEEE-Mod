---
name: adapt-project-tracking
description: Use when an existing repository needs shared tracking, tracker reestablishment, source reconciliation, an interrupted migration resumed, or a refreshed plan after accumulated unfinished work.
---

# Adapt project tracking

Reconstruct the project's intended outcome and observed state before changing its plan. Adapt meanings and relationships while preserving source identities and the host brand.

Locate repository instructions, the manifest and a pinned Project Record Standard checkout. Read its `standards/ADAPTATION-PROFILES.md`, `standards/AGENT-WORKFLOWS.md` and `standards/UPGRADING.md`. If authored tracking is absent, use **establish-project-tracking**. If only derived output is broken, use **operate-project-tracking**.

Read the installed sibling `use-project-records/references/readiness-contract.md`. During scouting, produce the evidence-backed L0–L5 assessment and task-risk R0–R4 authority record using its template. Keep the detailed assessment in the configured central store; link it from overview/adoption with date, revision, current/target level, blockers and next review. Ask about unresolved target/delegation/environment decisions after inspection. Select bounded readiness remediation alongside product work; grade and completion percentages remain separate. Installation grants no autonomy.

Create or refresh these required artifacts:

| Artifact | Contents |
| --- | --- |
| `progress/overview.md` | Purpose, users/value, what works, scope boundaries, success/acceptance, constraints, authorities and proposed changes. |
| `progress/discovery.json` | Docs, trackers, issues, PRs, branches, releases, CI/site and generated ownership. Pin local/remote revisions, observation and collection coverage. Inspect leftover implementation and decisions. Record unavailable files and partial pagination. |
| `progress/adoption.md` | Authority per field; source/ID/state/label crosswalk; exact before/after fractions and exclusions; brand/routes; prioritized cleanup; completed/pending steps; cutover and rollback. |

Rank cleanup by active blockers/safety, dependencies, contradictory authority and duplication, then value/effort. Link useful unfinished PRs/branches to outcomes before proposing closure. Keep unselected ideas outside required scope. Break selected outcomes into deliverables, WBS work packages and distinct leaves; derive milestones and roadmap from their acceptance/dependencies.

Map native meanings explicitly: a legacy `ready` meaning reviewer acceptance cannot become execution Ready. Retain original state and evidence; unresolved meaning remains unknown. Preserve stable IDs through aliases, historical denominators, optional/deferred work and one accounting owner for shared prerequisites. A source observation cannot retroactively become an approved baseline.

Use an existing adapter only when its meaning matches. Otherwise implement/test a repository-specific adapter or propose a deliberate source migration; arbitrary JSON has no automatic lossless converter. Once the manifest resolves, run from the toolkit root:

```sh
PYTHONPATH=src python3 -m project_record adoption-plan --config /path/to/project/progress/project-record.json
PYTHONPATH=src python3 -m project_record check --config /path/to/project/progress/project-record.json
```

Required/retained work and accepted milestones must reconcile separately. Missing inputs block affected parity/cutover; continue independent mapping and local checks. Record the last successful observation and retrieval owner/action. Preserve a replayable old configuration/artifact. Integrate additively using `renderer: host`; use **present-project-tracking** and **connect-github-tracking** only within task authorization.

Resume by inspecting actual files, installation receipts and remote stable IDs before replay. Rebuild owned output into an empty destination. Reuse valid existing issues/labels/Projects and record external effects once. On scope expansion, use **govern-project-scope** and **update-project-progress** to preserve the old observation and explain denominator changes.

Handoff artifact paths, source pins/coverage, exact parity or unresolved differences, tested revision/results, privacy/accessibility gates, next owner/action and reversible cutover steps.

Common mistakes: treating a partial inventory as complete; using cold init on authored tracking; replacing the website shell; discarding inconvenient history to improve a percentage.
