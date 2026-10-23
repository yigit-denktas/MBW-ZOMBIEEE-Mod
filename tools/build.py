#!/usr/bin/env python3
"""Prepare a clean ZOMBIEEE remaster install from a verified historical RAR.

Requires 7-Zip; does not modify or redistribute the original mod archive.
This is an installation scaffold, not proof that gameplay works on WSE2.
"""
import argparse
import hashlib
import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

from doctor import inspect_module
from preflight import report_for_module
from patch_defenders import patch_file
from city_defense import apply_module as apply_city_defense
from all_map_defense import apply_module as apply_all_maps
from wave_reinforcements import apply_module as apply_wave_support
from tactical_recovery import apply_module as apply_tactical_recovery
from bot_loadouts import apply_module as apply_balanced_ai_loadouts
from solo_assist import apply_module as apply_solo_assist
from private_commands import apply_module as apply_private_commands
from difficulty import profile, PROFILES
from archive_audit import inspect_original_archive

ROOT = Path(__file__).resolve().parent.parent
ORIGINAL_SHA256 = "9be100ff41ce6f8ebadd4aa27377f70f402883fab271999a8cab8cc1da001d1e"
MODULE_NAME = "ZOMBIEEE_Remaster"


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def find_7zip() -> str:
    for name in ("7zz", "7z", "7za", "7z.exe", "7zz.exe"):
        found = shutil.which(name)
        if found:
            return found
    for path in (
        Path(r"C:\Program Files\7-Zip\7z.exe"),
        Path(r"C:\Program Files (x86)\7-Zip\7z.exe"),
    ):
        if path.is_file():
            return str(path)
    raise RuntimeError("7-Zip not found: install 7-Zip and put 7z on PATH")


def run7(exe: str, command: str, archive: Path, output: Path | None = None) -> None:
    cmd = [exe, command, "-y", str(archive)]
    if output is not None:
        cmd.append(f"-o{output}")
    print("Running:", exe, command, "<source RAR>", flush=True)
    subprocess.run(cmd, check=True)


def rename_module_title(module_ini: Path) -> None:
    text = module_ini.read_text(encoding="utf-8", errors="replace")
    rows = text.splitlines(keepends=True)
    matched = [i for i, row in enumerate(rows) if row.strip().startswith("module_name") and "=" in row]
    if len(matched) != 1:
        raise ValueError("Expected exactly one module_name = entry in module.ini")
    ending = "\r\n" if rows[matched[0]].endswith("\r\n") else "\n"
    rows[matched[0]] = "module_name = ZOMBIEEE Remaster" + ending
    module_ini.write_text("".join(rows), encoding="utf-8")


def apply_overlay(module_dir: Path) -> None:
    for path in (ROOT / "overlay").rglob("*"):
        if path.is_file():
            destination = module_dir / path.relative_to(ROOT / "overlay")
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(path, destination)
    rename_module_title(module_dir / "module.ini")


def build(archive: Path, out: Path, replace: bool = False, experimental_defenders: int = 0,
          city_guardposts: bool = False, all_map_defenses: bool = False,
          wave_reinforcements: bool = False, tactical_recovery: bool = False,
          defender_loadouts: str = "original", solo_assist: bool = False,
          private_commands: bool = False, difficulty: str = "standard") -> dict:
    support = profile(difficulty)
    if difficulty != "standard" and not wave_reinforcements:
        raise ValueError("Nonstandard difficulty needs --wave-reinforcements")
    if private_commands and not tactical_recovery:
        raise ValueError("--private-commands requires --tactical-recovery and solo host")
    if private_commands and solo_assist:
        raise ValueError("Use --private-commands or --solo-assist, not both")
    if not 0 <= experimental_defenders <= 8:
        raise ValueError("--experimental-defenders must be between 0 and 8")
    if defender_loadouts not in ("original", "balanced-ai"):
        raise ValueError("Unknown --defender-loadouts profile")
    if defender_loadouts != "original" and not experimental_defenders:
        raise ValueError("AI-only loadouts require experimental defenders")
    if tactical_recovery and not wave_reinforcements:
        raise ValueError("--tactical-recovery requires --wave-reinforcements")
    if tactical_recovery and experimental_defenders < 3:
        raise ValueError("--tactical-recovery requires at least 3 experimental defenders")
    if wave_reinforcements and not (city_guardposts or all_map_defenses):
        raise ValueError("--wave-reinforcements requires --city-guardposts or --all-map-defenses")
    city_guardposts = city_guardposts or all_map_defenses
    if city_guardposts and not experimental_defenders:
        raise ValueError("Defence positions require --experimental-defenders 1..8")
    archive = archive.expanduser().resolve(strict=True)
    out = out.expanduser().resolve()
    if out.name != MODULE_NAME:
        raise ValueError(f"Output directory must be named {MODULE_NAME}: {out}")
    if out.exists() and not replace:
        raise FileExistsError(f"Destination already exists (use --replace after backup): {out}")
    # Identity (RAR signature, pinned size and SHA-256) is separate from
    # per-member CRC verification. The installer receipt records both.
    identity = inspect_original_archive(archive)
    if not identity["identity_ok"]:
        raise ValueError("Original RAR identity failed: " + ", ".join(identity["problems"]))
    digest = identity["actual_sha256"]

    exe = find_7zip()
    run7(exe, "t", archive)
    out.parent.mkdir(parents=True, exist_ok=True)

    with tempfile.TemporaryDirectory(prefix="zombieee-extract-") as td:
        stage = Path(td)
        run7(exe, "x", archive, stage)
        source = stage / "ZOMBIEEE"
        if not source.is_dir():
            raise RuntimeError("Original root folder ZOMBIEEE missing after extraction")
        if not inspect_module(source)["core_ok"]:
            raise RuntimeError("Core original files/mission/five map files failed validation")
        preflight = report_for_module(source)
        if not preflight["ok"]:
            raise RuntimeError("Mission/resource preflight failed: " +
                               str(preflight.get("problems", preflight.get("error"))))
        apply_overlay(source)
        balanced = defender_loadouts == "balanced-ai"
        loadout_report = apply_balanced_ai_loadouts(source) if balanced else None
        defender_report = None
        if experimental_defenders:
            defender_report = patch_file(source, experimental_defenders, balanced_ai=balanced)
            updated = report_for_module(source)
            if not updated["ok"] or updated["mission"]["triggers"] != 26:
                raise RuntimeError("Experimental defender patch failed post-apply diagnostics")
        city_report = None
        if city_guardposts:
            city_report = apply_city_defense(source)
            updated = report_for_module(source)
            if not updated["ok"] or updated["mission"]["triggers"] != 27:
                raise RuntimeError("City defence failed static post-apply validation")
        all_maps_report = None
        if all_map_defenses:
            all_maps_report = apply_all_maps(source)
            updated = report_for_module(source)
            if not updated["ok"] or updated["mission"]["triggers"] != 27:
                raise RuntimeError("Five-map defence failed static validation")
        wave_report = None
        if wave_reinforcements:
            wave_report = apply_wave_support(source, cap=experimental_defenders,
                                             balanced_ai=balanced,
                                             first_wave=support.first_reinforcement_wave,
                                             city_only=not all_map_defenses)
            updated = report_for_module(source)
            if not updated["ok"] or updated["mission"]["triggers"] != 29:
                raise RuntimeError("Wave reinforcement failed static post-apply validation")
        recovery_report = None
        if tactical_recovery:
            recovery_report = apply_tactical_recovery(source,
                low_water=support.fallback_at_or_below,
                high_water=support.regroup_at_or_above,
                city_only=not all_map_defenses)
            updated = report_for_module(source)
            if not updated["ok"] or updated["mission"]["triggers"] != 31:
                raise RuntimeError("Tactical recovery failed static post-apply validation")
        solo_report = None
        if solo_assist:
            solo_report = apply_solo_assist(source)
            updated = report_for_module(source)
            expect = (31 if tactical_recovery else 29 if wave_reinforcements else
                      27 if city_guardposts else 26 if experimental_defenders else 25) + 1
            if not updated["ok"] or updated["mission"]["triggers"] != expect:
                raise RuntimeError("Host-only solo assist failed static post-apply diagnostics")
        private_report = None
        if private_commands:
            private_report = apply_private_commands(source)
            updated = report_for_module(source)
            if not updated["ok"] or updated["mission"]["triggers"] != 35:
                raise RuntimeError("Private hotkey commands failed static validation")
        if not inspect_module(source)["core_ok"] or not (source / "lua" / "main.lua").is_file():
            raise RuntimeError("Module overlay failed static validation")
        (source / "ZOMBIEEE_REMASTER.json").write_text(json.dumps({
            "remaster_version": (ROOT / "VERSION").read_text().strip(),
            "source_archive_sha256": digest,
            "target": "Warband 1.174 core / WSE2 1.1.5.4",
            "runtime_verified": False,
            "archive_crc_verified": True,
            "archive_identity": identity,
            "original_mission_trigger_count": preflight["mission"]["triggers"],
            "final_trigger_count": (31 if tactical_recovery else 29 if wave_reinforcements else 27 if city_guardposts else 26 if experimental_defenders else 25) + int(solo_assist) + (4 if private_commands else 0),
            "preflight": preflight,
            "experimental_defender_patch": defender_report,
            "defender_loadout_profile": defender_loadouts,
            "ai_only_loadout_clones": loadout_report,
            "solo_assist": solo_report,
            "private_commands": private_report,
            "difficulty": support.name,
            "difficulty_parameters": {"first_reinforcement_wave": support.first_reinforcement_wave,
                                      "fallback_at_or_below": support.fallback_at_or_below,
                                      "regroup_at_or_above": support.regroup_at_or_above},
            "experimental_map_scope": ("all-original-maps" if all_map_defenses
                                       else "city-only" if city_guardposts
                                       else "original-baseline"),
            "experimental_city_guardposts": city_report,
            "experimental_all_map_defenses": all_maps_report,
            "experimental_wave_reinforcements": wave_report,
            "experimental_tactical_recovery": recovery_report,
        }, indent=2) + "\n", encoding="utf-8")

        # Stage the final copy on the destination volume and replace atomically.
        with tempfile.TemporaryDirectory(prefix="zombieee-install-", dir=out.parent) as temp:
            candidate = Path(temp) / MODULE_NAME
            shutil.copytree(source, candidate)
            previous = None
            if out.exists():
                previous = out.with_name(out.name + ".previous")
                if previous.exists():
                    raise FileExistsError(f"Existing rollback directory must be handled first: {previous}")
                out.rename(previous)
            try:
                candidate.rename(out)
            except BaseException:
                if previous and previous.exists() and not out.exists():
                    previous.rename(out)
                raise
            else:
                if previous:
                    print(f"Previous module retained at {previous}")
    return {"module": str(out), "source_sha256": digest, "static_validation": "PASS", "experimental_defenders": experimental_defenders, "city_guardposts": city_guardposts, "all_map_defenses": all_map_defenses,
            "wave_reinforcements": wave_reinforcements, "tactical_recovery": tactical_recovery,
            "experimental_map_scope": ("all-original-maps" if all_map_defenses
                                        else "city-only" if city_guardposts
                                        else "original-baseline"),
            "defender_loadouts": defender_loadouts, "solo_assist": solo_assist,
            "private_commands": private_commands, "difficulty": difficulty,
            "runtime_verified": False}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--archive", required=True, type=Path)
    parser.add_argument("--out", required=True, type=Path)
    parser.add_argument("--replace", action="store_true")
    parser.add_argument("--experimental-defenders", type=int, default=0, metavar="N", help="Opt-in 1–8 allied bots; default 0 preserves original mission")
    parser.add_argument("--city-guardposts", action="store_true", help="Optional guarded City tactical post overlay")
    parser.add_argument("--all-map-defenses", action="store_true", help="Experimental original five-map tactical overlays; implies City posts")
    parser.add_argument("--wave-reinforcements", action="store_true", help="Once-per-wave defender top-up, for City-only or all-map tactical overlays")
    parser.add_argument("--tactical-recovery", action="store_true", help="Fallback/regroup server AI with hysteresis (requires 3+ defenders and wave reinforcements)")
    parser.add_argument("--defender-loadouts", choices=("original", "balanced-ai"), default="original", help="Append balanced AI-only troop clones without changing player classes")
    parser.add_argument("--solo-assist", action="store_true", help="EXPERIMENTAL: only local non-dedicated host in a 1-player session gets periodic health/ammo")
    parser.add_argument("--private-commands", action="store_true", help="EXPERIMENTAL solo listen-host-only Ctrl+F7/F8/F9 actions, audited by counters")
    parser.add_argument("--difficulty", choices=tuple(PROFILES), default="standard", help="Survivor-support difficulty: controls reinforcement wave and fallback thresholds")
    args = parser.parse_args()
    try:
        print(json.dumps(build(args.archive, args.out, args.replace, args.experimental_defenders,
                         args.city_guardposts, args.all_map_defenses, args.wave_reinforcements,
                         args.tactical_recovery, args.defender_loadouts, args.solo_assist,
                         args.private_commands, args.difficulty), indent=2))
    except (RuntimeError, FileNotFoundError, FileExistsError, ValueError, subprocess.CalledProcessError) as exc:
        print(f"Build refused: {exc}", file=sys.stderr)
        raise SystemExit(2)


if __name__ == "__main__":
    main()
