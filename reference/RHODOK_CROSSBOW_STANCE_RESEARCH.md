# Rhodok crossbow / formation stance research for survivors (task-87)

**Status: docs-only research. No game launch, no code/data/asset change, no acceptance claim.** This document answers what the Native "Rhodok crossbow" pattern actually is, what stand-ground/hold orders do, and which parts can be translated into survivor team-order/positioning rules for A's **task-84** (hold-ground guard-post stance, no chasing) and **task-85** (assisted focus-fire + special-swarm defense). Engine claims are marked with evidence; anything not established is marked **[unverified]**.

Observation date: **2026-10-24**. Base: `main` `b1a11a2`, worktree `agent/h-rhodok-stance`. Related: `reference/WARBAND_ENGINE_AI_RESEARCH.md` (task-61), `reference/SURVIVOR_CLASS_MATRIX.md` (task-67), `reference/CITY_MAP_DEFENSE_DESIGN.md` (task-63), `docs/COMBAT_BALANCE.md`, `reference/CITY_FIREARM_BALANCE_2026-10-24.md`.

---

## 0. The short answer

There is **no faction-specific Rhodok crossbow AI routine** in the Native module source. "Rhodok crossbow tactics" are an emergent combination of:

1. **Troop data** — crossbow + bolts + pavise shield + sidearm, high crossbow proficiency, no cavalry;
2. **Native tactic selection** — an archer-heavy army (>50% archers, <35% cavalry) picks `btactic_hold` (hold high ground);
3. **Player-style formation orders** — hold position, stand closer, stand ground, fire at will, charge;
4. **Community formation mods/play patterns** — class-scoped division orders, archers behind infantry, skirmishers/support formations.

For our survivors, the transferable part is **(2)+(3): stance orders and placement**, not a hidden AI behaviour. The hard parts — per-agent target selection, "assist this ally's target", true no-chase, friendly-fire-aware shooting, shield-wall behaviour — are **engine-blocked** in Warband (see §6–§8).

---

## 1. Sources actually read (with dates)

| # | Source | Type / date | What it establishes |
| --- | --- | --- | --- |
| S1 | [LilyModzStuff/warband_mod_source — `module_troops.py`](https://github.com/LilyModzStuff/warband_mod_source/blob/c9737d7793ccdb185d8d3caedda0da915104e405/source/module_troops.py), commit `c9737d7`, **2019-04-05** | Public Native-derived module source (Diplomacy lineage) | Rhodok crossbowman/trained/sharpshooter equipment and proficiencies (lines ~588–600) |
| S2 | Same repo — [`module_scripts.py`](https://github.com/LilyModzStuff/warband_mod_source/blob/c9737d7793ccdb185d8d3caedda0da915104e405/source/module_scripts.py) | Public Native-derived module source | Class percentages → tactic selection (31296–31329); hold tactic init (31377–31387); tactic apply → charge (32213–32268); `stand_ground` usage in siege belfry (≈35424); order labels "@Holding"/"@Standing" (35791/35812) |
| S3 | Same repo — `module_constants.py` | Public module source | `btactic_hold=1`, `follow_leader=2`, `charge=3`, `stand_ground=4` (lines 1884–1887); note `btactic_stand_ground` is defined but **not used by the battle-tactic scripts** |
| S4 | [Veehats/WarbandCoop headers](https://github.com/Veehats/WarbandCoop/blob/786de5c3735546cb29dd89e3cb6dceb6fff18113/header_operations.py), commit `786de5c`, observed **2026-10-24** | Public 1.174-era headers | `mordr_hold=0`, `stand_closer=7`, `spread_out=8`, `stand_ground=11`, `hold_fire=12`, `fire_at_will=13`, `charge=2`, `fall_back=6`, `retreat=14`; `team_give_order` 1790, `team_set_order_position` 1791, `agent_set_division` 1783, `agent_get_attack_action` 1763, `agent_set_look_target_agent` 1713 |
| S5 | [Mount & Blade Wiki — Kingdom of Rhodoks Tactics](https://mountandblade.fandom.com/wiki/Kingdom_of_Rhodoks_Tactics) (Fandom API, observed **2026-10-24**; Wayback capture **2025-09-09**) | Community wiki | Rhodok battle/siege tactics: crossbows + pavise shields, ranged on hills, infantry a few paces in front of archers, hold position, stand closer, phalanx, create groups, firing line |
| S6 | [TaleWorlds forums — "What is 'Stand ground' command used for?"](https://web.archive.org/web/20231017144159/https://forums.taleworlds.com/index.php?threads/what-is-stand-ground-command-used-for.229101/), thread started **2012-05-09**, Wayback **2023-10-17** | Community discussion (incl. Caba'drin, a well-known Warband modder) | Hold position = move to designated spot, form up, hold, still face/engage; stand ground = halt in place, no reform, then behave like hold; both still allow local melee engagement; no hard "no chase" guarantee |
| S7 | [cvlc/tgsmod `formAI_constants.py`](https://github.com/cvlc/tgsmod/blob/4e2fb81b814e2dc420430a679f8deeafcd63b40b/formAI_constants.py), commit `4e2fb81`, **2015-12-13** (lineage: Motomataru FormAI, nexus 2475) | Community formation-AI module source | `AI_long_range=13000` (130 m), `AI_firing_distance=6500` (65 m), `AI_charge_distance=2000` (20 m), `Hold_Point=100` ("archer hold if outnumbered") |
| S8 | Same repo — `formations_constants.py`, `formations_scripts.py`, `formAI_scripts.py` | Community formation AI | Division types incl. `sdt_skirmisher=4`, `sdt_support=6`, `sdt_bodyguard=7` (lines 132–140); class-scoped `grc_*` orders/positions; `team_set_slot` + `team_give_order` hold/advance/charge; per-class placement and fire-order handling |
| S9 | [Realistic Battle Mod — Battle AI manual](https://fellow93.github.io/RealisticBattleProject/features/ai/) (observed **2026-10-24**; repo [Fellow93/RealisticBattleProject](https://github.com/Fellow93/RealisticBattleProject), commit `7f9069b`, **2026-10-06**) | Bannerlord community mod manual/source | Archers skirmish and pull back behind infantry; infantry screen; shield wall under fire; archers sidearm ≈2.5 m; target priority; battle-joined at 70–95 m; AI behaviour log |
| S10 | [TacticalWarfareAI README](https://github.com/davrodwconnections/TacticalWarfareAI) (pushed **2026-08-13**; observed 2026-10-24) | Bannerlord community mod (Harmony, v2.4.1) | Formation reactions, target prioritisation, archers fall back behind infantry; lessons about target overrides silencing archers and friendly-lane shooting |
| S11 | Project evidence: `docs/COMBAT_BALANCE.md`, `reference/CITY_FIREARM_BALANCE_2026-10-24.md`, `reference/CITY_MAP_DEFENSE_DESIGN.md`, task-61/67 docs, task-83 task text | Our own docs | Firearms treated as crossbow-type weapons; crossbow item stats; guard posts/anchors; engine limits (no target setter; division adoption unproven; no per-agent armour/shield change) |

**Inaccessible/recorded:** GameFAQs thread on stand ground vs hold (HTTP 403); live TaleWorlds pages 403 (Wayback used). Fandom page text was retrieved via its API because the normal page is Cloudflare-gated.

---

## 2. What the Native "Rhodok crossbow" pattern actually is

### 2.1 Troop data (S1)

| Troop | Equipment | Crossbow proficiency | Shield skill | Other |
| --- | --- | ---: | ---: | --- |
| Rhodok Crossbowman | `itm_crossbow`, `itm_bolts`, `itm_tab_shield_pavise_a`, sword/club | all weapon proficiencies 85 (`wp(85)`) | 1 | athletics 2 |
| Rhodok Trained Crossbowman | `itm_crossbow`, `itm_bolts`, pavise, sidearm | 105 | 2 | athletics 3 |
| Rhodok Sharpshooter | `itm_sniper_crossbow`, `itm_steel_bolts`, `itm_tab_shield_pavise_c`, sword/pick/hammer, mail | 140 | 4 | athletics 6 |

This is the "crossbow + shield + sidearm, no cavalry" identity. Crossbows are slow to reload but high damage (community wiki: 40–70 per bolt, S5). Native has no separate "crossbow AI"; the weapon's action behaviour and proficiency do the work.

### 2.2 Native tactic selection is composition-based, not faction-based (S2, S3)

In `script_select_battle_tactic_aux`:

- the only faction-specific exclusion is **Khergits** (`neq fac_kingdom_3`, line ~31321) — Rhodoks are **not** a special case;
- if the team has **>50% archers and <35% cavalry**, it selects `btactic_hold` (lines ~31324–31326);
- otherwise it usually selects `btactic_follow_leader` (line ~31329), with a random gate.

`script_battle_tactic_init_aux` for `btactic_hold` (lines ~31377–31387):

- finds high ground around the leader;
- issues `team_give_order(team, grc_everyone, mordr_hold)` and `team_set_order_position(team, grc_everyone, pos)`;
- issues `team_give_order(team, grc_archers, mordr_advance)` **twice** (archers get a separate forward treatment).

`script_battle_tactic_apply_aux` (lines ~32213–32268):

- while holding: if the closest enemy is **<10 m** or the average distance is **<40 m**, switch the whole team to `mordr_charge`;
- `btactic_follow_leader`: hold at 23 m ahead of the leader toward the enemy; charge when enemy <50 m after 30 s;
- hard forced charge at **300 s** for any non-charge tactic.

`btactic_stand_ground=4` exists in the constants (S3) but the battle-tactic selection/apply code does **not** use it; `mordr_stand_ground` appears in the source in a siege **belfry positioning** script (S2 ≈35424), not in field-battle tactics.

**Conclusion:** "Rhodok crossbow stance" = archer-heavy composition → **hold high ground + archers advance + charge when the enemy closes** (or after 5 min). It is a *scripted tactic pattern*, not a crossbow-specific AI. Our City mod can reproduce the **orders/geometry** but not a hidden behaviour.

### 2.3 Crossbow-type firearms in our build (S11)

Our survivor firearms are treated as **crossbow-type weapons** by the engine (`tools/firearm_balance.py` docstring; task-83). That means the same AI reload/shoot/stand-still behaviour applies to the M16A2/MP5/Remington/Cynergy loadouts. Task-83 is the A-lane owner for fixing the resulting charge/stand-still and proficiency issues; this doc does not re-derive that work.

**Shield caveat:** our survivor clones carry **no shield item** (task-46 loadout; E's original-behavior review), so the Rhodok pavise/screen cannot be reproduced without a separate owner/G asset/data decision. Do not describe survivor squads as a shield wall.

---

## 3. Stand ground vs hold position — engine semantics

### 3.1 Order ids and labels (S2, S4)

| Order | Id | Native UI label | Native usage observed in source |
| --- | ---: | --- | --- |
| `mordr_hold` | 0 | "@Holding" | Battle tactic hold: `team_set_order_position` + hold (field battles); sieges: defenders hold positions |
| `mordr_stand_ground` | 11 | "@Standing" | Siege belfry crews (`team_give_order(..., mordr_stand_ground)`); not used by field-battle tactic scripts |
| `mordr_stand_closer` | 7 | "@Standing Closer" | Formation spacing; used by Native siege/formation scripts |
| `mordr_spread_out` | 8 | "@Spreading Out" | Formation spacing |
| `mordr_charge` | 2 | "@Charging" | Tactic flip when enemy closes / 5-min forced charge |
| `mordr_advance` | 5 | "@Advancing" | Hold-tactic archer advance |
| `mordr_fall_back` | 6 | "@Falling Back" | Formation fallback |
| `mordr_retreat` | 14 | (retreat) | Field-leaving; never for zombies |

### 3.2 Community-consensus semantics (S6)

From the 2012 TaleWorlds thread (multiple posters, incl. Caba'drin):

- **Hold position**: troops **move to the indicated spot**, form up around it, then hold. They still turn to face and engage enemies that reach them.
- **Stand ground**: essentially **"HALT!"** — troops stop where they are, do not reform on a spot, then behave as they would under hold (including local melee engagement). Several posters note it is useful to stop scattering/chasing and to set a firing line; another calls it "defend this position" vs hold's "defend my position".
- **Neither order is a hard leash**: nearby enemies can still pull individuals into melee; stand ground does not regroup strays.

**Engine-verification status:** the order ids/labels and native usage are source-grounded. The exact engine implementation of stand ground vs hold is community-described, not officially documented — **[unverified]** beyond the observed usage above.

### 3.3 What this means for task-84 ("campers", no chasing)

- The reliable mechanism is **`team_set_order_position` + `mordr_hold` re-issued on the 5 s cadence** to the post/division, exactly as the current City trigger does.
- `mordr_stand_ground` is a **halt corrective**, not a regrouping tool: it stops a unit where it is, so use it only after units are already near the post, or accept that strays stay stray. To pull strays back, use a hold order with the post position / fallback order.
- **No-chase cannot be guaranteed by orders alone.** Hold/stand-ground still allow local melee engagement; the engine may pursue. Treat "no chase" as a **measured outcome** (positions vs post, attack action, movement) and tag it **B-unproven/B-engine**, not as a property of the order.
- Do **not** use per-agent `agent_set_scripted_destination` to enforce a leash; task-61/63 already established that this breaks formations and is an anti-pattern.

---

## 4. Ranged screen (melee in front, crossbows behind)

### 4.1 Community Rhodok pattern (S5)

The wiki's Rhodok advice is explicit and matches our desired layout:

- station ranged units on the nearest hill;
- place infantry **a few paces in front of the archers** to block cavalry/infantry;
- crossbowmen are effective against slowly approaching infantry;
- create **groups** (party screen) so shield-carrying crossbowmen stand in front of sharpshooters;
- use **hold position** and **stand closer** to form the firing line/phalanx;
- keep some infantry with the archers so they are not defenceless.

This is a player-tactic description, not engine code, but it is a direct community precedent for **screen + ranged behind + hold stance**.

### 4.2 Community formation AI (S7, S8)

FormAI implements the class/formation layer that Native lacks:

- division types include `sdt_infantry`, `sdt_archer`, `sdt_cavalry`, `sdt_polearm`, `sdt_skirmisher`, **`sdt_support`**, **`sdt_bodyguard`** (S8) — a dedicated "support" division concept closest to our "assist melee" idea;
- it issues class-scoped orders/positions (`team_give_order`/`team_set_order_position` on `grc_*`) and holds/sets formation destinations;
- it uses AI ranges `130 m` (long), `65 m` (firing), `20 m` (charge), with a "Hold_Point" rule of "archer hold if outnumbered" (S7);
- it handles per-division fire orders and formation placement (archers/skirmishers/infantry).

All of this is **formation-level** (class/division orders), not per-agent target selection.

### 4.3 Bannerlord community design lessons (S9, S10)

RBM and TacticalWarfareAI both implement the screen successfully — but through formation AI/Harmony hooks Warband does not expose:

- RBM: "main infantry advances; **archers stand just behind it and shoot over it**"; archers skirmish and **pull back behind infantry**; shield wall under missile fire; when melee closes, archers switch to sidearms at ≈2.5 m; target priority is engine/AI logic.
- TacticalWarfareAI: "archers take nearby high ground and **fall back behind their own infantry** when melee closes"; "targets are chosen, not stumbled into"; but its README documents that **target overrides silenced archers** and that friendly-lane/friendly fire handling required iteration.

**Transfer to Warband:** we can only implement the **placement + hold/fire orders** half. Friendly-fire/line-of-fire avoidance and explicit target choice are **B-engine** (§7).

---

## 5. Assist melee / focus fire

### 5.1 What exists in the two engines

| Capability | Warband | Bannerlord |
| --- | --- | --- |
| Per-agent target setter | **None**. `agent_ai_get_look_target`/`move_target`/`behavior_target` (2080–2082) and cached enemies (2670/2671, availability unverified) are **read-only**; `agent_set_look_target_agent` (1713) only sets look direction, combat effect **[unverified]** | Engine target selection; mods override via Harmony (RBM/TacticalWarfare) |
| Formation-level target | Native/FormAI can set **order positions** toward an enemy battlegroup (FormAI `script_battlegroup_get_attack_destination`), but this is movement, not per-agent shooting | `FormationAI` target/`BehaviorComponent` system |
| "Shoot the ally's engaged enemy" | **No API**; engine decides | Mods implement target priority via hooks; not a base-game command |
| Friendly-fire-aware shooting | Engine-internal, not exposed; community evidence **[unverified]** | RBM/TacticalWarfare implement lanes/arcs; documented failure modes |

### 5.2 What is feasible in our mod

- **Positioning/lanes**: place ranged divisions so their field of fire covers the melee frontage **without standing directly behind the melee line** (offset lanes). This reduces friendly-fire ambiguity even though we cannot command it.
- **Fire discipline**: `mordr_fire_at_will` + `mordr_use_ranged_weapons` + `agent_ai_set_can_weapon_switch(0)` while ammo > 0 (current City behavior). Do **not** use `mordr_hold_fire` as a default (task-45 regression suppressed shooting).
- **Observation**: C can read `agent_get_attack_action` (1763) and weapon/ammo state; target attribution is not available. `agent_ai_get_behavior_target` is a readback but currently not read (needs msfiles declaration + capability flag per task-61/67).
- **Assist as responsibility**: a ranged class can be *positioned* to support the melee frontage, and measured by damage/kills near the melee; it cannot be told to "shoot the same target" without a target setter.

**Verdict:** "assist melee/focus fire" is **B-engine** as a targeting feature. A's task-85 can implement **lane geometry + posture + telemetry**, not true focus fire. Any claim that survivors "focus the ally's target" must be reported as emergent/unverified.

---

## 6. Post defense and no-chase

### 6.1 Geometry and orders

- Posts 2/3/4 and anchor E0 are the current guard geometry (task-63); current City behavior adopts team-0 bots into divisions 5/6/7 and holds rear entries `(0,1,0)` every 5 s (`tools/city_defense.py`).
- Recommended task-84 stance mapping:
  - **center/line class** → hold post 2;
  - **flank class** → hold post 3 (lateral leash by position, not scripted destination);
  - **overwatch/ranged class** → hold behind center/at post 4 side;
  - **close reserve** → hold E0/frontage of anchor; commit only when an enemy is inside the defence radius.
- Re-issue `team_set_order_position` + `mordr_hold` each cycle; add `mordr_stand_closer` after the hold settles for a tighter line; use `mordr_stand_ground` only as a halt corrective for a unit that is already near its post.
- Fallback/regroup: `mordr_fall_back` to E0/entry 0, then re-hold; **never** `mordr_retreat` for zombies; survivors fall back, not rout.

### 6.2 What cannot be enforced

- **No hard defence radius**: no op sets a per-agent leash; hold/stand-ground still allow local engagement and engine pursuit (S6; task-61). The only honest levers are placement, re-issued orders, fallback, and telemetry.
- **Division adoption/order reach** is still unproven (task-61 §4.4; task-67/84 status): if bots are not actually in 5/6/7 or orders do not reach them, the stance is a label. The decisive test is the division round-trip + order-observability experiment from task-61/67.
- **Shield/pavise screen** is unavailable (no shield item; §2.3) and shield-wall behaviour is engine AI, not an order.

---

## 7. Special swarm defense

### 7.1 What the community/engine offers

- **No target priority API in Warband.** Specials (Tank/strong/fast) cannot be designated; melee AI swarms whatever is nearest; ranged AI chooses internally. FormAI can direct a *formation* toward an enemy battlegroup, but not individual shooters at a special.
- Bannerlord mods implement "special/threat priority" through engine/Harmony hooks (RBM/TacticalWarfare target-priority features), which are not available here.
- Actual swarm behaviour is therefore **emergent**: melee units near the special engage it; ranged units fire at whatever the engine selects. This matches task-67's conclusion that "priority is responsibility, not enforcement".

### 7.2 Feasible defensive design

- **Funnel geometry**: put specials on the approach that the melee screen and post line cover; keep ranged lanes offset so they can fire into the approach (not through allies).
- **Melee screen commitment**: hold the melee class at the defence radius so a special entering the radius is met by multiple melee agents; the engine's proximity targeting will produce a swarm.
- **Ranged fire-at-will**: keep crossbows firing while ammo remains; avoid hold-fire.
- **Capability experiments (not baseline)**: WSE2 `agent_set_can_multihit` (3353), `agent_set_can_piercing` (3359), `agent_set_crush_through` (3355) are per-agent, server-side, and could improve anti-swarm/anti-shield outcomes; they do **not** select targets. Separate build + D evidence only.
- **Telemetry limit**: class × victim-troop kill attribution is not feasible now (task-67 D/C), so "ranged prioritised the special" cannot be proven with current data; only aggregate kills/positions/attack action.

---

## 8. Translation matrix — feasible vs blocked

| Survivor rule | Warband mechanism | Feasibility | Notes |
| --- | --- | --- | --- |
| Camp at posts, no wandering | `team_set_order_position` + `mordr_hold` per division, re-issued 5 s; anchor/offsets | **F-now** order layer | Division adoption/order reach **B-unproven**; no hard leash |
| Halt a straying unit | `mordr_stand_ground` (11) | **F-now** (corrective) | Stops in place, does not regroup; community semantics |
| Tighten the line | `mordr_stand_closer` (7), `mordr_spread_out` (8) | **F-now** | Formation spacing, engine-executed |
| Ranged behind melee screen | Class→division mapping + hold positions at offsets | **F-build** (placement) | No explicit screen/friendly-fire op; adoption unproven |
| Fire discipline for crossbows | `mordr_fire_at_will`, `mordr_use_ranged_weapons`, `agent_ai_set_can_weapon_switch(0)`; ammo gate | **F-now** | Do not use hold_fire as default (task-45) |
| Faster/earlier shooting (crossbow-type) | Proficiency/accuracy build changes (task-83), `agent_set_accuracy_modifier` 2092 | **F-build/F-now** | 2092 stacks/overrides the auto-accuracy profile; A task-83 owns |
| Assist melee / focus fire | No target setter; lanes/position/fire-at-will only | **B-engine** for targeting; **F-build** lanes | Report as responsibility/emergent, not enforced |
| Special-swarm priority | No target priority; proximity swarm + funnel geometry | **B-engine** for priority; **F-build** geometry | WSE2 multihit/piercing experiments only |
| No chasing outside radius | No leash op; hold is advisory | **B-engine/B-unproven** | Measure positions/attack action; never scripted destinations |
| Post fallback/regroup | `mordr_fall_back` to E0 + re-hold; mode global | **F-build**, order reach **B-unproven** | Never `mordr_retreat`; no rout |
| Shields/pavise screen | No shield item on clones; no shield-wall order | **B-engine** (behaviour), **F-build** (data if owner approves) | Do not claim Rhodok shield wall |
| Crossbow reload/stand-still | Engine weapon AI; task-83 fix path | **B-engine** (behaviour) | A task-83; measure time-to-first-shot/reload |

---

## 9. What to feed A's task-84 and task-85

### task-84 — hold-ground guard-post stance, no chasing

1. Keep **hold + order position** as the primary stance; re-issue per division every 5 s; use `stand_closer` after settle; `stand_ground` only as a halt corrective.
2. Implement the **screen geometry** from Rhodok pattern: melee division forward of ranged, ranged offset into firing lanes, close reserve at E0. This is a placement change, not new AI.
3. **Do not** promise no-chase from orders. Record it as an outcome to measure (distance from post, attack action, movement) and escalate to D; tag B-engine/B-unproven.
4. Keep the existing ammo gate/fire-at-will; no hold-fire default.
5. If the pavise/shield idea is wanted, it is a **data/owner/G decision**, not a stance trick.

### task-85 — assisted focus-fire + special swarm

1. **Assist**: implement lanes/positioning so ranged covers melee frontage; measure whether ranged fire coincides with melee engagement (attack action, weapon mode, positions). There is no target setter — do not claim focus fire.
2. **Special swarm**: geometry/funnel + melee hold at radius + fire-at-will; the swarm is emergent. Optionally test WSE2 multihit/piercing/crush-through in separate builds; no target priority claim.
3. **Telemetry asks (C)**: `agent_get_attack_action`, weapon/ammo, per-class presence, positions vs post, fallback/regroup events, `agent_is_routed` as **unknown** (no verified getter); no class × victim attribution (not feasible now).
4. **D validation**: A/B stance runs (hold vs hold+stand_closer vs stand_ground corrective), screen-offset variants, special-near-post scenario, crossbow reload/time-to-first-shot; no acceptance before sealed evidence.

---

## 10. Unverified / limits

1. **No faction-specific Rhodok AI**: confirmed absent from the public Native-derived source; exact 1.174 Native may differ only by data, not by a hidden routine **[unverified beyond source]**.
2. **Stand ground vs hold semantics** rest on community consensus (2012 thread) plus observed native usage; engine code is not available.
3. **Hold/stand ground do not guarantee no-chase**; local melee engagement is expected (community + engine behaviour).
4. **Division adoption/order reach** is unproven in our runtime (task-61/67); the stance may be a label until the round-trip passes.
5. **No target setter/priority**; assist/focus/special priority are responsibilities, not enforceable.
6. **Friendly-fire avoidance** by AI is engine-internal and unverified in Warband; RBM/TacticalWarfare show this is a real failure mode in Bannerlord, so do not assume Warband handles it.
7. **Crossbow-type firearms**: engine behaviour/reload and task-83 fixes remain A-lane and runtime-unverified.
8. **Shields**: survivor clones carry none; Rhodok pavise tactics are not reproducible without a data/asset decision.
9. **Source lineage**: S1/S2 are a 2019 Native-derived mod source (Diplomacy lineage); line-level facts are source-attributed, not engine guarantees.
10. **Fandom wiki** is community content, not official; retrieved via API because the page is Cloudflare-gated.

---

## 11. Handoff

- This is research/handoff only: no build, trigger, scene, loadout or asset change; no acceptance claim.
- **A (task-84/85)**: use §8/§9 as the implementation boundary; the only enforceable tools are class/division orders, positions, spacing, fire/weapon orders and per-agent WSE2 safeties.
- **C**: observe stance/assist outcomes with attack action, weapon/ammo, positions, per-class presence, fallback/regroup; keep target/rout attribution honest.
- **D**: run the A/B stance and screen-offset comparisons from §9; no visual/behaviour acceptance before sealed evidence.
- Cross-review welcome from A/C/D; findings should be appended here rather than silently assumed.

*End of research document.*
