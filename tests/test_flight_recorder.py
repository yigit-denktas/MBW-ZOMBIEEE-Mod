"""Offline Agent C flight-recorder fixtures; no game, cloud or CI required."""
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

from telemetry.flight_recorder import (
    record_session, safe_launcher_receipt, verify_recording,
)


class FlightRecorderTests(unittest.TestCase):
    def run_child(self, root: Path, script: str, **kwargs):
        game_log = root / "wse2.log"
        game_log.write_text("STALE LOG SHOULD NOT BE INCLUDED\n", encoding="utf-8")
        settings = {"timeout": 5, "poll": 0.02}
        settings.update(kwargs)
        result = record_session(
            root / "evidence", "test-city", [game_log],
            command=[sys.executable, "-c", script, str(game_log)],
            **settings)
        session = root / "evidence" / "test-city"
        return result, session

    def test_child_crash_survives_and_keeps_evidence(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            child = (
                "import os, pathlib, sys; "
                "p=pathlib.Path(sys.argv[1]); "
                "p.open('a').write('ZDB1|boot|triggers=35\\n"
                "token: hunter2\\nFATAL ERROR: ACCESS VIOLATION\\n'); "
                "os._exit(7)"
            )
            report, folder = self.run_child(root, child)
            self.assertEqual(report["exit_code"], 7)
            self.assertEqual(report["outcome"], "exited")
            self.assertTrue(report["exit_code_observed"])
            self.assertTrue((folder / "recorder.json").is_file())
            self.assertTrue(verify_recording(folder)["verified"])
            log = (folder / "logs" / "log_01.txt").read_text(encoding="utf-8")
            self.assertIn("ZDB1|boot|triggers=35", log)
            self.assertIn("FATAL ERROR", log)
            self.assertNotIn("hunter2", log)
            self.assertNotIn("STALE LOG", log)
            lines = (folder / "events.jsonl").read_text().splitlines()
            self.assertTrue(all(json.loads(line)["schema"] == "zombieee.flight.v1"
                                for line in lines))
            self.assertTrue(any(json.loads(line)["event"] == "process_finished"
                                for line in lines))

    def test_large_log_is_bounded_and_marks_truncation(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            child = (
                "import pathlib,sys; "
                "pathlib.Path(sys.argv[1]).open('a').write('x'*5000)"
            )
            report, folder = self.run_child(root, child, max_log_bytes=128)
            self.assertEqual(report["log_truncated"], [True])
            self.assertLessEqual((folder / "logs" / "log_01.txt").stat().st_size, 128)
            self.assertTrue(verify_recording(folder)["verified"])

    def test_tampered_snapshot_fails_verification(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            report, folder = self.run_child(root, "pass")
            self.assertTrue(verify_recording(folder)["verified"])
            (folder / "recorder.json").write_text("{}", encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "integrity"):
                verify_recording(folder)

    def test_launcher_receipt_allowlist_removes_private_fields(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            original = {
                "schema": "zombieee.session.v1", "session_id": "solo-one",
                "city": "tbfc_invasion_4", "outcome": "unknown",
                "private_path": "C:\\Users\\Alice\\Games",
                "host_pid": 1234, "auth_token": "hunter2",
                "build_manifest_sha256": "a" * 64,
            }
            path = root / "receipt.json"
            path.write_text(json.dumps(original), encoding="utf-8")
            safe = safe_launcher_receipt(path)
            self.assertNotIn("host_pid", safe)
            self.assertNotIn("auth_token", safe)
            self.assertNotIn("private_path", safe)
            self.assertEqual(safe["build_manifest_sha256"], "a" * 64)
            path.write_text('{"schema":"wrong"}')
            with self.assertRaisesRegex(ValueError, "schema"):
                safe_launcher_receipt(path)

    def test_timeout_terminates_only_owned_child(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            result, folder = self.run_child(
                root, "import time; time.sleep(60)", timeout=0.2)
            self.assertEqual(result["outcome"], "timeout")
            self.assertTrue(result["exit_code_observed"])
            self.assertTrue(verify_recording(folder)["verified"])

    def test_external_process_cannot_be_killed_or_assigned_exit_code(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            result = record_session(
                root / "evidence", "external", [], observe_pid=99999999,
                timeout=0.05, poll=0.01)
            self.assertIsNone(result["exit_code"])
            self.assertFalse(result["exit_code_observed"])
            self.assertIn(result["outcome"],
                          ("timeout", "disappeared_exit_code_unknown"))
            self.assertTrue(verify_recording(root / "evidence" / "external")["verified"])

    def test_session_reuse_and_unbounded_inputs_refused(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            with self.assertRaisesRegex(ValueError, "session"):
                record_session(root, "../escape", [], command=[sys.executable])
            with self.assertRaisesRegex(ValueError, "bounds"):
                record_session(root, "x", [], command=[sys.executable],
                               max_log_bytes=3 * 1024 * 1024)
            report, folder = self.run_child(root, "pass")
            with self.assertRaises(FileExistsError):
                self.run_child(root, "pass")


if __name__ == "__main__":
    unittest.main()
