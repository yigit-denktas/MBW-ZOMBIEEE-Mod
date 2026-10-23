> **Superseded intermediate regression report.** The 139-test `neq(wave, last_wave)` fix did not handle adjacent rounds ending at the *same* numbered wave. The active code now keys the last top-up by **(original round start, wave)**, preserves the original 25 triggers, and passes **140/140** local original-asset tests. See [current definitive round-aware report](CITY_ROUND_AWARE_REINFORCEMENT_2026-10-24.md). This page describes the earlier intermediate revision only.

# City wave reinforcements across round restarts — source audit

Agent A · 2026-10-24 · City-only experimental native patch · **not** in-engine validation.

## Historical source finding

The owned original 2012 ZOMBIEEE Beta 0.4 `mst_multiplayer_iv` native trigger **3** initializes `wave_number = 0` before the mission. Original trigger **7** contains two zero assignments for `wave_number` in its round-completion paths; original trigger **10** also assigns `wave_number = 0` in its round-start/reset sequence. The original game type is **7** (separate fixed issue described in [City AI audit](CITY_AI_WAVE_AUDIT_2026-10-23.md)).

Our appended `zdr_last_reinforced_wave` sentinel was initialized to **0** in an `ti_after_mission_start` trigger and then updated to the current original wave whenever a top-up ran. The initial added wave trigger required **`gt(wave_number, zdr_last_reinforced_wave)`**. A subsequent round resetting `wave_number` to 0 did not have a corresponding reset of that remaster sentinel. After a first round ending at wave 4, a second round at wave 2 would satisfy the threshold, game type and round-active conditions but fail `2 > 4`: **no reinforcement until wave 5**.

This was a source-reachable *regression risk*, not a measured gameplay failure. The previous 134-test structural/semantic suite did not assert successive-round behavior.

## Minimal correction

- Keep native trigger count unchanged: 25 original, 31 final City core (35 with private hotkeys, 32 with solo assist).
- Keep original trigger lines, original global names, City scene data and other four maps unchanged.
- Replace one condition in appended wave trigger 28: `gt(wave_number, sentinel)` (opcode **32**) → `neq(wave_number, sentinel)` (opcode **2147483679**, native `neg|eq`).
- Preserve the existing `wave_number >= first_wave` and `g_round_ended == 0` conditions.
- Preserve updating the sentinel to the current wave **before** adding replacements. The same wave will then fail `neq` on later 4-second ticks; a new wave or the same numbered wave in a later original round passes once, even when the new round's wave number is less than the preceding round's final wave.
- Teach `tools/ai_wave_contract.py` to insist on the original round-reset assignments in triggers 7 and 10 and the precise `neq`/sentinel-update pair; reject a reintroduced strict-`gt` guard or modified original wave reset.

### Illustrative logical sequence (not an engine replay)

| Round | Current wave | Stored wave before condition | Top-up eligible (threshold = 2) |
|---|---:|---:|---|
| 1 | 2 | 0 | yes, sentinel→2 |
| 1 | 2 | 2 | no, same wave |
| 1 | 3 | 2 | yes, sentinel→3 |
| 1 | 4 | 3 | yes, sentinel→4 |
| 2 | 0 | 4 | no, below threshold |
| 2 | 1 | 4 | no, below threshold |
| 2 | 2 | 4 | **yes**, sentinel→2 |
| 2 | 2 | 2 | no, same wave |
| 2 | 3 | 2 | yes, sentinel→3 |

The native reset is a necessary source fact, but this table is only a *model of the condition*. Static tests cannot certify actual native execution timing, level loading, cross-round agent persistence or AI activity.

## Executed verification

```text
ZOMBIEEE_ORIGINAL_MODULE=<privately extracted historical module> \
ZOMBIEEE_ORIGINAL_ARCHIVE=<owned original RAR> \
python -m unittest discover -s tests -q
Ran 139 tests — OK (0 failures, 0 skips)

python tools/verify_city_chain.py --original <module> --archive <RAR> --json
passed=true; runtime_verified=false
standard/balanced stages: 25→26→27→29→31→35
```

Local environment Linux/Python 3.13.5, with original beta source and unchanged RAR. Added five source-based tests: original reset ops exist, repeated-wave second-round model, old GT substitution negative, original reset removal negative, and compiled wave guard direct check. The four amended GitHub blobs were checked against their exact locally tested byte identities:
- `tools/wave_reinforcements.py`: `858e6e1588b0089e9bf507b6493ff546c7e77336`
- `tools/ai_wave_contract.py`: `7fa10c554eeafe497557871a157d627f4ec0fab5`
- `tests/test_wave_reinforcements.py`: `777dca0deea1e082aa0d41309c71a33474f7f364`
- `tests/test_ai_wave_contract.py`: `6deb5ac439e9ce7ffd643380d563196264471053`

The later/current City patch chain, not an older 131/134-test snapshot, must be the installer input for the final controlled candidate. B's last Windows 131/131 was before both the geometry and this round-reset change. Actual Warband/WSE2 gameplay and second-round reinforcement observations remain unverified; avoid any claim that a private server started or completed two real rounds.

Opcode documentation: [Warband Module System `header_operations.py`](https://github.com/Veehats/WarbandCoop/blob/main/header_operations.py) documents `eq=31`, `gt=32`, `neg=0x80000000`, `neq=neg|eq`. [WSE2 boot contract](../docs/WSE2_CITY_BOOT_CONTRACT.md) retains separate engine startup/private-socket evidence.
