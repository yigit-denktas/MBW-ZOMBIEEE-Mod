# Agent A — City engine / integration lead

**Branch:** `agent/a-city-engine` (created from `main@048564a526de9b36abd55874271c7b80f36e5cf5`).
**Tracking:** [24-leaf public record](https://github.com/yigit-denktas/MBW-ZOMBIEEE-Mod/blob/project-record-setup-v041/progress/ledger.json), [A/B/C allocation](https://github.com/yigit-denktas/MBW-ZOMBIEEE-Mod/blob/project-record-setup-v041/progress/agent-allocation.json).

### Owned ledger leaves
`ZOM-REC-01`, `ZOM-REC-02`, `ZOM-REC-03`, `ZOM-ENG-01`, `ZOM-ENG-02`, `ZOM-ENG-03`, `ZOM-AI-01`, `ZOM-AI-02`, `ZOM-AI-03`, `ZOM-WAVE-01`, `ZOM-ADMIN-01`; optional post-v1 `ZOM-MAP-01`.

### Initial sprint — in this order
1. Audit `tools/build.py`, `tools/preflight.py`, source provenance and compiled mission/table assumptions. Convert fragile assumptions into offline regression tests and strict installer errors; don't assert a partial RAR decode was fully valid.
2. Prepare original 0.4 RAR identity/CRC preflight that can run on Windows 11 with safe autodetection/fallback to local 7-Zip; make output machine-readable for B and C.
3. Document the exact City WSE2 launch checklist/config and which parts remain unverified. Provide B a minimal launch contract, and C the mission/wave/event names needed to disambiguate logs.
4. Review B and C draft PRs and integration tests; prevent merge collisions and update the Project Record ledger/Pages snapshot only after evidence review.

**Do not** mutate Agent B Windows installer code or Agent C Lua/diagnostic code. No CI, no proprietary assets in Git, no game launch claims without Windows evidence, no premature all-five-maps expansion.

### Current source facts
Original `ZOMBIEEEBeta04.rar` SHA-256 `9be100ff41ce6f8ebadd4aa27377f70f402883fab271999a8cab8cc1da001d1e`; v0.1.8 source has only *offline* tests; old invasion mission is `mst_multiplayer_iv` on City `tbfc_invasion_4`; WSE2 1.1.5.4 was pinned in the repository but remains a target until in-engine verification. Need legally owned game and source archive for final test.

### Initial deliverable
A small code/test PR implementing more reliable original-RAR / compiled-mission startup preflight, plus documented WSE2 source boundaries and a single integrated final-session test plan. Keep original 25 invasion triggers intact in default mode.


## Continuation — post-control City static gate (2026-10-23)

- **Code:** `tools/final_city_gate.py` and `tools/build.py` now require an exact final byte check for the complete City-only tactical profile after optional `--private-commands` or `--solo-assist`. The accepted 31-trigger mission/variables and City SCO hash are frozen before host controls; final native bytes and SCO must match the frozen core plus the selected deterministic patch. The install receipt contains `city_final_acceptance` with control mode, checks, SHA-256 and `runtime_verified:false`. Existing `city_static_acceptance` remains the earlier prerequisite.
- **Tests:** 8 synthetic source-free negative controls passed in a separate local reproduction; three source-grounded test methods were added to `tests/test_city_acceptance.py` but **not executed**. The original user archive/module and exact full branch checkout were unavailable here. Do not claim all City gameplay or installer tests passed.
- **B coordination:** [PR #11 directions](https://github.com/yigit-denktas/MBW-ZOMBIEEE-Mod/pull/11#issuecomment-6374942213) — B to build actual passive-recorder adapter with B-owned fake game processes, HMAC attach/stop, secure local control files, exact B+C interop and no game-before-recorder.
- **C coordination:** [PR #12 directions](https://github.com/yigit-denktas/MBW-ZOMBIEEE-Mod/pull/12#issuecomment-6374942751) — C to run exact checkout tests, integrate real B adapter rather than simulated B only, and document PID-reuse limitations/possible schema addition.
- **Next A gate:** secure complete *exact* PR #10 checkout, run `python -m unittest discover -s tests -v` using original module when available; run archive `7z t` separately; review B/C combined fake-process fixture and keep all PRs draft until offline acceptance. **WSE2 and City combat remain unverified.**

## Exact-source City verification, 2026-10-23

- Original `ZOMBIEEEBeta04.rar` recovered from the owner's private file Library and pinned SHA-256/size verified. Core input CRCs: **10/10** (native mission, scenes, variables, troops, item kinds, 5 invasion SCOs). Historical source inputs have not been committed or redistributed.
- Reassembled **51 PR #10 source/config/test files** at `7c92adfcf631abd1e6e09534e9a915bee543c67a` and verified their Git blob identities. New verifier `tools/verify_city_chain.py` and portable archive test path also match the committed Git blobs exactly.
- With `ZOMBIEEE_ORIGINAL_MODULE` and `ZOMBIEEE_ORIGINAL_ARCHIVE` pointing to the owned source, full suite: **124 passed / 0 failed / 0 skipped**, Linux Python 3.13.5, rerun twice. This supersedes previous reconstructed/partial result disclaimers for the tested code, **but not for all Windows/WSE2 behavior**.
- Reproducible verifier: `python tools/verify_city_chain.py --original PATH_TO_ZOMBIEEE --archive PATH_TO_RAR --json`. Two City variants (original and balanced AI) each pass **25→26→27→29→31→35** native trigger chain, with original prefix preserved, canonical City SCO verified, all four deferred scenes unchanged and 1,225 final globals. Optional solo-assist passes **31→32** with 1,222 globals.
- The full standard-variant staged source mirror checked **1,068 extracted files: 1,065 byte-identical; exactly 3 approved edits** (mission, variables, City SCO), no unexpected edits. The original inputs also remain unchanged.
- **Critical limitation:** the available libarchive RAR reader is not a complete substitute for 7-Zip. Of 1,068 extracted RAR members, **969** matched per-member archive CRC and **99** did not, with explicit unsupported-filter decoder errors. All 10 required City inputs matched, but full archive member CRC **remains NOT VERIFIED**; do not attribute mismatches to an archive defect or install a libarchive-extracted build. Genuine `7z t` and real `tools/build.py` installation are still required. WSE2 gameplay and B/C runtime/recorder integration also remain unverified.
- Reports: [human-readable](../reference/CITY_CHAIN_VERIFICATION_2026-10-23.md) · [machine-readable](../reference/CITY_CHAIN_VERIFICATION_2026-10-23.json). Keep PR #10 draft/unmerged pending final integration gates.

## Native survivor wave/recovery audit: P0 mode mismatch fixed (2026-10-23)

**Source-grounded discovery:** Original Beta 0.4 `mst_multiplayer_iv` trigger 3 (`ti_before_mission_start = -19`) unconditionally assigns `g_multiplayer_game_type = 7`. The initial A patches incorrectly guarded both newly added wave reinforcement (index 28) and tactical recovery (index 30) on mode **6**, making both branches dormant under original initialization. Fixed both to shared `INVASION_GAME_TYPE=7` without modifying the original 25 native triggers.

New `tools/ai_wave_contract.py` independently decodes native condition/consequence blocks and requires original-mode initialization, correct 7-mode guards, round/wave gates, reserved living NPC team/groups, reinforcement sentinel and tactical state transitions. `tools/city_acceptance.py` now fails closed if those invariants fail; the install receipt additionally records source-derived `city_static_acceptance.original_invasion_game_type=7`, **not** runtime-observed mode. Added seven regression methods including old type-6 reinsertion, modified source init, malformed native stream, wrong visitor team.

**Exact local original-asset suite**: **131/131 tests passed, 0 skipped** (Linux Python 3.13.5; original pinned 2012 inputs). `tools/verify_city_chain.py` PASS again, 25→26→27→29→31→35 original and balanced AI, plus 31→32 solo assist. All amended GitHub source blobs match the tested local content. Details: [City AI/wave audit](../reference/CITY_AI_WAVE_AUDIT_2026-10-23.md). The [earlier 124-test chain report](../reference/CITY_CHAIN_VERIFICATION_2026-10-23.md) is now expressly a historical **pre-fix static** snapshot.

**Remaining:** no actual WSE2 gameplay; full genuine 7-Zip archive member CRC not run; B/C exact current recorder interop and offline installer pending. Continue with conservative City positions, runtime boot-spec research, and B/C integration; no extra user playtests. PR #10 stays draft/unmerged.
