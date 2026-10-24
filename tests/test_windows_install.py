"""Reversible install tests: backup-first activation, rollback, journal, no deletes."""
import json
import os
import struct
import sys
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))
from launcher.install import (  # noqa: E402
    CITY_BUILD_FLAGS, InstallFailure, MODULE_NAME, build_argv, execute_install,
    install_paths, module_inventory, plan_install, restore_backup,
    verify_built_module)

SOURCE_SHA = 'ab' * 32


def pe(path):
    path.parent.mkdir(parents=True, exist_ok=True)
    data = bytearray(256)
    data[:2] = b'MZ'
    struct.pack_into('<I', data, 60, 128)
    data[128:132] = b'PE\0\0'
    path.write_bytes(bytes(data))
    return path


def write_module(path, *, source_sha=SOURCE_SHA, triggers=31,
                 map_scope='city-only', runtime_verified=False,
                 crc_verified=True, marker=None):
    path.mkdir(parents=True, exist_ok=True)
    for name in ('module.ini', 'mission_templates.txt', 'scripts.txt',
                 'troops.txt', 'variables.txt'):
        (path / name).write_text('fixture\n', encoding='utf-8')
    (path / 'lua').mkdir(exist_ok=True)
    (path / 'lua' / 'main.lua').write_text(
        'print("ZDB1|heartbeat|count=1")\n', encoding='utf-8')
    (path / 'lua' / 'msfiles').mkdir(exist_ok=True)
    (path / 'lua' / 'msfiles' / 'ID_troops.py').write_text('', encoding='utf-8')
    manifest = {
        'source_archive_sha256': source_sha,
        'runtime_verified': runtime_verified,
        'archive_crc_verified': crc_verified,
        'experimental_map_scope': map_scope,
        'final_trigger_count': triggers,
        'original_mission_trigger_count': 25,
    }
    (path / 'ZOMBIEEE_REMASTER.json').write_text(json.dumps(manifest),
                                                 encoding='utf-8')
    if marker is not None:
        (path / marker).write_text('old', encoding='utf-8')
    return path


class InstallFixture:
    def __init__(self, root):
        self.root = Path(root)
        self.game = self.root / 'Warband'
        pe(self.game / 'mb_warband.exe')
        (self.game / 'Modules').mkdir(parents=True)
        self.archive = self.root / 'ZOMBIEEEBeta04.rar'
        self.archive.write_bytes(b'Rar!\x1a\x07\x00fixture')
        self.evidence = self.root / 'evidence'
        self.identity = {
            'identity_ok': True, 'crc_status': 'verified',
            'seven_zip_available': True, 'actual_sha256': SOURCE_SHA,
            'expected_sha256': SOURCE_SHA,
            'expected_size': self.archive.stat().st_size,
            'problems': [],
        }

    def plan(self, transaction_id='tx-1'):
        return plan_install(
            game_root=self.game, transaction_id=transaction_id,
            archive=self.archive, archive_identity=self.identity,
            evidence_dir=self.evidence, expected_source_sha256=SOURCE_SHA)

    def build_runner(self, *, make_module=True, returncode=0, stderr=''):
        calls = []

        def runner(argv, cwd):
            calls.append((list(argv), Path(cwd)))
            stage = Path(argv[argv.index('--out') + 1])
            if make_module:
                write_module(stage)
            return SimpleNamespace(returncode=returncode, stdout='built',
                                   stderr=stderr)
        return runner, calls


class PlanTests(unittest.TestCase):
    def test_plan_uses_agent_a_builder_and_city_profile(self):
        with tempfile.TemporaryDirectory() as tmp:
            fixture = InstallFixture(tmp)
            plan = fixture.plan()
            self.assertEqual(plan['blockers'], [])
            self.assertTrue(plan['execution_enabled'])
            self.assertEqual(plan['operation'], 'install')
            argv = plan['build_argv']
            self.assertIn('tools' + os.sep + 'build.py', ' '.join(argv))
            self.assertIn('--archive', argv)
            self.assertIn('--out', argv)
            for flag in CITY_BUILD_FLAGS:
                self.assertIn(flag, argv)
            self.assertIn('--city-guardposts', argv)
            self.assertNotIn('--all-map-defenses', argv)
            self.assertFalse(plan['runtime_verified'])
            self.assertTrue(plan['journal'].endswith('install-journal-tx-1.json'))
            self.assertEqual(plan['stage_module'], str(
                fixture.game / 'Modules' / '.zombieee-stage-tx-1' / MODULE_NAME))

    def test_existing_transaction_paths_block_instead_of_overwriting(self):
        with tempfile.TemporaryDirectory() as tmp:
            fixture = InstallFixture(tmp)
            stage = fixture.game / 'Modules' / '.zombieee-stage-tx-2'
            stage.mkdir()
            plan = fixture.plan(transaction_id='tx-2')
            self.assertIn('stage_path_exists', plan['blockers'])
            self.assertFalse(plan['execution_enabled'])

    def test_archive_identity_failure_blocks_the_plan(self):
        with tempfile.TemporaryDirectory() as tmp:
            fixture = InstallFixture(tmp)
            fixture.identity = {'identity_ok': False, 'crc_status': 'blocked_identity',
                                'seven_zip_available': False,
                                'actual_sha256': 'cd' * 32,
                                'problems': ['sha256_mismatch']}
            with self.assertRaises(InstallFailure):
                execute_install(fixture.plan(), process_checker=lambda: [])


class ExecuteInstallTests(unittest.TestCase):
    def _execute(self, fixture, **overrides):
        runner, calls = fixture.build_runner(**{
            key: value for key, value in overrides.items()
            if key in ('make_module', 'returncode', 'stderr')})
        options = {'build_runner': runner, 'process_checker': lambda: []}
        options.update({key: value for key, value in overrides.items()
                        if key not in ('make_module', 'returncode', 'stderr')})
        receipt = execute_install(fixture.plan(), **options)
        return receipt, calls

    def test_fresh_install_is_digest_verified_and_journaled(self):
        with tempfile.TemporaryDirectory() as tmp:
            fixture = InstallFixture(tmp)
            receipt, calls = self._execute(fixture)
            self.assertEqual(receipt['status'], 'installed')
            self.assertEqual(len(calls), 1)
            target = fixture.game / 'Modules' / MODULE_NAME
            self.assertTrue(target.is_dir())
            self.assertIsNone(receipt['backup'])
            self.assertEqual(receipt['installed_sha256'], receipt['module_sha256'])
            self.assertGreater(receipt['file_count'], 0)
            journal = json.loads(Path(receipt['journal']).read_text(encoding='utf-8'))
            steps = [entry['step'] for entry in journal['steps']]
            self.assertIn('build_verified', steps)
            self.assertIn('activated', steps)
            self.assertIn('committed', steps)
            self.assertFalse(journal['runtime_verified'])
            self.assertFalse((fixture.game / 'Modules'
                              / '.zombieee-stage-tx-1').exists())

    def test_update_never_overwrites_without_a_backup(self):
        with tempfile.TemporaryDirectory() as tmp:
            fixture = InstallFixture(tmp)
            target = fixture.game / 'Modules' / MODULE_NAME
            write_module(target, triggers=25, map_scope='original-baseline')
            (target / 'user-note.txt').write_text('preserve me', encoding='utf-8')
            receipt, _calls = self._execute(fixture)
            self.assertEqual(receipt['status'], 'installed')
            backup = Path(receipt['backup'])
            self.assertTrue(backup.is_dir())
            self.assertEqual((backup / 'user-note.txt').read_text(encoding='utf-8'),
                             'preserve me')
            manifest = json.loads((target / 'ZOMBIEEE_REMASTER.json').read_text())
            self.assertEqual(manifest['final_trigger_count'], 31)

    def test_build_failure_leaves_existing_target_untouched(self):
        with tempfile.TemporaryDirectory() as tmp:
            fixture = InstallFixture(tmp)
            target = fixture.game / 'Modules' / MODULE_NAME
            write_module(target)
            (target / 'keep.txt').write_text('keep', encoding='utf-8')
            receipt, _calls = self._execute(fixture, returncode=2,
                                            stderr='builder failed')
            self.assertEqual(receipt['status'], 'build_failed')
            self.assertIn('builder failed', receipt['stderr_tail'])
            self.assertTrue((target / 'keep.txt').is_file())
            self.assertFalse((fixture.game / 'Modules'
                              / (MODULE_NAME + '.backup-tx-1')).exists())

    def test_build_verification_failure_does_not_activate(self):
        with tempfile.TemporaryDirectory() as tmp:
            fixture = InstallFixture(tmp)
            runner, _calls = fixture.build_runner(returncode=0, make_module=False)
            receipt = execute_install(fixture.plan(), build_runner=runner,
                                      process_checker=lambda: [])
            self.assertEqual(receipt['status'], 'build_verification_failed')
            self.assertFalse((fixture.game / 'Modules' / MODULE_NAME).exists())

    def test_activation_failure_restores_the_backup(self):
        with tempfile.TemporaryDirectory() as tmp:
            fixture = InstallFixture(tmp)
            target = fixture.game / 'Modules' / MODULE_NAME
            write_module(target)
            plan = fixture.plan()

            def locked_rename(source, destination):
                if (Path(source) == Path(plan['stage_module'])
                        and Path(destination) == target):
                    raise OSError('simulated file lock')
                os.rename(source, destination)

            runner, _calls = fixture.build_runner()
            receipt = execute_install(plan, build_runner=runner,
                                      process_checker=lambda: [],
                                      rename=locked_rename)
            self.assertEqual(receipt['status'], 'activation_failed_rolled_back')
            self.assertTrue(receipt['rollback']['restored'])
            self.assertTrue((target / 'ZOMBIEEE_REMASTER.json').is_file())
            self.assertFalse((fixture.game / 'Modules'
                              / (MODULE_NAME + '.backup-tx-1')).exists())

    def test_unrecoverable_activation_retains_both_trees_for_recovery(self):
        with tempfile.TemporaryDirectory() as tmp:
            fixture = InstallFixture(tmp)
            target = fixture.game / 'Modules' / MODULE_NAME
            write_module(target)
            plan = fixture.plan()

            def broken_rename(source, destination):
                if Path(destination) == target:
                    raise OSError('simulated lock')
                os.rename(source, destination)

            runner, _calls = fixture.build_runner()
            receipt = execute_install(plan, build_runner=runner,
                                      process_checker=lambda: [],
                                      rename=broken_rename)
            self.assertEqual(receipt['status'], 'recovery_required')
            self.assertTrue(receipt['rollback']['recovery_required'])
            self.assertTrue((fixture.game / 'Modules'
                             / (MODULE_NAME + '.backup-tx-1')).is_dir())
            self.assertTrue(Path(plan['stage_module']).is_dir())

    def test_digest_mismatch_after_activation_rolls_back(self):
        with tempfile.TemporaryDirectory() as tmp:
            fixture = InstallFixture(tmp)
            target = fixture.game / 'Modules' / MODULE_NAME
            write_module(target)
            plan = fixture.plan()

            def lying_inventory(path):
                if Path(path) == target:
                    return {'module_sha256': 'ff' * 32, 'file_count': 1}
                return module_inventory(path)

            runner, _calls = fixture.build_runner()
            receipt = execute_install(plan, build_runner=runner,
                                      process_checker=lambda: [],
                                      inventory=lying_inventory)
            self.assertEqual(receipt['status'], 'verification_failed_rolled_back')
            self.assertTrue(receipt['rollback']['restored'])
            self.assertTrue((target / 'ZOMBIEEE_REMASTER.json').is_file())
            self.assertFalse((fixture.game / 'Modules'
                              / (MODULE_NAME + '.backup-tx-1')).exists())

    def test_running_game_process_blocks_before_any_write(self):
        with tempfile.TemporaryDirectory() as tmp:
            fixture = InstallFixture(tmp)
            runner, calls = fixture.build_runner()
            receipt = execute_install(fixture.plan(), build_runner=runner,
                                      process_checker=lambda: ['mb_warband_wse2.exe'])
            self.assertEqual(receipt['status'], 'blocked')
            self.assertIn('game_processes_running', receipt['blockers'])
            self.assertEqual(calls, [])
            self.assertFalse((fixture.game / 'Modules' / MODULE_NAME).exists())


class RollbackTests(unittest.TestCase):
    def test_explicit_rollback_retains_current_target(self):
        with tempfile.TemporaryDirectory() as tmp:
            fixture = InstallFixture(tmp)
            target = fixture.game / 'Modules' / MODULE_NAME
            write_module(target, triggers=31)
            backup = target.with_name(MODULE_NAME + '.backup-tx-9')
            write_module(backup, triggers=25, map_scope='original-baseline')
            result = restore_backup({'target': str(target), 'backup': str(backup)},
                                    timestamp='20261024-040000')
            self.assertEqual(result['status'], 'restored')
            self.assertTrue(result['rejected'])
            self.assertTrue(Path(result['rejected']).is_dir())
            manifest = json.loads((target / 'ZOMBIEEE_REMASTER.json').read_text())
            self.assertEqual(manifest['final_trigger_count'], 25)
            self.assertFalse(backup.exists())

    def test_rollback_fails_closed_on_missing_or_foreign_backup(self):
        with tempfile.TemporaryDirectory() as tmp:
            fixture = InstallFixture(tmp)
            result = restore_backup({'target': str(fixture.game / 'Modules' / MODULE_NAME),
                                     'backup': str(fixture.root / 'elsewhere')})
            self.assertEqual(result['status'], 'failed')
            self.assertEqual(result['error'], 'backup_path_not_sibling')

    def test_verify_reports_structural_checks_and_never_runtime(self):
        with tempfile.TemporaryDirectory() as tmp:
            module = write_module(Path(tmp) / MODULE_NAME)
            report = verify_built_module(module, expected_source_sha256=SOURCE_SHA)
            self.assertTrue(report['ok'])
            self.assertEqual(report['trigger_count'], 31)
            self.assertFalse(report['runtime_verified'])
            self.assertTrue(report['checks']['probe_prefix'])
            broken = write_module(Path(tmp) / 'broken', triggers=25,
                                  map_scope='original-baseline')
            report = verify_built_module(broken, expected_source_sha256=SOURCE_SHA)
            self.assertFalse(report['ok'])
            self.assertIn('trigger_count', report['problems'])
            self.assertIn('city_scope', report['problems'])

    def test_build_argv_is_windowed_and_never_uses_a_replacement_flag(self):
        argv = build_argv(Path('C:/owned/ZOMBIEEEBeta04.rar'),
                          Path('C:/owned/Modules/.stage/ZOMBIEEE_Remaster'))
        self.assertIn('--archive', argv)
        self.assertIn('--out', argv)
        self.assertNotIn('--replace', argv)

    def test_install_paths_reject_unsafe_transaction_ids(self):
        for value in ('../escape', 'a b', '', 'x' * 65):
            with self.subTest(value=value), self.assertRaises(ValueError):
                install_paths('C:/game', value)


if __name__ == '__main__':
    unittest.main()
