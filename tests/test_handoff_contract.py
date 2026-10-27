"""Contract checks for PKG-101 handoff/queue data (offline, ledger only)."""
import json
import unittest
from pathlib import Path

LEDGER = Path(__file__).resolve().parents[1] / "progress" / "ledger.json"
FIXED_REVIEWERS = {"E", "review-b2"}
HANDOFF_KEYS = {"from", "to", "reviewer", "status", "artifact", "unblock"}


class HandoffContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data = json.loads(LEDGER.read_text(encoding="utf-8"))
        cls.items = cls.data["items"]

    def test_every_handoff_has_required_fields(self):
        for item in self.items:
            handoff = item.get("handoff")
            if not handoff:
                continue
            self.assertEqual(set(handoff), HANDOFF_KEYS, item["id"])
            for key in HANDOFF_KEYS:
                self.assertTrue(str(handoff[key]).strip(), item["id"] + ":" + key)

    def test_reviewers_are_fixed_reviewers(self):
        for item in self.items:
            handoff = item.get("handoff")
            if handoff and handoff.get("reviewer"):
                self.assertIn(handoff["reviewer"], FIXED_REVIEWERS, item["id"])

    def test_no_handoff_points_at_a_merged_pr_as_in_review(self):
        for item in self.items:
            handoff = item.get("handoff") or {}
            artifact = str(handoff.get("artifact", ""))
            if "PR #52" in artifact:
                self.assertNotEqual(handoff.get("status"), "in-review", item["id"])

    def test_queue_derivation_is_total(self):
        def queue(item):
            if item["state"] == "done":
                return "done"
            unmet = [d for d in item.get("dependsOn", [])
                     if not any(x["id"] == d and x["state"] == "done" for x in self.items)]
            if unmet:
                return "waiting-dependency"
            handoff = item.get("handoff") or {}
            if handoff.get("status") == "waiting-external":
                return "waiting-external"
            if handoff.get("to") == "owner" or handoff.get("status") == "owner-action":
                return "owner-action"
            if item["state"] in {"active", "review", "ready"}:
                return "in-progress"
            return "ready"
        counts = {}
        for item in self.items:
            counts[queue(item)] = counts.get(queue(item), 0) + 1
        self.assertEqual(sum(counts.values()), len(self.items))
        self.assertGreater(counts.get("waiting-dependency", 0), 0)
        self.assertGreater(counts.get("in-progress", 0), 0)


if __name__ == "__main__":
    unittest.main()
