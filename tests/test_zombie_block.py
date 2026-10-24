"""Canonical invader shield policy tests (task-83)."""
import os
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
from zombie_block import (INVADER_RANGE, ORIGINAL_SHIELD, PRACTICE_SHIELD,
                          WOODEN_SHIELD, ZombieBlockError, apply_module, item_ids)

ORIGINAL = Path(os.environ.get("ZOMBIEEE_ORIGINAL_MODULE", "/missing/ZOMBIEEE"))
SKILL_WORD = 3
SHIELD_SHIFT = 8


@unittest.skipUnless(ORIGINAL.is_dir(), "Owned original module required")
class ZombieBlockTests(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.module = Path(temp.name)
        for name in ("troops.txt", "item_kinds1.txt"):
            shutil.copy2(ORIGINAL / name, self.module / name)
        self.before = (self.module / "troops.txt").read_text(encoding="utf-8").splitlines()
        self.ids = item_ids(self.module)

    def _rows(self):
        return (self.module / "troops.txt").read_text(encoding="utf-8").splitlines()

    def _invader_indexes(self, rows):
        troop = -1
        result = []
        for index, line in enumerate(rows):
            if line.strip().startswith("trp_"):
                troop += 1
                if INVADER_RANGE[0] <= troop < INVADER_RANGE[1]:
                    result.append((troop, index))
        return result

    def test_stock_removes_all_shields_and_zero_skill(self):
        report = apply_module(self.module, "stock")
        self.assertTrue(report["applied"])
        self.assertEqual(report["mode"], "stock")
        self.assertEqual(report["gate"], "passed")
        self.assertEqual(report["wooden_shield_troops"], [])
        after = self._rows()
        self.assertEqual(len(self.before), len(after))
        removed = {str(self.ids[name]) for name in
                   (WOODEN_SHIELD, PRACTICE_SHIELD, ORIGINAL_SHIELD)}
        for troop, index in self._invader_indexes(after):
            pairs = after[index + 1].split()
            items = {pairs[i] for i in range(0, len(pairs), 2)}
            self.assertFalse(items & removed, f"shield remains on troop {troop}")
            words = [int(w) for w in after[index + 4].split()]
            self.assertEqual((words[SKILL_WORD] >> SHIELD_SHIFT) & 0xF, 0)

    def test_cosmetic_half_only_alternate_practice_shield_skill_zero(self):
        report = apply_module(self.module, "cosmetic-half")
        self.assertEqual(report["gate"], "passed")
        self.assertEqual(len(report["cosmetic_troops"]), 9)
        after = self._rows()
        practice = str(self.ids[PRACTICE_SHIELD])
        wooden = str(self.ids[WOODEN_SHIELD])
        for troop, index in self._invader_indexes(after):
            pairs = after[index + 1].split()
            items = {pairs[i] for i in range(0, len(pairs), 2)}
            self.assertNotIn(wooden, items)
            expected = (troop - INVADER_RANGE[0]) % 2 == 0
            self.assertEqual(practice in items, expected, f"troop {troop}")
            words = [int(w) for w in after[index + 4].split()]
            self.assertEqual((words[SKILL_WORD] >> SHIELD_SHIFT) & 0xF, 0)

    def test_stock_twice_is_idempotent(self):
        apply_module(self.module, "stock")
        first = (self.module / "troops.txt").read_text(encoding="utf-8")
        report = apply_module(self.module, "stock")
        self.assertEqual(report["changed_count"], 0)
        self.assertEqual((self.module / "troops.txt").read_text(encoding="utf-8"), first)

    def test_missing_shield_item_fails_closed(self):
        text = (self.module / "item_kinds1.txt").read_text(encoding="utf-8")
        self.module.joinpath("item_kinds1.txt").write_text(
            text.replace(" itm_practice_shield ", " itm_renamed_shield "),
            encoding="utf-8")
        with self.assertRaises(ZombieBlockError):
            apply_module(self.module, "cosmetic-half")


if __name__ == "__main__":
    unittest.main()
