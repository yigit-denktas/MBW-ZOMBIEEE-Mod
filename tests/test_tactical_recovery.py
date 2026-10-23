"""Native tactical recovery tests. Engine movement remains unverified."""
import os
from pathlib import Path
import shutil
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
from patch_defenders import index_troops, patch_text as patch_defenders, mission_bounds, PatchError
from city_defense import scene_index, apply_module as city_apply
from all_map_defense import apply_module as all_apply
from wave_reinforcements import apply_module as wave_apply
from tactical_recovery import apply_module, mapping, recovery_trigger, TACTICAL_GLOBAL
from scene_tactics import decode_scene
from trace_calls import read_mission_calls

ORIGINAL = Path(os.environ.get("ZOMBIEEE_ORIGINAL_MODULE", "/not-mounted/ZOMBIEEE"))


@unittest.skipUnless(ORIGINAL.is_dir(), "Supply extracted original Beta 0.4 using ZOMBIEEE_ORIGINAL_MODULE")
class TacticalRecoveryTests(unittest.TestCase):
    def stage_original(self, root):
        (root / "SceneObj").mkdir()
        for name in ("troops.txt", "scenes.txt", "variables.txt", "mission_templates.txt"):
            shutil.copy2(ORIGINAL / name, root / name)
        for number in range(1, 6):
            name = f"scn_tbfc_invasion_{number}.sco"
            shutil.copy2(ORIGINAL / "SceneObj" / name, root / "SceneObj" / name)
        mission = root / "mission_templates.txt"
        mission.write_bytes(patch_defenders(
            mission.read_bytes().decode("utf-8"), index_troops(root / "troops.txt"), 4).encode("utf-8"))
        city_apply(root)
        all_apply(root)
        wave_apply(root, 4)

    def test_complete_original_pipeline_and_trigger_prefix(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            self.stage_original(root)
            before = (root / "mission_templates.txt").read_bytes().decode("utf-8")
            info = apply_module(root)
            after = (root / "mission_templates.txt").read_bytes().decode("utf-8")
            names = (root / "variables.txt").read_text().splitlines()
            self.assertEqual(info["final_trigger_count"], 31)
            self.assertEqual((len(names), names[-1]), (1222, TACTICAL_GLOBAL))
            p, n, end = mission_bounds(after.splitlines(keepends=True))
            self.assertEqual(n, 31)
            self.assertEqual(after.splitlines()[p + 1:p + 1 + 29],
                             before.splitlines()[p + 1:p + 1 + 29])
            self.assertEqual(before.splitlines()[:p], after.splitlines()[:p])
            self.assertEqual(len(read_mission_calls(root / "mission_templates.txt")), 31)
            for number in range(1, 6):
                name = f"scn_tbfc_invasion_{number}.sco"
                a = decode_scene((ORIGINAL / "SceneObj" / name).read_bytes())
                b = decode_scene((root / "SceneObj" / name).read_bytes())
                self.assertEqual(a["vertices"], b["vertices"])
                self.assertEqual(a["faces"], b["faces"])
            with self.assertRaises(PatchError):
                apply_module(root)

    def test_recovery_is_server_only_and_divisions_isolated(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            self.stage_original(root)
            scene_ids = {i: scene_index(root / "scenes.txt", f"scn_tbfc_invasion_{i}")
                         for i in range(1, 6)}
            g = mapping((root / "variables.txt").read_text())
            trigger = recovery_trigger(g, scene_ids).split()
            self.assertEqual(trigger[:4], ["3.000000", "0.000000", "0.000000", "4"])
            self.assertIn("417", trigger)  # server only
            self.assertIn("1765", trigger)  # agent group
            self.assertIn("33", trigger)  # between 5 and 8
            self.assertEqual(trigger.count("1791"), 18)
            self.assertEqual(trigger.count("1790"), 18)
            self.assertEqual(trigger.count("1780"), 16)

    def test_invalid_recovery_thresholds_rejected(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            self.stage_original(root)
            scene_ids = {i: scene_index(root / "scenes.txt", f"scn_tbfc_invasion_{i}")
                         for i in range(1, 6)}
            g = mapping((root / "variables.txt").read_text())
            for low, high in ((-1, 3), (2, 2), (3, 2), (1, 9)):
                with self.subTest(low=low, high=high):
                    with self.assertRaises(PatchError):
                        recovery_trigger(g, scene_ids, low, high)


if __name__ == "__main__":
    unittest.main()
