"""City-only zombie head-armor removal (task-81 headshot lethality slice).

Warband item flags encode item type in the low nibble: 12 = head armor,
13 = body armor, 14 = foot armor, 15 = gloves (verified against the pinned
item table). This tool removes head-armor equipment pairs from invader troops
894..911 only, leaving weapons/body/legs and all item stats unchanged. It does
not claim a headshot outcome; D must validate lethality in-game.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

INVADER_RANGE = (894, 912)
HEAD_ARMOR_TYPE = 12
UNUSED_PAIR = "-1"


class HeadArmorError(ValueError):
    pass


def head_armor_ids(module: Path) -> set[int]:
    lines = (Path(module) / "item_kinds1.txt").read_text(
        encoding="utf-8", errors="replace").splitlines()
    ids = set()
    item = -1
    for line in lines:
        stripped = line.strip()
        if not stripped.startswith("itm_"):
            continue
        item += 1
        tokens = stripped.split()
        try:
            meshes = int(tokens[3])
            flags = int(tokens[4 + 2 * meshes])
        except (ValueError, IndexError) as exc:
            raise HeadArmorError("Malformed item header") from exc
        if flags & 0xF == HEAD_ARMOR_TYPE:
            ids.add(item)
    if not ids:
        raise HeadArmorError("No head-armor items found in item table")
    return ids


def apply_module(module: Path, mode: str = "removed") -> dict:
    module = Path(module)
    if mode not in ("removed", "stock"):
        raise HeadArmorError("mode must be removed or stock")
    head_ids = head_armor_ids(module)
    head_text = {str(value) for value in head_ids}
    path = module / "troops.txt"
    original = path.read_bytes()
    lines = original.decode("utf-8").splitlines(keepends=True)
    troop = -1
    changed = []
    removed = 0
    for index, raw in enumerate(lines):
        if not raw.strip().startswith("trp_"):
            continue
        troop += 1
        if not INVADER_RANGE[0] <= troop < INVADER_RANGE[1]:
            continue
        equip_index = index + 1
        equip = lines[equip_index]
        tokens = equip.strip().split()
        if len(tokens) % 2:
            raise HeadArmorError("Malformed equipment line")
        pairs = [tokens[i:i + 2] for i in range(0, len(tokens), 2)]
        removed_here = 0
        if mode == "removed":
            for pair in pairs:
                if pair[0] in head_text:
                    pair[0] = UNUSED_PAIR
                    pair[1] = "0"
                    removed_here += 1
        if removed_here:
            prefix = equip[:len(equip) - len(equip.lstrip())]
            newline = "\r\n" if equip.endswith("\r\n") else ("\n" if equip.endswith("\n") else "")
            lines[equip_index] = prefix + " ".join(
                token for pair in pairs for token in pair) + newline
            changed.append(troop)
            removed += removed_here
    if mode == "removed" and removed == 0:
        raise HeadArmorError("No invader head-armor item was removed")
    # Gate: no head-armor id remains on any invader troop.
    remaining = 0
    troop = -1
    for index, raw in enumerate(lines):
        if not raw.strip().startswith("trp_"):
            continue
        troop += 1
        if not INVADER_RANGE[0] <= troop < INVADER_RANGE[1]:
            continue
        pairs = lines[index + 1].strip().split()
        items = {pairs[i] for i in range(0, len(pairs), 2)}
        remaining += len(items & head_text)
    if mode == "removed" and remaining:
        raise HeadArmorError(f"Head armor remains on {remaining} invader pairs")
    text = "".join(lines)
    receipt = {
        "schema": "zombieee.zombie-head-armor.v1",
        "applied": True,
        "mode": mode,
        "head_armor_type": HEAD_ARMOR_TYPE,
        "head_armor_items": sorted(head_ids),
        "removed_pairs": removed,
        "changed_troops": changed,
        "remaining_head_armor_pairs": remaining,
        "item_stats_unchanged": True,
        "headshot_lethality": "expected direction only; D must validate in-game",
        "runtime_verified": False,
        "sha256_before": hashlib.sha256(original).hexdigest(),
        "sha256_after": hashlib.sha256(text.encode("utf-8")).hexdigest(),
    }
    path.write_bytes(text.encode("utf-8"))
    return receipt


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--module", type=Path, required=True)
    parser.add_argument("--mode", choices=("removed", "stock"), default="removed")
    parser.add_argument("--apply", action="store_true")
    args = parser.parse_args()
    try:
        if not args.apply:
            raise HeadArmorError("use --apply against an extracted module")
        print(json.dumps(apply_module(args.module, args.mode), indent=2))
    except (OSError, ValueError, HeadArmorError) as exc:
        print(json.dumps({"applied": False,
                          "error": type(exc).__name__ + ": " + str(exc)}))
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
