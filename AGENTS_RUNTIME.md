# Runtime Evidence Guide (ZOMBIEEE Remaster / City)

Scope: agents who launch, seal, or interpret runtime sessions for the City
(`tbfc_invasion_4`, mission template `mst_multiplayer_iv`, loopback dedicated
host on `127.0.0.1:7240`). This file is guidance; it never authorizes installs,
merges, deployment, or acceptance. Runtime evidence is diagnostic until a
reviewer accepts it, and `runtime_verified` stays `false` until a human decides
otherwise.

Companion skill: `.agents/skills/runtime-evidence-before-claim/SKILL.md` — read
it before writing any "it works / it's fixed / zero shots" sentence.

## 1. Non-negotiables

1. **One host per port.** Only one WSE2 dedicated host may bind the loopback
   port. A second launch while a lane is active fails or corrupts the first.
2. **Never install over a running lane.** Builders/Lead install; runtime agents
   verify no `mb_warband_wse2*` process exists before an install window. Record
   the install backup directory, mission hash, and probe identity per run.
3. **Record the lane.** Every launch records: lane name, module path + mission
   `mission_templates.txt` SHA-256, probe identity, port, run directory, and
   launch timestamp. If the module changes mid-run, the run is **contaminated**
   and must be discarded (not "mostly valid").
4. **Seal before interpreting.** Only a sealed session (8-file recorder bundle
   with `manifest.json`, `verified=true`) is evidence. Screenshots without a
   seal are illustration only.
5. **Unknown is not zero.** Absent fields stay `null`/`-1`/`UNKNOWN`; they never
   become `0`, "no", or "passed".
6. **No acceptance claims.** Evidence reports state what was observed and the
   gaps; they never claim acceptance, victory, or a fixed build.

## 2. Environment map

| Path | Purpose |
| --- | --- |
| `<repo>` (`_zom-main-merge` worktree) | Docs/merged main worktree. Authored sources live here. |
| `…\MountBlade Warband\Modules\ZOMBIEEE_Remaster` | Installed module under test. SHA it before/after each lane. |
| `…\MountBlade Warband\Logs\rgl_log_<stamp>_crash.txt` and `…\Dumps\*.dmp` | Engine crash evidence (only when a crash occurred). |
| `local/session/` (runtime worktree) | Harnesses, receipts, sealed evidence, crash mirrors, replays. |
| `local/session/ai_idle_session.py` | Host + unattended client, auto-join, screenshots/frames, join retry, seal. |
| `local/session/playcity_validate.py` | Launcher-based `play --no-install` run with receipt recovery. |
| `local/session/lane_report.py` | PASS/FAIL/UNKNOWN lane JSON (join, errors, crash, coverage, screenshots). |
| `local/session/encode_replay.py` | Frame PNGs → MP4 + replay metadata (GIF path is broken; do not cite GIFs). |
| `local/session/build_night_v3.py`, `install_v3.py`, `verify_ai_only.py` | Build/install/seal verification helpers (install authority stays with Lead). |
| `tools/receipt_summary.py`, `tools/telemetry_studio/` | ZDB1 summary, heatmap export, probe-health gate (use the merged branch the Lead pins). |

Evidence directories: sealed runs are `ai-idle-<stamp>-<tag>/<hash>/`;
screenshots in `screens/` with `screens/manifest.json`; dense frames in
`frames/`; replay evidence in `replays/`; summaries as `summary_*.json`; crash
copies as `CRASH_*`.

## 3. Assumptions (state them; don't silently rely on them)

- Sampling is bounded: heartbeat 15 s baseline, adaptive 1–5 s where available.
  Anything between samples is unknown.
- Shots are an **ammo-delta proxy**, not an event count (`proven=false`); ammo
  refills mask shots, and attack-action transitions are not shot counts.
- Kills are agent lifetime counters summed over observed agents, not session
  kills or KD.
- `no_player` is the latest event carrying an explicit `no_player` marker (in
  practice the final heartbeat). Read it with `composition.mode` and
  `lifecycle.player_joined/player_died`; never quote it alone.
- Hit attribution is frozen **unavailable** (runtime trigger params are not
  populated); it is a gap, not a failure of gameplay.
- Divisions/behavior/mounted/shield/action readbacks are unavailable; unknown
  never becomes zero.
- The client console can be spammed by probe output; screenshots must be
  reviewed for overlay blockers before they are cited as gameplay.

## 4. Standard procedure

### 4.1 Preflight
1. No running `mb_warband_wse2*` process; port `7240` free.
2. Module identity: `mission_templates.txt` SHA-256, `scripts.txt` SHA-256,
   receipt flag that matters for the test (orders/refill/accuracy/targets).
3. Probe identity and capability line; run the probe-health gate on the last
   sealed build when available.
4. Owner/Lead confirmed quiet window; install authority with Lead.

### 4.2 Quick lane, then full lane
1. **3-minute quick lane** first: join (retry chain, alternating faction row),
   `--player-respawn-as-bot 1`, screenshots + frames, seal.
2. Only if quick shows join, no crash, no critical errors, and expected
   telemetry, run the **10-minute full lane** on the same module.
3. Never install between the quick and full lane; if the module changed, restart.

### 4.3 Seal and gates
1. Verify the manifest (8 files, SHA-256, `verified=true`).
2. Run the probe-health gate; heartbeat > 0, adaptive counters present, no
   critical error family. Missing data is a gap, not a pass.
3. Run the pinned `tools/receipt_summary.py <sealed-root> --json`
   (add `--build-receipt` when the build documents a measurement parameter such
   as `ammo_refill=off`).
4. Emit `lane_report.py` JSON with lane/module/port and PASS/FAIL/UNKNOWN.
5. Review screenshots before citing visuals; list them with what they show.

### 4.4 Report
State: run directory, sealed manifest hash, module/mission/probe identity, lane
duration, exact metric values, thresholds met/failed, screenshot paths reviewed,
and explicit gaps. Include the proxy/refill/`no_player` caveats that apply. No
acceptance wording.

## 5. Evidence gates (provisional triage, not acceptance)

| Gate | PASS condition | Caveat |
| --- | --- | --- |
| Join | `player_joined` lifecycle event present | CLI clicks are flaky; retry chain required |
| Heartbeats | > 0 and cadence not stalled | Pre-round/no-client runs have no heartbeats |
| Errors | 0 invalid-agent/group, 0 probe Lua errors, 0 `EXCEPTION` | Original trigger-14 `-1` may remain in pre-guard builds |
| Crash | no new crash log/dump | Killed processes are not crashes |
| Fire volume | first shot < 30 s; `agents_fired_ratio ≥ 0.4`; `shots/min ≥ 5` | shots are ammo-delta proxy; refill masks them |
| Coverage | adaptive samples present for both teams | sampler gaps stay gaps |
| Visuals | reviewed in-game frames with no overlay blocker | menu/death frames are not gameplay evidence |

## 6. Common failures and fixes

| Failure | Symptom | Fix |
| --- | --- | --- |
| Install during run | run sealed but module hash changed; mixed evidence | discard run, record contamination, rerun after quiet window |
| Idle player death | "Choose an option" death menu over screenshots; round resets | run with `--player_respawn_as_bot 1` (or spectator) |
| `no_player` misread | summary says `no_player=true` but player joined and later died | read final heartbeat + lifecycle; cite joined/died/absent |
| Refill masks shots | `ammo_burn=0` while `release_actions>0` | use a refill-off measurement build or mark shots unmeasurable |
| Summary skips adaptive rows | zero shots while raw `adaptive_sample` has ammo drops | fix parser (`agent=` key) before reporting zero |
| Client console spam | probe text covers HUD in screenshots | server-only adaptive output; regenerate or crop with care |
| Join flakiness | stuck on faction screen, no `player_joined` | alternate row clicks, retry up to 10×, verify markers |
| 0-byte GIF | replays/*.gif empty | cite MP4/JSON only; delete empty GIFs |
| Stale receipt | launcher prints an older launch receipt | use the newest matching launch id; verify timestamps |
| Crash after probe error | AV in `mbAgent::updateWalkingEffects` after invalid-agent Lua error | preserve crash log+dump, stop lane, report exact stack |

## 7. Handoff and review

- Hand reviewers: sealed bundle path, manifest hash, module/mission/probe
  identity, lane report JSON, summaries, screenshot list, and gaps. Do not send
  conclusions as facts.
- Reviewers verify the files directly; a reviewer PASS is evidence review, not
  gameplay acceptance.
- Builders do not evaluate their own runtime claims; runtime agents do not
  approve their own builds. Route disagreements to the Lead.
- Do not edit root `AGENTS.md`, trackers, or public release files from a runtime
  task; docs-only changes go to the designated docs worktree/branch.

## 8. File map for a runtime claim

1. `ai-idle-<stamp>-<tag>/<hash>/manifest.json` — sealed inventory.
2. `.../<hash>/host_stdout.log` — ZDB1 truth (heartbeats, samples, lifecycle).
3. `.../<hash>/logs/log_01.txt` — dedicated engine log (errors, Lua).
4. `screens/` + `screens/manifest.json` — reviewed visual evidence.
5. `frames/` + `replays/*.mp4` — motion evidence (private until cleared).
6. `summary_<tag>.json` — pinned-tool numbers.
7. `lane_<name>.json` — lane/module/port + PASS/FAIL/UNKNOWN.
8. `CRASH_rgl_log_crash.txt` / `CRASH_dump.dmp` — crash evidence when present.

## 9. One-line lesson

A sealed bundle plus a reviewed screenshot beats any confident sentence: if the
artifact paths, counters, and caveats are not on the page, the claim is not
evidence yet.
