# Issue #50 crash triage - P0 native-wave City `mbAgent::updateWalkingEffects`

**Status:** docs-only crash triage. **No game launch in this task; no fix applied; no acceptance.**
This report separates observed evidence from hypotheses, preserves unknowns, and gives A/D
a minimal sealed bisect matrix. Issue #50 remains the blocker; the known-good module
(`f57c800`) remains the only restored state.

- **Observed:** 2026-10-24, Agent E, supporting issue
  [#50](https://github.com/yigit-denktas/MBW-ZOMBIEEE-Mod/issues/50).
- **Crash evidence:** `local/session/CRASH_rgl_log_crash.txt` (copy of D's
  `rgl_log_24.10.2026_15.56.05_crash.txt`) and `local/session/CRASH_dump.dmp`
  (266,377 bytes, SHA-256 `80067212...9867b3a`).
- **Sealed run:** `local/session/ai-evidence-task-p0-native-v2/653b9eed...`
  (session `653b9eed17d334ff2877a3806cbc9cf5`; host log SHA-256 `57439d4c...64360`).
- **Post-crash relaunch:** `local/session/ai-evidence-CRASH-p0-native-v3/5866ce2e...`
  (32 s, one heartbeat; clean startup only, not a fix).
- **A-supplied crash module facts (2026-10-24, not independently re-derived here):**
  parked module `Modules\ZOMBIEEE_Remaster.crashed-p0-155717`, branch
  `agent/a-p0-native-wave` @ `7610376`; module receipt SHA-256
  `ac464785b8da83408997c7b93be0a9867341fc05cd9e8577ee80e974ca5a577b`; mission
  `mission_templates.txt` SHA-256
  `a569d02ae4a0c65a145c24a1bd20ac3f82ad77b9a5d9d85eb0158a2edc945b2f`; 25 original
  triggers -> **31 compiled triggers**; native-wave speed loop appended; tactical
  recovery enabled with `guard_groups=[5,6,7]`; wave reinforcements enabled.

## 1. Crash facts (observed)

| Time (local) | Event | Evidence |
| --- | --- | --- |
| 15:53:11 | flight recorder starts; process attach follows | v2 `recorder.json` start `13:53:11Z` |
| 15:53:15 | WSE2 1.174 process/log start | crash log lines 1-5 |
| 15:53:28 | `Starting map tbfc_invasion_4 in mode multiplayer_iv` | crash log |
| 15:55:38 | `SCRIPT ERROR: Invalid Agent ID: 0` | crash log line 432 |
| 15:55:38 | `- Lua (line 0, opcode 1765, modifier 0x0)` | crash log line 433 |
| 15:55:38 | `Mission Template [44] mst_multiplayer_iv Trigger [32] Conditions (Lua) (line 0, opcode 5113, ...)` | crash log line 434 |
| 15:56:06 | `EXCEPTION_ACCESS_VIOLATION (0xC0000005, 0x00000000, 0x000000E4)` | crash log line 435 |
| 15:56:06 | `mbAgent::updateWalkingEffects+0x35` at `+0x42B735` | crash log line 437 |
| 15:56:06 | stack: `mbAgent::frameMove+0x60A` -> `mbMission::frameMove+0xBCA` -> `mbTacticalWindow::frameMove+0x917` -> `mbCoreGame::frameMove+0x28C` -> D3D frame -> `WinMain` | crash log lines 437-448 |
| 15:56:23 | v2 recorder ends (`duration_seconds=191.594`, `outcome=stopped`) | v2 `recorder.json` |
| 15:56:54-15:57:27 | post-crash v3 relaunch, 32 s, one heartbeat, no crash | v3 bundle |

**One `Invalid Agent ID: 0` line, 28 seconds before the AV.** The script error is not
itself the exception; the exception is an engine-side agent animation/frame update crash.
The minidump has no project-module path strings (only system/module PDB paths), so the
exact installed module identity is **not** proven by the dump; it is supplied by A's
receipt (above).

## 2. Trigger 32 is the probe heartbeat trigger, not a compiled mission trigger

A's key correction, independently corroborated by the v2 boot stream and current Lua:

- `overlay/lua/main.lua` registers two Lua triggers through **`game.addTrigger`**:
  an entry trigger at **1 s** and a heartbeat trigger at **15 s** (lines 792 and 877 in
  current main).
- v2 boot reports `triggers=31` (compiled) and:
  `probe_registered|kind=entry|index=31`;
  `probe_registered|kind=heartbeat|index=32`.
- The crash log's **Trigger [32] Conditions (Lua)** is therefore the **probe heartbeat
  Lua trigger**, not a compiled mission trigger. `Mission Template [44]` is the template
  id, not a trigger count.

So the earlier "v2 boot 31 vs log 32" is **not** an installed-module mismatch. The
compiled mission has 31 triggers; the probe adds its own Lua trigger at index 32.

## 3. Sealed v2 bundle end-state

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

The slot/speed fix worked in v2 (slots 894, team-1 speed 60 at wave 1); the crash came
later in the same run. ZDB1 stops at or before the crash; v2 has no post-crash heartbeat.

## 4. Crash-build confound: tactical recovery's own 1765 loop is present

A reports the crash build (receipt `ac464...`) has `experimental_tactical_recovery.enabled=true`
with **`guard_groups=[5,6,7]`**, and wave reinforcements enabled. The tactical recovery
trigger is a **3 s per-tick loop** that calls `agent_get_group` (native **1765**) inside
`try_for_agents` after alive/non-player/team checks (`tools/tactical_recovery.py`). So the
crash build contains **two** relevant per-tick paths:

1. probe heartbeat `read_group` -> native 1765 (Lua trigger 32);
2. tactical recovery native 1765 group read (compiled trigger, 3 s).

The clean bisect package from A removes both tactical-recovery and wave-reinforcement
triggers (27 triggers, no 1765 recovery loop), leaving the speed loop as the only new
per-tick P0 change. That is the right first comparison.

## 5. The probe `read_group` call-convention bug

Current main `overlay/lua/main.lua` still calls:

```lua
local ok, first, second = pcall(function() return fn(agent) end)
```

for `game.agent_get_group`, in both the convention probe and the post-detection read.
Native opcode **1765** is `(destination, agent_id)`; the Lua binding's first argument is
a placeholder destination, so this call can bind **agent_id = 0** - exactly the logged
`Invalid Agent ID: 0`. The current guard checks the Lua `agent > 0`, but that does not fix
the native argument order. v2's own probe lines (`group_convention=unknown`; anomaly at
agent=1) show the probe already doubted its own call.

C's unfrozen fix branch `agent/c-invalid-agent-guard` @ `2e837c2` corrects this:

- parent `39aa3a7` changes `read_group` to `fn(0, agent)` and adds an `agent_live` guard;
- `4e888a0` adds "never call agent ops with id 0 in trigger-32 condition path";
- `2e837c2` is the metadata-only head revision.

This is the **strongest evidence-matched hypothesis for the script error**: a probe
call-convention bug, not a P0 speed-loop opcode. The 28 s-later AV remains engine-side and
its causal link to the script error is **unproven**.

## 6. The P0 speed loop (bisect target, not yet implicated)

A's P0 native-wave patch (commit `7610376`, branch `agent/a-p0-native-wave`) appends a
**per-tick** speed loop to original **trigger 15** (1 s wave controller):

```
2133 speed=55; 2122 speed += wave*5; 2120; 4/32 cap 100; 2133 cap
12 try_for_agents; 1702 agent_is_alive; 1707 agent_is_non_player;
1770 agent_get_team; 31 team==1; 2093 agent_set_speed_modifier; 3 try_end
```

Source: `tools/native_wave_patch.py` `_speed_ops` / `patch_mission_text`. It uses setter
**2093**, not getter **1765**, and has alive/non-player/team guards but **no explicit
agent-id>0 guard** (A says added afterwards). It is a real per-tick risk, but the crash
log's opcode does not implicate it directly. It remains the main **bisect** target.

A's chosen direction (proposal, not implemented): keep per-tick speed **only for the
bisect**; if it reproduces, production speed control should be a **one-shot on wave
transition/after spawn** with valid-id + alive guard, not a 1 s setter loop.

## 7. Per-tick vs one-shot P0 operations

From the 31-trigger build shape (A's crash receipt; base snapshot for op detail):

| Trigger | Cadence | Class | Relevant ops | Risk |
| --- | --- | --- | --- | --- |
| 14 | one-shot/initial wave table | **wave table writes** | 40+ `502 faction_set_slot`; four invalid faction writes redirected to slot 245 | sets slots; no agent pointers |
| 15 | **1 s** | original wave controller + **P0 speed append** | `2133`, `2122`, `2120`, `4/32`, `12 try_for_agents`, `1702`, `1707`, `1770`, `31`, **`2093`**, `3` | per-tick agent write; no explicit id>0 guard |
| 25 | one-shot (`-20`) | survivor spawn | spawn ops | one-shot |
| 26 | **5 s** (base shape) | City orders + older speed loop | `502`; speed locals/`2093`; team-0 order/count loop (`12/1702/1707/1770/31/2119/2120/1783/1766/1780/1791/1790/1727/3343/3314`) | per-tick order/agent writes; uses 1766 setter |
| 27 | one-shot (`-20`) | wave reinforcement init | globals | one-shot |
| 28 | **4 s** | wave reinforcement | agent scan / `1265 add_visitors` / orders | per-tick spawn/agent scan |
| 29 | one-shot (`-20`) | tactical recovery init | globals | one-shot |
| 30 | **3 s** | tactical recovery | `12/1702/1707/1770/31/1765/33` + orders | per-tick **1765 getter**; present in crash build |
| probe entry | 1 s Lua | probe pre-round sampling | agentsIt/read-only | could run before round |
| probe heartbeat | **15 s Lua** | probe telemetry | agentsIt + `read_group` (1765) | **Trigger 32; script-error site** |

The clean pair (no recovery/wave) has no trigger-30 1765 loop; the full pair includes it.
Do not merge the clean and full shapes in a causal claim.

## 8. Known Warband/WSE2 crash modes that match the evidence

| Mode | Match | Confidence |
| --- | --- | --- |
| **Fake/placeholder agent id 0 in a Lua/native getter**; engine logs `Invalid Agent ID: 0` and continues | Exact 1765/Lua context at probe Trigger 32; project documented this symptom before (DIAGNOSTICS crash rule; probe comments); v2 probe anomalied on group convention | **high** for the script error |
| **Delayed engine-side AV in agent animation/frame update** after invalid agent operation (dangling/partially-updated agent/effect list) | AV in `mbAgent::updateWalkingEffects`, 28 s after the script error; stack through `mbAgent::frameMove`/`mbMission::frameMove` | plausible; **causality unproven** |
| **Dead-agent race in per-tick `try_for_agents` loop** (alive check then getter/setter; agent dies in same tick) | triggers 15/30 and probe heartbeat all run per-tick agent ops; no log line directly implicates 2093 | possible; needs bisect |
| **Invalid command/order target** (team/division/agent writes) | trigger 26/30 write divisions/groups; no invalid-agent line from those ops | low |
| **Renderer/GPU/Steam overlay AV** independent of script | stack passes through game frame; invalid-agent precursor exactly matches a known mode | low/unlikely |

Do not claim the speed loop is the root cause, that the probe is the root cause of the AV,
or that the AV is benign. The script error and AV are separate observed events; the causal
bridge is unknown.

## 9. Minimal bisect matrix for A/D

A supplied two package pairs from branch `9b97e15` (packages not located in this shared
workspace; ask A for absolute paths before D runs):

- **clean pair:** `...\p0bisect\clean-off` and `clean-on` - 27 triggers, **no tactical
  recovery and no wave reinforcement**; speed loop off/on.
- **full pair:** `...\p0bisect\build-off` and `build-on` - recovery/wave enabled; speed
  loop off/on (matches the crash build shape more closely).

D should seal **clean-off vs clean-on with C's corrected probe (`2e837c2`) first**. If
clean-off crashes, the probe/other path is implicated; if only clean-on crashes, the speed
loop is implicated.

| # | Build | Probe | Speed loop | Other loops | Purpose |
| ---: | --- | --- | --- | --- | --- |
| 1 | clean-off (`9b97e15`) | **corrected** `2e837c2` | **off** | none (no recovery/wave) | control; must be crash-free |
| 2 | clean-on (`9b97e15`) | corrected | **per-tick with alive/non-player/team guard** | none | isolates the trigger-15 speed loop |
| 3 | clean-off | **old single-arg** `fn(agent)` | off | none | reproduces probe invalid-agent path only |
| 4 | clean-on | **old single-arg** | per-tick | none | probe + loop without recovery confound |
| 5 | clean-on | corrected | **one-shot** on wave transition/spawn | none | discriminates one-shot vs per-tick |
| 6 | clean-on | corrected | per-tick + **explicit valid-id>0 guard** (re-check before 2093) | none | tests guard, not cadence |
| 7 | full-off (`build-off`) | corrected | off | recovery + wave enabled | tests recovery/wave without speed |
| 8 | full-on (`build-on`) | corrected | per-tick | recovery + wave enabled | reproduces crash-build shape; control |
| 9 | full-off | corrected, **tactical recovery disabled** | off | wave only | isolates the 1765 recovery loop |
| 10 | full-on | corrected, **tactical recovery disabled** | per-tick | wave only | speed loop without 1765 recovery loop |

**Pass/fail per row:** no `Invalid Agent ID: 0`; no `EXCEPTION_ACCESS_VIOLATION`; stable
heartbeat; sealed crash log + dump; exact module receipt + compiled/probe trigger map.
Any crash must be reported with its bundle and exact build receipt, not folded into a
generic "P0 crashes" claim.

Suggested order: **1 -> 2 -> 3 -> 4 -> 5 -> 6**, then 7-10 only if the clean pair is
contradictory. This tests the probe-first hypothesis before changing A's loop.

## 10. Required evidence / actions

1. **C:** merge/freeze the unfrozen probe fix branch `agent/c-invalid-agent-guard`
   (`2e837c2`; parent `39aa3a7` changes `read_group` to `fn(0, agent)` + `agent_live`;
   `4e888a0` no-id0 trigger-32 path). Add a negative test for id 0 and verify the
   installed build's Lua probe hash in each sealed run.
2. **A:** provide absolute `p0bisect` package paths; keep per-tick speed only for bisect;
   implement the one-shot wave-transition/spawn alternative with valid-id + alive guard;
   record `native_speed_loop=off|on` and the compiled/probe trigger map in the receipt.
3. **D:** seal the clean pair first with the corrected probe; then full/recovery rows.
   Include crash log + dump + module receipt + trigger map per run.
4. **No P0 seal/relaunch** until the matrix is clean and the crash is root-caused; keep
   `f57c800` known-good.
5. **Trigger-32 map:** no longer a module mismatch; record it as **compiled 31 + probe
   heartbeat Lua trigger index 32** in future receipts so it is not misread as 32
   compiled triggers.

## 11. Non-claims

No game was launched by this task. No root cause is accepted; no crash is fixed; no
availability/acceptance/legal claim is made. The script error and AV are observed; the
causal link, and the relative contribution of probe vs speed loop vs tactical recovery,
are unknown until A/D seal the section 9 matrix. A-supplied facts (module receipt hashes,
parked path, bisect package paths, `guard_groups`) are recorded with that provenance; only
the v2 stream, crash log, source triggers and current/C-branch Lua were independently
inspected here.
