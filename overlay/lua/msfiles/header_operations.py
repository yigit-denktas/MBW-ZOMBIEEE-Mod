# Minimal operation-name bindings for WSE2's Lua Module System integration.
# Original constants independently transcribed from Warband header_operations.
# Source reference: https://github.com/Veehats/WarbandCoop/blob/main/header_operations.py
#
# Only the read-only operations used by the diagnostics probe are exported.
# Does NOT copy game assets, inject native code or expose privileged controls.
# WSE2 will parse these names when loaded from lua/msfiles/header_operations.py.
#
# The trailing operation-class lists are REQUIRED, not documentation. WSE2's
# Lua bridge decides the calling convention from these lists alone:
#   * an lhs operation takes a destination register as its first Lua argument;
#   * a can_fail operation returns its boolean result instead of an error code.
# An operation in neither list is called with every argument treated as a plain
# value, so a destination register number reaches the script VM as a constant
# and the VM aborts that script with "Illegal lvalue in statement".
#
# Observed live 2026-10-24 in mst_multiplayer_iv Trigger [32] (the ZDB1 15 s
# heartbeat), because this file used to declare constants without the lists:
#   SCRIPT ERROR: Illegal lvalue in statement
#   - Lua (line 0, opcode 1770)                      <- agent_get_team
#   - ... Trigger [32] Conditions (Lua) (opcode 5113) <- lua_triggerCallback
# The same omission made multiplayer_is_server (opcode 417) return an error
# code instead of a boolean, so the dedicated host reported role=client.
# Keep every game.<operation>() call in lua/main.lua covered below; the offline
# regression test tests/test_flight_lua_msfiles.py enforces it.

multiplayer_is_server = 417
agent_is_alive = 1702
# Classifies an agent by type: false means the agent is not human (a horse).
# 1704 is corroborated by the original compiled mission templates, where it is
# used 67 times as a one-argument boolean condition and always followed by
# agent_get_troop_id / str_store_troop_name - i.e. a human-only naming path.
agent_is_human = 1704
agent_is_non_player = 1707
agent_get_position = 1710
agent_get_troop_id = 1718
agent_get_kill_count = 1723
agent_get_wielded_item = 1726
agent_get_ammo = 1727
agent_get_group = 1765
agent_get_team = 1770
agent_get_speed_modifier = 2067
agent_get_time_speed_multiplier = 3336
agent_get_action_speed_modifier = 3341
team_get_hold_fire_order = 1784
team_get_movement_order = 1785
team_get_riding_order = 1786
team_get_weapon_usage_order = 1787
faction_get_slot = 522
store_current_scene = 2211

lhs_operations = [
    agent_get_position,
    agent_get_troop_id,
    agent_get_kill_count,
    agent_get_wielded_item,
    agent_get_ammo,
    agent_get_group,
    agent_get_team,
    agent_get_speed_modifier,
    agent_get_time_speed_multiplier,
    agent_get_action_speed_modifier,
    team_get_hold_fire_order,
    team_get_movement_order,
    team_get_riding_order,
    team_get_weapon_usage_order,
    faction_get_slot,
    store_current_scene,
]

can_fail_operations = [
    multiplayer_is_server,
    agent_is_alive,
    agent_is_human,
    agent_is_non_player,
]
