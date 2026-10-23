"""Source-grounded native solo-host assistance tests."""
import os
from pathlib import Path
import sys
import unittest
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
from solo_assist import patch_text, solo_assist_trigger
from patch_defenders import mission_bounds, PatchError

ORIGINAL = Path(os.environ.get("ZOMBIEEE_ORIGINAL_MODULE",
                               "/mnt/data/zombie04_inspect/ZOMBIEEE"))


class SoloAssistTests(unittest.TestCase):
    def test_opcodes_and_guards(self):
        tokens = solo_assist_trigger().split()
        self.assertEqual(tokens[:4], ["12.000000", "0.000000", "0.000000", "2"])
        self.assertEqual(tokens[4:8], ["417", "0", "2147484066", "0"])
        self.assertIn("17", tokens)    # enumerate players
        self.assertIn("401", tokens)   # player active
        self.assertIn("415", tokens)   # own player ID
        self.assertIn("406", tokens)   # local player -> agent
        self.assertIn("1702", tokens)  # alive only
        self.assertIn("1721", tokens)  # refill host HP
        self.assertIn("1728", tokens)  # refill host ammo
        self.assertNotIn("477", tokens)  # no anticheat disable

    def test_period_bounds(self):
        for period in (-1, 0, 2, 61, 600):
            with self.subTest(period=period):
                with self.assertRaises(PatchError):
                    solo_assist_trigger(period)

    @unittest.skipUnless(ORIGINAL.is_dir(), "Set ZOMBIEEE_ORIGINAL_MODULE")
    def test_baseline_only_and_no_double_application(self):
        original = (ORIGINAL / "mission_templates.txt").read_bytes().decode()
        patched, count = patch_text(original)
        self.assertEqual(count, 26)
        before = original.splitlines()
        after = patched.splitlines()
        p, n, end = mission_bounds(after)
        self.assertEqual(n, 26)
        self.assertEqual(after[p+1:p+26], before[p+1:p+26])
        with self.assertRaises(PatchError):
            patch_text(patched)
        with self.assertRaises(PatchError):
            patch_text(patched, period=30)

    @unittest.skipUnless(ORIGINAL.is_dir(), "Set ZOMBIEEE_ORIGINAL_MODULE")
    def test_unsupported_mission_count_fails(self):
        original = (ORIGINAL / "mission_templates.txt").read_bytes().decode()
        rows = original.splitlines(keepends=True)
        count_line, count, _ = mission_bounds(rows)
        self.assertEqual(count, 25)
        newline = "\r\n" if rows[count_line].endswith("\r\n") else "\n"
        rows[count_line] = "24" + newline
        with self.assertRaises(PatchError):
            patch_text("".join(rows))

    def test_compiled_body_sizes(self):
        parts = solo_assist_trigger().split()
        start = 4
        for _ in range(int(parts[3])):
            arity = int(parts[start + 1])
            start += 2 + arity
        count = int(parts[start]); start += 1
        for _ in range(count):
            arity = int(parts[start + 1])
            start += 2 + arity
        self.assertEqual(start, len(parts))


if __name__ == "__main__":
    unittest.main()
