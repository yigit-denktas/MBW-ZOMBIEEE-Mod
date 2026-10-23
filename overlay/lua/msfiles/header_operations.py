# Minimal operation-name bindings for WSE2's Lua Module System integration.
# Original constants independently transcribed from Warband header_operations.
# Source reference: https://github.com/Veehats/WarbandCoop/blob/main/header_operations.py
#
# Only the read-only operations used by the diagnostics probe are exported.
# Does NOT copy game assets, inject native code or expose privileged controls.
# WSE2 will parse these names when loaded from lua/msfiles/header_operations.py.

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
