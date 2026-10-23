#!/usr/bin/env python3
"""Opt-in compiled Warband invasion trigger to spawn a small allied squad.

Adds one server-only ti_after_mission_start trigger to multiplayer_iv.
All original trigger lines are preserved. Not yet validated in WSE2 gameplay.
"""
from __future__ import annotations
import argparse
from pathlib import Path

MISSION = "mst_multiplayer_iv"
TROOP_BASE = 360287970189639680
SERVER_ONLY = "417 0"  # multiplayer_is_server
VISITORS = 1265        # add_visitors_to_current_scene
AFTER_START = "-20.000000"  # ti_after_mission_start
SURVIVOR_TEAM = 0
SURVIVOR_ENTRIES = (0, 1)
SURVIVOR_CLASSES = (
    "trp_swadian_crossbowman_multiplayer",  # Commando
    "trp_swadian_sniper_multiplayer",       # Sniper
    "trp_swadian_man_at_arms_multiplayer",  # Scout
    "trp_swadian_infantry_multiplayer",     # Lumberjack
)


class PatchError(ValueError):
    pass


def index_troops(path: Path) -> dict[str, int]:
    """Resolve numeric troop operands from original compiled troop order."""
    lines = Path(path).read_text(encoding="utf-8", errors="replace").splitlines()
    if not lines or not lines[0].startswith("troopsfile version"):
        raise PatchError("Unrecognised troops.txt header")
    try:
        declared = int(lines[1].strip())
    except (ValueError, IndexError) as exc:
        raise PatchError("Malformed troops.txt count") from exc
    names = [line.split()[0] for line in lines[2:] if line.startswith("trp_")]
    if len(names) != declared:
        raise PatchError(f"Troop count mismatch: {len(names)} != {declared}")
    # Original Beta 0.4 contains five duplicated invader names; indexes are
    # positional, so do not renumber or de-duplicate its entire troop table.
    mapping = {}
    for index, name in enumerate(names):
        if name in SURVIVOR_CLASSES and name in mapping:
            raise PatchError("Ambiguous survivor troop: " + name)
        mapping.setdefault(name, index)
    return mapping


def mission_bounds(lines: list[str]) -> tuple[int, int, int]:
    starts = [i for i, line in enumerate(lines) if line.startswith(MISSION + " ")]
    if len(starts) != 1:
        raise PatchError(f"Expected exactly one {MISSION}, got {len(starts)}")
    p = starts[0] + 1
    while p < len(lines) and not lines[p].strip():
        p += 1
    if p >= len(lines):
        raise PatchError("No mission description")
    p += 1
    while p < len(lines) and not lines[p].strip():
        p += 1
    try:
        entry_count = int(lines[p].split()[0])
    except (ValueError, IndexError) as exc:
        raise PatchError("Missing entry point count") from exc
    if entry_count != 64:
        raise PatchError(f"Expected original 64 entry points, found {entry_count}")
    p += entry_count
    while p < len(lines) and not lines[p].strip():
        p += 1
    try:
        trigger_count = int(lines[p].strip())
    except (ValueError, IndexError) as exc:
        raise PatchError("Missing invasion trigger count") from exc
    if not 0 <= trigger_count <= 100:
        raise PatchError("Implausible trigger count")
    insert_at = p + 1 + trigger_count
    if insert_at > len(lines):
        raise PatchError("Truncated mission trigger lines")
    return p, trigger_count, insert_at


def build_trigger(count: int, troop_ids: dict[str, int],
                  troop_classes: tuple[str, ...] = SURVIVOR_CLASSES) -> str:
    if not 1 <= count <= 8:
        raise PatchError("Allied squad size must be between 1 and 8")
    missing = [name for name in troop_classes if name not in troop_ids]
    if missing:
        raise PatchError("Missing survivor troops: " + ", ".join(missing))
    classes = [troop_classes[i % len(troop_classes)] for i in range(count)]
    ops = []
    for index, name in enumerate(classes):
        entry = SURVIVOR_ENTRIES[index % 2]
        operand = TROOP_BASE + troop_ids[name]
        ops.extend(["1265", "5", str(entry), str(operand), "1", "0", "0"])
    # 1 condition op (server only), count consequence ops (native MP spawns)
    return " ".join([AFTER_START, "0.000000", "0.000000",
                     "1", SERVER_ONLY, str(count), *ops])


def patch_text(original: str, troops: dict[str, int], count: int,
               troop_classes: tuple[str, ...] = SURVIVOR_CLASSES) -> str:
    lines = original.splitlines(keepends=True)
    p, triggers, end = mission_bounds(lines)
    if triggers != 25 or lines[p].strip() != "25":
        raise PatchError(f"Refusing non-original invasion trigger count: {triggers}")
    trigger = build_trigger(count, troops, troop_classes)
    newline = "\r\n" if "\r\n" in original else "\n"
    lines[p] = "26" + newline
    lines.insert(end, trigger + newline)
    result = "".join(lines)
    if mission_bounds(result.splitlines(keepends=True))[1] != 26:
        raise PatchError("Resulting mission invalid")
    return result


def patch_file(module_dir: Path, count: int, balanced_ai: bool = False) -> dict:
    module_dir = Path(module_dir)
    path = module_dir / "mission_templates.txt"
    original = path.read_bytes().decode("utf-8")
    troops = index_troops(module_dir / "troops.txt")
    if balanced_ai:
        from bot_loadouts import CLONES
        troop_classes = CLONES
    else:
        troop_classes = SURVIVOR_CLASSES
    patched = patch_text(original, troops, count, troop_classes)
    path.write_bytes(patched.encode("utf-8"))
    return {
        "experimental_defenders": count,
        "troop_profile": "balanced-ai" if balanced_ai else "original-0.4",
        "team": SURVIVOR_TEAM,
        "spawn_entries": SURVIVOR_ENTRIES,
        "original_invasion_triggers": 25,
        "patched_invasion_triggers": 26,
        "verified_in_engine": False,
        "warning": "One-time squad spawn only: no hold orders or wave respawn yet.",
    }


def main():
    import json
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--module", required=True, type=Path)
    p.add_argument("--count", type=int, default=4)
    p.add_argument("--apply", action="store_true", help="Else dry-run only")
    args = p.parse_args()
    try:
        original = (args.module / "mission_templates.txt").read_bytes().decode("utf-8")
        patched = patch_text(original, index_troops(args.module / "troops.txt"), args.count)
        if args.apply:
            result = patch_file(args.module, args.count)
        else:
            result = {"dry_run": True, "experimental_defenders": args.count,
                      "changed_characters": len(patched) - len(original),
                      "verified_in_engine": False}
        print(json.dumps(result, indent=2))
    except (OSError, PatchError) as exc:
        p.exit(2, f"Defender patch refused: {exc}\n")


if __name__ == "__main__":
    main()
