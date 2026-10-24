# ZOMBIEEE survivor class matrix — commando, sniper, scout, lumberjack (task-67)

**Status: docs-only design proposal. No game launch; no build or data change; no acceptance claim.** This document turns the Warband/Bannerlord AI research into a class matrix for the four AI survivor classes already present in the City build (troop ordinals 981–984). Everything labelled **F-now / F-build / B-engine / B-unproven** is a feasibility claim about the current modding surface, not an observed behaviour. Runtime truth still belongs to D's sealed runs.

Observation date: **2026-10-24**. Base: `main` `090061e`, worktree `agent/h-survivor-matrix`. Related: [`WARBAND_ENGINE_AI_RESEARCH.md`](WARBAND_ENGINE_AI_RESEARCH.md) (task-61), [`BANNERLORD_AI_ENGINE_RESEARCH.md`](BANNERLORD_AI_ENGINE_RESEARCH.md) (task-56), [`CITY_MAP_DEFENSE_DESIGN.md`](CITY_MAP_DEFENSE_DESIGN.md) (task-63), [`../docs/COMBAT_BALANCE.md`](../docs/COMBAT_BALANCE.md), [`ORIGINAL_0.4_BEHAVIOR.md`](ORIGINAL_0.4_BEHAVIOR.md).

---

## 0. Feasibility vocabulary

| Tag | Meaning |
| --- | --- |
| **F-now** | Implementable with the existing build surface (module triggers + native ops + WSE2 ops already used by the project), no engine feature is missing. Runtime still unverified until D seals it. |
| **F-build** | Requires a build/data change (new clone troops, loadout/tier table, receipt/tests, owner approval) but no engine blocker. |
| **B-engine** | Blocked by the engine/modding surface: no op exists for it, or the only op is read-only/unrelated (e.g. target selection, per-agent armour change). Do not design around it as if available. |
| **B-unproven** | Depends on a mechanism that is plausible but not proven in our runtime: order addressability/division adoption (task-61 §4.4), WSE2 binding availability, or a trigger/event not confirmed on the pinned build. |

**Engine constraints inherited from task-61** (do not redesign around them):

1. No native target setter. `agent_ai_get_*_target` / cached-enemy ops are read-only; `agent_set_look_target_agent` (1713) only sets look direction, not combat targeting. **Target priority is B-engine**; class "priority" is a responsibility/positioning design, not an enforceable policy.
2. `agent_get_group` is **not** a division; orders address class/division 0–9. Division adoption (`agent_set_division` 5/6/7) is **B-unproven** until the division round-trip experiment passes (task-61 §10).
3. Range-keeping/kiting per agent is **B-engine**; preferred range bands can only be expressed as **placement + hold/fire discipline** (F-now/F-build), not as per-agent distance logic.
4. No per-agent armour/inventory change. `agent_set_wielded_item` (1747) only swaps already-carried weapons; `agent_unequip_item` (1774) removes; there is no "equip armour" op. **Mid-mission equipment upgrade is B-engine**; upgrade path must be respawn/tier data (F-build).
5. Morale/rout: the City 25-trigger chain has no Native courage script (static), but the engine may still route agents (task-61 caveat). Class fallback is a **movement order/mode**, not a courage parameter.

---

## 1. Evidence base for the matrix

| Evidence | What it fixes |
| --- | --- |
| Original 0.4 playable classes 875–878 (E's static review): Commando, Sniper, Lumberjack, Scout; firearms prof **120/200/100/120**, shield skill 2, no shield item in AI clones | class skill identity and relative accuracy |
| AI clone loadouts (task-46 / `docs/COMBAT_BALANCE.md`): Commando M16A2 + Beretta + Bowie; Sniper Remington 700 + Beretta + Bowie; Scout MP5 + SW5904 + Bowie; Lumberjack Cynergy shotgun + Bowie; 8 ammo packs each (double), one melee | weapons and ammo reality |
| Automatic-firearm accuracy profile: auto weapons +8..10 accuracy; single-shot unchanged | fire-behaviour asymmetry between auto and precision classes |
| Current City behaviour (`tools/city_defense.py`): 5 s trigger adopts team-0 bots into divisions 5/6/7, rear hold entries `(0,1,0)`, per-agent ammo gate (`agent_get_ammo`, `agent_ai_set_can_weapon_switch`), WSE2 `agent_ai_set_simple_behavior(hold, 6 s)`, no scripted destination, spawn_agent refill clones 981–984, survivor count grows +1 per completed round (base 8, cap 12) | what is already implemented and reusable |
| City geometry (task-63): anchor E0 (167.718, 184.445), guard posts 2/3/4 at 15.8–22.3 units forward, zombie approaches from three southern clusters ~57–71 units from the forward posts, no north/east/west entries | range-band and slot geometry |
| Enemy roster (E's review): wave natives 894–901 (Zombie/Tough/Fast/Cop/Steroid/Mutated/Witchy), generic fill 902–912 (weak Invaders, Tank/strong, mounted Tank 908, Horde, ranged 911/912); current weak-wave-1 profile restricts generic to 894 | special-target taxonomy and profile dependency |
| Task-56/61 research: formation classes + ranged-behind/melee-screen; one intent owner → orders → engine; no behaviour tree; no target setter | design pattern and hard limits |

**Class → troop ordinal mapping** (from `tools/patch_defenders.py` / `tools/bot_loadouts.py` zip order and `docs/DIAGNOSTICS.md`):

| Ordinal | Clone | Original class |
| ---: | --- | --- |
| 981 | `trp_zdr_commando_bot` | Commando (875) |
| 982 | `trp_zdr_sniper_bot` | Sniper (876) |
| 983 | `trp_zdr_scout_bot` | Scout (878) |
| 984 | `trp_zdr_lumberjack_bot` | Lumberjack (877) |

This table is the contract A must use (`agent_get_troop_id` 1718 → class branch); C must use the same map for class-aware telemetry.

---

## 2. Master class matrix

Values are **design targets**, not observed values. Range bands are engagement distances from the survivor anchor/element, expressed in scene units (the project's "metres" convention).

| | **Commando** (981) | **Sniper** (982) | **Scout** (983) | **Lumberjack** (984) |
| --- | --- | --- | --- | --- |
| **Role** | Line/screen anchor; main volume of fire | Precision overwatch; shield/strong-breaker | Mobile flank screen; anti-fast/ranged harassment | Close reserve; last stand at the anchor |
| **Preferred band** | 18–35 | 35–60 | 10–22 | 0–10 |
| **Weapon** | M16A2 auto | Remington 700 single | MP5 auto | Cynergy shotgun |
| **Fire behavior** | fire-at-will, burst/auto as engine allows, keep ranged weapon while ammo | fire-at-will at long band, single deliberate shots; do not waste on out-of-band targets (proposal) | fire-at-will, shortest bursts; reposition between bursts | fire-at-will only when close; melee bowie allowed at ammo 0 or <10 units |
| **Movement** | baseline 100% | 85% (deliberate, no chase) | 115% (fastest) | 95% |
| **Speed feasibility note** | team-0 per-class `agent_set_speed_modifier` (2093) is F-now; not D-observable until re-sealed. Native wave-speed loop applies to **team 1 only**, so no conflict. | same | same | same |
| **Build/stats** | firearms 120; medium armour | firearms 200; light/medium; no charge | firearms 120; light armour | firearms 100; heavier clothing; close combat |
| **Formation slot** | division 5 — centre screen (post 2 / E0 frontage) | division 7 — rear overwatch (E0 rear edge / post 4 side) | division 6 — flank screen (post 3 / lateral leash) | reserve — division 5 rear element (baseline); division 8 is **B-unproven/blocked** (in the 0–9 space but adoption/orders unproven); never first line |
| **Target responsibility** | Fast/Tough/Witchy and any special that closes | Tank/strong/shielded/mounted first, then Witchy/Steroid | Fast 896, ranged 911/912, flanking specials | mass/weak at close range; bodyguard the anchor |
| **Fallback trigger** | ammo 0 **and** local threat high; HP < 30% | enemies < 15 units or screen collapsed; HP < 40% | first to fall back: local ratio > 1.5, HP < 50% | last to fall back; only at anchor pressure or ammo 0 |
| **Desperation** | hold and fire to last magazine; melee only at ammo 0 | fall back, do not melee-charge | disengage and re-form at E0 | close to melee at <10 or ammo 0 |
| **Upgrade path** | T1 auto rifle (AK47/FN SCAR-L), T2 M249 | T1 Mk12 SPR, T2 M82 | T1 MP5K/MP7, T2 P90 | T1 armour/shells, T2 armour + shotgun retained |
| **Feasibility** | loadout/role F-now; per-class division B-unproven; target priority B-engine | same; precise range discipline B-engine as dynamic, F-now as placement | speed F-now; flank leash B-unproven | close melee gate F-now experiment; sustain B-engine |

**Reading the table:** the columns are *intent*. Only the rows tagged F-now/F-build in §8 are implementable today; target responsibility, dynamic range keeping and per-agent fire-mode selection remain design goals that the engine cannot enforce.

---

## 3. Range-band model (placement, not targeting)

### 3.1 Geometry grounding

Task-63 decodes the City map: survivor anchor at ≈(167.7, 184.4); forward posts 2/3/4 at 15.8–22.3 units; zombie clusters enter at ≈(107,129), (157,113), (203,116), i.e. **57–71 units from the forward posts** and ~72–83 from the anchor. This gives a natural engagement ladder:

| Band | Distance from anchor | Class that owns it | What it means |
| --- | ---: | --- | --- |
| Contact | 0–10 | Lumberjack | shotgun/melee; reserve commits only here |
| Close | 10–22 | Scout | flank screen; MP5 bursts; disengage if pressured |
| Mid | 18–35 | Commando | main line volume of fire |
| Long | 35–60 | Sniper | first shots; shield/strong priority |
| Beyond | >60 | none (hold fire) | do not advance; let them come |

The bands overlap deliberately (real fights compress distances). The point is **who is allowed to be where**, not a per-agent distance controller.

### 3.2 Feasibility

- **F-now:** anchor offsets and hold positions (rear entries 0/1, forward posts 2/3/4 only under the approved staged line) produce the intended distances as long as survivors hold. Class-specific anchor offsets can be encoded as position math in the same 5 s trigger.
- **B-engine:** dynamic per-agent range keeping (kiting/retreat-to-band) does not exist. Any claim that a sniper "keeps 40 m" is false unless it is stationary/holding; the engine will close if it decides to.
- **B-unproven:** whether per-division hold orders actually keep each class on its offset (division adoption + addressability, task-61).

---

## 4. Fire behaviour matrix

| Class | Weapon class | Native fire control | Proposed discipline | Feasibility |
| --- | --- | --- | --- | --- |
| Commando | automatic rifle | engine auto/semi by weapon; team `mordr_fire_at_will` + `mordr_use_ranged_weapons`; `agent_ai_set_can_weapon_switch(0)` while ammo > 0 | fire at will, keep rifle, never melee-charge | **F-now** (already implemented for all defenders; per-class split B-unproven) |
| Sniper | bolt-action | same order set; accuracy profile unchanged (single-shot) | hold fire until target is in long band? — **cannot express "until band"**; use fire-at-will, rely on position/LOS | **F-now as position; B-engine as conditional fire** |
| Scout | SMG | same; auto accuracy buff applies | fire at will, short exposure, keep SMG | **F-now** (loadout/position); class-specific cadence B-engine |
| Lumberjack | shotgun | same; melee allowed at ammo 0 today | hold fire until close (not expressible per class without division orders); melee at <10 or ammo 0 | **F-now experiment** (per-agent weapon-switch gate); **B-unproven** if tied to division orders |

**Do not repeat the task-45 regression:** issuing `mordr_hold_fire` suppressed all shooting. The default order set must stay `mordr_hold` + `mordr_fire_at_will` + `mordr_use_ranged_weapons`; class fire discipline can only differ through **division-scoped** orders (needs adoption) or per-agent WSE2 toggles.

**Per-agent toggles already available (WSE2):** `agent_ai_set_can_weapon_switch` 3343, `agent_ai_set_can_fight` 3344, `agent_ai_set_can_aim` 3352, `agent_ai_set_simple_behavior` 3314; native `agent_set_accuracy_modifier` 2092. None of them selects a target or enforces a range.

**Accuracy interaction (A, 2026-10-24):** native `agent_set_accuracy_modifier` (2092) **stacks with or overrides** the build-level automatic-firearm accuracy profile (task-22 `+8..10` points). Treat per-class accuracy as an interaction that must be measured, not as an independent second profile; D/C must record both the item-table accuracy and the runtime modifier.

**Optional experiments (not baseline):** WSE2 `agent_set_can_multihit` 3353 (shotgun vs horde), `agent_set_can_piercing` 3359 (sniper vs line), `agent_set_crush_through` 3355 (shield pressure). All are per-agent mutations, server-side, and need separate builds + D evidence; do not bundle them into the class matrix baseline.

---

## 5. Formation slots and defensive posture

### 5.1 Slot proposal

| Class | Division | Position | Notes |
| --- | ---: | --- | --- |
| Commando | 5 | centre screen (post 2 when the staged forward line is approved; otherwise E0 frontage) | main line; keeps the centre pinch |
| Scout | 6 | east/flank screen (post 3), leash ≤ 12 units from E1 | may reposition laterally; never chase beyond leash |
| Sniper | 7 | rear overwatch at E0 rear edge / post 4 side with LOS | first to fall back; no forward commitment |
| Lumberjack | 5 rear element or 8 | behind E0 / between anchor and centre | last line; if division 8 is used it is **B-unproven** (native uses 8 as a reserved division in field battles, task-61) |

**Current build reality:** the default is rear hold `(0,1,0)` with all team-0 bots adopted round-robin into 5/6/7 (no class mapping); forward posts are only used with `--defensive-line forward` after the task-63 staged approval. Class→division mapping is therefore **F-build**, and its effect is **B-unproven** until task-61's division round-trip proves adoption/addressability.

### 5.2 Threat posture (task-62 alignment)

- All classes use the **anchor-and-screen** model: hold, do not chase; Scout is the only class allowed a bounded lateral probe (leash), and it still returns to E1.
- Threat assessment uses **all three southern approach axes** (A/B/C from task-63), not local zombie count only. Center pinch (post 2) is the commando's main responsibility; flanks belong to scout.
- If encirclement pressure rises (two axes active, or a class element below 50% strength), the mode machine falls back to E0 rather than feeding units forward. This is a **mode/threshold design**, F-build; the per-agent decision is engine-side.
- No class is allowed to charge. The only forward movement is a bounded scout probe explicitly ordered by the mode machine, and it must be reversible with a `mordr_fall_back` to E0.

---

## 6. Special-zombie priority (responsibility, not targeting)

**B-engine:** there is no target setter. Priority below is a *responsibility assignment* to be measured via kill attribution and positioning, not an enforceable target list.

### 6.1 Threat tiers

| Tier | Enemies (ordinals) | Threat | Primary class | Secondary |
| --- | --- | --- | --- | --- |
| P0 | 907/908/909/910 Tank/strong/mounted, 895 Tough (shield), 898 Steroid, 900 Witchy | shield/HP/mounted pressure; breaks the line | Sniper (long band), Lumberjack at close | Commando volume fire |
| P1 | 896 Fast, 911/912 ranged Horde | flanks and chip damage; reaches the line first | Scout (screen/evade) | Commando |
| P2 | 894 Zombie, 899/901 Mutated, 902–906 weak Invaders | mass; attrites ammo | Commando | Lumberjack |

**Profile dependency:** the current default restricts generic fill to weak 894 and uses native visitors 894–901; strong/mounted/shielded 902–912 exist only with the `full`/generic profiles. The matrix must not claim P0 enemies are present in the default weak profile; A/C/D must record the active profile with every observation.

### 6.2 Feasible proxies for priority

- **F-now:** class loadout/weapon choice and position (sniper rear with LOS to the main approach; scout lateral; lumberjack close) — these shape *which* enemies each class meets first, without selecting targets.
- **F-now:** kill attribution by class × victim troop (`kills_by_class_team0[troop]`) so D can test whether P0 enemies actually die early; this is measurement, not control.
- **B-engine:** explicit "focus the Tank" target assignment, target marking, per-agent priority list, look-target as a proxy (`agent_set_look_target_agent` 1713 affects look direction only; its combat effect is unverified and not designed here).
- **F-build experiments:** armour-piercing/multi-target WSE2 toggles (§4) as *capability* improvements, still not target selection.

---

## 7. Fallback and desperation rules

The mode machine is the same for all classes (task-53), with class-conditioned thresholds. **F-build** for thresholds/orders; per-agent tactical retreat remains engine-side.

| Mode | Condition (per class where noted) | Action | Feasibility |
| --- | --- | --- | --- |
| HOLD-FIRE | default; ammo > 0 | hold at anchor/element; fire-at-will; keep ranged weapon | F-now |
| FALLBACK | Scout first (local ratio >1.5 or HP <50%); Sniper on screen collapse/enemy <15; Commando ammo 0 + high threat or HP <30%; Lumberjack last | `mordr_fall_back` to E0/entry 0, then re-issue hold. **No target/strength getter** — thresholds can only use counts, positions, ammo and HP; no per-target threat evaluation | **F-build** threshold computation; **B-unproven** order reach |
| REGROUP | after fallback, ≥3 survivors, local pressure below threshold | move to E0 apron, re-issue class slots after settle delay | F-build |
| DESPERATE-MELEE | ammo 0 and enemy <10 (Lumberjack always; others only then) | allow melee switch / bowie | F-now experiment (per-agent gate); **no charge** |
| RESUPPLY | between waves/round transition | refill ammo (`agent_refill_ammo` 1728), relative heal (`agent_set_hit_points` 1721), regroup | F-now (ops exist; runtime unverified) |
| DISENGAGE | never for zombies; survivors only to E0 | fallback, not rout; `agent_is_routed` must stay 0 | F-build + D evidence; engine caveat |

**Desperation must not become a charge.** A melee switch is allowed only when the enemy is already at contact distance or ammo is exhausted; otherwise the class falls back. This is the same "no retreat for zombies / fallback for survivors, never rout" separation from task-61.

---

## 8. Between-wave upgrade path

### 8.1 Options and feasibility

| Option | What it gives | Feasibility | Blockers |
| --- | --- | --- | --- |
| **A. Regroup + rearm at E0** | between-wave consolidation: heal, refill ammo, re-form classes, announce arrivals | **F-now** (ops exist) / D unverified | order reach; no purchase UI |
| **B. Build-time class tiers** | T1/T2 clone troops with better original-0.4 armour/weapons; refill trigger selects tier by wave/round | **F-build** | new troop records, owner approval, loadout/item validation, receipts/tests, spawn trigger change |
| **C. Mid-mission armour/weapon purchase** | survivors buy/upgrade between waves | **B-engine** | no per-agent equipment/armour op; no bot inventory/currency UI; `item_set_head/body_armor` (WSE2 3804/3805) edits item templates globally, not a survivor upgrade |
| **D. Weapon switching only** | swap among carried weapons | **F-now** | `agent_set_wielded_item` 1747; does not add new gear |

### 8.2 Proposed tier table (design options, not built)

All items must come from the documented original 0.4 item set; names below are those seen in the project's firearm/loadout documentation (M16A2, AK47, FN SCAR-L, M249, MP5, MP5K, MP7, P90, Mk12 SPR, M82, Remington 700, Cynergy). A must verify each item's numeric ID and compatibility before any build; **no new items**.

| Tier | Commando | Sniper | Scout | Lumberjack |
| --- | --- | --- | --- | --- |
| T0 (current) | M16A2 | Remington 700 | MP5 | Cynergy |
| T1 (wave ≥3 proposal) | AK47 or FN SCAR-L | Mk12 SPR | MP5K or MP7 | same shotgun + better original armour |
| T2 (wave ≥5 proposal) | M249 | M82 | P90 | same shotgun + best original armour |

Armour progression is limited to original clothing items already in the archive (e.g. police/sheriff uniforms/lumberjack shirt variants); do **not** invent armour values or add native assets. Tier selection must be recorded in the receipt and exposed to C (`troop_tier`, `spawn_tier_source`).

### 8.3 Why tiering is the honest upgrade path

The engine only lets a spawn choose a troop record; it does not let a script add armour or a weapon to a living bot. Therefore "between-wave upgrades" are **respawn as a better class record** (B) plus **rearm/heal** (A), not a shop. This must be stated in the owner-facing summary; a purchase/upgrade UI would be a different project scope (engine/UI work, not this matrix).

---

## 9. Coordination asks

### A — implementation

1. **Class mapping in the 5 s trigger:** read `agent_get_troop_id` (1718), map 981–984 → class, assign the class division/slot (5/6/7; reserve slot 8 is **B-unproven/blocked**, use division 5 rear element as baseline), and apply class speed (`agent_set_speed_modifier` 2093: commando 100, sniper 85, scout 115, lumberjack 95 — targets; team-0 only, no conflict with the team-1 wave-speed loop, D-observable only after re-seal). Class accuracy via `agent_set_accuracy_modifier` (2092) **interacts with / can override the global auto-accuracy profile** — do not treat them as independent; measure both.
2. **Keep the order set fixed:** `mordr_hold` + `mordr_fire_at_will` + `mordr_use_ranged_weapons`; per-agent ammo gate (`can_weapon_switch`) stays; no `mordr_hold_fire`; no scripted destination.
3. **Class-conditioned fallback thresholds** in the mode machine (scout first, lumberjack last) using **counts, positions, ammo and HP only — there is no target/strength getter**; fallback uses E0/entry 0; regroup after. Order reach is **B-unproven** until division adoption is proven.
4. **Between-wave options:** (A) refill/heal/regroup now; (B) tier clones + refill tier selection as a separate build change with receipt fields; do not attempt mid-mission armour changes.
5. **Experiment-gated only:** WSE2 multihit/piercing/crush-through for shotgun/sniper; separate build, D evidence, no baseline claim.
6. **Record receipt fields:** class→division map, speed/accuracy modifiers per class, tier selection, fire orders, fallback thresholds, and `class_matrix_version`.

### C — telemetry

1. **Class map:** troop id → class (981–984) in heartbeat/ai_sample; aggregate per class.
2. **Range/engagement evidence:** distance from each survivor to nearest enemy (or anchor) at shot/first damage/kill; per-class histogram; label the measurement point explicitly.
3. **Kill attribution by class × victim troop id** (`kills_team0_by_class`, `victim_troops`), so P0/P1/P2 prioritisation can be tested rather than assumed.
4. **Fire/weapon evidence:** weapon, ammo, `agent_get_simple_behavior`, `agent_get_attack_action`, `agent_ai_set_can_weapon_switch` state where readable; `agent_is_routed` per class.
5. **Fallback/regroup events** per class and mode dwell; `hold_behavior_observed` stays false until positions/behaviour show it.
6. **Upgrade evidence:** tier spawned per class, refill series, heal/ammo refill events; gaps as `tier_source_unknown` when A has not exposed them.

### D — sealed validation

1. **Class-hold/fire run:** each class holds its slot, fires, retains weapon; per-class positions/ranges; no charge.
2. **Priority-responsibility run:** with the profile that actually contains P0/P1 enemies, measure kills/deaths by class × victim troop; report whether P0 die early relative to their share.
3. **Fallback/desperation run:** ammo-limited variant to force melee gate; scout falls back first, lumberjack last; `agent_is_routed` stays 0.
4. **Between-wave run:** regroup/rearm at E0; tier selection (if implemented) shows T1/T2 spawn by wave; no purchase claim.
5. **Negative controls:** weak-wave-1 profile must not be described as validating P0 priority; no acceptance claim.

---

## 10. Feasible-now vs blocked — summary

| Item | Status |
| --- | --- |
| Class→loadout identity (981–984) | **F-now** (data exists) |
| Class→division/slot mapping | **F-build**; effect **B-unproven** until adoption/readback proves |
| Class-specific speed via 2093 (team 0) | **F-now** (op exists; class mapping F-build; D-observable only after re-seal; no conflict with team-1 wave-speed loop) |
| Fire-at-will/hold/keep-rifle orders | **F-now** (already in build) |
| Class-specific fire cadence/mode | **B-engine** (no per-agent fire-mode op; launcher fire-mode is global, task-68) |
| Range bands as placement | **F-now/F-build** |
| Dynamic range keeping/kiting | **B-engine** |
| Target responsibility/priority enforcement | **B-engine** (no target setter) |
| Kill attribution by class × victim | **F-build** telemetry (C) |
| Melee last-resort gate | **F-now** (per-agent gate exists; class-conditioned variant F-build) |
| Fallback/regroup thresholds (counts/positions/ammo/HP only — no target/strength getter) | **F-build**; order reach **B-unproven** |
| Regroup/rearm/heal between waves | **F-now** ops; runtime unverified |
| Tier clones + wave-based selection | **F-build** (owner approval, troop records, tests, receipt) |
| Mid-mission armour/weapon purchase | **B-engine** |
| WSE2 multihit/piercing/crush-through | **F-now experiment** per-agent mutation; not baseline |
| Zombie non-retreat / survivor non-rout | **F-build observation + D**; engine-rout caveat (task-61) |

---

## 11. Risks and unverified items

1. **Division adoption/addressability** is unproven; if the round-trip fails, class→slot and class-specific division orders collapse to labels (task-61 §4.4).
2. **Group/order namespace confusion** (26/28/29/31, 8..15) remains unresolved; never pass group values as `team_give_order` sub-classes or as `add_visitors` group arguments.
3. **Target priority cannot be enforced.** Any observed "sniper prioritises tanks" is emergent or positional; report it as such.
4. **Range bands are placement targets.** Engine AI can close distance; no per-agent kiting claim.
5. **Current profile gating:** weak-wave-1 default restricts generic enemies to 894; P0/P1 validation requires the profile that actually spawns them, recorded in the receipt.
6. **Fire modes** are not per-agent today; task-68's launcher fire-mode is global/pre-game, not per class. Do not claim class-specific burst/auto.
7. **Mid-mission upgrades are blocked** by the engine's equipment API; only respawn-tier + rearm/heal are honest.
8. **WSE2 binding availability** for 3314/3343/3352/3353/3355/3359 must be capability-probed; a header entry is not proof on the pinned build.
9. **Morale/rout:** static absence of courage scripts in the City chain does not prove the engine cannot route; use `agent_is_routed` observation.
10. **Class skills/armour** changes are build-time data only; do not assume runtime stat edits.

---

## 12. Handoff

- This document is design input only; it changes no build, loadout, trigger, scene or asset. No acceptance is claimed.
- A implements §9-A in the City-only layer; C implements §9-C fields with capability flags; D runs §9-D sealed. Owner approval is required for new tier troop records or any scene/defence-line change.
- **A, 2026-10-24 (against `f1ba5c5`): consistent with build, corrections applied:** reserve slot 8 marked **B-unproven/blocked** (baseline is division 5 rear element); class speed on team 0 confirmed feasible/F-now and non-conflicting with the team-1-only native wave-speed loop, observable after re-seal; `agent_set_accuracy_modifier` (2092) explicitly stated to stack/override the global automatic-accuracy profile; fallback thresholds limited to counts/positions/ammo/HP (**no target/strength getter**) with order reach B-unproven; refill/heal ops 1728/1721 confirmed native; tier clones explicitly owner-approved separately; multihit/piercing separate builds only.
- C and D were sent the telemetry/validation asks; any later findings should be appended here. No unresolved A blocker.

*End of document.*
