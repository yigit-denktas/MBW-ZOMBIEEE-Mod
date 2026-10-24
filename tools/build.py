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
from patch_defenders import patch_file, index_troops, TROOP_BASE, SURVIVOR_CLASSES
from native_roster_patch import GLOBAL_BASE, apply_module as apply_native_roster
from city_defense import (GUARD_ENTRIES, REAR_HOLD_ENTRIES,
                          apply_module as apply_city_defense)
from all_map_defense import apply_module as apply_all_maps
from wave_reinforcements import apply_module as apply_wave_support
from tactical_recovery import apply_module as apply_tactical_recovery
from bot_loadouts import apply_module as apply_balanced_ai_loadouts
from firearm_balance import apply_module as apply_firearm_balance
from zombie_block import apply_module as apply_zombie_block
from solo_assist import apply_module as apply_solo_assist
from private_commands import apply_module as apply_private_commands
from difficulty import profile, PROFILES
from archive_audit import inspect_original_archive
from city_acceptance import audit_city
from final_city_gate import audit_final_city_controls

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
          private_commands: bool = False, difficulty: str = "standard",
          firearm_accuracy: str = "default",
          zombie_bot_roster: str = "weak", zombie_block: str = "default",
          defensive_line: str = "rear") -> dict:
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
    if firearm_accuracy not in ("default", "stock"):
        raise ValueError("Unknown --firearm-accuracy profile")
    if zombie_bot_roster not in ("weak", "full"):
        raise ValueError("Unknown --zombie-bot-roster profile")
    if zombie_block not in ("default", "stock"):
        raise ValueError("Unknown --zombie-block profile")
    if defensive_line not in ("rear", "forward"):
        raise ValueError("Unknown --defensive-line profile")
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
        # Preserve a minimal, private source evidence copy BEFORE applying
        # any gameplay overlay. The stage and evidence are both deleted on
        # failure; original user files remain untouched. Use this for the
        # complete City tactical profile, including optional host controls.
        audit_city_profile = city_guardposts and tactical_recovery and not all_map_defenses
        original_evidence = None
        if audit_city_profile:
            original_evidence = stage / "original-city-evidence"
            (original_evidence / "SceneObj").mkdir(parents=True)
            for name in ("mission_templates.txt", "scenes.txt", "variables.txt"):
                shutil.copy2(source / name, original_evidence / name)
            for n in range(1, 6):
                scene_name = f"scn_tbfc_invasion_{n}.sco"
                shutil.copy2(source / "SceneObj" / scene_name,
                             original_evidence / "SceneObj" / scene_name)
        apply_overlay(source)
        balanced = defender_loadouts == "balanced-ai"
        loadout_report = apply_balanced_ai_loadouts(source) if balanced else None
        # Default build profile: automatic firearms get a modest accuracy buff;
        # single-shot firearms and every non-firearm item keep their stats.
        firearm_report = apply_firearm_balance(source, firearm_accuracy)
        if (firearm_accuracy == "default" and
                firearm_report.get("changed_count") !=
                len(firearm_report["automatic_items"])):
            raise RuntimeError("Firearm accuracy profile did not patch every automatic weapon")
        # City-only native roster fix: the compiled Native bot-troop script can
        # only see the 2012 multiplayer-AI troop block, so the invader faction's
        # appended Zombie troops are otherwise unreachable and team 2 spawns
        # Crazed Civilian placeholders. Apply before the mission overlays; this
        # changes compiled scripts only and is recorded in the receipt.
        city_roster_profile = city_guardposts and not all_map_defenses
        roster_report = None
        zombie_block_report = None
        if city_roster_profile:
            # City builds also use the native bot-spawn path for the allied squad
            # (D's sealed run: native team-0 bots spawn, team-0 add_visitors do not).
            defender_range = None
            game_type_global = None
            if experimental_defenders:
                from bot_loadouts import CLONES
                classes = CLONES if balanced else SURVIVOR_CLASSES
                troop_ids = index_troops(source / "troops.txt")
                ids = [troop_ids[name] for name in classes]
                if ids != list(range(min(ids), max(ids) + 1)):
                    raise RuntimeError("Defender troop ids are not a contiguous native-bot range")
                defender_range = (min(ids), max(ids) + 1)
                variables = (source / "variables.txt").read_text(encoding="utf-8").splitlines()
                if "g_multiplayer_game_type" not in variables:
                    raise RuntimeError("Missing g_multiplayer_game_type for defender roster")
                game_type_global = GLOBAL_BASE + variables.index("g_multiplayer_game_type")
            invader_range = ((894, 895) if zombie_bot_roster == "weak"
                             else (894, 912))
            roster_report = apply_native_roster(source, defender_range=defender_range,
                                                game_type_global=game_type_global,
                                                invader_range=invader_range)
            if not roster_report.get("applied") or not roster_report.get("invader_candidates"):
                raise RuntimeError("Native Zombie roster patch failed static validation")
            if defender_range and not roster_report.get("defender_candidates"):
                raise RuntimeError("Native defender roster range has no faction-15 troops")
            if zombie_block == "default":
                zombie_block_report = apply_zombie_block(source)
                if (not zombie_block_report.get("applied")
                        or not zombie_block_report.get("troops")):
                    raise RuntimeError("Zombie shield/block patch failed static validation")
        defender_report = None
        if experimental_defenders:
            defender_report = patch_file(source, experimental_defenders,
                                         balanced_ai=balanced,
                                         city_only=city_guardposts and not all_map_defenses)
            updated = report_for_module(source)
            if not updated["ok"] or updated["mission"]["triggers"] != 26:
                raise RuntimeError("Experimental defender patch failed post-apply diagnostics")
        city_report = None
        if city_guardposts:
            city_report = apply_city_defense(
                source, REAR_HOLD_ENTRIES if defensive_line == "rear" else GUARD_ENTRIES)
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
            defender_cap = experimental_defenders if city_roster_profile else 0
            defender_troops = ()
            if defender_cap:
                from bot_loadouts import CLONES
                classes = CLONES if balanced else SURVIVOR_CLASSES
                troop_ids = index_troops(source / "troops.txt")
                defender_troops = tuple(TROOP_BASE + troop_ids[name] for name in classes)
            recovery_report = apply_tactical_recovery(source,
                low_water=support.fallback_at_or_below,
                high_water=support.regroup_at_or_above,
                city_only=not all_map_defenses,
                defender_cap=defender_cap,
                defender_troops=defender_troops)
            updated = report_for_module(source)
            if not updated["ok"] or updated["mission"]["triggers"] != 31:
                raise RuntimeError("Tactical recovery failed static post-apply validation")
        # Fail closed on a structurally damaged City patch BEFORE adding the
        # optional private controls. At this point the complete native City
        # build must have 31 triggers. The checker also ensures that the
        # original 25 triggers, all four non-City scenes, and the canonical
        # City SCO geometry still match the original source.
        city_static_report = None
        if audit_city_profile:
            city_static_report = audit_city(source, original_evidence)
            if not city_static_report["city_accepted"]:
                raise RuntimeError("City static acceptance failed: " +
                                   ", ".join(city_static_report["problems"]))
        # Freeze the fully audited 31-trigger City core before any optional
        # host controls append native triggers or global variables.
        verified_city_snapshot = None
        if city_static_report is not None:
            verified_city_snapshot = (
                (source / "mission_templates.txt").read_bytes(),
                (source / "variables.txt").read_bytes(),
                city_static_report["city_overlay_expected_sha256"],
            )
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
        # A pre-control City PASS is not sufficient to certify the final
        # installation. Replay the explicitly selected additive host-control
        # patch against the frozen audited core and compare COMPLETE bytes.
        # In particular reject mutations to the original/native tactical
        # triggers, appended globals, or City SCO after the earlier audit.
        city_final_report = None
        if verified_city_snapshot is not None:
            city_final_report = audit_final_city_controls(
                source,
                verified_mission=verified_city_snapshot[0],
                verified_variables=verified_city_snapshot[1],
                verified_city_sha256=verified_city_snapshot[2],
                private_commands=private_commands,
                solo_assist=solo_assist,
            )
            if not city_final_report["passed"]:
                raise RuntimeError("Final City static gate failed: " +
                                   ", ".join(city_final_report["problems"]))
        if not inspect_module(source)["core_ok"] or not (source / "lua" / "main.lua").is_file():
            raise RuntimeError("Module overlay failed static validation")
        (source / "ZOMBIEEE_REMASTER.json").write_text(json.dumps({
            "remaster_version": (ROOT / "VERSION").read_text().strip(),
            "source_archive_sha256": digest,
            "target": "Warband 1.174 core / WSE2 1.1.5.4",
            "runtime_verified": False,
            "archive_crc_verified": True,
            "archive_identity": identity,
            "city_static_acceptance": ({"checks": city_static_report["checks"],
                "original_invasion_game_type": city_static_report.get("original_invasion_game_type"),
                "city_overlay_expected_sha256": city_static_report.get("city_overlay_expected_sha256"),
                "city_overlay_actual_sha256": city_static_report.get("city_overlay_actual_sha256"),
                "runtime_verified": False} if city_static_report else None),
            "city_final_acceptance": city_final_report,
            "original_mission_trigger_count": preflight["mission"]["triggers"],
            "final_trigger_count": (31 if tactical_recovery else 29 if wave_reinforcements else 27 if city_guardposts else 26 if experimental_defenders else 25) + int(solo_assist) + (4 if private_commands else 0),
            "preflight": preflight,
            "native_roster_patch": roster_report,
            "firearm_accuracy": firearm_report,
            "zombie_bot_roster": zombie_bot_roster,
            "zombie_block": zombie_block_report,
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
    parser.add_argument("--firearm-accuracy", choices=("default", "stock"), default="default", help="Default build profile buffs automatic firearm accuracy (+5..10 pts); stock keeps original stats")
    parser.add_argument("--zombie-bot-roster", choices=("weak", "full"), default="weak", help="City generic invader bots: weak original Zombie 894 only or full native 894..911 roster")
    parser.add_argument("--zombie-block", choices=("default", "stock"), default="default", help="Give City invader troops a shield for block capability; stock keeps original equipment")
    parser.add_argument("--defensive-line", choices=("rear", "forward"), default="rear", help="City defender hold line: rear/spawn line (default) or the old forward guard sectors")
    args = parser.parse_args()
    try:
        print(json.dumps(build(args.archive, args.out, args.replace, args.experimental_defenders,
                         args.city_guardposts, args.all_map_defenses, args.wave_reinforcements,
                         args.tactical_recovery, args.defender_loadouts, args.solo_assist,
                         args.private_commands, args.difficulty, args.firearm_accuracy,
                         args.zombie_bot_roster, args.zombie_block, args.defensive_line), indent=2))
    except (RuntimeError, FileNotFoundError, FileExistsError, ValueError, subprocess.CalledProcessError) as exc:
        print(f"Build refused: {exc}", file=sys.stderr)
        raise SystemExit(2)


if __name__ == "__main__":
    main()
