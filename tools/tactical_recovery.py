#!/usr/bin/env python3
"""Opt-in tactical fallback/regroup for original Beta 0.4 compiled missions.

Appends two native triggers after the already patched 29-trigger, 1222-global
module. It never replaces the original 25 invasion triggers. A periodic
server-only trigger counts living non-player allied agents in divisions 5..7.

Living allies <= low_water: fallback to survivor entry 0.
Living allies >= high_water: regroup at current map's guarded positions.
State changes once per transition to avoid thrashing and order spam.
With ``defender_cap`` the same periodic trigger also restores missing private
survivor divisions (bounded top-up) so the one-shot mission-start spawn cannot
leave the squad permanently absent after a dedicated round reset.
"""
from pathlib import Path
from patch_defenders import PatchError, mission_bounds
from city_defense import scene_index, SCENE_BASE, POS_BASE, DIVISIONS
from wave_reinforcements import (GLOBAL_BASE, LOCAL_BASE, SENTINEL, ROUND_STAMP,
                                 INVASION_GAME_TYPE)

TACTICAL_GLOBAL = "zdr_defence_mode"
EXPECTED_PREVIOUS_GLOBALS = 1222
EXPECTED_PREVIOUS_TRIGGERS = 29


def encode(opcode: int, *args: int) -> list[str]:
    return [str(opcode), str(len(args)), *(str(arg) for arg in args)]


def mapping(variables: str) -> dict[str, int]:
    names = variables.splitlines()
    if (len(names) != EXPECTED_PREVIOUS_GLOBALS or
            names[-2:] != [SENTINEL, ROUND_STAMP] or TACTICAL_GLOBAL in names or
            len(set(names)) != len(names)):
        raise PatchError("Requires unmodified 1222-name remaster wave-variable table")
    needed = ("g_multiplayer_game_type", "g_round_ended", "wave_number")
    if any(name not in names for name in needed):
        raise PatchError("Original mission state globals missing")
    return {name: GLOBAL_BASE + names.index(name) for name in needed} | {
        TACTICAL_GLOBAL: GLOBAL_BASE + len(names)}


def initial_mode(mode: int) -> str:
    return " ".join(["-20.000000", "0.000000", "0.000000",
                     "1", *encode(417), "1", *encode(2133, mode, 0)])


def recovery_trigger(globals_: dict[str, int], scenes: dict[int, int],
                     low_water: int = 1, high_water: int = 3,
                     defender_cap: int = 0,
                     defender_troops: tuple[int, ...] = ()) -> str:
    if not (0 <= low_water < high_water <= 8):
        raise PatchError("Require 0 <= low_water < high_water <= 8")
    if defender_cap and (not 1 <= defender_cap <= 8 or len(defender_troops) != 4):
        raise PatchError("Defender respawn needs cap 1..8 and four troop operands")
    supported = set(scenes)
    if supported not in ({4}, set(range(1, 6))):
        raise PatchError("Recovery requires original City only or all five map indices")
    if len(set(scenes.values())) != len(scenes):
        raise PatchError("Duplicate scene indices")
    local = [LOCAL_BASE + i for i in range(11)]
    conditions = [
        encode(417),  # server only
        encode(31, globals_["g_multiplayer_game_type"], INVASION_GAME_TYPE),  # original Invasion
        encode(31, globals_["g_round_ended"], 0),
        encode(30, globals_["wave_number"], 1),
    ]
    if supported == {4}:
        conditions.extend([
            encode(2211, LOCAL_BASE + 8),  # store current scene
            encode(31, LOCAL_BASE + 8, SCENE_BASE + scenes[4]),
        ])
    body = [
        encode(2133, local[0], 0),
        encode(12, local[1]),       # for agents
        encode(1702, local[1]),     # alive
        encode(1707, local[1]),     # non-player
        encode(1770, local[2], local[1]),  # team
        encode(31, local[2], 0),    # survivor team
        encode(1765, local[3], local[1]),  # division
        encode(33, local[3], 5, 8),  # reserved divisions only
        encode(2105, local[0], 1),
        encode(3),                  # end for
    ]
    if defender_cap:
        # Periodic round-aware respawn of the private survivor squad. The
        # original one-shot -20 spawn fires before the dedicated mission's
        # round reset and can be cleared; this top-up runs every 3 s while the
        # round is active, restoring missing private survivor divisions.
        body.extend([
            encode(4),                              # try_begin
            encode(2121, local[5], defender_cap, local[0]),  # missing = cap - living
            encode(32, local[5], 0),                # gt missing 0
            encode(6, local[6], 0, local[5]),       # for replacement index
            encode(2120, local[7], local[0], local[6]),  # slot = living + i
            encode(2119, local[8], local[7], 4),    # class = slot % 4
            encode(2119, local[9], local[7], 2),    # entry = slot % 2
            encode(2119, local[10], local[7], 3),   # group offset = slot % 3
            encode(2120, local[10], local[10], 5),  # reserved division 5..7
            encode(4),                              # class try_begin
            encode(31, local[8], 0),
            encode(1265, local[9], defender_troops[0], 1, 0, local[10]),
            encode(5),
            encode(31, local[8], 1),
            encode(1265, local[9], defender_troops[1], 1, 0, local[10]),
            encode(5),
            encode(31, local[8], 2),
            encode(1265, local[9], defender_troops[2], 1, 0, local[10]),
            encode(5),
            encode(1265, local[9], defender_troops[3], 1, 0, local[10]),
            encode(3),                              # class end
            encode(3),                              # for end
            encode(3),                              # respawn end
        ])
    body.extend([
        encode(4),                  # try_begin
        encode(33, local[0], 0, low_water + 1),  # low-water
        encode(31, globals_[TACTICAL_GLOBAL], 0),  # not already retreating
        encode(2133, globals_[TACTICAL_GLOBAL], 1),
        encode(1780, POS_BASE + 120, 0),  # survivor fallback entry
    ])
    for division in DIVISIONS:
        body.extend([
            encode(1791, 0, division, POS_BASE + 120),
            encode(1790, 0, division, 0),  # native hold order
        ])
    body.extend([
        encode(5),  # else_try
        encode(30, local[0], high_water),
        encode(31, globals_[TACTICAL_GLOBAL], 1),
        encode(2133, globals_[TACTICAL_GLOBAL], 0),
        encode(2211, local[4]),  # current scene
        encode(4),  # map switch
    ])
    for index, map_number in enumerate(sorted(scenes)):
        if index:
            body.append(encode(5))
        body.append(encode(31, local[4], SCENE_BASE + scenes[map_number]))
        post_ids = (2, 3, 4) if map_number == 4 else (41, 42, 43)
        for division, entry in zip(DIVISIONS, post_ids):
            body.extend([
                encode(1780, POS_BASE + 120, entry),
                encode(1791, 0, division, POS_BASE + 120),
                encode(1790, 0, division, 0),
            ])
    body.extend([encode(3), encode(3)])  # end switch and mode branch
    return " ".join(["3.000000", "0.000000", "0.000000",
                     str(len(conditions)),
                     *(v for op in conditions for v in op),
                     str(len(body)),
                     *(v for op in body for v in op)])


def patch_text(mission: str, variables: str, scenes: dict[int, int],
               low_water: int = 1, high_water: int = 3,
               defender_cap: int = 0,
               defender_troops: tuple[int, ...] = ()) -> tuple[str, str]:
    globals_ = mapping(variables)
    lines = mission.splitlines(keepends=True)
    count_line, count, end = mission_bounds(lines)
    if count != EXPECTED_PREVIOUS_TRIGGERS:
        raise PatchError("Tactical recovery requires the 29-trigger wave remaster")
    newline = "\r\n" if "\r\n" in mission else "\n"
    additions = [
        initial_mode(globals_[TACTICAL_GLOBAL]),
        recovery_trigger(globals_, scenes, low_water, high_water,
                         defender_cap, defender_troops),
    ]
    lines[count_line] = "31" + newline
    lines[end:end] = [row + newline for row in additions]
    result = "".join(lines)
    if mission_bounds(result.splitlines(keepends=True))[1] != 31:
        raise PatchError("Tactical recovery would corrupt mission trigger count")
    variable_newline = "\r\n" if "\r\n" in variables else "\n"
    return result, variables.rstrip("\r\n") + variable_newline + TACTICAL_GLOBAL + variable_newline


def apply_module(module: Path, low_water: int = 1, high_water: int = 3,
                 city_only: bool = False, defender_cap: int = 0,
                 defender_troops: tuple[int, ...] = ()) -> dict:
    module = Path(module)
    mission_path, variables_path = module / "mission_templates.txt", module / "variables.txt"
    chosen = (4,) if city_only else range(1, 6)
    scenes = {i: scene_index(module / "scenes.txt", f"scn_tbfc_invasion_{i}")
              for i in chosen}
    original_m = mission_path.read_bytes()
    original_v = variables_path.read_bytes()
    changed_m, changed_v = patch_text(
        original_m.decode("utf-8"), original_v.decode("utf-8"),
        scenes, low_water, high_water, defender_cap, defender_troops)
    mission_path.write_bytes(changed_m.encode("utf-8"))
    try:
        variables_path.write_bytes(changed_v.encode("utf-8"))
    except BaseException:
        mission_path.write_bytes(original_m)
        raise
    return {
        "enabled": True,
        "city_only": bool(city_only),
        "scene_indices": scenes,
        "state_global": TACTICAL_GLOBAL,
        "low_water": low_water,
        "high_water": high_water,
        "guard_groups": list(DIVISIONS),
        "fallback_entry": 0,
        "reevaluation_seconds": 3,
        "defender_respawn_cap": defender_cap,
        "defender_respawn_troops": list(defender_troops),
        "final_trigger_count": 31,
        "runtime_verified": False,
        "warning": "Experimental native orders; LOS and WSE2 group behaviour await final test.",
    }
