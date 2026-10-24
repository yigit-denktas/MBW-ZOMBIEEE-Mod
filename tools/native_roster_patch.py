#!/usr/bin/env python3
"""City-only native roster fix: make faction bots spawn Zombie and defender troops.

Compiled Native script ``multiplayer_find_bot_troop_and_group_for_spawn`` scans a
hard-coded multiplayer-AI troop range (855..874) and keeps only troops whose
faction matches the team faction. The 2012 ZOMBIEEE mod appended its Zombie
troops (894..911) after ``trp_multiplayer_end``, so for the invader faction the
engine could only ever select the two placeholder Crazed-Civilian troops
(873/874). Result: ``set_bot_count 2 N`` populates team 1 with Crazed Civilians.

In City builds the same function is also the native spawn path for allied team-0
bots: team 0's faction (fac_kingdom_1, 15) would spawn Swadian AI troops from
855..874. An optional defender range makes City-mode team-0 bots use the build's
private survivor troop block instead (981..984, or 875..878 for the original
loadout profile). D's sealed run proved that native bot spawning works on the
dedicated host while team-0 ``add_visitors`` produced no allied agents, so this
becomes the reliable allied-squad spawn path.

Patch shape (inserted after the one team-faction read, before the scan loops):

- faction 16 (fac_kingdom_invaders) -> 894..911 native Zombies;
- faction 15 (fac_kingdom_1) AND ``$g_multiplayer_game_type == 7`` -> defender
  range when the build supplies one;
- every other faction/game type keeps the original 855..874 range.

The compiled script body is rewritten in place and validated by re-decoding.
``runtime_verified`` is always false: only a sealed WSE2 run can prove the
engine actually spawns the roster.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

SCRIPT_NAME = "multiplayer_find_bot_troop_and_group_for_spawn"
SECOND_TEAM_FACTION = "fac_kingdom_invaders"
FACTION_BASE = 432345564227567616
TROOP_BASE = 360287970189639680
LOCAL_BASE = 1224979098644774912
GLOBAL_BASE = 144115188075855872
# original compiled multiplayer-AI block
ORIGINAL_TROOP_BEGIN = 855
ORIGINAL_TROOP_END = 875  # exclusive
# ZOMBIEEE Beta 0.4 native Zombie block (faction fac_kingdom_invaders)
INVADER_TROOP_BEGIN = 894
INVADER_TROOP_END = 912  # exclusive: 894..911
TEAM_GET_FACTION = 458
TRY_FOR_RANGE = 6
ASSIGN = 2133
EQ = 31
TRY_BEGIN = 4
ELSE_TRY = 5
TRY_END = 3

DEFENDER_FACTION_ID = 15  # fac_kingdom_1, team 0
CITY_GAME_TYPE = 7


class RosterPatchError(ValueError):
    pass


def _ops_from_body(body: list[int]) -> list[tuple[int, tuple[int, ...]]]:
    if not body:
        raise RosterPatchError("Empty compiled script body")
    count = body[0]
    if not 0 <= count <= 10000:
        raise RosterPatchError("Implausible compiled script operation count")
    position, ops = 1, []
    for _ in range(count):
        if position + 1 >= len(body):
            raise RosterPatchError("Truncated compiled script operation")
        opcode, argc = body[position], body[position + 1]
        position += 2
        if not 0 <= argc <= 128 or position + argc > len(body):
            raise RosterPatchError("Invalid compiled script operation arity")
        ops.append((opcode, tuple(body[position:position + argc])))
        position += argc
    if position != len(body):
        raise RosterPatchError("Unexpected tokens after compiled script body")
    return ops


def _body_from_ops(ops: list[tuple[int, tuple[int, ...]]]) -> list[int]:
    body = [len(ops)]
    for opcode, args in ops:
        body.extend((opcode, len(args)))
        body.extend(args)
    return body


def _roster_block(defender_range: tuple[int, int] | None,
                  game_type_global: int | None,
                  defender_faction_id: int = DEFENDER_FACTION_ID,
                  ) -> list[tuple[int, tuple[int, ...]]]:
    l5 = LOCAL_BASE + 5
    l12, l13 = LOCAL_BASE + 12, LOCAL_BASE + 13
    block = [
        (TRY_BEGIN, ()),
        (EQ, (l5, FACTION_BASE + 16)),
        (ASSIGN, (l12, TROOP_BASE + INVADER_TROOP_BEGIN)),
        (ASSIGN, (l13, TROOP_BASE + INVADER_TROOP_END)),
    ]
    if defender_range is not None:
        begin, end = defender_range
        if not (0 <= begin < end <= 9000):
            raise RosterPatchError("Invalid defender troop range")
        if game_type_global is None:
            raise RosterPatchError("Defender range requires the game-type global")
        block += [
            (ELSE_TRY, ()),
            (EQ, (l5, FACTION_BASE + defender_faction_id)),
            (EQ, (game_type_global, CITY_GAME_TYPE)),
            (ASSIGN, (l12, TROOP_BASE + begin)),
            (ASSIGN, (l13, TROOP_BASE + end)),
        ]
    block += [
        (ELSE_TRY, ()),
        (ASSIGN, (l12, TROOP_BASE + ORIGINAL_TROOP_BEGIN)),
        (ASSIGN, (l13, TROOP_BASE + ORIGINAL_TROOP_END)),
        (TRY_END, ()),
    ]
    return block


def patch_ops(ops: list[tuple[int, tuple[int, ...]]],
              defender_range: tuple[int, int] | None = None,
              game_type_global: int | None = None,
              ) -> list[tuple[int, tuple[int, ...]]]:
    """Return the faction-conditional roster variant of the Native script."""
    l5 = LOCAL_BASE + 5
    if any(opcode == EQ and args == (l5, FACTION_BASE + 16)
           for opcode, args in ops):
        raise RosterPatchError("Script already carries the roster patch")
    l0, l6, l10 = LOCAL_BASE, LOCAL_BASE + 6, LOCAL_BASE + 10
    l12, l13 = LOCAL_BASE + 12, LOCAL_BASE + 13
    faction_read = (TEAM_GET_FACTION, (l5, l0))
    if ops.count(faction_read) != 1:
        raise RosterPatchError("Unexpected team faction read in bot-troop script")
    first_loop = (TRY_FOR_RANGE,
                  (l6, TROOP_BASE + ORIGINAL_TROOP_BEGIN,
                   TROOP_BASE + ORIGINAL_TROOP_END))
    if ops.count(first_loop) != 1:
        raise RosterPatchError("Unexpected first multiplayer troop range")
    end_assign = (ASSIGN, (l10, TROOP_BASE + ORIGINAL_TROOP_END))
    if ops.count(end_assign) != 1:
        raise RosterPatchError("Unexpected bot-troop end assignment")
    second_loop = (TRY_FOR_RANGE,
                   (l6, TROOP_BASE + ORIGINAL_TROOP_BEGIN, l10))
    if ops.count(second_loop) != 1:
        raise RosterPatchError("Unexpected second multiplayer troop range")

    block = _roster_block(defender_range, game_type_global)
    patched = []
    for opcode, args in ops:
        if (opcode, args) == faction_read:
            patched.append((opcode, args))
            patched.extend(block)
        elif (opcode, args) == first_loop:
            patched.append((TRY_FOR_RANGE, (l6, l12, l13)))
        elif (opcode, args) == end_assign:
            patched.append((ASSIGN, (l10, l13)))
        elif (opcode, args) == second_loop:
            patched.append((TRY_FOR_RANGE, (l6, l12, l10)))
        else:
            patched.append((opcode, args))
    return patched


def troop_factions(module: Path) -> dict[int, int]:
    """Resolve troop -> faction from the compiled troops table (ordinal = troop id)."""
    lines = (Path(module) / "troops.txt").read_text(encoding="utf-8",
                                                   errors="replace").splitlines()
    rows = [line.split() for line in lines if line.startswith("trp_")]
    result = {}
    for index, tokens in enumerate(rows):
        if len(tokens) < 8:
            raise RosterPatchError(f"Malformed compiled troop row {index}")
        try:
            result[index] = int(tokens[7])
        except ValueError as exc:
            raise RosterPatchError(f"Malformed troop faction at {index}") from exc
    return result


def expected_candidates(module: Path, faction_id: int,
                        troop_range: tuple[int, int] | None = None) -> list[int]:
    factions = troop_factions(module)
    if troop_range is not None:
        begin, end = troop_range
    elif faction_id == 16:
        begin, end = INVADER_TROOP_BEGIN, INVADER_TROOP_END
    else:
        begin, end = ORIGINAL_TROOP_BEGIN, ORIGINAL_TROOP_END
    return [index for index in range(begin, end) if factions.get(index) == faction_id]


def patch_text(text: str, module: Path,
               defender_range: tuple[int, int] | None = None,
               game_type_global: int | None = None) -> tuple[str, dict]:
    lines = text.splitlines(keepends=True)
    headers = [i for i, line in enumerate(lines)
               if line.split()[:1] == [SCRIPT_NAME] and line.strip().endswith("-1")]
    if len(headers) != 1:
        raise RosterPatchError("Expected exactly one multiplayer bot-troop script")
    header = headers[0]
    if header + 1 >= len(lines):
        raise RosterPatchError("Missing bot-troop script body")
    body = list(map(int, lines[header + 1].split()))
    ops = _ops_from_body(body)
    patched_ops = patch_ops(ops, defender_range, game_type_global)
    expected_delta = len(_roster_block(defender_range, game_type_global))
    if len(patched_ops) - len(ops) != expected_delta:
        raise RosterPatchError("Roster patch produced an unexpected operation count")
    patched_body = _body_from_ops(patched_ops)
    # Re-decode before writing anything.
    if _ops_from_body(patched_body) != patched_ops:
        raise RosterPatchError("Roster patch failed compiled round-trip")
    newline = "\r\n" if "\r\n" in text else "\n"
    lines[header + 1] = " ".join(map(str, patched_body)) + newline
    receipt = {
        "applied": True,
        "script": SCRIPT_NAME,
        "operation_count_before": len(ops),
        "operation_count_after": len(patched_ops),
        "original_troop_range": [ORIGINAL_TROOP_BEGIN, ORIGINAL_TROOP_END],
        "invader_troop_range": [INVADER_TROOP_BEGIN, INVADER_TROOP_END],
        "invader_candidates": expected_candidates(module, 16),
        "defender_troop_range": list(defender_range) if defender_range else None,
        "defender_candidates": (expected_candidates(module, DEFENDER_FACTION_ID,
                                                    defender_range)
                                if defender_range else []),
        "defender_game_type_global": game_type_global,
        "foreign_faction_candidates_unchanged": True,
        "runtime_verified": False,
        "warning": "Static compiled-script patch only; the sealed WSE2 run must prove "
                   "the engine spawns the Zombie roster and native team-0 defender bots.",
    }
    if defender_range:
        receipt["defender_faction"] = DEFENDER_FACTION_ID
        receipt["defender_game_type"] = CITY_GAME_TYPE
    return "".join(lines), receipt


def apply_module(module: Path, defender_range: tuple[int, int] | None = None,
                 game_type_global: int | None = None) -> dict:
    """Patch the staged module's compiled scripts table in place."""
    module = Path(module)
    path = module / "scripts.txt"
    original = path.read_bytes()
    text = original.decode("utf-8")
    changed, receipt = patch_text(text, module, defender_range, game_type_global)
    receipt = dict(receipt)
    receipt["sha256_before"] = hashlib.sha256(original).hexdigest()
    receipt["sha256_after"] = hashlib.sha256(changed.encode("utf-8")).hexdigest()
    path.write_bytes(changed.encode("utf-8"))
    return receipt


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--module", type=Path, required=True)
    parser.add_argument("--defender-range", help="BEGIN,END for City team-0 bot troops")
    parser.add_argument("--game-type-global", type=int)
    parser.add_argument("--apply", action="store_true")
    args = parser.parse_args()
    defender_range = None
    if args.defender_range:
        begin, end = map(int, args.defender_range.split(","))
        defender_range = (begin, end)
    try:
        text = (args.module / "scripts.txt").read_text(encoding="utf-8")
        changed, receipt = patch_text(text, args.module, defender_range,
                                      args.game_type_global)
        if not args.apply:
            receipt = dict(receipt, dry_run=True, changed_characters=len(changed) - len(text))
        else:
            receipt = apply_module(args.module, defender_range, args.game_type_global)
    except (OSError, ValueError, RosterPatchError) as exc:
        print(json.dumps({"applied": False, "error": type(exc).__name__ + ": " + str(exc)}))
        return 2
    print(json.dumps(receipt, indent=2))
    return 0 if receipt.get("applied") else 2


if __name__ == "__main__":
    raise SystemExit(main())
