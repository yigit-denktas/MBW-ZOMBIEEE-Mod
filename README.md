# ZOMBIEEE — Restoration & Remaster

Modernization of the **2012 ZOMBIEEE (Invasion) Beta 0.4** mod for *Mount & Blade: Warband*. Original contributors retain credit and ownership of their work.

**Current project version:** `0.1.1` (development scaffold; **not yet playable/engine-verified**).  
**Target:** Warband official 1.174 data format under [WSE2](https://github.com/Ruslan-700/WSE2-Releases/releases/tag/v1.1.5.4) 1.1.5.4 (14 October 2026).  
**Scope:** preserve the original guns, zombies, wave mode, maps and feel; restore current-runtime compatibility; add AI survivor teammates, defensible hold points, quality-of-life features, private cheats, and later LAN co-op. **ZOMBIEEE2 is explicitly excluded.**

## Requirements and local development

Obtain a legitimate Warband installation, your own original `ZOMBIEEEBeta04.rar`, 7-Zip and Python 3.10+. The source archive is **not** distributed here.

```powershell
py -3 -m unittest discover -s tests -v
py -3 tools\build.py --archive "C:\Downloads\ZOMBIEEEBeta04.rar" --out "C:\Games\MountBlade Warband\Modules\ZOMBIEEE_Remaster"
py -3 tools\doctor.py --module "C:\Games\MountBlade Warband\Modules\ZOMBIEEE_Remaster"
```

Install [WSE2](https://github.com/Ruslan-700/WSE2-Releases/releases/tag/v1.1.5.4) separately. Select `ZOMBIEEE_Remaster` in the launcher. The installer checks the original archive digest and 7-Zip integrity, stages a clean copy, applies a small overlay, and refuses to overwrite an existing installation without `--replace`.

## Project documents

- [Development roadmap](docs/ROADMAP.md)
- [Manual engine validation](docs/MANUAL_TESTS.md)
- [Provenance and redistribution](docs/PROVENANCE.md)
- [Engine target](docs/ENGINE.md)
- [Next development handoff](docs/NEXT_RUN.md)
- [Version history](CHANGELOG.md)

## Versioning and status

This project follows [SemVer](https://semver.org/). The historic original mod version `0.4` is **not** a remaster release number. `v0.1.0` identifies tooling and an initial compatibility target, not a working game. Milestone `v0.2.0` requires actual WSE2 startup and wave gameplay evidence. **No CI**; run local tests and capture manual gameplay results. The 0.1.1 preflight currently detects 64 entry points, 25 invasion triggers and 30/30 referenced BRF resources in the supplied original 0.4 archive; these are *static findings*, not a playable game certification.

## Attribution and licensing

Original ZOMBIEEE creators: Artizan, Nemerius, Belendor, BattalGaziTR, Hayalperest and Artintrex; see [PROVENANCE](docs/PROVENANCE.md) for OSP credits. [Original TaleWorlds discussion](https://forums.taleworlds.com/index.php?threads/wb-zombieee-invasion-we-need-your-advice.219327/).

**Original RAR content, Warband binaries, sounds, textures, models, scenes, and third-party OSP assets must not be committed.** There is no blanket license to redistribute the original material. No CI workflows or third-party executables belong here.
