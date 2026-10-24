# City combat regressions - 2026-10-24 (task-30)

**Agent A fixes for the owner's live run (`local/session/play-city/flights/891af9e0...`). Static/offline only; D validates in game.**

## (a) Defenders charging instead of shooting

Cause: the City 5 s adoption trigger set `agent_set_scripted_destination` on every
team-0 bot, which overrode combat aiming. Fix: removed that per-agent scripted
destination entirely. The trigger keeps `agent_set_division` / `agent_set_group`
and the team hold orders; it must not move agents individually. Defenders' native
AI (including firearms/ammo from the balanced loadouts) is left in control.

Tradeoff: guard-post hold stability is weaker without scripted destinations; that
is intentional - playable combat wins over a telemetry hold claim (DISC-28 was
already unproven/active).

## (b) Mutated/Steroid Zombies and mounted units in wave 1

City generic invader bots previously selected the full native block 894..911
(Zombie/Tough/Fast/Cop/Steroid/Mutated/Witchy/...). New build profile
`--zombie-bot-roster weak` (default) restricts generic team-2 bots to the weak
block **894 only** (Zombie/Tough/Fast/Cop); `--zombie-bot-roster full` restores
894..911. Receipt records `invader_troop_range` and `zombie_bot_roster`.
Residual: the original native wave visitors are outside this selector; if the
engine's wave 1 still spawns special/mounted visitors, that needs a separate
City-only wave-spawn patch (not done here) or rotation `--enemy-profile native-only`.

## (c) Zombies have 0 block

Compiled invader troops already carry a high shield skill but no shield item.
New `--zombie-block default` (on) appends `itm_wooden_shield` (item id 493) to the
first unused equipment pair of native invader troops **894..911 only**; all other
troop rows are byte-identical. `--zombie-block stock` disables. Receipt records
`zombie_block.shield_item`, troop list and SHA-256. Runtime confirmation that the
engine equips/blocks with the shield is D's sealed run.

## Validation

- Offline: full suite 514 OK / 7 skips; build receipt shows invader range
  [894,898], 4 weak candidates, zombie_block changed_count=18; chain verification
  passes with `troops.txt` as an intentional City change.
- D must validate: defenders fire at range (firearm muzzle/ammo), no melee charge
  from the removed destination override; wave-1 generic bots all in 894 only;
  zombies block with shields and survive better; receipts keep
  `runtime_verified=false`.
- No gameplay/release acceptance; required City outcomes stay 0/23, milestones 0/5.

## Defensive rear line (follow-up, owner live feedback)

The remaining forward movement came from the team hold orders: the old sectors
(entries 2/3/4) sit forward of the spawn line, so `mordr_hold` still walked the
squad into the wave even without scripted destinations. Default City builds now
hold the **rear/spawn line** (`REAR_HOLD_ENTRIES = (0,1,0)`, survivor entries
0/1) every 5 s with no forward sector rotation and no scripted destination.
`--defensive-line forward` restores the old guard sectors; the build receipt
records `experimental_city_guardposts.hold_entries` and `defensive_line`.

Launcher defender squad default increased from 4 to **8** native team-0 bots
(`DEFENDER_SQUAD_BOTS = 8`) so the line has bodies and native bot refill keeps
replacing losses; the City build still appends four clone troop types (981..984).
Expected D evidence: team0 centroid stays near the spawn/rear line instead of
moving toward the enemy, defenders fire (ammo decreasing, ranged weapon modes),
and the squad survives longer / trades better; report exact positions and KD,
with `runtime_verified=false` and no acceptance claim.

## Standoff/fire discipline - task-42 (after task-38)

- Survivor AI: existing rear hold + hold/fire/ranged team orders, plus per-bot
  ammo-gated **WSE2** safety: `agent_ai_set_can_weapon_switch(agent, 0)` keeps the
  firearm while `agent_get_ammo > 0`; the native melee switch is only allowed when
  the magazine is empty (knife/melee last resort). `agent_ai_set_simple_behavior(
  aisb_hold, 6 s)` keeps formation behaviour without any scripted destination.
- Explosive classes: the balanced AI clone loadouts contain **no bomb/grenade
  items** (only guns, cartridges and, for the lumberjack, a bowie knife), so there
  is no AI throwable to gate by cluster density. Bomb gating is therefore not
  applicable to AI survivors; it remains a player-equipment design decision, not
  a mission-trigger rule. Receipt records
  `explosive_gating=not_applicable_ai_loadouts_have_no_bombs`.
- Zombie pace/slow visitors/rear line are unchanged from task-38; the intent is
  that survivors shoot the slowed wave before it reaches the line. Runtime
  distance/KD/ammo evidence is D's sealed validation; no acceptance claim.

## Task-45 balance after sealed task-38/42 evidence

Sealed runs showed 72/72 ranged, rear hold and refill working, but KD 4-6 kills
vs 49-52 deaths, zombies outmoving defenders, and wave 2 never reached. Fixes:
- remove `mordr_hold_fire` from the per-group order set (hold + fire_at_will +
  use_ranged_weapons only) so defenders actually engage;
- zombie speed base 70% -> **60%** at wave 0/1 (+5%/wave, cap 100%);
- launcher generic enemy default 32 -> **24** generic bots (`DEFAULT_TEAM2_BOTS`);
  weak-wave1/native-only profiles unchanged.
D validates KD, wave-2 reachability (894-only) and the ammo/melee branch with a
no-refill variant; no acceptance claim.

## Task-46 survivor consolidation (after task-45 balance)

- Exactly one melee weapon per AI survivor: all four clone loadouts carry itm_bowie (and no other melee item).
- Double ammunition: each clone carries eight matching cartridge stacks (was four).
- Survivors accumulate per won round: a bounded invader-faction slot counter (slot 250, previous round-ended slot 252) increments on a real round-end -> new-round transition; the spawn_agent refill target = 8 + wins, capped 12. Rear hold and refill remain.
- Explicit Invasion path: the City hold/order trigger now also requires $g_multiplayer_game_type == 7, so it cannot act in other multiplayer modes; receipt records game_type=7.
- Task-45 balance retained: fire_at_will/use_ranged orders (no hold_fire), 60%% wave-1 zombie base pace, 24 generic bots default. D validates KD/wave-2/ammo; no acceptance.

