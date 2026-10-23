"""Non-invasive compiled call-graph tests (not in-engine tests)."""
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "tools"))
from trace_calls import SCRIPT_BASE, decode_operations, read_mission_calls, read_scripts, trace


class TraceCallsTests(unittest.TestCase):
    def test_resolve_script_operand(self):
        code = [1, 2, SCRIPT_BASE + 42, 123]
        self.assertEqual(decode_operations(code, 0, 1), (4, [42]))

    def test_truncated_call(self):
        with self.assertRaises(ValueError):
            decode_operations([1, 2, SCRIPT_BASE], 0, 1)

    def test_minimal_invasion_call_map(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            (root / "scripts.txt").write_text(
                "scriptsfile version 1\n2\nfoo -1\n 0\nbar -1\n 1 1 1 " +
                str(SCRIPT_BASE) + "\n")
            (root / "mission_templates.txt").write_text(
                "missionsfile version 1\n1\nmst_multiplayer_iv multiplayer_iv 2 -1\n"
                "description\n1 0 16 1 0\n1\n1.0 0.0 0.0 0 1 1 1 " +
                str(SCRIPT_BASE + 1) + "\n")
            self.assertEqual(len(read_scripts(root / "scripts.txt")), 2)
            self.assertEqual(read_mission_calls(root / "mission_templates.txt")[0]["script_indices"], [1])
            report = trace(root)
            self.assertEqual(report["direct_mission_calls"], ["bar"])
            self.assertEqual(report["mission_trigger_count"], 1)


if __name__ == "__main__":
    unittest.main()
