"""Source-grounded City-only invasion checks; no WSE2 runtime claims.

Only the historical City SCO is staged. If any patch accidentally demands or
writes Granny's House, Bridge, Shipyard or Abandoned Town, this test fails.
"""
import os
from pathlib import Path
import shutil
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
from patch_defenders import patch_file, mission_bounds
from city_defense import apply_module as city_defense, scene_index, SCENE_BASE
from wave_reinforcements import apply_module as wave_topups, LOCAL_BASE
from tactical_recovery import apply_module as recovery
from trace_calls import read_mission_calls

ORIGINAL = Path(os.environ.get("ZOMBIEEE_ORIGINAL_MODULE",
                               "/mnt/data/zombie04_inspect/ZOMBIEEE"))


@unittest.skipUnless(ORIGINAL.is_dir(), "Set ZOMBIEEE_ORIGINAL_MODULE to original Beta 0.4")
class CityOnlyIntegration(unittest.TestCase):
    def stage_city(self, root):
        (root / "SceneObj").mkdir()
        for name in ("troops.txt", "scenes.txt", "variables.txt", "mission_templates.txt"):
            shutil.copy2(ORIGINAL / name, root / name)
        original_city = ORIGINAL / "SceneObj" / "scn_tbfc_invasion_4.sco"
        shutil.copy2(original_city, root / "SceneObj" / original_city.name)
        return (root / "mission_templates.txt").read_bytes()

    def test_city_full_patch_chain_without_other_scene_files(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            original_mission = self.stage_city(root)
            patch_file(root, 4, city_only=True)
            city_defense(root)
            wave = wave_topups(root, cap=4, city_only=True)
            tactical = recovery(root, city_only=True)
            self.assertTrue(wave["city_only"])
            self.assertTrue(tactical["city_only"])
            self.assertEqual(wave["final_trigger_count"], 29)
            self.assertEqual(tactical["final_trigger_count"], 31)
            self.assertEqual((root / "variables.txt").read_text().splitlines()[-2:],
                             ["zdr_last_reinforced_wave", "zdr_defence_mode"])
            result = (root / "mission_templates.txt").read_bytes().decode()
            before = original_mission.decode()
            p, count, _ = mission_bounds(result.splitlines(keepends=True))
            p_before, original_count, _ = mission_bounds(before.splitlines(keepends=True))
            self.assertEqual((original_count, count), (25, 31))
            self.assertEqual(result.splitlines()[p + 1:p + 26],
                             before.splitlines()[p_before + 1:p_before + 26])
            triggers = read_mission_calls(root / "mission_templates.txt")
            self.assertEqual(len(triggers), 31)
            scenes = list((root / "SceneObj").glob("*.sco"))
            self.assertEqual([p.name for p in scenes], ["scn_tbfc_invasion_4.sco"])
            self.assertNotEqual((root / "SceneObj" / scenes[0].name).read_bytes(),
                                (ORIGINAL / "SceneObj" / scenes[0].name).read_bytes())

    def test_city_only_wave_and_recovery_both_have_scene_checks(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            self.stage_city(root)
            patch_file(root, 4, city_only=True)
            city_defense(root)
            wave_topups(root, cap=4, city_only=True)
            recovery(root, city_only=True)
            text = (root / "mission_templates.txt").read_text()
            rows = text.splitlines()
            p, count, _ = mission_bounds(text.splitlines(keepends=True))
            self.assertEqual(count, 31)
            city = SCENE_BASE + scene_index(root / "scenes.txt")
            # Initial ally spawn (25), wave top-up (28), and tactical
            # recovery (30) must all reject non-City map scenes.
            for index in (25, 28, 30):
                parts = rows[p + 1 + index].split()
                conditions = int(parts[3])
                cursor = 4
                encoded = []
                for _ in range(conditions):
                    op, argc = int(parts[cursor]), int(parts[cursor + 1])
                    cursor += 2
                    encoded.append((op, tuple(int(x) for x in parts[cursor:cursor + argc])))
                    cursor += argc
                self.assertIn((2211, (LOCAL_BASE + 8,)), encoded)
                self.assertIn((31, (LOCAL_BASE + 8, city)), encoded)

    def test_all_maps_not_required_to_apply_city_waves(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            self.stage_city(root)
            patch_file(root, 3, city_only=True)
            city_defense(root)
            wave_topups(root, cap=3, city_only=True)
            _, count, _ = mission_bounds((root / "mission_templates.txt").read_text().splitlines(keepends=True))
            self.assertEqual(count, 29)

    def test_original_city_scene_asset_is_unchanged_at_source(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            city = ORIGINAL / "SceneObj" / "scn_tbfc_invasion_4.sco"
            source_bytes = city.read_bytes()
            self.stage_city(root)
            patch_file(root, 4, city_only=True)
            city_defense(root)
            self.assertEqual(city.read_bytes(), source_bytes)

    def test_city_guard_orders_reject_wrong_original_scene(self):
        from city_defense import patch_orders
        from patch_defenders import patch_text as initial_patch, index_troops
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            self.stage_city(root)
            city_id = scene_index(root / "scenes.txt")
            troops = index_troops(root / "troops.txt")
            compiled = initial_patch((root / "mission_templates.txt").read_text(),
                                     troops, 4, city_scene=city_id)
            # City-only guard orders accept the source.
            allowed = patch_orders(compiled, city_id)
            self.assertEqual(mission_bounds(allowed.splitlines(keepends=True))[1], 27)
            # A different scene ID must not silently redirect survivor bots.
            with self.assertRaisesRegex(ValueError, "incorrectly scoped"):
                patch_orders(compiled, city_id + 1)


if __name__ == "__main__":
    unittest.main()
