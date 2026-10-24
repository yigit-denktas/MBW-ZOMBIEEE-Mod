# Windows bootstrap: Agent B lane

Implements the B slices of issues #8 and #9. The current branch adds a complete
one-command Play City flow: discovery, pinned archive audit, reversible
build/install, validated rotation, recorder arming, owned dedicated host,
loopback auto-join, stop-after-client-exit, artifact sealing and manifest
verification. It is **implemented and offline-tested only**: no real WSE2
startup, installation, auto-join or City wave has been demonstrated in this
branch, no desktop shortcut is wired, and D owns the sealed runtime validation.
No ledger leaf is accepted by these tests.

## Use

From the repository root, with Python 3.10+ available as `python` (or `py -3`):

```powershell
python -m launcher.discovery
python -m launcher.discovery --steam-root 'D:\Steam Library' --custom-path 'D:\Owned Game' --custom-path 'D:\Local Tools\wse2_launcher.exe'
python -m launcher.discovery --no-known-folders --custom-path 'D:\Owned Game'
python -m installer.manifest --game-root 'D:\Owned Game' --archive 'D:\Downloads\ZOMBIEEEBeta04.rar' --transaction-id review-01
python -m installer.manifest --game-root 'D:\Owned Game' --archive 'D:\Downloads\ZOMBIEEEBeta04.rar' --transaction-id audit-01 --audit-archive-hash
python -m unittest discover -s tests -v
```

The paths above are examples, never defaults. `--steam-root` names a Steam
directory containing `steamapps`, not the `steamapps` directory itself. The
API `discover(steam_roots=(), custom_paths=(), known_roots=())` scans only its
explicit inputs; the CLI additionally reads environment-derived Program Files
folders and optional Steam registry hints. WSE2 needs no assumed registry key.
No whole-drive scan, downloads, candidate execution or install writes occur.
Python may create its ordinary bytecode cache in the source checkout; it can
be disabled with `python -B`. Local JSON contains local paths and must remain
private; it is not a public diagnostic bundle.

## Discovery JSON v1

`candidates` contains Warband roots and `wse2_candidates` executable paths.
Each entry has `path`, `executable`, `kind`, `status`, `confidence`,
`engine_version`, `version_status`, `ownership`, `runtime_verified`,
`provenance` and `blockers`.

- `found` means a file passed MZ/PE header sanity checks. It does not certify
  executable integrity, ownership, complete game data or ability to run.
- Confidence is `medium` for that limited evidence, otherwise `none`.
- `engine_version` is a Windows fixed file-version resource when available;
  `version_status=file_resource_only` explicitly limits that observation.
  Missing metadata or a non-Windows inspection produces `null` / `unknown`.
  A WSE2 filename/resource does not establish its release or compatibility.
- Ownership remains `unknown`. A Steam appmanifest is provenance, not proof
  of an entitlement or a complete installation. No DRM is inspected or altered.
- Failed paths are retained with `missing_executable`, `unreadable_executable`
  or `invalid_pe_header`; they never become found candidates.
- `ambiguity` covers multiple valid game roots or WSE2 executables. `selected`
  is the single Warband root, if any; it does not select or pair WSE2. Explicit
  user selection is required when `selection_required` is present.
- Missing optional manifests are normal. Malformed, oversized, inaccessible
  inputs and bounded-search truncation appear in `warnings`. Search is limited
  to 512 entries and three directory levels per supplied root, skipping links
  and Windows reparse points. Supply a direct WSE2 path if discovery truncates.

Steam discovery supports modern and legacy `libraryfolders.vdf`, the Warband
appmanifest (48700), a known common-directory name and custom paths. Duplicate
normalized roots merge their provenance. WSE2 filenames containing `wse2` are
only hints; unexpected nested layouts are inspected within the stated bound.
An unknown renamed executable needs further integration work.

CLI exit code is 0 for one unambiguous Warband candidate and 2 otherwise.
Always inspect JSON blockers, including `wse2_not_found`; exit 0 is not a
readiness verdict. The planner always emits a proposal and does not execute it.

## Install manifest and recovery design

`plan_install(game_root, archive, transaction_id)` emits schema v1 with:
`dry_run=true`, `execution_enabled=false`, `consent_required=true`, operation,
input paths, stage/target/backup/journal paths, `build_argv`, blockers, ordered
steps and rollback intent. Transaction IDs permit only 1–64 ASCII letters,
digits, underscores and hyphens, beginning with a letter or digit. Existing
transaction paths, redirected destinations, invalid game EXEs and missing
archives block the proposal. Permissions/free space/process locks are not
probed by writing and must be revalidated by the eventual installer.

`input_game_root` retains the absolute lexical input before resolution;
`game_root` is the resolved preview. `path_issues` records symlink/reparse or
inspection failures in the raw root, every ancestor, executable and all module/
transaction destinations, including the journal. Junctions cannot disappear
from evidence through early resolution. Parent traversal is blocked separately.
Every later `exists()`/`is_dir()`/`is_file()` probe is guarded too: Windows
access denials can surface from `stat()` after a lexical check succeeded, so an
inspection failure adds `path_inspection_failed` and `path_issues` evidence
instead of aborting the JSON proposal. `operation` is `unknown` when the
installed-target probe cannot be inspected, and `archive_missing`/
`warband_invalid` are never inferred from an unreadable path.
`recheck_required_before_write=true` is unconditional: an offline path check
cannot prevent a later filesystem race. A real installer must recheck through
owned handles immediately before every write, rename, recovery or removal.

The builder argv uses the current Python interpreter and existing
`tools/build.py --archive ... --out ...`. Invoke as an argv list with
`shell=False`, never a joined shell string. The output is a new
`Modules/.zombieee-stage-ID/ZOMBIEEE_Remaster`, never the live target, and
`--replace` is not supplied. Archive digest, 7-Zip integrity, extraction and
compiled module validation remain the existing builder's responsibility.
By default the archive is not hashed and `archive_digest_unverified` remains a
blocker. `--audit-archive-hash` consumes Agent A's `tools/archive_audit.py` as a
read-only subprocess with `--archive ... --json`, without duplicating hash
policy. The tool is on A's branch and unavailable on the v0.1.8 base until
integration. An absent tool, invalid report, timeout or rejected identity remains
a structured blocker; only successful boolean `identity_ok:true` removes the
digest blocker. `archive_crc_unverified` remains because this invocation does
not request a 7-Zip member test. `archive_audit` and `archive_audit_argv` expose
these observations and the exact planned invocation. No builder process runs
in this slice.

Proposed transaction sequence, **not implemented**:

1. Display exact paths/actions, receive explicit install/update consent, verify
   owned inputs and the agreed Agent A build contract. Close related processes.
2. Re-resolve paths and reject links/reparse redirects, changed inputs and
   collisions. Acquire an exclusive transaction lock. Record a durable journal
   outside the module; use atomic journal replacement and flush it after each
   transition. Check available space and permissions without elevation by default.
3. Build into the fresh same-volume stage using the existing CLI. On failure,
   leave the original install untouched; retain bounded failure evidence.
4. Validate output and save a relative-file SHA-256 inventory. Journal intent
   before moving an existing target to its unique backup, then record success.
5. Rename staged module to target, validate it, mark committed and retain the
   backup until explicit cleanup consent. Individual same-volume renames are
   atomic; the pair is not one atomic Windows transaction. Antivirus and open
   handles can prevent either operation.
6. If activation fails after moving the old target, restore the backup. If
   rollback fails, preserve both trees and journal and report recovery required.
   On restart reconcile journal with filesystem inventory before any write.

Update/repair must compare the saved inventory and preserve user-modified or
unrecognized files, with conflicts shown before consent. Uninstall is a separate
consent operation: remove only installer-owned unchanged files, preserve user
data and backups, and never delete the game or WSE2. No recursive deletion of an
inferred directory is acceptable. Shortcut ownership needs its own receipt.
These are requirements for a later installer; this module cannot perform them.

## Fake solo state machine

`Session(route='dedicated'|'listen', endpoint='127.0.0.1', timeout=30)` models
alternatives, not a selected engine route. `handle(event, now, **data)` consumes
monotonic timestamps and returns action strings. It imports no process or
network APIs. `receipt()` is an in-memory simulation snapshot using Agent A's
provisional `zombieee.session.v1` envelope, with additive simulation/lifecycle
fields. Unobserved PIDs, versions, fingerprints, timestamps, exit codes and
evidence references stay null; outcome stays unknown. It is not an on-disk
session log or proof of runtime evidence. Opaque UUIDs distinguish model
sessions and startup attempts; real process observations remain unimplemented.

| State/event | Result |
| --- | --- |
| idle/stopped/failed + start | request recorder only; enter waiting_recorder |
| waiting_recorder + process_started(recorder) | record simulated owned identity; still wait |
| waiting_recorder + valid recorder_ready | request host (dedicated) or client (listen); waiting_game_start |
| waiting_game_start + process_started(game) | waiting_host |
| waiting_host + host_ready | dedicated: request client, waiting_client_start; listen: awaiting_join |
| waiting_client_start + process_started(client) | awaiting_join |
| awaiting_join + joined | client joined; awaiting_mission, never playing yet |
| awaiting_mission + mission_entered | modeled playing |
| startup/join/mission state + deadline | timeout and stop requested processes |
| active + stop / unexpected process exit | stop client/host; retain recorder until both exit |
| stopping + confirmed game exits | stop recorder |
| stopping + confirmed recorder exit | stopped, or failed with retained error |
| fully stopped/failed + start | clean new attempt |

Async events require matching session/attempt IDs; started/exited events also
carry PID and process-start identity. Old attempts and foreign sessions are
ignored before they can affect timers or process tracking. Recorder readiness
must be the canonical `zombieee.recorder-ready.v1` marker: known recorder
identity and `watcher_id`, `log_offsets_captured`/`watcher_active` true,
`engine_ready`/`mission_ready` false, and a fresh adapter liveness confirmation.
A dedicated client spawn requires a second liveness confirmation.
Duplicate/stale readiness cannot start another process. `host_ready`,
`joined` and `mission_entered` are separate fake observations: host readiness
never means the player joined, and a join observation never means the City
mission was entered. Only `mission_entered` reaches the modeled playing state.

Late ready/join events cannot bypass deadlines. Late process-start acknowledgments
are tracked and stopped so cleanup can still confirm their exits. Duplicate stop
and exit acknowledgments are harmless. Retry is rejected while any previous
requested process remains. Spawn failure uses `start_failed`; `exited` requires
the previously acknowledged owned identity. If shutdown never acknowledges exit,
the model remains stopping: it does not claim success or kill unrelated processes.
See [the recorder handshake v1](WINDOWS_RECORDER_HANDSHAKE.md) and Agent A's
authoritative
[recorder lifecycle contract](https://github.com/yigit-denktas/MBW-ZOMBIEEE-Mod/blob/agent/a-city-engine/handoffs/RECORDER_LIFECYCLE_V1.md)
for exact fields, adapter responsibilities and the pending C integration gate.

Only literal loopback `127.0.0.1` is accepted, with fixed original City
`tbfc_invasion_4` and mission `multiplayer_iv`. This constraint does not prove
that any real engine can bind privately. There is **no real bind or auto-join**.
No firewall changes, public server identity, server-browser publication, network
port setup or anti-cheat changes occur. The existing sample server config is
unverified and must not be passed to a real engine as a privacy guarantee.

Before an OS adapter exists, Agent A must establish exact verified executable,
argv/config syntax, startup semantics, loopback-only bind and nonpublication,
readiness evidence, join mechanism and graceful stop protocol for each process.
The adapter must acknowledge recorder readiness before spawning game processes,
track only owned child handles, handle partial startup failures, enforce startup
and shutdown deadlines, preserve failed cleanup for retry and avoid blind kills.
Neither route is accepted from a fake readiness event.

## Recorder adapter and B/C interop

`launcher/recorder.py` implements B against Agent C's actual passive recorder
CLI: owned recorder child, fresh session/attempt/start IDs, recorder-only
control key, bounded per-session readiness marker with redirect rejection,
canonical marker validation, atomic HMAC-SHA256 attach/stop controls, exact
attachment acknowledgment, stop only after B's game children exit, and SHA-256
evidence-manifest verification. It never starts or kills a game process. See
[the recorder handshake](WINDOWS_RECORDER_HANDSHAKE.md) for the state contract
and limits.

Process-level interop fixtures run C's exact checkout (`agent/c-flight-recorder`
at `1119cca2568f6a3f9c18af4689568a814a7985f4`) and an expendable fake game child:

```powershell
$env:ZOMBIEEE_RECORDER_DIR = 'C:\path\to\agent-c-flight-recorder'
python -m unittest discover -s tests -p "test_windows_recorder.py" -v
```

Windows result on 2026-10-23: **14 tests, OK, 1 skipped** (symlink creation is
not permitted here); the eight interop cases cover ready→attach→stop with
verified evidence, forged HMAC rejection, premature-stop rejection then retry
after game exit, >2 MiB late fatal-log retention, recorder startup timeout,
recorder crash before readiness, recorder death after readiness,
crash→`telemetry.recovery` incomplete/unverified report, and the Win32
creation-FILETIME probe. Fake runs pass C's `--simulation` flag, so the receipt
records `simulation=true` and `game_runtime=unknown`. Full B suite with the C
checkout: **162 tests OK / 31 skipped**. Without a C checkout the eight process
cases skip explicitly. The control key is absent from every recorded file; C's
attachment ack is unsigned local control, so correlation/order is validated
rather than a MAC.

## Evidence and remaining gates

Fixture tests cover modern/legacy Steam libraries, spaces, missing/invalid EXEs,
unknown versions, corrupt/traversing manifests, duplicate/multiple installs,
bounded nested WSE2, inaccessible search, read-only operation, Windows junctions,
manifest staging/collisions, post-lexical access denials, canonical recorder
marker fields, recorder adapter interop, fake route readiness, crashes, timeout,
cleanup and retry. Windows version metadata is exercised on the running Python
executable without starting a candidate. Windows junction fixtures require a
process context permitted to create junctions; a restricted sandbox may deny them.

One real-machine read-only discovery run on a local Windows 11 Steam installation
returned one `found` Warband candidate (`confidence=medium`,
`version_status=file_resource_only`, ownership unknown) and three `found` WSE2
candidates with unknown versions, so explicit user selection is required. The
bounded scan reported `search_limit_reached` for the game directory. Only counts
and statuses are recorded here; no local paths or logs are committed, and no
candidate was executed.

Not demonstrated: verified WSE2 release/startup, atomic install/rollback under
Windows locks or crash/power loss, actual private binding, desktop shortcut,
real in-engine recorder attachment, automatic join or gameplay. One combined
final Windows session remains pending after A/B/C integration.

## Host stdout sealing and validated rotation (bug-fix pass)

- The passive recorder cannot capture another process's stdout. The launcher owns the host child via `launcher.host_session.HostSession`, which tees bounded stdout/stderr to `host_stdout.log`.
- After both game children exit and **before** `PassiveRecorder.stop_after_exit`, call `adapter.add_artifact(host_stdout)`. C hashes every file in the session directory at seal time, so the ZDB1 probe stream is then inside the verified manifest (issue #16).
- `launcher.rotation.build_rotation` is the single source of truth for the dedicated rotation: 1-based team numbering, positive second-team bot count, respawn/round fields, and the explicit generic-bot (Crazed Civilian) roster caveat. `Session.rotation_commands()` and `Session.receipt()['rotation_sha256']` expose it.

## One-command Play City (B launcher)

`launcher.play_city` is the owner-facing entry point. It composes the existing
B/C/A pieces instead of duplicating them: discovery + engine pairing
(`launcher/engines.py`), A's pinned archive audit (`tools/archive_audit.py
--verify-crc`) and builder (`tools/build.py`) with backup-first activation
(`launcher/install.py`), the validated rotation (`launcher/rotation.py`), C's
passive recorder adapter (`launcher/recorder.py`), owned host/client children
(`launcher/host_session.py`), and the lifecycle model (`launcher/solo.py`).

```powershell
# Read-only readiness report (no writes, no launch)
python -m launcher.play_city doctor

# Show the exact plan; the first run needs the owned Beta 0.4 RAR
python -m launcher.play_city plan
python -m launcher.play_city plan --rebuild

# The one command: install if needed, then play and record
python -m launcher.play_city

# Explicit variants
python -m launcher.play_city install        # build/backup/activate only
python -m launcher.play_city --no-install   # never touch the game tree
python -m launcher.play_city --max-minutes 90
python -m launcher.play_city rollback --receipt '<evidence-root>\install-receipt-<tx>.json'
```

Optional flags: `--game-root`, `--client-exe`, `--dedicated-exe`
(`mb_warband_wse2.exe` / `mb_warband_wse2_dedicated.exe`), `--archive`
(repeat only when selecting explicitly), `--evidence-root`, `--steam-root`,
`--custom-path`, `--no-known-folders`, `--json`, and the timeout flags.
Bare invocation defaults to `play`; `play --rebuild` forces a fresh build.

### Flow (fail-closed at every step)

1. Discovery and pairing: exactly one owned Warband root and its WSE2 client +
   dedicated executable; ambiguity is a blocker, never a guess.
2. Install **only when the City module is missing or fails structural checks**
   (or `--rebuild`). A's read-only audit pins the original RAR4 SHA-256 and runs
   the 7-Zip member CRC. The builder runs into a fresh same-volume
   `Modules/.zombieee-stage-<tx>/ZOMBIEEE_Remaster`; its own
   `ZOMBIEEE_REMASTER.json` receipt is checked (`city-only`, 31 triggers,
   original 25, `runtime_verified=false`, probe prefix) and the module is
   digest-verified before an existing target is renamed to
   `Modules/ZOMBIEEE_Remaster.backup-<tx>`. Nothing is deleted; a journal is
   written before each transition. Activation or digest failure restores the
   backup; if restore itself fails, both trees are retained and the receipt says
   `recovery_required`.
3. Rotation: validated lines are written to the private launch directory and
   passed with `-r`; they are never written into the game tree or the repo.
   Because one-click City always builds/uses A's City defender profile, the
   default rotation requests A's **native team-0 allied squad** with
   `set_bot_count 1 8` (named default `DEFENDER_SQUAD_BOTS = 8`, 1-based
   rotation team 1 = telemetry team 0; A's roster patch maps faction 15 +
   `g_multiplayer_game_type==7` bots to survivor troops 981..984, so the eight
   native bots share the four clone troop types). Eight bodies are kept on the
   rear hold line and native refill replaces losses; four were observed wiped
   against the wave-1 horde. The size is a normal `--team0-bots N` parameter
   (alias `--team1-bots`), so tuning does not need another flag;
   `--stock-rotation` / `--team0-bots 0` keeps the stock zero-ally rotation
   for a module built without defenders. `build_rotation()` itself keeps its
   stock default; `build_defender_rotation()` is the explicit profile.
   Enemy staging is a separate validated option for the live wave/balance
   regression: `--enemy-profile generic` (default, 32 team-2 generic bots),
   `--enemy-profile weak-wave1` (a small staged wave-1 count, 8 generic
   team-2 bots) or `--enemy-profile native-only` (`set_bot_count 2 0`: no
   generic team-2 bots, only native wave visitors; the historical no-wave
   failure makes this an evidence-gated experiment). `--team2-bots N`
   overrides the count. Defender squad (`set_bot_count 1 8`), loopback bind
   and the sealed stop are unchanged. Plan and launch receipt record
   `enemy_profile` and `team2_bots`; e.g.
   `python -m launcher.play_city --enemy-profile native-only --max-minutes 3 --json`.
4. Recorder first: C's passive recorder is armed and must publish a canonical
   ready marker for this exact session/attempt/PID before any game child starts.
   The host is then started with a generated loopback-only WSE2 config
   (`bLoopbackServer=true`, `sServerAddress=127.0.0.1`, `iServerPort=7240`,
   RCON/OGP disabled), and the launcher waits for a read-only `netstat`
   observation of the owned host PID on exactly `127.0.0.1:7240`.
5. Auto-join: the owner's client is started with
   `--module ZOMBIEEE_Remaster --address 127.0.0.1:7240 --no-intro` and both
   owned PIDs are attached to the recorder. `joined`/`mission_entered` are
   recorded only when C's `ZDB1|` markers actually appear; a missing marker is an
   evidence gap, never a claim.
6. Stop: leaving the game (client exit) is the normal end of the session. The
   launcher stops the client, asks the host to `quit` with a bounded
   terminate/kill fallback, then copies `host_stdout.log` into the recorder
   session directory **before** the signed stop. C seals the bundle; the launcher
   verifies the SHA-256 manifest and renders `tools/diagnostics.py summary` into
   the launch directory. Ctrl+C performs the same owned shutdown.

Private evidence defaults to `local/session/play-city/` (gitignored):
`flights/<session>/` (sealed recorder bundle) and `launches/<session>/`
(rotation, loopback config, host/client stdout, `launch-receipt.json`,
`summary.json`). The WSE2 dedicated engine log is
`<game-root>/zombieee_play_<session>.log`; the launcher never deletes it. These
files contain local paths and must stay private.

### No-launch profile matrix planner (D)

`python -m launcher.play_city matrix` is the read-only planner for the AI/balance
validation loop. It starts no host, build or recorder, writes nothing, and prints
the exact expectations D should compare with the sealed bundle:

```powershell
python -m launcher.play_city matrix
python -m launcher.play_city matrix --enemy-profile weak-wave1
python -m launcher.play_city matrix --enemy-profile native-only
python -m launcher.play_city matrix --team0-bots 8 --team2-bots 8
python -m launcher.play_city matrix --expected-zombie-block stock   # task-34 target
python -m launcher.play_city matrix --json
```

It reports the requested team-0/team-2 counts, the exact `rotation.txt` lines and
SHA-256 (defender=8: generic `87c8d767…b6240`, weak-wave1 `eda8af7b…1c2d3`,
native-only `fbfb3d93…237e`), the expected wave-1 generic troop ids from the
installed build receipt (`894` only for A's weak roster), defender troop ids
(`981..984` for the balanced-ai clones), rear hold entries `[0, 1, 0]`, zombie
block mode (stock vs shield patch), map scope/trigger count and the launch
receipt fields D must assert. `expected.summary_paths` maps each assertion to
C's `zombieee.receipt-summary.v1` paths (`composition.team0.bots`,
`teams.bots_team0`, `defenders.troops`, `troops.team1`,
`waves.wave1.team1_classes`, `positions.team0.centroid`,
`defenders.guard_entries_reached` as a bounded cap-16 coarse proxy, top-level
`evidence_gaps`); `defenders.shield` is always `null` (no shield getter), so
the planner never encodes a shield expectation and reports block as
telemetry-unavailable. A pre-round-only sealed run legitimately shows
`waves.max=null` plus an `evidence_gaps` entry.

A's task-34 wave gating/refill receipt fields are covered too: the planner
reports `wave_visitors` (`slow` = every native wave slot 200..244 resolves to
the original slow Zombie 894, vs `original` 0.4 table) and the spawn_agent
defender refill (`defender_target` must match the requested team-0 squad size;
`defender_reinforce=false` means stock). Use `--expected-wave-visitors
slow|original` and `--expected-defender-reinforce default|stock` to match the
build D is validating. Mismatches between the requested profile and the
installed build are listed explicitly (e.g. `weak-wave1` on a full-roster
build, forward hold sectors, shield block when stock is expected, original
wave visitors, a refill target that differs from the team-0 count); unresolved
evidence is reported as gaps, never fabricated. Exit code is `0` only when the
plan is runnable, the installed receipt is readable and no mismatch was found.

The planner reads only `Modules/ZOMBIEEE_Remaster/ZOMBIEEE_REMASTER.json`; it does
not build, install or launch. `--expected-zombie-block default` accepts the
shield build and `--expected-hold forward` accepts forward sectors. Expected
values are not runtime evidence: the sealed summary still owns positions, wave
classes and wave completion.

### Installer maintenance: verify, repair and uninstall (ZOM-WIN-02)

The install receipt now carries the per-file SHA-256 **ownership inventory** of
the bytes the installer wrote. Maintenance commands compare the live module with
that inventory and never guess ownership:

```powershell
python -m launcher.play_city verify  --receipt '<install-receipt-<tx>.json>'
python -m launcher.play_city repair  --receipt '<receipt>' --from-module '<verified build dir>'
python -m launcher.play_city repair  --receipt '<receipt>' --from-module '<build>' --replace-modified
python -m launcher.play_city uninstall --receipt '<receipt>'
python -m launcher.play_city uninstall --receipt '<receipt>' --purge-owned
```

- `verify` is read-only and reports missing / modified / unrecognised files
  against the receipt (exit 2 when attention is needed).
- `repair` copies missing owned files from a module that still passes Agent A's
  static City checks; modified owned files are **preserved and reported** unless
  `--replace-modified` is explicit. Unrecognised user files are never touched.
  Repair refuses while a Warband/WSE2 process is running.
- `uninstall` is quarantine-first: the whole module is renamed to
  `Modules/ZOMBIEEE_Remaster.uninstalled-<tx>` and **nothing is deleted by
  default**. `--purge-owned` may then delete only owned, byte-identical files
  inside the quarantine; modified and unrecognised files remain, directories are
  kept, the game/WSE2 and the retained install backup are never touched. A
  game-process check blocks both repair and uninstall.
- Both actions write bounded journal/receipt files under the private evidence
  root; `verify`/`repair`/`uninstall` keep `runtime_verified=false`.

### Desktop control panel, settings and shortcut (ZOM-WIN-03)

- `python -m launcher.control_panel --print-actions` lists the desktop actions:
  Play Solo City, Settings/profile matrix, Open evidence/logs, Verify/repair,
  Uninstall (quarantine), Release checks. The Tk window is created lazily and
  only starts those documented CLI commands as child processes; it never
  launches the game directly or bypasses the launcher's checks.
- Private settings (`python -m launcher.play_city settings show|write
  [--settings <path>]`) store only non-secret launch defaults: `game_root`,
  `archive`, `evidence_root`, `enemy_profile`, `team0_bots`, `team2_bots`,
  `max_minutes`, `no_known_folders`. The file defaults to
  `%LOCALAPPDATA%\ZOMBIEEE\launcher-settings.json` (or repo-local `local/`);
  passwords, control keys, serials/tokens are refused, unknown safe keys are
  ignored with a warning, and the CLI always wins over settings.
- `python -m launcher.play_city shortcut [--output '<path>.lnk' --create]`
  inspects the shortcut spec by default (no writes). The target is
  `pythonw.exe -m launcher.control_panel` with the optional `--settings` path;
  creation is explicit, Windows-only, refuses to overwrite an existing `.lnk`,
  and passes values to a fixed PowerShell `WScript.Shell` script through
  environment variables only. The game is never the shortcut target.

### Release delivery checks (ZOM-REL-01 candidate gate)

```powershell
python -m launcher.release_gate
python -m launcher.release_gate --json --game-root '<Warband root>'
```

Read-only candidate gate: required delivery files exist, `VERSION` is
well-formed/consistent with the installed module receipt, the reproducible
commands (`launcher.play_city`, `tools/build.py`, `archive_audit`) are documented,
no proprietary archives/game executables/logs are tracked by Git, no local
personal install paths or obvious secrets appear in tracked text, and a supplied
installed module still passes the City structural checks with
`runtime_verified=false`. It also requires the release traceability record
(`docs/release-traceability.json` + `docs/RELEASE_TRACEABILITY.md`) to match
`VERSION` and the current CHANGELOG heading, with every non-blocked work item
linked to a PR/commit and every included PR covered. The report says
`delivery_status=candidate-checks-only`
and `acceptance=none`; it never claims a playable release, and owner review plus
D's sealed runtime evidence remain required. Missing runtime evidence is a gap,
not a pass.

### Truth boundaries

`summary.json` is C's sealed-bundle summary stored verbatim, not a launcher
interpretation. Its `no_player` flag reflects only the latest heartbeat window;
always read it together with the composition block (for example
`mode=human_present`) instead of treating that single flag as player absence.

All receipts keep `runtime_verified=false`, `outcome=unknown` and
`simulation=false`; `lifecycle_outcome`/`status` describe only the launcher's own
owned-process lifecycle (`clean_stop`, `failed`, `interrupted`). A verified
manifest proves sealed bytes, not gameplay. No public bind, firewall rule, port
forwarding, server-browser publication, anti-cheat change, serial key or upload
exists in this path, and only literal IPv4 loopback is accepted. A desktop
shortcut is intentionally **not** wired yet: D must first validate the real
flow with sealed evidence; until then the documented CLI is the interface.
Real WSE2 startup semantics, the generated minimal config and in-engine recorder
attachment remain runtime gates owned by D. The launcher's own loopback bind
observation is not proof that the engine cannot bind publicly.

### Offline evidence

`launcher.install` tests cover fresh install, backup-preserving update, build
failure, build-verification failure, locked activation with restore, unrecoverable
activation with retained trees, post-activation digest mismatch rollback, running
process refusal, explicit rollback and unsafe transaction IDs. `launcher.engines`
covers root/client/dedicated selection and ambiguity. `launcher.runtime` covers
the exact loopback netstat parse, bounded tails and deterministic waits.
`launcher.city_launch` drives the whole flow over injected recorder/process/clock
fakes: recorder-before-host-before-client order, loopback argv, rotation emission,
attach, join/mission markers, stop after client exit, artifact-before-stop,
manifest/summary results, and fail-closed cleanup for bind timeout, recorder
readiness failure, attachment rejection, recorder death and Ctrl+C. No game,
recorder subprocess or network probe is started by tests. Latest Windows result:
`python -B -m unittest discover -s tests -q` → **583 tests, OK, 112
skipped**; the B launcher/C-recorder interop cases run because C's recorder
is present in the merged tree. Launcher-only suites are green:
`python -B -m unittest discover -s tests -p "test_windows_*.py" -q` →
**194 tests, OK, 1 skipped** (includes the release-traceability, M2 maintenance, settings,
shortcut/control-panel and release-gate fixtures).

### Python 3.13 NUL-path regression

On Python 3.13, `os.scandir`/`open` raise `ValueError` (not `OSError`) for an
embedded NUL in a configured path. `launcher.discovery` previously let that
escape, aborting the whole structured report; it now records a bounded warning
and reports the candidate as `invalid_path`. Regression tests cover NUL search
roots, NUL WSE2 candidates and NUL Steam roots on both 3.11 and 3.13.


