"""Real Lua-semantics regression tests for the probe's team-indexing and
round-identity rules (no game required).

The probe runs on a Lua 5.1-ABI interpreter (WSE2 ships LuaJIT). These tests
execute the exact constructor/arithmetic constructs from `overlay/lua/main.lua`
on that real interpreter, then assert the source still uses those forms. A
1-based table literal (`{a, b}`) silently leaves team 0 nil and a
`a .. b - c` chain silently means `(a .. b) - c`; both crashed the v3 probe at
runtime (`attempt to perform arithmetic on a nil value`/string) and must stay
covered.

Skipped when the local WSE2 Lua dll is unavailable (the repo never ships it).
Override the dll with ZOMBIEEE_LUA_DLL.
"""
import ast
import ctypes
import os
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PROBE = Path(os.environ.get("ZOMBIEEE_PROBE_LUA", str(ROOT / "overlay" / "lua" / "main.lua")))
DLL_CANDIDATES = [
    os.environ.get("ZOMBIEEE_LUA_DLL"),
    str(ROOT / "local" / "wse2-1.1.5.4" / "lua5164.dll"),
    str(ROOT.parent / "local" / "wse2-1.1.5.4" / "lua5164.dll"),
]
LUA_DLL = next((path for path in DLL_CANDIDATES if path and Path(path).is_file()), None)

# These constructs mirror the probe exactly; the second block documents why the
# 1-based literal form is forbidden for team tables.
SEMANTICS_SCRIPT = """
local checks = {}
-- 0-based team tables: the only valid form for team ids 0/1.
local result = {
    humans = {[0] = 0, [1] = 0},
    bots = {[0] = 0, [1] = 0},
    alive = {[0] = 0, [1] = 0},
    kills = {[0] = 0, [1] = 0},
    pos_count = {[0] = 0, [1] = 0},
    pos_sum = {[0] = {0, 0}, [1] = {0, 0}},
}
result.humans[0] = result.humans[0] + result.bots[0]
result.kills[0] = result.kills[0] + 2
result.pos_sum[0][1] = result.pos_sum[0][1] + 10.5
checks[#checks + 1] = tostring(result.humans[0] == 0)
checks[#checks + 1] = tostring(result.kills[0] == 2)
checks[#checks + 1] = tostring(result.pos_sum[0][1] == 10.5)

-- Parenthesised arithmetic before concatenation (the v3 latent bug).
local players = "|players_team0=" .. (result.humans[0] - math.max(result.bots[0], 0))
checks[#checks + 1] = tostring(players == "|players_team0=0")
local ok, err = pcall(function() return ("a" .. result.humans[0]) - 1 end)
checks[#checks + 1] = tostring(ok == false)
checks[#checks + 1] = tostring(tostring(err):find("arithmetic") ~= nil)

-- 1-based literal must be rejected as a model of team tables.
local bad = { humans = {0, 0} }
checks[#checks + 1] = tostring(bad.humans[0] == nil)
checks[#checks + 1] = tostring(bad.humans[1] == 0)


-- lhs operation accessor contract: result comes from the RETURNED values,
-- never from a stale register; errors and non-numeric results are unknown.
local function read_agent_number(fn)
    local ok, value, op_error = pcall(fn)
    if not ok then return -1 end
    if op_error ~= nil and op_error ~= 0 then return -1 end
    local number = tonumber(value)
    if number == nil then return -1 end
    return math.floor(number)
end
checks[#checks + 1] = tostring(read_agent_number(function() return 5, 0 end) == 5)
checks[#checks + 1] = tostring(read_agent_number(function() return 7, 0 end) == 7)
checks[#checks + 1] = tostring(read_agent_number(function() return 7, 1 end) == -1)
checks[#checks + 1] = tostring(read_agent_number(function() error("boom") end) == -1)
checks[#checks + 1] = tostring(read_agent_number(function() return nil, 0 end) == -1)

-- Hybrid lhs return shapes: plain (intResult, intError) and condition-style
-- (boolDidNotFail, intResult, intError) must both decode; failures are -1.
local function read_lhs(fn)
    local ok, first, second, third = pcall(fn)
    if not ok then return -1 end
    local value, op_error
    if type(first) == "boolean" then value, op_error = second, third
    else value, op_error = first, second end
    if op_error ~= nil and type(op_error) == "number" and op_error ~= 0 then return -1 end
    local number = tonumber(value)
    if number == nil then return -1 end
    return math.floor(number)
end
checks[#checks + 1] = tostring(read_lhs(function() return 5, 0 end) == 5)
checks[#checks + 1] = tostring(read_lhs(function() return true, 6, 0 end) == 6)
checks[#checks + 1] = tostring(read_lhs(function() return false, 6, 1 end) == -1)
checks[#checks + 1] = tostring(read_lhs(function() return true, nil, 0 end) == -1)

-- Convention detection for agent_get_group: try lhs call, then direct call,
-- cache whichever returns a plausible division, else "unreadable".
local function group_from(ok, first, second)
    if not ok then return -1 end
    local value
    if type(first) == "boolean" then value = second
    elseif type(first) == "number" then value = first
    else value = second end
    if type(value) ~= "number" or value < 0 or value > 255 then return -1 end
    return math.floor(value)
end
local function group_lhs(fn)
    local ok, first, second = pcall(function() return fn(0, 1) end)
    return group_from(ok, first, second)
end
local function group_direct(fn)
    local ok, first, second = pcall(function() return fn(1) end)
    return group_from(ok, first, second)
end
local function detect(fn)
    local value = group_lhs(fn)
    if value >= 0 then return "lhs", value end
    value = group_direct(fn)
    if value >= 0 then return "direct", value end
    return "unreadable", -1
end
local conv, value
conv, value = detect(function(...)
    if select("#", ...) ~= 2 then error("argc") end
    return 5, 0
end)
checks[#checks + 1] = tostring(conv == "lhs" and value == 5)
conv, value = detect(function(...)
    if select("#", ...) ~= 1 then error("argc") end
    return true, 7, 0
end)
checks[#checks + 1] = tostring(conv == "direct" and value == 7)
conv, value = detect(function() error("unreadable") end)
checks[#checks + 1] = tostring(conv == "unreadable" and value == -1)

-- Group reader safety contract: never call with a fake agent, detect once,
-- guard an agent-id echo, and stay unknown rather than guessing.
local group_convention, capability_lines, calls = nil, 0, 0
local function decode_group(agent, ok, first, second)
    if not ok then return -1 end
    local value
    if type(first) == "boolean" then value = second
    elseif type(first) == "number" then value = first
    else value = second end
    if type(value) ~= "number" or value < 0 or value > 255 then return -1 end
    value = math.floor(value)
    if value == agent then return -1 end
    return value
end
local function read_group(agent, fn)
    if type(fn) ~= "function" then return -1 end
    if type(agent) ~= "number" or agent <= 0 then return -1 end
    if group_convention == nil then
        calls = calls + 1
        local ok, first, second = pcall(function() return fn(0, agent) end)
        local candidate = decode_group(agent, ok, first, second)
        group_convention = candidate >= 0 and "direct" or "unknown"
        capability_lines = capability_lines + 1
    end
    if group_convention ~= "direct" then return -1 end
    calls = calls + 1
    local ok, first, second = pcall(function() return fn(0, agent) end)
    return decode_group(agent, ok, first, second)
end
local function echo_fn(_destination, agent) return agent, 0 end
local function group_fn(_destination, _agent) return 6, 0 end
checks[#checks + 1] = tostring(read_group(0, group_fn) == -1)          -- no fake agent
checks[#checks + 1] = tostring(read_group(-1, group_fn) == -1)
local ok_group, group_value = pcall(function()
    return read_group(12, echo_fn)  -- first agent, direct call echoes its id
end)
checks[#checks + 1] = tostring(ok_group and group_value == -1)
checks[#checks + 1] = tostring(group_convention == "unknown")
checks[#checks + 1] = tostring(capability_lines == 1)
local one_shot_before = calls
checks[#checks + 1] = tostring(read_group(12, echo_fn) == -1)
checks[#checks + 1] = tostring(group_convention == "unknown")

-- A fresh reader verifies the direct convention once, then reuses it.
group_convention, capability_lines, calls = nil, 0, 0
checks[#checks + 1] = tostring(read_group(7, group_fn) == 6)
checks[#checks + 1] = tostring(group_convention == "direct")
checks[#checks + 1] = tostring(capability_lines == 1)

-- Two-argument convention: destination=0, agent=real id.
group_convention, capability_lines, calls = nil, 0, 0
local seen_destination, seen_agent
local function capture_fn(destination, agent)
    seen_destination, seen_agent = destination, agent
    return 11, 0
end
checks[#checks + 1] = tostring(read_group(7, capture_fn) == 11)
checks[#checks + 1] = tostring(seen_destination == 0 and seen_agent == 7)

-- Faction-slot guard: never call a faction op with an encoded/negative operand,
-- and never call it for an invalid slot.
local function read_faction_slot(faction, slot, fn)
    if type(faction) ~= "number" or faction < 0 or faction > 63 then return -1 end
    if type(slot) ~= "number" or slot < 0 or slot > 255 then return -1 end
    return fn(0, faction, slot)
end
local faction_calls = 0
local function faction_mock(_, faction, slot)
    faction_calls = faction_calls + 1
    return 360287970189640574
end
checks[#checks + 1] = tostring(read_faction_slot(-1, 200, faction_mock) == -1)
checks[#checks + 1] = tostring(read_faction_slot(432345564227567632, 200, faction_mock) == -1)
checks[#checks + 1] = tostring(read_faction_slot(16, 999, faction_mock) == -1)
checks[#checks + 1] = tostring(faction_calls == 0)
checks[#checks + 1] = tostring(read_faction_slot(16, 200, faction_mock) == 360287970189640574)
checks[#checks + 1] = tostring(faction_calls == 1)

-- Invalid-agent guard: never pass 0/negative/non-number to an agent op.
local function valid_agent_id(agent)
    return type(agent) == "number" and agent > 0 and math.floor(agent) == agent
end
checks[#checks + 1] = tostring(valid_agent_id(0) == false)
checks[#checks + 1] = tostring(valid_agent_id(-1) == false)
checks[#checks + 1] = tostring(valid_agent_id("3") == false)
checks[#checks + 1] = tostring(valid_agent_id(3) == true)

-- Team-order guard: group 0 must never reach the op; groups 1..9 only.
local team_calls = 0
local function read_team_order(team, subclass, fn)
    if type(team) ~= "number" or team < 0 or team > 1 then return -1 end
    if type(subclass) ~= "number" or subclass < 1 or subclass > 9 then return -1 end
    team_calls = team_calls + 1
    return fn(0, team, subclass)
end
checks[#checks + 1] = tostring(read_team_order(0, 0, function() team_calls = team_calls + 1; return 0, 0 end) == -1)
checks[#checks + 1] = tostring(team_calls == 0)
local seen_team, seen_subclass
local team_value = read_team_order(0, 5, function(destination, team, subclass)
    seen_team, seen_subclass = team, subclass
    return 2, 0
end)
checks[#checks + 1] = tostring(team_value == 2 and seen_team == 0 and seen_subclass == 5)
return table.concat(checks, ",")
"""


def load_lua():
    dll = ctypes.CDLL(LUA_DLL)
    dll.luaL_newstate.restype = ctypes.c_void_p
    dll.luaL_openlibs.argtypes = [ctypes.c_void_p]
    dll.luaL_loadstring.argtypes = [ctypes.c_void_p, ctypes.c_char_p]
    dll.luaL_loadstring.restype = ctypes.c_int
    dll.lua_pcall.argtypes = [ctypes.c_void_p, ctypes.c_int, ctypes.c_int, ctypes.c_int]
    dll.lua_pcall.restype = ctypes.c_int
    dll.lua_tolstring.argtypes = [ctypes.c_void_p, ctypes.c_int, ctypes.c_void_p]
    dll.lua_tolstring.restype = ctypes.c_char_p
    dll.lua_close.argtypes = [ctypes.c_void_p]
    return dll


@unittest.skipUnless(LUA_DLL, "local WSE2 Lua dll not available")
class RealLuaSemanticsTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.dll = load_lua()

    def run_lua(self, script):
        state = self.dll.luaL_newstate()
        self.assertTrue(state)
        self.dll.luaL_openlibs(state)
        try:
            rc = self.dll.luaL_loadstring(state, script.encode("utf-8"))
            self.assertEqual(rc, 0)
            rc = self.dll.lua_pcall(state, 0, 1, 0)  # one result: the checks string
            if rc != 0:
                message = self.dll.lua_tolstring(state, -1, None) or b"?"
                self.fail("Lua error: " + message.decode("utf-8", "replace"))
            raw = self.dll.lua_tolstring(state, -1, None) or b""
            return raw.decode("utf-8", "replace")
        finally:
            self.dll.lua_close(state)

    def test_team_tables_arithmetic_and_precedence(self):
        checks = self.run_lua(SEMANTICS_SCRIPT).split(",")
        self.assertEqual(len(checks), 45)
        for index, value in enumerate(checks, 1):
            self.assertEqual(value, "true", f"Lua semantics check {index} failed")

    def test_probe_source_uses_the_verified_forms(self):
        text = PROBE.read_text(encoding="utf-8")
        # 0-based team tables (v3 regression: `humans = {0, 0}` left [0] nil).
        for table in ("humans", "bots", "horses", "alive", "kills", "pos_count"):
            self.assertIn(f"{table} = {{[0] = ", text)
        self.assertIn("pos_sum = {[0] = {0, 0}, [1] = {0, 0}}", text)
        self.assertNotIn("humans = {0, 0}", text)
        # Parenthesised arithmetic before string concatenation.
        self.assertIn("|players_team0=\" .. (world.humans[0] - math.max(world.bots[0], 0))",
                      text)
        self.assertIn("|players_team1=\" .. (world.humans[1] - math.max(world.bots[1], 0))",
                      text)
        # A silent sample_world failure is not allowed: bounded probe_failed.
        self.assertIn('kind=sample_world|error=', text)

    def test_round_identity_requires_a_real_transition(self):
        text = PROBE.read_text(encoding="utf-8")
        # A monotonically increasing g_round_start_time must not emit
        # round_started (false events); only a clock reset or observed round-end
        # transition may. The increase is reported once as a bounded anomaly.
        self.assertNotIn("observed=round_identity_change", text)
        self.assertIn('"round_clock_reset"', text)
        self.assertIn('"round_end_transition"', text)
        self.assertIn('emit("round_started", "|observed="', text)
        self.assertIn("round_clock_reset", text)
        self.assertIn("kind=round_start_monotonic", text)
        self.assertIn("round_start < previous_round_start", text)
        self.assertIn("previous_round_ended == 1 and round_ended == 0", text)
        parse = ast.parse if False else None  # source is Lua; static string checks only


if __name__ == "__main__":
    unittest.main()
