> **Historical static snapshot (before AI game-type correction).** This 124-test report proved byte/trigger preservation but did **not** establish the wave and recovery predicates could run. A subsequent original-mission audit found both controllers incorrectly checked game type **6** while the original Invasion mission unconditionally initializes **7**. They are fixed and covered by **131/131** tests in [the current City AI/wave audit](CITY_AI_WAVE_AUDIT_2026-10-23.md). Do not use this report alone as AI-functional acceptance.

# ZOMBIEEE Remaster — City native patch-chain verification

**Date:** 2026-10-23  
**Track:** Agent A, draft PR #10 (`agent/a-city-engine`)  
**Verified source:** 51 GitHub code/config/test blobs at PR commit `7c92adfcf631abd1e6e09534e9a915bee543c67a`, individually reconstructed and checked against their exact Git blob SHA-1. The follow-on verifier at commit `91b3cfddf2e9f3fefd375cacbf2b0324ee2f6cec` also matched the executed local file's Git blob `9d266fa54592aa7123052a8fbe1536df9f91f760`; the archive-test environment-variable fix at commit `20f600397073ef37cb4c92e178e9b11dc2048d11` matched its executed local blob `52f564cf572cbb00dfafa223f50f6e56671757fb`.  
**Environment:** Linux x86_64; Python 3.13.5. No Warband or WSE2 executable was launched.

## Result

**PASS — static source-level patch chain and staged asset preservation.** This is **not** a real Warband/WSE2 runtime acceptance or a full-archive CRC success.

| Verification | Evidence/result |
|---|---|
| Historical RAR identity | Exact 167,493,071 bytes and SHA-256 `9be100ff41ce6f8ebadd4aa27377f70f402883fab271999a8cab8cc1da001d1e` |
| Critical original City inputs | 10/10 match original RAR entry size and CRC32 (`mission_templates.txt`, `scenes.txt`, `variables.txt`, `troops.txt`, `item_kinds1.txt`, and all five `scn_tbfc_invasion_N.sco`) |
| Complete PR #10 Python suite | **124 run, 124 passed, 0 failed, 0 skipped** using the original extracted module and pinned RAR |
| Standard City trigger stages | **25 → 26 → 27 → 29 → 31 → 35**; every compiled native stream decodes fully |
| Balanced-AI City trigger stages | **25 → 26 → 27 → 29 → 31 → 35**; original player classes protected by existing tests |
| Optional solo-assist route | **31 → 32**, complete native decoding and final static gate PASS |
| Original invasion trigger prefix | Original 25 native trigger lines byte-preserved at every stage in both full-chain profiles |
| Four deferred map SCOs | Four original scenes unchanged at every stage, City guard conditions present |
| Original scenes table | Unchanged across variants |
| Canonical City overlay | `audit_city` PASS for both complete tactical profiles; final City SHA-256 matches its canonical overlay |
| Final optional controls | Full mission/global byte comparison against explicitly requested deterministic patch PASS for both hotkey and solo-assist modes |
| Final native global counts | **1,225** for 35-trigger private-command variants; **1,222** for solo-assist |
| Full staged original-file preservation | **1,068 extracted original files examined; 1,065 unchanged; exactly 3 intentional changes**: `mission_templates.txt`, `variables.txt`, and `SceneObj/scn_tbfc_invasion_4.sco`. **0 unexpected changes**. No other original staged file changed. |
| Original input folder | Ten critical original inputs identical before and after every stage; verifier only writes into temporary private copies |

The machine-readable result is at `reference/CITY_CHAIN_VERIFICATION_2026-10-23.json`. Both outputs deliberately omit machine-local private paths.

## Reproduce on an owned local original installation

From the exact Agent A branch checkout, set the environment variables to the extracted original Beta 0.4 module and the pinned original RAR. In PowerShell:

```powershell
$env:ZOMBIEEE_ORIGINAL_MODULE = 'C:\path\to\extracted\ZOMBIEEE'
$env:ZOMBIEEE_ORIGINAL_ARCHIVE = 'C:\path\to\ZOMBIEEEBeta04.rar'
python -m unittest discover -s tests -v
python tools/verify_city_chain.py --original $env:ZOMBIEEE_ORIGINAL_MODULE --archive $env:ZOMBIEEE_ORIGINAL_ARCHIVE --json
```

To separately establish full member CRC with a genuine 7-Zip installation (not a fixture or alternative extractor), run:

```powershell
python tools/archive_audit.py --archive $env:ZOMBIEEE_ORIGINAL_ARCHIVE --verify-crc --json
```

The chain verifier copies historical inputs only into temporary folders; it does not overwrite the game or source module, does not create a public server, and does not redistribute mod assets.

## Evidence qualifications and remaining gates

- The pinned RAR matches exact size and SHA-256. The local environment did **not** have an official 7-Zip binary; therefore full member CRC is **not checked**.
- A libarchive-based extraction was sufficient to recover the ten source-critical files, whose RAR-header CRCs were independently verified. However, across all **1,068** RAR file entries, this alternative decoder yielded **969 entries matching their archive CRC and 99 entries with size/CRC mismatch**. Libarchive explicitly reported unsupported RAR filter parsing on several entries. These mismatches **must not be attributed to a corrupt original archive** without genuine 7-Zip verification. Nor may the partially recovered output be treated as a trustworthy completed installation.
- The 1,068-file **staged preservation comparison** proves the City patches did not change unrelated bytes of the extracted snapshot. It does **not** establish that all 1,068 extraction results were correct.
- The full `tools/build.py` **7-Zip test/extract and transactional output installation** path was not executed against a real CRC-verified extraction. The new `verify_city_chain.py` replays its native City patch functions directly, independent of the installer.
- In-engine functionality remains **unknown**: correct native opcode semantics, defender survival/targeting/visibility, actual wave progression, host-only cheat effects, WSE2 boot and private solo joining. C's crash-recorder evidence and B's launcher also require their combined real-process offline interop tests.
- This report does **not** approve a PR merge, release milestone or user gameplay acceptance. Keep PR #10 draft until the remaining installation and runtime gates have actual evidence.
