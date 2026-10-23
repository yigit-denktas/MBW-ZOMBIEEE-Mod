#!/usr/bin/env python3
"""Optional AI-only balanced troop clones for original ZOMBIEEE Beta 0.4.

The four playable survivor troops and all original troop IDs remain byte-for-byte
unchanged. Append four explicitly named AI-only copies with inventory defaults
drawn exclusively from items already shipped in the user's original mod.
"""
from __future__ import annotations
import argparse
import json
from pathlib import Path
from patch_defenders import PatchError, SURVIVOR_CLASSES

SOURCE_TROOP_COUNT = 981
SOURCE_ITEM_COUNT = 684
CLONES = (
    "trp_zdr_commando_bot",
    "trp_zdr_sniper_bot",
    "trp_zdr_scout_bot",
    "trp_zdr_lumberjack_bot",
)
# Four weapon slots at most (including ammunition). Clothing remains equipped.
LOADOUTS = (
    ("itm_m16a2", "itm_cartridges", "itm_cartridges", "itm_beretta_92fs",
     "itm_police_uniform_a", "itm_leather_gloves", "itm_boots"),
    ("itm_remington_model_700", "itm_cartridges", "itm_cartridges",
     "itm_beretta_92fs", "itm_police_uniform_b", "itm_brogans_a"),
    ("itm_mp5", "itm_cartridges_1", "itm_cartridges_1", "itm_sw_5904",
     "itm_police_uniform_a", "itm_brogans_a"),
    ("itm_browning_cynergy", "itm_cartridges_2", "itm_cartridges_2",
     "itm_bowie", "itm_lumberjack", "itm_boots"),
)


def index_items(text: str) -> dict[str, int]:
    lines = text.splitlines()
    if len(lines) < 3 or lines[0].strip() != "itemsfile version 3":
        raise PatchError("Unexpected original item_kinds1.txt format")
    try:
        declared = int(lines[1].strip())
    except ValueError as exc:
        raise PatchError("Invalid item count") from exc
    names = [line.split()[0] for line in lines if line.lstrip().startswith("itm_")]
    if declared != SOURCE_ITEM_COUNT or len(names) != declared:
        raise PatchError("Original item table count has changed")
    # The 2012 release itself contains 16 duplicate item identifiers. Their
    # positional numeric IDs are canonical; never deduplicate or renumber them.
    # Require only selected defender equipment to have an unambiguous ID.
    selected = {name for loadout in LOADOUTS for name in loadout}
    for name in selected:
        if names.count(name) != 1:
            raise PatchError("Missing or ambiguous defender item: " + name)
    mapping = {}
    for i, name in enumerate(names):
        mapping.setdefault(name, i)
    return mapping


def _parse_troops(text: str):
    rows = text.splitlines(keepends=True)
    if len(rows) < 8 or not rows[0].startswith("troopsfile version 2"):
        raise PatchError("Unexpected original troop format")
    try:
        declared = int(rows[1].strip())
    except ValueError as exc:
        raise PatchError("Invalid troop count") from exc
    indexes = [i for i, row in enumerate(rows) if row.startswith("trp_")]
    if len(indexes) != declared:
        raise PatchError("Troop headers/count mismatch")
    return rows, declared, indexes


def _clone_record(rows: list[str], start: int, stop: int,
                  new_name: str, item_numbers: list[int], newline: str) -> str:
    record = rows[start:stop]
    if len(record) < 6 or not record[0].startswith("trp_"):
        raise PatchError("Unexpected troop record structure")
    header = record[0].split()
    if len(header) < 10:
        raise PatchError("Malformed troop header")
    header[:3] = [new_name, new_name[4:].upper(), new_name[4:].upper()]
    copied = list(record)
    copied[0] = " ".join(header) + newline
    inventory = record[1].split()
    if len(inventory) != 128:
        raise PatchError("Expected exactly 64 original inventory item/modifier pairs")
    equipment = []
    for item in item_numbers:
        equipment.extend([str(item), "0"])
    equipment.extend(["-1", "0"] * (64 - len(item_numbers)))
    copied[1] = "  " + " ".join(equipment) + " " + newline
    return "".join(copied)


def patch_text(troops: str, items: str) -> tuple[str, dict]:
    item_indexes = index_items(items)
    rows, count, indexes = _parse_troops(troops)
    if count != SOURCE_TROOP_COUNT:
        raise PatchError("Cannot append AI clones to a modified troop table")
    current = {rows[i].split()[0]: n for n, i in enumerate(indexes)}
    if any(name in current for name in CLONES):
        raise PatchError("AI loadout clones already present")
    if len(set(SURVIVOR_CLASSES)) != 4 or any(n not in current for n in SURVIVOR_CLASSES):
        raise PatchError("Original playable survivor classes missing")
    newline = "\r\n" if "\r\n" in troops else "\n"
    rendered = []
    for human, clone, loadout in zip(SURVIVOR_CLASSES, CLONES, LOADOUTS):
        missing = [name for name in loadout if name not in item_indexes]
        if missing:
            raise PatchError("Missing original 0.4 items: " + ", ".join(missing))
        ordinal = current[human]
        start = indexes[ordinal]
        stop = indexes[ordinal + 1] if ordinal + 1 < len(indexes) else len(rows)
        rendered.append(_clone_record(rows, start, stop, clone,
                                      [item_indexes[name] for name in loadout], newline))
    output = list(rows)
    output[1] = str(count + len(CLONES)) + newline
    if output and not output[-1].endswith(("\n", "\r")):
        output[-1] += newline
    changed = "".join(output) + "".join(rendered)
    _, declared, after = _parse_troops(changed)
    if declared != count + 4 or len(after) != declared:
        raise PatchError("Appended troop table failed structural validation")
    return changed, {
        "profile": "balanced-ai", "new_troops": list(CLONES),
        "original_count": count, "patched_count": declared,
        "equipment": {clone: list(items) for clone, items in zip(CLONES, LOADOUTS)},
        "original_playable_classes_unchanged": True,
        "runtime_verified": False,
    }


def apply_module(module: Path) -> dict:
    module = Path(module)
    path = module / "troops.txt"
    old = path.read_bytes()
    changed, report = patch_text(old.decode("utf-8"),
                                 (module / "item_kinds1.txt").read_text(encoding="utf-8"))
    path.write_bytes(changed.encode("utf-8"))
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--module", type=Path, required=True)
    parser.add_argument("--apply", action="store_true")
    args = parser.parse_args()
    p = args.module
    if args.apply:
        report = apply_module(p)
    else:
        _, report = patch_text((p / "troops.txt").read_bytes().decode(),
                               (p / "item_kinds1.txt").read_text(encoding="utf-8"))
        report["dry_run"] = True
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
