# ZOMBIEEE — Remaster & Preservation

A private, City-first compatibility rebuild of the 2012 **ZOMBIEEE (Invasion) Beta 0.4** multiplayer mod for *Mount & Blade: Warband* — built from a legally owned original archive, instrumented with a local flight recorder, and documented without overclaiming.

> **Status: not accepted as a playable release.** Runtime evidence now exists — native Zombie roster, native allied defenders, hands-off AI-vs-AI combat, wave 2 in a defender-heavy variant, and a live-validated `play_city` path — but the City release still sits at **0/23 required outcomes / 0/5 accepted milestones** with `runtime_verified=false`. Division/hold behavior, wave 3+/completion, combat feel, redistribution and public release gates remain open. Do not treat any build here as an accepted release.

## Scope

- **Engine target:** official Warband data format **1.174** under [WSE2 **1.1.5.4**](https://github.com/Ruslan-700/WSE2-Releases/releases/tag/v1.1.5.4).
- **Historical input:** *your own* 2012 `ZOMBIEEEBeta04.rar`; no original assets are distributed here.
- **First release scope:** the original **City** invasion (`tbfc_invasion_4` / mission `multiplayer_iv`) only. The other four original maps are deferred; the independent *ZOMBIEEE2* continuation is excluded.
- **Goal:** preserve the original guns, zombies, wave mode, maps and feel; restore current-runtime compatibility; then add survivor AI, defensible hold points, quality-of-life options and, later, private LAN co-op.

## What works today (offline only)

- **Deterministic build from your own archive.** `tools/build.py` verifies the pinned archive identity (size/SHA-256), runs a real 7-Zip integrity/extraction pass, stages a clean copy, applies a small reviewed overlay and refuses to overwrite an existing install without `--replace`. It does not modify or redistribute the original RAR.
- **City-only native variants.** Optional append-only patches add allied defenders, navmesh-derived City guard posts, once-per-wave survivor top-ups and a fallback/regroup controller. The original 25 invasion triggers are preserved byte-identically in default mode; each optional variant is statically validated and counted in the build receipt (`city_static_acceptance`, `city_final_acceptance`).
- **Read-only static verifiers.** Archive identity/CRC audit, compiled-mission preflight, City chain verification, doctor and round-lifecycle audit all run without starting the game.
- **Local flight recorder and diagnostics.** The recorder seals a hashed, redacted session bundle; `tools/diagnostics.py summary <attempt-dir>` verifies the manifest and reports what was actually observed, failing closed on tampering.
- **Windows discovery/rotation groundwork.** Offline discovery of owned Warband/WSE2 installs and a validated dedicated-host rotation builder, both exercised only against fake fixtures so far.
- **Offline regression suite.** See [Testing](#testing) for the current count on this machine.

## Runtime evidence (bounded, not release acceptance)

- No-player/dual-team AI spawn is sealed: 8 allied bots + 32 enemies with zero client; native Zombie roster **894..911** (873/874 absent).
- Native allied defenders **981..984** spawn (`bots_team0=4`) and move out of the spawn cluster; scripted-destination movement is proven, stable hold/guard-entry identity is not.
- **Wave 2** observed in the defender-heavy variant (`set_bot_count 1 8 / 2 4`, `player_respawn_as_bot 1`); stock squad runs max wave 1 due the native round reset.
- `python -m launcher.play_city` validated live three times: loopback-only host, join/mission observed, clean stop, verified 8-file sealed manifest.
- Sealed evidence and reproduce notes: `local/session/PLAYABLE_EVIDENCE.md`, `NIGHT_STATUS_D.md` (local, gitignored).
## What does not work yet

- **No accepted end-to-end release loop.** Launch/join/mission/stop works in the validated `play_city` path, but wave 3+/completion, stable squad hold/guard-entry identity, combat feel, installer/public release and redistribution gates are not accepted.
- **AI behavior is partially proven.** Native Zombie troops (894..911) and native defenders (981..984) spawn and fight; wave 2 is only observed in the defender-heavy variant (`set_bot_count 1 8 / 2 4` + `player_respawn_as_bot 1`), not in stock squad configurations. Division 5–7 adoption/hold is unobservable in this runtime; no wave-carryover patch is shipped.
- **Strict no-client cannot start a round.** The pure no-client run seals only the spawn/pre-round snapshot; AI-vs-AI combat evidence uses one **unattended client with zero human input**, not a literal player-less round.
- **One-click launcher is implemented and live-validated**, but there is no desktop shortcut, public installer/redistribution or release packaging yet.

## Prerequisites

You must supply, and keep private, everything proprietary:

1. A **legitimately owned** *Mount & Blade: Warband* installation using the official **1.174** data format.
2. Your own copy of **`ZOMBIEEEBeta04.rar`** (ZOMBIEEE Beta 0.4, 2012). It is **not** provided by this repository. Pinned identity: `167,493,071` bytes, SHA-256 `9be100ff41ce6f8ebadd4aa27377f70f402883fab271999a8cab8cc1da001d1e` (see [reference/ARCHIVE.txt](reference/ARCHIVE.txt)).
3. [WSE2 v1.1.5.4](https://github.com/Ruslan-700/WSE2-Releases/releases/tag/v1.1.5.4) installed separately. WSE2 is a third-party runtime, not an official release and not Bannerlord.
4. **7-Zip** available on `PATH`, since the builder performs the real archive integrity and extraction pass.
5. **Python 3.10+** as `py -3` (or `python`). The offline tooling and tests also run on non-Windows systems.

## Build

Paths below are examples only — never commit real local paths.

```powershell
# 1. Verify the archive identity and (optionally) its member CRC with 7-Zip.
py -3 tools\archive_audit.py --archive "D:\path\to\ZOMBIEEEBeta04.rar" --verify-crc --json

# 2. Build the current City tactical variant into your Warband Modules\ folder.
py -3 tools\build.py --archive "D:\path\to\ZOMBIEEEBeta04.rar" `
  --out "D:\Warband\Modules\ZOMBIEEE_Remaster" `
  --experimental-defenders 4 --city-guardposts --wave-reinforcements --tactical-recovery

# 3. Read-only static checks against the built module.
py -3 tools\doctor.py --module "D:\Warband\Modules\ZOMBIEEE_Remaster"
py -3 tools\preflight.py --module "D:\Warband\Modules\ZOMBIEEE_Remaster" --json
py -3 tools\verify_city_chain.py --original "D:\path\to\extracted\ZOMBIEEE" `
  --archive "D:\path\to\ZOMBIEEEBeta04.rar" --json
```

| Variant | Extra flags |
| --- | --- |
| Baseline original invasion (25 triggers) | *(none)* |
| City tactical core | `--experimental-defenders 4 --city-guardposts --wave-reinforcements --tactical-recovery` |
| Balanced AI-only loadouts | add `--defender-loadouts balanced-ai` (requires defenders) |
| Support difficulty | add `--difficulty story\|standard\|hard\|nightmare` (non-standard requires `--wave-reinforcements`) |
| Private host controls / solo assist | add `--private-commands` *(requires `--tactical-recovery`)* **or** `--solo-assist` — mutually exclusive |
| All five original maps (deferred scope) | `--all-map-defenses` instead of `--city-guardposts` |

`tools/build.py` refuses to overwrite an existing destination; move it aside or pass `--replace` only after taking a backup. The complete optional profiles are counted in the receipt and are **not** claimed playable.

## Testing

```powershell
py -3 -m unittest discover -s tests -v
```

Tests are offline and require **no game launch**. Set `ZOMBIEEE_ORIGINAL_MODULE` and `ZOMBIEEE_ORIGINAL_ARCHIVE` to your private extracted module and original RAR to enable the original-asset source tests; without them those tests skip explicitly rather than pass by default. There is **no CI** by owner choice.

Latest recorded run (2026-10-24, Windows 11, Python 3.11.9, rebased on `main` `3823168`): **410 tests discovered, 7 skipped, 1 error**. The error is a pre-existing Windows-only launcher bug (`test_windows_discovery…` passes an embedded-NUL path to `os.scandir`) and also fails on unmodified `main`; it is not caused by docs changes, but the suite must not be described as green until it is fixed.

## Run (target path — unverified)

The following is the intended private, local-only path. It has **not** been accepted; treat it as a design target:

1. Build or place `ZOMBIEEE_Remaster` in your Warband `Modules\` folder (step 2 above writes it there).
2. Launch Warband through **WSE2 1.1.5.4** and select `ZOMBIEEE_Remaster`.
3. Start the original City invasion locally: mission `multiplayer_iv`, map `tbfc_invasion_4`; keep the listener on loopback (`127.0.0.1`) and make no firewall, port-forwarding or public-server changes.
4. If you arm the recorder, keep the whole evidence bundle private and inspect it with `py -3 tools\diagnostics.py summary <sealed-attempt-dir>` rather than uploading it.

See [docs/MANUAL_TESTS.md](docs/MANUAL_TESTS.md) and [docs/INTEGRATED_CITY_ACCEPTANCE_2026-10-24.md](docs/INTEGRATED_CITY_ACCEPTANCE_2026-10-24.md) for the evidence gates a run must satisfy before anyone may call it working.

## Evidence and project record

- **Canonical Project Record ledger** (tracker branch): [progress/ledger.json](https://github.com/yigit-denktas/MBW-ZOMBIEEE-Mod/blob/project-record-setup-v041/progress/ledger.json) — 23 required City outcomes, 0 accepted; milestones 0/5; additional leaves are explicitly non-additive support work.
- **Public static tracker** (GitHub Pages, documented as observed in the tracker): <https://yigit-denktas.github.io/MBW-ZOMBIEEE-Mod/>
- **Integrated City acceptance ledger** (14 gates G00–G13, evidence classes and strict semantics): [docs/INTEGRATED_CITY_ACCEPTANCE_2026-10-24.md](docs/INTEGRATED_CITY_ACCEPTANCE_2026-10-24.md)
- **Diagnostics, recorder and sealed receipts:** [docs/DIAGNOSTICS.md](docs/DIAGNOSTICS.md), [docs/CITY_INCIDENT_V1.md](docs/CITY_INCIDENT_V1.md)
- **Ownership, permission and archive provenance:** [docs/PROVENANCE.md](docs/PROVENANCE.md), [reference/ARCHIVE.txt](reference/ARCHIVE.txt)
- **Open work:** [#5](https://github.com/yigit-denktas/MBW-ZOMBIEEE-Mod/issues/5) attribution/legal, [#6](https://github.com/yigit-denktas/MBW-ZOMBIEEE-Mod/issues/6) final-session evidence, [#8](https://github.com/yigit-denktas/MBW-ZOMBIEEE-Mod/issues/8)/[#9](https://github.com/yigit-denktas/MBW-ZOMBIEEE-Mod/issues/9) Windows launcher, [#13](https://github.com/yigit-denktas/MBW-ZOMBIEEE-Mod/issues/13)/[#14](https://github.com/yigit-denktas/MBW-ZOMBIEEE-Mod/issues/14) roster/rotation, [#15](https://github.com/yigit-denktas/MBW-ZOMBIEEE-Mod/issues/15) recorder read race. (`#16` sealing is closed; the live sealed-attempt gate is still open.)

**Evidence bundles never enter Git.** `local/`, `evidence/`, `*.rar`, `*.exe`, `*.dll`, `Modules/` and logs are ignored. The public repository contains tooling, documentation and tests only — no game assets, executables, serial keys, session logs or personal paths.

## Current status — 2026-10-24

- **Release reality:** City required outcomes **0/23**, accepted milestones **0/5**, `runtime_verified=false`. Every "done" item in the ledger is bounded support work, not release acceptance.
- **Observed (unsealed, Lead-reported)** on merged main `4c56242` with C's corrected probe: dedicated host loopback-only `127.0.0.1:7240`, `role=server`, `game_type=7`, `ready_for_spawn=1`; `set_bot_count 2 32` produced `team1=41`, `wave=1`. This is a candidate observation, not acceptance.
- **Open defects:** stable squad hold/guard-entry identity (division 5-7 adoption unobservable); wave 3+/completion and stock-squad wave 2; combat feel with the firearm profile; legal redistribution/public release gates. Native Zombie roster, native defenders, wave 2 in the defender-heavy variant and sealed ZDB1/play_city evidence are demonstrated but are not release acceptance.
- **Known original quirk:** repeated engine `SCRIPT ERROR: Invalid Faction ID: -1` is decoded as four trailing `faction_set_slot(-1, 200, …)` writes in the 2012 mission (trigger 14), byte-identical to the pinned original prefix. It is non-fatal and not proven causal; no gameplay patch is authorized.
- **Version:** project version `0.1.8` is a development scaffold. `v0.2.0` is reserved for an actual WSE2 startup + City smoke test, which has not happened. See [CHANGELOG.md](CHANGELOG.md), [docs/ROADMAP.md](docs/ROADMAP.md), [docs/ENGINE.md](docs/ENGINE.md).

## Attribution and permission

The original **ZOMBIEEE (Invasion) Beta 0.4** was publicly released in 2012 for the Warband community. Its team and credits below were verified from the **archived original TaleWorlds thread OP** (Wayback capture of 2023-10-08; permalink `…/threads/wb-zombieee-invasion-we-need-your-advice.219327/`, first post `/post-5251005`). The live TaleWorlds forum now blocks automated access behind Cloudflare.

**Original team (as listed in the OP):**

| Name | Role |
| --- | --- |
| **Artizan** | Scripter, 3D modeller (co-founder) |
| **Nemerius** (spelled *Nemeruis* in the OP) | Scripter, 3D modeller, textures, 2D art, sounds, music, map editor (thread starter, co-founder) |
| **Belendor** | Scripter |
| **BattalGaziTR** | Rigs, animations |
| **Hayalperest** | Scene prop 3D modeller |
| **Artintrex** | Research |

**OSP / third-party credits (same OP):** Shredzor's OSP, Arch3r's Invasion OSP, Modern Buildings OSP, Thel's OSP, Polished Landscapes, MatBerserker, Highlander, Revan Shan, Specialist, BattleOfValmy, Belendor, Shikimaru and the WTF clan.

**Permission record.** The repository owner personally knew the original ZOMBIEEE team and attests that the original TaleWorlds page explicitly allowed anyone to take and play the mod; this private, local preservation build is treated as authorized on that basis. That attestation is recorded in [docs/PROVENANCE.md](docs/PROVENANCE.md) together with the archived evidence and the list of what remains **unverified** — notably, no re-checkable free-reuse sentence was found in the archived thread pages, because the live page is bot-blocked.

**Redistribution is not implied.** The original RAR, its assets, Warband/WSE2 binaries and all third-party OSP content stay under their own terms and **out of this repository**. This project's own code and documentation are separate from the historical mod. If a public packaged release is ever considered, issue [#5](https://github.com/yigit-denktas/MBW-ZOMBIEEE-Mod/issues/5) tracks the per-asset provenance/permission work that must happen first.

**RAR readme note.** The distributed archive's top-level `Readme.txt` is the 2010 **Nirecotive** readme (*"This is Nirecotive mod. Made by Nireco"*), i.e. the ZOMBIEEE module was built on the Nirecotive multiplayer base. It is not a ZOMBIEEE credits file; see [docs/PROVENANCE.md](docs/PROVENANCE.md).

## Repository map

| Path | Contents |
| --- | --- |
| `tools/` | Build/install, archive audit, preflight, verification, triage and diagnostics CLIs |
| `launcher/`, `installer/` | Offline Windows discovery, rotation, host/recorder adapters and install planning |
| `overlay/` | The remaster module overlay (Lua probe, msfiles metadata) applied at build time |
| `telemetry/`, `handoffs/` | Recorder protocol contracts and agent/integration handoffs |
| `docs/` | Provenance, engine target, roadmaps, diagnostics and acceptance ledgers |
| `reference/` | Archive identity and source-verification reports |
| `tests/` | Offline regression suite (no game launch) |

## Notes on honest reporting

This project deliberately separates **source-verified**, **observed**, **unknown** and **failed** evidence, and forbids promoting one class to another. A static build receipt, a self-reported test count or a log line is not playability. If a run is incomplete, missing telemetry is reported as `unknown`, never as zero, pass or success.
