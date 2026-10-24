"""P0 native wave-controller patch and visitor-argument tests."""
import os
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
from native_wave_patch import patch_mission_text
from patch_defenders import mission_bounds
from ai_wave_contract import decode_trigger

ORIGINAL = Path(os.environ.get("ZOMBIEEE_ORIGINAL_MODULE", "/mnt/data/zombieee"))


@unittest.skipUnless(ORIGINAL.is_dir(), "original module not available")
class NativeWavePatchTests(unittest.TestCase):
    def test_trigger14_table_894_and_trigger15_speed_appended(self):
        text = (ORIGINAL / "mission_templates.txt").read_text(encoding="utf-8")
        variables = (ORIGINAL / "variables.txt").read_text(encoding="utf-8").splitlines()
        wave_global = 144115188075855872 + variables.index("wave_number")
        out, report = patch_mission_text(text, wave_global)
        self.assertTrue(report["trigger14_wave_table_patched"])
        self.assertTrue(report["trigger15_speed_loop_appended"])
        self.assertEqual(report["invalid_faction_writes_guarded"], 4)
        lines = out.splitlines(keepends=True)
        p, count, end = mission_bounds(lines)
        rows = [line.strip() for line in lines[p + 1:end]]
        t14 = decode_trigger(rows[14])[1]
        slots = [args for op, args in t14
                 if op == 502 and args[0] == 432345564227567632
                 and 200 <= args[1] <= 244]
        self.assertTrue(slots)
        self.assertTrue(all(args[2] == 360287970189639680 + 894 for args in slots))
        t15 = decode_trigger(rows[15])[1]
        self.assertTrue(any(op == 2093 for op, _ in t15))


if __name__ == "__main__":
    unittest.main()
