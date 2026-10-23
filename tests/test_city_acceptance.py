"""Offline City acceptance regression. No original assets committed."""
import os
from pathlib import Path
import shutil
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
from city_acceptance import audit_city
from patch_defenders import patch_file, mission_bounds
from city_defense import apply_module as city_defense
from wave_reinforcements import apply_module as waves
from tactical_recovery import apply_module as recovery

ORIGINAL = Path(os.environ.get(
    "ZOMBIEEE_ORIGINAL_MODULE", "/mnt/data/zombie04_inspect/ZOMBIEEE"))


@unittest.skipUnless(ORIGINAL.is_dir(), "Original Beta 0.4 required; never bundled")
class CityAcceptanceTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        (self.root / "SceneObj").mkdir()
        for name in ("troops.txt", "scenes.txt", "variables.txt",
                     "mission_templates.txt"):
            shutil.copy2(ORIGINAL / name, self.root / name)
        for number in range(1, 6):
            name = f"scn_tbfc_invasion_{number}.sco"
            shutil.copy2(ORIGINAL / "SceneObj" / name,
                         self.root / "SceneObj" / name)
        patch_file(self.root, 4, city_only=True)
        city_defense(self.root)
        waves(self.root, cap=4, city_only=True)
        recovery(self.root, city_only=True)

    def test_valid_city_is_static_only(self):
        result = audit_city(self.root, ORIGINAL)
        self.assertTrue(result["city_accepted"], result["problems"])
        self.assertFalse(result["runtime_verified"])
        self.assertEqual((result["original_triggers"],
                          result["city_triggers"]), (25, 31))

    def test_missing_city_gate_is_rejected(self):
        path = self.root / "mission_templates.txt"
        content = path.read_text()
        old = "2211 1 1224979098644774920 31 2 1224979098644774920"
        self.assertIn(old, content)
        path.write_text(content.replace(
            old, "2211 1 1224979098644774920 31 2 1224979098644774912", 1))
        result = audit_city(self.root, ORIGINAL)
        self.assertFalse(result["city_accepted"])
        self.assertFalse(result["checks"]["trigger_28_city_scene_gate"])

    def test_original_native_trigger_change_is_rejected(self):
        path = self.root / "mission_templates.txt"
        rows = path.read_text().splitlines(keepends=True)
        count_row, _, _ = mission_bounds(rows)
        rows[count_row + 1] = rows[count_row + 1].replace(
            rows[count_row + 1].split()[0], "123.000000", 1)
        path.write_text("".join(rows))
        result = audit_city(self.root, ORIGINAL)
        self.assertFalse(result["city_accepted"])
        self.assertFalse(result["checks"]["original_trigger_prefix"])

    def test_modified_deferred_scene_rejected(self):
        path = self.root / "SceneObj" / "scn_tbfc_invasion_3.sco"
        path.write_bytes(path.read_bytes() + b"CHANGED")
        result = audit_city(self.root, ORIGINAL)
        self.assertFalse(result["city_accepted"])
        self.assertFalse(result["checks"]["other_scene_3_untouched"])

    def test_missing_source_scene_evidence_rejected(self):
        (self.root / "SceneObj" / "scn_tbfc_invasion_5.sco").unlink()
        result = audit_city(self.root, ORIGINAL)
        self.assertFalse(result["city_accepted"])
        self.assertIn("Insufficient matching evidence for scene 5",
                      result["problems"])


if __name__ == "__main__":
    unittest.main()
