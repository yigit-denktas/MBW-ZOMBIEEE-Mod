"""B rotation contract tests: 1-based team numbering + respawn/round fields."""
import sys
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))
from launcher.rotation import (  # noqa: E402
    ROSTER_CAVEAT, build_rotation, rotation_sha256, validate_rotation)


class RotationContractTests(unittest.TestCase):
    def test_default_rotation_has_validated_fields_and_order(self):
        lines = build_rotation()
        self.assertEqual(lines[-1], 'start')
        self.assertIn('set_bot_count 2 32', lines)
        self.assertIn('set_bot_count 1 0', lines)
        self.assertIn('set_respawn_period 5', lines)
        self.assertIn('set_round_max_seconds 1800', lines)
        self.assertIn('set_defender_spawn_count 0', lines)
        self.assertIn('set_player_respawn_as_bot 0', lines)
        self.assertLess(lines.index('max_num_bots 200'),
                        lines.index('set_bot_count 2 32'))
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

    def test_roster_caveat_is_explicit(self):
        self.assertIn('Crazed Civilian', ROSTER_CAVEAT)
        self.assertIn('native Zombie', ROSTER_CAVEAT)


if __name__ == '__main__':
    unittest.main()
