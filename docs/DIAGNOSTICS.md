# End-of-development diagnostic recorder (v0.1.8)

**No step-by-step game testing required.** Continue development and local static verification normally. After the final build is ready, play one private WSE2 session, exit the game, and run the collector once. It packages evidence for later analysis rather than making you troubleshoot each intermediate build.

## What is recorded

- Versioned ZDB1 events written by the Lua overlay to WSE2's existing engine log: startup, compiled trigger count, hook registration, invasion mission entry, host/client role, total agent count and optional survivor team-0 / zombie team-1 counts when WSE2 exposes the team getter, and a heartbeat every 15 seconds (maximum 480). The probe is read-only.
- Up to 25 existing engine logs from WSE2/Warband game and Documents folders, plus explicitly supplied custom logs. Up to 8 MiB per log: on larger logs, the first 256 KiB and final ~7.75 MiB are retained with an explicit truncation marker, preserving startup and crash context. Source filenames and modification times are recorded.
- OS version/architecture, Python version, remaster version, source archive SHA-256, WSE2 target, experimental defender count, and installed module file SHA-256 hashes (without distributing mod assets).
- Session metadata, extracted events.jsonl, SHA-256 manifest, and integrity verification that rejects altered ZIP entries.
- Best-effort redaction of credentials, email addresses, IP addresses, Steam IDs and user-home paths. No unredacted logs, memory dumps or automatic uploads.

**Privacy limitation:** player names, chat, unusual identifiers and sensitive scene names might survive. Inspect the ZIP before sharing. Raw logs remain on your computer and evidence bundles are never uploaded automatically.

## One command, only at the end

After installing the game and final remaster, close Warband and run from the repository root on Windows:

    .\tools\Collect-Diagnostics.ps1 -WarbandRoot 'C:\Program Files (x86)\Steam\steamapps\common\MountBlade Warband' -Session final-solo

Produces timestamped local files under evidence/: ZOMBIEEE-evidence-*.zip and ZOMBIEEE-report-*.md. It does not launch Warband, install CI or send data over the network. If WSE2 uses an unusual log location, add -AdditionalLogs @('C:\path\to\custom.log').

For subsequent investigations, all offline:

    py -3 tools\diagnostics.py verify .\evidence\some-evidence.zip
    py -3 tools\diagnostics.py analyze .\evidence\some-evidence.zip --report .\evidence\report.md
    py -3 tools\diagnostics.py compare .\evidence\first.zip .\evidence\second.zip

Pass comparison ZIP paths explicitly, in chronological order. Comparison reports recurring, new and resolved error codes across builds.

## Analyzer rule catalogue

| Code | Meaning |
| --- | --- |
| R001 | Missing BRF/resource; inspect archive CRC and referenced assets |
| R002 | Fatal exception or crash; inspect nearby native log lines |
| R003 | Compiled script/operation error |
| R004 | WSE2 Lua failure |
| R005 | Missing texture, sound or other media |
| R010 | No logs to diagnose |
| R011 | Lua bootstrap event absent |
| R012 | No invasion entry despite bootstrap event |
| R013 | Mission entered but heartbeat absent |
| R014 | Wrong trigger count (25 original, 26 with defenders, 27 with tactical positions, 29 with wave reinforcements, 31 with recovery) |
| R015 | Logs older than seven days, potentially unrelated |
| R016 | WSE2 Lua diagnostic hook failed to register |
| R017 | Installed module manifest missing; cannot correlate build and runtime |
| R018 | Experimental allied team absent across sampled server frames while zombies exist |

**Conservative interpretation:** errors are evidence; an error-free report is inconclusive, not proof that zombies, friendly bots, waves, weapons, or multiplayer work. Final gameplay verification is still required once the implementation is complete.

Local tests: python -m unittest discover -s tests -v. No CI. Original Beta 0.4 only; ZOMBIEEE2 excluded.

## Team-count limitations

The mission probe uses WSE2's documented agent iterator. If the optional native team getter is unavailable, team0/team1 are reported as -1, **not zero**. The analyzer records team-data availability and never diagnoses missing allies from unavailable metrics. When at least two server-side samples show team 0 empty while team 1 is populated, it flags a *candidate* ally-spawn issue (R018), not a proven cause. Bot combat competence, navigation and wave victory still require the final game session.

The guarded installer also stores `archive_crc_verified`, `original_mission_trigger_count` and `final_trigger_count`. The evidence pack includes only allowlisted build metadata plus SHA-256 hashes of installed module files, so a later report can distinguish an unknown archive from a modified installation. None of the mod assets are included.

## Scene overlay receipt

The v0.1.4 installer records `final_trigger_count=27` if `--city-guardposts` is active. Original City data still has 226 objects; a patched copy has 229. The existing module fingerprint captures the modified `mission_templates.txt`, while the unmodified original archive remains untouched. Read the [City defence overlay](CITY_DEFENSE.md) for source-derived entry coordinates and offline checks.

## v0.1.5 build provenance

The collector fingerprints `variables.txt` (including the optional reinforcement sentinel) and all five original `SceneObj/scn_tbfc_invasion_*.sco` scene files in addition to the compiled mission, troop data, and Lua bootstrap. It does **not** package original game assets. The actual `final_trigger_count` is recorded by the installer for 25/26/27/29 variants. At final runtime test, compare the installed build fingerprint with that manifest before assuming the wrong code is running.

## v0.1.8 tactical and movement observability

The recorder now tries to read wave_number, g_round_ended, zdr_last_reinforced_wave and zdr_defence_mode from WSE2's documented game.gvar interface. If a global is missing, it records -1: not available. It emits a bounded heartbeat every 15 seconds, plus wave_change and tactical_change events.

Optional agent_sample records only reserved AI survivor divisions (5–7), when WSE2 exposes the necessary operation getter functions: agent ID, group, current tactical mode and rounded game-world X/Y. It records at most 16 bots per heartbeat. **This position function may be unavailable without WSE2 Module System headers**; missing samples are reported as unknown, not as a false stuck-agent diagnosis.

New analyzer rules: R019 candidate stalled wave (>=9 heartbeats on one wave while zombies remain), R020 rapid fallback/regroup oscillation, R021 apparent failure to regroup despite healthy-looking team-0 counts, R022 unusually stationary defenders *after* a tactical state change. These are conservative heuristics, never proof of causality. Static hold-position behaviour without a new order should not generate R022.

The full experimental build receipt records final_trigger_count=31 plus the tactical low/high thresholds. Original assets, executable and the RAR are still excluded from Git and from diagnostic bundles. [Tactical recovery design](TACTICAL_RECOVERY.md).

## v0.1.8 native command and AI combat forensics

A locally authored minimal `overlay/lua/msfiles/header_operations.py` maps only read-only Warband native getters that our WSE2 Lua telemetry uses. The runtime attempts `combat_sample` (agent/group/wave/known weapon ID/ammo/kill count) and `command_exec` events from native command counter increments, up to 16 non-player reserved-group defenders every 15 seconds. No real player coordinates or names are required. Unavailable native operations are recorded as unknown.

New offline codes: **R023** candidate ammunition depletion, **R024** prolonged engagement with no observed defender kill increments, **R025** hotkey execution inconsistent with build receipt, **R026** missing AI combat observability. The final JSON and Markdown reports include an **acceptance evidence matrix** for engine startup, mission entry, zombie waves, allied agents, combat activity, fallback/regroup and private commands. Unknown does not mean failed or passed. An error-free log is not proof of playability. [Full forensic reference](FORENSIC_DIAGNOSTICS.md).


## Dedicated bot-count configuration is not bot telemetry

The v0.1.8 probe now emits `|opmeta=1` in `recorder_capabilities` and adds
`game_type` (`g_multiplayer_game_type`), `ready_for_spawn`
(`g_multiplayer_ready_for_spawning_agent`), `bots_team1`
(`g_multiplayer_num_bots_team_1`) and `round_start` (`g_round_start_time`)
next to the existing tactical `mode` (`zdr_defence_mode`), which is never the
game type. These are read-only `game.gvar` reads; a missing global is `-1`
(unknown), never 0.

**First observed enemy wave (2026-10-24, merged `main@4c56242` rebuild):** an
unconfigured dedicated rotation produced `team1=0 wave=0` while the corrected
probe already reported `role=server`, `game_type=7`,
`ready_for_spawn=1`. Adding the 1-based second-team bot count to the
dedicated rotation (`set_bot_count 2 32`) produced
`agents=42 team0=1 team1=41 wave=1` and a `wave_change` event. The earlier
absence of team-1 agents was therefore a dedicated rotation configuration
gap, not a build or probe artefact.

`bots_team1` is the `g_multiplayer_num_bots_team_1` global and stayed 0 even
while team 1 held 41 agents: the rotation command is 1-based
(`set_bot_count 2 ...` addresses the enemy team) while that global names the
first team. **Do not read `bots_team1=0` as "no enemy bots"** and never infer
population from it — the measured `team1` agent count is the only evidence.
The launcher/installer must establish bot counts before `start` (B's lane).
One observed `wave=1` is not wave completion, AI combat or gameplay
acceptance.

**Respawn/round commands and sampling resolution (2026-10-24 follow-up):** a
second dedicated attempt added `set_respawn_period 5`,
`set_defender_spawn_count 0`, `set_round_max_seconds 1800` and
`set_player_respawn_as_bot 0`. The dedicated server's own help describes these
only as "sets respawn period", "sets maximum seconds for round", etc., with
no printed unit, and the 15 s heartbeat cannot resolve a 5 s respawn: a death
plus immediate respawn is invisible between samples. The attempt did show
repeated new rounds (`round_start` 28 -> 61 -> 133 -> 228 -> 317, `wave`
resetting to 0 and `team1` repopulating each round), one explicit
`round=1` (`g_round_ended`) marker, and the player's team-0 agent present from
heartbeat 3 through 21. It did **not** sample a `team0=0 -> 1` transition
while connected, so it measures neither respawn latency nor a death/respawn
cycle; round restarts (~33-95 s apart) ended well before the 1800 s limit, so
they were game-mode ends. The final `team0=0` over ~45 s is four times the
configured 5 s period and coincides with client exit, so "died and quit in a
respawn window" cannot be distinguished from "left before the new round"
(`exit_code_observed=false` in passive mode). Do not read `team0=0` as a
death, and keep the generic `set_bot_count` roster (Crazed Civilian, issues
#13/#14) separate from native zombie troops.

**Sealed receipt completeness caveat:** in that attempt the stored redacted
`logs/log_01.txt` was a strict prefix of the engine log, missing its final
appended line, while `recorder.json` reported `log_seen_bytes=[15172]` and
`log_omitted_bytes=[0]`. Integrity still verified, but the receipt slightly
overstates log completeness: the same terminal-write race class as the
atomic-replace issue #15. Treat the last poll window as possibly absent and
never infer completion from `log_omitted_bytes=[0]` alone. The engine log also
carries no probe stream at all: host stdout stays outside the bundle (issue
#16).

## Telemetry v2: troop histogram, lifecycle events and receipt summary

The ZDB1 probe (overlay `0.2.0`, `|opmeta=1`) now emits, in `mission_enter`
and every heartbeat, a bounded per-team troop histogram: `troops_team0/1=id:count,...`,
`troop_names_team0/1=id:label,...`, `troop_ids_unknown=N` and
`troops_truncated=N`. At most 12 distinct troops and 400 characters per team;
labels come only from the bounded `lua/msfiles/ID_troops.py` table (13
documented roster ids, 32-character sanitized names), never from a guessed
string opcode - an unknown id or a different module version stays numeric and
is counted as unknown rather than mislabelled. A missing troop getter reports
`-1`.

Explicit lifecycle events are emitted only from observed transitions and only
for `role=server`: `player_joined` (first alive team-0 non-player agent),
`player_died` (previously alive agent observed dead), `player_left` (previously
alive agent removed; NOT classified as death or disconnect), `player_respawned`
(new alive player after an observed absence), `round_started` (`round_start`
identity changed) and `wave_started` (wave transition to >= 1). Each carries
`observed=...` plus wave, round_start, team counts, game_type, ready_for_spawn
and bots_team1. 15 s sampling cannot resolve a 5 s respawn: a death and
immediate respawn between samples emits nothing, so absence of an event is not
absence of a death. `wave_change` and `tactical_change` remain for compatibility.

`python tools/diagnostics.py summary <sealed-session-dir-or-attempt-dir> [--json]`
verifies the recorder manifest first (exact file set, safe paths, no symlinks,
SHA-256) and fails closed with exit code 2 on tampering. It then reports
session/attempt/outcome, probe `opmeta`/role/game_type/ready_for_spawn,
max/last team counts, the union troop histogram with labels and bounds,
observed waves/rounds, lifecycle events, engine-error counts by class (no raw
text) and explicit evidence gaps: `zdbi_stream_not_sealed`, passive
`exit_code_observed=false`, unknown engine runtime, and log
truncation/omission/poll failures. It never reports `runtime_verified=true`.

The ZDB1 stream can only be read when the launcher/recorder seals
`host_stdout.log` into the session directory (B `HostSession` +
`PassiveRecorder.add_artifact` before the signed stop); a passive attach alone
cannot capture another process's stdout, and attempts 7/8 sealed no ZDB1
stream at all.

## Playerless AI-vs-AI team composition

The v2 probe also reports per-team agent composition in `mission_enter` and
every heartbeat: `humans_team0/1`, `players_team0/1` (human, non-AI agents),
`bots_team0/1` (human AI agents), `horses_team0/1`, plus `alive_players_team0`
for lifecycle context. `agent_is_horse` does not exist in this engine/WSE2
surface, so the bounded fallback is the native type predicate
`agent_is_human` (opcode 1704, declared as can-fail; corroborated by the
original compiled mission templates where it appears 67 times as a
one-argument boolean agent condition and is always followed by troop-id or
troop-name operations): human == false is counted as a horse, human == true +
non-player is a bot, human == true + player is a human. A missing predicate
leaves that category `-1` (unknown), never 0. Category counts are
per-agent-iteration (spawned agents), so a category may include agents that are
not currently alive; lifecycle events still use explicit alive predicates.

Composition labels extend the bounded `msfiles/ID_troops.py` roster aid with
the observed ids: `874=trp_invaderb_multiplayer_ai`,
`32=trp_mercenary_horseman`, `33=trp_mercenary_cavalry` (16 documented entries
total). Labels remain an aid: ids outside the table stay numeric and are
counted in `troop_ids_unknown`.

Engagement and position evidence is emitted in the same heartbeat/mission_enter
line: `no_player` (1/0/-1), `alive_team0/1`, `kills_team0/1` (sum of
`agent_get_kill_count` over observed agents per team), `pos_team0/1` (centroid
`x:y` of sampled non-player bots), `bbox_team0/1` (`min_x:min_y:max_x:max_y`)
and `pos_sampled_team0/1`. Positions are read only for non-player bots through
position register 90, never for a human player; at most 8 bot samples per
heartbeat are emitted as `ai_sample` events (`team/id/x/y/kills/wave/tick`). A
missing position/kill/alive getter, or no successful sample, leaves the
aggregate `-1`/`none` (unknown), never 0.

Field naming: the pre-existing `bots_team1` ZDB1 field is the native
`g_multiplayer_num_bots_team_1` global and is kept for backward compatibility;
AI bot counts per team use `bot_agents_team0/1`, so the two meanings never
collide. The receipt summary exposes the stable no-client harness keys:
`no_player` (bool or null), `teams` with `max_team0/max_team1`,
`bots_team0/1`, `horses_team0/1`, `alive_team0/1`, `positions.{team0,team1}`
(bounded centroid + spread bbox + sampled/distinct bots + `moving_bots`
derived from `ai_sample` displacement), `engagement.{kills_team0,kills_team1}`
(absent -> null, never 0-as-unknown) and `events` (ZDB1 line count, sealed
flag, bounded event-type counts). `player_*` lifecycle events remain
observed-only and are reported as absent, not zero, in playerless mode.

### Probe runtime hardening (v3 hotfix)

Two runtime bugs in the v3 composition code were caught by live evidence and
fixed with real-Lua-semantics tests:

* **Team-indexed tables must be 0-based.** A Lua literal `{0, 0}` creates only
  indices 1 and 2, so `humans[0] + bots[0]` threw `attempt to perform
  arithmetic on a nil value` and the whole `sample_world()` returned
  `ok=false` (every composition/position/kill field `-1` on all heartbeats).
  All per-team tables are now declared `{[0] = ..., [1] = ...}`.
* **Parenthesise arithmetic before concatenation.** `a .. b - c` parses as
  `(a .. b) - c`; `players_team0/1` now use
  `(world.humans[0] - math.max(world.bots[0], 0))`.
* Position-object field access is entirely inside `guarded_call` (a WSE2 pos
  userdata can throw on field access), and a failed `sample_world` now emits a
  bounded `probe_failed|kind=sample_world|error=...` instead of silently
  returning all `-1`.

`tests/test_flight_lua_semantics.py` executes the exact constructor/arithmetic
constructs on the bundled Lua 5.1-ABI interpreter (skipped when the local dll
is absent) and asserts the source keeps the verified forms.

**Round identity:** `g_round_start_time` is the mission time at round start,
but on an idle-client build it was observed increasing by ~15 s per heartbeat
(15, 30, 45, ...). Emitting `round_started` for every change produced false
events, so the probe now emits it only for a real transition: a clock reset
(`round_start` decreased) or an observed round-end transition
(`g_round_ended` 1 -> 0). A monotonic increase is reported **once** as
`probe_anomaly|kind=round_start_monotonic`, never as a round. The summary
counts a raw heartbeat `round_start` only when the value is stable across
samples, adds `rounds.identity_unstable` and the `round_identity_unstable`
evidence gap on the anomaly, and never reports a monotonic series as rounds.

### Division telemetry (`agent_get_group`) and hold-order observability

The probe now reports bounded per-team division counts in the heartbeat:
`groups_team0/1=group:count,...` (at most 12 groups/team, same bounded helper as
the troop histogram) for non-player bots, `group_read_unknown`, and a
`group=` field on each bounded `ai_sample`. `agent_get_group` (opcode 1765) is
verified against the original compiled scripts, where it appears as
`is_human; is_alive; agent_get_group <dest> <agent>`.

The summary adds `divisions` with `team0`/`team1` bounded group histograms,
`sampled_team0/1` group counts from `ai_sample`, `read_unknown`,
`defender_groups_observed` (divisions 5-7 on team 0), `defender_divisions_observed`
and `defenders_sampled` (whether any `combat_sample` was sealed). Absent
defender divisions raise `defender_divisions_unobserved`; unreadable groups
raise `division_reads_unreliable`.

**Division-getter safety (DISC-28 update):** the earlier convention probe
passed a lhs placeholder `0` and the engine bound it as an agent id, spamming
`SCRIPT ERROR: Invalid Agent ID: 0` (6,575 times) and corrupting sealed stdout.
The reader now follows strict rules: it **never calls an agent opcode with a
fake/zero agent**, it is **deferred until a full round is running** (heartbeat
with `round_start>0` and `ready_for_spawn>0`, never the pre-round/entry
trigger), it uses only the **direct single-argument** call, it **caches the
convention one-shot**, and it treats a returned value equal to the agent id as
an echo (wrong convention) instead of a division. If detection is impossible it
emits one `probe_capability|group_convention=unknown` and one bounded
`probe_anomaly|kind=group_convention_unknown`; the summary then reports
`divisions.convention=unknown` plus the `group_convention_unknown` gap and the
honest fallback (`defender_division_unreadable`, defenders still observable via
troop ids 981-984). A write-based set/read **round-trip** is intentionally not
performed by this read-only probe (it would mutate AI divisions inside the
evidence run); that verification belongs to the launcher/native lane, and until
it confirms the convention the division values remain observation-only and
`hold_behavior_observed` stays false.

**Division-getter convention (DISC-28):** `agent_get_group` (1765) is a
condition-style lhs op in some WSE2 builds: it returns
`(boolDidNotFail, intResult, intError)` instead of `(intResult, intError)`.
The shared accessor now decodes both shapes, and the dedicated `read_group`
probes the working call convention once (`(0, agent)` lhs call, then
`(agent)` direct), caches it, validates `0..255`, and emits a single bounded
`probe_anomaly|kind=group_unreadable` plus `probe_capability|group_convention=`
if nothing works. If divisions genuinely cannot be read, the summary reports
`defenders.division_source="unavailable"` with the
`defender_division_unreadable` gap (defenders may still be observed via their
981-984 troop ids) and never invents a division or hold claim.

**Troop-id defender fallback (native groups):** live evidence shows native
defender bots in groups 26/28/29/31 rather than 5-7, so a divisions-only filter
hides their positions. The probe and summary therefore classify team-0
non-player bots as defenders when either the division is 5-7 **or** the troop id
is in the native defender roster **981-984**: `sample_defenders` samples
position/group/troop/alive/kills for them regardless of group, heartbeat
`defender_source=group|troop-fallback` plus a bounded `defender_groups`
histogram are emitted, and `ai_sample` carries `troop=` and `defender=1`.
The summary reports `defenders.division_source`
(`group`/`troop-fallback`/`unavailable`) and `defenders.groups` from those
samples, so `positions_sampled`, `distinct_positions`, `guard_entries_reached`,
`moving` and `hold_samples` become observable even when adoption into 5-7 never
took effect. It never fabricates a 5-7 division, never claims hold behaviour
(`hold_behavior_observed=false`), and keeps `defender_divisions_unobserved` /
`defender_division_unreadable` gaps honest.

### Per-bot combat, loadout and wave-class telemetry (combat v2)

`ai_sample` and `combat_sample` now carry bounded per-bot combat fields for
non-player bots: `weapon` (`agent_get_wielded_item`), `ammo`
(`agent_get_ammo`), `alive` (`agent_is_alive`), `group`, `troop`, `kills` and a
derived `weapon_mode` = `ranged` (ammo > 0) / `melee` (ammo == 0 with a known
weapon) / `unknown`. Heartbeats aggregate `defender_weapons`,
`defender_modes`, `ranged_team0`, `melee_team0`, `defender_ids` and a cumulative
`defender_deaths` (bounded, observed alive-defender ids disappearing within the
same round; a new round resets the baseline and does not count as deaths).
`defender_died` events carry the observed id. The summary exposes
`defenders.weapons`, `weapon_modes`, `weapon_mode_observed`,
`ranged_agents_team0`, `melee_fallback_team0`, `alive_samples`, `ammo`,
`deaths`, and `engagement.defender_kills` / `defender_deaths` so defender kills
can be read against observed defender deaths (lifetime counters remain
explicitly non-per-wave attribution).

`shield`/block capability, current action and mounted-rider identity have no
verified read-only WSE2 operation in this mod (capability line reports
`shield_getter=0`, `mounted_getter=0`, `action_getter=0`): those fields stay `-1`
and the summary raises `shield_telemetry_unavailable`,
`action_telemetry_unavailable`, `mounted_telemetry_unavailable` instead of
guessing. Team-1 horses are counted and their agent ids exposed as
`horse_ids_team1` (bounded, max 8); `mounted_team1` is only reported when the
engine exposes it. Wave-1 telemetry adds `waves.wave1` with a bounded team-1
troop-class breakdown (`generic`/`native_zombie`/`defender`/`survivor`/
`unknown`), so a strong native/mounted wave-1 can be proven from sealed
evidence without a gameplay claim. All fields are bounded; unknown remains
unknown, never zero.

### Task-43 follow-up: team-1 speed, full order scope, ammo-transition inference

D's task-42 sealed runs exposed three readback gaps, now closed:

- **Team-1 zombie speed was unreadable** (`defender_speed_modifiers` covered only
  defenders, and `ai_sample` rows lacked speed keys). The probe now reads
  `agent_get_speed_modifier` (2067), `agent_get_time_speed_multiplier` (3336)
  and `agent_get_action_speed_modifier` (3341) for **every non-player bot**,
  emitting per-team histograms `speed_modifiers_team0/1`,
  `time_multipliers_team0/1`, `action_speeds_team0/1` plus unknown counters.
  `ai_sample` now carries `speed=`, `time_multiplier=`, `action_speed=` for each
  sampled bot, so A's 70% team-1 slowdown is verifiable from a sealed run.
  Missing team-1 readback raises `speed_readback_team1_unavailable`.
- **Order readback scope:** `defender_orders` now reads all team-order
  sub-classes `0..9` (not only 5-7/9) and the heartbeat states
  `defender_orders_scope=team0_subclasses_0_9_native_groups_no_op`. Native bots
  observed in groups 26/28/29/31 are outside the class range;
  `team_give_order` has no grouping-by-agent-group form, so native-group orders
  are **exactly unavailable** and the summary raises
  `native_group_orders_unavailable` instead of pretending to confirm them.
- **Melee-last-resort inference:** the summary now reports
  `defenders.ammo_transition` (`samples`, `agents`, `agents_with_ammo`,
  `agents_empty`, `melee_after_empty_observed`) derived from per-agent
  `ammo > 0 -> 0` transitions plus `weapon_mode=melee`. This is an inference,
  not a direct AI-mode getter; the note records that explicitly.

### Invalid Agent ID: 0 guard (P0, trigger 32 conditions)

Client/pre-round heartbeat condition callbacks could yield agent id 0 from
`game.agentsIt()`; direct agent ops then logged
`SCRIPT ERROR: Invalid Agent ID: 0` at `Trigger [32] Conditions (Lua)`.
Every agent read helper now rejects non-number/<=0 ids **before** calling an
engine op: `read_agent_number` (already), `is_alive` -> false, `is_npc` -> false,
`is_human` -> nil, `agent_position` -> nil, `read_group` (already). The
recorder capability line reports `invalid_agent_guard=1` so D can confirm the
fixed probe. Regression tests: static guard/capability surface plus real-Lua
valid-id checks (0/negative/non-number are rejected; valid >0 accepted).
This is separate from the trigger-14 `-1` faction guard and the faction-id 16
raw-operand fix.

### Requested fire mode echo (task-68 consumer side)

`tools/receipt_summary.py` accepts an optional external launcher receipt
(`--launcher-receipt PATH`, schema `zombieee.city-launch-receipt.v1`; also
auto-discovered at `<evidence-root>/launches/<session_id>/launch-receipt.json`
from `<evidence-root>/flights/<session_id>`). It exposes only the requested
configuration under top-level `session.fire_mode*`:
`fire_mode`, normalized `fire_mode_scope="pre-game-session-only"`,
`fire_mode_source="requested_build_or_launcher"`, `fire_mode_applied`,
`fire_mode_manual_switch_supported=false`, and the tuning-only semantics string.
The sidecar is not signed evidence; absence is `null`/unknown and is not a gap.
It is never merged into `firearms.*`; `session.fire_mode_mismatch` and the
`fire_mode_requested_observed_mismatch` gap appear only when both the requested
mode and observed `fire_modes_observed` exist (ai is compared with wave%3
expected labels; fixed modes against the observed label). Diagnostic only.

### Firearm telemetry (task-60)

**Accuracy/reload modifiers and fire-mode labels (task-59/60):** the probe
also reads WSE2 `agent_get_accuracy_modifier` (2066) and
`agent_get_reload_speed_modifier` (2068) per sampled bot (ai_sample and
combat_sample), with capability flags `accuracy_getter`/`reload_getter`.
`firearms.team0/1` exposes `accuracy_modifiers`, `reload_speed_modifiers`,
`attack_action_transitions`, `release_actions`, `reload_actions`, and
`fire_modes_observed` — the latter is a **label inferred** by matching the
observed accuracy/reload pair against A's documented policy (single 150/120,
burst 135/145, auto 115/165), compared with `wave % 3` as
`fire_mode_expected` / `fire_mode_match_samples` / `fire_mode_mismatch_samples`.
It is **not** an engine single/burst/auto mode readback; no such getter exists.
The item-accuracy build patch and manual/reticle UI state are not runtime
readable here, so `item_accuracy_patch`, `manual_fire_mode`, `reticle_width`,
`target_icon_width`, `player_accuracy_state` and `aim_error_proxy` stay `None`
with explicit gaps (`item_accuracy_patch_receipt_only`,
`manual_fire_mode_unavailable`, ...).



Per-bot `attack_action` (`agent_get_attack_action`, 1763; declared lhs) is now
sampled in `ai_sample` and `combat_sample` alongside weapon/ammo. The summary
adds `firearms.team0`/`team1` with observed:

- `samples`, `agents`, `agents_with_shots`, `weapon_ids`;
- `shots_observed`, `ammo_burn`, `reloads_observed` — **inferred from ammo
  decreases/increases between samples**, not from an engine shot event;
- `shot_intervals_ticks` (count/min/avg/max) in sample tick units; a reload
  resets the interval baseline; wall-clock cadence is unknown;
- `kills_delta_observed` and `shot_to_kill_ratio` (lower bound; no hit counter);
- `attack_actions` histogram (0 free, 1 readying, 2 releasing, 3 completing,
  4 parried, 5 reloading, 6 after release, 7 cancelling).

Unavailable fields stay `None` with explicit gaps:
`shot_telemetry_ammo_delta_only`, `hit_telemetry_unavailable`,
`aim_error_unavailable`, `reticle_telemetry_unavailable`,
`weapon_fire_mode_unavailable`, `player_accuracy_state_unavailable`, and
`attack_action_unavailable` when no action samples exist. There is no verified
readable fire-mode, reticle/target-icon width, player accuracy-state or
aim-error getter in this build; the probe capability line reports
`accuracy_getter=0|reticle_getter=0|aim_error_getter=0|fire_mode_getter=0`.
Never report inferred shots as hit/accuracy evidence.

### Task-55 P0: wave-table faction-slot and scene readback

**Faction-id and error-spam guard (2026-10-24 follow-up):** WSE2 Lua's
`faction_get_slot` expects the **raw faction id** (16 for the invader faction),
not the encoded module operand (`432345564227567632`). Passing the encoded value
caused repeated `SCRIPT ERROR: Invalid Faction ID: -2147483648` from the probe's
Lua trigger condition callbacks (trigger 31/32 Conditions (Lua), opcode 522).
The probe now (a) uses raw `FACTION_INVADER = 16`, (b) validates faction 0..63
and slot 0..255 before any call, and (c) enables the readback only on a
server-side `mst_multiplayer_iv` heartbeat (`wave_slot_read_enabled`), never
from the pre-round/entry condition callback. Regression coverage:
`tests/test_flight_lua_msfiles.py` static guards and
`tests/test_flight_lua_semantics.py` no-call-on-invalid-operand checks.



To separate "the City trigger wrote 894" from "the engine kept original/wave
values" (DISC-59: static trigger/flags present but runtime still showed 896 and
speed 100), the probe now reads, read-only:

- **Wave-table faction slots** `200, 221, 231, 241` plus control slot `245` from
  invader faction 16 via `faction_get_slot` (522, declared lhs). Values are
  troop references decoded to troop ids (e.g. `200:894`); unknown/raw values are
  kept as-is, never inferred. Emitted as `wave_faction_slots=slot:troop,...`;
  the summary exposes `waves.faction_slots` and `waves.slots_slow` (all four
  probe slots == 894), with the `wave_slot_readback_unavailable` gap when absent.
- **Current scene** via `store_current_scene` (2211, declared lhs), emitted as
  `current_scene=` and exposed as `waves.current_scene`, so the trigger's
  scene-condition assumption can be checked against the runtime scene id.
- **Team-1 speed/time readback** already exists (`speed_modifiers_team1`,
  `time_multipliers_team1`, `ai_sample.speed`). Time multipliers are now stored
  as the **raw WSE2 getter value** (default observed 100; the previous `/10`
  conversion was unverified and could misreport 100 as 10).
- Capability flags `faction_slot_getter` and `scene_getter` record whether the
  two ops are available.

Interpretation: slots reading 894 during a wave-2/3 heartbeat proves the 5 s/4 s
overlay writes are being applied (so a still-leaking 896 points at a later
original selector/spawn path); slots showing original Fast values prove the
overlay writes are not applied (trigger not executing, condition mismatch, or
overwritten). `current_scene` distinguishes a scene-condition failure. Nothing
here asserts acceptance; D must supply the sealed readback.

### Speed / hold / wave-2 / refill telemetry (task-41)

For A's task-38 speed and hold patch the probe now reads back what the engine
actually applied, without assuming the patch worked:

- Per defender agent: native `agent_get_speed_modifier` (2067, percent 0..1000),
  WSE2 `agent_get_time_speed_multiplier` (3336, fixed point converted to
  percent) and `agent_get_action_speed_modifier` (3341). Heartbeats aggregate
  bounded histograms `defender_speed_modifiers`, `defender_time_multipliers`,
  `defender_action_speeds` with `speed_read_unknown`/`time_read_unknown`/
  `action_read_unknown`; `ai_sample` carries the raw per-bot values.
- Defender order/behavior mode: team-order readback via
  `team_get_hold_fire_order` (1784), `team_get_movement_order` (1785),
  `team_get_weapon_usage_order` (1787) and `team_get_riding_order` (1786) for
  sub-classes 5, 6, 7 and everyone (9), emitted as
  `defender_orders=<sub>:<hold_fire>:<movement>:<weapon>:<riding>;...`.
  There is no verified behavior getter in this build, so the summary reports
  `defenders.behavior_mode=None` plus the `behavior_mode_unavailable` gap.
- Movement rate from position deltas: the summary pairs consecutive
  `ai_sample` positions for the same agent id and tick, reporting
  `positions.team0/team1.movement_rate` and `defenders.movement_rate`
  (`agents`, `pairs`, `total_distance`, `avg_per_interval`,
  `max_per_interval`, units = position-units per tick interval). This proves
  zombies actually slowed and defenders held/moved, independent of the
  configured values.
- Wave 2+ visitor classes: `waves.classes_by_wave` now carries the bounded
  team-1 class breakdown (`generic`/`native_zombie`/`defender`/`survivor`/
  `unknown`) for every observed wave, not just wave 1.
- Defender refill: from the heartbeat `defenders_team0` series the summary
  reports `defenders.refill` (`samples`, `unique_counts`, `peak`, `min`,
  `refill_observed` when the count increases after a decrease), so
  `spawn_agent` refills can be seen without trusting a configured target.

Capability line adds `speed_modifier_getter`, `time_multiplier_getter`,
`action_speed_getter`, `team_order_getter`, `behavior_getter=0`. Missing fields
stay `None`/`-1` with explicit gaps (`speed_readback_unavailable`,
`defender_orders_unavailable`, `movement_rate_unavailable`,
`behavior_mode_unavailable`); nothing is assumed from configuration.

### Defender block: divisions 5-7, guard entries and hold observability

Beyond the per-team group histogram the probe emits team-0 defender specifics:
`defenders_team0`, `defender_alive_team0`, `defender_kills_team0` and
`defender_read_unknown`, accumulated only for non-player team-0 bots in
divisions 5-7. The summary adds a `defenders` block:
`observed`, `divisions`, `bots`, `troops` (981-984), `alive`, `kills`,
`read_unknown`, `positions_sampled`, `distinct_positions`,
`guard_entries_reached`, `moving`, `hold_samples` and
`hold_behavior_observed` (always false: samples cannot assert hold behaviour).
`guard_entries_reached` is a bounded proxy - distinct coarse positions rounded
to 1 m, capped at 16 - and is **not** a guard-entry identity. Gaps:
`defenders_not_observed`, `defender_positions_unobserved`,
`defender_telemetry_unreliable`. This makes A/F hold-sector claims either
observable (divisions seen, positions/motion measured) or honestly unobserved
(DISC-28 stays active; no hold-behaviour claim from samples).

This closes the observability gap behind silent `sample_defenders` in defender
runs: if defender bots are in divisions 5-7 the heartbeat group histogram now
shows it directly, and if they are not, the summary reports the adoption as
unobserved instead of assuming hold orders. It remains an observation field, not
an AI-behaviour acceptance claim; the probe never assumes orders were adopted.

### Kill and troop reads: returned lhs values, not stale registers

WSE2 lhs module operations return `(intResult, intError)`; the first Lua
argument is only a placeholder destination and `game.reg0` afterwards is
**stale**. The v3 probe read troop/kill/group/ammo/weapon results through
`game.reg0`, which made every agent report a single troop id in the histogram
and produced implausible kill sums (e.g. `kills_team1 ~= 15351` for 17 bots)
while `ai_sample.kills=-1`. This also explains the earlier "all 17 team-1
agents share one troop id" observation: it was one stale read applied to the
whole histogram, not 17 independent reads; the roster range conclusion
(894..911, never 873/874) still held, but per-agent counts were unreliable.

The accessor now uses the **returned value**, treats a non-zero error, a throw
or a non-numeric result as `-1` (unknown, never 0), bounds kill counts to
`MAX_PLAUSIBLE_KILLS=10000` and troop ids to `MAX_TROOP_ID`, and emits at most
one bounded `probe_anomaly|kind=kill_count_out_of_range`. No partial or
fabricated sums: one unreadable agent makes that team's `kills_teamX=-1`. The
probe emits `kills_measured_team0/1`, `kills_unknown_team0/1` and
`troop_read_unknown`; the summary marks `engagement.kills_*` **reliable** only
when both teams report measured=1 with no unknown agents (otherwise it adds the
`engagement_kills_unreliable` gap), and `troops.reliable` follows
`troop_read_unknown`. Kill counters are agent lifetime counters summed over
observed agents - never session kills and never a victory claim. Old bundles
without the measurement markers are therefore labelled unreliable, not zero.

### Roster classes for sealed AI evidence

The bounded `msfiles/ID_troops.py` label table now covers the documented
Zombie/defender roster: generic faction-default placeholders `873`/`874`, the
native invader block `894..911` (the exact range A's `native_roster_patch`
scans for `fac_kingdom_invaders`, end-exclusive `912`), defender clones
`981..984` (`trp_zdr_commando_bot`/`sniper`/`scout`/`lumberjack`), old
survivor troops `875..878` and mercenary `32`/`33`. The 2012 module has
duplicated invader names, so later duplicates carry an explicit id suffix
(e.g. `trp_invader4_multiplayer_ai_905`); classification is always by ID
range, so a label cannot change the class.

The summary adds `troops.classes` (`generic`, `native_zombie`, `defender`,
`survivor`, `unknown`) and `troops.roster`
(`generic/native_zombie/defender_observed`, `*_ids`, `unknown_id_count`) on
top of the per-team histograms. Unknown ids stay numeric and counted. When a
histogram is sealed but no `894..911` id appears, the summary raises
`native_zombie_roster_not_observed`; it never upgrades a label to a roster
claim.

**Telemetry side effects of A's `native_roster_patch` (read-only review):** it
edits only the compiled body of `multiplayer_find_bot_troop_and_group_for_spawn`
(the faction-conditional troop range); it inserts **no mission trigger**, so
the C probe's appended trigger indices (`boot|triggers=31`, entry=`31`,
heartbeat=`32`) and the historical trigger-14/32 evidence mapping stay valid.
It appends troop records `981..984` after the original `981` (IDs `0..980`
unchanged), adds globals, and assigns defenders to divisions 5–7 with hold
orders — which C's existing `combat_sample` path already samples for
non-player team-0 agents. The build receipt gains `native_roster_patch`
(ignored by C's allowlisted collector). No ZDB1 or recorder-wire change is
required.
**Pre-round scheduling limitation (no-client runs):** with no connected player
the dedicated server never starts a round (`g_round_start_time=0`), and mission
time appears paused in the waiting-for-players state. Only the 1 s entry
trigger is observed to run, while the 15 s heartbeat trigger never becomes
due, so a pure no-client run would otherwise carry no periodic samples. The
probe therefore emits `mission_enter` plus at most 6 bounded
`pre_round_sample` events (same state fields, composition, engagement and
positions) from that proven trigger, and the summary reports
`events.pre_round_only=true` with a `pre-round:` note. This is a
**scheduling fact, not a probe bug**: no read-only probe change can make the
15 s mission trigger due before a round starts, and the probe does not force
round state. Heartbeats, wave changes and per-round evidence still require a
round (for example an idle client joining); `no_probe_heartbeats` is reported
honestly alongside the pre-round composition samples.

A module rebuild is required for a live run to emit the new fields: copy
`overlay/lua/main.lua`, `overlay/lua/msfiles/header_operations.py` and
`overlay/lua/msfiles/ID_troops.py` into the built module (the normal
`tools/build.py` overlay step) and install that build. The recorder and
`summary` command need no rebuild; they read whatever the probe sealed.

The receipt summary derives a `composition` block with max per-team
humans/players/bots/horses, a `mode` (`no_human_player_observed`,
`human_present`, `unknown`, `unknown_no_agents_observed`) and
`player_events_expected`. In `no_human_player_observed` mode the text output
prints an explicit playerless note: absent `player_*` lifecycle events are
expected by construction, not a measured zero, while `round_started` /
`wave_started` and the troop histogram still report whether AIs spawned and
advanced. No summary promotes this composition to gameplay acceptance.

## Agent C: external flight recorder (development prototype)

**Status: offline prototype on `agent/c-flight-recorder`; Windows/WSE2 integration not verified.** The recorder runs as a separate Python process, observes a subprocess launched with `--` or a pre-existing PID with `--observe-pid`, and independently stores atomic, bounded evidence snapshots. No game memory injection, shell execution, external telemetry or background uploads. It does not replace the final WSE2 session.

Run from the repository root. The following commands use a **fake Python game**, not an actual Warband invocation:

~~~powershell
py -3 -m unittest discover -s tests -p 'test_flight_*.py' -v
py -3 -m telemetry.flight_recorder --output-root .\evidence\flight --session fake-city --timeout 10 -- py -3 -c "import sys; sys.exit(7)"
py -3 tools\diagnostics.py collect --flight-root .\evidence\flight\fake-city --output .\evidence\fake-city.zip --session fake-city
py -3 tools\diagnostics.py verify .\evidence\fake-city.zip
py -3 tools\diagnostics.py analyze .\evidence\fake-city.zip --report .\evidence\fake-city.md
~~~

A real integrated session should pass existing WSE2/Warband log paths using repeated `--log` arguments. For Agent B's future launcher, pass its **optional** private per-user `zombieee.session.v1` JSON receipt with `--launcher-receipt`; only allowlisted fields are reproduced. This is an interface prototype, **not** a claim that automatic City launch or WSE2 flags work.

- **Recorder storage:** `evidence/flight/<session_id>/recorder.json`, `events.jsonl`, redacted `logs/log_XX.txt` and `manifest.json`, atomically written with SHA-256 digests over the actual redacted bytes.
- **Collection:** `diagnostics.py collect --flight-root <completed-session-dir> ...` verifies all recorder entries first, refuses a modified source, then carries the scrubbed snapshots plus their process receipt into the existing self-checked evidence ZIP.
- **Log window:** the recorder starts at the log files' current end (not historical prior-session text), polls without modifying the game, stores at most 12 logs × 2 MiB each, limits event records to 2,048 and records truncation. Each source preserves its early records plus a rolling late tail; omitted bytes are recorded in `log_omitted_bytes` and marked with `ZDB1-OMITTED ... BYTES BETWEEN HEAD AND TAIL`. A second size guard applies after redaction expansion. Capture still cannot prove every engine event was logged.
- **Process evidence:** owned-child exit codes are observed; a merely watched PID has **unknown** exit code. Timeout and startup failure are recorded separately. Per-process CPU, memory and FPS are **unknown**, not fake values; wall-clock duration is measured.
- **Privacy:** common credentials, home paths, IPs, email addresses and Steam IDs are redacted best-effort. `verify` additionally reports counts for *potential* remaining sensitive strings, never the offending values. It **always requires manual privacy review before any ZIP is shared**, even when all automated counts are zero. SHA-256 verifies accidental modifications, not provenance or proof that logs are safe.
- **Forensic leads:** R027 means external recorder timed out; R028 means an owned child exited nonzero. Neither is an automatic verdict of a Warband crash. Actual WSE2 Lua and game-run acceptance checks retain the `unknown` state until observed.

Run the full offline suite with `py -3 -m unittest discover -s tests -v` before review. These test files do not require original mod or WSE2 assets, and there is **no CI**.

## Agent A review hardening — C-1/C-2/C-3

- **Crash tail (C-1):** bounded early log plus rolling late tail, an exact per-source omission marker, and independent post-redaction output-size enforcement. Early startup and later crash signatures survive an oversized middle log segment. A clean recorder does not prove every game event was emitted.
- **Passive recorder handshake (C-2):** Agent B launches the separate recorder **before any game PID exists**. C waits passively and writes an atomic `recorder-ready.json` only after creating private session storage, capturing initial log offsets and entering the watcher. The canonical marker schema is **`zombieee.recorder-ready.v1`** (hyphen, not underscore). It includes opaque `session_id`, `attempt_id`, `recorder_start_id`, `watcher_id`, the local recorder PID, and booleans `log_offsets_captured:true`, `watcher_active:true`, `engine_ready:false`, `mission_ready:false`. Agent B must independently validate its owned recorder's PID, process start identity, liveness and freshness before starting the game; neither game nor City mission readiness is inferred from recorder readiness.
- **Authenticated attach/stop:** Agent B passes a random 32-byte control key to C in private environment variable `ZOMBIEEE_RECORDER_CONTROL_KEY` (64 hex digits; no key is persisted or forwarded to the game). B then starts the host/client and writes `recorder-attach.json` with `schema:zombieee.recorder-attach.v1`, the matching three identity strings, positive `host_pid` and/or `client_pid`, and `mac`. `mac` is HMAC-SHA256 with the control key over the JSON object excluding `mac`, serialized using Python `json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode("utf-8")`. C rejects stale/wrong attempts, invalid PID types and incorrect MACs; on acceptance it writes `recorder-attachment-ack.json` but never asserts that host, game or mission is ready. After both game processes have ended, B writes a similarly signed `recorder-stop.json` with schema `zombieee.recorder-stop.v1` to finish and seal C's evidence. All PIDs and control files stay local and do not enter the publishable ZIP.
- **Unsafe paths and child output (C-3):** verification and ZIP import reject filesystem symlinks and Windows reparse points including an intermediate `logs` directory. In **owned-child mode only**, stdout/stderr are drained on bounded threads, redacted, hashed, and annotated with separate source-omission and post-redaction omitted-byte counts. A process externally owned by B has no inferred stderr stream or exit code; use WSE2/host logs and B's local launcher receipt.
- **No real host flags guessed:** B's explicit private-local lifecycle and actual WSE2 startup are still unverified. Any insecure or public host route is out of scope.

### Passive startup example (standalone Python; no game launched)

```powershell
# Agent B generates a fresh random key and correlation ID for each attempt.
# The environment variable is PRIVATE to the C process.
$env:ZOMBIEEE_RECORDER_CONTROL_KEY = '<64 hex digits generated securely by B>'
py -3 -m telemetry.flight_recorder --passive --output-root '.\\evidence\\flight' --session city-attempt-1 --attempt attempt-1 --recorder-start-id '<opaque-id>' --log 'C:\\path\\to\\rgl_log.txt' --timeout 3600
```

Agent B owns the supervising process and writes authenticated control JSON from the same user account; the command above runs until a signed stop message or timeout. It **does not** launch Warband. B waits for `recorder-ready.json` before proceeding. When C finishes, `py -3 tools\\diagnostics.py collect --flight-root .\\evidence\\flight\\city-attempt-1 --output .\\evidence\\city-attempt-1.zip --session city-attempt-1` verifies and packages the local session without automatically uploading data.

### Offline validation scope

Regression files `tests/test_flight_recorder.py`, `tests/test_flight_review.py` and `tests/test_flight_passive.py` cover fake child crashes, late crash tails, bounded redacted subprocess output, handshake-first ordering, **true game-PID-free passive startup**, HMAC-authenticated attach/stop, stale-token rejection, unsafe symlinks, timeouts, and unknown observation states. A locally recreated Linux recorder/fixture mirror ran **16 focused tests with 16 passing**, plus one additional expanding-redaction assertion. The **exact GitHub branch full suite and collector integration tests remain unexecuted** because local GitHub DNS is unavailable. They are still required on an accessible checkout before merge. No Windows gameplay tests or CI were performed.

## Agent integration boundary

Agent B owns launcher and installer orchestration. Agent C owns this recorder and evidence processing, consumes B's optional local JSON session receipt without storing full paths, PIDs, command lines, chat or credentials in report outputs. Agent A owns the [provisional session contract](https://github.com/yigit-denktas/MBW-ZOMBIEEE-Mod/blob/agent/a-city-engine/handoffs/SESSION_CONTRACT.md) on its branch and must review any schema change. Only Agent A can declare a final WSE2 City result accepted based on objective runtime evidence, not these offline fixtures.

## Additional Agent C forensic hardening (Issue #6)

- **Read-only Windows PID liveness:** `windows_pid_alive` uses a Windows process handle with `SYNCHRONIZE` and `WaitForSingleObject(handle, 0)` instead of POSIX-style `os.kill(pid, 0)`. It never sends a Windows termination signal. Access denied or an unsupported state is *unknown*. Regression fixtures use mock handles, not a real game or Windows process.
- **Stop ordering:** the passive watcher does not seal evidence while any attached host/client PID is still seen alive or cannot be confirmed exited. An authenticated early stop remains retryable after process exit. This is an additional safety check, not a substitute for B's independently owned process handles or authority.
- **Large logs and rotated paths:** only the first truncation event per log is emitted to limit I/O; the final receipt retains exact `log_omitted_bytes` for each source. Regression cases cover rotation after startup and a credential split across polling intervals; redaction is best effort and manual ZIP inspection remains mandatory.
- **End-to-end fake B/C process test:** `tests/test_flight_b_interop.py` uses a separate C CLI process, validates the launch gate, rejects a bad HMAC, starts a B-simulated crashing host, refuses early shutdown, then checks the late fatal log and verified ZIP. This test is purely synthetic; it is **not** Agent B's actual launcher implementation or a WSE2 runtime test.
- **R029 scene/build mismatch:** the analyzer checks `experimental_map_scope=city-only` against a *measured* server-side `scene` field **if one is present**. When a scene getter is missing, the report explicitly says `unknown`. The mission-template field and B's intended City destination are never treated as proof of the loaded scene. A known explicit non-City scene produces a candidate mismatch with source/line evidence, not a gameplay verdict. No undocumented WSE2 scene getter has been added.
- **Process leads R027/R028:** findings now attach recorder-source timestamps and calibrated confidence that distinguishes local timeout/nonzero exit from an actual engine cause.

**Execution evidence boundary:** the reconstructed Linux C recorder mirror passed its existing 16 focused tests and another eight safety/process/rotation checks (24 passing, 0 failures/skips across these runs). These are *not* an execution of the exact remote branch. The new GitHub tests, complete `tools/diagnostics.py` suite, and Windows/WSE2 behavior still need validation on an accessible checkout. No CI or repeated manual gameplay sessions are requested.



## C recorder protocol/evidence follow-up (Agent A P0 review)

Agent B's newest `launcher/solo.py` at `69dd354` implements the canonical
`waiting_recorder` state **only as an offline state machine**; it is not an
executable process adapter. The next actual B+C acceptance fixture must launch
B's *real future adapter* with C's passive CLI, not merely duplicate C's
standalone B-simulated fake-host test.

**New source files:** `telemetry/identity.py` reads process birth identities
read-only (Linux `/proc/<pid>/stat` start ticks, Windows `GetProcessTimes`
creation FILETIME). This is C's best-effort local safety guard, **not** a new
v1 wire field or proof of B's process ownership. When a signed stop sees a
different start identity than it saw on attachment, C refuses to seal with a
clean stop and records `pid_start_identity_status=reused_suspected`.
Inaccessible OS identity is `unknown` in forensic output; no raw PID, process
birth time or control key is exported in the public ZIP. The proposed,
**unapproved** optional attach identity fields and residual OS race caveats
are documented in [PID_REUSE_REVIEW.md](PID_REUSE_REVIEW.md). Agent A and Agent B
must approve any shared schema extension before implementation.

**Simulated sessions:** pass `--simulation` to C's CLI, or
`simulation=True` when calling its Python API. The recorder JSON (and
attachment acknowledgment) then records `simulation=true`,
`game_runtime=unknown`; real host/game behavior remains unknown in every
recorder receipt until a separately verified engine session. Python/Windows
process *start* is not City mission start. The collector carries safe status
fields (but not the underlying OS process identity) into the diagnostic ZIP.

**Protocol fixture examples (all values synthetic):**
`tests/fixtures/recorder_ready_v1.json`,
`tests/fixtures/recorder_attachment_ack_v1.json`,
`tests/fixtures/recorder_completion_v1.json`, and
`tests/fixtures/recorder_incomplete_v1.json`.
The readiness marker's `recorder_pid=424242` is **an invented fixture PID**,
not anyone's process. The completion JSON is a small **illustrative subset**
of the full `recorder.json` schema, not a digest-verified real session.
Fixture examples do not contain actual HMACs, paths or game-owned PIDs.

### Recorder death / incomplete evidence

`python -m telemetry.recovery <local-session-folder>` performs a **read-only**
inspection of a private session. This is useful if the recorder crashes or
is terminated by the OS before it writes `manifest.json`. It returns a
path-free `zombieee.flight.recovery.v1` receipt:
`session_complete=false`, `integrity_verified=false`,
`shareable_without_review=false`, `game_runtime=unknown` and
`manual_privacy_review_required=true` for an incomplete session.
A present but invalid final manifest is also explicitly unverified.
It **does not** reconstruct missing events, fabricate a checksum, automatically
bundle or transmit sensitive logs, or mark a failed game test successful.
Its exit status is 0 only for a valid complete recorder session, 1 for
incomplete/invalid, and 2 for refused inspection.

**Current validation boundary:** these newer C source/test changes are
committed on GitHub but have **not** been executed against the exact remote
branch because Github DNS/network checkout is blocked in this environment.
Older recorder-mirror test runs are not accepted as current-branch evidence.
Run on a branch checkout: `python -m unittest discover -s tests -p
'test_flight_*.py' -v`, followed by `python -m unittest discover -s tests
-v`. Record exact revision/platform/pass/skip/failure counts and keep
original module data out of Git and any public bundle. No CI or intermediate
Windows gameplay test.


### Recorder event-journal cost bound

Event writes now append an individually flushed and fsynced line to
`events.jsonl` rather than atomically replacing the entire accumulated
journal on every event. This avoids quadratic write amplification across
up to 2,048 events. The per-run event count and `event_drops` remain explicit,
and the final manifest SHA-256 covers the complete finished journal. A hard
OS termination can leave an incomplete final line; the recovery inspector
reports the session as **unsealed**, never verified. This is a bounded
offline implementation change, **not an observed WSE2 performance claim**.

The current C source also contains tests for process birth-identity sampling,
PID reuse fail-closed shutdown, synthetic protocol fixtures, recorder death
inspection, and per-event append-only cost. These tests **require exact
GitHub branch execution** before PR #12 can be accepted. The latest B adapter
has independently tested an earlier C revision `eade015` on Windows; that
does **not** certify later C commits, so B/A should rerun the combined offline
suite against C's current head after reviewing new fields.


## City Incident Report v1 (Agent C P1)

`tools/diagnostics.py analyze <local-evidence.zip> --report <local-output.md>`
now returns `city_incident` (schema `zombieee.city-incident.v1`), in
addition to the existing R001–R029 rules and acceptance matrix.

The incident report preserves the actual count of A's source audit checks
from bounded sanitized receipt summaries (not the single aggregate pass bit).
Counts that are missing, inconsistent, non-integer or out of range fail closed,
even if the ZIP hashes are internally consistent. This new read-only layer separates source-receipt **claims** from actual
runtime observations, correlates scene/wave/defender/tactical markers within
each log, and summarizes recorder startup, rotation, bounded omissions,
abnormal exits and build inconsistencies as noncausal investigation leads.
The observed historical invasion initializer is **game type 7** in the
updated Agent A source contract; a source assertion is not proof that a
live session entered the City mission. Existing absent or negative getter
values stay **unknown**, never zero.

It stores **two distinct timeline lanes**: ZDB1 source/line ordering (within
a log source only) versus C flight-recorder UTC timestamps. No fabricated
cross-source timestamp or game success. Log excerpts, arbitrary event
strings, local paths, control keys and PIDs are not copied to this summary.
The collector exports only summaries of A's `city_static_acceptance`
and `city_final_acceptance` receipts; even an all-green installed receipt
only sets `source_receipt_claims_passed=true` and
`independently_reverified=false`, not authenticated source provenance.

Details and reproduction commands:
[City Incident Report v1](CITY_INCIDENT_V1.md). Added 13 synthetic test
methods across `test_flight_city_incident.py`,
`test_flight_city_privacy.py`, `test_flight_city_limits.py`. These are
**committed, not reported as executed** until B/A complete an exact checkout
run. No CI, public network, copyrighted assets or repeated owner tests.


### Optional observed round identity (post-A round-aware source revision)

The Lua probe now tries read-only server global getters for
`g_round_start_time` (`round_start`) and
`zdr_last_reinforced_round_start` (`refilled_round_start`) at mission
entry/heartbeat, plus round identity on `wave_change`. A `-1` getter is
**unknown**; source/build receipts must not synthesize an observed round.
Invasion `g_round_ended` (`round`) is merely a state flag, not a round
identifier. The existing `refilled` is the saved wave number only.

City incident v1 can distinguish a decreasing wave with an actually changed
round ID (expected) from a decreasing wave without observed changed round
(candidate `CITY-I04`; cause always unknown). Same-wave observations
across different measured rounds do not imply within-round progression.
Even observing both round globals does **not** prove successful AI top-up.
See [the round evidence contract](CITY_INCIDENT_V1.md#round-aware-reinforcement-source-contract-versus-observed-globals).
