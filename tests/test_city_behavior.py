"""Tests for the offline Warband AI behavior plan prototype (task-35).

The prototype is pure Python: these tests assert the community-sourced opcode
and enum tables and the plan/validation rules. They prove nothing about engine
behavior and never launch the game.
"""

import io
import json
import unittest
from contextlib import redirect_stdout

from tools.city_behavior import (
    NATIVE_OPS,
    SIMPLE_BEHAVIORS,
    SUBCLASSES,
    TEAM_ORDERS,
    WSE2_OPS,
    Op,
    describe,
    hold_and_fire_plan,
    main,
    validate_plan,
    visitor_spawn_plan,
    zombie_speed_plan,
)


class EnumTableTests(unittest.TestCase):
    def test_team_order_enum_matches_community_header(self):
        self.assertEqual(TEAM_ORDERS["mordr_hold"], 0)
        self.assertEqual(TEAM_ORDERS["mordr_charge"], 2)
        self.assertEqual(TEAM_ORDERS["mordr_stand_ground"], 11)
        self.assertEqual(TEAM_ORDERS["mordr_hold_fire"], 12)
        self.assertEqual(TEAM_ORDERS["mordr_fire_at_will"], 13)
        self.assertEqual(TEAM_ORDERS["mordr_use_ranged_weapons"], 16)

    def test_group_subclasses(self):
        self.assertEqual(SUBCLASSES["grc_infantry"], 0)
        self.assertEqual(SUBCLASSES["grc_archers"], 1)
        self.assertEqual(SUBCLASSES["grc_cavalry"], 2)
        self.assertEqual(SUBCLASSES["grc_heroes"], 3)
        self.assertEqual(SUBCLASSES["grc_everyone"], 9)

    def test_simple_behaviors(self):
        self.assertEqual(SIMPLE_BEHAVIORS["aisb_hold"], 0)
        self.assertEqual(SIMPLE_BEHAVIORS["aisb_ranged"], 5)
        self.assertEqual(SIMPLE_BEHAVIORS["aisb_no_enemies"], 12)


class OpcodeTableTests(unittest.TestCase):
    def test_native_ops(self):
        expected = {
            "agent_set_scripted_destination": 1730,
            "agent_force_rethink": 1732,
            "agent_clear_scripted_mode": 1735,
            "agent_set_speed_limit": 1736,
            "agent_set_attack_action": 1745,
            "agent_set_defend_action": 1746,
            "agent_set_wielded_item": 1747,
            "agent_get_attack_action": 1763,
            "agent_set_group": 1766,
            "agent_set_team": 1771,
            "agent_set_division": 1783,
            "agent_unequip_item": 1774,
            "agent_set_ammo": 1776,
            "team_get_hold_fire_order": 1784,
            "team_get_weapon_usage_order": 1787,
            "team_give_order": 1790,
            "team_set_order_position": 1791,
            "entry_point_get_position": 1780,
            "set_spawn_position": 1970,
            "spawn_agent": 1972,
            "agent_set_speed_modifier": 2093,
            "add_visitors_to_current_scene": 1265,
            "faction_set_slot": 502,
        }
        for name, number in expected.items():
            self.assertEqual(NATIVE_OPS[name], number, name)

    def test_wse2_ops(self):
        expected = {
            "agent_set_scripted_destination_no_attack": 1748,
            "agent_ai_set_simple_behavior": 3314,
            "agent_set_item_slot_ammo": 3305,
            "agent_set_time_speed_multiplier": 3335,
            "agent_set_action_speed_modifier": 3340,
            "agent_ai_set_can_weapon_switch": 3343,
            "agent_ai_set_can_fight": 3344,
            "agent_ai_set_can_aim": 3352,
        }
        for name, number in expected.items():
            self.assertEqual(WSE2_OPS[name], number, name)


class HoldPlanTests(unittest.TestCase):
    def test_hold_plan_posts_position_before_order(self):
        plan = hold_and_fire_plan()
        names = [op.name for op in plan]
        self.assertEqual(names[0], "team_set_order_position")
        self.assertEqual(names[1], "team_give_order")
        self.assertEqual(plan[0].args, (0, 9, 120))
        self.assertEqual(plan[1].args, (0, 9, TEAM_ORDERS["mordr_hold"]))
        self.assertTrue(all(op.number == NATIVE_OPS[op.name] for op in plan))

    def test_hold_plan_fire_and_ranged_orders(self):
        plan = hold_and_fire_plan(fire_order="fire_at_will")
        orders = [op.args[2] for op in plan if op.name == "team_give_order"]
        self.assertIn(TEAM_ORDERS["mordr_hold"], orders)
        self.assertIn(TEAM_ORDERS["mordr_fire_at_will"], orders)
        self.assertIn(TEAM_ORDERS["mordr_use_ranged_weapons"], orders)
        self.assertNotIn(TEAM_ORDERS["mordr_hold_fire"], orders)

    def test_hold_fire_is_issued_once_and_optional(self):
        plan = hold_and_fire_plan(hold_fire=False, ranged_weapons=False)
        orders = [op.args[2] for op in plan if op.name == "team_give_order"]
        self.assertNotIn(TEAM_ORDERS["mordr_hold_fire"], orders)
        with self.assertRaises(ValueError):
            hold_and_fire_plan(fire_order="mordr_hold_fire")

    def test_per_agent_wse2_safeties_emitted(self):
        plan = hold_and_fire_plan(agent_ids=(7, 9), guarantee_seconds=5)
        can_switch = [op for op in plan
                      if op.name == "agent_ai_set_can_weapon_switch"]
        behaviors = [op for op in plan
                     if op.name == "agent_ai_set_simple_behavior"]
        self.assertEqual(len(can_switch), 2)
        self.assertTrue(all(op.args[1] == 0 for op in can_switch))
        self.assertEqual([op.args[0] for op in behaviors], [7, 9])
        self.assertTrue(all(op.args[1] == SIMPLE_BEHAVIORS["aisb_hold"]
                            for op in behaviors))
        self.assertTrue(all(op.args[2] == 5 for op in behaviors))

    def test_agent_id_validation(self):
        with self.assertRaises(ValueError):
            hold_and_fire_plan(agent_ids=(3, 3))
        with self.assertRaises(ValueError):
            hold_and_fire_plan(agent_ids=tuple(range(1, 20)))
        with self.assertRaises(ValueError):
            hold_and_fire_plan(agent_ids=(0,))

    def test_scripted_destination_plan_rejected(self):
        plan = hold_and_fire_plan()
        scripted = list(plan) + [Op("agent_set_scripted_destination",
                                    NATIVE_OPS["agent_set_scripted_destination"],
                                    (1, 120, 0))]
        with self.assertRaises(ValueError):
            validate_plan(scripted)

    def test_mixed_team_orders_rejected(self):
        plan = hold_and_fire_plan(team=0)
        plan.append(Op("team_give_order", NATIVE_OPS["team_give_order"],
                       (1, 9, TEAM_ORDERS["mordr_hold"])))
        with self.assertRaises(ValueError):
            validate_plan(plan)


class SpeedPlanTests(unittest.TestCase):
    def test_speed_modifier_plan(self):
        plan = zombie_speed_plan((4, 5, 6), percent=70)
        self.assertEqual(len(plan), 3)
        self.assertEqual(plan[0].name, "agent_set_speed_modifier")
        self.assertEqual(plan[0].number, 2093)
        self.assertEqual([op.args for op in plan],
                         [(4, 70), (5, 70), (6, 70)])

    def test_time_multiplier_plan_uses_fixed_point(self):
        plan = zombie_speed_plan((4,), percent=70, mode="time_multiplier")
        self.assertEqual(plan[0].name, "agent_set_time_speed_multiplier")
        self.assertEqual(plan[0].number, 3335)
        self.assertEqual(plan[0].args, (4, 700))

    def test_speed_bounds(self):
        for bad in (0, 1001, -1):
            with self.assertRaises(ValueError):
                zombie_speed_plan((4,), percent=bad)
        with self.assertRaises(ValueError):
            zombie_speed_plan((4,), mode="mission_time_speed")


class VisitorPlanTests(unittest.TestCase):
    def test_visitor_plan_sequence(self):
        plan = visitor_spawn_plan(entry_no=0, troop_id=894, count=2,
                                  team=1, group=0)
        names = [op.name for op in plan]
        self.assertEqual(names[0], "entry_point_get_position")
        self.assertEqual(names[1], "set_spawn_position")
        self.assertEqual(names[2], "spawn_agent")
        self.assertEqual(plan[2].args, (894,))
        self.assertEqual(names[3], "agent_set_team")
        self.assertEqual(plan[3].args, ("reg0", 1))
        self.assertEqual(names[4], "agent_set_group")
        self.assertEqual(plan[4].args, ("reg0", 0))
        # one spawn block per count
        self.assertEqual(plan.count(plan[2]), 2)

    def test_visitor_plan_bounds(self):
        with self.assertRaises(ValueError):
            visitor_spawn_plan(count=0)
        with self.assertRaises(ValueError):
            visitor_spawn_plan(count=99)
        with self.assertRaises(ValueError):
            visitor_spawn_plan(team=2)
        with self.assertRaises(ValueError):
            visitor_spawn_plan(entry_no=999)
        with self.assertRaises(ValueError):
            visitor_spawn_plan(troop_id=-1)
        with self.assertRaises(ValueError):
            visitor_spawn_plan(group=9)


class CliTests(unittest.TestCase):
    def test_json_plan_output(self):
        buffer = io.StringIO()
        with redirect_stdout(buffer):
            code = main(["--plan", "hold", "--agents", "7,9", "--json"])
        self.assertEqual(code, 0)
        payload = json.loads(buffer.getvalue())
        self.assertEqual(payload[0]["op"], "team_set_order_position")
        self.assertEqual(payload[0]["number"], 1791)
        self.assertIn("agent_ai_set_can_weapon_switch",
                      [entry["op"] for entry in payload])

    def test_describe_includes_opcode_numbers(self):
        lines = describe(hold_and_fire_plan())
        self.assertIn("1791 team_set_order_position(0, 9, 120)", lines)
        self.assertTrue(any(line.startswith("1790 team_give_order") for line in lines))


if __name__ == "__main__":
    unittest.main()
