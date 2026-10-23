"""Generate a read-only installation proposal, never apply it."""
import argparse
import json
import re
import stat
import subprocess
import sys
from pathlib import Path

from launcher.discovery import executable_status

ROOT = Path(__file__).resolve().parents[1]
ARCHIVE_AUDIT = ROOT / 'tools/archive_audit.py'


def path_issues(paths):
    """Inspect lexical paths and every ancestor without resolving away links.

    This is a read-only observation, not a race-proof authorization to write.
    Missing components are expected for a fresh stage/target. Other inspection
    failures stay blockers. Real installation must recheck through owned handles.
    """
    issues, seen = [], set()
    for path in paths:
        for component in (*reversed(path.parents), path):
            if component in seen:
                continue
            seen.add(component)
            try:
                info = component.lstat()
            except FileNotFoundError:
                continue
            except (OSError, ValueError):
                issues.append({'path': str(component), 'reason': 'path_inspection_failed'})
                continue
            if stat.S_ISLNK(info.st_mode) or getattr(info, 'st_file_attributes', 0) & 0x400:
                issues.append({'path': str(component), 'reason': 'reparse_or_symlink'})
    return issues


def _probe(path, method):
    """Return a boolean filesystem probe, or None when inspection failed.

    `Path.exists()`, `is_file()` and `is_dir()` re-raise non-ignorable OSErrors
    such as Windows access denials even after a successful lexical check. A
    planner must never let that abort the JSON proposal, so every later probe is
    normalized to True, False or None (unknown) and recorded as an issue.
    """
    try:
        return bool(getattr(path, method)())
    except FileNotFoundError:
        return False
    except (OSError, ValueError):
        return None


def _lexical_exists(path):
    """True/False/None via lstat so a redirected leaf remains visible."""
    try:
        path.lstat()
    except FileNotFoundError:
        return False
    except (OSError, ValueError):
        return None
    return True


def audit_archive(archive, audit_tool=None):
    """Consume A's read-only identity CLI. Never duplicate its hash policy.

    audit_tool is an injection point for fixture scripts. Production uses the
    repository-owned tool only, once A's branch is integrated. No extraction,
    7-Zip CRC or builder invocation occurs here.
    """
    tool = ARCHIVE_AUDIT if audit_tool is None else Path(audit_tool)
    result = {'status': 'unavailable', 'identity_ok': None, 'crc_status': 'not_checked'}
    try:
        available = tool.is_file()
    except (OSError, ValueError):
        result['status'] = 'audit_failed'
        return result
    if not available:
        return result
    try:
        completed = subprocess.run(
            [sys.executable, str(tool), '--archive', str(archive), '--json'],
            capture_output=True, text=True, encoding='utf-8', timeout=60, shell=False)
        report = json.loads(completed.stdout)
    except (OSError, ValueError, subprocess.TimeoutExpired):
        result['status'] = 'audit_failed'
        return result
    if not isinstance(report, dict) or type(report.get('identity_ok')) is not bool:
        result['status'] = 'invalid_report'
        return result
    if completed.returncode not in (0, 2) or (completed.returncode != 0 and report['identity_ok']):
        result['status'] = 'audit_failed'
        return result
    result['identity_ok'] = report['identity_ok']
    result['status'] = 'identity_verified' if report['identity_ok'] else 'identity_rejected'
    # This invocation never requested CRC, even if unexpected output says verified.
    return result


def plan_install(game_root, archive, transaction_id, *, audit=False):
    if not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9_-]{0,63}', transaction_id):
        raise ValueError('transaction_id must be 1..64 safe ASCII characters')
    raw_game = Path(game_root).expanduser()
    if not raw_game.is_absolute():
        raw_game = Path.cwd() / raw_game
    raw_modules = raw_game / 'Modules'
    issues = path_issues((raw_game, raw_game / 'mb_warband.exe', raw_modules,
                          raw_modules / 'ZOMBIEEE_Remaster',
                          raw_modules / ('.zombieee-stage-' + transaction_id),
                          raw_modules / ('.zombieee-backup-' + transaction_id),
                          raw_modules / ('.zombieee-journal-' + transaction_id + '.json')))

    def record_inspection_failure(path):
        issue = {'path': str(path), 'reason': 'path_inspection_failed'}
        if issue not in issues:
            issues.append(issue)

    def probe(path, method):
        observed = _probe(path, method)
        if observed is None:
            record_inspection_failure(path)
        return observed

    try:
        game = raw_game.resolve()
    except (OSError, RuntimeError, ValueError):
        game = raw_game
        issues.append({'path': str(raw_game), 'reason': 'path_resolution_failed'})
    raw_archive = Path(archive).expanduser()
    try:
        archive = raw_archive.resolve()
    except (OSError, RuntimeError, ValueError):
        archive = raw_archive
        issues.append({'path': str(raw_archive), 'reason': 'path_resolution_failed'})
    modules = game / 'Modules'
    target = modules / 'ZOMBIEEE_Remaster'
    stage = modules / ('.zombieee-stage-' + transaction_id)
    backup = modules / ('.zombieee-backup-' + transaction_id)
    journal = modules / ('.zombieee-journal-' + transaction_id + '.json')
    blockers = ['execution_not_implemented', 'consent_not_recorded', 'archive_digest_unverified',
                'archive_crc_unverified']
    if '..' in raw_game.parts:
        blockers.append('noncanonical_input_path')
    archive_audit = audit_archive(archive) if audit else {
        'status': 'not_requested', 'identity_ok': None, 'crc_status': 'not_checked'}
    if archive_audit['identity_ok'] is True:
        blockers.remove('archive_digest_unverified')
    elif audit:
        blockers.append('archive_audit_' + archive_audit['status'])
    executable = game / 'mb_warband.exe'
    try:
        executable_state = executable_status(executable)
    except (OSError, ValueError):
        # open() can raise ValueError for a malformed configured path (e.g. NUL)
        # even though the surrounding path checks already normalized it.
        executable_state = 'unreadable_executable'
    if executable_state == 'unreadable_executable':
        record_inspection_failure(executable)
    elif executable_state != 'found':
        blockers.append('warband_invalid')
    if probe(archive, 'is_file') is False:
        blockers.append('archive_missing')
    for path in (stage, backup, journal):
        exists = _lexical_exists(path)
        if exists is None:
            record_inspection_failure(path)
        elif exists:
            blockers.append('transaction_path_exists')
    for path in (modules, target, stage, backup, journal):
        exists = probe(path, 'exists')
        is_dir = probe(path, 'is_dir')
        if exists is True and is_dir is False:
            blockers.append('destination_not_directory')
    target_exists = probe(target, 'exists')
    operation = 'unknown' if target_exists is None else (
        'update' if target_exists else 'install')
    if any(issue['reason'] == 'reparse_or_symlink' for issue in issues):
        blockers.append('redirected_destination')
    if any(issue['reason'] != 'reparse_or_symlink' for issue in issues):
        blockers.append('path_inspection_failed')
    unique_issues = []
    for issue in issues:
        if issue not in unique_issues:
            unique_issues.append(issue)
    return {
        'schema_version': 1, 'dry_run': True, 'execution_enabled': False,
        'consent_required': True, 'operation': operation,
        'transaction_id': transaction_id, 'game_root': str(game),
        'input_game_root': str(raw_game), 'path_issues': unique_issues,
        'recheck_required_before_write': True,
        'archive': str(archive), 'target': str(target), 'stage': str(stage),
        'archive_audit': archive_audit,
        'archive_audit_argv': [sys.executable, str(ARCHIVE_AUDIT), '--archive', str(archive), '--json'],
        'backup': str(backup), 'journal': str(journal),
        'build_argv': [sys.executable, str(ROOT / 'tools/build.py'), '--archive', str(archive),
                       '--out', str(stage / 'ZOMBIEEE_Remaster')],
        'blockers': list(dict.fromkeys(blockers)),
        'steps': ['record_explicit_consent_and_revalidate_paths', 'lock_and_write_durable_journal',
                  'build_into_stage_with_existing_builder', 'verify_staged_inventory_and_hashes',
                  'rename_existing_target_to_backup_if_present', 'rename_staged_module_to_target',
                  'verify_target_and_commit_journal', 'retain_backup_for_explicit_cleanup'],
        'rollback': ['if_old_target_moved_and_activation_failed_restore_backup',
                     'never_delete_unrecognized_or_user_modified_files',
                     'retain_journal_and_both_trees_if_restore_fails'],
        'runtime_verified': False,
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--game-root', required=True)
    parser.add_argument('--archive', required=True)
    parser.add_argument('--transaction-id', required=True)
    parser.add_argument('--audit-archive-hash', action='store_true',
                        help="Run Agent A's read-only archive audit if integrated; no extraction")
    args = parser.parse_args()
    print(json.dumps(plan_install(args.game_root, args.archive, args.transaction_id,
                                audit=args.audit_archive_hash), indent=2))


if __name__ == '__main__':
    main()
