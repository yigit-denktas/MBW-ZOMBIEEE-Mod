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

---

# Agent B handoff — issues #8 and #9

Base: main v0.1.8, `048564a`; branch: `agent/b-windows-launcher`.
Coordination source: `progress/agent-allocation.json` on
`project-record-setup-v041`, read 2026-10-23. This is implementation evidence,
not a release acceptance claim. No progress/ledger, README, Pages, builder,
diagnostics or Lua files are changed.

Delivered first slices:

- **ZOM-WIN-01:** bounded read-only discovery CLI/API with structured provenance,
  candidate failures, ambiguity and unknown ownership/runtime semantics.
- **ZOM-WIN-02:** dry-run manifest and transaction/recovery design; real install,
  repair/update/uninstall and consent persistence remain pending.
- **ZOM-SOLO-01:** fake-process City lifecycle model; route, engine flags,
  private bind, readiness and joining require engine evidence.
- **ZOM-WIN-03 / ZOM-SOLO-02:** desktop UI/shortcut and real auto-join remain gated.

See [Windows bootstrap](../docs/WINDOWS_BOOTSTRAP.md) for commands, schemas,
recovery requirements and exact test limits.

## Proposed interfaces for review

Agent A: B calls the existing builder only as
`[python, tools/build.py, --archive, archive, --out, stage/ZOMBIEEE_Remaster]`.
No `--replace`, engine process or experimental flags are chosen in this slice.
The builder remains responsible for archive integrity and output compilation.
The optional `--audit-archive-hash` planner flag consumes A's shared
`tools/archive_audit.py --archive ... --json` subprocess contract. On this
v0.1.8 branch that tool remains unavailable until A is integrated; fixtures
exercise the adapter without copying or duplicating A's verifier.
A confirmed the City profile in its PR #11 review: `--experimental-defenders 4
--city-guardposts --wave-reinforcements --tactical-recovery`, without
`--all-map-defenses` (optional balanced-ai after static checks), and installed
receipt `experimental_map_scope=city-only`. It depends on PR #10 and is not
executed by the v0.1.8 planner. Validated startup/private-bind/join/stop semantics
still require the shared contract and runtime evidence.

Agent C: B's pure state machine emits intent actions `start:recorder`,
`start:host`, `start:client`, `stop:client`, `stop:host`, `stop:recorder`.
The eventual adapter must wait for recorder readiness, preserve recording until
all game processes exit, and consume C's recorder start/ready/stop API without
duplicating log collection. Current `Session.receipt()` contains only simulation
state in A's provisional `zombieee.session.v1` envelope, with additive
simulation fields, null runtime observations and `outcome:unknown`. It is
**not** the recorder API or a validated evidence receipt.

B-1/B-2 revision: start requests only the recorder and waits for the canonical
`zombieee.recorder-ready.v1` marker. The consumer verifies
session/attempt/recorder identity, `watcher_id`, the
`log_offsets_captured`/`watcher_active` true and `engine_ready`/`mission_ready`
false fields, and a fresh adapter liveness observation before requesting the
first game process. Game spawn, `host_ready`, `joined` and `mission_entered` are
separate correlated milestones for both routes: host readiness never means a
player joined, and a join observation never means the City mission was entered.
Only `mission_entered` reaches the modeled `playing` state. The marker and C
responsibilities are documented in
[Windows recorder handshake](../docs/WINDOWS_RECORDER_HANDSHAKE.md) and
coordinated on PR #12; C production and a real adapter remain pending.
B-3 keeps lexical input-root/component/reparse evidence, including root/ancestor
junctions and journal redirects, guards every later filesystem probe (a denied
`stat()` returns `path_inspection_failed` evidence instead of aborting the
planner) and requires rechecks before future writes.

Real receipts will follow A's shared envelope. Proposed additive fields, pending
A/C agreement: process start identity, readiness source and lifecycle status.
The real adapter must supply an opaque session ID,
UTC start/end timestamps (end null while active), simulation=false,
local_only=true only after private bind validation, selected verified route,
City/mission, module manifest SHA-256, process roles/PIDs plus start identity,
readiness source, lifecycle state, exit code/reason and recorder reference.
Unavailable evidence stays null/unknown. Store atomically in a per-user local
directory derived from Windows known folders; C consumes read-only and owns
redaction, hashing, bundle construction and publication controls. No receipt
files or local user paths are committed here.

The adapter must correlate observations to a session/attempt and owned process
identity, refuse stale readiness, keep credentials out of argv/receipts, and
implement consent for actual launches. Do not use the simulation alone as
authorization or evidence that the engine's network listener is private.

## Acceptance proposal to Agent A

Keep all five WIN/SOLO leaves pending acceptance. Record the offline fixture
tests as implementation evidence only. Legal redistribution remains unverified;
no licensed binaries, original mod assets, executable dependencies or CI added.
No user playtest is requested during this first slice.

## Verification — 2026-10-23

First slice: `python -m unittest discover -s tests -q` → **127 tests, OK, 30
skipped** (existing asset-dependent tests require `ZOMBIEEE_ORIGINAL_MODULE`);
all 35 B fixture/CLI tests passed on Windows, including directory junctions and
read-only file-version inspection. Junction tests ran outside the restricted
sandbox because it denies junction creation; all fixtures stayed in temporary
directories. No real game process was launched or install attempted.

B-1/B-2/B-3 revision: `python -m unittest discover -s tests -q` → **148 tests,
OK, 30 skipped**; all **56** B fixture/CLI tests pass. Added coverage for the
canonical recorder marker fields, no game start before valid recorder-ready on
both routes, stale/foreign/duplicate/late readiness, recorder and game crash,
recorder loss during shutdown, spawn failure, separate host-ready/joined/
mission-entered milestones, join and mission timeouts, retry cleanup,
top-level/ancestor junctions, journal redirects, post-lexical `stat()` denials
and malformed configured paths (review P2). No real game process was launched
or install attempted.

Independent read-only code review found a malformed Steam path could abort
structured discovery. Fixed normalization handling for invalid custom/library/
Steam roots and rejected control characters in install-directory names. The
regression preserves a valid candidate alongside corrupt inputs. A later review
found that a denied `stat()` after a successful lexical check could abort the
install planner; every subsequent probe is now guarded and returns
`path_inspection_failed` evidence. A follow-up review found recorder loss during
shutdown could be normalized to a clean `stopped`; it now retains
`recorder_exited_during_shutdown` and ends `failed`. Runtime and original-asset
checks remain pending; test counts do not certify a playable release.
