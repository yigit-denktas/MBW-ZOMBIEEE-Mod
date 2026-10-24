---
name: prepare-project-delivery
description: Use when a scoped result needs change fragments, changelog entries, release planning, readiness gates, publication records, deployment observations or a delivery handoff.
---

# Prepare project delivery

Package the bounded result with evidence and compatibility effects. Plans, publication and deployment are distinct observations.

Read repository instructions, the native version/channel policy, and the pinned toolkit's `standards/GITHUB.md`, `standards/AUTOMATION.md` and `standards/DELIVERY.md`. Inspect actual candidate work and publication channels through authorized tools; record inaccessible channels as unknown.

| Record | Required identity |
| --- | --- |
| Change fragment | Unique ID, component/type, plain summary, affected work/capability IDs, PR/evidence and compatibility/migration impact when relevant. Use `templates/change.example.json`; register one authoritative writer. |
| Release plan | Component, channel, native version, exact candidate revision/digest, included work/changes and explicit evidence gates. |
| Receipt | Kind, gate subject, result, exact candidate revision, attributed source and observation; retain failed/partial/mismatched historical attempts. |
| Publication | Observed component/channel/version, source revision or artifact digest, channel URL, included changes, actual publication time or unknown, and separate observation time. |
| Deployment | Environment/deployment identity, actual revision/digest, deployment/observation time, URL and scoped health evidence. |

List meaningful fragments under manifest `changeFiles` with authority, visibility and observation. The runtime rejects duplicate change IDs and overlapping writers. Unshipped changes remain Unreleased. Use the existing version source; avoid adding a competing VERSION file.

From the toolkit root, build into a new dedicated output destination:

```sh
PYTHONPATH=src python3 -m project_record pipeline --config /path/to/project/progress/project-record.json --output /path/to/new-delivery-build --audience owner
```

Read its `delivery.json` and `CHANGELOG-generated.md`. Readiness uses the declared gates and matching receipts; an empty gate set is unassessed. Work completion, hosted checks, keyboard review, physical inspection and designated approval remain separate where required. Tests on revision A cannot certify candidate B. A healthy old deployment cannot establish the candidate's health.

Prepare all authorized local artifacts and checks even when a gate is unavailable. Handoff the missing evidence and responsible next action. A ready plan establishes readiness for publication review, not actual publication. Perform external publication/deployment only under the task's existing authorization, then read back the result and record actual identities/times.

Report bounded result → included changes → named passed/total gates and percentage → remaining limits → observed publications/deployments → next action. A no-release project states that policy; unavailable channel data stays unknown. Correct historical delivery facts through sourced amendments.

Common mistakes: treating a tag/changelog heading as a release; importing old CI success into a new candidate; claiming owner approval from a request to continue; silently retargeting historical releases.
