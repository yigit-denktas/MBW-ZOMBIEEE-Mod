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
