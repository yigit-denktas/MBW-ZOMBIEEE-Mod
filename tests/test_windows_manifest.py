import sys
import json
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from installer.manifest import plan_install, audit_archive
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

    def test_top_level_game_junction_keeps_raw_path_evidence(self):
        linked = self.root / 'game alias'
        directory_link(linked, self.root)
        plan = plan_install(linked, self.archive, 'root-link')
        self.assertIn('redirected_destination', plan['blockers'])
        self.assertEqual(plan['input_game_root'], str(linked))
        self.assertEqual(plan['game_root'], str(self.root))
        self.assertTrue(any(i['path'] == str(linked) for i in plan['path_issues']))
        self.assertTrue(plan['recheck_required_before_write'])

    def test_junction_in_game_root_ancestor_is_detected(self):
        parent = self.root / 'real parent'
        game = parent / 'game'
        pe(game / 'mb_warband.exe')
        alias = self.root / 'parent alias'
        directory_link(alias, parent)
        plan = plan_install(alias / 'game', self.archive, 'ancestor')
        self.assertIn('redirected_destination', plan['blockers'])
        self.assertTrue(any(i['path'] == str(alias) for i in plan['path_issues']))

    def test_journal_redirect_blocks_plan(self):
        outside = self.root / 'outside'
        outside.mkdir()
        directory_link(self.root / 'Modules/.zombieee-journal-link.json', outside)
        self.assertIn('redirected_destination', plan_install(self.root, self.archive, 'link')['blockers'])

    def test_unreadable_path_inspection_blocks_plan(self):
        with patch('installer.manifest.Path.lstat', side_effect=PermissionError('fixture denied')):
            plan = plan_install(self.root, self.archive, 'denied')
        self.assertIn('path_inspection_failed', plan['blockers'])
        self.assertTrue(plan['path_issues'])

    def test_stat_denial_after_lexical_check_stays_structured(self):
        """Review P2: exists()/is_dir() re-raise access denials after lstat succeeded."""
        real_stat = Path.stat
        modules = self.root / 'Modules'

        def deny_modules(path, *args, **kwargs):
            if Path(path) == modules:
                raise PermissionError('fixture denied')
            return real_stat(path, *args, **kwargs)

        with patch('installer.manifest.Path.stat', deny_modules):
            plan = plan_install(self.root, self.archive, 'denied-stat')
        self.assertIn('path_inspection_failed', plan['blockers'])
        self.assertTrue(any(issue['path'] == str(modules)
                            and issue['reason'] == 'path_inspection_failed'
                            for issue in plan['path_issues']))
        self.assertTrue(plan['dry_run'])
        self.assertFalse(plan['execution_enabled'])

        target = modules / 'ZOMBIEEE_Remaster'

        def deny_target(path, *args, **kwargs):
            if Path(path) == target:
                raise PermissionError('fixture denied')
            return real_stat(path, *args, **kwargs)

        with patch('installer.manifest.Path.stat', deny_target):
            plan = plan_install(self.root, self.archive, 'denied-target')
        self.assertEqual(plan['operation'], 'unknown')
        self.assertIn('path_inspection_failed', plan['blockers'])

    def test_unreadable_archive_and_executable_never_abort_planner(self):
        real_stat = Path.stat
        archive = self.archive

        def deny_archive(path, *args, **kwargs):
            if Path(path) == archive:
                raise PermissionError('fixture denied')
            return real_stat(path, *args, **kwargs)

        with patch('installer.manifest.Path.stat', deny_archive):
            plan = plan_install(self.root, archive, 'archive-denied')
        self.assertIn('path_inspection_failed', plan['blockers'])
        self.assertNotIn('archive_missing', plan['blockers'])

        with patch('installer.manifest.executable_status', return_value='unreadable_executable'):
            plan = plan_install(self.root, self.archive, 'exe-denied')
        self.assertIn('path_inspection_failed', plan['blockers'])
        self.assertNotIn('warband_invalid', plan['blockers'])

    def test_embedded_nul_configured_path_returns_structured_plan(self):
        plan = plan_install(str(self.root) + '\x00x', self.archive, 'nul')
        self.assertIn('path_inspection_failed', plan['blockers'])
        self.assertTrue(plan['path_issues'])
        self.assertTrue(plan['dry_run'])
        self.assertFalse(plan['execution_enabled'])

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

    def audit_tool(self, output, exit_code=0):
        tool = self.root / 'fake archive audit.py'
        tool.write_text('import sys\nprint(' + repr(output) + ')\nsys.exit(' + str(exit_code) + ')\n')
        return tool

    def test_archive_audit_uses_shared_cli_and_keeps_crc_unknown(self):
        tool = self.audit_tool(json.dumps({'identity_ok': True, 'crc_status': 'not_checked'}))
        with patch('installer.manifest.ARCHIVE_AUDIT', tool):
            plan = plan_install(self.root, self.archive, 'audit', audit=True)
        self.assertNotIn('archive_digest_unverified', plan['blockers'])
        self.assertIn('archive_crc_unverified', plan['blockers'])
        self.assertFalse(plan['execution_enabled'])
        self.assertTrue(plan['archive_audit']['identity_ok'])

    def test_audit_missing_tool_invalid_output_and_failed_identity_remain_unknown(self):
        self.assertEqual(audit_archive(self.archive, self.root / 'missing.py')['status'], 'unavailable')
        for output, code in [('not json', 0), ('[]', 0), ('{"identity_ok": "true"}', 0),
                             ('{"identity_ok": true}', 2)]:
            with self.subTest(output=output):
                result = audit_archive(self.archive, self.audit_tool(output, code))
                self.assertIsNot(result['identity_ok'], True)
