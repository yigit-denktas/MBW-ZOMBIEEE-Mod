"""Verify, repair and quarantine-uninstall an installed City module.

The install receipt written by :mod:`launcher.install` records the per-file
SHA-256 ownership inventory (``files``) of the bytes the installer wrote. This
module compares the live module tree with that inventory and never guesses
ownership:

* ``verify`` is read-only: it reports missing, modified and unrecognised files.
* ``repair`` copies missing (and, only with explicit opt-in, modified) owned
  files from a freshly built module; modified files are otherwise preserved and
  reported, and unrecognised user files are never touched.
* ``uninstall`` moves the whole module to a same-volume private quarantine by
  default (nothing deleted); ``purge_owned`` may then delete only owned,
  byte-identical files from the quarantine, leaving modified/unrecognised files
  and directories intact. The game, WSE2 and the retained install backup are
  never touched.

No game process is started. All functions are offline, bounded and fail closed
on a missing/foreign receipt, redirected paths, running game processes or an
unverified repair source. Receipts keep ``runtime_verified=false``.
"""
from __future__ import annotations

import json
import os
import re
import shutil
from pathlib import Path

from .install import (MODULE_NAME, InstallError, module_file_hashes,
                      read_module_manifest, running_game_processes,
                      verify_built_module)

MAX_RECEIPT_BYTES = 1024 * 1024
SCHEMA_VERIFICATION = 'zombieee.module-verification.v1'
SCHEMA_REPAIR_PLAN = 'zombieee.repair-plan.v1'
SCHEMA_REPAIR_RECEIPT = 'zombieee.repair-receipt.v1'
SCHEMA_UNINSTALL_PLAN = 'zombieee.uninstall-plan.v1'
SCHEMA_UNINSTALL_RECEIPT = 'zombieee.uninstall-receipt.v1'
TRANSACTION_RE = re.compile(r'[A-Za-z0-9][A-Za-z0-9_-]{0,63}\Z')


class MaintenanceError(RuntimeError):
    """Repair/uninstall was used outside its validated contract."""


def _bounded_json(path, limit=MAX_RECEIPT_BYTES):
    path = Path(path)
    with open(path, 'rb') as stream:
        data = stream.read(limit + 1)
    if len(data) > limit:
        raise MaintenanceError('oversized_receipt: ' + path.name)
    try:
        value = json.loads(data.decode('utf-8'))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise MaintenanceError('invalid_receipt_json: ' + path.name) from exc
    if not isinstance(value, dict):
        raise MaintenanceError('receipt_not_object: ' + path.name)
    return value


def load_install_receipt(path):
    """Load a successful install receipt with a usable ownership inventory."""
    receipt = _bounded_json(path)
    if receipt.get('schema') != 'zombieee.install-receipt.v1':
        raise MaintenanceError('not_an_install_receipt')
    if receipt.get('status') != 'installed':
        raise MaintenanceError('install_receipt_not_successful')
    files = receipt.get('files')
    if not isinstance(files, list) or not files:
        raise MaintenanceError('install_receipt_missing_ownership_inventory')
    expected = {}
    for entry in files:
        if not isinstance(entry, dict):
            raise MaintenanceError('invalid_ownership_entry')
        relative = entry.get('path')
        digest = entry.get('sha256')
        parts = Path(str(relative)).parts if isinstance(relative, str) else ()
        if (not isinstance(relative, str) or not relative or relative.startswith('/')
                or '\\' in relative or '..' in parts
                or not isinstance(digest, str)
                or not re.fullmatch(r'[0-9a-f]{64}', digest)):
            raise MaintenanceError('unsafe_ownership_entry')
        expected[relative] = digest
    receipt['_expected'] = expected
    return receipt


def verify_module(module_dir, install_receipt):
    """Read-only comparison of the live module against the install inventory."""
    module_dir = Path(module_dir)
    expected = install_receipt.get('_expected')
    if not isinstance(expected, dict):
        raise MaintenanceError('install receipt was not loaded with ownership')
    if not module_dir.is_dir():
        return {'schema': SCHEMA_VERIFICATION, 'schema_version': 1,
                'module_dir': str(module_dir), 'read_only': True,
                'receipt_schema': install_receipt.get('schema'),
                'verified': False, 'problems': ['module_missing'],
                'missing': [], 'modified': [], 'unrecognized': [],
                'owned_unchanged': 0, 'file_count': 0,
                'runtime_verified': False, 'write_required': False}
    actual = {entry['path']: entry['sha256']
              for entry in module_file_hashes(module_dir)}
    missing = sorted(set(expected) - set(actual))
    extra = sorted(set(actual) - set(expected))
    modified = sorted(path for path in set(expected) & set(actual)
                      if expected[path] != actual[path])
    unchanged = len(expected) - len(missing) - len(modified)
    problems = []
    if missing:
        problems.append('missing_owned_files')
    if modified:
        problems.append('modified_owned_files')
    if extra:
        problems.append('unrecognized_files')
    verification = {
        'schema': SCHEMA_VERIFICATION, 'schema_version': 1,
        'module_dir': str(module_dir), 'read_only': True,
        'receipt_schema': install_receipt.get('schema'),
        'verified': not problems,
        'problems': problems,
        'file_count': len(actual),
        'owned_files': len(expected),
        'owned_unchanged': unchanged,
        'missing': missing[:500],
        'modified': modified[:500],
        'unrecognized': extra[:500],
        'missing_count': len(missing),
        'modified_count': len(modified),
        'unrecognized_count': len(extra),
        'write_required': bool(missing),
        'runtime_verified': False,
    }
    return verification


def _game_root_from_receipt(install_receipt):
    target = install_receipt.get('target')
    if not isinstance(target, str) or Path(target).name != MODULE_NAME:
        raise MaintenanceError('install_receipt_has_foreign_target')
    target = Path(target)
    modules = target.parent
    if modules.name.casefold() != 'modules':
        raise MaintenanceError('install_target_not_under_modules')
    return modules.parent


def _redirected(paths):
    from .recorder import is_redirected
    issues = []
    seen = set()
    for value in paths:
        current = Path(value).expanduser().absolute()
        for component in (*reversed(current.parents), current):
            key = os.path.normcase(str(component))
            if key in seen:
                continue
            seen.add(key)
            if is_redirected(component):
                issues.append(str(component))
    return issues


def _source_inventory(source_module, expected):
    """Hash only the owned paths a repair may copy from the source module."""
    source_module = Path(source_module)
    if not source_module.is_dir():
        raise MaintenanceError('repair_source_missing')
    try:
        verify_built_module(source_module)
    except InstallError as exc:
        raise MaintenanceError('repair_source_invalid: ' + str(exc)) from exc
    available = {entry['path']: entry['sha256']
                 for entry in module_file_hashes(source_module)}
    return available


def plan_repair(*, install_receipt, source_module, transaction_id, evidence_dir,
                replace_modified=False, running_processes=None):
    """Plan restoring missing (optionally modified) owned files; no writes."""
    if not TRANSACTION_RE.fullmatch(str(transaction_id)):
        raise MaintenanceError('transaction_id must be 1..64 safe ASCII characters')
    game_root = _game_root_from_receipt(install_receipt)
    target = Path(install_receipt['target'])
    if type(replace_modified) is not bool:
        raise MaintenanceError('replace_modified must be a boolean')
    evidence = Path(evidence_dir).expanduser().absolute()
    blockers, warnings = [], []
    try:
        verification = verify_module(target, install_receipt)
    except (OSError, MaintenanceError) as exc:
        verification = {'verified': False, 'problems': [str(exc)],
                        'missing': [], 'modified': [], 'unrecognized': [],
                        'missing_count': 0, 'modified_count': 0}
        blockers.append('verification_failed')
    updates = list(verification.get('missing') or [])
    conflicts = list(verification.get('modified') or [])
    if replace_modified:
        updates.extend(conflicts)
        conflicts = []
    source = None
    if updates:
        try:
            source = _source_inventory(source_module, install_receipt['_expected'])
        except MaintenanceError as exc:
            blockers.append(str(exc))
        else:
            absent = [path for path in updates if path not in source]
            mismatched = [path for path in updates
                          if path in source
                          and source[path] != install_receipt['_expected'][path]]
            if absent:
                blockers.append('repair_source_missing_owned_files')
            if mismatched:
                blockers.append('repair_source_owned_file_mismatch')
    if not target.is_dir():
        blockers.append('module_missing')
    if running_processes:
        blockers.append('game_processes_running')
    if _redirected([game_root, target, source_module, evidence]):
        blockers.append('redirected_path')
    if not evidence.is_dir() and evidence.exists():
        blockers.append('evidence_root_not_directory')
    if verification.get('unrecognized_count'):
        warnings.append('unrecognized_files_preserved')
    if conflicts and not replace_modified:
        warnings.append('modified_owned_files_preserved')
    return {
        'schema': SCHEMA_REPAIR_PLAN, 'schema_version': 1,
        'operation': 'repair', 'dry_run': True, 'consent_required': True,
        'transaction_id': str(transaction_id),
        'game_root': str(game_root),
        'target': str(target),
        'source_module': str(Path(source_module).expanduser().absolute()),
        'evidence_root': str(evidence),
        'journal': str(evidence / ('repair-journal-' + str(transaction_id) + '.json')),
        'verification': verification,
        'updates': updates[:500],
        'conflicts': conflicts[:500],
        'unrecognized_preserved': verification.get('unrecognized') or [],
        'replace_modified': replace_modified,
        '_expected': dict(install_receipt['_expected']),
        'blockers': list(dict.fromkeys(blockers)),
        'warnings': warnings,
        'steps': ['recheck_paths_processes_and_receipt',
                  'copy_missing_owned_files_from_verified_source',
                  'optionally_replace_modified_owned_files_if_requested',
                  'verify_owned_inventory_after_repair',
                  'preserve_modified_and_unrecognized_user_files'],
        'runtime_verified': False,
    }


def execute_repair(plan, *, copy_file=None, process_checker=None,
                   timestamp=None):
    """Execute a validated repair plan; returns a receipt, never a claim."""
    if not isinstance(plan, dict) or plan.get('schema') != SCHEMA_REPAIR_PLAN:
        raise MaintenanceError('not a repair plan')
    if plan.get('blockers'):
        raise MaintenanceError('repair plan blocked: ' + ', '.join(plan['blockers']))
    copy_file = shutil.copy2 if copy_file is None else copy_file
    process_checker = (running_game_processes if process_checker is None
                       else process_checker)
    timestamp = timestamp or __import__('time').strftime('%Y%m%d-%H%M%S')
    from .install import _Journal
    journal = _Journal(plan.get('journal'), transaction_id=plan['transaction_id'])
    target = Path(plan['target'])
    source = Path(plan['source_module'])
    receipt = {
        'schema': SCHEMA_REPAIR_RECEIPT, 'schema_version': 1,
        'transaction_id': plan['transaction_id'], 'timestamp': timestamp,
        'game_root': plan['game_root'], 'target': str(target),
        'source_module': str(source), 'status': 'unknown',
        'repaired': [], 'preserved_conflicts': list(plan['conflicts']),
        'preserved_unrecognized': list(plan['unrecognized_preserved']),
        'verification_before': plan['verification'],
        'verification_after': None, 'error': None, 'runtime_verified': False,
    }
    if process_checker():
        receipt['error'] = 'game_processes_running'
        receipt['status'] = 'blocked'
        return receipt
    journal.step('preflight')
    for relative in plan['updates']:
        destination = target / relative
        if not destination.parent.is_dir():
            destination.parent.mkdir(parents=True, exist_ok=True)
        try:
            copy_file(str(source / relative), str(destination))
        except (OSError, shutil.Error) as exc:
            receipt['error'] = 'copy_failed:' + relative + ':' + type(exc).__name__
            journal.step('copy_failed', path=relative)
            receipt['status'] = 'failed'
            return receipt
        receipt['repaired'].append(relative)
        journal.step('repaired_file', path=relative)
    expected = plan.get('_expected') or {}
    if not isinstance(expected, dict) or not expected:
        receipt['error'] = 'missing_expected_ownership_map'
        receipt['status'] = 'failed'
        return receipt
    verification_after = verify_module(
        target, {'schema': 'zombieee.install-receipt.v1',
                 '_expected': expected})
    receipt['verification_after'] = verification_after
    if not verification_after['missing']:
        receipt['status'] = 'repaired' if receipt['repaired'] else 'noop'
    else:
        receipt['status'] = 'partial'
    journal.step('finish', status=receipt['status'])
    return receipt


def plan_uninstall(*, install_receipt, transaction_id, evidence_dir,
                   purge_owned=False, running_processes=None):
    """Plan a quarantine-first uninstall; no deletion by default."""
    if not TRANSACTION_RE.fullmatch(str(transaction_id)):
        raise MaintenanceError('transaction_id must be 1..64 safe ASCII characters')
    if type(purge_owned) is not bool:
        raise MaintenanceError('purge_owned must be a boolean')
    game_root = _game_root_from_receipt(install_receipt)
    target = Path(install_receipt['target'])
    modules = target.parent
    quarantine = modules / (MODULE_NAME + '.uninstalled-' + str(transaction_id))
    evidence = Path(evidence_dir).expanduser().absolute()
    blockers, warnings = [], []
    try:
        verification = verify_module(target, install_receipt)
    except (OSError, MaintenanceError) as exc:
        verification = {'verified': False, 'problems': [str(exc)],
                        'missing': [], 'modified': [], 'unrecognized': [],
                        'missing_count': 0, 'modified_count': 0}
        blockers.append('verification_failed')
    if not target.is_dir():
        blockers.append('module_missing')
    if quarantine.exists():
        blockers.append('quarantine_path_exists')
    if running_processes:
        blockers.append('game_processes_running')
    if _redirected([game_root, target, quarantine, evidence]):
        blockers.append('redirected_path')
    if not evidence.is_dir() and evidence.exists():
        blockers.append('evidence_root_not_directory')
    if verification.get('unrecognized_count') or verification.get('modified_count'):
        warnings.append('user_files_preserved_in_quarantine')
    return {
        'schema': SCHEMA_UNINSTALL_PLAN, 'schema_version': 1,
        'operation': 'uninstall', 'dry_run': True, 'consent_required': True,
        'transaction_id': str(transaction_id),
        'game_root': str(game_root),
        'target': str(target),
        'quarantine': str(quarantine),
        'evidence_root': str(evidence),
        'journal': str(evidence / ('uninstall-journal-' + str(transaction_id) + '.json')),
        'verification': verification,
        '_expected': dict(install_receipt['_expected']),
        'purge_owned': purge_owned,
        'owned_unchanged_count': verification.get('owned_unchanged', 0),
        'preserved_modified': verification.get('modified') or [],
        'preserved_unrecognized': verification.get('unrecognized') or [],
        'blockers': list(dict.fromkeys(blockers)),
        'warnings': warnings,
        'steps': ['recheck_paths_processes_and_receipt',
                  'move_module_to_private_same_volume_quarantine',
                  'optionally_delete_only_owned_unchanged_files_from_quarantine',
                  'preserve_modified_unrecognized_files_and_all_game_data',
                  'leave_retained_install_backup_untouched'],
        'runtime_verified': False,
    }


def execute_uninstall(plan, *, rename=None, unlink=None, process_checker=None,
                      timestamp=None):
    """Execute a validated uninstall plan with quarantine-first semantics."""
    if not isinstance(plan, dict) or plan.get('schema') != SCHEMA_UNINSTALL_PLAN:
        raise MaintenanceError('not an uninstall plan')
    if plan.get('blockers'):
        raise MaintenanceError('uninstall plan blocked: ' + ', '.join(plan['blockers']))
    rename = os.rename if rename is None else rename
    unlink = os.unlink if unlink is None else unlink
    process_checker = (running_game_processes if process_checker is None
                       else process_checker)
    timestamp = timestamp or __import__('time').strftime('%Y%m%d-%H%M%S')
    from .install import _Journal
    journal = _Journal(plan.get('journal'), transaction_id=plan['transaction_id'])
    target = Path(plan['target'])
    quarantine = Path(plan['quarantine'])
    receipt = {
        'schema': SCHEMA_UNINSTALL_RECEIPT, 'schema_version': 1,
        'transaction_id': plan['transaction_id'], 'timestamp': timestamp,
        'game_root': plan['game_root'], 'target': str(target),
        'quarantine': str(quarantine), 'status': 'unknown',
        'moved_to_quarantine': False, 'purged_owned_files': [],
        'preserved_modified': list(plan['preserved_modified']),
        'preserved_unrecognized': list(plan['preserved_unrecognized']),
        'game_data_deleted': False, 'error': None, 'runtime_verified': False,
    }
    if process_checker():
        receipt['error'] = 'game_processes_running'
        receipt['status'] = 'blocked'
        return receipt
    journal.step('preflight')
    if target.exists() and not quarantine.exists():
        try:
            rename(str(target), str(quarantine))
        except OSError as exc:
            receipt['error'] = 'quarantine_move_failed:' + type(exc).__name__
            receipt['status'] = 'failed'
            return receipt
        receipt['moved_to_quarantine'] = True
        journal.step('moved_to_quarantine', quarantine=str(quarantine))
    if plan.get('purge_owned') and quarantine.is_dir():
        expected = plan.get('_expected') or {}
        preserved = set(plan['preserved_modified']) | set(
            plan['preserved_unrecognized'])
        for relative in sorted(expected):
            if relative in preserved:
                continue
            path = quarantine / relative
            try:
                unlink(str(path))
            except FileNotFoundError:
                continue
            except OSError as exc:
                receipt['error'] = 'purge_failed:' + relative + ':' + type(exc).__name__
                receipt['status'] = 'failed'
                return receipt
            receipt['purged_owned_files'].append(relative)
        journal.step('purged_owned', count=len(receipt['purged_owned_files']))
    receipt['status'] = ('quarantined' if not plan.get('purge_owned')
                         else 'uninstalled')
    journal.step('finish', status=receipt['status'])
    return receipt


def find_latest_install_receipt(evidence_root):
    """Newest ``install-receipt-*.json`` under the private evidence root."""
    root = Path(evidence_root).expanduser().absolute()
    candidates = []
    try:
        entries = list(root.iterdir())
    except (FileNotFoundError, NotADirectoryError, OSError):
        return None
    for entry in entries:
        name = entry.name
        if not name.startswith('install-receipt-') or not name.endswith('.json'):
            continue
        try:
            candidates.append((entry.stat().st_mtime, entry))
        except OSError:
            continue
    if not candidates:
        return None
    candidates.sort(key=lambda item: item[0], reverse=True)
    return candidates[0][1]
