#!/usr/bin/env python3
"""Static diagnostics for ZOMBIEEE compiled module. NOT a gameplay/runtime validation."""
import argparse
import json
from pathlib import Path

REQUIRED_TABLES = (
    "module.ini", "scripts.txt", "mission_templates.txt", "troops.txt",
    "item_kinds1.txt", "scenes.txt", "scene_props.txt", "presentations.txt",
    "variables.txt", "strings.txt",
)
REQUIRED_SCENES = tuple(f"scn_tbfc_invasion_{n}.sco" for n in range(1, 6))


def inspect_module(path: Path) -> dict:
    path = Path(path)
    tables = {name: (path / name).is_file() and (path / name).stat().st_size > 0
              for name in REQUIRED_TABLES}
    scenes = {name: (path / "SceneObj" / name).is_file() and
              (path / "SceneObj" / name).stat().st_size > 2000 for name in REQUIRED_SCENES}
    mission = path / "mission_templates.txt"
    source = mission.read_text(encoding="utf-8", errors="replace") if mission.is_file() else ""
    scenes_txt = path / "scenes.txt"
    scene_source = scenes_txt.read_text(encoding="utf-8", errors="replace") if scenes_txt.is_file() else ""
    report = {
        "path": str(path.resolve()),
        "core_tables": tables,
        "five_scene_files": scenes,
        "invasion_mission": "mst_multiplayer_iv multiplayer_iv" in source,
        "scene_ids": {f"tbfc_invasion_{i}": f"scn_tbfc_invasion_{i} " in scene_source for i in range(1, 6)},
        "lua_bootstrap": (path / "lua" / "main.lua").is_file(),
        "warning": "Static checks only: WSE2, sound, textures, gameplay and bots are untested.",
    }
    report["core_ok"] = all(tables.values()) and all(scenes.values()) and report["invasion_mission"] and all(report["scene_ids"].values())
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--module", type=Path, required=True)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    result = inspect_module(args.module)
    if args.json:
        print(json.dumps(result, indent=2))
    else:
        print(f"ZOMBIEEE static doctor: {'PASS' if result['core_ok'] else 'FAIL'}")
        for section in ("core_tables", "five_scene_files", "scene_ids"):
            missing = [name for name, ok in result[section].items() if not ok]
            print(f"  {section}: {'OK' if not missing else 'MISSING ' + ', '.join(missing)}")
        print(f"  invasion_mission: {result['invasion_mission']}")
        print(f"  lua_bootstrap: {result['lua_bootstrap']}")
        print(f"  {result['warning']}")
    raise SystemExit(0 if result["core_ok"] else 2)


if __name__ == "__main__":
    main()
