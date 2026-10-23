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

## Latest owner request: B runtime selection + City defensive-position hardening (2026-10-24)

- Reviewed B `d41aefc` on PR #11: `7z t` pinned original RAR **all members OK**; exact A Windows asset-suite **131/131** after 2 `Path.write_text(..., newline="")` fixture fixes (now committed to A); exact C `1119cca` Windows 59 focused with 3 skips / 151 full with 33 skips; actual B+C adapter 14 focused with 1 skip / B full 162 with 31 skips. These are B **reported** test executions. Source integrity+offline interop gates advanced; real WSE2 never launched.
- Architecture **selected**: one **dedicated** `mb_warband_wse2_dedicated.exe` host and one local `mb_warband_wse2.exe` client under WSE2 Warband **1.1.5.4** and Warband **1.174**, with C arming first. Three B-discovered WSE2 binaries are still version/identity `unknown`; can't select actual local executable *paths* until read-only classification, role matching and release identity are verified. No automatic launch/installer elevation. See [WSE2 City boot contract](../docs/WSE2_CITY_BOOT_CONTRACT.md), instructions posted to B PR #11.
- **City posts revised** on A: actual face-edge connectivity; area >=3.0, nearest scene-prop origin >=3.0; reserved 2/3/4 coordinates **(169.423,169.376), (185.190,185.009), (146.250,183.491)**. These are risk proxies, not collision/LOS proof. No other original map modified. Original-asset **134/134** Python tests passed locally (Linux 3.13.5); post-hardening full City replay passed. Changed source/test Git blobs verified. See [guard hardening](../reference/CITY_GUARD_HARDENING_2026-10-24.md). Prior City-SCO checksums in pre-hardening reports are historical.
- B P1 stays fixture-only reversible installer, plus confidential read-only candidate classification. C v1 wire unchanged. The final private Windows game test remains **one consolidated session**, after explicit consent and instrumented local-only socket observation.

## Current A native-state gate — 2026-10-24 (140 original-asset tests)

A discovered the historical wave reset caused two successive rounds to share a wave number. The first `neq(wave,last)` fix only covered lower subsequent waves and **was superseded before integration**. Active trigger 28 now uses the original `g_round_start_time` together with the current `wave_number` as a round+wave key; both appended last-seen values are stored before a top-up. Source sentinel `zdr_last_reinforced_wave` remains a plain wave. Extra append-only global: `zdr_last_reinforced_round_start`; original first 1,220 globals/25 triggers preserved; active City tactical core now **1,223 globals / 31 triggers**, private-controls build **1,226 globals / 35 triggers**, solo assist **1,223 / 32**. Latest full original-source local run **140/140 passing, zero skips** and full chain stage replay `passed=true`, `runtime_verified=false`. All 11 updated code/test files were hash-confirmed after GitHub commit. Detailed [round-aware report](../reference/CITY_ROUND_AWARE_REINFORCEMENT_2026-10-24.md). B must not mix older A artifacts, cached global counts or previous City SCO hashes. The previous B Windows 131/131 results do not cover this revision.


## Independent A work after B/C precheck — 2026-10-24

Reviewed B PR #11 and C PR #12 + issue #6: owner-approved first boot had been **announced** but **no completed actual runtime receipt** had been posted at the checkpoint. It cites older A `2643321` and older C `53c2f88`; do not certify current round-aware A/C P1 from historical boot. B confirms WSE2 dedicated x86/client files verified against official 1.1.5.4 package. B's reversible journal installer executor still not on PR #11; C's count correction `e4553547` passes source review but requires exact-head tests.

A implemented read-only `tools/round_lifecycle_audit.py` + 4 original-asset positive/negative tests. It proves 9 native source patterns (original wave reset and round timestamp, mission-only initial defender spawn/hold orders, periodic reinforcements/recovery, one-time tactical-mode init) and intentionally reports runtime restart, NPC persistence, hold-order persistence and WSE2 timer behavior as **unknown**. Local 144/144 tests pass (Python 3.13.5, original owner Beta 0.4 module/RAR), full City chain `passed=true`, `runtime_verified=false`. No native gameplay patch changes in this slice. See [round-lifecycle audit](../reference/CITY_ROUND_LIFECYCLE_AUDIT_2026-10-24.md).

A published [14-gate integrated acceptance ledger](../docs/INTEGRATED_CITY_ACCEPTANCE_2026-10-24.md) distinguishing source CRC/binary integrity from actual socket/listener, join, mission/scene, team, wave, round restart, recorder ZIP, private installer and current-version binding. Do not merge until the correct *candidate and exact evidence* pass; keep all PRs draft. Priority now: review actual B/C completed boot observations before touching gameplay behavior further.

## Server-side mission evidence hardening — 2026-10-24

While actual B boot results remained unposted, A fixed a **false-positive diagnostics predicate** in `tools/evidence_readiness.py`: any client/foreign mission entry was formerly reported as invasion entered. Now `invasion_mission_entered` requires explicit `role=server` with matching `multiplayer_iv` template, and `city_scene_observed` requires a distinct explicit City scene marker from that same server event; server zombie/wave heartbeat measures likewise require the correct mission. Missing C/Lua scene getter is **unknown**, not failure or inferred City success. A local test suite passed **149/149**, zero skips/failures, including 5 new client/foreign/unknown/positive tests. Gameplay and B/C wire unchanged. [Full rationale](../reference/CITY_SERVER_EVIDENCE_GATING_2026-10-24.md). The existing old boot attempt using A `2643321` must retain historical candidate scope.
