"""Generate a read-only installation proposal, never apply it."""
import argparse
import json
import re
import sys
from pathlib import Path

from launcher.discovery import executable_status

ROOT = Path(__file__).resolve().parents[1]


def plan_install(game_root, archive, transaction_id):
    if not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9_-]{0,63}', transaction_id):
        raise ValueError('transaction_id must be 1..64 safe ASCII characters')
    game = Path(game_root).expanduser().resolve()
    archive = Path(archive).expanduser().resolve()
    modules = game / 'Modules'
    target = modules / 'ZOMBIEEE_Remaster'
    stage = modules / ('.zombieee-stage-' + transaction_id)
    backup = modules / ('.zombieee-backup-' + transaction_id)
    journal = modules / ('.zombieee-journal-' + transaction_id + '.json')
    blockers = ['execution_not_implemented', 'consent_not_recorded', 'archive_digest_unverified']
    if executable_status(game / 'mb_warband.exe') != 'found':
        blockers.append('warband_invalid')
    if not archive.is_file():
        blockers.append('archive_missing')
    if any(p.exists() or p.is_symlink() for p in (stage, backup, journal)):
        blockers.append('transaction_path_exists')
    for path in (modules, target, stage, backup):
        if path.resolve() != path:
            blockers.append('redirected_destination')
        if path.exists() and not path.is_dir():
            blockers.append('destination_not_directory')
    return {
        'schema_version': 1, 'dry_run': True, 'execution_enabled': False,
        'consent_required': True, 'operation': 'update' if target.exists() else 'install',
        'transaction_id': transaction_id, 'game_root': str(game),
        'archive': str(archive), 'target': str(target), 'stage': str(stage),
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
    args = parser.parse_args()
    print(json.dumps(plan_install(args.game_root, args.archive, args.transaction_id), indent=2))


if __name__ == '__main__':
    main()
