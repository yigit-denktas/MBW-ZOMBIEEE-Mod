"""Offline SCO and native City tactics tests. Original RAR never redistributed."""
import os
from pathlib import Path
import shutil
import sys
import tempfile
import unittest
import copy
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
from patch_defenders import PatchError, index_troops, patch_text, mission_bounds
from city_defense import apply_module, orders_trigger, patch_orders, scene_index
from scene_tactics import SceneError, decode_scene, plan_city, apply_city_overlay

ORIGINAL = Path(os.environ.get("ZOMBIEEE_ORIGINAL_MODULE", "/mnt/data/zombie04_inspect/ZOMBIEEE"))


class CityDefenseTests(unittest.TestCase):
    def setUp(self):
        if not ORIGINAL.is_dir():
            self.skipTest("Set ZOMBIEEE_ORIGINAL_MODULE to locally extracted original Beta 0.4")
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.module = Path(self.tmp.name)
        (self.module / "SceneObj").mkdir()
        for name in ("troops.txt", "scenes.txt", "mission_templates.txt"):
            shutil.copy2(ORIGINAL / name, self.module / name)
        shutil.copy2(ORIGINAL / "SceneObj" / "scn_tbfc_invasion_4.sco",
                     self.module / "SceneObj" / "scn_tbfc_invasion_4.sco")
        mission = self.module / "mission_templates.txt"
        mission.write_bytes(patch_text(
            mission.read_bytes().decode("utf-8"),
            index_troops(self.module / "troops.txt"), 4).encode("utf-8"))

    def test_all_five_original_scenes_parse(self):
        for num in range(1, 6):
            with self.subTest(map=num):
                data = (ORIGINAL / "SceneObj" / f"scn_tbfc_invasion_{num}.sco").read_bytes()
                scene = decode_scene(data)
                self.assertEqual(scene["version"], 4)
                self.assertGreater(len(scene["vertices"]), 100)

    def test_original_city_navmesh(self):
        scene = decode_scene((self.module / "SceneObj" / "scn_tbfc_invasion_4.sco").read_bytes())
        self.assertEqual((len(scene["objects"]), len(scene["vertices"]), len(scene["faces"])),
                         (226, 323, 270))
        self.assertEqual(len([o for o in scene["objects"] if o["type"] == 1]), 11)

    def test_scene_plan_uses_unused_entry_ids(self):
        raw = (self.module / "SceneObj" / "scn_tbfc_invasion_4.sco").read_bytes()
        plan = plan_city(raw)
        self.assertEqual(plan["zombie_entries"], list(range(32, 41)))
        self.assertEqual([p["entry"] for p in plan["guard_posts"]], [2, 3, 4])
        self.assertTrue(all(9 <= p["distance_from_survivors"] <= 24
                            for p in plan["guard_posts"]))
        altered = apply_city_overlay(raw, plan)
        self.assertEqual(len(altered) - len(raw), 252)
        check = decode_scene(altered)
        self.assertEqual(len(check["objects"]), 229)
        self.assertEqual(check["vertices"], decode_scene(raw)["vertices"])
        self.assertEqual(check["faces"], decode_scene(raw)["faces"])
        with self.assertRaises(SceneError):
            apply_city_overlay(altered, plan)

    def test_guard_posts_have_face_and_anchor_clearance(self):
        raw = (self.module / "SceneObj" / "scn_tbfc_invasion_4.sco").read_bytes()
        plan = plan_city(raw)
        self.assertEqual(plan["nav_reachable_faces"], 201)
        self.assertGreaterEqual(plan["min_prop_anchor_clearance"], 3.0)
        self.assertTrue(all(post["nearest_prop_anchor"] >= 3.0
                            for post in plan["guard_posts"]))
        self.assertEqual([post["entry"] for post in plan["guard_posts"]], [2, 3, 4])
        self.assertEqual([post["position"] for post in plan["guard_posts"]], [
            [169.423, 169.376, 3.191], [185.19, 185.009, 3.191],
            [146.25, 183.491, 3.191]])

    def test_guard_posts_fail_closed_if_scene_prop_clearance_disappears(self):
        raw = (self.module / "SceneObj" / "scn_tbfc_invasion_4.sco").read_bytes()
        scene = copy.deepcopy(decode_scene(raw))
        for face in scene["faces"]:
            center = tuple(sum(scene["vertices"][v][d] for v in face) / len(face)
                           for d in range(3))
            scene["objects"].append({"type": 0, "entry": 0, "position": center,
                                      "name": "synthetic_blocker"})
        with mock.patch("scene_tactics.decode_scene", return_value=scene):
            with self.assertRaisesRegex(SceneError, "clearance-screened"):
                plan_city(raw)

    def test_guard_posts_fail_closed_without_connected_faces(self):
        raw = (self.module / "SceneObj" / "scn_tbfc_invasion_4.sco").read_bytes()
        scene = copy.deepcopy(decode_scene(raw))
        scene["edges"] = scene["edges"][:1]
        with mock.patch("scene_tactics.decode_scene", return_value=scene):
            with self.assertRaises(SceneError):
                plan_city(raw)

    def test_truncated_scene_rejected(self):
        raw = (self.module / "SceneObj" / "scn_tbfc_invasion_4.sco").read_bytes()
        with self.assertRaises(SceneError):
            decode_scene(raw[:120])

    def test_orders_city_only_and_private_groups(self):
        idx = scene_index(self.module / "scenes.txt")
        orders = orders_trigger(idx).split()
        self.assertEqual(orders[:4], ["5.000000", "0.000000", "0.000000", "3"])
        self.assertEqual(orders[4:6], ["417", "0"])
        self.assertIn(str(72057594037927936 + idx), orders)
        self.assertEqual(orders.count("1780"), 3)
        self.assertEqual(orders.count("1791"), 3)
        self.assertEqual(orders.count("1790"), 3)

    def test_orders_rotate_sectors_per_wave(self):
        wave_global = 144115188075855872 + 1209  # original wave_number index
        orders = orders_trigger(0, wave_global).split()
        self.assertEqual(orders.count("1780"), 3)
        self.assertEqual(orders.count("1791"), 3)
        self.assertEqual(orders.count("1790"), 3)
        self.assertIn("2119", orders)  # wave parity / sector modulo
        self.assertIn("2121", orders)  # division - 5
        self.assertIn("2120", orders)  # entry math
        self.assertIn("1783", orders)  # native team-0 bot division adoption
        self.assertIn("1766", orders)  # group assignment used by team orders
        self.assertNotIn("1730", orders)  # no scripted destination override of combat AI
        self.assertIn("12", orders)  # try_for_agents adoption loop
        self.assertEqual(orders.count("1783"), 1)
        self.assertIn(str(wave_global), orders)
        # periodicity and City-only conditions stay intact
        self.assertEqual(orders[:3], ["5.000000", "0.000000", "0.000000"])
        self.assertEqual(orders[3], "3")

    def test_original_triggers_still_untouched(self):
        before = (self.module / "mission_templates.txt").read_bytes().decode("utf-8")
        changed = patch_orders(before, scene_index(self.module / "scenes.txt"))
        _, count0, end0 = mission_bounds(before.splitlines(keepends=True))
        _, count1, end1 = mission_bounds(changed.splitlines(keepends=True))
        self.assertEqual((count0, count1), (26, 27))
        self.assertEqual(before.splitlines()[end0 - 26:end0 - 1],
                         changed.splitlines()[end1 - 27:end1 - 2])
        visitors = changed.splitlines()[end1 - 2].split()
        self.assertEqual([visitors[7 + 7 * i + 6] for i in range(4)],
                         ["5", "6", "7", "5"])

    def test_integrated_scene_and_mission(self):
        original = (ORIGINAL / "SceneObj" / "scn_tbfc_invasion_4.sco").read_bytes()
        report = apply_module(self.module)
        self.assertEqual(report["invasion_triggers"], 27)
        self.assertEqual(len(report["city_guard_posts"]), 3)
        self.assertEqual(original, (ORIGINAL / "SceneObj" / "scn_tbfc_invasion_4.sco").read_bytes())
        with self.assertRaises((PatchError, SceneError)):
            apply_module(self.module)


if __name__ == "__main__":
    unittest.main()
