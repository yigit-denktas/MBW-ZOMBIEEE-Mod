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

## Firearm accuracy build profile (task-22, 2026-10-24)

The build now applies a default **automatic-firearm accuracy** profile: every
item sharing the automatic-weapon flag mask (M249, FAMAS, AK47, FN SCAR-L, MP5,
HK MP5K, HK MP7, P90, Mk12 SPR, M16A2) gains `+clamp(round(old*0.10), 5, 10)`
accuracy points (+8..+10 on the pinned values). Single-shot firearms (Remington
700, Browning Cynergy, pistols including Beretta 92FS/SW5904, M82) and all
non-firearm items are byte-identical. `--firearm-accuracy stock` keeps original
stats; the receipt records changed items and SHA-256 before/after with
`runtime_verified=false`. See `reference/CITY_FIREARM_BALANCE_2026-10-24.md`.
No gameplay validation is claimed; D/Lead validate in a sealed run.

## City combat regression profiles (task-30, 2026-10-24)

- **No scripted-destination override:** the 5 s City adoption trigger no longer sets
  `agent_set_scripted_destination`; defenders keep native combat aiming (owner saw
  them charge into melee instead of shooting). Division/group writes and team hold
  orders remain. Hold stability is intentionally not claimed.
- **Weak wave-1 generic bots (default):** `--zombie-bot-roster weak` restricts city
  generic invader bots to the weak native block 894 only (weak Invader scythe/pitchfork/butcher-knife);
  `full` restores 894..911. Receipt records the range/profile.
- **Zombie block (default on):** `--zombie-block default` gives native invader
  troops 894..911 the `itm_wooden_shield` item (they already have shield skill);
  other troops unchanged; `stock` disables. Runtime block behaviour needs D's sealed
  validation. No acceptance claim; 0/23 outcomes unchanged.

## Defensive rear line + larger squad (2026-10-24 follow-up)

- City defender hold orders now default to the **rear/spawn entries 0/1**
  (`REAR_HOLD_ENTRIES`), static every 5 s, with no scripted destination and no
  forward sector rotation; `--defensive-line forward` restores the old 2/3/4
  guard sectors. Receipt records `hold_entries` / `defensive_line`.
- Launcher defender squad default is **8** native team-0 bots (native refill keeps
  bodies up); build still appends clone troops 981..984. Player-facing combat
  validation (defenders firing, holding, KD) remains D's sealed evidence; no
  acceptance claim.

## Standoff/fire discipline (task-42)

Per-bot ammo-gated WSE2 safety on team-0 defenders: keep the ranged weapon
(`agent_ai_set_can_weapon_switch=0`) while ammo exists; allow the native melee
switch only at zero ammo (last resort); `agent_ai_set_simple_behavior(aisb_hold,6 s)`
keeps formation behaviour. No scripted destination. AI clone loadouts carry no
bombs/grenades, so explosive gating by cluster density is not applicable to AI
survivors (receipt `explosive_gating=not_applicable_ai_loadouts_have_no_bombs`);
player bomb gating remains an equipment/design decision. D validates movement,
ammo and KD; no acceptance claim.

## Task-45 KD/pressure tuning (after task-42 sealed evidence)

D's sealed task-38/42 runs showed defenders ranged and rear-held but KD poor
(6/49 and 4/52 kills/deaths), zombies outmoving them, and wave 2 never reached.
City balance changes:
- **Fire orders fixed:** the per-group order set no longer issues
  `mordr_hold_fire(12)`; it issues `mordr_hold(0)`, `mordr_fire_at_will(13)` and
  `mordr_use_ranged_weapons(16)` so the squad actually fires instead of suppressing.
- **Incoming pressure:** native zombie pace base lowered from 70% to **60%** at
  wave 0/1 (+5%/wave, capped 100%); launcher generic enemy profile default
  32 -> **24** generic bots (`DEFAULT_TEAM2_BOTS`), while weak-wave1 8 and
  native-only 0 profiles are unchanged.
- Rear hold [0,1,0], 8 team-0 bots, spawn_agent refill, slow 894 visitors, weak 894
  generic fill and zombie-block profile remain. D must re-seal to measure KD and
  wave-2 reachability; no acceptance claim.

## Task-46 survivor consolidation

- One melee weapon per AI survivor (itm_bowie), **double ammo** (8 cartridge stacks per clone).
- Survivor target grows by **+1 per completed round** (faction-slot counter, base 8, cap 12) and spawn_agent refills to that target; rear hold/standoff/refill unchanged.
- City trigger explicitly gated on Invasion game_type=7; receipt records it.
- Task-45 balance (fire_at_will, 60%% wave-1 zombie pace, 24 generic bots) retained. D validates KD/wave-2; no acceptance.

