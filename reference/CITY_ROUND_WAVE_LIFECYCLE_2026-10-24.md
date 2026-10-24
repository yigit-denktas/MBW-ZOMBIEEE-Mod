# City round vs wave lifecycle - 2026-10-24 (task-26)

**Agent A static diagnosis of the pinned ZOMBIEEE Beta 0.4 City mission. No runtime/gameplay acceptance.**

## Observation (D's 495 s / 10-round sealed run, main a6b5fe9)

`waves.max=1`; `round_starts=[0,28,79,135,225,264,312,373,444,491]`; team1 max 22;
defenders 981..984 present; kills reliable; every new round restarts at wave 0.

## Decoded native lifecycle (original `mission_templates.txt`)

- **Trigger 3** (-19, after mission start): initialises `$g_wave_number = 0`.
- **Trigger 6** (-25, round start): clears `$g_round_ended = 0`; does **not** touch wave.
- **Trigger 7** (-26, round end): sets `$g_round_ended = 1` **and** `$g_wave_number = 0`.
- **Trigger 15** (1 s periodic, server-gated): increments `$g_wave_number` and spawns the wave.

So the wave reset is **native round-end behaviour**, not a City overlay defect. A round
that ends (team-0 wipe / native reset) before wave 1 is cleared returns the next round to
wave 0. Wave 2 is therefore a *survival-through-wave-1* outcome, not a counter the build
can simply keep incrementing without changing native difficulty progression.

Tool: `tools/round_wave_lifecycle.py` (read-only; optional `--built` compares the original
25-trigger prefix byte-for-byte). Offline test: `tests/test_round_wave_lifecycle.py`.

## Options / tradeoff

1. **Hands-off AI validation (recommended, no module change):** rotation
   `set_player_respawn_as_bot 1` keeps team 0 alive when the unattended player dies, so the
   round does not end on player death; combined with a defender-heavy variant
   (`--experimental-defenders 8` and/or `set_bot_count 2 4`) the squad can clear wave 1 and
   reach wave 2. This changes rotation only.
2. **Owner solo:** wave reset per round is native design; wave 2 is a survival achievement.
   Survivability/density tuning (more/better defenders, slightly lower early wave density)
   is the compatible lever; the firearm accuracy profile already improves sustained fire.
3. **Not recommended:** a City-only wave-carryover patch that restores wave_number after
   round reset. It would alter native wave progression/spawn difficulty and risks spawning
   multiple waves' enemies at once; only consider with owner play-testing, and never by
   editing the original 25 triggers (append-only City overlay only).

## Bounds

Static analysis only. D must validate the defender-heavy + `set_player_respawn_as_bot 1`
variant in a sealed run; wave >= 2 remains unobserved until then. Required City outcomes
stay 0/23, milestones 0/5, `runtime_verified=false`.
