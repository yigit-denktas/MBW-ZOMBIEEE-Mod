# Three-agent delivery board — 2026-10-23

**Source of truth:** [proposed Project Record ledger](ledger.json), [machine-readable allocation](agent-allocation.json), [live public tracker](https://yigit-denktas.github.io/MBW-ZOMBIEEE-Mod/). **Code baseline:** `main@048564a526de9b36abd55874271c7b80f36e5cf5` (v0.1.8 experimental, not WSE2-verified).

## Why these three lanes?

A runtime adapter is meaningless unless B can discover/start a legally owned game, and C can diagnose what happened if the process fails. All three must progress in **parallel** under explicit file ownership rather than a sequential list of 24 tasks. City is the **only** first-release map. Optional `ZOM-MAP-01` remains preserved but must not gate `ZOM-QA-02`.

| Lane | Work branch | Ledger leaves | Start now | Shared dependency |
| --- | --- | ---: | --- | --- |
| **Agent A — City engine and integrator** | [agent/a-city-engine](https://github.com/yigit-denktas/MBW-ZOMBIEEE-Mod/tree/agent/a-city-engine) | 12 (11 required + 1 deferred) | Archive/compiled mission preflight, City WSE2 boot contract, coordination | Needs Windows evidence for engine acceptance |
| **Agent B — Windows launcher and installer** | [agent/b-windows-launcher](https://github.com/yigit-denktas/MBW-ZOMBIEEE-Mod/tree/agent/b-windows-launcher) | 7 required | Win11 Steam/WSE2 discovery with fake filesystem fixtures; dry-run/reversible install | Wait for A's proven launch flags before real solo auto-connect |
| **Agent C — Flight recorder and forensic analysis** | [agent/c-flight-recorder](https://github.com/yigit-denktas/MBW-ZOMBIEEE-Mod/tree/agent/c-flight-recorder) | 5 required | External watcher, simulated process crash, bounded event schema, corruption/redaction test | Consume B session receipt; real WSE2 events later |

**Chat entry points:** [A handoff](https://github.com/yigit-denktas/MBW-ZOMBIEEE-Mod/blob/agent/a-city-engine/handoffs/AGENT_A.md), [B handoff](https://github.com/yigit-denktas/MBW-ZOMBIEEE-Mod/blob/agent/b-windows-launcher/handoffs/AGENT_B.md), [C handoff](https://github.com/yigit-denktas/MBW-ZOMBIEEE-Mod/blob/agent/c-flight-recorder/handoffs/AGENT_C.md). [Shared session contract](https://github.com/yigit-denktas/MBW-ZOMBIEEE-Mod/blob/agent/a-city-engine/handoffs/SESSION_CONTRACT.md).

## Critical path and bounded dependency work

**Immediately executable offline:** `ZOM-ENG-01` (A, prepare original archive/CRC verification), `ZOM-WIN-01` (B, discovery fixtures but final acceptance still depends on valid archive/engine evidence), `ZOM-OBS-02` (C, external watcher with fake crashes), `ZOM-LEGAL-01` (B, rights matrix), and `ZOM-REC-01` (A, toolkit provenance). These are independent *preparation* efforts: the ledger's runtime acceptance criteria remain pending.

**After offline integration G0:** A + B + C jointly stage one **City-only** Windows run with owned Warband/WSE2/original archive and flight recorder. It should establish WSE2 boot, the first complete zombie wave, launcher/host behaviour, and real logs. Do not reinterpret source tests as this evidence.

**After runtime evidence G1:** A fixes actual bot team/spawn/combat and commands; B finishes real one-click hosting/connecting and Windows repair; C tunes combat/profiling diagnostics. Only then start meaningful balance comparisons and sustained release QA.

**Final user gate G2:** one integrated private City release candidate with reliable AI, reversible installer, shortcut/solo flow, verified local diagnostic bundle, and owner acceptance. We do not request repetitive manual tests between each patch.

## Ownership, review and progress rules

Agent A is coordinator and owns the Project Record source and the separate public `gh-pages` projection. B and C **must not** edit `progress/**` or `gh-pages` directly. Agents work in separate PRs based on the exact `main` SHA, cite tests and blockers, and do not merge or change each other's file families without review. No CI and no original mod/game assets in Git.

The owner has approved **City first** and autonomous coding delegation; readiness remains provisionally L0 until a clean Windows bootstrap is evidenced. The tracker records **23 required outcome criteria** (none accepted yet), not feature implementation counts. Original six issues are preserved and installer/local-host issues [#8](https://github.com/yigit-denktas/MBW-ZOMBIEEE-Mod/issues/8) and [#9](https://github.com/yigit-denktas/MBW-ZOMBIEEE-Mod/issues/9) now supplement them.

## Current review blockers

- The v0.4.1 toolkit's release ZIP archive SHA-256 is release-published but not locally byte-verified; official installer/CLI checks remain pending.
- No verified WSE2/Warband runtime session yet; loader semantics, multiplayer host initiation and Lua APIs remain unknown.
- Browser interaction/screen-reader accessibility beyond static checks has not yet been demonstrated; Pages content is public and its JSON fetched successfully.
- Installer redistribution permissions, original OSP assets and final user-local repair prompts need explicit evidence.

## Code review and next tasks — 2026-10-23

| PR | Lane | Evidence | Current merge decision | Immediate next tasks |
| --- | --- | --- | --- | --- |
| [#10](https://github.com/yigit-denktas/MBW-ZOMBIEEE-Mod/pull/10) | A | Source integrity and City native guard code; complete branch offline tests outstanding | **Hold** | Execute full City-only compiled patch suite, check integration contracts |
| [#11](https://github.com/yigit-denktas/MBW-ZOMBIEEE-Mod/pull/11) | B | **B-reported** 97 passes, 30 asset skips; fixture-only process lifecycle | **Changes required** | Recorder ready **before** host/client; host-ready distinct from joined; raw game-root junction safety |
| [#12](https://github.com/yigit-denktas/MBW-ZOMBIEEE-Mod/pull/12) | C | Flight recorder and ZIP analyzer; author explicitly says tests not run | **Changes required** | Bounded crash tail; recorder-ready acknowledgment; validate symlink ancestors and run full test suite |
| [#7](https://github.com/yigit-denktas/MBW-ZOMBIEEE-Mod/pull/7) | tracking | Published public Pages view; v0.4.1 release ZIP not independently verified | **Hold** | Complete toolkit verification and record integrity before merge |

[Review #11](https://github.com/yigit-denktas/MBW-ZOMBIEEE-Mod/pull/11#issuecomment-6373896560) · [Review #12](https://github.com/yigit-denktas/MBW-ZOMBIEEE-Mod/pull/12#issuecomment-6373897277) · [B issue #8](https://github.com/yigit-denktas/MBW-ZOMBIEEE-Mod/issues/8) · [B issue #9](https://github.com/yigit-denktas/MBW-ZOMBIEEE-Mod/issues/9) · [C issue #6](https://github.com/yigit-denktas/MBW-ZOMBIEEE-Mod/issues/6).

**Critical interface handshake, jointly B/C:** B starts recorder only, receives C-issued versioned readiness for the correct session/attempt after durable log offsets are captured, *then* starts the game. Host-ready/client-joined/mission-entered are separate observations. Recorder remains alive until all owned child processes exit. Unknown stays unknown. No Windows game claims are supported by mocked events.

Status remains **0/23 required City outcome leaves accepted, 0/5 milestones accepted**. Code review labels and active prototypes never increase acceptance. The other four maps remain optional/deferred.

### B/C integration mismatch observed at follow-up review

Agent C's current recorder creates an atomic `recorder-ready.json` with `zombieee.recorder_ready.v1`, but requires a child command or **existing** PID; B wants to launch its own host/client *after* receiving readiness. The two models cannot simply be combined without a new passive watcher or changing which agent launches the game. B's discussed schema `zombieee.recorder-ready.v1` also differs (underscore vs hyphen). [B correction](https://github.com/yigit-denktas/MBW-ZOMBIEEE-Mod/pull/11#issuecomment-6374020607) · [C correction](https://github.com/yigit-denktas/MBW-ZOMBIEEE-Mod/pull/12#issuecomment-6374021323).

C has pushed implementation updates for log head/tail and path checks, but compatible handshake and executed test evidence are still required. **No merge or 0/23 acceptance changed.**

## Agent A integration update — City static gate and recorder decision

- [Static City acceptance source](https://github.com/yigit-denktas/MBW-ZOMBIEEE-Mod/blob/agent/a-city-engine/tools/city_acceptance.py) validates the original 25 native triggers, count 31, server+City guards on triggers 25/28/30, append-only globals and byte-identical other four original scene assets; **runtime_verified=false** by contract. Negative tests on A's branch are committed. A locally reproduced original City module yielded structural pass only when all deferred scene files were present; this was not a full exact branch checkout.
- [Recorder lifecycle contract](https://github.com/yigit-denktas/MBW-ZOMBIEEE-Mod/blob/agent/a-city-engine/handoffs/RECORDER_LIFECYCLE_V1.md) binds B-owned game processes to C passive pre-launch recorder. Schema `zombieee.recorder-ready.v1`; private HMAC controls; host readiness distinct from City mission entrance. B/C integration test is next.
- Existing project accepted baseline remains **0/23 required City outcome gates**, regardless of static progress. PRs #10, #11, #12 remain pending review.

### Agent A City integrity integration — 2026-10-23

- [Draft PR #10](https://github.com/yigit-denktas/MBW-ZOMBIEEE-Mod/pull/10) now requires the **exact canonical City guard-post SCO bytes**, guarding against incidental corruption, rather than accepting any changed City hash. Its release checker still checks the original 25 trigger prefix, scene guards, appended globals and all four unmodified deferred scene files.
- The City-only **builder itself** now saves temporary original source evidence before patching and fails closed if the post-31-trigger City output does not satisfy that audit; optional private hotkeys/solo assist are added only after acceptance. The local build receipt records checked City digests with runtime=false.
- **20 local replay tests passed:** 8 archive identity/CRC fixtures, 6 preflight fixtures, 6 City acceptance fixtures including a corrupted-scene negative control. This is **not** the full exact GitHub checkout test suite and does not verify WSE2/Warband gameplay.
- No CI, original assets in Git, automatic merges, or additional acceptance awarded. 0/23 City outcome gates remain accepted.

### Integration close-out — branches merged into main `4c56242` (2026-10-24)

- Merged reviewed heads: A `d3dbef5` → `9eed34b`; C `675188a` → `0fe86a4`; B `d41aefc` → `4c56242`. Remote `main` is `4c5624259ed9ce876da06d1996e728c63666a398`; PRs #10/#12/#11 merged; head branches deleted.
- Windows suites at merge time: A **158 OK/0 skips**; C **112 focused OK/3 skips**, **204 full OK/33 skips**; B **162 OK/39 skips**; merged main **340 OK/4 skips**. Conflicts only in `tools/evidence_readiness.py` (took C's newer gating + capability snapshot) and `tests/test_evidence_readiness.py` (kept A's superset).
- **Incident conclusions:** trigger-14 `Invalid Faction ID:-1` is original Beta 0.4 trailing `faction_set_slot(-1,200,trp_invader_multiplayer_ai)` content, non-fatal and not proven causal; probe `mode` is `zdr_defence_mode`, not game type; dedicated `role=client`/trigger-32 lvalue were one WSE2 msfiles operation-metadata defect, fixed by C in `675188a` with the signed wire unchanged.
- **Open:** no runtime acceptance. One corrected-probe controlled City observation (Lead-coordinated), B post-merge verification, the transient B/C file-replace race (`ZOM-DISC-22`), and the original required outcomes/installer/legal gates remain. Required City outcomes stay **0/23**, milestones **0/5**.

### Live bot-count breakthrough and follow-ups — 2026-10-24

- Merged-main candidate first enemy wave: baseline `role=server game_type=7 ready_for_spawn=1 bots_team1=0 team1=0 wave=0`; `set_bot_count 1 32` → allied-only `team0=33`; **`set_bot_count 2 32` → `agents=42 team0=1 team1=41 wave=1`, `wave_change wave=1`**.
- Root cause of earlier no-AI: dedicated rotation bot configuration (1-based `set_bot_count`; `g_multiplayer_num_bots_team_1` is the first team), not the build.
- New defects: wave-1 generic bots are faction-default Crazed Civilian, not native Zombie troops (#13/#14); no respawn/new round after player death (#13/#14). Required rotation commands: `max_num_bots`, `set_bot_count 2`, `set_respawn_period 5`, `set_round_max_seconds 1800`, `set_defender_spawn_count 0`, `set_player_respawn_as_bot 0` before `start`.
- Evidence: #15 recorder atomic-replace race (`ZOM-DISC-22`), #16 seal host ZDB1 stdout (`ZOM-DISC-24`); #1 closed → #13. Main tip `0eb9374`, suite **351 OK/4 skips**; `tools/city_runtime_triage.py --rotation` enforces the contract.
- No gameplay acceptance: wave 2+/completion, native zombie roster, allied divisions 5-7, round transition, sealed receipt and teardown remain open. Required City outcomes **0/23**, milestones **0/5**.

### Telemetry-v2 bug-fix integration — 2026-10-24

- Main tip `42d4ec37b0f44dda693247f8a9bbb67a77a42228`: C telemetry v2 merge `0393794` (head `a29fabf`), B sealing/retry/rotation merge `42d4ec3` (head `d1011e2`).
- Merged suite **380 OK/4 skips, 3 consecutive clean runs** (owned module+archive). Pre-fix B interop `PermissionError` flake observed once in 7 runs; 3/3 is not a general stability proof.
- Five bug-fix upgrades as support leaves: `ZOM-DISC-22` (#15, done), `ZOM-DISC-23` (#14, active — live validated rotation/roster pending), `ZOM-DISC-24` (#16, active — sealed ZDB1 attempt pending), `ZOM-DISC-25` (#13, done — histogram+lifecycle), `ZOM-DISC-26` (#6/#16, done — receipt summary CLI). No `ZOM-DISC-27` umbrella (schema already separates support from outcomes).
- Verified read-only: `python tools/diagnostics.py summary <attempt8>` → verified True (7 files), 4 invalid-faction-id errors, gaps include `zdbi_stream_not_sealed`, `runtime_verified=false`.
- Required City outcomes remain **0/23**, milestones **0/5**, `runtime_verified=false`. No gameplay/wave acceptance. Next bug-fix evidence: live validated rotation/roster and a sealed ZDB1-bearing attempt.

### Hands-off runtime evidence and defender/firearm fixes — 2026-10-24

- Main `24ed22f` (canonical build `a6b5fe9`); merged suite 493 OK/7 skips with the documented pre-existing NUL-flake caveat (fixed by F, not reported as stably green).
- Sealed evidence: native Zombies 894..911 reliable; native team-0 defenders 981..984 (bots_team0=4, player+4; spawn proven, division adoption/hold unproven); both-team positions; sealed host ZDB1 stdout; one-command play_city lifecycle passed (runtime_verified=false).
- Kill/troop accessor fix (C 9756b14) makes engagement/troop fields reliable; legacy unreliable sums labelled rather than zeroed.
- Still open: wave 2+/completion, survivor sector-hold correctness over time, firearm combat feel, legal redistribution, all release gates. Required City outcomes **0/23**, milestones **0/5**.
