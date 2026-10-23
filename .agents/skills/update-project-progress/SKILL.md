---
name: update-project-progress
description: Use when work is implemented, verified, blocked, accepted, deferred, cancelled, or newly discovered and a project's authoritative progress, evidence or history needs updating.
---

# Update project progress

Update the authoritative source once, then regenerate its projections. A progress update records what the evidence establishes at a specific revision.

Locate project instructions, the field-authority map and pinned toolkit. Read its `standards/STANDARD.md`, `standards/GITHUB.md` package-completion section and `standards/AGENT-WORKFLOWS.md` growth section.

| Required update record | Contents |
| --- | --- |
| Before | Preserve authored source bytes, manifest metadata and an immutable normalized observation. Keep existing historical snapshots. |
| Work/evidence | Stable ID, bounded result, criterion, implementation revision/artifact, typed receipts with subject/result/source/revision, remaining gate, responsible next action. |
| Scope | Added/removed/deferred/cancelled or split/merged IDs, reasons/aliases, denominator effect and actual authority decision when required. |
| After | Validated named fractions/percentages, state and scope effects, changed source paths, generated outputs, checks and limitations. |

For a new observation, pin its actual source identity/date; rebuilding alone leaves observation metadata unchanged. In a manifest, retain the old raw source and metadata under `snapshots`/`previousSourceFile` before replacing the current observation. Follow the source format's writer policy; normalized exports are derived files.

Award Done only against the leaf's own criterion. Distinguish implementation, verification, physical/owner acceptance and milestone gates. A receipt for another subject or revision remains historical. When an inspection is unavailable, record implementation and missing evidence, keep the affected leaf/gate pending and continue independent work. Existing legacy Done claims retain their source meaning without recertification.

When the outcome or scope expands, refresh overview/discovery and use **govern-project-scope**. Include newly selected required work visibly, then explain changes through history; avoid silently changing IDs or dropping unfinished obligations. Ideas awaiting selection remain discovery. Active/Review earns no partial completion credit.

From the toolkit root, export before and after to separate empty destinations and compare the normalized files:

```sh
PYTHONPATH=src python3 -m project_record check --config /path/to/project/progress/project-record.json
PYTHONPATH=src python3 -m project_record compare /path/to/before/loomglass.json /path/to/after/loomglass.json
```

Use `export --help` for observation exports; `pipeline` also produces typed history bridges, release readiness and matching README output. Respect public-input review and dedicated-output ownership. Preview README marker updates; route generator-owned files through their declared generator.

Report outcome → implementation/evidence → named before/after counts and percentages → scope explanation → remaining gate/next action. Link the exact tested revision and results. Record a meaningful change fragment or the reason none is needed. Use **prepare-project-delivery** for release implications; a merged PR alone establishes no publication.

Common mistakes: editing generated percentages; overwriting the previous observation; treating a merge as physical acceptance; reobserving inaccessible sources by changing a build timestamp.
