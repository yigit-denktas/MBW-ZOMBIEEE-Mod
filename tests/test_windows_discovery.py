"""Synthetic PE/Steam fixtures prove discovery behavior, never gameplay."""
import json
import struct
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from launcher.discovery import discover, file_version


def pe(path):
    path.parent.mkdir(parents=True, exist_ok=True)
    data = bytearray(256)
    data[:2] = b'MZ'
    struct.pack_into('<I', data, 60, 128)
    data[128:132] = b'PE\0\0'
    struct.pack_into('<H', data, 132, 0x14c)
    path.write_bytes(data)
    return path


def directory_link(link, target):
    if os.name == 'nt':
        subprocess.run(['cmd', '/c', 'mklink', '/J', str(link), str(target)],
                       capture_output=True, check=True)
    else:
        link.symlink_to(target, target_is_directory=True)


class DiscoveryTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)

    def game(self, root):
        pe(root / 'mb_warband.exe')
        (root / 'Modules').mkdir()
        return root

    def test_modern_multiple_libraries_spaces_and_provenance(self):
        steam = self.root / 'Steam'
        extra = self.root / 'Other Library'
        (steam / 'steamapps').mkdir(parents=True)
        game = self.game(extra / 'steamapps/common/My Warband')
        (extra / 'steamapps/appmanifest_48700.acf').write_text(
            '"AppState" { "appid" "48700" "installdir" "My Warband" }')
        (steam / 'steamapps/libraryfolders.vdf').write_text(
            '"libraryfolders" { "0" { "path" ' + json.dumps(str(extra)) + ' } }')
        report = discover([steam])
        self.assertEqual(report['candidates'][0]['path'], str(game.resolve()))
        self.assertEqual(report['candidates'][0]['status'], 'found')
        self.assertIn('steam_manifest', report['candidates'][0]['provenance'][0])
        self.assertIsNone(report['candidates'][0]['engine_version'])
        self.assertFalse(report['ambiguity'])

    def test_legacy_libraries_and_multiple_games_require_selection(self):
        steam = self.root / 'Steam'
        library = self.root / 'Library'
        (steam / 'steamapps').mkdir(parents=True)
        first = self.game(steam / 'steamapps/common/MountBlade Warband')
        self.game(library / 'steamapps/common/MountBlade Warband')
        (steam / 'steamapps/libraryfolders.vdf').write_text(
            '"LibraryFolders" { "1" ' + json.dumps(str(library)) + ' }')
        report = discover([steam], [first])
        self.assertEqual(len(report['candidates']), 2)
        self.assertTrue(report['ambiguity'])
        self.assertIsNone(report['selected'])

    def test_invalid_missing_executables_never_found(self):
        invalid = self.root / 'invalid'
        invalid.mkdir()
        (invalid / 'mb_warband.exe').write_text('MZ is not enough')
        report = discover([], [invalid, self.root / 'missing'])
        self.assertFalse(any(c['status'] == 'found' for c in report['candidates']))
        self.assertIn('warband_not_found', report['blockers'])

    def test_nested_wse2_and_duplicate_paths_are_read_only(self):
        game = self.game(self.root / 'Game')
        wse = pe(game / 'unexpected/WSE2/bin/wse2_launcher.exe')
        before = {str(p): p.read_bytes() for p in self.root.rglob('*') if p.is_file()}
        with patch('pathlib.Path.mkdir', side_effect=AssertionError('write')):
            report = discover([], [game, game / 'mb_warband.exe'])
        self.assertEqual(len(report['candidates']), 1)
        self.assertEqual(report['wse2_candidates'][0]['executable'], str(wse))
        self.assertEqual(before, {str(p): p.read_bytes() for p in self.root.rglob('*') if p.is_file()})

    def test_malformed_manifest_is_reported_and_does_not_abort(self):
        steam = self.root / 'steam'
        (steam / 'steamapps').mkdir(parents=True)
        (steam / 'steamapps/libraryfolders.vdf').write_text('"libraryfolders" {')
        report = discover([steam])
        self.assertTrue(report['warnings'])
        self.assertIn('warband_not_found', report['blockers'])

    def test_traversal_in_manifest_is_rejected(self):
        steam = self.root / 'steam'
        (steam / 'steamapps').mkdir(parents=True)
        (steam / 'steamapps/appmanifest_48700.acf').write_text(
            '"AppState" { "appid" "48700" "installdir" "../../outside" }')
        report = discover([steam])
        self.assertFalse(any(c['status'] == 'found' for c in report['candidates']))
        self.assertTrue(report['warnings'])

    def test_unreadable_root_is_warning(self):
        with patch('launcher.discovery.os.scandir', side_effect=PermissionError('fixture denied')):
            report = discover([], [self.root])
        self.assertTrue(report['warnings'])

    def test_known_folder_and_custom_wse2_executable(self):
        game = self.game(self.root / 'MountBlade Warband')
        wse = pe(self.root / 'separate tools/wse2_launcher.exe')
        report = discover([], [wse], [game])
        self.assertEqual(report['selected'], str(game))
        self.assertEqual(report['wse2_candidates'][0]['status'], 'found')

    def test_wse2_ambiguity_and_invalid_candidate(self):
        game = self.game(self.root / 'Game')
        pe(game / 'one/wse2_launcher.exe')
        pe(game / 'two/mb_warband_wse2.exe')
        invalid = game / 'bad_wse2.exe'
        invalid.write_text('not PE')
        report = discover([], [game])
        self.assertTrue(report['ambiguity'])
        self.assertIn('selection_required', report['blockers'])
        self.assertEqual(sum(c['status'] == 'found' for c in report['wse2_candidates']), 2)

    def test_search_budget_is_explicit(self):
        game = self.game(self.root / 'Game')
        for i in range(520):
            (game / str(i)).write_text('fixture')
        report = discover([], [game])
        self.assertTrue(any(w['reason'] == 'search_limit_reached' for w in report['warnings']))

    def test_symlink_is_not_followed_in_wse_search(self):
        game = self.game(self.root / 'Game')
        outside = self.root / 'outside'
        pe(outside / 'wse2_launcher.exe')
        directory_link(game / 'redirect', outside)
        self.assertEqual(discover([], [game])['wse2_candidates'], [])

    def test_oversized_and_wrong_typed_vdf_fail_closed(self):
        steam = self.root / 'steam'
        (steam / 'steamapps').mkdir(parents=True)
        path = steam / 'steamapps/libraryfolders.vdf'
        for contents in ('"libraryfolders" "wrong"', ' ' * (1024 * 1024 + 1)):
            path.write_text(contents)
            self.assertTrue(discover([steam])['warnings'])

    @unittest.skipUnless(os.name == 'nt', 'Windows version resources only')
    def test_version_resource_read_without_executing_candidate(self):
        self.assertTrue(file_version(Path(sys.executable)).startswith(
            '.'.join(str(v) for v in sys.version_info[:3])))
        self.assertIsNone(file_version(pe(self.root / 'fixture.exe')))

    def test_cli_returns_json_and_failure_status_without_inputs(self):
        result = subprocess.run(
            [sys.executable, '-B', '-m', 'launcher.discovery', '--no-known-folders'],
            cwd=Path(__file__).resolve().parents[1], capture_output=True, text=True)
        self.assertEqual(result.returncode, 2)
        self.assertEqual(json.loads(result.stdout)['selected'], None)
        self.assertEqual(result.stderr, '')

    def test_nul_in_manifest_or_custom_path_returns_warning_json(self):
        steam = self.root / 'steam'
        (steam / 'steamapps').mkdir(parents=True)
        (steam / 'steamapps/appmanifest_48700.acf').write_text(
            '"AppState" { "appid" "48700" "installdir" "Bad\x00Name" }')
        game = self.game(self.root / 'valid game')
        report = discover([steam, str(steam) + '\x00'], [str(self.root / 'bad') + '\x00', game])
        self.assertTrue(report['warnings'])
        self.assertEqual(report['selected'], str(game))
        self.assertNotIn('warband_not_found', report['blockers'])
