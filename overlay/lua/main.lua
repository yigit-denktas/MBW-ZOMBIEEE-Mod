-- ZOMBIEEE Remaster 0.1.7: bounded, read-only engine telemetry.
-- Messages go to WSE2's existing game log; no network or file I/O.
-- ZDB1|event|key=value|...; no player names, IPs or chat.
local VERSION = "0.1.5"
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
local function resolve_role()
    if type(game.multiplayer_is_server) == "function" then
        local value = guarded_call(game.multiplayer_is_server, nil)
        if value ~= nil then return value and "server" or "client" end
    end
    return "unknown"
end
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
        local n, a, z = 0, 0, 0
        for agent in game.agentsIt() do
            n = n + 1
            if supports_team then
                local side = guarded_call(function() return game.agent_get_team(0, agent) end, nil)
                if side == 0 then a = a + 1 end
                if side == 1 then z = z + 1 end
            end
            if n >= 4096 then break end
        end
        return n, supports_team and a or -1, supports_team and z or -1
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
        .. "|mode=" .. global_int("zdr_defence_mode")
        .. "|refilled=" .. global_int("zdr_last_reinforced_wave")
end
local previous_wave = nil
local previous_mode = nil
-- Sampling bot coordinates is purely optional. Game operations need WSE2
-- Module System headers to be present; otherwise this produces no samples.
local function sample_defender_positions(tick, mode)
    if type(game.agentsIt) ~= "function"
        or type(game.agent_get_team) ~= "function"
        or type(game.agent_get_group) ~= "function"
        or type(game.agent_is_non_player) ~= "function"
        or type(game.agent_get_position) ~= "function" then
        return
    end
    local seen = 0
    local ok = pcall(function()
        for agent in game.agentsIt() do
            local team = guarded_call(function() return game.agent_get_team(0, agent) end, -1)
            local group = guarded_call(function() return game.agent_get_group(0, agent) end, -1)
            local ai = guarded_call(function() return game.agent_is_non_player(agent) end, false)
            if team == 0 and group >= 5 and group <= 7 and ai then
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
                        seen = seen + 1
                        if seen >= 16 then break end
                    end
                end
            end
        end
    end)
    if not ok then return end
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
                emit("wave_change", "|wave=" .. wave .. "|mode=" .. mode)
                previous_wave = wave
            end
            if mode >= 0 and mode ~= previous_mode then
                emit("tactical_change", "|wave=" .. wave .. "|mode=" .. mode
                     .. "|tick=" .. heartbeat_count)
                previous_mode = mode
            end
            sample_defender_positions(heartbeat_count, mode)
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
