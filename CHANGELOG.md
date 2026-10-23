# Changelog

Uses [Semantic Versioning](https://semver.org/) for the remaster, not the historical original.

## [0.1.5] - 2026-10-23

### Added
- Source-derived, reproducible guard-post proposals for Granny's House, Bridge, Shipyard and Abandoned Town using free entries 41–43.
- A five-map, server-only, scene-scoped tactical order trigger replacing the previous City-only *remaster* order trigger. All 25 original mission triggers stay intact.
- Optional reinforcement keyed to original `wave_number`: resets a new dedicated sentinel at mission start, counts living non-player team-0 agents in groups 5–7 and tops up to the requested cap once per new wave from wave 2.
- Opt-in installer flags `--all-map-defenses` and `--wave-reinforcements`. Normal builds retain original behaviour.
- Extra diagnostic SHA-256 fingerprints of the compiled `variables.txt` table and five tactical scene files.
- Original Beta 0.4 offline integration and additional regression tests for waves, scene geometry, troop ordinals and duplicate patching.

### Unverified
- Runtime troop spawning, AI orders/pathfinding, map sightlines, networking, wave completion, performance and WSE2 execution. No CI or original third-party binaries added.

## [0.1.4] - 2026-10-23

### Added
- Source-derived SCO reader for five original maps, including City navigation mesh and survivor/zombie spawn entries.
- Deterministic three-post City defence plan from the connected walkable navmesh, with guard entries 2/3/4 inserted only into a copy of the original scene.
- Opt-in `--city-guardposts` installer flag (requires experimental survivor bots).
- Split allied bots into groups 5/6/7 and issue server-only one-time City hold orders; original 25 mission triggers and zombie entry points preserved.
- Scene and compiled mission integration tests on original Beta 0.4 data; no CI and no redistribution of original binary assets.

### Still unverified
- WSE2 gameplay, bot AI pathing/shooting, physical obstacle clearance, multiplayer synchronization and complete zombie waves.
- Guard post geometry is navmesh-based; gameplay may require adjusting positions.

## [0.1.3] - 2026-10-23

### Added
- Read-only WSE2 mission lifecycle telemetry with structured ZDB1 events, bounded periodic agent-count sampling, and guarded Lua probes.
- One-command end-of-session Windows evidence collector; discovers native engine logs and retains modification-time/truncation metadata.
- Redacted, SHA-256-checksummed ZIP evidence packages and offline Markdown failure reports; detection of missing assets, crashes, Lua/script faults, stale logs and unexpected compiled mission trigger counts.
- Multi-session comparison for persistent, new and resolved diagnostic rule IDs.
- Installed module-file SHA-256 fingerprints and verified 7-Zip CRC/trigger-count receipts; no compiled assets or unredacted logs packaged.
- Optional WSE2 survivor/zombie team sampling with explicit unknown values and regression diagnosis.
- Fifteen additional offline diagnostic regression tests, including large-log head/tail retention.

### Not verified
- No Windows WSE2 gameplay test yet; allied bot combat, spawning, pathing, wave completion and private networking remain unverified.
- Redaction is best-effort: inspect bundles before sharing.
- Source RAR still needs independent 7-Zip CRC test on Windows.

## [0.1.2] - 2026-10-23

### Added
- Opt-in native original 0.4 allied survivor spawn: `--experimental-defenders 1..8` (default off).
- One `ti_after_mission_start` server-only trigger calling `add_visitors_to_current_scene` for team 0, original entries 0/1.
- Data-derived troop IDs, duplicate invader-name handling, original CRLF preservation and installer post-apply static validation.
- Windows PowerShell smoke-test helper plus seven tests; **21 local Python tests pass**.

### Not verified
- WSE2 runtime or bot gameplay, defensive movement orders, wave respawns, multiplayer synchronization.
- Independent Windows 7-Zip CRC check of the original RAR.

## [0.1.1] - 2026-10-23

### Added
- Compiled invasion parser identifying entry points and mission trigger intervals.
- Missing, duplicate and case-mismatched local BRF dependency diagnostics.
- Installer preflight guard and static findings recorded in the install manifest.
- WSE2 Lua one-time invasion mission-entry diagnostic probe.
- Six additional local preflight regression tests.
- Non-invasive compiled `call_script` tracer identifying bot spawn/leader integration points.
- Three local call-graph regression tests (**14 tests total**).

### Not verified
- The original RAR still requires independent Windows 7-Zip CRC testing.
- No Warband/WSE2 launch or completed wave; no allied defender gameplay yet.

## [0.1.0] - 2026-10-23

### Added
- Archive-provenance policy and initial guarded local installation tools.
- Static core module doctor, initial Lua bootstrap, standalone tests and manual verification checklist.
- Version policy and restoration-first roadmap.

### Not shipped
- No tested runtime build, allied bot positions, admin cheats or measured performance improvements.
