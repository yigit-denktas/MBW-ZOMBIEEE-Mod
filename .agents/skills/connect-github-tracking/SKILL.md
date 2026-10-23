---
name: connect-github-tracking
description: Use when project work needs GitHub issues, issue titles, labels, parent or blocking relationships, milestones, Project fields/views, or reconciliation with an existing JSON tracker.
---

# Connect GitHub tracking

Connect existing native objects through stable IDs and explicit field authority. Shared meanings can use project-owned label aliases.

Read repository instructions, `progress/discovery.json`, `progress/adoption.md`, and the pinned toolkit's `standards/GITHUB.md`. Prefer connected GitHub tools. Inventory existing issues in all relevant states, PRs, milestones, Projects, labels and field IDs with observation time, pagination and coverage. Record inaccessible sources.

| Mapping | Contract |
| --- | --- |
| Title | `[stable-ID] Verb + concrete outcome`, within 120 characters; retain ID through rename/rescope. |
| Body | Outcome → Scope → Acceptance → Evidence → Dependencies → Next action; affected ledger IDs and owner. |
| Labels | One type, one project-local priority, relevant project-owned areas. Map existing aliases before adding labels. |
| Relationships | Native parent/sub-issue/blocking links; one primary milestone per accounting leaf; shared prerequisites are references. |
| Authority | Name the writer per field: for example JSON completion, GitHub assignment/discussion, Project workflow. Completion projections are derived. |
| Views | Reuse the Project: active work, milestone roadmap, blockers and release readiness as useful locally. |

The alias JSON maps **existing label name → shared meaning**: `{"kind/feature":"type:feature","urgency/next":"priority:P1","ui":"area:presentation"}`. Keep native label names on GitHub; the linter translates them for validation.

Prepare a local issue JSON and alias map using the actual project labels. From the toolkit root:

```sh
PYTHONPATH=src python3 -m project_record lint-issue /path/to/issue.json --aliases /path/to/label-aliases.json
```

Use `templates/labels.json` and `templates/.github/ISSUE_TEMPLATE/work-package.yml` as vocabulary/shape references, not a wholesale replacement for local conventions. The issue linter validates declared strings; it cannot prove that objects exist or grants were authorized.

For authorized writes, prepare a bounded object/field diff, find existing objects by saved IDs and stable work IDs, then reread current values before mutation. Preserve human edits and unrelated fields; use available revision/lease checks. Record created/updated IDs, URL, input observation and result in the handoff. Read back the result. An interrupted create requires reconciliation before retry, preventing duplicate issues or Projects.

If collection fails or pagination is partial, preserve the last successful snapshot and display the failure/coverage. An unseen issue is not proven absent; do not create replacements or delete unseen objects from that response. Draft and lint local work while retrieval is blocked. Track collection attempts separately with **operate-project-tracking**.

Handoff issue drafts, alias/authority/object maps, source coverage, proposed/applied effects, checks and next action. Use existing task authorization; local tracker setup alone authorizes no external writes, credentials or schedules.

Common mistakes: a second status-label writer; recreating a valid board; counting both an issue and its ledger leaf; overwriting human state from an older snapshot.
