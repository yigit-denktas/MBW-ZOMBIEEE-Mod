# Agent C · PID reuse and recorder control — design review

**Status:** proposed coordination only. Do **not** change the shared v1 attach
wire protocol without Agent A / Agent B approval. Source branch: `agent/c-flight-recorder`.

## Threat model

A process ID is an OS allocation, not a permanent process identity. After a B-owned
host exits, the OS may reuse its PID for an unrelated program before the C
watcher checks `recorder-stop.json`. This can make a mere `alive(pid)` test
ambiguous. C never terminates a B-owned game or any externally attached PID;
a mistaken PID match could still contaminate forensic *status* or prevent
cleanup.

The authority to start/stop game processes remains **Agent B's owned process
handles**, not values read from C's private control JSON. HMAC ensures the
control message came from the holder of the per-attempt local key; it does not
prove PID ownership or prevent OS reuse. C's process probes are best effort,
not authoritative.

## Current additive implementation, no wire change

C measures a **local, private** process birth identifier on attachment:

- Linux: process-start clock ticks, `/proc/<pid>/stat` field 22. The parser
  handles spaces and closing parentheses inside process names.
- Windows: process creation `FILETIME` from a handle opened with
  `PROCESS_QUERY_LIMITED_INFORMATION` and `GetProcessTimes`.
- Unsupported OS/access denial/racy exit: **unknown**, never fabricated.

At signed stop, C compares a readable current identity to what was observed
when accepting attachment. If they differ, it marks `pid_start_identity_status:
reused_suspected` and **does not claim a clean stop**. An alive or
uninspectable process similarly blocks early stop. If the local identity
cannot be obtained, C reports `unknown`. Only the enumerated status appears
in the public allowlisted recorder JSON; **no PIDs, creation times or control
keys** are exported in the ZIP. C does not infer an external process exit
code from liveness.

**Residual uncertainties:** a child may exit before C first observes the PID;
an inaccessible creation-time query leaves a gap; a PID may be reused between
C's liveness and creation-time checks; Linux birth ticks alone are not globally
unique across boots. Therefore C cannot independently certify that an
attached PID was B-owned, or that all game processes have exited. Agent B's
actual owned handles and a correlated OS creation identity are required.

## Proposed backward-compatible v1 augmentation (NOT implemented)

After A/B approval, B may include optional HMAC-covered attach fields:

```json
{
  "schema": "zombieee.recorder-attach.v1",
  "session_id": "opaque-session",
  "attempt_id": "opaque-attempt",
  "recorder_start_id": "opaque-recorder-start",
  "host_pid": 12345,
  "host_start_identity": "windows-filetime:example-number",
  "client_pid": null,
  "client_start_identity": null,
  "mac": "<HMAC computed by B; never publish real value>"
}
```

Use **per-platform exact encoding** compatible with C's local probe. C would
compare these optional identifiers to the observed OS identity at attach and
stop and fail closed on mismatch. Older senders can omit the fields; the
receipt then explicitly says `unknown` rather than `verified`. The
HMAC signs the complete object including any additional fields, as it does
today. This does not change the canonical `zombieee.recorder-ready.v1`
marker or recorder ownership.

**Decision needed from Agent A + Agent B:** approve specific field names and
allowed values, whether Linux boot ID also needs to be included, and whether
a missing OS identity should block *attachment* versus only recording an
`unknown` status. Do not land this wire change on C alone.

## Fixture/testing boundary

Unit tests use fake Windows handles and synthetic Linux `/proc` records.
Test status alone does not prove exact Windows APIs or real Warband ownership.
The actual B adapter should pass a child handle/start observation to its state
machine and execute crash/retry tests without exposing OS identifiers in
shareable forensic evidence.
