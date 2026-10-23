#!/usr/bin/env python3
"""Offline City overlay checks; never evidence of Warband/WSE2 runtime.

Compare the generated module against an owned, unmodified original Beta 0.4
module. This tool only reads existing files and emits path-free evidence.
"""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path
from patch_defenders import mission_bounds
from city_defense import SCENE_BASE, LOCAL0, scene_index
from wave_reinforcements import LOCAL_BASE
from trace_calls import read_mission_calls

ORIGINAL_TRIGGERS = 25
CITY_TRIGGERS = 31
SCO_NAME = "scn_tbfc_invasion_4.sco"


def _conditions(row):
    parts = row.split()
    if len(parts) < 5:
        raise ValueError("Compiled native trigger truncated")
    count = int(parts[3])
    if not 0 <= count <= 10000:
        raise ValueError("Invalid native condition count")
    pos, decoded = 4, []
    for _ in range(count):
        if pos + 2 > len(parts):
            raise ValueError("Incomplete native condition header")
        opcode, argc = int(parts[pos]), int(parts[pos + 1])
        pos += 2
        if not 0 <= argc <= 128 or pos + argc > len(parts):
            raise ValueError("Truncated native condition operands")
        decoded.append((opcode, tuple(int(a) for a in parts[pos:pos + argc])))
        pos += argc
    if pos >= len(parts):
        raise ValueError("Missing native consequence count")
    return decoded


def _triggers(module):
    file = module / "mission_templates.txt"
    lines = file.read_text(encoding="utf-8").splitlines(keepends=True)
    count_row, count, end = mission_bounds(lines)
    if len(read_mission_calls(file)) != count:
        raise ValueError("Compiled native stream could not be decoded")
    return [line.rstrip("\r\n") for line in lines[count_row + 1:end]], count


def audit_city(module: Path, original: Path) -> dict:
    """Check original content preservation, City guards and native arity."""
    module, original = Path(module), Path(original)
    evidence = {
        "schema": "zombieee.city-static.v1", "city_accepted": False,
        "runtime_verified": False, "checks": {}, "problems": [],
        "scope": "city-only",
    }

    def require(name, condition, problem):
        evidence["checks"][name] = bool(condition)
        if not condition:
            evidence["problems"].append(problem)

    try:
        baseline, before = _triggers(original)
        actual, after = _triggers(module)
        require("original_trigger_count", before == ORIGINAL_TRIGGERS,
                "Original source invasion must have 25 triggers")
        require("city_trigger_count", after == CITY_TRIGGERS,
                "Expected 31 native City tactical triggers")
        require("original_trigger_prefix", actual[:25] == baseline[:25],
                "Original invasion trigger contents were modified")
        city = SCENE_BASE + scene_index(module / "scenes.txt")
        require("scenes_table_untouched",
                (module / "scenes.txt").read_bytes() ==
                (original / "scenes.txt").read_bytes(),
                "Original scene table was changed")
        for index in (25, 28, 30):
            operations = _conditions(actual[index]) if len(actual) > index else []
            register = LOCAL0 if index == 25 else LOCAL_BASE + 8
            require(f"trigger_{index}_city_scene_gate",
                    (417, ()) in operations and
                    (2211, (register,)) in operations and
                    (31, (register, city)) in operations,
                    f"Native trigger {index} missing server/City guards")
        variables = (module / "variables.txt").read_text(encoding="utf-8").splitlines()
        base_variables = (original / "variables.txt").read_text(encoding="utf-8").splitlines()
        require("global_variable_append_only",
                len(variables) == len(base_variables) + 3 and
                variables[:len(base_variables)] == base_variables and
                variables[-3:] == ["zdr_last_reinforced_wave",
                                  "zdr_last_reinforced_round_start",
                                  "zdr_defence_mode"],
                "Original global variable table changed")
        src = original / "SceneObj" / SCO_NAME
        new = module / "SceneObj" / SCO_NAME
        # Byte difference alone cannot establish guard-post integrity: an
        # arbitrary truncated or maliciously modified SCO also differs.
        # Rebuild the canonical City overlay from the untouched source and
        # require the candidate's COMPLETE bytes to match its expected output.
        # This includes the original object table and navigation mesh.
        from scene_tactics import plan_city, apply_city_overlay
        if not (src.is_file() and new.is_file()):
            require("city_sco_canonical_overlay", False,
                    "Missing original or generated City scene")
        else:
            original_city_bytes = src.read_bytes()
            expected_city_bytes = apply_city_overlay(
                original_city_bytes, plan_city(original_city_bytes))
            actual_city_bytes = new.read_bytes()
            require("city_sco_canonical_overlay",
                    actual_city_bytes == expected_city_bytes,
                    "City scene differs from the exact navmesh-derived guard-post overlay")
            evidence["city_overlay_expected_sha256"] = hashlib.sha256(
                expected_city_bytes).hexdigest()
            evidence["city_overlay_actual_sha256"] = hashlib.sha256(
                actual_city_bytes).hexdigest()
        for number in (1, 2, 3, 5):
            name = f"scn_tbfc_invasion_{number}.sco"
            before_path = original / "SceneObj" / name
            after_path = module / "SceneObj" / name
            if before_path.is_file() and after_path.is_file():
                require(f"other_scene_{number}_untouched",
                        hashlib.sha256(before_path.read_bytes()).digest() ==
                        hashlib.sha256(after_path.read_bytes()).digest(),
                        f"Deferred original scene {number} was modified")
            else:
                evidence["checks"][f"other_scene_{number}_evidence"] = False
                evidence["problems"].append(
                    f"Insufficient matching evidence for scene {number}")
        # Structural trigger counts alone miss a dormant logical branch:
        # original mst_multiplayer_iv initializes its game type to 7, while
        # the first remaster wave/recovery patches compared it to 6.
        from ai_wave_contract import inspect_city_ai
        ai = inspect_city_ai(baseline, actual, base_variables, variables)
        for name, passed in ai["checks"].items():
            require("ai_" + name, passed,
                    "City AI native contract failed: " + name)
        evidence["original_invasion_game_type"] = ai["original_invasion_mode"]
        evidence["original_triggers"] = before
        evidence["city_triggers"] = after
    except (OSError, ValueError, IndexError, KeyError) as exc:
        evidence["problems"].append(
            "Static inspection error: " + type(exc).__name__ + ": " + str(exc))
    evidence["city_accepted"] = not evidence["problems"]
    return evidence


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--original", type=Path, required=True)
    parser.add_argument("--module", type=Path, required=True)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    data = audit_city(args.module, args.original)
    if args.json:
        print(json.dumps(data, indent=2, sort_keys=True))
    else:
        print("City static contract:", "PASS" if data["city_accepted"] else "FAIL")
        print("Checks:", len(data["checks"]), "Problems:", len(data["problems"]))
        print("WSE2 game runtime: UNKNOWN")
    return 0 if data["city_accepted"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
