"""Engine pairing tests: read-only selection of Warband + WSE2 client/dedicated."""
import sys
import tempfile
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))
from launcher.engines import (  # noqa: E402
    CLIENT_NAMES, DEDICATED_NAMES, plan_engines, select_engines, select_game_root)


def pe(path):
    path.parent.mkdir(parents=True, exist_ok=True)
    data = bytearray(256)
    data[:2] = b'MZ'
    import struct
    struct.pack_into('<I', data, 60, 128)
    data[128:132] = b'PE\0\0'
    path.write_bytes(bytes(data))
    return path


def game(root):
    pe(root / 'mb_warband.exe')
    (root / 'Modules').mkdir(parents=True, exist_ok=True)
    return root


def candidate(path, kind):
    executable = str(path / 'mb_warband.exe') if kind == 'warband' else str(path)
    return {'path': str(path), 'executable': executable, 'kind': kind,
            'status': 'found', 'provenance': ['fixture']}


def report(games=(), wse2=()):
    return {'schema_version': 1, 'read_only': True,
            'candidates': [candidate(Path(item), 'warband') for item in games],
            'wse2_candidates': [candidate(Path(item), 'wse2') for item in wse2],
            'ambiguity': len(games) > 1 or len(wse2) > 1,
            'selected': str(games[0]) if len(games) == 1 else None,
            'blockers': [], 'warnings': []}


class EnginePairingTests(unittest.TestCase):
    def test_single_root_pairs_local_client_and_dedicated(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = game(Path(tmp) / 'Warband')
            client = pe(root / CLIENT_NAMES[0])
            dedicated = pe(root / DEDICATED_NAMES[0])
            result = select_engines(report([root], [client, dedicated]), root)
            self.assertEqual(result['blockers'], [])
            self.assertEqual(result['client']['executable'], str(client))
            self.assertEqual(result['dedicated']['executable'], str(dedicated))

    def test_multiple_warband_roots_require_selection(self):
        with tempfile.TemporaryDirectory() as tmp:
            first = game(Path(tmp) / 'one')
            second = game(Path(tmp) / 'two')
            chosen, blockers = select_game_root(report([first, second]))
            self.assertIsNone(chosen)
            self.assertIn('selection_required', blockers)
            self.assertIn('warband_not_found',
                          select_game_root(report([]))[1])

    def test_explicit_root_must_match_discovery_evidence(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = game(Path(tmp) / 'Warband')
            report_data = report([root])
            chosen, blockers = select_game_root(report_data, game_root=root)
            self.assertEqual(chosen['path'], str(root))
            self.assertEqual(blockers, [])
            stray = game(Path(tmp) / 'Other')
            chosen, blockers = select_game_root(report_data, game_root=stray)
            self.assertIsNone(chosen)
            self.assertIn('game_root_not_discovered', blockers)

    def test_missing_dedicated_falls_back_to_single_outside_root(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = game(Path(tmp) / 'Warband')
            client = pe(root / CLIENT_NAMES[0])
            dedicated = pe(Path(tmp) / 'tools' / DEDICATED_NAMES[0])
            result = select_engines(report([root], [client, dedicated]), root)
            self.assertEqual(result['blockers'], [])
            self.assertEqual(result['dedicated']['executable'], str(dedicated))

    def test_missing_client_is_a_blocker(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = game(Path(tmp) / 'Warband')
            dedicated = pe(root / DEDICATED_NAMES[0])
            result = select_engines(report([root], [dedicated]), root)
            self.assertIn('client_not_found', result['blockers'])
            self.assertIsNone(result['client'])

    def test_ambiguous_client_outside_root_requires_selection(self):
        """No direct-root client: two remote candidates must not be guessed."""
        with tempfile.TemporaryDirectory() as tmp:
            root = game(Path(tmp) / 'Warband')
            dedicated = pe(root / DEDICATED_NAMES[0])
            first = pe(Path(tmp) / 'tools-a' / CLIENT_NAMES[0])
            second = pe(Path(tmp) / 'tools-b' / CLIENT_NAMES[0])
            result = select_engines(report([root], [first, second, dedicated]), root)
            self.assertIn('client_selection_required', result['blockers'])
            self.assertIsNone(result['client'])

    def test_direct_root_client_wins_over_nested_hint(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = game(Path(tmp) / 'Warband')
            dedicated = pe(root / DEDICATED_NAMES[0])
            pe(root / 'unexpected' / 'nested' / CLIENT_NAMES[0])
            direct = pe(root / CLIENT_NAMES[0])
            result = select_engines(report([root], [dedicated, direct]), root)
            self.assertEqual(result['blockers'], [])
            self.assertEqual(result['client']['executable'], str(direct))

    def test_explicit_executables_are_validated_not_assumed(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = game(Path(tmp) / 'Warband')
            client = pe(root / CLIENT_NAMES[0])
            missing = Path(tmp) / 'not-there.exe'
            result = select_engines(report([root], [client]), root,
                                    dedicated_exe=missing)
            self.assertIn('dedicated_missing_executable', result['blockers'])
            invalid = Path(tmp) / 'invalid.exe'
            invalid.write_text('not a PE')
            result = select_engines(report([root], [client]), root,
                                    dedicated_exe=invalid)
            self.assertIn('dedicated_invalid_pe_header', result['blockers'])

    def test_same_executable_cannot_fill_both_roles(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = game(Path(tmp) / 'Warband')
            client = pe(root / CLIENT_NAMES[0])
            result = select_engines(report([root], [client]), root,
                                    client_exe=client, dedicated_exe=client)
            self.assertIn('engine_roles_same_executable', result['blockers'])

    def test_plan_engines_combines_selection_and_pairing(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = game(Path(tmp) / 'Warband')
            client = pe(root / CLIENT_NAMES[0])
            dedicated = pe(root / DEDICATED_NAMES[0])
            result = plan_engines(report([root], [client, dedicated]))
            self.assertEqual(result['blockers'], [])
            self.assertEqual(result['warband']['path'], str(root))
            self.assertEqual(result['client']['provenance'], ['fixture'])


if __name__ == '__main__':
    unittest.main()
