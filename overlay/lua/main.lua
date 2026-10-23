-- ZOMBIEEE Remaster 0.1.1: non-invasive WSE2 runtime diagnostics.
-- Observe WSE2 startup and invasion mission entry. Do not modify original triggers.
local VERSION = "0.1.1"
local MISSION = "mst_multiplayer_iv"
local prefix = "[ZOMBIEEE Remaster " .. VERSION .. "] "

print(prefix .. "Lua bootstrap loaded")

if not game then
    print(prefix .. "game API unavailable; diagnostics disabled")
    return
end

if type(game.getNumTriggers) == "function" then
    local ok, value = pcall(game.getNumTriggers, MISSION)
    if ok then
        print(prefix .. "compiled invasion trigger count: " .. tostring(value))
    else
        print(prefix .. "trigger inspection failed: " .. tostring(value))
    end
end

-- WSE2 SDK: addTrigger(strTemplateId, checkTime, delay, rearm, conditionsCallback).
-- The callback logs once on entry and intentionally has no gameplay operations.
if type(game.addTrigger) == "function" then
    local reported = false
    local function mission_probe()
        if reported then
            return false
        end
        reported = true
        local mission_name = "unknown"
        if type(game.getCurTemplateId) == "function" then
            local ok, value = pcall(game.getCurTemplateId)
            if ok then
                mission_name = tostring(value)
            end
        end
        print(prefix .. "invasion mission entered; template=" .. mission_name)
        return false
    end
    local ok, index = pcall(game.addTrigger, MISSION, 1.0, 0, 0, mission_probe)
    if ok then
        print(prefix .. "mission entry probe registered: " .. tostring(index))
    else
        print(prefix .. "mission entry probe failed: " .. tostring(index))
    end
else
    print(prefix .. "addTrigger unavailable; mission entry probe skipped")
end
