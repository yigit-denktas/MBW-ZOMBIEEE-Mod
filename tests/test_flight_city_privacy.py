"""Synthetic City incident privacy and collector tests."""
import json
from pathlib import Path
import sys
import tempfile
import unittest
import zipfile

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
from diagnostics import collect, analyze, read_bundle


class CityEvidencePrivacyTests(unittest.TestCase):
    def test_build_receipt_private_metadata_does_not_enter_archive(self):
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            mod = base / "module"
            mod.mkdir()
            receipt = {
                "experimental_map_scope": "city-only",
                "city_static_acceptance": {
                    "checks": {"original": True, "city_native": True},
                    "original_invasion_game_type": 7,
                    "hidden_metadata": "DO_NOT_EXPORT_PRIVATE_METADATA",
                },
                "city_final_acceptance": {
                    "passed": True, "control_mode": "none",
                    "problems": ["DO_NOT_EXPORT_PRIVATE_METADATA"],
                },
            }
            (mod / "ZOMBIEEE_REMASTER.json").write_text(json.dumps(receipt))
            archive = base / "evidence.zip"
            collect(None, mod, archive, [], "fixture")
            payload = read_bundle(archive)
            safe = payload["module.json"].decode()
            self.assertNotIn("DO_NOT_EXPORT_PRIVATE_METADATA", safe)
            report = analyze(payload)["city_incident"]
            self.assertTrue(report["build"]["source_verified"])
            self.assertFalse(report["runtime"]["gameplay_verified"])

    def test_arbitrary_event_fields_and_paths_are_removed(self):
        event = {"event": "command_exec", "source": "private/user/location",
                 "line": 1, "fields": {"cmd": "private-phrase",
                                       "wave": "2", "token": "hidden-value"}}
        payload = {"events.jsonl": (json.dumps(event) + "\n").encode(),
                   "logs/log_01.txt": b"ZDB1|boot\n"}
        result = analyze(payload)["city_incident"]
        data = json.dumps(result)
        self.assertNotIn("private-phrase", data)
        self.assertNotIn("hidden-value", data)
        self.assertNotIn("private/user/location", data)
        self.assertIn("unattributed_log", data)

    def test_clock_lanes_are_not_mixed(self):
        game = {"event": "boot", "source": "logs/log_01.txt", "line": 5,
                "fields": {"triggers": "31"}}
        rec = {"event": "recorder_ready", "utc": "2026-10-23T21:00:00+00:00"}
        payload = {"events.jsonl": (json.dumps(game) + "\n").encode(),
                   "flight_events.jsonl": (json.dumps(rec) + "\n").encode(),
                   "logs/log_01.txt": b"ZDB1|boot\n"}
        city = analyze(payload)["city_incident"]
        self.assertEqual(city["timeline"]["cross_lane_order"],
                         "unknown_without_shared_clock")
        self.assertEqual(city["timeline"]["engine"]["ordering"], "per_file_line_only")
        self.assertEqual(city["timeline"]["recorder"]["ordering"], "recorder_utc_only")

    def test_simulation_and_omissions_are_explicit(self):
        flight = {"simulation": True, "game_runtime": "unknown",
                  "outcome": "timeout", "log_omitted_bytes": [88],
                  "event_drops": 3}
        payload = {"flight_recorder.json": json.dumps(flight).encode(),
                   "logs/log_01.txt": b"harmless\n"}
        city = analyze(payload)["city_incident"]
        self.assertTrue(city["runtime"]["simulation"])
        self.assertTrue(city["recording_gap"])
        self.assertIn("synthetic_session_not_gameplay", city["unknowns"])


if __name__ == "__main__":
    unittest.main()
