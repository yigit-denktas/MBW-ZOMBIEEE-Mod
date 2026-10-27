import contextlib
import io
import json
import tempfile
import unittest
from pathlib import Path

from telemetry import dependency_impact as di


def make_item(item_id, *, state="active", depends_on=(), owner="Alice",
              queue="A", priority="P1", required=True, blocked=False,
              title=None, unmapped=()):
    return {
        "id": item_id,
        "title": title or f"Item {item_id}",
        "state": state,
        "blocked": blocked,
        "dependsOn": list(depends_on),
        "unmappedDependencies": list(unmapped),
        "owner": owner,
        "implementationLane": queue,
        "priority": priority,
        "required": required,
    }


def make_ledger(items):
    return {"contractVersion": "0.2.0", "items": list(items)}


class DependencyChainTests(unittest.TestCase):
    def test_direct_and_transitive_dependents_chain(self):
        report = di.analyze(make_ledger([
            make_item("A", state="done"),
            make_item("B", depends_on=["A"]),
            make_item("C", state="backlog", depends_on=["B"]),
            make_item("D", state="backlog", depends_on=["C"]),
        ]), source_path="fixture")
        items = {row["id"]: row for row in report["items"]}

        self.assertEqual(items["A"]["direct_dependents"], ["B"])
        self.assertEqual(items["A"]["direct_dependents_count"], 1)
        self.assertEqual(items["A"]["transitive_dependents_count"], 3)
        self.assertEqual(items["B"]["transitive_dependents_count"], 2)
        self.assertEqual(items["C"]["transitive_dependents_count"], 1)
        self.assertEqual(items["D"]["transitive_dependents_count"], 0)

        self.assertEqual(items["A"]["open_transitive_dependents_count"], 3)
        self.assertEqual(items["B"]["open_transitive_dependents_count"], 2)
        self.assertFalse(items["B"]["impacted"])  # A is done
        self.assertTrue(items["C"]["impacted"])
        self.assertEqual(items["C"]["unresolved_prerequisites"], ["B"])
        self.assertEqual(items["D"]["unresolved_prerequisites"], ["B", "C"])

        self.assertEqual(report["summary"]["dependencies"], 3)
        self.assertEqual(report["summary"]["roots"], 1)
        self.assertEqual(report["summary"]["leaves"], 1)
        # A is done, so it is not a blocker; B is the top consequential blocker.
        self.assertEqual([row["id"] for row in report["consequential_blockers"]],
                         ["B", "C"])
        self.assertEqual(report["consequential_blockers"][0]["rank"], 1)

    def test_diamond_dependency(self):
        report = di.analyze(make_ledger([
            make_item("A", state="done"),
            make_item("B", depends_on=["A"]),
            make_item("C", depends_on=["A"]),
            make_item("D", depends_on=["B", "C"]),
        ]), source_path="fixture")
        items = {row["id"]: row for row in report["items"]}
        self.assertEqual(items["A"]["direct_dependents"], ["B", "C"])
        self.assertEqual(items["A"]["transitive_dependents_count"], 3)
        self.assertEqual(items["D"]["depends_on"], ["B", "C"])
        self.assertEqual(items["D"]["unresolved_prerequisites"], ["B", "C"])
        self.assertTrue(items["D"]["impacted"])

    def test_ranking_uses_blocked_priority_and_required_tiebreaks(self):
        report = di.analyze(make_ledger([
            make_item("A", priority="P2"),
            make_item("B", priority="P1", blocked=True),
            make_item("C", priority="P0"),
            make_item("X", depends_on=["A"]),
            make_item("Y", depends_on=["B"]),
            make_item("Z", depends_on=["C"]),
        ]), source_path="fixture")
        # All three blockers have one open dependent. Explicit blocked first,
        # then priority, then id.
        self.assertEqual([row["id"] for row in report["consequential_blockers"]],
                         ["B", "C", "A"])

    def test_required_dependents_break_ties_before_priority(self):
        report = di.analyze(make_ledger([
            make_item("A", priority="P2"),
            make_item("B", priority="P0"),
            make_item("X", depends_on=["A"], required=True),
            make_item("Y", depends_on=["B"], required=False),
        ]), source_path="fixture")
        self.assertEqual([row["id"] for row in report["consequential_blockers"]],
                         ["A", "B"])


class CycleTests(unittest.TestCase):
    def test_synthetic_cycle_is_detected_and_terminates(self):
        report = di.analyze(make_ledger([
            make_item("A", depends_on=["C"]),
            make_item("B", depends_on=["A"]),
            make_item("C", depends_on=["B"]),
            make_item("D", depends_on=["B"]),
        ]), source_path="fixture")

        self.assertEqual(len(report["cycles"]), 1)
        cycle = report["cycles"][0]
        self.assertEqual(cycle["cycle_id"], "CYCLE-1")
        self.assertEqual(cycle["members"], ["A", "B", "C"])
        self.assertEqual([tuple(edge) for edge in cycle["edges"]],
                         [("A", "B"), ("B", "C"), ("C", "A")])
        self.assertEqual(cycle["external_dependents"], ["D"])
        self.assertEqual(report["summary"]["in_cycle"], 3)
        self.assertEqual(report["summary"]["cycles"], 1)

        items = {row["id"]: row for row in report["items"]}
        self.assertTrue(items["A"]["in_cycle"])
        self.assertEqual(items["A"]["cycle_id"], "CYCLE-1")
        # Transitive traversal must not loop; D sees the whole cycle upstream.
        self.assertEqual(items["A"]["transitive_dependents_count"], 3)
        self.assertEqual(items["D"]["unresolved_prerequisites"], ["A", "B", "C"])
        self.assertTrue(items["D"]["impacted"])

        cycle_gaps = [gap for gap in report["gaps"]
                      if gap["code"] == "dependency_cycle"]
        self.assertEqual(len(cycle_gaps), 1)

    def test_self_dependency_is_a_cycle(self):
        report = di.analyze(make_ledger([
            make_item("A", depends_on=["A"]),
        ]), source_path="fixture")
        self.assertEqual(len(report["cycles"]), 1)
        self.assertEqual(report["cycles"][0]["members"], ["A"])
        self.assertEqual(report["cycles"][0]["edges"], [["A", "A"]])


class ScheduleUnknownTests(unittest.TestCase):
    def test_schedule_is_explicitly_unknown(self):
        report = di.analyze(make_ledger([
            make_item("A"),
            make_item("B", depends_on=["A"]),
        ]), source_path="fixture")

        self.assertEqual(report["schedule"]["status"], "unknown")
        self.assertFalse(report["schedule"]["durations_used"])
        self.assertFalse(report["schedule"]["effort_estimated"])
        self.assertFalse(report["schedule"]["float_computed"])
        self.assertFalse(report["schedule"]["cpm_computed"])
        self.assertEqual(report["gaps"][0]["code"], "schedule_unknown")
        self.assertIn("duration", report["gaps"][0]["details"]["fields_unavailable"])

        markdown = di.render_markdown(report)
        self.assertIn("Schedule unknown", markdown)
        self.assertIn("schedule_unknown", markdown)
        self.assertIn("No duration", markdown)


class RollupTests(unittest.TestCase):
    def test_owner_and_queue_rollups(self):
        report = di.analyze(make_ledger([
            make_item("A", owner="Alice", queue="A", blocked=True),
            make_item("B", owner="Alice", queue="A", depends_on=["A"]),
            make_item("C", owner="Bob", queue="B", state="backlog",
                      depends_on=["B"]),
        ]), source_path="fixture")

        owners = {row["owner"]: row for row in report["owners"]}
        self.assertEqual(owners["Alice"]["items"], 2)
        self.assertEqual(owners["Alice"]["open"], 2)
        self.assertEqual(owners["Alice"]["blocked"], 1)
        self.assertEqual(owners["Alice"]["impacted"], 1)
        self.assertEqual(owners["Alice"]["direct_dependents"], 2)
        self.assertEqual(owners["Alice"]["transitive_dependents"], 2)
        self.assertEqual(owners["Alice"]["open_transitive_dependents"], 2)
        self.assertEqual(owners["Bob"]["items"], 1)
        self.assertEqual(owners["Bob"]["impacted"], 1)

        queues = {row["queue"]: row for row in report["queues"]}
        self.assertEqual(queues["A"]["items"], 2)
        self.assertEqual(queues["B"]["items"], 1)
        self.assertEqual(queues["B"]["open_transitive_dependents"], 0)

        pairs = {(row["owner"], row["queue"]): row
                 for row in report["owner_queue"]}
        self.assertEqual(pairs[("Alice", "A")]["items"], 2)
        self.assertEqual(pairs[("Bob", "B")]["items"], 1)


class IntegrityTests(unittest.TestCase):
    def test_dangling_unmapped_and_missing_owner_queue_gaps(self):
        broken = make_item("A", depends_on=["MISSING"], owner="",
                           queue="", unmapped=["GHOST"])
        report = di.analyze(make_ledger([
            broken,
            make_item("B", depends_on=["A"]),
        ]), source_path="fixture")

        codes = {gap["code"] for gap in report["gaps"]}
        self.assertIn("dangling_dependency", codes)
        self.assertIn("unmapped_dependency", codes)
        self.assertIn("missing_owner_or_queue", codes)
        self.assertEqual(report["dangling_dependencies"],
                         [{"item": "A", "dependency": "MISSING"}])
        items = {row["id"]: row for row in report["items"]}
        self.assertEqual(items["A"]["owner"], "unassigned")
        self.assertEqual(items["A"]["queue"], "unassigned")
        self.assertEqual(items["A"]["depends_on"], [])
        self.assertEqual(items["B"]["transitive_dependents_count"], 0)

    def test_duplicate_ids_are_rejected_with_a_gap(self):
        report = di.analyze(make_ledger([
            make_item("A"),
            make_item("A", state="done"),
        ]), source_path="fixture")
        self.assertEqual(report["summary"]["items"], 1)
        self.assertEqual(report["integrity"]["duplicate_item_ids"], ["A"])
        self.assertIn("duplicate_item_id",
                      {gap["code"] for gap in report["gaps"]})


class CliTests(unittest.TestCase):
    def test_cli_writes_json_and_markdown(self):
        ledger = make_ledger([
            make_item("A", state="done"),
            make_item("B", depends_on=["A"]),
            make_item("C", depends_on=["B"]),
        ])
        with tempfile.TemporaryDirectory() as temp:
            temp_path = Path(temp)
            ledger_path = temp_path / "ledger.json"
            json_path = temp_path / "out" / "impact.json"
            md_path = temp_path / "out" / "IMPACT.md"
            ledger_path.write_text(json.dumps(ledger), encoding="utf-8")

            with contextlib.redirect_stdout(io.StringIO()):
                code = di.main([
                    "--ledger", str(ledger_path),
                    "--json-out", str(json_path),
                    "--md-out", str(md_path),
                    "--top", "2",
                ])
            self.assertEqual(code, 0)
            self.assertTrue(json_path.is_file())
            self.assertTrue(md_path.is_file())

            parsed = json.loads(json_path.read_text(encoding="utf-8"))
            self.assertEqual(parsed["schema"], di.SCHEMA)
            self.assertEqual(parsed["summary"]["items"], 3)
            self.assertEqual(parsed["gaps"][0]["code"], "schedule_unknown")
            markdown = md_path.read_text(encoding="utf-8")
            self.assertIn("# Dependency impact", markdown)
            self.assertIn("Consequential blockers", markdown)
            self.assertIn("schedule_unknown", markdown)
            self.assertIn("Queue rollup", markdown)

    def test_repository_ledger_smoke(self):
        root = Path(__file__).resolve().parents[1]
        ledger = di.load_ledger(root / "progress" / "ledger.json")
        report = di.analyze(ledger, source_path="progress/ledger.json")
        self.assertEqual(report["schema"], di.SCHEMA)
        self.assertGreater(report["summary"]["items"], 0)
        self.assertEqual(report["gaps"][0]["code"], "schedule_unknown")
        self.assertEqual(report["summary"]["dangling_dependencies"], 0)
        self.assertTrue(report["items"])
        self.assertTrue(report["owners"])
        self.assertTrue(report["queues"])


if __name__ == "__main__":
    unittest.main()
