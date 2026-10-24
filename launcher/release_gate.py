"""Read-only delivery checks for a City-first solo release candidate.

This is a **candidate gate**, not acceptance. It verifies the repository-facing
delivery contract that the release notes depend on:

* required files exist (version, README, Windows bootstrap/provenance docs,
  launcher, installer planner, A's builder and archive audit);
* documented reproducible commands are present;
* ``VERSION`` is well-formed and matches the installed module receipt when one is
  supplied;
* no proprietary archives/game executables/logs are tracked by Git;
* no local personal install paths or obvious secrets are present in tracked text;
* a supplied installed module is structurally a City build and still says
  ``runtime_verified=false``.

Nothing is built, installed or launched. Missing runtime evidence is reported as
a gap; it never flips a check to accepted.
"""
from __future__ import annotations

import argparse
import json
import re
import subprocess
from pathlib import Path

from .install import MODULE_NAME, verify_built_module

SCHEMA = 'zombieee.release-gate.v1'
MAX_TRACKED_FILES = 20000
MAX_SCAN_BYTES = 256 * 1024
VERSION_RE = re.compile(r'\d+\.\d+\.\d+\Z')
REQUIRED_FILES = {
    'VERSION': 'release version',
    'README.md': 'user-facing readme',
    'docs/WINDOWS_BOOTSTRAP.md': 'Windows install/launch instructions',
    'docs/PROVENANCE.md': 'provenance and attribution',
    'launcher/play_city.py': 'one-command entry point',
    'launcher/control_panel.py': 'desktop launcher surface',
    'launcher/install.py': 'reversible installer',
    'launcher/maintenance.py': 'repair and quarantine uninstall surface',
    'installer/manifest.py': 'install planner',
    'tools/build.py': 'Agent A builder',
    'tools/archive_audit.py': 'pinned archive audit',
}
REQUIRED_COMMAND_TOKENS = (
    'launcher.play_city',
    'tools/build.py',
    'archive_audit',
)
FORBIDDEN_EXTENSIONS = ('.rar', '.zip', '.7z', '.exe', '.dll', '.log')
PERSONAL_PATH_RE = re.compile(r'[A-Za-z]:\\Users\\[^\\\s"|\']+')
SECRET_RE = re.compile(
    r"(BEGIN [A-Z ]*PRIVATE KEY|\bghp_[A-Za-z0-9]{20,}"
    r"|\bgithub_pat_[A-Za-z0-9_]{20,}|\bAKIA[0-9A-Z]{16}"
    r"|\bsk-[A-Za-z0-9]{20,})")
SCAN_ALLOWLIST_PREFIXES = ('tests/', 'reference/')


class ReleaseGateError(RuntimeError):
    """The gate could not inspect its inputs."""


def git_tracked_files(root, *, runner=None, timeout=60):
    """Bounded list of tracked paths; never mutates the repository."""
    if runner is None:
        def runner(command, **kwargs):
            return subprocess.run(command, capture_output=True, text=True,
                                  timeout=kwargs.get('timeout', timeout),
                                  shell=False)
    try:
        completed = runner(['git', '-C', str(Path(root).absolute()),
                            'ls-files', '-z'], timeout=timeout)
    except (OSError, subprocess.TimeoutExpired) as exc:
        raise ReleaseGateError('git_tracked_files_unavailable') from exc
    if getattr(completed, 'returncode', 1) != 0:
        raise ReleaseGateError('git_tracked_files_failed')
    raw = completed.stdout if isinstance(completed.stdout, str) else ''
    files = [item for item in raw.split('\x00') if item][:MAX_TRACKED_FILES]
    return files


def _read_bounded(path):
    try:
        with open(path, 'rb') as stream:
            return stream.read(MAX_SCAN_BYTES).decode('utf-8', errors='replace')
    except OSError:
        return ''


def build_release_gate(*, root=None, game_root=None, tracked_files=None,
                       git_runner=None, expected_version=None):
    """Compose the read-only delivery-gate report."""
    root = Path(root) if root is not None else Path(__file__).resolve().parents[1]
    root = root.absolute()
    checks, blockers, warnings = {}, [], []

    def check(name, ok, note=''):
        checks[name] = {'ok': bool(ok), 'note': note}
        if not ok:
            blockers.append(name)
        return bool(ok)

    missing = [relative for relative in REQUIRED_FILES
               if not (root / relative).is_file()]
    check('required_files', not missing,
          'missing=' + ','.join(missing) if missing else 'all present')
    version_text = ''
    version_path = root / 'VERSION'
    if version_path.is_file():
        version_text = _read_bounded(version_path).strip().splitlines()
        version_text = version_text[0] if version_text else ''
    check('version_format', bool(VERSION_RE.match(version_text)),
          'VERSION=' + (version_text or 'missing'))
    if expected_version is not None:
        check('version_matches_expected', version_text == expected_version,
              'expected=' + str(expected_version))
    instructions = ''
    for relative in ('docs/WINDOWS_BOOTSTRAP.md', 'README.md'):
        instructions += '\n' + _read_bounded(root / relative)
    missing_tokens = [token for token in REQUIRED_COMMAND_TOKENS
                      if token not in instructions]
    check('reproducible_commands', not missing_tokens,
          'missing=' + ','.join(missing_tokens) if missing_tokens else 'documented')

    if tracked_files is None:
        try:
            tracked_files = git_tracked_files(root, runner=git_runner)
        except ReleaseGateError as exc:
            tracked_files = []
            warnings.append('git_tracked_files_unavailable')
            warnings.append(str(exc)[:120])
    banned = [name for name in tracked_files
              if Path(name).suffix.casefold() in FORBIDDEN_EXTENSIONS]
    check('no_tracked_binaries_or_logs', not banned,
          'banned=' + ','.join(banned[:20]) if banned else 'clean')
    scanned = 0
    personal_hits, secret_hits = [], []
    for name in tracked_files:
        if name.startswith(SCAN_ALLOWLIST_PREFIXES):
            continue
        path = root / name
        if not path.is_file():
            continue
        text = _read_bounded(path)
        scanned += 1
        if PERSONAL_PATH_RE.search(text):
            personal_hits.append(name)
        if SECRET_RE.search(text):
            secret_hits.append(name)
    check('no_personal_local_paths', not personal_hits,
          'files=' + ','.join(personal_hits[:20]) if personal_hits else 'clean')
    check('no_obvious_secrets', not secret_hits,
          'files=' + ','.join(secret_hits[:20]) if secret_hits else 'clean')
    checks['tracked_text_scan'] = {'ok': True,
                                   'note': 'scanned %d tracked files' % scanned}

    module = None
    if game_root is not None:
        module_dir = Path(game_root).expanduser().absolute() / 'Modules' / MODULE_NAME
        if module_dir.is_dir():
            module = verify_built_module(module_dir)
            check('installed_module_city_structure', module.get('ok') is True,
                  'problems=' + ','.join(module.get('problems') or [])
                  if module.get('problems') else 'city module valid')
            check('installed_runtime_not_claimed',
                  module.get('checks', {}).get('runtime_verified_false') is True,
                  'build receipt says runtime_verified=false')
        else:
            warnings.append('installed_module_not_found')
    else:
        warnings.append('installed_module_not_provided')
    if module is not None and version_text:
        try:
            import json as _json
            with open(Path(game_root).expanduser().absolute() / 'Modules'
                      / MODULE_NAME / 'ZOMBIEEE_REMASTER.json', 'rb') as stream:
                manifest = _json.loads(stream.read(1024 * 1024).decode('utf-8'))
        except (OSError, ValueError):
            manifest = {}
        remaster_version = manifest.get('remaster_version')
        if isinstance(remaster_version, str):
            check('module_version_matches', remaster_version == version_text,
                  'module=' + remaster_version)
        else:
            warnings.append('module_version_unknown')

    gate = {
        'schema': SCHEMA, 'schema_version': 1,
        'read_only': True, 'no_launch': True,
        'ok': not blockers,
        'blockers': blockers,
        'warnings': warnings,
        'checks': checks,
        'version': version_text or None,
        'remaster_module': ({'ok': module.get('ok'),
                             'module_sha256': module.get('module_sha256'),
                             'file_count': module.get('file_count'),
                             'map_scope': module.get('map_scope'),
                             'trigger_count': module.get('trigger_count')}
                            if module else None),
        'delivery_status': 'candidate-checks-only',
        'acceptance': 'none',
        'runtime_verified': False,
        'notes': [
            'This gate never claims playable acceptance; owner review and sealed '
            'runtime evidence remain required.',
            'Archives, game binaries, WSE2 and original assets are never committed.',
        ],
    }
    return gate


def format_release_gate(gate):
    lines = ['Release delivery checks: ' + ('OK' if gate['ok'] else 'BLOCKED')]
    for name, entry in gate.get('checks', {}).items():
        lines.append('  %-32s %s%s' % (name, 'pass' if entry.get('ok') else 'FAIL',
                                       ' (' + entry['note'] + ')'
                                       if entry.get('note') else ''))
    for blocker in gate.get('blockers') or []:
        lines.append('  blocker : ' + str(blocker))
    for warning in gate.get('warnings') or []:
        lines.append('  warning : ' + str(warning))
    lines.append('  status  : ' + str(gate.get('delivery_status'))
                 + '; runtime_verified=false; acceptance=none')
    return '\n'.join(lines)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', help='repository checkout to check')
    parser.add_argument('--game-root', help='optional installed Warband root')
    parser.add_argument('--json', action='store_true')
    args = parser.parse_args(argv)
    gate = build_release_gate(root=args.root, game_root=args.game_root)
    if args.json:
        print(json.dumps(gate, indent=2, sort_keys=True))
    else:
        print(format_release_gate(gate))
    return 0 if gate['ok'] else 2


if __name__ == '__main__':
    raise SystemExit(main())
