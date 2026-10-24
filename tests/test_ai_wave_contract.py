"""City AI semantics regression against original Beta 0.4 native mission."""
import os
import re
from pathlib import Path
import shutil
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'tools'))
from ai_wave_contract import decode_trigger, inspect_city_ai
from wave_reinforcements import (INVASION_GAME_TYPE, GLOBAL_BASE, WAVE_CHANGED,
                                 ROUND_STAMP, ROUND_OR_WAVE_CHANGED)
from patch_defenders import patch_file, mission_bounds
from city_defense import apply_module as apply_city
from wave_reinforcements import apply_module as apply_wave
from tactical_recovery import apply_module as apply_recovery
from city_acceptance import audit_city

ORIGINAL = Path(os.environ.get('ZOMBIEEE_ORIGINAL_MODULE', '/missing/ZOMBIEEE'))


def triggers(root):
    lines = (root / 'mission_templates.txt').read_text().splitlines(keepends=True)
    at, count, end = mission_bounds(lines)
    return [line.strip() for line in lines[at + 1:end]]


class NativeDecoderTests(unittest.TestCase):
    def test_rejects_trailing_truncated_and_negative_arity(self):
        for row in ('1 0 0 1 417 0 0 garbage',
                    '1 0 0 1 31 2 10 0',
                    '1 0 0 1 417 -1 0'):
            with self.subTest(row=row), self.assertRaises(ValueError):
                decode_trigger(row)

    def test_reads_both_native_sections(self):
        self.assertEqual(decode_trigger('1 0 0 1 417 0 1 2133 2 5 7'),
                         ([(417, ())], [(2133, (5, 7))]))


@unittest.skipUnless(ORIGINAL.is_dir(), 'Owned 2012 original required')
class OriginalInvasionModeTests(unittest.TestCase):
    def setUp(self):
        self.td = tempfile.TemporaryDirectory()
        self.addCleanup(self.td.cleanup)
        self.root = Path(self.td.name)
        (self.root / 'SceneObj').mkdir()
        for name in ('troops.txt', 'mission_templates.txt', 'variables.txt', 'scenes.txt'):
            shutil.copy2(ORIGINAL / name, self.root / name)
        for number in range(1, 6):
            name = f'scn_tbfc_invasion_{number}.sco'
            shutil.copy2(ORIGINAL / 'SceneObj' / name, self.root / 'SceneObj' / name)
        patch_file(self.root, 4, city_only=True)
        apply_city(self.root)
        apply_wave(self.root, cap=4, city_only=True)
        apply_recovery(self.root, city_only=True)
        self.before = triggers(ORIGINAL)
        self.after = triggers(self.root)
        self.old_vars = (ORIGINAL / 'variables.txt').read_text().splitlines()
        self.new_vars = (self.root / 'variables.txt').read_text().splitlines()

    def inspect(self, *, old=None, new=None):
        return inspect_city_ai(self.before if old is None else old,
                               self.after if new is None else new,
                               self.old_vars, self.new_vars)

    def test_original_unconditionally_initializes_game_type_seven(self):
        self.assertEqual(INVASION_GAME_TYPE, 7)
        actual = self.inspect()
        self.assertFalse(actual['problems'], actual)
        self.assertEqual(actual['original_invasion_mode'], 7)
        base_idx = self.old_vars.index('g_multiplayer_game_type')
        _, effects = decode_trigger(self.before[3])
        self.assertEqual(effects[0], (2133, (GLOBAL_BASE + base_idx, 7)))
        for trigger_idx in (28, 30):
            conditions, _ = decode_trigger(self.after[trigger_idx])
            self.assertIn((31, (GLOBAL_BASE + base_idx, 7)), conditions)
            self.assertNotIn((31, (GLOBAL_BASE + base_idx, 6)), conditions)

    def test_compiled_mode_six_regression_cannot_pass(self):
        type_global = GLOBAL_BASE + self.old_vars.index('g_multiplayer_game_type')
        for idx, key in ((28, 'reinforcement_correct_mode'),
                         (30, 'recovery_correct_mode')):
            with self.subTest(idx=idx):
                mutated = self.after.copy()
                marker = f'31 2 {type_global} 7'
                self.assertIn(marker, mutated[idx])
                mutated[idx] = mutated[idx].replace(marker,
                                                    f'31 2 {type_global} 6', 1)
                result = self.inspect(new=mutated)
                self.assertFalse(result['checks'][key])
                self.assertFalse(all(result['checks'].values()))

    def test_static_acceptance_rejects_dormant_six_mode(self):
        path = self.root / 'mission_templates.txt'
        lines = path.read_text().splitlines(keepends=True)
        at, _, _ = mission_bounds(lines)
        index = at + 1 + 28
        marker = f'31 2 {GLOBAL_BASE + self.old_vars.index("g_multiplayer_game_type")} 7'
        self.assertIn(marker, lines[index])
        lines[index] = lines[index].replace(marker, marker[:-1] + '6', 1)
        path.write_text(''.join(lines))
        result = audit_city(self.root, ORIGINAL)
        self.assertFalse(result['city_accepted'])
        self.assertFalse(result['checks']['ai_reinforcement_correct_mode'])

    def test_original_mode_change_invalidates_audit(self):
        old = self.before.copy()
        init = old[3].split()
        offset = init.index(str(GLOBAL_BASE + self.old_vars.index('g_multiplayer_game_type')))
        self.assertEqual(init[offset + 1], '7')
        init[offset + 1] = '6'
        old[3] = ' '.join(init)
        result = self.inspect(old=old)
        self.assertFalse(result['checks']['original_invasion_mode_initialization'])

    def test_original_round_restart_resets_wave_counter(self):
        g_wave = GLOBAL_BASE + self.old_vars.index('wave_number')
        for idx in (7, 10):
            with self.subTest(trigger=idx):
                _, operations = decode_trigger(self.before[idx])
                self.assertIn((2133, (g_wave, 0)), operations)
        self.assertTrue(self.inspect()['checks']['original_wave_resets_between_rounds'])

    def test_reinforcement_guard_handles_second_round_before_previous_max(self):
        g_wave = GLOBAL_BASE + self.old_vars.index('wave_number')
        g_last = GLOBAL_BASE + self.new_vars.index('zdr_last_reinforced_wave')
        g_round = GLOBAL_BASE + self.old_vars.index('g_round_start_time')
        g_stamp = GLOBAL_BASE + self.new_vars.index(ROUND_STAMP)
        conditions, effects = decode_trigger(self.after[28])
        self.assertIn((ROUND_OR_WAVE_CHANGED, (g_round, g_stamp)), conditions)
        self.assertIn((WAVE_CHANGED, (g_wave, g_last)), conditions)
        self.assertIn((2133, (g_last, g_wave)), effects)
        self.assertIn((2133, (g_stamp, g_round)), effects)
        sentinel, last_round = 0, -1
        attempts = []
        # The original mission resets wave_number to zero between rounds.
        # Crucial equal-last-wave case: each round can end at the same wave.
        for round_number, wave in [(1, 2), (1, 2), (1, 3), (1, 4),
                                   (2, 0), (2, 1), (2, 2), (2, 2), (2, 3),
                                   (3, 0), (3, 2), (3, 2)]:
            if wave >= 2 and (round_number != last_round or wave != sentinel):
                sentinel, last_round = wave, round_number
                attempts.append((round_number, wave))
        self.assertEqual(attempts, [(1, 2), (1, 3), (1, 4), (2, 2),
                                    (2, 3), (3, 2)])

    def test_missing_round_identity_guard_is_rejected(self):
        round_start = GLOBAL_BASE + self.old_vars.index('g_round_start_time')
        stamp = GLOBAL_BASE + self.new_vars.index(ROUND_STAMP)
        marker = f'{ROUND_OR_WAVE_CHANGED} 2 {round_start} {stamp}'
        changed = self.after.copy()
        self.assertIn(marker, changed[28])
        changed[28] = changed[28].replace(marker,
            f'{WAVE_CHANGED} 2 {round_start} {stamp}', 1)
        self.assertFalse(self.inspect(new=changed)['checks']['reinforcement_once_per_wave'])

    def test_old_strict_gt_guard_is_rejected(self):
        g_wave = GLOBAL_BASE + self.old_vars.index('wave_number')
        g_last = GLOBAL_BASE + self.new_vars.index('zdr_last_reinforced_wave')
        original_neq = f'{WAVE_CHANGED} 2 {g_wave} {g_last}'
        changed = self.after.copy()
        self.assertIn(original_neq, changed[28])
        changed[28] = changed[28].replace(original_neq,
                                         f'32 2 {g_wave} {g_last}', 1)
        self.assertFalse(self.inspect(new=changed)['checks']['reinforcement_once_per_wave'])

    def test_original_reset_removal_is_rejected(self):
        g_wave = GLOBAL_BASE + self.old_vars.index('wave_number')
        original = self.before.copy()
        marker = f'2133 2 {g_wave} 0'
        self.assertIn(marker, original[10])
        original[10] = original[10].replace(marker, f'2133 2 {g_wave} 1', 1)
        self.assertFalse(self.inspect(old=original)['checks']['original_wave_resets_between_rounds'])

    def test_wrong_visitor_team_is_rejected(self):
        changed = self.after.copy()
        # Multiplayer add_visitors_to_current_scene: (entry,troop,1,team0,group 5..7).
        changed[28], replacements = re.subn(
            r'(1265 5 [01] \d+ 1) 0 ([567])', r'\1 1 \2', changed[28], count=1)
        self.assertEqual(replacements, 1)
        result = self.inspect(new=changed)
        self.assertFalse(result['checks']['reinforcement_visitors_team_and_groups'])


if __name__ == '__main__':
    unittest.main()
