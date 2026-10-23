# Manual engine acceptance tests (Windows; no CI)

Before diagnosing engine failure, run the **archival integrity** and **static preflight** checks separately. The extracted source archive is not distributed in this public repository.

```powershell
7z t "C:\Downloads\ZOMBIEEEBeta04.rar"
py -3 -m unittest discover -s tests -v
py -3 tools\build.py --archive "C:\Downloads\ZOMBIEEEBeta04.rar" --out "C:\Games\MountBlade Warband\Modules\ZOMBIEEE_Remaster"
py -3 tools\doctor.py --module "C:\Games\MountBlade Warband\Modules\ZOMBIEEE_Remaster"
py -3 tools\preflight.py --module "C:\Games\MountBlade Warband\Modules\ZOMBIEEE_Remaster" --json
```

Expect compiled invasion `mst_multiplayer_iv`: **64 entry points / 25 original triggers**, and **30/30 mod BRF resources**. A passing preflight does *not* prove sound/texture CRC integrity or engine runtime compatibility.

Next, use the *WSE2 1.1.5.4* Windows launcher with module `ZOMBIEEE_Remaster`. Preserve a copy of `rgl_log.txt`, WSE2 version and screenshot. Look for lines:

```text
[ZOMBIEEE Remaster 0.1.1] Lua bootstrap loaded
[ZOMBIEEE Remaster 0.1.1] compiled invasion trigger count: 25
[ZOMBIEEE Remaster 0.1.1] mission entry probe registered: ...
[ZOMBIEEE Remaster 0.1.1] invasion mission entered; template=...
```

The additional runtime trigger may make the WSE2-reported count **26** on some log timings. The count printed by the bootstrap runs before registering the probe.

| Test | Pass criteria |
|---|---|
| RAR archive | 7-Zip reports integrity OK without skipped or damaged entries |
| Fresh module | Build completes, doctor passes, preflight passes |
| Runtime startup | WSE2 launches with no fatal resource/parser error |
| Invasion | City `tbfc_invasion_4`, `multiplayer_iv`, complete one zombie wave |
| Survivor equipment | All four classes load and fire/reload |
| Interactions | Ammo, health boxes, explosive props work |
| Original bots | Record player/zombie bot side and actual behaviour |
| All five maps | Granny's House, Bridge, Shipyard, City, Abandoned Town |
| Stability | Ten successive waves and latency/frame-time readings |

No runtime rows have been independently verified. No public hosting or cheat controls until server authority is checked.

## Experimental defender verification

Rebuild the module with `--experimental-defenders 4` (or use `tools/Smoke-Test.ps1`). Static preflight should show 26 triggers, not the original 25. On a **private server**, confirm four new team-0 survivor agents, native zombie waves, and at least one completed wave. Collect `rgl_log.txt`, screenshot and WSE2 version. If there is a fault, use the default unmodified mode and report Issue #2. Do not claim gameplay passed without evidence.

## One-time evidence collection at final release candidate

No intermediate user playtest reports are required. Continue development and offline regression tests. At the final integrated build, play a private solo game then run:

    .\tools\Collect-Diagnostics.ps1 -WarbandRoot 'C:\Program Files (x86)\Steam\steamapps\common\MountBlade Warband' -Session final-solo

This creates a locally stored redacted evidence ZIP and analyzer report under evidence/. Review the bundle before sharing. See [DIAGNOSTICS.md](DIAGNOSTICS.md). Native engine gameplay cannot be certified from unit tests alone.

## Final integrated tactical recovery check (after development)

Build the experimental 31-trigger variant with --experimental-defenders 4 --all-map-defenses --wave-reinforcements --tactical-recovery. In one private WSE2 session, allow casualties, inspect fallback to survivor spawn and regroup after subsequent wave reinforcement; check that zombie paths and all five maps remain intact. Exit and collect one local evidence archive with tools/Collect-Diagnostics.ps1. The analyzer will report wave/mode state, candidate stalls and optional movement data. No intermediate playtesting is expected.

## v0.1.7 final solo testing

At the final integrated Windows test, enable --experimental-defenders 4 --defender-loadouts balanced-ai --all-map-defenses --wave-reinforcements --tactical-recovery --solo-assist. Validate the four AI-only weapons and ammo, original playable class loadouts, wave-based class rotation, and that solo assist affects only a one-player listen host. Collect one end-of-session evidence ZIP; no incremental testing requested.

## v0.1.8 one-time final forensic gate

Use the complete 35-trigger private build with `--private-commands --difficulty standard` (do not combine with `--solo-assist`). In the final private listen-host session only, verify Left Ctrl+F7/F8/F9 and the corresponding command counters. Leave the game running for at least one 15-second telemetry heartbeat after any hotkey. Capture weapons/ammo/kills samples where possible and check that all zombie waves and five original maps remain usable. The evidence matrix will report missing getters as unknown, not as 0 activity. No incremental user testing before the integrated candidate.
