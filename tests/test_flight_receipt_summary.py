"""Offline tests for the sealed-receipt "what happened" summary (no game required)."""
import hashlib
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
from receipt_summary import (  # noqa: E402
    MAX_HIST_ENTRIES, ReceiptError, format_summary, resolve_receipt_root,
    summarize_receipt)

FLIGHT = "zombieee.flight.v1"

ZDBI_LINES = [
    "ZDB1|boot|version=0.2.0|triggers=31",
    "ZDB1|recorder_capabilities|version=0.2.0|sampling_interval_s=15|opmeta=1"
    "|troop_hist=1|lifecycle=1|troop_map=13|max_hist_troops=12",
    "ZDB1|probe_registered|version=0.2.0|kind=heartbeat|index=32",
    "ZDB1|mission_enter|version=0.2.0|role=server|template=mst_multiplayer_iv"
    "|agents=32|team0=0|team1=32|wave=0|round=0|mode=0|game_type=7"
    "|ready_for_spawn=1|bots_team1=0|troops_team0=none|troop_names_team0=none"
    "|troops_team1=873:32|troop_names_team1=873:trp_invader_multiplayer_ai"
    "|troop_ids_unknown=0|troops_truncated=0|players_team0=0",
    "ZDB1|round_started|version=0.2.0|observed=entry_observation|role=server"
    "|wave=0|round_start=1|team0=0|team1=32|game_type=7|ready_for_spawn=1|bots_team1=0",
    "ZDB1|heartbeat|version=0.2.0|count=1|role=server|agents=42|team0=1|team1=41"
    "|template=mst_multiplayer_iv|wave=1|round=0|mode=0|game_type=7"
    "|ready_for_spawn=1|bots_team1=0|troops_team0=877:1|troop_names_team0=877:trp_swadian_infantry_multiplayer"
    "|troops_team1=873:32,894:9|troop_names_team1=873:trp_invader_multiplayer_ai,894:trp_invader1_multiplayer_ai"
    "|troop_ids_unknown=0|troops_truncated=0|players_team0=1",
    "ZDB1|wave_started|version=0.2.0|observed=wave_transition|role=server|wave=1"
    "|round_start=1|team0=1|team1=41|game_type=7|ready_for_spawn=1|bots_team1=0",
    "ZDB1|player_joined|version=0.2.0|role=server|count=1|id=7|observed=first_alive_player",
    "ZDB1|player_died|version=0.2.0|role=server|count=2|id=7|wave=1|observed=dead_agent",
    "ZDB1|player_respawned|version=0.2.0|role=server|count=3|id=9|wave=1|observed=alive_after_absence",
    "ZDB1|round_started|version=0.2.0|observed=round_identity_change|role=server"
    "|wave=1|round_start=61|team0=1|team1=41|game_type=7|ready_for_spawn=1|bots_team1=0",
    "ZDB1|heartbeat|version=0.2.0|count=2|role=server|agents=42|team0=1|team1=41"
    "|template=mst_multiplayer_iv|wave=1|round=0|mode=0|game_type=7"
    "|ready_for_spawn=1|bots_team1=0|troops_team1=873:32|players_team0=1",
]

ENGINE_LOG = "\n".join([
    "02:12:19 - SCRIPT ERROR: Invalid Faction ID: -1",
    "02:12:19 - - Mission Template [44] mst_multiplayer_iv Trigger [14] Consequences",
    "02:12:19 - SCRIPT ERROR: Invalid Faction ID: -1",
    "02:12:19 - SCRIPT ERROR: Invalid Faction ID: -1",
    "02:12:19 - SCRIPT ERROR: Invalid Faction ID: -1",
])


def receipt(**overrides):
    base = {
        "schema": FLIGHT, "session_id": "a1c335262cfa6a306dcdf4561fc67a46",
        "attempt_id": "20cdb8a9c8230286", "outcome": "stopped",
        "simulation": False, "watch_mode": "passive",
        "duration_seconds": 380.5, "exit_code_observed": False,
        "game_runtime": "unknown", "log_seen_bytes": [15172],
        "log_omitted_bytes": [0], "log_truncated": [False],
        "event_count": 3, "event_drops": 0,
    }
    base.update(overrides)
    return base


def seal(root: Path, files: dict, manifest=None, receipt_doc=None):
    session = root / "session"
    session.mkdir(parents=True)
    payload = {"recorder.json": json.dumps(receipt_doc or receipt()).encode()}
    payload.update({name: (content.encode() if isinstance(content, str) else content)
                    for name, content in files.items()})
    for name, content in payload.items():
        path = session / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(content)
    if manifest is None:
        manifest = {"schema": FLIGHT, "sha256": {
            name: hashlib.sha256(content).hexdigest()
            for name, content in payload.items()}}
    (session / "manifest.json").write_text(json.dumps(manifest))
    return session


class ReceiptSummaryTests(unittest.TestCase):
    def run_summary(self, files=None, **kwargs):
        td = tempfile.TemporaryDirectory()
        self.addCleanup(td.cleanup)
        files = files if files is not None else {
            "host_stdout.log": "\n".join(ZDBI_LINES),
            "logs/log_01.txt": ENGINE_LOG,
        }
        session = seal(Path(td.name), files, **kwargs)
        return summarize_receipt(session)

    def test_summary_extracts_sealed_probe_and_lifecycle(self):
        summary = self.run_summary()
        self.assertTrue(summary["verified"])
        self.assertEqual(summary["schema"], "zombieee.receipt-summary.v1")
        self.assertEqual(summary["session_id"], "a1c335262cfa6a306dcdf4561fc67a46")
        probe = summary["probe"]
        self.assertEqual((probe["opmeta"], probe["role"], probe["game_type"],
                          probe["ready_for_spawn"], probe["troop_map"]),
                         (1, "server", 7, 1, 13))
        self.assertEqual(summary["teams"]["max_team1"], 41)
        self.assertEqual(summary["teams"]["max_team0"], 1)
        self.assertEqual(summary["troops"]["team1"], {873: 32, 894: 9})
        self.assertEqual(summary["troops"]["names"]["team1"][873],
                         "trp_invader_multiplayer_ai")
        self.assertEqual(summary["waves"]["observed"], [0, 1])
        self.assertEqual(summary["rounds"]["round_starts"], [1, 61])
        lifecycle = summary["lifecycle"]
        self.assertEqual(len(lifecycle["player_joined"]), 1)
        self.assertEqual(len(lifecycle["player_died"]), 1)
        self.assertEqual(len(lifecycle["player_respawned"]), 1)
        self.assertEqual(len(lifecycle["round_started"]), 2)
        self.assertEqual(len(lifecycle["wave_started"]), 1)
        self.assertEqual(summary["engine_errors"]["total"], 4)
        self.assertEqual(summary["engine_errors"]["kinds"]["invalid_faction_id_minus_one"], 4)
        self.assertIn("process_exit_not_observed_passive", summary["evidence_gaps"])
        self.assertIn("engine_runtime_unknown", summary["evidence_gaps"])
        self.assertNotIn("zdbi_stream_not_sealed", summary["evidence_gaps"])
        self.assertNotIn("engine_log_truncated", summary["evidence_gaps"])
        self.assertFalse(summary["runtime_verified"])
        self.assertEqual(summary["runtime_status"], "unknown")

    def test_host_stdout_is_required_and_absence_is_explicit(self):
        summary = self.run_summary(files={"logs/log_01.txt": ENGINE_LOG})
        self.assertIn("zdbi_stream_not_sealed", summary["evidence_gaps"])
        self.assertIsNone(summary["probe"]["role"])
        self.assertIsNone(summary["teams"]["max_team1"])  # unknown, never 0
        self.assertIsNone(summary["troops"]["team1"])
        self.assertFalse(summary["runtime_verified"])

    def test_tampered_sealed_file_fails_closed(self):
        td = tempfile.TemporaryDirectory()
        self.addCleanup(td.cleanup)
        session = seal(Path(td.name), {"host_stdout.log": "\n".join(ZDBI_LINES)})
        (session / "host_stdout.log").write_text("ZDB1|heartbeat|role=client\n")
        with self.assertRaises(ReceiptError):
            summarize_receipt(session)

    def test_tampered_recorder_receipt_fails_closed(self):
        td = tempfile.TemporaryDirectory()
        self.addCleanup(td.cleanup)
        session = seal(Path(td.name), {"host_stdout.log": "\n".join(ZDBI_LINES)})
        (session / "recorder.json").write_text(json.dumps(receipt(outcome="completed")))
        with self.assertRaises(ReceiptError):
            summarize_receipt(session)

    def test_extra_unsealed_file_fails_closed(self):
        td = tempfile.TemporaryDirectory()
        self.addCleanup(td.cleanup)
        session = seal(Path(td.name), {"host_stdout.log": "\n".join(ZDBI_LINES)})
        (session / "injected.txt").write_text("ZDB1|boot")
        with self.assertRaises(ReceiptError):
            summarize_receipt(session)

    def test_bad_or_unsafe_manifest_fails_closed(self):
        cases = [
            {"schema": "wrong", "sha256": {"recorder.json": "0" * 64}},
            {"schema": FLIGHT, "sha256": {"../recorder.json": "0" * 64}},
            {"schema": FLIGHT, "sha256": {"C:\\x\\recorder.json": "0" * 64}},
            {"schema": FLIGHT, "sha256": {}},
            {"schema": FLIGHT},
        ]
        for index, manifest in enumerate(cases):
            td = tempfile.TemporaryDirectory()
            self.addCleanup(td.cleanup)
            session = seal(Path(td.name), {}, manifest=manifest)
            with self.assertRaises(ReceiptError, msg=f"case {index}"):
                summarize_receipt(session)

    def test_histogram_and_lifecycle_are_bounded(self):
        hist = ",".join(f"{800 + i}:{i + 1}" for i in range(40))
        lines = [
            "ZDB1|recorder_capabilities|opmeta=1|sampling_interval_s=15",
            "ZDB1|heartbeat|count=1|role=server|team0=1|team1=40|wave=1"
            "|game_type=7|ready_for_spawn=1|troops_team1=" + hist,
        ] + [f"ZDB1|player_died|role=server|count={i}|id={i}|observed=dead_agent"
             for i in range(80)]
        summary = self.run_summary(files={"host_stdout.log": "\n".join(lines)})
        self.assertLessEqual(len(summary["troops"]["team1"]), MAX_HIST_ENTRIES)
        self.assertLessEqual(len(summary["lifecycle"]["player_died"]), 32)
        self.assertEqual(summary["teams"]["max_team1"], 40)

    def test_absent_team_metrics_stay_unknown(self):
        lines = [
            "ZDB1|heartbeat|count=1|role=server|team0=-1|team1=-1|wave=-1"
            "|game_type=-1|ready_for_spawn=-1",
        ]
        summary = self.run_summary(files={"host_stdout.log": "\n".join(lines)})
        self.assertIsNone(summary["teams"]["max_team0"])
        self.assertIsNone(summary["teams"]["max_team1"])
        self.assertIsNone(summary["probe"]["game_type"])

    def test_accepts_parent_attempt_directory(self):
        td = tempfile.TemporaryDirectory()
        self.addCleanup(td.cleanup)
        parent = Path(td.name) / "evidence-attempt9"
        session = seal(parent, {"host_stdout.log": "\n".join(ZDBI_LINES)})
        self.assertEqual(resolve_receipt_root(parent), session)
        self.assertTrue(summarize_receipt(parent)["verified"])

    def test_human_format_names_the_limits(self):
        text = format_summary(self.run_summary())
        self.assertIn("verified:", text)
        self.assertIn("role=server", text)
        self.assertIn("runtime:         verified=False status=unknown", text)
        self.assertIn("troops team1:", text)

    def test_cli_summary_and_fail_closed_exit_code(self):
        td = tempfile.TemporaryDirectory()
        self.addCleanup(td.cleanup)
        session = seal(Path(td.name), {"host_stdout.log": "\n".join(ZDBI_LINES)})
        ok = subprocess.run([sys.executable, str(ROOT / "tools" / "diagnostics.py"),
                             "summary", str(session), "--json"],
                            capture_output=True, text=True, cwd=ROOT)
        self.assertEqual(ok.returncode, 0, ok.stderr)
        payload = json.loads(ok.stdout)
        self.assertTrue(payload["verified"])
        (session / "host_stdout.log").write_text("tampered")
        bad = subprocess.run([sys.executable, str(ROOT / "tools" / "diagnostics.py"),
                              "summary", str(session)],
                             capture_output=True, text=True, cwd=ROOT)
        self.assertEqual(bad.returncode, 2)
        self.assertIn("verification failed", bad.stderr)



    def test_playerless_composition_and_absent_player_events(self):
        lines = [
            "ZDB1|recorder_capabilities|opmeta=1|sampling_interval_s=15",
            "ZDB1|heartbeat|count=1|role=server|team0=33|team1=41|wave=0"
            "|game_type=7|ready_for_spawn=1|players_team0=0|players_team1=0"
            "|humans_team0=33|humans_team1=41|bot_agents_team0=33|bot_agents_team1=41"
            "|horses_team0=0|horses_team1=0|troops_team0=33:33"
            "|troops_team1=873:32,874:9",
            "ZDB1|round_started|observed=entry_observation|role=server|wave=0"
            "|round_start=2|team0=33|team1=41|game_type=7|ready_for_spawn=1",
            "ZDB1|wave_started|observed=wave_transition|role=server|wave=1"
            "|round_start=2|team0=33|team1=41|game_type=7|ready_for_spawn=1",
        ]
        summary = self.run_summary(files={"host_stdout.log": "\n".join(lines)})
        composition = summary["composition"]
        self.assertEqual(composition["mode"], "no_human_player_observed")
        self.assertEqual(composition["team0"]["bots"], 33)
        self.assertEqual(composition["team1"]["bots"], 41)
        self.assertEqual(composition["team1"]["horses"], 0)
        self.assertFalse(composition["player_events_expected"])
        # Absent player_* events are expected in this mode, not a measured zero.
        for kind in ("player_joined", "player_died", "player_respawned", "player_left"):
            self.assertEqual(summary["lifecycle"][kind], [])
        self.assertEqual(summary["waves"]["observed"], [0, 1])
        text = format_summary(summary)
        self.assertIn("composition mode: no_human_player_observed", text)
        self.assertIn("playerless:", text)

    def test_horses_are_counted_in_composition(self):
        lines = [
            "ZDB1|heartbeat|count=1|role=server|team0=5|team1=5|players_team0=0"
            "|players_team1=0|bot_agents_team0=2|bot_agents_team1=2|horses_team0=3|horses_team1=4"
            "|humans_team0=2|humans_team1=2",
        ]
        summary = self.run_summary(files={"host_stdout.log": "\n".join(lines)})
        self.assertEqual(summary["composition"]["team0"]["horses"], 3)
        self.assertEqual(summary["composition"]["team1"]["horses"], 4)
        self.assertEqual(summary["composition"]["mode"], "no_human_player_observed")

    def test_human_present_mode_keeps_player_events_expected(self):
        lines = [
            "ZDB1|heartbeat|count=1|role=server|team0=1|team1=41|players_team0=1"
            "|players_team1=0|bot_agents_team0=0|bot_agents_team1=41|horses_team0=0|horses_team1=0",
        ]
        summary = self.run_summary(files={"host_stdout.log": "\n".join(lines)})
        self.assertEqual(summary["composition"]["mode"], "human_present")
        self.assertTrue(summary["composition"]["player_events_expected"])

    def test_unknown_composition_is_explicit(self):
        lines = [
            "ZDB1|heartbeat|count=1|role=server|team0=5|team1=5|players_team0=-1"
            "|bot_agents_team0=-1|horses_team0=-1|humans_team0=-1",
        ]
        summary = self.run_summary(files={"host_stdout.log": "\n".join(lines)})
        composition = summary["composition"]
        self.assertEqual(composition["mode"], "unknown")
        self.assertIsNone(composition["team0"]["players"])
        self.assertIn("team_composition_unknown", summary["evidence_gaps"])


    def _playerless_lines(self):
        common = ("|players_team0=0|players_team1=0|humans_team0=8|humans_team1=32"
                  "|bot_agents_team0=8|bot_agents_team1=32|horses_team0=0|horses_team1=0"
                  "|alive_team0=8|alive_team1=32|no_player=1")
        return [
            "ZDB1|recorder_capabilities|opmeta=1|sampling_interval_s=15|composition=1"
            "|engagement=1|position_summary=1",
            "ZDB1|heartbeat|count=1|role=server|team0=8|team1=32|wave=1|game_type=7"
            "|ready_for_spawn=1" + common +
            "|kills_team0=0|kills_team1=3|pos_team0=10.5:20.5|pos_team1=30.0:40.0"
            "|bbox_team0=9.0:19.0:11.0:21.0|bbox_team1=25.0:35.0:35.0:45.0"
            "|pos_sampled_team0=8|pos_sampled_team1=8",
            "ZDB1|ai_sample|role=server|tick=1|team=1|id=100|x=30.0|y=40.0|kills=1|wave=1",
            "ZDB1|heartbeat|count=2|role=server|team0=8|team1=32|wave=1|game_type=7"
            "|ready_for_spawn=1" + common +
            "|kills_team0=0|kills_team1=5|pos_team0=10.5:20.5|pos_team1=31.0:41.0"
            "|bbox_team0=9.0:19.0:11.0:21.0|bbox_team1=25.0:35.0:35.0:45.0"
            "|pos_sampled_team0=8|pos_sampled_team1=8",
            "ZDB1|ai_sample|role=server|tick=2|team=1|id=100|x=31.0|y=41.0|kills=2|wave=1",
            "ZDB1|ai_sample|role=server|tick=2|team=1|id=101|x=30.0|y=40.0|kills=0|wave=1",
            "ZDB1|ai_sample|role=server|tick=1|team=1|id=101|x=30.0|y=40.0|kills=0|wave=1",
            "ZDB1|round_started|observed=round_identity_change|role=server|wave=1"
            "|round_start=2|team0=8|team1=32|game_type=7|ready_for_spawn=1",
            "ZDB1|wave_started|observed=wave_transition|role=server|wave=1"
            "|round_start=2|team0=8|team1=32|game_type=7|ready_for_spawn=1",
        ]

    def test_playerless_run_reports_no_player_positions_kills(self):
        summary = self.run_summary(files={"host_stdout.log": "\n".join(self._playerless_lines())})
        self.assertIs(summary["no_player"], True)
        teams = summary["teams"]
        self.assertEqual((teams["max_team0"], teams["max_team1"]), (8, 32))
        self.assertEqual((teams["bots_team0"], teams["bots_team1"]), (8, 32))
        self.assertEqual((teams["horses_team0"], teams["horses_team1"]), (0, 0))
        self.assertEqual((teams["alive_team0"], teams["alive_team1"]), (8, 32))
        positions = summary["positions"]
        self.assertEqual(positions["team1"]["centroid"], {"x": 31.0, "y": 41.0})
        self.assertEqual(positions["team1"]["spread"],
                         {"min_x": 25.0, "min_y": 35.0, "max_x": 35.0, "max_y": 45.0})
        self.assertEqual(positions["team1"]["sampled"], 8)
        self.assertEqual(positions["team1"]["distinct_bots"], 2)
        self.assertEqual(positions["team1"]["moving_bots"], 1)  # id 100 displaced
        self.assertEqual(summary["engagement"], {"kills_team0": 0, "kills_team1": 5})
        self.assertGreaterEqual(summary["events"]["zdbi_lines"], 8)
        self.assertEqual(summary["events"]["counts"].get("ai_sample"), 4)
        for kind in ("player_joined", "player_died", "player_respawned", "player_left"):
            self.assertEqual(summary["lifecycle"][kind], [])
        self.assertNotIn("position_telemetry_unavailable", summary["evidence_gaps"])
        self.assertNotIn("kill_telemetry_unavailable", summary["evidence_gaps"])
        text = format_summary(summary)
        self.assertIn("no_player:       True", text)
        self.assertIn("engagement:      kills_team0=0 kills_team1=5", text)

    def test_absent_positions_and_kills_are_none_not_zero(self):
        lines = ["ZDB1|heartbeat|count=1|role=server|team0=1|team1=1|wave=1"]
        summary = self.run_summary(files={"host_stdout.log": "\n".join(lines)})
        self.assertIsNone(summary["positions"]["team0"]["centroid"])
        self.assertIsNone(summary["engagement"]["kills_team0"])
        self.assertIn("position_telemetry_unavailable", summary["evidence_gaps"])
        self.assertIn("kill_telemetry_unavailable", summary["evidence_gaps"])

    def test_gvar_bots_field_never_masquerades_as_ai_bot_count(self):
        # bots_team1 is the native g_multiplayer_num_bots_team_1 global; it must
        # not be read as the AI bot population (that is bot_agents_team1).
        lines = ["ZDB1|heartbeat|count=1|role=server|team0=1|team1=41|wave=1"
                 "|bots_team1=0"]
        summary = self.run_summary(files={"host_stdout.log": "\n".join(lines)})
        self.assertIsNone(summary["teams"]["bots_team0"])
        self.assertIsNone(summary["teams"]["bots_team1"])

if __name__ == "__main__":
    unittest.main()
