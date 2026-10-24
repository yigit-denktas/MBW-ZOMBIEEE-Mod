# Issue #50 crash triage - P0 native-wave City `mbAgent::updateWalkingEffects`

**Status:** docs-only crash triage. **No game launch in this task; no fix applied; no acceptance.**
This report separates **observed** evidence from **hypotheses**, preserves unknowns, and
gives A/D a minimal sealed bisect matrix. Issue #50 remains the blocker; the known-good
module (`f57c800`) remains the only restored state.

- **Observed:** 2026-10-24, Agent E, supporting issue
  [#50](https://github.com/yigit-denktas/MBW-ZOMBIEEE-Mod/issues/50).
- **Crash evidence:** `local/session/CRASH_rgl_log_crash.txt` (copy of D's
  `MountBlade Warband\Logs\rgl_log_24.10.2026_15.56.05_crash.txt`) and
  `local/session/CRASH_dump.dmp`.
- **Sealed run:** `local/session/ai-evidence-task-p0-native-v2/653b9eed...`
  (session `653b9eed17d334ff2877a3806cbc9cf5`).
- **Post-crash relaunch:** `local/session/ai-evidence-CRASH-p0-native-v3/5866ce2e...`
  (32 s, 1 heartbeat; clean startup only, not a fix).

## 1. Crash facts (observed, not inferred)

| Time (local) | Event | Evidence |
| --- | --- | --- |
| 15:53:11 | flight recorder starts; process attach follows | `recorder.json` start `13:53:11Z` |
| 15:53:15 | WSE2 1.174 process/log start | crash log line 1-5 |
| 15:53:28 | `Starting map tbfc_invasion_4 in mode multiplayer_iv` | crash log |
| 15:55:38 | `SCRIPT ERROR: Invalid Agent ID: 0` | crash log line 432 |
| 15:55:38 | `- Lua (line 0, opcode 1765, modifier 0x0)` | crash log line 433 |
| 15:55:38 | `Mission Template [44] mst_multiplayer_iv Trigger [32] Conditions (Lua) (line 0, opcode 5113, ...)` | crash log line 434 |
| 15:56:06 | `EXCEPTION_ACCESS_VIOLATION (0xC0000005, 0x00000000, 0x000000E4)` | crash log line 435 |
| 15:56:06 | `mbAgent::updateWalkingEffects+0x35` at `+0x42B735` | crash log line 437 |
| 15:56:06 | stack: `mbAgent::frameMove+0x60A` -> `mbMission::frameMove+0xBCA` -> `mbTacticalWindow::frameMove+0x917` -> `mbCoreGame::frameMove+0x28C` -> D3D frame -> `WinMain` | crash log lines 437-448 |
| 15:56:23 | v2 recorder ends (`duration_seconds=191.594`, `outcome=stopped`) | `recorder.json` |
| 15:56:54-15:57:27 | post-crash v3 relaunch, 32 s, one heartbeat, no crash | v3 bundle |

**There is one `Invalid Agent ID: 0` line, 28 seconds before the AV.** The script error is
not itself the exception; the exception is an engine-side animation/agent update crash.
The crash log has no engine symbols beyond exported function names; the minidump has no
project-module path strings (only system/module PDB paths), so the exact installed module
identity is **not** proven by the dump.

## 2. Sealed v2 bundle end-state

| Field | Value |
| --- | --- |
| `host_stdout.log` | 121,392 bytes, SHA-256 `57439d4c...64360` |
| `events.jsonl` | lifecycle only (`recorder_ready`, `recorder_listening`, `log_unavailable`, `process_attached`, `process_finished`); **no ZDB1 gameplay events** |
| ZDB1 records | 371: 1 boot, 1 mission_enter, 12 heartbeat, 2 round_started, 4 wave_change, 2 wave_started, 1 tactical_change, 150 ai_sample, 89 combat_sample, 89 agent_sample, 9 defender_died, 1 probe_capability, 1 probe_anomaly |
| last heartbeat | count 12, wave 1, round 0, alive_team0 7, alive_team1 9, scene 516, `speed_modifiers_team1=60:15`, bots_team1 8 |
| final ai sample tick | tick 12: sampled alive team0 2, team1 6 (sampling subset; heartbeat counts differ) |
| wave slots at end | `200:894,221:894,231:894,241:894,245:873` |
| probe lines | `probe_capability|group_convention=unknown`; `probe_anomaly|kind=group_convention_unknown|agent=1` |
| early log artifact | `logs/log_01.txt` ends at `Starting map ...` (14,513 bytes); it does **not** contain the crash tail - the crash log is a separate copy |

So the slot/speed fix did work in the v2 run (slots 894, team-1 speed 60 at wave 1), and
the crash happened later in the same run. The ZDB1 stream stops at or before the crash; no
post-crash heartbeat exists in v2.

## 3. Trigger/opcode correlation

### 3.1 What the crash log says

- Invalid agent at native opcode **1765** (`agent_get_group`) called from **Lua**
  (line 0), surfaced while mission template 44 (`mst_multiplayer_iv`) was executing
  trigger **32** conditions (Lua opcode 5113).
- The AV is in **`mbAgent::updateWalkingEffects`**, called from `mbAgent::frameMove`; this
  is not the opcode itself and is not proof that 1765 is the immediate faulting
  instruction. It is consistent with a **delayed engine-side agent/effect-state fault**
  after an invalid-agent operation.

### 3.2 Trigger 32 vs the build source - unresolved provenance gap

Available build snapshots from this repository contain **27 or 31 triggers**, not 32:

- `_zom-city-build-strict`: 27 triggers (25 original + defender + City guard/order, no
  wave-reinforcement/recovery set).
- `_zom-city-build-base`: 31 triggers (through tactical recovery).
- v2 boot: `ZDB1|boot|...|triggers=31`.
- No mission template snapshot in the workspace has 32 triggers; the crash run's exact
  installed module manifest is not in the sealed v2 bundle.

Therefore **the log's Trigger [32] cannot be mapped to a source trigger from the captured
bundle alone**. Do not assume Trigger 32 is the trigger-15 speed loop. The build receipt /
installed module SHA for the crash run is a required missing artifact (see section 7).

### 3.3 The direct `Invalid Agent ID: 0` candidate: probe `read_group` call convention

C's ledger triage (ZOM-DISC-59) and the current probe code point at the same mechanism:

- `overlay/lua/main.lua` `read_group(agent)` calls `game.agent_get_group` as
  `fn(agent)` - **one argument** (currently lines 254-268; the convention probe uses the
  same single-arg call).
- Native `agent_get_group` is opcode **1765** and its native form is
  `(destination, agent_id)`. The Lua binding's first argument is a placeholder
  destination, so the call can bind **agent_id = 0** - exactly the logged
  `Invalid Agent ID: 0`.
- v2 already shows the probe telling on itself:
  `group_convention=unknown` and `probe_anomaly ... agent=1`.
- The current probe comment in the same file records the historical symptom: a LHS
  placeholder 0 bound as an agent id "spammed `Invalid Agent ID: 0`, corrupting the
  sealed stdout". The guard `agent > 0` checks the Lua value but **does not fix the native
  argument order**; it can still make a native call whose effective agent id is 0.

This is the **strongest evidence-matched hypothesis for the script error**: a probe
call-convention bug, not a P0 speed-loop opcode. The AV remains engine-side and its
causal link to the script error is **unproven**; the 28-second gap and the animation
update stack are consistent with delayed agent-state damage, but not proof.

### 3.4 The P0 speed-loop candidate

The P0 native-wave patch (commit `7610376`, branch `agent/a-p0-native-wave`) appends a
**per-tick** speed loop to **trigger 15** (original 1 s wave controller), not a new trigger:

```
2133 speed=55; 2122 speed += wave*5; 2120; 4/32 cap 100; 2133 cap
12 try_for_agents; 1702 agent_is_alive; 1707 agent_is_non_player;
1770 agent_get_team; 31 team==1; 2093 agent_set_speed_modifier; 3 try_end
```

Source: `tools/native_wave_patch.py` `_speed_ops` / `patch_mission_text`. It uses setter
2093, **not** getter 1765, and includes alive/non-player/team guards but no explicit
positive-id/active guard. It is a real per-tick risk, but the crash log's opcode does not
implicate it directly. It remains the primary **bisect** target because it is the P0
change under test and per-tick; it should be isolated, not assumed.

### 3.5 Other 1765 sites

`1765` also appears in native per-tick loops:

- tactical recovery trigger (3 s, appended as part of the 31-trigger path):
  `try_for_agents` -> alive -> non-player -> team 0 -> `agent_get_group` (1765) ->
  division range check; then fallback/regroup.
- private commands (4 optional host-control triggers; not default) use the same
  `1765` group read.

These are secondary 1765 candidates if trigger-index mapping or build configuration
differs from the v2 snapshot.

## 4. Per-tick vs one-shot P0 operations

From the 31-trigger build shape (`_zom-city-build-base`; A branch commit `7610376`
changes the original trigger 14/15 path):

| Trigger | Cadence | P0 operation class | Ops relevant to agents/state | Risk |
| --- | --- | --- | --- | --- |
| 14 | original one-shot/periodic wave-table writer (prefix `-19`, no conditions) | **wave table writes** | 40+ `502 faction_set_slot`; four invalid faction writes redirected to slot 245 | one-shot setting; no agent pointers |
| 15 | **1 s** original wave controller | **P0 appends per-tick speed loop** | `2133`, `2122`, `2120`, `4/32`, `12 try_for_agents`, `1702 alive`, `1707 nonplayer`, `1770 team`, `31`, **`2093 set_speed_modifier`** | per-tick agent write; no invalid-id/active guard |
| 25 | one-shot (`-20`) | survivor spawn (defender patch) | spawn ops | one-shot |
| 26 | **5 s** | City order + older speed loop (base snapshot) | `502` wave slots; speed locals/`2093`; team-0 try loop `12/1702/1707/1770/31/2119/2120/1783/1766/1780/1791/1790/1727/3343/3314` | per-tick orders and agent group/division writes; uses 1766 (setter), not 1765 |
| 27 | one-shot (`-20`) | wave reinforcement init | globals only | one-shot |
| 28 | **4 s** | wave reinforcement | agent scan / `1265 add_visitors` / order setup | per-tick spawn/agent scan |
| 29 | one-shot (`-20`) | tactical recovery init | globals only | one-shot |
| 30 | **3 s** | tactical recovery | `12/1702/1707/1770/31/1765/33` + order writes | per-tick **1765 getter** with alive guard; secondary candidate |

The exact crash build (7610376 with A's patch) is expected to replace the trigger-26 speed
loop with the trigger-15 append, but that built artifact is not sealed; do not merge these
two build shapes in a causal claim.

## 5. Known Warband/WSE2 crash modes that match the evidence

| Mode | Match to this crash | Confidence |
| --- | --- | --- |
| **Fake/placeholder agent id 0** in a Lua/native agent getter; engine logs `Invalid Agent ID: 0` and continues | Exact opcode 1765 + Lua context; project documented this symptom before (DIAGNOSTICS R-crash rule and probe comments); v2 probe anomalied on group convention | **high** for the script error |
| **Delayed engine-side AV in agent animation/frame update** after invalid agent operation (dangling/partially-updated agent, effect list) | AV in `mbAgent::updateWalkingEffects`, 28 s after the script error; stack through `mbAgent::frameMove`/`mbMission::frameMove` | plausible; **causality unproven** |
| **Dead-agent race in a per-tick `try_for_agents` loop** (alive check then getter/setter; agent dies in same tick) | P0 speed loop and tactical recovery both call agent ops in per-tick loops; no crash log line implicates 2093 or 1765 loop directly | possible; needs bisect |
| **Invalid command/order target** (team/division/agent writes) | City order trigger writes divisions/groups; no invalid-agent line from those ops | low |
| **Renderer/GPU or Steam overlay AV** independent of script | Stack passes through game frame; no evidence of render fault; invalid-agent precursor exactly matches a known mode | low/unlikely |

**Do not claim** that the speed loop is the root cause, that the probe is the root cause of
the AV, or that the AV is benign. The script error and AV are separate observed events;
the causal bridge is unknown and must be tested.

## 6. Minimal bisect matrix for A/D (no loop / one-shot / per-tick with guards)

All rows are sealed D runs of the same City scenario/build base where possible. A owns
the build variants; D seals each run with crash log + dump + module receipt. **No game
launch by E.** A single change per row; do not combine loop and probe changes.

| # | Probe `read_group` | Trigger-15 speed loop | Other per-tick loops | Purpose / discriminator |
| --- | --- | --- | --- | --- |
| 0 | Current fixed guard + **correct call** `(dest, agent)` or wrapper | **No loop** (stock trigger 15; no 2093 append) | Stock only | Known-good behavior / control; must not log invalid agent |
| 1 | **Old single-arg** `fn(agent)` (reproduce) | **No loop** | Stock only | Prove the probe convention alone produces `Invalid Agent ID: 0`; observe whether AV follows |
| 2 | **Correct call** | **No loop** | Stock only | If 1 crashes and 2 does not, probe is the script-error cause; AV causality still needs row 3-5 |
| 3 | Correct call | **One-shot** (apply speed once at wave start/spawn; no per-tick 2093) | Stock only | Isolate one-shot state change; no repeated agent writes |
| 4 | Correct call | **Per-tick with alive/non-player/team guard** (current `_speed_ops`) | Stock only | Reproduce P0 per-tick loop without probe noise |
| 5 | Correct call | **Per-tick with strict valid-id guard** (agent >0, active/alive re-check immediately before 2093, skip invalid; bounded fallback) | Stock only | If 4 crashes and 5 does not, the loop/guard is the factor |
| 6 | Correct call | Per-tick current | **Tactical recovery disabled** | Isolates the only other native 1765 per-tick loop |
| 7 | Correct call | Per-tick strict | **City order trigger disabled** (no team/division/order writes) | Isolates per-tick order/agent writes from speed setter |
| 8 | Correct call | Per-tick strict | **All P0 agent loops disabled** (only wave-table trigger 14) | Isolates wave-table writes and non-agent P0 changes |

**Pass/fail for each row:** no `Invalid Agent ID: 0`; no `EXCEPTION_ACCESS_VIOLATION`;
stable heartbeat through the run; crash log/dump sealed; module SHA + trigger count
recorded. Any crash **must** be reported with its bundle + exact build receipt, not merged
into a generic "P0 crashes" claim.

Suggested order: **1 -> 2 -> 3 -> 4 -> 5**, then 6/7/8 only if rows 4-5 still crash.
This tests probe-first (strong evidence) before changing A's loop.

## 7. Required evidence / task gaps

1. **Exact installed module identity for the crash run** (build 7610376): module SHA,
   `ZOMBIEEE_REMASTER.json`, trigger count, mission template trigger map. The v2 bundle
   has 31-trigger boot and no module receipt; crash log says Trigger 32; the mismatch
   must be resolved before naming a trigger.
2. **C probe fix:** correct `read_group` native call convention (destination placeholder +
   real agent id; or a documented wrapper), never call 1765 with a bare agent as the first
   argument; keep/verify invalid/dead-id guard; add a negative unit test for id 0 and a
   one-shot capability probe that does not spam.
3. **A loop decision:** one-shot vs per-tick speed; if per-tick, add explicit valid-id
   guard and bound the effect; no 2093 on invalid/dead agent; keep trigger-15 cadence
   evidence in the receipt.
4. **Remove the other 1765 ambiguity:** either disable tactical recovery's group read in
   the bisect build or document that it is not in the crash build.
5. **D sealed bisect runs** per section 6; crash log + dump + bundle + trigger map per row.
6. **No P0 seal/relaunch** until the crash is root-caused and the known-good f57c800 path
   is preserved (issue #50 requirement).

## 8. Recommendations (no fix applied here)

- **Immediate:** stop P0 seals/relaunches; keep f57c800 known-good.
- **First fix candidate:** C's probe `read_group` convention - the log opcode and v2
  capability/anomaly match it directly. Fix it before blaming the speed loop.
- **Then:** bisect A's trigger-15 loop (no loop -> one-shot -> per-tick with strict
  guard); keep tactical recovery/city orders out of the comparison or run them as
  separate rows.
- **Do not** add a blanket `--feature-branch` or release-metadata exception for a crashing
  build; no release claim until the crash is gone and D seals the matrix.
- **Do not** treat the v3 post-crash 32 s relaunch as a fix; it only shows the engine can
  start after the crash.

## 9. Non-claims

No game was launched by this task. No root cause is accepted; no crash is fixed; no
availability/acceptance/legal claim is made. The exact Trigger [32] mapping is unresolved
because the crash-run module receipt is missing. The script error and AV are observed;
the causal link, and the relative contribution of probe vs speed loop, are unknown until
the section 6 matrix is sealed.
