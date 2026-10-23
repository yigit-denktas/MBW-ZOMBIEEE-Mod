"""Published B/C examples must not leak real private process metadata."""
import json
from pathlib import Path
import unittest


FIXTURES = Path(__file__).parent / "fixtures"


class ProtocolFixtureTests(unittest.TestCase):
    def read(self, name):
        data = (FIXTURES / name).read_bytes()
        self.assertLess(len(data), 4096)
        self.assertNotIn(b"ZOMBIEEE_RECORDER_CONTROL_KEY", data)
        self.assertNotIn(b"auth_token", data)
        self.assertNotIn(b"host_pid", data)
        self.assertNotIn(b"client_pid", data)
        self.assertNotIn(b"mac", data)
        self.assertNotIn(b"PRIVATE KEY", data)
        return json.loads(data)

    def test_canonical_ready_marker_contains_no_game_success(self):
        data = self.read("recorder_ready_v1.json")
        self.assertEqual(data["schema"], "zombieee.recorder-ready.v1")
        self.assertTrue(data["log_offsets_captured"])
        self.assertTrue(data["watcher_active"])
        self.assertFalse(data["engine_ready"])
        self.assertFalse(data["mission_ready"])
        self.assertEqual(data["recorder_pid"], 424242)  # synthetic sample only

    def test_attachment_ack_is_only_recorder_ack(self):
        data = self.read("recorder_attachment_ack_v1.json")
        self.assertEqual(data["schema"], "zombieee.recorder-attachment-ack.v1")
        self.assertTrue(data["attachment_accepted"])
        self.assertFalse(data["game_ready"])
        self.assertTrue(data["simulation"])
        self.assertEqual(data["game_runtime"], "unknown")

    def test_completion_preserves_null_unobserved_game_metrics(self):
        data = self.read("recorder_completion_v1.json")
        self.assertEqual(data["schema"], "zombieee.flight.v1")
        self.assertEqual(data["outcome"], "stopped")
        self.assertTrue(data["simulation"])
        self.assertEqual(data["game_runtime"], "unknown")
        self.assertIsNone(data["exit_code"])
        self.assertFalse(data["exit_code_observed"])
        self.assertIsNone(data["metrics"]["cpu_seconds"])
        self.assertIsNone(data["metrics"]["peak_memory_kib"])

    def test_incomplete_cannot_be_promoted_to_complete(self):
        data = self.read("recorder_incomplete_v1.json")
        self.assertFalse(data["session_complete"])
        self.assertFalse(data["integrity_verified"])
        self.assertFalse(data["shareable_without_review"])
        self.assertTrue(data["manual_privacy_review_required"])


if __name__ == "__main__":
    unittest.main()
