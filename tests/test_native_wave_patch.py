"""P0 native wave-controller patch tests (speed loop disabled for crash bisect)."""
import os
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
from native_wave_patch import (NativeWavePatchError, _decode, _local,
                               _speed_ops, patch_mission_text)
from patch_defenders import mission_bounds
from ai_wave_contract import decode_trigger

ORIGINAL = Path(os.environ.get("ZOMBIEEE_ORIGINAL_MODULE", "/mnt/data/zombieee"))
LOCAL0 = 1224979098644774912


@unittest.skipUnless(ORIGINAL.is_dir(), "original module not available")
class NativeWavePatchTests(unittest.TestCase):
    def setUp(self):
        self.text = (ORIGINAL / "mission_templates.txt").read_text(encoding="utf-8")
        variables = (ORIGINAL / "variables.txt").read_text(encoding="utf-8").splitlines()
        self.wave_global = 144115188075855872 + variables.index("wave_number")

    def _rows(self, text):
        lines = text.splitlines(keepends=True)
        p, count, end = mission_bounds(lines)
        return [line.strip() for line in lines[p + 1:end]]

    def test_trigger14_table_894_and_speed_loop_disabled(self):
        out, report = patch_mission_text(self.text, self.wave_global)
        self.assertTrue(report["trigger14_wave_table_patched"])
        self.assertFalse(report["trigger15_speed_loop_appended"])
        self.assertTrue(report["speed_loop_disabled_for_bisect"])
        self.assertEqual(report["invalid_faction_writes_guarded"], 4)
        rows = self._rows(out)
        t14 = decode_trigger(rows[14])[1]
        slots = [args for op, args in t14
                 if op == 502 and args[0] == 432345564227567632
                 and 200 <= args[1] <= 244]
        self.assertTrue(slots)
        self.assertTrue(all(args[2] == 360287970189639680 + 894 for args in slots))
        t15 = decode_trigger(rows[15])[1]
        self.assertFalse(any(op == 2093 for op, _ in t15))

    def test_speed_ops_operands_and_locals_when_enabled(self):
        original_ops = _decode(self._rows(self.text)[15])[2]
        max_local = max(a for _op, args in original_ops for a in args
                        if LOCAL0 <= a < LOCAL0 + 64)
        ops = _speed_ops(self.wave_global)
        mult = [(op, args) for op, args in ops if op == 2122]
        self.assertTrue(mult)
        self.assertTrue(all(args[1] == self.wave_global and args[2] == 4
                            for _op, args in mult))
        self.assertFalse(any(op == 2123 for op, _ in ops))
        used = {a for _op, args in ops for a in args if LOCAL0 <= a < LOCAL0 + 64}
        self.assertGreater(min(used), max_local)
        self.assertTrue(any(op == 2093 for op, _ in ops))

    def test_double_patch_is_rejected(self):
        out, _ = patch_mission_text(self.text, self.wave_global)
        with self.assertRaises(NativeWavePatchError):
            patch_mission_text(out, self.wave_global)

    def test_chain_accepts_off_and_on_native_speed_stages(self):
        import tempfile
        from verify_city_chain import mission_check, stage_source
        for speed_loop in (False, True):
            with tempfile.TemporaryDirectory() as td:
                stage = Path(td)
                stage_source(ORIGINAL, stage, speed_loop=speed_loop)
                result = mission_check(stage, ORIGINAL, 25)
                self.assertTrue(result["original_25_triggers_unchanged"])


if __name__ == "__main__":
    unittest.main()
