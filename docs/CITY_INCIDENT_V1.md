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
| CITY-I04 | wave number decreased in one log | Candidate regression; rematch/restart still possible |
| CITY-I05 | City source receipt check returned false | Build-source consistency lead, not game observation |
| CITY-I06 | declared original invasion type other than 7 | Source-contract inconsistency, no assumed runtime |
| CITY-I07 | observed non-City scene vs City-only build | Scene/build mismatch candidate, cause unknown |

All leads say `cause=unknown`. No incident suggests an anti-cheat bypass,
public game hosting, automatic uploads or executable installer changes.
The report never marks `runtime.gameplay_verified=true`: final acceptance
requires the single real private WSE2 session with direct evidence.

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
