# AGENTS_TELEMETRY.md

Status: docs-only role guide. This file defines the telemetry/probe/evidence lane:
how to read a sealed run, which summary fields are evidence, and which claims are
forbidden until a reviewer accepts them. It does not grant merge, install,
launch, or acceptance authority.

## Scope

You own:

- the Lua probe contract and ZDB1 event schema;
- receipt parsing and summaries (`tools/receipt_summary.py`);
- telemetry-studio ingest, anomaly, probe-health, heatmap export and loop tools;
- heatmap/spatial consumer outputs (`telemetry/spatial_analysis.py`);
- evidence packages, gap lists, and the telemetry side of review fixes.

You do **not** own: game installs or sealed-run execution (runtime lane), build
behavior changes (AI/combat lane), merge/acceptance (Lead/owner), or publish
claims (legal/review).

Read this file with `AGENTS_TESTING.md` and `docs/REVIEW_POLICY.md`. Do not
preload other role files unless the task crosses that lane.

## Core rules

1. `main` is the only code branch; one small package at a time:
   **target -> tests -> build -> review -> integrate**. No mass merges.
2. Evidence beats narrative: revision + command + artifact + result + gap.
   UNKNOWN is never PASS.
3. A green suite is not runtime evidence and never acceptance. Keep
   `runtime_verified=false` and `acceptance=none` unless an owner accepts.
4. Builders do not review peers or self-approve. Fixed reviewers:
   `review-b2` and `E`.
5. Raw gameplay captures stay private. Publish derived tables only.
6. Never invent, backfill, or infer a missing telemetry value. Zero is a
   measurement result, not a default.
7. Every telemetry package submission includes: branch/PR + SHA, scope,
   acceptance criteria, tests, receipt/evidence, known gaps.
8. Read `.agents/skills/runtime-evidence-before-claim/SKILL.md` before making a
   runtime claim, and
   `.agents/skills/telemetry-proxy-evidence/SKILL.md` before any shot/fire/
   cadence/zero claim.

## Procedure: analyze a sealed bundle

Run from the worktree root. Use the pinned summary from the branch under review;
do not mix a branch's probe with another branch's parser unless the integration
receipt says so.

1. **Confirm the seal.** The bundle must have `manifest.json` and
   `verified=true`; mission/module identity must be unchanged for the whole run.
   If the module changed mid-run, discard the bundle.
2. **Check probe health.**
   `python -m tools.telemetry_studio probe-health <bundle> --json`
   Expect heartbeat > 0, required triggers registered, no critical error family.
   A `fail` or a named gap blocks the related claim; report it, do not average it
   away.
3. **Ingest and inspect coverage.**
   `python -m tools.telemetry_studio ingest <bundle> --json`
   `python -m tools.telemetry_studio anomalies <bundle> --json`
   Record heartbeat cadence, adaptive sample count, missing fields, and parser
   gaps.
4. **Summarize with the pinned tool.**
   `python tools/receipt_summary.py <bundle> --json`
   For a measurement build (for example `ammo_refill=off`) add the receipt:
   `python tools/receipt_summary.py <bundle> --build-receipt <MEASUREMENT.json> --json`
   For a 3-minute smoke run use `--brief`; still attach the JSON when a number is
   quoted.
5. **Read the shot contract before quoting a shot number.**
   Inspect `firearms.shot_measurement`, `firearms.team0/1.sample_sources`,
   `agents`, `agents_with_shots`, `agents_fired_ratio`, `shot_decrease_events`,
   `shots_observed`, `shots_per_minute`, `time_to_first_shot`, and
   `evidence_gaps`.
6. **Export spatial input only from the same sealed bundle.**
   `python -m tools.telemetry_studio heatmap-export <bundle> --out points.json`
   Then `python telemetry/spatial_analysis.py --input points.json --out-dir <dir>`.
   Spatial output is descriptive; chokepoints are occupancy candidates, not
   proven blockers.
7. **Write the evidence line.** State the sealed path, command, exact field
   values, proxy/caveat labels, and gaps. Do not write "fixed", "validated",
   "accepted", or "zero shots" from a proxy.

## Shot / evidence contract

| Field | Meaning | Rule |
|---|---|---|
| `firearms.shot_measurement.proxy` | Shots are inferred from ammo deltas | Always `true`; never present as a direct engine event |
| `firearms.shot_measurement.proven` | Whether the shot count is proven | Always `false`; do not flip it by narrative |
| `ammo_refill_masks_shots` gap | Refill_ammo can add ammo and reset the inference baseline | Do not claim cadence/shot counts; obtain a documented refill-off build receipt |
| `ammo_refill_off` | Build receipt says refill is off | Clears only the refill-masking gap; shots remain a proxy |
| `shots_observed` | Rounds inferred from ammo decreases | Do not call it "shots fired" or "proven shots" |
| `shot_decrease_events` | Number of observed ammo-decrease transitions | Different from rounds; report both or neither |
| `agents_with_shots` / `agents_fired_ratio` | Coverage of firing agents in observed series | A low ratio can be real or sampler-limited; name the coverage |
| `sample_sources` | Sources consumed by the firearm series | Must show `adaptive_sample` when adaptive rows exist; absence is a parser gap |
| `attack_action*` | Engine action state, not a shot counter | Release/ready transitions are not shots |
| `time_to_first_shot` | First ammo decrease minus team's first observed sample | `baseline=team_first_observed_sample`; not round-start latency; `unit=ticks` when `ts_ms` is absent |
| `ts_ms` | Probe-relative elapsed time | Never UTC, never cross-run wall clock |
| `hit_attempts/hit_events/hit_param_invalid` | Runtime hit-trigger counters | Runtime hit params are unavailable/frozen: `0` samples is UNKNOWN, not "no hits" |
| `evidence_gaps` | Explicit unknowns/failures | Every gap relevant to the claim must be copied into the report |

Additional invariants:

- Adaptive output is server-role only (`adaptive_server_only=1`); client
  screenshots must not be covered by ZDB1 console spam.
- Adaptive rows use `agent=` while ai/combat rows use `id=`. A parser that reads
  only `id=` silently drops adaptives; check `sample_sources` and agent counts.
- One-second adaptive logs can exceed a small parse window. The summary budgets
  `ARTIFACT_LIMIT=8 MiB` and `MAX_EVENTS=20000`; if a log exceeds that, record a
  coverage/tail gap and do not treat missing later rows as zero.
- `zero_shots_not_proven` must remain in the report when both teams show zero;
  report it as "0 ammo-delta events observed; zero not proven".
- A hit trigger that fires with `hit_param_invalid == hit_attempts` proves the
  callback is wired, not that hit attribution works. Compiled trigger params are
  required; that is a backlog item, not an observed hit count.

## Common failures (paid for already)

| Symptom | Root cause | Required response |
|---|---|---|
| Summary says 0 shots / 0 agents fired while raw adaptive rows show ammo drops | Parser read only `id=`, adaptive rows use `agent=` | Fix/consume `agent=`; verify `sample_sources` includes adaptive; re-run summary; record before/after |
| Late-run shots missing; early samples only | 1 s adaptive log exceeded old 2 MiB / 4096-event window | Use the 8 MiB/20000 parser window or report a coverage/tail gap; never report zero from a truncated window |
| Ammo burn looks erratic / zero | `refill_ammo` adds ammo, masking decreases and resetting intervals | Use `--build-receipt` with `ammo_refill=off`; otherwise no cadence claim |
| "0 shots" reported as "defenders never fire" | Proxy zero treated as fact | Write "0 ammo-delta events observed; zero not proven" and cite gaps |
| `attack_action` release count called shots | Action state is not a shot counter | Report separately as action transitions |
| Hit samples = 0 and summary marks hit attribution | Runtime `game.addTrigger` event params are not populated | Hit attribution UNKNOWN/unavailable; fail probe-health; compiled trigger is backlog |
| Client screenshots half-covered by ZDB1 text | Adaptive output printed on client | Gate adaptive to server role; rebuild/reseal; visual evidence cannot be used until clean |
| Adaptive counters present but summary firearms empty | Wrong source key or branch mixes parser/probe | Check parser branch and `sample_sources`; a mixed-branch receipt is contaminated |
| Numbers differ from a reviewer's | Different summary revision or build receipt | Quote the summary SHA and command; do not average two runs |
| Suite red after merging multiple packages | Mass merge with conflicting signatures/constants | Revert to last green tag; integrate package-by-package with full suite at each step |

## Tests and gates

- Targeted: `python -m unittest tests.test_flight_receipt_summary -q`,
  `python -m unittest tests.test_telemetry_studio -q`,
  `python -m unittest tests.test_spatial_analysis -q`.
- Full: `python -m unittest discover -s tests -q`.
- Release: `python -m launcher.release_gate`.
- Project record: `python -m project_record check` and `build`/`readme` when
  tracking output changes.
- Metadata-only edits change `source_revision`: run the gate **after** the
  metadata sync, not before.
- Runtime evidence needs a sealed bundle, manifest, mission/module identity, and
  the branch SHA; if absent, report UNKNOWN.

## Assumptions and boundaries

- The game is not launched by this lane; another lane produces the sealed run.
- ZDB1 schema fields are observed fields, not engine truth; interpretation stays
  labelled proxy/inferred.
- The `timeline`/`ts_ms` domain is the probe process, not a universal clock.
- Spatial samples describe observed positions only; no target/intent inference.
- Missing frames, gaps, unreadable divisions, unknown classes, and frozen hit
  params remain gaps. They are never silently zero.
- A reviewer PASS is evidence review, not owner acceptance.

## Handoff and review

Submit to Lead/reviewers with:

- branch/PR + SHA, base SHA, scope, target/tests/build/review state;
- exact commands and pinned summary JSON path;
- sealed bundle path, manifest/verified status, mission/module identity;
- probe-health status and every FAIL/UNKNOWN gap;
- screenshots only if opened and described (never raw private captures in public
  output);
- known limitations and follow-up package, if any.

While review runs, start the next package only after Lead assigns it; keep review
fixes in a separate commit/scope from the next target. Do not self-review, merge,
install, or claim acceptance.

## File map

| Path | Purpose |
|---|---|
| `overlay/lua/main.lua` | Probe: heartbeat, ai/combat/adaptive samples, triggers, capabilities |
| `tools/receipt_summary.py` | Fail-closed ZDB1 summary, firearm/shot/coverage fields, gaps, `--brief`, `--build-receipt` |
| `tools/telemetry_studio/` | Ingest, anomaly, perf, probe-health, heatmap export, loop receipts |
| `telemetry/spatial_analysis.py` | Heatmap consumer: occupancy/flow, cohesion, situations, chokepoints, SVGs |
| `telemetry/flight_recorder.py` | External flight-recorder protocol/redaction |
| `docs/DIAGNOSTICS.md` | Probe history and diagnostics caveats |
| `docs/RELEASE_TRACEABILITY.md` + `docs/release-traceability.json` | Revision/metadata gate |
| `tests/test_flight_receipt_summary.py` | Summary parser/shot-proxy regressions |
| `tests/test_telemetry_studio.py` | Ingest/probe-health/heatmap regressions |
| `tests/test_spatial_analysis.py` | Condition filtering/cohesion/panels regression |
| `.agents/skills/runtime-evidence-before-claim/SKILL.md` | General runtime evidence contract |
| `.agents/skills/telemetry-proxy-evidence/SKILL.md` | Shot/proxy/zero-specific guard |

## One-line lesson

Read the sealed artifact and the shot contract first; quote exact proxy fields and
gaps, or say UNKNOWN — a parser zero is never proof that no shots happened.
