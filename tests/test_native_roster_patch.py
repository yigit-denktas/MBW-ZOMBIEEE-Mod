"""Compiled Native roster patch: team-2 faction bots must select Zombie troops."""
import os
from pathlib import Path
import shutil
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
from native_roster_patch import (SCRIPT_NAME, RosterPatchError, apply_module,
                                 expected_candidates, _ops_from_body,
                                 troop_factions)

ORIGINAL = Path(os.environ.get("ZOMBIEEE_ORIGINAL_MODULE", "/missing/ZOMBIEEE"))
TROOP_BASE = 360287970189639680


@unittest.skipUnless(ORIGINAL.is_dir(), "Owned original module required")
class NativeRosterPatchTests(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.module = Path(temp.name)
        for name in ("scripts.txt", "troops.txt"):
            shutil.copy2(ORIGINAL / name, self.module / name)
        self.original_scripts = (self.module / "scripts.txt").read_text(encoding="utf-8")
        self.factions = troop_factions(self.module)

    def _ops(self):
        lines = (self.module / "scripts.txt").read_text(encoding="utf-8").splitlines()
        header = next(i for i, line in enumerate(lines)
                      if line.startswith(SCRIPT_NAME + " "))
        return header, _ops_from_body(list(map(int, lines[header + 1].split())))

    def test_invader_candidates_are_native_zombie_troops(self):
        report = apply_module(self.module)
        self.assertTrue(report["applied"])
        self.assertEqual(report["invader_candidates"], list(range(894, 912)))
        for index in report["invader_candidates"]:
            self.assertEqual(self.factions[index], 16)
        self.assertNotIn(873, report["invader_candidates"])
        self.assertNotIn(874, report["invader_candidates"])

    def test_other_factions_keep_the_original_troop_range(self):
        before = [i for i in range(855, 875) if self.factions.get(i) == 15]
        apply_module(self.module)
        header, ops = self._ops()
        vector = [args for opcode, args in ops if opcode == 2133 and len(args) == 2]
        self.assertIn((1224979098644774924, TROOP_BASE + 855), vector)  # l12 fallback begin
        self.assertIn((1224979098644774925, TROOP_BASE + 875), vector)  # l13 fallback end
        self.assertIn((1224979098644774924, TROOP_BASE + 894), vector)  # l12 invader begin
        self.assertIn((1224979098644774925, TROOP_BASE + 912), vector)  # l13 invader end
        self.assertEqual(before, [i for i in range(855, 875)
                                  if self.factions.get(i) == 15])

    def test_only_the_bot_troop_script_body_changes(self):
        before = (self.module / "scripts.txt").read_text(encoding="utf-8").splitlines()
        apply_module(self.module)
        after = (self.module / "scripts.txt").read_text(encoding="utf-8").splitlines()
        self.assertEqual(len(before), len(after))
        changed = [i for i, (old, new) in enumerate(zip(before, after)) if old != new]
        self.assertEqual(len(changed), 1)
        self.assertTrue(before[changed[0] - 1].startswith(SCRIPT_NAME + " "))

    def test_second_patch_is_refused(self):
        apply_module(self.module)
        with self.assertRaises(RosterPatchError):
            apply_module(self.module)

    def test_malformed_script_body_is_refused(self):
        path = self.module / "scripts.txt"
        lines = path.read_text(encoding="utf-8").splitlines(keepends=True)
        header = next(i for i, line in enumerate(lines)
                      if line.startswith(SCRIPT_NAME + " "))
        body = lines[header + 1].split()
        body[0] = str(int(body[0]) + 1)  # claim one operation more than encoded
        lines[header + 1] = " ".join(body) + "\n"
        path.write_text("".join(lines), encoding="utf-8")
        with self.assertRaises(RosterPatchError):
            apply_module(self.module)

    def test_missing_script_is_refused(self):
        path = self.module / "scripts.txt"
        lines = [line for line in path.read_text(encoding="utf-8").splitlines(keepends=True)
                 if not line.startswith(SCRIPT_NAME + " ")]
        path.write_text("".join(lines), encoding="utf-8")
        with self.assertRaises(RosterPatchError):
            apply_module(self.module)


if __name__ == "__main__":
    unittest.main()
