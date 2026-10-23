"""City incident output bounds; fake events only."""
import sys
from pathlib import Path
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
from city_incidents import incident_for_session, MAX_OBSERVATIONS


class CityIncidentLimits(unittest.TestCase):
    def test_late_event_survives_bounded_read(self):
        boot = {"event": "boot", "source": "logs/log_01.txt", "line": 1, "fields": {}}
        tail = {"event": "wave_change", "source": "logs/log_01.txt",
                "line": MAX_OBSERVATIONS + 1, "fields": {"wave": "9"}}
        report = incident_for_session([boot] * MAX_OBSERVATIONS + [tail],
                                      [], {}, {}, [])
        self.assertEqual(report["runtime"]["wave_numbers"], [9])
        self.assertTrue(report["recording_gap"])
        self.assertEqual(report["timeline"]["engine"]["uninspected_input_records"], 1)

    def test_initial_reinforcement_zero_is_not_a_reinforcement(self):
        beats = [{"event": "heartbeat", "source": "logs/log_01.txt",
                  "line": 2, "fields": {"role": "server", "wave": "1",
                                          "refilled": "0"}}]
        report = incident_for_session(beats, [], {}, {}, [])
        self.assertIsNone(report["runtime"]["last_reinforced_waves"])


if __name__ == "__main__":
    unittest.main()
