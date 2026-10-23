---
name: operate-project-tracking
description: Use when tracking automation, CI, observation freshness, failed collection, operational telemetry, generated-output corruption, interrupted installation, replay, rollback or toolkit upgrades need attention.
---

# Operate project tracking

Recover the derived system from pinned sources while preserving authored facts and observation history. Project operations telemetry records evidence; it does not invent service health.

Read repository instructions, field/output ownership, existing CI/runbook and the pinned toolkit's `standards/AUTOMATION.md`, `standards/UPGRADING.md` and `standards/AGENT-WORKFLOWS.md`.

| Operational record | Required contents |
| --- | --- |
| Ownership | Source writers, generator-owned output, host deployment owner, service/support/recovery owner and authorization boundary. |
| Reproduction | Toolkit/contract version and exact source/file hashes; configuration, adapter, audience and last successful artifact identity. |
| Collection | Actual attempt time, source observation/last success, status, page/cursor coverage, error/quota evidence and next responsible retry. |
| Build/delivery | Run/revision, result, artifact hashes, observed deployment/health; separate from collection freshness. |
| Recovery | Diagnosis, preserved inputs/history, scoped generated replacement, verification and replayable rollback. |

First distinguish authored-source damage, derived-output damage and failed external retrieval. Preserve diagnostics and last successful source observation. For damaged authored data, recover a verified source/backup and reconcile later edits; never reset it to fix a renderer. For derived damage, rebuild pinned inputs into a new empty dedicated destination, check hashes/counts/privacy/routes and replace only owned output under the repository's accepted policy.

For stale or partial external retrieval, keep last-success counts visibly dated. A failed or incomplete collection cannot establish absence, deletions or zero progress. Use `templates/collection-attempt.example.json` for a sourced attempt receipt. From the toolkit root:

```sh
PYTHONPATH=src python3 -m project_record status --config /path/to/project/progress/project-record.json --only loomglass --as-of 2026-10-22 --observation /path/to/attempt.json
```

This command validates supplied observations and performs no network collection. A rebuild or successful attempt receipt does not refresh the source file's observation. Unknown deployment health stays unknown. Continuing operations remain separate from bounded project progress.

Reuse accepted CI and generated-file policy. Exercise the same offline action entry point locally and in hosted CI; use relevant project checks for changed application paths. Tracker-only changes do not launch inference or unrelated costly suites. Record quota/capacity failures and a bounded retry/handoff; they are failed/unknown checks, not passes.

Resume an interrupted install from `.project-record/agent-installation.json`, actual hashes and remote IDs, not cold init. Preview `install-skills`; it preserves existing AGENTS/outside files and rejects local conflicts. For upgrades, compare old/new outputs, review schema/adapter changes, then use `--upgrade --apply` on unchanged owned files. Preserve a verified previous version/artifact and avoid duplicate writers/jobs.

Report restored output separately from stale source/health. Handoff exact commands/identities, named fractions, coverage/errors, tests, replaced paths, remaining limits and next owner/action. Existing task authorization governs deployments, schedules, credentials and external changes.

Common mistakes: deleting the ledger to repair UI; rebuilding into mixed/private output; overwriting human edits; claiming current observation from today’s build.
