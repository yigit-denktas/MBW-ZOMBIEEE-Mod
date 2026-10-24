# Modder diagnostics & telemetry research — reuse, adapt, ignore (task-48)

**Status: docs-only reference. Observation date 2026-10-24. Link-only: no third-party code, assets or debug strings were copied; no game launch.** This survey answers one question: what existing Warband/WSE2 modder tooling can replace or harden parts of our ZDB1 diagnostics, so we stop reinventing — and where our probe is already beyond what the community tools expose.

Baseline for comparison is our own diagnostic stack: `overlay/lua/main.lua` (ZDB1 structured events), `tools/diagnostics.py`, `tools/receipt_summary.py`, sealed receipt verification, the `SCRIPT ERROR`/engine-error classifier, and the capability/gap model in [`../docs/DIAGNOSTICS.md`](../docs/DIAGNOSTICS.md). Everything below is evidence about *external* tooling, not an acceptance claim about our build.

## Sources actually reviewed

| Source | Access / date | What it provides | Licence / reuse |
| --- | --- | --- | --- |
| [`Ruslan-700/WSE2-Releases`](https://github.com/Ruslan-700/WSE2-Releases) — README + `CHANGELOG.MD`; latest release `v1.1.5.4` published 2026-10-14 | Fetched 2026-10-24 | WSE2 feature/operation/config history: render & simulation diagnostics overlay + periodic log options, profiler operations, mission debug window, Lua debugger, `table.print` (changelog's "rename `_log` to `log_rgl`" sits under Lua: it is a **Lua API rename** (`game._log` -> `game.log_rgl`), **not** an engine log-file rename) | Release repository has **no LICENSE file** (GitHub licence API returns 404); README only. Treat binaries/docs as third-party, link-only, no redistribution. |
| Local WSE2 1.1.5.4 SDK: `luaGuide.html`, `README.txt`, `EVAL_README.txt`, `header_operations_addon.py`, `module_config_template.ini` | Read locally 2026-10-24 (pinned 1.1.5.4) | Lua API and debugger/profiler documentation; `print`/`table.print`, overlays, `hookScript`, `game.fail`; config layout; `feval`/`EVAL_README` | Third-party SDK files; link-only, no copying. |
| [WSE2 forum thread 384882](https://forums.taleworlds.com/index.php?threads/warband-script-enhancer.384882/) | **HTTP 403 on 2026-10-24** (Cloudflare); recorded inaccessible | Primary WSE2 documentation pointer from `README.txt` | Not used as evidence beyond the recorded inaccessibility. |
| Native module system (community header `header_operations.py`, cross-checked with `Veehats/WarbandCoop`; **no licence detected in that mirror -> cross-check only, no table copying**; prefer the public-domain wiki DB + WSE2 SDK) | Read 2026-10-24 | `display_debug_message` 1104 (writes `<string_id>` to `rgl_log.txt` and displays it in debug mode per wiki/header; the extra "when edit mode is enabled" coupling appears only in a community header comment and is **unverified**), `display_message` 1106, `set_show_messages` 1107; `rgl_log.txt` documented as the engine log | Opcode definitions only. |
| [Mount&Blade Modding Wiki archive — operations list](https://mbmodwiki.github.io/List_of_operations) (OLL Clan; public-domain statement; DB generated 2011 by Swyter/Theoris) | Read 2026-10-24 | Native op semantics; confirms there is no structured telemetry/AI-state API | Public domain (statement on the archive). |
| [`cvlc/tgsmod`](https://github.com/cvlc/tgsmod) FormAI/Motomataru files (`formAI_*`, `formations_*`, `header_operations.py`) | Read 2026-10-24 | Battle-AI debug style: commented-out human `display_message` strings; no machine-readable telemetry | TGS licence does **not** grant FormAI rights (Nexus permissions govern); link-only, nothing copied. |
| Dedicated-server `help` output captured locally (`local/session/dedicated_help.txt`) | Captured 2026-10-24 | Server console commands incl. `get_bot_count`, `set_bot_count`, `get_*` state getters — out-of-band state checks | Local evidence, not redistributed. |
| [ZeroBrane Studio](https://studio.zerobrane.com/) | Read 2026-10-24 | Lua IDE / `mobDebug` host used by WSE2's Lua debugger | MIT per project site (LICENSE not independently re-verified); dev-only, not vendored. |
| Agent E independent cross-review (PR #30, `reference/CROSS_REVIEW_LEGAL_RELEASE_2026-10-24.md`, branch `agent/e-cross-review` @ `b0c9d5c`) | Reviewed 2026-10-24 | Licence/privacy/claim review of this draft | Docs-only review; no copied content. |
| Crash-log names seen in community reports (`rgl_log_<date>_crash.txt`) via search results | 2026-10-24 | WSE2 may write crash-named log files next to the game | **Community observation, not independently verified**; none observed on D's install; verify before relying on it. |

**Inaccessible:** the TaleWorlds WSE2 thread (403). **No licence file** ships in the WSE2 releases repo, so nothing from WSE2 is bundled here; all WSE2 features are documented as external, optional tooling.

## What the existing tooling actually exposes

### WSE2 engine-side diagnostics (the usable reuse)

- **Engine log file (install-verified by D, 2026-10-24):** the live log is
  `<game-install>\rgl_log.txt`
  (config `sLogPath=rgl_log.txt`), overwritten per launch and containing the
  client command line and Steam init lines. The **stable** secondary artifact is
  the rotated `…\MountBlade Warband\Logs\rgl_log_<DD.MM.YYYY_HH.MM.SS>.txt`
  (23-27 KB each in observed runs). Dedicated runs additionally write
  `Warband\dedicated_session_<stamp>.log` via server_config `sLogPath`; our
  recorder already copies it into the bundle as `logs/log_01.txt`. Script errors,
  opcode failures and crash traces land here even when the in-game console is
  noisy. **Crash-named logs were not observed** on this install (`*crash*` absent
  across many sessions) — treat crash files as 'only if a crash occurs', never
  promise them. **Naming caution:** the WSE2 changelog's "rename `_log` to
  `log_rgl`" is in the **Lua** section and renames the Lua API
  (`game._log` -> `game.log_rgl`), not the engine log file; op 1104's docs still
  name `rgl_log.txt`, and D's install shows `rgl_log.txt` + `Logs/rgl_log_*`.
- **Render/simulation diagnostics:** changelog adds an on-screen overlay **and periodic log output** controlled by `bShowRenderStats`, `bShowSimulationStats`, `iRenderStatsLogInterval`, `iSimulationStatsLogInterval`. These are engine performance/stall counters, not AI state — useful to explain "probe stopped sampling" or frame hitches.
- **Profiler:** `profiler_start` (3040), `profiler_stop` (3041), `profiler_is_recording` (3042), `profiler_mark` (3043, text marker "good for analyzing individual parts of a script"), with a timeline UI and profiler binary format. This is the right tool to measure probe overhead / script hot paths, in development, not in sealed evidence.
- **Mission debug window:** `wse_mission_debug_window` mapped presentation (in-game debug UI). Manual inspection only; not automatable into receipt evidence.
- **Lua debugging:** WSE2 ships a Lua **debugger** (documented in `luaGuide.html`, `mobDebug`/ZeroBrane IDE), `print`/`table.print`, `hookScript` (can hook `game_get_console_command`), and `game.fail()`. Development-loop tools; they do not persist machine-readable state.

### Modder logging conventions (human-facing)

- `display_message` (1106) shows a coloured message to players;
  `display_debug_message` (1104) writes its `<string_id>` to `rgl_log.txt` and
  displays it in debug mode (wiki/header). The additional "when edit mode is
  enabled" coupling appears only in a community header comment and the
  `bEditMode` changelog entry; treat that coupling as **unverified**.
  `set_show_messages` (1107) toggles window messages.
- This is the dominant community pattern for "debug output" (FormAI/Motomataru scripts contain commented-out `display_message` debug strings; battle-AI mods print human sentences). It is **unstructured text**, exactly the class of output that interleaved with our `SCRIPT ERROR` spam and corrupted a sealed `host_stdout.log` in DISC-28b.
- None found in reviewed sources for a standard machine-readable community schema (not independently proven absent): no per-agent behavior mode, weapon/ammo/mode, order readback, speed modifier, movement rate or wave-class counters. Battle-AI mods tune behavior and print prose; they do not ship observability.

### Server/console surface

- Dedicated-server `help` lists `get_bot_count`/`set_bot_count`, `get_*` state getters and admin commands; WSE2 also exposes `execute_server_console_command` (3514, verified in the pinned SDK addon) for scripts. These are out-of-band sanity checks (e.g. configured bot count), not per-agent evidence, and they require a launch — C never runs them.

## Adopt / adapt / ignore for our ZDB1

| Capability | Existing tool/pattern | ZDB1 today | Recommendation |
| --- | --- | --- | --- |
| Independent engine-error stream | `rgl_log.txt` (engine log; the WSE2 `log_rgl` changelog entry is a **Lua API** rename, not the file) | we scan `host_stdout.log` and classify `SCRIPT ERROR`; D saw stdout interleaving | **Adopt (secondary):** launcher/collector should also capture the engine log tail + SHA and classify crash/error markers; ZDB1 stays primary. |
| Engine stalls / perf context | WSE2 stats overlay + `i*StatsLogInterval` periodic log | no perf context in receipts; over-sampling risk understood | **Adapt:** optional diagnostic-only WSE2 config (simulation stats + interval) captured as separate log artifact; off in normal sealed runs. |
| Probe overhead / hot spots | WSE2 profiler ops (3040-3043) + timeline | none | **Adapt (dev only):** wrap probe callbacks with `profiler_mark` during development; never required for evidence. |
| Ad-hoc tracing in probe | `print`, `table.print`, `display_message`, `display_debug_message` | ZDB1 structured `print("ZDB1|...")` lines | **Ignore for production probe:** unstructured text corrupts sealed stdout (DISC-28b). Debug strings remain a dev-only aid on a disposable build, never mixed into evidence runs. |
| Interactive AI debugging | Lua debugger (ZeroBrane/mobDebug), mission debug window | none | **Ignore for evidence** (manual/dev only); **adopt mentally** for future behavior-patch debugging sessions. |
| Out-of-band server state | console getters (`get_bot_count`, `get_*`), `execute_server_console_command` | verified via build receipt/rotation instead | **Adapt optionally:** launcher-side checks; not part of C's read-only probe and not a substitute for per-agent evidence. |
| Structured AI/combat telemetry | **none in the community** | ZDB1 is already richer: per-bot weapon/ammo/alive/weapon_mode, defender histograms, speed/time/action readback, orders 0..9, movement-rate, wave classes, refill | **Keep investing in ZDB1:** no external tool can replace it, and our gaps below are not fillable from community sources. |
| Evidence sealing / summary | **no community equivalent** | manifest verification, fail-closed summary, capability/gap model | **Keep** (differentiator). |
| Crash diagnosis | Crash-named logs exist in community reports, but **none observed on this install (D, 2026-10-24)** | `probe_failed`/`engine_errors` only | **Adopt conditionally:** if a crash-named log appears, include its tail; do not promise crash files. |
| Round/wave identity | no community tool | ledger + `g_round_start_time` gating, wave class counters | **Keep**; no reuse candidate exists. |

## Gap-by-gap verdict (why the gaps remain)

| ZDB1 gap | Could external tooling close it? | Verdict |
| --- | --- | --- |
| `behavior_mode_unavailable` (no AI-mode getter) | No. None found in reviewed sources for per-agent AI-mode readback (not independently verified as impossible); the mission debug window is manual | Keep gap; infer behavior from weapon/ammo transitions, `movement_rate`, positions, order readback (documented in task-43). |
| `native_group_orders_unavailable` (groups 26/28/29/31) | No. `team_give_order`/`team_get_*_order` take sub-class ids; community formation mods do not read back group orders either | Keep explicit unavailability; use class-order readback + positional evidence. |
| `shield_telemetry_unavailable`, `action_telemetry_unavailable`, `mounted_telemetry_unavailable` | No verified read-only ops in community headers/WSE2 SDK for our build | Keep gaps; state them in summaries; do not infer from visuals. |
| No per-agent speed readback (team 1) | **Closed in task-43** using WSE2 getters (`agent_get_speed_modifier` 2067, time/action getters) — these are WSE2/native ops, so community knowledge helped | Adopted (already). |
| Engine stdout interleaving / corruption | Partly: `rgl_log.txt` is an independent stream | Adopt as secondary artifact (bounded tail), not a replacement. |
| Probe/perf overhead | Yes, in dev: WSE2 profiler | Adapt dev-only. |
| Kill attribution ambiguity | No community tool | Keep lifetime-counter caveat + `ammo_transition`/damage-side inference; no reuse. |

## Cross-review results (D install, 2026-10-24)

D verified the above against the real install without a game launch:

- **Log paths confirmed:** live `rgl_log.txt`, rotated `Logs/rgl_log_<DD.MM.YYYY_HH.MM.SS>.txt` (23-27 KB each, newest observed `rgl_log_24.10.2026_13.20.54.txt`), and dedicated `Warband\dedicated_session_<stamp>.log` (already copied by our recorder as `logs/log_01.txt`). Use the **rotated/dedicated** file as the secondary artifact, not the per-launch overwritten live log.
- **Crash logs:** none observed across many sessions on WSE2 1.1.5.4 dedicated; keep the collector's crash-file branch but document it as conditional.
- **Stats options exist but are unverified on dedicated:** `<local>\Documents\Mount&Blade Warband WSE2\rgl_config.ini` contains `bShowSimulationStats=false`, `bShowRenderStats=false`, `iSimulationStatsLogInterval=10`, `iRenderStatsLogInterval=10`, plus `bLogSpeedModifiers=false`. They were not enabled on the pinned dedicated build; render stats are meaningless without a renderer, simulation stats are plausible but unproven. Recommendation: diagnostic runs only, via a throwaway config copy, never sealed evidence.
- **Privacy-safe attach recipe:** bounded tail (last 200 lines or <=64 KB) of the dedicated session log, optionally plus the rotated `Logs/rgl_log_*` tail; redact/exclude Windows/UNC/POSIX paths, usernames, server name/password lines, `7656119\d+` (SteamID), IPv4 except `127.0.0.1`, `Steam (API|achievement)` lines, and any `Input:`/chat/player-name lines. `bLogConnects`/`bLogChat`/`bLogIPs` could add names/IPs in a real multiplayer session, so redact before attaching. Our bundles currently only ship the recorder's own log; an extra scrubbed `engine_tail.log` is safe when bounded and redacted. Keep the artifact under gitignored `local/`/`evidence/`, compute SHA-256 of the **redacted** file, never commit or upload it, and privacy-review before sharing.
- **Additional tool notes:** `bLogSpeedModifiers=false` exists in the config and may log speed-modifier changes (untested) — a possible future engine-side cross-check for speed readback, not evidence today. `Logs/rgl_log_*` rotation is a better artifact than the live file. Module-level `module_config.ini` under `Documents\Mount&Blade Warband WSE2\ZOMBIEEE_Remaster` holds per-module settings, not diagnostics. D concurs that no community tool closes the behavior/order/shield/mounted gaps.
- **Licence/privacy:** engine logs are locally generated runtime output, not WSE2 code; attaching a scrubbed bounded tail is fine, and the WSE2 release's missing LICENSE still means link-only/no vendoring.

## Practical adoption list (no code change in this task)

1. **Evidence collector:** add optional **rotated/dedicated** engine-log capture — `Logs/rgl_log_*` and/or the dedicated session log, bounded tail (last 200 lines / <=64 KB) + SHA-256, redacted per the recipe above; SHA-256 of the redacted artifact; keep local/gitignored and never commit/upload; classify `SCRIPT ERROR`, `stack`, `crash` markers. Crash files only if present (none observed). Secondary evidence only — ZDB1 remains authoritative.
2. **Diagnostic-run config:** allow a separate, clearly labelled "stats" run with a throwaway config copy enabling `bShowSimulationStats`/`iSimulationStatsLogInterval` (and render equivalents; unverified on dedicated) to explain stalls; never mix with acceptance or sealed evidence.
3. **Dev loop:** WSE2 Lua debugger + `profiler_mark` around probe callbacks; keep `display_message`/`print` debugging out of sealed runs (DISC-28b lesson).
4. **Legal hygiene:** WSE2 has no shipping licence file in its release repo; keep everything link-only, do not vendor SDK/binary; FormAI/Motomataru and forum content remain third-party (permissions recorded in [`WARBAND_AI_MODDING.md`](WARBAND_AI_MODDING.md), sourced via E's pack).
5. **Cross-review (done):** D confirmed log paths, the rotated/dedicated artifact preference, the existence (not the dedicated efficacy) of the stats options, the absence of crash logs so far, and a privacy-safe tail recipe. Remaining open item: whether `bLogSpeedModifiers` can serve as an engine-side speed cross-check (untested). E also reviewed this draft independently (PR #30) and requested the log-naming, display_debug_message, privacy and unverified-claim fixes now folded in; E will do a final file-level pass. No C game launch.

## Bottom line

Community tooling gives us **engine logs, perf stats and interactive Lua debugging** — useful as secondary cross-checks and dev aids. It gives us **no machine-readable AI/combat telemetry at all**. Our ZDB1 probe, sealed receipts and summary already exceed what any reviewed mod/tool exposes; the right move is to adopt the engine log as a secondary artifact and the profiler for development, ignore human-facing debug prints in evidence runs, and keep closing ZDB1 gaps with verified native/WSE2 getters (as done for team-1 speed in task-43) rather than looking for a community replacement.
