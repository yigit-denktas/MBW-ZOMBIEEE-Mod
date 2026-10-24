"""Offline Warband AI behavior plan builder and validator (task-35 prototype).

This module is a **read-only, offline** aid: it builds abstract native operation
sequences for the City defender hold, per-agent zombie speed control and visitor
spawning, and validates them against the opcode/enum tables below. It never
starts Warband, never reads or writes game state, and does not prove anything
about engine behavior. Runtime evidence still comes from D's sealed recorder
run (see ``reference/WARBAND_AI_MODDING.md`` and C's receipt summary).

Sources for the numbers/enums (observation date 2026-10-24):

* native ops: public Warband module-system ``header_operations.py`` mirror
  (``cvlc/tgsmod``, cross-checked with ``Veehats/WarbandCoop``);
* enums: public ``header_mission_templates.py`` (``grc_*``, ``mordr_*``,
  ``rordr_*``, ``wordr_*``, ``aordr_*``, ``aisb_*``);
* WSE2-only ops: WSE2 1.1.5.4 SDK ``header_operations_addon.py``.

The plan is intentionally **team-order first**: per-agent
``agent_set_scripted_destination`` is rejected because the community experiment
log documents destination queueing, arrival freeze and formation-breaking
movement (see the reference document).
"""

from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from typing import Iterable, Sequence

# Native operation numbers (community module-system header).
NATIVE_OPS: dict[str, int] = {
    "faction_set_slot": 502,
    "add_visitors_to_current_scene": 1265,
    "agent_get_attack_action": 1763,
    "agent_set_group": 1766,
    "agent_set_team": 1771,
    "agent_set_division": 1783,
    "agent_unequip_item": 1774,
    "agent_set_ammo": 1776,
    "agent_set_speed_limit": 1736,
    "agent_set_speed_modifier": 2093,
    "agent_set_wielded_item": 1747,
    "agent_force_rethink": 1732,
    "agent_clear_scripted_mode": 1735,
    "agent_set_scripted_destination": 1730,
    "agent_ai_set_aggressiveness": 1753,
    "entry_point_get_position": 1780,
    "team_get_hold_fire_order": 1784,
    "team_get_movement_order": 1785,
    "team_get_riding_order": 1786,
    "team_get_weapon_usage_order": 1787,
    "team_give_order": 1790,
    "team_set_order_position": 1791,
    "team_get_order_position": 1794,
    "set_spawn_position": 1970,
    "spawn_agent": 1972,
    "agent_get_wielded_item": 1726,
    "agent_get_ammo": 1727,
    "agent_refill_ammo": 1728,
    "agent_set_attack_action": 1745,
    "agent_set_defend_action": 1746,
    "agent_set_look_target_agent": 1713,
}

# WSE2 1.1.5.4 addon operations.
WSE2_OPS: dict[str, int] = {
    "agent_set_scripted_destination_no_attack": 1748,
    "agent_ai_set_simple_behavior": 3314,
    "agent_set_item_slot_ammo": 3305,
    "agent_get_wielded_item_slot_no": 3308,
    "agent_set_time_speed_multiplier": 3335,
    "agent_get_time_speed_multiplier": 3336,
    "agent_set_action_speed_modifier": 3340,
    "agent_ai_set_can_weapon_switch": 3343,
    "agent_ai_set_can_fight": 3344,
    "agent_ai_set_can_aim": 3352,
    "shift_entry_point": 3623,
}

# header_mission_templates.py values.
SUBCLASSES: dict[str, int] = {
    "grc_infantry": 0,
    "grc_archers": 1,
    "grc_cavalry": 2,
    "grc_heroes": 3,
    "grc_everyone": 9,
}
TEAM_ORDERS: dict[str, int] = {
    "mordr_hold": 0,
    "mordr_follow": 1,
    "mordr_charge": 2,
    "mordr_advance": 5,
    "mordr_fall_back": 6,
    "mordr_stand_closer": 7,
    "mordr_spread_out": 8,
    "mordr_stand_ground": 11,
    "mordr_hold_fire": 12,
    "mordr_fire_at_will": 13,
    "mordr_use_ranged_weapons": 16,
    "mordr_form_2_row": 23,
}
SIMPLE_BEHAVIORS: dict[str, int] = {
    "aisb_hold": 0,
    "aisb_go_to_pos": 1,
    "aisb_melee": 4,
    "aisb_ranged": 5,
    "aisb_charge_horseback": 7,
    "aisb_patrol": 11,
    "aisb_no_enemies": 12,
}

MAX_PLAN_OPS = 128
MAX_AGENT_IDS = 16
MAX_VISITOR_COUNT = 16
MAX_TROOP_ID = 100000
MAX_POSITION_REG = 255


@dataclass(frozen=True)
class Op:
    """One abstract native/WSE2 operation (number + arguments, no registers)."""

    name: str
    number: int
    args: tuple[object, ...]
    wse2: bool = False


def _op(name: str, *args: object) -> Op:
    if name in NATIVE_OPS:
        return Op(name, NATIVE_OPS[name], args, wse2=False)
    if name in WSE2_OPS:
        return Op(name, WSE2_OPS[name], args, wse2=True)
    raise ValueError(f"unknown operation: {name}")


def _check_team(team: int) -> None:
    if team not in (0, 1):
        raise ValueError(f"team must be 0 or 1, got {team!r}")


def _check_subclass(sub_class: int) -> None:
    if sub_class not in SUBCLASSES.values():
        raise ValueError(f"unknown sub_class {sub_class!r}")


def _check_position_reg(position_reg: int) -> None:
    if not isinstance(position_reg, int) or not 0 <= position_reg <= MAX_POSITION_REG:
        raise ValueError(f"position register out of range: {position_reg!r}")


def _check_agent_ids(agent_ids: Iterable[int]) -> tuple[int, ...]:
    ids = tuple(agent_ids)
    if len(ids) > MAX_AGENT_IDS:
        raise ValueError(f"too many agent ids ({len(ids)} > {MAX_AGENT_IDS})")
    if len(set(ids)) != len(ids):
        raise ValueError("duplicate agent ids")
    for agent in ids:
        if not isinstance(agent, int) or not 1 <= agent <= 65535:
            raise ValueError(f"agent id out of range: {agent!r}")
    return ids


def hold_and_fire_plan(
    team: int = 0,
    sub_class: int = SUBCLASSES["grc_everyone"],
    position_reg: int = 120,
    *,
    hold_fire: bool = True,
    fire_order: str = "hold_fire",
    ranged_weapons: bool = True,
    agent_ids: Sequence[int] = (),
    guarantee_seconds: int = 6,
    wse2: bool = True,
) -> list[Op]:
    """Team-order hold plan; optional per-agent WSE2 hold/weapon-switch safeties.

    Ordering matters: post the position first, then issue the hold order, then
    fire/weapon orders (the native formation scripts do the same). The plan is
    meant to be re-issued on the ~5 s re-plan cadence, not per tick.
    """
    _check_team(team)
    _check_subclass(sub_class)
    _check_position_reg(position_reg)
    fire_orders = {"hold_fire": TEAM_ORDERS["mordr_hold_fire"],
                   "fire_at_will": TEAM_ORDERS["mordr_fire_at_will"]}
    if fire_order not in fire_orders:
        raise ValueError("fire_order must be 'hold_fire' or 'fire_at_will'")
    ids = _check_agent_ids(agent_ids)
    if guarantee_seconds < 0:
        raise ValueError("guarantee_seconds must be >= 0")

    ops: list[Op] = [
        _op("team_set_order_position", team, sub_class, position_reg),
        _op("team_give_order", team, sub_class, TEAM_ORDERS["mordr_hold"]),
    ]
    if hold_fire:
        ops.append(_op("team_give_order", team, sub_class, fire_orders[fire_order]))
    if ranged_weapons:
        ops.append(_op("team_give_order", team, sub_class,
                       TEAM_ORDERS["mordr_use_ranged_weapons"]))
    if wse2:
        for agent in ids:
            # Preserve the ranged weapon: stop the native melee auto-switch.
            ops.append(_op("agent_ai_set_can_weapon_switch", agent, 0))
            ops.append(_op("agent_ai_set_simple_behavior", agent,
                           SIMPLE_BEHAVIORS["aisb_hold"], guarantee_seconds))
    validate_plan(ops)
    return ops


def zombie_speed_plan(
    agent_ids: Sequence[int],
    *,
    percent: int = 70,
    mode: str = "speed_modifier",
) -> list[Op]:
    """No-gear zombie slowdown plan.

    ``speed_modifier`` uses native ``agent_set_speed_modifier`` (2093, percent,
    100 default, 0..1000), movement only. ``time_multiplier`` uses WSE2
    ``agent_set_time_speed_multiplier`` (3335, fixed point where 1000 = 1.0);
    70% is emitted as 700 and slows the whole agent (attacks included).
    """
    ids = _check_agent_ids(agent_ids)
    if not isinstance(percent, int) or not 1 <= percent <= 1000:
        raise ValueError("percent must be an integer in 1..1000 (0 freezes the agent)")
    if mode == "speed_modifier":
        ops = [_op("agent_set_speed_modifier", agent, percent) for agent in ids]
    elif mode == "time_multiplier":
        ops = [_op("agent_set_time_speed_multiplier", agent, percent * 10)
               for agent in ids]
    else:
        raise ValueError("mode must be 'speed_modifier' or 'time_multiplier'")
    validate_plan(ops)
    return ops


def visitor_spawn_plan(
    entry_no: int = 0,
    troop_id: int = 894,
    count: int = 1,
    *,
    team: int = 1,
    group: int | None = 0,
    position_reg: int = 120,
) -> list[Op]:
    """Native visitor/spawn plan: entry point -> spawn position -> spawn + assign.

    ``spawn_agent`` stores the new agent id in ``reg0``; the plan uses the
    symbolic ``"reg0"`` for the follow-up team/group assignment. Repeat the
    spawn block ``count`` times in the generated module code.
    """
    _check_position_reg(position_reg)
    _check_team(team)
    if not isinstance(entry_no, int) or not 0 <= entry_no <= 255:
        raise ValueError(f"entry_no out of range: {entry_no!r}")
    if not isinstance(troop_id, int) or not 0 <= troop_id <= MAX_TROOP_ID:
        raise ValueError(f"troop_id out of range: {troop_id!r}")
    if not isinstance(count, int) or not 1 <= count <= MAX_VISITOR_COUNT:
        raise ValueError(f"count out of range (1..{MAX_VISITOR_COUNT})")
    if group is not None and (not isinstance(group, int) or not 0 <= group <= 8):
        raise ValueError(f"group out of range: {group!r}")
    ops: list[Op] = [
        _op("entry_point_get_position", position_reg, entry_no),
        _op("set_spawn_position", position_reg),
    ]
    for _ in range(count):
        ops.append(_op("spawn_agent", troop_id))
        ops.append(_op("agent_set_team", "reg0", team))
        if group is not None:
            ops.append(_op("agent_set_group", "reg0", group))
    validate_plan(ops)
    return ops


_SCRIPTED_OPS = {"agent_set_scripted_destination",
                 "agent_set_scripted_destination_no_attack"}


def validate_plan(plan: Sequence[Op]) -> None:
    """Fail closed on unknown/incorrect plans.

    Rejects scripted-destination plans (community-documented queue/freeze and
    formation-breaking behavior), out-of-range team orders, percent bounds,
    duplicate/oversized agent lists and oversized plans.
    """
    if not plan:
        raise ValueError("empty plan")
    if len(plan) > MAX_PLAN_OPS:
        raise ValueError(f"plan too long ({len(plan)} > {MAX_PLAN_OPS})")
    team_orders: list[tuple[int, int]] = []
    hold_fire_count = 0
    position_posts: list[int] = []
    for op in plan:
        if not isinstance(op, Op):
            raise ValueError(f"plan entries must be Op, got {type(op).__name__}")
        if op.name in _SCRIPTED_OPS:
            raise ValueError(
                "scripted-destination plans are rejected: use team orders "
                "(team_set_order_position + mordr_hold) and, if needed, "
                "agent_clear_scripted_mode + agent_force_rethink")
        expected = NATIVE_OPS.get(op.name) or WSE2_OPS.get(op.name)
        if expected is None:
            raise ValueError(f"unknown operation: {op.name}")
        if expected != op.number:
            raise ValueError(f"wrong opcode for {op.name}: {op.number} != {expected}")
        if op.name == "team_give_order":
            team, sub_class, order = op.args
            _check_team(team)
            _check_subclass(sub_class)
            if order not in TEAM_ORDERS.values():
                raise ValueError(f"unknown team order id: {order!r}")
            team_orders.append((team, sub_class))
            if order == TEAM_ORDERS["mordr_hold_fire"]:
                hold_fire_count += 1
        elif op.name == "team_set_order_position":
            team, sub_class, position_reg = op.args
            _check_team(team)
            _check_subclass(sub_class)
            _check_position_reg(position_reg)
            position_posts.append(position_reg)
        elif op.name == "agent_set_speed_modifier":
            agent, percent = op.args
            _check_agent_ids([agent])
            if not isinstance(percent, int) or not 1 <= percent <= 1000:
                raise ValueError(f"speed percent out of range: {percent!r}")
        elif op.name == "agent_set_time_speed_multiplier":
            agent, fixed = op.args
            _check_agent_ids([agent])
            if not isinstance(fixed, int) or not 1 <= fixed <= 10000:
                raise ValueError(f"time multiplier fixed point out of range: {fixed!r}")
        elif op.name == "agent_ai_set_simple_behavior":
            agent, behavior, guarantee = op.args
            _check_agent_ids([agent])
            if behavior not in SIMPLE_BEHAVIORS.values():
                raise ValueError(f"unknown simple behavior: {behavior!r}")
            if not isinstance(guarantee, int) or not 0 <= guarantee <= 600:
                raise ValueError("simple-behavior guarantee out of range (0..600s)")
        elif op.name == "agent_ai_set_can_weapon_switch":
            agent, value = op.args
            _check_agent_ids([agent])
            if value not in (0, 1):
                raise ValueError("can_weapon_switch value must be 0 or 1")
        elif op.name == "spawn_agent":
            (troop,) = op.args
            if not isinstance(troop, int) or not 0 <= troop <= MAX_TROOP_ID:
                raise ValueError(f"troop id out of range: {troop!r}")
    if hold_fire_count > 1:
        raise ValueError("hold-fire order must be issued at most once per plan")
    if team_orders and len({entry for entry in team_orders}) > 1:
        raise ValueError("mixed team/sub_class team orders in one plan")
    if position_posts and not team_orders:
        raise ValueError("team_set_order_position requires a following team order")


def describe(plan: Sequence[Op]) -> list[str]:
    """Human-readable plan lines, e.g. ``1790 team_give_order(0, 9, 0)``."""
    lines = []
    for op in plan:
        args = ", ".join(str(arg) for arg in op.args)
        suffix = " (WSE2)" if op.wse2 else ""
        lines.append(f"{op.number} {op.name}({args}){suffix}")
    return lines


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--plan", choices=("hold", "speed", "visitor"),
                        default="hold")
    parser.add_argument("--agents", default="",
                        help="comma-separated agent ids for hold/speed plans")
    parser.add_argument("--percent", type=int, default=70)
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--validate", action="store_true")
    args = parser.parse_args(argv)

    agents = [int(part) for part in args.agents.split(",") if part.strip()]
    if args.plan == "hold":
        plan = hold_and_fire_plan(agent_ids=agents)
    elif args.plan == "speed":
        plan = zombie_speed_plan(agents, percent=args.percent)
    else:
        plan = visitor_spawn_plan(count=1)
    if args.validate:
        validate_plan(plan)
    if args.json:
        print(json.dumps([{"op": op.name, "number": op.number,
                           "args": list(op.args), "wse2": op.wse2}
                          for op in plan], indent=2))
    else:
        for line in describe(plan):
            print(line)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
