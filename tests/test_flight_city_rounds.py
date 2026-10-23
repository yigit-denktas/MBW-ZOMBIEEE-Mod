"""Round-aware incident tests: source claims are not runtime global reads."""
import json
import sys
from pathlib import Path
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
from city_incidents import incident_for_session
from diagnostics import analyze


def beat(line, *, wave, round_start=None, refilled_round_start=None):
    fields = {"role": "server", "wave": str(wave), "team0": "4"}
    if round_start is not None:
        fields["round_start"] = str(round_start)
    if refilled_round_start is not None:
        fields["refilled_round_start"] = str(refilled_round_start)
    return {"event": "heartbeat", "fields": fields,
            "source": "logs/log_01.txt", "line": line}


class CityRoundEvidenceTests(unittest.TestCase):
    def test_new_round_may_restart_at_lower_wave(self):
        events = [beat(1, wave=4, round_start=120, refilled_round_start=120),
                  beat(2, wave=1, round_start=260, refilled_round_start=120)]
        report = incident_for_session(events, [], {}, {}, [])
        ids = {lead["code"] for lead in report["incident_leads"]}
        self.assertNotIn("CITY-I04", ids)
        self.assertEqual(report["runtime"]["round_start_observations"], [120, 260])
        self.assertEqual(report["runtime"]["last_reinforced_round_starts"], [120])
        self.assertFalse(report["runtime"]["round_aware_reinforcement_verified"])

    def test_identical_wave_in_two_rounds_is_not_one_round_progress(self):
        events = [beat(1, wave=2, round_start=100),
                  beat(2, wave=2, round_start=200)]
        report = incident_for_session(events, [], {}, {}, [])
        self.assertEqual(report["runtime"]["repeated_wave_across_distinct_rounds"], [2])
        self.assertEqual(report["runtime"]["wave_progression_within_one_round"], "unknown")
        self.assertEqual(report["runtime"]["round_identity"], "observed_engine_global")

    def test_two_waves_in_one_observed_round_prove_markers_only(self):
        events = [beat(1, wave=2, round_start=100),
                  beat(2, wave=3, round_start=100)]
        report = incident_for_session(events, [], {}, {}, [])
        self.assertEqual(report["runtime"]["wave_progression_within_one_round"],
                         "observed_markers")
        self.assertFalse(report["runtime"]["gameplay_verified"])

    def test_decreasing_wave_without_round_marker_is_inconclusive(self):
        events = [beat(1, wave=4), beat(2, wave=1)]
        report = incident_for_session(events, [], {}, {}, [])
        lead = next(x for x in report["incident_leads"] if x["code"] == "CITY-I04")
        self.assertEqual(lead["cause"], "unknown")
        self.assertIn("round_start_global_unobserved", report["unknowns"])

    def test_missing_getters_and_source_receipt_never_create_round_observation(self):
        source = {
            "experimental_map_scope": "city-only",
            "city_static_acceptance": {
                "checks": {"round_start_identity_or_guard": True},
                "original_invasion_game_type": 7},
            "city_final_acceptance": {"passed": True},
        }
        events = [beat(1, wave=2, round_start=-1, refilled_round_start=-1)]
        report = incident_for_session(events, [], source, {}, [])
        self.assertTrue(report["build"]["source_receipt_claims_passed"])
        self.assertFalse(report["build"]["round_aware_source_contract_verified"])
        self.assertEqual(report["runtime"]["round_identity"], "unknown")
        self.assertIsNone(report["runtime"]["round_start_observations"])
        self.assertIsNone(report["runtime"]["last_reinforced_round_starts"])

    def test_lua_round_fields_are_optional_measured_values(self):
        fields = {"role": "server", "wave": "2",
                  "round_start": "400", "refilled_round_start": "395"}
        data = {
            "events.jsonl": (json.dumps({"event": "heartbeat", "fields": fields,
                                        "source": "logs/log_01.txt",
                                        "line": 2}) + "\n").encode(),
            "logs/log_01.txt": b"ZDB1|heartbeat|role=server",
        }
        city = analyze(data)["city_incident"]
        self.assertEqual(city["runtime"]["round_start_observations"], [400])
        self.assertEqual(city["runtime"]["last_reinforced_round_starts"], [395])
        self.assertFalse(city["runtime"]["round_aware_reinforcement_verified"])


if __name__ == "__main__":
    unittest.main()
