"""Source-based private commands and difficulty patch regression tests."""
import os
from pathlib import Path
import shutil
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
from difficulty import profile, PROFILES
from patch_defenders import PatchError, mission_bounds, patch_file
from bot_loadouts import apply_module as ai_loadouts
from city_defense import apply_module as city_defense
from all_map_defense import apply_module as all_maps
from wave_reinforcements import apply_module as wave_topups
from tactical_recovery import apply_module as recovery
from private_commands import COUNTERS, build_hotkey, patch_text, apply_module, GLOBAL_BASE
from trace_calls import read_mission_calls

ORIGINAL = Path(os.environ.get("ZOMBIEEE_ORIGINAL_MODULE",
                               "/mnt/data/zombie04_inspect/ZOMBIEEE"))


@unittest.skipUnless(ORIGINAL.is_dir(), "Set ZOMBIEEE_ORIGINAL_MODULE to the original extracted module")
class PrivateCommandsTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.original_mission = (ORIGINAL / "mission_templates.txt").read_bytes().decode()

    def stage(self, root):
        (root / "SceneObj").mkdir()
        for name in ("troops.txt", "scenes.txt", "variables.txt", "mission_templates.txt", "item_kinds1.txt"):
            shutil.copy2(ORIGINAL / name, root / name)
        for n in range(1, 6):
            filename = f"scn_tbfc_invasion_{n}.sco"
            shutil.copy2(ORIGINAL / "SceneObj" / filename, root / "SceneObj" / filename)
        ai_loadouts(root)
        patch_file(root, 4, balanced_ai=True)
        city_defense(root)
        all_maps(root)
        wave_topups(root, cap=4, balanced_ai=True, first_wave=2)
        recovery(root, low_water=1, high_water=3)

    def test_true_source_patched_to_35_triggers_and_1226_globals(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            self.stage(root)
            before = (root / "mission_templates.txt").read_bytes().decode()
            report = apply_module(root)
            new = (root / "mission_templates.txt").read_bytes().decode()
            original = self.original_mission.splitlines()
            self.assertEqual(mission_bounds(new.splitlines(keepends=True))[1], 35)
            self.assertEqual(len(read_mission_calls(root / "mission_templates.txt")), 35)
            self.assertEqual(len((root / "variables.txt").read_text().splitlines()), 1226)
            self.assertEqual((root / "variables.txt").read_text().splitlines()[-3:], list(COUNTERS))
            self.assertEqual(report["max_active_players"], 1)
            self.assertEqual(report["dedicated_allowed"], False)
            self.assertEqual(report["trigger_additions"], 4)
            p_old, _, _ = mission_bounds(before.splitlines(keepends=True))
            p_new, _, _ = mission_bounds(new.splitlines(keepends=True))
            self.assertEqual(original[p_old+1:p_old+26], new.splitlines()[p_new+1:p_new+26])
            with self.assertRaises(PatchError):
                apply_module(root)

    def test_guards_and_actions_are_explicit(self):
        for key, effect, target in ((0x41, "heal", "1721"), (0x42, "ammo", "1728"),
                                     (0x43, "squad", "1721")):
            with self.subTest(effect=effect):
                op = build_hotkey(key, GLOBAL_BASE + 1223, effect).split()
                self.assertEqual(op[:4], ["0.000000", "0.000000", "0.000000", "4"])
                self.assertEqual(op[4:8], ["417", "0", "2147484066", "0"])
                self.assertIn("70", op)  # left Ctrl held
                self.assertIn("71", op)  # function key clicked
                self.assertIn("17", op)  # active player enumeration
                self.assertIn("415", op) # local host ID
                self.assertIn("401", op)
                self.assertIn("31", op)
                self.assertIn(target, op)
                self.assertNotIn("418 0", " ".join(op[:8]))  # not plain dedicated check

    def test_wrong_build_rejected(self):
        with self.assertRaises(PatchError):
            patch_text(self.original_mission,
                       (ORIGINAL / "variables.txt").read_text())

    def test_difficulty_profiles_are_explicit_and_ordered(self):
        self.assertEqual(list(PROFILES), ["story", "standard", "hard", "nightmare"])
        starts = [profile(n).first_reinforcement_wave for n in PROFILES]
        self.assertEqual(starts, [1, 2, 3, 4])
        for d in PROFILES.values():
            self.assertLess(d.fallback_at_or_below, d.regroup_at_or_above)
        with self.assertRaises(ValueError):
            profile("apocalypse-unknown")


if __name__ == "__main__":
    unittest.main()
