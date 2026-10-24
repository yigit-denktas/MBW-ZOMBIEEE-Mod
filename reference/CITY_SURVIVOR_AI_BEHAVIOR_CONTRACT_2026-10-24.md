# City survivor AI behavior contract - 2026-10-24 (task-17)

**Agent A - native module-system logic only, compatible reimplementation; no third-party code or assets copied. Engine validation pending D's sealed run.**

## Research notes

- **Motomataru Formations AI** (`cvlc/tgsmod` `formations_presentations.py`, fetched read-only): formations are driven by `script_set_formation_destination(team, division, position)` plus team formation slots and `mordr_hold`; the scripted formation destination is a *custom module script*, not a native opcode. Our module does not ship that script, so the compatible minimal equivalent is the native **`team_set_order_position` (1791) + `team_give_order(mordr_hold, 0)` (1790)** pair on reserved divisions, which is what the City overlay already uses. We do not copy any formation code or assets.
- **Doghotel Brainy Bots dedicated-server patch**: the public page returned HTTP 403 from this machine; no code inspected. Principle adopted only at the contract level: server-side native orders (not presentations/UI) are what change AI behavior on a dedicated host.
- **mbmodwiki "Adding new multiplayer faction"**: confirms multiplayer AI troops are ordinary `_multiplayer_ai` troops assigned to a faction and the engine spawns the faction's multiplayer-AI troops for bots (this matches the compiled-script scan A patched for the Zombie roster; see `native_roster_patch`).
- **Zombie simplicity**: no kiting/flanking/formation script is added for team 1. Zombies keep native aggressive seek behavior; they are numerous because configured bots plus untouched original wave visitors spawn them. The roster patch only changes which troop ids are selected, not their AI.

## Native behavior contract (City-only build)

| Actor | Contract |
| --- | --- |
| Private survivors (team 0, divisions 5-7) | Spawn at survivor entries 0/1; topped up to cap every 3 s while the round is active (`tactical_recovery`), so the one-shot `-20` spawn cannot leave team 0 empty after a dedicated round reset. |
| Survivor sectors | Three guard entries 2/3/4 (navmesh-derived; City SCO overlay). Hold trigger runs every 5 s, re-issuing `team_set_order_position` + `mordr_hold` per division. Sector rotates by one step per original `wave_number` parity: entry = `2 + ((division-5 + wave%2) % 3)`, so the squad re-uses adjacent map sectors each wave instead of freezing in one spot. |
| Fallback / regroup | Existing `tactical_recovery` thresholds (low_water 1, high_water 3) order fallback to survivor entry 0 when wiped to <=1, regroup to guard posts at >=3; state global `zdr_defence_mode` prevents thrash. |
| Generic team-0 bots | If the rotation sets `set_bot_count 1 N`, those are separate native faction bots (unchanged behavior); private survivors are the reserved divisions 5-7. Hands-off runs may use either or both. |
| Zombie horde (team 1) | Native faction bots select the Zombie troop block 894..911 after the build-time roster patch (no 873/874 Crazed Civilians as bot troops). Original wave visitor spawns remain untouched. No complex team-1 orders are added - simple aggressive native seek is intentional. |

## Implementation (branch `agent/a-survivor-hold`, on top of main `87aa498`)

- `tools/city_defense.py`: `orders_trigger(scene_idx, wave_global)` computes the dynamic sector entry with native `store_mod`/`store_sub`/`store_add` on `$wave_number`; `apply_module` resolves the original `wave_number` global index from `variables.txt`. Fixed (static) entries are still emitted when no variables table is supplied, for fixture tests.
- `tools/tactical_recovery.py` (already merged): 3 s respawn top-up of missing survivors (cap = `--experimental-defenders`).
- Build receipt: `experimental_city_guardposts.wave_sector_rotation=true`.

## Offline acceptance

- Branch suite: 399 tests OK / 4 skips; targeted `test_city_defense` asserts dynamic ops (`2119` wave parity, `2121` division-5, `2120` entry math) and still exactly 3 `1780`/`1791`/`1790` per trigger.
- `verify_city_chain` reproduced 25->26->27->29->31 with static + final gates accepted and `runtime_verified=false`.
- **Engine proof still pending:** D's sealed no-client run must show C's `pos_team0` moving toward guard entries 2/3/4, `bbox`/`ai_sample` spread, survivors holding near posts, fallback/regroup transitions, and team1 Zombie ids 894..911. No gameplay acceptance before that.
