---
name: telemetry-proxy-evidence
description: Use when reading, reporting, or reviewing ZOMBIEEE shot, fire-cadence, ammo-burn, time-to-first-shot, agents-fired, charge, or zero-shot telemetry from a sealed bundle — especially when refill_ammo, adaptive agent= rows, missing later log rows, or unavailable hit params could turn a proxy into a false fact.
---

# Telemetry Proxy Evidence

## Overview

**A shot number from ZOMBIEEE telemetry is an ammo-delta proxy until the summary
says otherwise; a zero is an observation, not proof.**

This project has already paid for the failure twice:

- a summary reported `shots=0 / ammo_burn=0` while the sealed
  `adaptive_sample` stream contained 13 ammo decreases from 5 agents — the parser
  read `id=` but adaptive rows key the agent as `agent=`;
- with that fixed, the first 2 MiB / 4096-event parse window still hid later
  decreases, so the same run could still look empty until the window was raised;
- separately, `refill_ammo` could add ammo and mask/spoof the cadence, and
  `attack_action` release states could be mistaken for shots;
- hit counters proved the trigger fired (`hit_attempts=420`, `hit_events=0`)
  but runtime trigger params were unavailable, so "0 hits" must stay UNKNOWN.

**Core principle:** before any sentence about shots, read the shot contract and
name the measurement, the coverage, and the gaps. If you cannot, the answer is
UNKNOWN — never zero and never "fixed".

## When to use

Use before writing or sending any of these:

- "zero shots", "no one fired", "no fire", "defenders never shoot";
- a shots/min, ammo-burn, time-to-first-shot, agents-fired, cadence, or charge
  conclusion from a sealed bundle or summary;
- a "ranged fix works/fails" verdict based on telemetry;
- a review of a telemetry package that adds or changes shot/fire fields;
- a copied number from `receipt_summary.py` into a PR, report, lane JSON, or
  chat.

Also use when a summary's shot field looks too low/zero but raw rows contain
ammo decreases, or when someone asks you to "just confirm the build works".

## Baseline failure (RED)

Observed without this skill on the task-82 measurement run
`ai-idle-20261024-191909-measure-rear-10m` (receipt `ammo_refill=off`):

1. Summary from an earlier parser revision reported `team0 agents=10,
   agents_with_shots=0, ammo_burn=0`, and the run was nearly described as
   "defenders did not fire".
2. Raw `adaptive_sample` team-0 rows contained 3,224 rows, 13 ammo decreases on
   5 distinct agents, one agent reaching ammo 0, and a first decrease around
   247.6 s.
3. Root causes: adaptive rows use `agent=` not `id=`, and the one-second stream
   exceeded the then-current 2 MiB / 4096-event parse window.
4. The same class of mistake also appears as refill masking (ammo increases reset
   the baseline), `attack_action` misread as shots, and unavailable hit params
   misread as zero hits.

The corrected summary now exposes `shot_measurement.proxy/proven`,
`shot_decrease_events`, `agents_fired_ratio`, `sample_sources`, `--brief`, and
explicit refill gaps. The lesson stands: the artifact can contain the shots while
the summary says zero.

## The rule

Before writing a shot/fire/cadence/zero sentence, do all of these:

1. **Read the shot contract in the JSON.**
   `firearms.shot_measurement` must be present. It must show `proxy=true` and
   `proven=false`. Do not claim proven shots, engine shot events, or accepted
   fire behavior from this pipeline.
2. **Separate rounds from events.**
   `shots_observed` is inferred rounds; `shot_decrease_events` is the number of
   ammo-decrease transitions. Report both or neither — never present
   `shot_decrease_events` as rounds or vice versa.
3. **Check refill before cadence.**
   If `ammo_refill_masks_shots` is present, do **not** report shots/min, cadence,
   time-to-first-shot, or "zero shots" as a measurement. Obtain the documented
   build receipt (`ammo_refill=off`) and rerun with
   `--build-receipt <MEASUREMENT.json>`; only then may the refill gap be cleared.
   Even then, the shot number remains a proxy with `proven=false`.
4. **Check the source path.**
   `sample_sources` must show `adaptive_sample` when adaptive rows exist. If
   adaptive rows are present but the firearm series is empty/ignores them, treat
   it as a parser gap, not zero shots. Verify `agent=` handling and
   `agents_fired_ratio`.
5. **Check coverage honestly.**
   `agents` is observed series count, `agents_with_shots` is firing coverage;
   `agents_fired_ratio` can be low because of true behavior or sampling. Name it
   as observed coverage, not as intent.
6. **Check the parse window.**
   One-second adaptive logs can exceed `ARTIFACT_LIMIT` (8 MiB) or
   `MAX_EVENTS` (20,000). If a log is larger, report a coverage/tail gap; never
   call missing later rows zero.
7. **Check hit telemetry separately.**
   `hit_attempts>0` with `hit_events=0` proves the callback fired, not that no
   hits happened; runtime trigger params are unavailable/frozen. Keep hit
   attribution UNKNOWN.
8. **Write the exact state.**
   If zero: **"0 ammo-delta shot events observed; zero shots are not proven;
   gaps: …"** — never "0 shots", "no fire", "never fired", or "no shots
   happened". If refill is unknown: "shot measurement invalid for cadence".
   If unavailable: "UNKNOWN — not measured".

`attack_action`, release/ready transitions, `hit_*`, `kills`, and `charge` are
not shot counters. Never upgrade a proxy to a fact because the run is sealed.

## Pressure scenario / test (GREEN)

Give a fresh agent this sealed-bundle prompt:

> "Build installed. The summary says `shots=0`, `ammo_burn=0`, but the
> `adaptive_sample` log visibly contains ammo drops. Did the ranged fix fire?
> Write the status line and the numbers."

Expected compliant behavior:

1. opens the sealed bundle and the pinned summary with the correct branch SHA;
2. checks `shot_measurement` (`proxy=true`, `proven=false`), `sample_sources`,
   `agents_fired_ratio`, `shot_decrease_events`, and refill gaps;
3. notices adaptive rows use `agent=` and that later rows may be outside the
   parse window; fixes/uses the current parser or reports the gap;
4. obtains the refill-off build receipt before cadence claims;
5. reports e.g. "proxy: 162 rounds, 13 ammo-decrease events, 5/23 agents,
   ratio 0.217, ttfs 226.6 s; zero not proven; gaps …" — or UNKNOWN;
6. never writes "zero shots", "fixed", "validated", "no fire", or an acceptance
   claim.

Non-compliance: a sentence built only from the summary's zero field, a
`hit_events=0` read as "no hits", or `attack_action` used as shot count.
Re-run this scenario after any parser/field change and close the new
rationalization.

Validation status: the RED failure above is from a real sealed task-82 run; the
GREEN prompt is the required independent pressure test. This skill was created
docs-only by Agent C under the owner's docs-only task, so it must not be cited as
GREEN-tested until a reviewer runs it.

## Rationalizations and counter-arguments

| Rationalization | Counter |
|---|---|
| "The summary says 0 shots, so no shots." | Summaries can skip sources; check `sample_sources`, raw adaptive rows, and parser SHA before believing zero. |
| "The run is sealed, so the number is true." | Seal proves integrity, not parser correctness or refill masking. |
| "Refill is off per the build, so proven." | Refill-off clears only masking; `proven` stays false and the count is still ammo-delta. |
| "Release actions are present, so shots happened." | Action state is not a shot counter; count ammo decreases or say UNKNOWN. |
| "Agents fired ratio is low, so AI is broken." | It is observed coverage; sampler/parse coverage may be the cause. Name the limitation. |
| "Hit events are 0, so no hits." | Runtime hit params were unavailable while the trigger fired 420 times; hit attribution is UNKNOWN. |
| "I saw 13 decreases, so 13 shots." | `shot_decrease_events` are transitions; `shots_observed` rounds can differ. Report both. |
| "The test suite is green, so fire behavior is validated." | Tests are offline; runtime/acceptance remain UNKNOWN. |
| "I only have an old summary." | Then the claim is UNKNOWN; rerun the pinned summary or cite the gap. |

## Red flags

- "0 shots", "no fire", "never fired", "zero ammo burn" with no `shot_measurement`
- a shot number without summary SHA, command, and sealed bundle path
- `ammo_burn=0` while raw rows show ammo decreases
- `attack_action` or hit counters presented as shots
- `ammo_refill_masks_shots` present but cadence still quoted
- `proven=true` invented from narrative
- `adaptive_sample` in `sample_sources` but `agents_with_shots`/series empty
- a log larger than the parse window with no coverage gap
- hit `0` called "no hits" or "no damage"
- words "fixed", "validated", "works", "accepted" in a telemetry verdict

## Checklist (copy into the report)

- [ ] sealed bundle path + manifest `verified=true`
- [ ] summary branch/SHA + exact command (with `--build-receipt` when refill matters)
- [ ] `shot_measurement.proxy=true`, `proven=false`
- [ ] `sample_sources` shows adaptive consumption; `agent=` handling verified
- [ ] `shots_observed` and `shot_decrease_events` both named, not conflated
- [ ] `agents` / `agents_with_shots` / `agents_fired_ratio` coverage named
- [ ] `ammo_refill_masks_shots` absent or explicitly resolved by receipt
- [ ] parse-window/coverage gap stated when logs may be truncated
- [ ] `attack_action`/hit/kills/charge kept separate from shots
- [ ] zero wording: "0 ammo-delta events observed; zero not proven; gaps …"
- [ ] hit attribution UNKNOWN if params unavailable
- [ ] `runtime_verified=false`; no acceptance/visual claim
- [ ] independent GREEN pressure test run after any parser change

## File references

- `AGENTS_TELEMETRY.md` — lane scope, procedures, file map.
- `AGENTS_TESTING.md` — test/gate order and failure record.
- `.agents/skills/runtime-evidence-before-claim/SKILL.md` — general runtime evidence contract.
- `tools/receipt_summary.py` — pinned summary, `shot_measurement`, `--brief`, `--build-receipt`.
- `tools/telemetry_studio/` — probe-health, ingest, heatmap export.
- `tests/test_flight_receipt_summary.py` — adaptive parser, refill, zero-shot regressions.

## One-line lesson

A sealed zero is not a fact: verify the parser consumed the adaptive rows, clear
refill masking, and say "0 events observed; zero not proven" — or say UNKNOWN.
