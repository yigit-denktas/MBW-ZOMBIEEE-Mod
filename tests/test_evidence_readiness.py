"""Conservative final-WSE2-session acceptance evidence matrix tests."""
import sys
import unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
from evidence_readiness import matrix_for_session


def ev(name, **data):
    return {"event": name, "fields": {k: str(v) for k, v in data.items()}}


class EvidenceReadinessTests(unittest.TestCase):
    def state(self, matrix, name):
        return matrix["checks"][name]["status"]

    def test_zero_evidence_is_unknown_not_pass(self):
        report = matrix_for_session([], [], {}, 0, {"observability": {}, "observed_kill_increments": 0})
        self.assertEqual(self.state(report, "engine_boot_event"), "unknown")
        self.assertEqual(self.state(report, "wave_progression"), "unknown")
        self.assertEqual(self.state(report, "ai_kills_increased"), "unknown")
        self.assertEqual(self.state(report, "fatal_error_in_log"), "unknown")

    def test_observed_progression_is_not_claimed_wave_completion(self):
        events = [ev("boot"), ev("mission_enter")]
        events += [ev("heartbeat", role="server", count=i, wave=i,
                      team0=4, team1=20) for i in (1, 2, 3)]
        report = matrix_for_session(events, [], {}, 1,
                                    {"observability": {"combat_samples": 0},
                                     "observed_kill_increments": 0})
        self.assertEqual(report["observed_waves"], [1, 2, 3])
        self.assertEqual(self.state(report, "wave_progression"), "observed")
        self.assertEqual(self.state(report, "zombies_visible"), "observed")
        self.assertEqual(self.state(report, "reserved_ai_seen"), "unknown")

    def test_allied_evidence_requires_real_samples(self):
        data = {"observability": {"combat_samples": 6}, "observed_kill_increments": 3}
        report = matrix_for_session([ev("combat_sample")], [], {}, 1, data)
        self.assertEqual(self.state(report, "reserved_ai_seen"), "observed")
        self.assertEqual(self.state(report, "ai_kills_increased"), "observed")

    def test_fallback_followed_by_regroup_is_observed(self):
        events = [ev("tactical_change", mode=0), ev("tactical_change", mode=1),
                  ev("tactical_change", mode=0), ev("command_exec", cmd="zdr_cmd_heal")]
        report = matrix_for_session(events, [], {"difficulty": "story"}, 1,
                                    {"observability": {}, "observed_kill_increments": 0})
        self.assertEqual(self.state(report, "fallback_entered"), "observed")
        self.assertEqual(self.state(report, "regroup_after_fallback"), "observed")
        self.assertEqual(self.state(report, "private_command_executed"), "observed")
        self.assertEqual(report["build_flags"]["difficulty"], "story")

    def test_absence_of_crash_pattern_is_not_a_stability_pass(self):
        data = {"observability": {}, "observed_kill_increments": 0}
        report = matrix_for_session([], [], {}, 1, data)
        self.assertEqual(self.state(report, "fatal_error_in_log"), "not_detected")
        crash = matrix_for_session([], [{"id": "R002"}], {}, 1, data)
        self.assertEqual(self.state(crash, "fatal_error_in_log"), "detected")


if __name__ == "__main__":
    unittest.main()
