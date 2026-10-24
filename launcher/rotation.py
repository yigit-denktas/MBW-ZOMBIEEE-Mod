"""Validated private City rotation contract for the Windows launcher.

The first live City runs showed three server-side configuration traps that are
not visible in the build:

* ``set_bot_count`` team numbers are 1-based (1 = player/first team); the
  City native defender squad is switched on with team-1 bots = 4 (telemetry
  team 0), while ``build_rotation()`` stays stock by default;
* without a positive second-team bot count the native wave controller stayed at
  ``wave=0`` / ``team1=0``;
* without respawn/round settings the player could remain dead with no new
  round, and generic ``set_bot_count`` bots use the faction-default
  ``trp_invader_multiplayer_ai`` (Crazed Civilian), not the native Zombie roster.

This module is the single source of truth for the command sequence the launcher
must emit before ``start``. It is deliberately data-only: it never launches a
process, writes a config or claims gameplay acceptance. The roster caveat is
tracked separately in issue #13/#14; this contract only guarantees the
load-bearing rotation fields.
"""
from __future__ import annotations

import hashlib

MISSION = 'multiplayer_iv'
MAP = 'tbfc_invasion_4'
FACTIONS = ('fac_kingdom_1', 'fac_kingdom_invaders')
SERVER_NAME = 'ZOMBIEEE_Local_Test'

# The generic-bot roster is a known limitation, not a hidden default.
ROSTER_CAVEAT = ('generic set_bot_count bots use the faction default '
                 'trp_invader_multiplayer_ai (Crazed Civilian); native Zombie '
                 'troops require a separate spawn path (issue #13)')

DEFAULT_MAX_BOTS = 200
DEFAULT_TEAM1_BOTS = 0
# A's merged roster patch maps faction 15 + ``g_multiplayer_game_type==7``
# bots to the 981..984 survivor troops; ``set_bot_count 1 4`` is the switch
# that spawns the native team-0 allied squad (1-based rotation team 1).
DEFENDER_SQUAD_BOTS = 4
DEFAULT_TEAM2_BOTS = 32
DEFAULT_RESPAWN_PERIOD = 5
DEFAULT_ROUND_MAX_SECONDS = 1800
DEFAULT_DEFENDER_SPAWNS = 0
DEFAULT_PLAYER_RESPAWN_AS_BOT = 0


def _int(value, name, minimum, maximum):
    if type(value) is not int or not minimum <= value <= maximum:
        raise ValueError(name + ' must be an integer in [%d, %d]' % (minimum, maximum))
    return value


def build_rotation(*, server_name=SERVER_NAME, mission=MISSION, map_name=MAP,
                   team1_bots=DEFAULT_TEAM1_BOTS, team2_bots=DEFAULT_TEAM2_BOTS,
                   defender_squad=False,
                   max_bots=DEFAULT_MAX_BOTS,
                   respawn_period=DEFAULT_RESPAWN_PERIOD,
                   round_max_seconds=DEFAULT_ROUND_MAX_SECONDS,
                   defender_spawns=DEFAULT_DEFENDER_SPAWNS,
                   player_respawn_as_bot=DEFAULT_PLAYER_RESPAWN_AS_BOT):
    """Return the validated rotation commands, with ``start`` last.

    ``team2_bots`` is the second/backend team (1-based command numbering) and
    must be positive: a zero value reproduced the no-wave failure.
    """
    if not isinstance(server_name, str) or not server_name.strip():
        raise ValueError('server_name must be a non-empty string')
    if mission != MISSION or map_name != MAP:
        raise ValueError('only the original City mission/map is supported')
    if type(defender_squad) is not bool:
        raise ValueError('defender_squad must be a boolean')
    if defender_squad:
        if team1_bots != DEFAULT_TEAM1_BOTS:
            raise ValueError('defender_squad conflicts with an explicit team1_bots')
        team1_bots = DEFENDER_SQUAD_BOTS
    team1_bots = _int(team1_bots, 'team1_bots', 0, 200)
    team2_bots = _int(team2_bots, 'team2_bots', 1, 500)
    max_bots = _int(max_bots, 'max_bots', 50, 500)
    if team1_bots + team2_bots > max_bots:
        raise ValueError('team bot counts exceed max_num_bots')
    respawn_period = _int(respawn_period, 'respawn_period', 1, 300)
    round_max_seconds = _int(round_max_seconds, 'round_max_seconds', 60, 7200)
    defender_spawns = _int(defender_spawns, 'defender_spawns', 0, 6)
    player_respawn_as_bot = _int(player_respawn_as_bot, 'player_respawn_as_bot', 0, 1)
    return [
        'set_server_name ' + server_name.strip(),
        'set_mission ' + mission,
        'set_map ' + map_name,
        'set_factions ' + ' '.join(FACTIONS),
        'set_factions_voteable 0',
        'set_randomize_factions 0',
        'max_num_bots %d' % max_bots,
        # 1-based: 1 = player/first team, 2 = second/opposing team.
        'set_bot_count 1 %d' % team1_bots,
        'set_bot_count 2 %d' % team2_bots,
        'set_respawn_period %d' % respawn_period,
        'set_defender_spawn_count %d' % defender_spawns,
        'set_round_max_seconds %d' % round_max_seconds,
        'set_player_respawn_as_bot %d' % player_respawn_as_bot,
        'start',
    ]


def build_defender_rotation(**kwargs):
    """City rotation that switches on the native team-0 defender squad.

    ``set_bot_count`` numbering is 1-based, so rotation team 1 is telemetry
    team 0. ``build_rotation()`` keeps its stock default (no allied bots).
    """
    if 'team1_bots' in kwargs:
        raise TypeError('build_defender_rotation fixes team1_bots')
    kwargs['defender_squad'] = True
    return build_rotation(**kwargs)


def rotation_sha256(lines):
    """Stable digest of the exact rotation lines (UTF-8, LF, trailing LF)."""
    payload = ('\n'.join(lines) + '\n').encode('utf-8')
    return hashlib.sha256(payload).hexdigest()


def validate_rotation(lines):
    """Fail closed if a rotation list violates the observed contract.

    Checks are intentionally textual: the launcher must emit exactly these
    commands, in this order, with no unvalidated extra team/bot settings.
    """
    if not isinstance(lines, (list, tuple)) or not lines:
        raise ValueError('rotation must be a non-empty list')
    lines = [str(line) for line in lines]
    if lines[-1] != 'start':
        raise ValueError('rotation must end with start')
    if any(line == 'start' for line in lines[:-1]):
        raise ValueError('only one start command is allowed, at the end')
    required_prefix = [
        'set_server_name ', 'set_mission ' + MISSION, 'set_map ' + MAP,
        'set_factions ' + ' '.join(FACTIONS), 'set_factions_voteable 0',
        'set_randomize_factions 0',
    ]
    for index, prefix in enumerate(required_prefix):
        if not lines[index].startswith(prefix):
            raise ValueError('unexpected rotation line at %d: %r' % (index, lines[index]))
    expected = build_rotation(
        team1_bots=int(lines[7].split()[2]),
        team2_bots=int(lines[8].split()[2]),
        max_bots=int(lines[6].split()[1]),
        respawn_period=int(lines[9].split()[1]),
        defender_spawns=int(lines[10].split()[1]),
        round_max_seconds=int(lines[11].split()[1]),
        player_respawn_as_bot=int(lines[12].split()[1]),
    )
    if lines != expected:
        raise ValueError('rotation does not match the validated command contract')
    if int(lines[8].split()[2]) <= 0:
        raise ValueError('second-team bot count must be positive')
    return True
