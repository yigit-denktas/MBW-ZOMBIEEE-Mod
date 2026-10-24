"""Raise survivor AI crossbow/archery proficiency.

The 2012 module treats firearms as crossbow-type weapons, so AI firearm use is
driven by the **crossbow proficiency** in the troop row (proficiencies line:
one-handed, two-handed, polearm, archery, crossbow, throwing, firearms).
This City-only patch raises archery and crossbow proficiency for the four AI
clone troops only; no item damage or flag is changed.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

from bot_loadouts import CLONES

ARCHERY_INDEX = 3
CROSSBOW_INDEX = 4
ARCHERY_DELTA = 20
CROSSBOW_DELTA = 50
CAP = 300


class ProficiencyError(ValueError):
    pass


def patch_text(text: str) -> tuple[str, dict]:
    lines = text.splitlines(keepends=True)
    changed = []
    for index, raw in enumerate(lines):
        name = raw.strip().split()[0] if raw.strip() else ""
        if name not in CLONES:
            continue
        if index + 3 >= len(lines):
            raise ProficiencyError(f"Truncated troop row for {name}")
        prof_index = index + 3
        tokens = lines[prof_index].split()
        if len(tokens) != 7:
            raise ProficiencyError(f"Unexpected proficiency row for {name}")
        try:
            values = [int(value) for value in tokens]
        except ValueError as exc:
            raise ProficiencyError("Non-numeric proficiency value") from exc
        old_arch, old_cross = values[ARCHERY_INDEX], values[CROSSBOW_INDEX]
        values[ARCHERY_INDEX] = min(CAP, old_arch + ARCHERY_DELTA)
        values[CROSSBOW_INDEX] = min(CAP, old_cross + CROSSBOW_DELTA)
        raw_prof = lines[prof_index]
        prefix = raw_prof[:len(raw_prof) - len(raw_prof.lstrip())]
        newline = "\r\n" if raw_prof.endswith("\r\n") else (
            "\n" if raw_prof.endswith("\n") else "")
        lines[prof_index] = prefix + " ".join(str(value) for value in values) + newline
        changed.append({"troop": name, "archery_before": old_arch,
                        "archery_after": values[ARCHERY_INDEX],
                        "crossbow_before": old_cross,
                        "crossbow_after": values[CROSSBOW_INDEX]})
    if len(changed) != len(CLONES):
        raise ProficiencyError(
            f"Expected {len(CLONES)} clone troops, patched {len(changed)}")
    report = {
        "schema": "zombieee.survivor-proficiency.v1",
        "applied": True,
        "firearm_class": "crossbow_type_ranged",
        "archery_delta": ARCHERY_DELTA,
        "crossbow_delta": CROSSBOW_DELTA,
        "cap": CAP,
        "changed": changed,
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
