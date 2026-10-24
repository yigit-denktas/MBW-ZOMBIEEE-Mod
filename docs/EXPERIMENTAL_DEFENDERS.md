# Experimental allied defenders — 0.1.2

This is an **opt-in, unverified-in-engine** first pass for adding allies to original ZOMBIEEE 0.4 without distributing or modifying the source RAR. The default install remains the unmodified original mission with a diagnostic Lua overlay.

## How it works

The original `mst_multiplayer_iv` mission has 64 entry points and 25 native triggers. Its existing spawning logic calls `add_visitors_to_current_scene` (operation **1265**) and distinguishes survivor team **0** from invader team **1**. Side-0 entry points **0 and 1** were observed in the compiled spawn logic; invader-side spawns use entries **32–39**.

`tools/patch_defenders.py` appends exactly **one** extra native trigger:

- Event: `ti_after_mission_start` (**-20.0**), fires once per loaded mission.
- Condition: `multiplayer_is_server` (**417**) so clients do not spawn duplicate agents.
- Consequences: `add_visitors_to_current_scene` (**1265**) for each ally, assigned to team 0, group 0, alternating survivor spawn entries 0 and 1.
- Classes: Commando, Sniper, Scout and Lumberjack, rotating for up to eight allies.
- Troop operands are generated from the actual original `troops.txt` ordinal; the patch **does not hardcode numeric troop indexes**.
- Original 25 trigger lines remain unchanged. The mission's declared trigger count is incremented to 26.

Source: the user's original 0.4 compiled module and [Warband's operation reference](https://github.com/Veehats/WarbandCoop/blob/main/header_operations.py); mission lifecycle: [Warband trigger definitions](https://github.com/mbw-economy/Economy-Mod-for-Mount-and-Blade--Warband/blob/master/Module_system%201.134/header_triggers.py).

## Build with allies (Windows)

```powershell
py -3 tools\build.py --archive "C:\Downloads\ZOMBIEEEBeta04.rar" --out "C:\Games\MountBlade Warband\Modules\ZOMBIEEE_Remaster" --experimental-defenders 4
```

Or use `tools/Smoke-Test.ps1` to run local unit tests, build and preflight.

`--experimental-defenders 0` (default) installs **no extra mission trigger**. The valid range is 1–8. The installer checks the original RAR SHA-256 and runs `7z t` before deployment; a failed CRC check blocks installation. `--replace` creates a `.previous` backup.

You can preview the patch on an already extracted **unmodified original** module without writing anything:

```powershell
py -3 tools\patch_defenders.py --module "C:\path\to\original\ZOMBIEEE" --count 4
```

## What is NOT yet implemented

- The bots' equipment, combat, navigation, survival, and visual synchronization have **not** been observed in WSE2.
- These initial allies spawn **once per mission**; there are no respawns between waves.
- They do **not** receive hold/rally/fallback orders; no defensive areas are changed yet.
- The original survivors' faction and spawn routing is inferred from compiled operations. It needs an actual WSE2 multiplayer server test.
- The trigger may need moving to a later event if Warband ignores these visitors at `ti_after_mission_start`. Keep the feature off in ordinary builds until tested.
- This does not make Warband single-player campaign mode into an invasion mode; it targets its multiplayer invasion mission, which can be hosted privately.

## Acceptance and diagnosis

1. Original unmodified install: City `tbfc_invasion_4` loads and original zombies spawn.
2. Experimental build: host privately, confirm **four ally agents on team 0** and record whether they fight zombies.
3. Confirm zombie team 1 still spawns correctly and wave progression is unaffected.
4. Capture WSE2 version, `rgl_log.txt`, one screenshot, and wave count.
5. Try `--experimental-defenders 1` then 4 to localize failures. Do not enable public server cheats or port forwarding.

This is not `v0.2.0`. Successful gameplay evidence, not static parsing, determines that milestone.

## Overnight behavior update (task-14/17, branch `agent/a-survivor-hold`)

- **Respawn:** the one-shot `-20` squad spawn is complemented by a 3 s top-up of missing private survivors (cap = `--experimental-defenders`) on the active round, so dedicated round resets cannot leave team 0 empty.
- **Hold positions:** the City order trigger re-issues hold positions every 5 s and rotates each division's guard sector by one step per original `wave_number` parity. Fixed guard entries remain 2/3/4; no original triggers or scene entry points change.
- **Zombie horde:** City-only builds patch the compiled bot-troop selection so invader bots use native Zombie troops 894..911 instead of Crazed Civilian placeholders; no team-1 tactical AI is added (simple aggressive seek stays).
- Full behavior contract: `reference/CITY_SURVIVOR_AI_BEHAVIOR_CONTRACT_2026-10-24.md`. Runtime validation is D's sealed no-client run; no acceptance is claimed here.

