"""Log rotation, per-poll split credentials and bounded event recording."""
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import threading
import time
import unittest

from telemetry.flight_recorder import record_session, verify_recording


class FlightLogBoundaryTests(unittest.TestCase):
    def test_rotation_and_split_secret_do_not_leak(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            log = root / "wse2.log"
            log.write_text("PREVIOUS SESSION DO NOT INCLUDE\n" * 500)
            game = subprocess.Popen([sys.executable, "-c", "import time;time.sleep(1.0)"])
            results = []
            errors = []
            def collect():
                try:
                    results.append(record_session(
                        root / "evidence", "rotated", [log],
                        observe_pid=game.pid, poll=0.01, timeout=3,
                        max_log_bytes=4096))
                except BaseException as error:
                    errors.append(error)
            worker = threading.Thread(target=collect)
            worker.start()
            output = root / "evidence" / "rotated"
            try:
                until = time.monotonic() + 2
                while not (output / "recorder-ready.json").exists() and time.monotonic() < until:
                    time.sleep(0.01)
                self.assertTrue((output / "recorder-ready.json").exists())
                with log.open("a") as file:
                    file.write("token=secret-part")
                time.sleep(0.06)
                with log.open("a") as file:
                    file.write("-that-was-split-across-polls\n")
                time.sleep(0.06)
                log.rename(root / "wse2.log.old")
                log.write_text("ZDB1|boot|triggers=35\nFATAL ERROR: rotated log\n")
                game.wait(timeout=3)
                worker.join(timeout=3)
                self.assertFalse(worker.is_alive())
                self.assertFalse(errors)
                self.assertTrue(verify_recording(output)["verified"])
                text = (output / "logs" / "log_01.txt").read_text()
                self.assertIn("FATAL ERROR: rotated log", text)
                self.assertNotIn("PREVIOUS SESSION", text)
                self.assertNotIn("secret-part-that-was-split", text)
                self.assertIn("<REDACTED>", text)
                events = [json.loads(x) for x in
                          (output / "events.jsonl").read_text().splitlines()]
                self.assertIn("log_rotated", [x["event"] for x in events])
                self.assertIsNone(results[0]["exit_code"])
            finally:
                if game.poll() is None:
                    game.terminate()
                    game.wait(timeout=2)
                worker.join(timeout=3)


if __name__ == "__main__":
    unittest.main()
