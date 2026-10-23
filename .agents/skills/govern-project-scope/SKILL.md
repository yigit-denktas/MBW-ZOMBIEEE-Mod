---
name: govern-project-scope
description: Use when a project's purpose, scope, work breakdown, milestones, roadmap, cleanup priorities, baseline, risks or operating responsibilities must be established or changed as work expands.
---

# Govern project scope

Keep the project overview, scoped work and decision authority connected. Progressive discovery changes the plan through visible revisions.

Read repository instructions, existing governance and the pinned toolkit's `standards/PMI-ALIGNMENT.md`, `standards/AGENT-WORKFLOWS.md` and `src/project_record/governance.py`. This is a tailored implementation of public PMI guidance, not certification or a licensed-standard conformance assessment.

| Governance slot | Required content |
| --- | --- |
| Overview | Purpose/value, users/stakeholders, current capabilities, included/excluded scope, success criteria, constraints, accountable owner and acceptance/change authorities. |
| Discovery/triage | Relevant docs/trackers, issues, PRs, branches and delivery evidence with coverage/date. Cleanup ordered by active blockers/safety, dependencies, conflicting authority, then value/effort. |
| Work breakdown | Outcomes/deliverables → WBS work packages → distinct leaves with criteria/owner/evidence; link shared prerequisites once. Declare complete, partial or unassessed WBS coverage. |
| Planning views | Milestone checkpoints with exit gates; roadmap horizons/dependencies and sourced targets versus commitments. Issues/PRs are delivery packages, not extra accounting credit. |
| Decisions | Observed/proposed/approved baselines and scope changes with reasons, impact and actual attributed authority evidence. |
| Risks/operations | Uncertain event, owner, response, intervention trigger, state; continuing service owner, incident/support route, observability, recovery and handover. |

Tailor governance, scope, schedule, finance, stakeholders, resources and risk individually as applied, not assessed or tailored out with a reason. Preserve accepted local policy. Unknown finances remain unassessed; leaf percentages establish no earned value, effort, cost or benefit measurement.

When new work appears, first determine whether it belongs to the current outcome, a future outcome, an incident or continuing operations. Refresh the overview and affected scouting coverage. Select and prioritize bounded work; retain unselected ideas outside required scope. Include management, integration, assurance and handover where relevant.

Before changing the ledger, preserve its old observation. Retain stable IDs, aliases and exclusions; record added/removed/split/merged scope and its acceptance, dependency, resource, schedule/risk and denominator effects. Use **update-project-progress** to generate the history bridge. Approval already provided for the task remains valid; installing or continuing setup does not invent a baseline decision.

Validate from the toolkit root:

```sh
PYTHONPATH=src python3 -m project_record check --config /path/to/project/progress/project-record.json
```

Handoff the overview/discovery/adoption paths, WBS mapping, proposed/decided changes, named before/after fractions, cleanup rationale, gaps and next accountable action. Keep operational health separate from the bounded project percentage.

Common mistakes: duplicate WBS credit; treating a snapshot as approved; forcing all maintenance into an endless denominator; deleting unfinished work to raise completion.
