#!/usr/bin/env python3
"""Reproduce City-only native patch-chain static acceptance from owned Beta 0.4.

Copies only the minimum original inputs to private temporary directories.
Does not extract archives, modify originals, start WSE2, or prove gameplay.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import shutil
import tempfile
from pathlib import Path

from archive_audit import inspect_original_archive
from city_acceptance import audit_city
from final_city_gate import audit_final_city_controls
from patch_defenders import (mission_bounds, patch_file, index_troops,
                             TROOP_BASE, SURVIVOR_CLASSES)
from native_roster_patch import GLOBAL_BASE, apply_module as apply_roster
from city_defense import apply_module as apply_city
from wave_reinforcements import apply_module as apply_wave
from tactical_recovery import apply_module as apply_recovery
from private_commands import apply_module as apply_private
from solo_assist import apply_module as apply_solo
from bot_loadouts import apply_module as apply_loadouts, CLONES
from firearm_balance import apply_module as apply_firearm_balance
from zombie_block import apply_module as apply_zombie_block
from trace_calls import read_mission_calls
from preflight import report_for_module

SCENE_NAMES = [f"scn_tbfc_invasion_{n}.sco" for n in range(1, 6)]
CORE_INPUTS = ["mission_templates.txt", "variables.txt", "scenes.txt", "troops.txt", "scripts.txt", "item_kinds1.txt"]


def sha(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as inp:
        for chunk in iter(lambda: inp.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def stage_source(original: Path, dest: Path) -> None:
    (dest / "SceneObj").mkdir(parents=True)
    for name in CORE_INPUTS:
        shutil.copy2(original / name, dest / name)
    for name in SCENE_NAMES:
        shutil.copy2(original / "SceneObj" / name, dest / "SceneObj" / name)


def mission_check(stage: Path, original: Path, expected: int) -> dict:
    text = (stage / "mission_templates.txt").read_text(encoding="utf-8")
    source = (original / "mission_templates.txt").read_text(encoding="utf-8")
    lines, baseline = text.splitlines(keepends=True), source.splitlines(keepends=True)
    idx, count, _ = mission_bounds(lines)
    src_idx, src_count, _ = mission_bounds(baseline)
    from trace_calls import read_mission_calls
    decoded = read_mission_calls(stage / "mission_templates.txt")
    result = {
        "expected": expected, "count": count,
        "native_stream_complete": len(decoded) == count,
        "original_25_triggers_unchanged": (
            src_count == 25 and
            [v.rstrip("\r\n") for v in lines[idx+1:idx+26]] ==
            [v.rstrip("\r\n") for v in baseline[src_idx+1:src_idx+26]]),
        "deferred_scenes_unchanged": all(
            sha(stage / "SceneObj" / name) == sha(original / "SceneObj" / name)
            for name in SCENE_NAMES if not name.endswith("_4.sco")),
        "scenes_table_unchanged": sha(stage / "scenes.txt") == sha(original / "scenes.txt"),
    }
    if not (count == expected and all(v for k, v in result.items()
                                        if k not in ("expected", "count"))):
        raise RuntimeError("City chain invariant failed after native stage " + str(expected))
    return result


def verify(original: Path, archive: Path | None = None) -> dict:
    original = Path(original)
    inputs = {name: original / name for name in CORE_INPUTS}
    inputs.update({"SceneObj/"+name: original / "SceneObj" / name for name in SCENE_NAMES})
    before = {name: sha(path) for name, path in inputs.items()}
    if any(p.is_symlink() for p in original.rglob("*")):
        raise RuntimeError("Symlink found within historical module source")
    complete_original_inventory = {
        p.relative_to(original).as_posix(): sha(p)
        for p in original.rglob("*") if p.is_file()
    }
    base = report_for_module(original)
    if not base["ok"] or base["mission"]["triggers"] != 25:
        raise RuntimeError("Original module failed source preflight")
    report = {
        "schema": "zombieee.city-chain-verification.v1",
        "runtime_verified": False,
        "historical_source": "ZOMBIEEE Beta 0.4",
        "original_files": {"files": len(before), "preserved": None},
        "original_preflight": {"ok": True, "triggers": 25,
                               "resources_found": base["resources"]["mod_resources_found"]},
        "variants": {},
        "archive": None,
    }
    if archive is not None:
        identity = inspect_original_archive(Path(archive))
        if not identity["identity_ok"]:
            raise RuntimeError("Original historical RAR identity failed")
        report["archive"] = {"sha256": identity["actual_sha256"],
                             "size": identity["actual_size"],
                             "identity_ok": True,
                             "full_member_crc": "not_checked"}
    with tempfile.TemporaryDirectory(prefix="zombieee-city-verify-") as tmp:
        root = Path(tmp)
        for variant in ("standard", "balanced-ai"):
            stage = root / variant
            if variant == "standard":
                # Full candidate mirror: prove unmodified historical assets are
                # byte-identical, not merely that the four other maps survived.
                shutil.copytree(original, stage)
            else:
                stage_source(original, stage)
            if variant == "balanced-ai":
                apply_loadouts(stage)
            firearm = apply_firearm_balance(stage, "default")
            chain = [mission_check(stage, original, 25)]
            patch_file(stage, 4, city_only=True, balanced_ai=variant == "balanced-ai")
            chain.append(mission_check(stage, original, 26))
            apply_city(stage)
            chain.append(mission_check(stage, original, 27))
            apply_wave(stage, cap=4, city_only=True,
                       balanced_ai=variant == "balanced-ai", slow_visitors=True)
            chain.append(mission_check(stage, original, 29))
            classes = CLONES if variant == "balanced-ai" else SURVIVOR_CLASSES
            troop_ids = index_troops(stage / "troops.txt")
            defense_ids = [troop_ids[name] for name in classes]
            game_type_global = GLOBAL_BASE + (stage / "variables.txt").read_text(
                encoding="utf-8").splitlines().index("g_multiplayer_game_type")
            roster = apply_roster(stage, defender_range=(min(defense_ids), max(defense_ids) + 1),
                                  game_type_global=game_type_global,
                                  invader_range=(894, 895))
            zombie = apply_zombie_block(stage)
            respawn_troops = tuple(TROOP_BASE + troop_ids[name] for name in classes)
            apply_recovery(stage, city_only=True, defender_cap=0)
            chain.append(mission_check(stage, original, 31))
            core = audit_city(stage, original)
            if not core["city_accepted"]:
                raise RuntimeError("City static contract failed: " + ", ".join(core["problems"]))
            snapshot = ((stage / "mission_templates.txt").read_bytes(),
                        (stage / "variables.txt").read_bytes(),
                        core["city_overlay_expected_sha256"])
            apply_private(stage)
            chain.append(mission_check(stage, original, 35))
            final = audit_final_city_controls(
                stage, verified_mission=snapshot[0],
                verified_variables=snapshot[1],
                verified_city_sha256=snapshot[2], private_commands=True)
            if not final["passed"]:
                raise RuntimeError("Final City hotkey gate failed: " + ", ".join(final["problems"]))
            report["variants"][variant] = {
                "chain": chain,
                "city_static_accepted": core["city_accepted"],
                "canonical_city_scene_sha256": core["city_overlay_expected_sha256"],
                "hotkey_final_accepted": final["passed"],
                "native_roster_patch": {key: roster[key] for key in
                                        ("applied", "invader_candidates",
                                         "sha256_before", "sha256_after")},
                "firearm_accuracy": {key: firearm[key] for key in
                                     ("applied", "changed_count", "automatic_items",
                                      "sha256_before", "sha256_after")},
                "zombie_block": {key: zombie[key] for key in
                                 ("applied", "shield_item", "troops",
                                  "sha256_before", "sha256_after")},
                "final_native_sha256": final["final_native_sha256"],
                "global_count": len((stage / "variables.txt").read_text().splitlines()),
                "runtime_verified": False,
            }
            if report["variants"][variant]["global_count"] != 1226:
                raise RuntimeError("Unexpected 35-trigger global count")
            if variant == "standard":
                allowed = {"mission_templates.txt", "variables.txt",
                           "scripts.txt", "item_kinds1.txt", "troops.txt",
                           "SceneObj/scn_tbfc_invasion_4.sco"}
                changed = {name for name, digest in complete_original_inventory.items()
                           if not (stage / name).is_file() or sha(stage / name) != digest}
                unexpected = changed - allowed
                if unexpected or not changed == allowed:
                    raise RuntimeError("Staged full original module asset preservation failed")
                report["variants"][variant]["asset_preservation"] = {
                    "original_files_checked": len(complete_original_inventory),
                    "untouched_files": len(complete_original_inventory) - len(changed),
                    "intentional_original_changes": sorted(changed),
                    "unexpected_changes": len(unexpected),
                    "passed": True,
                }
        solo = root / "solo-assist"
        stage_source(original, solo)
        apply_firearm_balance(solo, "default")
        patch_file(solo, 4, city_only=True)
        apply_city(solo)
        apply_wave(solo, cap=4, city_only=True, slow_visitors=True)
        solo_troops = index_troops(solo / "troops.txt")
        solo_defense_ids = [solo_troops[name] for name in SURVIVOR_CLASSES]
        solo_game_type = GLOBAL_BASE + (solo / "variables.txt").read_text(
            encoding="utf-8").splitlines().index("g_multiplayer_game_type")
        apply_roster(solo, defender_range=(min(solo_defense_ids), max(solo_defense_ids) + 1),
                     game_type_global=solo_game_type, invader_range=(894, 895))
        apply_zombie_block(solo)
        apply_recovery(solo, city_only=True, defender_cap=0)
        prior = audit_city(solo, original)
        if not prior["city_accepted"]:
            raise RuntimeError("Solo profile prerequisite failed")
        mission = (solo / "mission_templates.txt").read_bytes()
        variables = (solo / "variables.txt").read_bytes()
        apply_solo(solo)
        stage = mission_check(solo, original, 32)
        gate = audit_final_city_controls(
            solo, verified_mission=mission, verified_variables=variables,
            verified_city_sha256=prior["city_overlay_expected_sha256"], solo_assist=True)
        if not gate["passed"]:
            raise RuntimeError("Final City solo-assist gate failed")
        report["variants"]["solo-assist"] = {
            "final_native_check": stage,
            "final_accepted": gate["passed"], "global_count": len(
                (solo / "variables.txt").read_text().splitlines()),
            "runtime_verified": False,
        }
    after = {name: sha(path) for name, path in inputs.items()}
    report["original_files"]["preserved"] = before == after
    if before != after:
        raise RuntimeError("Original input files changed during verification")
    report["passed"] = True
    return report


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--original", type=Path, required=True)
    p.add_argument("--archive", type=Path)
    p.add_argument("--json", action="store_true")
    args = p.parse_args()
    try:
        result = verify(args.original, args.archive)
    except (OSError, ValueError, RuntimeError) as e:
        # No user paths or secret file contents in failure output.
        print(json.dumps({"passed": False, "runtime_verified": False,
                          "error_type": type(e).__name__, "description": "Static City verification failed"}))
        return 2
    print(json.dumps(result, indent=2, sort_keys=True) if args.json else
          "City original→26→27→29→31→35 / solo32: STATIC PASS; WSE2 UNKNOWN")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
