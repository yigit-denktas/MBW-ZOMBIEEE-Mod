"""Firearm accuracy profile tests: automatic weapons buffed, single-shot untouched."""
import os
from pathlib import Path
import shutil
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
from firearm_balance import (FirearmPatchError, accuracy_delta,
                             apply_module, item_index, patch_text)

ORIGINAL = Path(os.environ.get("ZOMBIEEE_ORIGINAL_MODULE", "/missing/ZOMBIEEE"))
AUTO = ("itm_m16a2", "itm_mp5", "itm_ak47", "itm_famas", "itm_p90", "itm_m249",
        "itm_hk_mp5k", "itm_hk_mp7")
GUARD = ("itm_remington_model_700", "itm_browning_cynergy", "itm_beretta_92fs",
         "itm_sw_5904")


def make_table(auto_accuracy=80, guard_accuracy=(99, 85, 73, 73)):
    """Synthetic compiled item table with one-mesh items."""
    def row(name, flag, accuracy):
        tokens = [name, name.title(), name.title(), "1", "mesh", "0", str(flag),
                  "123456", "100", "0", "1.500000", "100", "0", "0",
                  str(accuracy), "0", "0", "0", "0", "0", "0", "0", "0"]
        return " " + " ".join(tokens)

    rows = ["itemsfile version 3", "112"]
    for index, name in enumerate(AUTO):
        rows.append(row(name, 999, auto_accuracy + index))
    for name, accuracy in zip(GUARD, guard_accuracy):
        rows.append(row(name, 222, accuracy))
    for index in range(100):
        rows.append(row(f"itm_dummy_{index:03d}", 111, 50))
    rows.append("")
    return "\n".join(rows) + "\n"


class SyntheticFirearmBalanceTests(unittest.TestCase):
    def test_patch_buffs_only_automatic_items(self):
        text = make_table()
        before = text.splitlines()
        changed, report = patch_text(text, "default")
        after = changed.splitlines()
        self.assertTrue(report["applied"])
        self.assertEqual(report["changed_count"], len(AUTO))
        self.assertEqual(before[:2], after[:2])
        self.assertEqual(len(before), len(after))
        diff = [i for i, (old, new) in enumerate(zip(before, after)) if old != new]
        self.assertEqual(len(diff), len(AUTO))
        for line in (after[i] for i in diff):
            tokens = line.split()
            self.assertIn(tokens[0], AUTO)
        for item in report["changed"]:
            self.assertEqual(item["delta"], accuracy_delta(item["before"]))
            self.assertTrue(10 <= item["delta"] <= 20)

    def test_guards_and_other_items_unchanged(self):
        text = make_table()
        changed, _ = patch_text(text, "default")
        before, after = text.splitlines(), changed.splitlines()
        for old, new in zip(before, after):
            tokens = old.split()
            if tokens and tokens[0] in GUARD:
                self.assertEqual(old, new)

    def test_stock_profile_is_byte_identical(self):
        text = make_table()
        changed, report = patch_text(text, "stock")
        self.assertFalse(report["applied"])
        self.assertEqual(changed, text)

    def test_missing_anchor_is_rejected(self):
        text = make_table().replace("itm_m16a2", "itm_renamed")
        with self.assertRaises(FirearmPatchError):
            patch_text(text, "default")

    def test_truncated_table_is_rejected(self):
        with self.assertRaises(FirearmPatchError):
            patch_text(make_table().split("itm_dummy_000")[0], "default")

    def test_accuracy_index_matches_known_layout(self):
        text = make_table()
        items = item_index(text.splitlines())
        for index, tokens, accuracy_index in items:
            if tokens[0] == "itm_m16a2":
                self.assertEqual(tokens[accuracy_index], "80")
                self.assertEqual(tokens[accuracy_index + 1], "0")  # difficulty
                self.assertEqual(tokens[accuracy_index + 3], "0")  # speed rating placeholder
                break
        else:
            self.fail("synthetic m16a2 row missing")


@unittest.skipUnless(ORIGINAL.is_dir(), "Owned original module required")
class OriginalFirearmBalanceTests(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.module = Path(temp.name)
        shutil.copy2(ORIGINAL / "item_kinds1.txt", self.module / "item_kinds1.txt")

    def test_real_table_automatic_group_excludes_single_shot(self):
        text = (self.module / "item_kinds1.txt").read_text(encoding="utf-8")
        _, report = patch_text(text, "default")
        group = set(report["automatic_items"])
        for name in AUTO:
            self.assertIn(name, group)
        for name in GUARD:
            self.assertNotIn(name, group)
        self.assertGreaterEqual(len(group), 8)

    def test_apply_buffs_and_preserves_everything_else(self):
        before_text = (self.module / "item_kinds1.txt").read_text(encoding="utf-8")
        before = before_text.splitlines()
        report = apply_module(self.module)
        after = (self.module / "item_kinds1.txt").read_text(encoding="utf-8").splitlines()
        self.assertEqual(len(before), len(after))
        changed_rows = [i for i, (old, new) in enumerate(zip(before, after)) if old != new]
        self.assertEqual(len(changed_rows), report["changed_count"])
        for index in changed_rows:
            self.assertIn(after[index].split()[0], report["automatic_items"])
        for item in report["changed"]:
            self.assertEqual(item["delta"], accuracy_delta(item["before"]))
        self.assertNotEqual(report["sha256_before"], report["sha256_after"])

    def test_stock_apply_does_not_write(self):
        original = (self.module / "item_kinds1.txt").read_bytes()
        report = apply_module(self.module, "stock")
        self.assertFalse(report["applied"])
        self.assertEqual((self.module / "item_kinds1.txt").read_bytes(), original)


if __name__ == "__main__":
    unittest.main()
