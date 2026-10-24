"""Regression tests for the read-only City runtime triage tool.

These prove only what the shipped native data and the observed probe source say.
They never claim engine execution, spawn causality or gameplay acceptance.
"""
import json
import os
from pathlib import Path
import shutil
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
from ai_wave_contract import decode_trigger
from city_defense import apply_module as add_city
from city_runtime_triage import (analyse_defects, audit_observed_defects,
                                 mission_rows, named_table, variable_names)
from patch_defenders import patch_file
from tactical_recovery import apply_module as add_tactics
from wave_reinforcements import apply_module as add_wave

ORIGINAL = Path(os.environ.get("ZOMBIEEE_ORIGINAL_MODULE", "/missing/ZOMBIEEE"))
PROBE = (Path(__file__).resolve().parents[1] / "overlay" / "lua" / "main.lua")
ASSIGN = 2133
MODE_GLOBAL = "zdr_defence_mode"


def encode(start, conditions, consequences):
    parts = [start, "0.000000", "0.000000", str(len(conditions))]
    for opcode, args in conditions:
        parts += [str(opcode), str(len(args))] + [str(value) for value in args]
    parts.append(str(len(consequences)))
    for opcode, args in consequences:
        parts += [str(opcode), str(len(args))] + [str(value) for value in args]
    return " ".join(parts)


@unittest.skipUnless(ORIGINAL.is_dir(), "Owned original module required")
class CityRuntimeTriageTests(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.module = Path(temp.name)
        (self.module / "SceneObj").mkdir()
        for name in ("troops.txt", "scenes.txt", "mission_templates.txt",
                     "variables.txt", "factions.txt"):
            shutil.copy2(ORIGINAL / name, self.module / name)
        for number in range(1, 6):
            name = f"scn_tbfc_invasion_{number}.sco"
            shutil.copy2(ORIGINAL / "SceneObj" / name,
                         self.module / "SceneObj" / name)
        patch_file(self.module, 4, city_only=True)
        add_city(self.module)
        add_wave(self.module, city_only=True)
        add_tactics(self.module, city_only=True)
        self.original_rows = mission_rows(ORIGINAL)
        self.module_rows = mission_rows(self.module)
        self.factions = named_table(ORIGINAL / "factions.txt", "fac_")
        self.troops = named_table(ORIGINAL / "troops.txt", "trp_")
        self.variables = variable_names(self.module)
        self.probe_text = PROBE.read_text(encoding="utf-8")

    SAMPLE_ROTATION = (
        "set_server_name ZOMBIEEE_Local_Test\n"
        "set_mission multiplayer_iv\n"
        "set_map tbfc_invasion_4\n"
        "set_factions fac_kingdom_1 fac_kingdom_invaders\n"
        "max_num_bots 200\n"
        "set_bot_count 1 0\n"
        "set_bot_count 2 32\n"
        "set_respawn_period 5\n"
        "set_round_max_seconds 1800\n"
        "set_defender_spawn_count 0\n"
        "set_player_respawn_as_bot 0\n"
        "start\n"
    )

    def analyse(self, module_rows=None, probe_text=None, rotation_text=None):
        return analyse_defects(
            self.original_rows,
            self.module_rows if module_rows is None else module_rows,
            self.factions, self.troops, self.variables,
            self.probe_text if probe_text is None else probe_text,
            rotation_text)

    def test_observed_trigger_14_is_original_and_trailing(self):
        report = self.analyse()
        self.assertEqual(report["problems"], [], report["problems"])
        self.assertTrue(all(report["checks"].values()), report["checks"])
        defect = report["defects"]["trigger_14"]
        self.assertFalse(defect["introduced_by_remaster"])
        self.assertTrue(defect["original_trigger_preserved"])
        self.assertTrue(defect["last_ops_of_trigger"])
        self.assertEqual([row["consequence_index"] for row in defect["invalid_ops"]],
                         [24, 25, 26, 27])
        self.assertEqual({row["intended_troop"] for row in defect["invalid_ops"]},
                         {"trp_invader_multiplayer_ai"})
        self.assertEqual(defect["preceding_valid_faction"], "fac_kingdom_invaders")
        self.assertEqual(defect["preceding_valid_writes"], 24)
        self.assertEqual(defect["failed_slot_prior_valid_write"],
                         {"slot": 200, "faction": "fac_kingdom_invaders",
                          "troop": "trp_invader1_multiplayer_ai"})
        self.assertFalse(report["runtime_verified"])
        self.assertEqual(report["causality"], "unproven")
        self.assertEqual(report["disposition"],
                         "trigger14_original_non_causal_source_scope_only_engine_execution_unproven")

    def test_remaster_introduced_faction_write_is_flagged(self):
        rows = list(self.module_rows)
        rows[14] = rows[14].replace("502 3 -1 200 ",
                                    "502 3 432345564227567632 200 ", 1)
        report = self.analyse(module_rows=rows)
        self.assertFalse(report["checks"]["trigger_14_unchanged"])
        self.assertFalse(report["checks"]["invalid_faction_ops_present"])
        self.assertTrue(report["defects"]["trigger_14"]["introduced_by_remaster"])
        self.assertTrue(report["problems"])

    def test_moved_invalid_write_loses_trailing_scope(self):
        conditions, consequences = decode_trigger(self.module_rows[14])
        self.assertEqual(consequences[-1][0], 502)
        moved = [consequences[-1]] + consequences[:-1]
        rows = list(self.module_rows)
        rows[14] = encode(self.module_rows[14].split()[0], conditions, moved)
        report = self.analyse(module_rows=rows)
        self.assertFalse(report["checks"]["invalid_faction_ops_are_last"])
        self.assertFalse(report["checks"]["failed_slot_has_prior_valid_write"])
        self.assertFalse(report["defects"]["trigger_14"]["last_ops_of_trigger"])

    def test_probe_bound_to_game_type_is_rejected(self):
        probe = self.probe_text.replace('global_int("zdr_defence_mode")',
                                        'global_int("g_multiplayer_game_type")')
        report = self.analyse(probe_text=probe)
        self.assertFalse(report["checks"]["probe_mode_is_tactical_state"])
        self.assertTrue(report["defects"]["probe_fields"]["reads_game_type"])

    def test_nonzero_tactical_mode_initializer_is_rejected(self):
        mode = 144115188075855872 + self.variables.index(MODE_GLOBAL)
        rows = list(self.module_rows)
        for index, row in enumerate(rows):
            conditions, consequences = decode_trigger(row)
            if row.split()[0] == "-20.000000" and (ASSIGN, (mode, 0)) in consequences:
                position = consequences.index((ASSIGN, (mode, 0)))
                changed = list(consequences)
                changed[position] = (ASSIGN, (mode, 1))
                rows[index] = encode(row.split()[0], conditions, changed)
                break
        else:
            self.fail("tactical mode initializer not found")
        report = self.analyse(module_rows=rows)
        self.assertFalse(report["checks"]["tactical_mode_initialized_zero"])

    def test_wave_controller_missing_server_gate_is_rejected(self):
        conditions, consequences = decode_trigger(self.module_rows[15])
        self.assertEqual(consequences[0], (417, ()))
        rows = list(self.module_rows)
        rows[15] = encode(self.module_rows[15].split()[0], conditions,
                          consequences[1:])
        report = self.analyse(module_rows=rows)
        self.assertFalse(report["checks"]["wave_controller_server_gate_first"])
        self.assertFalse(report["checks"]["wave_controller_unchanged"])

    def test_rotation_contract_passes_with_second_team_bots(self):
        report = self.analyse(rotation_text=self.SAMPLE_ROTATION)
        rotation = report["defects"]["launcher_rotation"]
        self.assertTrue(rotation["analysed"])
        self.assertTrue(rotation["second_team_bots_configured"])
        self.assertTrue(rotation["bot_counts_before_start"])
        self.assertEqual(rotation["max_num_bots"], 200)
        self.assertEqual(rotation["problems"], [])
        self.assertTrue(report["checks"]["launcher_second_team_bots_positive"])
        self.assertTrue(report["checks"]["launcher_bot_counts_before_start"])

    def test_rotation_without_second_team_bots_is_rejected(self):
        rotation = self.SAMPLE_ROTATION.replace("set_bot_count 2 32\n", "")
        report = self.analyse(rotation_text=rotation)
        self.assertFalse(report["checks"]["launcher_second_team_bots_positive"])
        self.assertTrue(report["defects"]["launcher_rotation"]["problems"])

    def test_rotation_first_team_bots_only_is_rejected(self):
        rotation = self.SAMPLE_ROTATION.replace("set_bot_count 2 32",
                                                "set_bot_count 1 32")
        report = self.analyse(rotation_text=rotation)
        self.assertFalse(report["checks"]["launcher_second_team_bots_positive"])

    def test_rotation_bot_counts_after_start_are_rejected(self):
        rotation = self.SAMPLE_ROTATION.replace("set_bot_count 2 32\n", "").replace(
            "start\n", "start\nset_bot_count 2 32\n")
        report = self.analyse(rotation_text=rotation)
        self.assertFalse(report["checks"]["launcher_bot_counts_before_start"])

    def test_rotation_respawn_contract_is_enforced(self):
        report = self.analyse(rotation_text=self.SAMPLE_ROTATION)
        self.assertTrue(report["checks"]["launcher_respawn_period_positive"])
        self.assertTrue(report["checks"]["launcher_round_max_seconds_positive"])
        self.assertTrue(report["checks"]["launcher_defender_spawn_count_zero"])
        self.assertTrue(report["checks"]["launcher_player_respawn_as_bot_zero"])

    def test_rotation_missing_respawn_period_is_rejected(self):
        rotation = self.SAMPLE_ROTATION.replace("set_respawn_period 5\n", "")
        report = self.analyse(rotation_text=rotation)
        self.assertFalse(report["checks"]["launcher_respawn_period_positive"])

    def test_rotation_defender_bots_are_rejected(self):
        rotation = self.SAMPLE_ROTATION.replace("set_defender_spawn_count 0",
                                                "set_defender_spawn_count 32")
        report = self.analyse(rotation_text=rotation)
        self.assertFalse(report["checks"]["launcher_defender_spawn_count_zero"])

    def test_rotation_player_respawn_as_bot_is_rejected(self):
        rotation = self.SAMPLE_ROTATION.replace("set_player_respawn_as_bot 0",
                                                "set_player_respawn_as_bot 1")
        report = self.analyse(rotation_text=rotation)
        self.assertFalse(report["checks"]["launcher_player_respawn_as_bot_zero"])

    def test_rotation_reports_generic_bot_roster_caveat(self):
        report = self.analyse(rotation_text=self.SAMPLE_ROTATION)
        caveat = report["defects"]["launcher_rotation"]["roster_caveat"]
        self.assertIn("faction default troop", caveat)

    def test_missing_rotation_is_unverified_not_silent_pass(self):
        report = self.analyse()
        self.assertFalse(report["defects"]["launcher_rotation"]["analysed"])
        self.assertTrue(any("Rotation file not supplied" in warning
                            for warning in report["warnings"]))
        self.assertFalse(report["runtime_verified"])

    def test_file_audit_with_rotation_stays_path_free(self):
        with tempfile.TemporaryDirectory() as folder:
            rotation = Path(folder) / "Native.txt"
            rotation.write_text(self.SAMPLE_ROTATION, encoding="utf-8")
            report = audit_observed_defects(ORIGINAL, self.module, PROBE, rotation)
        self.assertEqual(report["problems"], [], report["problems"])
        self.assertTrue(report["defects"]["launcher_rotation"]["second_team_bots_configured"])
        self.assertNotIn(str(ORIGINAL), json.dumps(report))
        self.assertFalse(report["runtime_verified"])

    def test_report_is_path_free(self):
        blob = json.dumps(self.analyse())
        self.assertNotIn(str(ORIGINAL), blob)
        self.assertNotIn("C:\\\\", blob)
        self.assertNotIn("/mnt/", blob)

    def test_file_audit_is_path_free_and_unverified(self):
        report = audit_observed_defects(ORIGINAL, self.module, PROBE)
        self.assertEqual(report["problems"], [], report["problems"])
        self.assertFalse(report["runtime_verified"])
        self.assertEqual(report["causality"], "unproven")
        self.assertNotIn(str(ORIGINAL), json.dumps(report))

    def test_missing_module_is_not_evidence(self):
        with tempfile.TemporaryDirectory() as empty:
            report = audit_observed_defects(ORIGINAL, Path(empty) / "missing")
        self.assertEqual(report["disposition"], "inspection_failed_not_evidence")
        self.assertFalse(report["runtime_verified"])
        self.assertTrue(report["problems"])


if __name__ == "__main__":
    unittest.main()
