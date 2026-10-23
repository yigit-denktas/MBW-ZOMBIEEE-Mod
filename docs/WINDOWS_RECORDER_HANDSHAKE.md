# B/C recorder startup handshake v1

Agent A requested B-1/B-2 in PR #11 and C-2 in PR #12, then committed the
authoritative [recorder/launcher lifecycle contract v1](https://github.com/yigit-denktas/MBW-ZOMBIEEE-Mod/blob/agent/a-city-engine/handoffs/RECORDER_LIFECYCLE_V1.md).
B implements and tests the **consumer** side described here; Agent C owns
marker production, recording and diagnostics; Agent A owns the shared contract.
This is an **offline protocol and simulation model**: no real recorder/engine
adapter, private bind, auto-join or runtime acceptance is implied.

## Ownership and canonical schema

- **B owns** game host/client process lifetimes, their OS handles and start
  identities, plus the opaque session ID, attempt ID, recorder-start identity
  and a separate random 256-bit control key. The key reaches C only through
  the private per-child environment variable `ZOMBIEEE_RECORDER_CONTROL_KEY`
  and never appears in argv, logs, receipts or committed files.
- **C owns** a passive recorder: `--passive` takes no game PID and launches no
  game. Before B starts anything, C selects a unique private session directory,
  captures starting log offsets and establishes watcher persistence, then
  atomically publishes `recorder-ready.json`.
- Canonical schema is **`zombieee.recorder-ready.v1`** (hyphen), with:

```json
{
  "schema": "zombieee.recorder-ready.v1",
  "session_id": "opaque-session",
  "attempt_id": "opaque-attempt",
  "recorder_pid": 123,
  "recorder_start_id": "opaque-process-start-identity",
  "watcher_id": "opaque-watcher-token",
  "ready_utc": "2026-10-23T00:00:00+00:00",
  "log_offsets_captured": true,
  "watcher_active": true,
  "log_source_count": 1,
  "engine_ready": false,
  "mission_ready": false
}
```

A checked-in consumer fixture mirrors this marker shape in
[tests/fixtures/recorder_ready_v1.json](../tests/fixtures/recorder_ready_v1.json);
C owns the producing side and its own fixture on PR #12.

## Ordering

1. B creates opaque session and attempt IDs. `Session.handle('start')` requests
   **only** `start:recorder` and enters `waiting_recorder` with a deadline.
2. The adapter starts its owned recorder, keeps the process handle and start
   identity, and reports `process_started` with `process=recorder`, `pid`,
   `start_id`, `session_id` and `attempt_id`. This does not authorize game start.
3. C prepares the local output/session directory, captures log offsets and
   establishes watcher persistence. Only after these succeed does it atomically
   publish the canonical marker above.
4. B reads the marker from the exact per-attempt C output location, never a
   global search or a previous recording directory. The eventual reader must
   bound its input (proposed 16 KiB), reject redirected files/ancestors, and
   validate the schema, correlation IDs and types. It compares
   `session_id`/`attempt_id`/`recorder_pid`/`recorder_start_id`/`watcher_id`
   with its owned recorder child, verifies `log_offsets_captured is true`,
   `watcher_active is true`, `engine_ready is false` and `mission_ready is false`,
   and probes that same owned handle. The model receives the marker fields plus
   a separate adapter observation `recorder_alive=true`; liveness is **not** a
   claim C may self-certify in JSON.
5. Only a current, known, live and canonical recorder acknowledgment can request
   the first game process. B enters `waiting_game_start`, then accepts a
   correlated `process_started` acknowledgment before waiting for `host_ready`.
6. For dedicated simulation, a `host_ready` event with a fresh
   `recorder_alive=true` may request the separate client. A client
   `process_started` acknowledgment advances to `awaiting_join`. For listen
   simulation, the existing client/host process advances to `awaiting_join`
   after host readiness. A `joined` observation moves to `awaiting_mission`;
   only a separately observed `mission_entered` reaches the modeled `playing`
   state. **Neither route enters playing from host readiness or a join
   observation alone.** No WSE2 flags or actual readiness detection are defined
   by these fake events.
7. After game start B writes an HMAC-authenticated `recorder-attach.json` with
   the owned host/client PIDs; C acknowledges attachment. Attachment is not
   engine readiness and does not prove a mission started.
8. On shutdown B stops only its known game children, waits for both exits, then
   sends the authenticated `recorder-stop.json`. C flushes bounded logs and
   hashes before exiting. Unacknowledged shutdown remains recoverable and
   incomplete; the model never claims success or kills unrelated processes.

The process-start token must uniquely identify that recorder lifetime and be
agreed by B/C (for example a B-generated per-child nonce bound to its owned
handle and echoed by C). The adapter must also retain the OS creation identity
to prevent PID reuse. The fake tests use synthetic identities, not OS PIDs.
These tokens correlate events; they do not authenticate a public artifact.

## Model events and cleanup

Async `process_started`, `recorder_ready`, `host_ready`, `joined`,
`mission_entered`, `exited` and `start_failed` require exact
`session_id`/`attempt_id`; missing/mismatched IDs are ignored without changing
the current timer. `process_started` and `exited` carry `process`, `pid`,
`start_id`. `start_failed` names a requested process that never obtained a start
acknowledgment. Stop/tick/start are synchronous controls from B's owner, rather
than recorder messages.

The model rejects/ignores early, stale, duplicate, foreign-session or wrong-
identity readiness, including a marker with `engine_ready`/`mission_ready` true
or missing readiness booleans. A recorder start failure or startup timeout
cannot request a game. Recorder death after the acknowledgment stops any
requested games. Game/client startup failure follows the same cleanup ordering.
Late spawn acknowledgments are retained and immediately stopped, rather than
forgotten.

Stop requests client/host first and keeps the recorder until their exits are
confirmed. Then it requests recorder stop. A pending spawn cancellation must be
acknowledged with `start_failed`; a spawned process must report its actual
owned identity on exit. Retry requires all requested processes to be resolved,
uses a new attempt ID and ignores events from the previous attempt. Hanging
shutdown remains `stopping` and cannot silently report success or retry over a
live process. B/C still need to agree on a real graceful recorder-stop API and
how bounded shutdown failure is surfaced; no blind process kill is implemented.

## B adapter implementation

`launcher/recorder.py` (`PassiveRecorder`) implements the B side against C's
actual `python -m telemetry.flight_recorder --passive` CLI:

- Generates fresh opaque session/attempt/start IDs and a 32-byte control key;
  the key reaches only the recorder child through
  `ZOMBIEEE_RECORDER_CONTROL_KEY`. It is never put in argv, game environments,
  logs or receipts.
- Keeps the owned recorder `Popen` handle, its PID and the start identity.
  Readiness comes only from the exact private
  `<output-root>/<session_id>/recorder-ready.json`, read with a 16 KiB bound and
  symlink/reparse rejection from the private root down. Validation requires the
  canonical schema, session/attempt/start correlation, owned PID, non-empty
  `watcher_id`, `log_offsets_captured`/`watcher_active` true,
  `engine_ready`/`mission_ready` false, and a live owned handle.
- Writes atomic HMAC-SHA256 `recorder-attach.json` and `recorder-stop.json`
  using C's sorted compact ASCII canonical JSON. Attach accepts only B-owned
  game children, waits for the exact attachment acknowledgment
  (`attachment_accepted=true`, `game_ready=false`), rejects a pre-existing ack
  and a second attach, and refuses to stop while any attached game child is
  still running. Stop is sent only after those children are confirmed exited.
- Verifies C's `manifest.json` SHA-256 inventory after completion and returns
  the receipt/evidence summary. Recorder death at any point fails closed; only
  B's own recorder child may be terminated on failure, never a game process.

Limits: C's attachment acknowledgment is an unsigned local control file, so B
validates structure, correlation and ordering rather than a MAC; any same-user
local attacker is outside this offline model. The adapter starts no game and
does not claim host, join, mission or WSE2 readiness.

Interop fixtures (`tests/test_windows_recorder.py`) run unit checks always and
six process-level cases when an Agent C checkout is available:

```powershell
$env:ZOMBIEEE_RECORDER_DIR = 'C:\path\to\agent-c-flight-recorder'
python -m unittest discover -s tests -p "test_windows_recorder.py" -v
```

Without that variable, the interop cases skip with an explicit reason. The
process cases launch C's actual passive CLI and an expendable fake game child:
ready→attach→stop with verified evidence, forged-HMAC rejection, premature-stop
rejection and retry after game exit, a >2 MiB late fatal-log tail, recorder
startup timeout, recorder crash before readiness, and recorder death after
readiness blocking attachment.

## Contract and acceptance limits

The local receipt retains A's `zombieee.session.v1` envelope, adds model state,
attempt ID and recorder acknowledgment, and keeps `simulation=true`, runtime
fields null and outcome unknown. No evidence bundle, PID or timestamp is
invented from these fake actions.

A has confirmed the intended City-only build profile in PR #11:
`--experimental-defenders 4 --city-guardposts --wave-reinforcements --tactical-recovery`,
optionally `--defender-loadouts balanced-ai` after static checks, without
`--all-map-defenses`. The installed build receipt should contain
`experimental_map_scope=city-only`. This profile depends on unmerged A changes
in PR #10; B's baseline planner does not execute it against the v0.1.8 builder.
Real launch route, private binding, joining, marker production, authenticated
attach/stop and shutdown remain integration gates. No intermediate owner
gameplay test is requested.
