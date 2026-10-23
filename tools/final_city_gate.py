#!/usr/bin/env python3
"""Offline post-control City integrity gate. Never WSE2 runtime evidence.

The canonical City 31-trigger profile is audited before optional host-only
controls. This gate checks that the *final* mission, globals and City scene
exactly match the audited profile plus the explicitly requested control patch.
"""
from __future__ import annotations

import hashlib
from pathlib import Path


def _digest(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def audit_final_city_controls(
    module: Path,
    *,
    verified_mission: bytes,
    verified_variables: bytes,
    verified_city_sha256: str,
    private_commands: bool = False,
    solo_assist: bool = False,
) -> dict:
    """Fail closed on any final build deviation; return path-free evidence.

    Call only after city_acceptance.audit_city returned city_accepted=True.
    Snapshots must come from the same staging directory before host controls.
    """
    result = {
        "schema": "zombieee.city-final-static.v1",
        "passed": False,
        "runtime_verified": False,
        "control_mode": ("invalid" if private_commands and solo_assist else
                         "private-commands" if private_commands else
                         "solo-assist" if solo_assist else "none"),
        "checks": {},
        "problems": [],
    }

    def check(name: str, correct: bool, error: str) -> None:
        result["checks"][name] = bool(correct)
        if not correct:
            result["problems"].append(error)

    if private_commands and solo_assist:
        result["problems"].append("Conflicting host-control modes")
        return result

    try:
        source_mission = verified_mission.decode("utf-8")
        source_variables = verified_variables.decode("utf-8")
        if private_commands:
            from private_commands import patch_text
            expected_mission, expected_variables = patch_text(
                source_mission, source_variables)
        elif solo_assist:
            from solo_assist import patch_text
            expected_mission, _ = patch_text(source_mission)
            expected_variables = source_variables
        else:
            expected_mission = source_mission
            expected_variables = source_variables

        expected_mission_bytes = expected_mission.encode("utf-8")
        expected_variable_bytes = expected_variables.encode("utf-8")
        folder = Path(module)
        observed_mission = (folder / "mission_templates.txt").read_bytes()
        observed_variables = (folder / "variables.txt").read_bytes()
        observed_city = (folder / "SceneObj" /
                         "scn_tbfc_invasion_4.sco").read_bytes()

        check("final_native_mission_exact",
              observed_mission == expected_mission_bytes,
              "Final invasion mission differs from approved City + selected controls")
        check("final_variable_table_exact",
              observed_variables == expected_variable_bytes,
              "Final variables differ from approved City + selected controls")
        check("final_city_scene_unchanged",
              _digest(observed_city) == verified_city_sha256,
              "City scene changed after the canonical overlay was audited")
        result["final_native_sha256"] = _digest(observed_mission)
        result["final_variables_sha256"] = _digest(observed_variables)
        result["final_city_sha256"] = _digest(observed_city)
    except (OSError, ValueError, UnicodeError, ImportError) as exc:
        # Avoid leaking exception strings containing absolute user paths.
        result["problems"].append(
            "Unable to validate final City build: " + type(exc).__name__)
    result["passed"] = not result["problems"]
    return result
