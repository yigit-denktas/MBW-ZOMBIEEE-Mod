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
Please specify the City build profile and validated startup/private-bind/join/
stop contract in A-owned `handoffs/SESSION_CONTRACT.md` before integration.

Agent C: B's pure state machine emits intent actions `start:recorder`,
`start:host`, `start:client`, `stop:client`, `stop:host`, `stop:recorder`.
The eventual adapter must wait for recorder readiness, preserve recording until
all game processes exit, and consume C's recorder start/ready/stop API without
duplicating log collection. Current `Session.receipt()` contains only simulation
state and is **not** that API or a validated evidence receipt.

Proposed real receipt, pending A/C agreement: schema version, opaque session ID,
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

`python -m unittest discover -s tests -q`: **124 tests, OK, 30 skipped**
(the existing asset-dependent tests require `ZOMBIEEE_ORIGINAL_MODULE`). All
32 B fixture/CLI tests passed on Windows, including directory junctions and
read-only file-version inspection. Junction tests ran outside the restricted
sandbox because it denies junction creation; all fixtures stayed in temporary
directories. No real game process was launched or install attempted.

Independent read-only code review found a malformed Steam path could abort
structured discovery. Fixed normalization handling for invalid custom/library/
Steam roots and rejected control characters in install-directory names. The
regression preserves a valid candidate alongside corrupt inputs. Final full-suite
verification above includes that fix. Runtime and original-asset checks remain
pending; test counts do not certify a playable release.
