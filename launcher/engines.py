"""Read-only pairing of a discovered Warband install with its WSE2 programs.

Discovery already proves a broad, bounded picture: one or more Warband roots and
zero or more ``wse2`` executables. The one-click launcher needs something
narrower and fail-closed: exactly one Warband root, plus the WSE2 **client** and
**dedicated** executables that will actually be started.

This module only selects candidates and explains why it could not. It never
executes a candidate, never writes to the game tree and never assumes that a
file name proves a compatible WSE2 release. ``executable_status`` remains the
same MZ/PE-header sanity check used by discovery.
"""
from __future__ import annotations

import os
from pathlib import Path

from .discovery import executable_status

CLIENT_NAMES = ('mb_warband_wse2.exe',)
DEDICATED_NAMES = ('mb_warband_wse2_dedicated.exe',)
WARBAND_NAME = 'mb_warband.exe'

CLIENT_ROLE = 'client'
DEDICATED_ROLE = 'dedicated'
ROLE_NAMES = {CLIENT_ROLE: CLIENT_NAMES, DEDICATED_ROLE: DEDICATED_NAMES}


def _key(path):
    return os.path.normcase(str(Path(path).expanduser().absolute()))


def found_games(report):
    """Found Warband candidates from a discovery v1 report (never inferred)."""
    candidates = report.get('candidates') if isinstance(report, dict) else None
    return [item for item in candidates or []
            if isinstance(item, dict) and item.get('status') == 'found'
            and item.get('kind') == 'warband']


def found_wse2(report):
    candidates = report.get('wse2_candidates') if isinstance(report, dict) else None
    return [item for item in candidates or []
            if isinstance(item, dict) and item.get('status') == 'found'
            and item.get('kind') == 'wse2']


def select_game_root(report, *, game_root=None):
    """Return ``(candidate, blockers)`` for exactly one owned Warband root.

    An explicit root is accepted only when discovery itself validated a matching
    candidate, so the caller cannot bypass the read-only discovery evidence.
    """
    blockers = []
    games = found_games(report)
    if not games:
        return None, ['warband_not_found']
    if game_root is not None:
        wanted = _key(game_root)
        matches = [item for item in games if _key(item.get('path')) == wanted]
        if len(matches) == 1:
            return matches[0], blockers
        return None, ['game_root_not_discovered']
    if len(games) > 1:
        return None, ['selection_required']
    return games[0], blockers


def _wse2_path(item):
    executable = item.get('executable')
    return Path(executable) if isinstance(executable, str) else None


def _match_role(candidates, names, *, parent=None):
    """Found candidates with a role file name, optionally under one directory."""
    matched = []
    for item in candidates:
        path = _wse2_path(item)
        if path is None or path.name.casefold() not in names:
            continue
        if parent is not None and _key(path.parent) != _key(parent):
            continue
        matched.append(item)
    return matched


def _choose(matched, role, blockers):
    if not matched:
        blockers.append(role + '_not_found')
        return None
    unique = {}
    for item in matched:
        unique.setdefault(_key(_wse2_path(item)), item)
    if len(unique) > 1:
        blockers.append(role + '_selection_required')
        return None
    return next(iter(unique.values()))


def _explicit(exe, role, blockers):
    """Validate one caller-supplied executable without executing it."""
    path = Path(str(exe)).expanduser()
    status = executable_status(path)
    if status != 'found':
        blockers.append(role + '_' + status)
        return None
    return {'path': str(path), 'executable': str(path), 'kind': 'wse2',
            'status': 'found', 'provenance': ['explicit']}


def select_engines(report, game_root, *, client_exe=None, dedicated_exe=None):
    """Pair the WSE2 client and dedicated executables for one Warband root.

    Auto-pairing prefers executables directly inside the selected game root
    (the layout the historical one-click runs used). If a role is absent there,
    a single matching executable anywhere in the bounded discovery result is
    accepted. Ambiguity is a blocker, never a guess.
    """
    blockers = []
    game_root = Path(game_root)
    candidates = found_wse2(report)
    chosen = {}
    for role, names, explicit in (
            (CLIENT_ROLE, CLIENT_NAMES, client_exe),
            (DEDICATED_ROLE, DEDICATED_NAMES, dedicated_exe)):
        if explicit is not None:
            item = _explicit(explicit, role, blockers)
            chosen[role] = item
            continue
        local = _match_role(candidates, names, parent=game_root)
        item = _choose(local, role, blockers)
        if item is None and (role + '_not_found') in blockers:
            # Fall back to a single role-named executable outside the root.
            blockers.remove(role + '_not_found')
            fallback = _match_role(candidates, names)
            item = _choose(fallback, role, blockers)
        chosen[role] = item
    if chosen[CLIENT_ROLE] is not None and chosen[DEDICATED_ROLE] is not None:
        if _key(chosen[CLIENT_ROLE]['path']) == _key(chosen[DEDICATED_ROLE]['path']):
            blockers.append('engine_roles_same_executable')
    return {
        'warband_root': str(game_root),
        'client': chosen[CLIENT_ROLE],
        'dedicated': chosen[DEDICATED_ROLE],
        'blockers': blockers,
        'runtime_verified': False,
    }


def plan_engines(report, *, game_root=None, client_exe=None, dedicated_exe=None):
    """Select the game root and both WSE2 programs in one fail-closed step."""
    selected, blockers = select_game_root(report, game_root=game_root)
    if selected is None:
        return {'warband_root': None, 'client': None, 'dedicated': None,
                'blockers': blockers, 'runtime_verified': False}
    engines = select_engines(report, selected['path'], client_exe=client_exe,
                             dedicated_exe=dedicated_exe)
    engines['warband'] = selected
    return engines
