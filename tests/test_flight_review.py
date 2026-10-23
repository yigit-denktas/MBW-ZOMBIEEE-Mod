"""Agent A C-1/C-2/C-3 regressions. Offline/fake child only."""
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import threading
import time
import unittest

from telemetry.flight_recorder import record_session, verify_recording, scrub_bounded
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
from diagnostics import collect, read_bundle, analyze


class AgentAReviewTests(unittest.TestCase):
    def test_late_crash_survives_gap_and_retention_is_bounded(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            log = root / "wse2.log"
            log.write_text("stale\n")
            script = (
                "import pathlib,sys,os;"
                "p=pathlib.Path(sys.argv[1]);"
                "p.open('ab').write(b'ZDB1|boot|triggers=35\\n' + b'x'*(3*1024*1024)"
                " + b'\\nFATAL ERROR: late crash\\n');"
                "os._exit(19)"
            )
            receipt = record_session(root / "out", "tail", [log],
                command=[sys.executable, "-c", script, str(log)],
                timeout=5, poll=0.01, max_log_bytes=4096)
            folder = root / "out" / "tail"
            saved = (folder / "logs" / "log_01.txt").read_text()
            self.assertIn("ZDB1|boot|triggers=35", saved)
            self.assertIn("FATAL ERROR: late crash", saved)
            self.assertNotIn("stale", saved)
            self.assertIn("[ZDB1-OMITTED ", saved)
            self.assertLessEqual(len(saved.encode()), 4096)
            self.assertGreater(receipt["log_omitted_bytes"][0], 0)
            self.assertEqual(receipt["exit_code"], 19)
            self.assertTrue(verify_recording(folder)["verified"])
            target = root / "safe.zip"
            collect(None, None, target, [], "tail", flight_root=folder)
            findings = {row["id"] for row in analyze(read_bundle(target))["findings"]}
            self.assertIn("R002", findings)
            self.assertIn("R028", findings)

    def test_early_child_crash_is_after_ready_handshake(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            folder = root / "out" / "handshake"
            script = (
                "import json,pathlib,os,sys;"
                "ready=json.loads(pathlib.Path(sys.argv[1]).read_text());"
                "assert ready['schema']=='zombieee.recorder_ready.v1';"
                "assert ready['attempt_id']=='attempt-03';"
                "assert ready['log_offsets_captured'] is True;"
                "assert ready['engine_ready'] is False;"
                "print('TOKEN=fake-secret',flush=True);"
                "os._exit(17)"
            )
            receipt = record_session(root / "out", "handshake", [],
                command=[sys.executable, "-c", script, str(folder / "recorder-ready.json")],
                attempt_id="attempt-03", timeout=5, poll=0.01)
            ready = json.loads((folder / "recorder-ready.json").read_text())
            self.assertEqual(ready["session_id"], "handshake")
            self.assertEqual(ready["recorder_pid"], os.getpid())
            self.assertTrue(ready["watcher_active"])
            self.assertEqual(receipt["exit_code"], 17)
            events = [json.loads(l) for l in (folder / "events.jsonl").read_text().splitlines()]
            names = [e["event"] for e in events]
            self.assertLess(names.index("recorder_ready"), names.index("process_started"))
            self.assertTrue(verify_recording(folder)["verified"])

    def test_external_launcher_can_wait_for_ready_before_child(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            game_log = root / "game.log"
            game_log.write_text("old\n")
            launcher = subprocess.Popen([sys.executable, "-c", "import time;time.sleep(10)"])
            errors, results = [], []
            folder = root / "out" / "standby"
            def worker():
                try:
                    results.append(record_session(root / "out", "standby", [game_log],
                        observe_pid=launcher.pid, attempt_id="retry-1",
                        timeout=4, poll=0.01))
                except Exception as error:
                    errors.append(error)
            thread = threading.Thread(target=worker)
            try:
                thread.start()
                deadline = time.monotonic() + 2
                while not (folder / "recorder-ready.json").is_file() and time.monotonic() < deadline:
                    time.sleep(0.01)
                self.assertTrue((folder / "recorder-ready.json").exists())
                ready = json.loads((folder / "recorder-ready.json").read_text())
                self.assertEqual(ready["attempt_id"], "retry-1")
                self.assertTrue(ready["log_offsets_captured"])
                # Simulate Agent B now spawning the game, after recorder-ready.
                with game_log.open("a") as out:
                    out.write("ZDB1|boot|triggers=35\nFATAL ERROR: immediate\n")
                time.sleep(0.07)
            finally:
                launcher.terminate()
                launcher.wait(timeout=2)
                thread.join(timeout=3)
            self.assertFalse(thread.is_alive())
            self.assertFalse(errors)
            self.assertEqual(results[0]["outcome"], "disappeared_exit_code_unknown")
            self.assertIsNone(results[0]["exit_code"])
            self.assertIn("FATAL ERROR", (folder / "logs" / "log_01.txt").read_text())
            self.assertTrue(verify_recording(folder)["verified"])

    def test_intermediate_symlink_rejected_before_verification_and_zip(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            record_session(root / "out", "links", [], command=[sys.executable, "-c", "pass"])
            folder = root / "out" / "links"
            logs = folder / "logs"
            logs.rmdir()
            target = root / "elsewhere"
            target.mkdir()
            try:
                logs.symlink_to(target, target_is_directory=True)
            except (OSError, NotImplementedError) as error:
                self.skipTest(f"Symlink privilege unavailable: {type(error).__name__}")
            with self.assertRaisesRegex(ValueError, "link|reparse"):
                verify_recording(folder)
            with self.assertRaisesRegex(ValueError, "link|reparse"):
                collect(None, None, root / "danger.zip", [], "links", flight_root=folder)
            self.assertFalse((root / "danger.zip").exists())

    def test_owned_child_stdout_and_stderr_are_bounded_and_redacted(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            program = (
                "import sys,os;"
                "sys.stdout.write('chat: ExamplePlayer says hello\\n'+'x'*10000"
                "+'\\nFATAL ERROR: stdout crash\\n');"
                "sys.stderr.write('token=verysecret123\\nWARN: stderr recorded\\n');"
                "sys.stdout.flush();sys.stderr.flush();os._exit(6)"
            )
            receipt = record_session(root / "out", "pipes", [],
                command=[sys.executable, "-c", program],
                max_log_bytes=512, timeout=5, poll=0.01)
            folder = root / "out" / "pipes"
            stdout = (folder / "logs" / "stdout.txt").read_text()
            stderr = (folder / "logs" / "stderr.txt").read_text()
            self.assertIn("FATAL ERROR: stdout crash", stdout)
            self.assertIn("[ZDB1-OMITTED ", stdout)
            self.assertNotIn("ExamplePlayer", stdout)
            self.assertLessEqual(len(stdout.encode()), 512)
            self.assertNotIn("verysecret123", stderr)
            self.assertIn("WARN", stderr)
            self.assertGreater(receipt["process_output_omitted_bytes"]["stdout"], 0)
            self.assertTrue(receipt["process_output_capture_complete"])
            self.assertTrue(verify_recording(folder)["verified"])
            target = root / "pipe.zip"
            collect(None, None, target, [], "pipes", flight_root=folder)
            report = analyze(read_bundle(target))
            self.assertIn("R002", {f["id"] for f in report["findings"]})

    def test_redaction_expansion_stays_under_byte_cap(self):
        # A six-character email becomes a seven-character redaction marker;
        # repeated replacements must not break the configured output bound.
        raw = (b"ZDB1|boot\\n" + b"x@y.co " * 1000 +
               b"\\nFATAL ERROR: preserved at tail\\n")
        saved, extra = scrub_bounded(raw, 128)
        self.assertLessEqual(len(saved), 128)
        self.assertGreater(extra, 0)
        self.assertIn(b"FATAL ERROR", saved)
        self.assertNotIn(b"x@y.co", saved)
        self.assertIn(b"ZDB1-OMITTED", saved)

    def test_start_failure_does_not_fake_game_run(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            with self.assertRaises(OSError):
                record_session(root / "out", "start-error", [],
                    command=[str(root / "cannot-run-this-foo")], timeout=2)
            folder = root / "out" / "start-error"
            meta = json.loads((folder / "recorder.json").read_text())
            self.assertEqual(meta["outcome"], "start_failed")
            self.assertIsNone(meta["exit_code"])
            self.assertTrue(verify_recording(folder)["verified"])


if __name__ == "__main__":
    unittest.main()
