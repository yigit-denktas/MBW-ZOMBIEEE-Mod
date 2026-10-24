"""Reversible execution of Agent A's pinned City build into a Warband install.

The one-click launcher may not re-implement Agent A's builder, archive policy or
gameplay patches. This module only orchestrates:

1. a read-only preflight (owned Warband root, pinned archive identity, 7-Zip
   member CRC, no running game processes, no redirected transaction paths);
2. ``tools/build.py`` as a subprocess into a fresh same-volume stage;
3. validation of the built module's own ``ZOMBIEEE_REMASTER.json`` receipt;
4. a **backup first** activation: an existing ``Modules/ZOMBIEEE_Remaster`` is
   renamed to ``.backup-<transaction>`` and is never deleted;
5. a digest comparison of the installed tree against the staged tree;
6. rollback to the backup if activation or verification fails, retaining both
   trees (and a durable journal) when rollback itself cannot complete.

No game process is started here. Nothing in the game tree is deleted. Callers
must pass Agent A's verified archive identity rather than a duplicated hash
policy, and the builder remains the sole owner of build correctness.

The journal and receipts are private local evidence and are not committed.
"""
from __future__ import annotations

import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

MODULE_NAME = 'ZOMBIEEE_Remaster'
JOURNAL_SCHEMA = 'zombieee.install-journal.v1'
RECEIPT_SCHEMA = 'zombieee.install-receipt.v1'
TRANSACTION_RE = re.compile(r'[A-Za-z0-9][A-Za-z0-9_-]{0,63}\Z')
MODULE_NAME_RE = re.compile(r'[A-Za-z][A-Za-z0-9_]{0,63}\Z')
MAX_MANIFEST_BYTES = 8 * 1024 * 1024
MAX_MODULE_FILES = 5000
MAX_OUTPUT_BYTES = 2000
GAME_PROCESS_NAMES = ('mb_warband.exe', 'mb_warband_wse2.exe',
                      'mb_warband_wse2_dedicated.exe')

# Agent A's accepted City-only profile (see handoffs/SESSION_CONTRACT.md).
CITY_BUILD_FLAGS = (
    '--experimental-defenders', '4',
    '--city-guardposts',
    '--wave-reinforcements',
    '--tactical-recovery',
    '--defender-loadouts', 'balanced-ai',
)

REQUIRED_MODULE_FILES = ('module.ini', 'mission_templates.txt', 'scripts.txt',
                         'troops.txt', 'variables.txt', 'lua/main.lua')


class InstallError(RuntimeError):
    """The plan is invalid or the installer was used out of contract."""


class InstallFailure(InstallError):
    """An expected, recorded execution failure (not a programming error)."""


def _key(path):
    return os.path.normcase(str(Path(path).expanduser().absolute()))


def _now_stamp():
    import time
    return time.strftime('%Y%m%d-%H%M%S')


def _sha256_file(path):
    digest = hashlib.sha256()
    with open(path, 'rb') as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b''):
            digest.update(chunk)
    return digest.hexdigest()


def _walk_module_files(module_dir, *, max_files=MAX_MODULE_FILES):
    """Yield (relative POSIX path, absolute path); reject links and oversize."""
    module_dir = Path(module_dir)
    if not module_dir.is_dir():
        raise InstallError('module directory missing: ' + module_dir.name)
    count = 0
    for root, dirs, files in os.walk(module_dir, followlinks=False):
        root_path = Path(root)
        for name in list(dirs):
            candidate = root_path / name
            if candidate.is_symlink():
                raise InstallError('unsafe_link_in_module: '
                                   + str(candidate.relative_to(module_dir)))
        for name in sorted(files):
            path = root_path / name
            if path.is_symlink():
                raise InstallError('unsafe_link_in_module: '
                                   + str(path.relative_to(module_dir)))
            count += 1
            if count > max_files:
                raise InstallError('module_file_limit_exceeded')
            yield path.relative_to(module_dir).as_posix(), path


def module_file_hashes(module_dir, *, max_files=MAX_MODULE_FILES):
    """Per-file SHA-256 ownership inventory for repair/uninstall.

    Bounded and sorted; links are rejected exactly like ``module_inventory``.
    The result identifies installer-owned bytes so later repair/uninstall can
    preserve modified or unrecognised user files instead of guessing.
    """
    files = []
    for relative, file_path in _walk_module_files(module_dir, max_files=max_files):
        files.append({'path': relative, 'sha256': _sha256_file(file_path)})
    files.sort(key=lambda item: item['path'])
    return files


def module_inventory(module_dir, *, max_files=MAX_MODULE_FILES):
    """Aggregate SHA-256 inventory compatible with the nightly build receipts.

    Digest is SHA-256 over ``relative_path\\0<sha256>\\n`` lines in sorted
    order. It identifies this exact tree; it is not a signature.
    """
    entries = []
    for relative, path in _walk_module_files(module_dir, max_files=max_files):
        entries.append(relative + '\0' + _sha256_file(path) + '\n')
    entries.sort()
    aggregate = hashlib.sha256(''.join(entries).encode('utf-8')).hexdigest()
    return {'module_sha256': aggregate, 'file_count': len(entries)}


def _bounded_text(value, limit=MAX_OUTPUT_BYTES):
    text = value if isinstance(value, str) else (
        value.decode('utf-8', errors='replace') if isinstance(value, (bytes, bytearray))
        else '')
    return text[-limit:]


def read_module_manifest(module_dir, *, limit=MAX_MANIFEST_BYTES):
    path = Path(module_dir) / 'ZOMBIEEE_REMASTER.json'
    try:
        with open(path, 'rb') as stream:
            data = stream.read(limit + 1)
    except (OSError, ValueError) as exc:
        raise InstallError('build_manifest_unreadable: ' + type(exc).__name__) from exc
    if len(data) > limit:
        raise InstallError('build_manifest_oversized')
    try:
        value = json.loads(data.decode('utf-8'))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise InstallError('build_manifest_invalid_json') from exc
    if not isinstance(value, dict):
        raise InstallError('build_manifest_not_object')
    return value


def verify_built_module(module_dir, *, expected_source_sha256=None,
                        expected_map_scope='city-only', min_trigger_count=31,
                        require_probe=True):
    """Validate one built/installed City module against its own receipt.

    This is a bounded structural check of Agent A's build receipt plus a few
    core files. It is **not** runtime evidence and never flips
    ``runtime_verified``.
    """
    module_dir = Path(module_dir)
    result = {'module_dir': str(module_dir), 'ok': False, 'checks': {},
              'problems': [], 'runtime_verified': False}
    try:
        manifest = read_module_manifest(module_dir)
    except InstallError as exc:
        result['problems'].append(str(exc))
        return result

    def check(name, value):
        result['checks'][name] = bool(value)
        if not value:
            result['problems'].append(name)
        return bool(value)

    source = manifest.get('source_archive_sha256')
    check('module_directory_exists', module_dir.is_dir())
    check('source_sha256_present',
          isinstance(source, str) and bool(re.fullmatch(r'[0-9a-f]{64}', source)))
    if expected_source_sha256 is not None:
        check('source_sha256_pinned', source == expected_source_sha256)
    check('runtime_verified_false', manifest.get('runtime_verified') is False)
    check('archive_crc_verified', manifest.get('archive_crc_verified') is True)
    check('city_scope', manifest.get('experimental_map_scope') == expected_map_scope)
    trigger_count = manifest.get('final_trigger_count')
    check('trigger_count', type(trigger_count) is int
          and trigger_count >= min_trigger_count)
    check('original_trigger_count',
          manifest.get('original_mission_trigger_count') == 25)
    for name in REQUIRED_MODULE_FILES:
        check('file:' + name, (module_dir / name).is_file())
    probe_text = ''
    probe_path = module_dir / 'lua' / 'main.lua'
    if probe_path.is_file():
        try:
            probe_text = probe_path.read_text(encoding='utf-8', errors='replace')
        except OSError:
            probe_text = ''
    if require_probe:
        check('probe_prefix', 'ZDB1|' in probe_text)
        check('probe_heartbeat', 'heartbeat' in probe_text)
    try:
        inventory = module_inventory(module_dir)
        result.update(inventory)
    except InstallError as exc:
        result['problems'].append(str(exc))
    result['trigger_count'] = trigger_count if type(trigger_count) is int else None
    result['source_archive_sha256'] = source if isinstance(source, str) else None
    result['map_scope'] = manifest.get('experimental_map_scope')
    result['ok'] = not result['problems']
    return result


def _redirected_components(paths):
    """Existing symlink/reparse components from each path root down."""
    from .recorder import is_redirected
    issues = []
    seen = set()
    for path in paths:
        current = Path(path).expanduser().absolute()
        for component in (*reversed(current.parents), current):
            key = _key(component)
            if key in seen:
                continue
            seen.add(key)
            if is_redirected(component):
                issues.append(str(component))
    return issues


def validate_module_name(module_name):
    """Return a safe Warband module directory name or raise ValueError."""
    if not isinstance(module_name, str) or not MODULE_NAME_RE.fullmatch(module_name):
        raise ValueError('module_name must be 1..64 safe module characters')
    return module_name


def install_paths(game_root, transaction_id, *, evidence_dir=None,
                  module_name=MODULE_NAME):
    """Return the exact transaction paths used by the plan and journal."""
    if not TRANSACTION_RE.fullmatch(str(transaction_id)):
        raise ValueError('transaction_id must be 1..64 safe ASCII characters')
    module_name = validate_module_name(module_name)
    modules = Path(game_root).expanduser().absolute() / 'Modules'
    target = modules / module_name
    stage_root = modules / ('.zombieee-stage-' + transaction_id)
    return {
        'game_root': str(Path(game_root).expanduser().absolute()),
        'modules': str(modules),
        'target': str(target),
        'stage_root': str(stage_root),
        'stage_module': str(stage_root / module_name),
        'backup': str(modules / (module_name + '.backup-' + transaction_id)),
        'journal': str(Path(evidence_dir).expanduser().absolute()
                       / ('install-journal-' + transaction_id + '.json'))
        if evidence_dir is not None else None,
    }


def build_argv(archive, stage_module, *, python_executable=None,
               repo_root=None, city_flags=CITY_BUILD_FLAGS):
    repo_root = Path(repo_root) if repo_root is not None else Path(__file__).resolve().parents[1]
    return [python_executable or sys.executable,
            str(repo_root / 'tools' / 'build.py'),
            '--archive', str(Path(archive).expanduser().absolute()),
            '--out', str(Path(stage_module).expanduser().absolute()),
            *[str(flag) for flag in city_flags]]


def running_game_processes(*, runner=None, timeout=30):
    """Read-only process-name probe; never starts, stops or inspects a game."""
    if os.name != 'nt':
        return []
    if runner is None:
        def runner(argv, **kwargs):
            return subprocess.run(argv, capture_output=True, text=True,
                                  timeout=kwargs.get('timeout', timeout), shell=False)
    try:
        completed = runner(['tasklist', '/FO', 'CSV', '/NH'], timeout=timeout)
    except (OSError, subprocess.TimeoutExpired, ValueError):
        return ['process_enumeration_unavailable']
    text = completed.stdout if isinstance(completed.stdout, str) else ''
    found = []
    for line in text.splitlines():
        name = line.split(',')[0].strip().strip('"').casefold()
        if name in GAME_PROCESS_NAMES and name not in found:
            found.append(name)
    return found


def plan_install(*, game_root, transaction_id, archive=None, archive_identity=None,
                 evidence_dir=None, expected_source_sha256=None,
                 python_executable=None, repo_root=None, city_flags=CITY_BUILD_FLAGS,
                 build_timeout=1800, running_processes=None,
                 module_name=MODULE_NAME):
    """Build a dry install plan; never writes, builds or launches anything.

    ``archive_identity`` must be Agent A's read-only audit report (the
    ``tools/archive_audit.py --json`` shape). A launcher must never construct a
    positive identity by itself.
    """
    from .discovery import executable_status
    from installer.manifest import path_issues

    game_root = Path(game_root).expanduser().absolute()
    transaction_id = str(transaction_id)
    paths = install_paths(game_root, transaction_id, evidence_dir=evidence_dir,
                           module_name=module_name)
    target = Path(paths['target'])
    stage_root = Path(paths['stage_root'])
    stage_module = Path(paths['stage_module'])
    backup = Path(paths['backup'])
    blockers, warnings = [], []
    evidence_path = (Path(evidence_dir).expanduser().absolute()
                     if evidence_dir is not None else None)
    inspected = [game_root, game_root / 'Modules', target, stage_root,
                 stage_module, backup]
    if archive is not None:
        inspected.append(Path(archive).expanduser().absolute())
    if evidence_path is not None:
        inspected.append(evidence_path)
    redirects = _redirected_components(inspected)
    if redirects:
        blockers.append('transaction_path_redirected')
    try:
        issues = path_issues([game_root, game_root / 'Modules', target,
                              stage_root, stage_module, backup]
                             + ([evidence_path] if evidence_path else []))
    except (OSError, ValueError):
        issues = [{'path': str(game_root), 'reason': 'path_inspection_failed'}]
    if any(issue.get('reason') == 'path_inspection_failed' for issue in issues):
        blockers.append('path_inspection_failed')

    executable_state = executable_status(game_root / 'mb_warband.exe')
    if executable_state != 'found':
        blockers.append('warband_invalid:' + executable_state)
    if target.exists() and not target.is_dir():
        blockers.append('target_not_directory')
    for path, name in ((stage_root, 'stage_path_exists'),
                       (backup, 'backup_path_exists')):
        if path.exists():
            blockers.append(name)
    if evidence_path is None:
        blockers.append('evidence_root_missing')
    else:
        try:
            if evidence_path.exists() and not evidence_path.is_dir():
                blockers.append('evidence_root_not_directory')
        except OSError:
            blockers.append('evidence_root_inspection_failed')

    archive_status = {'status': 'not_requested', 'identity_ok': None,
                      'crc_status': 'not_checked', 'seven_zip_available': None,
                      'actual_sha256': None,
                      'expected_sha256': None, 'problems': []}
    if archive is None:
        blockers.append('archive_missing')
    else:
        archive = Path(archive).expanduser().absolute()
        if not archive.is_file():
            blockers.append('archive_missing')
        if not isinstance(archive_identity, dict):
            blockers.append('archive_identity_unverified')
        else:
            identity_ok = archive_identity.get('identity_ok') is True
            crc_status = archive_identity.get('crc_status')
            archive_status = {
                'status': 'identity_verified' if identity_ok else 'identity_rejected',
                'identity_ok': identity_ok,
                'crc_status': crc_status,
                'seven_zip_available': archive_identity.get('seven_zip_available'),
                'actual_sha256': archive_identity.get('actual_sha256'),
                'expected_sha256': archive_identity.get('expected_sha256'),
                'problems': [str(problem) for problem in
                             (archive_identity.get('problems') or [])][:16],
            }
            if not identity_ok:
                blockers.append('archive_identity_failed')
            elif crc_status != 'verified':
                blockers.append('archive_crc_unverified')
            source_sha = archive_identity.get('actual_sha256')
            if expected_source_sha256 is not None and source_sha != expected_source_sha256:
                blockers.append('archive_sha256_mismatch')
            elif isinstance(source_sha, str) and re.fullmatch(r'[0-9a-f]{64}', source_sha):
                expected_source_sha256 = source_sha
            else:
                blockers.append('archive_sha256_unavailable')

    if running_processes is None:
        running_processes = []
    if running_processes:
        blockers.append('game_processes_running')

    unique_blockers = list(dict.fromkeys(blockers))
    stage_available = not stage_root.exists()
    plan = {
        'schema_version': 1,
        'schema': 'zombieee.install-plan.v1',
        'dry_run': True,
        'execution_enabled': not unique_blockers,
        'consent_required': True,
        'transaction_id': transaction_id,
        'module_name': module_name,
        'operation': 'update' if target.exists() else 'install',
        'game_root': str(game_root),
        'modules': paths['modules'],
        'target': paths['target'],
        'stage_root': paths['stage_root'],
        'stage_module': paths['stage_module'],
        'backup': paths['backup'],
        'journal': paths['journal'],
        'evidence_root': str(evidence_path) if evidence_path is not None else None,
        'archive': str(archive) if archive is not None else None,
        'archive_identity': archive_status,
        'expected_source_sha256': expected_source_sha256,
        'city_build_flags': [str(flag) for flag in city_flags],
        'build_argv': build_argv(archive, stage_module,
                                python_executable=python_executable,
                                repo_root=repo_root, city_flags=city_flags)
        if archive is not None else None,
        'build_timeout': int(build_timeout),
        'stage_available': stage_available,
        'path_issues': issues[:32],
        'running_processes': list(running_processes)[:8],
        'blockers': unique_blockers,
        'warnings': warnings,
        'steps': [
            'recheck_processes_paths_and_archive_identity_before_write',
            'build_into_fresh_same_volume_stage_with_existing_builder',
            'validate_built_module_receipt_and_digest',
            'rename_existing_target_to_backup_if_present',
            'rename_staged_module_to_target',
            'verify_installed_digest_matches_staged_digest',
            'commit_journal_and_retain_backup',
        ],
        'rollback': [
            'build_or_validation_failure_leaves_target_untouched',
            'activation_failure_restores_backup',
            'verification_failure_moves_target_back_to_stage_and_restores_backup',
            'if_restore_fails_retain_both_trees_and_journal_for_recovery',
            'never_delete_unrecognized_or_user_modified_files',
        ],
        'runtime_verified': False,
    }
    return plan


class _Journal:
    def __init__(self, path, *, transaction_id):
        self.path = Path(path) if path is not None else None
        self.entries = []
        self.data = {'schema': JOURNAL_SCHEMA, 'transaction_id': transaction_id,
                     'steps': self.entries, 'runtime_verified': False}
        self._write()

    def _write(self):
        if self.path is None:
            return
        self.path.parent.mkdir(parents=True, exist_ok=True)
        data = (json.dumps(self.data, indent=2, sort_keys=True) + '\n').encode('utf-8')
        temp = self.path.with_name(self.path.name + '.tmp')
        temp.unlink(missing_ok=True)
        try:
            with open(temp, 'xb') as stream:
                stream.write(data)
                stream.flush()
                os.fsync(stream.fileno())
            os.replace(temp, self.path)
        finally:
            temp.unlink(missing_ok=True)

    def step(self, name, **fields):
        entry = {'step': name}
        entry.update(fields)
        self.entries.append(entry)
        self.data['steps'] = self.entries
        self._write()
        return entry


def _default_build_runner(plan):
    def run(argv, cwd):
        return subprocess.run(argv, cwd=str(cwd), capture_output=True, text=True,
                              timeout=plan['build_timeout'], shell=False)
    return run


def _recheck(plan):
    """Re-validate the load-bearing paths immediately before any write."""
    problems = []
    target = Path(plan['target'])
    for path in (Path(plan['game_root']), Path(plan['game_root']) / 'Modules'):
        if not path.is_dir():
            problems.append('game_tree_missing')
    executable = Path(plan['game_root']) / 'mb_warband.exe'
    try:
        if not executable.is_file():
            problems.append('warband_executable_missing')
    except OSError:
        problems.append('warband_executable_unreadable')
    if Path(plan['stage_root']).exists():
        problems.append('stage_path_exists')
    if Path(plan['backup']).exists():
        problems.append('backup_path_exists')
    try:
        if target.exists() and not target.is_dir():
            problems.append('target_not_directory')
    except OSError:
        problems.append('target_inspection_failed')
    if _redirected_components([Path(plan['game_root']), target,
                               Path(plan['stage_root']), Path(plan['backup'])]):
        problems.append('transaction_path_redirected')
    archive = plan.get('archive')
    if not isinstance(archive, str) or not Path(archive).is_file():
        problems.append('archive_missing')
    else:
        expected_size = (plan.get('archive_identity') or {}).get('expected_size')
        try:
            size = Path(archive).stat().st_size
        except OSError:
            size = None
        if type(expected_size) is int and size is not None and size != expected_size:
            problems.append('archive_size_changed')
    return problems


def execute_install(plan, *, build_runner=None, inventory=module_inventory,
                    rename=None, rmdir=None, process_checker=None,
                    timestamp=None):
    """Execute a validated install plan with backup-first activation.

    Returns a receipt dict (never raises for expected build/activation
    failures). A ``recovery_required`` status means both trees were retained and
    a human must reconcile them; nothing was deleted.
    """
    if not isinstance(plan, dict) or plan.get('schema') != 'zombieee.install-plan.v1':
        raise InstallError('not an install plan')
    if plan.get('blockers'):
        raise InstallFailure('plan blocked: ' + ', '.join(plan['blockers']))
    if plan.get('execution_enabled') is not True:
        raise InstallFailure('plan execution not enabled')
    rename = os.rename if rename is None else rename
    rmdir = os.rmdir if rmdir is None else rmdir
    build_runner = _default_build_runner(plan) if build_runner is None else build_runner
    process_checker = running_game_processes if process_checker is None else process_checker
    timestamp = timestamp or _now_stamp()
    journal = _Journal(plan.get('journal'), transaction_id=plan['transaction_id'])
    target = Path(plan['target'])
    stage_root = Path(plan['stage_root'])
    stage_module = Path(plan['stage_module'])
    backup = Path(plan['backup'])

    receipt = {
        'schema': RECEIPT_SCHEMA, 'schema_version': 1,
        'transaction_id': plan['transaction_id'], 'timestamp': timestamp,
        'game_root': plan['game_root'], 'target': plan['target'],
        'backup': None, 'stage_root': plan['stage_root'],
        'operation': plan['operation'], 'archive': plan['archive'],
        'archive_sha256': (plan.get('archive_identity') or {}).get('actual_sha256'),
        'build_argv': plan.get('build_argv'),
        'journal': plan.get('journal'),
        'module_sha256': None, 'file_count': None, 'files': None,
        'installed_sha256': None, 'installed_file_count': None,
        'status': 'unknown', 'blockers': [], 'error': None,
        'stderr_tail': None, 'verification': None,
        'rollback': None, 'runtime_verified': False,
    }

    def finish(status, **fields):
        receipt.update(fields)
        receipt['status'] = status
        journal.step('finish', status=status,
                     blockers=list(receipt['blockers'])[:16])
        return receipt

    processes = process_checker()
    if processes:
        receipt['blockers'].append('game_processes_running')
        return finish('blocked')
    journal.step('preflight_recheck')
    problems = _recheck(plan)
    if problems:
        receipt['blockers'] = problems
        return finish('blocked')

    journal.step('build_started', argv=' '.join(str(part) for part in plan['build_argv'])[:1000])
    try:
        completed = build_runner(plan['build_argv'], Path(plan['game_root']))
    except subprocess.TimeoutExpired:
        receipt['error'] = 'build_timeout'
        return finish('build_failed')
    except (OSError, ValueError) as exc:
        receipt['error'] = 'build_runner_' + type(exc).__name__
        return finish('build_failed')
    returncode = getattr(completed, 'returncode', None)
    if returncode != 0:
        receipt['error'] = 'build_exit_' + str(returncode)
        receipt['stderr_tail'] = _bounded_text(getattr(completed, 'stderr', '') or '')
        journal.step('build_failed', returncode=returncode)
        return finish('build_failed')

    verification = verify_built_module(
        stage_module,
        expected_source_sha256=plan.get('expected_source_sha256'))
    receipt['verification'] = {key: verification.get(key) for key in
                               ('ok', 'checks', 'problems', 'trigger_count',
                                'map_scope', 'module_sha256', 'file_count')}
    if not verification['ok']:
        receipt['blockers'] = list(verification['problems'])[:16]
        journal.step('build_verification_failed')
        return finish('build_verification_failed',
                      module_sha256=verification.get('module_sha256'),
                      file_count=verification.get('file_count'))
    built_sha = verification['module_sha256']
    built_count = verification['file_count']
    try:
        built_files = module_file_hashes(stage_module)
    except InstallError as exc:
        receipt['blockers'] = ['ownership_inventory_failed:' + str(exc)][:16]
        journal.step('ownership_inventory_failed')
        return finish('build_verification_failed')
    journal.step('build_verified', module_sha256=built_sha,
                 file_count=built_count)

    had_target = target.exists()
    if had_target:
        journal.step('backup_started', backup=str(backup))
        try:
            rename(str(target), str(backup))
        except OSError as exc:
            receipt['error'] = 'backup_rename_failed:' + type(exc).__name__
            journal.step('backup_failed')
            return finish('backup_failed')
        receipt['backup'] = str(backup)
        journal.step('backup_moved', backup=str(backup))

    journal.step('activation_started')
    try:
        rename(str(stage_module), str(target))
    except OSError as exc:
        receipt['error'] = 'activation_rename_failed:' + type(exc).__name__
        restored, recovery_required = False, False
        if had_target and backup.exists() and not target.exists():
            try:
                rename(str(backup), str(target))
                restored = True
            except OSError:
                recovery_required = True
        receipt['rollback'] = {'restored': restored,
                               'recovery_required': recovery_required}
        journal.step('activation_failed', restored=restored,
                     recovery_required=recovery_required)
        if restored:
            return finish('activation_failed_rolled_back')
        return finish('recovery_required' if recovery_required
                      else 'activation_failed')
    journal.step('activated')

    installed = inventory(target)
    if installed['module_sha256'] != built_sha:
        receipt['error'] = 'installed_digest_mismatch'
        receipt['installed_sha256'] = installed['module_sha256']
        receipt['installed_file_count'] = installed['file_count']
        restored = False
        if had_target and backup.exists():
            try:
                rename(str(target), str(stage_module))
                rename(str(backup), str(target))
                restored = True
            except OSError:
                restored = False
        receipt['rollback'] = {'restored': restored,
                               'recovery_required': had_target and not restored}
        journal.step('verification_failed', restored=restored)
        if restored:
            return finish('verification_failed_rolled_back')
        return finish('recovery_required' if had_target
                      else 'verification_failed')

    try:
        rmdir(str(stage_root))
    except OSError:
        pass
    receipt.update({
        'module_sha256': built_sha, 'file_count': built_count,
        'files': built_files,
        'installed_sha256': installed['module_sha256'],
        'installed_file_count': installed['file_count'],
    })
    journal.step('committed', module_sha256=built_sha, file_count=built_count)
    return finish('installed')


def restore_backup(receipt, *, timestamp=None, rename=None):
    """Explicit user rollback: move the current target aside and restore backup.

    The current target is retained as ``<target>.rejected-<stamp>``; nothing is
    deleted. Returns a receipt-like dict and never invents a success.
    """
    rename = os.rename if rename is None else rename
    timestamp = timestamp or _now_stamp()
    receipt = receipt if isinstance(receipt, dict) else {}
    result = {'schema': 'zombieee.rollback-receipt.v1', 'timestamp': timestamp,
              'status': 'failed', 'error': None, 'restored': False,
              'rejected': None, 'runtime_verified': False}
    target_value, backup_value = receipt.get('target'), receipt.get('backup')
    if not isinstance(target_value, str) or not isinstance(backup_value, str):
        result['error'] = 'backup_not_recorded'
        return result
    target, backup = Path(target_value), Path(backup_value)
    if target.name != MODULE_NAME:
        result['error'] = 'target_name_mismatch'
        return result
    if backup.parent != target.parent or not backup.name.startswith(
            MODULE_NAME + '.backup-'):
        result['error'] = 'backup_path_not_sibling'
        return result
    if not backup.is_dir():
        result['error'] = 'backup_missing'
        return result
    if _redirected_components([target, backup]):
        result['error'] = 'redirected_path'
        return result
    current_moved = None
    if target.exists():
        if not target.is_dir():
            result['error'] = 'target_not_directory'
            return result
        current_moved = target.with_name(target.name + '.rejected-' + timestamp)
        if current_moved.exists():
            result['error'] = 'rejected_path_exists'
            return result
        try:
            rename(str(target), str(current_moved))
        except OSError as exc:
            result['error'] = 'reject_rename_failed:' + type(exc).__name__
            return result
        result['rejected'] = str(current_moved)
    try:
        rename(str(backup), str(target))
    except OSError as exc:
        result['error'] = 'restore_rename_failed:' + type(exc).__name__
        if current_moved is not None and current_moved.exists() and not target.exists():
            try:
                rename(str(current_moved), str(target))
                result['rejected'] = None
            except OSError:
                result['error'] = 'recovery_required'
        return result
    result.update({'status': 'restored', 'restored': True})
    return result
