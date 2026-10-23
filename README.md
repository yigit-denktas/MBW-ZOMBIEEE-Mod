# ZOMBIEEE — Restoration & Remaster

Modernization of the **2012 ZOMBIEEE (Invasion) Beta 0.4** mod for *Mount & Blade: Warband*. Original contributors retain credit and ownership of their work.

**Current project version:** `0.1.8` (development scaffold; **not yet playable/engine-verified**).  
**Target:** Warband official 1.174 data format under [WSE2](https://github.com/Ruslan-700/WSE2-Releases/releases/tag/v1.1.5.4) 1.1.5.4 (14 October 2026).  
**Scope:** preserve the original guns, zombies, wave mode, maps and feel; restore current-runtime compatibility; add AI survivor teammates, defensible hold points, quality-of-life features, private cheats, and later LAN co-op. **ZOMBIEEE2 is explicitly excluded.**

<!-- project-record:start -->
### Project record — City-first outcome and discovered work

| Measure | Evidence-gated status | Boundary |
| --- | ---: | --- |
| Original required City-release outcomes | **0/23 · 0.0% accepted** | The original 23 required leaf criteria remain unaccepted; the deferred five-map leaf stays optional. |
| Discovered supporting work <span aria-label="Discovered task">●</span> | **11/15 · 73.3% bounded complete** | Unplanned source bug fixes, hardening, audits and integration tasks; **not additional release credit**. Four still need current-revision verification. |
| Accepted outcome milestones | **0/5 · 0.0% accepted** | WSE2 City gameplay, durable Windows installation and owner release acceptance remain open. |
| Agent readiness | **L0 (provisional, not reassessed)** | Separately evidenced readiness, not derived from work completion. |

**Active outcome:** verified private City mission on Warband/WSE2 with survivor AI and a safe installer and recorder. **Scoped evidence:** B reports full original archive `7z t` CRC and pinned WSE2 1.1.5.4 client/host binary identity. A reports 149/149 local original-asset source tests. The first Windows City boot was announced on **older A/C revisions**, with no completed results posted at this observation. These observations do not establish playable waves, host networking or owner acceptance.

**<span aria-label="Discovered task">●</span> Discovered** means work absent from the original 2026-10-23 proposal; it is linked to an existing outcome and tracked in a **separate denominator**. [Scope-change history](progress/scope-changes/2026-10-24-discovered-work.json) preserves the original [24-task snapshot](progress/snapshots/ledger-2026-10-23-original.json).

[Interactive tracker](https://yigit-denktas.github.io/MBW-ZOMBIEEE-Mod/) · [A/B/C allocation](progress/agent-handoff.md) · [Scoped overview](progress/overview.md) · [Ledger](progress/ledger.json) · [Readiness limits](progress/readiness-summary.md)

<small>Source observation 2026-10-24. Project Record proposal remains unapproved as a complete release baseline. The GitHub Pages branch was updated with this source; independent live-page/assistive validation of the new revision remains pending. No gameplay or release certification is inferred from a static source test.</small>
<!-- project-record:end -->

## Requirements and local development

Obtain a legitimate Warband installation, your own original `ZOMBIEEEBeta04.rar`, 7-Zip and Python 3.10+. The source archive is **not** distributed here.

```powershell
py -3 -m unittest discover -s tests -v
py -3 tools\build.py --archive "C:\Downloads\ZOMBIEEEBeta04.rar" --out "C:\Games\MountBlade Warband\Modules\ZOMBIEEE_Remaster"
py -3 tools\doctor.py --module "C:\Games\MountBlade Warband\Modules\ZOMBIEEE_Remaster"
py -3 tools\preflight.py --module "C:\Games\MountBlade Warband\Modules\ZOMBIEEE_Remaster" --json
py -3 tools\trace_calls.py --module "C:\Games\MountBlade Warband\Modules\ZOMBIEEE_Remaster" --json
```

Install [WSE2](https://github.com/Ruslan-700/WSE2-Releases/releases/tag/v1.1.5.4) separately. Select `ZOMBIEEE_Remaster` in the launcher. The installer checks the original archive digest and 7-Zip integrity, stages a clean copy, applies a small overlay, and refuses to overwrite an existing installation without `--replace`.

## Project documents

- [Development roadmap](docs/ROADMAP.md)
- [Manual engine validation](docs/MANUAL_TESTS.md)
- [Provenance and redistribution](docs/PROVENANCE.md)
- [Engine target](docs/ENGINE.md)
- [Next development handoff](docs/NEXT_RUN.md)
- [Original invasion bot-call reconstruction](docs/BOT_RECON.md)
- [Experimental allied defenders](docs/EXPERIMENTAL_DEFENDERS.md)
- [City tactical defence overlay](docs/CITY_DEFENSE.md)
- [Five-map defences and wave reinforcements](docs/FIVE_MAP_WAVES.md)
- [Tactical fallback, regroup and movement diagnostics](docs/TACTICAL_RECOVERY.md)
- [AI loadouts and solo-host assistance](docs/COMBAT_BALANCE.md)
- [Forensic recorder, private keys and difficulty](docs/FORENSIC_DIAGNOSTICS.md)
- [End-of-development diagnostics](docs/DIAGNOSTICS.md)
- [Version history](CHANGELOG.md)

## Versioning and status

This project follows [SemVer](https://semver.org/). The historic original mod version `0.4` is **not** a remaster release number. `v0.1.0` identifies tooling and an initial compatibility target, not a working game. Milestone `v0.2.0` requires actual WSE2 startup and wave gameplay evidence. **No CI**; run local tests and capture manual gameplay results. The original 0.4 preflight detects 64 entry points, 25 invasion triggers and 30/30 referenced BRF resources in the supplied original 0.4 archive; these are *static findings*, not a playable game certification.

## Attribution and licensing

Original ZOMBIEEE creators: Artizan, Nemerius, Belendor, BattalGaziTR, Hayalperest and Artintrex; see [PROVENANCE](docs/PROVENANCE.md) for OSP credits. [Original TaleWorlds discussion](https://forums.taleworlds.com/index.php?threads/wb-zombieee-invasion-we-need-your-advice.219327/).

**Original RAR content, Warband binaries, sounds, textures, models, scenes, and third-party OSP assets must not be committed.** There is no blanket license to redistribute the original material. No CI workflows or third-party executables belong here.

**Experimental 0.1.2:** append `--experimental-defenders 4` to the installer command for four allied survivor bots (allowed 1–8, default off). This adds one server-only mission trigger; no original 0.4 trigger is replaced. Static tests pass, but WSE2 runtime and AI behavior remain unverified. [Full guide](docs/EXPERIMENTAL_DEFENDERS.md). No CI.

### No intermediate playtesting required

Development continues with static analysis and automated local tests. When the **final integrated candidate** is ready, exit Warband after one private session and run:

    .\tools\Collect-Diagnostics.ps1 -WarbandRoot 'C:\Program Files (x86)\Steam\steamapps\common\MountBlade Warband' -Session final-solo

This creates a **local, redacted, hashed** evidence ZIP and Markdown diagnostic report. The bundle contains engine logs, mission lifecycle markers, agent counts (if WSE2 exposes them), module hashes and version data. It neither sends data externally nor asks for repeated testing. See [the diagnostics guide](docs/DIAGNOSTICS.md). **Windows gameplay remains unverified.**

### New experimental City positions (v0.1.4)

Three AI-mesh-derived City guard posts are placed in a **COPY** of the 2012 scene. A private defender squad is split into groups 5, 6 and 7 and receives server-authoritative hold-position orders only when the current map is City. Original 25 triggers and all original zombie entries remain intact. This option is disabled unless explicitly requested:

```powershell
py -3 tools\build.py --archive "C:\Downloads\ZOMBIEEEBeta04.rar" --out "C:\Games\MountBlade Warband\Modules\ZOMBIEEE_Remaster" --experimental-defenders 4 --city-guardposts
```

Normal build: 25 invasion triggers. Experimental allies: 26. Allies plus City defence: 27. **Offline compatibility verified against supplied scene and compiled mission data; Windows engine gameplay and AI behaviour remain unverified.** See [technical analysis](docs/CITY_DEFENSE.md).

### Experimental 0.1.5: all original maps + wave-aware reinforcements

The original `wave_number` global drives a *separate* server-side survivor top-up to the requested cap once per wave after wave 1. Survivors are counted only if alive, non-player, team 0, in reserved groups 5–7. All five maps now have opt-in navmesh-derived defence markers and map-scoped orders. Source RAR and original zombie waves remain untouched.

```powershell
py -3 tools\build.py --archive "C:\Downloads\ZOMBIEEEBeta04.rar" --out "C:\Games\MountBlade Warband\Modules\ZOMBIEEE_Remaster" --experimental-defenders 4 --all-map-defenses --wave-reinforcements
```

The mode is disabled by default. Expected compiled invasion trigger counts: original **25**, allies **26**, map defences **27**, with wave reinforcement **29**. Changes to `variables.txt` and every modified original map are fingerprinted in the final-session diagnostic bundle. Offline scene/mission integration passed; **in-engine behavior is not verified**. [Details](docs/FIVE_MAP_WAVES.md).

### Experimental v0.1.6 — tactical fallback and regroup

A further opt-in native controller counts **living non-player team-0 defenders in reserved groups 5–7** every three seconds. On one or fewer survivors, they are ordered back to the original survivor spawn. Once the squad has recovered to at least three through the existing wave-limited reinforcements, they regroup at the current map's navigation-mesh-derived guard posts. The separate thresholds prevent repeated order switching.

    py -3 tools\build.py --archive "C:\Downloads\ZOMBIEEEBeta04.rar" --out "C:\Games\MountBlade Warband\Modules\ZOMBIEEE_Remaster" --experimental-defenders 4 --all-map-defenses --wave-reinforcements --tactical-recovery

This option requires at least 3 defenders. The full variant contains **31** compiled invasion triggers and **1,222** globals; all 25 original triggers are retained. The default remains the unmodified original 25-trigger invasion. Final-session diagnostics now inspect real wave/tactical values, stalled waves, oscillation and optional defender movement samples when WSE2 exposes the required getters. **No gameplay is yet verified.** Read [the tactical recovery report](docs/TACTICAL_RECOVERY.md).

### v0.1.7 — optional AI loadouts and local solo assistance

Four appended AI-only troops can be enabled via `--defender-loadouts balanced-ai`, leaving all playable class records untouched. Wave reinforcements now rotate class by original wave number. `--solo-assist` adds a separate host-only, one-player/non-dedicated health-and-ammo refill trigger; it does not disable anti-cheat and is disabled by default. The complete optional build has 985 troop entries, 1,222 variables and 32 invasion triggers; baseline remains 981 troops/25 triggers. Gameplay remains unverified.

See [combat and solo assistance](docs/COMBAT_BALANCE.md) for full flags and limitations.

### v0.1.8 — Diagnosable private host commands and support difficulty

- `--private-commands`: one-player listen-host-only **Left Ctrl+F7** heal host, **Ctrl+F8** refill host ammo, **Ctrl+F9** heal/rearm reserved AI defenders. Adds auditable native command counters. Requires full tactical build; disabled by default and mutually exclusive with periodic `--solo-assist`.
- `--difficulty story|standard|hard|nightmare`: modifies survivor *reinforcement timing and fallback thresholds*, not original zombie HP or wave sizes. Requires `--wave-reinforcements` unless standard.
- WSE2 read-only Lua operation mappings for bounded defender weapon, ammo, kill-count and movement sampling. Offline forensic analyzer now includes crash/wave/team/combat/command leads, source hashes and an evidence matrix that distinguishes **observed** from **unknown**.
- Full private-command variant: **35 invasion triggers, 1,225 globals, 985 troops**, with 25 original triggers intact. This is **not a certified playable release**; a single final WSE2/Windows session will produce our integrated evidence.

[See the detailed forensic plan](docs/FORENSIC_DIAGNOSTICS.md).

**Release scope decision (2026-10-23):** City is sufficient for first solo release; the other four original maps remain a deferred expansion. Public tracker publication was requested and is handled separately through `gh-pages`, with live activation to be verified.
