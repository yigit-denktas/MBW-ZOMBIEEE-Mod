"""Pure-data tests for opt-in survivor bot spawn patch, not WSE2 gameplay."""
import os
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "tools"))
from patch_defenders import (
    PatchError, SURVIVOR_CLASSES, TROOP_BASE, build_trigger,
    index_troops, mission_bounds, patch_text,
)
from preflight import read_invasion_mission


def fixture():
    lines = ["missionsfile version 1", "1", "mst_multiplayer_iv multiplayer_iv 2 -1",
             "description", "64 0 16 1 0"]
    lines.extend(f"{i} 16 1 0" for i in range(1, 64))
    lines += ["25"] + ["1.000000 0.000000 0.000000 0 1 0" for _ in range(25)]
    return "\r\n".join(lines) + "\r\n"


def troops():
    return {name: index + 100 for index, name in enumerate(SURVIVOR_CLASSES)}


class DefenderPatchTests(unittest.TestCase):
    def test_original_compiled_triggers_preserved_with_crlf(self):
        original = fixture()
        changed = patch_text(original, troops(), 4)
        _, count, inserted = mission_bounds(changed.splitlines(keepends=True))
        self.assertEqual(count, 26)
        self.assertEqual(changed.count("1.000000 0.000000 0.000000 0 1 0"), 25)
        self.assertEqual(changed.count("\r\n"), original.count("\r\n") + 1)
        added_line = changed.splitlines(keepends=True)[inserted - 1]
        self.assertTrue(added_line.startswith("-20.000000"))
        self.assertEqual(changed.replace("26\r\n", "25\r\n", 1).replace(added_line, "", 1), original)

    def test_server_only_survivor_entries_and_team(self):
        tokens = build_trigger(4, troops()).split()
        self.assertEqual(tokens[:7], ["-20.000000", "0.000000", "0.000000", "1", "417", "0", "4"])
        for index in range(4):
            op = tokens[7 + 7 * index:14 + 7 * index]
            self.assertEqual(op[:2], ["1265", "5"])
            self.assertEqual(op[2], str(index % 2))
            self.assertEqual(op[4:], ["1", "0", "0"])
            self.assertGreaterEqual(int(op[3]), TROOP_BASE)

    def test_bounds_and_double_patch_rejected(self):
        for count in [-1, 0, 9]:
            with self.assertRaises(PatchError):
                patch_text(fixture(), troops(), count)
        once = patch_text(fixture(), troops(), 2)
        with self.assertRaises(PatchError):
            patch_text(once, troops(), 2)

    def test_missing_troops_rejected(self):
        with self.assertRaises(PatchError):
            patch_text(fixture(), {}, 4)

    def test_original_duplicate_invader_names_do_not_shift_ids(self):
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / "troops.txt"
            names = list(SURVIVOR_CLASSES) + ["trp_invader", "trp_invader"]
            path.write_text("troopsfile version 2\n6\n" +
                            "".join(name + " fields\n" for name in names))
            found = index_troops(path)
            self.assertEqual(found["trp_invader"], 4)
            self.assertEqual(len(found), 5)
            path.write_text("troopsfile version 2\n6\n" +
                            "".join(name + " fields\n" for name in names[:4]+[names[0],names[-1]]))
            with self.assertRaises(PatchError):
                index_troops(path)

    def test_patched_mission_passes_existing_static_parser(self):
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / "mission_templates.txt"
            path.write_bytes(patch_text(fixture(), troops(), 4).encode())
            self.assertEqual(read_invasion_mission(path)["triggers"], 26)

    def test_original_archive_integration_if_supplied(self):
        root = Path(os.environ.get("ZOMBIEEE_ORIGINAL_MODULE", "/mnt/data/zombie04_inspect/ZOMBIEEE"))
        if not root.is_dir():
            self.skipTest("Set ZOMBIEEE_ORIGINAL_MODULE to extracted user-owned original")
        before = (root / "mission_templates.txt").read_bytes()
        result = patch_text(before.decode(), index_troops(root / "troops.txt"), 4).encode()
        self.assertEqual(result.count(b"\r\n"), before.count(b"\r\n") + 1)
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / "mission_templates.txt"
            path.write_bytes(result)
            self.assertEqual(read_invasion_mission(path)["triggers"], 26)


if __name__ == "__main__":
    unittest.main()
