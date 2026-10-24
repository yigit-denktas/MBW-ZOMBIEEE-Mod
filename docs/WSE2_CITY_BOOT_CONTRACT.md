# WSE2 City-first Windows boot selection and acceptance contract

**Agent A decision, 2026-10-24 · implementation target; no game process launched.** B reported one `found` Warband candidate and three `found` WSE2 executable candidates on the owner's Windows 11 machine. Their executable basenames, SHA-256 identities, detailed version/installation relationships and engine behavior were **not provided**. Do not select an unknown executable solely because it was detected.

## 1. Selected architecture and roles

**SELECTED: dedicated private City host + one local WSE2 multiplayer client, supervised by B, with C's passive recorder starting first.** A dedicated host has a documented upstream executable and CLI template and allows separate server/client evidence. A listen-host remains an explicit fallback ONLY if the dedicated route fails in observed controlled local tests; it is not silently interchangeable. Nothing in this design certifies local-only binding or successful joining.

**Pinned products:**
- Warband **1.174**: provisional candidate is the **single Steam-manifest-derived Warband install** B found (1 `found` PE executable), pending read-only game-file version, Steam provenance and ownership confirmation. `found` only means the PE header parsed. Do not modify that installation.
- WSE2 **1.1.5.4 Warband edition**, upstream release 2026-10-14, not `WSE2_WFaS`. Published Warband **WSE2.zip** SHA-256 `118ed9517356a7016bfb911bccb600a3d95682407687ec0552fdc5acdb91f06a` (70,730,391 B); **WSE2_Installer.exe** SHA-256 `b358a41fb415eefac8668903f1f0849fda7186f2cc98269c2cfe8b7d916332aa` (20,821,783 B). Those are **archive/installer package hashes**, not hashes of individual installed executables. Never compare an on-disk exe hash with a package hash, or claim release identity from a fixed PE version resource alone.
- Original source Beta 0.4 `ZOMBIEEEBeta04.rar` SHA-256 `9be100ff41ce6f8ebadd4aa27377f70f402883fab271999a8cab8cc1da001d1e`; B observed `7z t`: **Everything is Ok**, exit 0, 1,068 files. User-owned assets stay local, out of public Git.

**WSE2 role mapping (confirmed upstream path and launcher examples, actual local matches not yet proven):**
- Dedicated host: `mb_warband_wse2_dedicated.exe`.
- Multiplayer client: `mb_warband_wse2.exe`.
- Launcher UI, *not* by itself the host/client: `wse2_launcher.exe`.

The three `found` entries may simply be distinct roles within one installation rather than three rival runtime versions. Do not make an arbitrary pick. B must provide an **internal-only, read-only candidate classification** (basename, PE platform/version, SHA-256 of each candidate exe, containing-root equivalence, companion files, source provenance, resolved links/reparse status), excluding full paths/user identities from GitHub. Select one **matching pair** from the pinned Warband WSE2 tree if independently substantiated; otherwise `selection_status=blocked_unverified_candidate` and no spawn. No download, elevation, replacement, implicit acceptance, or launch needed for this classification.

## 2. Upstream CLI evidence vs not-yet-proven behavior

The official `Ruslan-700/WSE2-Releases` Warband tree contains:
- `Native_WSE2_dedicated.bat`: `start mb_warband_wse2_dedicated.exe --config-path server_config.ini -r Native.txt --module Native`
- `Native_WSE2.bat`: `start mb_warband_wse2.exe --module Native --no-intro`
- `Warband/server_config.ini` contains `[Network] bLoopbackServer=false`, `bHttpServerQueries=true`, `bRCONServer=false`, `sServerAddress=`, `iServerPort=7240`. These are **published defaults**, not privacy guarantees.

**Template, NOT authorized execution command:**
```text
[owned dedicated exe] --config-path [private session config] -r [validated session command text] --module ZOMBIEEE_Remaster
[owned game client exe] --module ZOMBIEEE_Remaster --no-intro
```
WSE2's `-r` script content/semantics and the client auto-connect mechanism for the historic `multiplayer_iv` mission are not established by the upstream example. Do not invent a `--connect` argument, inject a client patch, force server browser publication or assert that a CLI process start proves City mission entry.

**Session-only safety proposal pending OS observation:**
- Generate a private config copy rather than mutate global WSE2 settings. Candidate values for examination: `bLoopbackServer=true`, `sServerAddress=127.0.0.1`, `bHttpServerQueries=false`, `bAutoRestartOnCrash=false`, `bRCONServer=false`, `bOGPServer=false`, and no server browser/master listing. **Do not assume these fields actually restrict every bind address; verify the socket bound address using OS observation before joining.** If any listener binds `0.0.0.0`, `::`, or unexpected public interface, do not proceed; stop only owned process handles and retain C evidence. Avoid firewall or port forwarding changes.
- Prefer City `tbfc_invasion_4`, mission template `multiplayer_iv`, B session route `dedicated`, local client `127.0.0.1`, source-verifiable final static receipt. Player-side actual in-game join and mission-entry logs must be independently observed.
- C must be `ready` and armed before B starts any game. After B validates C marker and host/client matching owned processes, signed attach; after all game children exit, signed stop. No claim of playable waves from PID or network liveness.

## 2.1 Dedicated rotation bot-count requirement — observed 2026-10-24

**Root cause of the earlier "no team-1 agents" finding is dedicated rotation configuration, not the remaster build.** Lead-reported live observation on merged `main` `4c56242` with a rebuilt City module (C's corrected `opmeta=1` probe, recorder armed, dedicated host loopback-only `127.0.0.1:7240`). Sealed recorder receipt and screenshots are still pending.

Observed sequence (ZDB1 / host state):

| Step | Observation |
| --- | --- |
| Baseline, no bot-count commands | `role=server game_type=7 ready_for_spawn=1 bots_team1=0 team1=0 wave=0` for 90+ s |
| `set_bot_count 1 32` | `agents=33 team0=33 team1=0` — all allied bots on the player team, no enemies |
| `set_bot_count 2 32` | `agents=42 team0=1 team1=41 wave=1`, `wave_change wave=1`; still `game_type=7`, `ready_for_spawn=1`, loopback-only |

Engine semantics that caused the trap:

- `set_bot_count` is **1-based**: `1` is the first team, `2` is the second/enemy team.
- `$g_multiplayer_num_bots_team_1` is the **first** team, so a probe field named `bots_team1` does not describe the enemy team and must not be read as one.
- With no player/bot population the native round never became active enough for the original one-second wave controller to pass its round-start/time gate; configuring the second team populated the enemy team and the original wave advanced to `wave=1` with `team1=41` living agents (`32` configured + `9` original wave-1 visitors — arithmetic consistent with the source, not separately itemized in the evidence).

**Required for any B launcher/installer P1 attempt (before `start`):**

```text
max_num_bots 200
set_bot_count 1 0
set_bot_count 2 32
set_respawn_period 5
set_round_max_seconds 1800
set_defender_spawn_count 0
set_player_respawn_as_bot 0
start
```

All of these commands must be emitted **before `start`**. Offline enforcement: `tools/city_runtime_triage.py --rotation <generated rotation>` exposes `launcher_*` checks (start present, positive `max_num_bots`, positive second-team bot count, bot counts before `start`). This is a static contract, not gameplay proof.

### Wave-1 roster and respawn defects (issues #13/#14)

- The wave-1 enemy population created by generic `set_bot_count` is the **faction default troop**: observed as `trp_invader_multiplayer_ai` = **Crazed Civilian** (suited humans), not the native Zombie troops (`trp_invader1_multiplayer_ai` etc.). The nine original wave visitors are the native-trigger spawns; the other configured bots are generic. The launcher/rotation must establish the correct invader roster before calling a wave correct — tracked as issue #14 and supporting ledger work.
- After player death, no respawn/new round was observed (`team0=0`, `wave=0`). The rotation must set `set_respawn_period`, `set_round_max_seconds`, `set_defender_spawn_count 0` and `set_player_respawn_as_bot 0`; tracked as issues #13/#14.
- Related evidence hardening: issue #15 (recorder atomic-replace read race, supporting leaf `ZOM-DISC-22`) and issue #16 (seal dedicated-host ZDB1 stdout inside the flight evidence bundle).

**Boundaries:** one enemy wave observed; wave 2+, original allied survivor divisions 5-7, fallback/regroup, combat, round transition and controlled teardown remain unverified. No gameplay or release acceptance is claimed.

## 3. Evidence and acceptance sequence (one consolidated final private test)

| Gate | Authority | Acceptance / failure |
|---|---|---|
| 0. Original archive | B Windows `7z t` | **Observed PASS** in B's 2026-10-23 report; source identity pinned |
| 1. City static | A `city_static_acceptance` + `city_final_acceptance.passed` | Source check must pass; `original_invasion_game_type=7`, original 25 triggers preserved; AI runtime still unknown |
| 2. WSE2 executable selection | B read-only local identity | **PENDING**: resolve among three candidates by role and pinned edition/version; do not publish private paths |
| 3. Installed module | B journaled installer | PENDING: validated output + journal/rollback; no live-install mutation before explicit consent |
| 4. Recorder armed | B+C | Recorded matching live C PID/session/attempt; watcher+offset ready. Not game-ready |
| 5. Dedicated host private binding | B OS+engine logs | **SCOPED OBSERVED** (Lead, merged-main candidate): UDP `127.0.0.1:7240` loopback-only and host readiness reported; sealed receipt still pending |
| 6. Client joined City | B and C | **SCOPED OBSERVED** (Lead, merged-main candidate): corrected probe reports `role=server`, `game_type=7`, `ready_for_spawn=1`; player agent present. Explicit server-side City scene marker and sealed receipt still pending |
| 7. Survivors and waves | A+C | **FIRST ENEMY WAVE OBSERVED** (Lead, merged-main candidate): after second-team bot configuration `wave=1`, `wave_change wave=1`, `team1=41` living agents. Wave 2+, original allied survivor groups 5-7, fallback/regroup, combat and round transition remain pending |
| 8. Shutdown + evidence | B+C | PENDING: B-owned children exited, signed C stop, verified ZIP hashes and manual privacy review |

**Failure behavior:** Keep blocked/unknown states explicit. No false `engine_ready`, `joined`, `mission_entered` or `runtime_verified`; do not fall back to public or LAN hosting, reinstall silently, change RCON/firewall or kill unrelated processes.

## 4. Integration instructions

- **B / PR #11**: finish inert-fixture journal installer P1; classify executable roles/version read-only, keep exact paths private and return path-free selection facts. Do not run actual installation or WSE2 without consent. Later wire dedicated host and client only after privately observed CLI/session route.
- **C / PR #12**: no wire change; keep simulated receipts explicitly labeled; record stage transitions distinctly, with undecidable engine metrics `unknown`.
- **A / PR #10**: maintain City-only geometry/compiled-script gates; record actual runtime status only after the one final Windows session. No premature merge or user intermediate playtests.

## Grounded upstream references
- [WSE2 v1.1.5.4 published release](https://github.com/Ruslan-700/WSE2-Releases/releases/tag/v1.1.5.4)
- [Official dedicated launch example](https://github.com/Ruslan-700/WSE2-Releases/blob/master/Warband/Native_WSE2_dedicated.bat)
- [Official client launch example](https://github.com/Ruslan-700/WSE2-Releases/blob/master/Warband/Native_WSE2.bat)
- [Official server settings](https://github.com/Ruslan-700/WSE2-Releases/blob/master/Warband/server_config.ini)
- [Project's WSE2 pin](../reference/WSE2_1.1.5.4.json)
