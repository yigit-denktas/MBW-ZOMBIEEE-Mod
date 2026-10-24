# Bot-vs-bot round and balance analysis - D sealed bundles

**Status:** read-only statistical analysis of sealed telemetry. **No game launch by this
task.** No acceptance, no causal conclusion, no balance clearance. Derived metrics are
descriptive and bounded by the gaps listed in section 8; `runtime_verified=false` remains.

- **Observed:** 2026-10-24, Agent E, task-69.
- **Inputs:** D's sealed bundles under `local/session/ai-evidence-*` and launcher-sealed
  flights under `_zom-d-profiles/local/session/play-city/flights/*`; each has
  `manifest.json` (`zombieee.flight.v1` sha256 table), `recorder.json`, and
  `host_stdout.log` containing the `ZDB1|...` stream.
- **Analyzer:** C's canonical `tools.telemetry_studio balance` (schema
  `zombieee.balance-analysis.v1`) from branch `agent/c-task65-balance` @ `f30cec8`;
  canonical parser `tools/receipt_summary.py`/`tools/diagnostics.py`. The analyzer was
  run read-only on the bundles; its per-window outcomes and lower-bound troop
  contributions are the statistical base for this report.
- **Machine-readable tables:** [`bot_vs_bot_runs.csv`](bot_vs_bot_runs.csv),
  [`bot_vs_bot_round_windows.csv`](bot_vs_bot_round_windows.csv),
  [`bot_vs_bot_troop_contributions.csv`](bot_vs_bot_troop_contributions.csv),
  [`bot_vs_bot_gaps.csv`](bot_vs_bot_gaps.csv).

**Important:** `events.jsonl` in a sealed bundle contains only recorder lifecycle records
(`recorder_ready`, `process_attached`, `log_unavailable`, ...). The gameplay stream is in
`host_stdout.log`. Do not analyze `events.jsonl` for rounds, KD or classes.

## 1. Dataset and inclusion rules

Included (canonical per D):

| Role | Bundle/session | Why included |
| --- | --- | --- |
| `P0-clean` | `local/session/ai-evidence-task55-p0/257b29b1...` | current P0-clean run; scene/slots evidence; zero engine errors in captured stream |
| `wave-progression` | `local/session/ai-evidence-task45-wave2/d7bfc372...` | only run with waves 1-4 observed |
| `wave2b` | `local/session/ai-evidence-task44-wave2b/b9241c71...` | wave-2 evidence after the 896 leak fix |
| `launcher-sealed` | six flights under `_zom-d-profiles/.../play-city/flights/<session>` | sealed launcher receipts; module SHA, weak-wave1 enemy profile, defender-squad rotation, city-only, 31 triggers |

Excluded from statistics (kept as history only):

- `ai-evidence-*canon*`, `ai-evidence-final-*`, `ai-evidence-disc28*`,
  `ai-evidence-wave2*-attempt` - pre-fix/limited heartbeats or no sealed heartbeats.
- `ai-evidence-task44-wave2` - explicitly pre-task43 probe per D; do not mix with the
  later wave2b.
- `ai-evidence-task45-ammo` - interrupted by a module swap; mixed provenance.
- No-client/pre-round-only bundles: no heartbeats, so no round or class statistics.

## 2. Run inventory

`rounds` below are **C analyzer round segments**, not official match rounds: ZDB1 has no
round-end event and round identity is unstable, so segment counts are a bounded view.
`team1 wins` are only called when observed team-0 alive = 0 and team-1 alive > 0.

| Role | Session prefix | Module/build | Windows | Team1 wins | Reset / unknown | Max wave | Mean end alive0 |
| --- | --- | --- | ---: | ---: | ---: | ---: | ---: |
| wave2b | `b9241c71` | unknown (evidence bundle) | 32 | 2 | 17 / 13 | 1 | 6.56 |
| wave-progression | `d7bfc372` | unknown (evidence bundle) | 29 | 2 | 16 / 10 (+1 mutual wipe) | 4 | 6.56 |
| P0-clean | `257b29b1` | unknown (evidence bundle) | 29 | 2 | 18 / 9 | 1 | 6.06 |
| launcher-sealed | `095d3b4a` | `5e506492...` | 31 | 3 | 15 / 13 | 1 | 6.16 |
| launcher-sealed | `1f99593c` | `db296ad0...` | 21 | 5 | 9 / 7 | 1 | 4.54 |
| launcher-sealed | `684864b6` | `db296ad0...` | 12 | 1 | 5 / 6 | 1 | 5.71 |
| launcher-sealed | `b04f47f6` | `d87afb5f...` | 20 | 1 | 13 / 6 | 2 | 6.00 |
| launcher-sealed | `bfd6876b` | `7e0b3a6b...` | 30 | 3 | 18 / 9 | 1 | 5.89 |
| launcher-sealed | `ee8c7f88` | `db296ad0...` | 9 | 0 | 5 / 4 | 1 | 7.40 |

Full per-run fields (heartbeat coverage, engine errors, durations, positioning,
lower-bound kill counters) are in `bot_vs_bot_runs.csv`. The six flights share
`enemy_profile=weak-wave1`, `rotation_profile=defender-squad`, `map_scope=city-only`,
`trigger_count=31`; module SHA differs, so they are **not controlled variants**.

## 3. Round outcomes, wipe and KD

Across the 9 runs, C's analyzer produced **213 segmented windows**:

| Outcome | Count | Meaning |
| --- | ---: | --- |
| `round_reset_no_wipe` | 116 | window reset with both teams alive; **not** a win/wipe claim |
| `unknown` | 77 | no usable boundary/end state; **not zero** |
| `team1_win` | 19 | observed team-0 alive = 0, team-1 alive > 0 |
| `mutual_wipe` | 1 | both observed alive = 0 |
| `team0_win` | **0** | no window with team-1 alive = 0 while team-0 alive > 0 |

- **No team-0 win was observed in any included run.** 19 team-1 wins were observed; the
  remaining 194 windows are reset/unknown or mutual wipe, not evidence of a draw.
- Team-0 "win rate on known windows" is 0.0 in every run where it is defined; team-0
  wipe rate on known windows is 1.0 for most runs (0.667 for wave-progression;
  undefined for `ee8c7f88`, which had no known win/wipe window). These rates rest on
  **2-5 known windows per run**
  and must not be presented as a stable win probability.
- Because round identity is unstable and there is no explicit round-end event, the 19
  losses are **observed segment losses**, not an official series score.

### KD is not measurable from this stream

C's canonical parser warns and this analysis confirms: `kills_*` are **agent lifetime
kill counters summed over observed agents**, not session kills and not a KD ratio.
Troop contributions are a **lower bound** from max observed lifetime kills per sampled
agent. Across the included runs the lower bounds are **team-0 = 104 kills** and
**team-1 = 129 kills**; that is not a KD ratio and cannot be used as one. True hit,
damage, death and assist attribution is absent (section 8).

## 4. Survival and time trends

- Mean end-alive0 ranges **4.54-7.40** across runs, but windows ending at a reset inflate
  this; median end-alive0 is 8 for most runs. It is **not** survival time.
- `wall_clock_seconds` is `null` for every window: ZDB1 lines carry no timestamps, so
  wall-clock survival, time-to-first-death and time-to-wipe are **unknown**. Do not infer
  them from heartbeat counts without a measured cadence.
- Observed waves: most runs reach wave 1 only; `wave-progression` reaches wave 4,
  `b04f47f6` reaches wave 2. No run has a complete wave series with a documented end.
- Within a session, team-1 observed strength rises from ~7-8 to 14-25 by wave 1 while
  team-0 stays at ~8-9; team-0 losses cluster in those windows. This is a **within-run
  descriptive pattern**, confounded by spawn timing, wave composition and missing
  parameters; it is not a time-trend estimate.
- Runs span different builds and launcher profiles. Any "newer run performs better"
  reading is confounded by build/module changes; no controlled time trend is claimed.

## 5. Class/troop contributions (lower bound)

Aggregated over the included runs (sampled agents; max observed lifetime kills per
agent, summed by troop; **lower bound, not per-death attribution**):

| Team | Troop | Name | Agents sampled | Kills lower bound | Kills/agent (bound) |
| --- | ---: | --- | ---: | ---: | ---: |
| team0 | 981 | `trp_zdr_commando_bot` | 45 | 26 | 0.58 |
| team0 | 982 | `trp_zdr_sniper_bot` | 43 | 25 | 0.58 |
| team0 | 983 | `trp_zdr_scout_bot` | 38 | 23 | 0.61 |
| team0 | 984 | `trp_zdr_lumberjack_bot` | 28 | 30 | **1.07** |
| team1 | 894 | `trp_invader1_multiplayer_ai` | 219 | 119 | 0.54 |
| team1 | 895/896/898 | extra invader troops seen in one run | 1-6 each | 2-5 each | small N |

What this supports: the lumberjack troop has the highest **observed lower-bound**
kills/agent among the four default defender classes in this sample (1.07 vs 0.58-0.61).
What it does **not** support: a claim that lumberjacks are better, that changing the
class mix would improve outcomes, or per-class survival/death rates. The sample is small,
weapons/ammo/class assignment vary by build, AI samples stop for dead agents, and there is
no per-troop death count. `bot_vs_bot_troop_contributions.csv` carries per-run rows.

## 6. Positioning and map relevance

C's analyzer reports sampled `ai_sample` positions per run:

- Team-0 centroid range roughly **(161-176, 166-180)**; spread RMS **9.6-18.9**.
- Team-1 centroid range roughly **(147-162, 138-152)**; spread RMS **25.5-37.7**.
- Team-1 bbox covers the southern approaches; team-0 samples sit north of them. This is
  consistent with the City map design's northern anchor/southern approach reading, but
  position samples are sparse, no LOS/collision/cover is measured, and dead-agent
  positions are absent. It is **not** proof of holding a line or of spawn fairness.

## 7. Ranked small changes - experiments, not causal recommendations

C's balance analyzer with **no parameter receipts** returns **no ranked causal
recommendations**; it explicitly reports parameter-metadata missing and requires a new
sealed run. The table below is therefore a **feasibility-ranked experiment backlog**
derived from the descriptive gaps, not a sensitivity result. Confidence is deliberately
low.

**A's contract (2026-10-24) constrains what is actually runnable today:** `--defender-target`
is validated only **1-8** (cap 12 is the in-mission growth cap, not a build value), so
8 -> 9 is **not a valid build**; wave-1 visitor counts are hard-coded in the compiled
controller (no build flag); ammo is fixed at 8 stacks (9 is a loadout-code change, not a
parameter); class mix has no flag; and a north-anchor hold experiment is gated on
team-order adoption evidence (task-53/61), not testable yet. Minimum receipt for any run:
build SHA, `defender_target`, `defender_reinforce`, `wave_visitors`, `defender_orders`,
`defensive_line`, `team0_class_mix`, `ammo_stacks`, `fire_mode` (when F lands it), speed
profile, sealed bundle id.

| Rank | Candidate | Feasibility today | Evidence basis | Confidence | Next gate/run |
| ---: | --- | --- | --- | --- | --- |
| 0 | **P0 native-speed/slot seal** (A lane) | prerequisite, not a balance change | pause balance changes until native speed/faction-slot evidence is sealed | n/a | A/D seal first |
| 1 | Defender target **4 vs 8** (not +1) | **testable now** on the same P0 build; `defender_reinforce=default` | team-0 ~8-9 vs team-1 14-25; 19 team-1 wins, 0 team-0 wins | low | 4+ sealed runs per value, receipt `defender_target` |
| 2 | Class-mix variants (one slot) | **blocked** until a `team0_class_mix` parameter + receipt exists | lumberjack 1.07 vs 0.58-0.61 lower-bound kills/agent (small N) | very low | tooling task, then controlled run |
| 3 | Ammo stacks **8 vs 9** (one class) | **blocked** until loadout code supports `ammo_stacks` + receipt | lower-bound ranged-class kills vary; ammo not attributed | low | loadout task, then controlled run |
| 4 | Wave-1 pressure **-1/-2 or stagger** | **blocked**: counts are hard-coded in the compiled controller | all 19 team-1 wins are in max-wave 0-1 windows; team-1 jumps 7/8 -> 14-25 | low | trigger-15 count patch + receipt, then run |
| 5 | North-anchor **hold/regroup** or spawn-fairness | **gated** on task-53/61 order-adoption evidence; not causal today | team-0 centroid north, team-1 southern; hold adoption unobserved | very low | adoption evidence first, then D measurement |

Ranking is by **feasibility and expected information gain**, not expected effect size.
Every item requires the parameter receipt above; otherwise it is a hypothesis, not a
finding. No item is an approved run or an acceptance claim.

## 8. Unmeasured variables -> new tasks

From C's `gaps_as_tasks` plus the gaps observed here:

| # | Missing measurement | Why it matters | Suggested lane | Priority |
| ---: | --- | --- | --- | --- |
| 1 | Explicit round-end/winner event or documented boundary, stable round ID | 77/213 windows are `unknown`; round segments are unstable | C/D | high |
| 2 | Per-hit/per-death attribution or kill-event stream | no true KD, damage, assists, class death attribution | C/D | high |
| 3 | Wall-clock round survival/time-to-death | ZDB1 has no timestamps; survival time unknown | C/D | high |
| 4 | Build/parameter receipt in every sealed bundle | no controlled variants; module SHA only on launcher flights | B/D/F | high |
| 5 | Per-troop deaths/alive counts per round | class contribution currently lower-bound kills only | C/D | medium |
| 6 | Spawn/entry timestamps and team entry fairness | spawn protection/fairness cannot be evaluated | C/D/A | medium |
| 7 | Enough per-round position samples for formation spread | positioning is aggregate, not round-by-round | C/D | medium |
| 8 | Kill-counter semantics (lifetime reset, unknown agents) | 104 vs 129 lower-bound totals are not KD | C | high |
| 9 | Wave composition: native visitors vs configured bots | wave-1 pressure cannot be attributed | A/C/D | medium |
| 10 | Human/no-human mode normalization | launcher flights mix players=0/1; no-client heartbeats differ | D/C | low |
| 11 | Class/troop identity for extra team-1 troops (895/896/898 etc.) | team-1 class shares are single-run and unverified | C | low |
| 12 | Controlled variant protocol + seed/build hash receipt | shared weak-wave1/defender-squad profiles are not variants | Lead/D | high |

These are proposed follow-up tasks, not accepted defects; no new acceptance state is
created here.

## 9. Coordination and reproducibility

- **C:** the `balance` analyzer (schema `zombieee.balance-analysis.v1`) is the canonical
  statistical base. It is on branch `agent/c-task65-balance` @ `f30cec8`, not yet on
  main; confirm/merge it and freeze the JSON schema before release metadata cites it.
  The analyzer intentionally returns no causal recommendations without parameter
  receipts; that behavior is correct and is preserved in this report.
- **D:** canonical paths used: `task55-p0` (P0-clean), `task45-wave2` (wave progression),
  `task44-wave2b` (wave2b), plus six launcher-sealed flights with receipts. The three
  evidence bundles lack a sealed build receipt; do not infer build/parameter values from
  task names. No historical/pre-fix bundle is mixed in.
- **A:** supplied the 2026-10-24 feasibility contract in section 7. Only defender target
  **4 vs 8** is testable on the current P0 build; class-mix, ammo-stacks and wave-1
  pressure need tooling/controller changes first, and the north-anchor hold experiment is
  gated on task-53/61 order-adoption evidence. These are proposals, not approved runs.
- **Reproduction:** run C's analyzer from the branch worktree:

```text
python -m tools.telemetry_studio balance <sealed-session-1> ... <sealed-session-n> \
  --json   # no --params: no controlled variants, no ranked causal recommendations
```

The tables were generated from the analyzer's JSON plus the launcher receipts' known
parameters (module SHA, enemy profile, rotation profile, map scope, trigger count).
`wall_clock_seconds` is always null in the analyzer output.

## 10. Non-claims

- No game was launched by this task; no acceptance, balance clearance, win-rate claim,
  causal claim or release-readiness claim is made.
- Round outcomes are **bounded observations** from unstable segments, not official match
  results. Unknown windows are unknown, not draws or zero kills.
- Kill/class numbers are **lower bounds** from lifetime counters, not KD. Positioning is
  sampled coordinates, not LOS, cover or hold proof.
- `runtime_verified=false`; all remaining measurements stay pending until the tasks in
  section 8 land and a new sealed run is captured.
