# City survivor AI / wave-controller audit — 23 October 2026

**Agent A · PR #10 · scope: original Beta 0.4 `mst_multiplayer_iv` + opt-in City-only build.** Static source and native-operand analysis, **not** executed Warband/WSE2 gameplay.

## P0 functional defect discovered and fixed

Original Beta 0.4 invasion mission trigger **3** is `ti_before_mission_start` (`-19.000000`). It has **zero conditions** and its first consequence unconditionally assigns `g_multiplayer_game_type = 7` using native opcode `assign` (2133). The original global is at offset **495** of the 1,220-name table.

Before this fix, remaster triggers **28** (survivor reinforcement every 4 s) and **30** (fallback/regroup every 3 s) both contained `eq(g_multiplayer_game_type, 6)`. Under the original mission's initialized type **7**, neither trigger could pass that condition. Prior full Python tests and SHA/source integrity checks only established structural correctness, **not** whether the new controllers' gates could be true.

**Fix:** `tools/wave_reinforcements.py` defines `INVASION_GAME_TYPE = 7`; both wave and tactical recovery now use that same value. We did **not** rewrite original triggers, zombie waves, or map assets.

## Independent fail-closed native audit

Added `tools/ai_wave_contract.py` and integrated it with `tools/city_acceptance.py`. The checker fully decodes native condition and consequence operation blocks (rejects malformed arity/trailing tokens) and derives the original game-type global from `variables.txt`. It requires:

- Original trigger 3: an unconditional `-19` event with initial assignment `assign(g_multiplayer_game_type, 7)`.
- New triggers 28 and 30: **exactly** `eq(g_multiplayer_game_type, 7)` for that original global, plus server-only gating.
- Wave reinforcement: original `wave_number` greater than the last serviced wave, sentinel updated from the same wave, round not ended, live non-player team-0 agents in only reserved groups 5–7, and four class/visitor branches spawning one team-0 survivor each into reserved groups.
- Tactical recovery: round active, living non-player survivor team/group filters and explicit enter-fallback/leave-fallback state writes.
- City-only native scene guards and the original trigger prefix are **additionally** enforced by existing `city_acceptance.py`; the canonical City SCO and four deferred scenes still have to pass their independent byte-preservation checks.

Installation receipt `city_static_acceptance.original_invasion_game_type = 7` records the **source-derived** value, *not* an observed in-game runtime value. The new audit checks are included in the receipt's `checks` dictionary.

## Evidence

| Check | Reproduction | Observed result |
|---|---|---|
| Original source initialization | decode original trigger 3 + original variable table | type **7**, unconditional assign |
| Previous regression reproduced | mutate new trigger 28 or 30 game-type check back to 6 | **Rejected** independently |
| Historical source manipulation | mutate original initialization to 6 | **Rejected** |
| Non-survivor reinforcement | mutate visitor branch to team 1 | **Rejected** |
| Full source-grounded suite | `python -m unittest discover -s tests -q` | **131 tests, OK, zero skips** |
| Reproducible City chain | `python tools/verify_city_chain.py --original <owned module> --archive <owned RAR> --json` | `passed=true`, `runtime_verified=false` |

The **131/131** run took place on Linux/Python 3.13.5 with `ZOMBIEEE_ORIGINAL_MODULE` and `ZOMBIEEE_ORIGINAL_ARCHIVE` set to the owner's pinned Beta 0.4 inputs. Previous baseline was **124/124**, before seven new semantic/native-decoder regression tests. The changed files were compared to their committed Git blob SHA values after uploading. The full stage sequence still passes with **25 → 26 → 27 → 29 → 31 → 35** native triggers in both standard and balanced-AI profiles; optional solo-assist is **31 → 32**.

**Exact native-opcode reference:** the publicly available Warband Module System [`header_operations.py`](https://github.com/Veehats/WarbandCoop/blob/main/header_operations.py) defines `eq=31`, `gt=32`, `is_between=33`, `try_for_agents=12`, `agent_get_group=1765`, `agent_get_team=1770`, and `add_visitors_to_current_scene=1265`; [`header_triggers.py`](https://github.com/Veehats/WarbandCoop/blob/main/header_triggers.py) identifies `ti_before_mission_start=-19`. Those files provide opcode definitions, not observed engine behavior.

## Remaining runtime questions

A static passing gate **does not prove** native branches execute in WSE2, the engine starts the intended mission, or that survivors move, attack and stay alive. At final integrated private City session, obtain independently observed server role, actual scene ID, waves incrementing, `zdr_last_reinforced_wave` increasing only after eligible waves, defender counts/team/groups, tactical mode 0↔1 transitions when thresholds are crossed, ammo/kill samples where supported, and bounded recorder evidence. Unknown measurements must remain unknown. No intermediate user playtest.

Full original RAR member CRC with genuine 7-Zip, actual installer transaction and B/C adapter with newest C revision also remain open. Keep PR #10 **draft** until integration and runtime gates are cleared. Older [City chain verification](CITY_CHAIN_VERIFICATION_2026-10-23.md) remains a historical **pre-fix structural** evidence snapshot; do not treat its 124-test run as the current AI-correctness claim.
