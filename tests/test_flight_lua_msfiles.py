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
    "agent_is_human": (1704, "can_fail"),
    "agent_is_non_player": (1707, "can_fail"),
    "agent_get_position": (1710, "lhs"),
    "agent_get_troop_id": (1718, "lhs"),
    "agent_get_kill_count": (1723, "lhs"),
    "agent_get_attack_action": (1763, "lhs"),
    "agent_get_accuracy_modifier": (2066, "lhs"),
    "agent_get_reload_speed_modifier": (2068, "lhs"),
    "agent_get_wielded_item": (1726, "lhs"),
    "agent_get_ammo": (1727, "lhs"),
    "agent_get_group": (1765, "lhs"),
    "agent_get_team": (1770, "lhs"),
    "agent_get_speed_modifier": (2067, "lhs"),
    "agent_get_time_speed_multiplier": (3336, "lhs"),
    "agent_get_action_speed_modifier": (3341, "lhs"),
    "team_get_hold_fire_order": (1784, "lhs"),
    "team_get_movement_order": (1785, "lhs"),
    "team_get_riding_order": (1786, "lhs"),
    "team_get_weapon_usage_order": (1787, "lhs"),
    "faction_get_slot": (522, "lhs"),
    "store_current_scene": (2211, "lhs"),
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
        # agent_get_team is now read through the returned-value lhs accessor
        # (A's live team-count fix); a failed read must mark the count unknown
        # instead of counting the agent as team 0.
        self.assertIn('read_agent_number("agent_get_team", agent)', self.main)
        self.assertIn("result.measured = false", self.main)
        self.assertIn("result.team0, result.team1 = -1, -1", self.main)
        self.assertNotIn("game.agent_get_team(0, agent)", self.main)

    def test_v2_troop_histogram_is_bounded_and_declared(self):
        # Names come from the bounded msfiles/ID_troops.py table, never from an
        # unverified string opcode: the probe must not call str_store_troop_name.
        self.assertIn("game.const.troops", self.main)
        self.assertNotIn("str_store_troop_name", self.main)
        self.assertIn("|troop_hist=1", self.main)
        for field in ("|troops_team0=", "|troops_team1=",
                      "|troop_names_team0=", "|troop_names_team1=",
                      "|troop_ids_unknown=", "|troops_truncated="):
            self.assertIn(field, self.main)
        for bound in ("MAX_HIST_TROOPS = 12", "MAX_HIST_LINE = 400",
                      "MAX_TROOP_NAME = 32", "MAX_PLAYER_IDS = 8"):
            self.assertIn(bound, self.main)

    def test_troop_id_map_is_bounded_and_documented(self):
        id_file = ROOT / "overlay" / "lua" / "msfiles" / "ID_troops.py"
        self.assertTrue(id_file.is_file())
        constants, _lists = parse_header(id_file.read_text(encoding="utf-8"))
        values = list(constants.values())
        self.assertLessEqual(len(constants), 32)  # bounded label table
        self.assertEqual(len(set(values)), len(values), "duplicate troop id label")
        for name, opcode in constants.items():
            self.assertIsInstance(opcode, int, name)
            self.assertGreaterEqual(opcode, 0)
            self.assertLess(opcode, 1000, name)
        # A's native_roster_patch scans invader IDs 894..911 (end-exclusive 912).
        self.assertEqual({v for v in values if 894 <= v <= 911}, set(range(894, 912)))
        # Defender clones appended by the remaster patch.
        self.assertEqual({v for v in values if 981 <= v <= 984}, {981, 982, 983, 984})
        for defender in ("trp_zdr_commando_bot", "trp_zdr_sniper_bot",
                         "trp_zdr_scout_bot", "trp_zdr_lumberjack_bot"):
            self.assertIn(defender, constants)
        for generic in ("trp_invader_multiplayer_ai", "trp_invaderb_multiplayer_ai"):
            self.assertIn(generic, constants)
        self.assertEqual(constants["trp_invader_multiplayer_ai"], 873)
        self.assertEqual(constants["trp_invaderb_multiplayer_ai"], 874)

    def test_v2_lifecycle_events_are_explicit(self):
        self.assertIn("|lifecycle=1", self.main)
        for event in ("player_joined", "player_died", "player_respawned",
                      "player_left", "round_started", "wave_started"):
            self.assertIn(f'emit("{event}"', self.main)
        # Events carry their observation basis; none is inferred from a metric.
        for basis in ("observed=first_alive_player", "observed=dead_agent",
                      "observed=alive_after_absence", "observed=agent_removed",
                      '"round_clock_reset"', "observed=wave_transition"):
            self.assertIn(basis, self.main)

    def test_v2_events_are_emitted_only_from_observed_transitions(self):
        # Player lifecycle requires a server-role world sample and previous state.
        self.assertIn('if role ~= "server" or not world or not world.ok then return end',
                      self.main)
        self.assertIn("previous_alive_players", self.main)
        self.assertIn("previous_round_start", self.main)

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



    def test_composition_categories_are_measured_and_bounded(self):
        # Playerless AI-vs-AI: humans are all human agents, players are human
        # non-AI agents, bots are human AI agents, horses are the native
        # agent_is_human==false fallback (agent_is_horse does not exist here).
        self.assertIn("|composition=1", self.main)
        self.assertIn("|human_getter=", self.main)
        self.assertIn("agent_is_horse does not exist in this engine", self.main)
        for field in ("|humans_team0=", "|humans_team1=",
                      "|players_team0=", "|players_team1=",
                      "|bot_agents_team0=", "|bot_agents_team1=",
                      "|horses_team0=", "|horses_team1=",
                      "|alive_players_team0="):
            self.assertIn(field, self.main)
        # A missing type predicate must not fabricate a category.
        self.assertIn("if not result.human_measured then", self.main)
        self.assertIn("result.horses[0], result.horses[1] = -1, -1", self.main)


    def test_engagement_and_position_telemetry_is_bounded(self):
        self.assertIn("|engagement=1|position_summary=1", self.main)
        self.assertIn("MAX_AI_SAMPLES = 8", self.main)
        for field in ("|no_player=", "|alive_team0=", "|alive_team1=",
                      "|kills_team0=", "|kills_team1=", "|pos_team0=", "|pos_team1=",
                      "|bbox_team0=", "|bbox_team1=",
                      "|pos_sampled_team0=", "|pos_sampled_team1="):
            self.assertIn(field, self.main)
        self.assertIn('emit("ai_sample"', self.main)
        # Only non-player bots are position-sampled; no human position is read.
        self.assertIn("is_human(agent) == true and is_npc(agent)", self.main)
        self.assertIn("reading a human player's position", self.main)
        # A missing getter must leave the aggregate unknown (-1), never 0.
        self.assertIn("if not supports_alive then result.alive[0], result.alive[1] = -1, -1 end",
                      self.main)
        self.assertIn("if not supports_kills then result.kills[0], result.kills[1] = -1, -1 end",
                      self.main)


    def test_pre_round_sampling_is_bounded_on_the_proven_entry_trigger(self):
        # No-client servers never start a round; the 1 s entry trigger is the
        # only probe trigger observed to run, so it carries bounded pre-round
        # samples (<=6) instead of relying on the unreached 15 s heartbeat.
        self.assertIn("MAX_PRE_ROUND_SAMPLES = 6", self.main)
        self.assertIn("|pre_round=1", self.main)
        self.assertIn('emit("pre_round_sample"', self.main)
        self.assertIn("local function pre_round_snapshot", self.main)
        self.assertLess(self.main.index("local function pre_round_snapshot"),
                        self.main.index("local function first_entry"))
        self.assertIn("pre_round_snapshot(sample_world(), resolve_role()", self.main)


    def test_team_tables_are_zero_based_and_players_arithmetic_parenthesised(self):
        # v3 runtime regression: Lua literals are 1-based, so team tables must be
        # declared explicitly 0-based, and concatenation needs parentheses around
        # arithmetic (a .. b - c would parse as (a .. b) - c).
        for table in ("humans", "bots", "horses", "alive", "kills", "pos_count"):
            self.assertIn(f"{table} = {{[0] = ", self.main)
        self.assertIn("pos_sum = {[0] = {0, 0}, [1] = {0, 0}}", self.main)
        self.assertNotIn("humans = {0, 0}", self.main)
        self.assertIn("|players_team0=\" .. (world.humans[0] - math.max(world.bots[0], 0))",
                      self.main)
        self.assertIn("|players_team1=\" .. (world.humans[1] - math.max(world.bots[1], 0))",
                      self.main)
        self.assertIn("kind=sample_world|error=", self.main)

    def test_round_started_requires_a_real_transition(self):
        # g_round_start_time increasing (15/30/45) is not a round identity: only
        # a clock reset or an observed round-end transition may emit, otherwise
        # one bounded probe_anomaly is reported.
        self.assertNotIn("observed=round_identity_change", self.main)
        self.assertIn('"round_clock_reset"', self.main)
        self.assertIn('"round_end_transition"', self.main)
        self.assertIn("kind=round_start_monotonic", self.main)
        self.assertIn("round_start < previous_round_start", self.main)
        self.assertIn("previous_round_ended == 1 and round_ended == 0", self.main)


    def test_lhs_reads_use_return_values_not_stale_registers(self):
        # WSE2 lhs ops return (result, error); game.reg0 is stale. Reading it
        # made every agent report one troop id and produced bogus kill sums.
        self.assertNotIn("tonumber(game.reg0)", self.main)
        self.assertIn("local ok, first, second, third = pcall", self.main)
        self.assertIn('if op_error ~= nil and type(op_error) == "number" and op_error ~= 0 then', self.main)
        self.assertIn("MAX_PLAUSIBLE_KILLS = 10000", self.main)
        self.assertIn("kind=kill_count_out_of_range", self.main)
        self.assertIn("result.kills_unknown[team] > 0", self.main)
        self.assertIn("|kills_measured_team0=", self.main)
        self.assertIn("|troop_read_unknown=", self.main)


    def test_division_telemetry_is_bounded_and_bot_only(self):
        for token in ("|groups_team0=", "|groups_team1=", "|group_read_unknown=",
                      "groups0 = {}, groups1 = {}", "sample.group"):
            self.assertIn(token, self.main)
        self.assertIn("read_group(agent)", self.main)
        # sampler stays bounded (histogram text helper caps ids/chars)
        self.assertIn("result.groups_text0 = (histogram_text(result.groups0))", self.main)


    def test_defender_telemetry_is_division_gated_and_bounded(self):
        for token in ("|defenders_team0=", "|defender_alive_team0=",
                      "|defender_kills_team0=", "|defender_read_unknown=",
                      "result.defender_count", "result.defender_read_unknown"):
            self.assertIn(token, self.main)
        self.assertIn("DEFENDER_TROOP_MIN = 981", self.main)
        self.assertIn("DEFENDER_TROOP_MAX = 984", self.main)
        self.assertIn("troop_defender or group_defender", self.main)
        self.assertIn("|defender_source=", self.main)
        self.assertIn("|defender_groups=", self.main)
        self.assertIn("|troop=", self.main)
        self.assertIn("MAX_PLAUSIBLE_KILLS", self.main)


    def test_group_reader_never_uses_a_fake_agent(self):
        # A lhs placeholder passed as 0 was bound as an agent id by the engine
        # and spammed "Invalid Agent ID: 0"; the group reader must use the real
        # agent only, defer until a full-round heartbeat, cache one-shot.
        self.assertIn("|group_reader=destination_agent", self.main)
        self.assertIn("local group_read_enabled = false", self.main)
        self.assertIn("if not agent_live(agent) then return -1 end", self.main)
        self.assertIn("if value == agent then return -1 end", self.main)
        self.assertIn("if group_capability_emitted then return end", self.main)
        self.assertIn("return fn(0, agent) end)", self.main)

    def test_group_reader_handles_both_lhs_return_shapes(self):
        # agent_get_group (1765) is condition-style in some builds: accept both
        # (intResult, intError) and (boolDidNotFail, intResult, intError), probe
        # the working convention once, and never guess a division.
        self.assertIn("type(first) == \"boolean\"", self.main)
        self.assertIn("local function read_group(agent)", self.main)
        self.assertIn("group_convention", self.main)
        self.assertIn("|group_convention=", self.main)
        self.assertIn("|group_reader=destination_agent", self.main)
        self.assertIn("kind=group_convention_unknown", self.main)
        self.assertIn("MAX_DIVISION = 255", self.main)
        self.assertIn("local group = read_group(agent)", self.main)


    def test_combat_and_wave_telemetry_surface(self):
        self.assertIn("|combat_v2=1", self.main)
        for token in ("|defender_weapons=", "|defender_modes=", "|ranged_team0=",
                      "|melee_team0=", "|defender_deaths=", "|horse_ids_team1=",
                      "|shield_team0=", "|mounted_team1=", "|action=",
                      "|weapon_mode=", "|weapon=", "|ammo=", "|alive=",
                      "defender_died"):
            self.assertIn(token, self.main)
        self.assertIn("agent_get_wielded_item", self.main)
        self.assertIn("agent_get_ammo", self.main)
        self.assertIn("agent_is_alive", self.main)


    def test_task41_speed_order_and_movement_readback_surface(self):
        for token in ("agent_get_speed_modifier", "agent_get_time_speed_multiplier",
                      "agent_get_action_speed_modifier",
                      "team_get_hold_fire_order", "team_get_movement_order",
                      "team_get_riding_order", "team_get_weapon_usage_order",
                      "|defender_speed_modifiers=", "|defender_time_multipliers=",
                      "|defender_action_speeds=", "|defender_orders=",
                      "|speed_read_unknown=", "|speed_modifier_getter=",
                      "|team_order_getter=", "|behavior_getter=0"):
            self.assertIn(token, self.main)
        self.assertIn("local function read_team_order", self.main)
        self.assertIn("agent_get_speed_modifier = 2067", header_text())


    def test_task43_team1_speed_and_order_scope_surface(self):
        for token in ("|speed=", "|time_multiplier=", "|action_speed=",
                      "|speed_modifiers_team1=", "|time_multipliers_team1=",
                      "|action_speeds_team1=",
                      "|defender_orders_scope=team0_subclasses_0_9_native_groups_no_op",
                      "for subclass = 0, 9 do",
                      "speed_hist_team[side]"):
            self.assertIn(token, self.main)


    def test_task55_faction_slot_and_scene_readback_surface(self):
        for token in ("faction_get_slot", "store_current_scene",
                      "|wave_faction_slots=", "|current_scene=",
                      "|faction_slot_getter=", "|scene_getter=",
                      "WAVE_SLOT_PROBES = {200, 221, 231, 241, 245}",
                      "read_faction_slot(FACTION_INVADER, slot)"):
            self.assertIn(token, self.main)
        self.assertIn("faction_get_slot = 522", header_text())
        self.assertIn("store_current_scene = 2211", header_text())


    def test_task55_faction_slot_uses_raw_id_and_no_spam_guard(self):
        # WSE2 Lua expects the raw faction id (16); the encoded module operand
        # (432345564227567632) produced "Invalid Faction ID: -2147483648" spam in
        # trigger 31/32 condition callbacks.
        self.assertIn("local FACTION_INVADER = 16", self.main)
        self.assertNotIn("432345564227567632", self.main)
        self.assertIn("faction < 0 or faction > MAX_FACTION_ID", self.main)
        self.assertIn("if wave_slot_read_enabled then", self.main)
        self.assertIn("local wave_slot_read_enabled = false", self.main)
        self.assertIn('role == "server"', self.main)
        self.assertIn('current_mission() == "mst_multiplayer_iv"', self.main)


    def test_task60_firearm_attack_action_surface(self):
        self.assertIn("agent_get_attack_action = 1763", header_text())
        self.assertIn("agent_get_accuracy_modifier = 2066", header_text())
        self.assertIn("agent_get_reload_speed_modifier = 2068", header_text())
        for token in ("|attack_action=", "|attack_action_getter=",
                      "|accuracy_getter=", "|reload_getter=",
                      "|accuracy_modifier=", "|reload_speed_modifier=",
                      "|reticle_getter=0", "|aim_error_getter=0",
                      "|fire_mode_getter=0"):
            self.assertIn(token, self.main)


    def test_invalid_agent_id_guard_surface(self):
        # Trigger 32 condition callbacks must never call an agent op with id 0.
        self.assertIn("|invalid_agent_guard=1", self.main)
        self.assertGreaterEqual(self.main.count("agent <= 0 then return false"), 2)
        self.assertIn("type(agent) ~= \"number\" or agent <= 0 then return nil", self.main)
        self.assertIn("type(agent) ~= \"number\" or agent <= 0 then return -1", self.main)


    def test_group_reader_two_arg_convention_and_skip_counters(self):
        self.assertIn("return fn(0, agent) end)", self.main)
        self.assertIn("|group_call_convention=two_arg", self.main)
        self.assertIn("|group_live_guard=1", self.main)
        self.assertIn("skipped_invalid_agent = 0, skipped_dead_agent = 0", self.main)
        self.assertIn("result.skipped_invalid_agent = result.skipped_invalid_agent + 1", self.main)
        self.assertIn("result.skipped_dead_agent = result.skipped_dead_agent + 1", self.main)
        self.assertIn("|skipped_invalid_agent=", self.main)
        self.assertIn("|skipped_dead_agent=", self.main)

if __name__ == "__main__":
    unittest.main()
