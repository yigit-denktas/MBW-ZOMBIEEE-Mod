#!/usr/bin/env python3
"""Opt-in local-only private cheat HOTKEYS with auditable global counters.

The native triggers run on a non-dedicated, single-player listen host.  They
never execute for remote clients, and never disable anti-cheat.  Hotkey support
and authority still require the final WSE2 in-engine validation.
"""
from __future__ import annotations
from pathlib import Path
from patch_defenders import PatchError, mission_bounds
from solo_assist import operation, NEG, LOCAL

GLOBAL_BASE = 144115188075855872
COUNTERS = ("zdr_cmd_heal", "zdr_cmd_ammo", "zdr_cmd_squad")
KEY_LEFT_CONTROL = 0x1D
KEY_F7 = 0x41
KEY_F8 = 0x42
KEY_F9 = 0x43
GROUP_MIN, GROUP_MAX = 5, 8


def _common_preconditions(key: int) -> list[list[str]]:
    return [
        operation(417),                    # multiplayer_is_server
        operation(NEG | 418),              # not dedicated
        operation(70, KEY_LEFT_CONTROL),   # key_is_down (Ctrl)
        operation(71, key),                # key_clicked (F7, F8, F9)
    ]


def _authorized_host() -> tuple[list[list[str]], int]:
    player, count, host, agent, team = (LOCAL + n for n in range(5))
    ops = [
        operation(2133, count, 0),
        operation(17, player),      # try_for_players
        operation(401, player),     # player_is_active
        operation(2105, count, 1),
        operation(3),               # try_end
        operation(4),               # try_begin
        operation(31, count, 1),    # exactly one active human player
        operation(415, host),       # multiplayer_get_my_player
        operation(401, host),
        operation(406, agent, host),
        operation(1702, agent),     # alive
        operation(1770, team, agent),
        operation(31, team, 0),
    ]
    return ops, agent


def build_hotkey(key: int, counter: int, effect: str) -> str:
    if (key, effect) not in ((KEY_F7, "heal"), (KEY_F8, "ammo"), (KEY_F9, "squad")):
        raise PatchError("Invalid private command mapping")
    conditions = _common_preconditions(key)
    body, host_agent = _authorized_host()
    if effect == "heal":
        body.append(operation(1721, host_agent, 100, 0))
    elif effect == "ammo":
        body.append(operation(1728, host_agent))
    else:
        agent, team, group = LOCAL + 5, LOCAL + 6, LOCAL + 7
        body.extend([
            operation(12, agent),           # try_for_agents
            operation(1702, agent),         # alive
            operation(1707, agent),         # only non-player bots
            operation(1770, team, agent),
            operation(31, team, 0),
            operation(1765, group, agent),
            operation(33, group, GROUP_MIN, GROUP_MAX),
            operation(1721, agent, 100, 0),
            operation(1728, agent),
            operation(3),
        ])
    body.extend([operation(2105, counter, 1), operation(3)])
    return " ".join([
        "0.000000", "0.000000", "0.000000",
        str(len(conditions)), *(v for op in conditions for v in op),
        str(len(body)), *(v for op in body for v in op),
    ])


def patch_text(mission: str, variables: str) -> tuple[str, str]:
    existing = variables.splitlines()
    if len(existing) != 1223 or existing[-1] != "zdr_defence_mode":
        raise PatchError("Private commands require the 31-trigger tactical-recovery build")
    if any(name in existing for name in COUNTERS):
        raise PatchError("Private command counters already installed")
    lines = mission.splitlines(keepends=True)
    row, count, end = mission_bounds(lines)
    if count not in (31, 32):
        raise PatchError("Private commands require the 31/32-trigger tactical build")
    nl = "\r\n" if "\r\n" in mission else "\n"
    ids = [GLOBAL_BASE + len(existing) + i for i in range(len(COUNTERS))]
    # Init is a dedicated fourth trigger: otherwise a stale mission-to-mission
    # counter could be mistaken for an event in the diagnostic recorder.
    start_ops = [operation(2133, idx, 0) for idx in ids]
    init = " ".join(["-20.000000", "0.000000", "0.000000", "1",
                      *operation(417), str(len(start_ops)),
                      *(v for op in start_ops for v in op)])
    inserted = [init, build_hotkey(KEY_F7, ids[0], "heal"),
                build_hotkey(KEY_F8, ids[1], "ammo"),
                build_hotkey(KEY_F9, ids[2], "squad")]
    lines[row] = str(count + len(inserted)) + nl
    lines[end:end] = [t + nl for t in inserted]
    changed = "".join(lines)
    if mission_bounds(changed.splitlines(keepends=True))[1] != count + 4:
        raise PatchError("Private command mission roundtrip failed")
    vnl = "\r\n" if "\r\n" in variables else "\n"
    changed_vars = variables.rstrip("\r\n") + vnl + vnl.join(COUNTERS) + vnl
    return changed, changed_vars


def apply_module(module: Path) -> dict:
    module = Path(module)
    mp, vp = module / "mission_templates.txt", module / "variables.txt"
    original_m, original_v = mp.read_bytes(), vp.read_bytes()
    changed_m, changed_v = patch_text(original_m.decode(), original_v.decode())
    mp.write_bytes(changed_m.encode())
    try:
        vp.write_bytes(changed_v.encode())
    except BaseException:
        mp.write_bytes(original_m)
        raise
    return {
        "enabled": True,
        "bindings": {"Ctrl+F7": "heal_host", "Ctrl+F8": "refill_host_ammo",
                     "Ctrl+F9": "heal_refill_reserved_survivors"},
        "server_only": True, "dedicated_allowed": False,
        "max_active_players": 1, "counter_globals": list(COUNTERS),
        "trigger_additions": 4, "verified_in_engine": False,
    }
