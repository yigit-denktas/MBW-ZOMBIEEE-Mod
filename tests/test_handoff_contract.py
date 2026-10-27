"""Contract checks for PKG-101 handoff/queue data (offline, ledger only)."""
import json
import unittest
from pathlib import Path

LEDGER = Path(__file__).resolve().parents[1] / "progress" / "ledger.json"
FIXED_REVIEWERS = {"E", "review-b2"}
HANDOFF_KEYS = {"from", "to", "reviewer", "status", "artifact", "unblock"}
EXPECTED_QUEUES = {"ready": 3, "in-progress": 17, "waiting-dependency": 32,
                   "waiting-external": 2, "owner-action": 1, "done": 71}


class HandoffContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data = json.loads(LEDGER.read_text(encoding="utf-8"))
        cls.items = cls.data["items"]
        cls.by_id = {item["id"]: item for item in cls.items}

    def queue(self, item):
        if item["state"] == "done":
            return "done"
        if any(self.by_id.get(dep, {}).get("state") != "done" for dep in item.get("dependsOn", [])):
            return "waiting-dependency"
        handoff = item.get("handoff") or {}
        if handoff.get("status") == "waiting-external":
            return "waiting-external"
        if handoff.get("to") == "owner" or handoff.get("status") == "owner-action":
            return "owner-action"
        if item["state"] in {"active", "review", "ready"}:
            return "in-progress"
        return "ready"

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
            if "PR #52" in str(handoff.get("artifact", "")):
                self.assertNotEqual(handoff.get("status"), "in-review", item["id"])

    def test_queues_match_exact_counts_at_this_revision(self):
        counts = {}
        for item in self.items:
            queue = self.queue(item)
            counts[queue] = counts.get(queue, 0) + 1
        self.assertEqual(counts, EXPECTED_QUEUES)


if __name__ == "__main__":
    unittest.main()
