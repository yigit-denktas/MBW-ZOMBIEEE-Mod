# Agent C — crash-resistant flight recorder and forensic game diagnostics

**Work branch:** `agent/c-flight-recorder` (exists, based on `main@048564a526de9b36abd55874271c7b80f36e5cf5`). **Repo:** `yigit-denktas/MBW-ZOMBIEEE-Mod`. Start by reading `tools/diagnostics.py`, `tools/tactical_analysis.py`, `tools/combat_analysis.py`, `tools/evidence_readiness.py`, `overlay/lua/main.lua`, `docs/DIAGNOSTICS.md` and [Agent A's integration contract](https://github.com/yigit-denktas/MBW-ZOMBIEEE-Mod/blob/agent/a-city-engine/handoffs/SESSION_CONTRACT.md). Source ledger: [Project Record Standard review](https://github.com/yigit-denktas/MBW-ZOMBIEEE-Mod/blob/project-record-setup-v041/progress/ledger.json); [allocation](https://github.com/yigit-denktas/MBW-ZOMBIEEE-Mod/blob/project-record-setup-v041/progress/agent-allocation.json).

## Assignment and principles

Own ledger IDs `ZOM-OBS-01`, `ZOM-OBS-02`, `ZOM-PERF-01`, `ZOM-QA-01`, `ZOM-QA-02`, primarily [GitHub issue #6](https://github.com/yigit-denktas/MBW-ZOMBIEEE-Mod/issues/6). The user regards telemetry and diagnostics as **the core instrument** for future AI, engine and gameplay fixes. Actual Windows 11 WSE2 playtest is deferred to a single integrated session near release. Do not claim game data existed unless observed. Missing operations must be `unknown`, never 0, "passed", or "no error".

Own `telemetry/**`, `tools/diagnostics.py`, `tools/tactical_analysis.py`, `tools/combat_analysis.py`, `tools/evidence_readiness.py`, `overlay/lua/**`, `tests/test_diagnostics.py` and `docs/DIAGNOSTICS.md` and `docs/FORENSIC_DIAGNOSTICS.md`. Avoid Agent A's `tools/build.py` and native gameplay patches, Agent B's `launcher/**`, `installer/**`, and Agent A's `handoffs/SESSION_CONTRACT.md`. Do not edit `progress/**`, `gh-pages` or `README.md`. No CI and no game assets.

## First independent development cycle — start now

1. **External flight recorder prototype:** a separate local process survives a simulated child process crash, watches bounded text logs/process lifecycle, performs atomic file writes, captures start/exit/timeout and CPU/memory when actually available, preserves timestamps and build provenance, and applies bounded retention. Tests with a fake game process; never need Warband installed to run them. Prefer standard Python libs for cross-platform tests, with Windows-specific features guarded.
2. **Event schema:** version the ZDB1 runtime records: boot, mission_start, heartbeat, agent/team, original wave transitions, kills/ammo/weapons/position *only when native WSE2 operation mapping works*, and fatal/errors. Explicitly report per-metric availability and trace sampling rate, rather than treating absent events as bad gameplay.
3. **Integration contract:** consume Agent B's eventual local JSON session receipt (per [Agent A contract](https://github.com/yigit-denktas/MBW-ZOMBIEEE-Mod/blob/agent/a-city-engine/handoffs/SESSION_CONTRACT.md)). Build a deterministic SHA-256 manifest for event/log artifacts, redact personal paths, account info, tokens, IPs and chat, and provide a private zip that is never uploaded without user action.
4. **Forensic evidence:** extend/validate `tools/diagnostics.py collect/verify/analyze/compare` and the readiness matrix with synthetic scenarios: corrupted log, missing event, truncated log, engine crash, stale build hash, stalled waves, AI with zero ammo, known weapon/no kills, failed startup, group-order thrashing. Every alert needs supporting event ids/timestamps, actionable hypotheses and confidence/unknown status; never claim causal proof from correlation.
5. **Privacy and performance:** no player names, chat, exact personal paths or external requests in public outputs; exact event limits to prevent FPS degradation. Report actual FPS/frame timings only when the underlying engine exposes them and they were measured. Make diagnostics optional, bounded and graceful if WSE2 Lua lacks getters.
6. **Negative controls:** confirm a stationary defender on a legitimate hold position is *not* labelled stuck and unavailable kill getter does *not* count as zero kills.

## Definition of your first PR

- Recorder survives a forced simulated crash and produces a locally verifiable, redacted report with build/session ids.
- Evidence bundle corruption is detected by checksum verification, data is bounded, and unsupported metrics are marked unknown.
- Unit tests run **offline**; document exact commands, results and what remains untested in WSE2/Windows.
- Push only to `agent/c-flight-recorder`; open draft PR against `main` with test receipts. Do not merge without Agent A's integration review.
- No CI, no third-party asset redistribution, no telemetry cloud hosting.
- Do not ask user for repeated game tests until final integrated Windows candidate.

**Start immediately. Report any schema changes to Agent A and Agent B via GitHub PR/issues, not chat-only.**