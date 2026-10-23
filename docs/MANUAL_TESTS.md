# Manual verification (Windows, not automated)

Capture game version, WSE2 release, mod version, archive SHA-256, `rgl_log.txt`, timestamps, screenshots and pass/fail notes. None of these runtime cases is currently certified.

| Check | Evidence needed |
|---|---|
| `7z t ZOMBIEEEBeta04.rar` | Integrity test returns exit 0 |
| Fresh module install | `build.py` exits 0 and doctor validates 5 scenes/mission |
| WSE2 boot | Module loads without crash, invalid token or missing resource |
| Invasion | City `multiplayer_iv` starts, zombies spawn, first wave ends |
| Equipment | Commando, Sniper, Lumberjack, Scout fire and reload as intended |
| Map roster | Granny's House, Bridge, Shipyard, City, Abandoned Town load |
| Supply and props | Ammunition/health boxes, barricades and explosive barrels work |
| Hostile/friendly bots | Verify actual team IDs and bot spawn semantics |
| Lua probe | WSE2 loads bootstrap, log records diagnostic |
| Stability and profiling | At least ten waves, counts/frame times/log checked |

`configs/solo_server.cfg` is experimental, not an independently validated host setup. No public port forwarding or cheats before permission checks.
