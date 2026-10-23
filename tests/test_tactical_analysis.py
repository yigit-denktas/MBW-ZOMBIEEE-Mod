"""Offline synthetic tests for conservative WSE2 wave/tactical diagnostics."""
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
from tactical_analysis import analyze_tactical_events


def event(kind, **fields):
    return {"event": kind, "fields": {k: str(v) for k, v in fields.items()}}


class TacticalAnalysisTests(unittest.TestCase):
    def ids(self, records, installed=None):
        return {item["id"] for item in analyze_tactical_events(records, installed or {})["findings"]}

    def test_stalled_wave_flagged(self):
        records = [event("heartbeat", role="server", count=i, wave=4, team1=12,
                         team0=3, mode=0) for i in range(1, 10)]
        self.assertIn("R019", self.ids(records))

    def test_wave_progression_is_not_stalled(self):
        records = [event("heartbeat", role="server", count=i, wave=4 if i <= 5 else 5,
                         team1=12, team0=3, mode=0) for i in range(1, 11)]
        self.assertNotIn("R019", self.ids(records))

    def test_unavailable_wave_never_flagged(self):
        records = [event("heartbeat", role="server", count=i, wave=-1, team1=12)
                   for i in range(1, 30)]
        self.assertNotIn("R019", self.ids(records))

    def test_repeated_mode_switches(self):
        records = [event("tactical_change", tick=i, wave=2, mode=i % 2)
                   for i in range(1, 5)]
        self.assertIn("R020", self.ids(records))

    def test_mode_changes_across_waves_not_thrash(self):
        records = [event("tactical_change", tick=i, wave=i, mode=i % 2)
                   for i in range(1, 5)]
        self.assertNotIn("R020", self.ids(records))

    def test_lingering_fallback_with_healthy_team(self):
        records = [event("heartbeat", role="server", count=i, wave=3, team1=14,
                         team0=5, mode=1) for i in range(1, 4)]
        self.assertIn("R021", self.ids(records, {"tactical_recovery": {"high_water": 3}}))

    def test_idle_guard_is_not_diagnosed_as_stuck(self):
        records = [event("agent_sample", tick=i, id=7, group=5, x=10, y=20)
                   for i in range(1, 10)]
        self.assertNotIn("R022", self.ids(records))

    def test_unchanged_position_after_order_warns(self):
        records = [event("agent_sample", tick=1, id=7, group=5, x=10, y=20),
                   event("tactical_change", tick=2, mode=1, wave=4)]
        records += [event("agent_sample", tick=i, id=7, group=5, x=10, y=20)
                    for i in range(2, 5)]
        self.assertIn("R022", self.ids(records))

    def test_agent_movement_after_order_clears_warning(self):
        records = [event("agent_sample", tick=1, id=7, group=5, x=10, y=20),
                   event("tactical_change", tick=2, mode=1, wave=4)]
        records += [event("agent_sample", tick=i, id=7, group=5, x=10 + i * 2, y=20)
                    for i in range(2, 5)]
        self.assertNotIn("R022", self.ids(records))

    def test_missing_or_malformed_telemetry_is_unknown(self):
        records = [event("agent_sample", tick="?", id=7, group=5, x="bad", y=20),
                   event("heartbeat", role="client", count=4, wave=4, team1=9)]
        report = analyze_tactical_events(records, {})
        self.assertFalse(report["observability"]["position_sampled_agents"])
        self.assertFalse(report["findings"])


if __name__ == "__main__":
    unittest.main()
