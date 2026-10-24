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

