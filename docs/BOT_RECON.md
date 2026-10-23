# Original invasion bot call graph — static reconstruction

Source: the uploaded **ZOMBIEEE Beta 0.4** compiled Warband module, not ZOMBIEEE2.

The new `tools/trace_calls.py` parses the Warband `call_script` operation (opcode 1) from `scripts.txt` and each `multiplayer_iv` trigger. It resolves script-id operands to names without changing or redistributing the original compiled game scripts.

## Reproducible commands

```powershell
py -3 tools\preflight.py --module "C:\path\to\Warband\Modules\ZOMBIEEE_Remaster"
py -3 tools\trace_calls.py --module "C:\path\to\Warband\Modules\ZOMBIEEE_Remaster" --json
```

## Findings from the original archive

- 571 compiled scripts, 25 invasion mission triggers.
- Trigger **15** directly references `multiplayer_find_bot_troop_and_group_for_spawn`.
- Trigger **18** directly references `multiplayer_find_bot_troop_and_group_for_spawn` and `multiplayer_find_spawn_point`.
- Trigger **19** directly references `multiplayer_change_leader_of_bot`.
- The original module includes four survivor classes and AI troop definitions, but the mere existence of this code does **not** prove that friendly survivor bots function properly.

These are **0-based trigger indices in the compiled mission**, not line numbers or wave numbers. A referenced script might be inside a conditional branch and might never execute in a particular mode.

## Next programming task

Use these identified operations and the WSE2 mission-entry hook to record original team ownership and determine which bot path is responsible for zombies versus survivors. Preserve zombie wave spawning and keep allied bot additions server-authoritative. Only then introduce hold, rally and fallback positions on City. No compatibility or gameplay successes are claimed until tested on Windows.
