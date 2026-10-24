"""Task-82 survivor crossbow/archery proficiency tests."""
import os
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
from bot_loadouts import patch_text as clone_loadouts
from survivor_proficiency import patch_text
from city_defense import REAR_HOLD_ENTRIES, orders_trigger

ORIGINAL = Path(os.environ.get("ZOMBIEEE_ORIGINAL_MODULE", "/mnt/data/zombieee"))


@unittest.skipUnless(ORIGINAL.is_dir(), "original module not available")
class SurvivorProficiencyTests(unittest.TestCase):
    def setUp(self):
        troops = (ORIGINAL / "troops.txt").read_text(encoding="utf-8")
        items = (ORIGINAL / "item_kinds1.txt").read_text(encoding="utf-8")
        self.with_clones, _ = clone_loadouts(troops, items)

    def test_all_four_clones_get_archery_and_crossbow_bonus(self):
        changed, report = patch_text(self.with_clones)
        self.assertTrue(report["applied"])
        self.assertEqual(report["firearm_class"], "crossbow_type_ranged")
        self.assertEqual(len(report["changed"]), 4)
        for row in report["changed"]:
            self.assertGreater(row["archery_after"], row["archery_before"])
            self.assertGreater(row["crossbow_after"], row["crossbow_before"])
        # The patched text must not change the four clone names/count.
        self.assertEqual(changed.count("trp_zdr_"), 4)

    def test_city_trigger_keeps_ranged_and_blocks_melee_chase(self):
        row = orders_trigger(0, wave_global=1209, hold_entries=REAR_HOLD_ENTRIES)
        tokens = row.split()
        for opcode in ("1790", "2092", "2094", "1737"):
            self.assertIn(opcode, tokens)
        self.assertNotIn("1730", tokens)  # no scripted charge destination
        for order in ("13", "16"):
            self.assertIn(order, tokens)  # fire_at_will / use_ranged

    def test_truncated_rows_rejected(self):
        with self.assertRaises(ValueError):
            patch_text("trp_zdr_commando_bot only-one-line\n")


if __name__ == "__main__":
    unittest.main()
