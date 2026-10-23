"""Crash interruption evidence is inspectable, not a verified/completed ZIP."""
import json
import os
from pathlib import Path
import secrets
import subprocess
import sys
import tempfile
import time
import unittest

from telemetry.recovery import inspect_recording
from telemetry.flight_recorder import record_session


class RecoveryTests(unittest.TestCase):
    def test_finished_session_is_verified_without_automatic_sharing(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            record_session(root / "out", "done", [], command=[sys.executable, "-c", "pass"],
                           simulation=True, poll=0.01, timeout=3)
            report = inspect_recording(root / "out" / "done")
            self.assertTrue(report["session_complete"])
            self.assertTrue(report["integrity_verified"])
            self.assertFalse(report["shareable_without_review"])
            self.assertTrue(report["manual_privacy_review_required"])
            self.assertTrue(report["simulation"])
            self.assertEqual(report["game_runtime"], "unknown")

    def test_terminated_recorder_is_incomplete_and_not_shareable(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            log = root / "game.log"
            log.write_text("stale\\n")
            key = secrets.token_bytes(32)
            env = os.environ.copy()
            env["ZOMBIEEE_RECORDER_CONTROL_KEY"] = key.hex()
            recorder = subprocess.Popen([
                sys.executable, "-m", "telemetry.flight_recorder", "--passive",
                "--simulation", "--output-root", str(root / "out"), "--session",
                "interrupted", "--attempt", "a2", "--recorder-start-id", "nonce-id",
                "--log", str(log), "--poll", ".02", "--timeout", "6",
            ], cwd=Path(__file__).resolve().parents[1], env=env,
                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            session = root / "out" / "interrupted"
            try:
                deadline = time.monotonic() + 3
                while not (session / "recorder-ready.json").exists() and time.monotonic() < deadline:
                    time.sleep(.01)
                self.assertTrue((session / "recorder-ready.json").exists())
                with log.open("a") as out:
                    out.write("ZDB1|boot|triggers=35\\nFATAL ERROR: synthetic\\n")
                time.sleep(.12)
                recorder.terminate()
                recorder.wait(timeout=3)
                report = inspect_recording(session)
                self.assertFalse(report["session_complete"])
                self.assertFalse(report["integrity_verified"])
                self.assertEqual(report["observation"], "incomplete_recorder_session")
                self.assertFalse(report["shareable_without_review"])
                self.assertTrue((session / "logs" / "log_01.txt").exists())
                self.assertFalse((session / "manifest.json").exists())
            finally:
                if recorder.poll() is None:
                    recorder.kill()
                    recorder.wait(timeout=2)

    def test_tampered_finished_manifest_is_not_verified(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            record_session(root, "tamper", [], command=[sys.executable, "-c", "pass"])
            session = root / "tamper"
            (session / "recorder.json").write_text("{}")
            report = inspect_recording(session)
            self.assertEqual(report["observation"], "final_manifest_invalid")
            self.assertFalse(report["integrity_verified"])

    def test_redirected_session_root_is_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            target = root / "target"
            target.mkdir()
            path = root / "redirect"
            try:
                path.symlink_to(target, target_is_directory=True)
            except (OSError, NotImplementedError) as error:
                self.skipTest(f"symlink privilege unavailable: {type(error).__name__}")
            with self.assertRaisesRegex(ValueError, "Unsafe"):
                inspect_recording(path)


if __name__ == "__main__":
    unittest.main()
