#!/usr/bin/env python3
"""Opt-in local-host-only solo health/ammo assist for original Warband invasion.

This is NOT a keybind/menu and does not grant powers to remote multiplayer
clients. Requires a listen server, an active local host player, and exactly
one active player. Uses only Warband native operations; gameplay unverified.
"""
from __future__ import annotations
from pathlib import Path
from patch_defenders import PatchError, mission_bounds

NEG = 2147483648
LOCAL = 1224979098644774912


def operation(code, *args):
    return [str(code), str(len(args)), *(str(arg) for arg in args)]


def solo_assist_trigger(period=12) -> str:
    if not isinstance(period, int) or not 5 <= period <= 60:
        raise PatchError("Solo-assist period must be 5..60 seconds")
    players = LOCAL
    count = LOCAL + 1
    host = LOCAL + 2
    agent = LOCAL + 3
    team = LOCAL + 4
    conditions = [
        operation(417),        # multiplayer_is_server
        operation(NEG | 418),  # NOT dedicated server
    ]
    body = [
        operation(2133, count, 0),
        operation(17, players),   # iterate active multiplayer players
        operation(401, players),  # player_is_active
        operation(2105, count, 1),
        operation(3),             # try_end
        operation(4),             # try_begin
        operation(31, count, 1),  # only one actual player connected
        operation(415, host),     # get local server host player ID
        operation(401, host),     # host player must be active
        operation(406, agent, host),  # player_get_agent_id
        operation(1702, agent),  # alive
        operation(1770, team, agent),  # agent_get_team
        operation(31, team, 0),  # survivors only
        operation(1721, agent, 100, 0),  # set HP to 100% of max
        operation(1728, agent),  # refill current ammo
        operation(3),             # try_end
    ]
    return " ".join([
        f"{float(period):.6f}", "0.000000", "0.000000",
        str(len(conditions)), *(x for o in conditions for x in o),
        str(len(body)), *(x for o in body for x in o),
    ])


def patch_text(mission: str, period: int = 12) -> tuple[str, int]:
    lines = mission.splitlines(keepends=True)
    line, count, end = mission_bounds(lines)
    if count not in (25, 26, 27, 29, 31):
        raise PatchError("Unknown mission trigger count, refusing solo cheat injection")
    marker = solo_assist_trigger(period)
    nl = "\r\n" if "\r\n" in mission else "\n"
    lines[line] = str(count + 1) + nl
    lines.insert(end, marker + nl)
    changed = "".join(lines)
    if mission_bounds(changed.splitlines(keepends=True))[1] != count + 1:
        raise PatchError("Solo assist did not roundtrip")
    return changed, count + 1


def apply_module(module: Path, period: int = 12) -> dict:
    path = Path(module) / "mission_templates.txt"
    original = path.read_bytes()
    changed, count = patch_text(original.decode("utf-8"), period)
    path.write_bytes(changed.encode("utf-8"))
    return {
        "enabled": True, "solo_only": True, "dedicated_server": False,
        "requires_exactly_one_active_player": True,
        "host_only": True, "period_seconds": period,
        "effects": ["host-health-full", "host-ammo-refill"],
        "final_trigger_count": count, "runtime_verified": False,
        "warning": "Listen-server singleton gating is static only; WSE2 runtime not tested.",
    }
