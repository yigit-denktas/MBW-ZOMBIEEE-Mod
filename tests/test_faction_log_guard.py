"""Trigger-14 invalid-faction log guard tests."""
import os
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
from faction_log_guard import (FactionLogGuardError, INVADER_FACTION,
                               UNUSED_SLOT, patch_mission_text)
from faction_log_guard_prefix import original_prefix_ok, trigger_guard_diff
from ai_wave_contract import decode_trigger
from patch_defenders import mission_bounds

ORIGINAL = Path(os.environ.get("ZOMBIEEE_ORIGINAL_MODULE",
                               "C:/Users/yigit/Documents/repos/MBW-ZOMBIEEE-Mod/local/original-beta04/ZOMBIEEE"))
MISSION = ORIGINAL / "mission_templates.txt"


def rows(text):
    lines = text.splitlines(keepends=True)
    p, count, end = mission_bounds(lines)
    return [line.strip() for line in lines[p + 1:end]]


@unittest.skipUnless(MISSION.is_file(), "original module not available")
class FactionLogGuardTests(unittest.TestCase):
    def test_only_four_trailing_trigger14_ops_change(self):
        original = MISSION.read_text(encoding="utf-8")
        guarded, report = patch_mission_text(original)
        self.assertEqual(report["replaced_ops"], 4)
        self.assertFalse(report["wave_composition_changed"])
        before = rows(original)
        after = rows(guarded)
        self.assertTrue(all(a == b for i, (a, b) in enumerate(zip(before, after))
                            if i != 14))
        self.assertEqual(len(after), len(before))
        tail = decode_trigger(after[14])[1][-4:]
        for op, args in tail:
            self.assertEqual(op, 502)
            self.assertEqual(args[0], INVADER_FACTION)
            self.assertEqual(args[1], UNUSED_SLOT)
        self.assertTrue(trigger_guard_diff(before[14], after[14]))
        self.assertTrue(original_prefix_ok(after, before))

    def test_unexpected_shape_rejected(self):
        text = MISSION.read_text(encoding="utf-8")
        corrupted = text.replace("502 3 -1 200", "502 3 -1 201", 1)
        with self.assertRaises(FactionLogGuardError):
            patch_mission_text(corrupted)


if __name__ == "__main__":
    unittest.main()
