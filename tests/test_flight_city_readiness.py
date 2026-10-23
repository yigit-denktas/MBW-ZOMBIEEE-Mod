"""Reject false-positive server/City readiness from synthetic Lua markers."""
import json
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
from evidence_readiness import matrix_for_session, capability_snapshot
from city_incidents import incident_for_session


def event(kind, **fields):
    return {"event": kind, "fields": fields, "source": "logs/log_01.txt", "line": 1}


def matrix(events):
    return matrix_for_session(events, [], {"experimental_map_scope": "city-only"},
                              1, {"observability": {}})["checks"]


class CityReadinessTests(unittest.TestCase):
    def test_client_invasion_does_not_prove_server_entry(self):
        ev = [event("mission_enter", role="client", template="multiplayer_iv",
                    scene="scn_tbfc_invasion_4")]
        checks = matrix(ev)
        self.assertEqual(checks["invasion_mission_entered"]["status"], "unknown")
        self.assertEqual(checks["city_scene_observed"]["status"], "unknown")
        city = incident_for_session(ev, [], {}, {}, [])
        self.assertEqual(city["runtime"]["server_city_entry"], "unknown")

    def test_server_wrong_template_with_city_scene_is_not_invasion(self):
        ev = [event("mission_enter", role="server", template="multiplayer_tdm",
                    scene="scn_tbfc_invasion_4")]
        checks = matrix(ev)
        self.assertEqual(checks["invasion_mission_entered"]["status"], "unknown")
        self.assertEqual(checks["city_scene_observed"]["status"], "unknown")
        city = incident_for_session(ev, [], {}, {}, [])
        self.assertEqual(city["runtime"]["server_city_entry"], "unknown")

    def test_server_invasion_without_scene_is_not_city(self):
        ev = [event("mission_enter", role="server",
                    template="mst_multiplayer_iv")]
        checks = matrix(ev)
        self.assertEqual(checks["invasion_mission_entered"]["status"], "observed")
        self.assertEqual(checks["city_scene_observed"]["status"], "unknown")
        city = incident_for_session(ev, [], {}, {}, [])
        self.assertEqual(city["runtime"]["server_city_entry"], "unknown")

    def test_explicit_server_invasion_city_is_observed_marker_only(self):
        ev = [event("mission_enter", role="server", template="multiplayer_iv",
                    scene="scn_tbfc_invasion_4")]
        checks = matrix(ev)
        self.assertEqual(checks["invasion_mission_entered"]["status"], "observed")
        self.assertEqual(checks["city_scene_observed"]["status"], "observed")
        city = incident_for_session(ev, [], {}, {}, [])
        self.assertEqual(city["runtime"]["server_city_entry"], "observed_marker")
        self.assertFalse(city["runtime"]["gameplay_verified"])

    def test_wrong_template_heartbeat_cannot_fake_waves_or_zombies(self):
        ev = [event("heartbeat", role="server", template="multiplayer_dm",
                    wave="2", team1="10"),
              event("heartbeat", role="server", template="multiplayer_dm",
                    wave="3", team1="12")]
        checks = matrix(ev)
        self.assertEqual(checks["zombies_visible"]["status"], "unknown")
        self.assertEqual(checks["wave_progression"]["status"], "unknown")

    def test_server_invasion_heartbeat_can_attest_wave_markers(self):
        ev = [event("heartbeat", role="server", template="mst_multiplayer_iv",
                    wave="2", team1="9"),
              event("heartbeat", role="server", template="mst_multiplayer_iv",
                    wave="3", team1="11")]
        checks = matrix(ev)
        self.assertEqual(checks["zombies_visible"]["status"], "observed")
        self.assertEqual(checks["wave_progression"]["status"], "observed")
        self.assertEqual(checks["invasion_mission_entered"]["status"], "unknown")

    def test_malformed_client_events_are_not_observations(self):
        ev = [event("mission_enter", role="server", template=True, scene="scn_tbfc_invasion_4"),
              {"event": "heartbeat", "fields": None},
              {"event": "heartbeat", "fields": [], "source": "logs/log_01.txt"}]
        checks = matrix(ev)
        self.assertEqual(checks["city_scene_observed"]["status"], "unknown")
        self.assertEqual(checks["wave_progression"]["status"], "unknown")


if __name__ == "__main__":
    unittest.main()
