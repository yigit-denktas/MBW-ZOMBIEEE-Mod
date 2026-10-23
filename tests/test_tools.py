"""Local tooling tests only. There is no CI and these are NOT gameplay tests."""
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "tools"))
from build import MODULE_NAME, ORIGINAL_SHA256, apply_overlay, rename_module_title, sha256
from doctor import REQUIRED_SCENES, REQUIRED_TABLES, inspect_module


class ToolingTests(unittest.TestCase):
    def fixture(self, path: Path) -> Path:
        path.mkdir()
        for name in REQUIRED_TABLES:
            (path / name).write_text("placeholder\n")
        (path / "module.ini").write_text("module_name = Native\ncompatible_with_warband = 1\n")
        (path / "mission_templates.txt").write_text("mst_multiplayer_iv multiplayer_iv 2 -1\n")
        (path / "scenes.txt").write_text("\n".join(f"scn_tbfc_invasion_{i} fake" for i in range(1, 6)))
        (path / "SceneObj").mkdir()
        for name in REQUIRED_SCENES:
            (path / "SceneObj" / name).write_bytes(b"x" * 3000)
        return path

    def test_sha256(self):
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / "abc"
            path.write_bytes(b"abc")
            self.assertEqual(sha256(path), "ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad")

    def test_archive_digest_contract(self):
        self.assertEqual(len(ORIGINAL_SHA256), 64)
        self.assertEqual(MODULE_NAME, "ZOMBIEEE_Remaster")

    def test_static_inspection_and_overlay(self):
        with tempfile.TemporaryDirectory() as td:
            module = self.fixture(Path(td) / "ZOMBIEEE")
            self.assertTrue(inspect_module(module)["core_ok"])
            self.assertFalse(inspect_module(module)["lua_bootstrap"])
            apply_overlay(module)
            self.assertTrue(inspect_module(module)["core_ok"])
            self.assertTrue(inspect_module(module)["lua_bootstrap"])
            self.assertIn("ZOMBIEEE Remaster", (module / "module.ini").read_text())
            apply_overlay(module)
            self.assertEqual((module / "module.ini").read_text().count("module_name ="), 1)

    def test_missing_scene_fails(self):
        with tempfile.TemporaryDirectory() as td:
            module = self.fixture(Path(td) / "ZOMBIEEE")
            (module / "SceneObj" / REQUIRED_SCENES[2]).unlink()
            self.assertFalse(inspect_module(module)["core_ok"])

    def test_ambiguous_name_fails(self):
        with tempfile.TemporaryDirectory() as td:
            ini = Path(td) / "module.ini"
            ini.write_text("module_name = x\nmodule_name = y\n")
            with self.assertRaises(ValueError):
                rename_module_title(ini)


if __name__ == "__main__":
    unittest.main()
