# City Incident Report v1 — Agent C forensic interpretation

This is an **offline diagnostic interpretation** of an already-hash-verified
evidence ZIP for the original ZOMBIEEE Beta 0.4 City invasion. It is **not**
a new game feature, acceptance oracle, or runtime capability. First release
scope remains City (`tbfc_invasion_4`); other original scenes are deferred.

## Where it appears

`python tools/diagnostics.py analyze <local-verified-evidence.zip> --report <local-report.md>`

The JSON analysis includes `city_incident` with schema
`zombieee.city-incident.v1`; the Markdown output includes the City timeline,
incident leads and unknown observations. The logic lives in
`tools/city_incidents.py`, called by `tools/diagnostics.py` after its usual
evidence and privacy inspections. The underlying `read_bundle` verifies SHA-256
over each ZIP entry **before** analysis; this is integrity, not authenticity.

## Source provenance is not game evidence

The diagnostics collector reads `ZOMBIEEE_REMASTER.json` from an explicitly
selected local module and allowlists only these bounded City fields:

- `city_static_acceptance`: summary count and boolean result of A's native
  checks; source-derived `original_invasion_game_type`, expected **7**.
- `city_final_acceptance`: `passed` as a strict boolean and the approved
  control mode, which attests A's post-control source consistency.
- `experimental_map_scope=city-only` and existing safe build flags.

The ZIP keeps the original static audit's bounded numeric `check_count`,
`passed_checks`, `failed_checks`, `checks_valid` and **one**
`all_checks_passed` boolean. The incident report does **not** confuse that
single summary bit with the number of original source checks. It validates
integer types (excluding booleans), positive bounded counts, exact
passed+failed totals, and agreement between the summary bit and the failures.
Malformed or inconsistent summaries produce `source_check_failed`,
`static_summary_consistent=false` and no accepted source claim. Such data
cannot be promoted to independent verification even if a ZIP's SHA-256
manifest is internally consistent.

It deliberately **discards raw checks, raw problems, filenames, local source
paths, raw command lines and private process IDs**. A complete set of
self-reported source receipts yields `build.source_receipt_claims_passed=true`,
but `build.independently_reverified=false`. This incident analyzer does **not**
rerun A's City verifier, re-extract the owner's historical RAR, or establish
authenticated provenance merely from a checksum. A separate exact-source
verifier may establish source validity; neither operation proves live WSE2
gameplay.

**Important source fix:** A found the original invasion's unconditional
`g_multiplayer_game_type=7` initializer. An earlier added wave/recovery
condition wrongly checked 6. Agent A fixed it in PR #10, backed by offline
native checks; no earlier structural passing result can substitute for
direct observed wave progression. No live game type is invented from an
expected value. Actual `wave_number`, `zdr_last_reinforced_wave`,
`zdr_defence_mode`, reserved defender combat, host/scene and process outcomes
are individually *observed marker* or *unknown*.

## Round-aware reinforcement: source contract versus observed globals

Agent A's latest **source** revision adds `zdr_last_reinforced_round_start`
to remember the original `g_round_start_time` alongside the unchanged
`zdr_last_reinforced_wave`. The native top-up guard now distinguishes
`(round_start, wave)`, because original invasion rounds reset
`wave_number=0` and successive rounds may reach the same wave number.
This is a source-native correctness condition, not evidence that top-ups or
pathfinding worked in WSE2. It is **not** independently attested by this
report's collapsed source audit counters:
`build.round_aware_source_contract_verified=false`.

Agent C's optional Lua event probe now attempts **read-only engine global
reads** on the server at mission entry and each heartbeat:

- `round_start` = `g_round_start_time`, a mission-timer global and
  *runtime round identity candidate*, **not a UTC timestamp**.
- `refilled_round_start` = `zdr_last_reinforced_round_start`, the
  last stored top-up round identity. It can lag the current round; this
  is not automatically a fault.
- `refilled` remains `zdr_last_reinforced_wave`; it is a wave number,
  never a round identifier.
- Existing `round` is `g_round_ended` (0/1), **not** round identity.

Only **explicit server-role** `mission_enter`, `heartbeat` and
`wave_change` events may establish measured round identities. Historical
`wave_change` events without a `role` field are still accepted as
**lower-confidence wave-number candidates**, but any accompanying
`round_start` or `refilled_round_start` fields on such events are
ignored. Client-role markers cannot establish server round identity,
even if they contain plausible numbers. The updated Lua probe emits
`role=server` on newly instrumented wave changes.

The safe getter returns -1 when absent/unknown, which the incident
report excludes. Only actual server ZDB1 event fields can populate
`runtime.round_start_observations`,
`runtime.last_reinforced_round_starts` or
`runtime.wave_progression_within_one_round`. If no getter/field was
observed, those remain `unknown`/`null`, regardless of how green the
build receipt looks.

`CITY-I04` is a **noncausal lead** for wave number decreasing in the same
log *without an explicitly measured changed round*. A lower wave with
different measured `round_start` is an expected new-round pattern, so it
does not raise that lead. Distinct rounds that both show wave 2 are
reported as repeated wave numbers **across observed rounds**, not as
progression within one round. Even paired round and reinforced-round
samples never certify that bots spawned or fought:
`runtime.round_aware_reinforcement_verified=false`.

**Version boundary:** B's first owner-authorized live City attempt uses
older A `2643321` and C `53c2f88` source, whereas A's round-aware
source fix is at `141a7926` and C's newer round probe is subsequent.
Any evidence from that first attempt is historical-candidate evidence
only. Do not retroactively infer either new global was instrumented or
the latest source changes were exercised by that attempt.

## Two timeline lanes, not one fabricated chronology

1. **Engine observations:** ZDB1 lines reference the safe ZIP member
   `logs/log_NN.txt` and bounded line numbers. Their ordering is trustworthy
   only **within that one captured log source**. No event UTC is invented.
2. **Recorder observations:** C's bounded event journal provides its own
   recorded UTC. This is recorder wall-clock time, not WSE2 engine time.

The lanes deliberately declare `cross_lane_order:
unknown_without_shared_clock`. Both retain the earliest and latest entries
(up to 96 per lane); `omitted_middle` counts discarded timeline entries.
Missing log intervals, redaction/truncation markers, flight omissions and
event drops yield an explicit `recording_gap` lead.

Only known numeric fields and typed scene names enter the report. Unknown
getters (`-1`), missing combat samples and absent waves are **not zero** or
negative evidence. A `mission_enter` without a measured server-side
`scene` field does not prove City was entered. Historical game markers
do not establish working bot combat, total wave completion or player controls.

## Conservative incident leads

| Code | Trigger | Safe conclusion |
| --- | --- | --- |
| CITY-I01 | diagnostic R002 | Fatal text **pattern** detected; root cause unknown |
| CITY-I02 | timeout/interruption/start failure receipt | Abnormal recorder session; engine status unknown |
| CITY-I03 | omitted interval or bounded timeline | Some potentially relevant events were not preserved |
| CITY-I04 | wave number decreased without measured new round | Candidate observation gap or regression; rematch/restart still possible |
| CITY-I05 | City source receipt check returned false | Build-source consistency lead, not game observation |
| CITY-I06 | declared original invasion type other than 7 | Source-contract inconsistency, no assumed runtime |
| CITY-I07 | observed non-City scene vs City-only build | Scene/build mismatch candidate, cause unknown |
| CITY-I08 | WSE2 log text `Invalid Faction ID: -1` (R030) | Invalid faction reference detected in engine text; root cause and gameplay impact unknown |

All leads say `cause=unknown`. No incident suggests an anti-cheat bypass,
public game hosting, automatic uploads or executable installer changes.
The report never marks `runtime.gameplay_verified=true`: final acceptance
requires the single real private WSE2 session with direct evidence.

## First observed private WSE2 boot: scoped evidence only

Agent B reported its first owner-authorized City dedicated-host attempt with
a verified loopback-only UDP listener, recorder readiness and owned host/client
attachment, followed by four `SCRIPT ERROR: Invalid Faction ID: -1`
messages around source-native `mst_multiplayer_iv` Trigger 14 opcode 502.
The generic R003 script error remains; new R030 classifies this particular
**logged text** and CITY-I08 records a **noncausal diagnostic lead**.
It does **not** prove the error was introduced by the remaster, caused a
wave failure, or prevented a player join. That comparison belongs to
Agent A's original-versus-patched native source audit. Do not infer
successful combat from a launched host process.

This **live session uses the exact staged and launched A/C source versions
documented by B**, not automatically the current PR heads. The recorder
must seal its own evidence manifest after owned game processes exit;
until then, the final incident bundle and verified gameplay remain unknown.
Only path-free observations may be published; local raw logs stay private.

## Live trigger-32 Lua lvalue error: C overlay defect, fixed offline

The first live WSE2 City session logged the following on **both** host and
client, once per 15 s:

```
SCRIPT ERROR: Illegal lvalue in statement
- Lua (line 0, opcode 1770, modifier 0x0)
- Mission Template [44] mst_multiplayer_iv Trigger [32] Conditions (Lua) (line 0, opcode 5113, modifier 0x0)
```

The same session's ZDB1 lines bind the index without guessing: the original
`mst_multiplayer_iv` reports `boot|triggers=31`, so the overlay's appended entry
trigger is `probe_registered|kind=entry|index=31` and its 15 s heartbeat is
`probe_registered|kind=heartbeat|index=32`. Trigger [32] is therefore Agent C's
read-only heartbeat, not an original mission trigger. Opcode 5113 is WSE2's
`lua_triggerCallback` and opcode 1770 is `agent_get_team`.

**Root cause (fixed in `overlay/lua/msfiles/header_operations.py`):** WSE2's
Lua bridge learns each module-system operation's calling convention only from
the trailing `lhs_operations` / `can_fail_operations` lists required by its
luaGuide. The header had the opcode constants but not those lists, so
`game.agent_get_team(0, agent)` sent the destination register number to the
script VM as a plain constant and the VM rejected the store with "Illegal
lvalue in statement". This is C-owned telemetry only; the VM aborted that store,
so the probe cannot have changed gameplay state. Agent A still owns the
original-versus-patched question of why no team-1 agents or waves appeared.

**Two evidence-hygiene consequences of the same omission:**

1. `multiplayer_is_server` (opcode 417, a bare can-fail condition in the
   original compiled mission templates) returned an error code instead of a
   boolean, so the **dedicated host logged `role=client`**. The whole
   `role == "server"` branch (`wave_change`, `tactical_change`, defender and
   command samples) never ran in any live session so far.
2. Because `agent_get_team` failed, the heartbeat's `team0`/`team1` values can
   coincide with the failed call's zero result. The attempt-4 line
   `agents=1 team0=1 team1=0` is therefore **not a measured team composition**
   and stays `unknown` until it is re-observed with the fixed overlay.

The failed team read now yields `-1` (unknown) instead of being counted as team
0, and an unrecognized role result stays `unknown` instead of defaulting to
client. The fixed overlay also emits `|opmeta=1` in `recorder_capabilities` and
adds explicit, separately named guarded reads — `game_type`
(`g_multiplayer_game_type`), `ready_for_spawn`
(`g_multiplayer_ready_for_spawning_agent`), `bots_team1`
(`g_multiplayer_num_bots_team_1`) and `round_start`
(`g_round_start_time`) — while `mode` remains the tactical
`zdr_defence_mode`. Every absent getter is `-1`/unknown, never an inferred zero.

**Version boundary:** the 2026-10-24 evidence was produced by Lua overlay
`version=0.1.8` **without** the `opmeta=1` marker, i.e. before this fix; the
Lua string version is intentionally unchanged. `tests/test_flight_lua_msfiles.py`
now statically rejects any header that omits the operation-class lists or any
overlay call to an unclassified operation. R030/CITY-I08 (`Invalid Faction ID:
-1`, trigger [14] opcode 502) is untouched: it is original Beta 0.4 content and
remains a **noncausal** lead.

## Dedicated bot-count gap and the first observed enemy wave

The fixed probe was validated on the rebuilt City module from merged
`main@4c56242` (recorder armed, host loopback-only). Its ZDB1 lines now
self-identify with `|opmeta=1` and report `role=server`, `game_type=7`,
`ready_for_spawn=1` and per-agent team sampling. The new dedicated session log
contains only the four original Trigger 14 `Invalid Faction ID: -1` messages;
there is no repeated `SCRIPT ERROR: Illegal lvalue in statement`.

The same rebuilt module then produced the **first observed enemy wave**, and
the three configurations isolate the cause:

1. Unconfigured dedicated rotation: `team1=0 wave=0` for 90+ s while the probe
   already reported `role=server`, `game_type=7`, `ready_for_spawn=1`. The
   probe was no longer blind, so this was not a measurement artefact.
2. `set_bot_count 1 32` (1-based first team, the player team):
   `agents=33 team0=33 team1=0` — allied bots only.
3. `set_bot_count 2 32` (1-based second team, the enemy team):
   `agents=42 team0=1 team1=41 wave=1` plus `wave_change wave=1`, still
   loopback-only. The final run's entry marker was
   `agents=32 team0=0 team1=32 wave=0`, so enemy agents were present before
   the player joined and the wave counter advanced afterwards.

The earlier "no team-1 agents/waves" observation therefore has a
**dedicated-server rotation configuration** cause: the rotation lacked a
second-team bot count before `start`. It is not a remaster build defect and it
is distinct from A's original-versus-patched source attribution and from
R030/CITY-I08. The launcher/installer still needs a validated configuration
step (for example `max_num_bots` plus the 1-based `set_bot_count` entries)
before any City re-run; that is B's lane.

The measured round identity also advanced correctly within one session
(`round_start` 2 -> 84 -> 152) with `wave` resetting to 0 at each new round.
That is the expected new-round pattern from A's round-aware source contract,
so it is **not** a CITY-I04 wave regression; CITY-I04 still requires a lower
wave without a measured new round.

**Field-semantics caveat (evidence hygiene):** `bots_team1` is a read of the
native `g_multiplayer_num_bots_team_1` global. It stayed `0` in the successful
run even while team 1 held 41 agents, because the rotation command is 1-based
(`set_bot_count 2 ...` addresses the enemy team) while that global names the
first team. `bots_team1=0` must **not** be read as "no enemy bots", and enemy
population must only come from the measured `team1` agent count.

A single observed `wave=1` is not wave completion, AI combat acceptance or
gameplay verification; `runtime.gameplay_verified` stays false and the sealed
recorder receipt plus screenshots still have to be reviewed.

## Respawn and round-restart configuration: what was and was not measured

A follow-up dedicated attempt (2026-10-24 02:12 UTC) added
`set_respawn_period 5`, `set_defender_spawn_count 0`,
`set_round_max_seconds 1800` and `set_player_respawn_as_bot 0` to the team-2
bot rotation. The recorder sealed the attempt (`outcome=stopped`,
`simulation=false`, 7 integrity-verified files) and the corrected probe again
emitted `|opmeta=1`, `role=server`, `game_type=7`, `ready_for_spawn=1`, with no
`Illegal lvalue` and no new script errors beyond the four original Trigger 14
faction messages.

What the probe **directly observed** at its 15 s sampling:

* repeated new rounds: `round_start` 28 -> 61 -> 133 -> 228 -> 317, with
  `wave` resetting to 0 and `team1` repopulating (32/41) at each new round;
* one explicit round-end marker: `round=1` (`g_round_ended`) on heartbeat 9;
* the player present on team 0 from heartbeat 3 through heartbeat 21;
* team0=0 on heartbeats 22-24 on the last new round, around the client exit
  that stopped the recorder.

**Respawn-interval semantics — bounded claim only.** The dedicated server's own
help text lists `set_respawn_period <value>` as "sets respawn period" with no
printed unit, and `set_round_max_seconds <value>` as "maximum seconds for
round". The probe samples every 15 s, so a 5 s respawn is shorter than one
sampling interval: a death followed by an immediate respawn is invisible
between samples. There is **no sampled `team0=0 -> 1` transition while the
player was connected**, so this attempt measures neither respawn latency nor a
death/respawn cycle; it only shows a team-0 agent present again at every
sampled heartbeat from 3 to 21. Round restarts were roughly 33/72/95/89 s
apart, far below the configured 1800 s maximum, so they were game-mode round
ends rather than the max-seconds limit. The final `team0=0` spans ~45 s, more
than the configured 5 s period, and coincides with client exit; the ZDB1
stream cannot distinguish "died again and quit before respawn" from "left
before the new round", and `exit_code_observed=false` (B owns the process
handles) keeps that unknown. Neither `team0=0` nor `team1>0` may be promoted
to a death or a native-zombie claim: the generic `set_bot_count` roster is
Crazed Civilian (issues #13/#14).

**Sealed receipt completeness caveat:** in this attempt the stored redacted
`logs/log_01.txt` is a strict prefix of the engine log and misses its final
appended line (~82 characters), while `recorder.json` reports
`log_seen_bytes=[15172]` with `log_omitted_bytes=[0]`. The bundle is
integrity-verified but slightly overstates log completeness — the same class
as the terminal-write/atomic-replace issue #15, not corruption. The engine log
itself contains only the original Trigger 14 errors; the probe stream remains
outside the sealed bundle (issue #16).

## Verification and privacy

Synthetic regression tests cover source/runtime claims, the original game
type 7, scene measurement versus intended mission, absent team telemetry,
log gaps, cross-log wave order, recorder UTC segregation, sensitive string
exclusion, redacted build receipt allowlisting and rejecting altered ZIPs.
The reporter uses only bounded, whitelisted fields (96 events per lane) and
never copies arbitrary event values into the incident timeline.

**Always manually inspect the evidence ZIP and report before sharing.** The
existing redaction and SHA-256 checks are best effort and not an anonymization
guarantee.

Commands to run on an **exact current branch checkout**:

```sh
python -m unittest discover -s tests -p "test_flight_*.py" -v
python -m unittest discover -s tests -v
```

No CI is enabled, no original mod/game assets have been added to the repo,
and no real WSE2 playability claim is made. A verified City static receipt
and an observed WSE2 City invasion remain different release gates.
