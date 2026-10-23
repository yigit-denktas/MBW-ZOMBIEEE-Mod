"""Offline diagnostics tests; no engine or network needed."""
import hashlib
import json
import sys
import tempfile
import unittest
import zipfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
from diagnostics import analyze, aggregate, collect, extract_events, read_bundle, scrub, to_markdown


class DiagnosticsTests(unittest.TestCase):
    def make_bundle(self, root, log_text, defenders=4):
        game = root / "game"
        game.mkdir()
        (game / "rgl_log.txt").write_text(log_text, encoding="utf-8")
        mod = root / "module"
        mod.mkdir()
        (mod / "ZOMBIEEE_REMASTER.json").write_text(json.dumps({
            "remaster_version": "0.1.3", "runtime_verified": False,
            "target": "Warband/WSE2", "source_archive_sha256": "abc",
            "experimental_defender_patch": {"experimental_defenders": defenders},
            "preflight": {"ok": True, "mission": {"triggers": 25}},
            "private_path": "C:\\Users\\Secret\\original.rar",
        }))
        bundle = root / "evidence.zip"
        self.assertEqual(collect(game, mod, bundle, [], "smoke-1")["log_count"], 1)
        return bundle

    def test_redaction(self):
        value = ("set_pass_admin hunter2\nUser test@example.com 192.168.1.14:7240 "
                 "76561198012345678 C:\\Users\\Alice\\Documents")
        cleaned = scrub(value)
        for secret in ("hunter2", "test@example.com", "192.168.1.14", "76561198012345678", "Alice"):
            self.assertNotIn(secret, cleaned)

    def test_event_line_numbers(self):
        events = extract_events("ignored\n[info] ZDB1|heartbeat|tick=3|agents=7\n", "logs/a.txt")
        self.assertEqual(events[0]["event"], "heartbeat")
        self.assertEqual(events[0]["fields"]["agents"], "7")
        self.assertEqual(events[0]["line"], 2)

    def test_complete_bundle_with_valid_events(self):
        with tempfile.TemporaryDirectory() as td:
            bundle = self.make_bundle(Path(td),
                "ZDB1|boot|triggers=26\nZDB1|mission_enter|role=server\nZDB1|heartbeat|agents=12\n")
            data = read_bundle(bundle)
            self.assertNotIn("private_path", data["module.json"].decode())
            report = analyze(data)
            self.assertEqual(report["evidence"]["events"], 3)
            self.assertFalse(report["findings"])
            self.assertIn("No known error", to_markdown(report))

    def test_fatal_and_missing_resource(self):
        with tempfile.TemporaryDirectory() as td:
            bundle = self.make_bundle(Path(td), "Unable to open file: bad.brf\nFATAL ERROR: ACCESS VIOLATION\n")
            report = analyze(read_bundle(bundle))
            self.assertEqual(report["status"], "critical")
            self.assertTrue({"R001", "R002"} <= {f["id"] for f in report["findings"]})

    def test_missing_mission_and_trigger_mismatch(self):
        with tempfile.TemporaryDirectory() as td:
            bundle = self.make_bundle(Path(td), "ZDB1|boot|triggers=25\n")
            ids = {f["id"] for f in analyze(read_bundle(bundle))["findings"]}
            self.assertTrue({"R012", "R014"} <= ids)

    def test_tamper_detected(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            bundle = self.make_bundle(root, "ZDB1|boot\n")
            with zipfile.ZipFile(bundle) as z:
                files = {name: z.read(name) for name in z.namelist()}
            files["logs/log_01.txt"] = b"forged"
            altered = root / "forged.zip"
            with zipfile.ZipFile(altered, "w") as z:
                for name, data in files.items():
                    z.writestr(name, data)
            with self.assertRaisesRegex(ValueError, "integrity"):
                read_bundle(altered)

    def test_zip_path_traversal_rejected(self):
        with tempfile.TemporaryDirectory() as td:
            bundle = Path(td) / "unsafe.zip"
            with zipfile.ZipFile(bundle, "w") as z:
                z.writestr("../unexpected.txt", "bad")
                z.writestr("manifest.json", "{}")
            with self.assertRaisesRegex(ValueError, "Unsafe"):
                read_bundle(bundle)

    def test_refuse_overwriting_evidence(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            self.make_bundle(root, "text\n")
            with self.assertRaises(FileExistsError):
                collect(root / "game", root / "module", root / "evidence.zip", [])

    def test_absent_logs_not_success(self):
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / "empty.zip"
            collect(None, None, path, [], "empty")
            self.assertIn("R010", [f["id"] for f in analyze(read_bundle(path))["findings"]])

    def test_manifest_hash(self):
        with tempfile.TemporaryDirectory() as td:
            path = self.make_bundle(Path(td), "ZDB1|boot|triggers=26\n")
            files = read_bundle(path)
            with zipfile.ZipFile(path) as z:
                manifest = json.loads(z.read("manifest.json"))
            self.assertEqual(manifest["sha256"]["events.jsonl"],
                             hashlib.sha256(files["events.jsonl"]).hexdigest())

    def test_oversized_log_retains_boot_and_crash(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            game = root / "game"
            game.mkdir()
            text = ("ZDB1|boot|triggers=26\n" + "harmless filler\n" * 610000 +
                    "FATAL ERROR: ACCESS VIOLATION\n")
            (game / "rgl_log.txt").write_text(text, encoding="utf-8")
            bundle = root / "oversized.zip"
            collect(game, None, bundle, [])
            files = read_bundle(bundle)
            log = files["logs/log_01.txt"].decode()
            self.assertIn("ZDB1|boot|triggers=26", log)
            self.assertIn("FATAL ERROR", log)
            self.assertIn("ZDB1-TRUNCATED", log)
            metadata = json.loads(files["session.json"])
            self.assertEqual(metadata["files"][0]["truncation"], "head_and_tail")

    def test_compare_reports_resolved_faults(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            before = root / "old"; before.mkdir()
            after = root / "new"; after.mkdir()
            old = self.make_bundle(before, "Cannot load resource: missing.brf\n")
            new = self.make_bundle(after,
                "ZDB1|boot|triggers=26\nZDB1|mission_enter\nZDB1|heartbeat\n")
            result = aggregate([old, new])
            self.assertIn("R001", result["resolved_issues_since_first"])
            self.assertFalse(result["new_issues_in_last"])

    def test_server_allies_absent_when_hostiles_present(self):
        with tempfile.TemporaryDirectory() as td:
            bundle = self.make_bundle(Path(td),
                "ZDB1|boot|triggers=26\n"
                "ZDB1|mission_enter|role=server|agents=8|team0=0|team1=8\n"
                "ZDB1|heartbeat|role=server|agents=12|team0=0|team1=12\n")
            report = analyze(read_bundle(bundle))
            self.assertTrue(report["team_evidence"]["available"])
            self.assertIn("R018", {f["id"] for f in report["findings"]})

    def test_missing_team_op_does_not_raise_false_alarm(self):
        with tempfile.TemporaryDirectory() as td:
            bundle = self.make_bundle(Path(td),
                "ZDB1|boot|triggers=26\n"
                "ZDB1|mission_enter|role=server|agents=12|team0=-1|team1=-1\n"
                "ZDB1|heartbeat|role=server|agents=16|team0=-1|team1=-1\n")
            report = analyze(read_bundle(bundle))
            self.assertFalse(report["team_evidence"]["available"])
            self.assertNotIn("R018", {f["id"] for f in report["findings"]})

    def test_invalid_session_label(self):
        with tempfile.TemporaryDirectory() as td:
            with self.assertRaises(ValueError):
                collect(None, None, Path(td) / "a.zip", [], "../../bad")


if __name__ == "__main__":
    unittest.main()
