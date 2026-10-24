"""Task-81 invader head-armor removal tests."""
import os
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
from zombie_head_armor import (HEAD_ARMOR_TYPE, INVADER_RANGE, apply_module,
                               head_armor_ids)

ORIGINAL = Path(os.environ.get("ZOMBIEEE_ORIGINAL_MODULE", "/missing/ZOMBIEEE"))


@unittest.skipUnless(ORIGINAL.is_dir(), "original module not available")
class HeadArmorTests(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.module = Path(temp.name)
        for name in ("troops.txt", "item_kinds1.txt"):
            shutil.copy2(ORIGINAL / name, self.module / name)

    def test_removes_all_invader_head_armor(self):
        before = (self.module / "item_kinds1.txt").read_text(encoding="utf-8")
        head_ids = head_armor_ids(self.module)
        report = apply_module(self.module, "removed")
        self.assertTrue(report["applied"])
        self.assertGreater(report["removed_pairs"], 0)
        self.assertEqual(report["remaining_head_armor_pairs"], 0)
        rows = (self.module / "troops.txt").read_text(encoding="utf-8").splitlines()
        troop = -1
        head_text = {str(value) for value in head_ids}
        for index, line in enumerate(rows):
            if not line.strip().startswith("trp_"):
                continue
            troop += 1
            if INVADER_RANGE[0] <= troop < INVADER_RANGE[1]:
                pairs = rows[index + 1].split()
                items = {pairs[i] for i in range(0, len(pairs), 2)}
                self.assertFalse(items & head_text, f"troop {troop}")
        # Item stats untouched.
        self.assertEqual((self.module / "item_kinds1.txt").read_text(encoding="utf-8"), before)

    def test_stock_leaves_head_armor(self):
        report = apply_module(self.module, "stock")
        self.assertEqual(report["removed_pairs"], 0)
        self.assertGreater(report["remaining_head_armor_pairs"], 0)


if __name__ == "__main__":
    unittest.main()
