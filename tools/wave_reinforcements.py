#!/usr/bin/env python3
"""Opt-in wave reinforcements using original 0.4 wave_number, not a new wave system."""
from pathlib import Path
from patch_defenders import PatchError, mission_bounds, SURVIVOR_CLASSES, TROOP_BASE, index_troops

GLOBAL_BASE = 144115188075855872
LOCAL_BASE = 1224979098644774912
SENTINEL = "zdr_last_reinforced_wave"
ROUND_STAMP = "zdr_last_reinforced_round_start"
ORIGINAL_GLOBALS = 1220
# Verified in original mst_multiplayer_iv ti_before_mission_start (-19).
INVASION_GAME_TYPE = 7
FACTION_BASE = 432345564227567616
TROOP_BASE = 360287970189639680
INVADER_FACTION = FACTION_BASE + 16
SLOW_ZOMBIE = 894
WAVE_TABLE_SLOTS = tuple(range(200, 245))
# Warband native neq = neg|eq = 0x80000000|31.
# A round restart resets wave_number to zero while the sentinel survives.
WAVE_CHANGED = 2147483679
ROUND_OR_WAVE_CHANGED = (1 << 30) | WAVE_CHANGED  # this_or_next|neq
GROUPS = (5, 6, 7)


def op(code, *args):
    return [str(code), str(len(args)), *(str(a) for a in args)]


def globals_from_original(raw):
    names = raw.splitlines()
    if (len(names) != ORIGINAL_GLOBALS or
            any(key in names for key in (SENTINEL, ROUND_STAMP)) or
            len(set(names)) != len(names)):
        raise PatchError("Expected unchanged original Beta 0.4 global variable table")
    required = ("wave_number", "g_multiplayer_game_type", "g_round_ended",
                "g_round_start_time")
    if any(key not in names for key in required):
        raise PatchError("Original wave/game state variables missing")
    result = {key: GLOBAL_BASE + names.index(key) for key in required}
    result[SENTINEL] = GLOBAL_BASE + len(names)
    result[ROUND_STAMP] = GLOBAL_BASE + len(names) + 1
    return result


def initialize_wave_state(sentinel, round_stamp):
    return " ".join(["-20.000000", "0.000000", "0.000000",
                     "1", *op(417), "2", *op(2133, sentinel, 0),
                     *op(2133, round_stamp, -1)])


def reinforce_on_wave(g, troop_ids, cap=4, troop_classes=SURVIVOR_CLASSES, first_wave=2,
                      city_scene=None, slow_visitors=True):
    if not 1 <= first_wave <= 10:
        raise PatchError("Reinforcement first_wave must be 1..10")
    if not 1 <= cap <= 8:
        raise PatchError("Reinforcement cap must be 1..8")
    if any(name not in troop_ids for name in troop_classes):
        raise PatchError("Requested survivor troop profile missing")
    loc = [LOCAL_BASE + n for n in range(8)]
    conditions = [
        op(417),  # multiplayer_is_server
        op(31, g["g_multiplayer_game_type"], INVASION_GAME_TYPE),  # original Invasion
        op(30, g["wave_number"], first_wave),  # ge: threshold from support difficulty
        # The historical mission resets wave_number across rounds. A separate
        # original round-start timer identifies the new round even if both
        # rounds reach the SAME numbered wave (e.g., each ends at wave 2).
        op(ROUND_OR_WAVE_CHANGED, g["g_round_start_time"], g[ROUND_STAMP]),
        op(WAVE_CHANGED, g["wave_number"], g[SENTINEL]),
        op(31, g["g_round_ended"], 0),
    ]
    if city_scene is not None:
        if not isinstance(city_scene, int) or city_scene < 0:
            raise PatchError("Invalid original City scene index")
        from city_defense import SCENE_BASE
        conditions.extend([
            op(2211, LOCAL_BASE + 8),  # store_current_scene for City-only build
            op(31, LOCAL_BASE + 8, SCENE_BASE + city_scene),
        ])
    body = []
    if slow_visitors:
        # Redundant visitor-table normalization: the 4 s wave trigger also
        # rewrites every wave slot to the slow Zombie 894, so a leaked Fast/
        # strong slot cannot survive even if the 5 s City trigger is skipped.
        for slot in WAVE_TABLE_SLOTS:
            body.append(op(502, INVADER_FACTION, slot, TROOP_BASE + SLOW_ZOMBIE))
    body += [
        op(2133, g[ROUND_STAMP], g["g_round_start_time"]),
        op(2133, g[SENTINEL], g["wave_number"]),
        op(2133, loc[0], 0),
        op(12, loc[1]),  # for agents
        op(1702, loc[1]),  # alive
        op(1707, loc[1]),  # AI, not player
        op(1770, loc[2], loc[1]),  # team
        op(31, loc[2], 0),  # survivor team
        # Count every team-0 non-player bot: native bots report groups 26-31,
        # so a 5..8 group filter would count zero and over-spawn.
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
               1, 0, GROUPS[index % 3]),  # 5th arg is the reserved group_no 5..7
        ])
    body.extend([op(3), op(3), op(3)])
    return " ".join(["4.000000", "0.000000", "0.000000", str(len(conditions)),
                     *(value for operation in conditions for value in operation),
                     str(len(body)),
                     *(value for operation in body for value in operation)])


def patch_text(mission, variables, troop_ids, cap=4, troop_classes=SURVIVOR_CLASSES, first_wave=2,
               city_scene=None, slow_visitors=True):
    g = globals_from_original(variables)
    lines = mission.splitlines(keepends=True)
    count_row, count, insert_at = mission_bounds(lines)
    if count != 27 or lines[count_row].strip() != "27":
        raise PatchError("Wave top-up requires the 27-trigger tactical mission")
    nl = "\r\n" if "\r\n" in mission else "\n"
    lines[count_row] = "29" + nl
    lines[insert_at:insert_at] = [
        initialize_wave_state(g[SENTINEL], g[ROUND_STAMP]) + nl,
        reinforce_on_wave(g, troop_ids, cap, troop_classes, first_wave, city_scene,
                           slow_visitors) + nl,
    ]
    changed = "".join(lines)
    if mission_bounds(changed.splitlines(keepends=True))[1] != 29:
        raise PatchError("Compiled mission round-trip failed")
    variable_nl = "\r\n" if "\r\n" in variables else "\n"
    return (changed, variables.rstrip("\r\n") + variable_nl +
            SENTINEL + variable_nl + ROUND_STAMP + variable_nl)


def apply_module(module: Path, cap=4, balanced_ai=False, first_wave=2,
                 city_only=False, slow_visitors=True):
    module = Path(module)
    mission_path, variable_path = module / "mission_templates.txt", module / "variables.txt"
    original_m, original_v = mission_path.read_bytes(), variable_path.read_bytes()
    if balanced_ai:
        from bot_loadouts import CLONES
        classes = CLONES
    else:
        classes = SURVIVOR_CLASSES
    city_scene = None
    if city_only:
        from city_defense import scene_index
        city_scene = scene_index(module / "scenes.txt")
    changed_m, changed_v = patch_text(original_m.decode("utf-8"),
        original_v.decode("utf-8"), index_troops(module / "troops.txt"),
        cap, classes, first_wave, city_scene, slow_visitors)
    mission_path.write_bytes(changed_m.encode("utf-8"))
    try:
        variable_path.write_bytes(changed_v.encode("utf-8"))
    except Exception:
        mission_path.write_bytes(original_m)
        raise
    return {
        "enabled": True, "squad_cap": cap, "starts_at_wave": first_wave,
        "troop_profile": "balanced-ai" if balanced_ai else "original-0.4",
        "class_rotation": "original_wave_number_plus_replacement_index_mod_4",
        "original_wave_variable": "wave_number", "added_variable": SENTINEL,
        "round_identity_variable": "g_round_start_time",
        "added_round_marker": ROUND_STAMP,
        "city_only": bool(city_only), "scene_gate": city_scene,
        "final_trigger_count": 29, "runtime_verified": False,
        "limitations": "Replacements once per wave; no mid-wave resurrection.",
    }
