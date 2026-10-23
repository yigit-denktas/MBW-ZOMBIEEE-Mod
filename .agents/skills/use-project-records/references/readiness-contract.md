# Repository readiness during setup and adaptation

Readiness describes the engineering system an agent can rely on. Work completion describes delivered scope. Keep L0–L5 separate from every completion percentage and from task risk R0–R4.

## Assess before planning autonomous operation

Start with read-only discovery. Inspect the existing assessment, repository policy, bootstrap, CI, runtime, sandbox and deployment evidence. Record the tested revision/environment and source dates. File presence is a lead; a lockfile, AGENTS file or CI badge alone proves no level. Unperformed checks remain unknown.

Use the adjacent `readiness-assessment.json` as an empty record, not a grade certificate. Every dimension has pass, partial, fail or unknown status, evidence and gaps. A pass requires demonstrated behavior; partial/fail records a concrete blocker, owner and next action.

| Dimension | Evidence to examine |
| --- | --- |
| 1. Work definition | Bounded tasks, criteria, dependencies, non-goals and reproducible bugs. |
| 2. Repository knowledge | Current entrypoint, architecture/decisions, ownership and truthful status. |
| 3. Reproducible environment | Canonical clean bootstrap, resolved dependencies, safe fixtures and isolated services. |
| 4. Verification loop | Appropriate tests and integration/runtime evidence, stable commands and controlled flakes. |
| 5. Architectural constraints | Enforced schemas, dependency boundaries, analysis and ownership. |
| 6. Machine-usable tools | Structured CLI/API/MCP, repeatable scripts, scoped read/write access and fallbacks. |
| 7. Security boundaries | Enforced workspace/network/credential/resource boundaries and protected delivery. |
| 8. Small-batch reviewability | Bounded changes, independent review, reversible delivery and proven rollback. |
| 9. Runtime observability | Queryable health/logs/metrics, deployment identity and relevant runtime checks. |
| 10. Evaluation and governance | Held-out tasks, real-task metrics, drift review and active autonomy rules. |

## Level gates

The current grade is the highest level whose cumulative gates are demonstrated. Missing evidence prevents promotion; do not average dimension scores.

| Level | Required evidence |
| --- | --- |
| L0 Opaque | Default when L1 is not demonstrated. State whether evidence is missing or a check failed. |
| L1 Reproducible | Dimension 3 passes; a canonical verification baseline exists; ordinary tasks need no undocumented rescue. |
| L2 Legible | L1 plus dimensions 1 and 2 pass; ownership/safety boundaries are discoverable and the target task can be scoped. |
| L3 Verifiable | L2 plus dimension 4 passes, critical integration/runtime behavior is tested and flake/readiness debt is controlled. |
| L4 Constrained | L3 plus dimensions 5–8 pass for the delegated task class; sandbox/network/credential/delivery controls are enforced, required environment separation works and rollback is proven. |
| L5 Measured | L4 plus dimensions 9–10 pass; held-out tests and real-task success/intervention metrics meet declared thresholds over a defined window; promotion/downgrade rules operate. |

A task may require a lower authority than the repository grade suggests. Partial/fail/unknown evidence cannot satisfy a required pass. Separate observed current level from desired target; L5 is not mandatory for every project.

## Risk and authority

Classify the task by its consequences and privilege: R0 information/docs; R1 localized reversible changes; R2 ordinary behavior; R3 authentication, billing, migrations, critical paths or dependency policy; R4 privileged/destructive operations or weakened controls.

| Readiness | Default authority ceiling for future delegated work |
| --- | --- |
| L0 | Explore and propose. |
| L1 | Small bounded edits with close review. |
| L2 | Implement and prepare a PR; human merge. |
| L3 | Ready task to verified PR; merge follows repository policy. |
| L4 | Risk-specific delegation; only explicitly allowed R0/R1 work can qualify for unattended merge/deploy. |
| L5 | Measured policy may expand R0/R1 and selected R2 delegation; R3 keeps stronger approval by default; R4 stays planning/simulation unless narrowly supervised authority is explicitly supplied. |

Use the narrowest applicable boundary from readiness, task risk, current operational health and actual repository/owner policy. Existing explicit authorization for bounded setup/remediation remains valid; an assessment or installation grants no additional permissions. Do not turn a target grade into active authority.

Before unattended merge/deploy, verify explicit risk-class delegation, active branch/ruleset and independent checks/review, tested rollback, healthy recent metrics and no relevant blocker. Keep production access behind the protected delivery path. Policy statements are not proof that controls run.

For important applications (real users, persistent data, authentication, billing, consequential automation or infrastructure), inspect development, test/CI, staging/preview where risk warrants it, and production. Record identities, secrets/data separation, reachable networks, immutable artifact promotion, migration rehearsal, rollback and post-deploy health. Coding/test environments sharing production credentials or routes block L4. Small static/docs/experimental projects may use a reduced topology with a recorded reason; untested isolation remains unknown. Never use production secrets to prove readiness.

## Ask, record and improve

After scouting, ask only unresolved questions: what work should agents handle, what target level serves that goal, who accepts/merges/deploys, what environments exist, and what success/intervention thresholds and observation window apply? Use existing policy where it answers these questions.

Keep detailed assessments centrally in the configured assessment repository/store, keyed by repository, with `latest.json`, `latest.md` and dated history. For Personal Agent Stack-managed projects the convention is `assessments/owner__repo/`. Target `progress/overview.md` and `progress/adoption.md` carry the assessment reference, date/revision, current/target level, authority limits, key blockers and next action. They do not become a second assessment authority. If the central store is inaccessible, prepare the report in a private staging artifact and mark central persistence pending; do not publish private assessment evidence to README/Pages. Record the configured destination before writing externally.

Turn selected objective gaps into bounded remediation leaves linked to milestones and verification criteria. Prioritize broken safety boundaries and active outcome blockers, then reproducibility, verification and dependencies. Keep unselected maturity ambitions outside required work. Preserve previous observations and named percentages when adding readiness work. A completed assessment with honest unknowns is useful; it does not mean the target level was reached.

Reassess on onboarding, before increasing autonomy, after major runtime/build/security changes, an incident or undocumented human rescue. For actively autonomous projects, record at least monthly full reviews and weekly lightweight drift checks; scheduling requires the existing task's authorization. Broken bootstrap, flaky CI above threshold, missing controls/runtime evidence, stale instructions, repeated incidents/reverts or rising intervention burden reduce affected authority. Record the downgrade and containment, continue independent authorized work, and restore authority only after evidence and policy permit it.

## Assessment handoff

Include repository/revision/date, ten dimension results with scoped evidence/gaps, cumulative current and proposed target level, task risk, R0–R4 authority, operational-health limitations, central reference/history, selected remediation and denominator effect, next review date/trigger and who can approve any proposed promotion. Report untested checks explicitly. Skill installation does not execute an audit, enforce isolation or schedule future reviews.
