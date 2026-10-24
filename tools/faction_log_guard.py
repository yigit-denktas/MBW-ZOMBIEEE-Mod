"""City-only log guard for original Beta 0.4 trigger 14 invalid faction writes.

The original mission template ends trigger 14 with four
``faction_set_slot(-1, 200, trp_invader_multiplayer_ai)`` consequences. The
engine logs ``SCRIPT ERROR: Invalid Faction ID: -1`` for each at mission start.
This guard rewrites only those four trailing operations to a valid invader
faction and the unused slot 245, leaving wave composition untouched. It is a
logs-only City exception; trigger-14's valid 24 slot writes are not changed.
"""
from __future__ import annotations

from pathlib import Path

from patch_defenders import mission_bounds

FACTION_BASE = 432345564227567616
INVADER_FACTION = FACTION_BASE + 16
UNUSED_SLOT = 245
TROOP_BASE = 360287970189639680
INVALID_FACTION = -1
INVALID_SLOT = 200
TRIGGER_INDEX = 14
TRAILING_INVALID_OPS = 4


class FactionLogGuardError(ValueError):
    """Raised when the original trigger-14 shape is not the expected one."""


def _decode_ops(tokens: list[str], start: int) -> list[tuple[int, tuple[int, ...]]]:
    count = int(tokens[start])
    cursor = start + 1
    ops = []
    for _ in range(count):
        op = int(tokens[cursor])
        argc = int(tokens[cursor + 1])
        cursor += 2
        args = tuple(int(value) for value in tokens[cursor:cursor + argc])
        cursor += argc
        ops.append((op, args))
    return ops


def patch_mission_text(text: str) -> tuple[str, dict]:
    """Return guarded mission text and a bounded, path-free report."""
    lines = text.splitlines(keepends=True)
    p, trigger_count, end = mission_bounds(lines)
    rows = lines[p + 1:end]
    if len(rows) != trigger_count or trigger_count <= TRIGGER_INDEX:
        raise FactionLogGuardError("Mission trigger table incomplete")
    row = rows[TRIGGER_INDEX]
    tokens = row.split()
    condition_count = int(tokens[3])
    cursor = 4
    for _ in range(condition_count):
        argc = int(tokens[cursor + 1])
        cursor += 2 + argc
    ops = _decode_ops(tokens, cursor)
    if len(ops) != 28:
        raise FactionLogGuardError(
            f"Original trigger 14 must have 28 consequences, found {len(ops)}")
    changed = 0
    encoded: list[str] = []
    for index, (op, args) in enumerate(ops):
        if op == 502 and args == (INVALID_FACTION, INVALID_SLOT, TROOP_BASE + 873):
            if index < len(ops) - TRAILING_INVALID_OPS:
                raise FactionLogGuardError(
                    "Invalid faction write is not in the trailing four")
            encoded.extend(["502", "3", str(INVADER_FACTION), str(UNUSED_SLOT),
                            str(TROOP_BASE + 873)])
            changed += 1
        else:
            encoded.extend([str(op), str(len(args)), *(str(a) for a in args)])
    if changed != TRAILING_INVALID_OPS:
        raise FactionLogGuardError(
            f"Expected 4 trailing invalid faction writes, found {changed}")
    prefix = tokens[:cursor]
    new_row = " ".join([*prefix, str(len(ops)), *encoded]) + (
        "\r\n" if row.endswith("\r\n") else "\n")
    rows[TRIGGER_INDEX] = new_row
    output = "".join(lines[:p + 1] + rows + lines[end:])
    report = {
        "schema": "zombieee.faction-log-guard.v1",
        "trigger": TRIGGER_INDEX,
        "replaced_ops": changed,
        "invalid_faction": INVALID_FACTION,
        "valid_faction": INVADER_FACTION,
        "unused_slot": UNUSED_SLOT,
        "wave_composition_changed": False,
    }
    return output, report


def apply_module(module: Path) -> dict:
    path = Path(module) / "mission_templates.txt"
    text = path.read_text(encoding="utf-8")
    updated, report = patch_mission_text(text)
    path.write_text(updated, encoding="utf-8", newline="")
    report["module"] = "mission_templates.txt"
    return report


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("module", type=Path)
    args = parser.parse_args()
    print(apply_module(args.module))
