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
agent_is_non_player = 1707
agent_get_position = 1710
agent_get_troop_id = 1718
agent_get_kill_count = 1723
agent_get_wielded_item = 1726
agent_get_ammo = 1727
agent_get_group = 1765
agent_get_team = 1770

lhs_operations = [
    agent_get_position,
    agent_get_troop_id,
    agent_get_kill_count,
    agent_get_wielded_item,
    agent_get_ammo,
    agent_get_group,
    agent_get_team,
]

can_fail_operations = [
    multiplayer_is_server,
    agent_is_alive,
    agent_is_non_player,
]
