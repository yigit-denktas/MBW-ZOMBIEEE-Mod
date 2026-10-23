"""Negative controls for false certainty and privacy leak reporting."""
import sys
from pathlib import Path
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
from diagnostics import privacy_audit, scrub
from evidence_readiness import capability_snapshot


class PrivacyAndCapabilitiesTests(unittest.TestCase):
    def test_clean_privacy_scan_still_requires_manual_review(self):
        report = privacy_audit({"logs/log_01.txt": b"ordinary ZDB1 log\n"})
        self.assertEqual(report["automatic_review"], "no_known_patterns_found")
        self.assertTrue(report["manual_review_required"])

    def test_unredacted_private_evidence_is_flagged_without_values(self):
        log = b"email=person@example.com address=192.168.1.2\n"
        report = privacy_audit({"logs/log_01.txt": log})
        self.assertEqual(report["automatic_review"], "potential_disclosure")
        self.assertEqual(report["potential_patterns"]["email"], 1)
        self.assertEqual(report["potential_patterns"]["ipv4"], 1)
        self.assertNotIn("person@", repr(report))
        self.assertNotIn("192.168.", repr(report))

    def test_scrub_then_audit_has_no_ordinary_email_or_ip(self):
        safe = scrub("person@example.com 192.168.1.2").encode()
        report = privacy_audit({"logs/log_01.txt": safe})
        self.assertEqual(report["potential_patterns"]["email"], 0)
        self.assertEqual(report["potential_patterns"]["ipv4"], 0)

    def test_missing_capabilities_stay_unknown(self):
        result = capability_snapshot([])
        self.assertEqual(result["status"], "unknown")
        self.assertEqual(result["bindings"]["kills_getter"], "unknown")

    def test_binding_presence_is_not_measurement_success(self):
        events = [{
            "event": "recorder_capabilities", "fields": {
                "team_getter": "1", "kills_getter": "0",
                "ammo_getter": "-1", "max_defenders": "16",
                "sampling_interval_s": "15", "max_heartbeats": "480",
            }}]
        result = capability_snapshot(events)
        self.assertEqual(result["bindings"]["team_getter"], "binding_present")
        self.assertEqual(result["bindings"]["kills_getter"], "binding_absent")
        self.assertEqual(result["bindings"]["ammo_getter"], "unknown")
        self.assertEqual(result["limits"]["max_defenders"], 16)
        self.assertNotIn("passed", repr(result))


if __name__ == "__main__":
    unittest.main()
