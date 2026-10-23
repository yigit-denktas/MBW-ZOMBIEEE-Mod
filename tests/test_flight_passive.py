"""Passive C/B recorder handshake: no game PID exists until after readiness."""
import hashlib
import hmac
import json
import os
from pathlib import Path
import secrets
import subprocess
import sys
import tempfile
import threading
import time
import unittest

from telemetry.flight_recorder import record_session, verify_recording


def sign_control(kind: str, key: bytes, **fields) -> dict:
    obj = {"schema": "zombieee.recorder-" + kind + ".v1", **fields}
    encoded = json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode()
    obj["mac"] = hmac.new(key, encoded, hashlib.sha256).hexdigest()
    return obj


def write_atomic(path: Path, value: dict) -> None:
    tmp = path.with_name(path.name + ".tmp")
    tmp.write_text(json.dumps(value), encoding="utf-8")
    os.replace(tmp, path)


class PassiveRecorderTests(unittest.TestCase):
    def test_passive_starts_without_game_then_attaches_and_stops(self):
        key = secrets.token_bytes(32)
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            log = base / "engine.log"
            log.write_text("old engine text\n")
            folder = base / "recordings" / "city-1"
            got, errors = [], []

            def worker():
                try:
                    got.append(record_session(
                        base / "recordings", "city-1", [log],
                        passive=True, control_key=key,
                        attempt_id="attempt-2", recorder_start_id="b-created-uuid",
                        timeout=5, poll=0.01))
                except BaseException as exc:
                    errors.append(exc)

            thread = threading.Thread(target=worker)
            thread.start()
            deadline = time.monotonic() + 2
            while not (folder / "recorder-ready.json").is_file() and time.monotonic() < deadline:
                time.sleep(0.01)
            self.assertTrue((folder / "recorder-ready.json").is_file())
            ready = json.loads((folder / "recorder-ready.json").read_text())
            self.assertEqual(ready["schema"], "zombieee.recorder-ready.v1")
            self.assertEqual(ready["recorder_pid"], os.getpid())
            self.assertEqual(ready["recorder_start_id"], "b-created-uuid")
            self.assertEqual(ready["attempt_id"], "attempt-2")
            self.assertTrue(ready["log_offsets_captured"])
            self.assertFalse(ready["engine_ready"])

            # Emulate B starting a host only after correlated recorder readiness.
            game = subprocess.Popen([sys.executable, "-c",
                                     "import time;time.sleep(.12)"])
            common = {"session_id": "city-1", "attempt_id": "attempt-2",
                      "recorder_start_id": "b-created-uuid"}
            try:
                write_atomic(folder / "recorder-attach.json",
                             sign_control("attach", key, **common, host_pid=game.pid))
                deadline = time.monotonic() + 2
                while not (folder / "recorder-attachment-ack.json").is_file() and time.monotonic() < deadline:
                    time.sleep(0.01)
                self.assertTrue((folder / "recorder-attachment-ack.json").is_file())
                ack = json.loads((folder / "recorder-attachment-ack.json").read_text())
                self.assertEqual(ack["schema"], "zombieee.recorder-attachment-ack.v1")
                self.assertFalse(ack["game_ready"])
                with log.open("a") as handle:
                    handle.write("ZDB1|boot|triggers=35\nFATAL ERROR: early host crash\n")
            finally:
                game.wait(timeout=2)
            write_atomic(folder / "recorder-stop.json", sign_control("stop", key, **common))
            thread.join(timeout=3)
            self.assertFalse(thread.is_alive())
            self.assertFalse(errors)
            self.assertEqual(got[0]["outcome"], "stopped")
            self.assertIsNone(got[0]["exit_code"])
            saved = (folder / "logs" / "log_01.txt").read_text()
            self.assertNotIn("old engine text", saved)
            self.assertIn("FATAL ERROR", saved)
            self.assertTrue(verify_recording(folder)["verified"])

    def test_bad_mac_wrong_attempt_and_stale_stop_are_rejected(self):
        key = secrets.token_bytes(32)
        other_key = secrets.token_bytes(32)
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            folder = base / "out" / "city-2"
            result = []
            thread = threading.Thread(target=lambda: result.append(
                record_session(base / "out", "city-2", [], passive=True,
                               control_key=key, recorder_start_id="real-id",
                               attempt_id="attempt-9", poll=0.01, timeout=3)))
            thread.start()
            deadline = time.monotonic() + 2
            while not (folder / "recorder-ready.json").exists() and time.monotonic() < deadline:
                time.sleep(0.01)
            self.assertTrue((folder / "recorder-ready.json").exists())
            common = {"session_id": "city-2", "attempt_id": "attempt-9",
                      "recorder_start_id": "real-id"}
            forged = sign_control("attach", other_key, **common, host_pid=32123)
            write_atomic(folder / "recorder-attach.json", forged)
            time.sleep(0.08)
            self.assertFalse((folder / "recorder-attachment-ack.json").exists())
            stale = sign_control("stop", key, session_id="city-2",
                                 attempt_id="attempt-8", recorder_start_id="real-id")
            write_atomic(folder / "recorder-stop.json", stale)
            time.sleep(0.08)
            self.assertTrue(thread.is_alive())
            # Rejected controls must not prevent a valid authenticated stop.
            write_atomic(folder / "recorder-stop.json", sign_control("stop", key, **common))
            thread.join(timeout=2)
            self.assertFalse(thread.is_alive())
            self.assertEqual(result[0]["outcome"], "stopped_without_attachment")
            events = (folder / "events.jsonl").read_text()
            self.assertIn("control_rejected", events)
            self.assertNotIn("process_attached", events)
            self.assertTrue(verify_recording(folder)["verified"])

    def test_passive_requires_key_and_no_game_pid(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            with self.assertRaisesRegex(ValueError, "control key"):
                record_session(root, "no-key", [], passive=True,
                               recorder_start_id="id")
            with self.assertRaisesRegex(ValueError, "cannot spawn"):
                record_session(root, "reject-game", [], passive=True,
                               command=[sys.executable], control_key=b"x"*32,
                               recorder_start_id="id")
            self.assertFalse((root / "no-key").exists())
            self.assertFalse((root / "reject-game").exists())


if __name__ == "__main__":
    unittest.main()
