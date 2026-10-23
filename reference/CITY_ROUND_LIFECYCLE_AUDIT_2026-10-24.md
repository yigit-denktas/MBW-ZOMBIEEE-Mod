# City round-transition survivor behavior — read-only native audit

**Agent A · 2026-10-24 · PR #10**. This review was performed on the owner's original, locally extracted **ZOMBIEEE Beta 0.4** compiled mission and a fully patched **City-only 31-trigger** staging copy. No game executable was started, no original asset modified or published.

## Why it matters

The original original mission's round completion and start logic resets `wave_number` to zero and records a new `g_round_start_time`. Agent A already fixed a stale wave-top-up sentinel by storing the pair of last reinforced **round start + wave number**. That fixes source-level top-up gating but does **not** prove that original allies respawn after round reset or that prior tactical hold/retreat orders survive.

The appended tactical sequence retains **31** City triggers and is compiled in this order:

| Trigger index (0-based) | Native timing | Source-derived role | Round-transition implication |
|---|---|---|---|
| 25 | `ti_after_mission_start=-20` | Spawn first 4 allied NPC visitors into groups 5/6/7 | May not run again on an in-place round restart |
| 26 | 5 s start / effectively infinite rearm | Give initial group-specific entry 2/3/4 hold positions | Not a periodic round re-issue |
| 27 | `ti_after_mission_start=-20` | Initialize last-wave and round-start markers | One-shot, but new handler updates both later |
| 28 | 4 s periodic | Top up living reserved survivors once per (round-start, wave) identity | Correct source predicate; actual bot spawning still unmeasured |
| 29 | `ti_after_mission_start=-20` | Initialize tactical fallback mode 0 | Not expressly reset at an in-place original round restart |
| 30 | 3 s periodic | Count living survivors; issue fallback/regroup on hysteresis transition | Orders reissued **only when** mode changes. If engine silently resets orders between rounds, no automatic reassertion is established |

The original source also contains a `g_round_ended` reset as a guard; the periodic remaster handlers check `g_round_ended=0` and source-confirmed game-type **7**.

## Executed output

```text
python tools/round_lifecycle_audit.py --original <owned original> --module <staged 31-trigger City> --json
exit code: 0
source_pattern_verified: true
runtime_verified: false
source_checks: 9 passed of 9
problems: []
disposition: source_verified_runtime_open_no_automatic_gameplay_patch

ZOMBIEEE_ORIGINAL_MODULE=<owned original> ZOMBIEEE_ORIGINAL_ARCHIVE=<original RAR> \
  python -m unittest discover -s tests -q
Ran 144 tests in 5.200 seconds — OK (0 skipped, 0 failures)

python tools/verify_city_chain.py --original <owned original> --archive <RAR> --json
passed=true; runtime_verified=false
```

The new `tests/test_round_lifecycle_audit.py` adds four regression tests: valid live-source pattern; modified once-only hold interval; corrupted new round timestamp assignment; changed original 25-trigger prefix. All **144/144** latest A Python tests include earlier source/native regressions for game type 7 and identical numbered waves on successive rounds.

**Risk classification (not a proven game defect):**
- Does a new original round reuse the same mission instance? Unknown.
- Are allied reserve NPCs retained, killed, despawned or automatically repopulated? Unknown.
- Do WSE2 group hold positions persist after round restart? Unknown.
- Should `zdr_defence_mode` be reset/reasserted every round? Unknown.
- Does `g_round_start_time` distinguish consecutive rapid rounds in actual Warband scheduling? Unknown.
- Are guards able to traverse, aim and fight? Unknown.

## Next decision

Do **not** add speculative per-round survivor spawn/orders while B's owner-authorized **older-source** controlled boot is in progress. Review its *actual* source-version-pinned scene/wave/team logs first. If the first boot cannot reach the mission, prioritize launcher/module/engine faults instead of native AI. If it reaches City but shows missing allies/orders at the next original round, use the above trigger indices and exact failing observations to design a separately testable correction. Retain all 25 original triggers and 4 deferred scenes.

Relevant contract: [integrated City acceptance ledger](../docs/INTEGRATED_CITY_ACCEPTANCE_2026-10-24.md), [round-aware wave fix](CITY_ROUND_AWARE_REINFORCEMENT_2026-10-24.md).
