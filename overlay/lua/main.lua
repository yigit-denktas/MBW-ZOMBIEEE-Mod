-- ZOMBIEEE Remaster 0.1.8: bounded, read-only engine telemetry.
-- Messages go to WSE2's existing game log; no network or file I/O.
-- ZDB1|event|key=value|...; no player names, IPs or chat.
local VERSION = "0.1.8"
local MISSION = "mst_multiplayer_iv"
local function emit(event, details)
    print("ZDB1|" .. event .. "|version=" .. VERSION .. (details or ""))
end
local function guarded_call(fn, default)
    if type(fn) ~= "function" then return default end
    local ok, value = pcall(fn)
    if not ok then return default end
    return value
end
local trigger_count = guarded_call(function() return game.getNumTriggers(MISSION) end, -1)
emit("boot", "|triggers=" .. tostring(trigger_count))

if type(game) ~= "table" or type(game.addTrigger) ~= "function" then
    emit("probe_unavailable", "|reason=no_game_trigger_api")
    return
end
-- multiplayer_is_server (opcode 417) is a can_fail condition: WSE2 only returns
-- its boolean result when the operation is listed in
-- msfiles/header_operations.py can_fail_operations. A missing binding or an
-- unrecognized result stays "unknown" instead of silently reading as client.
-- Live evidence 2026-10-24: the dedicated host logged role=client because the
-- can_fail metadata was absent; server-only sampling never ran.
local function resolve_role()
    if type(game.multiplayer_is_server) ~= "function" then return "unknown" end
    local ok, value = pcall(game.multiplayer_is_server)
    if not ok then return "unknown" end
    if value == true or value == 1 then return "server" end
    if value == false or value == 0 then return "client" end
    return "unknown"
end
-- One-time declaration reports binding presence, NOT successful engine operation.
-- No names/coordinates or other private player data in these fields.
local function binding_flag(name)
    return type(game[name]) == "function" and 1 or 0
end
-- opmeta=1 marks an overlay whose msfiles/header_operations.py declares the
-- WSE2 operation-class lists (lhs_operations / can_fail_operations). Live
-- evidence without this marker predates that fix, so its role/team fields are
-- not a measured composition.
emit("recorder_capabilities",
    "|sampling_interval_s=15|max_heartbeats=480|max_defenders=16|opmeta=1"
    .. "|agents_it=" .. binding_flag("agentsIt")
    .. "|team_getter=" .. binding_flag("agent_get_team")
    .. "|group_getter=" .. binding_flag("agent_get_group")
    .. "|npc_getter=" .. binding_flag("agent_is_non_player")
    .. "|position_getter=" .. binding_flag("agent_get_position")
    .. "|weapon_getter=" .. binding_flag("agent_get_wielded_item")
    .. "|ammo_getter=" .. binding_flag("agent_get_ammo")
    .. "|kills_getter=" .. binding_flag("agent_get_kill_count"))
local mission_seen = false
local heartbeat_count = 0
local function current_mission()
    local value = guarded_call(game.getCurTemplateId, "unknown")
    return tostring(value):gsub("[^%w_]", "_"):sub(1, 60)
end
local function sample_agents()
    if type(game.agentsIt) ~= "function" then return -1, -1, -1 end
    local supports_team = type(game.agent_get_team) == "function"
    local ok, total, team0, team1 = pcall(function()
        local n, a, z, measured = 0, 0, 0, true
        for agent in game.agentsIt() do
            n = n + 1
            if supports_team then
                -- agent_get_team is an lhs operation (destination register
                -- first). Only a successful store is a measurement: a failed
                -- operation must stay unknown, never be counted as team 0.
                local ok_team, side, op_error = pcall(function()
                    return game.agent_get_team(0, agent)
                end)
                if ok_team and (op_error == nil or op_error == 0)
                    and (side == 0 or side == 1) then
                    if side == 0 then a = a + 1 else z = z + 1 end
                else
                    measured = false
                end
            end
            if n >= 4096 then break end
        end
        if not supports_team then return n, -1, -1 end
        return n, measured and a or -1, measured and z or -1
    end)
    if not ok then return -1, -1, -1 end
    return total, team0, team1
end
-- WSE2 SDK supports game.gvar.NAME and reads variables.txt at startup.
-- Sentinel -1 = not available (e.g., baseline module without tactical overlay).
local function global_int(name)
    return guarded_call(function()
        local n = tonumber(game.gvar[name])
        if n ~= nil then return math.floor(n) end
        return -1
    end, -1)
end
local function state_fields()
    return "|wave=" .. global_int("wave_number")
        .. "|round=" .. global_int("g_round_ended")
        -- mode is the tactical zdr_defence_mode, NOT the multiplayer game type.
        .. "|mode=" .. global_int("zdr_defence_mode")
        -- g_multiplayer_game_type is the original invasion type (expected 7).
        .. "|game_type=" .. global_int("g_multiplayer_game_type")
        .. "|refilled=" .. global_int("zdr_last_reinforced_wave")
        -- These are engine global reads, NOT inferred from source receipt.
        -- -1 means getter unavailable / pre-round-aware build.
        .. "|round_start=" .. global_int("g_round_start_time")
        .. "|refilled_round_start=" .. global_int("zdr_last_reinforced_round_start")
        -- Spawn gating and team-1 bot population are separate globals; absent
        -- getters must stay -1 (unknown) rather than be inferred from source.
        .. "|ready_for_spawn=" .. global_int("g_multiplayer_ready_for_spawning_agent")
        .. "|bots_team1=" .. global_int("g_multiplayer_num_bots_team_1")
        .. "|cmdheal=" .. global_int("zdr_cmd_heal")
        .. "|cmdammo=" .. global_int("zdr_cmd_ammo")
        .. "|cmdsquad=" .. global_int("zdr_cmd_squad")
end
local previous_wave = nil
local previous_mode = nil
local previous_commands = {}
-- Sampling bot coordinates is purely optional. Game operations need WSE2
-- Module System headers to be present; otherwise this produces no samples.
-- Agent operations are optional; missing Module System bindings mean unknown,
-- not zero kills, ammo or weapons. No player positions are ever collected.
local function read_agent_number(name, agent, extra)
    local fn = game[name]
    if type(fn) ~= "function" then return -1 end
    local ok = pcall(function()
        if extra ~= nil then fn(0, agent, extra) else fn(0, agent) end
    end)
    if not ok then return -1 end
    return tonumber(game.reg0) or -1
end
local function is_npc(agent)
    local value = guarded_call(function()
        return game.agent_is_non_player(agent)
    end, false)
    return value == true or value == 1
end
local function sample_defenders(tick, mode, wave)
    if type(game.agentsIt) ~= "function"
        or type(game.agent_get_team) ~= "function"
        or type(game.agent_get_group) ~= "function"
        or type(game.agent_is_non_player) ~= "function" then return end
    local seen = 0
    local ok = pcall(function()
        for agent in game.agentsIt() do
            local team = read_agent_number("agent_get_team", agent)
            local group = read_agent_number("agent_get_group", agent)
            if team == 0 and group >= 5 and group <= 7 and is_npc(agent) then
                local kills = read_agent_number("agent_get_kill_count", agent)
                local ammo = read_agent_number("agent_get_ammo", agent, 0)
                local weapon = read_agent_number("agent_get_wielded_item", agent, 0)
                if kills >= 0 or ammo >= 0 or weapon >= 0 then
                    emit("combat_sample", "|tick=" .. tick .. "|id=" .. agent
                        .. "|group=" .. group .. "|wave=" .. wave .. "|mode=" .. mode
                        .. "|kills=" .. kills .. "|ammo=" .. ammo .. "|weapon=" .. weapon)
                end
                if type(game.agent_get_position) == "function" then
                    local position = guarded_call(function()
                        game.agent_get_position(90, agent)
                        return game.preg[90]
                    end, nil)
                    if position and position.o then
                        local x, y = tonumber(position.o.x), tonumber(position.o.y)
                        if x and y then
                            emit("agent_sample", "|tick=" .. tick .. "|id=" .. agent
                                .. "|group=" .. group .. "|mode=" .. mode
                                .. "|x=" .. math.floor(x * 10 + 0.5) / 10
                                .. "|y=" .. math.floor(y * 10 + 0.5) / 10)
                        end
                    end
                end
                seen = seen + 1
                if seen >= 16 then break end
            end
        end
    end)
    if not ok then emit("probe_failed", "|kind=combat") end
end
local function sample_command_counters()
    local counters = {"zdr_cmd_heal", "zdr_cmd_ammo", "zdr_cmd_squad"}
    for _, name in ipairs(counters) do
        local value = global_int(name)
        if value >= 0 then
            local prior = previous_commands[name]
            if prior ~= nil and value > prior then
                emit("command_exec", "|cmd=" .. name .. "|count=" .. value
                    .. "|delta=" .. (value - prior))
            end
            previous_commands[name] = value
        end
    end
end
local function first_entry()
    if mission_seen then return false end
    mission_seen = true
    local all, allied, hostile = sample_agents()
    emit("mission_enter", "|role=" .. resolve_role() ..
         "|template=" .. current_mission() .. "|agents=" .. all ..
         "|team0=" .. allied .. "|team1=" .. hostile .. state_fields())
    return false
end
local ok_entry, idx = pcall(game.addTrigger, MISSION, 1.0, 0, 0, first_entry)
if ok_entry then
    emit("probe_registered", "|kind=entry|index=" .. tostring(idx))
else
    emit("probe_failed", "|kind=entry")
end
local function heartbeat()
    heartbeat_count = heartbeat_count + 1
    -- At most 480 periodic records (~2 h at 15 s each).
    if heartbeat_count <= 480 then
        local all, allied, hostile = sample_agents()
        local role = resolve_role()
        local wave, mode = global_int("wave_number"), global_int("zdr_defence_mode")
        emit("heartbeat", "|count=" .. heartbeat_count .. "|role=" .. role
            .. "|agents=" .. all .. "|team0=" .. allied .. "|team1=" .. hostile
            .. "|template=" .. current_mission() .. state_fields())
        if role == "server" then
            if wave >= 0 and wave ~= previous_wave then
                emit("wave_change", "|role=server|wave=" .. wave .. "|mode=" .. mode
                     .. "|game_type=" .. global_int("g_multiplayer_game_type")
                     .. "|round_start=" .. global_int("g_round_start_time")
                     .. "|refilled_round_start=" .. global_int("zdr_last_reinforced_round_start")
                     .. "|ready_for_spawn=" .. global_int("g_multiplayer_ready_for_spawning_agent")
                     .. "|bots_team1=" .. global_int("g_multiplayer_num_bots_team_1"))
                previous_wave = wave
            end
            if mode >= 0 and mode ~= previous_mode then
                emit("tactical_change", "|wave=" .. wave .. "|mode=" .. mode
                     .. "|tick=" .. heartbeat_count)
                previous_mode = mode
            end
            sample_defenders(heartbeat_count, mode, wave)
            sample_command_counters()
        end
    end
    return false
end
local ok_heart, heart_idx = pcall(game.addTrigger, MISSION, 15.0, 0, 0, heartbeat)
if ok_heart then
    emit("probe_registered", "|kind=heartbeat|index=" .. tostring(heart_idx))
else
    emit("probe_failed", "|kind=heartbeat")
end
