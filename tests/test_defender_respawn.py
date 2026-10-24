"""Periodic private-survivor respawn stays inside the City tactical build."""
import os
from pathlib import Path
import shutil
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
from ai_wave_contract import decode_trigger
from city_defense import apply_module as add_city
from patch_defenders import (PatchError, index_troops, mission_bounds,
                             patch_file, TROOP_BASE, SURVIVOR_CLASSES)
from tactical_recovery import apply_module as add_tactics
from wave_reinforcements import apply_module as add_wave

ORIGINAL = Path(os.environ.get("ZOMBIEEE_ORIGINAL_MODULE", "/missing/ZOMBIEEE"))
CAP = 4


@unittest.skipUnless(ORIGINAL.is_dir(), "Owned original module required")
class DefenderRespawnTests(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.module = Path(temp.name)
        (self.module / "SceneObj").mkdir()
        for name in ("troops.txt", "scenes.txt", "mission_templates.txt",
                     "variables.txt"):
            shutil.copy2(ORIGINAL / name, self.module / name)
        for number in range(1, 6):
            name = f"scn_tbfc_invasion_{number}.sco"
            shutil.copy2(ORIGINAL / "SceneObj" / name,
                         self.module / "SceneObj" / name)
        patch_file(self.module, CAP, city_only=True)
        add_city(self.module)
        add_wave(self.module, cap=CAP, city_only=True)

    def _build(self, cap=CAP):
        troop_ids = index_troops(self.module / "troops.txt")
        troops = tuple(TROOP_BASE + troop_ids[name] for name in SURVIVOR_CLASSES)
        report = add_tactics(self.module, city_only=True, defender_cap=cap,
                             defender_troops=troops)
        return report, troops

    def _recovery_effects(self):
        lines = (self.module / "mission_templates.txt").read_text(
            encoding="utf-8").splitlines(keepends=True)
        at, count, end = mission_bounds(lines)
        self.assertEqual(count, 31)
        rows = [line.strip() for line in lines[at + 1:end]]
        return decode_trigger(rows[30])[1]

    def test_respawn_block_spawns_missing_private_survivors(self):
        report, troops = self._build()
        self.assertEqual(report["defender_respawn_cap"], CAP)
        self.assertEqual(tuple(report["defender_respawn_troops"]), troops)
        effects = self._recovery_effects()
        codes = [opcode for opcode, _ in effects]
        # missing = cap - living; bounded loop; four class branches spawn team 0
        self.assertIn(2121, codes)
        self.assertIn(6, codes)
        self.assertIn(2120, codes)
        self.assertIn(2119, codes)
        visitors = [args for opcode, args in effects if opcode == 1265]
        self.assertEqual(len(visitors), 4)
        self.assertEqual([args[1] for args in visitors], list(troops))
        self.assertTrue(all(args[3] == 0 for args in visitors))  # survivor team 0
        local_group = 1224979098644774912 + 10  # l10 = 5 + slot % 3
        self.assertTrue(all(args[4] == local_group for args in visitors))
        self.assertIn((2120, (local_group, local_group, 5)), effects)  # group 5..7
        self.assertIn((2119, (1224979098644774912 + 10,
                              1224979098644774912 + 7, 3)), effects)  # slot % 3

    def test_respawn_disabled_keeps_previous_trigger_bytes(self):
        report, _ = self._build(cap=0)
        self.assertEqual(report["defender_respawn_cap"], 0)
        self.assertFalse(any(opcode == 1265 for opcode, _ in self._recovery_effects()))

    def test_invalid_cap_or_troops_are_rejected(self):
        with self.assertRaises(PatchError):
            self._build(cap=9)
        troop_ids = index_troops(self.module / "troops.txt")
        troops = tuple(TROOP_BASE + troop_ids[name] for name in SURVIVOR_CLASSES)
        with self.assertRaises(PatchError):
            add_tactics(self.module, city_only=True, defender_cap=CAP,
                        defender_troops=troops[:3])


if __name__ == "__main__":
    unittest.main()
