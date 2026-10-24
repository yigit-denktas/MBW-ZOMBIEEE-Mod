"""Repair / verify / quarantine-uninstall tests for the installed City module.

No game process, no build and no real installer is invoked: every module tree is
a temporary fixture and receipts are written by the test itself.
"""
import json
import struct
import sys
import tempfile
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))
from launcher.install import module_file_hashes  # noqa: E402
from launcher.maintenance import (  # noqa: E402
    MaintenanceError, execute_repair, execute_uninstall,
    find_latest_install_receipt, load_install_receipt, plan_repair,
    plan_uninstall, verify_module)

SOURCE_SHA = 'ab' * 32
MODULE_NAME = 'ZOMBIEEE_Remaster'


def pe(path):
    path.parent.mkdir(parents=True, exist_ok=True)
    data = bytearray(256)
    data[:2] = b'MZ'
    struct.pack_into('<I', data, 60, 128)
    data[128:132] = b'PE\0\0'
    path.write_bytes(bytes(data))
    return path


def write_module(path, *, extra=None, marker='installed'):
    path.mkdir(parents=True, exist_ok=True)
    files = {
        'module.ini': 'module_name = ZOMBIEEE Remaster\n',
        'mission_templates.txt': 'mission\ntmpl\n',
        'scripts.txt': 'scripts\n',
        'troops.txt': 'troops\n',
        'variables.txt': 'variables\n',
        'lua/main.lua': 'print("ZDB1|heartbeat|count=1")\n',
        'lua/msfiles/ID_troops.py': 'troops = {}\n',
        'ZOMBIEEE_REMASTER.json': json.dumps({
            'source_archive_sha256': SOURCE_SHA,
            'runtime_verified': False,
            'archive_crc_verified': True,
            'experimental_map_scope': 'city-only',
            'final_trigger_count': 31,
            'original_mission_trigger_count': 25,
        }),
        'marker.txt': marker,
    }
    files.update(extra or {})
    for relative, text in files.items():
        file_path = path / relative
        file_path.parent.mkdir(parents=True, exist_ok=True)
        file_path.write_text(text, encoding='utf-8')
    return path


def make_receipt(game_root, module_dir, *, receipt_path=None):
    target = Path(module_dir).absolute()
    files = module_file_hashes(target)
    receipt = {
        'schema': 'zombieee.install-receipt.v1', 'schema_version': 1,
        'transaction_id': 'tx-fixture', 'timestamp': '20261024-140000',
        'game_root': str(Path(game_root).absolute()), 'target': str(target),
        'operation': 'install', 'archive_sha256': SOURCE_SHA,
        'module_sha256': 'x' * 64, 'file_count': len(files), 'files': files,
        'installed_sha256': 'x' * 64, 'installed_file_count': len(files),
        'status': 'installed', 'runtime_verified': False,
    }
    path = Path(receipt_path) if receipt_path is not None else (
        Path(game_root) / 'install-receipt-fixture.json')
    path.write_text(json.dumps(receipt), encoding='utf-8')
    return path


class MaintenanceFixture:
    def __init__(self, root):
        self.root = Path(root)
        self.game = self.root / 'Warband'
        pe(self.game / 'mb_warband.exe')
        (self.game / 'Modules').mkdir(parents=True)
        self.target = self.game / 'Modules' / MODULE_NAME
        self.source = self.root / 'build' / MODULE_NAME
        self.evidence = self.root / 'evidence'
        self.evidence.mkdir()
        write_module(self.target)
        write_module(self.source)
        self.receipt_path = make_receipt(self.game, self.target)
        self.receipt = load_install_receipt(self.receipt_path)


class VerifyTests(unittest.TestCase):
    def test_clean_module_verifies(self):
        with tempfile.TemporaryDirectory() as tmp:
            fixture = MaintenanceFixture(tmp)
            report = verify_module(fixture.target, fixture.receipt)
            self.assertTrue(report['verified'])
            self.assertEqual(report['problems'], [])
            self.assertFalse(report['write_required'])
            self.assertFalse(report['runtime_verified'])
            self.assertEqual(report['missing'], [])
            self.assertEqual(report['modified'], [])
            self.assertEqual(report['unrecognized'], [])

    def test_modified_missing_and_extra_files_are_classified(self):
        with tempfile.TemporaryDirectory() as tmp:
            fixture = MaintenanceFixture(tmp)
            (fixture.target / 'marker.txt').write_text('user edited',
                                                       encoding='utf-8')
            (fixture.target / 'scripts.txt').unlink()
            (fixture.target / 'user-notes.txt').write_text('mine',
                                                          encoding='utf-8')
            report = verify_module(fixture.target, fixture.receipt)
            self.assertFalse(report['verified'])
            self.assertIn('missing_owned_files', report['problems'])
            self.assertIn('modified_owned_files', report['problems'])
            self.assertIn('unrecognized_files', report['problems'])
            self.assertEqual(report['missing'], ['scripts.txt'])
            self.assertEqual(report['modified'], ['marker.txt'])
            self.assertEqual(report['unrecognized'], ['user-notes.txt'])

    def test_invalid_or_unsafe_receipts_are_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            fixture = MaintenanceFixture(tmp)
            for payload in ({'schema': 'wrong'}, {'schema': 'zombieee.install-receipt.v1',
                                                  'status': 'installed', 'files': []},
                            {'schema': 'zombieee.install-receipt.v1',
                             'status': 'installed',
                             'files': [{'path': '../escape', 'sha256': 'a' * 64}]}):
                path = fixture.root / 'bad.json'
                path.write_text(json.dumps(payload), encoding='utf-8')
                with self.subTest(payload=payload), self.assertRaises(MaintenanceError):
                    load_install_receipt(path)


class RepairTests(unittest.TestCase):
    def _broken_fixture(self, tmp):
        fixture = MaintenanceFixture(tmp)
        (fixture.target / 'scripts.txt').unlink()
        (fixture.target / 'marker.txt').write_text('user edited', encoding='utf-8')
        (fixture.target / 'user-notes.txt').write_text('mine', encoding='utf-8')
        return fixture

    def test_plan_and_execute_repair_preserves_user_files(self):
        with tempfile.TemporaryDirectory() as tmp:
            fixture = self._broken_fixture(tmp)
            plan = plan_repair(install_receipt=fixture.receipt,
                               source_module=fixture.source,
                               transaction_id='repair-1',
                               evidence_dir=fixture.evidence)
            self.assertEqual(plan['blockers'], [])
            self.assertEqual(plan['updates'], ['scripts.txt'])
            self.assertEqual(plan['conflicts'], ['marker.txt'])
            self.assertIn('modified_owned_files_preserved', plan['warnings'])
            self.assertIn('_expected', plan)  # private ownership map for execution
            receipt = execute_repair(plan, process_checker=lambda: [])
            self.assertEqual(receipt['status'], 'repaired')
            self.assertEqual(receipt['repaired'], ['scripts.txt'])
            self.assertEqual((fixture.target / 'paths-nope.txt').exists(), False)
            self.assertEqual((fixture.target / 'marker.txt').read_text(
                encoding='utf-8'), 'user edited')
            self.assertEqual((fixture.target / 'user-notes.txt').read_text(
                encoding='utf-8'), 'mine')
            after = verify_module(fixture.target, fixture.receipt)
            self.assertEqual(after['missing'], [])
            self.assertEqual(after['modified'], ['marker.txt'])
            self.assertEqual(after['unrecognized'], ['user-notes.txt'])

    def test_repair_can_replace_modified_owned_files_only_with_opt_in(self):
        with tempfile.TemporaryDirectory() as tmp:
            fixture = self._broken_fixture(tmp)
            plan = plan_repair(install_receipt=fixture.receipt,
                               source_module=fixture.source,
                               transaction_id='repair-2',
                               evidence_dir=fixture.evidence,
                               replace_modified=True)
            self.assertIn('marker.txt', plan['updates'])
            self.assertEqual(plan['conflicts'], [])
            receipt = execute_repair(plan, process_checker=lambda: [])
            self.assertEqual(receipt['status'], 'repaired')
            self.assertEqual((fixture.target / 'marker.txt').read_text(
                encoding='utf-8'), 'installed')

    def test_repair_plan_blocks_bad_source_or_running_game(self):
        with tempfile.TemporaryDirectory() as tmp:
            fixture = self._broken_fixture(tmp)
            plan = plan_repair(install_receipt=fixture.receipt,
                               source_module=fixture.root / 'missing',
                               transaction_id='repair-3',
                               evidence_dir=fixture.evidence)
            self.assertIn('repair_source_missing', plan['blockers'])
            plan = plan_repair(install_receipt=fixture.receipt,
                               source_module=fixture.source,
                               transaction_id='repair-4',
                               evidence_dir=fixture.evidence,
                               running_processes=['mb_warband.exe'])
            self.assertIn('game_processes_running', plan['blockers'])
            with self.assertRaises(MaintenanceError):
                execute_repair(plan, process_checker=lambda: [])

    def test_repair_refuses_when_game_running_at_execution(self):
        with tempfile.TemporaryDirectory() as tmp:
            fixture = self._broken_fixture(tmp)
            plan = plan_repair(install_receipt=fixture.receipt,
                               source_module=fixture.source,
                               transaction_id='repair-5',
                               evidence_dir=fixture.evidence)
            receipt = execute_repair(plan, process_checker=lambda: [
                'mb_warband_wse2.exe'])
            self.assertEqual(receipt['status'], 'blocked')
            self.assertFalse((fixture.target / 'scripts.txt').exists())


class UninstallTests(unittest.TestCase):
    def test_default_uninstall_quarantines_everything(self):
        with tempfile.TemporaryDirectory() as tmp:
            fixture = MaintenanceFixture(tmp)
            (fixture.target / 'user-notes.txt').write_text('mine',
                                                           encoding='utf-8')
            (fixture.target / 'marker.txt').write_text('user edited',
                                                       encoding='utf-8')
            plan = plan_uninstall(install_receipt=fixture.receipt,
                                  transaction_id='uninstall-1',
                                  evidence_dir=fixture.evidence)
            self.assertEqual(plan['blockers'], [])
            self.assertIn('user_files_preserved_in_quarantine', plan['warnings'])
            receipt = execute_uninstall(plan, process_checker=lambda: [])
            quarantine = Path(plan['quarantine'])
            self.assertEqual(receipt['status'], 'quarantined')
            self.assertFalse(fixture.target.exists())
            self.assertTrue(quarantine.is_dir())
            self.assertTrue((quarantine / 'user-notes.txt').is_file())
            self.assertTrue((quarantine / 'marker.txt').is_file())
            self.assertTrue((quarantine / 'scripts.txt').is_file())
            self.assertEqual(receipt['preserved_unrecognized'], ['user-notes.txt'])
            self.assertEqual(receipt['preserved_modified'], ['marker.txt'])
            self.assertFalse(receipt['game_data_deleted'])
            # The game executable and install backup are untouched.
            self.assertTrue((fixture.game / 'mb_warband.exe').is_file())

    def test_purge_owned_deletes_only_owned_unchanged_files(self):
        with tempfile.TemporaryDirectory() as tmp:
            fixture = MaintenanceFixture(tmp)
            (fixture.target / 'user-notes.txt').write_text('mine',
                                                           encoding='utf-8')
            (fixture.target / 'marker.txt').write_text('user edited',
                                                       encoding='utf-8')
            plan = plan_uninstall(install_receipt=fixture.receipt,
                                  transaction_id='uninstall-2',
                                  evidence_dir=fixture.evidence,
                                  purge_owned=True)
            receipt = execute_uninstall(plan, process_checker=lambda: [])
            quarantine = Path(plan['quarantine'])
            self.assertEqual(receipt['status'], 'uninstalled')
            self.assertTrue(receipt['purged_owned_files'])
            self.assertIn('scripts.txt', receipt['purged_owned_files'])
            self.assertFalse((quarantine / 'scripts.txt').exists())
            self.assertTrue((quarantine / 'marker.txt').is_file())
            self.assertTrue((quarantine / 'user-notes.txt').is_file())
            self.assertFalse(receipt['game_data_deleted'])

    def test_uninstall_blocks_missing_module_and_existing_quarantine(self):
        with tempfile.TemporaryDirectory() as tmp:
            fixture = MaintenanceFixture(tmp)
            plan = plan_uninstall(install_receipt=fixture.receipt,
                                  transaction_id='uninstall-3',
                                  evidence_dir=fixture.evidence)
            Path(plan['quarantine']).mkdir()
            plan = plan_uninstall(install_receipt=fixture.receipt,
                                  transaction_id='uninstall-3',
                                  evidence_dir=fixture.evidence)
            self.assertIn('quarantine_path_exists', plan['blockers'])
            with self.assertRaises(MaintenanceError):
                execute_uninstall(plan, process_checker=lambda: [])


class ReceiptDiscoveryTests(unittest.TestCase):
    def test_latest_install_receipt_is_bounded_and_newest(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            first = root / 'install-receipt-a.json'
            second = root / 'install-receipt-b.json'
            first.write_text('{}', encoding='utf-8')
            second.write_text('{}', encoding='utf-8')
            (root / 'other.json').write_text('{}', encoding='utf-8')
            import os
            import time
            os.utime(first, (1, 1))
            os.utime(second, (time.time() + 10, time.time() + 10))
            self.assertEqual(find_latest_install_receipt(root), second)
            self.assertIsNone(find_latest_install_receipt(root / 'missing'))


if __name__ == '__main__':
    unittest.main()
