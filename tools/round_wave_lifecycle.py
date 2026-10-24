#!/usr/bin/env python3
"""Read-only diagnosis of the native City round vs wave lifecycle.

D's 495 s / 10-round sealed run reached only wave 1: every sealed round ended
(team-0 wipe / native reset) before the wave controller advanced to 2, and each
new round restarted at wave 0. This tool decodes the original mission template
and reports exactly where ``$g_wave_number`` is initialised, incremented and
reset, plus the round-ended writes, so the tradeoff is evidence-based rather
than guessed.

Findings for the pinned ZOMBIEEE Beta 0.4 City mission:

- trigger 3 (-19 after-mission-start) initialises wave_number = 0;
- trigger 7 (-26 round end) sets ``g_round_ended = 1`` and wave_number = 0;
- trigger 6 (-25 round start) clears ``g_round_ended = 0`` but does not touch
  wave_number;
- trigger 15 (1 s periodic server wave controller) increments wave_number and
  spawns the wave.

Therefore the reset is **native round-end behaviour**, not a City patch defect:
a round that ends before the wave is cleared returns the next round to wave 0.
To observe wave 2 in the hands-off harness the round must survive long enough to
clear wave 1 -- options are rotation/roster, not a mission rewrite:

1. ``set_player_respawn_as_bot 1`` (hands-off AI validation) keeps team 0 alive
   when the unattended player dies, so the round does not end on player death.
2. A defender-heavy variant (``--experimental-defenders 8`` and/or
   ``set_bot_count 2 4``) lets the squad clear wave 1 before being wiped.
3. A City-only "wave carryover" patch (persisting wave_number across rounds)
   would change native difficulty progression and is **not recommended** without
   play-testing; the original 25 triggers must stay byte-identical.

No runtime claim is made by this tool; it is static analysis of the pinned
mission plus an optional comparison against a built module.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from ai_wave_contract import decode_trigger
from patch_defenders import mission_bounds

GLOBAL_BASE = 144115188075855872
WAVE_GLOBAL = GLOBAL_BASE + 1209       # $g_wave_number
ROUND_ENDED = GLOBAL_BASE + 512        # $g_round_ended
ASSIGN = 2133
STORE_ADD = 2120
WAVE_INIT_TRIGGER = 3
ROUND_START_TRIGGER = 6
ROUND_END_TRIGGER = 7
WAVE_CONTROLLER_TRIGGER = 15
ORIGINAL_TRIGGER_COUNT = 25


def _rows(mission: Path) -> list[str]:
    lines = mission.read_text(encoding="utf-8", errors="replace").splitlines(keepends=True)
    start, count, end = mission_bounds(lines)
    if count < ORIGINAL_TRIGGER_COUNT:
        raise ValueError("Mission template is truncated")
    return [line.strip() for line in lines[start + 1:end]]


def _writes(cons, global_operand):
    return [(op, args) for op, args in cons
            if op == ASSIGN and args and args[0] == global_operand]


def analyse(mission: Path) -> dict:
    rows = _rows(mission)
    reset = _rows_trigger(rows, ROUND_END_TRIGGER)
    start = _rows_trigger(rows, ROUND_START_TRIGGER)
    init = _rows_trigger(rows, WAVE_INIT_TRIGGER)
    controller = _rows_trigger(rows, WAVE_CONTROLLER_TRIGGER)

    reset_cond, reset_cons = decode_trigger(reset)
    start_cond, start_cons = decode_trigger(start)
    init_cond, init_cons = decode_trigger(init)
    ctl_cond, ctl_cons = decode_trigger(controller)

    wave_reset = [op for op, args in _writes(reset_cons, WAVE_GLOBAL)
                  if len(args) >= 2 and args[1] == 0]
    round_end_set = [op for op, args in _writes(reset_cons, ROUND_ENDED)
                     if len(args) >= 2 and args[1] == 1]
    wave_init = [op for op, args in _writes(init_cons, WAVE_GLOBAL)
                 if len(args) >= 2 and args[1] == 0]
    round_start_clear = [op for op, args in _writes(start_cons, ROUND_ENDED)
                         if len(args) >= 2 and args[1] == 0]
    wave_increment = [(op, args) for op, args in ctl_cons
                      if op == STORE_ADD and args and args[0] == WAVE_GLOBAL]

    checks = {
        "round_end_resets_wave_to_zero": bool(wave_reset),
        "round_end_sets_round_ended": bool(round_end_set),
        "wave_initialised_at_mission_start": bool(wave_init),
        "round_start_clears_round_ended": bool(round_start_clear),
        "wave_controller_increments_wave": bool(wave_increment),
        "round_end_trigger_is_negative_header": reset.split()[0].startswith("-"),
        "wave_controller_is_periodic": controller.split()[:3] == ["1.000000", "0.000000", "0.000000"],
    }
    return {
        "wave_global": WAVE_GLOBAL,
        "round_ended_global": ROUND_ENDED,
        "triggers": {
            "wave_init": {"index": WAVE_INIT_TRIGGER, "header": init.split()[:3],
                          "wave_assignments": wave_init},
            "round_start": {"index": ROUND_START_TRIGGER, "header": start.split()[:3],
                            "round_ended_assignments": round_start_clear},
            "round_end": {"index": ROUND_END_TRIGGER, "header": reset.split()[:3],
                          "wave_assignments": wave_reset,
                          "round_ended_assignments": round_end_set},
            "wave_controller": {"index": WAVE_CONTROLLER_TRIGGER,
                                "header": controller.split()[:3],
                                "wave_increments": wave_increment},
        },
        "checks": checks,
        "passed": all(checks.values()),
        "finding": ("Native lifecycle: wave_number is initialised to 0, incremented by the "
                    "1 s server wave controller, and reset to 0 by the round-end trigger. "
                    "A round that ends (team-0 wipe / native reset) before wave 1 is cleared "
                    "restarts at wave 0. This is native behaviour, not a City patch defect."),
        "hands_off_options": [
            "rotation set_player_respawn_as_bot 1 (keep team 0 alive when the unattended player dies)",
            "defender-heavy variant: --experimental-defenders 8 and/or set_bot_count 2 4",
            "survive wave 1 with the native defender squad + firearm accuracy profile",
        ],
        "not_recommended": ("City-only wave-carryover patch: changes native difficulty progression "
                            "and must not alter the original 25 triggers without play-testing."),
    }


def _rows_trigger(rows: list[str], index: int) -> str:
    if index >= len(rows):
        raise ValueError(f"Missing original trigger {index}")
    return rows[index]


def compare_built(original_mission: Path, built_mission: Path) -> dict:
    original_rows = _rows(original_mission)
    built_rows = _rows(built_mission)
    prefix_equal = built_rows[:ORIGINAL_TRIGGER_COUNT] == original_rows[:ORIGINAL_TRIGGER_COUNT]
    return {
        "built_trigger_count": len(built_rows),
        "original_trigger_count": len(original_rows),
        "original_25_triggers_byte_identical": prefix_equal,
        "appended_trigger_count": len(built_rows) - ORIGINAL_TRIGGER_COUNT,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--original", type=Path, required=True,
                        help="Original module directory (mission_templates.txt)")
    parser.add_argument("--built", type=Path,
                        help="Optional built City module directory for prefix comparison")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    try:
        report = analyse(args.original / "mission_templates.txt")
        if args.built:
            report["built_comparison"] = compare_built(
                args.original / "mission_templates.txt",
                args.built / "mission_templates.txt")
    except (OSError, ValueError) as exc:
        print(json.dumps({"passed": False, "error": type(exc).__name__ + ": " + str(exc)}))
        return 2
    print(json.dumps(report, indent=2))
    return 0 if report["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
