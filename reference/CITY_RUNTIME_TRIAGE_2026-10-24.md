# City runtime defect triage — first observed dedicated-host attempt (24 October 2026)

**Agent A · PR #10 · scope: source-scope triage of the first observed City attempt. Source and probe-field analysis only; not engine acceptance.**

## Candidate identity (what actually ran)

| Item | Observation |
| --- | --- |
| Host | `mb_warband_wse2_dedicated.exe`, WSE2 `1.174 1154` (log line "Build: Release Dedicated") |
| Module | installed `Modules/ZOMBIEEE_Remaster` |
| Built candidate | staged City module from A `141a792` + pinned Beta 0.4 archive (per B build report) |
| Installed ↔ staged identity | `mission_templates.txt` SHA-256 `9e8229e779023524…`, `variables.txt` `1b0b1b4106324fe7…`, `module.ini` and install receipt all **byte-identical** between the staged build and the installed module. Receipt: 31 triggers / 1,223 globals, 26 static checks, `runtime_verified=false` |
| Map/mode | rotation file `set_mission multiplayer_iv`, `set_map tbfc_invasion_4`, `set_factions fac_kingdom_1 fac_kingdom_invaders`, `start` |
| Host socket | UDP `127.0.0.1:7240` only (loopback), no public listener; one outbound TCP connection, not an inbound listener |
| Probe that produced evidence | **A overlay `overlay/lua/main.lua`** (8,379 bytes, SHA-256 `1ce64f9f…`), installed into the module at build time — an older probe, not current C HEAD |

The probe therefore predates the C forensic changes; its limitations are part of the evidence, not only a code bug.

## Observed facts (verbatim, no interpretation)

Dedicated host stdout (`host_stdout.log`, 19 lines):

```
ZDB1|boot|version=0.1.8|triggers=31
ZDB1|probe_registered|version=0.1.8|kind=entry|index=31
ZDB1|probe_registered|version=0.1.8|kind=heartbeat|index=32
ZDB1|mission_enter|version=0.1.8|role=client|template=mst_multiplayer_iv|agents=0|team0=0|team1=0|wave=0|round=0|mode=0|...
ZDB1|heartbeat|version=0.1.8|count=1..15|role=client|agents=1|team0=1|team1=0|template=mst_multiplayer_iv|wave=0|round=0|mode=0|...
```

Dedicated session log (`dedicated_session_20261024-011107.log`):

- `Starting map tbfc_invasion_4 in mode multiplayer_iv` at 01:11:08.
- Four `SCRIPT ERROR: Invalid Faction ID: -1` at `mst_multiplayer_iv Trigger [14] Consequences (line 24/25/26/27, opcode 502)`.
- `Illegal lvalue in statement` every 15 s at `Trigger [32] Conditions (Lua)` (01:11:30–01:15:00) — C-owned probe defect.
- No other script error, no script-error text naming a troop, team or spawn operation.

Steam screenshots 01:12:25–01:13:57 (four frames): the client is inside the City scene, HUD `0`–`0`, round timer frozen at **5:00**, no zombie and no allied agent visible. The 01:12:25 frame is the client log overlay showing the same `ZDB1` heartbeat lines and both script-error classes.

Recorder evidence (`evidence-attempt4-…`): 9 events, `simulation=false`, 2 attached processes, recorded log = the dedicated log (18,607 bytes), no truncation. Readiness was recorded before the host started; `game_ready=false` at attachment; the client process exited by itself with code 0 and the session was stopped 247 s after recorder start. **This is not a completed gameplay receipt.**

## Defect triage 1 — `Invalid Faction ID: -1` (trigger 14)

Decoded native trigger 14 (`-19.000000`, 28 consequence operations):

- Operations **0–23** are `faction_set_slot` (`502`) writes of invader troops into faction **index 16 = `fac_kingdom_invaders`**, slots 200–243. These are the legitimate invader troop tables.
- Operations **24–27** are four identical `faction_set_slot(-1, 200, trp_invader_multiplayer_ai)` writes: faction operand is the literal **-1**, which is not a faction.
- Engine "line N" is the **zero-based consequence index**, so lines 24–27 are exactly these four trailing operations.

Source-scope findings:

1. **Not introduced by the remaster.** The generated module's first 25 triggers are byte-identical to the pinned 2012 Beta 0.4 mission; trigger 14 is therefore historical original content, present before any A patch.
2. **They are the last four operations of the trigger**, after all 24 valid faction writes, and the engine reports each error but continues the script (the earlier writes in the same trigger demonstrably executed — only four errors appear, one per invalid write).
3. **No spawn operand is left unset by the failure.** The failed target, `fac_kingdom_invaders` slot 200, was already written by operation 0 to a valid troop (`trp_invader1_multiplayer_ai`). The four operations would have overwritten that slot with `trp_invader_multiplayer_ai`, so their failure changes a wave-composition default, not the existence of a valid troop value.
4. **The original wave controller does not depend on them.** The team-1 spawn path in trigger 15 reads faction slots 200/221/231/241 through `team_get_faction` and spawns via `add_visitors_to_current_scene`; it issues no `faction_set_slot` and no invalid faction operand of its own.

**Assessment (source scope only):** trigger-14 errors are a pre-existing authoring bug, are non-fatal, and do not explain the observed zero team-1 agents by themselves. They are **not** a remaster defect and **not** a proven cause of the spawn failure. A "fix" rewriting `-1` to `fac_kingdom_invaders` would silently change the wave-1 fallback troop and must not be applied as part of the default build without separate evidence.

## Defect triage 2 — runtime `mode=0`

The probe's `mode` field is bound to **`$zdr_defence_mode`**, A's tactical fallback state global, *not* to `$g_multiplayer_game_type`. The City build initializes `zdr_defence_mode` to **0** in a `ti_after_mission_start` trigger, so `mode=0` is the **source-expected normal state**, not a mission-start ordering failure and not evidence about the engine game type.

The source pinned original trigger 3 unconditionally assigns `g_multiplayer_game_type = 7` before mission start. **The engine game type was never observed in this attempt**: the probe did not read `g_multiplayer_game_type` at all. Any statement of the form "runtime mode 0 contradicts source 7" conflates two different globals and is invalid.

## Defect triage 3 — no team-1 agents / wave progression

Source expectation (unchanged original trigger 15, period `1.000000`):

- First consequence operation is `multiplayer_is_server` (`417`), then mission time is compared against `g_round_start_time`.
- After ~20 s the controller sets `wave_number` to its first value; after ~30 s without live team-1 agents it advances the wave and calls `add_visitors_to_current_scene` for the invader troops at random invader entries 32–39.

Observed: the host printed `wave=0` and `team1=0` in all 15 heartbeats over ≈225 s, and the joined client's agent enumeration also saw only the player.

**This is not yet a proven native-controller failure**, because the evidence channel was blind server-side:

- The installed probe decided role from a boolean WSE2 Lua binding and reported the dedicated host as **client**; its `if role == "server"` branch (wave-change records, defender sampling, command counters) was therefore **silently disabled**.
- The same overlay lacked the operation metadata lists WSE2 needs, which is why the engine logs `agent_get_team` as an illegal lvalue; bound reads that silently return an error state are not trustworthy measurements.
- The engine's round timer was frozen at 5:00 in every client frame, which is consistent with (but does not prove) a round that never became active.

The correct disposition is therefore **causality unproven**. A corrected probe must re-observe `g_multiplayer_game_type`, `g_round_start_time`, `g_multiplayer_ready_for_spawning_agent`, bot counts and team-1 agents on the dedicated host before any gameplay patch is justified.

## What was NOT established

- No runtime game type, no server-side round-start timestamp, no bot-ready state.
- No proof that the wave controller ran, was gated, or failed; no proof about `g_round_start_time`.
- No proof of a spawn-relevant engine effect of the four faction errors.
- No gameplay acceptance, no wave/round/combat observation, no installer or recorder acceptance.

## Reproduction

```text
python tools/city_runtime_triage.py --original <owned Beta 0.4 module> \
    --module <built City module> --probe overlay/lua/main.lua --json
python -m unittest tests.test_city_runtime_triage -v
python -m unittest discover -s tests -q
```

Local result: **158 tests, OK, zero skips** (Windows 11, Python 3.11.9, owned original module and pinned archive). Tool result on the installed module: all source-scope checks pass, `runtime_verified=false`, `causality=unproven`.

## Next controlled observation (requires Lead coordination)

One short, instrumented, loopback-only attempt after the C probe fix, recording at minimum: `g_multiplayer_game_type`, `g_round_start_time`, `g_multiplayer_ready_for_spawning_agent`, `g_multiplayer_num_bots_team_1`, server-role detection, and team-1 agent counts, then stop. No repeated owner playtests and no gameplay patch before that evidence exists.
