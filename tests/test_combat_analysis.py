"""Synthetic evidence tests for conservative combat and private command analysis."""
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
from combat_analysis import analyze_combat_events


def e(name, **kv):
    return {"event": name, "fields": {k: str(v) for k, v in kv.items()}}


class CombatAnalysisTests(unittest.TestCase):
    def codes(self, records, installed=None):
        return {f["id"] for f in analyze_combat_events(records, installed or {})["findings"]}

    def beats(self, n=8, zombies=12):
        return [e("heartbeat", role="server", count=i, wave=3, team0=5, team1=zombies)
                for i in range(1, n + 1)]

    def test_out_of_ammo_with_hostiles(self):
        data = self.beats()
        data += [e("combat_sample", tick=i, wave=3, id=17, group=5,
                   kills=0, ammo=0, weapon=101) for i in range(1, 5)]
        self.assertIn("R023", self.codes(data))

    def test_no_ammo_metric_is_unknown_not_zero(self):
        data = self.beats()
        data += [e("combat_sample", tick=i, wave=3, id=17, group=5,
                   kills=-1, ammo=-1, weapon=-1) for i in range(1, 6)]
        self.assertNotIn("R023", self.codes(data))

    def test_missing_enemies_does_not_mean_out_of_ammo(self):
        data = self.beats(zombies=0)
        data += [e("combat_sample", tick=i, wave=3, id=17, group=5,
                   kills=0, ammo=0, weapon=101) for i in range(1, 5)]
        self.assertNotIn("R023", self.codes(data))

    def test_extended_engagement_without_kills_warns(self):
        data = self.beats()
        for i in range(1, 8):
            for agent in (17, 18):
                data.append(e("combat_sample", tick=i, wave=3, id=agent,
                              group=5, kills=0, ammo=12, weapon=101))
        self.assertIn("R024", self.codes(data))

    def test_progress_between_samples_avoids_no_kills_warning(self):
        data = self.beats()
        for i in range(1, 8):
            for agent in (17, 18):
                data.append(e("combat_sample", tick=i, wave=3, id=agent,
                              group=5, kills=i if agent == 17 else 0,
                              ammo=12, weapon=101))
        self.assertNotIn("R024", self.codes(data))
        self.assertGreater(analyze_combat_events(data, {})["observed_kill_increments"], 0)

    def test_command_requires_matching_manifest(self):
        data = [e("command_exec", cmd="zdr_cmd_heal", count=1, delta=1)]
        self.assertIn("R025", self.codes(data, {}))
        self.assertNotIn("R025", self.codes(data, {"private_commands": {"enabled": True}}))

    def test_missing_combat_samples_is_observability_gap(self):
        self.assertIn("R026", self.codes(self.beats(), {"experimental_defenders": 4}))
        self.assertNotIn("R026", self.codes(self.beats(), {"experimental_defenders": 0}))

    def test_corrupt_records_do_not_invent_combat_progress(self):
        data = [e("combat_sample", tick="bad", wave="?", id=17, group=5,
                  kills="NaN", ammo="unknown", weapon="nil")]
        result = analyze_combat_events(data, {})
        self.assertFalse(result["observability"]["available"])
        self.assertFalse(result["findings"])


if __name__ == "__main__":
    unittest.main()
