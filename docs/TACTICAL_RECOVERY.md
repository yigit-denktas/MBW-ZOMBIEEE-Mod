# Tactical recovery and replay diagnostics — experimental v0.1.6

This change extends the **original 2012 ZOMBIEEE Beta 0.4** with a native, server-only fall-back/regroup state machine. It does not incorporate ZOMBIEEE2, touch the source RAR, replace original invasion triggers, or add CI.

## Two states, with hysteresis

| State | Trigger | Behaviour |
|---|---|---|
| 0 · HOLD | Default | Preserve the map's three guarded positions (divisions 5, 6, 7) |
| 1 · FALLBACK | One or fewer living AI defenders in reserved groups | Order divisions 5–7 to original survivor entry 0 and hold |
| 0 · REGROUP | Three or more living AI defenders recover | Return divisions 5–7 to the current map's three guard posts |

The server checks every 3 seconds, only during the original Invasion mission with an active round and wave >=1. It counts *living, non-player, team-0* agents in the **reserved groups 5–7**. Players and the original zombie AI are not counted or ordered. Switching occurs only when a threshold is crossed **and** the current mode differs, avoiding repeated orders each tick.

The defensive modes use existing native Warband operations and the scene-specific entry markers from v0.1.5. Hold positions remain unchanged unless casualties force a fallback, after which wave reinforcements can restore the squad. The existing replenishment is capped once per new wave; dead allies are not revived mid-wave.

## Compiled-module safety

- Requires the already patched 29-trigger, 1,221-global experimental v0.1.5 configuration.
- Appends global variable **zdr_defence_mode** at the end, preserving all original ordinal global IDs.
- Appends exactly 2 compiled mission triggers: one server-only match initialization, one 3-second state machine.
- Final experimental mission: **31 triggers** and **1,222 global names**. The original 25 trigger bodies remain unchanged.
- Requires **3–8 allied defenders**, wave reinforcements and all-five-map defence markers. This is strictly opt-in.

**Default baseline is still 25 triggers** and does not spawn remaster allies. The full v0.1.6 experimental command is:

    py -3 tools\build.py --archive "C:\Downloads\ZOMBIEEEBeta04.rar" --out "C:\Games\MountBlade Warband\Modules\ZOMBIEEE_Remaster" --experimental-defenders 4 --all-map-defenses --wave-reinforcements --tactical-recovery

No change to normal extraction/build mode. The guarded installer checks the source archive and records the expected final trigger count in its local build receipt.

## Replay improvements

The read-only WSE2 Lua probe now attempts to read actual mission variables through the documented **game.gvar** interface: wave_number, g_round_ended, zdr_last_reinforced_wave, and zdr_defence_mode. Values unavailable to WSE2 are reported as **-1 (unknown)**, never treated as zero.

Every bounded 15-second heartbeat records wave, team counts where available, and tactical mode. The probe also records wave and mode transitions. Optional read-only agent position samples are emitted **only** when WSE2 exposes the relevant operation bindings. Sampling is capped at 16 allied non-player agents per heartbeat; no player positions, player names, chat, network data or game controls are recorded.

**The Lua position API may not be available without WSE2 Module System operation headers.** Its absence does not prevent the game running. The analyzer does not infer immobility without position samples.

The offline analyzer adds:

| Rule | Signal | Caveat |
|---|---|---|
| R019 | Wave number unchanged in >=9 consecutive server heartbeats while zombies remain | Long or difficult waves may be legitimate |
| R020 | Four alternating tactical state changes within about two minutes on one wave | Diagnose possible oscillation |
| R021 | Fallback persists with apparently healthy team-0 counts | Team-0 counts may include human players/other divisions |
| R022 | Sampled defender moved less than one metre across ~45s after a new tactical order | Defender might already be at destination; not proof of broken pathfinding |

No alert is raised for idle guards without a new order. The analyzer retains an observability report so absent telemetry is clearly distinguished from zero movement.

## Actual test boundary

**Offline tests against the user-supplied original 0.4 have passed:** complete original-data patch chain, the 31 compiled trigger streams, original trigger-prefix preservation, state conditions and guard division isolation. Synthetic replay tests cover stalls, mode thrashing, stuck candidates and false-positive protections. The read-only WSE2 global-variable mechanism is supported by the official WSE2 Lua SDK documentation.

**Not yet verified in-game:** successful WSE2 load, order execution, AI movement, actual combat, wave reinforcement timing, client replication, geometry clearance and frame rate. The user will run the **one final integrated Windows test** after implementation is finished, not repeated intermediate tests. Collect logs with tools/Collect-Diagnostics.ps1 and review the SHA-256-verified evidence archive.

References: [Warband operation definitions](https://github.com/Veehats/WarbandCoop/blob/main/header_operations.py), [WSE2 Lua SDK](https://github.com/Ruslan-700/WSE2-Releases/blob/master/Warband/WSE2%20SDK/luaGuide.html), [original creators' thread](https://forums.taleworlds.com/index.php?threads/wb-zombieee-invasion-we-need-your-advice.219327/).
