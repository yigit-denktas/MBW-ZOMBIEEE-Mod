# Original ZOMBIEEE Beta 0.4 behavior — static file review vs our City build

**Task:** task-33 (Agent E). **Scope:** read-only review of the pinned original Beta 0.4
extracted module against our latest staged City build. **No game was launched; no original
asset is copied into this repository; no runtime/AI acceptance is claimed.**

**Why this exists:** the owner and task-30 need original-file facts instead of guesses about
survivor shooting, wave-1 enemy mix, mounted/shielded enemies, and blocking. This document
records what the 2012 compiled files actually say, with file/line evidence, and lists
actionable deltas for task-30 (A) and task-31 (C).

---

## 0. Sources, identity and method

| Item | Value |
| --- | --- |
| Original module (local only, never committed) | `local/original-beta04/ZOMBIEEE` (1,068 files) |
| Original archive | `ZOMBIEEEBeta04.rar`, `167,493,071` bytes, SHA-256 `9be100ff41ce6f8ebadd4aa27377f70f402883fab271999a8cab8cc1da001d1e` |
| Original tables | `troops.txt` 981 troops, `item_kinds1.txt` 684 items, `mission_templates.txt` 50 templates / `mst_multiplayer_iv` 64 entries + 25 triggers, `scripts.txt` 571 scripts |
| Compared build (latest staged City build at review time) | `_zom-city-build-final/ZOMBIEEE_Remaster`; receipt `ZOMBIEEE_REMASTER.json`, `runtime_verified=false`, `source_archive_sha256` matches, `final_trigger_count=31`, `troops=985`, native mission SHA-256 `45e325e929b2894fd345585c1b67a853c488bc2505a84ed595d816c5a65eff6a` |
| Decode of compiled format | Warband Module System writers `process_troops`/`process_items` (read-only format reference; no code copied) |

**Reproducible decoding notes** (needed to read the citations below):

- Compiled troop record = 6 lines: header (`id name plural e13 flags scene reserved faction e14 e15`),
  64 inventory `(item, modifier)` pairs, attributes `str agi int cha level`, 7 weapon
  proficiencies, skills bitfield (6 × 32-bit words, **4 bits per skill**, skill index **26 =
  shield**, 24 = riding, 25 = athletics, 35 = power_strike, 36 = ironflesh), then two 256-bit face keys.
- Item type = `flags & 0x1F` (`1` horse, `2` one-handed, `3` two-handed, `4` polearm, `5` arrows,
  `6` bolts, `7` **shield**, `8` bow, `9` crossbow, `0x10` pistol, `0x11` musket, `0x12` bullets).
- Operand bases: troop `360287970189639680`; faction `432345564227567616`; global
  `144115188075855872`; script `936748722493063168`. Mission trigger row = 3 timing floats,
  condition count/ops, consequence count/ops; server-gated triggers start their consequence
  block with `multiplayer_is_server` (opcode 417). Faction `15 = fac_kingdom_1` (team 0),
  `16 = fac_kingdom_invaders` (team 1).

Line numbers below are 1-based lines of the **original extracted text files** (local/private).
Ranges are inclusive.

---

## 1. Survivor AI and loadouts — original 0.4 had no usable ranged AI survivor force

### 1.1 What the engine would spawn for team-0 bots

- Mission trigger **18** (`mission_templates.txt:2011`, every tick, server-only, gated on
  `g_multiplayer_ready_for_spawning_agent`) spawns one configured bot at a time and calls
  `multiplayer_find_bot_troop_and_group_for_spawn` (`scripts.txt:249-250`). That script scans
  troop ordinals **855–874** and keeps only troops whose faction equals the team's faction.
- Team 0's faction (`fac_kingdom_1`, id 15) therefore resolves to exactly three native AI troops:

| Ordinal | Line | Troop | Inventory (actual items) | Ammo? | Melee? | Proficiencies (1h/2h/pole/arch/xbow/throw/firearm) | Shield skill |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 855 | `troops.txt:5988` | `trp_swadian_crossbowman_multiplayer_ai` | `itm_sw_5904` pistol + clothes/boots | **none** | **none** | 110/90/100/0/100/0/0 | 5 |
| 856 | `troops.txt:5995` | `trp_swadian_infantry_multiplayer_ai` | same pistol + clothes/boots | **none** | **none** | 125/105/115/0/0/0/0 | 4 |
| 857 | `troops.txt:6002` | `trp_swadian_man_at_arms_multiplayer_ai` | same pistol + clothes/boots (flags include `tf_mounted` 0x400) | **none** | **none** | 120/100/110/0/0/0/0 | 4 |

**Conclusion:** original 0.4 team-0 bots would spawn with a pistol and **no ammunition and no
melee weapon**. Whatever the engine does with an unloadable pistol, it cannot produce sustained
ranged fire. The data-level answer to "do 0.4 survivor bots shoot?" is **no reliable shooting**.

### 1.2 What 0.4 team-1 generic bots would spawn as

For the invader faction (16), only ordinals **873/874** fall inside the 855–874 scan window:

- `trp_invader_multiplayer_ai` (ordinal 873, `troops.txt:6114`) and
  `trp_invaderb_multiplayer_ai` (ordinal 874, `troops.txt:6121`): display **Crazed_Civilian**,
  inventory only `itm_business_suit_a` + `itm_brogans_a` — **no weapon, no shield, no ammo**.
- This exactly explains the live observation that `set_bot_count 2 N` produced
  `trp_invader_multiplayer_ai` Crazed Civilians and no native Zombies
  (`reference/CITY_DEDICATED_BOT_CONFIG_FINDING_2026-10-24.md`): it is original data + the
  native scan window, not a remaster regression.

### 1.3 Original human survivor classes (source of our clone stats)

These are player-select classes, **not** AI troops; nothing in the original mission spawns them
as bots.

| Ordinal | Line | Class | Weapons / ammo in inventory | Firearms prof | Shield skill |
| --- | --- | --- | --- | --- | --- |
| 875 | `troops.txt:6128` | Commando | `itm_cartridges` + `itm_beretta_92fs` | 120 | 2 |
| 876 | `troops.txt:6135` | Sniper | `itm_cartridges` + `itm_remington_model_700` | 200 | 2 |
| 877 | `troops.txt:6142` | Lumberjack | `itm_cartridges_2` + `itm_browning_cynergy` + `itm_bowie` | 100 | 2 |
| 878 | `troops.txt:6149` | Scout | `itm_cartridges_1` + `itm_sw_5904` | 120 | 2 |

Ammo items are real: `itm_cartridges` (`item_kinds1.txt:635`), `itm_cartridges_1` (`:639`),
`itm_cartridges_2` (`:643`, display "Shotgun_Shell"), all type bullets.

### 1.4 No survivor behavior/formation logic exists in original 0.4

All 25 original `mst_multiplayer_iv` triggers were decoded and scanned: **none** contains
`team_set_order_position` (1791), `team_give_order` (1790), `agent_set_scripted_destination`,
`agent_set_division` or `agent_set_group`. The only survivor-related mission logic is the native
bot spawn in trigger 18. There is no hold/rally/fallback/formation script in the shipped module.
Original survivor "AI" is just the engine's default combat AI.

### 1.5 What our build adds (and why it can suppress shooting)

- Four AI-only clones appended: `trp_zdr_commando_bot` (build `troops.txt:6869`),
  `trp_zdr_sniper_bot` (`:6876`), `trp_zdr_scout_bot` (`:6883`),
  `trp_zdr_lumberjack_bot` (`:6890`). They copy the class attributes/proficiencies/skills and
  replace inventory with a real gun + **two ammo packs** + sidearm/melee
  (e.g. commando: `itm_m16a2`, `itm_cartridges` ×2, `itm_beretta_92fs`). They inherit shield
  skill 2 from the classes but **have no shield item**, so they cannot shield-block.
- Appended trigger **26** (build `mission_templates.txt:2019`, every 5 s) iterates **every alive
  non-player team-0 agent**, assigns divisions/groups 5–7, calls
  `agent_set_scripted_destination` to a guard entry, then issues
  `team_set_order_position`/`team_give_order(hold)` for divisions 5/6/7.
- Appended trigger **28** (`:2021`) tops the squad up per wave; trigger **30** (`:2023`) does the
  fallback/regroup state machine. Appended trigger 25 (`:2018`) spawns the initial 4 defenders.
- Consequence: our survivors get a real ranged loadout, but the 5-second scripted destination
  and team hold orders are applied to **all** team-0 bots and can override combat movement/aiming.
  That is the likely data-level driver of the owner's "survivors charge/melee" observation.

---

## 2. Enemy troop roster and original wave staging

### 2.1 Wave-visitor block: ordinals 894–901 (`trp_invader1..8`)

| Ordinal | Line | Troop | Attributes (str/agi/int/cha/lvl) | Weapons in inventory | Shield item | Shield skill | Notes |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 894 | `troops.txt:6261` | `trp_invader1_multiplayer_ai` — Zombie | 40/3/4/5/5 | `itm_invisible2` (invisible one-handed) | – | **0** | **wave-1 troop** |
| 895 | `troops.txt:6268` | `trp_invader2` — Tough_Zombie | 45/21/4/5/13 | `itm_invisible` | `itm_zombie_hand` (shield, `item_kinds1.txt:2455`) | **5** | only original invader with shield + skill |
| 896 | `troops.txt:6275` | `trp_invader3` — Fast_Zombie | 10/50/4/5/5 | `itm_invisible` | – | 0 | |
| 897 | `troops.txt:6282` | `trp_invader4` — Cop_Zombie | 50/24/4/5/5 | `itm_invisible` | – | 0 | |
| 898 | `troops.txt:6289` | `trp_invader5` — Steroid_Zombie | 140/40/4/5/5 | `itm_invisible` | – | 0 | high strength |
| 899 | `troops.txt:6296` | `trp_invader6` — Mutated_Zombie | 50/50/24/5/5 | `itm_invisible` | – | 0 | |
| 900 | `troops.txt:6303` | `trp_invader7` — Witchy | 140/50/4/5/25 | **`itm_cleaver`** (real one-handed) | – | 0 | `tf_undead` flag |
| 901 | `troops.txt:6310` | `trp_invader8` — Mutated_Zombie | 50/50/24/5/5 | `itm_invisible` | – | 0 | |

`itm_invisible`/`itm_invisible2` (`item_kinds1.txt:2447`/`:2451`) are real one-handed weapon
items representing the zombie claw/attack; they are not decorative. None of 894–901 is mounted
(no `tf_mounted` flag, no horse item).

### 2.2 Generic-fill block: ordinals 902–912 (what our roster patch randomizes over)

Our build's roster patch advertises `invader_candidates = 894..911` (receipt
`native_roster_patch`), i.e. **18 records**, drawn uniformly by the native bot script.

| Ordinal | Line | Display | Role | Weapon(s) | Shield item | Shield skill | Mounted? |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 902 | `troops.txt:6317` | Invader | weak melee | `itm_scythe`, `itm_stones` | – | 0 | no |
| 903 | `troops.txt:6324` | Invader | weak melee | `itm_scythe`, `itm_stones` | – | 0 | no |
| 904 | `troops.txt:6331` | Invader | weak melee | `itm_spiked_mace`, `itm_stones` | – | 0 | no |
| 905 | `troops.txt:6338` | Invader (duplicate id `trp_invader4`) | weak melee | `itm_pitch_fork`, `itm_stones` | – | 0 | no |
| 906 | `troops.txt:6345` | Invader (duplicate id `trp_invader5`) | weak melee | `itm_butchering_knife` | – | 0 | no |
| 907 | `troops.txt:6352` | Tank (duplicate id `trp_invader6`) | strong | `itm_one_handed_battle_axe_b` | `itm_tab_shield_round_a` (`:2047`, hp 195) | **0** | no |
| 908 | `troops.txt:6359` | Tank | **strong + mounted** | `itm_bastard_sword_b` | `itm_tab_shield_round_a` | **0** | **yes — `itm_warhorse` (`:602`), riding 5** |
| 909 | `troops.txt:6366` | Horde | strong melee | `itm_sledgehammer` | – | 0 | no |
| 910 | `troops.txt:6373` | Tank (duplicate id `trp_invader7`) | strong | `itm_mace_3` | `itm_tab_shield_round_a` | **0** | no |
| 911 | `troops.txt:6380` | Horde (duplicate id `trp_invader8`) | **ranged** | `itm_crossbow` + `itm_bolts` | – | 0 | no |
| 912 | `troops.txt:6387` | Horde (`trp_invader9_new`) | ranged | `itm_nomad_bow` + `itm_arrows` | – | 0 | no |

- Ordinals 913–929 also exist (`Horde/Tough_guy/Juggernaut/.../bosses`), but are **outside** our
  894–911 candidate range. Two of them are mounted (`920 trp_invader_boss2`, `922
  trp_invader_klargus_minion`) and several carry shields — do not extend the range without a
  wave allowlist.
- **Duplicate IDs matter:** records 905/906/907/910 re-use the names
  `trp_invader4/5/6/7_multiplayer_ai` for different data. The engine and the native scan address
  troops by **ordinal**; do not dedupe, rename, or look them up by name.
- Strong/shielded/mounted/ranged in wave 1 are therefore **not original wave content** — they
  can only appear because our generic fill randomly selects 907/908/910/911.

### 2.3 Original wave staging (trigger 14 slots + trigger 15 spawner)

- Trigger **14** (`mission_templates.txt:2007`, one-shot at mission start) writes the invader
  faction (16) wave table into slots 200–243:

| Slot | Troop (ordinal) | Slot | Troop (ordinal) |
| --- | --- | --- | --- |
| 200, 201, 202 | `trp_invader1` (894) | 209, 210 | `trp_invader7` (900) |
| 203 | `trp_invader2` (895) | 211, 212 | `trp_invader8` (901) |
| 204, 205 | `trp_invader3` (896) | 221, 222 | `trp_invader5` (898) |
| 206 | `trp_invader4` (897) | 231 | `trp_invader2` (895) |
| 207, 208 | `trp_invader6` (899) | 232 (last write) | `trp_invader8` (901) |
| 241 | `trp_invader3` (896) | 242 | `trp_invader4` (897) |
| 243 | `trp_invader8` (901) | | |

  The same trigger ends with **four `faction_set_slot(-1, 200, trp_invader(873))` writes** — the
  original authoring bug behind the live `Invalid Faction ID: -1` errors. Slot 200 has already
  been set to invader1 at that point, so this is non-fatal and not causal. Do not patch it.

- Trigger **15** (`mission_templates.txt:2008`, 1 s, server-only, starts only after round
  elapsed > 20 s) spawns the native waves. For wave index `i` in 1..15 it:
  1. checks `last_wave != i` and `wave_number == i`;
  2. calls `modify_visitors_at_site` and spawns at **random entries 32–39**, team 1;
  3. plain (odd) waves: loop count `(i + 8) × max(1, active_players/4)`; each iteration adds one
     random troop in the integer interval `[slot 200, slot 201 + i/4)`. Adjacent slots usually
     resolve to the same troop id, so most plain waves are a single troop type (the interval
     widens only for waves 13/15);
  4. waves `i % 4 == 0`: exactly 1 iteration, adding **1 troop from slot `221+(i-4)/4` and 8 from
     slot `231+(i-4)/4`**;
  5. waves `i % 4 == 2`: 7 iterations, adding **1 troop from slot `241+(i-2)/4`** each.
- Effective wave table for one player-group (1–7 active players; doubles per extra 4 players):

| Wave | Composition | Count (1 player-group) |
| --- | --- | --- |
| 1 | `invader1` Zombie (894) only | **9** |
| 2 | `invader3` Fast (896) | 7 |
| 3 | `invader1` Zombie | 11 |
| 4 | 1× `invader5` Steroid (898) + 8× `invader2` Tough (895) | 9 |
| 5 | `invader1` Zombie | 13 |
| 6 | `invader4` Cop (897) | 7 |
| 7 | `invader1` Zombie | 15 |
| 8 | 1× `invader5` (898) + 8× `invader8` Mutated (901) | 9 |
| 9 | `invader1` Zombie (894) — random range width 1 | 17 |
| 10 | `invader8` Mutated (901) | 7 |
| 11 | `invader1` Zombie (894) — random range width 1 | 19 |
| 12, 14 | resolve slots 223/233/244, which trigger 14 **never writes** | undefined/empty |
| 13, 15 | random `invader1`/`invader2` (894–895) | 21 / 23 |

  So original wave 1 is **only ordinary Zombies** (`trp_invader1`, no shield, no mount, no ranged).
  The wave table is defined for waves 1–11, 13 and 15; waves 12 and 14 resolve faction slots that
  trigger 14 never writes (runtime effect unknown), so do not use the original table as a
  "more than 11 waves" template without accepting that gap.

---

## 3. Shield / block behavior

- Blocking is driven by **equipment + shield skill**. In the original invader roster only
  `trp_invader2` Tough_Zombie (895) has both a shield item (`itm_zombie_hand`, shield, hp 60,
  `item_kinds1.txt:2455`) and shield skill **5**.
- Every other invader record has shield skill **0**, including the shield-carrying Tanks
  (907/908/910) and the invader bosses. Wave-1 troop invader1 (894) has **no shield item and
  shield skill 0**.
- Therefore the owner's "zombies block 0" is **original 0.4 data behavior for wave 1**, not a
  remaster regression. To let zombies shield-block you must change data: add a shield item and
  shield skill to the City-only invader allowlist (Tough Zombie's setup is the original example),
  or implement a separate block rule. Whether native AI actually raises a shield during combat is
  engine behavior and remains **unverified** without an engine test.
- Our defender clones inherit shield skill 2 from the playable classes but their loadouts contain
  **no shield item**, so our survivors also cannot shield-block as currently equipped.

---

## 4. Wave-1 density/composition: original vs our `set_bot_count 2 32`

| Property | Original 0.4 | Our current build (`set_bot_count 2 32`) |
| --- | --- | --- |
| Wave-1 native visitors | 9 × `trp_invader1` Zombie (scales with `active_players/4`) | 9 × `trp_invader1` Zombie, unchanged (first 25 triggers byte-identical) |
| Extra generic bots | none by default | 32 random records from 894–911 |
| Wave-1 total (1 player) | ~9 | ~41 (`team1=41` observed) |
| Wave-1 troop types | one: Zombie | 18-way random: includes weak melee (902–906), Tank (907/908/910), **mounted 908**, **crossbow 911** |
| Mounted enemies | none in waves 1–15 (bosses 920/922 are outside wave table) | possible: ordinal 908 has `itm_warhorse` + riding 5 |
| Shielded enemies | none in wave 1 (only Tough Zombie later via table) | possible: 907/908/910 carry round shields (skill 0) |
| Ranged enemies | none in wave 1 | possible: 911 crossbow + bolts |
| Blocking | wave-1 zombies block 0 (no shield, skill 0) | same data, plus random Tank/others |

Two independent effects, both expected to be visible live:

1. **Density:** 32 generic + 9 native = 41 (4.5× original wave 1).
2. **Composition:** the generic 32 are uniform over 894–911, so roughly 3/18 are Tanks
   (one of them mounted), 1/18 is the crossbow Horde, and 5/18 are weak melee. That is why the
   owner saw strong/mounted/ranged enemies in wave 1 while the native table staged only Zombies.

---

## 5. Actionable deltas (for A task-30, C task-31, D rebuild)

1. **Wave-1 composition (A, task-30 #2):** either run original waves only
   (`set_bot_count 2 0`, native 9 Zombies) or make the generic fill **wave-aware**. Align the
   candidate allowlist to the original wave table: wave 1 → ordinal 894 only; wave 2 → 896;
   wave 3 → 894; wave 4 → 898 + 895; wave 5 → 894; wave 6 → 897; wave 7 → 894; wave 8 → 898 +
   901; wave 9+ → widen. Never include **908** (mounted), **907/910** (Tank/shield) or **911**
   (crossbow) in wave 1. Do not extend the range to 912+ without a separate allowlist.
2. **Mounted wave-1 (A):** ordinal **908** is the only mounted record inside the current
   894–911 range (`itm_warhorse`, riding 5). Excluding 908 from wave 1 removes the mounted
   complaint without touching any original trigger.
3. **Survivor ranged behavior (A, task-30 #1):** our clones already have real guns + 2 ammo packs;
   original 0.4 had **no** functioning AI shooting, so there is no original behavior to restore.
   The data-level blocker is appended trigger 26 (`mission_templates.txt:2019`): it assigns
   divisions/groups and `agent_set_scripted_destination` to **every** team-0 bot every 5 s, then
   team hold orders. Gate it (only when no enemy is near, or only while in fallback/regroup
   mode, and only for the private defender group), or drop the per-agent scripted destination and
   keep only the team hold order, so ranged AI can engage.
4. **Blocking (A, task-30 #3):** "zombies block 0" is original for wave 1 (no shield, shield skill
   0). Only Tough_Zombie (895) has `itm_zombie_hand` + shield skill 5; Tanks have shields but
   shield skill 0. If the owner wants blockable/blocking zombies, add a shield item + shield skill
   to a City-only invader allowlist (and accept that this changes original behavior); if the goal
   is survivors blocking, our clones need a shield item (they already have skill 2).
5. **Do not patch trigger 14's four `faction_set_slot(-1, …)` writes** — they are original
   2012 authoring artifacts and non-causal (slot 200 already holds invader1). Patching them would
   change wave-1 fallback composition.
6. **Do not dedupe invader IDs:** ordinals 905/906/907/910 reuse `trp_invader4/5/6/7` names with
   different data. Keep ordinal-based selection/lookup; a name-based map would pick the wrong
   record.
7. **Telemetry (C, task-31):** the fields that would make these facts observable live are:
   `wave_number`/`last_wave`, team-1 troop histogram split by ordinal (expect 894 for pure wave 1;
   902–911 for generic fill), mounted/horse count (`agent_is_horse` or horse troop id),
   per-agent shield/block capability, and the ammo/weapon of team-0 bots. Without ordinal-aware
   histograms the 902–911 mix is indistinguishable in summary output.

---

## 6. Evidence index (file:line)

| Evidence | Location |
| --- | --- |
| Native AI bot spawner (server gate + ready gate) | `mission_templates.txt:2011` (trigger 18) |
| Bot troop/faction scan and selection script | `scripts.txt:249-250` (`multiplayer_find_bot_troop_and_group_for_spawn`; scan operand range 855–874) |
| Team-0 native AI troops (pistol, no ammo) | `troops.txt:5988`, `:5995`, `:6002` |
| Generic invader AI (Crazed Civilian, unarmed) | `troops.txt:6114`, `:6121` |
| Playable survivor classes / real loadouts | `troops.txt:6128`, `:6135`, `:6142`, `:6149` |
| Wave-visitor zombies 894–901 | `troops.txt:6261`, `:6268`, `:6275`, `:6282`, `:6289`, `:6296`, `:6303`, `:6310` |
| Generic-fill records 902–912 (incl. Tank/mounted/ranged) | `troops.txt:6317`, `:6324`, `:6331`, `:6338`, `:6345`, `:6352`, `:6359`, `:6366`, `:6373`, `:6380`, `:6387` |
| Invader wave slot table + invalid `-1` writes | `mission_templates.txt:2007` (trigger 14) |
| Wave spawner (branch logic, entries 32–39, counts) | `mission_templates.txt:2008` (trigger 15) |
| Zombie claw item / zombie-hand shield / round shield / warhorse | `item_kinds1.txt:2447`, `:2451`, `:2455`, `:2047`, `:602` |
| Ammo items | `item_kinds1.txt:635`, `:639`, `:643` |
| Native pistol / M16 | `item_kinds1.txt:2182`, `:2277` |
| Faction ids 15/16 | `factions.txt:33`, `:35` |
| Our clones | build `troops.txt:6869`, `:6876`, `:6883`, `:6890` |
| Our appended triggers 25–30 (initial squad, hold/orders, wave top-up, fallback) | build `mission_templates.txt:2018`–`:2023` |
| Our roster patch candidates and build identity | build receipt `ZOMBIEEE_REMASTER.json` (`native_roster_patch.invader_candidates`, `runtime_verified=false`) |

---

## 7. Limits / unknowns (not claimed)

- **No engine test:** this is a static file review. Whether native AI fires, blocks, mounts or
  holds positions is **unknown** until a sealed WSE2 run observes it.
- Unset faction slots (waves 12/14) may resolve to troop 0 or no troop at engine level; the
  literal operand is 0 and the runtime effect is **unknown**. Do not claim a specific failure.
- Duplicate troop IDs are unambiguous at the ordinal level but a name-based lookup is ambiguous;
  engine behavior for name lookups was not tested.
- The build compared is the latest **staged** City build present at review time, bound by its
  receipt (`final_native_sha256`, `runtime_verified=false`). It is not a release acceptance and
  may be superseded by D's next rebuild.
- REA was not used: the compiled mission/scripts/tables are plain text and were decoded directly;
  no binary reverse engineering or external tool installation was required.
