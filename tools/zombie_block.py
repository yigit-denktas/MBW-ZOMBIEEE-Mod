#!/usr/bin/env python3
"""City-only invader melee-block profile: give native Zombie bots a shield.

Owner's live City run showed Zombies have no block. The invader troops already
have a high shield skill (compiled troops table), but their equipment lists no
shield item, so they cannot block. This profile appends one low-tier shield
(item ``itm_wooden_shield``) to the first unused equipment pair of the
City-native invader troops only (ordinal 894..911); every other troop row is
byte-identical, and the built module is the only target.

No runtime claim: the sealed WSE2 run must confirm the engine equips the shield
and the block animation appears.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

INVADER_RANGE = (894, 912)  # native Zombie troop block
SHIELD_ITEM = "itm_wooden_shield"
UNUSED_PAIR = "-1"
SHIELD_SKILL = 5
# Compiled troop skills: six 32-bit words, four bits per skill; skill 26 = shield.
SKILL_WORD = 26 // 8          # 3
SHIELD_SHIFT = (26 % 8) * 4    # 8
SKILL_MASK = 0xF << SHIELD_SHIFT


class ZombieBlockError(ValueError):
    pass


def item_ids(module: Path) -> dict[str, int]:
    """Resolve item name -> compiled item id from item_kinds1.txt (ordinal = id)."""
    lines = (Path(module) / "item_kinds1.txt").read_text(encoding="utf-8",
                                                       errors="replace").splitlines()
    rows = [line.strip().split() for line in lines if line.strip().startswith("itm_")]
    return {tokens[0]: index for index, tokens in enumerate(rows)}


def shield_id(module: Path) -> int:
    ids = item_ids(module)
    if SHIELD_ITEM not in ids:
        raise ZombieBlockError(f"Shield item {SHIELD_ITEM} missing from the item table")
    return ids[SHIELD_ITEM]


def _equipment_line(lines: list[str], index: int) -> tuple[str, str]:
    raw = lines[index]
    prefix = raw[:len(raw) - len(raw.lstrip())]
    newline = "\r\n" if raw.endswith("\r\n") else ("\n" if raw.endswith("\n") else "")
    body = raw.strip()
    pair = body.split()
    if len(pair) < 2 or len(pair) % 2:
        raise ZombieBlockError("Malformed compiled troop equipment line")
    return prefix, newline


def patch_text(text: str, module: Path) -> tuple[str, dict]:
    shield = shield_id(module)
    lines = text.splitlines(keepends=True)
    troop = -1
    changed = []
    skill_changes = []
    for index, raw in enumerate(lines):
        stripped = raw.strip()
        if not stripped.startswith("trp_"):
            continue
        troop += 1
        if not INVADER_RANGE[0] <= troop < INVADER_RANGE[1]:
            continue
        equip_index = index + 1
        if equip_index >= len(lines):
            raise ZombieBlockError("Missing equipment line for an invader troop")
        prefix, newline = _equipment_line(lines, equip_index)
        tokens = lines[equip_index].strip().split()
        pairs = [tokens[i:i + 2] for i in range(0, len(tokens), 2)]
        if any(pair[0] == str(shield) for pair in pairs):
            changed.append(tokens[0] if tokens else str(troop))
            continue
        for pair in pairs:
            if pair[0] == UNUSED_PAIR:
                pair[0] = str(shield)
                pair[1] = "0"
                break
        else:
            raise ZombieBlockError("No unused equipment pair for an invader troop")
        flat = [token for pair in pairs for token in pair]
        lines[equip_index] = prefix + " ".join(flat) + newline
        # Shield proficiency: every invader record carries shield skill 0 in the
        # original data (E's decode: six 32-bit skill words, 4 bits per skill,
        # skill index 26 = shield). Raise the nibble to Tough-Zombie level (5).
        # header, equipment, attributes, proficiencies, then the skill words
        skills_index = equip_index + 3
        if skills_index >= len(lines):
            raise ZombieBlockError("Missing skill line for an invader troop")
        skill_line = lines[skills_index]
        skill_prefix = skill_line[:len(skill_line) - len(skill_line.lstrip())]
        skill_newline = ("\r\n" if skill_line.endswith("\r\n")
                         else ("\n" if skill_line.endswith("\n") else ""))
        words = skill_line.split()
        if len(words) != 6:
            raise ZombieBlockError("Unexpected compiled skill-word line")
        words = [int(word) for word in words]
        current = (words[SKILL_WORD] & SKILL_MASK) >> SHIELD_SHIFT
        if current < SHIELD_SKILL:
            words[SKILL_WORD] = ((words[SKILL_WORD] & ~SKILL_MASK)
                                 | (SHIELD_SKILL << SHIELD_SHIFT))
            lines[skills_index] = (skill_prefix
                                   + " ".join(map(str, words)) + skill_newline)
            skill_changes.append(stripped.split()[0])
        changed.append(stripped.split()[0])
    if len(changed) != INVADER_RANGE[1] - INVADER_RANGE[0]:
        raise ZombieBlockError("Not every invader troop received the shield")
    receipt = {
        "applied": True,
        "shield_item": SHIELD_ITEM,
        "shield_item_id": shield,
        "troop_range": list(INVADER_RANGE),
        "troops": changed,
        "changed_count": len(changed),
        "shield_skill": SHIELD_SKILL,
        "shield_skill_troops": skill_changes,
        "runtime_verified": False,
        "warning": "Static equipment addition only; the sealed WSE2 run must confirm "
                   "the engine equips the shield and block behaviour.",
    }
    return "".join(lines), receipt


def apply_module(module: Path) -> dict:
    module = Path(module)
    path = module / "troops.txt"
    original = path.read_bytes()
    text = original.decode("utf-8")
    changed, receipt = patch_text(text, module)
    receipt = dict(receipt)
    receipt["sha256_before"] = hashlib.sha256(original).hexdigest()
    receipt["sha256_after"] = hashlib.sha256(changed.encode("utf-8")).hexdigest()
    path.write_bytes(changed.encode("utf-8"))
    return receipt


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--module", type=Path, required=True)
    parser.add_argument("--apply", action="store_true")
    args = parser.parse_args()
    try:
        if args.apply:
            receipt = apply_module(args.module)
        else:
            text = (args.module / "troops.txt").read_text(encoding="utf-8")
            _, receipt = patch_text(text, args.module)
            receipt = dict(receipt, dry_run=True)
    except (OSError, ValueError, ZombieBlockError) as exc:
        print(json.dumps({"applied": False,
                          "error": type(exc).__name__ + ": " + str(exc)}))
        return 2
    print(json.dumps(receipt, indent=2))
    return 0 if receipt.get("applied") else 2


if __name__ == "__main__":
    raise SystemExit(main())
