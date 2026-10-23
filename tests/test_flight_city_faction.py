"""WSE2 real-boot Invalid Faction ID signature; synthetic offline logs only."""
from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
from diagnostics import analyze
from city_incidents import incident_for_session


class CityInvalidFactionTests(unittest.TestCase):
    def test_engine_invalid_faction_id_minus_one_is_high_noncausal_lead(self):
        log = ("Starting map tbfc_invasion_4 in mode multiplayer_iv\n"
               "SCRIPT ERROR: Invalid Faction ID: -1\n"
               "Mission Template [44] mst_multiplayer_iv Trigger [14] "
               "Consequences (opcode 502)\n")
        report = analyze({"logs/log_01.txt": log.encode()})
        match = next(f for f in report["findings"] if f["id"] == "R030")
        self.assertEqual(match["severity"], "high")
        self.assertEqual(match["examples"][0]["file"], "logs/log_01.txt")
        incident = next(f for f in report["city_incident"]["incident_leads"]
                        if f["code"] == "CITY-I08")
        self.assertEqual(incident["cause"], "unknown")
        self.assertEqual(report["city_incident"]["runtime"]["server_city_entry"], "unknown")
        self.assertFalse(report["city_incident"]["runtime"]["gameplay_verified"])

    def test_other_faction_error_or_only_source_receipt_does_not_trigger(self):
        for text in ("Invalid Faction ID: 2\n",
                     "mission_template=multiplayer_iv\n",
                     "g_multiplayer_game_type=7\n"):
            with self.subTest(text=text):
                report = analyze({"logs/log_01.txt": text.encode()})
                self.assertNotIn("R030", {f["id"] for f in report["findings"]})
                self.assertNotIn("CITY-I08",
                                 {f["code"] for f in report["city_incident"]["incident_leads"]})

    def test_known_faction_finding_never_certifies_native_cause(self):
        report = incident_for_session([], [], {}, {}, [{"id": "R030"}])
        lead = next(f for f in report["incident_leads"] if f["code"] == "CITY-I08")
        self.assertEqual(lead["cause"], "unknown")
        self.assertFalse(report["runtime"]["gameplay_verified"])


if __name__ == "__main__":
    unittest.main()
