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
