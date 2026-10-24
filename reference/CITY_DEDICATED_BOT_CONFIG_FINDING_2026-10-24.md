# Dedicated rotation bot-count finding — 2026-10-24

**Agent A · scope: live-observation documentation and static launcher contract. Not gameplay acceptance.**

## Observation

Lead-reported live observation on merged `main` `4c56242` with a rebuilt City module (C's corrected `opmeta=1` probe, recorder armed, dedicated host loopback-only `127.0.0.1:7240`). Sealed recorder receipt and screenshots are still pending.

On merged `main` `4c56242`, rebuilt City module, C's corrected `opmeta=1` probe, recorder armed, dedicated host bound UDP `127.0.0.1:7240` only:

| Configuration | Observed ZDB1 / host state |
| --- | --- |
| none (baseline) | `role=server game_type=7 ready_for_spawn=1 bots_team1=0 team1=0 wave=0` for 90+ s |
| `set_bot_count 1 32` | `agents=33 team0=33 team1=0` |
| `set_bot_count 2 32` | `agents=42 team0=1 team1=41 wave=1`, `wave_change wave=1`; `game_type=7 ready_for_spawn=1` |

The wave-1 enemy population (`41`) is arithmetically consistent with `32` configured bots plus `9` original wave-1 visitors (`1 + 8` from the untouched original trigger 15); this decomposition is not separately itemized in the evidence.

## Root cause (bounded)

The earlier "no team-1 agents" observation was caused by the dedicated **rotation configuration**, not the remaster build:

- `set_bot_count` is **1-based**: team `1` is the first team, team `2` is the second/enemy team.
- Probe field `bots_team1` reads `$g_multiplayer_num_bots_team_1`, which is the **first** team; it must not be reported as the enemy count.
- Without a configured second team, the native round/bot population stayed empty and the original wave controller never passed its round-start/time gate; configuring the second team produced `wave=1` and `team1=41` living agents.

## Required launcher/installer behavior (B P1, no gameplay acceptance)

Emit before `start`:

```text
max_num_bots 200
set_bot_count 1 0
set_bot_count 2 32
start
```

Optional: `set_round_max_seconds` may bound the round. The rotation remains a private local file; no game process, path, token or asset enters Git.

## Offline enforcement

```text
python tools/city_runtime_triage.py --original <owned original module> --module <built City module>     --probe overlay/lua/main.lua --rotation <generated rotation> --json
```

New `launcher_*` checks fail closed if the rotation lacks `start`, a positive `max_num_bots`, a positive second-team bot count, or declares bot counts after `start`. Static contract only.

## Boundaries

- One enemy wave observed; no wave 2+, original allied survivor divisions 5-7, fallback/regroup, combat, round transition or controlled teardown evidence yet.
- Sealed recorder receipt and wave/AI screenshots are pending from Lead.
- Trigger-14 `Invalid Faction ID: -1` remains original Beta 0.4 content, non-fatal and not proven causal; no gameplay patch.
- Required City release outcomes remain **0/23** and accepted milestones **0/5**.

## Follow-up — roster and respawn defects (still no acceptance)

- **Roster:** the 32 generic bots from `set_bot_count 2 32` are the faction default troop — observed as `trp_invader_multiplayer_ai` = **Crazed Civilian**, not the native Zombie troops (`trp_invader1_multiplayer_ai` etc.). Only the original wave visitors spawn the native invader troop list. The launcher/rotation must verify the invader roster; tracked as issue #14 (and #13 for wave roster/completion/allies). `tools/city_runtime_triage.py --rotation` reports a static `roster_caveat` — it cannot verify the runtime troop identity.
- **Respawn:** after player death, no respawn/new round was observed (`team0=0`, `wave=0`). Required before `start`: `set_respawn_period 5`, `set_round_max_seconds 1800`, `set_defender_spawn_count 0`, `set_player_respawn_as_bot 0`. The rotation contract now fails closed if any of these are missing/wrong.
- **Evidence hardening:** issue #15 (recorder atomic-replace race, `ZOM-DISC-22`) and issue #16 (seal dedicated-host ZDB1 stdout inside flight evidence).
- Issue #1 closed as superseded by #13.
- Required City release outcomes remain **0/23**, milestones **0/5**; wave 2+, original zombie roster, allied survivor divisions 5-7, round transition and teardown remain unverified.

## Native Zombie roster fix (branch gent/a-native-roster-fix)

**Mechanism (proven statically):** the compiled Native script multiplayer_find_bot_troop_and_group_for_spawn scans a hard-coded multiplayer-AI troop range 855..874, keeps troops whose faction equals the team faction, and picks one at random. ZOMBIEEE Beta 0.4 appended its Zombie troops (	rp_invader1..8_multiplayer_ai = 894..911) after 	rp_multiplayer_end, so ac_kingdom_invaders bots could only ever resolve to the two placeholder Crazed-Civilian troops 873/874. 	ools/native_roster_patch.py inserts a faction-conditional range in the compiled script (City-only build): faction 16 (invaders) scans 894..911; every other team faction keeps 855..874. No troops, equipment, factions or mission triggers are modified. Expected team-1 bot ids after rebuild: **894..911** (Zombie), never 873/874.

**Private defender timely respawn:** the one-shot 	i_after_mission_start=-20 squad spawn can be cleared by the dedicated round reset. The 3 s tactical-recovery trigger now also tops up missing private survivors (cap = --experimental-defenders) on the active round, using the same balanced-AI/survivor class troops and reserved divisions 5-7. The City hold-position trigger now re-issues orders every 5 s instead of once, so orders survive round resets and respawns. Both are recorded in the build receipt (
ative_roster_patch, experimental_tactical_recovery.defender_respawn_*).

**Rebuild required:** the installed module must be rebuilt from this branch; the engine has no runtime toggle for these data/trigger fixes. Offline: branch suite green; erify_city_chain passes (11 preserved inputs, chain 25->26->27->29->31); a City build produced 31 triggers, accepted static/final gates, 
ative_roster_patch.invader_candidates = 894..911. **Engine proof still pending** (sealed AI-vs-AI run).

