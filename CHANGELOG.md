# Changelog

Uses [Semantic Versioning](https://semver.org/) for the remaster, not the historical original.

## [0.3.0-beta.1] — consolidated source save point (source 26f303264cf14df40075db2b856f1d9d7b547ffc) (2026-10-24)

- Consolidated reviewed C/G/H work; 634 tests OK, release gate 0; tag `save/0.3.0-beta.1-consolidated-2026-10-24`.
- Froze 18 branch tips as `archive/2026-10-24/*` tags before cleanup; manifest in `archive/2026-10-24/branches.json`.
- Added granular cards for privacy/gate, parser caveat, spatial consumer, A packaging, parallel lanes, consolidation.
- `runtime_verified=false`, acceptance none; fire-volume/parallel-lane runtime remain unproven.

## [0.3.0-beta.1] - 2026-10-24

**Pre-release candidate — not released, not accepted.** This consolidates the
UI/launcher/telemetry/AI work merged since 0.2.0 into the SemVer pre-release
candidate **`0.3.0-beta.1`** (a beta, not an RC: 0.3.0 milestone acceptance is
still active) at source revision `095f1b0`. The `0.3.0` milestone remains reserved
for verified allied survivor/class/loadout acceptance ([docs/ROADMAP.md](docs/ROADMAP.md));
work-item → PR → commit → version links are in
[docs/RELEASE_TRACEABILITY.md](docs/RELEASE_TRACEABILITY.md) and
[docs/release-traceability.json](docs/release-traceability.json).

### Added
- **One-command launcher maintenance (M2):** per-file ownership receipts plus
  read-only `verify`, `repair` from a verified build, and quarantine-first
  `uninstall` (no game data deleted by default; modified/unrecognised files
  preserved) — [PR #28](https://github.com/yigit-denktas/MBW-ZOMBIEEE-Mod/pull/28), `579b446`.
- **Desktop surface/settings:** control panel (Play Solo/settings/logs/repair/uninstall/release),
  private schema-validated settings and an inspectable desktop shortcut spec —
  [PR #28](https://github.com/yigit-denktas/MBW-ZOMBIEEE-Mod/pull/28).
- **Delivery gate:** read-only release checks for required files, VERSION/
  traceability links, tracked-binary/path/secret hygiene and installed-module
  structure (candidate-checks-only) — [PR #28](https://github.com/yigit-denktas/MBW-ZOMBIEEE-Mod/pull/28).
- **AI standoff/hold/fire and wave staging (implemented; runtime acceptance
  pending):** native-group hold/fire orders, slow Zombie 894 wave-visitor
  gating, 8-defender squad with `spawn_agent` refill, ammo-gated ranged
  standoff — commits `ec34e3b`/`f0c3e68` (task-38), `c0b9a36`/`0884b64`
  (task-34), `8676eaa`/`fdb642f` (task-42). Division/hold adoption remains
  unobserved.
- **Telemetry:** team-1 speed/order/ammo-transition readbacks and combat fields —
  commits `9c39889`/`156dfb0` (task-41), `c72de64`/`a3ed506` (task-43).
- **Release metadata:** this pre-release candidate, CHANGELOG and work-item/PR/
  version traceability record.
- **Legal/rights dossier:** cited rights, credits and redistribution open risks —
  [PR #27](https://github.com/yigit-denktas/MBW-ZOMBIEEE-Mod/pull/27).
- **Tracker/Pages dependency graph and consolidation** — [PR #7](https://github.com/yigit-denktas/MBW-ZOMBIEEE-Mod/pull/7), record commits.

- **Free-asset licence catalogue + icon/currency mapping contract (docs/definitions
  only, no binaries):** verified-licence source catalogue, Warband integration
  constraints and adopt/adapt/avoid decisions (`reference/FREE_ASSET_SOURCES.md`),
  kill-feed/HUD icon mapping for melee/bow/crossbow/firearm/zombie/money-USD
  (`docs/ICON_MAPPING.md`), definitions-only `configs/ui_icon_map.json`;
  independent licence review by Agent E, **no legal clearance or acceptance** —
  [PR #31](https://github.com/yigit-denktas/MBW-ZOMBIEEE-Mod/pull/31) `85b9c0b`,
  merged `8b38f7d`.
  Native Warband/ZOMBIEEE assets have no recorded redistribution right and are
  not bundled.
### Changed
- Launcher City default rotation now requests the native team-0 defender squad
  (`set_bot_count 1 8`) with enemy profiles `generic`/`weak-wave1`/`native-only`
  and a `--team0-bots`/`--team2-bots` override — [PRs #20/#21](https://github.com/yigit-denktas/MBW-ZOMBIEEE-Mod/pull/21), `c86df95`, `c301f22`.
- `VERSION` is now a SemVer **pre-release** candidate; `release-check` accepts
  pre-release SemVer and requires traceability links.

- C cross-review fixes for survivor formation/cohesion and wave staging
  (task-45/46) are included from `14896fb`/merge `2535c56`; implementation-only,
  runtime acceptance still pending.
- P0 faction-slot/scene telemetry readback for appended-trigger runtime
  diagnostics (task-55, `1f00079`/merge `6489e4c`) is included;
  implementation-only, runtime isolation acceptance pending.
- C faction-slot probe fix (`07c85e4`/merge `d7ec9db`) is included;
  implementation-only, runtime isolation acceptance pending. Bannerlord
  engine/combat-AI research (`db39186`) is docs-only context.
- Original trigger-14 invalid-faction log guard (`985fee7`/merge `509f16a`,
  ZOM-DISC-60) is included; implementation-only, sustained-runtime acceptance
  pending.
### Still not accepted
- City required outcomes **0/23**, milestones **0/5**, `runtime_verified=false`.
- Native defender **spawn** is proven, but division 5–7 adoption / stable hold /
  guard-entry identity remains **unobserved** (candidate-only wording); wave
  2+/completion, defender KD balance (task-45/46 pending), combat feel and
  sustained solo testing remain open.
- The historical `0.2.0` entries above are preserved without retroactive PR
  links; post-0.2.0 links live in this candidate section and the traceability
  record.
- Redistribution/legal clearance, accessibility review, packaging/signing and
  owner acceptance remain open. No tag, GitHub release or deployment is claimed.

## [0.2.0] - 2026-10-24

### Added
- Native Zombie roster 894..911 fixed (faction-conditional compiled bot-troop scan), with 873/874 Crazed Civilian bots absent in sealed evidence.
- Native allied defender spawn 981..984, group/division adoption path, scripted-destination movement and per-round respawn top-up.
- Wave 2 observed in the defender-heavy variant (`set_bot_count 1 8 / 2 4`, `player_respawn_as_bot 1`); stock squad remains max wave 1 due native round reset.
- One-command `python -m launcher.play_city`: discovery, pinned archive audit, backup-first install/rollback, validated rotation, recorder, loopback host, auto-join client, sealed manifest + summary.
- Sealed ZDB1 probe stream, troop/position/kill telemetry, roster labels, pre-round samples, returned-value lhs fixes, **zero-spam group probe**, and automatic-firearm accuracy profile.
- README/provenance with archived original-team credits and owner-attested permission basis; redistribution remains uncleared.

### Still not accepted
- Division 5-7 adoption / stable hold / guard-entry identity is unobservable in this runtime; movement only.
- Wave 3+/completion, stock-squad wave 2, combat feel, installer/public release, legal redistribution.
- City required outcomes **0/23**, milestones **0/5**, `runtime_verified=false`; suite caveat retained.
## [0.1.8] - 2026-10-23

### Added
- Native, opt-in Left Ctrl+F7/F8/F9 private host controls (heal host, refill ammo, heal/rearm reserved AI defenders), gated by server, non-dedicated, one active player and local living survivor host.
- Three appended command counters and one reset trigger; game-side execution can be corroborated in read-only WSE2 logs.
- Explicit story/standard/hard/nightmare survivor-support profiles modifying the first reinforcement wave and tactical fallback hysteresis, without modifying original zombie difficulty.
- Minimal read-only WSE2 Lua Module System operation bindings to sample bot weapons, ammunition, kills and position where supported.
- Expanded structured ZDB1 event stream, combat forensic rules R023-R026, and an acceptance matrix marking missing observations as unknown.
- Fixed Lua integer-zero role detection and a Markdown report crash when bot findings contain non-file structured evidence.
- New unit tests for native hotkeys, original-data patch integration, combat false positives, acceptance evidence, and report rendering.

### Still unverified
- Actual Warband/WSE2 Lua bindings, host keypress delivery, remote-player exclusion, AI combat engagement, wave victory, and client/server synchronization. These require the one-time final integrated Windows test.
- No CI, no ZOMBIEEE2 assets or third-party game binaries.

## [0.1.7] - 2026-10-23

### Added
- Optional 4 AI-only original-class-derived troop clones at IDs 981–984 (Commando M16A2, Sniper Remington 700, Scout MP5, Lumberjack Browning Cynergy) with original 0.4 ammo/clothing assets. Original playable troops unchanged.
- Preserved 16 duplicated historical item identifiers while requiring selected AI equipment IDs to be unambiguous.
- Wave-based reinforcement class rotation, avoiding repeated first-class replacement bias.
- Private listen-host-only solo HP/ammo assist every 12 seconds, guarded against dedicated servers and sessions with multiple active players; no anti-cheat bypass.
- New original-data loadout and solo-assist regression tests, build provenance and local diagnostic metadata.

### Unverified
- Actual Warband/WSE2 player counting, AI weapon selection, firing, ammo compatibility and combat. Timed cheat preset is not yet an interactive cheat-code menu. No CI.

## [0.1.6] - 2026-10-23

### Added
- Opt-in server-authoritative defender HOLD/FALLBACK state machine. Detect casualties across private groups 5–7; fall back at <=1 remaining bot, regroup at >=3 surviving bots, issue orders only when state changes.
- Preserve original wave, map and zombie logic. Append two compiled mission triggers and one global without renumbering existing data: 31 total triggers and 1,222 total globals in the complete experimental build.
- WSE2 Lua diagnostics read actual original wave and round globals and the appended tactical-state global through the documented game.gvar interface.
- Bounded wave and mode transition logging and optional defender position samples (graceful unavailable behavior without WSE operation bindings).
- Offline analysis signals for candidate stalled waves, tactical oscillation, apparently ineffective regrouping, and immobile defenders after a state change; stationary guard posts alone are not treated as stuck.
- Guarded installer flag --tactical-recovery, dependency checks and expanded local regression coverage.

### Still unverified
- WSE2/Windows execution, bot pathing, retreat arrival, firefights, wave completion, multiplayer replication and exact frame-time impact. No CI.

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


<!-- task-65 branch metadata-only source revision: 1374abd -->


<!-- P0 probe fix metadata-only source revision: 39aa3a7 -->


<!-- P0 probe team-order fix metadata-only source revision: 4848ee2 -->


<!-- telemetry hardening metadata-only source revision: 08a9546 -->


<!-- telemetry hardening metadata-only source revision: d0f7edf -->


<!-- telemetry claim-wording metadata-only source revision: 79d7b84 -->


<!-- hit mapping metadata-only source revision: 8759eed -->


<!-- task-74 heatmap metadata-only source revision: b06f427 -->


<!-- task-71 hit-trigger metadata-only source revision: 1845906 -->


<!-- task-76 adaptive sampling metadata-only source revision: 67dd281 -->


<!-- heartbeat nil-fix metadata-only source revision: 8d07f2f -->


<!-- hit-param two-arg metadata-only source revision: 0d9415c -->


<!-- hit-param diagnostic metadata-only source revision: d988597 -->


<!-- task-82 ranged telemetry metadata-only source revision: 41062a3 -->


<!-- ranged adaptive coverage metadata-only source revision: 1d714c7 -->


<!-- shot proxy metadata-only source revision: 9e4342c -->


<!-- refill-off context metadata-only source revision: c170ebf -->


<!-- adaptive parser/brief metadata-only source revision: b54124c -->


<!-- task-72 spatial metadata-only source revision: 6a1f653 -->


<!-- task-72 review fixes metadata-only source revision: 0325ea6 -->
