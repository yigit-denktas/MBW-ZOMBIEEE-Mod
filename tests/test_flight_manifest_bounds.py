"""Fail closed on oversized or unsafe private metadata before ZIP import."""
import json
from pathlib import Path
import sys
import tempfile
import unittest

from telemetry.flight_recorder import record_session, verify_recording, safe_launcher_receipt


class ManifestBoundsTests(unittest.TestCase):
    def test_too_large_launcher_receipt_rejected_without_parsing(self):
        with tempfile.TemporaryDirectory() as tmp:
            file = Path(tmp) / "receipt.json"
            file.write_text("x" * (16 * 1024 + 1), encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "Oversized"):
                safe_launcher_receipt(file)

    def test_redirected_launcher_receipt_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            real = base / "real.json"
            real.write_text('{"schema":"zombieee.session.v1"}')
            alias = base / "alias.json"
            try:
                alias.symlink_to(real)
            except (OSError, NotImplementedError) as e:
                self.skipTest(type(e).__name__)
            with self.assertRaisesRegex(ValueError, "Unsafe"):
                safe_launcher_receipt(alias)

    def test_oversized_recorder_manifest_is_not_read_as_valid(self):
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            record_session(base, "big", [], command=[sys.executable, "-c", "pass"])
            (base / "big" / "manifest.json").write_bytes(b" " * (1024 * 1024 + 1))
            with self.assertRaisesRegex(ValueError, "Oversized"):
                verify_recording(base / "big")

    def test_non_sha_hex_digest_is_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            record_session(base, "hash", [], command=[sys.executable, "-c", "pass"])
            path = base / "hash" / "manifest.json"
            manifest = json.loads(path.read_text())
            manifest["sha256"]["recorder.json"] = "unexpected"
            path.write_text(json.dumps(manifest))
            with self.assertRaisesRegex(ValueError, "digest metadata"):
                verify_recording(base / "hash")


if __name__ == "__main__":
    unittest.main()
