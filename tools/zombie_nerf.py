"""City-only zombie HP/skill nerf (task-81).

Warband troops have no direct hit-point field; troop HP is derived from
strength (35 + 2*strength in the 2012 module convention). This tool lowers
strength toward 65% HP and halves weapon proficiencies for the invader troops
894..912 only. Armor/headshot lethality are not changed here (receipt gap).
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

INVADER_MIN = 894
INVADER_MAX = 912
HP_FACTOR = 0.675
SKILL_FACTOR = 0.5
HP_BASE = 35


class ZombieNerfError(ValueError):
    pass


def _hp(strength: int) -> int:
    return HP_BASE + 2 * strength


def patch_text(text: str) -> tuple[str, dict]:
    lines = text.splitlines(keepends=True)
    # Build id->name directly from this text.
    name_to_id = {}
    for raw in lines:
        s = raw.strip()
        if s.startswith("trp_"):
            name_to_id[s.split()[0]] = len(name_to_id)
    id_to_name = {value: key for key, value in name_to_id.items()}
    targets = {id_to_name[i] for i in range(INVADER_MIN, INVADER_MAX + 1)
               if i in id_to_name}
    if len(targets) < 10:
        raise ZombieNerfError(f"Expected invader troop block, found {len(targets)}")
    changed = []
    for index, raw in enumerate(lines):
        name = raw.strip().split()[0] if raw.strip() else ""
        if name not in targets:
            continue
        if index + 3 >= len(lines):
            raise ZombieNerfError(f"Truncated troop row {name}")
        attr_tokens = lines[index + 2].split()
        prof_tokens = lines[index + 3].split()
        if len(attr_tokens) != 5 or len(prof_tokens) != 7:
            raise ZombieNerfError(f"Unexpected troop stats for {name}")
        attrs = [int(v) for v in attr_tokens]
        profs = [int(v) for v in prof_tokens]
        old_str = attrs[0]
        old_hp = _hp(old_str)
        new_str = max(0, round((old_hp * HP_FACTOR - HP_BASE) / 2))
        attrs[0] = new_str
        attrs[1] = max(0, attrs[1] // 2)
        new_profs = [max(0, int(v * SKILL_FACTOR)) if i < 6 else v
                     for i, v in enumerate(profs)]
        lines[index + 2] = " ".join(str(v) for v in attrs) + (
            "\r\n" if lines[index + 2].endswith("\r\n") else "\n")
        lines[index + 3] = " ".join(str(v) for v in new_profs) + (
            "\r\n" if lines[index + 3].endswith("\r\n") else "\n")
        changed.append({"troop": name, "strength_before": old_str,
                        "strength_after": new_str,
                        "hp_before": old_hp, "hp_after": _hp(new_str),
                        "hp_ratio": round(_hp(new_str) / old_hp, 3),
                        "proficiency_factor": SKILL_FACTOR})
    if len(changed) < 10:
        raise ZombieNerfError("Invader HP/skill patch incomplete")
    report = {
        "schema": "zombieee.zombie-nerf.v1",
        "applied": True,
        "hp_factor_target": HP_FACTOR,
        "hp_formula": "35 + 2*strength (2012 module convention)",
        "proficiency_factor": SKILL_FACTOR,
        "changed_count": len(changed),
        "changed": changed,
        "armor_unchanged": True,
        "headshot_lethality": "not changed in this build; separate item/armor task",
        "runtime_verified": False,
    }
    return "".join(lines), report


def apply_module(module: Path) -> dict:
    path = Path(module) / "troops.txt"
    original = path.read_bytes()
    changed, report = patch_text(original.decode("utf-8"))
    report["sha256_before"] = hashlib.sha256(original).hexdigest()
    report["sha256_after"] = hashlib.sha256(changed.encode("utf-8")).hexdigest()
    path.write_bytes(changed.encode("utf-8"))
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--module", type=Path, required=True)
    parser.add_argument("--apply", action="store_true")
    args = parser.parse_args()
    if args.apply:
        print(json.dumps(apply_module(args.module), indent=2))
    else:
        text = (args.module / "troops.txt").read_text(encoding="utf-8")
        _, report = patch_text(text)
        report["dry_run"] = True
        print(json.dumps(report, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
