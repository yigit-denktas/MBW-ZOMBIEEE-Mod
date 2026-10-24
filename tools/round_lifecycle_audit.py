#!/usr/bin/env python3
"""Read-only source audit of City AI across an original invasion round restart.

This does not simulate Warband's trigger scheduler, pathfinding, AI orders or
runtime. It reports code that needs direct WSE2 round-transition evidence.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from ai_wave_contract import decode_trigger
from patch_defenders import mission_bounds
from wave_reinforcements import GLOBAL_BASE, ROUND_STAMP, SENTINEL


def mission_rows(path: Path) -> list[str]:
    lines = Path(path).read_text(encoding="utf-8").splitlines(keepends=True)
    count_at, count, end = mission_bounds(lines)
    return [line.strip() for line in lines[count_at + 1:end]]


def audit_round_lifecycle(original: Path, city_module: Path) -> dict:
    """Verify source properties; return explicit *risks*, not gameplay verdicts."""
    before = mission_rows(Path(original) / "mission_templates.txt")
    after = mission_rows(Path(city_module) / "mission_templates.txt")
    src_globals = (Path(original) / "variables.txt").read_text(encoding="utf-8").splitlines()
    final_globals = (Path(city_module) / "variables.txt").read_text(encoding="utf-8").splitlines()
    if len(before) != 25 or len(after) not in (31, 32, 35):
        raise ValueError("Expected historical original and City tactical mission")
    if len(src_globals) != 1220 or final_globals[:1220] != src_globals:
        raise ValueError("Not the pinned append-only City variable table")
    for name in ("wave_number", "g_round_start_time", "g_round_ended"):
        if src_globals.count(name) != 1:
            raise ValueError("Historical round variable is missing or duplicated")
    for name in (SENTINEL, ROUND_STAMP, "zdr_defence_mode"):
        if final_globals.count(name) != 1:
            raise ValueError("Remaster round variable is missing or duplicated")
    old_ops = {i: decode_trigger(before[i])[1] for i in (3, 7, 10)}
    conditions, effects = {}, {}
    for i in range(25, 31):
        conditions[i], effects[i] = decode_trigger(after[i])
    g = {name: GLOBAL_BASE + src_globals.index(name)
         for name in ("wave_number", "g_round_start_time", "g_round_ended")}
    checks = {
        "original_25_triggers_preserved": after[:25] == before,
        "original_round_wave_reset": all((2133, (g["wave_number"], 0)) in old_ops[idx]
                                         for idx in (7, 10)),
        "original_new_round_timestamp": (2370, (g["g_round_start_time"],)) in old_ops[10],
        "new_squad_spawn_after_mission_start_only": (
            after[25].split()[0] == "-20.000000"
            and any(code == 1265 for code, _ in effects[25])),
        "hold_orders_reissued_periodically": (
            after[26].split()[:3] == ["5.000000", "0.000000", "0.000000"]
            and sum(code == 1791 for code, _ in effects[26]) == 3
            and sum(code == 1790 for code, _ in effects[26]) == 3),
        "reinforcement_periodic": (
            after[28].split()[0] == "4.000000"
            and any(code == 1265 for code, _ in effects[28])),
        "recovery_periodic": (
            after[30].split()[0] == "3.000000"
            and sum(code == 1791 for code, _ in effects[30]) == 6),
        "tactical_mode_initialized_once": (
            after[29].split()[0] == "-20.000000"
            and (2133, (GLOBAL_BASE + final_globals.index("zdr_defence_mode"), 0)) in effects[29]),
        "round_identity_stored_in_wave_handler": (
            (2133, (GLOBAL_BASE + final_globals.index(ROUND_STAMP),
                     g["g_round_start_time"])) in effects[28]),
    }
    if not all(checks.values()):
        return {"schema": "zombieee.round-lifecycle-source.v1", "source_pattern_verified": False,
                "runtime_verified": False, "checks": checks,
                "problems": [key for key, ok in checks.items() if not ok],
                "unknown_runtime_observations": ["in_place_round_restart", "survivor_respawn",
                                                 "hold_order_persistence", "tactical_mode_persistence"]}
    return {
        "schema": "zombieee.round-lifecycle-source.v1",
        "source_pattern_verified": True, "runtime_verified": False,
        "checks": checks, "problems": [],
        "verified_source_patterns": [
            "original wave counter resets on round transition",
            "original round-start clock written on new round",
            "added defenders are initially spawned after mission start",
            "private hold orders are re-issued every 5 seconds to survive round resets",
            "reinforcement and tactical recovery are periodic",
            "tactical mode initializer runs after mission start, not at every round reset",
            "round-aware reinforcement stores original round-start timestamp",
        ],
        "unknown_runtime_observations": [
            "whether round transitions reuse one mission instance",
            "whether survivor bots persist or are removed and need re-spawning",
            "whether original hold positions survive in-place round transitions",
            "whether retreat mode state should be reset when the next round begins",
            "whether WSE2's round-start timer token is unique at observed transition times",
            "whether any survivor actually traverses the City scene and engages zombies",
        ],
        "disposition": "source_verified_runtime_open_no_automatic_gameplay_patch",
    }


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--original", required=True, type=Path)
    p.add_argument("--module", required=True, type=Path)
    p.add_argument("--json", action="store_true")
    a = p.parse_args()
    try:
        report = audit_round_lifecycle(a.original, a.module)
    except (OSError, ValueError, IndexError, KeyError) as error:
        print(json.dumps({"source_pattern_verified": False, "runtime_verified": False,
                          "error_type": type(error).__name__}))
        return 2
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0 if report["source_pattern_verified"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
