# Runtime target and evidence

- Licensed Mount & Blade: Warband data format: official stable 1.174.
- Current target: [WSE2 v1.1.5.4](https://github.com/Ruslan-700/WSE2-Releases/releases/tag/v1.1.5.4), released 2026-10-14.
- Historical input: ZOMBIEEE (Invasion) Beta 0.4 compiled Warband module.
- WSE2 Lua documentation: https://github.com/Ruslan-700/WSE2-Releases/blob/master/Warband/WSE2%20SDK/luaGuide.html

WSE2 is a third-party modified runtime, **not** a successor official Warband game release and not Bannerlord. The target version is pinned for reproducibility and may be updated after regression testing.

The old mod's Python `module_*.py` source was not included. Prefer reversible overlays, Lua instrumentation and selective reconstruction. Mod compatibility with WSE2, scene loading, actual bot spawning and wave completion remain **unverified** until recorded in Windows gameplay evidence. Do not infer performance benefits solely from the engine's changelog.

## Agent A: original archive + compiled native preflight (offline evidence only)

The first integration slice adds `tools/archive_audit.py`, a read-only identity/CRC probe for the historical 2012 Beta 0.4 source. It checks RAR4 signature, file size and SHA-256 (pinned in `reference/ARCHIVE.txt`) without copying assets. Its `--verify-crc` mode runs an optional Windows 7-Zip member integrity test and **never extracts the RAR**.

```powershell
# Identity only (works without 7-Zip; not a full member CRC test)
py -3 tools\archive_audit.py --archive "C:\Downloads\ZOMBIEEEBeta04.rar" --json

# Full member CRC with installed 7-Zip. Returns status=verified only after exit code 0.
py -3 tools\archive_audit.py --archive "C:\Downloads\ZOMBIEEEBeta04.rar" --verify-crc --json
```

Machine-readable outcomes distinguish `identity_ok` from `crc_status: not_checked | verified | failed | unavailable | timeout | blocked_identity`. The output omits full filesystem paths and 7-Zip raw stdout. `tools/build.py` now uses the shared identity inspector before invoking the existing 7-Zip CRC/extraction sequence and stores the identity result in the installed build receipt. No game file or 2012 asset is published.

The mission preflight now also decodes the **complete compiled operation arities** for each condition and consequence, instead of trusting trigger header timing/count alone. This helps catch truncated native script bodies **before** attempting to start WSE2. It is still a static parser, not a validator of every native opcode's semantics.

**Evidence currently available:** the locally provided source archive matched RAR4 signature, expected 167,493,071 bytes and pinned SHA-256. A standalone copy of this preflight decoded the supplied partially extracted original `mst_multiplayer_iv` as 64 entries, 25 native triggers and 30/30 nonempty mod BRFs. Synthetic tests passed for invalid body arity, wrong archive hash/signature, missing 7-Zip and CRC error/timeout handling.

**Unverified and blocking:** a full original-member `7z t` run (7-Zip not available in this development container); a clean Windows 11 original extraction; actual WSE2 game boot, automatic hosting, agent behaviour and a completed City wave. These should be captured in the consolidated final Windows run rather than asserted from file parsing.

## City-first scope enforcement — Agent A, review branch

The owner chose **City only** for the first accepted solo release. The builder now supports the following *experimental static build profile* **without applying defence markers to any of the other four original scenes**:

```powershell
py -3 tools\build.py --archive "C:\Downloads\ZOMBIEEEBeta04.rar" --out "C:\Games\MountBlade Warband\Modules\ZOMBIEEE_Remaster" --experimental-defenders 4 --city-guardposts --wave-reinforcements --tactical-recovery --defender-loadouts balanced-ai
```

Three native-script boundaries now gate City-specific behaviour on the actual `scn_tbfc_invasion_4` scene ID:

1. **Initial survivor spawn:** `tools/patch_defenders.py` adds server/current-scene/City-match conditions to the one-time allied spawn when `city_only=True`. Its normal baseline/all-map trigger remains unchanged.
2. **Wave reinforcement:** `tools/wave_reinforcements.py` requires an actual City scene match before its wave-limited replacement handler can execute.
3. **Fallback/regroup:** `tools/tactical_recovery.py` now accepts either City-only or the prior five-scene map table, adding a City scene condition in the City-only variant.

`tools/city_defense.py` validates both the original server-only ally spawn trigger and the City-scoped variant without hardcoded operation indices. The original compiled 25 invasion triggers remain untouched. On a fully enabled City-first build, the experimental mission still has **31** triggers and the previous append-only `zdr_*` globals; it no longer needs `--all-map-defenses`.

**Preservation:** The remaining four original `.sco` files are neither edited nor required by City-specific patch functions. They still exist in the complete original archive; City-only is an **experimental gameplay-overlay scope**, not permission to redistribute or delete the original maps. Existing `--all-map-defenses` is backwards-compatible and separately gated.

**Additional evidence limit:** New `tests/test_city_only_build.py` stages just the original City scene with the compiled source tables and asserts City-gated spawn, reinforcement and recovery operations; verification must still run on a complete original installation and WSE2 before acceptance. Presence of these native condition tokens proves neither scene-loader execution nor working AI movement.

**Installer interface for Agent B:** Accept `--city-guardposts --wave-reinforcements --tactical-recovery` without requiring all maps. The build receipt includes `experimental_map_scope: "city-only"`, or `"all-original-maps"` for the legacy full variant. **Forensics interface for Agent C:** carry this recorded scope into the private evidence summary and compare it with `scn_tbfc_invasion_4` observations. Never infer actual gameplay from build flags.

## Offline City acceptance gate (Agent A)

A standalone read-only auditor now detects malformed City-only output **before** B's installer attempts to launch WSE2:

```powershell
py -3 tools\city_acceptance.py --original "C:\Path\To\OriginalZOMBIEEE" --module "C:\Games\MountBlade Warband\Modules\ZOMBIEEE_Remaster" --json
```

It decodes all compiled mission trigger bodies; requires **25 original native triggers preserved bit-for-bit as a prefix**, **31 total City-only experimental triggers**, native server and City scene guards on ally spawn (trigger 25), wave top-up (28) and tactical recovery (30); validates 1,222 append-only global variables and byte equality for the other four original invasion scenes. Missing non-City scene evidence is a failed gate rather than a claimed pass. This command only reads files and returns exit 2 on a failed structural check. A source-based local reproduction passed the structural audit (31 triggers, 1,222 globals and four unchanged non-City SCOs); five independent simulated negative controls passed locally for wrong guard, original trigger modification, missing and modified scene evidence. The **exact PR #10 GitHub source's complete patch-and-test suite remains unexecuted in this environment**. None of these checks establishes actual WSE2 game runtime, local server permissions or AI shooting.

The canonical B/C launch/record interface is [RECORDER_LIFECYCLE_V1.md](../handoffs/RECORDER_LIFECYCLE_V1.md): B owns host/client process handles and waits for C's authenticated passive-recorder ready marker before any game start.
