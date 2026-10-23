"""Source-grounded AI-only loadout and reinforcement checks."""
import os
from pathlib import Path
import sys
import tempfile
import unittest
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
from bot_loadouts import patch_text as clone_loadouts, CLONES, LOADOUTS, index_items
from patch_defenders import index_troops, patch_text as allies, PatchError, mission_bounds
from wave_reinforcements import reinforce_on_wave, globals_from_original

ORIGINAL = Path(os.environ.get("ZOMBIEEE_ORIGINAL_MODULE",
                               "/mnt/data/zombie04_inspect/ZOMBIEEE"))


@unittest.skipUnless(ORIGINAL.is_dir(), "Set ZOMBIEEE_ORIGINAL_MODULE to extracted original Beta 0.4")
class BotLoadoutTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.base_troops = (ORIGINAL / "troops.txt").read_bytes().decode("utf-8")
        cls.items = (ORIGINAL / "item_kinds1.txt").read_bytes().decode("utf-8")
        cls.mission = (ORIGINAL / "mission_templates.txt").read_bytes().decode("utf-8")

    def test_four_ai_variants_keep_original_prefix_intact(self):
        changed, report = clone_loadouts(self.base_troops, self.items)
        self.assertEqual(report["patched_count"], 985)
        self.assertEqual(changed.splitlines()[2:6868], self.base_troops.splitlines()[2:])
        self.assertEqual(len([x for x in changed.splitlines() if x.startswith("trp_")]), 985)
        with self.assertRaises(PatchError):
            clone_loadouts(changed, self.items)

    def test_original_player_classes_keep_equipment_and_numbers(self):
        changed, _ = clone_loadouts(self.base_troops, self.items)
        original = [x for x in self.base_troops.splitlines() if x.startswith("trp_")]
        updated = [x for x in changed.splitlines() if x.startswith("trp_")]
        self.assertEqual(original, updated[:981])
        self.assertEqual(updated[981:985], [
            x for x in updated if x.split()[0] in CLONES])

    def test_four_clones_equipped_only_with_original_items(self):
        changed, _ = clone_loadouts(self.base_troops, self.items)
        names = index_items(self.items)
        rows = changed.splitlines()
        for clone, expected in zip(CLONES, LOADOUTS):
            with self.subTest(clone=clone):
                head = next(i for i, line in enumerate(rows) if line.startswith(clone + " "))
                pairs = list(map(int, rows[head + 1].split()))
                self.assertEqual(len(pairs), 128)
                self.assertEqual(pairs[::2][:len(expected)], [names[n] for n in expected])
                self.assertTrue(all(n == -1 for n in pairs[::2][len(expected):]))
                self.assertTrue(all(n == 0 for n in pairs[1::2]))

    def test_allied_spawn_points_to_new_ai_troops(self):
        changed, _ = clone_loadouts(self.base_troops, self.items)
        with tempfile.TemporaryDirectory() as td:
            path = Path(td)/"troops.txt"
            path.write_text(changed, newline="")
            troop_ids = index_troops(path)
        output = allies(self.mission, troop_ids, 4, CLONES)
        self.assertEqual(mission_bounds(output.splitlines(keepends=True))[1], 26)
        trigger = output.splitlines()[mission_bounds(output.splitlines(keepends=True))[2] - 1]
        for name in CLONES:
            self.assertIn(str(360287970189639680 + troop_ids[name]), trigger)

    def test_reinforcement_uses_wave_plus_replacement_rotation(self):
        g = globals_from_original((ORIGINAL/"variables.txt").read_text())
        changed, _ = clone_loadouts(self.base_troops, self.items)
        with tempfile.TemporaryDirectory() as td:
            path = Path(td)/"troops.txt"
            path.write_text(changed, newline="")
            ids = index_troops(path)
        trigger = reinforce_on_wave(g, ids, 4, CLONES)
        self.assertIn("2120 3", trigger)
        self.assertIn("2119 3", trigger)
        for troop in CLONES:
            self.assertIn(str(360287970189639680 + ids[troop]), trigger)

    def test_unknown_or_corrupt_items_rejected(self):
        with self.assertRaises(PatchError):
            clone_loadouts(self.base_troops, self.items.replace("itemsfile version 3", "itemsfile version 8"))
        with self.assertRaises(PatchError):
            clone_loadouts(self.base_troops, self.items.replace("itm_m16a2 ", "itm_missing_m16a2 ", 1))


if __name__ == "__main__":
    unittest.main()
