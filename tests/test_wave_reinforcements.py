"""Original Beta 0.4 integration checks (set ZOMBIEEE_ORIGINAL_MODULE).

No game launch. Tests skip if the original RAR has not been extracted locally.
"""
import os
from pathlib import Path
import shutil
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
from patch_defenders import index_troops, patch_text as spawn_allies, mission_bounds, PatchError
from city_defense import patch_orders as city_order, scene_index
from wave_reinforcements import (
    globals_from_original, initialize_wave_state, reinforce_on_wave,
    patch_text as patch_waves, apply_module, SENTINEL, GLOBAL_BASE, WAVE_CHANGED,
)
ORIGINAL = Path(os.environ.get("ZOMBIEEE_ORIGINAL_MODULE", "/missing/ZOMBIEEE"))


@unittest.skipUnless(ORIGINAL.is_dir(), "Supply original extracted module using ZOMBIEEE_ORIGINAL_MODULE")
class WaveReinforcementTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.variables = (ORIGINAL / "variables.txt").read_bytes().decode()
        cls.troops = index_troops(ORIGINAL / "troops.txt")
        cls.original = (ORIGINAL / "mission_templates.txt").read_bytes().decode()
        cls.tactical = city_order(spawn_allies(cls.original, cls.troops, 4),
                                  scene_index(ORIGINAL / "scenes.txt"))

    def test_wave_variables_from_original(self):
        globals_ = globals_from_original(self.variables)
        self.assertEqual(globals_["wave_number"], GLOBAL_BASE + 1209)
        self.assertEqual(globals_[SENTINEL], GLOBAL_BASE + 1220)

    def test_reinforcement_ops(self):
        values = reinforce_on_wave(globals_from_original(self.variables), self.troops).split()
        self.assertEqual(values[:4], ["4.000000", "0.000000", "0.000000", "5"])
        for opcode in ("417", "1702", "1707", "1765", "1770", "2119", "1265"):
            self.assertIn(opcode, values)
        self.assertEqual(values.count("1265"), 4)

    def test_wave_gate_recognizes_new_round_at_lower_wave_number(self):
        from ai_wave_contract import decode_trigger
        conditions, _ = decode_trigger(reinforce_on_wave(
            globals_from_original(self.variables), self.troops))
        g = globals_from_original(self.variables)
        self.assertIn((WAVE_CHANGED, (g['wave_number'], g[SENTINEL])), conditions)
        self.assertNotIn((32, (g['wave_number'], g[SENTINEL])), conditions)

    def test_patch_preserves_original_triggers(self):
        changed, names = patch_waves(self.tactical, self.variables, self.troops)
        self.assertEqual(mission_bounds(changed.splitlines(keepends=True))[1], 29)
        self.assertEqual(len(names.splitlines()), len(self.variables.splitlines())+1)
        self.assertEqual(self.tactical.splitlines()[1994:2014], changed.splitlines()[1994:2014])

    def test_refuses_repeat_and_modified_global_table(self):
        changed, names = patch_waves(self.tactical, self.variables, self.troops)
        with self.assertRaises(PatchError):
            patch_waves(changed, names, self.troops)
        with self.assertRaises(PatchError):
            globals_from_original(self.variables + "not_original\n")

    def test_integrated_copy(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            for name in ("troops.txt", "variables.txt"):
                shutil.copy2(ORIGINAL/name,root/name)
            (root/"mission_templates.txt").write_bytes(self.tactical.encode())
            result = apply_module(root, cap=4)
            self.assertEqual(result["final_trigger_count"], 29)
            self.assertTrue((root/"variables.txt").read_text().endswith(SENTINEL+"\n"))


if __name__ == "__main__":
    unittest.main()
