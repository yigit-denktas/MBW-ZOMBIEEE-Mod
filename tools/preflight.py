#!/usr/bin/env python3
"""Read-only checks of compiled invasion mission and module BRF references.

This cannot verify asset CRC, native game resources or WSE2 runtime compatibility.
"""
import argparse
import json
import re
from pathlib import Path

MISSION = "mst_multiplayer_iv"


def _nonempty(lines, start):
    for index in range(start, len(lines)):
        if lines[index].strip():
            return index
    raise ValueError("Unexpected end of mission_templates.txt")


def read_invasion_mission(path: Path) -> dict:
    lines = Path(path).read_text(encoding="utf-8", errors="replace").splitlines()
    headers = [i for i, line in enumerate(lines) if line.startswith(MISSION + " ")]
    if len(headers) != 1:
        raise ValueError(f"Expected one {MISSION} header, found {len(headers)}")
    index = _nonempty(lines, headers[0] + 1)  # description
    index = _nonempty(lines, index + 1)  # count + entry 0
    fields = lines[index].split()
    if len(fields) < 2 or not fields[0].isdigit():
        raise ValueError("Malformed mission entry count")
    entry_count = int(fields[0])
    if not 0 <= entry_count <= 256:
        raise ValueError("Implausible invasion entry count")
    # First entry shares the entry-count line in Warband's compiled format.
    for number in range(1, entry_count):
        index = _nonempty(lines, index + 1)
        parts = lines[index].split()
        if not parts or not parts[0].isdigit() or int(parts[0]) != number:
            raise ValueError(f"Entry point {number} missing on line {index + 1}")
    index = _nonempty(lines, index + 1)
    if not lines[index].strip().isdigit():
        raise ValueError("Malformed invasion trigger count")
    trigger_count = int(lines[index].strip())
    if not 0 <= trigger_count <= 1024:
        raise ValueError("Implausible invasion trigger count")
    intervals = []
    for _ in range(trigger_count):
        index = _nonempty(lines, index + 1)
        parts = lines[index].split()
        if len(parts) < 4:
            raise ValueError(f"Malformed trigger line {index + 1}")
        try:
            intervals.append(float(parts[0]))
            float(parts[1]); float(parts[2])
        except ValueError as exc:
            raise ValueError(f"Invalid trigger timing line {index + 1}") from exc
    return {
        "mission_id": MISSION,
        "entry_points": entry_count,
        "triggers": trigger_count,
        "intervals": intervals,
        "rapid_periodic_triggers": sum(0 <= x < 0.1 for x in intervals),
        "note": "Trigger intervals are not measurements of game performance.",
    }


def inspect_assets(module_dir: Path) -> dict:
    module_dir = Path(module_dir)
    ini = (module_dir / "module.ini").read_text(encoding="utf-8", errors="replace")
    names = [name.strip() for name in re.findall(
        r"(?m)^\s*load_mod_resource\s*=\s*([^#\r\n]+)", ini)]
    files = {file.name.lower(): file for file in (module_dir / "Resource").glob("*.brf")}
    missing, case_mismatch, duplicates = [], [], []
    seen = set()
    for name in names:
        if name.lower() in seen:
            duplicates.append(name)
        seen.add(name.lower())
        expected = name + ".brf"
        candidate = files.get(expected.lower())
        if candidate is None or candidate.stat().st_size == 0:
            missing.append(expected)
        elif candidate.name != expected:
            case_mismatch.append({"referenced": expected, "on_disk": candidate.name})
    return {
        "mod_resources_referenced": len(names),
        "mod_resources_found": len(names) - len(missing),
        "missing_mod_resources": missing,
        "case_mismatches": case_mismatch,
        "duplicate_mod_resources": duplicates,
        "native_resources": "Not checked; require original Warband installation.",
    }


def report_for_module(module_dir: Path) -> dict:
    module_dir = Path(module_dir)
    try:
        resources = inspect_assets(module_dir)
        mission = read_invasion_mission(module_dir / "mission_templates.txt")
    except (OSError, ValueError) as exc:
        return {"ok": False, "error": str(exc), "runtime_verified": False}
    problems = list(resources["missing_mod_resources"])
    if mission["triggers"] == 0:
        problems.append("Invasion mission has no triggers")
    return {
        "ok": not problems,
        "problems": problems,
        "resources": resources,
        "mission": mission,
        "runtime_verified": False,
        "warning": "Static only; RAR CRC, native assets and WSE2 gameplay require separate verification.",
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--module", type=Path, required=True)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    result = report_for_module(args.module)
    if args.json:
        print(json.dumps(result, indent=2))
    else:
        print("ZOMBIEEE preflight:", "PASS (static only)" if result["ok"] else "FAIL")
        if "error" in result:
            print(result["error"])
        else:
            print("Invasion:", result["mission"]["entry_points"], "entry points /",
                  result["mission"]["triggers"], "triggers")
            print("BRFs:", result["resources"]["mod_resources_found"], "/",
                  result["resources"]["mod_resources_referenced"])
            print("Problems:", result["problems"])
        print("Not a WSE2 runtime compatibility test")
    raise SystemExit(0 if result["ok"] else 2)


if __name__ == "__main__":
    main()
