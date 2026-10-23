import sys
import json
import subprocess
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from installer.manifest import plan_install
from test_windows_discovery import pe, directory_link


class ManifestTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        pe(self.root / 'mb_warband.exe')
        (self.root / 'Modules').mkdir()
        self.archive = self.root / 'Original with spaces.rar'
        self.archive.write_bytes(b'fixture only, builder must reject digest')

    def test_plan_is_read_only_and_builder_targets_stage_not_live(self):
        before = sorted(str(p) for p in self.root.rglob('*'))
        plan = plan_install(self.root, self.archive, 'test-1')
        self.assertTrue(plan['dry_run'])
        self.assertFalse(plan['execution_enabled'])
        self.assertEqual(plan['build_argv'][-1], str(self.root / 'Modules/.zombieee-stage-test-1/ZOMBIEEE_Remaster'))
        self.assertNotIn('--replace', plan['build_argv'])
        self.assertEqual(before, sorted(str(p) for p in self.root.rglob('*')))
        self.assertIn('archive_digest_unverified', plan['blockers'])

    def test_existing_install_is_backed_up_in_plan(self):
        (self.root / 'Modules/ZOMBIEEE_Remaster').mkdir()
        plan = plan_install(self.root, self.archive, 'backup')
        self.assertEqual(plan['operation'], 'update')
        self.assertEqual(plan['backup'], str(self.root / 'Modules/.zombieee-backup-backup'))
        self.assertTrue(plan['consent_required'])

    def test_unsafe_transaction_name_refused(self):
        for name in ('../escape', '', 'x/y', 'a\\b', 'a:b'):
            with self.subTest(name=name), self.assertRaises(ValueError):
                plan_install(self.root, self.archive, name)

    def test_missing_inputs_and_colliding_stage_block_plan(self):
        stage = self.root / 'Modules/.zombieee-stage-collision'
        stage.mkdir()
        plan = plan_install(self.root, self.root / 'missing.rar', 'collision')
        self.assertIn('archive_missing', plan['blockers'])
        self.assertIn('transaction_path_exists', plan['blockers'])

    def test_invalid_game_blocks_plan(self):
        (self.root / 'mb_warband.exe').write_text('bad')
        self.assertIn('warband_invalid', plan_install(self.root, self.archive, 'bad')['blockers'])

    def test_journal_collision_blocks_plan(self):
        (self.root / 'Modules/.zombieee-journal-used.json').write_text('{}')
        self.assertIn('transaction_path_exists', plan_install(self.root, self.archive, 'used')['blockers'])

    def test_redirected_modules_blocks_plan(self):
        (self.root / 'Modules').rmdir()
        outside = self.root / 'elsewhere'
        outside.mkdir()
        directory_link(self.root / 'Modules', outside)
        self.assertIn('redirected_destination', plan_install(self.root, self.archive, 'redirect')['blockers'])

    def test_cli_plan_preserves_paths_with_spaces_without_writes(self):
        before = sorted(str(p) for p in self.root.rglob('*'))
        result = subprocess.run(
            [sys.executable, '-B', '-m', 'installer.manifest', '--game-root', str(self.root),
             '--archive', str(self.archive), '--transaction-id', 'cli'],
            cwd=Path(__file__).resolve().parents[1], capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        plan = json.loads(result.stdout)
        self.assertEqual(plan['build_argv'][3], str(self.archive))
        self.assertFalse(plan['execution_enabled'])
        self.assertEqual(before, sorted(str(p) for p in self.root.rglob('*')))
