"""Local preflight unit tests: compiled data structure, not gameplay."""
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "tools"))
from preflight import inspect_assets, read_invasion_mission, report_for_module


def fake_mission(entry_count=2, trigger_count=2):
    entries = [f"{entry_count} 0 16 1 0"] + [
        f"{i} 0 16 1 0" for i in range(1, entry_count)]
    triggers = ["1.0 0 0 0 0"] * trigger_count
    return "\n".join([
        "missionsfile version 1", "1", "mst_multiplayer_iv multiplayer_iv 2 -1",
        "Description", *entries, str(trigger_count), *triggers]) + "\n"


class PreflightTests(unittest.TestCase):
    def setup_module(self, temp):
        root = Path(temp)
        (root / "Resource").mkdir()
        (root / "module.ini").write_text(
            "load_resource = native_things\nload_mod_resource = zombies\n")
        (root / "Resource" / "zombies.brf").write_bytes(b"fixture-resource")
        (root / "mission_templates.txt").write_text(fake_mission())
        return root

    def test_valid_module(self):
        with tempfile.TemporaryDirectory() as temp:
            report = report_for_module(self.setup_module(temp))
            self.assertTrue(report["ok"])
            self.assertEqual(report["mission"]["entry_points"], 2)
            self.assertEqual(report["mission"]["triggers"], 2)
            self.assertEqual(report["resources"]["mod_resources_referenced"], 1)
            self.assertFalse(report["runtime_verified"])

    def test_missing_brf(self):
        with tempfile.TemporaryDirectory() as temp:
            mod = self.setup_module(temp)
            (mod / "Resource" / "zombies.brf").unlink()
            self.assertEqual(inspect_assets(mod)["missing_mod_resources"], ["zombies.brf"])
            self.assertFalse(report_for_module(mod)["ok"])

    def test_native_resource_not_reported_missing(self):
        with tempfile.TemporaryDirectory() as temp:
            mod = self.setup_module(temp)
            self.assertEqual(inspect_assets(mod)["missing_mod_resources"], [])

    def test_corrupt_entry_points(self):
        with tempfile.TemporaryDirectory() as temp:
            mod = self.setup_module(temp)
            target = mod / "mission_templates.txt"
            target.write_text(fake_mission().replace("1 0 16 1 0", "7 0 16 1 0"))
            with self.assertRaises(ValueError):
                read_invasion_mission(target)
            self.assertFalse(report_for_module(mod)["ok"])

    def test_missing_trigger(self):
        with tempfile.TemporaryDirectory() as temp:
            mod = self.setup_module(temp)
            target = mod / "mission_templates.txt"
            target.write_text(fake_mission().rsplit("\n", 3)[0] + "\n")
            self.assertFalse(report_for_module(mod)["ok"])

    def test_case_mismatch_warning(self):
        with tempfile.TemporaryDirectory() as temp:
            mod = self.setup_module(temp)
            (mod / "Resource" / "zombies.brf").rename(mod / "Resource" / "ZOMBIES.brf")
            report = inspect_assets(mod)
            self.assertEqual(report["missing_mod_resources"], [])
            self.assertEqual(len(report["case_mismatches"]), 1)


if __name__ == "__main__":
    unittest.main()
