"""Round vs wave lifecycle diagnosis: native reset, not a City patch defect."""
import os
from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
from round_wave_lifecycle import (GLOBAL_BASE, ORIGINAL_TRIGGER_COUNT,
                                  ROUND_ENDED, WAVE_GLOBAL, analyse)

ORIGINAL = Path(os.environ.get("ZOMBIEEE_ORIGINAL_MODULE", "/missing/ZOMBIEEE"))


@unittest.skipUnless(ORIGINAL.is_dir(), "Owned original module required")
class RoundWaveLifecycleTests(unittest.TestCase):
    def test_native_lifecycle_is_accepted(self):
        report = analyse(ORIGINAL / "mission_templates.txt")
        self.assertTrue(report["passed"], report["checks"])
        self.assertEqual(report["wave_global"], WAVE_GLOBAL)
        self.assertEqual(report["round_ended_global"], ROUND_ENDED)
        for name in ("round_end_resets_wave_to_zero", "round_end_sets_round_ended",
                     "wave_initialised_at_mission_start",
                     "round_start_clears_round_ended",
                     "wave_controller_increments_wave"):
            self.assertTrue(report["checks"][name], name)

    def test_round_end_reset_is_native(self):
        report = analyse(ORIGINAL / "mission_templates.txt")
        triggers = report["triggers"]
        self.assertEqual(triggers["round_end"]["index"], 7)
        self.assertTrue(triggers["round_end"]["header"][0].startswith("-"))
        self.assertTrue(triggers["round_end"]["wave_assignments"])
        self.assertTrue(triggers["wave_controller"]["wave_increments"])
        self.assertEqual(triggers["wave_controller"]["header"][0], "1.000000")
        self.assertEqual(ORIGINAL_TRIGGER_COUNT, 25)

    def test_city_tradeoff_documented(self):
        report = analyse(ORIGINAL / "mission_templates.txt")
        self.assertTrue(any("set_player_respawn_as_bot 1" in x
                            for x in report["hands_off_options"]))
        self.assertIn("wave-carryover", report["not_recommended"])


if __name__ == "__main__":
    unittest.main()
