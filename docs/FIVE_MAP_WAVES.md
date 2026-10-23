# Experimental v0.1.5 — Five-map defensive AI and wave reinforcements

This optional upgrade works **only with the original ZOMBIEEE Beta 0.4**. It does not use or redistribute ZOMBIEEE2. The original archive, scene geometry, zombie spawn entries and original 25 invasion triggers are preserved. The Windows/WSE2 runtime remains unverified.

## Compiled gameplay research

Original `variables.txt` contains 1,220 names. The mod's own Invasion trigger #15 (zero-based, mission `mst_multiplayer_iv`) updates `wave_number`, `wave_timer` and `last_wave`, spawning zombie variants with native `add_visitors_to_current_scene` (1265). The remaster **does not replace** these wave mechanics.

The new optional `wave_reinforcements.py` appends the separate variable `zdr_last_reinforced_wave` at the end of `variables.txt`, preserving all original numeric variable operands. It adds two mission triggers:

1. Reset the new per-match sentinel at mission start, server-only.
2. Every four seconds, only on the server, check Invasion game type 6, `wave_number >= 2`, `g_round_ended == 0`, and a wave number greater than the last reinforced wave. Count living **non-player**, **team 0** agents in reserved groups **5, 6 and 7**. Spawn replacements, up to the configured squad cap, **once per new wave**. The first wave is not reinforced. Dead allies are not resurrected mid-wave.

The independent native operation sequence uses `try_for_agents` (12), `agent_is_alive` (1702), `agent_is_non_player` (1707), `agent_get_team` (1770), `agent_get_group` (1765), `store_sub` (2121), `store_mod` (2119), and `add_visitors_to_current_scene` (1265). Original zombie spawning and team-1 AI remain untouched.

This is a *candidate implementation*. Group assignment and wave timing must be verified against the actual runtime in the final integrated test.

## Defensive locations for all five original maps

Each map's AI navigation mesh is read from the original `.sco`. Three candidate guard posts are placed on reachable mesh-face centres, spaced at least 9 metres apart and at least 15 metres from original zombie entries. The placement algorithm does **not** guarantee walls, props, line of sight, elevation clearance or actual pathfinding. Original scene objects and navmesh are preserved.

| Original map | Guard marker IDs | New marker coordinates (X, Y, Z) |
|---|---|---|
| Granny's House | 41, 42, 43 | (130.975,197.503,2.674); (142.374,220.911,3.193); (113.118,216.572,3.854) |
| Bridge | 41, 42, 43 | (155.270,137.880,5.672); (181.164,129.349,5.672); (184.722,148.056,5.672) |
| Shipyard | 41, 42, 43 | (185.000,89.000,2.980); (167.000,65.000,2.951); (191.000,59.000,3.803) |
| City | 2, 3, 4 | (165.500,169.267,3.191); (183.272,191.292,3.191); (153.814,188.910,3.191) |
| Abandoned Town | 41, 42, 43 | (299.000,197.000,3.971); (321.880,181.386,4.269); (323.342,207.081,4.245) |

The existing City tactical trigger is replaced by a **five-map, scene-conditional trigger**, not duplicated. Every map's survivor groups 5/6/7 are ordered to its own three markers; the original 25 triggers are unchanged.

## Build modes and expected trigger counts

| Build flags | Invasion triggers |
|---|---:|
| No experimental flags | 25 |
| `--experimental-defenders 4` | 26 |
| Add `--city-guardposts` | 27 |
| Use `--all-map-defenses` (implies City posts) | 27 |
| Add `--wave-reinforcements` | 29 |

The full opt-in build:

```powershell
py -3 tools\build.py --archive "C:\Downloads\ZOMBIEEEBeta04.rar" --out "C:\Games\MountBlade Warband\Modules\ZOMBIEEE_Remaster" --experimental-defenders 4 --all-map-defenses --wave-reinforcements
```

`--wave-reinforcements` requires `--all-map-defenses`, which in turn requires 1–8 experimental defenders. This prevents applying the wave patch to a module without the reserved ally groups.

## Offline verification and next risks

An integrated temporary-copy exercise applied the original squad patch, City scene patch, five-map overlays, and reinforcement patch to the original compiled Beta 0.4 data in sequence. The result was **29 invasion triggers**, **1,221 global variable names** (original 1,220 + one remaster variable), original scene navigation meshes intact, original RAR untouched. New tests check variable ordinals, opcodes, duplicate-patch refusal and five-map scene roundtrips.

All of this is **static verification only**. Runtime engine loading, group assignment, AI combat, wave completion, performance and multiplayer sync remain to be checked with the existing one-time WSE2 evidence collector. A test that merely parses a file cannot certify that a bot fights.

Sources: [original TaleWorlds development thread](https://forums.taleworlds.com/index.php?threads/wb-zombieee-invasion-we-need-your-advice.219327/); [Warband native operations](https://github.com/Veehats/WarbandCoop/blob/main/header_operations.py); [WSE2 releases](https://github.com/Ruslan-700/WSE2-Releases/releases).
