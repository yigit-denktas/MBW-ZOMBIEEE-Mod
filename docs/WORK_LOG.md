# Work log

## 2026-10-23 — v0.1.7 AI-only loadouts and solo assist

- Original 0.4 compiled items contain 16 duplicated names. Preserved original positional IDs; cloned four AI-only troops using unambiguous original weapons/ammo.
- Wave replacement class rotates by original wave number and replacement ordinal; original wave cap and server guard preserved.
- Added guarded non-dedicated single-player host-only HP/ammo assist, disabled by default and rejected on repeat patching.
- Verified 985 troops, 1,222 variables and 32 valid compiled mission triggers on a temporary original-data patch chain; reran 48 offline local tests (37 previous + 11 new original-data tests), all passed.
- Actual Windows/WSE2 operation unverified; no CI or intermediate user tests.

## 2026-10-23 — 0.1.6: fall-back/regroup under pressure

- Implemented native 3-second tactical controller for original ZOMBIEEE 0.4; one extra state global and two triggers appended after the v0.1.5 29-trigger module.
- Mode 0 (HOLD): current-map guard posts. Mode 1 (FALLBACK): survivor entry 0. Only reserved team-0, AI-controlled divisions 5–7 are involved.
- Casually depleted defenders at <=1 trigger fallback; after a later reinforcement recovery to >=3, squad receives map-specific regroup orders.
- Integrated full offline original-module patch chain to 31 compiled triggers; original 25 unchanged; 1,222 globals total.
- Expanded Lua event recorder with wave, round, tactical mode and optional bounded non-player defender movement samples; analyzer uses evidence-gated stall, mode-thrash and movement heuristics.
- 37 tests passed in the local integration subset (original 0.4 tests and synthetic diagnostics); WSE2 runtime remains unverified. No CI, no intermediate user playtests.

## 2026-10-23 — 0.1.5: wave-limited reinforcements and five original maps

- Located original `wave_number` (global ordinal 1209), `wave_counted`, `last_wave` and `wave_timer` inside original compiled invasion trigger 15.
- Implemented a separate server-only reinforcement trigger and match-init sentinel without altering original zombie spawn logic; caps living non-player team-0 defenders in private groups 5–7 at requested squad count.
- Generated reachable AI-mesh post candidates for all five 2012 maps; inserted previously unused entries 41–43 on four maps and preserved City entries 2–4.
- Integrated five-map-scoped hold orders and once-per-wave survivor replenishment behind opt-in build flags.
- Original-copy offline prototype passed: 29 invasion triggers, 1,221 globals (one added), AI meshes and original RAR unchanged. Seven new regression cases authored; no Windows runtime confirmation.
- Updated diagnostic fingerprints for wave table and all five scenes; no CI, no ZOMBIEEE2.

## 2026-10-23 — 0.1.4: concrete City tactical overlay

- Parsed all five original 2012 SCO scenes using the documented format; City has 226 scene objects, 11 entries, 323 AI mesh vertices and 270 navmesh faces.
- Sampled 3 post centroids in the connected navmesh, 15–16m from survivor spawn, avoiding original zombie entries 32–40.
- Inserted only new City entry IDs 2, 3, 4 in an extracted scene COPY. Navigation mesh and existing 226 objects preserved.
- Segregated survivor allies into private divisions 5/6/7; appended one server-only City-scoped native hold-order trigger. 25 original triggers unchanged; optional combined build has 27.
- Offline integration against the supplied Beta 0.4 succeeded; original scenes and RAR never modified. No CI, no intermediate Windows handoffs, gameplay still unverified.

## 2026-10-23 — 0.1.3: unattended evidence and diagnostics

- Added versioned WSE2 read-only events (bootstrap, mission entry, role, bounded agent count/heartbeat).
- Built Python standard-library evidence collection/verification/offline analysis and cross-session comparison.
- Added Windows PowerShell wrapper for one-time evidence collection at the *final* integrated test.
- Automated local diagnostic tests cover redaction, tamper resistance, zip-slip rejection, missing or stale logs, crashes, missing resources, and cross-run comparison (15 new tests passed).
- Privacy by default: redacted log tails, module fingerprint hashes, no original assets, no upload/CI.
- **Runtime gameplay still unverified.** No new demand for step-by-step Windows tests.

## 2026-10-23 — 0.1.2: first opt-in allied defender spawn

- Traced original compiled `multiplayer_iv` and native `add_visitors_to_current_scene` opcode 1265, server-only check 417.
- New `tools/patch_defenders.py` adds one `ti_after_mission_start` trigger, 1–8 survivor-class bots at side-0 entries 0/1. Original 25 trigger lines preserved.
- Original 981-troop archive includes five duplicated invader troop names; preserve original numeric IDs and reject ambiguous survivor names.
- Tested injected mission against original extracted data: 26 triggers and 64 entry points; original call graph still parses.
- 21 local Python tests pass, new PowerShell smoke-test helper ready. WSE2 gameplay and 7-Zip RAR CRC not verified.

## 2026-10-23 — 0.1.1 diagnostic groundwork

- Canonical remote: yigit-denktas/MBW-ZOMBIEEE-Mod.
- New preflight found 30/30 locally referenced BRFs and 64 entry points / 25 triggers in historical 0.4 invasion mission; 11 local tooling tests passed.
- Build preflight now rejects missing module BRFs or malformed invasion data.
- Added WSE2 Lua mission entry instrumentation based on documented addTrigger API.
- Original RAR CRC test and Windows runtime smoke test still outstanding.
- No CI, no ZOMBIEEE2, no original assets committed.

## 2026-10-23 — 0.1.0

- Initialized remaster repository, guarded archive installer, static doctor and author credits.
