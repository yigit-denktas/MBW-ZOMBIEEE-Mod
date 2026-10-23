"""Negative controls for City-only scope: never infer scene from template."""
import json
import sys
from pathlib import Path
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
from diagnostics import analyze


def payload_for(fields):
    events = [
        {"event": "mission_enter", "fields": fields,
         "source": "logs/log_01.txt", "line": 4},
    ]
    return {
        "session.json": json.dumps({"session": "scope-check"}).encode(),
        "module.json": json.dumps({
            "experimental_map_scope": "city-only",
            "remaster_version": "offline-fixture",
        }).encode(),
        "events.jsonl": b"".join(json.dumps(e).encode() + b"\n" for e in events),
        "logs/log_01.txt": b"ZDB1|mission_enter|role=server\n",
    }


class CityScopeEvidenceTests(unittest.TestCase):
    def test_template_name_does_not_prove_scene(self):
        report = analyze(payload_for({
            "role": "server", "template": "mst_multiplayer_iv",
        }))
        self.assertEqual(report["scene_evidence"]["status"], "unknown")
        self.assertFalse(report["scene_evidence"]["available"])
        self.assertNotIn("R029", {f["id"] for f in report["findings"]})

    def test_unknown_scene_getter_does_not_raise_mismatch(self):
        report = analyze(payload_for({
            "role": "server", "scene": "unknown",
        }))
        self.assertEqual(report["scene_evidence"]["status"], "unknown")
        self.assertNotIn("R029", {f["id"] for f in report["findings"]})

    def test_confirmed_city_identifier_is_observed(self):
        report = analyze(payload_for({
            "role": "server", "scene": "scn_tbfc_invasion_4",
        }))
        self.assertEqual(report["scene_evidence"]["status"], "observed")
        self.assertEqual(report["scene_evidence"]["observed_scenes"], ["tbfc_invasion_4"])
        self.assertNotIn("R029", {f["id"] for f in report["findings"]})

    def test_explicit_noncity_scene_is_candidate_mismatch(self):
        report = analyze(payload_for({
            "role": "server", "scene": "scn_tbfc_invasion_3",
        }))
        self.assertEqual(report["scene_evidence"]["status"], "mismatch_observed")
        finding = next(f for f in report["findings"] if f["id"] == "R029")
        self.assertEqual(finding["severity"], "medium")
        self.assertEqual(finding["examples"][0]["line"], 4)
        self.assertIn("cause_unknown", finding["confidence"])


if __name__ == "__main__":
    unittest.main()
