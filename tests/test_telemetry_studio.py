"""Tests for the telemetry studio toolkit (synthetic fixtures only)."""

import hashlib
import io
import json
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path

from tools.telemetry_studio import (
    analyze_performance,
    compare_ingests,
    detect_anomalies,
    ingest_bundle,
    inspect_module,
    render_iteration_report,
    validate_event,
    schema_catalog,
)
from tools.telemetry_studio.balance import analyze_balance, render_balance_report
from tools.telemetry_studio.ingest import IngestError
from tools.telemetry_studio.__main__ import main
from tools.telemetry_studio.tail import tail_events

HEARTBEATS = [
    "ZDB1|heartbeat|count=1|role=server|agents=20|team0=8|team1=12|wave=1",
    "ZDB1|heartbeat|count=2|role=server|agents=21|team0=8|team1=13|wave=1",
    "ZDB1|heartbeat|count=4|role=server|agents=18|team0=7|team1=11|wave=2",
    "ZDB1|ai_sample|tick=1|team=0|id=7|group=5|troop=981|x=10.0|y=10.0",
    "ZDB1|ai_sample|tick=2|team=1|id=8|group=0|troop=894|x=20.0|y=20.0",
]


def _bundle(root: Path, lines: list[str], *, sealed: bool):
    log = root / "logs" / "log_01.txt"
    log.parent.mkdir(parents=True)
    text = "\n".join(lines) + "\n"
    log.write_text(text, encoding="utf-8")
    recorder = {"schema": "zombieee.flight.v1", "duration_seconds": 45.0,
                "event_count": len(lines), "event_drops": 0,
                "metrics": {"cpu_seconds": None, "peak_memory_kib": None,
                            "source": "unavailable"},
                "log_truncated": [False], "log_omitted_bytes": [0]}
    if sealed:
        (root / "recorder.json").write_text(json.dumps(recorder), encoding="utf-8")
        manifest = {"schema": "zombieee.flight.v1", "sha256": {}}
        for path in root.rglob("*"):
            if path.is_file():
                manifest["sha256"][str(path.relative_to(root)).replace("\\", "/")] = (
                    hashlib.sha256(path.read_bytes()).hexdigest())
        (root / "manifest.json").write_text(json.dumps(manifest), encoding="utf-8")
    return root


class SchemaTests(unittest.TestCase):
    def test_catalog_and_validation(self):
        catalog = schema_catalog()
        self.assertEqual(catalog["schema"], "zombieee.flight.v1")
        self.assertIn("heartbeat", catalog["events"])
        valid = {"event": "heartbeat", "fields": {"count": "3", "role": "server"}}
        self.assertEqual(validate_event(valid), [])
        bad_role = {"event": "heartbeat", "fields": {"count": "3", "role": "nope"}}
        self.assertTrue(validate_event(bad_role))
        unknown = {"event": "future_event", "fields": {}}
        self.assertTrue(validate_event(unknown))


class IngestTests(unittest.TestCase):
    def test_unsealed_ingest_parses_and_counts(self):
        with tempfile.TemporaryDirectory() as td:
            root = _bundle(Path(td), HEARTBEATS, sealed=False)
            ingest = ingest_bundle(root, allow_unsealed=True)
            self.assertFalse(ingest["verified"])
            self.assertIn("unsealed_bundle", ingest["gaps"])
            self.assertEqual(len(ingest["events"]), len(HEARTBEATS))
            self.assertEqual(ingest["event_counts"]["heartbeat"], 3)

    def test_sealed_ingest_verifies(self):
        with tempfile.TemporaryDirectory() as td:
            root = _bundle(Path(td), HEARTBEATS, sealed=True)
            ingest = ingest_bundle(root)
            self.assertTrue(ingest["verified"])
            self.assertEqual(ingest["file_count"], 2)

    def test_sealed_ingest_rejects_tamper(self):
        with tempfile.TemporaryDirectory() as td:
            root = _bundle(Path(td), HEARTBEATS, sealed=True)
            (root / "logs" / "log_01.txt").write_text("tampered\n", encoding="utf-8")
            with self.assertRaises(IngestError):
                ingest_bundle(root)

    def test_duplicate_log_copy_is_counted_once(self):
        with tempfile.TemporaryDirectory() as td:
            root = _bundle(Path(td), HEARTBEATS, sealed=False)
            (root / "host_stdout.log").write_text("\n".join(HEARTBEATS) + "\n",
                                                  encoding="utf-8")
            ingest = ingest_bundle(root, allow_unsealed=True)
            self.assertEqual(len(ingest["events"]), len(HEARTBEATS))
            self.assertGreater(ingest["duplicate_lines_skipped"], 0)


class PerfAnomalyTests(unittest.TestCase):
    def test_cadence_and_coverage(self):
        with tempfile.TemporaryDirectory() as td:
            root = _bundle(Path(td), HEARTBEATS, sealed=True)
            ingest = ingest_bundle(root)
            perf = analyze_performance(ingest)
            self.assertEqual(perf["heartbeats"], 3)
            self.assertEqual(perf["missing_heartbeat_intervals"], 1)  # 1->2->4
            self.assertIsNone(perf["tick_cadence_seconds"])
            self.assertIn("tick_cadence_seconds", perf["unknown"])
            self.assertIsNotNone(perf["ai_samples_per_heartbeat"])

    def test_error_spam_anomaly(self):
        with tempfile.TemporaryDirectory() as td:
            lines = HEARTBEATS + ["SCRIPT ERROR: Invalid Faction ID: -2147483648"] * 25
            root = _bundle(Path(td), lines, sealed=False)
            ingest = ingest_bundle(root, allow_unsealed=True)
            perf = analyze_performance(ingest)
            codes = {item["code"] for item in detect_anomalies(ingest, perf)}
            self.assertIn("invalid_faction_negative_spam", codes)
            self.assertIn("unsealed_bundle", codes)


class CompareTests(unittest.TestCase):
    def test_compare_deltas(self):
        with tempfile.TemporaryDirectory() as td:
            base = ingest_bundle(_bundle(Path(td) / "base", HEARTBEATS, sealed=True))
            better = HEARTBEATS + [
                "ZDB1|heartbeat|count=5|role=server|agents=20|team0=8|team1=12|wave=2"]
            cand = ingest_bundle(_bundle(Path(td) / "cand", better, sealed=True))
            result = compare_ingests(base, cand)
            self.assertEqual(result["deltas"]["heartbeats"]["verdict"], "better")
            self.assertIn("note", result)


class StaticInspectTests(unittest.TestCase):
    def test_trigger_and_opcode_inspection(self):
        with tempfile.TemporaryDirectory() as td:
            module = Path(td)
            mission = ("5.000000 0.000000 0.000000 4 417 0 2133 2 1 55 "
                       "2093 2 2 1 502 3 432345564227567632 200 360287970189640574 "
                       "502 3 -1 200 360287970189640574\n"
                       "4.000000 0.000000 0.000000 1 417 0 2093 2 2 1\n")
            (module / "mission_templates.txt").write_text(mission, encoding="utf-8")
            (module / "variables.txt").write_text("wave_number\n", encoding="utf-8")
            report = inspect_module(module)
            self.assertTrue(report["ok"])
            self.assertEqual(report["trigger_count"], 2)
            self.assertEqual(report["slow_894_slot_writes"], 1)
            self.assertEqual(report["invalid_faction_literal_ops"], 1)
            self.assertEqual(report["speed_trigger_count"], 2)


class ReportAndCliTests(unittest.TestCase):
    def test_report_marks_unknown_and_no_acceptance(self):
        with tempfile.TemporaryDirectory() as td:
            root = _bundle(Path(td), HEARTBEATS, sealed=True)
            ingest = ingest_bundle(root)
            text = render_iteration_report(
                ingest, hypothesis="lower error spam", next_hypothesis="re-seal",
                perf=analyze_performance(ingest), static=inspect_module(Path(td)) if False else None)
            self.assertIn("Telemetry Studio iteration receipt", text)
            self.assertIn("runtime_verified", text)
            self.assertIn("unknown", text)

    def test_tail_reads_existing_lines(self):
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / "log.txt"
            path.write_text("\n".join(HEARTBEATS), encoding="utf-8")
            events = list(tail_events(path, follow=False))
            self.assertEqual(len(events), len(HEARTBEATS))

    def test_cli_schema_json(self):
        buffer = io.StringIO()
        with redirect_stdout(buffer):
            code = main(["schema", "--json"])
        self.assertEqual(code, 0)
        self.assertIn("zombieee.flight.v1", buffer.getvalue())



class BalanceTests(unittest.TestCase):
    def _run(self, root: Path, lines: list[str]):
        return ingest_bundle(_bundle(root, lines, sealed=False), allow_unsealed=True)

    def test_rounds_wipe_troops_and_sensitivity(self):
        with tempfile.TemporaryDirectory() as td:
            common = [
                "ZDB1|heartbeat|count=1|round=1|team0=4|team1=4|alive_team0=4|alive_team1=4|wave=1",
            ]
            a = self._run(Path(td) / "a", common + [
                "ZDB1|heartbeat|count=2|round=1|team0=4|team1=0|alive_team0=4|alive_team1=0|wave=1",
                "ZDB1|ai_sample|tick=1|team=0|id=1|troop=981|kills=2|x=10.0|y=10.0",
                "ZDB1|ai_sample|tick=1|team=0|id=2|troop=981|kills=1|x=12.0|y=10.0",
                "ZDB1|ai_sample|tick=1|team=0|id=3|troop=983|kills=0",
                "ZDB1|ai_sample|tick=1|team=1|id=4|troop=894|kills=0",
            ])
            b = self._run(Path(td) / "b", common + [
                "ZDB1|heartbeat|count=2|round=1|team0=0|team1=3|alive_team0=0|alive_team1=3|wave=1",
                "ZDB1|ai_sample|tick=1|team=0|id=1|troop=981|kills=1",
                "ZDB1|ai_sample|tick=1|team=1|id=4|troop=894|kills=2",
            ])
            params = {str(a["root"]): {"defender_target": 8},
                      str(b["root"]): {"defender_target": 12}}
            result = analyze_balance([a, b], params)
            self.assertEqual(result["schema"], "zombieee.balance-analysis.v1")
            self.assertFalse(result["runtime_verified"])
            self.assertEqual(result["runs"][0]["metrics"]["outcomes"].get("team0_win"), 1)
            self.assertEqual(result["runs"][1]["metrics"]["outcomes"].get("team1_win"), 1)
            team0 = result["runs"][0]["metrics"]["troop_contributions"]["team0"]
            self.assertEqual(team0["kills_total_lower_bound"], 3)
            self.assertEqual(team0["troops"][0]["troop"], 981)
            self.assertEqual(result["sensitivity"]["matrix"][0]["parameter"], "defender_target")
            self.assertFalse(result["sensitivity"]["matrix"][0]["causal"])
            self.assertTrue(result["recommendations"])
            self.assertIn("hit_attribution_unavailable", result["gaps"])
            self.assertIn("spawn_entry_fairness_unavailable", result["gaps"])
            self.assertIsNotNone(result["runs"][0]["metrics"]["positioning"]["team0"])
            self.assertTrue(result["gaps_as_tasks"])
            text = render_balance_report(result)
            self.assertIn("not causal", text)
            self.assertIn("acceptance: **none**", text)

    def test_no_parameters_and_no_end_event_are_explicit(self):
        with tempfile.TemporaryDirectory() as td:
            run = self._run(Path(td) / "a", [
                "ZDB1|heartbeat|count=1|round=1|team0=4|team1=4|alive_team0=4|alive_team1=4|wave=1",
                "ZDB1|heartbeat|count=2|round=1|team0=4|team1=4|alive_team0=4|alive_team1=4|wave=1",
            ])
            result = analyze_balance([run])
            self.assertIn("parameter_metadata_missing", result["gaps"])
            self.assertIn("insufficient_runs_for_ranked_recommendations", result["gaps"])
            self.assertEqual(result["runs"][0]["metrics"]["rounds"][0]["outcome"],
                             "round_reset_no_wipe")

if __name__ == "__main__":
    unittest.main()
