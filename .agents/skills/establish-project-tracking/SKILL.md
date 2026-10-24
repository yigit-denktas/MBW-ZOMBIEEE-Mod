---
name: establish-project-tracking
description: Use when a new project needs a project overview, scoped plan, roadmap, progress tracker, or governance setup, including a repository that already has a README or website but no established tracking authority.
---

# Establish project tracking

Start from the project's intended outcome. Tracking records the discovered work; installing a dashboard alone does not establish the plan.

Locate repository instructions and a pinned Project Record Standard checkout (`src/project_record`, `standards/`). Set `PROJECT_RECORD_TOOLKIT` to that checkout. Read `standards/START-HERE.md` and `standards/PMI-ALIGNMENT.md` there.

Read the installed sibling `use-project-records/references/readiness-contract.md`. During scouting, produce the evidence-backed L0–L5 assessment and task-risk R0–R4 authority record using its template. Keep the detailed assessment in the configured central store; link it from overview/adoption with date, revision, current/target level, blockers and next review. Ask about unresolved target/delegation/environment decisions after inspection. Select bounded readiness remediation alongside product work; grade and completion percentages remain separate. Installation grants no autonomy.

Produce these artifacts in order:

| Artifact | Required contents |
| --- | --- |
| `progress/overview.md` | Purpose, users, value, what works, included/excluded scope, success/acceptance criteria, accountable owner, constraints and unresolved decisions. Attribute inferred scope as proposed. |
| `progress/discovery.json` | Inventory docs, existing trackers, issues, PRs, local/remote branches, releases, website and generated ownership. For each: source/revision, observation, complete/partial/inaccessible/not-applicable coverage, findings and retrieval gaps. Use connected GitHub tools with pagination; local Git alone cannot establish hosted coverage. |
| `progress/adoption.md` | Authority per field, brand/routes, stable-ID mapping, cleanup queue, sequence, verification and rollback. Rank cleanup by active-outcome blockage, safety/data loss, dependencies, then value and effort. Link stale PRs/branches for review; age alone does not authorize deletion or closure. |
| Authored ledger/manifest | Outcome → deliverables → WBS work packages → distinct accounting leaves; milestones are checkpoints, roadmap is their horizon/dependency view. Every leaf has one owner of accounting, criterion and primary milestone. Link shared prerequisites. Keep discovery ideas outside required scope until selected. |

If established tracking exists, use **adapt-project-tracking**. If only `.git`, a README or site exists, stage the scaffold and merge only absent tracking files. This example runs from the target project root after setting the toolkit variable:

```sh
set -eu
stage=$(mktemp -d)
PYTHONPATH="$PROJECT_RECORD_TOOLKIT/src" python3 -m project_record init --directory "$stage" --id loomglass --name Loomglass --owner Sam --observed-on 2026-10-22
test ! -e progress
test ! -L progress
cp -R "$stage/progress" ./progress
PYTHONPATH="$PROJECT_RECORD_TOOLKIT/src" python3 -m project_record check --config progress/project-record.json
```

Prepare overview/discovery before this copy; merge reviewed planning artifacts afterward. Empty scope is **0/0, Not measured**, private and unapproved. Populate only evidence-backed/proposed scope, tailor governance with **govern-project-scope**, then validate and compare counts. Use **connect-github-tracking**, **present-project-tracking** and **operate-project-tracking** for authorized integrations, public review and ongoing operation. Preview `install-skills` before applying its additive AGENTS installation.

Handoff the artifact paths, toolkit/contract identities, source coverage, named fractions, unresolved decisions, exact checks, completed/pending steps and next owner/action. If evidence is unavailable, finish independent local work and keep the affected gate pending.

Common mistakes: running `init` over an existing repository; treating an empty scaffold as a finished plan; copying a shared visual skin; making source gaps disappear behind zero counts.
