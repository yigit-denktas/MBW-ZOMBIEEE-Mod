# AGENTS_RELEASE.md — launcher / installer / release-gate book

Load this only for launcher, installer, release-gate, Pages-publishing or lane-planning work.
Testing order: `AGENTS_TESTING.md`. Role/review rules: root `AGENTS.md` + `AGENTS_LEAD.md`.

## Scope

- Owned here: `launcher/`, `installer/`, `tools/build.py` integration boundaries, release-gate checks, Pages source copy (`site/`), lane planning/config, user-facing Windows bootstrap docs.
- Not owned here: game AI/orders, telemetry probe/summary internals, ledger/readiness percentages (A), legal/rights claims (E), raw game captures/publication clearance.
- The gate is a **candidate check**, never acceptance. `runtime_verified=false` and `acceptance=none` stay unless the owner accepts sealed evidence.

## Session start

1. `git status`, branch/worktree, current `main` and `VERSION`; confirm you are not on another package branch.
2. Read `launcher/release_gate.py` and the gate tests before claiming anything about gate behavior.
3. Check `docs/release-traceability.json` `source_revision` versus actual `HEAD`; a stale source revision is a gate blocker until the metadata sync.
4. No install/launch for docs/gate work. If a run is required, stop: runtime owner/Lead owns installs, windows and abort authority.

## Procedure (small package)

1. Branch from current `main`; keep the package single-purpose.
2. Implement launcher/gate change with offline tests first.
3. Run targeted tests, then full suite, then the gate:
   - `python -m unittest discover -s tests -q`
   - `python -m launcher.release_gate`
   - `python -m launcher.play_city release-check --json` for the CLI surface
4. Assert gate semantics, not just exit code: parse the JSON, list `blockers`, `checks`, `acceptance`, `runtime_verified`.
5. Submit branch/SHA/scope/tests/evidence/gaps to a fixed reviewer (`review-b2` or `E`). Builders do not self-review or review peers.
6. Lead merges after sign-off; then run the single metadata/CHANGELOG/README sync and re-run the gate.
7. Delete the package branch only after integration; archive first when root rules require it.

## Assumptions and gate contract

- Gate exit codes: **0 = all checks pass; 2 = fail-closed** (any blocker, malformed inputs, missing git data as documented). Do not treat 2 as success.
- Gate is read-only: no writes, no launch, no network, no firewall/bind change.
- Required evidence is a report with `schema`, `checks`, `blockers`, `warnings`, `acceptance=none`, `runtime_verified=false`; missing/unknown evidence is a gap, not a pass.
- Privacy scan covers tracked text with **exact-file exemptions only**; no prefix allowlist that hides a directory.
- Path checks must catch plain, JSON-escaped and **mixed-separator** Windows paths, POSIX home paths, UNC and `file://` forms; placeholder-relative suffixes (`<warband-root>\\Logs\\...`) must not be false positives.
- Traceability checks: version/changelog/source revision consistency, work-item→PR/commit links, ancestry, and a fail-closed head/source guard. Metadata PRs use the documented metadata-only path; feature branches use an explicit invocation allowance if the gate supports one — never persist a feature-branch exception in the record.
- Lane planning is offline-only: `--lane 1|2` uses distinct module copies/ports; **concurrent WSE2 dedicated instances are UNKNOWN** until sealed runtime evidence exists. If WSE2 cannot, report an explicit blocker.
- Raw gameplay frames/screenshots are private evidence; public Pages output is derived-only unless owner + legal clearance. No ownership/IP claim.

## Common failures (paid lessons)

| Symptom | Actual cause | Rule |
|---|---|---|
| `no_personal_local_paths: clean` but manifests contain `C:\\Users\\...` | Scanner only matched single backslashes | Treat JSON-escaped/mixed separators as paths; add fixtures; never trust a clean line alone |
| Gate passes but a PR merged the old head | Source revision/head guard not enforced | Fail closed on stale source/merge; re-check the actual merged SHA |
| `release-check` exits 2 and a test is “fixed” to expect 0/2 broadly | Exit code hides blockers | Parse JSON; accept only explicitly known blockers, not any 2 |
| Feature branch cannot satisfy `source_revision == HEAD` | Self-referential revision is impossible | Metadata PRs stay metadata-only; feature allowance is invocation-only, never persisted |
| Gate flags `docs/DIAGNOSTICS.md` / `progress/ledger*.json` | Real absolute local paths in owned docs/tracker | Sanitize to placeholders (`<warband-root>`, `<local>`); do not add prefix exemptions |
| Placeholder `<warband-root>\\Logs\\...` flagged as UNC | UNC regex over-broad | Require real UNC start / exclude placeholder-relative forms; regression test |
| Suite red only on real-checkout M2 test | Correct true positive from A-owned path debt | Report blocker; update tolerance only to known blockers with a removal date/owner |
| Lane plan says “supported” | Only offline plan/argv tested | Say “offline-verified; concurrent WSE2 UNKNOWN/blocker”; no feature claim |
| Pages shows raw capture | Publishing bypassed privacy/legal gate | Remove raw asset, purge/replace refs, derived-only wording, publisher action |

## Lane lifecycle (launcher view)

- `--lane 1`: module `ZOMBIEEE_Remaster`, loopback `127.0.0.1:7240`.
- `--lane 2`: module `ZOMBIEEE_Remaster_lane2`, loopback `127.0.0.1:7241`.
- Each lane needs its own install target/stage/backup, server config and rotation; plan/argv must carry the lane module and endpoint; `parallel_lane_runtime_verified=false`.
- Lane support is a plan/install boundary, not proof of concurrent WSE2 sessions. Runtime owner must seal or report UNKNOWN/blocked.
- Never run two lanes during a release-gate-only task; never install while a game session is active.

## Handoff / review

Builder sends: branch, SHA, scope, changed files, commands/results, gate JSON summary (blockers), known gaps, `runtime_verified=false`.

Reviewer returns: PASS / BLOCKED / UNKNOWN with the exact artifact and reason. E handles release/legal wording; review-b2 handles gate correctness. Lead merges; no self-approval, no peer evaluation, no acceptance from the builder.

## File map

| Path | Role |
|---|---|
| `launcher/release_gate.py` | fail-closed release checks (privacy, traceability, version, layout) |
| `launcher/city_launch.py` | plan/argv/receipts/lane selection |
| `launcher/install.py` | backup-first install, module paths, receipts |
| `launcher/runtime.py` | loopback endpoint/bind helpers |
| `tests/test_windows_release_traceability.py` | gate privacy/traceability fixtures |
| `tests/test_windows_m2_gates.py` | gate CLI, settings, maintenance gates |
| `tests/test_windows_city_launch.py` | plan/launch/lane fixtures |
| `docs/release-traceability.json` + `docs/RELEASE_TRACEABILITY.md` | candidate revision/work-item/PR/gap record |
| `docs/WINDOWS_BOOTSTRAP.md` | operator/install/lane instructions |
| `VERSION`, `CHANGELOG.md`, `site/` | release/channel copy; publisher owns `gh-pages` |
| `progress/` | A-owned tracker/ledger; do not hand-edit generated data |
| `archive/` + archive tags | frozen branch/worktree recovery |

## Stop conditions

Stop and ask Lead/owner when a change would weaken a gate check, exempt a real path, alter an exit-code contract, publish a raw capture, claim lane/runtime support without sealed evidence, or requires install/launch/acceptance. UNKNOWN is not PASS.
