#!/usr/bin/env python3
"""Static native-opcode contract for original Invasion + opt-in City AI.

Proof is limited to compiler operands. An unexecuted trigger cannot be called
working gameplay merely because its byte stream decodes successfully.
"""
from __future__ import annotations

from wave_reinforcements import GLOBAL_BASE, ORIGINAL_GLOBALS, GROUPS, SENTINEL, INVASION_GAME_TYPE
from tactical_recovery import TACTICAL_GLOBAL


def decode_trigger(row: str) -> tuple[list[tuple[int, tuple[int, ...]]],
                                       list[tuple[int, tuple[int, ...]]]]:
    """Read BOTH native condition and consequence blocks, rejecting trailing tokens."""
    words = row.split()
    if len(words) < 5:
        raise ValueError('Native mission trigger truncated')
    for field in words[:3]:
        float(field)
    cursor = 3
    decoded = []
    for group in range(2):
        if cursor >= len(words):
            raise ValueError('Native operation count missing')
        size = int(words[cursor]); cursor += 1
        if not 0 <= size <= 10000:
            raise ValueError('Invalid native operation count')
        ops = []
        for _ in range(size):
            if cursor + 2 > len(words):
                raise ValueError('Native operation truncated')
            opcode, argc = int(words[cursor]), int(words[cursor + 1])
            cursor += 2
            if not 0 <= argc <= 128 or cursor + argc > len(words):
                raise ValueError('Invalid native operation arity')
            args = tuple(int(v) for v in words[cursor:cursor + argc])
            cursor += argc
            ops.append((opcode, args))
        decoded.append(ops)
    if cursor != len(words):
        raise ValueError('Unexpected tokens after native trigger')
    return decoded[0], decoded[1]


def inspect_city_ai(original_triggers: list[str], final_triggers: list[str],
                    original_variables: list[str], final_variables: list[str]) -> dict:
    """Check the City-only server-side AI/wave branch against the 2012 source.

    In particular, the original mission sets g_multiplayer_game_type to 7,
    not Warband's other multiplayer game type 6. Comparing to 6 makes our
    wave and recovery controllers permanently dormant on the original mode.
    """
    checks: dict[str, bool] = {}
    problems: list[str] = []

    def require(key: str, condition: bool, problem: str):
        checks[key] = bool(condition)
        if not condition:
            problems.append(problem)

    if len(original_triggers) != 25 or len(final_triggers) < 31:
        raise ValueError('Expected original 25 and final 31 City triggers')
    if len(original_variables) != ORIGINAL_GLOBALS or len(final_variables) < ORIGINAL_GLOBALS + 2:
        raise ValueError('Expected original and City global-variable tables')
    game_name = 'g_multiplayer_game_type'
    if original_variables.count(game_name) != 1:
        raise ValueError('Missing unique historical invasion mode global')
    g_type = GLOBAL_BASE + original_variables.index(game_name)
    original_init_conditions, original_init_ops = decode_trigger(original_triggers[3])
    # Original mission trigger 3 is ti_before_mission_start (-19), with no
    # conditions, and unconditionally writes game type 7 as its FIRST op.
    require('original_invasion_mode_initialization',
            original_triggers[3].split()[0] == '-19.000000' and
            not original_init_conditions and
            bool(original_init_ops) and
            original_init_ops[0] == (2133, (g_type, INVASION_GAME_TYPE)),
            'Historical Invasion mission does not initialize game type 7 as expected')

    wave_conditions, wave_ops = decode_trigger(final_triggers[28])
    recovery_conditions, recovery_ops = decode_trigger(final_triggers[30])
    for label, conditions in [('reinforcement', wave_conditions),
                              ('recovery', recovery_conditions)]:
        mode_comparisons = [(op, args) for op, args in conditions if g_type in args]
        require(label + '_correct_mode',
                mode_comparisons == [(31, (g_type, INVASION_GAME_TYPE))],
                label + ' must use the original Invasion game type 7, not 6')
        require(label + '_server_guard', (417, ()) in conditions,
                label + ' is missing multiplayer_is_server')

    for key in ('wave_number', 'g_round_ended'):
        if original_variables.count(key) != 1:
            raise ValueError('Missing original '+key)
    g_wave = GLOBAL_BASE + original_variables.index('wave_number')
    g_ended = GLOBAL_BASE + original_variables.index('g_round_ended')
    g_last = GLOBAL_BASE + final_variables.index(SENTINEL)
    g_mode = GLOBAL_BASE + final_variables.index(TACTICAL_GLOBAL)
    require('reinforcement_once_per_wave',
            (32, (g_wave, g_last)) in wave_conditions and
            (2133, (g_last, g_wave)) in wave_ops,
            'Reinforcement sentinel is not correlated to advancing original waves')
    require('reinforcement_round_active', (31, (g_ended, 0)) in wave_conditions,
            'Reinforcements could run after the round ended')
    require('recovery_round_active', (31, (g_ended, 0)) in recovery_conditions,
            'Tactical recovery could run after the round ended')
    require('reinforcement_reserved_survivors',
            any(op == 1702 for op, _ in wave_ops) and
            any(op == 1707 for op, _ in wave_ops) and
            any(op == 1770 for op, _ in wave_ops) and
            any(op == 31 and args[-1:] == (0,) for op, args in wave_ops) and
            any(op == 1765 for op, _ in wave_ops) and
            any(op == 33 and args[-2:] == (min(GROUPS), max(GROUPS) + 1)
                for op, args in wave_ops),
            'Reinforcement must count live NPCs in survivor team 0 and groups 5-7')
    require('recovery_reserved_survivors',
            all(any(op == code for op, _ in recovery_ops)
                for code in (1702, 1707, 1770, 1765)) and
            any(op == 33 and args[-2:] == (min(GROUPS), max(GROUPS) + 1)
                for op, args in recovery_ops),
            'Tactical recovery must count only live reserved survivor NPCs')
    require('recovery_hysteresis_state',
            (2133, (g_mode, 1)) in recovery_ops and
            (2133, (g_mode, 0)) in recovery_ops,
            'Tactical fallback/regroup state transitions are missing')
    require('reinforcement_visitors_team_and_groups',
            len([1 for op, args in wave_ops if op == 1265]) == 4 and
            all(len(args) == 5 and args[2] == 1 and args[3] == 0 and args[4] in GROUPS
                for op, args in wave_ops if op == 1265),
            'Reinforcements must add exactly four class branches to team 0 and reserved groups')
    return {'checks': checks, 'problems': problems,
            'original_invasion_mode': INVASION_GAME_TYPE,
            'runtime_verified': False}