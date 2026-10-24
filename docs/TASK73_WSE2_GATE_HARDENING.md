# Task-73 — WSE2 pinned-release and gate hardening (implementation plan)

Status: **plan/draft only**, no code or acceptance claim. PR #48 remains frozen at
`3b089d0`; this work is a separate branch after the integration batch and the
single metadata sync. No game launch.

Observed external facts (2026-10-24, GitHub release API): WSE2 release
`v1.1.5.4` publishes `WSE2.zip` with SHA-256
`118ed9517356a7016bfb911bccb600a3d95682407687ec0552fdc5acdb91f06a` and
`WSE2_Installer.exe` with SHA-256
`b358a41fb415eefac8668903f1f0849fda7186f2cc98269c2cfe8b7d916332aa`.
These are observations for pinning, not yet an owner-approved project pin.

Community patterns reviewed: upstream launcher auto-update/version UI and
extract-over-Warband distribution, module `postFX.fx` WSE2 compatibility,
user config under `Documents\Mount&Blade Warband WSE2\rgl_config.ini`, and
per-mod save handling. Sources:
[WSE2 Releases v1.1.5.4](https://github.com/Ruslan-700/WSE2-Releases/releases/tag/v1.1.5.4),
[community WSE2 guide](https://shichuibuluo.com/article/wse2_guide).

## 1. Pinned WSE2 release verification

Add a read-only `launcher/wse2_pin.py` (or extend `launcher/engines.py`):

- **Pin record** (checked-in JSON/constants): repository, release tag, asset
  names, asset SHA-256, source URL, observation date, x86/x64 scope, owner
  approval state. The pin is updated manually from the release API; the gate
  never silently follows a new release.
- **Archive verification:** SHA-256 of the downloaded `WSE2.zip`/installer
  against the pin; mismatch/unknown → blocker for a sealed run.
- **Installed-file verification:** derive expected launcher/client/dedicated
  file hashes from the pinned archive manifest and compare against the installed
  Warband root (`wse2_launcher.exe`, `mb_warband_wse2.exe`,
  `mb_warband_wse2_x64.exe`, `mb_warband_wse2_dedicated.exe`, required DLLs).
  Mixed/stale/partially-extracted installs fail closed.
- **Auto-update guard:** launcher version/update state is informational. For an
  evidence run, detect a version/update change since harness start and refuse to
  label the run pinned; never update during a sealed run.
- **Receipt/evidence fields:** `wse2_release_pin` (tag + asset digest + source +
  observed date), `wse2_installed_hashes`, `wse2_pin_verified`,
  `wse2_pin_problems`, `runtime_verified=false`. Unknown stays `unknown`, never
  zero/pass.
- **Tests (offline):** fixture archive/manifest with good and mutated hashes,
  missing files, mixed x86/x64, stale-install fixture, auto-update-detected
  fixture; assert blocker/warning/gap semantics.

## 2. Layout and config isolation

- **Required layout check:** pinned extract-over-Warband files present; client
  and dedicated binaries both from the pinned release; no foreign module root,
  Steam Workshop module path, or duplicate `Modules/ZOMBIEEE_Remaster` tree.
- **Module scope:** City module build stays under `Modules/ZOMBIEEE_Remaster`;
  the launcher never copies the module into the game root or Documents.
- **User config isolation:** never bundle, overwrite, copy or read
  `Documents\Mount&Blade Warband WSE2\rgl_config.ini`; generate only the private
  per-session `server-config.ini` under the evidence launch dir. Evidence
  manifests exclude Documents, saves, user logs, browser/Steam data.
- **Log handling:** private WSE2/engine logs stay local evidence; no absolute
  user paths in tracked files or receipts intended for sharing.
- **Tests:** fixture roots with/without workshop/foreign modules, config
  presence, duplicate module trees, path-redirection/NUL cases; no writes outside
  the private evidence dir.

## 3. Spectator screenshot-manifest checks

New validation rule: every in-game run captures **start / mid / wave / end**
spectator screenshots. The launcher cannot capture or key-drive screenshots
(WSE2/Warband expose no input/presentation key API; same limit as #43), so the
operator or D captures them and the gate validates the manifest, not pixels.

Proposed manifest schema `zombieee.spectator-screenshots.v1`:

```json
{
  "schema": "zombieee.spectator-screenshots.v1",
  "schema_version": 1,
  "session_id": "<hex, matches launch/recorder session>",
  "captured_utc": "<ISO-8601>",
  "capture_mode": "operator|automation",
  "screenshots": [
    {"phase": "start", "file": "start.png", "sha256": "<hex>",
     "captured_utc": "<ISO-8601>", "reviewer": "<name>",
     "review_note": "<short observation>", "verdict": "reviewed-matches"}
  ]
}
```

Checks (fail closed / gap as appropriate):

- exactly one entry each for `start`, `mid`, `wave`, `end`; no duplicates;
- files exist under the private evidence root, extensions `.png`/`.jpg` only,
  SHA-256 matches the file; session id matches the launch/recorder session;
- `reviewer`, `review_note`, `verdict` present; `unreviewed`/missing verdict is
  a **gap**, never treated as validated;
- screenshots are private evidence; manifests may be shared only after path
  review; the gate does not judge visual truth and never grants acceptance
  from screenshots alone.

Tests: fixture manifest good/missing phase/duplicate phase/hash mismatch/session
mismatch/unreviewed/extra file; assert gap vs blocker distinctions.

## 4. Integration and rollout

- Wire the read-only checks into `launcher/release_gate.py` and, where relevant,
  `play_city doctor`/install plan warnings; keep `candidate-checks-only`,
  `acceptance=none`, `runtime_verified=false`.
- Ship in three small PRs after the batch + metadata sync:
  1. pin record + archive/installed verification + tests;
  2. layout/config isolation checks + tests;
  3. screenshot-manifest validator + tests/docs.
- Do not touch frozen PR #48 (fire-mode launcher surface); requested
  `fire_mode` remains launcher sidecar/`session.*`, observed telemetry remains
  `firearms.*`, mismatch diagnostic only.
- No public bind/firewall/serial/path leakage; no game launch in tests.

## 5. Open decisions (need Lead/owner)

- Approve the exact WSE2 pin (tag/asset/SHA-256) and x86 vs x64 scope.
- Offline pin update policy vs optional cached release-API check.
- Screenshot capture ownership (operator vs D automation) and where private
  evidence lives; whether the gate requires a reviewer identity.
- Whether the pin check is a release blocker or a warning until the owner locks
  the pin.

No acceptance, legal-clearance, runtime or publication claim is made here.
