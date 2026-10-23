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
from final_city_gate import audit_final_city_controls
from private_commands import apply_module as add_private_commands
from solo_assist import apply_module as add_solo_assist

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
        self.assertEqual(result["original_invasion_game_type"], 7)
        self.assertTrue(result["checks"]["ai_original_invasion_mode_initialization"])
        self.assertTrue(result["checks"]["ai_reinforcement_correct_mode"])
        self.assertTrue(result["checks"]["ai_recovery_correct_mode"])

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

    def test_city_scene_corruption_rejected_even_when_file_changed(self):
        path = self.root / "SceneObj" / "scn_tbfc_invasion_4.sco"
        payload = bytearray(path.read_bytes())
        payload[-1] ^= 1  # preserve valid object count and change a navmesh byte
        path.write_bytes(payload)
        result = audit_city(self.root, ORIGINAL)
        self.assertFalse(result["city_accepted"])
        self.assertFalse(result["checks"]["city_sco_canonical_overlay"])

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


    def _accepted_snapshot(self):
        core = audit_city(self.root, ORIGINAL)
        self.assertTrue(core["city_accepted"], core["problems"])
        return ((self.root / "mission_templates.txt").read_bytes(),
                (self.root / "variables.txt").read_bytes(),
                core["city_overlay_expected_sha256"])

    def test_real_source_postcontrol_gate_private_hotkeys(self):
        mission, variables, city_digest = self._accepted_snapshot()
        add_private_commands(self.root)
        result = audit_final_city_controls(
            self.root, verified_mission=mission,
            verified_variables=variables, verified_city_sha256=city_digest,
            private_commands=True)
        self.assertTrue(result["passed"], result["problems"])
        self.assertEqual(result["control_mode"], "private-commands")
        self.assertFalse(result["runtime_verified"])

    def test_real_source_postcontrol_gate_solo_assist(self):
        mission, variables, city_digest = self._accepted_snapshot()
        add_solo_assist(self.root)
        result = audit_final_city_controls(
            self.root, verified_mission=mission,
            verified_variables=variables, verified_city_sha256=city_digest,
            solo_assist=True)
        self.assertTrue(result["passed"], result["problems"])
        self.assertEqual(result["control_mode"], "solo-assist")

    def test_real_source_postcontrol_gate_rejects_late_tamper(self):
        mission, variables, city_digest = self._accepted_snapshot()
        add_private_commands(self.root)
        path = self.root / "mission_templates.txt"
        path.write_bytes(path.read_bytes() + b"unapproved native mutation\\n")
        result = audit_final_city_controls(
            self.root, verified_mission=mission,
            verified_variables=variables, verified_city_sha256=city_digest,
            private_commands=True)
        self.assertFalse(result["passed"])
        self.assertFalse(result["checks"]["final_native_mission_exact"])


if __name__ == "__main__":
    unittest.main()
