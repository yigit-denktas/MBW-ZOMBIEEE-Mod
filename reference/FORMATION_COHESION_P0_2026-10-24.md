# Formation/cohesion + class roles on the P0 base (task-53/62)

Branch base: `agent/a-p0-native-wave` @ `9b97e15` (P0 trigger-14 894 table; trigger-15 speed loop disabled by default). No `agent_set_scripted_destination` (1730) or per-agent destination path is introduced.

## Implemented (team-order/formation only)

- `--defensive-line adaptive` on `tools/build.py`; receipt `formation_mode=adaptive`, `formation_anchor=entry0_north_base`, `formation_sectors={"5":2,"6":3,"7":4}`, `role_divisions={981:5,982:5,983:6,984:7}`, `target_priority=native_nearest; no public target setter`.
- Class mapping via `agent_get_troop_id(1718)` → division: commando/sniper 5, scout 6, lumberjack 7; `agent_set_division(1783)` + `agent_set_group(1766)` re-applied every 5 s.
- Adaptive policy: count team-0 alive and team-1 alive each tick; **defensive** when round ended (`g_round_ended==1`), team1 > 2×team0, or ≤1 survivor → set all divisions to north base entry 0 and issue `mordr_fall_back(6)`; otherwise hold forward guard posts 2/3/4 and issue `mordr_hold(0)` + `mordr_fire_at_will(13)` + `mordr_use_ranged_weapons(16)`.
- Per-agent WSE2 standoff (ammo-gated weapon switch + `aisb_hold`) retained.
- E map context: zombie entries are three southern clusters (SW/S/SSE), north/rear is the fallback direction; forward posts are 2 centre, 3 east, 4 west. No map/scene edits.
- Between-wave/`round_ended` = pull back to base; advantage/even = forward hold. No true centroid/cohesion-radius math is available without a public position/order readback, so cohesion is a **team-order anchor**, not a proven formation shape.

## Explicitly not implemented / blocked

- **Target priority/special-zombie selection:** no public target setter; receipt says `native_nearest` only. Special-target focus in the class matrix is responsibility, not enforcement.
- **Division/group adoption:** C/H evidence says native bot groups are 26/28/29/31, outside `team_give_order` sub-class 0–9; commands may be no-ops. D must validate addressability before claiming formation behavior.
- **True one-shot vs per-tick:** adaptive orders re-issue every 5 s; per-tick P0 speed remains separate/held.
- **Reticle/class fire modes:** out of scope here (F/H lanes).
- No acceptance; visual plan: D captures spectator/overview start/mid/end + formation images; A reviews before recording any result.

## Verification

Static tests: `tests/test_formation_adaptive.py` (no 1730, class/division ops, forward entries, fallback/fire orders). Build with `--defensive-line adaptive` + receipt; chain remains green for default profiles. D sealed run + visual evidence pending.
