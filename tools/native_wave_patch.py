"""City-only original wave-controller patch.

D's sealed readback proved appended triggers 26/28 cannot change the native wave
table or team-1 speed: slots stayed 221:898, 231:895, 241:896 and speed 100.
This tool patches the ORIGINAL compiled triggers instead:

* trigger 14: every valid invader slot write (slots 200..244) is set to the slow
  Zombie 894 troop; the four trailing invalid faction -1 writes are redirected to
  a valid faction and unused slot 245 (log guard, no wave effect).
* trigger 15: appends a bounded per-tick team-1 speed loop using native
  ``agent_set_speed_modifier`` (2093), wave-scaled 55 + 5*wave capped 100.

Only the generated module is patched; the original RAR and every non-City file
stay untouched. This is a City-only exception recorded in the build receipt.
"""
from __future__ import annotations

from pathlib import Path

from patch_defenders import mission_bounds

FACTION_BASE = 432345564227567616
INVADER_FACTION = FACTION_BASE + 16
TROOP_BASE = 360287970189639680
SLOW_ZOMBIE = 894
UNUSED_SLOT = 245
WAVE_TABLE_SLOTS = tuple(range(200, 245))
TRIGGER14 = 14
TRIGGER15 = 15
SPEED_BASE = 50
SPEED_PER_WAVE = 4
SPEED_CAP = 85


class NativeWavePatchError(ValueError):
    pass


def _decode(row: str):
    tokens = row.split()
    conditions = []
    cursor = 4
    for _ in range(int(tokens[3])):
        op = int(tokens[cursor]); argc = int(tokens[cursor + 1]); cursor += 2
        args = tuple(int(v) for v in tokens[cursor:cursor + argc]); cursor += argc
        conditions.append((op, args))
    count = int(tokens[cursor]); cursor += 1
    ops = []
    for _ in range(count):
        op = int(tokens[cursor]); argc = int(tokens[cursor + 1]); cursor += 2
        args = tuple(int(v) for v in tokens[cursor:cursor + argc]); cursor += argc
        ops.append((op, args))
    return tokens[:3], conditions, ops, tokens[cursor:]


def _encode(prefix, conditions, ops, tail):
    tokens = [*prefix, str(len(conditions))]
    for op, args in conditions:
        tokens.extend([str(op), str(len(args)), *(str(a) for a in args)])
    tokens.append(str(len(ops)))
    for op, args in ops:
        tokens.extend([str(op), str(len(args)), *(str(a) for a in args)])
    tokens.extend(tail)
    return " ".join(tokens)


def _local(n: int) -> int:
    return 1224979098644774912 + n


def _speed_ops(wave_global: int | None) -> list[tuple[int, tuple[int, ...]]]:
    speed, agent, team, wave = (_local(n) for n in (44, 45, 46, 47))
    ops = [(2133, (speed, SPEED_BASE))]
    if wave_global is not None:
        ops += [(2122, (wave, wave_global, SPEED_PER_WAVE)),
                (2120, (speed, speed, wave)),
                (4, ()), (32, (speed, SPEED_CAP)), (2133, (speed, SPEED_CAP)), (3, ())]
    ops += [(12, (agent,)), (1702, (agent,)), (1707, (agent,)),
            (1770, (team, agent)), (31, (team, 1)), (32, (agent, 0)),
            (2093, (agent, speed)), (3, ())]
    return ops


def patch_mission_text(text: str, wave_global: int | None = None,
                       speed_loop: bool = False,
                       wave_count_multiplier: int = 1) -> tuple[str, dict]:
    lines = text.splitlines(keepends=True)
    p, count, end = mission_bounds(lines)
    if count < 16:
        raise NativeWavePatchError("Mission has fewer than 16 original triggers")
    rows = lines[p + 1:end]
    newline = "\r\n" if rows[TRIGGER14].endswith("\r\n") else "\n"

    prefix, conditions, ops, tail = _decode(rows[TRIGGER14].strip())
    changed = 0
    invalid = 0
    new_ops = []
    for op, args in ops:
        if op == 502 and len(args) == 3:
            faction, slot, troop = args
            if faction == -1 and slot == 200:
                invalid += 1
                new_ops.append((502, (INVADER_FACTION, UNUSED_SLOT, troop)))
                changed += 1
                continue
            if faction == INVADER_FACTION and slot in WAVE_TABLE_SLOTS:
                new_ops.append((502, (faction, slot, TROOP_BASE + SLOW_ZOMBIE)))
                if troop != TROOP_BASE + SLOW_ZOMBIE:
                    changed += 1
                continue
        new_ops.append((op, args))
    if invalid != 4:
        raise NativeWavePatchError(f"Expected four invalid trigger-14 writes, found {invalid}")
    if changed < 24:
        raise NativeWavePatchError("Trigger 14 wave table was not fully patched")
    rows[TRIGGER14] = _encode(prefix, conditions, new_ops, tail) + newline

    # Trigger 15: append the per-tick team-1 speed loop to the original wave
    # controller's consequence block. Its own conditions are unchanged.
    prefix15, conditions15, ops15, tail15 = _decode(rows[TRIGGER15].strip())
    scaled_counts = []
    if wave_count_multiplier != 1:
        if wave_count_multiplier not in (2, 3):
            raise NativeWavePatchError("Wave count multiplier must be 1, 2 or 3")
        scaled = []
        for op, args in ops15:
            if op == 1265 and len(args) == 5:
                old_count = args[2]
                new_count = old_count * wave_count_multiplier
                scaled.append((op, (args[0], args[1], new_count, args[3], args[4])))
                scaled_counts.append({"before": old_count, "after": new_count})
            else:
                scaled.append((op, args))
        ops15 = scaled
    if speed_loop:
        ops15 = [*ops15, *_speed_ops(wave_global)]
        rows[TRIGGER15] = _encode(prefix15, conditions15, ops15, tail15) + newline

    output = "".join(lines[:p + 1] + rows + lines[end:])
    report = {
        "schema": "zombieee.native-wave-patch.v1",
        "trigger14_wave_table_patched": True,
        "trigger14_slot_writes_changed": changed,
        "invalid_faction_writes_guarded": invalid,
        "trigger15_speed_loop_appended": bool(speed_loop),
        "speed_loop_disabled_for_bisect": not speed_loop,
        "slow_troop": SLOW_ZOMBIE,
        "speed_base": SPEED_BASE,
        "speed_per_wave": SPEED_PER_WAVE,
        "speed_cap": SPEED_CAP,
        "wave_composition_changed": True,
        "wave_count_multiplier": wave_count_multiplier,
        "wave_counts_scaled": scaled_counts,
        "wave_count_cap": "engine/native-visible cap; no extra City spawn cap",
    }
    return output, report


def apply_module(module: Path, wave_global: int | None = None,
                 speed_loop: bool = False,
                 wave_count_multiplier: int = 1) -> dict:
    path = Path(module) / "mission_templates.txt"
    updated, report = patch_mission_text(path.read_text(encoding="utf-8"),
                                         wave_global=wave_global,
                                         speed_loop=speed_loop,
                                         wave_count_multiplier=wave_count_multiplier)
    path.write_text(updated, encoding="utf-8", newline="")
    return report
