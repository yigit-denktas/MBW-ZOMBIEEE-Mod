# Warband engine & combat-AI research — what is controllable, what is engine-internal (task-61)

**Status: docs-only desk research. No Warband/WSE2/Bannerlord process was launched; no game code was decompiled or copied; no asset was extracted.** Engine facts below come from (a) public module-system headers, (b) a Native-derived module source mirror (read-only, cited by URL/line, no code copied), (c) third-party WSE2 SDK documentation, (d) dated community analysis, and (e) our own sealed evidence docs. Anything not established that way is marked **[unverified]**.

Companion document: `reference/BANNERLORD_AI_ENGINE_RESEARCH.md` (task-56). Observation date: **2026-10-24**. Base: `main` `8b4f8c4`, worktree `agent/h-warband-research`.

This is design input for A (behaviour/build), C (telemetry/summary) and D (sealed validation). It changes no build, claims no acceptance, and supersedes two assumptions recorded elsewhere in the project (see §4.3, §5.2, §5.4): the "native groups 26/28/29/31" interpretation and the belief that AI behaviour/rout state is unreadable.

---

## 1. Sources actually used

| # | Source | Type / date | What it establishes here | Limits |
| --- | --- | --- | --- | --- |
| S1 | [Veehats/WarbandCoop `header_operations.py`](https://github.com/Veehats/WarbandCoop/blob/786de5c3735546cb29dd89e3cb6dceb6fff18113/header_operations.py) and [`header_triggers.py`](https://github.com/Veehats/WarbandCoop/blob/786de5c3735546cb29dd89e3cb6dceb6fff18113/header_triggers.py) (public 1.174-era module-system headers; commit `786de5c`, observed 2026-10-24) | Public headers | Opcode ids/signatures/comments, trigger constants (`ti_*`), native ops used in this document | Declarations only; they do not prove engine behaviour |
| S2 | [LilyModzStuff/warband_mod_source](https://github.com/LilyModzStuff/warband_mod_source) — Native-derived module source (commit `c9737d7`, 2019-04-05; observed 2026-10-24) | Public module source (community mirror) | Multiplayer bot spawn/leader logic, `add_visitors` group argument, `agent_fix_division`, battle-tactic scripts, Native battle morale/rout scripts and their 3 s trigger | A mod source (Diplomacy lineage), not official Native; some Native code is commented out/modified. Read-only, no code copied |
| S3 | [cvlc/tgsmod `header_operations.py`](https://github.com/cvlc/tgsmod/blob/master/header_operations.py) (2015-era header mirror; observed 2026-10-24) | Public header (older baseline) | Attribution baseline: distinguishes ops present by 2015 from later additions | Old; not a complete 1.174 opcode set |
| S4 | [Mount&Blade Modding Wiki — List of operations](https://mbmodwiki.github.io/List_of_operations) (public domain statement; DB generated 2011-03-19; observed 2026-10-24) | Community wiki | Independent opcode cross-check (ids/signatures) | 2011 snapshot; lacks later ops |
| S5 | [Chinese forum thread 2109811 — "AI formations and making formations with Native mechanisms"](https://bbs.mountblade.com.cn/forum.php?mod=viewthread&action=printable&tid=2109811), author 黑暗路西法, **2025-02-09** (observed 2026-10-24) | Community analysis (quotes Native scripts) | Native three-stage battle AI, ~5 s tactic re-application, classes/divisions 0–8, `team_give_order`/`mordr_*`/`mordr_form_*` recipes, `agent_set_division`/`class_set_name` usage | Community reconstruction; quotes a source version where the tactic triggers are active (our S2 mirror has them commented out) |
| S6 | [Chinese forum thread 2111625 — in-mission AI control pitfalls](https://bbs.mountblade.com.cn/forum.php?mod=viewthread&action=printable&tid=2111625) (published 2025; recorded in `reference/WARBAND_AI_MODDING.md`, observed 2026-10-24) | Community experiment log | Movement vs weapon-switch vs attack AI are independent; `agent_force_rethink` scope; scripted-destination queue/freeze pitfalls | Second-hand here (via our prior research doc; thread not re-fetched for this task) |
| S7 | [OSP — "Overhauled Morale and Routing" (TaleWorlds Forums)](https://web.archive.org/web/20240813154826/https://forums.taleworlds.com/index.php?threads/overhauled-morale-and-routing-also-reduces-stuttering.320256/), started **2014-12-13**; Wayback capture 2024-08-13 (observed 2026-10-24) | Community OSP code thread | Documents that Native battle morale/rout is module-script driven (courage slots, battle ratio, 3 s trigger, `agent_start/stop_running_away`, 4-second grace, hero exemption); documents `ti_on_order_issued` and `agent_get_simple_behavior` use; nested per-agent loops cause stutter | OSP code is community work with its own permissions — **no code copied**, facts only |
| S8 | [WSE2 v1.1.5.4 release](https://github.com/Ruslan-700/WSE2-Releases/releases/tag/v1.1.5.4) (published **2026-10-14**; project pin `reference/WSE2_1.1.5.4.json`) and the pinned [WSE2 SDK addon header](https://github.com/Ruslan-700/WSE2-Releases) (local copy observed 2026-10-24) | Third-party runtime + SDK | WSE2 extension opcodes used by the project (AI set/read, time/action speed, weapon-switch/fight/aim toggles) | Third-party, not official; project pin is metadata-only (no artifact independently hashed) |
| S9 | Project evidence docs: `reference/CITY_AI_WAVE_AUDIT_2026-10-23.md`, `reference/CITY_ROUND_WAVE_LIFECYCLE_2026-10-24.md`, `docs/DIAGNOSTICS.md`, `reference/WARBAND_AI_MODDING.md` (2026-10-23/24) plus sealed `local/session` host logs (gitignored, observed 2026-10-24) | Our own static + sealed evidence | ZOMBIEEE 25-trigger City chain, wave/round lifecycle, group-getter convention, corrected group values | Runtime evidence is bounded to the sealed runs it came from; local logs are not public artifacts |
| S10 | [Nexus Mods 2475 — Motomataru FormAI lineage](https://www.nexusmods.com/mbwarband/mods/2475) (WB 1.153/2012; v1.168/2017) via `reference/WARBAND_AI_COMMUNITY_SOURCES.md` | Community mod / provenance | Licence boundary for community formation AI: link-only, no code imported | Page has been Cloudflare-403 historically; provenance recorded by E's source pack |

**Inaccessible / recorded:** live TaleWorlds forum pages are frequently 403 to this machine; the 2014 OSP thread was read through a 2024 Wayback capture. S6 was not independently re-fetched for this task; it is cited through our prior research document. WSE2 binaries were not downloaded for this task; only public metadata and the SDK addon header were read.

---

## 2. Engine basis and control surface

Warband is a proprietary engine (RGL) with a **module system**: Python-ish source tables compile to game data (`mission_templates.txt`, `scripts.txt`, `variables.txt`, …); mission logic is expressed as **opcodes** inside mission-template triggers and scripts. There is no official C# surface, no Harmony, no engine source. WSE2 is a separate third-party runtime that extends the opcode set and adds Lua instrumentation; it does not open the engine's decision code (S1, S8).

### 2.1 Mission, entries, triggers

A mission template defines spawn entries (troop counts, flags, AI flags, equipment) and a list of **triggers**. Public Native comments define a trigger as five fields (S2 `module_triggers.py` header; S1 `header_triggers.py`):

1. **check interval** — how often conditions are evaluated (seconds);
2. **delay interval** — wait before running consequences after conditions pass;
3. **re-arm interval** — minimum time before the trigger can fire again (`ti_once` = never);
4. **conditions** block — executed on every check; empty conditions are always true;
5. **consequences** block — executed when conditions pass.

Special `ti_*` constants make triggers event-driven instead of polled: `ti_before_mission_start (-19)`, `ti_after_mission_start (-20)`, `ti_on_agent_spawn (-25)`, `ti_on_agent_killed_or_wounded (-26)`, `ti_on_order_issued (-71)`, `ti_server_player_joined (-15)`, `ti_on_multiplayer_mission_end (-16)` (S1 `header_triggers.py`; the order-issued constant is absent from the 2015 header S3 and present in 1.174-era S1, so it is a later native trigger — exact patch version **[unverified]**).

This is the Warband equivalent of Bannerlord's `MissionBehavior` callback set — except the callbacks are script blocks and the event payload arrives through `store_trigger_param_*`.

### 2.2 Server authority

Multiplayer missions run server-authoritative logic: the dedicated host evaluates server-gated triggers (`multiplayer_is_server` = 417), owns bot spawning/management, and synchronises agents to clients. The Native multiplayer template includes a **`multiplayer_server_manage_bots`** trigger every 3 s that keeps each bot's leader valid (S2 `module_mission_templates.py:3207`). Any behaviour experiment that must change AI is server-side work; client-side triggers cannot.

### 2.3 What the module system can and cannot control

| Layer | Controllable from module code? | Evidence |
| --- | --- | --- |
| Which agents exist, team, troop, equipment | Yes — `add_visitors_to_current_scene`, `spawn_agent`, `set_spawn_position`, equipment overrides at spawn | S1/S2 |
| Formation/division membership | Yes — `agent_set_division` (1783); class is read with `agent_get_class` (1772), while troop class is data (`troop_get_class`/`troop_set_class`, 1516/1517). Divisions are the order channel | S1, S5 |
| Team orders (move/hold/charge/fallback/retreat, fire, weapon usage, form/spacing) | Yes — `team_give_order` (1790), `team_set_order_position` (1791), `mordr_*`, `wordr_*`, formation orders | S1, S5 |
| Read back orders / order position / gap | Yes — `team_get_movement_order`, `_weapon_usage_order`, `_hold_fire_order`, `team_get_order_position`, `team_get_gap_distance` | S1 |
| Per-agent movement scripting | Yes — `agent_set_scripted_destination(_no_attack)`, `agent_clear_scripted_mode`, `agent_force_rethink` | S1, S6 |
| AI target selection scoring | **No** — engine-internal; only read via getters, and influence via scripted destination/behaviour/alarm/aggressiveness | S1 |
| Attack/defence execution, pathfinding, formation geometry | **No** — engine-internal; orders are advisory inputs to it | S1, S5 |
| Alert/alarm state | Yes — `agent_is_alarmed`/`agent_set_is_alarmed` (1806/1807) | S1 |
| Aggressiveness / speed / accuracy / damage knobs | Yes — `agent_ai_set_aggressiveness` (1753), `agent_set_speed_limit` (1736), `agent_set_speed_modifier` (2093), `agent_set_accuracy_modifier` (2092), `agent_set_damage_modifier` (2091) | S1 |
| Simple behaviour (hold / go-to / melee / ranged / …) | Read: `agent_get_simple_behavior` (1738, native); Set: WSE2 `agent_ai_set_simple_behavior` (3314) | S1, S8 |
| Rout/running-away state | Read: `agent_is_routed` (1699); start/stop: `agent_start_running_away` (1751), `agent_stop_running_away` (1752); decision logic is **module script** in Native single-player battle | S1, S2, S7 |
| Spawn/round phase model | **No engine model** — waves/rounds are module globals and triggers in our mission template | S2, S9 |

**Key structural point:** Warband gives mods a rich *order and query* surface over an opaque individual AI. It does **not** give mods new per-agent decision logic, target-selection policies or a behaviour-component system.

---

## 3. AI architecture — how Native battle AI is layered

Community analysis of Native battle templates (S5) describes three stages, which map cleanly onto Bannerlord's three layers:

1. **Tactic selection** — once the first troop batch is spawned, module scripts choose a battle tactic from a small set (`btactic_hold=1`, `btactic_follow_leader=2`, `btactic_charge=3`, `btactic_stand_ground=4`; values from S5; tactic scripts `select_battle_tactic`, `battle_tactic_init`, `battle_tactic_apply` exist in S2 at `module_scripts.py:31244`, `:32193`).
2. **Initial deployment** — the tactic's init script sets a hold position, orders formations to hold/advance, and sets leader speed limits.
3. **Re-application** — Native re-runs the tactic script on a roughly **5-second cadence** until it falls back to an all-charge (S5; the quoted trigger is `(5, 0, 0, …)`).

Important caveat: in the S2 mirror the tactic trigger calls are **commented out** (`module_mission_templates.py:5567-5596`), while S5 quotes them active in Native. Both are consistent with the same fact: **the tactic layer is module-script code that a mod can enable, edit or remove** — it is not an immutable engine subsystem. Whether a given 1.174 mission runs it is per-template and must be checked, not assumed. **[unverified]** for our ZOMBIEEE template specifically (our decoded 25-trigger chain contains the invasion wave controller, not the Native field-battle tactic trigger).

Below the tactic layer:

- **Team/division order layer** — orders are addressed to a team and a *sub-class* (class/division 0–9, see §4). This is the layer a mod can reliably drive.
- **Individual AI layer** — engine pathfinding, target choice, attack/defence, weapon use. Observable through read-only getters (§5) but not scriptable except through engine-sanctioned knobs and scripted mode.

**There is no behaviour-tree or weighted-behaviour-layer API in Warband.** Contrast Bannerlord's `BehaviorComponent`/`GetAIWeight`/`BehaviorCoherence` system. Warband AI decisions are engine-internal; the modding vocabulary is *orders + a handful of per-agent flags*.

---

## 4. Teams, divisions, classes and "groups" — the namespace problem

### 4.1 Classes/divisions are the team-order address space

`header_mission_templates.py` (S1/S2) defines:

```
grc_infantry = 0, grc_archers = 1, grc_cavalry = 2, grc_heroes = 3, grc_everyone = 9
```

Native battle code iterates `try_for_range(":cur_group", 0, grc_everyone)` — i.e. **0..8 are valid formation/class slots and 9 means everyone** (S2 `module_mission_templates.py:3518-3533`; S5 explicitly notes "Native has 0–8, nine groups total"). Native also issues an order to division `8` with the comment "Division 8 to avoid potential conflicts" (S2 `module_mission_templates.py:412`). Community formation work extends the class table within 0–8 and names slots with `class_set_name` (S5, op 1837).

Ops:

- `agent_get_class` (1772), `agent_get_division` (1773), `agent_set_division` (1783) — S1.
- `team_give_order(team, sub_class, order_id)` (1790), `team_set_order_position(team, sub_class, position)` (1791), `team_get_order_position` (1794), `team_get_movement_order`/`_hold_fire_order`/`_weapon_usage_order`/`_riding_order` (1784-1787), `team_get_gap_distance` (1828), `team_set_order_listener` (1795), `team_get_leader`/`team_set_leader` (1792/1793) — S1.
- Order ids (S1/S2): `mordr_hold=0, follow=1, charge=2, mount=3, dismount=4, advance=5, fall_back=6, stand_closer=7, spread_out=8, use_blunt_weapons=9, use_any_weapon=10, stand_ground=11, hold_fire=12, fire_at_will=13, retreat=14, use_melee_weapons=15, use_ranged_weapons=16`, fire-command variants 17–21, `mordr_form_1_row..5_row=22..26`; `rordr_*`, `wordr_*`, `aordr_*`.

The order surface therefore covers: **movement intent, fire discipline, weapon-usage class, riding, and a coarse formation form/spacing** — but not arrangement geometry, facing, or per-agent target policy (those are engine/other-layer).

### 4.2 `agent_get_group` is not a division — it is leader/owner identity in multiplayer

This is the central namespace confusion behind "native groups 26/28/29/31". Evidence from Native-derived scripts (S2):

- `script_multiplayer_find_player_leader_for_bot` (line 13712) returns **`reg0 = player_no`** — the human player who will lead the bot.
- `script_multiplayer_find_bot_troop_and_group_for_spawn` (line 13823) documents `reg0 = troop_id, reg1 = group_id`, and in its body sets **`reg1 = :leader_player`**.
- `script_multiplayer_change_leader_of_bot` (line 13870) calls `agent_set_group(agent, leader_player)`.
- `multiplayer_server_manage_bots` (mission template line 3207) validates bots with `agent_get_group` and **`player_is_active(group)`**.
- The actual bot spawn call passes that value as the visitor's group:
  `add_visitors_to_current_scene(entry, selected_troop, 1, selected_team, selected_group)` (mission template line 3193), where `selected_group` came from the leader lookup.

So in the multiplayer bot path, **group = owning/leading player id**. It is a different namespace from the 0–9 sub-class used by `team_give_order`.

### 4.3 Correcting the "26/28/29/31" evidence

Earlier project docs (`docs/DIAGNOSTICS.md`, written while the `agent_get_group` call convention was still being fixed) recorded native defender bots "in groups 26/28/29/31". The sealed log shows why:

- pre-fix sample lines: `id=26|group=26`, `id=28|group=28`, … — **group equals the agent id**, i.e. the getter returned its own argument (wrong call convention / echo), not a group.
- post-fix samples in a later sealed host log: `groups_team0=9:1,11:1,12:1,15:1`, `groups_team1=8:1,10:1,13:1,14:1`.

Therefore:

1. **26/28/29/31 were never group values** — they were agent ids echoed by the then-unfixed accessor. The doc claim should be treated as superseded.
2. Real observed values after the fix are **8..15**, four per team in that run. Their exact identity is **not established**. Candidate hypotheses:
   - H1 leader/owner player ids (the documented Native meaning) — but a bot-only host should not have eight human leader ids; if the engine/WSE2 assigns bots to virtual leader slots, this remains plausible.
   - H2 an engine/WSE2 bot-group slot namespace (8..15 is consistent with a small per-team slot pool);
   - H3 a spawn/entry-derived id unrelated to both.
3. Either way, **these values are not `team_give_order` sub-classes**. Passing them as `sub_class` would not address the agent's class/division and may address nothing (or class 8/9 semantics), which is why "adopt bots into groups 5–7" via orders cannot work as written.

### 4.4 Correct path for our survivor/defender adoption

1. Use `agent_set_division(agent, d)` to place each bot in a real order-addressable division `d ∈ 0..8` (5/6/7 are fine as our reserved roles; they are within the valid range).
2. Re-issue adoption on the same cadence as the orders, because the engine/other scripts may reassign divisions (Native itself has `script_agent_fix_division` at `module_scripts.py:73544` precisely to correct engine-applied divisions on agents).
3. Read back with `agent_get_division` (and `agent_get_class`) and verify with `agent_get_simple_behavior` before assuming orders reach the agent.
4. Issue `team_give_order(team, division, order)` / `team_set_order_position(team, division, pos)` to those divisions only.
5. **Do not** pass leader/group ids as `sub_class`, and **do not** pass 5–7 as the `group` argument of `add_visitors_to_current_scene` in multiplayer: the Native MP call passes the **leader player id** there. Passing a formation slot is a type error that can explain visitors not spawning. Inspect the original trigger operands before changing any visitor call.

**Experiment gate:** whether the engine retains a scripted division change for MP bots, and whether orders to division 5/6/7 actually steer them, is **unverified**; §10 gives the decisive tests.

---

## 5. Agent AI decisions: what can be observed and nudged

### 5.1 Target selection

The scoring is engine-internal; Native exposes read-only accessors:

- `agent_ai_get_look_target` (2080), `agent_ai_get_move_target` (2081), `agent_ai_get_behavior_target` (2082) — S1.
- `agent_ai_get_num_cached_enemies` (2670) and `agent_ai_get_cached_enemy` (2671) — "nearby enemies, nearest to farthest" (S1); these are **absent from the 2015 header** (S3) and present in 1.174-era S1, so treat as later-native and test availability on the pinned runtime. **[unverified]** exact patch.
- `agent_get_attack_action` (1763) exposes attack state machine values (`free/readying/releasing/completing/parried/reloading/after_release/cancelling`) — S1.
- Scripted influence: `agent_set_scripted_destination` / `_no_attack` (1730/1748), `agent_clear_scripted_mode` (1735), `agent_force_rethink` (1732), plus WSE2 `agent_set_scripted_destination_no_attack` semantics; pitfalls documented in S6.

There is **no native target setter**. A mod can force a scripted *destination* (with or without attacks), toggle behaviour, or disable fighting, but cannot assign an arbitrary target.

### 5.2 Ranged vs melee, weapon use

- `agent_get_simple_behavior` (1738, native) returns the `aisb_*` behaviour (`hold=0, go_to_pos=1, mount=2, dismount=3, melee=4, ranged=5, ranged_horseback=6, charge_horseback=7, maneuver_horseback=8, flock=9, race=10, patrol=11, no_enemies=12, horse_hold=13, horse_run_away=14`; constants S1/S2). **This is a native readback we previously treated as unavailable.**
- WSE2 sets it: `agent_ai_set_simple_behavior` (3314) with optional guaranteed time; WSE2 also has `agent_ai_set_can_weapon_switch` (3343), `agent_ai_set_can_fight` (3344), `agent_ai_set_can_aim` (3352) (S8).
- Weapons/ammo: `agent_get_wielded_item` (1726), `agent_get_ammo` (1727), `agent_set_ammo` (1776), `agent_get_ammo_for_slot` (1825), `agent_set_item_slot_ammo` (3305 WSE2), `agent_get_attack_action` (1763), `agent_set_wielded_item` (1747), `agent_set_attack_action` (1745), `agent_set_defend_action` (1746) — S1/S8.
- Fire discipline is a **team order**, not a per-agent toggle: `mordr_hold_fire`, `mordr_fire_at_will`, `mordr_use_ranged_weapons`, `wordr_*`; readbacks exist (S1).
- Accuracy/damage/speed: `agent_set_accuracy_modifier` (2092, 0–1000%), `agent_set_damage_modifier` (2091), `agent_set_speed_modifier` (2093, 0–1000%), `agent_set_speed_limit` (1736, AI-only km/h) — S1.

### 5.3 Alertness, aggressiveness, behaviour flags

- Alarm: `agent_is_alarmed`/`agent_set_is_alarmed` (1806/1807). The alert state is real and script-visible; semantics of "alarmed" are engine-defined and not documented in the header. **[unverified]** exact effect.
- `agent_ai_set_aggressiveness` (1753): header comment "100 is default; higher = less likely to run back". This is about **running back/reforming/skirmishing**, not about rout — do not conflate.
- `agent_ai_set_always_attack_in_melee` (1737) for siege ladders; `agent_ai_set_can_crouch` (2083); `options_set_combat_ai` (265, 0 good/1 average/2 poor) and `options_set_combat_speed` (268) are global difficulty/pacing, not per-agent AI design tools.

### 5.4 Morale, rout and retreat

Warband's battlefield morale/rout is **not engine-opaque in single-player**: Native implements it in module scripts (S2, S7):

- Per-agent slots `slot_agent_is_running_away` (15) and `slot_agent_courage_score` (16) (S2 `module_constants.py`).
- `script_apply_effect_of_other_people_on_courage_scores` (line 31448) spreads courage changes from nearby casualties/kills; `script_decide_run_away_or_not` (line 31848) starts/stops running away using courage threshold vs hit points and a battle ratio; `script_cf_agent_can_rout` (line 70325) gates routing by casualty ratio.
- Running away is applied with **`agent_start_running_away` (1751)** and cleared with **`agent_stop_running_away` (1752)**; the script calls `agent_clear_scripted_mode` first and respects a 4-second grace period and hero exemption.
- Native battle template invokes this on a **3-second cyclic trigger** `(3, 0, 0, …)` for every alive human agent (`module_mission_templates.py:5580-5588`).
- Rout state is readable: `agent_is_routed` (1699). `mordr_retreat` (14) is a separate **team order** that can force retreat independent of courage.

For our multiplayer invasion mission:

- The ZOMBIEEE City template's 25 native triggers are the invasion wave/round controller (S9); **no Native field-battle courage trigger is part of that chain** per A's audit. Therefore zombie "retreat" from the Native morale script is not expected — but this is a static claim and must be observed. **[unverified at runtime]**
- Nevertheless, the engine ops exist, and another script/mod could call them. Our no-retreat rule remains: never issue `mordr_retreat` to team 1, never let a configured rout trigger run for team 1, and if `agent_is_routed` is ever observed on team 1, the corrective op is `agent_stop_running_away` (mutating; test-mode only).
- For survivors, Bannerlord-style morale shock is unnecessary: our intended "fall back to anchor" is a movement order to a rear position, not a rout. Adding courage/rout to survivors would create exactly the unrecoverable loop the owner wants to avoid.

---

## 6. Mission triggers and the wave system

### 6.1 Trigger mechanics (Warband's "mission behaviour" equivalent)

Per S1/S2 (§2.1): check interval, delay, re-arm, conditions, consequences. Empty conditions are always true. `ti_once` disarms. Check interval is in seconds; the engine will not check more often than its mission tick allows, so 0.1 s is the practical floor for scripted polling **[unverified exact floor]**. Event triggers (`ti_on_agent_spawn`, `ti_on_agent_killed_or_wounded`, `ti_on_order_issued`, etc.) avoid polling cost.

Cost matters: each check runs the whole condition block; a `try_for_agents` loop inside a frequent trigger is O(agents) per check. The OSP morale thread (S7) documents exactly this failure mode (nested per-agent loops over the whole battle every 3 s causing stutter). Our wave/order triggers should stay bounded and use precomputed counts where possible.

### 6.2 The ZOMBIEEE City wave lifecycle (our own evidence)

Decoded from the original compiled template (S9 `CITY_ROUND_WAVE_LIFECYCLE_2026-10-24.md`). The bullet labels below combine A's functional reading with the public header's `ti_*` meanings; where they differ, the functional reading is A's, not an official label:

- **Trigger 3** — interval `-19` = `ti_before_mission_start` in the public header (A's audit calls it an after-start init): initialises `game_type=7` and `wave_number=0`.
- **Trigger 6** — interval `-25` = `ti_on_agent_spawn` in the public header (A's audit reads it as the round-start reset): clears `round_ended`.
- **Trigger 7** — interval `-26` = `ti_on_agent_killed_or_wounded` in the public header (A's audit reads it as round end): sets `round_ended=1` **and resets `wave_number=0`**.
- **Trigger 15** (1 s periodic, server-gated): increments `wave_number` and spawns that wave's visitors.

The interval→function mapping for triggers 3/6/7 is **[unverified]** interpretation and should be confirmed against the compiled template operands before any logic is hung off it.

Consequences:

- Wave progression is not an engine subsystem; it is a **module-global + trigger** design. A "wave end" means whatever those globals/triggers say it means.
- Round end resets the wave; wave 2 is a survival outcome, not a counter that can simply be incremented without changing difficulty.
- Any wave/arrival clarity feature (phase, remaining, next-wave ETA, arrival events) must be **module-owned state** exposed to telemetry; there is no engine phase query to read (contrast Bannerlord's `MissionAgentSpawnLogic`).

### 6.3 Bot spawning and `set_bot_count`

- Bots are spawned through the multiplayer spawn path: leader lookup → troop selection → `add_visitors_to_current_scene(entry, troop, count, team, group)` (S2 §4.2). The bot's `group` argument is its leader/owner player id.
- `$g_multiplayer_num_bots_team_1/2` are the server bot-count globals (S2 `module_scripts.py:13712-13860`); `ready_for_spawning_agent` gates spawn.
- `set_bot_count` is **not a native opcode** — it is a server/launcher command used by our rotation (`reference/CITY_DEDICATED_BOT_CONFIG_FINDING_2026-10-24.md`), which changes those globals/engine config. Do not look for it in `header_operations.py`.
- The Native `multiplayer_server_manage_bots` trigger (3 s) re-validates bot leaders; this is why a bot's "group" can change over time, and why a leader/owner id is not a stable formation address.

### 6.4 Event triggers available for telemetry

- `ti_on_agent_spawn` (-25): per-agent spawn event (payload via `store_trigger_param_1` = agent).
- `ti_on_agent_killed_or_wounded` (-26): death/wound event (dead agent, killer, wounded flag).
- `ti_on_order_issued` (-71): order event; the OSP thread uses trigger param 1 = order, param 2 = agent (S7). It is present in 1.174-era headers (S1), absent from 2015 headers (S3); exact support on our pinned WSE2 build must be tested. **[unverified]**

These are the Warband analogue of Bannerlord's `MissionBehavior` callbacks, and are the cleanest way for C to obtain **wave/arrival events** and **order-reachability evidence** without polling.

---

## 7. WSE2 extensions (pinned v1.1.5.4)

WSE2 is a third-party runtime that extends the module system; it is **not** an official Warband update and not Bannerlord (S8). For AI work the relevant extensions in the pinned SDK addon header are:

| Op | No. | Use / caveat |
| --- | --- | --- |
| `agent_ai_get_move_target_position` | 3312 | read the agent's move-target position |
| `agent_ai_set_simple_behavior` | 3314 | set `aisb_*`; optional guarantee; **the counterpart to native getter 1738** |
| `agent_get_position_in_group` | 3333 | position within group (formation context) |
| `agent_set_time_speed_multiplier` / `get_` | 3335 / 3336 | whole-agent simulation speed (attacks/reloads too), not just movement |
| `agent_set_action_speed_modifier` | 3340 | action-only speed, separate from movement |
| `agent_ai_set_can_weapon_switch` | 3343 | stop AI melee switch (hold-and-fire) |
| `agent_ai_set_can_fight` | 3344 | engage toggle, not a fire toggle |
| `agent_ai_set_can_aim` | 3352 | ballistic-arc aiming toggle |
| `ai_mesh_face_group_translate` | 3621 | navmesh face-group move (base-building/doors) |

WSE2 also provides a Lua instrumentation surface (S8 SDK `luaGuide.html`) used by our recorder; it does not expose new AI decision logic, behaviour trees or target selection. All WSE2 specifics are pin- and version-sensitive; the project pin is metadata-only and the binaries were not independently verified here.

---

## 8. Comparison with Bannerlord's three-layer AI

| Concept | Bannerlord (task-56 doc) | Warband (this doc) |
| --- | --- | --- |
| Tactic layer | Engine tactic AI class, commander personality, terrain/composition (dev blog) | Module-script `select_battle_tactic`/`apply` layer, ~5 s cadence, removable/commented; **not** an engine API |
| Formation layer | `Formation` object, 6 independent order channels, `FormationAI` with weighted `BehaviorComponent`s, `GetAIWeight`/`BehaviorCoherence` | Team orders to class/division 0–9; `mordr_*` movement/fire/weapon/form subset; no behaviour components, no arrangement API, no weights |
| Individual layer | `AgentAI`/`HumanAIComponent`, simple behaviour table parameterised by orders, read/write API | Engine-internal engine AI; native readbacks (targets, simple behaviour, attack action, rout, alarm) + knobs (aggressiveness, speed/accuracy/damage, alarm, scripted mode) |
| Behaviour tree | Not documented; weighted behaviour selection | No equivalent anywhere |
| Target selection | Formation target + agent target, overridable hooks | Engine-internal; read-only getters/cache; no setter |
| Morale/panic | Engine morale + panic spread + replaceable panic handler; dev-blog model | Native **module-script** courage/rout in SP battle (3 s trigger); `agent_start/stop_running_away`, `agent_is_routed`; absent from our MP invasion trigger chain (static) |
| Spawn/round state | `MissionAgentSpawnLogic` exposes total/initial/remaining/phase events | No engine phase model; module globals + triggers (wave_number, round_ended) |
| Modding surface | C#/XML/`MissionBehavior`/Harmony, behaviour extension | Opcodes/triggers/scripts, WSE2 opcodes+Lua; order-steering only |
| Debuggability | `DebugMore`/`DebugScores`, formation queries | Getter opcodes, order readbacks, `ti_on_order_issued`, our Lua recorder |

**Design conclusion:** Bannerlord's replaceable behaviours are not available here. Warband's usable abstraction is **"intent owner → orders to divisions → engine executes, with readback verification"**. Any Bannerlord-inspired feature must be expressed as (i) module state/triggers, (ii) team orders, (iii) bounded per-agent flags, and (iv) telemetry proof. This is the same conclusion as the Bannerlord doc, but with the limits made concrete.

---

## 9. Adopt / adapt / avoid (Warband-specific)

| Decision | Item | Why / caveat |
| --- | --- | --- |
| **Adopt** | Module-level tactic/state owner with a ~5 s re-plan cadence | Native does exactly this; cheap and legible; matches our 5 s order trigger |
| **Adopt** | Orders to **divisions 0–8** as the only group-intent mechanism; readback (`agent_get_division`, `team_get_movement_order`) before claiming | This is the actual addressable surface; group ids are not |
| **Adopt** | Event triggers for evidence: `ti_on_agent_spawn`, `ti_on_agent_killed_or_wounded`, `ti_on_order_issued` | Turns telemetry from polling into events; order-issued is the only direct proof that an order reached a division |
| **Adopt** | Native readbacks now confirmed: `agent_get_simple_behavior`, `agent_is_routed`, target getters/cache, attack action | Replaces earlier "unavailable" assumptions; each needs a capability flag and runtime test |
| **Adapt** | Bannerlord weighted mode choice → small module state machine with dwell/hysteresis (`HOLD_FIRE`, `FALLBACK_TO_ANCHOR`, `REGROUP`, `LIMITED_ADVANCE`) | Implement in globals/triggers; no engine AI hook |
| **Adapt** | Formation classes → divisions 5/6/7 roles (screen/ranged/reserve) | Only after adoption is proven; otherwise it is a label, not a behaviour |
| **Adapt** | Morale-shock idea → do **not** add rout to zombies; for survivors, fallback is a movement order | Native courage system would create the loop we are trying to remove |
| **Adapt** | Bannerlord spawn-state model → module-owned wave phase/arrival events exposed to C | No engine query exists; owner must be module state |
| **Avoid** | Treating `agent_get_group` as a division or passing group ids as `team_give_order` sub-classes | Group is leader/owner identity in MP; values 8..15/26..31 are not classes |
| **Avoid** | Passing 5–7 as the `group` argument of `add_visitors_to_current_scene` in MP | Native passes leader player id; wrong argument type may explain visitor spawn failures |
| **Avoid** | Per-agent `agent_set_scripted_destination` for group movement | Documented queue/freeze/formation-breaking pitfalls (S6); order layer exists |
| **Avoid** | Adding `mordr_retreat` or Native courage/rout logic for zombies | Owner requirement; use `agent_stop_running_away` only as an observed-corrective safety |
| **Avoid** | Global `mission_set_time_speed` for slow zombies | Alters the whole battle clock and telemetry cadence; use movement-only speed modifiers |
| **Avoid** | Heavy `try_for_agents` loops in high-frequency triggers | Documented stutter source (S7); keep bounded and event-driven |
| **Avoid** | Importing OSP/FormAI/Native code or assets | Community-code permissions differ (S7, S10); this doc records facts only |

**Corrections to earlier project assumptions**, to be folded into A/C docs:

1. "Native bots are in groups 26/28/29/31" — those were agent-id echoes; real observed groups are 8..15 and still not sub-classes (§4.3).
2. "No AI behaviour getter" — `agent_get_simple_behavior` (native 1738) and `agent_is_routed` (1699) exist; telemetry can read behaviour and rout state (§5.2, §5.4).
3. "add_visitors group = formation" — in MP the fifth argument is the leader/owner player id (§4.2/§4.4), a likely cause of our earlier visitor-spawn failure.

---

## 10. Concrete experiments for A / C / D

All write experiments are **test-mode only**, not evidence runs. Read-only probes can be sealed. Every experiment must record exact op availability and results; failed/absent stays unknown.

### A — behaviour/build

1. **Division adoption round-trip:** on the 5 s City order trigger, for each team-0 non-player bot set `agent_set_division(agent, 5/6/7)` by role, then read `agent_get_division` back and apply the role's `team_give_order` + `team_set_order_position`. Success = division persists over ≥2 samples and the agent's movement/`agent_get_simple_behavior` changes. If the engine resets division, reapply per tick and record the reset cadence.
2. **Order addressability matrix:** for sub-class values 0..9, issue `mordr_hold` and `mordr_charge` and record which agents/divisions move and what `agent_get_simple_behavior` reports. This establishes the actual mapping between class, division and orders on the pinned runtime.
3. **Zombie no-retreat audit:** read `agent_get_simple_behavior` and `agent_is_routed` for team-1 samples; never issue `mordr_retreat`/`mordr_stand_ground` to team 1; if routed is ever observed, test `agent_stop_running_away` plus `agent_ai_set_aggressiveness` as a corrective. Report whether the native courage trigger is even present in the built template (static check).
4. **Speed application:** keep `agent_set_speed_modifier` movement-only (55 + 5·wave target band 55–65%); verify by effective displacement, and treat the speed getter as suspect until the task-55 discrepancy is explained.
5. **Wave state owner:** one module owner for PREP/SPAWN/ACTIVE/CLEARED/INTERMISSION with globals; wave-end predicate includes alive team 1 and the spawn/visitor gate; emit arrival counts on transition; test `add_visitors` with the **leader/group argument corrected** (not 5–7).
6. **Behaviour pin:** WSE2 `agent_ai_set_simple_behavior` with a bounded guarantee on team-1 samples; read back and confirm it survives native re-planning; ensure `agent_force_rethink` is not undoing it.
7. **Order-issued logging trigger:** append a minimal `ti_on_order_issued` trigger (server-only, bounded) that records order/agent; verify it fires and that its payload matches the order issued. If unsupported, fall back to division readback.

### C — telemetry/summary

1. **Add confirmed readbacks:** `agent_get_simple_behavior` (aisb table), `agent_is_routed`, `agent_ai_get_behavior_target`, `agent_ai_get_look_target`, `agent_ai_get_move_target`, cached enemies (bounded count), `agent_get_attack_action`, `agent_is_alarmed`, `agent_get_division`, `agent_get_class`, team movement/hold-fire/weapon-usage order readbacks. Each with a capability flag and `unknown` semantics.
2. **Group semantics probe:** for observed group values, read `player_is_active(g)` and `player_get_team_no(g)` (guarded, valid agents only), and compare bot-only vs human-join runs. Report group histogram, division histogram and troop histogram together; never call it "division" without proof.
3. **Order-reachability evidence:** consume the `ti_on_order_issued` events if A adds the trigger; otherwise correlate division readbacks with positions. This is the decisive check for "orders reached the division".
4. **Retreat/rout:** report `agent_is_routed` counts per team per sample, plus forward/backward displacement as a secondary proxy; distinguish "routed" from "moving back" and from "not moving".
5. **Wave/arrival:** use spawn/death event triggers where available for wave and arrival events; otherwise counts + transition deltas; label proxies explicitly.
6. **Speed:** movement rate primary, modifier getter secondary/suspect.
7. **Summary:** add `ai.behaviour` (`aisb` histogram), `routing`, `orders`, `groups_vs_divisions`, and the wave/arrival block with explicit gaps.

### D — sealed validation

1. **Group/division semantics run:** one sealed read-only run with a human present and one bot-only run; compare group values and `player_is_active` results. This settles H1 vs H2/H3.
2. **Order addressability run:** after A's division adoption, sealed evidence that survivors in divisions 5/6/7 hold/fire (behaviour histogram, low movement, ranged weapon retention) and that order-issued events name those divisions.
3. **Zombie non-retreat run:** sealed evidence of zero `agent_is_routed` on team 1, no hold/stand-ground behaviour, forward displacement, and the configured speed band from movement data.
4. **Wave/arrival run:** one full transition with arrival counts/events; no "wave 0 forever while enemies exist".
5. **add_visitors correction run:** survivor visitors spawn with the corrected group argument; record the exact operand values used.
6. Keep `runtime_verified=false` and do not claim a mechanism until the sealed fields show it.

---

## 11. Open questions / unverified list

1. **Meaning of observed groups 8..15**: leader player ids, engine bot slots, or another namespace — **[unverified]**; the `player_is_active` experiment decides.
2. **Why 8..15 appear with no human players**: dedicated/WSE2 bot leader assignment is not documented; **[unverified]**.
3. **Division persistence for MP bots**: whether `agent_set_division` survives native re-planning/`multiplayer_server_manage_bots`; **[unverified]**.
4. **`add_visitors` team/group semantics in our WSE2 build**: Native code passes a leader id; the engine's validation and default group when omitted are **[unverified]**.
5. **Native courage trigger presence in the built ZOMBIEEE template**: project audit says the 25-trigger chain is the invasion controller, but a static confirmation (and a runtime `agent_is_routed` sample) is still needed.
6. **Exact native version for later ops** (`agent_ai_get_num_cached_enemies`/`cached_enemy`, `ti_on_order_issued`): present in 1.174-era headers, absent from 2015 headers; exact patch introduction **[unverified]**.
7. **`ti_on_order_issued` payload semantics and support under WSE2**: community-documented (trigger param 1 = order, param 2 = agent), not officially documented; test.
8. **Alarm semantics**: the header exposes get/set but not what "alarmed" changes in AI decisions; **[unverified]**.
9. **Native tactic layer active in our template**: S5 quotes it active in Native, S2 has it commented out; per-template check required.
10. **Trigger minimum interval / evaluation order**: header documents intervals but not the engine floor or ordering guarantees; **[unverified]**.
11. **WSE2 binary behaviour**: pinned metadata only; no artifact was independently hashed or run for this research.
12. **Source-version drift**: S2 is a 2019 Native-derived mod source; Native comments may have been edited. Treat line-level facts as source-attributed, not engine guarantees.

---

## 12. Handoff and review

- Only artifact from this task: this file. No build/tool/game change; no code or assets copied.
- Suggested use: A folds §4.4, §5.4, §9 corrections and §10-A into the task-53/54 behavior contract and the wave-state work; C folds §5, §6.4 and §10-C into telemetry (new readbacks change the "unavailable" assumptions); D uses §10-D as the next sealed matrix.
- Cross-review requested from **C or A**; their findings will be recorded here before the task is closed.
- The four project documents named in §9 should eventually be updated by their owners to reflect the group-id correction and the new readbacks; H lane does not edit them.

*End of research document.*
