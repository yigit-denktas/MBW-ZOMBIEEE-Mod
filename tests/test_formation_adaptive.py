"""Task-53/62 adaptive formation tests (team orders only, no 1730)."""
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
from city_defense import GUARD_ENTRIES, orders_trigger


class AdaptiveFormationTests(unittest.TestCase):
    def setUp(self):
        self.row = orders_trigger(0, wave_global=1209, round_ended_operand=512,
                                  adaptive=True, defender_orders=True)

    def test_no_per_agent_scripted_destination(self):
        self.assertNotIn("1730", self.row.split())

    def test_class_roles_and_sector_entries(self):
        tokens = self.row.split()
        self.assertIn("1718", tokens)  # agent_get_troop_id
        for troop in ("983", "984"):
            self.assertIn(troop, tokens)
        for entry in GUARD_ENTRIES:
            self.assertIn(str(entry), tokens)
        # 1780 position reads, then 1791/1790 orders per division.
        self.assertIn("1791", tokens)
        self.assertIn("1790", tokens)

    def test_defensive_fallback_and_fire_orders_present(self):
        # The static branch contains both fall-back (6) and hold (0) orders so
        # the runtime count/round-ended branch can pick one; fire-at-will and
        # ranged usage are always re-issued.
        tokens = self.row.split()
        pairs = [(tokens[i], tokens[i + 1]) for i in range(len(tokens) - 1)]
        for code in ("6", "0", "13", "16"):
            self.assertIn(code, tokens)
        self.assertIn("1790", tokens)
        self.assertIn("2211", tokens)  # City scene condition

    def test_no_scripted_destination_even_when_adaptive(self):
        self.assertNotIn("1730", self.row)


if __name__ == "__main__":
    unittest.main()
