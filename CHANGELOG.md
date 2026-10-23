# Changelog

Uses [Semantic Versioning](https://semver.org/) for the remaster, not the historical original.

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
