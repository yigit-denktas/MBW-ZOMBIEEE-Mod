"""Archive audit tests use fixtures, not copied original game assets."""
from pathlib import Path
import os
import hashlib
import subprocess
import sys
import tempfile
import unittest
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
from archive_audit import RAR4_MAGIC, inspect_original_archive, ORIGINAL_SHA256, ORIGINAL_SIZE


def fixture(path, content=None):
    value = content if content is not None else RAR4_MAGIC + b"synthetic-only"
    path.write_bytes(value)
    return {"expected_size": len(value), "expected_sha256": hashlib.sha256(value).hexdigest()}


class ArchiveAuditTests(unittest.TestCase):
    def test_identity_never_claims_crc(self):
        with tempfile.TemporaryDirectory() as td:
            p = Path(td) / "original.rar"
            args = fixture(p)
            r = inspect_original_archive(p, **args)
            self.assertTrue(r["identity_ok"])
            self.assertEqual(r["crc_status"], "not_checked")
            self.assertFalse(r["runtime_verified"])
            self.assertNotIn(str(td), str(r))

    def test_original_hash_and_size_constants_pinned(self):
        self.assertEqual(ORIGINAL_SHA256, "9be100ff41ce6f8ebadd4aa27377f70f402883fab271999a8cab8cc1da001d1e")
        self.assertEqual(ORIGINAL_SIZE, 167493071)

    def test_wrong_magic_rejected_even_when_checksum_matches(self):
        with tempfile.TemporaryDirectory() as td:
            p = Path(td) / "x.rar"
            args = fixture(p, b"notRAR")
            self.assertIn("not_rar4", inspect_original_archive(p, **args)["problems"])

    def test_wrong_sha_and_size_block_crc_subprocess(self):
        with tempfile.TemporaryDirectory() as td:
            p = Path(td) / "x.rar"
            args = fixture(p)
            args["expected_sha256"] = "0" * 64
            args["expected_size"] += 1
            with mock.patch("archive_audit.subprocess.run") as run:
                r = inspect_original_archive(p, verify_crc=True, seven_zip="7z", **args)
            run.assert_not_called()
            self.assertEqual(r["crc_status"], "blocked_identity")
            self.assertIn("sha256_mismatch", r["problems"])
            self.assertIn("size_mismatch", r["problems"])

    def test_crc_success_uses_no_extraction(self):
        with tempfile.TemporaryDirectory() as td:
            p = Path(td) / "x.rar"
            args = fixture(p)
            with mock.patch("archive_audit.subprocess.run", return_value=mock.Mock(returncode=0)) as run:
                r = inspect_original_archive(p, verify_crc=True, seven_zip="7z", **args)
            self.assertEqual(r["crc_status"], "verified")
            cmd = run.call_args.args[0]
            self.assertEqual(cmd[:3], ["7z", "t", "-bd"])
            self.assertNotIn("x", cmd[:3])

    def test_crc_failure_and_timeout_are_not_success(self):
        with tempfile.TemporaryDirectory() as td:
            p = Path(td) / "x.rar"
            args = fixture(p)
            with mock.patch("archive_audit.subprocess.run", return_value=mock.Mock(returncode=2)):
                self.assertEqual(inspect_original_archive(p, verify_crc=True, seven_zip="7z", **args)["crc_status"], "failed")
            with mock.patch("archive_audit.subprocess.run", side_effect=subprocess.TimeoutExpired("7z", 10)):
                self.assertEqual(inspect_original_archive(p, verify_crc=True, seven_zip="7z", **args)["crc_status"], "timeout")

    def test_missing_archive_and_missing_7zip(self):
        with tempfile.TemporaryDirectory() as td:
            p = Path(td) / "not_there.rar"
            self.assertIn("source_not_regular_file", inspect_original_archive(p)["problems"])
            args = fixture(p)
            with mock.patch("archive_audit.find_7zip", return_value=None):
                r = inspect_original_archive(p, verify_crc=True, **args)
            self.assertEqual(r["crc_status"], "unavailable")
            self.assertIn("seven_zip_unavailable", r["problems"])

    def test_original_user_archive_identity_if_present(self):
        original = Path(os.environ.get("ZOMBIEEE_ORIGINAL_ARCHIVE", "/mnt/data/ZOMBIEEEBeta04.rar"))
        if not original.is_file():
            self.skipTest("Original archive not mounted")
        report = inspect_original_archive(original)
        self.assertTrue(report["identity_ok"])
        self.assertEqual(report["crc_status"], "not_checked")


if __name__ == "__main__":
    unittest.main()
