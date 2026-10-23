# Agent B — Windows 11 installer and one-click City solo launcher

**Work branch:** `agent/b-windows-launcher` (exists, based on `main@048564a526de9b36abd55874271c7b80f36e5cf5`). **Target repo:** `yigit-denktas/MBW-ZOMBIEEE-Mod`. Start by reading `README.md`, `tools/build.py`, `tools/doctor.py`, `configs/solo_server.cfg`, and [Agent A's integration contract](https://github.com/yigit-denktas/MBW-ZOMBIEEE-Mod/blob/agent/a-city-engine/handoffs/SESSION_CONTRACT.md). Project Record proposal: [ledger](https://github.com/yigit-denktas/MBW-ZOMBIEEE-Mod/blob/project-record-setup-v041/progress/ledger.json) and [allocation](https://github.com/yigit-denktas/MBW-ZOMBIEEE-Mod/blob/project-record-setup-v041/progress/agent-allocation.json).

## Assignment and hard constraints

Own `ZOM-WIN-01`, `ZOM-WIN-02`, `ZOM-WIN-03`, `ZOM-SOLO-01`, `ZOM-SOLO-02` (plus installer-oriented `ZOM-LEGAL-01` and packaging `ZOM-REL-01` later). GitHub issues [#8 discovery/installer](https://github.com/yigit-denktas/MBW-ZOMBIEEE-Mod/issues/8) and [#9 private host](https://github.com/yigit-denktas/MBW-ZOMBIEEE-Mod/issues/9) are the source discussions.

User target: Windows 11, automatically detect a **licensed** installed Mount & Blade: Warband and compatible WSE2, apply original ZOMBIEEE Beta 0.4 content **locally from user-provided archive**, create a desktop shortcut, and double-click to **Play Solo City** with AI defenders. All other four maps and friends/co-op are deferred after first release.

Do not touch `tools/build.py`, `tools/diagnostics.py`, `overlay/lua/**`, `progress/**`, `gh-pages`, or agent A/C files. Own `launcher/**`, `installer/**`, new `tests/test_windows_*.py` and `docs/WINDOWS_*.md`. Agent A is integration lead; Agent C owns the recorder. No CI. Do not commit original RAR, Warband binaries, WSE2 executables, proprietary scenes, original textures, or personal paths/logs. Do not auto-download any proprietary content without verified rights and source.

## First independent development cycle — start now

1. Implement a read-only Windows game discovery API/CLI in `launcher/` or `installer/`: examine Steam library folders including modern/legacy VDF formats, typical Windows install roots, user override, WSE2 candidates, and empty/ambiguous cases. *No unsafe inference*: return structured candidate list, validation evidence, stable error codes and "unknown" where not observed.
2. Add deterministic cross-platform unit tests using fake Windows directory trees, Unicode and spaces in paths, multiple Steam libraries, invalid version/executable, missing WSE2, duplicate detections, and no permissions. Tests run without Windows game files.
3. Design reversible install workflow as **dry run first**: verify original source archive checksum, call existing `tools/build.py` via subprocess, stage to temporary directory, refuse overwrite without opt-in, atomically install with rollback and recovery journal. Never delete an existing game or original module. Errors produce machine-readable reports.
4. Prototype a **fake-process** City local-host lifecycle (start, readiness, connect, stop, crash, collect), explicitly **not** declaring WSE2 start flags valid until Agent A obtains runtime evidence. Keep local-only mode as default; no public matchmaking, firewall changes or port forwarding.
5. Prepare a launcher desktop shortcut design and a 'Play Solo' action only after actual launch behaviour is known. Settle listen-server vs dedicated helper by evidence, not guesswork. Session receipt must follow [Agent A contract](https://github.com/yigit-denktas/MBW-ZOMBIEEE-Mod/blob/agent/a-city-engine/handoffs/SESSION_CONTRACT.md); Agent C reads it for crash telemetry.

## Definition of your first PR

- Discovery code and fixture tests pass, and output includes ambiguous/unavailable statuses rather than false positives.
- Dry-run install manifest and rollback invariants are tested; launcher shell may be mocked.
- Documentation separates verified offline behaviour from untested Windows/WSE2 runtime.
- Push commits **only** to `agent/b-windows-launcher`; open a **draft PR** against `main`; do not merge without Agent A's integration review.
- Report tested commands, fixture results, file paths, API schema and integration questions back to Agent A via PR comments and/or GitHub issues.
- This is not the final game playtest. The user explicitly wants one final integrated Windows validation, not repeated manual intermediate tests.

**Start immediately. Do not ask the user where the game is installed: discovery is your task.**