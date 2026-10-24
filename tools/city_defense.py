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
DIVISIONS = (5, 6, 7)
GUARD_ENTRIES = (2, 3, 4)


def scene_index(path: Path, name="scn_tbfc_invasion_4") -> int:
    lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
    ids = [line.split()[0] for line in lines if line.startswith("scn_")]
    if len(ids) != 560 or ids.count(name) != 1:
        raise PatchError("Unexpected original scenes table")
    return ids.index(name)


def orders_trigger(scene_idx: int) -> str:
    # Conditions: server, store_current_scene(local0), equal(local0, City).
    conditions = ["417", "0", "2211", "1", str(LOCAL0),
                  "31", "2", str(LOCAL0), str(SCENE_BASE + scene_idx)]
    operations = []
    for group, entry in zip(DIVISIONS, GUARD_ENTRIES):
        pos = POS_BASE + 120
        operations += ["1780", "2", str(pos), str(entry)]  # entry_point_get_position
        operations += ["1791", "3", "0", str(group), str(pos)]  # team_set_order_position
        operations += ["1790", "3", "0", str(group), "0"]  # team_give_order: mordr_hold
    # Periodic 5 s upkeep: re-issues hold positions after dedicated round
    # resets / squad respawns (the initial one-shot order did not survive them).
    return " ".join(["5.000000", "0.000000", "0.000000",
                     "3", *conditions, "9", *operations])


def patch_orders(original: str, scene_idx: int) -> str:
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
    lines.insert(insert_at, orders_trigger(scene_idx) + newline)
    updated = "".join(lines)
    if mission_bounds(updated.splitlines(keepends=True))[1] != 27:
        raise PatchError("Invalid tactical trigger count")
    return updated


def apply_module(module: Path) -> dict:
    module = Path(module)
    scene_path = module / "SceneObj" / "scn_tbfc_invasion_4.sco"
    mission_path = module / "mission_templates.txt"
    original_scene = scene_path.read_bytes()
    original_mission = mission_path.read_bytes().decode("utf-8")
    plan = plan_city(original_scene)
    idx = scene_index(module / "scenes.txt")
    changed_scene = apply_city_overlay(original_scene, plan)
    changed_mission = patch_orders(original_mission, idx)
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
            "warning": "Navmesh-derived posts; movement, fire and runtime LOS unverified."}


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
