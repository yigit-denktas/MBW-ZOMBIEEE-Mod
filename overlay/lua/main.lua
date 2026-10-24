-- ZOMBIEEE Remaster telemetry v2: bounded, read-only engine telemetry.
-- Messages go to WSE2's existing game log; no network or file I/O.
-- ZDB1|event|key=value|...; no player names, IPs or chat.
-- v2 adds a bounded per-team troop histogram and explicit, observed-only
-- lifecycle events (player_joined/player_died/player_respawned/player_left/
-- round_started/wave_started). Every field is bounded; unavailable getters
-- stay -1 (unknown), never a fabricated zero.
local VERSION = "0.2.0"
local MISSION = "mst_multiplayer_iv"
local MAX_HIST_TROOPS = 12
local MAX_HIST_LINE = 400
local MAX_TROOP_NAME = 32
local MAX_PLAYER_IDS = 8
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
-- Troop labels are an observation aid from msfiles/ID_troops.py (bounded,
-- documented roster only). Unknown ids stay numeric; no name is invented.
local troop_names = {}
local troop_name_count = 0
local function build_troop_names()
    if type(game.const) ~= "table" or type(game.const.troops) ~= "table" then return 0 end
    local seen = 0
    for name, id in pairs(game.const.troops) do
        if seen >= 64 then break end
        if type(name) == "string" and type(id) == "number" then
            local slot = math.floor(id)
            if slot >= 0 and troop_names[slot] == nil then
                troop_names[slot] = name:gsub("[^%w_%-]", "_"):sub(1, MAX_TROOP_NAME)
                seen = seen + 1
            end
        end
    end
    return seen
end
troop_name_count = build_troop_names()
-- opmeta=1 marks an overlay whose msfiles/header_operations.py declares the
-- WSE2 operation-class lists (lhs_operations / can_fail_operations). Live
-- evidence without this marker predates that fix, so its role/team fields are
-- not a measured composition. troop_hist/lifecycle mark the v2 probe shape.
emit("recorder_capabilities",
    "|sampling_interval_s=15|max_heartbeats=480|max_defenders=16|opmeta=1"
    .. "|troop_hist=1|lifecycle=1|troop_map=" .. troop_name_count
    .. "|max_hist_troops=" .. MAX_HIST_TROOPS
    .. "|agents_it=" .. binding_flag("agentsIt")
    .. "|team_getter=" .. binding_flag("agent_get_team")
    .. "|troop_getter=" .. binding_flag("agent_get_troop_id")
    .. "|alive_getter=" .. binding_flag("agent_is_alive")
    .. "|group_getter=" .. binding_flag("agent_get_group")
    .. "|npc_getter=" .. binding_flag("agent_is_non_player")
    .. "|position_getter=" .. binding_flag("agent_get_position")
    .. "|weapon_getter=" .. binding_flag("agent_get_wielded_item")
    .. "|ammo_getter=" .. binding_flag("agent_get_ammo")
    .. "|kills_getter=" .. binding_flag("agent_get_kill_count"))
local mission_seen = false
local heartbeat_count = 0
local previous_wave = nil
local previous_mode = nil
local previous_commands = {}
local previous_round_start = nil
local previous_alive_players = {}
local player_seen = false
local player_pending = false
local function current_mission()
    local value = guarded_call(game.getCurTemplateId, "unknown")
    return tostring(value):gsub("[^%w_]", "_"):sub(1, 60)
end
-- Read-only agent getters. Module-system operations are optional: a missing
-- binding means unknown, not zero. Destination register 0 is a scratch slot.
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
local function is_alive(agent)
    local value = guarded_call(function()
        return game.agent_is_alive(agent)
    end, nil)
    if value == true or value == 1 then return true end
    if value == false or value == 0 then return false end
    return nil
end
-- Bounded histogram text: at most MAX_HIST_TROOPS distinct ids and
-- MAX_HIST_LINE characters. Truncation is counted, never silently dropped.
local function histogram_text(hist)
    local ids = {}
    for id in pairs(hist) do ids[#ids + 1] = id end
    table.sort(ids, function(a, b)
        if hist[a] ~= hist[b] then return hist[a] > hist[b] end
        return a < b
    end)
    local parts, names, unknown, trunc = {}, {}, 0, 0
    local used = 0
    for i = 1, #ids do
        local id = ids[i]
        local entry = id .. ":" .. hist[id]
        if i > MAX_HIST_TROOPS or used + #entry + 1 > MAX_HIST_LINE then
            trunc = trunc + 1
        else
            parts[#parts + 1] = entry
            used = used + #entry + 1
            local label = troop_names[id]
            if label then names[#names + 1] = id .. ":" .. label
            else unknown = unknown + 1 end
        end
    end
    local text = #parts > 0 and table.concat(parts, ",") or "none"
    local name_text = #names > 0 and table.concat(names, ",") or "none"
    return text, name_text, unknown, trunc
end
-- One bounded pass over the agent iterator collects per-team counts, the
-- bounded troop histogram and the observed team-0 non-player agents. A failed
-- team read makes the counts unknown (-1), never team 0.
local function sample_world()
    if type(game.agentsIt) ~= "function" then return { ok = false } end
    local supports_team = type(game.agent_get_team) == "function"
    local supports_troop = type(game.agent_get_troop_id) == "function"
    local supports_npc = type(game.agent_is_non_player) == "function"
    local ok, world = pcall(function()
        local result = { ok = true, total = 0, team0 = 0, team1 = 0,
                         measured = true, troop_measured = supports_troop,
                         hist0 = {}, hist1 = {}, players = {}, player_count = 0 }
        local n = 0
        for agent in game.agentsIt() do
            n = n + 1
            local side = nil
            if supports_team then
                local ok_team, value, op_error = pcall(function()
                    return game.agent_get_team(0, agent)
                end)
                if ok_team and (op_error == nil or op_error == 0)
                    and (value == 0 or value == 1) then
                    side = value
                else
                    result.measured = false
                end
            end
            if side == 0 then result.team0 = result.team0 + 1 end
            if side == 1 then result.team1 = result.team1 + 1 end
            if supports_troop and side ~= nil then
                local troop = read_agent_number("agent_get_troop_id", agent)
                if troop >= 0 then
                    local hist = side == 0 and result.hist0 or result.hist1
                    hist[troop] = (hist[troop] or 0) + 1
                end
            end
            if side == 0 and supports_npc then
                if not is_npc(agent) then
                    local alive = is_alive(agent)
                    if #result.players < MAX_PLAYER_IDS then
                        result.players[#result.players + 1] =
                            { id = agent, alive = alive == true }
                    end
                    if alive == true then result.player_count = result.player_count + 1 end
                end
            end
            if n >= 4096 then break end
        end
        result.total = n
        if supports_team then
            if not result.measured then
                result.team0, result.team1 = -1, -1
            end
        else
            result.team0, result.team1 = -1, -1
        end
        local t0, n0, u0, x0 = histogram_text(result.hist0)
        local t1, n1, u1, x1 = histogram_text(result.hist1)
        result.text0, result.names0 = t0, n0
        result.text1, result.names1 = t1, n1
        result.troop_unknown = u0 + u1
        result.troop_truncated = x0 + x1
        return result
    end)
    if not ok then return { ok = false } end
    return world
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
local function state_fields(world)
    local fields = "|wave=" .. global_int("wave_number")
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
    if world and world.ok then
        local text0 = world.troop_measured and world.text0 or "-1"
        local text1 = world.troop_measured and world.text1 or "-1"
        local names0 = world.troop_measured and world.names0 or "-1"
        local names1 = world.troop_measured and world.names1 or "-1"
        fields = fields .. "|troops_team0=" .. text0
            .. "|troop_names_team0=" .. names0
            .. "|troops_team1=" .. text1
            .. "|troop_names_team1=" .. names1
            .. "|troop_ids_unknown=" .. world.troop_unknown
            .. "|troops_truncated=" .. world.troop_truncated
            .. "|players_team0=" .. world.player_count
    else
        fields = fields .. "|troops_team0=-1|troop_names_team0=-1"
            .. "|troops_team1=-1|troop_names_team1=-1"
            .. "|troop_ids_unknown=-1|troops_truncated=-1|players_team0=-1"
    end
    return fields
end
local function lifecycle_fields(role, wave, world)
    return "|role=" .. role .. "|wave=" .. wave
        .. "|round_start=" .. global_int("g_round_start_time")
        .. "|team0=" .. ((world and world.ok) and world.team0 or -1)
        .. "|team1=" .. ((world and world.ok) and world.team1 or -1)
        .. "|game_type=" .. global_int("g_multiplayer_game_type")
        .. "|ready_for_spawn=" .. global_int("g_multiplayer_ready_for_spawning_agent")
        .. "|bots_team1=" .. global_int("g_multiplayer_num_bots_team_1")
end
-- Explicit lifecycle events are emitted only from observed transitions:
-- a previously alive team-0 non-player agent now dead/removed (player_died or
-- player_left), a new alive agent after an observed absence (player_respawned),
-- and the first alive player (player_joined). 15 s sampling cannot resolve a
-- 5 s respawn: a death and immediate respawn between samples emits nothing.
local function player_events(role, wave, world)
    if role ~= "server" or not world or not world.ok then return end
    local common = "|role=server|count=" .. heartbeat_count
        .. lifecycle_fields("server", wave, world)
    local present, alive = {}, {}
    for _, player in ipairs(world.players) do
        present[player.id] = player
        if player.alive then alive[player.id] = true end
    end
    for id in pairs(previous_alive_players) do
        local player = present[id]
        if player == nil then
            player_pending = true
            emit("player_left", common .. "|id=" .. id .. "|observed=agent_removed")
        elseif not player.alive then
            player_pending = true
            emit("player_died", common .. "|id=" .. id .. "|observed=dead_agent")
        end
    end
    if player_pending then
        for id in pairs(alive) do
            if not previous_alive_players[id] then
                emit("player_respawned", common .. "|id=" .. id
                    .. "|observed=alive_after_absence")
                player_pending = false
                break
            end
        end
    end
    if not player_seen and next(alive) ~= nil then
        player_seen = true
        emit("player_joined", common .. "|id=" .. next(alive)
            .. "|observed=first_alive_player")
    end
    previous_alive_players = alive
end
-- Sampling bot coordinates is purely optional. Game operations need WSE2
-- Module System headers to be present; otherwise this produces no samples.
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
    local world = sample_world()
    local role = resolve_role()
    local wave = global_int("wave_number")
    local round_start = global_int("g_round_start_time")
    emit("mission_enter", "|role=" .. role ..
         "|template=" .. current_mission() ..
         "|agents=" .. (world.ok and world.total or -1) ..
         "|team0=" .. (world.ok and world.team0 or -1) ..
         "|team1=" .. (world.ok and world.team1 or -1) .. state_fields(world))
    previous_round_start = round_start
    if round_start >= 0 then
        emit("round_started", "|observed=entry_observation"
            .. lifecycle_fields(role, wave, world))
    end
    if wave >= 1 then
        emit("wave_started", "|observed=entry_observation"
            .. lifecycle_fields(role, wave, world))
    end
    player_events(role, wave, world)
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
        local world = sample_world()
        local role = resolve_role()
        local wave, mode = global_int("wave_number"), global_int("zdr_defence_mode")
        emit("heartbeat", "|count=" .. heartbeat_count .. "|role=" .. role
            .. "|agents=" .. (world.ok and world.total or -1)
            .. "|team0=" .. (world.ok and world.team0 or -1)
            .. "|team1=" .. (world.ok and world.team1 or -1)
            .. "|template=" .. current_mission() .. state_fields(world))
        local round_start = global_int("g_round_start_time")
        if role == "server" then
            if wave >= 0 and wave ~= previous_wave then
                emit("wave_change", "|role=server|wave=" .. wave .. "|mode=" .. mode
                     .. "|game_type=" .. global_int("g_multiplayer_game_type")
                     .. "|round_start=" .. round_start
                     .. "|refilled_round_start=" .. global_int("zdr_last_reinforced_round_start")
                     .. "|ready_for_spawn=" .. global_int("g_multiplayer_ready_for_spawning_agent")
                     .. "|bots_team1=" .. global_int("g_multiplayer_num_bots_team_1"))
                if wave >= 1 then
                    emit("wave_started", "|observed=wave_transition"
                        .. lifecycle_fields("server", wave, world))
                end
                previous_wave = wave
            end
            if round_start >= 0 and previous_round_start ~= nil
                and round_start ~= previous_round_start then
                emit("round_started", "|observed=round_identity_change"
                    .. lifecycle_fields("server", wave, world))
            end
            if mode >= 0 and mode ~= previous_mode then
                emit("tactical_change", "|wave=" .. wave .. "|mode=" .. mode
                     .. "|tick=" .. heartbeat_count)
                previous_mode = mode
            end
            player_events("server", wave, world)
            sample_defenders(heartbeat_count, mode, wave)
            sample_command_counters()
        end
        previous_round_start = round_start
    end
    return false
end
local ok_heart, heart_idx = pcall(game.addTrigger, MISSION, 15.0, 0, 0, heartbeat)
if ok_heart then
    emit("probe_registered", "|kind=heartbeat|index=" .. tostring(heart_idx))
else
    emit("probe_failed", "|kind=heartbeat")
end
