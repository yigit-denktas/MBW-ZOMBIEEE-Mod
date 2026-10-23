-- ZOMBIEEE Remaster 0.1.0: WSE2 diagnostic-only overlay.
-- No gameplay changes, no new dependencies, no forced server privileges.
local VERSION = "0.1.0"
local MISSION = "mst_multiplayer_iv"
print("[ZOMBIEEE Remaster " .. VERSION .. "] Lua bootstrap loaded")

if game and type(game.getNumTriggers) == "function" then
    local ok, count = pcall(game.getNumTriggers, MISSION)
    if ok then
        print("[ZOMBIEEE Remaster] original invasion trigger count: " .. tostring(count))
    else
        print("[ZOMBIEEE Remaster] trigger probe deferred: " .. tostring(count))
    end
else
    print("[ZOMBIEEE Remaster] game Lua API unavailable; no changes applied")
end
