"""M2 installer/release gates: settings, shortcut/control panel, release checks.

No game launch, no build, no real shortcut and no live installer action: module
trees and repositories are temporary fixtures; external runners are injected.
"""
import io
import json
import os
import sys
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest import mock

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))
from launcher import control_panel  # noqa: E402
from launcher.city_launch import main as play_city_main  # noqa: E402
from launcher.install import module_file_hashes  # noqa: E402
from launcher.release_gate import (  # noqa: E402
    ReleaseGateError, build_release_gate, format_release_gate, git_tracked_files)
from launcher.settings import (  # noqa: E402
    SCHEMA as SETTINGS_SCHEMA, SettingsError, default_settings_path,
    load_settings, merge_cli, save_settings, validate_settings)
from launcher.shortcut import (  # noqa: E402
    SCHEMA as SHORTCUT_SCHEMA, ShortcutError, create_shortcut, shortcut_spec)

SOURCE_SHA = 'ab' * 32
MODULE_NAME = 'ZOMBIEEE_Remaster'


def write_module(path, *, extra=None):
    path.mkdir(parents=True, exist_ok=True)
    files = {
        'module.ini': 'module_name = ZOMBIEEE Remaster\n',
        'mission_templates.txt': 'm\n',
        'scripts.txt': 's\n',
        'troops.txt': 't\n',
        'variables.txt': 'v\n',
        'lua/main.lua': 'print("ZDB1|heartbeat|count=1")\n',
        'ZOMBIEEE_REMASTER.json': json.dumps({
            'source_archive_sha256': SOURCE_SHA,
            'remaster_version': '0.2.0',
            'runtime_verified': False,
            'archive_crc_verified': True,
            'experimental_map_scope': 'city-only',
            'final_trigger_count': 31,
            'original_mission_trigger_count': 25,
        }),
        'marker.txt': 'installed',
    }
    files.update(extra or {})
    for relative, text in files.items():
        file_path = path / relative
        file_path.parent.mkdir(parents=True, exist_ok=True)
        file_path.write_text(text, encoding='utf-8')
    return path


def game_with_module(root):
    game = Path(root) / 'Warband'
    (game / 'Modules').mkdir(parents=True)
    (game / 'mb_warband.exe').write_bytes(b'MZ' + b'\x00' * 62)
    target = write_module(game / 'Modules' / MODULE_NAME)
    return game, target


def install_receipt(game, target, path):
    files = module_file_hashes(target)
    receipt = {'schema': 'zombieee.install-receipt.v1', 'schema_version': 1,
               'transaction_id': 'tx', 'status': 'installed',
               'game_root': str(game), 'target': str(target),
               'archive_sha256': SOURCE_SHA, 'files': files,
               'module_sha256': 'x' * 64, 'file_count': len(files),
               'installed_sha256': 'x' * 64,
               'installed_file_count': len(files), 'runtime_verified': False}
    Path(path).write_text(json.dumps(receipt), encoding='utf-8')
    return Path(path)


class SettingsTests(unittest.TestCase):
    def test_validate_and_roundtrip(self):
        data = {'schema': SETTINGS_SCHEMA, 'schema_version': 1,
                'enemy_profile': 'weak-wave1', 'fire_mode': 'single',
                'team0_bots': 8,
                'team2_bots': 8, 'max_minutes': 3.0,
                'evidence_root': 'D:\\private-evidence'}
        settings, warnings = validate_settings(data)
        self.assertEqual(warnings, [])
        self.assertEqual(settings['enemy_profile'], 'weak-wave1')
        self.assertEqual(settings['fire_mode'], 'single')
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / 'settings.json'
            written = save_settings(data, path)
            self.assertEqual(written, path)
            loaded, warnings = load_settings(path)
            self.assertEqual(warnings, [])
            self.assertEqual(loaded['team0_bots'], 8)
            self.assertEqual(loaded['_path'], str(path.absolute()))
            self.assertEqual((path.parent / 'settings.json.tmp').exists(), False)

    def test_rejects_bad_shapes_choices_and_secrets(self):
        for payload in (
                {'schema': 'wrong'},
                {'schema': SETTINGS_SCHEMA, 'enemy_profile': 'insane'},
                {'schema': SETTINGS_SCHEMA, 'fire_mode': 'rapid'},
                {'schema': SETTINGS_SCHEMA, 'team0_bots': 500},
                {'schema': SETTINGS_SCHEMA, 'max_minutes': -1},
                {'schema': SETTINGS_SCHEMA, 'no_known_folders': 'yes'},
                {'schema': SETTINGS_SCHEMA, 'game_root': 'bad\x00path'},
                {'schema': SETTINGS_SCHEMA, 'admin_password': 'x'},
                {'schema': SETTINGS_SCHEMA, 'control_key': 'abc'}):
            with self.subTest(payload=payload), self.assertRaises(SettingsError):
                validate_settings(payload)

    def test_unknown_safe_settings_are_ignored_with_warning(self):
        settings, warnings = validate_settings(
            {'schema': SETTINGS_SCHEMA, 'colour': 'blue'})
        self.assertNotIn('colour', settings)
        self.assertIn('unknown_setting_ignored:colour', warnings)

    def test_default_path_uses_local_appdata_and_cli_wins(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = default_settings_path({'LOCALAPPDATA': tmp})
            self.assertEqual(path, Path(tmp) / 'ZOMBIEEE' / 'launcher-settings.json')
        args = SimpleNamespace(team0_bots=None, enemy_profile=None,
                               max_minutes=None, evidence_root=None)
        args = merge_cli({'team0_bots': 8, 'enemy_profile': 'weak-wave1'}, args)
        self.assertEqual(args.team0_bots, 8)
        self.assertEqual(args.enemy_profile, 'weak-wave1')
        args.team0_bots = 4
        merge_cli({'team0_bots': 8}, args)
        self.assertEqual(args.team0_bots, 4)


class ShortcutTests(unittest.TestCase):
    def test_spec_targets_control_panel_and_never_a_game(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / 'repo'
            root.mkdir()
            python = root / 'python.exe'
            python.write_text('', encoding='utf-8')
            (root / 'pythonw.exe').write_text('', encoding='utf-8')
            settings = root / 'settings.json'
            spec = shortcut_spec(repo_root=root, settings_path=settings,
                                 python_executable=python)
            self.assertEqual(spec['schema'], SHORTCUT_SCHEMA)
            self.assertEqual(spec['target'], str(root / 'pythonw.exe'))
            self.assertEqual(spec['module'], 'launcher.control_panel')
            self.assertIn('launcher.control_panel', spec['arguments'])
            self.assertIn('--settings', spec['arguments'])
            self.assertFalse(spec['launches_game_directly'])
            with self.assertRaises(ShortcutError):
                shortcut_spec(module='launcher.play_city_bypass')

    def test_create_shortcut_uses_environment_only(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            spec = shortcut_spec(repo_root=root)
            calls = {}

            def runner(command, **kwargs):
                calls['command'] = list(command)
                calls['env'] = dict(kwargs.get('env') or {})
                calls['shell'] = kwargs.get('shell')
                return SimpleNamespace(returncode=0, stdout='ok', stderr='')

            receipt = create_shortcut(spec, root / 'Play City.lnk', runner=runner)
            self.assertTrue(receipt['created'])
            (root / 'Play City.lnk').write_text('', encoding='utf-8')
            self.assertEqual(receipt['path'], str(root / 'Play City.lnk'))
            self.assertEqual(calls['shell'], None)
            self.assertEqual(calls['env']['ZOMBIEEE_TARGET'], spec['target'])
            self.assertEqual(calls['env']['ZOMBIEEE_ARGS'], spec['arguments'])
            self.assertIn('WScript.Shell', ' '.join(calls['command']))
            self.assertNotIn(spec['target'], ' '.join(calls['command']))
            with self.assertRaises(ShortcutError):
                create_shortcut(spec, root / 'Play City.lnk', runner=runner)
            with self.assertRaises(ShortcutError):
                create_shortcut(spec, root / 'bad.txt', runner=runner)
            with self.assertRaises(ShortcutError):
                create_shortcut(spec, root / 'none' / 'x.lnk', runner=runner)


class ControlPanelTests(unittest.TestCase):
    def test_actions_cover_play_settings_logs_repair_release(self):
        action_list = control_panel.actions(settings_path='C:/private/s.json')
        ids = [entry['id'] for entry in action_list]
        self.assertEqual(ids, ['play', 'settings', 'logs', 'repair',
                               'uninstall', 'release'])
        self.assertTrue(all(entry['command'] for entry in action_list))
        play = action_list[0]
        self.assertIn('launcher.play_city', play['command'])
        self.assertIn('play', play['command'])
        uninstall = next(e for e in action_list if e['id'] == 'uninstall')
        self.assertNotIn('--purge-owned', uninstall['command'])
        self.assertIn('--settings', play['command'])
        text = control_panel.format_actions(action_list)
        self.assertIn('Play Solo City', text)

    def test_print_actions_cli_starts_no_gui(self):
        with mock.patch('tkinter.Tk', side_effect=AssertionError('GUI started')):
            self.assertEqual(control_panel.main(['--print-actions']), 0)


class ReleaseGateTests(unittest.TestCase):
    def _repo(self, root):
        files = {
            'VERSION': '0.2.0\n',
            'README.md': 'Run python -m launcher.play_city. tools/build.py and '
                         'archive_audit are documented.\n',
            'docs/WINDOWS_BOOTSTRAP.md': 'python -m launcher.play_city; '
                                         'tools/build.py; archive_audit\n',
            'docs/PROVENANCE.md': 'provenance\n',
            'launcher/play_city.py': 'pass\n',
            'launcher/control_panel.py': 'pass\n',
            'launcher/install.py': 'pass\n',
            'launcher/maintenance.py': 'pass\n',
            'reference/LEGAL_RIGHTS_AND_CREDITS.md': 'legal dossier\n',
            'reference/CROSS_REVIEW_LEGAL_RELEASE_2026-10-24.md':
                'review record\n',
            'installer/manifest.py': 'pass\n',
            'tools/build.py': 'pass\n',
            'tools/archive_audit.py': 'pass\n',
            'CHANGELOG.md': '# Changelog\n\n## [0.2.0] - 2026-10-24\n',
            'docs/RELEASE_TRACEABILITY.md': 'fixture traceability\n',
            'docs/release-traceability.json': json.dumps({
                'schema': 'zombieee.release-traceability.v1',
                'schema_version': 1, 'candidate_version': '0.2.0',
                'release_state': 'candidate', 'acceptance': 'none',
                'runtime_verified': False,
                'work_items': [{
                    'id': 'ZOM-WIN-02', 'state': 'active', 'lane': 'B',
                    'acceptance': 'none', 'release': '0.2.0',
                    'prs': [{'number': 1,
                             'url': 'https://github.com/example/repo/pull/1',
                             'merge_commit': 'a' * 40}],
                    'commits': []}],
                'releases': [{
                    'version': '0.2.0', 'state': 'candidate',
                    'changelog': 'CHANGELOG.md#020',
                    'acceptance': 'none', 'runtime_verified': False,
                    'published': False, 'included_prs': [1]}],
                'gaps': ['fixture gap'],
            }, indent=2) + '\n',
        }
        for relative, text in files.items():
            path = Path(root) / relative
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(text, encoding='utf-8')
        return list(files)

    def test_clean_candidate_passes_without_acceptance_claim(self):
        with tempfile.TemporaryDirectory() as tmp:
            tracked = self._repo(tmp)
            gate = build_release_gate(root=tmp, tracked_files=tracked)
            self.assertTrue(gate['ok'], gate['blockers'])
            self.assertEqual(gate['acceptance'], 'none')
            self.assertFalse(gate['runtime_verified'])
            self.assertEqual(gate['delivery_status'], 'candidate-checks-only')
            self.assertIn('Release delivery checks: OK',
                          format_release_gate(gate))

    def test_missing_files_binaries_paths_and_secrets_block(self):
        with tempfile.TemporaryDirectory() as tmp:
            tracked = self._repo(tmp)
            (Path(tmp) / 'README.md').unlink()
            (Path(tmp) / 'docs/WINDOWS_BOOTSTRAP.md').unlink()
            gate = build_release_gate(root=tmp, tracked_files=tracked)
            self.assertIn('required_files', gate['blockers'])
            self.assertIn('reproducible_commands', gate['blockers'])
        with tempfile.TemporaryDirectory() as tmp:
            tracked = self._repo(tmp)
            tracked = tracked + ['vendor/ZOMBIEEEBeta04.rar', 'game.exe',
                                 'run.log']
            gate = build_release_gate(root=tmp, tracked_files=tracked)
            self.assertIn('no_tracked_binaries_or_logs', gate['blockers'])
        with tempfile.TemporaryDirectory() as tmp:
            tracked = self._repo(tmp)
            (Path(tmp) / 'launcher/install.py').write_text(
                'ARCHIVE = "C:' + chr(92) + 'Users' + chr(92) + 'Alice' + chr(92) + 'Downloads' + chr(92) + 'x.rar"\n',
                encoding='utf-8')
            gate = build_release_gate(root=tmp, tracked_files=tracked)
            self.assertIn('no_personal_local_paths', gate['blockers'])
        with tempfile.TemporaryDirectory() as tmp:
            tracked = self._repo(tmp)
            (Path(tmp) / 'launcher/install.py').write_text(
                'TOKEN = "ghp_' + 'a' * 30 + '"\n', encoding='utf-8')
            gate = build_release_gate(root=tmp, tracked_files=tracked)
            self.assertIn('no_obvious_secrets', gate['blockers'])

    def test_installed_module_check_and_git_runner_error(self):
        with tempfile.TemporaryDirectory() as tmp:
            tracked = self._repo(tmp)
            game, _target = game_with_module(tmp)
            gate = build_release_gate(root=tmp, game_root=game,
                                      tracked_files=tracked)
            self.assertTrue(gate['ok'], gate['blockers'])
            self.assertTrue(gate['remaster_module']['ok'])
        with tempfile.TemporaryDirectory() as tmp:
            tracked = self._repo(tmp)
            (Path(tmp) / 'Modules' / MODULE_NAME).mkdir(parents=True)
            gate = build_release_gate(root=tmp, game_root=tmp,
                                      tracked_files=tracked)
            self.assertIn('installed_module_city_structure', gate['blockers'])
        with tempfile.TemporaryDirectory() as tmp:
            tracked = self._repo(tmp)
            with mock.patch('launcher.release_gate.git_tracked_files',
                            side_effect=ReleaseGateError('git unavailable')):
                gate = build_release_gate(root=tmp)
            self.assertIn('git_tracked_files_unavailable', gate['warnings'])


class M2CliTests(unittest.TestCase):
    def test_verify_repair_uninstall_and_settings_cli(self):
        with tempfile.TemporaryDirectory() as tmp:
            game, target = game_with_module(tmp)
            receipt = install_receipt(game, target, Path(tmp) / 'receipt.json')
            (target / 'scripts.txt').unlink()
            (target / 'user-notes.txt').write_text('mine', encoding='utf-8')
            no_games = mock.patch(
                'launcher.city_launch.running_game_processes',
                return_value=[])
            no_games.start()
            self.addCleanup(no_games.stop)
            with mock.patch('sys.stdout'):
                code = play_city_main(['verify', '--receipt', str(receipt)])
            self.assertEqual(code, 2)
            source = write_module(Path(tmp) / 'build' / MODULE_NAME)
            with mock.patch('sys.stdout'):
                code = play_city_main(['repair', '--receipt', str(receipt),
                                       '--from-module', str(source),
                                       '--evidence-root', str(Path(tmp))])
            self.assertEqual(code, 0)
            self.assertTrue((target / 'scripts.txt').is_file())
            self.assertEqual((target / 'user-notes.txt').read_text(
                encoding='utf-8'), 'mine')
            with mock.patch('sys.stdout'):
                code = play_city_main(['uninstall', '--receipt', str(receipt),
                                       '--evidence-root', str(Path(tmp))])
            self.assertEqual(code, 0)
            self.assertFalse(target.exists())
            quarantines = list((game / 'Modules').glob(MODULE_NAME + '.uninstalled-*'))
            self.assertEqual(len(quarantines), 1)
            self.assertTrue((quarantines[0] / 'user-notes.txt').is_file())
            settings_path = Path(tmp) / 'settings.json'
            with mock.patch('sys.stdout'):
                code = play_city_main(['settings', 'write',
                                       '--settings', str(settings_path),
                                       '--team0-bots', '8'])
            self.assertEqual(code, 0)
            loaded, _warnings = load_settings(settings_path)
            self.assertEqual(loaded['team0_bots'], 8)

    def test_shortcut_and_release_check_cli_are_read_only(self):
        with tempfile.TemporaryDirectory() as tmp:
            with mock.patch('sys.stdout'):
                code = play_city_main(['shortcut', '--json'])
            self.assertEqual(code, 0)
        # release-check must be read-only and emit valid JSON. On a feature
        # checkout the fail-closed gate may report the known head-guard and
        # A-owned path debt; no other blockers are acceptable.
        with mock.patch('sys.stdout', new_callable=io.StringIO) as captured:
            code = play_city_main(['release-check', '--json'])
        self.assertIn(code, (0, 2))
        payload = json.loads(captured.getvalue())
        self.assertEqual(payload.get('schema'), 'zombieee.release-gate.v1')
        self.assertEqual(payload.get('acceptance'), 'none')
        self.assertIs(payload.get('runtime_verified'), False)
        if code == 2:
            self.assertLessEqual(
                set(payload.get('blockers') or []),
                {'traceability_head_revision', 'no_personal_local_paths'})


if __name__ == '__main__':
    unittest.main()
