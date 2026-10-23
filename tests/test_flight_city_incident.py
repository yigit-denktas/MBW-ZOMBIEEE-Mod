"""City incident source-versus-runtime tests; synthetic evidence only."""
import json
from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
from diagnostics import analyze, to_markdown


def event(kind, line, **fields):
    return {"event": kind, "fields": fields, "source": "logs/log_01.txt", "line": line}


def source():
    return {"experimental_map_scope": "city-only",
            "city_static_acceptance": {
                "checks": {"native_guard": True, "original_prefix": True},
                "original_invasion_game_type": 7, "runtime_verified": False},
            "city_final_acceptance": {"passed": True, "runtime_verified": False}}


def payload(events=(), module=None):
    return {"session.json": b'{"session":"synthetic"}',
            "module.json": json.dumps(module or {}).encode(),
            "events.jsonl": "".join(json.dumps(e) + "\n" for e in events).encode(),
            "logs/log_01.txt": b"ZDB1|boot|triggers=31\n"}


class CityIncidentTests(unittest.TestCase):
    def test_build_check_is_not_gameplay(self):
        ev = [event("mission_enter", 1, role="server", scene="scn_tbfc_invasion_4"),
              event("heartbeat", 2, role="server", wave="2", team0="4", team1="9"),
              event("wave_change", 3, wave="3")]
        report = analyze(payload(ev, source()))
        city = report["city_incident"]
        self.assertTrue(city["build"]["source_verified"])
        self.assertFalse(city["runtime"]["gameplay_verified"])
        self.assertEqual(city["runtime"]["wave_numbers"], [2, 3])
        self.assertEqual(city["runtime"]["survivor_team0_max"], 4)
        self.assertIn("City incident timeline", to_markdown(report))

    def test_missing_telemetry_remains_unknown(self):
        city = analyze(payload())["city_incident"]
        self.assertEqual(city["runtime"]["wave_progression"], "unknown")
        self.assertIsNone(city["runtime"]["survivor_team0_max"])
        self.assertIsNone(city["runtime"]["scene"])

    def test_source_game_type_six_is_not_runtime_fact(self):
        module = source()
        module["city_static_acceptance"]["original_invasion_game_type"] = 6
        city = analyze(payload(module=module))["city_incident"]
        self.assertFalse(city["build"]["source_verified"])
        self.assertIn("CITY-I06", {e["code"] for e in city["incident_leads"]})
        self.assertTrue(all(e["cause"] == "unknown" for e in city["incident_leads"]))


    def test_scene_mismatch_requires_measured_scene(self):
        wrong = [event("mission_enter", 1, role="server", scene="scn_tbfc_invasion_3")]
        city = analyze(payload(wrong, source()))["city_incident"]
        self.assertIn("CITY-I07", {x["code"] for x in city["incident_leads"]})
        desired = [event("mission_enter", 1, role="server", template="multiplayer_iv")]
        city = analyze(payload(desired, source()))["city_incident"]
        self.assertNotIn("CITY-I07", {x["code"] for x in city["incident_leads"]})


if __name__ == "__main__":
    unittest.main()
