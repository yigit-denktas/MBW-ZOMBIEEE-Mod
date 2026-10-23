# ZOMBIEEE recorder/launcher lifecycle contract v1

**Owner: Agent A · Integration interface · 2026-10-23**

This is a **pre-engine, local-offline contract** for Agent B (launcher) and Agent C (flight recorder). It does not establish that Warband/WSE2 supports a private host or unattended joining.

## Decided process ownership

- **B owns the host/client process lifecycle.** B discovers the licensed game/WSE2, builds the original City module using A's verified build CLI, starts and stops its *own* game child processes, and records actual process handles plus start identities.
- **C owns a passive local flight recorder.** C must start **before** the game, acquire the initial log offsets and write a durable readiness acknowledgment. In this mode C **does not launch, terminate or impersonate** B's game processes; it observes only IDs authenticated via B's private control channel.
- B must not launch any game child until a live C recorder for the matching session **and attempt** has acknowledged readiness. A timeout/failure to start recorder fails closed.

## Canonical handshake (aligned with Agent C's current proposed implementation)

B allocates an unpredictable opaque session ID and retry/attempt ID, an opaque recorder-start identity, and a **separate random 256-bit control key**. The key is passed to C through a *private per-child environment variable* `ZOMBIEEE_RECORDER_CONTROL_KEY`, not via command line, event log, build manifest or committed receipt. The local session directory must use per-user private permissions.

1. **Launch recorder only:** B spawns `python -m telemetry.flight_recorder --passive --output-root ... --session ... --attempt ... --recorder-start-id ... --log ...` in a local per-user directory; no Warband process yet. B owns the recorder process handle.
2. **Read readiness:** C creates `recorder-ready.json` *atomically* after setting session log offsets and initializing the watcher. The canonical schema is `zombieee.recorder-ready.v1` (hyphen), with `session_id`, `attempt_id`, `recorder_pid`, `recorder_start_id`, `watcher_id`, `log_offsets_captured=true`, `watcher_active=true`, `engine_ready=false` and `mission_ready=false`.
3. **Validate before game launch:** B checks the exact schema, current session/attempt/start identities, that `recorder_pid` equals B's *owned recorder handle* and remains live, valid ready booleans, local directory safety and startup deadline. **Do not trust an arbitrary PID or stale file alone.** Invalid/stale/duplicate markers, recorder exit, PID reuse ambiguity or timeout fail closed.
4. **Start owned local game:** B may request City host/client launch only after step 3, and only using an engine route which has separately passed the private bind/nonpublication and argv/config tests. If WSE2 launch syntax is still unknown, the OS adapter remains disabled and the tests use a fake game. `recorder_ready` is **not** `host_ready`, `client_joined` or `mission_entered`.
5. **Attach process identities:** B writes `recorder-attach.json` atomically using the same session/attempt/start identity and observed B-owned `host_pid`/`client_pid`, with an HMAC-SHA256 over canonical JSON using the private control key; C validates the message and writes `recorder-attachment-ack.json`. The recorder must never infer ownership from PID alone or derive the key from a public artifact. Attachment ack does not prove game startup.
6. **Observe actual game milestones:** Host process start, host-ready, client join, City mission entered, waves, NPC survival and zombie combat require separate recorded evidence. Until engine events are actually seen, emit `unknown`, not `passed` or zero. A simulated session is always `simulation=true`.
7. **Shutdown:** B stops its known game child processes only, waits for *both* exit acknowledgments, and then sends atomically written authenticated `recorder-stop.json` to C. C flushes the bounded tail/head logs and SHA-256 manifest before exiting. Unacknowledged shutdown retains a recoverable incomplete session rather than claiming success.

## Mandatory regression cases

- No game process is spawned before valid recorder-ready; wrong schema/session/attempt/start ID, stale readiness, dead/reused recorder PID, duplicate ready and timeout are rejected.
- Recorder crash before host start and crash immediately after ready; no false game-ready transition.
- Host-ready alone does **not** mean the client entered City; listen and dedicated paths need separate, engine-observed join evidence.
- Control attach/stop with invalid HMAC, wrong attempt, unowned PID, symlinked path and double-stop fail safely.
- C retains early startup **and late fatal** logs beyond the retention bound, with explicit omitted-byte accounting. A finished ZIP verifies each included file hash; privacy filters remain best-effort, requiring manual inspection before sharing.
- The final City module receipt records `experimental_map_scope=city-only`. The City structural validator `tools/city_acceptance.py` is read-only and does not establish runtime playability.

## Ownership and release boundary

Agent B changes `launcher/**` and `installer/**); Agent C changes `telemetry/**`, Lua and forensic pipeline; Agent A owns City patches, this contract, integration reviews and the Project Record ledger. Implementations in PRs #10/#11/#12 remain separate and **unmerged** until the offline interoperability tests pass. Do not add CI, proprietary binaries, remote data transmission, public networking or unapproved process killing.

This contract records the architecture; it does not certify private network binding, WSE2 startup or player gameplay. Owner prefers one consolidated Windows validation near release.
