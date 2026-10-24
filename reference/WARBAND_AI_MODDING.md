# Warband AI modding: community-grounded behavior research (task-35)

**Status: source-grounded research synthesis + an offline plan prototype. Not engine-verified gameplay; no acceptance claim.** Observation date 2026-10-24. Opcode *numbers* are definitions from the public module-system headers; *behavior* claims are attributed to the community sources below. Everything still needs D's sealed runtime evidence before it counts as observed.

## Sources actually read

| Source | What it is | Use |
| --- | --- | --- |
| [Mount&Blade Chinese forum thread 2111625 — "battle in-mission behavior control systems, research and pitfalls"](https://bbs.mountblade.com.cn/forum.php?mod=viewthread&action=printable&tid=2111625) | Player/modder experiment log, 2025 | Movement/attack/weapon-switch AI separation, `agent_force_rethink` scope, scripted-destination queue/arrival behavior, `agent_set_wielded_item` and `agent_set_attack_action` pitfalls |
| [Mount&Blade Chinese forum thread 2109811 — "AI formations and making formations with native mechanisms"](https://bbs.mountblade.com.cn/forum.php?mod=viewthread&action=printable&tid=2109811) | Native battle-tactic source walkthrough | Native 5 s tactic cadence, `team_give_order`/`team_set_order_position` patterns, `mordr_*` orders, `agent_set_speed_limit`, division regrouping via `agent_set_division` |
| [`cvlc/tgsmod`](https://github.com/cvlc/tgsmod) (`header_operations.py`, `module_scripts_form.py`) | Motomataru FormAI / TLD module system, community-maintained | Native op definitions; formation scripts; `(team_give_order, team, grc_infantry, mordr_hold_fire)`, `(team_give_order, team, grc_cavalry, mordr_fire_at_will)` usage |
| [`LilyModzStuff/warband_mod_source`](https://github.com/LilyModzStuff/warband_mod_source) (`source/header_mission_templates.py`) | Public Warband module-system headers | `grc_*`, `mordr_*`, `rordr_*`, `wordr_*`, `aordr_*`, `aisb_*` enum values |
| [`tldmod/tldmod`](https://github.com/tldmod/tldmod) (`ModuleSystem/module_scripts_form.py`) | Community formation AI implementation | Hold-fire/charge order sequencing in real module code |
| [`Ruslan-700/WSE2-Releases`](https://github.com/Ruslan-700/WSE2-Releases) (`Warband/WSE2 SDK/header_operations_addon.py`) + local `local/wse2-1.1.5.4/WSE2 SDK/header_operations_addon.py` | WSE2 1.1.5.4 SDK | WSE2-only ops: simple behavior, time speed multiplier, AI weapon-switch/fight/aim toggles, item-slot ammo, no-attack scripted destination, `shift_entry_point` |
| [`Veehats/WarbandCoop`](https://github.com/Veehats/WarbandCoop) (`header_operations.py`) | Public header mirror already used by the project | Cross-check of native numbers (`agent_get_group=1765`, `agent_get_team=1770`, `add_visitors_to_current_scene=1265`) |
| [TaleWorlds forum "Better MS Scripting Reference: header_operations expanded"](https://forums.taleworlds.com/index.php?threads/better-ms-scripting-reference-header_operations-expanded.213060/) | Community reference thread | **Inaccessible from this machine: HTTP 403 on 2026-10-24.** Recorded, not used as evidence. |
| Project docs [`CITY_SURVIVOR_AI_BEHAVIOR_CONTRACT_2026-10-24.md`](CITY_SURVIVOR_AI_BEHAVIOR_CONTRACT_2026-10-24.md), [`CITY_AI_WAVE_AUDIT_2026-10-23.md`](CITY_AI_WAVE_AUDIT_2026-10-23.md), [`CITY_ROUND_AWARE_REINFORCEMENT_2026-10-24.md`](CITY_ROUND_AWARE_REINFORCEMENT_2026-10-24.md) | Project source-grounded audits | Existing City hold/sector, wave-gating and reinforcement constraints |

## 1. How native AI control is layered

The movement AI, the weapon-switch AI and the attack-action AI are **independent**; you can change one without changing the others. `agent_force_rethink` is the exception: it resets movement **and** attack AI but does not reset the weapon-switch AI ([thread 2111625](https://bbs.mountblade.com.cn/forum.php?mod=viewthread&action=printable&tid=2111625)).

Native battle tactics are applied by a dedicated script that runs **every 5 seconds** and re-issues team orders; the tactic phase ends with a charge by default. This gives the safe command cadence for hold orders: issue once per re-plan (≈5 s), never per frame ([thread 2109811](https://bbs.mountblade.com.cn/forum.php?mod=viewthread&action=printable&tid=2109811)).

Native ops that matter here (numbers from the community header; comments are the header's own):

| Op | No. | Signature / note |
| --- | ---: | --- |
| `agent_set_scripted_destination` | 1730 | `<agent>, <position_reg>, <auto_set_z>[, <no_rethink>]` |
| `agent_force_rethink` | 1732 | resets movement + attack AI, not weapon-switch AI |
| `agent_clear_scripted_mode` | 1735 | returns the agent to native AI |
| `agent_set_speed_limit` | 1736 | speed limit in km/h, **AI only** |
| `agent_ai_set_always_attack_in_melee` | 1737 | siege ladder behavior |
| `agent_set_attack_action` | 1745 | `-2` clear, `0..3` direction, second value 0/1 = release/hold windup |
| `agent_set_defend_action` | 1746 | `-2` clear, direction, duration in 1/1000 s |
| `agent_set_wielded_item` | 1747 | switch to item; see pitfalls below |
| `agent_ai_set_aggressiveness` | 1753 | 100 default; lower = more likely to fall back |
| `agent_get_attack_action` | 1763 | `0 free, 1 readying, 2 releasing, 3 completing after hit, 4 parried, 5 reloading, 6 after release, 7 cancelling` |
| `agent_set_group` / `agent_set_team` / `agent_set_division` | 1766 / 1771 / 1783 | assignment used by team orders |
| `agent_unequip_item` | 1774 | removes the item; the removal is visually invisible |
| `agent_set_ammo` | 1776 | `<agent>, <item>, <value>` |
| `team_get_hold_fire_order` / `_movement_order` / `_riding_order` / `_weapon_usage_order` | 1784 / 1785 / 1786 / 1787 | read current team orders |
| `team_give_order` | 1790 | `<team>, <sub_class>, <order_id>`; order ids include movement **and** fire/weapon orders |
| `team_set_order_position` | 1791 | `<team>, <sub_class>, <position_reg>` |
| `team_get_order_position` | 1794 | read back the posted position |
| `set_spawn_position` / `spawn_agent` | 1970 / 1972 | `spawn_agent` stores the new agent id in `reg0` |
| `agent_set_speed_modifier` | 2093 | percentage, 100 default, allowed 0..1000 |
| `entry_point_get_position` | 1780 | `<position_reg>, <entry_no>` |
| `add_visitors_to_current_scene` | 1265 | `<entry>, <troop>, <count>, <team>, <group>` (team/group multiplayer-only) |
| `faction_set_slot` | 502 | used by the merged task-34 wave-table rewrite |

Enums (from `header_mission_templates.py`): `grc_infantry=0, grc_archers=1, grc_cavalry=2, grc_heroes=3, grc_everyone=9`; `mordr_hold=0, mordr_follow=1, mordr_charge=2, mordr_advance=5, mordr_fall_back=6, mordr_stand_closer=7, mordr_spread_out=8, mordr_stand_ground=11, mordr_hold_fire=12, mordr_fire_at_will=13, mordr_use_ranged_weapons=16, mordr_form_1..5_row=22..26`; `rordr_*`; `wordr_use_*`; `aordr_hold_your_fire=1`; and the WSE2 simple behaviors `aisb_hold=0, aisb_go_to_pos=1, aisb_melee=4, aisb_ranged=5, aisb_ranged_horseback=6, aisb_charge_horseback=7, aisb_patrol=11, aisb_no_enemies=12`.

WSE2-only ops used by this research (`header_operations_addon.py`): `agent_set_scripted_destination_no_attack=1748` (same as 1730, no attacks; `no_rethink` saves resources), `agent_ai_set_simple_behavior=3314` (`<agent>, <aisb>, [guarantee_seconds]`; persists until `agent_force_rethink`), `agent_set_item_slot_ammo=3305`, `agent_get_wielded_item_slot_no=3308`, `agent_set_time_speed_multiplier=3335` (fixed point), `agent_get_time_speed_multiplier=3336`, `agent_set_action_speed_modifier=3340`, `agent_ai_set_can_weapon_switch=3343`, `agent_ai_set_can_fight=3344`, `agent_ai_set_can_aim=3352`, `shift_entry_point=3623`.

## 2. Hold-and-fire instead of melee charge

**Use team orders, not per-agent scripted destinations, as the primary tool.** Community formation code repeatedly issues:

```text
(entry_point_get_position, pos, entry)
(team_set_order_position, team, sub_class, pos)
(team_give_order, team, sub_class, mordr_hold)          # 0: hold the posted position
(team_give_order, team, sub_class, mordr_hold_fire)     # 12: withhold ranged fire
# or (team_give_order, team, sub_class, mordr_fire_at_will)  # 13
(team_give_order, team, sub_class, mordr_use_ranged_weapons) # 16: keep ranged weapons
```

and re-issues them on the native ~5 s tactic tick ([thread 2109811](https://bbs.mountblade.com.cn/forum.php?mod=viewthread&action=printable&tid=2109811); real code in [`tldmod/module_scripts_form.py`](https://github.com/tldmod/tldmod/blob/master/ModuleSystem/module_scripts_form.py) uses `mordr_hold_fire` while charging and `mordr_fire_at_will`/`mordr_hold` combinations). The City build already uses `entry_point_get_position(1780) + team_set_order_position(1791) + team_give_order(1790, mordr_hold)` for divisions 5–7 every 5 s; the missing piece is the ranged orders and the per-agent safeties below.

**Why not per-agent `agent_set_scripted_destination`?** The community experiment log documents the pitfalls ([thread 2111625](https://bbs.mountblade.com.cn/forum.php?mod=viewthread&action=printable&tid=2111625)):

- destinations queue: a new destination is only taken after the previous one is reached; `agent_force_rethink` forces an immediate replan;
- after arrival the agent stays on the scripted spot; native AI does not resume without `agent_clear_scripted_mode`;
- one-shot native behaviors (victory cheer, etc.) are missed while scripted mode is active, so clear the mode and force a rethink when the scripted phase ends;
- setting a scripted destination per agent per tick creates straight-line, formation-breaking movement; in a hold scenario this fights the team-order layer.

If a move-without-attack behavior is needed, WSE2's `agent_set_scripted_destination_no_attack` (1748) is the compatible form (same destination semantics, but the agent will not attack enemies); clear it with `agent_clear_scripted_mode` (1735) plus `agent_force_rethink` (1732) when releasing the order.

**Per-agent WSE2 safeties for "hold and fire":**

- `agent_ai_set_can_weapon_switch(agent, 0)` (3343) — stops the AI's automatic melee switch. This is the most direct community-grounded fix for ranged defenders charging into melee: the AI keeps the ranged weapon.
- `agent_ai_set_simple_behavior(agent, aisb_hold, guarantee)` (3314) — force the hold behavior; with no/zero guarantee it persists until `agent_force_rethink`, so use a bounded guarantee (≈ the re-plan interval) and reapply rather than calling it every tick.
- `agent_ai_set_can_fight(agent, value)` (3344) — enables/disables engaging enemies. Useful to stop a charge, but note it is a **fight** toggle, not a fire toggle; a held agent that cannot engage may simply stand. Pair it with the fire/weapon orders rather than using it alone.
- `agent_ai_set_can_aim(agent, value)` (3352) — ballistic-arc aiming toggle; setting 0 makes ranged agents aim straight (useful for short-range hold/fire, changes accuracy semantics).
- `agent_ai_set_aggressiveness` (1753, native) can reduce run-back/flee behavior for a hold line.

**Recommended City plan (source-grounded, not yet observed):** on the every-5 s City trigger, per division 5–7 keep `team_set_order_position` at the guard/rear entry, `mordr_hold` (0), and add `mordr_hold_fire` (12) or `mordr_fire_at_will` (13) plus `mordr_use_ranged_weapons` (16) for ranged-capable divisions; once per adoption, apply `agent_ai_set_can_weapon_switch(agent, 0)` and a bounded `aisb_hold` guarantee to the sampled defender agents; only clear/rethink when switching back to charge, and never mix per-agent scripted destinations with the team-order hold.

## 3. Weapon choice and ammo

Native gets/sets: `agent_get_wielded_item` (1726, hand 0/1), `agent_get_ammo` (1727; value 1 = wielded item, 0 = all items), `agent_refill_ammo` (1728), `agent_set_ammo` (1776). WSE2 adds `agent_set_item_slot_ammo` (3305) and `agent_get_wielded_item_slot_no` (3308).

Community-documented pitfalls of forcing weapons ([thread 2111625](https://bbs.mountblade.com.cn/forum.php?mod=viewthread&action=printable&tid=2111625)):

- `agent_set_wielded_item` (1747) on a **shield** toggles equip/unequip; repeating it causes visible flicker — never spam it;
- the native weapon-switch AI resets when the agent changes target, so re-issuing the switch on target change causes one-frame seizures; the practical control is `agent_unequip_item` (1774) of unwanted weapons, but the removal is invisible (visual quality cost);
- fists count as a melee weapon to the native AI, so there is no clean way to guarantee a ranged weapon at close range; design the loadout/behavior instead (hold fire + can_weapon_switch=0 + team hold).
- `agent_set_attack_action` (1745) can be used to force/cancel an attack, but a held windup persists and suppresses native attacks until cancelled with `(agent_set_attack_action, agent, -2, 0|1)`; `agent_set_defend_action` (1746) can cancel an ongoing windup (duration in 1/1000 s).
- windup completion time is **not queryable**; it can only be estimated from known proficiency/weapon-speed conditions (same source).

Firearm behavior is therefore: keep the ranged weapon + hold-order/fire order + ammo control, and detect failures with C telemetry (`ai_sample.weapon/ammo/weapon_mode`, `defender_modes`, `ranged_team0`/`melee_team0`) rather than forcing the weapon every tick.

## 4. Slowing/steering zombies without ugly gear

Per-agent speed can be changed with no equipment at all:

- **`agent_set_speed_modifier` (2093, native)** — percentage, 100 default, range 0..1000. This is the primary no-gear slow: e.g. 60–80% for slow Zombies, scaled per wave if desired. It affects movement speed, not the attack animations.
- **`agent_set_speed_limit` (1736, native)** — AI-only speed limit in km/h (community usage: limiting a formation leader so the squad is not outrun). Less precise for a horde-wide slowdown than 2093.
- **`agent_set_time_speed_multiplier` (3335, WSE2, fixed point)** — slows the agent's whole simulation including attacks; a 700 fixed-point value is 70%. Good for a shuffling horde, but attack windups/reloads lengthen too, which can make zombies feel less threatening instead of just slower. Read back with 3336.
- **`agent_set_action_speed_modifier` (3340, WSE2)** — action-only modifier; keep it separate from movement so you can slow animation without making movement glue-slow.

Do **not** use the global `mission_set_time_speed`: it rewrites the whole battle clock (player included), changes telemetry tick semantics, and is not a per-horde slow. Avoid 0%: a frozen agent cannot navigate/attack properly. No gear/shield removal is needed for any of these.

## 5. Waves, visitors and reinforcement

- Native wave tables live in the compiled mission templates; the original invasion waves/visitors are outside the generic bot selector (see project [`CITY_AI_WAVE_AUDIT`](CITY_AI_WAVE_AUDIT_2026-10-23.md) and A's merged task-34). `add_visitors_to_current_scene` (1265) is the native visitor spawn: `<entry>, <troop>, <count>, <team>, <group>` (team/group multiplayer-only); `shift_entry_point` (3623, WSE2) shifts an entry like the engine does for visitors.
- **A's merged task-34** rewrites invader faction wave slots 200..244 to the slow Zombie 894 with `faction_set_slot` (502) every 5 s, and refills the 8-defender team-0 line with `entry_point_get_position` (1780) → `set_spawn_position` (1970) → `spawn_agent` (1972) cloning troops 981..984, bounded by a target count. That is the source-grounded pattern: gate/rewrite visitors first, then refill bodies per round.
- **`set_bot_count` is not a native script op** — it is a server/launcher command (agent D's `set_bot_count 1 N` path). It selects native faction bots; the troop ids come from the compiled `multiplayer_find_bot_troop_and_group_for_spawn` logic A patched (`native_roster_patch`, 894..911 or 981..984). Do not look for `set_bot_count` in `header_operations.py`.
- Other spawn building blocks: `agent_set_team` (1771), `agent_set_group` (1766, team-order sub-class) and `agent_set_division` (1783, formation/utilised class); after `spawn_agent` the new agent id is in `reg0`.
- Round identity: original invasion triggers reset `wave_number` and store `g_round_start_time`; reinforcement must gate on both wave change and round identity, not wave alone ([`CITY_ROUND_AWARE_REINFORCEMENT`](CITY_ROUND_AWARE_REINFORCEMENT_2026-10-24.md)).
- Scaling strategy that matches the evidence: keep waves within the slow 894 family (A task-34), cap/scale counts per wave, and refill the defender line from the rear spawn point; reserve Fast/Tough/strong visitor classes for later waves only if they are explicitly re-enabled, and verify with telemetry rather than trusting wave numbers.

## 6. What D's sealed evidence must show (verification mapping)

C's task-31 telemetry maps each claim to a measured field:

| Claim | Evidence to require |
| --- | --- |
| Defenders hold/fire instead of charging | `ai_sample.weapon/ammo/weapon_mode`; `defenders.weapon_modes` (ranged vs melee), `ranged_agents_team0` vs `melee_fallback_team0`; positions `moving`/`hold_samples`; no melee-only drift |
| Weapons/ammo actually used | `defenders.weapons` histogram, `ammo {zero,positive}`, `weapon`/`ammo` per sample |
| Zombie speed changed without gear | sample positions/`moving` cadence, `defender_deaths` vs `engagement.defender_kills`; troop ids unchanged (894 family) |
| Wave visitors gated/scaled | `waves.wave1.team1_classes` (native_zombie vs generic/defender/survivor/unknown), wave progression, troop histograms showing only 894-family |
| Defender refill works | `defenders.observed`, `troops` 981–984 counts, `alive`, deaths not permanent, `defenders.division_source` honest |
| Shield/action/mounted claims | **Unavailable** until a verified getter exists; summary raises `shield_telemetry_unavailable`/`action_telemetry_unavailable`/`mounted_telemetry_unavailable` |

Keep `runtime_verified=false` and `hold_behavior_observed=false` until D's sealed run shows the fields above; a green build or op-plan is not gameplay evidence.

## 7. Five highest-value deltas (for A task-34 / D validation)

1. **Hold/fire is a team-order problem, not a scripted-destination problem:** use `team_set_order_position(1791) + mordr_hold(0)`, add `mordr_hold_fire(12)` or `mordr_fire_at_will(13)` and `mordr_use_ranged_weapons(16)`, reissued on the native ~5 s cadence. Per-agent `agent_set_scripted_destination` (1730) queues/freezes and breaks formation; use WSE2 `agent_set_scripted_destination_no_attack` (1748) only for move-without-attack, then `agent_clear_scripted_mode` (1735) + `agent_force_rethink` (1732).
2. **WSE2 per-agent safeties are the missing "don't melee-charge" switch:** `agent_ai_set_can_weapon_switch(agent, 0)` (3343) preserves the ranged weapon; `agent_ai_set_simple_behavior(agent, aisb_hold=0, guarantee)` (3314) holds behavior (persists until `agent_force_rethink`); `agent_ai_set_can_aim` (3352) / `agent_ai_set_can_fight` (3344) as bounded toggles, not fire controls.
3. **Zombie speed without gear is a native op:** `agent_set_speed_modifier` (2093) percentage (100 default, 0..1000) or WSE2 `agent_set_time_speed_multiplier` (3335, fixed point) for a whole-agent shuffle; avoid global `mission_set_time_speed` and 0%; 60–80% with wave scaling, no equipment changes.
4. **Weapon/ammo control has hard pitfalls:** never spam `agent_set_wielded_item` (1747) on shields; native AI resets switch on target change; `agent_unequip_item` (1774) is invisible; fists count as melee, so guarantee ranged via behavior/orders, and use `agent_get_ammo` (1727)/`agent_set_ammo` (1776)/`agent_refill_ammo` (1728) + WSE2 `agent_set_item_slot_ammo` (3305) rather than forced switching.
5. **Wave visitors: rewrite/gate the table, then refill bodies:** `add_visitors_to_current_scene` (1265) for visitor entries; A's `faction_set_slot` (502) rewrite of invader wave slots 200..244 to slow 894, plus `set_spawn_position` (1970)/`spawn_agent` (1972) clone refill and round-aware gating; `set_bot_count` is a launcher/server command, not a native op — keep the 894 family and prove it via `waves.wave1.team1_classes` + defender deaths/positions telemetry.

## 8. Prototype

[`tools/city_behavior.py`](../tools/city_behavior.py) is a read-only, offline **plan builder/validator**: it emits the op tuples above (`hold_and_fire_plan`, `zombie_speed_plan`, `visitor_spawn_plan`) with enum/number validation (percent bounds, team/sub-class ranges, visitor counts, rejects scripted-destination plans) and never launches or touches the game. Tests: [`tests/test_city_behavior.py`](../tests/test_city_behavior.py). Use it to generate/review native blocks for A's module generator; runtime proof still belongs to D's sealed run.
