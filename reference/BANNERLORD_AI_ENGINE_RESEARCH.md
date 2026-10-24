# Bannerlord AI engine research — conceptual adaptation for the ZOMBIEEE remaster (task-56)

**Status: docs-only desktop research. No Bannerlord or Warband process was launched; no Bannerlord engine assembly, decompiled code, asset or dataset was read, extracted or copied.** Every engine claim below is either (a) quoted/paraphrased from an official TaleWorlds publication, (b) a public API-surface observation from the official generated API reference, or (c) explicitly marked **[unverified]**. Observation date: **2026-10-24**. Base: `main` `d47a89d` in worktree `agent/h-bannerlord-research`.

This document does **not** accept, validate or close any ZOMBIEEE gameplay item. It is an input to A (behavior/build), C (telemetry/summary) and D (sealed validation). Runtime claims remain whatever the sealed evidence says they are; nothing here is evidence about *our* build.

## 0. Why Bannerlord is relevant at all

The project targets **Warband 1.174 under WSE2 1.1.5.4**, not Bannerlord. Bannerlord is useful only as a **design reference**: it is the same studio's later, much more explicit take on (i) layering battle AI into tactic / formation / individual decisions, (ii) making the AI use the same order interface as the player, (iii) modelling morale, panic and panic spread as first-class systems, and (iv) exposing spawn/round state as queryable mission data. The parts we can reuse are *concepts and information models*; the parts we must not touch are its engine code, assemblies, data and assets (section 6).

---

## 1. Sources actually read (with dates and limits)

| # | Source | Type | Date observed / published | What it establishes here | Limits |
| --- | --- | --- | --- | --- | --- |
| S1 | [Dev Blog 25/10/18 — "Artificial intelligence"](https://web.archive.org/web/20241214225556/https://www.taleworlds.com/en/Games/Bannerlord/Blog/83) (live page returned HTTP 403 to this machine; Wayback capture used) | Official TaleWorlds | Published **2018-10-25**; observed via Wayback 2026-10-24 | Battle AI is explicitly split into **individual / formation / tactic** layers; formation AI issues orders and individual AI interprets them; AI has access to the same command interface as the player ("our combat AI doesn't cheat"); the layer split is the modding contract | Pre-release design description; no class-level detail, no code |
| S2 | [Dev Blog 12/07/18 — Campaign AI programmer interview](https://web.archive.org/web/20250523165133/https://www.taleworlds.com/en/Games/Bannerlord/Blog/68) | Official TaleWorlds | Published **2018-07-12**; observed via Wayback 2026-10-24 | Party morale is a real stat; low morale + casualties can make troops **flee** in battle, and a battle "can be lost even if most of your troops are still alive" | Campaign-map framing; not a battle-AI spec |
| S3 | [Dev Blog 26/09/19 — Siege assault AI](https://web.archive.org/web/20241113015245/https://www.taleworlds.com/en/Games/Bannerlord/Blog/127) | Official TaleWorlds | Published **2019-09-26**; observed via Wayback 2026-10-24 | AI commander estimates whether attack/defence can succeed and may **cancel an assault / retreat** as a *strategic decision*; retreat is not only a morale reflex | Siege-specific narrative |
| S4 | [Dev Blog 15/10/19 — Morale](https://web.archive.org/web/20250114200045/https://www.taleworlds.com/en/Games/Bannerlord/Blog/128) | Official TaleWorlds | Page dated **2019-10-14**; observed via Wayback 2026-10-24 | Concrete morale model: starting morale from party morale; casualties cause a penalty to nearby friends (up to a max of ten); shield wall reduces the penalty; a nearby friendly kill gives a boost; **panic spreads** and a few runners can break a formation; commander skills/perks modify it | Single-player battle description; exact constants not published |
| S5 | [Bannerlord Modding Documentation — Creating a Module (Official)](https://moddocs.bannerlord.com/asset-management/quickguide_create_a_mod/) | Official TaleWorlds docs | Observed 2026-10-24 | Module shape: `Modules/<name>/SubModule.xml`, `bin\Win64_Shipping_Client`, `ModuleData/*.xml` with `project.mbproj`, DLL class deriving from `MBSubModuleBase`; module content types (troops, items, factions, scenes, scripts) | Guide, not an AI reference |
| S6 | [Bannerlord Modding Documentation — Creating a Custom Game Mode (Official)](https://moddocs.bannerlord.com/multiplayer/custom_game_mode/) | Official TaleWorlds docs | Observed 2026-10-24 | A mission is composed from an **array of `MissionBehavior` objects** returned to `MissionState.OpenNew(...)`; server/client split; the example includes `SpawnComponent(new SpawnFrameBehavior(...), new SpawningBehavior(...))`, `MissionAgentPanicHandler`, `AgentHumanAILogic`, `MultiplayerTimerComponent`, scoreboard/notification components | Official sample covers MP, not the invasion/campaign battle; some listed behaviors are game-mode specific |
| S7 | [API reference — `FormationAI`](https://apidoc.bannerlord.com/v/1.4.7/class_tale_worlds_1_1_mount_and_blade_1_1_formation_a_i.html) | Official generated API docs (v1.4.7) | Observed 2026-10-24 | Formations hold a set of `BehaviorComponent`s; selection is exposed via `SetBehaviorWeight<T>(float)`, `GetBehavior<T>()`, `ActiveBehavior`, `BehaviorCount`, `Side` (`Left/Middle/Right`), `IsMainFormation`, event `OnActiveBehaviorChanged`, `Tick()` | Public surface only; scoring weights/formulas are not documented |
| S8 | [API reference — `BehaviorComponent`](https://apidoc.bannerlord.com/v/1.4.7/class_tale_worlds_1_1_mount_and_blade_1_1_behavior_component.html) | Official generated API docs (v1.4.7) | Observed 2026-10-24 | Abstract base with `GetAIWeight()` (abstract), `BehaviorCoherence`, `WeightFactor`, `PreserveExpireTime`, `CurrentOrder`, `Formation`, `TickOccasionally()`, `OnBehaviorCanceled()`, `OnLostAIControl()`. Inheritors include `BehaviorAdvance`, `BehaviorCautiousAdvance`, `BehaviorCharge`, `BehaviorTacticalCharge`, `BehaviorDefend`, `BehaviorDefendKeyPosition`, `BehaviorFlank`, `BehaviorProtectFlank`, `BehaviorHoldHighGround`, `BehaviorPullBack`, `BehaviorRegroup`, `BehaviorReserve`, `BehaviorRetreat`, `BehaviorRetreatToCastle/Keep`, `BehaviorSkirmish`, `BehaviorSkirmishLine`, `BehaviorScreenedSkirmish`, `BehaviorSparseSkirmish`, `BehaviorFireFromInfantryCover`, `BehaviorCavalryScreen`, `BehaviorVanguard`, `BehaviorSergeantMP*`, … | Names are evidence of a catalog of *named formation behaviours*; no source code |
| S9 | [API reference — `Formation`](https://apidoc.bannerlord.com/v/1.4.7/class_tale_worlds_1_1_mount_and_blade_1_1_formation.html) | Official generated API docs (v1.4.7) | Observed 2026-10-24 | Formation has **independent order channels** — `SetMovementOrder`, `SetFacingOrder`, `SetArrangementOrder`, `SetFormOrder`, `SetRidingOrder`, `SetFiringOrder` — plus `SetControlledByAI`, `SetTargetFormation`, `GetFormationPower`, `GetFormationMeleeFightingPower`, integrity data (`CachedAveragePosition`, `CachedClosestEnemyFormation`, `DetachedUnits`), `QuerySystem`, and logical vs physical class (`LogicalClass` fixed at spawn; `PhysicalClass` changes if a mount dies) | Class reference without tutorials |
| S10 | [API reference — `MovementOrder`](https://apidoc.bannerlord.com/v/1.4.7/struct_tale_worlds_1_1_mount_and_blade_1_1_movement_order.html) | Official generated API docs (v1.4.7) | Observed 2026-10-24 | Enumerates `AttackEntity`, `Charge`, `ChargeToTarget`, `Follow`, `Move`, `Retreat`, `Stop`, `Advance`, `FallBack`; `MovementState` = `Charge/Hold/Retreat/StandGround`; engine exposes `GetMovementOrderDefensiveness` | No numeric thresholds |
| S11 | [API reference — `Agent`](https://apidoc.bannerlord.com/v/1.4.7/class_tale_worlds_1_1_mount_and_blade_1_1_agent.html) | Official generated API docs (v1.4.7) | Observed 2026-10-24 | `AIStateFlag` (`Cautious`, `PatrollingCautious`, `Alarmed`, `Paused`, object-use states, `AlarmStateMask`); `AIScriptedFrameFlags` (`GoToPosition`, `NoAttack`, `ConsiderRotation`, `NeverSlowDown`, `DoNotRun`, `GoWithoutMount`, `RangerCanMoveForClearTarget`, …); `AISpecialCombatModeFlags` (`AttackEntity`, `SurroundAttackEntity`, `IgnoreAmmoLimitForRangeCalculation`); `SetScriptedPosition*`, `SetScriptedTargetEntity`, `SetAIBehaviorParams`, `GetTraitsMask` (e.g. shield gone after break), `GetBattleImportance`, `GetTargetFormationIndex` | Bitmask semantics partly undocumented |
| S12 | [API reference — `HumanAIComponent`](https://apidoc.bannerlord.com/v/1.4.7/class_tale_worlds_1_1_mount_and_blade_1_1_human_a_i_component.html) | Official generated API docs (v1.4.7) | Observed 2026-10-24 | Per-agent AI component with `AISimpleBehaviorKind` = `GoToPos`, `Melee`, `Ranged`, `ChargeHorseback`, `RangedHorseback`, `AttackEntityMelee`, `AttackEntityRanged`; `BehaviorValueSet` = `Default`, `DefensiveArrangementMove`, `Follow`, `DefaultMove`, `Charge`, `DefaultDetached`, `Overriden`; `OverrideBehaviorParams(kind, y1, x2, y2, x3, y3)`, `SetBehaviorValueSet`, `RefreshBehaviorValues(movementOrder, arrangementOrder)`, `OnRetreating`, `GetDesiredSpeedInFormation`, `AdjustSpeedLimit` | Parameter meanings are not documented |
| S13 | [API reference — `MissionBehavior` / `MissionLogic`](https://apidoc.bannerlord.com/v/1.4.7/class_tale_worlds_1_1_mount_and_blade_1_1_mission_behavior.html) (and `AgentHumanAILogic` derives from `MissionLogic`) | Official generated API docs (v1.4.7) | Observed 2026-10-24 | Callback surface includes `OnAgentCreated`, `OnAgentBuild`, `OnAgentHit`, `OnAgentRemoved`, `OnAgentDeleted`, `OnAgentFleeing`, `OnAgentPanicked`, `OnDeploymentFinished`, `OnTeamDeployed`, `OnMissionTick`, `OnMissionStateFinalized`, etc. — events, not a polling script | No ordering guarantees documented |
| S14 | [API reference — `MissionAgentSpawnLogic`](http://apidoc.bannerlord.com/v/1.3.14/class_tale_worlds_1_1_mount_and_blade_1_1_mission_agent_spawn_logic.html) | Official generated API docs (v1.3.14) | Observed 2026-10-24 | Spawn model with explicit **total vs initial** troops per side (`InitWithSinglePhase(defenderTotalSpawn, attackerTotalSpawn, defenderInitialSpawn, attackerInitialSpawn, spawnDefenders, spawnAttackers, spawnSettings)`), phase change actions, `OnInitialTroopsSpawned` / `OnReinforcementsSpawned`, `GetReinforcementInterval`, `SetReinforcementsSpawnEnabled`, `IsSideDepleted`, `NumberOfRemainingTroops`, `IsInitialSpawnOver`, `BattleSize` | v1.3.14 page (v1.4.7 path 404); version drift possible |
| S15 | [Community docs — `Agent`](https://docs.bannerlordmodding.com/_csharp-api/mountandblade/agent.html) | Community (WIP, v1.1) | Observed 2026-10-24 | Corroborates `AIStateFlag` values, `Agent.Main`, controller type `AI/Player`; useful as a cross-check only | Community-maintained, marked WIP |
| S16 | [Community docs — XML `NPCCharacter`](https://docs.bannerlordmodding.com/_xmldocs/npccharacters/npccharacter/) | Community docs for game XML | Observed 2026-10-24 | Troop/NPC data includes `is_female` (boolean), `default_group` = `Infantry | General | Ranged | HorseArcher | Cavalry` ("the default group the NPC belongs to when giving orders"), `formation_position_preference` (`Back`), `battleTemplate`, skills/equipment nodes | Community transcription of data schema; not an engine guarantee |
| S17 | [BUTR unofficial API — `SandBox.Missions.AgentBehaviors.ScriptBehavior`](https://bannerlordapi.butr.link/api/sandbox/SandBox.Missions.AgentBehaviors.ScriptBehavior.html) | Community-generated decompiled-surface reference | Observed 2026-10-24 | Scripted mission agent behaviours support `AddAgentTarget`, `AddTargetWithDelegate(selectTargetDelegate, …)`, `AddWorldFrameTarget`, `GetAvailability(bool)` (returns a float), `Tick`; inherits `AgentBehavior` with `BehaviorGroup` | Unofficial; used only to corroborate that target selection is a delegate-driven agent-behaviour concept |
| S18 | [Bannerlord Modding Tools EULA — Steam EULA page](https://store.steampowered.com/eula/1393600_eula_0) | Official legal text (publisher) | Observed 2026-10-24 | §1.3(i) prohibits reverse engineering/discovering source code in the Mod Tools, Game or DLC; §2.3 TaleWorlds retains all ownership/IP; §3.1 mods may only be distributed non-commercially and only as part of the Game; §3.2 TaleWorlds does not claim ownership of your mod | EULA for the modding tools; base-game EULA not fetched here |

**Inaccessible / recorded:** live `taleworlds.com` blog pages returned HTTP 403 (Cloudflare) to this machine — Wayback captures were used and their capture IDs are embedded in the URLs above. The Steam EULA for the base game id 261550 failed to render ("error loading the content") and is **not** used as evidence. No official TaleWorlds source was found that uses the term "behaviour tree" for battlefield AI (see §2.3).

---

## 2. Engine basis and how a battle actually runs

### 2.1 Platform and module shape

Bannerlord is a proprietary TaleWorlds C# engine. Official documentation defines a module as a folder under `Modules` containing:

- `SubModule.xml` (name, ID, version, dependencies, `ModuleCategory`);
- `bin\Win64_Shipping_Client` (and `..._Server` for dedicated servers) for compiled DLLs;
- `ModuleData` XML (troops, items, factions, …) governed by a `project.mbproj`;
- assets (meshes, materials, scenes, audio) and, optionally, C# classes deriving from `MBSubModuleBase` that register behaviours.

That is a **compiled-code modding surface plus declarative data**, not a Python module system. S5/S6.

### 2.2 Mission composition: behaviours, logics, views

A mission is opened with `MissionState.OpenNew(name, initializer, missionController => new MissionBehavior[] { … })`; the returned behaviours are ticked and receive callbacks. `MissionLogic` is a `MissionBehavior` subtype for game logic; `MissionView` handles presentation. The official custom-game-mode guide shows the order is real: lobby component, game-mode logic, timer, **spawn component**, equipment/team-select, boundary handlers, poll/admin/notifications, options, scoreboard, **`MissionAgentPanicHandler`**, **`AgentHumanAILogic`** (S13, S6).

Key structural facts for us:

1. **AI is composed from injectable behaviours.** A mod can add/remove/replace the panic handler, the spawning behaviour, the human-AI logic — i.e. *whether agents can panic at all is a mission-composition decision*, not a hard engine constant. S6.
2. **Callbacks are event-driven.** `OnAgentPanicked`, `OnAgentFleeing`, `OnAgentRemoved`, `OnDeploymentFinished` exist (S13). This is materially different from Warband mission-template triggers, which are script fragments evaluated on a timer/condition basis.
3. **Individual AI is parallelised.** S1 says handling hundreds of agents' per-agent decisions at once is solved with parallel processing; there is an `OnTickParallel` in `HumanAIComponent` (S12). This is the performance reason for the layered design, and the reason a mod is expected to hook behaviours rather than write an agent loop.

### 2.3 "Behaviour trees": what the sources actually show

**The term "behaviour tree" is not used in any official source read for this task. [unverified]**

What *is* documented is a **utility/weight behaviour-selection system at formation level** (S7, S8):

- a formation owns a collection of named `BehaviorComponent`s (`BehaviorCharge`, `BehaviorDefend`, `BehaviorSkirmish`, `BehaviorRetreat`, `BehaviorRegroup`, `BehaviorPullBack`, `BehaviorFlank`, …);
- each component exposes `GetAIWeight()`; the formation exposes `SetBehaviorWeight<T>(float)`, `ActiveBehavior`, `BehaviorCount`, and an `OnActiveBehaviorChanged` event;
- components carry `BehaviorCoherence`, `WeightFactor` and `PreserveExpireTime` — i.e. **selection by score with stickiness/decay**, not a hand-authored tree;
- `FormationAI` also tracks `Side` (Left/Middle/Right) and `IsMainFormation`, which is how a battle line is split into flanks/middle.

At the individual level, `HumanAIComponent.AISimpleBehaviorKind` is the small set `GoToPos/Melee/Ranged/ChargeHorseback/RangedHorseback/AttackEntityMelee/AttackEntityRanged`, and its parameter set is refreshed from the **current movement order and arrangement order** (`RefreshBehaviorValues(movementOrder, arrangementOrder)`), with `BehaviorValueSet` values `Default`, `DefensiveArrangementMove`, `Follow`, `DefaultMove`, `Charge`, `DefaultDetached`, `Overriden` (S12). That is a **context-parameterised behaviour table**, not a tree.

**Conclusion:** think "weighted behaviour scoreboard with sticky active behaviour", not "behaviour tree". If we ever build tooling, model it as a score vector + hysteresis, and do not wait for an engine BT hook that does not exist on the documented surface. (Tactic layer is described narratively in S1/S3; the class that owns it is not on the public docs read here. **[unverified]**)

### 2.4 Tactic layer

Per S1, Tactic AI is the "general": it reads terrain and army composition, is personality-influenced (cautious vs rash commander), picks an overall plan, and each formation "isn't strictly tied to it" — formations may deviate to exploit an advantage or pull back. S3 adds the concrete decision: an attacking commander may **call off an assault** when the exchange rate says further attack only bleeds troops.

For our purposes the tactic layer is the model for "**one intent owner per side, with subordinate autonomy bounded by the plan**". ZOMBIEEE has one intent owner (the wave controller) and two sides with very different autonomy budgets (zombies ≈ none; survivors ≈ formation-local).

---

## 3. Combat AI design details worth stealing

### 3.1 Target selection

Documented pieces (all surface-level):

- formation-level: `Formation.SetTargetFormation` / `Formation.TargetFormation`, and cached `CachedClosestEnemyFormation` (S9);
- agent-level: the individual AI "selects a target" (S1); the API exposes scripted overrides (`SetScriptedTargetEntity`, `AISpecialCombatModeFlags.AttackEntity/SurroundAttackEntity`) and `GetTargetFormationIndex` (S11);
- scripted mission agents select targets through a `SelectTargetDelegate` that returns availability as a float (S17).

**The exact target-scoring formula (distance/threat/visibility/weapon suitability) is not published. [unverified]** So: adopt the *shape* (two-level: formation target + agent target; a delegate/score that can be overridden per behaviour) and do not pretend to reproduce the numbers.

### 3.2 Ranged vs melee decisions

Evidence:

- formations have a **separate firing order** (`SetFiringOrder`/`FiringOrder`) alongside movement, arrangement, form, facing and riding orders (S9) — fire discipline is an *order channel*, not a per-agent toggle;
- individual AI has explicit `Ranged` and `Melee` simple behaviours and switches the behaviour-value set by context (S12);
- the agent exposes equipment/ammo reality: `GetTraitsMask` (a broken shield stops reporting the shield bit), reload action stages (`ReloadMidPhase`, `ReloadLastPhase`), and `AISpecialCombatModeFlags.IgnoreAmmoLimitForRangeCalculation` (S11).

This is the same separation our WSE2 work already relies on: **the weapon/fire decision is its own layer**; movement orders must not be used to fake it. Our live regression where survivors charged instead of shooting is exactly the failure mode Bannerlord's separation is designed to prevent (movement order ≠ fire order ≠ weapon-switch policy).

### 3.3 Formations and orders

The formation API is the single most reusable thing in Bannerlord:

| Order channel | Bannerlord | Our Warband/WSE2 analogue |
| --- | --- | --- |
| Move/hold/fallback/retreat | `MovementOrder` (`Charge`, `Advance`, `FallBack`, `Retreat`, `Stop`, `Move`, `Follow`, `AttackEntity`) | `team_set_order_position(1791)` + `team_give_order(1790, mordr_hold/charge/advance/fall_back)` |
| Fire discipline | `FiringOrder` (`RangedWeaponUsageOrderEnum`), per-agent `SetFiringOrder` | `mordr_hold_fire(12)`, `mordr_fire_at_will(13)`, `mordr_use_ranged_weapons(16)` |
| Formation shape | `ArrangementOrder`, `FormOrder` | native `mordr_form_*` / `mordr_spread_out` (subset; no full arrangement API) |
| Facing | `FacingOrder` | `team_give_order` facing? (not relied on here; **[unverified]**) |
| Riding | `RidingOrder` | no direct need for City |
| AI ownership | `SetControlledByAI(bool)` | implied by team orders; per-agent scripted mode overrides it |
| Unit class | `LogicalClass` (fixed at spawn), `PhysicalClass` (changes if dismounted), `FormationClass` counts | divisions `grc_infantry/archers/cavalry` + `agent_set_division` |

The critical lesson (S1, S8): **formation orders constrain intent, but the individual AI still decides how to execute** — a hold order does not freeze agents into a pose; it makes them fight from the ordered position, and it is exactly why "hold" can degrade into a charge if the individual layer is allowed to switch weapons and pursue. Conversely, per-agent scripted movement fights the order layer (already documented in our `reference/WARBAND_AI_MODDING.md` §2). Bannerlord keeps the layers separate; we should too.

Also note `Formation.GetFormationPower()`, `GetFormationMeleeFightingPower()` and `GetUnderAttackTypeOfUnits()` (S9): the engine computes group-level strength/visibility summaries for the AI to decide with. That is a direct precedent for **the overlay computing a bounded friend/enemy summary per tick instead of per-agent decisions**.

### 3.4 Morale, panic and retreat

This is the most design-relevant system for the owner's "zombies must be stupid and never retreat" requirement.

Documented model (S4, S2, S3):

1. Each soldier starts with morale derived from the party's morale.
2. A friendly death causes a morale penalty to nearby friends; the shock only counts up to a **maximum of ten** recent casualties (bounded propagation, not global).
3. Standing in a **shield wall reduces the penalty**; a nearby friendly **kill gives a boost**.
4. When morale crosses a threshold the soldier **panics and runs**.
5. A panic creates a penalty for nearby troops, so **rout is a chain reaction**; whole formations can break.
6. Retreat can also be a **commander decision**: the tactic AI estimates success and may disengage (S3) — distinct from individual panic.
7. The engine treats panic/flee as first-class events/behaviours: `MissionBehavior.OnAgentPanicked`, `OnAgentFleeing`, `MovementBehaviorType.Flee`, `HumanAIComponent.OnRetreating`, `AgentComponent.GetMoraleAddition/GetMoraleDecreaseConstant`, and a **replaceable `MissionAgentPanicHandler`** behaviour (S13, S11, S12, S6).

Consequences for us:

- **Panic is an input system.** "Make zombies not retreat" is not a speed clamp; it is *not feeding them the retreat/panic inputs* and *not appointing a commander who chooses withdrawal*. Our team 1 should never receive a fall-back/retreat order, must not be switched to a low-aggressiveness/defensive behaviour, and must not be given a scripted destination away from the enemy. If the Warband engine has any native rout path in MP [unverified], pin it with the WSE2 simple-behaviour op (melee/charge) rather than hoping orders suffice.
- **Distinguish "fall back" from "retreat".** Bannerlord has both (`MovementOrder.FallBack` vs `MovementOrder.Retreat`, and `MovementState.Hold/StandGround`) and treats the latter as a field-leaving/commander decision. For survivors we want *fallback to the base anchor* (a movement order) and never a rout; the state machine must name them differently and telemetry must not conflate them.
- **A bounded shock radius is a cheap, legible design.** If we ever add survivor cohesion shock (nearby deaths → fallback), cap the effect (Bannerlord: max ten casualties) and make it recoverable (hold/regroup), otherwise a bad wave becomes an unrecoverable rout loop.

### 3.5 Waves, spawning, reinforcement and round state

`MissionAgentSpawnLogic` is a ready-made information model (S14):

- explicit **total vs initial** spawn counts per side (`defenderTotalSpawn/attackerTotalSpawn` vs `…InitialSpawn`); the remainder arrives as reinforcements;
- `MissionSpawnSettings` controls reinforcement counts and intervals; `GetReinforcementInterval`, `SetReinforcementsSpawnEnabled`;
- events `OnInitialTroopsSpawned`, `OnReinforcementsSpawned`, `OnPhaseChangedDelegate`, `AddPhaseChangeAction`;
- state queries `IsInitialSpawnOver`, `IsDeploymentOver`, `IsSideDepleted`, `NumberOfRemainingTroops`, `NumberOfActiveDefenderTroops`, `NumberOfActiveAttackerTroops`.

The MP composition additionally uses `SpawnComponent(SpawnFrameBehavior, SpawningBehavior)`, a `MultiplayerTimerComponent`, and `MissionAgentPanicHandler` (S6). Scene-side, spawn points and "mission tactical positions" are authored assets with a debug tool (official docs index, S5 site).

**This is exactly what our wave/arrival clarity problem is missing:** not necessarily more spawning, but an explicit, queryable state model — "total this wave", "spawned so far", "remaining before next wave", "initial spawn over", "side depleted", "spawn gate open/closed", "next wave in N s" — with events on transitions. Our current build has wave counters and a bit of inference; that is the moral equivalent of reading the raw counters without the phase model.

Two additional transferable points:

- `IsSideDepleted` is a *state*, not a guess from "alive == 0" while visitors are still queued. Wave-end must be defined against all three of: alive team 1, spawner/queue state, and the round/wave gate. Define it once, in A's build, and expose it to C.
- Spawning is a **behaviour with an owner**, not a side effect of a trigger body. If our wave controller is fragmented across triggers (spawn, top-up, refill, gating), C cannot observe a single phase. A should expose a single wave-state owner (globals + explicit transitions) and let the existing triggers write into it.

### 3.6 Gender, class and composition

Bannerlord puts composition in **data**: `NPCCharacter` carries `is_female` (boolean), `default_group` (`Infantry/Ranged/Cavalry/HorseArcher/General`, "the default group the NPC belongs to when giving orders"), `formation_position_preference` (`Back`), `battleTemplate`, `skill_template`, equipment (S16). At runtime, a formation's `LogicalClass` is fixed at spawn and its `PhysicalClass` can change when a horse dies (S9).

Lesson for the male/female survivor distribution: **gender is an attribute of the troop/NPC data, and composition is a spawn-table decision.** It is not an AI behaviour and there is no "set gender" AI op. In our Warband build the practical route is therefore: **separate troop variants** (male/female faces/voices) per survivor class, plus a **weighted spawn table** that selects variants deterministically per wave. C then verifies the realised mixture from the troop-id histogram (which needs a documented id→variant table from A/E). **[unverified]**: we have not confirmed from the original module data which Warband field marks a troop female or whether our current spawn path can select variants without new troop entries; A/E must confirm before claiming anything.

---

## 4. Bannerlord modding surface vs Warband's module system

| Capability | Bannerlord | Warband (our target: module system + WSE2 1.1.5.4) |
| --- | --- | --- |
| Code | C# DLLs in `bin`, `MBSubModuleBase` registration; Harmony commonly used by community | No official C#; Python `module_*.py` compiled to text; native opcodes; WSE2 adds Lua + extra opcodes |
| Data | XML in `ModuleData` (troops/items/factions/parties), scenes, prefabs | `module_*.py` tables (troops/items/factions/parties) compiled to `*.txt`; mission templates |
| Mission logic | `MissionBehavior`/`MissionLogic` event callbacks; injectable behaviour array | Mission template triggers: condition block + consequence block, engine-scheduled; opcode script |
| AI control | Formation orders + AI behaviours + per-agent components | Team orders (`team_give_order`, `team_set_order_position`), per-agent scripted destination, aggressiveness, WSE2 simple behaviour/weapon switches |
| Spawn/round | `MissionAgentSpawnLogic`, spawn behaviours/components, timer component | `spawn_agent`, `add_visitors_to_current_scene`, entry points, triggers, globals, server `set_bot_count` |
| Morale/panic | First-class morale, panic events, panic handler behaviour | Not exposed as a modding API; proxy via aggressiveness/behaviour/orders. **[unverified]** whether MP invasion agents rout at all |
| Target selection | Two-level (formation target + agent target), scripted target overrides | No exposed target API; influence via aggressiveness/orders/weapon policy only |
| Formation shape | Independent movement/facing/arrangement/form/riding/firing orders | Movement + fire/weapon orders + limited form orders; no arrangement/facing API in the op set we use |
| Debug/telemetry | Engine debug views, `DebugMore/DebugScores` on `FormationAI` (S7), official docs tools | Recorder overlay, WSE2 Lua probe, our `tools/diagnostics.py` (read-only, sealed) |

The practical asymmetry: **Bannerlord's AI is designed to be extended at the behaviour layer; Warband's AI is designed to be steered at the order layer.** Any design that needs "new per-agent decision logic" is cheap in Bannerlord and expensive/unsupported in Warband. Therefore we should copy Bannerlord's *information architecture and decision cadence* while expressing all execution through existing order/behaviour ops — which is exactly the boundary our `reference/WARBAND_AI_MODDING.md` already established.

---

## 5. What is proprietary and must not be copied

1. **Engine and game code.** The Mod Tools EULA §1.3(i) forbids displaying, duplicating, dismantling, **reverse engineering**, circumventing or attempting to **discover the source code** or trade secrets of the Mod Tools, Game or DLC without prior consent; §2.3 says TaleWorlds retains all ownership and IP rights in the Mod Tools/Game/DLC (S18). **We must not decompile, disassemble, dump, paste or translate game/engine code.** Reading the official docs and API reference is fine; copying implementation from decompiled assemblies is not, regardless of how a community site obtained it.
2. **Assemblies/DLLs.** No Bannerlord DLL, XSLT, prefab, shader, scene, XML data file, animation or texture may be committed, extracted into our repo, or used as build input.
3. **Assets.** Troop models/textures/faces, UI art, sounds, scenes and animations are TaleWorlds or third-party licensed assets; "free to download" ≠ free to redistribute. Our own mod remains built only from the owner's legally owned Warband archive plus our original overlay (project policy already: `reference/ARCHIVE.txt`, README).
4. **Behaviour names/enums** (`BehaviorCharge`, `MovementOrder.FallBack`, …) are public API identifiers; citing them as facts is fine, importing a behaviour implementation is not.
5. **Mod distribution terms.** §3.1 restricts Bannerlord mods to non-commercial distribution as part of the Game. This research does not change our project's own legal position, which remains `reference/LEGAL_RIGHTS_AND_CREDITS.md` (E lane). Nothing here is legal advice.

**Adaptation boundary in one line:** take the *structure* (layers, order channels, bounded morale shock, explicit spawn state, data-driven composition); re-express it with our own code, our own data and Warband/WSE2 ops; never take Bannerlord code, assemblies, assets or decompiled logic.

---

## 6. Design lessons mapped to our concrete problems

### 6.1 Zombies: stupid, non-retreating, slower shamble

| Requirement | Bannerlord insight | Our implementation direction (A) |
| --- | --- | --- |
| Never retreat / no tactical withdrawal | Panic and retreat are **inputs/decisions** (morale shock, commander's success estimate), not inevitable physics (S3, S4). A crowd with no panic input and a charge-only intent has no withdrawal path. | Team 1 gets **only** charge/attack intent: never `mordr_hold`, `mordr_fall_back`, `mordr_stand_ground`; never a scripted destination away from survivors; keep aggressiveness high; pin `agent_ai_set_simple_behavior(agent, aisb_melee/charge…)` if any drift is observed. Audit that no team-1 agent is adopted into a defensive division/order. |
| Stupid (no kiting/flanking/formation) | Individual complexity lives in `HumanAIComponent`; formation behaviours like `BehaviorFlank`, `BehaviorSkirmish`, `BehaviorTacticalCharge` are opt-in components (S8, S12). Simplicity is the *default* when you don't add components. | Add nothing to team 1; do not give team 1 a target-selection policy, flank order, or regroup behaviour. Keep the native seek. Document that "stupid" is a non-feature, not a scripted hack. |
| Slower shamble | Move speed and action speed are different surfaces; `HumanAIComponent.GetDesiredSpeedInFormation`/`AdjustSpeedLimit` are movement-side (S12). S1's own performance framing is per-agent decisions, not global time. | Use movement-only `agent_set_speed_modifier(2093)` (native, percentage) on team-1 agents, wave-scaled from a base around 50–65% (start low, raise per wave), **not** `mission_set_time_speed`; only use WSE2 `agent_set_time_speed_multiplier(3335)` if we explicitly want attacks/reloads slowed too, and never 0%. Keep attack cadence normal so they stay threatening. |
| Wave-scaled speed | Tactic/formation scale by situation, not by global time (S1). | Speed multiplier = f(wave) with a hard floor and a cap; expose the applied value to C so speed can be proven per wave instead of inferred. |
| Verification | Bannerlord exposes formation/agent state for its own AI (S9, S11). | C must report effective team-1 speed/readback, forward displacement per interval, and any agent whose movement is away from the survivor mass (retreat samples). D validates. |

Caveat **[unverified]**: whether Warband MP invasion bots can even enter a native flee state. If they can, telemetry will show backward displacement without an order; then the WSE2 simple-behavior pin becomes mandatory rather than optional.

### 6.2 Survivors: formation cohesion, ranged behind, melee screen, adaptive outnumbered

Bannerlord's model gives four transferable rules:

1. **One intent owner, many executors.** Formation AI issues the same orders the player can (S1); individual AI interprets them (S8). For us: the overlay decides the survivor mode/anchor per division; the engine/native AI executes. No per-agent destination spam.
2. **Separate order channels.** Movement, firing and arrangement are independent (S9). For us: anchor/hold is a movement order, fire discipline is a fire order, and "ranged behind / melee screen" is a **placement + division-role** decision, not a weapon-force loop.
3. **Decide from group summaries.** Bannerlord's formation AI consumes power, closest-enemy and under-attack summaries (S9). For us: one bounded per-tick summary (survivor centroid, spread, enemy count/distance bands, ammo state) feeding a small mode choice.
4. **Stickiness/hysteresis.** `BehaviorCoherence` and `PreserveExpireTime` (S8) exist because otherwise formations oscillate. Our fallback/regroup already needs a mode global (`zdr_defence_mode`) for this reason; formalise it as a mode with minimum dwell time.

Concrete mapping:

- **Formation / cohesion:** divisions 5–7 adopt survivors into roles; anchor = rear survivor entry; per-division offset (screen closer to the enemy approach, ranged behind the screen, reserve behind ranged). Cohesion is measured, not assumed: centroid distance / max spread; if a survivor exceeds the leash radius, the fix is a **team order** re-issue (or a `mordr_fall_back` to the anchor), not an individual scripted path.
- **Ranged behind / melee screen:** role = division; ranged division keeps `mordr_use_ranged_weapons(16)` + `mordr_fire_at_will(13)` + WSE2 `agent_ai_set_can_weapon_switch(agent, 0)` (3343) for the ranged agents; screen division holds at a forward offset with melee fallback allowed only at close range. Ensure the screen actually sits between the ranged line and the zombie mass — verifiable from positions telemetry, not from orders alone.
- **Adaptive outnumbered/advantage:** compute a bounded ratio (nearby enemies vs effective survivors) and choose one of `HOLD_FIRE`, `FALLBACK_TO_ANCHOR`, `REGROUP`, `LIMITED_ADVANCE` with dwell + hysteresis. Outnumbered → hold tight/fallback to base; local superiority + low ammo → allow bounded advance, never a chase. This is the Bannerlord "formation may deviate from the plan when there is an urgent reason, then return to the plan" idea (S1), scaled down to a 4-state machine with explicit thresholds.
- **Fall back to base:** use `mordr_fall_back(6)` toward the base anchor entry, and only after arrival re-issue hold/fire. Keep "fallback" distinct from "retreat/rout": survivors never leave the field by AI decision.
- **Survivor reinforcement / accumulation:** Bannerlord's reserve model (initial vs total, reinforcements, `IsSideDepleted`) is the model for "more survivors accumulate as waves are won": explicit reserve pool, per-round refill cadence, cap, and **arrival events** so the owner sees reinforcements arriving (§6.3).
- **One melee weapon + doubled ammo (task-46):** loadout is data, not AI. Bannerlord's `GetTraitsMask`/weapon state shows equipment matters as *available capability* (S11); keep the loadout change and let telemetry prove weapon/ammo transitions instead of forcing switches every tick.

### 6.3 Wave end and arrival clarity

Our complaint (owner: waves keep coming, no survivors arriving, no clear wave end) maps directly onto Bannerlord's explicit spawn-state model (S14):

| Bannerlord concept | What it gives the player/debugger | Our equivalent |
| --- | --- | --- |
| `attackerTotalSpawn` vs `attackerInitialSpawn` | "this wave is 32, 8 arrive now, 24 later" | per-wave configured count vs spawned-so-far globals |
| `NumberOfRemainingTroops` / `IsSideDepleted` | progress and cleared state | survivors/enemies remaining before next transition |
| `OnInitialTroopsSpawned` / `OnReinforcementsSpawned` events | explicit events for log/UI | C recorder events `wave_spawned`, `wave_cleared`, `next_wave` |
| `GetReinforcementInterval` | "next batch in N s" | rotation field + telemetry `next_wave_eta` |
| `OnPhaseChangedDelegate` / `AddPhaseChangeAction` | phase-transition hook | A's wave state machine transitions (PREP/SPAWN/ACTIVE/CLEARED/INTERMISSION) |
| `MissionAgentPanicHandler` | panic is a plugin | no panic for zombies; feedback layer separate |

Concrete direction: define wave state **once** (A), expose it (C), and make the transitions *observable* — a game message/console line and a recorder event on `wave_cleared` and `wave_started`, with survivor arrival counted and announced. Today's build has counters but not a phase owner, so "wave end" and "survivors arriving" are judged by inference. No Bannerlord code required — this is an information-model adoption.

### 6.4 Male/female distribution

- Bannerlord: `is_female` is data on `NPCCharacter`; composition is a spawn/roster decision (S16). There is no AI-gender behaviour.
- Our equivalent: survivor classes are clone troops; gender is a property of the troop entry (Warband module data), not settable by an op. So the only robust route is **explicit male/female troop variants per class + a weighted, deterministic selection table**, and then telemetry that counts realised variants by troop id.
- Practical target: balanced enough to be visible (e.g. 40–60% per class over a round, not necessarily per spawn), deterministic per wave seed so D can reproduce, and never silently all-male via a default branch.
- **[unverified]**: Warband's exact gender field/face-key mechanism and whether existing clone troops can be gendered without new troop entries; A/E must confirm before claiming the distribution is implemented. C must not derive gender from face/name telemetry — only from a documented troop-id map.

---

## 7. Adopt / Adapt / Avoid

| Decision | Item | Why | Owner |
| --- | --- | --- | --- |
| **Adopt** | Three-layer separation: one tactic/intent owner → formation/division orders → individual execution | Proven structure; matches what Warband/WSE2 can actually control | A |
| **Adopt** | Orders are the only formation-intent mechanism; no per-agent pathing for group behaviour | Bannerlord's own individual AI interprets orders; our community evidence shows scripted destination breaks formations | A |
| **Adopt** | Weighted behaviour selection with stickiness (`BehaviorCoherence`, `PreserveExpireTime` concept) | Prevents oscillating hold/fallback thrash better than raw thresholds | A, C |
| **Adopt** | Explicit spawn/phase state model (initial vs total, remaining, phase events, side depleted) | Fixes wave-end/arrival clarity without new engine features | A, C, D |
| **Adopt** | Panic/retreat as an input subsystem that can be removed/not configured | Directly answers "zombies must never retreat" at the right layer | A |
| **Adopt** | Data-driven composition (gender/class/role as data, not AI) | Only mechanism Warband can express; matches Bannerlord's XML design | A, E |
| **Adapt** | Bounded morale shock radius (max 10 casualties, shield-wall mitigation, kill boost) | Useful as a *survivor cohesion shock* for fallback triggers, capped and recoverable; do not import a rout chain reaction | A |
| **Adapt** | Strategic retreat (commander success estimate) | Re-express as survivor "fall back to base" threshold, never full retreat | A |
| **Adapt** | Formation classes → division roles; class counts → role counts | Warband has divisions + `agent_set_division`, not arrangement API | A |
| **Adapt** | Formation power/under-attack summaries | Compute a bounded centroid/enemy-distance/ammo summary in the 5 s trigger; no per-agent polling | A, C |
| **Avoid** | Literal behaviour-tree tooling / expecting a BTC surface | Not on the documented Bannerlord surface either; we'd be building tooling for an abstraction that doesn't match either engine | all |
| **Avoid** | Per-agent scripted destination for group movement | Documented formation-breaking pitfall; order layer already exists | A |
| **Avoid** | Global `mission_set_time_speed` as a "slow zombies" tool | Slows the whole battle/clock and corrupts telemetry cadence; use per-agent movement modifier | A |
| **Avoid** | Forcing weapons every tick; toggling shields/equipment as a behaviour substitute | Flicker/one-frame seizures documented in our Warband reference; Bannerlord separates equipment capability from order intent | A |
| **Avoid** | Copying Bannerlord code/assemblies/assets/decompiled logic | EULA §1.3(i)/§2.3 (S18); project policy | all |
| **Avoid** | Implementing a rout/panic chain for zombies or survivors | Turns a balance bug into an unrecoverable loop; owner explicitly wants zombies non-retreating and survivors holding | A |

---

## 8. Concrete implications by lane

### A — behaviour/build (`tools/city_defense.py`, `tools/city_behavior.py`, `tools/build.py`, `tests/test_city_*.py`)

1. **Make the survivor controller a 4-mode intent machine with dwell/hysteresis** (`HOLD_FIRE`, `FALLBACK_TO_ANCHOR`, `REGROUP`, `LIMITED_ADVANCE`), driven by one bounded summary (centroid/spread, enemy distance bands/counts, ammo state, wave number). Keep intent at division level: anchor + `mordr_hold/fire_at_will/use_ranged_weapons` on the 5 s cadence. No per-agent movement destinations.
2. **Role-encode the divisions:** screen (forward offset, melee fallback allowed only close), ranged (rear offset, `can_weapon_switch=0` per agent, hold fire discipline), reserve (behind, fills gaps). Cohesion/leash radius enforced by re-issuing the order or a single `mordr_fall_back` to the anchor — never by scripting each agent.
3. **Zombie intent is charge-only:** never issue hold/fallback/stand-ground to team 1; never adopt team-1 agents into defensive divisions; keep aggressiveness high; if telemetry shows drift, pin WSE2 `agent_ai_set_simple_behavior` (melee/charge) with a bounded guarantee. Keep the movement speed on `agent_set_speed_modifier` (movement only), lower base (~50–65%), wave-scaled with floor/cap; do not slow attacks unless D reports the shamble looks wrong.
4. **Define wave state once:** PREP → SPAWN → ACTIVE → CLEARED → INTERMISSION with explicit globals, a wave-end predicate that includes alive team 1 **and** the spawn/visitor gate, and a next-wave delay. Emit/announce transitions; spawn survivor arrivals at the transition with an explicit count (cap 12) rather than silently topping up.
5. **Gender mix as data:** male/female survivor variants per class + weighted deterministic selection per wave (seed = wave/round); no "all male" default branch. Confirm the Warband troop-gender mechanism with E first; document the id→variant table for C.
6. **Telemetry contract first:** implement the globals/events C needs (wave phase, spawned/remaining, arrival counts, mode, anchor, applied speed) before tuning thresholds; otherwise balance changes are untestable.

### C — telemetry/summary (`overlay/lua/main.lua`, `tools/diagnostics.py`, tests/docs)

Minimum new/changed evidence (all bounded, absent-not-zero):

1. **Wave model:** `wave_phase`, `wave_number`, `wave_initial_total`, `wave_spawned`, `wave_remaining`, `wave_cleared` event, `next_wave_eta`, `round_start`; distinct `game_type` vs mode (already required by earlier tasks).
2. **Arrivals:** `survivor_arrivals` count + event per transition, `survivors_team0` vs cap, so "no survivors arriving" is measurable, not a feeling.
3. **Retreat detection (team 1):** per-interval displacement sign relative to survivor centroid (or distance growth to survivor mass) with a documented threshold; `retreat_samples_team1`; distinguish "not moving" from "moving away".
4. **Speed evidence:** effective team-1 movement rate and, if a getter exists, the applied speed modifier (readback is currently suspect — keep `-1/unknown` semantics and a capability flag rather than reporting 100 as fact).
5. **Cohesion/roles:** survivor centroid + spread, per-division mean distance to anchor, screen-vs-ranged relative distance to enemy mass, `mode` and `mode_dwell_s`.
6. **Ranged discipline:** weapon/ammo state per defender sample (`ranged_agents_team0`, `melee_fallback_team0`, weapon modes, ammo zero/positive), so "kept shooting" is provable.
7. **Gender mix:** only from documented troop-id map; `gender_hist_team0` with explicit `gender_map_unknown` when the map is absent. Never infer from names/faces.
8. **Summary:** add a "wave/arrival clarity" and "zombie approach" block to `tools/diagnostics.py summary`, with explicit gaps for anything unreadable; fail closed on tampering as today.

### D — sealed validation (`local/session`, launcher)

Proposed sealed matrix (each run separately sealed; no acceptance claim; exact counts from C):

1. **Zombie non-retreat + shamble:** sealed run with team1 waves only. Require: zero/negligible retreat samples, monotonically approaching displacement, effective speed at or below the configured cap, no team-1 hold/fallback observed in movement, team-1 troop ids still in the slow family (no 896 leak).
2. **Survivor hold/fire + roles:** rear hold, ranged agents retain weapons and shoot, screen sits forward of ranged, cohesion within leash, fallback triggers only under outnumbered pressure and recovers to hold.
3. **Wave end / arrival clarity:** observe at least one full transition: wave N cleared predicate → intermission → wave N+1 spawn; survivor arrivals counted; announcements/events visible in the sealed bundle; no "wave 0 forever while enemies exist".
4. **Gender mix:** realised male/female variant ratio over a round within the documented band (only if A's variant table exists); otherwise record `gender_map_unknown` and do not claim.
5. **Balance regression:** KD and wave-2 reachability against the task-38/42 baselines, using C's new fields; report gaps honestly.
6. Keep `runtime_verified=false` and `hold_behavior_observed`/`no_retreat_observed` false until the sealed fields actually show them.

---

## 9. Open questions / unverified list

1. **"Behaviour tree"**: not found in any official source read; Bannerlord's documented battlefield AI is weighted behaviour components + parameterised per-agent behaviour. Treat BT as an external metaphor unless someone cites official material. **[unverified]**
2. **Target-selection formula**: not published. We only know the two-level shape and override hooks. **[unverified]**
3. **Tactic-layer API**: described narratively (S1/S3) but no class page was read. **[unverified]**
4. **Bannerlord MP morale/panic semantics**: dev blogs describe SP battles; the MP sample includes `MissionAgentPanicHandler` but its exact behaviour in invasion-like modes is not documented. **[unverified]**
5. **Version drift**: docs mix v1.4.7 (most) and v1.3.14 (`MissionAgentSpawnLogic`); behaviour sets/names can change between versions. Cite versions, not "Bannerlord" generically.
6. **Warband-side gender mechanism and native flee**: not verified from original data/engine; A/E must confirm before claims, C must not infer.
7. **Warband order/readback limits**: whether team-1 orders and per-agent behaviour pins are readable/observable; C has previously marked order readback gaps — keep them explicit.
8. **Live `taleworlds.com`/Steam EULA base-game access**: blog pages 403 (Wayback used); base-game EULA failed to render. Recorded, not used.

---

## 10. Handoff notes

- This file is the only deliverable; **no build/tool/game change is implied or made**.
- Suggested use: A folds §6.1–§6.4 and §8-A into the task-53/54 behavior contract; C folds §6.3/§6.4 and §8-C into the telemetry contract; D uses §8-D as the sealed matrix. The Lead may decide whether to cite this file in `docs/` or the ledger — H lane does not edit the ledger.
- Cross-review requested from **C or A** per the task; findings should be recorded as comments in this file's review thread/PR, not silently accepted.
- No Bannerlord asset, code, assembly, XML data file or decompiled output is included or needed by this document.

*End of research document.*
