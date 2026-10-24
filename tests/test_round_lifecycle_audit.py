"""Source-only round-lifecycle audit; no engine or proprietary assets in Git."""
import os
from pathlib import Path
import shutil
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
from round_lifecycle_audit import audit_round_lifecycle
from patch_defenders import patch_file, mission_bounds
from city_defense import apply_module as add_city
from wave_reinforcements import apply_module as add_wave
from tactical_recovery import apply_module as add_tactics

ORIGINAL = Path(os.environ.get("ZOMBIEEE_ORIGINAL_MODULE", "/missing/ZOMBIEEE"))


@unittest.skipUnless(ORIGINAL.is_dir(), "Owned original module required")
class RoundLifecycleSourceTests(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.module = Path(temp.name)
        (self.module / "SceneObj").mkdir()
        for file in ("troops.txt", "scenes.txt", "mission_templates.txt", "variables.txt"):
            shutil.copy2(ORIGINAL / file, self.module / file)
        for i in range(1, 6):
            file = f"scn_tbfc_invasion_{i}.sco"
            shutil.copy2(ORIGINAL / "SceneObj" / file, self.module / "SceneObj" / file)
        patch_file(self.module, 4, city_only=True)
        add_city(self.module)
        add_wave(self.module, city_only=True)
        add_tactics(self.module, city_only=True)

    def test_source_flags_unverified_round_restart_behavior(self):
        report = audit_round_lifecycle(ORIGINAL, self.module)
        self.assertTrue(report["source_pattern_verified"], report["problems"])
        self.assertFalse(report["runtime_verified"])
        self.assertEqual(report["disposition"], "source_verified_runtime_open_no_automatic_gameplay_patch")
        self.assertIn("whether original hold positions survive in-place round transitions",
                      report["unknown_runtime_observations"])
        self.assertTrue(report["checks"]["original_round_wave_reset"])
        self.assertTrue(report["checks"]["hold_orders_reissued_periodically"])

    def test_changed_hold_order_interval_fails_source_pattern(self):
        path = self.module / "mission_templates.txt"
        lines = path.read_text(encoding="utf-8").splitlines(keepends=True)
        at, _, _ = mission_bounds(lines)
        index = at + 1 + 26
        parts = lines[index].split()
        self.assertEqual(parts[:3], ["5.000000", "0.000000", "0.000000"])
        parts[2] = "100000000.000000"
        newline = "\r\n" if "\r\n" in lines[index] else "\n"
        lines[index] = " ".join(parts) + newline
        path.write_text("".join(lines), encoding="utf-8")
        report = audit_round_lifecycle(ORIGINAL, self.module)
        self.assertFalse(report["source_pattern_verified"])
        self.assertFalse(report["checks"]["hold_orders_reissued_periodically"])
        self.assertFalse(report["runtime_verified"])

    def test_removed_round_timestamp_fails_source_pattern(self):
        path = self.module / "mission_templates.txt"
        data = path.read_text()
        lines = data.splitlines(keepends=True)
        at, _, _ = mission_bounds(lines)
        idx = at + 1 + 28
        stamp = str(144115188075855872 + (self.module / "variables.txt").read_text().splitlines().index("zdr_last_reinforced_round_start"))
        self.assertIn(stamp, lines[idx])
        # Keep op-arity valid while changing the referenced global.
        lines[idx] = lines[idx].replace(f"2133 2 {stamp} ", "2133 2 144115188075855872 ", 1)
        path.write_bytes("".join(lines).encode())
        report = audit_round_lifecycle(ORIGINAL, self.module)
        self.assertFalse(report["source_pattern_verified"])
        self.assertFalse(report["checks"]["round_identity_stored_in_wave_handler"])

    def test_wrong_original_trigger_prefix_fails_source_pattern(self):
        path = self.module / "mission_templates.txt"
        lines = path.read_text().splitlines(keepends=True)
        at, _, _ = mission_bounds(lines)
        lines[at + 1] = lines[at + 1].replace("0.000000", "1.000000", 1)
        path.write_bytes("".join(lines).encode())
        report = audit_round_lifecycle(ORIGINAL, self.module)
        self.assertFalse(report["checks"]["original_25_triggers_preserved"])
        self.assertFalse(report["source_pattern_verified"])


if __name__ == "__main__":
    unittest.main()
