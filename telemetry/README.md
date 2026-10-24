# Telemetry Studio loop log

This directory holds the **iteration receipts** produced by the telemetry studio
(Ralph-style loop). The toolkit itself is `tools/telemetry_studio/`; it is
read-only and never launches the game.

## Loop discipline

1. **Baseline** — ingest a verified sealed bundle (`python -m tools.telemetry_studio ingest <bundle>`), record metrics/anomalies.
2. **Hypothesis** — one falsifiable statement tied to a probe/granularity or behaviour knob.
3. **Change** — probe/granularity patch (C) or behaviour knob (A), built into a new installed module by the build/install lane.
4. **D sealed run** — same launcher/settings/knobs; bundle handed back with manifest.
5. **Ingest/evaluate** — `ingest`, `perf`, `anomalies`, `compare`, and `report` with the baseline+candidate bundles.
6. **Keep/discard** — decision recorded in the receipt; a keep still requires a later fully controlled run.
7. **Next hypothesis** — written into the receipt; `unknown` stays unknown.

A metric labelled `better`/`worse` is a heuristic. It is **not** an acceptance
claim, and `runtime_verified` stays false until a sealed run demonstrates the
behaviour.

## Iterations

| # | receipt | baseline | candidate | outcome |
| --- | --- | --- | --- | --- |
| 0 | [`ITERATION_0_task55.md`](ITERATION_0_task55.md) | D task45-wave2 sealed bundle | D task55-wave2 sealed bundle | discard task-55 encoded faction operand (fixed in `agent/c-task55-faction-fix` @ `07c85e4`); keep slot/scene readback pending re-seal |

## Measurement honesty

- Heartbeat cadence is measured from the ZDB1 `count` sequence (missing intervals,
  regressions); wall-clock cadence is `unknown` because ZDB1 lines have no timestamps.
- CPU seconds/peak memory are reported only when the recorder receipt contains
  them; otherwise `unknown`.
- WSE2 stats options are read from a local `rgl_config.ini` if present; the studio
  never enables them, and engine-side stall measurements are not claimed unless
  the options were actually active in the run.
- Engine error totals use the max across overlapping patterns (`SCRIPT ERROR`,
  `Invalid Faction ID`, `Illegal lvalue`) to avoid double counting log copies.
- Static inspection is text-only over the installed module; runtime Lua triggers
  (opcode 5113) are added by the overlay and never appear in `mission_templates.txt`.

## Spatial/heatmap analysis (task-72)

`telemetry/spatial_analysis.py` consumes `zombieee.heatmap-input.v1` and writes
`spatial-analysis.json`, `SPATIAL_ANALYSIS.md`, and simple per-team/wave SVG
grids: occupancy/flow, round panels, cohesion, movement classes, situation
panels (outnumbered/advantage/even from heartbeats), chokepoint *candidates*,
health/class coverage and gaps. It is descriptive only; chokepoints are
occupancy candidates, UNKNOWN never passes, and there is no visual/acceptance
claim.

CLI:
`python telemetry/spatial_analysis.py --input points.json --out-dir telemetry/spatial_out`
