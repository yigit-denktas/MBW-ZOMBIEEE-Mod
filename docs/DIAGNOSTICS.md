# End-of-development diagnostic recorder (v0.1.8)

**No step-by-step game testing required.** Continue development and local static verification normally. After the final build is ready, play one private WSE2 session, exit the game, and run the collector once. It packages evidence for later analysis rather than making you troubleshoot each intermediate build.

## What is recorded

- Versioned ZDB1 events written by the Lua overlay to WSE2's existing engine log: startup, compiled trigger count, hook registration, invasion mission entry, host/client role, total agent count and optional survivor team-0 / zombie team-1 counts when WSE2 exposes the team getter, and a heartbeat every 15 seconds (maximum 480). The probe is read-only.
- Up to 25 existing engine logs from WSE2/Warband game and Documents folders, plus explicitly supplied custom logs. Up to 8 MiB per log: on larger logs, the first 256 KiB and final ~7.75 MiB are retained with an explicit truncation marker, preserving startup and crash context. Source filenames and modification times are recorded.
- OS version/architecture, Python version, remaster version, source archive SHA-256, WSE2 target, experimental defender count, and installed module file SHA-256 hashes (without distributing mod assets).
- Session metadata, extracted events.jsonl, SHA-256 manifest, and integrity verification that rejects altered ZIP entries.
- Best-effort redaction of credentials, email addresses, IP addresses, Steam IDs and user-home paths. No unredacted logs, memory dumps or automatic uploads.

**Privacy limitation:** player names, chat, unusual identifiers and sensitive scene names might survive. Inspect the ZIP before sharing. Raw logs remain on your computer and evidence bundles are never uploaded automatically.

## One command, only at the end

After installing the game and final remaster, close Warband and run from the repository root on Windows:

    .\tools\Collect-Diagnostics.ps1 -WarbandRoot 'C:\Program Files (x86)\Steam\steamapps\common\MountBlade Warband' -Session final-solo

Produces timestamped local files under evidence/: ZOMBIEEE-evidence-*.zip and ZOMBIEEE-report-*.md. It does not launch Warband, install CI or send data over the network. If WSE2 uses an unusual log location, add -AdditionalLogs @('C:\path\to\custom.log').

For subsequent investigations, all offline:

    py -3 tools\diagnostics.py verify .\evidence\some-evidence.zip
    py -3 tools\diagnostics.py analyze .\evidence\some-evidence.zip --report .\evidence\report.md
    py -3 tools\diagnostics.py compare .\evidence\first.zip .\evidence\second.zip

Pass comparison ZIP paths explicitly, in chronological order. Comparison reports recurring, new and resolved error codes across builds.

## Analyzer rule catalogue

| Code | Meaning |
| --- | --- |
| R001 | Missing BRF/resource; inspect archive CRC and referenced assets |
| R002 | Fatal exception or crash; inspect nearby native log lines |
| R003 | Compiled script/operation error |
| R004 | WSE2 Lua failure |
| R005 | Missing texture, sound or other media |
| R010 | No logs to diagnose |
| R011 | Lua bootstrap event absent |
| R012 | No invasion entry despite bootstrap event |
| R013 | Mission entered but heartbeat absent |
| R014 | Wrong trigger count (25 original, 26 with defenders, 27 with tactical positions, 29 with wave reinforcements, 31 with recovery) |
| R015 | Logs older than seven days, potentially unrelated |
| R016 | WSE2 Lua diagnostic hook failed to register |
| R017 | Installed module manifest missing; cannot correlate build and runtime |
| R018 | Experimental allied team absent across sampled server frames while zombies exist |

**Conservative interpretation:** errors are evidence; an error-free report is inconclusive, not proof that zombies, friendly bots, waves, weapons, or multiplayer work. Final gameplay verification is still required once the implementation is complete.

Local tests: python -m unittest discover -s tests -v. No CI. Original Beta 0.4 only; ZOMBIEEE2 excluded.

## Team-count limitations

The mission probe uses WSE2's documented agent iterator. If the optional native team getter is unavailable, team0/team1 are reported as -1, **not zero**. The analyzer records team-data availability and never diagnoses missing allies from unavailable metrics. When at least two server-side samples show team 0 empty while team 1 is populated, it flags a *candidate* ally-spawn issue (R018), not a proven cause. Bot combat competence, navigation and wave victory still require the final game session.

The guarded installer also stores `archive_crc_verified`, `original_mission_trigger_count` and `final_trigger_count`. The evidence pack includes only allowlisted build metadata plus SHA-256 hashes of installed module files, so a later report can distinguish an unknown archive from a modified installation. None of the mod assets are included.

## Scene overlay receipt

The v0.1.4 installer records `final_trigger_count=27` if `--city-guardposts` is active. Original City data still has 226 objects; a patched copy has 229. The existing module fingerprint captures the modified `mission_templates.txt`, while the unmodified original archive remains untouched. Read the [City defence overlay](CITY_DEFENSE.md) for source-derived entry coordinates and offline checks.

## v0.1.5 build provenance

The collector fingerprints `variables.txt` (including the optional reinforcement sentinel) and all five original `SceneObj/scn_tbfc_invasion_*.sco` scene files in addition to the compiled mission, troop data, and Lua bootstrap. It does **not** package original game assets. The actual `final_trigger_count` is recorded by the installer for 25/26/27/29 variants. At final runtime test, compare the installed build fingerprint with that manifest before assuming the wrong code is running.

## v0.1.8 tactical and movement observability

The recorder now tries to read wave_number, g_round_ended, zdr_last_reinforced_wave and zdr_defence_mode from WSE2's documented game.gvar interface. If a global is missing, it records -1: not available. It emits a bounded heartbeat every 15 seconds, plus wave_change and tactical_change events.

Optional agent_sample records only reserved AI survivor divisions (5–7), when WSE2 exposes the necessary operation getter functions: agent ID, group, current tactical mode and rounded game-world X/Y. It records at most 16 bots per heartbeat. **This position function may be unavailable without WSE2 Module System headers**; missing samples are reported as unknown, not as a false stuck-agent diagnosis.

New analyzer rules: R019 candidate stalled wave (>=9 heartbeats on one wave while zombies remain), R020 rapid fallback/regroup oscillation, R021 apparent failure to regroup despite healthy-looking team-0 counts, R022 unusually stationary defenders *after* a tactical state change. These are conservative heuristics, never proof of causality. Static hold-position behaviour without a new order should not generate R022.

The full experimental build receipt records final_trigger_count=31 plus the tactical low/high thresholds. Original assets, executable and the RAR are still excluded from Git and from diagnostic bundles. [Tactical recovery design](TACTICAL_RECOVERY.md).

## v0.1.8 native command and AI combat forensics

A locally authored minimal `overlay/lua/msfiles/header_operations.py` maps only read-only Warband native getters that our WSE2 Lua telemetry uses. The runtime attempts `combat_sample` (agent/group/wave/known weapon ID/ammo/kill count) and `command_exec` events from native command counter increments, up to 16 non-player reserved-group defenders every 15 seconds. No real player coordinates or names are required. Unavailable native operations are recorded as unknown.

New offline codes: **R023** candidate ammunition depletion, **R024** prolonged engagement with no observed defender kill increments, **R025** hotkey execution inconsistent with build receipt, **R026** missing AI combat observability. The final JSON and Markdown reports include an **acceptance evidence matrix** for engine startup, mission entry, zombie waves, allied agents, combat activity, fallback/regroup and private commands. Unknown does not mean failed or passed. An error-free log is not proof of playability. [Full forensic reference](FORENSIC_DIAGNOSTICS.md).


## Agent C: external flight recorder (development prototype)

**Status: offline prototype on `agent/c-flight-recorder`; Windows/WSE2 integration not verified.** The recorder runs as a separate Python process, observes a subprocess launched with `--` or a pre-existing PID with `--observe-pid`, and independently stores atomic, bounded evidence snapshots. No game memory injection, shell execution, external telemetry or background uploads. It does not replace the final WSE2 session.

Run from the repository root. The following commands use a **fake Python game**, not an actual Warband invocation:

~~~powershell
py -3 -m unittest discover -s tests -p 'test_flight_*.py' -v
py -3 -m telemetry.flight_recorder --output-root .\evidence\flight --session fake-city --timeout 10 -- py -3 -c "import sys; sys.exit(7)"
py -3 tools\diagnostics.py collect --flight-root .\evidence\flight\fake-city --output .\evidence\fake-city.zip --session fake-city
py -3 tools\diagnostics.py verify .\evidence\fake-city.zip
py -3 tools\diagnostics.py analyze .\evidence\fake-city.zip --report .\evidence\fake-city.md
~~~

A real integrated session should pass existing WSE2/Warband log paths using repeated `--log` arguments. For Agent B's future launcher, pass its **optional** private per-user `zombieee.session.v1` JSON receipt with `--launcher-receipt`; only allowlisted fields are reproduced. This is an interface prototype, **not** a claim that automatic City launch or WSE2 flags work.

- **Recorder storage:** `evidence/flight/<session_id>/recorder.json`, `events.jsonl`, redacted `logs/log_XX.txt` and `manifest.json`, atomically written with SHA-256 digests over the actual redacted bytes.
- **Collection:** `diagnostics.py collect --flight-root <completed-session-dir> ...` verifies all recorder entries first, refuses a modified source, then carries the scrubbed snapshots plus their process receipt into the existing self-checked evidence ZIP.
- **Log window:** the recorder starts at the log files' current end (not historical prior-session text), polls without modifying the game, stores at most 12 logs × 2 MiB each, limits event records to 2,048 and records truncation. Each source preserves its early records plus a rolling late tail; omitted bytes are recorded in `log_omitted_bytes` and marked with `ZDB1-OMITTED ... BYTES BETWEEN HEAD AND TAIL`. A second size guard applies after redaction expansion. Capture still cannot prove every engine event was logged.
- **Process evidence:** owned-child exit codes are observed; a merely watched PID has **unknown** exit code. Timeout and startup failure are recorded separately. Per-process CPU, memory and FPS are **unknown**, not fake values; wall-clock duration is measured.
- **Privacy:** common credentials, home paths, IPs, email addresses and Steam IDs are redacted best-effort. `verify` additionally reports counts for *potential* remaining sensitive strings, never the offending values. It **always requires manual privacy review before any ZIP is shared**, even when all automated counts are zero. SHA-256 verifies accidental modifications, not provenance or proof that logs are safe.
- **Forensic leads:** R027 means external recorder timed out; R028 means an owned child exited nonzero. Neither is an automatic verdict of a Warband crash. Actual WSE2 Lua and game-run acceptance checks retain the `unknown` state until observed.

Run the full offline suite with `py -3 -m unittest discover -s tests -v` before review. These test files do not require original mod or WSE2 assets, and there is **no CI**.

## Agent A review hardening — C-1/C-2/C-3

- **Crash tail (C-1):** bounded early log plus rolling late tail, an exact per-source omission marker, and independent post-redaction output-size enforcement. Early startup and later crash signatures survive an oversized middle log segment. A clean recorder does not prove every game event was emitted.
- **Passive recorder handshake (C-2):** Agent B launches the separate recorder **before any game PID exists**. C waits passively and writes an atomic `recorder-ready.json` only after creating private session storage, capturing initial log offsets and entering the watcher. The canonical marker schema is **`zombieee.recorder-ready.v1`** (hyphen, not underscore). It includes opaque `session_id`, `attempt_id`, `recorder_start_id`, `watcher_id`, the local recorder PID, and booleans `log_offsets_captured:true`, `watcher_active:true`, `engine_ready:false`, `mission_ready:false`. Agent B must independently validate its owned recorder's PID, process start identity, liveness and freshness before starting the game; neither game nor City mission readiness is inferred from recorder readiness.
- **Authenticated attach/stop:** Agent B passes a random 32-byte control key to C in private environment variable `ZOMBIEEE_RECORDER_CONTROL_KEY` (64 hex digits; no key is persisted or forwarded to the game). B then starts the host/client and writes `recorder-attach.json` with `schema:zombieee.recorder-attach.v1`, the matching three identity strings, positive `host_pid` and/or `client_pid`, and `mac`. `mac` is HMAC-SHA256 with the control key over the JSON object excluding `mac`, serialized using Python `json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode("utf-8")`. C rejects stale/wrong attempts, invalid PID types and incorrect MACs; on acceptance it writes `recorder-attachment-ack.json` but never asserts that host, game or mission is ready. After both game processes have ended, B writes a similarly signed `recorder-stop.json` with schema `zombieee.recorder-stop.v1` to finish and seal C's evidence. All PIDs and control files stay local and do not enter the publishable ZIP.
- **Unsafe paths and child output (C-3):** verification and ZIP import reject filesystem symlinks and Windows reparse points including an intermediate `logs` directory. In **owned-child mode only**, stdout/stderr are drained on bounded threads, redacted, hashed, and annotated with separate source-omission and post-redaction omitted-byte counts. A process externally owned by B has no inferred stderr stream or exit code; use WSE2/host logs and B's local launcher receipt.
- **No real host flags guessed:** B's explicit private-local lifecycle and actual WSE2 startup are still unverified. Any insecure or public host route is out of scope.

### Passive startup example (standalone Python; no game launched)

```powershell
# Agent B generates a fresh random key and correlation ID for each attempt.
# The environment variable is PRIVATE to the C process.
$env:ZOMBIEEE_RECORDER_CONTROL_KEY = '<64 hex digits generated securely by B>'
py -3 -m telemetry.flight_recorder --passive --output-root '.\\evidence\\flight' --session city-attempt-1 --attempt attempt-1 --recorder-start-id '<opaque-id>' --log 'C:\\path\\to\\rgl_log.txt' --timeout 3600
```

Agent B owns the supervising process and writes authenticated control JSON from the same user account; the command above runs until a signed stop message or timeout. It **does not** launch Warband. B waits for `recorder-ready.json` before proceeding. When C finishes, `py -3 tools\\diagnostics.py collect --flight-root .\\evidence\\flight\\city-attempt-1 --output .\\evidence\\city-attempt-1.zip --session city-attempt-1` verifies and packages the local session without automatically uploading data.

### Offline validation scope

Regression files `tests/test_flight_recorder.py`, `tests/test_flight_review.py` and `tests/test_flight_passive.py` cover fake child crashes, late crash tails, bounded redacted subprocess output, handshake-first ordering, **true game-PID-free passive startup**, HMAC-authenticated attach/stop, stale-token rejection, unsafe symlinks, timeouts, and unknown observation states. A locally recreated Linux recorder/fixture mirror ran **16 focused tests with 16 passing**, plus one additional expanding-redaction assertion. The **exact GitHub branch full suite and collector integration tests remain unexecuted** because local GitHub DNS is unavailable. They are still required on an accessible checkout before merge. No Windows gameplay tests or CI were performed.

## Agent integration boundary

Agent B owns launcher and installer orchestration. Agent C owns this recorder and evidence processing, consumes B's optional local JSON session receipt without storing full paths, PIDs, command lines, chat or credentials in report outputs. Agent A owns the [provisional session contract](https://github.com/yigit-denktas/MBW-ZOMBIEEE-Mod/blob/agent/a-city-engine/handoffs/SESSION_CONTRACT.md) on its branch and must review any schema change. Only Agent A can declare a final WSE2 City result accepted based on objective runtime evidence, not these offline fixtures.

## Additional Agent C forensic hardening (Issue #6)

- **Read-only Windows PID liveness:** `windows_pid_alive` uses a Windows process handle with `SYNCHRONIZE` and `WaitForSingleObject(handle, 0)` instead of POSIX-style `os.kill(pid, 0)`. It never sends a Windows termination signal. Access denied or an unsupported state is *unknown*. Regression fixtures use mock handles, not a real game or Windows process.
- **Stop ordering:** the passive watcher does not seal evidence while any attached host/client PID is still seen alive or cannot be confirmed exited. An authenticated early stop remains retryable after process exit. This is an additional safety check, not a substitute for B's independently owned process handles or authority.
- **Large logs and rotated paths:** only the first truncation event per log is emitted to limit I/O; the final receipt retains exact `log_omitted_bytes` for each source. Regression cases cover rotation after startup and a credential split across polling intervals; redaction is best effort and manual ZIP inspection remains mandatory.
- **End-to-end fake B/C process test:** `tests/test_flight_b_interop.py` uses a separate C CLI process, validates the launch gate, rejects a bad HMAC, starts a B-simulated crashing host, refuses early shutdown, then checks the late fatal log and verified ZIP. This test is purely synthetic; it is **not** Agent B's actual launcher implementation or a WSE2 runtime test.
- **R029 scene/build mismatch:** the analyzer checks `experimental_map_scope=city-only` against a *measured* server-side `scene` field **if one is present**. When a scene getter is missing, the report explicitly says `unknown`. The mission-template field and B's intended City destination are never treated as proof of the loaded scene. A known explicit non-City scene produces a candidate mismatch with source/line evidence, not a gameplay verdict. No undocumented WSE2 scene getter has been added.
- **Process leads R027/R028:** findings now attach recorder-source timestamps and calibrated confidence that distinguishes local timeout/nonzero exit from an actual engine cause.

**Execution evidence boundary:** the reconstructed Linux C recorder mirror passed its existing 16 focused tests and another eight safety/process/rotation checks (24 passing, 0 failures/skips across these runs). These are *not* an execution of the exact remote branch. The new GitHub tests, complete `tools/diagnostics.py` suite, and Windows/WSE2 behavior still need validation on an accessible checkout. No CI or repeated manual gameplay sessions are requested.



## C recorder protocol/evidence follow-up (Agent A P0 review)

Agent B's newest `launcher/solo.py` at `69dd354` implements the canonical
`waiting_recorder` state **only as an offline state machine**; it is not an
executable process adapter. The next actual B+C acceptance fixture must launch
B's *real future adapter* with C's passive CLI, not merely duplicate C's
standalone B-simulated fake-host test.

**New source files:** `telemetry/identity.py` reads process birth identities
read-only (Linux `/proc/<pid>/stat` start ticks, Windows `GetProcessTimes`
creation FILETIME). This is C's best-effort local safety guard, **not** a new
v1 wire field or proof of B's process ownership. When a signed stop sees a
different start identity than it saw on attachment, C refuses to seal with a
clean stop and records `pid_start_identity_status=reused_suspected`.
Inaccessible OS identity is `unknown` in forensic output; no raw PID, process
birth time or control key is exported in the public ZIP. The proposed,
**unapproved** optional attach identity fields and residual OS race caveats
are documented in [PID_REUSE_REVIEW.md](PID_REUSE_REVIEW.md). Agent A and Agent B
must approve any shared schema extension before implementation.

**Simulated sessions:** pass `--simulation` to C's CLI, or
`simulation=True` when calling its Python API. The recorder JSON (and
attachment acknowledgment) then records `simulation=true`,
`game_runtime=unknown`; real host/game behavior remains unknown in every
recorder receipt until a separately verified engine session. Python/Windows
process *start* is not City mission start. The collector carries safe status
fields (but not the underlying OS process identity) into the diagnostic ZIP.

**Protocol fixture examples (all values synthetic):**
`tests/fixtures/recorder_ready_v1.json`,
`tests/fixtures/recorder_attachment_ack_v1.json`,
`tests/fixtures/recorder_completion_v1.json`, and
`tests/fixtures/recorder_incomplete_v1.json`.
The readiness marker's `recorder_pid=424242` is **an invented fixture PID**,
not anyone's process. The completion JSON is a small **illustrative subset**
of the full `recorder.json` schema, not a digest-verified real session.
Fixture examples do not contain actual HMACs, paths or game-owned PIDs.

### Recorder death / incomplete evidence

`python -m telemetry.recovery <local-session-folder>` performs a **read-only**
inspection of a private session. This is useful if the recorder crashes or
is terminated by the OS before it writes `manifest.json`. It returns a
path-free `zombieee.flight.recovery.v1` receipt:
`session_complete=false`, `integrity_verified=false`,
`shareable_without_review=false`, `game_runtime=unknown` and
`manual_privacy_review_required=true` for an incomplete session.
A present but invalid final manifest is also explicitly unverified.
It **does not** reconstruct missing events, fabricate a checksum, automatically
bundle or transmit sensitive logs, or mark a failed game test successful.
Its exit status is 0 only for a valid complete recorder session, 1 for
incomplete/invalid, and 2 for refused inspection.

**Current validation boundary:** these newer C source/test changes are
committed on GitHub but have **not** been executed against the exact remote
branch because Github DNS/network checkout is blocked in this environment.
Older recorder-mirror test runs are not accepted as current-branch evidence.
Run on a branch checkout: `python -m unittest discover -s tests -p
'test_flight_*.py' -v`, followed by `python -m unittest discover -s tests
-v`. Record exact revision/platform/pass/skip/failure counts and keep
original module data out of Git and any public bundle. No CI or intermediate
Windows gameplay test.


### Recorder event-journal cost bound

Event writes now append an individually flushed and fsynced line to
`events.jsonl` rather than atomically replacing the entire accumulated
journal on every event. This avoids quadratic write amplification across
up to 2,048 events. The per-run event count and `event_drops` remain explicit,
and the final manifest SHA-256 covers the complete finished journal. A hard
OS termination can leave an incomplete final line; the recovery inspector
reports the session as **unsealed**, never verified. This is a bounded
offline implementation change, **not an observed WSE2 performance claim**.

The current C source also contains tests for process birth-identity sampling,
PID reuse fail-closed shutdown, synthetic protocol fixtures, recorder death
inspection, and per-event append-only cost. These tests **require exact
GitHub branch execution** before PR #12 can be accepted. The latest B adapter
has independently tested an earlier C revision `eade015` on Windows; that
does **not** certify later C commits, so B/A should rerun the combined offline
suite against C's current head after reviewing new fields.


## City Incident Report v1 (Agent C P1)

`tools/diagnostics.py analyze <local-evidence.zip> --report <local-output.md>`
now returns `city_incident` (schema `zombieee.city-incident.v1`), in
addition to the existing R001–R029 rules and acceptance matrix.

This new read-only layer separates source-receipt **claims** from actual
runtime observations, correlates scene/wave/defender/tactical markers within
each log, and summarizes recorder startup, rotation, bounded omissions,
abnormal exits and build inconsistencies as noncausal investigation leads.
The observed historical invasion initializer is **game type 7** in the
updated Agent A source contract; a source assertion is not proof that a
live session entered the City mission. Existing absent or negative getter
values stay **unknown**, never zero.

It stores **two distinct timeline lanes**: ZDB1 source/line ordering (within
a log source only) versus C flight-recorder UTC timestamps. No fabricated
cross-source timestamp or game success. Log excerpts, arbitrary event
strings, local paths, control keys and PIDs are not copied to this summary.
The collector exports only summaries of A's `city_static_acceptance`
and `city_final_acceptance` receipts; even an all-green installed receipt
only sets `source_receipt_claims_passed=true` and
`independently_reverified=false`, not authenticated source provenance.

Details and reproduction commands:
[City Incident Report v1](CITY_INCIDENT_V1.md). Added 13 synthetic test
methods across `test_flight_city_incident.py`,
`test_flight_city_privacy.py`, `test_flight_city_limits.py`. These are
**committed, not reported as executed** until B/A complete an exact checkout
run. No CI, public network, copyrighted assets or repeated owner tests.
