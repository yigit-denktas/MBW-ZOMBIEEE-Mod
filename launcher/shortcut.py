"""Desktop shortcut creation for the private City control panel.

The shortcut launches the launcher's control panel (Play Solo / settings / logs /
repair / uninstall / release checks). Creation is explicit: a spec can be built
and inspected without touching the user's desktop, and the actual ``.lnk`` write
uses a fixed PowerShell ``WScript.Shell`` script with values passed only through
environment variables (never string-interpolated into the script).

No game is launched. No credential, serial or control key is accepted here.
"""
from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

SCHEMA = 'zombieee.desktop-shortcut.v1'
ALLOWED_MODULES = ('launcher.control_panel', 'launcher.play_city')
POWERSHELL_SCRIPT = (
    "$ErrorActionPreference = 'Stop';"
    "$shell = New-Object -ComObject WScript.Shell;"
    "$link = $shell.CreateShortcut($env:ZOMBIEEE_LNK);"
    "$link.TargetPath = $env:ZOMBIEEE_TARGET;"
    "$link.Arguments = $env:ZOMBIEEE_ARGS;"
    "$link.WorkingDirectory = $env:ZOMBIEEE_CWD;"
    "$link.Description = $env:ZOMBIEEE_DESC;"
    "$link.Save();"
    "Write-Output 'ok'"
)


class ShortcutError(RuntimeError):
    """The shortcut spec or destination was invalid."""


def _python_window_executable(python_executable=None):
    candidate = Path(python_executable or sys.executable).absolute()
    if candidate.name.casefold() == 'python.exe':
        windowed = candidate.with_name('pythonw.exe')
        if windowed.is_file():
            return windowed
    return candidate


def shortcut_spec(*, repo_root=None, settings_path=None, python_executable=None,
                  module='launcher.control_panel', name='Play City'):
    """Return an inspectable shortcut spec; no filesystem writes."""
    if module not in ALLOWED_MODULES:
        raise ShortcutError('shortcut module not allowed')
    repo_root = (Path(repo_root) if repo_root is not None
                 else Path(__file__).resolve().parents[1]).absolute()
    settings = None
    if settings_path is not None:
        settings = Path(settings_path).expanduser().absolute()
        if settings.suffix.casefold() != '.json':
            raise ShortcutError('settings path must be a .json file')
    argv = [str(_python_window_executable(python_executable)),
            '-m', module]
    if settings is not None:
        argv.extend(['--settings', str(settings)])
    return {
        'schema': SCHEMA, 'schema_version': 1,
        'name': str(name)[:120] or 'Play City',
        'target': argv[0], 'arguments': ' '.join(argv[1:]),
        'argv': argv,
        'working_directory': str(repo_root),
        'settings_path': str(settings) if settings is not None else None,
        'module': module,
        'runtime_verified': False,
        'launches_game_directly': False,
    }


def create_shortcut(spec, lnk_path, *, runner=None, overwrite=False,
                    timeout=30):
    """Create the ``.lnk`` via PowerShell; returns a bounded receipt."""
    if not isinstance(spec, dict) or spec.get('schema') != SCHEMA:
        raise ShortcutError('not a shortcut spec')
    lnk = Path(lnk_path).expanduser().absolute()
    if lnk.suffix.casefold() != '.lnk':
        raise ShortcutError('shortcut output must be a .lnk file')
    if not lnk.parent.is_dir():
        raise ShortcutError('shortcut parent directory missing')
    if lnk.exists() and not overwrite:
        raise ShortcutError('shortcut already exists')
    if os.name != 'nt':
        raise ShortcutError('desktop shortcuts require Windows')
    env = dict(os.environ)
    env.update({
        'ZOMBIEEE_LNK': str(lnk),
        'ZOMBIEEE_TARGET': str(spec['target']),
        'ZOMBIEEE_ARGS': str(spec['arguments']),
        'ZOMBIEEE_CWD': str(spec['working_directory']),
        'ZOMBIEEE_DESC': str(spec['name']),
    })
    if runner is None:
        def runner(command, **kwargs):
            return subprocess.run(command, capture_output=True, text=True,
                                  timeout=kwargs.get('timeout', timeout),
                                  shell=False, env=kwargs.get('env'))
    try:
        completed = runner(
            ['powershell.exe', '-NoProfile', '-NonInteractive', '-Command',
             POWERSHELL_SCRIPT], env=env, timeout=timeout)
    except (OSError, subprocess.TimeoutExpired) as exc:
        raise ShortcutError('shortcut_runner_' + type(exc).__name__) from exc
    returncode = getattr(completed, 'returncode', 0)
    if returncode != 0:
        raise ShortcutError('shortcut_creation_failed:' + str(returncode))
    return {
        'schema': 'zombieee.desktop-shortcut-receipt.v1', 'schema_version': 1,
        'path': str(lnk), 'created': True, 'module': spec.get('module'),
        'settings_path': spec.get('settings_path'),
        'launches_game_directly': False, 'runtime_verified': False,
    }
