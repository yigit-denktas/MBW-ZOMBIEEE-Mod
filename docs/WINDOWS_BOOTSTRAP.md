# Windows bootstrap: Agent B offline slice

Implements the first slices of issues #8 and #9 on v0.1.8. Discovery and install
planning are read-only. Solo orchestration is a pure simulation with a fake
process harness. **No game startup, installation, shortcut, auto-join or City
wave has been demonstrated.** No ledger leaf is accepted by these tests.

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
session log or proof of runtime evidence. `session_id=simulation-N` is local
to this model instance; a real adapter must allocate unique opaque IDs.

| State/event | Result |
| --- | --- |
| idle/stopped/failed + start | start recorder, then host (dedicated) or client (listen); wait for readiness |
| waiting_host + ready | dedicated: start client and wait for join; listen: modeled playing |
| joining + joined | modeled playing |
| waiting_host/joining + deadline | timeout and stop requested game processes |
| active + stop / unexpected process exit | stop client/host; retain recorder until both exit |
| stopping + confirmed game exits | stop recorder |
| stopping + confirmed recorder exit | stopped, or failed with retained error |
| fully stopped/failed + start | clean new attempt |

Late ready/join events cannot bypass deadlines. Duplicate stop and duplicate
exit acknowledgements are harmless. Retry is rejected while any previous
requested process remains. Fake start failures use an `exited` acknowledgement
for the requested process. If shutdown never acknowledges exit, the model
remains stopping: it does not claim success or kill unrelated processes.

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

## Evidence and remaining gates

Fixture tests cover modern/legacy Steam libraries, spaces, missing/invalid EXEs,
unknown versions, corrupt/traversing manifests, duplicate/multiple installs,
bounded nested WSE2, inaccessible search, read-only operation, Windows junctions,
manifest staging/collisions, fake route readiness, crashes, timeout, cleanup and
retry. Windows version metadata is exercised on the running Python executable
without starting a candidate. Windows junction fixtures require a process context
permitted to create junctions; the restricted Codex sandbox may deny them.

Not demonstrated: actual owned game discovery, verified WSE2 release/startup,
atomic install/rollback under Windows locks or crash/power loss, actual private
binding, desktop shortcut, real recorder integration, automatic join or gameplay.
One combined final Windows session remains pending after A/B/C integration.
