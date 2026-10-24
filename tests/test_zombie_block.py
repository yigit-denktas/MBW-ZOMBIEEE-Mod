"""City invader shield/block profile: only native Zombie troops are touched."""
import os
from pathlib import Path
import shutil
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
from zombie_block import (INVADER_RANGE, SHIELD_ITEM, ZombieBlockError,
                          apply_module, shield_id)

ORIGINAL = Path(os.environ.get("ZOMBIEEE_ORIGINAL_MODULE", "/missing/ZOMBIEEE"))


@unittest.skipUnless(ORIGINAL.is_dir(), "Owned original module required")
class ZombieBlockTests(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.module = Path(temp.name)
        for name in ("troops.txt", "item_kinds1.txt"):
            shutil.copy2(ORIGINAL / name, self.module / name)
        self.before = (self.module / "troops.txt").read_text(encoding="utf-8").splitlines()
        self.shield = shield_id(self.module)

    def _rows(self):
        return (self.module / "troops.txt").read_text(encoding="utf-8").splitlines()

    def test_apply_adds_shield_only_to_invader_block(self):
        report = apply_module(self.module)
        self.assertTrue(report["applied"])
        self.assertEqual(report["shield_item"], SHIELD_ITEM)
        self.assertEqual(report["changed_count"], INVADER_RANGE[1] - INVADER_RANGE[0])
        after = self._rows()
        self.assertEqual(len(self.before), len(after))
        troop = -1
        for old, new in zip(self.before, after):
            if old.strip().startswith("trp_"):
                troop += 1
            if old != new:
                self.assertTrue(INVADER_RANGE[0] <= troop < INVADER_RANGE[1],
                                f"changed non-invader troop {troop}")
        equipment = []
        troop = -1
        for index, line in enumerate(after):
            if line.strip().startswith("trp_"):
                troop += 1
                if INVADER_RANGE[0] <= troop < INVADER_RANGE[1]:
                    if index + 1 >= len(after):
                        self.fail("missing equipment line")
                    equipment.append(after[index + 1])
        self.assertEqual(len(equipment), INVADER_RANGE[1] - INVADER_RANGE[0])
        for line in equipment:
            tokens = line.split()
            pairs = list(zip(tokens[0::2], tokens[1::2]))
            self.assertIn(str(self.shield), [p[0] for p in pairs])
        # Skill word 3, shield nibble (skill 26): every invader must be >=5.
        troop = -1
        for index, line in enumerate(after):
            if line.strip().startswith("trp_"):
                troop += 1
                if not INVADER_RANGE[0] <= troop < INVADER_RANGE[1]:
                    continue
                words = [int(w) for w in after[index + 4].split()]
                self.assertEqual(len(words), 6)
                shield_skill = (words[3] >> 8) & 0xF
                self.assertGreaterEqual(shield_skill, 5)
        self.assertNotEqual(report["sha256_before"], report["sha256_after"])

    def test_second_apply_is_idempotent(self):
        first = apply_module(self.module)
        after_first = (self.module / "troops.txt").read_text(encoding="utf-8")
        second = apply_module(self.module)
        self.assertTrue(second["applied"])
        self.assertEqual((self.module / "troops.txt").read_text(encoding="utf-8"), after_first)
        self.assertNotEqual(first["sha256_before"], first["sha256_after"])

    def test_missing_shield_item_fails_closed(self):
        text = (self.module / "item_kinds1.txt").read_text(encoding="utf-8")
        self.module.joinpath("item_kinds1.txt").write_text(
            text.replace(" itm_wooden_shield ", " itm_renamed_shield "), encoding="utf-8")
        with self.assertRaises(ZombieBlockError):
            apply_module(self.module)


if __name__ == "__main__":
    unittest.main()
