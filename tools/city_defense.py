#!/usr/bin/env python3
"""Optional tactical City overlay after the experimental survivor-spawn patch.

Adds 3 SCO entry points on reachable AI-mesh faces, splits allies into private
groups 5/6/7 and re-issues native hold positions every 5 s *only on City* so the
orders survive dedicated round resets and squad respawns.
No changes to the original 25 invasion triggers or to zombie spawn entries.
"""
from __future__ import annotations
import argparse
import json
from pathlib import Path
from scene_tactics import plan_city, apply_city_overlay, decode_scene
from patch_defenders import mission_bounds, PatchError

SCENE_BASE = 72057594037927936
POS_BASE = 216172782113783808
LOCAL0 = 1224979098644774912
FACTION_BASE = 432345564227567616
TROOP_BASE = 360287970189639680
INVADER_FACTION = FACTION_BASE + 16
SLOW_ZOMBIE = 894
WAVE_TABLE_SLOTS = tuple(range(200, 245))
DEFAULT_DEFENDER_TARGET = 8
DEFENDER_TARGET_CAP = 12
WINS_SLOT = 248          # invader faction slot: completed rounds (bounded)
ROUND_SLOT = 249         # invader faction slot: previous g_round_ended
MISSION_SLOT = 250       # invader faction slot: previous round-start clock
ZOMBIE_SPEED_BASE = 55             # wave 0 55%; wave 1 = 60% (+5/wave)
# City survivor fire modes. AI cycles single -> burst -> auto by wave
# (mode = wave_number % 3); each mode trades accuracy vs reload speed.
FIRE_MODES = (
    {"name": "single", "accuracy": 150, "reload": 120},
    {"name": "burst", "accuracy": 135, "reload": 145},
    {"name": "auto", "accuracy": 115, "reload": 165},
)
ZOMBIE_SPEED_PER_WAVE = 5          # +5% per wave, capped at 100
HOLD_FIRE_ORDERS = (0, 13, 16)  # hold, fire_at_will, use_ranged_weapons (never suppress fire)
defender_reinforce_supported = True
DIVISIONS = (5, 6, 7)
GUARD_ENTRIES = (2, 3, 4)
# Rear/spawn-line hold: entries 0/1 are the survivor spawn points, so the squad
# holds behind the player instead of pushing forward into the zombie wave.
REAR_HOLD_ENTRIES = (0, 1, 0)


def scene_index(path: Path, name="scn_tbfc_invasion_4") -> int:
    lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
    ids = [line.split()[0] for line in lines if line.startswith("scn_")]
    if len(ids) != 560 or ids.count(name) != 1:
        raise PatchError("Unexpected original scenes table")
    return ids.index(name)


def orders_trigger(scene_idx: int, wave_global: int | None = None,
                   hold_entries: tuple[int, ...] = GUARD_ENTRIES,
                   wave_visitors: str = "slow",
                   defender_target: int = DEFAULT_DEFENDER_TARGET,
                   zombie_speed: bool = True,
                   defender_orders: bool = True,
                   game_type_operand: int | None = None,
                   round_ended_operand: int | None = None,
                   round_start_operand: int | None = None,
                   fire_mode: str = "ai") -> str:
    """City hold-order trigger body.

    With ``wave_global`` provided, each wave rotates the three sector posts by
    one step per division using the original ``wave_number`` global (dynamic
    entry numbers 2..4), so the squad re-uses adjacent map sectors instead of
    standing in one spot forever while still holding. The same trigger adopts
    native team-0 bots into divisions 5-7 (division/group writes only). It must
    NOT set agent scripted destinations: that overrode combat aiming in the
    owner's live run, making defenders charge instead of shooting. Without
    ``wave_global`` (unit tests) the original fixed assignments run.
    """
    conditions = ["417", "0", "2211", "1", str(LOCAL0),
                  "31", "2", str(LOCAL0), str(SCENE_BASE + scene_idx)]
    if game_type_operand is not None:
        # Explicit Invasion game_type=7 path: this trigger must not act in
        # unrelated multiplayer modes.
        conditions += ["31", "2", str(game_type_operand), "7"]
    pos = POS_BASE + 120
    ops = []
    if wave_visitors == "slow":
        # City-only wave table override, applied every 5 s after the original
        # trigger 14 has written the table (waves start later). Every wave slot
        # resolves to the original slow Zombie 894 instead of Fast/Tough/etc.
        for slot in WAVE_TABLE_SLOTS:
            ops.append(["502", "3", str(INVADER_FACTION), str(slot),
                        str(TROOP_BASE + SLOW_ZOMBIE)])
    if zombie_speed:
        # City-only zombie pace: native per-agent speed modifier, no gear or
        # global mission time speed. 60% at wave 0/1, +5% per wave, capped 100%.
        l12, l13, l14 = (str(LOCAL0 + n) for n in (12, 13, 14))
        ops.append(["2133", "2", l12, str(ZOMBIE_SPEED_BASE)])
        if wave_global is not None:
            ops.append(["2122", "3", l13, str(wave_global),
                        str(ZOMBIE_SPEED_PER_WAVE)])  # store_mul (2122)
            ops.append(["2120", "3", l12, l12, l13])  # + wave bonus
            ops.append(["4", "0"])                    # cap at 100
            ops.append(["32", "2", l12, "100"])
            ops.append(["2133", "2", l12, "100"])
            ops.append(["3", "0"])
        ops.append(["12", "1", l13])                  # try_for_agents
        ops.append(["1702", "1", l13])                # alive
        ops.append(["1707", "1", l13])                # non-player
        ops.append(["1770", "2", l14, l13])           # team
        ops.append(["31", "2", l14, "1"])             # team 1
        ops.append(["2093", "2", l13, l12])           # agent_set_speed_modifier
        ops.append(["3", "0"])                        # try_end
    if wave_global is None:
        for group, entry in zip(DIVISIONS, hold_entries):
            ops.append(["1780", "2", str(pos), str(entry)])
            ops.append(["1791", "3", "0", str(group), str(pos)])
            ops.append(["1790", "3", "0", str(group), "0"])
    elif adaptive:
        # Adaptive formation/cohesion (task-53/62): no scripted destinations.
        # Hold the three forward guard posts (E map: 2 centre, 3 east, 4 west)
        # while the squad is not outnumbered; otherwise pull the whole team back
        # to the north base entry (0) and issue a fall-back order. Roles are
        # divisions: commando/sniper 5, scout 6, lumberjack 7. Target priority
        # remains engine/native (no public setter) and is receipt metadata only.
        l0, l1, l2, l3 = (str(LOCAL0 + n) for n in (0, 1, 2, 3))
        l4, l5, l6, l7 = (str(LOCAL0 + n) for n in (4, 5, 6, 7))
        l8, l9, l10, l11 = (str(LOCAL0 + n) for n in (8, 9, 10, 11))
        # Count/adopt team-0 bots by class.
        ops.append(["2133", "2", l0, "0"])
        ops.append(["12", "1", l1])
        ops.append(["1702", "1", l1])
        ops.append(["1707", "1", l1])
        ops.append(["1770", "2", l2, l1])
        ops.append(["31", "2", l2, "0"])
        ops.append(["1718", "2", l4, l1])
        ops.append(["4", "0"])
        ops.append(["31", "2", l4, "984"])
        ops.append(["2133", "2", l3, "7"])
        ops.append(["5", "0"])
        ops.append(["31", "2", l4, "983"])
        ops.append(["2133", "2", l3, "6"])
        ops.append(["5", "0"])
        ops.append(["2133", "2", l3, "5"])
        ops.append(["3", "0"])
        ops.append(["1783", "2", l1, l3])
        ops.append(["1766", "2", l1, l3])
        if defender_orders:
            l5 = str(LOCAL0 + 5)
            ops.append(["1727", "3", l5, l1, "0"])
            ops.append(["4", "0"])
            ops.append(["31", "2", l5, "0"])
            ops.append(["3343", "2", l1, "1"])
            ops.append(["5", "0"])
            ops.append(["3343", "2", l1, "0"])
            ops.append(["3", "0"])
            ops.append(["3314", "3", l1, "0", "6"])
        ops.append(["2120", "3", l0, l0, "1"])
        ops.append(["3", "0"])
        # Count team-1 agents (pressure, not distance yet).
        ops.append(["2133", "2", l6, "0"])
        ops.append(["12", "1", l7])
        ops.append(["1702", "1", l7])
        ops.append(["1707", "1", l7])
        ops.append(["1770", "2", l8, l7])
        ops.append(["31", "2", l8, "1"])
        ops.append(["2120", "3", l6, l6, "1"])
        ops.append(["3", "0"])
        # Defensive mode: round ended, or team1 > 2*team0, or <=1 survivor.
        ops.append(["2133", "2", l9, "0"])
        if round_ended_operand is not None:
            ops.append(["2133", "2", l10, str(round_ended_operand)])
            ops.append(["4", "0"])
            ops.append(["31", "2", l10, "1"])
            ops.append(["2133", "2", l9, "1"])
            ops.append(["3", "0"])
        ops.append(["2120", "3", l10, l0, "2"])
        ops.append(["4", "0"])
        ops.append(["32", "2", l6, l10])
        ops.append(["2133", "2", l9, "1"])
        ops.append(["3", "0"])
        ops.append(["4", "0"])
        ops.append(["30", "2", l0, "1"])
        ops.append(["2133", "2", l9, "1"])
        ops.append(["3", "0"])
        if defender_orders:
            for index, group in enumerate(DIVISIONS):
                normal_entry = GUARD_ENTRIES[index]
                ops.append(["4", "0"])
                ops.append(["31", "2", l9, "1"])
                ops.append(["2133", "2", l11, "0"])       # defensive base
                ops.append(["5", "0"])
                ops.append(["2133", "2", l11, str(normal_entry)])
                ops.append(["3", "0"])
                ops.append(["1780", "2", str(pos), l11])
                ops.append(["1791", "3", "0", str(group), str(pos)])
                ops.append(["4", "0"])
                ops.append(["31", "2", l9, "1"])
                ops.append(["1790", "3", "0", str(group), "6"])  # fall back to base
                ops.append(["5", "0"])
                ops.append(["1790", "3", "0", str(group), "0"])  # hold forward
                ops.append(["3", "0"])
                ops.append(["1790", "3", "0", str(group), "13"])  # fire at will
                ops.append(["1790", "3", "0", str(group), "16"])  # use ranged
    elif tuple(hold_entries) == REAR_HOLD_ENTRIES:
        # Defensive line: adopt native team-0 bots into divisions 5-7, then hold
        # the rear/spawn entry positions every 5 s. No scripted destination and
        # no forward sector rotation.
        l0, l1, l2, l3 = (str(LOCAL0 + n) for n in (0, 1, 2, 3))
        ops.append(["2133", "2", l0, "0"])                 # count = 0
        ops.append(["12", "1", l1])                        # try_for_agents
        ops.append(["1702", "1", l1])                      # agent_is_alive
        ops.append(["1707", "1", l1])                      # non-player
        ops.append(["1770", "2", l2, l1])                  # agent_get_team
        ops.append(["31", "2", l2, "0"])                   # team 0
        ops.append(["2119", "3", l3, l0, "3"])             # count % 3
        ops.append(["2120", "3", l3, l3, "5"])             # division 5..7
        ops.append(["1783", "2", l1, l3])                  # agent_set_division
        ops.append(["1766", "2", l1, l3])                  # agent_set_group
        if defender_orders:
            # team_give_order/team_set_order_position only accept grc sub-classes
            # 0..9; native bot groups (26/28/29/31) are not valid sub-classes.
            # Use the computed division 5..7, which is inside the class space.
            ops.append(["1780", "2", str(pos), "0"])       # rear entry position
            ops.append(["1791", "3", "0", l3, str(pos)])   # team_set_order_position
            for order in HOLD_FIRE_ORDERS:
                ops.append(["1790", "3", "0", l3, str(order)])
            # Ranged standoff: keep the firearm while any usable ammo remains;
            # only allow the native melee weapon switch when all spare ammo is
            # exhausted (knife/melee is a last resort). agent_get_ammo(...,0)
            # means all carried ammo, not just the current magazine. WSE2 hold
            # behavior keeps the
            # formation from chasing, without any scripted destination.
            l5 = str(LOCAL0 + 5)
            ops.append(["1727", "3", l5, l1, "0"])         # agent_get_ammo
            ops.append(["4", "0"])                          # try_begin
            ops.append(["31", "2", l5, "0"])                # ammo == 0
            ops.append(["3343", "2", l1, "1"])              # allow switch (last resort)
            ops.append(["5", "0"])                          # else_try
            ops.append(["3343", "2", l1, "0"])              # keep ranged weapon
            ops.append(["3", "0"])                          # try_end
            ops.append(["3314", "3", l1, "0", "6"])         # WSE2 hold behavior
            # WSE2 fire-mode modifiers: faster cadence + tighter aim. The AI
            # picks single/burst/auto from the wave index; same target as the
            # native accuracy field, but applied per agent so it works with the
            # 2012 crossbow-style firearms. Preserve ammo/loadout.
            l6 = str(LOCAL0 + 6)
            if fire_mode == "ai" and wave_global is not None:
                ops.append(["2119", "3", l6, str(wave_global), "3"])
                ops.append(["4", "0"])                  # try_begin
                ops.append(["31", "2", l6, "0"])
                ops.append(["2092", "2", l1, str(FIRE_MODES[0]["accuracy"])])
                ops.append(["2094", "2", l1, str(FIRE_MODES[0]["reload"])])
                ops.append(["5", "0"])                  # else_try
                ops.append(["31", "2", l6, "1"])
                ops.append(["2092", "2", l1, str(FIRE_MODES[1]["accuracy"])])
                ops.append(["2094", "2", l1, str(FIRE_MODES[1]["reload"])])
                ops.append(["5", "0"])                  # else_try
                ops.append(["2092", "2", l1, str(FIRE_MODES[2]["accuracy"])])
                ops.append(["2094", "2", l1, str(FIRE_MODES[2]["reload"])])
                ops.append(["3", "0"])                  # try_end
            else:
                selected = {"single": FIRE_MODES[0], "burst": FIRE_MODES[1],
                            "auto": FIRE_MODES[2]}[
                                "burst" if fire_mode == "ai" else fire_mode]
                ops.append(["2092", "2", l1, str(selected["accuracy"])])
                ops.append(["2094", "2", l1, str(selected["reload"])])
        ops.append(["2120", "3", l0, l0, "1"])             # count += 1
        ops.append(["3", "0"])                             # try_end
        if defender_target:
            l6, l7, l12, l13 = (str(LOCAL0 + n) for n in (6, 7, 12, 13))
            l14 = str(LOCAL0 + 14)
            l8, l9, l10, l11 = (str(LOCAL0 + n) for n in (8, 9, 10, 11))
            # Rounds survived accumulate a bounded survivor target: 8 base,
            # +1 per completed round, cap 12. State lives in invader faction slots
            # so it persists across native round resets without new globals.
            if round_ended_operand is not None:
                ops.append(["522", "3", l6, str(INVADER_FACTION), str(WINS_SLOT)])
                ops.append(["522", "3", l7, str(INVADER_FACTION), str(ROUND_SLOT)])
                ops.append(["522", "3", l14, str(INVADER_FACTION), str(MISSION_SLOT)])
                ops.append(["2133", "2", l12, str(round_ended_operand)])
                if round_start_operand is not None:
                    ops.append(["2133", "2", l13, str(round_start_operand)])
                    # A clock going backwards means a new mission/rotation: reset.
                    ops.append(["4", "0"])                # try_begin
                    ops.append(["32", "2", l14, l13])     # old start > new start
                    ops.append(["2133", "2", l6, "0"])    # wins = 0
                    ops.append(["3", "0"])                # try_end
                ops.append(["4", "0"])                    # try_begin
                ops.append(["31", "2", l7, "1"])           # previous round ended
                ops.append(["31", "2", l12, "0"])          # new round started
                ops.append(["2120", "3", l6, l6, "1"])     # completed rounds += 1
                ops.append(["3", "0"])                    # try_end
                if round_start_operand is not None:
                    ops.append(["502", "3", str(INVADER_FACTION),
                                str(MISSION_SLOT), l13])   # stamp this mission clock
                ops.append(["4", "0"])                    # cap rounds
                ops.append(["32", "2", l6, "4"])
                ops.append(["2133", "2", l6, "4"])
                ops.append(["3", "0"])
                ops.append(["502", "3", str(INVADER_FACTION), str(WINS_SLOT), l6])
                ops.append(["502", "3", str(INVADER_FACTION), str(ROUND_SLOT), l12])
                # --defender-target is the base; each completed round adds one,
                # capped at DEFENDER_TARGET_CAP (never hard-coded 8).
                ops.append(["2120", "3", l13, str(defender_target), l6])
                ops.append(["4", "0"])
                ops.append(["32", "2", l13, str(DEFENDER_TARGET_CAP)])
                ops.append(["2133", "2", l13, str(DEFENDER_TARGET_CAP)])
                ops.append(["3", "0"])
            else:
                ops.append(["2133", "2", l13, str(defender_target)])
            ops.append(["2121", "3", l9, l13, l0])          # missing = target - count
            ops.append(["32", "2", l9, "0"])
            ops.append(["4", "0"])                          # try_begin
            ops.append(["1780", "2", str(pos), "0"])        # spawn at rear entry
            ops.append(["1970", "1", str(pos)])             # set_spawn_position
            ops.append(["6", "3", l10, "0", l9])            # try_for_range
            ops.append(["2119", "3", l11, l10, "4"])
            ops.append(["2120", "3", l11, l11, "981"])      # clone troops 981..984
            ops.append(["1972", "1", l11])                  # spawn_agent
            ops.append(["3", "0"])                          # try_end
            ops.append(["3", "0"])                          # try_end (if missing)
        for group, entry in zip(DIVISIONS, hold_entries):
            ops.append(["1780", "2", str(pos), str(entry)])
            ops.append(["1791", "3", "0", str(group), str(pos)])
            ops.append(["1790", "3", "0", str(group), "0"])  # mordr_hold
    else:
        # Native team-0 bots (proven engine spawn path; team-0 add_visitors
        # produced no allies in D's sealed run) are adopted into the reserved
        # divisions 5-7 round-robin before the sector orders are issued.
        l0, l1, l2, l3 = (str(LOCAL0 + n) for n in (0, 1, 2, 3))
        l5, l6, l7 = (str(LOCAL0 + n) for n in (5, 6, 7))
        # Sector rotation parity is computed once and shared by the team orders.
        ops.append(["2119", "3", l5, str(wave_global), "2"])  # store_mod parity
        ops.append(["2133", "2", l0, "0"])                 # count = 0
        ops.append(["12", "1", l1])                        # try_for_agents
        ops.append(["1702", "1", l1])                      # agent_is_alive
        ops.append(["1707", "1", l1])                      # non-player
        ops.append(["1770", "2", l2, l1])                  # agent_get_team
        ops.append(["31", "2", l2, "0"])                   # team 0
        ops.append(["2119", "3", l3, l0, "3"])             # count % 3
        ops.append(["2120", "3", l3, l3, "5"])             # division 5..7
        ops.append(["1783", "2", l1, l3])                  # agent_set_division
        ops.append(["1766", "2", l1, l3])                  # agent_set_group (order sub_class)
        ops.append(["2120", "3", l0, l0, "1"])             # count += 1
        ops.append(["3", "0"])                             # try_end
        if defender_target:
            l8, l9, l10, l11 = (str(LOCAL0 + n) for n in (8, 9, 10, 11))
            ops.append(["2133", "2", l8, str(defender_target)])
            ops.append(["2121", "3", l9, l8, l0])
            ops.append(["32", "2", l9, "0"])
            ops.append(["4", "0"])
            ops.append(["1780", "2", str(pos), "0"])
            ops.append(["1970", "1", str(pos)])
            ops.append(["6", "3", l10, "0", l9])
            ops.append(["2119", "3", l11, l10, "4"])
            ops.append(["2120", "3", l11, l11, "981"]);
            ops.append(["1972", "1", l11])
            ops.append(["3", "0"])
            ops.append(["3", "0"])
        for group in DIVISIONS:
            ops.append(["2121", "3", l6, str(group), "5"])  # division - 5
            ops.append(["2120", "3", l7, l6, l5])           # + parity
            ops.append(["2119", "3", l7, l7, "3"])          # % 3 sectors
            ops.append(["2120", "3", l7, l7, "2"])          # + first guard entry
            ops.append(["1780", "2", str(pos), l7])         # dynamic entry position
            ops.append(["1791", "3", "0", str(group), str(pos)])
            ops.append(["1790", "3", "0", str(group), "0"])  # mordr_hold
    tokens = [token for row in ops for token in row]
    # Periodic 5 s upkeep: re-issues hold positions after dedicated round
    # resets / squad respawns and re-selects the sector on each new wave.
    condition_count = 4 if game_type_operand is not None else 3
    return " ".join(["5.000000", "0.000000", "0.000000",
                     str(condition_count), *conditions, str(len(ops)), *tokens])


def patch_orders(original: str, scene_idx: int,
                 wave_global: int | None = None,
                 hold_entries: tuple[int, ...] = GUARD_ENTRIES,
                 wave_visitors: str = "slow",
                 defender_target: int = DEFAULT_DEFENDER_TARGET,
                 zombie_speed: bool = True,
                 defender_orders: bool = True,
                 game_type_operand: int | None = None,
                 round_ended_operand: int | None = None,
                 round_start_operand: int | None = None,
                 fire_mode: str = "ai") -> str:
    lines = original.splitlines(keepends=True)
    count_line, count, insert_at = mission_bounds(lines)
    if count != 26:
        raise PatchError("City tactics require the opt-in 26-trigger defender build")
    tokens = lines[insert_at - 1].split()
    if len(tokens) < 14 or tokens[:3] != [
        "-20.000000", "0.000000", "0.000000"
    ] or tokens[4:6] != ["417", "0"]:
        raise PatchError("Unexpected defender spawn trigger; refusing to modify")
    # Server-only triggers use 1 condition. A City-first trigger contains
    # three: server, current scene, equal to the original City scene ID.
    # Validate both rather than relying on a fixed token offset.
    if tokens[3] == "1":
        count_index = 6
    elif (tokens[3] == "3" and
          tokens[6:9] == ["2211", "1", str(LOCAL0)] and
          tokens[9:13] == ["31", "2", str(LOCAL0),
                          str(SCENE_BASE + scene_idx)]):
        count_index = 13
    else:
        raise PatchError("Unexpected or incorrectly scoped defender conditions")
    amount = int(tokens[count_index])
    first_operation = count_index + 1
    if not 1 <= amount <= 8 or len(tokens) != first_operation + 7 * amount:
        raise PatchError("Malformed defender spawn operations")
    for i in range(amount):
        start = first_operation + 7 * i
        if tokens[start:start + 2] != ["1265", "5"] or tokens[start + 5:start + 7] != ["0", "0"]:
            raise PatchError("Unknown visitor opcode format")
        tokens[start + 6] = str(DIVISIONS[i % len(DIVISIONS)])
    newline = "\r\n" if "\r\n" in original else "\n"
    lines[insert_at - 1] = " ".join(tokens) + newline
    lines[count_line] = "27" + newline
    lines.insert(insert_at, orders_trigger(scene_idx, wave_global, hold_entries,
                                            wave_visitors, defender_target,
                                            zombie_speed, defender_orders,
                                            game_type_operand,
                                            round_ended_operand,
                                            round_start_operand,
                                            fire_mode) + newline)
    updated = "".join(lines)
    if mission_bounds(updated.splitlines(keepends=True))[1] != 27:
        raise PatchError("Invalid tactical trigger count")
    return updated


def apply_module(module: Path, hold_entries: tuple[int, ...] = REAR_HOLD_ENTRIES,
                 wave_visitors: str = "slow",
                 defender_target: int = DEFAULT_DEFENDER_TARGET,
                 zombie_speed: bool = True,
                 defender_orders: bool = True,
                 fire_mode: str = "ai") -> dict:
    module = Path(module)
    scene_path = module / "SceneObj" / "scn_tbfc_invasion_4.sco"
    mission_path = module / "mission_templates.txt"
    original_scene = scene_path.read_bytes()
    original_mission = mission_path.read_bytes().decode("utf-8")
    plan = plan_city(original_scene)
    idx = scene_index(module / "scenes.txt")
    wave_global = None
    game_type_operand = None
    round_ended_operand = None
    round_start_operand = None
    variables_path = module / "variables.txt"
    if variables_path.is_file():
        variables = variables_path.read_text(encoding="utf-8").splitlines()
        if "wave_number" not in variables:
            raise PatchError("Original wave_number global missing for sector rotation")
        wave_global = 144115188075855872 + variables.index("wave_number")
        if "g_multiplayer_game_type" in variables:
            game_type_operand = (144115188075855872
                                 + variables.index("g_multiplayer_game_type"))
        if "g_round_ended" in variables:
            round_ended_operand = (144115188075855872
                                   + variables.index("g_round_ended"))
        if "g_round_start_time" in variables:
            round_start_operand = (144115188075855872
                                   + variables.index("g_round_start_time"))
    changed_scene = apply_city_overlay(original_scene, plan)
    changed_mission = patch_orders(original_mission, idx, wave_global, hold_entries,
                                    wave_visitors, defender_target,
                                    zombie_speed, defender_orders,
                                    game_type_operand, round_ended_operand,
                                    round_start_operand, fire_mode)
    if len(decode_scene(changed_scene)["objects"]) != len(decode_scene(original_scene)["objects"]) + 3:
        raise PatchError("Scene overlay failed binary roundtrip")
    # All validations happen before writes. On a mission-write failure, restore the SCO.
    scene_path.write_bytes(changed_scene)
    try:
        mission_path.write_bytes(changed_mission.encode("utf-8"))
    except Exception:
        scene_path.write_bytes(original_scene)
        raise
    return {"city_guard_posts": plan["guard_posts"],
            "defender_groups": list(DIVISIONS),
            "original_city_scene_objects": len(decode_scene(original_scene)["objects"]),
            "updated_city_scene_objects": len(decode_scene(changed_scene)["objects"]),
            "invasion_triggers": 27,
            "engine_verified": False,
            "wave_sector_rotation": True,
            "game_type": 7 if game_type_operand is not None else None,
            "defender_target_cap": DEFENDER_TARGET_CAP,
            "survivor_growth_per_round": 1 if round_ended_operand is not None else 0,
            "zombie_speed": zombie_speed,
            "defender_standoff": defender_orders,
            "explosive_gating": "not_applicable_ai_loadouts_have_no_bombs",
            # These are accuracy/reload tuning profiles only. WSE2 1.1.5.4
            # exposes no weapon fire-mode setter/getter, so the labels are
            # policy metadata, not an engine single/burst/auto switch.
            "fire_modes": [mode["name"] for mode in FIRE_MODES],
            "fire_mode": fire_mode,
            "fire_mode_policy": ("ai_wave_mod3_accuracy_reload_tuning"
                                 if fire_mode == "ai" else "fixed_session_tuning"),
            "fire_mode_semantics": (
                "accuracy_reload_tuning_only; no engine fire-mode setter/getter; "
                "labels are policy metadata"),
            "item_accuracy_scope": "global_item_table_not_city_only",
            "reload_direction": "unverified_percent_assumed_higher_is_faster",
            "spawn_transient": "new_or_refilled_bots_read_100_until_next_5s_tick",
            "accuracy_modifier_percent": [mode["accuracy"] for mode in FIRE_MODES],
            "reload_speed_modifier_percent": [mode["reload"] for mode in FIRE_MODES],
            "defender_orders": defender_orders,
            "wave_visitors": wave_visitors,
            "defender_target": defender_target,
            "defender_reinforce": defender_target > 0,
            "hold_entries": list(hold_entries),
            "defensive_line": tuple(hold_entries) == REAR_HOLD_ENTRIES,
            "formation_mode": ("adaptive" if adaptive else
                               ("rear" if tuple(hold_entries) == REAR_HOLD_ENTRIES
                                else "forward")),
            "formation_anchor": "entry0_north_base",
            "formation_sectors": {"5": 2, "6": 3, "7": 4},
            "formation_policy": ("adaptive_hold_or_fallback" if adaptive else "static"),
            "role_divisions": {"981": 5, "982": 5, "983": 6, "984": 7},
            "target_priority": "native_nearest; no public target setter",
            "warning": "Navmesh-derived posts; movement, fire and runtime LOS unverified.\n"
                       "Sectors rotate once per original wave_number parity; D validates positions."}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--module", type=Path, required=True)
    parser.add_argument("--apply", action="store_true")
    args = parser.parse_args()
    if args.apply:
        print(json.dumps(apply_module(args.module), indent=2))
    else:
        idx = scene_index(args.module / "scenes.txt")
        plan = plan_city((args.module / "SceneObj" / "scn_tbfc_invasion_4.sco").read_bytes())
        updated = patch_orders((args.module / "mission_templates.txt").read_bytes().decode("utf-8"), idx)
        print(json.dumps({"dry_run": True, "posts": plan["guard_posts"],
                          "result_triggers": mission_bounds(updated.splitlines(keepends=True))[1]}, indent=2))


if __name__ == "__main__":
    main()
