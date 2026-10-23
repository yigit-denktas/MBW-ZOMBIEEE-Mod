# City reinforcement round identity — definitive static revision (2026-10-24)

**Agent A · PR #10 · source-grounded, NOT real WSE2 gameplay.** Supersedes the earlier intermediate [139-test wave comparison](CITY_WAVE_ROUND_RESET_2026-10-24.md), which was correct for a lower second-round wave but **missed repeated identical wave numbers across adjacent rounds**.

## Root cause discovered in original Beta 0.4

Historical original `mst_multiplayer_iv` compiled triggers **7** and **10** assign `wave_number = 0` during round-ending and round-initialization paths. Trigger **10** also runs `store_mission_timer_a(g_round_start_time)` (opcode 2370). Mission startup trigger **3** assigns `g_multiplayer_game_type = 7` and `wave_number = 0`.

Agent A's original added top-ups stored only one global `zdr_last_reinforced_wave` (initially zero) and compared current wave with its stored number. A comparison of `wave_number > last_reinforced_wave` can suppress all early waves of later rounds. A *different-wave* comparison `wave_number != last_reinforced_wave` improves that case but **still fails when consecutive rounds both reach wave 2**: 2==2 even though these are independent rounds.

This is a proven **logical incompleteness of the native predicates given source reset semantics**. It has **not been reproduced as an in-game failure**.

## Implemented minimal native correction

- Append a second remaster wave state global, `zdr_last_reinforced_round_start`, holding original `g_round_start_time`. Existing `zdr_last_reinforced_wave` continues to hold the human-readable current wave. Original 1,220 globals retain their order; original 25 invasion triggers are byte-preserved.
- The one-time server `ti_after_mission_start` initializer now sets last wave to **0**, stored round identity to **-1**.
- Reinforcement conditions are still server-only, original Invasion game mode **7**, `wave_number >= first_wave`, `g_round_ended == 0`, and actual City-only scene ID.
- Two adjacent native conditions compose an OR: **`this_or_next|neq(g_round_start_time, zdr_last_reinforced_round_start)`** (opcode **3221225503**), then **`neq(wave_number, zdr_last_reinforced_wave)`** (opcode **2147483679**). The trigger runs if EITHER the round changed OR the current round's wave changed. Both state globals update together **before** the bounded top-up loop. A repeated 4-second check for the same round/wave does not spawn duplicate allies.
- The original wave logic/round restart code and all other original maps remain untouched. There are no additional mission triggers. Standard full-tactical City core remains **31**, private-hotkeys variant **35**, solo-assist variant **32**.
- Appended globals change from **2 to 3** (wave sentinel, round identity, tactical mode). Full private-hotkey build now has **1,226** globals, core City variant **1,223**, solo-assist variant **1,223**. `tools/private_commands.py`, `tools/tactical_recovery.py`, `tools/city_acceptance.py`, `tools/verify_city_chain.py` and dependent tests were updated consistently. **Existing compiled previous variants are superseded**; do not combine old and new partial overlays.
- The independent source contract requires original reset opcodes in triggers 7/10, original round-start timestamp assignment in trigger 10, exact OR pair and paired global updates. A missing round marker or downgraded strict-GT guard fails static acceptance.

### State illustration (logical model, not WSE2 execution)

| Original round | Current wave | Saved round+wave before tick | Top-up eligible? |
|---|---:|---|---|
| 1 | 2 | (-1, 0) | yes, save (1, 2) |
| 1 | 2 | (1, 2) | no |
| 1 | 3 | (1, 2) | yes |
| 1 | 4 | (1, 3) | yes |
| 2 | 0 | (1, 4) | no, before threshold |
| 2 | 2 | (1, 4) | yes, save (2, 2) |
| 2 | 2 | (2, 2) | no |
| 3 | 0 | (2, 2) | no |
| 3 | 2 | (2, 2) | **yes, despite identical last wave** |

Here round numbers are explanatory stand-ins for the **original mission's stored `g_round_start_time`**, not a synthetic global. Its actual wall-clock timing, potential timestamp collisions, and observed WSE2 behavior remain runtime gates.

## Executed checks

On local Linux / Python 3.13.5, against the owned pinned original Beta 0.4 extracted module and original RAR:

```text
ZOMBIEEE_ORIGINAL_MODULE=<owned module> ZOMBIEEE_ORIGINAL_ARCHIVE=<original RAR> \
  python -m unittest discover -s tests -q
Ran 140 tests in 5.067s — OK (0 failures, 0 skipped)

python tools/verify_city_chain.py --original <owned module> --archive <original RAR> --json
passed=true, runtime_verified=false
standard & balanced stages: 25 → 26 → 27 → 29 → 31 → 35
standard and balanced globals: 1226
solo-assist globals: 1223, native trigger total: 32
original input file digests preserved; four deferred scenes unchanged
```

All 11 updated GitHub source/test blobs were individually checked against byte-identical local sources via Git SHA-1, not merely reported test output. Offline tests include **second round with a lower first reinforced wave, repeated wave ticks, *identical last wave in successive rounds*, removed round-identity OR guard, old-GT insertion, and missing original reset**. No proprietary assets committed.

## Integration contract

Agent B's previously reported 131/131 Windows test suite and the archived 134/139-result snapshots **predate** this new code. Agent B should consume the latest `city_static_acceptance` / `city_final_acceptance` generated from the **same installed build**, not cache exact global counts or generated City SCO hash from earlier reports. A short independent Windows original-asset rerun on the exact final A commit will still be necessary before the one consolidated runtime session. No intermediate game test requested.

Agent C may report `zdr_last_reinforced_wave` as *observed* only if a real source-bound telemetry getter actually reads it; `zdr_last_reinforced_round_start` is a compiled-source state field until witnessed in-engine. **A clean ZIP or green build receipt is not evidence of wave progression or AI shooting.**

Upstream native modifier encoding: [Warband Module System `header_operations.py`](https://github.com/Veehats/WarbandCoop/blob/main/header_operations.py) (`this_or_next=0x40000000`, `neg=0x80000000`, `eq=31`, `neq=neg|eq`).
