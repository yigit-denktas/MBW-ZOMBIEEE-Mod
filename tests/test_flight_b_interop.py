"""True two-process C/B fixture; B is simulated, no Warband/WSE2 dependency.

The test launches the C CLI as a separate OS process, proves no game exists
before recorder readiness, attempts an invalid HMAC, attaches a B-owned fake
crashing game, verifies safe shutdown and the ZIP integrity/diagnostic report.
"""
import hashlib
import hmac
import json
import os
from pathlib import Path
import secrets
import subprocess
import sys
import tempfile
import time
import unittest

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "tools"))
from diagnostics import collect, read_bundle, analyze


def atomic_json(path, value):
    pending = path.with_name(path.name + ".tmp")
    pending.write_text(json.dumps(value, sort_keys=True), encoding="utf-8")
    os.replace(pending, path)


def signed(kind, key, session, attempt, start_id, **fields):
    body = {"schema": "zombieee.recorder-" + kind + ".v1",
            "session_id": session, "attempt_id": attempt,
            "recorder_start_id": start_id, **fields}
    encoded = json.dumps(body, sort_keys=True, separators=(",", ":"),
                         ensure_ascii=True).encode()
    body["mac"] = hmac.new(key, encoded, hashlib.sha256).hexdigest()
    return body


def ready_is_valid(ready, proc, session, attempt, start_id):
    # A simulation of B's required fail-closed gate, not the B implementation.
    return (ready.get("schema") == "zombieee.recorder-ready.v1"
            and ready.get("session_id") == session
            and ready.get("attempt_id") == attempt
            and ready.get("recorder_start_id") == start_id
            and ready.get("recorder_pid") == proc.pid
            and proc.poll() is None
            and ready.get("watcher_active") is True
            and ready.get("log_offsets_captured") is True
            and ready.get("engine_ready") is False
            and ready.get("mission_ready") is False)


def await_file(path, timeout=3):
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if path.is_file():
            return json.loads(path.read_text())
        time.sleep(0.02)
    raise AssertionError("File never published: " + path.name)


class FlightBInteropTests(unittest.TestCase):
    def test_process_handshake_bad_hmac_early_stop_and_crash_bundle(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            session, attempt = "city-fake", "trial-07"
            start_id = secrets.token_hex(16)
            secret = secrets.token_bytes(32)
            log = root / "game.log"
            log.write_text("UNRELATED PRIOR SESSION\n", encoding="utf-8")
            folder = root / "private" / session
            env = os.environ.copy()
            env["ZOMBIEEE_RECORDER_CONTROL_KEY"] = secret.hex()
            recorder = subprocess.Popen(
                [sys.executable, "-m", "telemetry.flight_recorder",
                 "--passive", "--output-root", str(root / "private"),
                 "--session", session, "--attempt", attempt,
                 "--recorder-start-id", start_id,
                 "--log", str(log), "--poll", "0.01", "--timeout", "6"],
                cwd=REPO, env=env, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            fake_host = None
            try:
                ready = await_file(folder / "recorder-ready.json")
                self.assertTrue(ready_is_valid(ready, recorder, session, attempt, start_id))
                self.assertFalse(ready_is_valid({**ready, "attempt_id": "old"},
                                                recorder, session, attempt, start_id))
                self.assertFalse(ready_is_valid({**ready, "recorder_pid": -1},
                                                recorder, session, attempt, start_id))
                self.assertFalse((folder / "recorder-attachment-ack.json").exists())

                fake_program = (
                    "import pathlib,sys,time,os;"
                    "p=pathlib.Path(sys.argv[1]);"
                    "p.open('a').write('ZDB1|boot|triggers=35\\n');"
                    "time.sleep(.15);"
                    "p.open('a').write('filler\\n'*460000 + 'FATAL ERROR: late simulated crash\\n');"
                    "time.sleep(.45);os._exit(13)"
                )
                fake_host = subprocess.Popen([sys.executable, "-c", fake_program, str(log)])
                # Bad authentication must not attach an otherwise valid PID.
                forged = signed("attach", secrets.token_bytes(32), session,
                                attempt, start_id, host_pid=fake_host.pid)
                atomic_json(folder / "recorder-attach.json", forged)
                time.sleep(0.08)
                self.assertFalse((folder / "recorder-attachment-ack.json").exists())

                atomic_json(folder / "recorder-attach.json",
                            signed("attach", secret, session, attempt, start_id,
                                   host_pid=fake_host.pid))
                accepted = await_file(folder / "recorder-attachment-ack.json")
                self.assertTrue(accepted["attachment_accepted"])
                self.assertFalse(accepted["game_ready"])

                # Signed stop sent before the host exits must not seal evidence.
                atomic_json(folder / "recorder-stop.json",
                            signed("stop", secret, session, attempt, start_id))
                time.sleep(0.08)
                self.assertIsNone(recorder.poll())
                self.assertFalse((folder / "manifest.json").exists())

                self.assertEqual(fake_host.wait(timeout=4), 13)
                stdout, stderr = recorder.communicate(timeout=5)
                self.assertEqual(recorder.returncode, 0, stderr.decode(errors="replace"))
                receipt = json.loads((folder / "recorder.json").read_text())
                self.assertEqual(receipt["watch_mode"], "passive")
                self.assertEqual(receipt["outcome"], "stopped")
                self.assertIsNone(receipt["exit_code"])
                self.assertGreater(receipt["log_omitted_bytes"][0], 0)
                snapshot = (folder / "logs" / "log_01.txt").read_text()
                self.assertIn("ZDB1|boot|triggers=35", snapshot)
                self.assertIn("FATAL ERROR: late simulated crash", snapshot)
                self.assertIn("ZDB1-OMITTED", snapshot)
                self.assertNotIn("UNRELATED PRIOR SESSION", snapshot)
                self.assertIn("game_process_not_confirmed_exited",
                              (folder / "events.jsonl").read_text())

                zip_path = root / "final-private.zip"
                collected = collect(None, None, zip_path, [], session, flight_root=folder)
                self.assertGreater(collected["log_count"], 0)
                data = read_bundle(zip_path)
                analysis = analyze(data)
                self.assertIn("R002", {finding["id"] for finding in analysis["findings"]})
                self.assertNotIn("R028", {finding["id"] for finding in analysis["findings"]})
                self.assertEqual(analysis["flight_recorder"]["watch_mode"], "passive")
                self.assertEqual(analysis["privacy"]["manual_review_required"], True)
                self.assertNotIn(secret.hex().encode(), b"".join(data.values()))
                self.assertEqual(analysis["evidence_matrix"]["checks"]["wave_progression"]["status"],
                                 "unknown")
            finally:
                if fake_host and fake_host.poll() is None:
                    fake_host.terminate()
                    fake_host.wait(timeout=2)
                if recorder.poll() is None:
                    recorder.terminate()
                    recorder.communicate(timeout=3)


if __name__ == "__main__":
    unittest.main()
