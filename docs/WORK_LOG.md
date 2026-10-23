# Work log

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
