#!/usr/bin/env python3
"""Opt-in wave reinforcements using original 0.4 wave_number, not a new wave system."""
from pathlib import Path
from patch_defenders import PatchError, mission_bounds, SURVIVOR_CLASSES, TROOP_BASE, index_troops

GLOBAL_BASE = 144115188075855872
LOCAL_BASE = 1224979098644774912
SENTINEL = "zdr_last_reinforced_wave"
ORIGINAL_GLOBALS = 1220
GROUPS = (5, 6, 7)


def op(code, *args):
    return [str(code), str(len(args)), *(str(a) for a in args)]


def globals_from_original(raw):
    names = raw.splitlines()
    if len(names) != ORIGINAL_GLOBALS or SENTINEL in names or len(set(names)) != len(names):
        raise PatchError("Expected unchanged original Beta 0.4 global variable table")
    required = ("wave_number", "g_multiplayer_game_type", "g_round_ended")
    if any(key not in names for key in required):
        raise PatchError("Original wave/game state variables missing")
    result = {key: GLOBAL_BASE + names.index(key) for key in required}
    result[SENTINEL] = GLOBAL_BASE + len(names)
    return result


def initialize_wave_state(sentinel):
    return " ".join(["-20.000000", "0.000000", "0.000000",
                     "1", *op(417), "1", *op(2133, sentinel, 0)])


def reinforce_on_wave(g, troop_ids, cap=4, troop_classes=SURVIVOR_CLASSES):
    if not 1 <= cap <= 8:
        raise PatchError("Reinforcement cap must be 1..8")
    if any(name not in troop_ids for name in troop_classes):
        raise PatchError("Requested survivor troop profile missing")
    loc = [LOCAL_BASE + n for n in range(8)]
    conditions = [
        op(417),  # multiplayer_is_server
        op(31, g["g_multiplayer_game_type"], 6),  # Invasion
        op(30, g["wave_number"], 2),  # ge: >= wave 2
        op(32, g["wave_number"], g[SENTINEL]),  # gt: one top-up per wave
        op(31, g["g_round_ended"], 0),
    ]
    body = [
        op(2133, g[SENTINEL], g["wave_number"]),
        op(2133, loc[0], 0),
        op(12, loc[1]),  # for agents
        op(1702, loc[1]),  # alive
        op(1707, loc[1]),  # AI, not player
        op(1770, loc[2], loc[1]),  # team
        op(31, loc[2], 0),  # survivor team
        op(1765, loc[3], loc[1]),  # group
        op(33, loc[3], 5, 8),  # only OUR groups, not normal allies
        op(2105, loc[0], 1),
        op(3),
        op(2121, loc[4], cap, loc[0]),  # missing = cap - living
        op(4),
        op(32, loc[4], 0),
        op(6, loc[5], 0, loc[4]),  # bounded 1..8
        # Rotate class selection with the original wave number so a single
        # casualty does not always create another Commando.
        op(2120, loc[7], g["wave_number"], loc[5]),
        op(2119, loc[6], loc[7], 4),  # wave + slot mod four classes
        op(4),
    ]
    for index, name in enumerate(troop_classes):
        if index:
            body.append(op(5))
        body.extend([
            op(31, loc[6], index),
            op(1265, index % 2, TROOP_BASE + troop_ids[name],
               1, 0, GROUPS[index % 3]),
        ])
    body.extend([op(3), op(3), op(3)])
    return " ".join(["4.000000", "0.000000", "0.000000", str(len(conditions)),
                     *(value for operation in conditions for value in operation),
                     str(len(body)),
                     *(value for operation in body for value in operation)])


def patch_text(mission, variables, troop_ids, cap=4, troop_classes=SURVIVOR_CLASSES):
    g = globals_from_original(variables)
    lines = mission.splitlines(keepends=True)
    count_row, count, insert_at = mission_bounds(lines)
    if count != 27 or lines[count_row].strip() != "27":
        raise PatchError("Wave top-up requires the 27-trigger tactical mission")
    nl = "\r\n" if "\r\n" in mission else "\n"
    lines[count_row] = "29" + nl
    lines[insert_at:insert_at] = [
        initialize_wave_state(g[SENTINEL]) + nl,
        reinforce_on_wave(g, troop_ids, cap, troop_classes) + nl,
    ]
    changed = "".join(lines)
    if mission_bounds(changed.splitlines(keepends=True))[1] != 29:
        raise PatchError("Compiled mission round-trip failed")
    variable_nl = "\r\n" if "\r\n" in variables else "\n"
    return changed, variables.rstrip("\r\n") + variable_nl + SENTINEL + variable_nl


def apply_module(module: Path, cap=4, balanced_ai=False):
    module = Path(module)
    mission_path, variable_path = module / "mission_templates.txt", module / "variables.txt"
    original_m, original_v = mission_path.read_bytes(), variable_path.read_bytes()
    if balanced_ai:
        from bot_loadouts import CLONES
        classes = CLONES
    else:
        classes = SURVIVOR_CLASSES
    changed_m, changed_v = patch_text(original_m.decode("utf-8"),
        original_v.decode("utf-8"), index_troops(module / "troops.txt"),
        cap, classes)
    mission_path.write_bytes(changed_m.encode("utf-8"))
    try:
        variable_path.write_bytes(changed_v.encode("utf-8"))
    except Exception:
        mission_path.write_bytes(original_m)
        raise
    return {
        "enabled": True, "squad_cap": cap, "starts_at_wave": 2,
        "troop_profile": "balanced-ai" if balanced_ai else "original-0.4",
        "class_rotation": "original_wave_number_plus_replacement_index_mod_4",
        "original_wave_variable": "wave_number", "added_variable": SENTINEL,
        "final_trigger_count": 29, "runtime_verified": False,
        "limitations": "Replacements once per wave; no mid-wave resurrection.",
    }
