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
ZOMBIE_SPEED_BASE = 60             # percent, wave 0/1 (task-45 pressure tuning)
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
                   defender_orders: bool = True) -> str:
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
            ops.append(["2123", "3", l13, str(wave_global),
                        str(ZOMBIE_SPEED_PER_WAVE)])  # store_mul
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
            l4 = str(LOCAL0 + 4)
            ops.append(["1765", "2", l4, l1])              # agent_get_group (native)
            ops.append(["1780", "2", str(pos), "0"])       # rear entry position
            ops.append(["1791", "3", "0", l4, str(pos)])   # team_set_order_position
            for order in HOLD_FIRE_ORDERS:
                ops.append(["1790", "3", "0", l4, str(order)])
            # Ranged standoff: keep the firearm while ammo remains; only allow
            # the native melee weapon switch when the magazine is empty
            # (knife/melee is a last resort). WSE2 hold behavior keeps the
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
        ops.append(["2120", "3", l0, l0, "1"])             # count += 1
        ops.append(["3", "0"])                             # try_end
        if defender_target:
            l8, l9, l10, l11 = (str(LOCAL0 + n) for n in (8, 9, 10, 11))
            ops.append(["2133", "2", l8, str(defender_target)])
            ops.append(["2121", "3", l9, l8, l0])           # missing = target - count
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
    return " ".join(["5.000000", "0.000000", "0.000000",
                     "3", *conditions, str(len(ops)), *tokens])


def patch_orders(original: str, scene_idx: int,
                 wave_global: int | None = None,
                 hold_entries: tuple[int, ...] = GUARD_ENTRIES,
                 wave_visitors: str = "slow",
                 defender_target: int = DEFAULT_DEFENDER_TARGET,
                 zombie_speed: bool = True,
                 defender_orders: bool = True) -> str:
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
                                            zombie_speed, defender_orders) + newline)
    updated = "".join(lines)
    if mission_bounds(updated.splitlines(keepends=True))[1] != 27:
        raise PatchError("Invalid tactical trigger count")
    return updated


def apply_module(module: Path, hold_entries: tuple[int, ...] = REAR_HOLD_ENTRIES,
                 wave_visitors: str = "slow",
                 defender_target: int = DEFAULT_DEFENDER_TARGET,
                 zombie_speed: bool = True,
                 defender_orders: bool = True) -> dict:
    module = Path(module)
    scene_path = module / "SceneObj" / "scn_tbfc_invasion_4.sco"
    mission_path = module / "mission_templates.txt"
    original_scene = scene_path.read_bytes()
    original_mission = mission_path.read_bytes().decode("utf-8")
    plan = plan_city(original_scene)
    idx = scene_index(module / "scenes.txt")
    wave_global = None
    variables_path = module / "variables.txt"
    if variables_path.is_file():
        variables = variables_path.read_text(encoding="utf-8").splitlines()
        if "wave_number" not in variables:
            raise PatchError("Original wave_number global missing for sector rotation")
        wave_global = 144115188075855872 + variables.index("wave_number")
    changed_scene = apply_city_overlay(original_scene, plan)
    changed_mission = patch_orders(original_mission, idx, wave_global, hold_entries,
                                    wave_visitors, defender_target,
                                    zombie_speed, defender_orders)
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
            "zombie_speed": zombie_speed,
            "defender_standoff": defender_orders,
            "explosive_gating": "not_applicable_ai_loadouts_have_no_bombs",
            "defender_orders": defender_orders,
            "wave_visitors": wave_visitors,
            "defender_target": defender_target,
            "defender_reinforce": defender_target > 0,
            "hold_entries": list(hold_entries),
            "defensive_line": tuple(hold_entries) == REAR_HOLD_ENTRIES,
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
