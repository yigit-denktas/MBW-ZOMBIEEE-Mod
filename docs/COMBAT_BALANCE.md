# Experimental v0.1.7 — AI combat equipment and private solo assistance

This package extends the **original 2012 ZOMBIEEE Beta 0.4**, not ZOMBIEEE2. Everything is opt-in. The original 981 troop records, 684 items, 25 invasion mission triggers, maps and RAR remain unchanged in the source. Modified data is generated locally from the user's own archive.

## Source-grounded inventory findings

The original playable Commando and Scout use handguns, Sniper has a Remington Model 700, and Lumberjack has a Browning Cynergy shotgun. Existing troop records and the original item-kind table were inspected directly. **The original item table has 16 duplicated identifiers**; these are historical records, not new errors. We preserve every original positional item index and reject only an absent/ambiguous item actually selected for the new AI equipment.

## New AI-only troop variants

Four *additional* troops are appended (IDs 981–984). They copy the class's original stats, skills, identity flags, and character features, but receive an AI defence loadout using original 0.4 items. They do **not** replace existing playable class troops.

| AI-only troop | Original-derived equipment |
|---|---|
| **ZDR Commando** | M16A2, 2× cartridge ammo, Beretta 92FS, police uniform, gloves, boots |
| **ZDR Sniper** | Remington Model 700, 2× cartridge ammo, Beretta 92FS, sheriff uniform, shoes |
| **ZDR Scout** | MP5, 2× G-Ammo, Smith & Wesson 5904, police uniform, shoes |
| **ZDR Lumberjack** | Browning Cynergy shotgun, 2× shotgun shell ammo, Bowie knife, original lumberjack shirt, boots |

Weapon/ammunition compatibility follows inferred choices from the original 0.4 equipment categories; firing mechanics and AI weapon selection remain **unverified in WSE2**. Four weapon inventory slots (including ammunition) are preserved. No original textures, sounds, BRF or new firearms were added.

Use `--defender-loadouts balanced-ai` with `--experimental-defenders 1..8`. Normal default is `--defender-loadouts original`.

### Less repetitive reinforcement

The optional original-wave-triggered defender replenishment now selects the next class using:

`(original_wave_number + reinforcement_spawn_index) % 4`

This rotates classes between waves. Previously, replacing only one defender always gave the first class, producing Commando-heavy squads. The total cap, once-per-wave restriction and server-only filtering remain unchanged. All four AI troop IDs are resolved from the original plus appended troop records, never invented numeric IDs.

## Host-only private solo assist

The optional `--solo-assist` adds **one** native mission trigger with a 12-second interval. It is designed to give the local solo listen-server host full health and ammunition between engagements. No keybind or in-game cheat menu is claimed yet.

The trigger requires ALL of the following native conditions:

- Current process must be the server and **must not** be a dedicated server
- **Exactly one active multiplayer player** in that session
- That player must be the **local host**, be alive, and belong to survivor team 0

Effects are confined to the host agent: `agent_set_hit_points(100%, relative)` and `agent_refill_ammo`. No anti-cheat functions are modified, no remote client receives a cheat and sessions with another active player should not satisfy the one-player gate. Some Warband builds may count bots differently in their multiplayer player iterator; if so, this feature safely refuses to apply rather than granting powers. **Permission enforcement is structurally validated but not yet confirmed in WSE2.** Do not run this experimental mode on a public server.

It is explicitly separate from normal gameplay. It is not a developer console for spawning zombies, editing waves or giving arbitrary admin powers.

## Build and triggers

```powershell
# Original gameplay with experimental AI squad and optional balanced bot-only weapons:
py -3 tools\build.py --archive "C:\Downloads\ZOMBIEEEBeta04.rar" --out "C:\Games\MountBlade Warband\Modules\ZOMBIEEE_Remaster" --experimental-defenders 4 --defender-loadouts balanced-ai

# Complete private experimental candidate, including five maps, waves, recovery and host solo assist:
py -3 tools\build.py --archive "C:\Downloads\ZOMBIEEEBeta04.rar" --out "C:\Games\MountBlade Warband\Modules\ZOMBIEEE_Remaster" --experimental-defenders 4 --defender-loadouts balanced-ai --all-map-defenses --wave-reinforcements --tactical-recovery --solo-assist
```

The combined experimental build contains **985 troop records, 1,222 globals and 32 compiled invasion triggers** (25 original + 6 previous remaster triggers + one solo-assist). The solo cheat flag adds exactly one trigger to any otherwise supported build. The default is still **981 troops and 25 original mission triggers**.

## Reproducible offline checks

Structural checks were performed on a local copy of the user's actual 0.4 tables. Four AI clones were assigned new troop IDs 981–984, all original troop records remained unchanged, cloned inventories resolved to original item IDs, and the wave-reinforcement stream referenced the four clones. The full local assembled variant (including previous map, wave, and recovery patches) parsed as 32 valid native mission triggers with 985 troops and 1,222 globals. Repeated solo-assist injection is rejected. The existing local regression suite was rerun (37 passed) and dedicated new tests were added to the repository.

**Not yet verified:** WSE2 launch, actual weapon/ammunition behavior, bot accuracy, cover/LOS, host-only conditions under active multiplayer, and completed waves. Preserve this distinction when reviewing the final evidence bundle.

See [Diagnostic policy](DIAGNOSTICS.md), [Tactical recovery](TACTICAL_RECOVERY.md) and [Warband's native operations](https://github.com/Veehats/WarbandCoop/blob/main/header_operations.py).

## v0.1.8 — actual private hotkeys and support difficulty

The previous timed `--solo-assist` remains optional. The new `--private-commands` is a **different, mutually exclusive** set of local host keypress actions (Left Ctrl+F7/F8/F9) and requires the full tactical build, one non-dedicated player and a living team-0 host. Each successful command increments an appended diagnostic global variable. See [Forensic diagnostics](FORENSIC_DIAGNOSTICS.md). Survivor-support difficulty profile changes reinforcement start and fallback thresholds only; original zombies are unmodified. Keyboard and permissions remain unverified in WSE2.
