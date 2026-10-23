"""Durable event journal has linear append cost and explicit event drop counts."""
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

from telemetry.flight_recorder import record_session, verify_recording, atomic_write


class EventJournalTests(unittest.TestCase):
    def test_events_append_individually_not_rewrite_whole_stream(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            writes = []
            def track(path, data):
                writes.append(path.name)
                return atomic_write(path, data)
            with patch("telemetry.flight_recorder.atomic_write", side_effect=track):
                report = record_session(root, "append", [],
                    command=[sys.executable, "-c", "pass"], poll=.01,
                    timeout=3, simulation=True)
            self.assertNotIn("events.jsonl", writes)
            event_lines = (root / "append" / "events.jsonl").read_text().splitlines()
            names = [json.loads(line)["event"] for line in event_lines]
            self.assertIn("recorder_ready", names)
            self.assertIn("process_started", names)
            self.assertIn("process_finished", names)
            self.assertEqual(report["event_count"], len(names))
            self.assertTrue(verify_recording(root / "append")["verified"])

    def test_events_cap_marks_omitted_events_in_receipt(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            report = record_session(root, "bounded", [],
                command=[sys.executable, "-c", "pass"], poll=.01,
                timeout=3, max_events=2)
            lines = (root / "bounded" / "events.jsonl").read_text().splitlines()
            self.assertEqual(len(lines), 2)
            self.assertGreater(report["event_drops"], 0)
            self.assertTrue(verify_recording(root / "bounded")["verified"])


if __name__ == "__main__":
    unittest.main()
