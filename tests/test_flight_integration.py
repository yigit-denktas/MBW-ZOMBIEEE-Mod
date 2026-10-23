"""Agent C end-to-end offline recorder -> collector -> analyzer fixtures."""
import json
from pathlib import Path
import sys
import tempfile
import unittest
import zipfile

from telemetry.flight_recorder import record_session, verify_recording

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
from diagnostics import collect, read_bundle, analyze


class FlightIntegrationTests(unittest.TestCase):
    def create_recording(self, root, exit_code=7):
        log = root / "live.log"
        log.write_text("stale pre-session record\n", encoding="utf-8")
        program = (
            "import os,sys,pathlib;"
            "p=pathlib.Path(sys.argv[1]);"
            "p.open('a').write('ZDB1|boot|triggers=35\\n"
            "ZDB1|mission_enter|role=server|team0=-1|team1=-1\\n"
            "FATAL ERROR: simulated crash\\n');"
            f"os._exit({exit_code})"
        )
        record = record_session(root / "recordings", "city-test", [log],
                                command=[sys.executable, "-c", program, str(log)],
                                timeout=5, poll=0.02)
        folder = root / "recordings" / "city-test"
        self.assertTrue(verify_recording(folder)["verified"])
        return record, folder

    def test_one_crash_yields_analyzable_verified_zip(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            state, recording = self.create_recording(root)
            self.assertEqual(state["exit_code"], 7)
            archive = root / "evidence.zip"
            collected = collect(None, None, archive, [], "city-final", flight_root=recording)
            self.assertGreaterEqual(collected["log_count"], 1)
            payload = read_bundle(archive)
            flight = json.loads(payload["flight_recorder.json"])
            self.assertEqual(flight["exit_code"], 7)
            self.assertNotIn(b"stale pre-session", payload["logs/log_01.txt"])
            self.assertIn(b"FATAL ERROR", payload["logs/log_01.txt"])
            self.assertIn(b"process_finished", payload["flight_events.jsonl"])
            report = analyze(payload)
            ids = {f["id"] for f in report["findings"]}
            self.assertIn("R002", ids)
            self.assertIn("R028", ids)
            self.assertEqual(report["flight_recorder"]["outcome"], "exited")
            self.assertEqual(report["evidence_matrix"]["checks"]["wave_progression"]["status"], "unknown")

    def test_tampered_recording_fails_closed(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            _, recording = self.create_recording(root)
            (recording / "recorder.json").write_text("{}", encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "integrity"):
                collect(None, None, root / "failed.zip", [], "city-final",
                        flight_root=recording)
            self.assertFalse((root / "failed.zip").exists())

    def test_unknown_team_getter_does_not_fake_empty_allies(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            _, recording = self.create_recording(root, exit_code=0)
            target = root / "data.zip"
            collect(None, None, target, [], "city-final", flight_root=recording)
            report = analyze(read_bundle(target))
            self.assertFalse(report["team_evidence"]["available"])
            self.assertNotIn("R018", {f["id"] for f in report["findings"]})


if __name__ == "__main__":
    unittest.main()
