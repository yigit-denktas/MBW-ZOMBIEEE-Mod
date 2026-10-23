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
