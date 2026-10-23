"""Static contract tests for the WSE2 Lua operation metadata (offline only).

Live incident (2026-10-24, mst_multiplayer_iv Trigger [32]: the ZDB1 15 s
heartbeat) logged on both server and client, every 15 s::

    SCRIPT ERROR: Illegal lvalue in statement
    - Lua (line 0, opcode 1770, modifier 0x0)
    - Mission Template [44] mst_multiplayer_iv Trigger [32] Conditions (Lua)
      (line 0, opcode 5113, modifier 0x0)

The same session's ZDB1 lines bind the index: ``boot|triggers=31``,
``probe_registered|kind=entry|index=31``,
``probe_registered|kind=heartbeat|index=32``. Trigger [32] is therefore this
repository's own 15 s heartbeat. Opcode 5113 is WSE2's ``lua_triggerCallback``
and opcode 1770 is native ``agent_get_team``.

WSE2's luaGuide requires ``lua/msfiles/header_operations.py`` to keep the
trailing ``lhs_operations = [...]`` / ``can_fail_operations = [...]`` lists: the
Lua bridge learns an operation's argument and return convention only from
those lists.

* Without an lhs declaration, ``game.agent_get_team(0, agent)`` (opcode 1770)
  sends the destination register number as a plain constant and the script VM
  aborts the store with "Illegal lvalue in statement".
* Without a can_fail declaration, ``game.multiplayer_is_server()`` (opcode 417,
  used as a bare condition in the original compiled mission templates) returns
  an error code instead of the boolean, which is why the dedicated host logged
  ``role=client`` and every server-only sample was skipped.

These tests read only repository files. No game, no original module, no assets.
"""
import ast
import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
HEADER = ROOT / "overlay" / "lua" / "msfiles" / "header_operations.py"
MAIN = ROOT / "overlay" / "lua" / "main.lua"

# Operation class expected from the native Warband operation signatures: a
# leading <destination> argument makes the operation lhs; a boolean condition
# (used bare inside modsys trigger conditions) makes it can-fail. Opcodes are
# pinned so a silently mis-transcribed number fails here instead of executing
# a different engine operation.
OPS = {
    "multiplayer_is_server": (417, "can_fail"),
    "agent_is_alive": (1702, "can_fail"),
    "agent_is_non_player": (1707, "can_fail"),
    "agent_get_position": (1710, "lhs"),
    "agent_get_troop_id": (1718, "lhs"),
    "agent_get_kill_count": (1723, "lhs"),
    "agent_get_wielded_item": (1726, "lhs"),
    "agent_get_ammo": (1727, "lhs"),
    "agent_get_group": (1765, "lhs"),
    "agent_get_team": (1770, "lhs"),
}

# `game.<name>` members that are WSE2 Lua API rather than module-system
# operations, so they have no opcode and no operation class.
LUA_API = frozenset({
    "addTrigger", "removeTrigger", "getNumTriggers", "getNumTemplates",
    "getCurTemplateId", "getCurTemplateNo", "getTemplateId", "agentsIt",
    "gvar", "reg0", "preg", "sreg", "const", "op",
})

LIVE_ERROR = (
    "live evidence: SCRIPT ERROR: Illegal lvalue in statement / "
    "Lua (line 0, opcode 1770) / Trigger [32] Conditions (Lua) (opcode 5113)"
)


def header_text():
    return HEADER.read_text(encoding="utf-8")


def main_text():
    return MAIN.read_text(encoding="utf-8")


def parse_header(text):
    """Return (opcode constants, {list name: [bare names]})."""
    tree = ast.parse(text, filename=str(HEADER))
    constants, lists = {}, {}
    for node in tree.body:
        if (isinstance(node, ast.Assign) and len(node.targets) == 1
                and isinstance(node.targets[0], ast.Name)):
            name = node.targets[0].id
            value = node.value
            if (isinstance(value, ast.Constant)
                    and isinstance(value.value, int)
                    and not isinstance(value.value, bool)):
                constants[name] = value.value
            elif isinstance(value, (ast.List, ast.Tuple)):
                lists[name] = list(_list_entries(value))
        elif (isinstance(node, ast.AugAssign) and isinstance(node.target, ast.Name)
                and isinstance(node.value, (ast.List, ast.Tuple))):
            lists.setdefault(node.target.id, []).extend(_list_entries(node.value))
    return constants, lists


def _list_entries(node):
    for element in node.elts:
        if isinstance(element, ast.Name):
            yield element.id
        elif isinstance(element, ast.Constant) and isinstance(element.value, str):
            yield element.value


def called_operations(text):
    """Module-system operations invoked by the overlay, by literal name."""
    names = set(re.findall(r"game\.([A-Za-z_][A-Za-z0-9_]*)\s*\(", text))
    # Dynamic dispatch: the operation name is a literal argument here.
    names.update(re.findall(
        r'read_agent_number\(\s*"([A-Za-z_][A-Za-z0-9_]*)"', text))
    names.update(re.findall(
        r'binding_flag\(\s*"([A-Za-z_][A-Za-z0-9_]*)"', text))
    return names - LUA_API


class LuaOperationMetadataTests(unittest.TestCase):
    def setUp(self):
        self.constants, self.lists = parse_header(header_text())
        self.main = main_text()

    def test_msfiles_declares_operation_class_lists(self):
        # WSE2's bridge has no fallback class table: without these lists every
        # declared operation is called as a plain "other" operation.
        self.assertIn("lhs_operations", self.lists, LIVE_ERROR)
        self.assertIn("can_fail_operations", self.lists, LIVE_ERROR)
        self.assertTrue(self.lists["lhs_operations"], LIVE_ERROR)
        self.assertTrue(self.lists["can_fail_operations"], LIVE_ERROR)

    def test_declared_opcodes_match_native_numbers(self):
        for name, (opcode, _kind) in OPS.items():
            self.assertEqual(
                self.constants.get(name), opcode,
                f"{name} must be opcode {opcode} for the engine to execute "
                f"the intended operation (got {self.constants.get(name)!r})")

    def test_every_used_operation_is_classified(self):
        unclassified = sorted(called_operations(self.main) - set(OPS))
        self.assertEqual(
            unclassified, [],
            "new game.<operation>() call site(s) are not classified in this "
            "test; add the opcode and lhs/can_fail class, then declare it in "
            "lua/msfiles/header_operations.py (" + LIVE_ERROR + ")")

    def test_lhs_operations_cover_destination_operations(self):
        declared = set(self.lists.get("lhs_operations", ()))
        used = called_operations(self.main)
        for name, (_opcode, kind) in OPS.items():
            if kind != "lhs" or name not in used:
                continue
            self.assertIn(
                name, declared,
                f"{name} is called with a destination register argument but is "
                f"not in lhs_operations; WSE2 would pass the register number as "
                f"a constant and the VM would reject the store ({LIVE_ERROR})")

    def test_can_fail_operations_cover_boolean_predicates(self):
        declared = set(self.lists.get("can_fail_operations", ()))
        used = called_operations(self.main)
        for name, (_opcode, kind) in OPS.items():
            if kind != "can_fail" or name not in used:
                continue
            self.assertIn(
                name, declared,
                f"{name} returns a boolean condition but is not in "
                f"can_fail_operations; WSE2 would return an error code instead "
                f"of the result (live: dedicated host logged role=client)")

    def test_heartbeat_trigger_still_registers_and_emits(self):
        # The fix must not disable the recorder probe itself.
        self.assertRegex(
            self.main,
            r"pcall\(\s*game\.addTrigger\s*,\s*MISSION\s*,\s*15\.0\s*,\s*0\s*,\s*0\s*,\s*heartbeat\s*\)")
        self.assertIn('emit("heartbeat"', self.main)
        self.assertIn('emit("probe_registered", "|kind=heartbeat|index="', self.main)
        self.assertIn("ZDB1|event", self.main)

    def test_team_counts_fail_closed_to_unknown(self):
        # agent_get_team failures must not be counted as team 0 (the live
        # attempt-4 team0=1 can coincide with the failed call's zero result).
        self.assertIn("game.agent_get_team(0, agent)", self.main)
        self.assertIn("op_error", self.main)
        self.assertIn("measured and a or -1", self.main)
        self.assertIn("measured and z or -1", self.main)

    def test_role_probe_uses_can_fail_operation(self):
        self.assertIn("game.multiplayer_is_server", self.main)
        self.assertIn("multiplayer_is_server",
                      self.lists.get("can_fail_operations", ()),
                      "multiplayer_is_server must be a declared can-fail "
                      "operation (" + LIVE_ERROR + ")")
        # Unrecognized results stay unknown rather than defaulting to client.
        self.assertIn('return "unknown"', self.main)

    def test_game_type_is_not_conflated_with_tactical_mode(self):
        self.assertIn('"|game_type=" .. global_int("g_multiplayer_game_type")', self.main)
        self.assertRegex(
            self.main,
            r'"\|mode="\s*\.\.\s*global_int\("zdr_defence_mode"\)')

    def test_spawn_and_team1_globals_are_guarded_reads(self):
        for gvar, field in (
                ("g_multiplayer_ready_for_spawning_agent", "|ready_for_spawn="),
                ("g_multiplayer_num_bots_team_1", "|bots_team1="),
                ("g_round_start_time", "|round_start=")):
            self.assertIn(f'global_int("{gvar}")', self.main)
            self.assertIn(field, self.main)
        # Unknown getters use -1, never a fabricated zero.
        self.assertIn("return -1", self.main)

    def test_overlay_marks_fixed_metadata_in_evidence(self):
        # Evidence produced before the fix has no opmeta marker, so its role
        # and team fields cannot be read as a measured composition.
        self.assertIn("|opmeta=1", self.main)

    def test_live_trigger_32_is_the_heartbeat_not_a_mission_trigger(self):
        # The original mst_multiplayer_iv has 31 triggers (indices 0-30), so
        # the appended entry=31 / heartbeat=32 mapping from the live log is the
        # only way Trigger [32] can be this overlay's own registration.
        self.assertIn("game.getNumTriggers(MISSION)", self.main)
        self.assertIn("|kind=entry|index=", self.main)


if __name__ == "__main__":
    unittest.main()
