---
name: answer-project-status
description: Use when someone asks what works, how complete a project or milestone is, what changed, what is blocked, what remains, or whether progress data is fresh.
---

# Answer project status

Report the observed outcome and its evidence limits. This workflow is read-only.

Locate repository instructions, field authority and the pinned toolkit. Read `standards/STANDARD.md` for metric meanings and `standards/AGENT-WORKFLOWS.md` for status/collection fields. From the toolkit root:

```sh
PYTHONPATH=src python3 -m project_record status --config /path/to/project/progress/project-record.json --as-of 2026-10-22 --freshness-days 7
```

For a sourced collection attempt, select one project with `--only` and pass `--observation attempt.json`. This reads a receipt; it performs no fetch. Failed or partial collection preserves the last successful observation and counts.

| Answer slot | Required content |
| --- | --- |
| Outcome | What works and where; what remains unavailable. |
| Progress | Named required/retained fractions and percentages; accepted milestones separately. Empty denominator: Not measured. |
| Provenance | Source revision/digest, observation date/age, coverage and errors; build time separately. |
| Change | ID-level state/scope bridge when available; otherwise only observed net count differences. |
| Next | Blocker, missing proof/decision and responsible action. |

Distinguish readiness, acceptance, publication, deployment and observed service health. Completed-leaf ratios establish neither effort/value delivered nor delivery dates. Use the existing timeline/calculators; interpret unequal denominators before describing movement as performance. Missing channels and inaccessible pages remain unknown.

Common mistakes: answering from generated badges alone; treating rebuild time as freshness; inventing totals; averaging unrelated project percentages into portfolio completion.
