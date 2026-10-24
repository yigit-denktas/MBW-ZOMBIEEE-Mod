"""Private launcher settings for the Windows one-click City entry point.

Settings are a small, versioned JSON file kept outside the repository (by default
under the user's local application data). They only carry non-secret launch
defaults; the pinned archive, evidence root and desktop entry point are local
paths and must stay private. No passwords, control keys, serials or tokens are
ever accepted here.
"""
from __future__ import annotations

import json
import os
from pathlib import Path

SCHEMA = 'zombieee.launcher-settings.v1'
SCHEMA_VERSION = 1
MAX_BYTES = 64 * 1024
DEFAULT_NAME = 'launcher-settings.json'
FORBIDDEN_KEYS = ('password', 'passwd', 'secret', 'token', 'serial', 'control_key',
                  'admin', 'rcon')
ENEMY_PROFILES = ('generic', 'weak-wave1', 'native-only')
FIELDS = {
    'game_root': (str, None),
    'archive': (str, None),
    'evidence_root': (str, None),
    'enemy_profile': (str, ENEMY_PROFILES),
    'team0_bots': (int, None),
    'team2_bots': (int, None),
    'max_minutes': (float, None),
    'no_known_folders': (bool, None),
}


class SettingsError(ValueError):
    """The settings file is malformed or unsafe."""


def default_settings_path(environ=None, *, repo_root=None):
    env = os.environ if environ is None else environ
    if env.get('LOCALAPPDATA'):
        return Path(env['LOCALAPPDATA']) / 'ZOMBIEEE' / DEFAULT_NAME
    if repo_root is not None:
        return Path(repo_root) / 'local' / DEFAULT_NAME
    return Path.home() / '.zombieee' / DEFAULT_NAME


def _check_field(name, value):
    kind, choices = FIELDS[name]
    if value is None:
        return None
    if kind is float:
        if type(value) is not float and type(value) is not int:
            raise SettingsError('invalid_type:' + name)
        if isinstance(value, bool) or not 0 <= float(value) <= 24 * 60:
            raise SettingsError('invalid_range:' + name)
        return float(value)
    if kind is int:
        if type(value) is not int or isinstance(value, bool):
            raise SettingsError('invalid_type:' + name)
        minimum, maximum = (0, 200) if name == 'team0_bots' else (0, 500)
        if not minimum <= value <= maximum:
            raise SettingsError('invalid_range:' + name)
        return value
    if kind is bool:
        if type(value) is not bool:
            raise SettingsError('invalid_type:' + name)
        return value
    if not isinstance(value, str) or not value:
        raise SettingsError('invalid_type:' + name)
    if name == 'enemy_profile' and value not in choices:
        raise SettingsError('invalid_choice:' + name)
    if name in ('game_root', 'archive', 'evidence_root'):
        if '\x00' in value:
            raise SettingsError('invalid_path:' + name)
    return value


def validate_settings(data):
    """Validate an object; unknown non-secret keys are ignored with warnings."""
    if not isinstance(data, dict):
        raise SettingsError('settings_not_object')
    if data.get('schema') != SCHEMA:
        raise SettingsError('wrong_settings_schema')
    settings = {'schema': SCHEMA, 'schema_version': SCHEMA_VERSION}
    warnings = []
    for name in FIELDS:
        if name in data:
            settings[name] = _check_field(name, data[name])
    for name in data:
        lowered = str(name).casefold()
        if name in ('schema', 'schema_version') or name in FIELDS:
            continue
        if any(fragment in lowered for fragment in FORBIDDEN_KEYS):
            raise SettingsError('secret_field_refused:' + str(name))
        warnings.append('unknown_setting_ignored:' + str(name)[:32])
    return settings, warnings


def load_settings(path=None, *, repo_root=None):
    path = Path(path) if path is not None else default_settings_path(
        repo_root=repo_root)
    if not path.is_file():
        return {'schema': SCHEMA, 'schema_version': SCHEMA_VERSION}, ['settings_missing']
    if path.is_symlink():
        raise SettingsError('settings_path_redirected')
    with open(path, 'rb') as stream:
        data = stream.read(MAX_BYTES + 1)
    if len(data) > MAX_BYTES:
        raise SettingsError('settings_oversized')
    try:
        parsed = json.loads(data.decode('utf-8'))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise SettingsError('settings_invalid_json') from exc
    settings, warnings = validate_settings(parsed)
    settings['_path'] = str(path.absolute())
    return settings, warnings


def save_settings(data, path=None, *, repo_root=None, environ=None):
    path = Path(path) if path is not None else default_settings_path(
        environ=environ, repo_root=repo_root)
    payload, _warnings = validate_settings(data)
    if path.is_symlink():
        raise SettingsError('settings_path_redirected')
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_name(path.name + '.tmp')
    temp.unlink(missing_ok=True)
    try:
        with open(temp, 'xb') as stream:
            stream.write((json.dumps(payload, indent=2, sort_keys=True)
                          + '\n').encode('utf-8'))
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temp, path)
    finally:
        temp.unlink(missing_ok=True)
    return path


def cli_defaults(settings):
    """Translate private settings into launcher CLI keyword defaults."""
    settings = settings or {}
    return {
        'game_root': settings.get('game_root'),
        'archive': [settings['archive']] if settings.get('archive') else None,
        'evidence_root': settings.get('evidence_root'),
        'enemy_profile': settings.get('enemy_profile'),
        'team0_bots': settings.get('team0_bots'),
        'team2_bots': settings.get('team2_bots'),
        'max_minutes': settings.get('max_minutes'),
        'no_known_folders': (True if settings.get('no_known_folders') else None),
    }


def merge_cli(settings, args):
    """Apply settings only where the CLI left a value unset (CLI wins)."""
    merged = dict(settings or {})
    for key, value in cli_defaults(settings).items():
        if value is None:
            continue
        current = getattr(args, key, None)
        if current is None:
            setattr(args, key, value)
    return args
