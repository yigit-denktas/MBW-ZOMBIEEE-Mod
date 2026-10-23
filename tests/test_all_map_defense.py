"""Navmesh-derived multi-map overlay tests, offline on user-provided original Beta 0.4."""
import os
from pathlib import Path
import shutil
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
from patch_defenders import index_troops, patch_text as ally, mission_bounds, PatchError
from city_defense import patch_orders as city_orders, scene_index
from scene_tactics import plan_city, apply_city_overlay, decode_scene
from map_blueprints import blueprint
from all_map_defense import add_markers, apply_module
ORIGINAL = Path(os.environ.get("ZOMBIEEE_ORIGINAL_MODULE", "/missing/ZOMBIEEE"))


@unittest.skipUnless(ORIGINAL.is_dir(), "Set ZOMBIEEE_ORIGINAL_MODULE to extracted original mod")
class AllMapDefenseTests(unittest.TestCase):
    def test_five_map_blueprints(self):
        for number in range(1,6):
            with self.subTest(map=number):
                data=(ORIGINAL/"SceneObj"/f"scn_tbfc_invasion_{number}.sco").read_bytes()
                plan=blueprint(data,number)
                self.assertEqual(len(plan["positions"]),3)
                self.assertEqual(plan["entry_ids"],[2,3,4] if number==4 else [41,42,43])
                if number!=4:
                    changed=add_markers(data,plan["entry_ids"],plan["positions"])
                    self.assertEqual(len(decode_scene(changed)["objects"]),
                                     len(decode_scene(data)["objects"])+3)
                    self.assertEqual(decode_scene(changed)["faces"],decode_scene(data)["faces"])

    def test_full_original_copy_then_five_map_patch(self):
        with tempfile.TemporaryDirectory() as temp:
            folder=Path(temp);(folder/"SceneObj").mkdir()
            for filename in ("scenes.txt","troops.txt","mission_templates.txt"):
                shutil.copy2(ORIGINAL/filename,folder/filename)
            for number in range(1,6):
                name=f"scn_tbfc_invasion_{number}.sco"
                shutil.copy2(ORIGINAL/"SceneObj"/name,folder/"SceneObj"/name)
            mission=folder/"mission_templates.txt"
            source=mission.read_bytes().decode("utf-8")
            source=ally(source,index_troops(folder/"troops.txt"),4)
            source=city_orders(source,scene_index(folder/"scenes.txt"))
            mission.write_bytes(source.encode("utf-8"))
            city=folder/"SceneObj"/"scn_tbfc_invasion_4.sco"
            orig=city.read_bytes()
            city.write_bytes(apply_city_overlay(orig,plan_city(orig)))
            output=apply_module(folder)
            self.assertEqual(output["final_trigger_count"],27)
            self.assertEqual(mission_bounds(mission.read_text().splitlines(keepends=True))[1],27)
            for number in range(1,6):
                name=f"scn_tbfc_invasion_{number}.sco"
                after=decode_scene((folder/"SceneObj"/name).read_bytes())
                before=decode_scene((ORIGINAL/"SceneObj"/name).read_bytes())
                self.assertEqual(before["vertices"],after["vertices"])
                new_ids={2,3,4} if number==4 else {41,42,43}
                self.assertTrue(new_ids.issubset({o["entry"] for o in after["objects"] if o["type"]==1}))
            with self.assertRaises(Exception):
                apply_module(folder)


if __name__ == "__main__":
    unittest.main()
