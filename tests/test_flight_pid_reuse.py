"""A reused attached PID cannot authenticate a clean passive shutdown."""
import hashlib
import hmac
import json
import os
from pathlib import Path
from unittest.mock import patch
import secrets
import tempfile
import threading
import time
import unittest

from telemetry.flight_recorder import record_session, verify_recording


def signed(kind, key, session, attempt, start):
    body = {"schema": "zombieee.recorder-" + kind + ".v1",
            "session_id": session, "attempt_id": attempt,
            "recorder_start_id": start}
    if kind == "attach":
        body["host_pid"] = 987654321
    payload = json.dumps(body, sort_keys=True, separators=(",", ":"),
                         ensure_ascii=True).encode("utf-8")
    body["mac"] = hmac.new(key, payload, hashlib.sha256).hexdigest()
    return body


def atomic_json(path, value):
    intermediate = path.with_name(path.name + ".tmp")
    intermediate.write_text(json.dumps(value))
    os.replace(intermediate, path)


class PassiveReuseTests(unittest.TestCase):
    def test_local_start_identity_change_blocks_clean_stop(self):
        key = secrets.token_bytes(32)
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            folder = base / "sessions" / "reuse"
            results, errors = [], []
            probes = [0]
            def identity(_pid):
                probes[0] += 1
                return "linux-proc-start:111" if probes[0] == 1 else "linux-proc-start:222"
            def worker():
                try:
                    results.append(record_session(
                        base / "sessions", "reuse", [], passive=True,
                        control_key=key, recorder_start_id="b-owned-identity",
                        attempt_id="attempt-2", timeout=1.0, poll=.01,
                        simulation=True))
                except BaseException as exc:
                    errors.append(exc)
            with patch("telemetry.flight_recorder.process_start_identity", side_effect=identity):
                thread = threading.Thread(target=worker)
                thread.start()
                deadline = time.monotonic() + 2
                while not (folder / "recorder-ready.json").exists() and time.monotonic() < deadline:
                    time.sleep(.01)
                self.assertTrue((folder / "recorder-ready.json").is_file())
                atomic_json(folder / "recorder-attach.json",
                            signed("attach", key, "reuse", "attempt-2", "b-owned-identity"))
                while not (folder / "recorder-attachment-ack.json").exists() and time.monotonic() < deadline:
                    time.sleep(.01)
                self.assertTrue((folder / "recorder-attachment-ack.json").is_file())
                atomic_json(folder / "recorder-stop.json",
                            signed("stop", key, "reuse", "attempt-2", "b-owned-identity"))
                thread.join(timeout=3)
            self.assertFalse(thread.is_alive())
            self.assertFalse(errors)
            self.assertEqual(results[0]["outcome"], "timeout")
            self.assertEqual(results[0]["pid_start_identity_status"], "reused_suspected")
            self.assertIsNone(results[0]["exit_code"])
            self.assertTrue(verify_recording(folder)["verified"])
            self.assertIn("pid_reuse_suspected", (folder / "events.jsonl").read_text())

    def test_local_start_identity_is_not_embedded_in_public_receipt(self):
        key = secrets.token_bytes(32)
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            report = record_session(base, "unknown", [], passive=True,
                control_key=key, recorder_start_id="nonce", timeout=.04,
                poll=.01, simulation=True)
            self.assertEqual(report["pid_start_identity_status"], "unknown")
            self.assertNotIn("host_pid", json.dumps(report))
            self.assertNotIn("linux-proc-start", json.dumps(report))
            self.assertNotIn(key.hex(), json.dumps(report))


if __name__ == "__main__":
    unittest.main()
