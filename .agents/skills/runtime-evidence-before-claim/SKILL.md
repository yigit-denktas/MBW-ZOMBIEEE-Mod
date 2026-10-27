---
name: runtime-evidence-before-claim
description: Use when reporting or judging runtime, gameplay, balance, telemetry, crash, or "it works / it's fixed / zero shots" results from a City session, sealed bundle, screenshot, or summary — before any claim leaves the machine.
---

# Runtime Evidence Before Claim

## Overview

**A runtime claim is a statement backed by a sealed artifact, a pinned summary, and a reviewed frame — not by a memory of a run.**

This project repeatedly produced confident but wrong runtime statements:
"0 shots" while raw telemetry contained 13 ammo decreases, "no player" while
the player had joined and died, "fixed" from a screenshot of a menu, and a
"valid" seal from a session where the module was swapped mid-run. The fix is
not more caution; it is a fixed evidence contract checked before the sentence is
written.

**Core principle:** if the artifact paths, counters, and caveats are not on the
page, the claim is not evidence yet.

## When to use

Use before writing or sending any of these:

- "it works", "fixed", "validated", "no regression", "zero shots", "no player"
- a game-balance or behavior conclusion drawn from a run
- a crash/regression verdict from logs or dumps
- a summary number copied into a report, PR, review, or chat
- a screenshot presented as proof of gameplay
- a recommendation to ship/accept a build

Also use when a reviewer or Lead asks "what's the evidence?" and you feel
tempted to answer from memory or from a previous run.

## Baseline failure (RED)

Observed without this skill in the ZOMBIEEE City runtime lane:

1. **Proxy misread as fact.** A summary reported `ammo_burn=0`,
   `agents_with_shots=0` and the run was described as "defenders never fire";
   the raw `adaptive_sample` stream held 13 ammo decreases / 5 firing agents —
   the summary parser had skipped adaptive rows. The fix was a parser change,
   not a gameplay change.
2. **Refill masking.** A build refilled ammo every 5 s; ammo-delta shot
   detection read zero even though release actions were present. The gate was
   declared failed; the measurement was invalid.
3. **`no_player` misread.** A run was called "playerless" because the summary
   said `no_player=true`; lifecycle showed `player_joined` at 42 s and
   `player_died` at 177 s, and the field was the final heartbeat state.
4. **Menu frame as gameplay.** Screenshots of the idle player's death menu were
   cited as "gameplay evidence" until reviewed.
5. **Install during run.** A module was installed while a lane was active; the
   run sealed but the evidence mixed two builds and had to be discarded.
6. **Unknown promoted to zero.** Unavailable telemetry (hit, division, mount,
   shield) was reported as 0/false in early summaries.

Each failure was cheap to prevent: read the sealed truth, run the pinned gate,
state the caveat.

## The rule

Before writing the claim, produce **all five** or downgrade the wording to
"unknown / not measured":

1. **Sealed bundle path** with `manifest.json`, 8 files, `verified=true`, and an
   unchanged module/mission identity for the whole run. If the module changed
   mid-run, discard the run.
2. **Pinned summary output** (`tools/receipt_summary.py … --json`, with
   `--build-receipt` when a measurement parameter like `ammo_refill=off` is
   documented) — numbers quoted exactly, from that file.
3. **Gate result**: probe-health (`ok`, heartbeat > 0, no critical error
   family) and the run's lane report (PASS/FAIL/UNKNOWN), with any FAIL/UNKNOWN
   named in the sentence.
4. **Reviewed visual evidence** when screenshots are cited: open the frames,
   confirm they show gameplay, and list which files were reviewed; a menu,
   loading, or faction screen is not gameplay.
5. **Caveats that apply**: shot metrics are ammo-delta proxies (`proven=false`);
   refill masks shots; kills are lifetime counters; `no_player` is the latest
   explicit marker (read with `composition.mode` + lifecycle); hit attribution
   is frozen unavailable.

If any of the five is missing, use: "not measured / unknown / not
interpretable from this run" — and say what would make it interpretable.

## Interpretation rules

- **Never quote `no_player` alone.** Pair it with `composition.mode` and
  `lifecycle.player_joined/player_died`; a joined-then-died player is not a
  playerless run.
- **Zero is a measurement, not a default.** `0 shots` requires an ammo-delta
  metric from a refill-off build or an explicit "proxy unmeasurable" caveat.
- **Proxy values never become facts.** Shots, KD, hit counts, and charge are
  inferred; label them proxy/lower-bound and keep `proven=false`.
- **Kills are agent lifetime counters** summed over observed agents; never call
  them session kills, wins, or KD ratios without saying so.
- **PASS is bounded by the run.** A lane PASS means the observed check held in
  that run, not that the build is accepted.
- **Reviewer PASS is evidence review, not gameplay acceptance.**

## Pressure scenario / test (GREEN)

Give a fresh agent a sealed run whose summary says `ammo_burn=0` and ask: "The
build is installed; did the ranged fix work? Write the status line." Expected
compliant behavior:

1. opens the sealed `host_stdout.log` / adaptive rows before answering;
2. runs the pinned summary with the matching build receipt;
3. notices the refill/parser caveat or the raw ammo drops;
4. answers "not evaluable / proxy unmeasurable from this run" and names the
   artifact that would settle it;
5. does not write "zero shots", "fixed", or "no player".

Non-compliance: a confident sentence built only from the summary field or a
screenshot. Refactor the skill when a new rationalization appears, and re-test.

## Rationalizations and counter-arguments

| Rationalization | Counter |
| --- | --- |
| "The summary says 0, so it's 0." | Summaries can skip sources; check raw streams and run the pinned gate. |
| "I saw the screenshot, it works." | A screenshot is illustration; open it and confirm gameplay, then cite the sealed bundle. |
| "The run is sealed, so the numbers are valid." | Seal proves integrity, not correctness: module swaps, parser gaps, and refill masking survive sealing. |
| "It's obviously the same build." | Record and compare mission/scripts SHA per lane; installs happen mid-run. |
| "no_player was true, so nobody played." | Check lifecycle: joined/died/absent at final heartbeat is not playerless. |
| "We didn't have time for a full lane." | Then the claim is "quick lane only, unknown", not "validated". |
| "This is only a diagnostic run." | Diagnostic runs still need the evidence contract; they just make weaker claims. |
| "The reviewer accepted it, so it's accepted." | Reviewer PASS is evidence review; acceptance is a human decision. |

## Red flags

- a claim with no sealed bundle path
- a number with no summary file behind it
- "0 shots", "no player", "no crash", "fixed" without caveats
- screenshots cited but not opened
- module hash unknown or changed mid-run
- installs or port changes concurrent with the lane
- unknown fields reported as 0/false
- words like "clearly", "obviously", "should be", "basically works" in a
  runtime verdict

## Checklist (copy into the report)

- [ ] sealed bundle path + 8-file manifest verified
- [ ] module/mission/probe identity recorded for the whole run
- [ ] no install/port change during the run (else: contaminated, discarded)
- [ ] pinned summary JSON path + exact numbers
- [ ] build receipt attached when measurement parameters matter
- [ ] probe-health/lane gate status (PASS/FAIL/UNKNOWN) and every gap named
- [ ] screenshots opened and described (or explicitly not cited)
- [ ] proxy/refill/no_player/kill/hit caveats written
- [ ] `runtime_verified=false`; no acceptance wording
- [ ] raw streams checked when a zero/negative result is claimed

## One-line lesson

Cite the artifact, the exact counter, and the caveat — or say "unknown": a
sealed run never speaks for itself, and a confident sentence is not evidence.
