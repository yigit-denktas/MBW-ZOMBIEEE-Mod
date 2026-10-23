-- ZOMBIEEE Remaster 0.1.3: bounded, read-only engine telemetry.
-- Messages go to WSE2's existing game log; no network or file I/O.
-- ZDB1|event|key=value|...; no player names, IPs or chat.
local VERSION = "0.1.3"
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
local function count_agents()
    if type(game.agentsIt) ~= "function" then return -1 end
    return guarded_call(function()
        local count = 0
        for _ in game.agentsIt() do
            count = count + 1
            if count >= 4096 then break end
        end
        return count
    end, -1)
end
local function first_entry()
    if mission_seen then return false end
    mission_seen = true
    emit("mission_enter", "|role=" .. resolve_role() ..
         "|template=" .. current_mission() .. "|agents=" .. count_agents())
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
        emit("heartbeat", "|count=" .. heartbeat_count .. "|role=" .. resolve_role()
            .. "|agents=" .. count_agents() .. "|template=" .. current_mission())
    end
    return false
end
local ok_heart, heart_idx = pcall(game.addTrigger, MISSION, 15.0, 0, 0, heartbeat)
if ok_heart then
    emit("probe_registered", "|kind=heartbeat|index=" .. tostring(heart_idx))
else
    emit("probe_failed", "|kind=heartbeat")
end
