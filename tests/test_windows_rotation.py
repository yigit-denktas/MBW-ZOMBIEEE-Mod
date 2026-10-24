"""B rotation contract tests: 1-based team numbering + respawn/round fields."""
import sys
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))
from launcher.rotation import (  # noqa: E402
    DEFAULT_ENEMY_PROFILE, DEFAULT_TEAM1_BOTS, DEFENDER_SQUAD_BOTS,
    ENEMY_PROFILES, ENEMY_PROFILE_BOTS, ROSTER_CAVEAT, WEAK_WAVE1_BOTS,
    build_defender_rotation, build_rotation, rotation_sha256,
    validate_rotation)


class RotationContractTests(unittest.TestCase):
    def test_default_rotation_has_validated_fields_and_order(self):
        lines = build_rotation()
        self.assertEqual(lines[-1], 'start')
        self.assertIn('set_bot_count 2 24', lines)
        self.assertIn('set_bot_count 1 0', lines)
        self.assertIn('set_respawn_period 5', lines)
        self.assertIn('set_round_max_seconds 1800', lines)
        self.assertIn('set_defender_spawn_count 0', lines)
        self.assertIn('set_player_respawn_as_bot 0', lines)
        self.assertLess(lines.index('max_num_bots 200'),
                        lines.index('set_bot_count 2 24'))
        self.assertTrue(validate_rotation(lines))

    def test_second_team_count_must_be_positive(self):
        with self.assertRaises(ValueError):
            build_rotation(team2_bots=0)
        with self.assertRaises(ValueError):
            build_rotation(team2_bots=-1)

    def test_invalid_numbers_rejected(self):
        for kwargs in ({'max_bots': 10}, {'respawn_period': 0},
                       {'round_max_seconds': 10}, {'team2_bots': 600},
                       {'player_respawn_as_bot': 2}):
            with self.subTest(kwargs=kwargs), self.assertRaises(ValueError):
                build_rotation(**kwargs)

    def test_validate_rejects_wrong_order_and_missing_start(self):
        lines = build_rotation()
        with self.assertRaises(ValueError):
            validate_rotation(lines[:-1])
        swapped = lines[:]
        swapped[7], swapped[8] = swapped[8], swapped[7]
        with self.assertRaises(ValueError):
            validate_rotation(swapped)

    def test_digest_is_stable_and_order_sensitive(self):
        lines = build_rotation()
        self.assertEqual(rotation_sha256(lines), rotation_sha256(list(lines)))
        changed = lines[:]
        changed[-2] = 'set_player_respawn_as_bot 1'
        self.assertNotEqual(rotation_sha256(lines), rotation_sha256(changed))


    def test_defender_squad_switches_team0_bots_only(self):
        stock = build_rotation()
        defender = build_defender_rotation()
        self.assertEqual(stock[7], 'set_bot_count 1 0')
        self.assertEqual(defender[7], 'set_bot_count 1 8')
        self.assertEqual(defender[8], 'set_bot_count 2 24')
        self.assertIn('set_defender_spawn_count 0', defender)
        self.assertTrue(validate_rotation(defender))
        self.assertEqual(DEFAULT_TEAM1_BOTS, 0)
        self.assertEqual(DEFENDER_SQUAD_BOTS, 8)
        self.assertEqual(defender, build_rotation(team1_bots=8))
        self.assertNotEqual(rotation_sha256(stock), rotation_sha256(defender))

    def test_defender_squad_flag_validates_conflicts(self):
        self.assertEqual(build_rotation(defender_squad=True),
                         build_defender_rotation())
        for kwargs in ({'team1_bots': 2, 'defender_squad': True},
                       {'defender_squad': 'yes'}, {'defender_squad': 1}):
            with self.subTest(kwargs=kwargs), self.assertRaises(ValueError):
                build_rotation(**kwargs)
        with self.assertRaises(TypeError):
            build_defender_rotation(team1_bots=4)

    def test_enemy_profiles_select_team2_counts(self):
        self.assertEqual(DEFAULT_ENEMY_PROFILE, 'generic')
        self.assertEqual(ENEMY_PROFILES, ('generic', 'weak-wave1', 'native-only'))
        self.assertEqual(ENEMY_PROFILE_BOTS['generic'], 24)
        self.assertEqual(ENEMY_PROFILE_BOTS['weak-wave1'], WEAK_WAVE1_BOTS)
        self.assertEqual(ENEMY_PROFILE_BOTS['native-only'], 0)
        self.assertEqual(build_rotation()[8], 'set_bot_count 2 24')
        self.assertEqual(build_rotation(enemy_profile='weak-wave1')[8],
                         'set_bot_count 2 8')
        native = build_rotation(enemy_profile='native-only')
        self.assertEqual(native[8], 'set_bot_count 2 0')
        self.assertTrue(validate_rotation(native, enemy_profile='native-only'))
        self.assertEqual(build_rotation(team2_bots=2)[8], 'set_bot_count 2 2')

    def test_enemy_profile_validation_is_fail_closed(self):
        for kwargs in ({'enemy_profile': 'unknown'},
                       {'enemy_profile': 'generic', 'team2_bots': 0},
                       {'enemy_profile': 'weak-wave1', 'team2_bots': 0},
                       {'enemy_profile': 'native-only', 'team2_bots': 2}):
            with self.subTest(kwargs=kwargs), self.assertRaises(ValueError):
                build_rotation(**kwargs)
        with self.assertRaises(ValueError):
            validate_rotation(build_rotation(enemy_profile='native-only'))
        with self.assertRaises(ValueError):
            validate_rotation(build_rotation(enemy_profile='native-only'),
                              enemy_profile='generic')

    def test_defender_and_enemy_profiles_compose(self):
        lines = build_rotation(defender_squad=True, enemy_profile='weak-wave1')
        self.assertEqual(lines[7], 'set_bot_count 1 8')
        self.assertEqual(lines[8], 'set_bot_count 2 8')
        self.assertTrue(validate_rotation(lines, enemy_profile='weak-wave1'))
        native = build_rotation(defender_squad=True, enemy_profile='native-only')
        self.assertEqual(native[7], 'set_bot_count 1 8')
        self.assertEqual(native[8], 'set_bot_count 2 0')

    def test_roster_caveat_is_explicit(self):
        self.assertIn('Crazed Civilian', ROSTER_CAVEAT)
        self.assertIn('native Zombie', ROSTER_CAVEAT)


if __name__ == '__main__':
    unittest.main()
