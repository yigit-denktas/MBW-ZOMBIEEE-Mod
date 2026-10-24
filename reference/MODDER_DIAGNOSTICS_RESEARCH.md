# Modder diagnostics & telemetry research — reuse, adapt, ignore (task-48)

**Status: docs-only reference. Observation date 2026-10-24. Link-only: no third-party code, assets or debug strings were copied; no game launch.** This survey answers one question: what existing Warband/WSE2 modder tooling can replace or harden parts of our ZDB1 diagnostics, so we stop reinventing — and where our probe is already beyond what the community tools expose.

Baseline for comparison is our own diagnostic stack: `overlay/lua/main.lua` (ZDB1 structured events), `tools/diagnostics.py`, `tools/receipt_summary.py`, sealed receipt verification, the `SCRIPT ERROR`/engine-error classifier, and the capability/gap model in [`../docs/DIAGNOSTICS.md`](../docs/DIAGNOSTICS.md). Everything below is evidence about *external* tooling, not an acceptance claim about our build.

## Sources actually reviewed

| Source | Access / date | What it provides | Licence / reuse |
| --- | --- | --- | --- |
| [`Ruslan-700/WSE2-Releases`](https://github.com/Ruslan-700/WSE2-Releases) — README + `CHANGELOG.MD`; latest release `v1.1.5.4` published 2026-10-14 | Fetched 2026-10-24 | WSE2 feature/operation/config history: render & simulation diagnostics overlay + periodic log options, `log_rgl`, profiler operations, mission debug window, Lua debugger, `table.print` | Release repository has **no LICENSE file** (GitHub licence API returns 404); README only. Treat binaries/docs as third-party, link-only, no redistribution. |
| Local WSE2 1.1.5.4 SDK: `luaGuide.html`, `README.txt`, `EVAL_README.txt`, `header_operations_addon.py`, `module_config_template.ini` | Read locally 2026-10-24 (pinned 1.1.5.4) | Lua API and debugger/profiler documentation; `print`/`table.print`, overlays, `hookScript`, `game.fail`; config layout; `feval`/`EVAL_README` | Third-party SDK files; link-only, no copying. |
| [WSE2 forum thread 384882](https://forums.taleworlds.com/index.php?threads/warband-script-enhancer.384882/) | **HTTP 403 on 2026-10-24** (Cloudflare); recorded inaccessible | Primary WSE2 documentation pointer from `README.txt` | Not used as evidence beyond the recorded inaccessibility. |
| Native module system (community header `header_operations.py`, cross-checked with `Veehats/WarbandCoop`) | Read 2026-10-24 | `display_debug_message` 1104 (debug mode; writes `rgl_log.txt` when edit mode is enabled), `display_message` 1106, `set_show_messages` 1107; `rgl_log.txt` documented as the engine log | Opcode definitions only. |
| [Mount&Blade Modding Wiki archive — operations list](https://mbmodwiki.github.io/List_of_operations) (OLL Clan; public-domain statement; DB generated 2011 by Swyter/Theoris) | Read 2026-10-24 | Native op semantics; confirms there is no structured telemetry/AI-state API | Public domain (statement on the archive). |
| [`cvlc/tgsmod`](https://github.com/cvlc/tgsmod) FormAI/Motomataru files (`formAI_*`, `formations_*`, `header_operations.py`) | Read 2026-10-24 | Battle-AI debug style: commented-out human `display_message` strings; no machine-readable telemetry | TGS licence does **not** grant FormAI rights (Nexus permissions govern); link-only, nothing copied. |
| Dedicated-server `help` output captured locally (`local/session/dedicated_help.txt`) | Captured 2026-10-24 | Server console commands incl. `get_bot_count`, `set_bot_count`, `get_*` state getters — out-of-band state checks | Local evidence, not redistributed. |
| [ZeroBrane Studio](https://studio.zerobrane.com/) | Read 2026-10-24 | Lua IDE / `mobDebug` host used by WSE2's Lua debugger | MIT (per project site); dev-only tool, not vendored. |
| WSE2 crash-log names observed in community reports (`rgl_log_<date>_crash.txt`) via search results | 2026-10-24 | WSE2 writes crash-named log files next to the game | Community observation; verify path on our install before relying on it. |

**Inaccessible:** the TaleWorlds WSE2 thread (403). **No licence file** ships in the WSE2 releases repo, so nothing from WSE2 is bundled here; all WSE2 features are documented as external, optional tooling.

## What the existing tooling actually exposes

### WSE2 engine-side diagnostics (the usable reuse)

- **Engine log file:** stock Warband writes `rgl_log.txt` (still the canonical name; WSE2 renamed its internal `_log` to `log_rgl` in 1.1.x, and `bEditMode` messages are written there). Script errors, opcode failures and crash traces land here even when the in-game console is noisy. This is the most useful independent error stream for our sealed runs.
- **Render/simulation diagnostics:** changelog adds an on-screen overlay **and periodic log output** controlled by `bShowRenderStats`, `bShowSimulationStats`, `iRenderStatsLogInterval`, `iSimulationStatsLogInterval`. These are engine performance/stall counters, not AI state — useful to explain "probe stopped sampling" or frame hitches.
- **Profiler:** `profiler_start` (3040), `profiler_stop` (3041), `profiler_is_recording` (3042), `profiler_mark` (3043, text marker "good for analyzing individual parts of a script"), with a timeline UI and profiler binary format. This is the right tool to measure probe overhead / script hot paths, in development, not in sealed evidence.
- **Mission debug window:** `wse_mission_debug_window` mapped presentation (in-game debug UI). Manual inspection only; not automatable into receipt evidence.
- **Lua debugging:** WSE2 ships a Lua **debugger** (documented in `luaGuide.html`, `mobDebug`/ZeroBrane IDE), `print`/`table.print`, `hookScript` (can hook `game_get_console_command`), and `game.fail()`. Development-loop tools; they do not persist machine-readable state.

### Modder logging conventions (human-facing)

- `display_message` (1106) shows a coloured message to players; `display_debug_message` (1104) shows it in debug mode and writes it to `rgl_log.txt` when edit mode is enabled; `set_show_messages` (1107) toggles window messages.
- This is the dominant community pattern for "debug output" (FormAI/Motomataru scripts contain commented-out `display_message` debug strings; battle-AI mods print human sentences). It is **unstructured text**, exactly the class of output that interleaved with our `SCRIPT ERROR` spam and corrupted a sealed `host_stdout.log` in DISC-28b.
- No standard community schema exists for AI/combat telemetry: no per-agent behavior mode, weapon/ammo/mode, order readback, speed modifier, movement rate or wave-class counters. Battle-AI mods tune behavior and print prose; they do not ship observability.

### Server/console surface

- Dedicated-server `help` lists `get_bot_count`/`set_bot_count`, `get_*` state getters and admin commands; WSE2 also exposes `execute_server_console_command` (3514) for scripts. These are out-of-band sanity checks (e.g. configured bot count), not per-agent evidence, and they require a launch — C never runs them.

## Adopt / adapt / ignore for our ZDB1

| Capability | Existing tool/pattern | ZDB1 today | Recommendation |
| --- | --- | --- | --- |
| Independent engine-error stream | `rgl_log.txt` / WSE2 `log_rgl` | we scan `host_stdout.log` and classify `SCRIPT ERROR`; D saw stdout interleaving | **Adopt (secondary):** launcher/collector should also capture the engine log tail + SHA and classify crash/error markers; ZDB1 stays primary. |
| Engine stalls / perf context | WSE2 stats overlay + `i*StatsLogInterval` periodic log | no perf context in receipts; over-sampling risk understood | **Adapt:** optional diagnostic-only WSE2 config (simulation stats + interval) captured as separate log artifact; off in normal sealed runs. |
| Probe overhead / hot spots | WSE2 profiler ops (3040-3043) + timeline | none | **Adapt (dev only):** wrap probe callbacks with `profiler_mark` during development; never required for evidence. |
| Ad-hoc tracing in probe | `print`, `table.print`, `display_message`, `display_debug_message` | ZDB1 structured `print("ZDB1|...")` lines | **Ignore for production probe:** unstructured text corrupts sealed stdout (DISC-28b). Debug strings remain a dev-only aid on a disposable build, never mixed into evidence runs. |
| Interactive AI debugging | Lua debugger (ZeroBrane/mobDebug), mission debug window | none | **Ignore for evidence** (manual/dev only); **adopt mentally** for future behavior-patch debugging sessions. |
| Out-of-band server state | console getters (`get_bot_count`, `get_*`), `execute_server_console_command` | verified via build receipt/rotation instead | **Adapt optionally:** launcher-side checks; not part of C's read-only probe and not a substitute for per-agent evidence. |
| Structured AI/combat telemetry | **none in the community** | ZDB1 is already richer: per-bot weapon/ammo/alive/weapon_mode, defender histograms, speed/time/action readback, orders 0..9, movement-rate, wave classes, refill | **Keep investing in ZDB1:** no external tool can replace it, and our gaps below are not fillable from community sources. |
| Evidence sealing / summary | **no community equivalent** | manifest verification, fail-closed summary, capability/gap model | **Keep** (differentiator). |
| Crash diagnosis | WSE2 crash-named logs (`rgl_log_*_crash.txt`, community reports) | `probe_failed`/`engine_errors` only | **Adopt:** collector should include crash-named log files and tails when present; classify, never silently drop. |
| Round/wave identity | no community tool | ledger + `g_round_start_time` gating, wave class counters | **Keep**; no reuse candidate exists. |

## Gap-by-gap verdict (why the gaps remain)

| ZDB1 gap | Could external tooling close it? | Verdict |
| --- | --- | --- |
| `behavior_mode_unavailable` (no AI-mode getter) | No. WSE2 exposes behavior setters/viewers but no per-agent AI-mode readback; debug window is manual | Keep gap; infer behavior from weapon/ammo transitions, `movement_rate`, positions, order readback (documented in task-43). |
| `native_group_orders_unavailable` (groups 26/28/29/31) | No. `team_give_order`/`team_get_*_order` take sub-class ids; community formation mods do not read back group orders either | Keep explicit unavailability; use class-order readback + positional evidence. |
| `shield_telemetry_unavailable`, `action_telemetry_unavailable`, `mounted_telemetry_unavailable` | No verified read-only ops in community headers/WSE2 SDK for our build | Keep gaps; state them in summaries; do not infer from visuals. |
| No per-agent speed readback (team 1) | **Closed in task-43** using WSE2 getters (`agent_get_speed_modifier` 2067, time/action getters) — these are WSE2/native ops, so community knowledge helped | Adopted (already). |
| Engine stdout interleaving / corruption | Partly: `rgl_log.txt` is an independent stream | Adopt as secondary artifact (bounded tail), not a replacement. |
| Probe/perf overhead | Yes, in dev: WSE2 profiler | Adapt dev-only. |
| Kill attribution ambiguity | No community tool | Keep lifetime-counter caveat + `ammo_transition`/damage-side inference; no reuse. |

## Practical adoption list (no code change in this task)

1. **Evidence collector:** add optional `rgl_log.txt`/`log_rgl` capture (tail + SHA-256 + crash-named files) alongside the sealed bundle; classify `SCRIPT ERROR`, `stack`, `crash` markers. Secondary evidence only — ZDB1 remains authoritative.
2. **Diagnostic-run config:** allow a separate, clearly labelled "stats" run with `bShowSimulationStats`/`iSimulationStatsLogInterval` (and render equivalents) to explain stalls; never mix with acceptance evidence.
3. **Dev loop:** WSE2 Lua debugger + `profiler_mark` around probe callbacks; keep `display_message`/`print` debugging out of sealed runs (DISC-28b lesson).
4. **Legal hygiene:** WSE2 has no shipping licence file in its release repo; keep everything link-only, do not vendor SDK/binary; FormAI/Motomataru and forum content remain third-party (permissions recorded in [`WARBAND_AI_MODDING.md`](WARBAND_AI_MODDING.md), sourced via E's pack).
5. **Cross-review:** D should confirm on a real install which WSE2 log/stats options exist for our pinned 1.1.5.4 dedicated build, and whether crash-named log files appear in the `local/session` layout. No C game launch.

## Bottom line

Community tooling gives us **engine logs, perf stats and interactive Lua debugging** — useful as secondary cross-checks and dev aids. It gives us **no machine-readable AI/combat telemetry at all**. Our ZDB1 probe, sealed receipts and summary already exceed what any reviewed mod/tool exposes; the right move is to adopt the engine log as a secondary artifact and the profiler for development, ignore human-facing debug prints in evidence runs, and keep closing ZDB1 gaps with verified native/WSE2 getters (as done for team-1 speed in task-43) rather than looking for a community replacement.
