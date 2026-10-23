"""Source-free negative controls for Agent A's final City integrity gate."""
from pathlib import Path
import hashlib
import sys
import tempfile
import types
import unittest
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
from final_city_gate import audit_final_city_controls


class FinalCityGateTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        (self.root / "SceneObj").mkdir()
        self.city = b"synthetic scene only"
        self.mission = b"synthetic original 31-trigger mission\n"
        self.variables = b"synthetic 1222 variables\n"
        self.write(self.mission, self.variables, self.city)

    def write(self, mission, variables, city):
        (self.root / "mission_templates.txt").write_bytes(mission)
        (self.root / "variables.txt").write_bytes(variables)
        (self.root / "SceneObj" / "scn_tbfc_invasion_4.sco").write_bytes(city)

    def audit(self, **flags):
        return audit_final_city_controls(
            self.root, verified_mission=self.mission,
            verified_variables=self.variables,
            verified_city_sha256=hashlib.sha256(self.city).hexdigest(),
            **flags)

    def test_unchanged_optional_controls_off(self):
        result = self.audit()
        self.assertTrue(result["passed"], result["problems"])
        self.assertFalse(result["runtime_verified"])
        self.assertEqual(result["control_mode"], "none")
        self.assertNotIn(str(self.root), str(result))

    def test_mutated_native_mission_fails_closed(self):
        self.write(self.mission + b"unexpected", self.variables, self.city)
        result = self.audit()
        self.assertFalse(result["passed"])
        self.assertFalse(result["checks"]["final_native_mission_exact"])

    def test_mutated_global_table_fails_closed(self):
        self.write(self.mission, self.variables + b"unapproved variable\n", self.city)
        result = self.audit()
        self.assertFalse(result["passed"])
        self.assertFalse(result["checks"]["final_variable_table_exact"])

    def test_changed_scene_after_precontrol_audit_fails(self):
        self.write(self.mission, self.variables, self.city + b"unexpected")
        result = self.audit()
        self.assertFalse(result["passed"])
        self.assertFalse(result["checks"]["final_city_scene_unchanged"])

    def test_conflicting_control_modes_fail_closed(self):
        result = self.audit(private_commands=True, solo_assist=True)
        self.assertFalse(result["passed"])
        self.assertEqual(result["control_mode"], "invalid")

    def test_replays_only_selected_solo_assist_patch(self):
        fake = types.ModuleType("solo_assist")
        fake.patch_text = lambda mission: (mission + "SOLO\n", 32)
        with mock.patch.dict(sys.modules, {"solo_assist": fake}):
            self.write(self.mission + b"SOLO\n", self.variables, self.city)
            self.assertTrue(self.audit(solo_assist=True)["passed"])
            self.write(self.mission + b"SOLO\n", self.variables + b"BAD", self.city)
            self.assertFalse(self.audit(solo_assist=True)["passed"])

    def test_private_control_patch_and_counter_tamper(self):
        fake = types.ModuleType("private_commands")
        fake.patch_text = lambda mission, variables: (
            mission + "FOUR HOTKEY TRIGGERS\n", variables + "3 COUNTERS\n")
        with mock.patch.dict(sys.modules, {"private_commands": fake}):
            self.write(self.mission + b"FOUR HOTKEY TRIGGERS\n",
                       self.variables + b"3 COUNTERS\n", self.city)
            self.assertTrue(self.audit(private_commands=True)["passed"])
            self.write(self.mission + b"FOUR HOTKEY TRIGGERS\n",
                       self.variables + b"COUNTER ALTERED\n", self.city)
            self.assertFalse(self.audit(private_commands=True)["passed"])

    def test_missing_file_never_passes_and_leaks_no_path(self):
        (self.root / "mission_templates.txt").unlink()
        result = self.audit()
        self.assertFalse(result["passed"])
        self.assertIn("FileNotFoundError", result["problems"][0])
        self.assertNotIn(str(self.root), str(result))


if __name__ == "__main__":
    unittest.main()
