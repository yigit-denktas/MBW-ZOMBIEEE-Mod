"""City invader shield policy: stock (zero shields) or cosmetic-half.

Owner policy (task-83 canonical): never add ``itm_wooden_shield`` by default.
``stock`` removes every shield item (wooden/practice/zombie_hand) from invader
troops 894..911 and forces shield skill 0. ``cosmetic-half`` gives every other
invader troop ``itm_practice_shield`` as a cosmetic-only item and still forces
shield skill 0 (no block). A post-patch gate fails if a wooden shield remains,
or if any invader shield skill is >0.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

INVADER_RANGE = (894, 912)
WOODEN_SHIELD = "itm_wooden_shield"
PRACTICE_SHIELD = "itm_practice_shield"
ORIGINAL_SHIELD = "itm_zombie_hand"
REMOVED_SHIELDS = (WOODEN_SHIELD, PRACTICE_SHIELD, ORIGINAL_SHIELD)
UNUSED_PAIR = "-1"
SKILL_WORD = 26 // 8
SHIELD_SHIFT = (26 % 8) * 4
SKILL_MASK = 0xF << SHIELD_SHIFT


class ZombieBlockError(ValueError):
    pass


def item_ids(module: Path) -> dict[str, int]:
    lines = (Path(module) / "item_kinds1.txt").read_text(encoding="utf-8",
                                                       errors="replace").splitlines()
    rows = [line.strip().split() for line in lines if line.strip().startswith("itm_")]
    return {tokens[0]: index for index, tokens in enumerate(rows)}


def apply_module(module: Path, mode: str = "stock") -> dict:
    module = Path(module)
    if mode not in ("stock", "cosmetic-half"):
        raise ZombieBlockError("mode must be stock or cosmetic-half")
    ids = item_ids(module)
    for name in REMOVED_SHIELDS:
        if name not in ids:
            raise ZombieBlockError(f"Missing shield item {name}")
    wooden = ids[WOODEN_SHIELD]
    practice = ids[PRACTICE_SHIELD]
    removed_ids = {ids[name] for name in REMOVED_SHIELDS}
    removed_text = {str(value) for value in removed_ids}
    path = module / "troops.txt"
    original = path.read_bytes()
    lines = original.decode("utf-8").splitlines(keepends=True)
    troop = -1
    changed = set()
    cosmetic = []
    for index, raw in enumerate(lines):
        stripped = raw.strip()
        if not stripped.startswith("trp_"):
            continue
        troop += 1
        if not INVADER_RANGE[0] <= troop < INVADER_RANGE[1]:
            continue
        if index + 4 >= len(lines):
            raise ZombieBlockError("Truncated invader troop row")
        equip_index = index + 1
        equip = lines[equip_index]
        tokens = equip.strip().split()
        if len(tokens) % 2:
            raise ZombieBlockError("Malformed equipment line")
        pairs = [tokens[i:i + 2] for i in range(0, len(tokens), 2)]
        for pair in pairs:
            if pair[0] in removed_text:
                pair[0] = UNUSED_PAIR
                pair[1] = "0"
        if mode == "cosmetic-half" and (troop - INVADER_RANGE[0]) % 2 == 0:
            for pair in pairs:
                if pair[0] == UNUSED_PAIR:
                    pair[0] = str(practice)
                    pair[1] = "0"
                    cosmetic.append(troop)
                    break
        prefix = equip[:len(equip) - len(equip.lstrip())]
        newline = "\r\n" if equip.endswith("\r\n") else ("\n" if equip.endswith("\n") else "")
        new_equip = prefix + " ".join(token for pair in pairs for token in pair) + newline
        if new_equip != equip:
            lines[equip_index] = new_equip
            changed.add(troop)
        skill_line = lines[index + 4]
        words = skill_line.split()
        if len(words) != 6:
            raise ZombieBlockError("Unexpected compiled skill-word line")
        values = [int(word) for word in words]
        current = (values[SKILL_WORD] & SKILL_MASK) >> SHIELD_SHIFT
        if current != 0:
            values[SKILL_WORD] &= ~SKILL_MASK
            skill_prefix = skill_line[:len(skill_line) - len(skill_line.lstrip())]
            skill_newline = ("\r\n" if skill_line.endswith("\r\n")
                             else ("\n" if skill_line.endswith("\n") else ""))
            lines[index + 4] = (skill_prefix + " ".join(map(str, values))
                                + skill_newline)
            changed.add(troop)
    # Post-patch gate.
    troop = -1
    gate = {"wooden_shield": 0, "shield_skill_positive": 0, "cosmetic_mismatch": 0}
    for index, raw in enumerate(lines):
        if not raw.strip().startswith("trp_"):
            continue
        troop += 1
        if not INVADER_RANGE[0] <= troop < INVADER_RANGE[1]:
            continue
        pairs = lines[index + 1].strip().split()
        item_pairs = {pairs[i] for i in range(0, len(pairs), 2)}
        if str(wooden) in item_pairs:
            gate["wooden_shield"] += 1
        if mode == "stock" and item_pairs & removed_text:
            gate["cosmetic_mismatch"] += 1
        if mode == "cosmetic-half":
            expected = (troop - INVADER_RANGE[0]) % 2 == 0
            if (str(practice) in item_pairs) != expected:
                gate["cosmetic_mismatch"] += 1
        words = [int(word) for word in lines[index + 4].split()]
        if ((words[SKILL_WORD] & SKILL_MASK) >> SHIELD_SHIFT) > 0:
            gate["shield_skill_positive"] += 1
    if any(gate.values()):
        raise ZombieBlockError(f"Shield policy gate failed: {gate}")
    changed_text = "".join(lines)
    receipt = {
        "schema": "zombieee.zombie-shield-policy.v1",
        "applied": True,
        "mode": mode,
        "removed_shield_items": list(REMOVED_SHIELDS),
        "shield_skill": 0,
        "cosmetic_troops": cosmetic,
        "changed_troops": sorted(changed),
        "changed_count": len(changed),
        "wooden_shield_troops": [],
        "gate": "passed",
        "runtime_verified": False,
        "warning": "Stock removes all invader shields; cosmetic-half is a visual "
                   "practice shield with shield skill 0 (no block). D must confirm "
                   "no block in-game.",
        "sha256_before": hashlib.sha256(original).hexdigest(),
        "sha256_after": hashlib.sha256(changed_text.encode("utf-8")).hexdigest(),
    }
    path.write_bytes(changed_text.encode("utf-8"))
    return receipt


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--module", type=Path, required=True)
    parser.add_argument("--mode", choices=("stock", "cosmetic-half"), default="stock")
    parser.add_argument("--apply", action="store_true")
    args = parser.parse_args()
    try:
        if not args.apply:
            raise ZombieBlockError("use --apply against an extracted module")
        print(json.dumps(apply_module(args.module, args.mode), indent=2))
    except (OSError, ValueError, ZombieBlockError) as exc:
        print(json.dumps({"applied": False,
                          "error": type(exc).__name__ + ": " + str(exc)}))
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
