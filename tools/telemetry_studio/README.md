# Telemetry Studio

A read-only toolkit for the ZOMBIEEE recorder (ZDB1) work. It ingests sealed
recorder bundles, parses/graphs the event stream, compares runs, flags
anomalies, measures performance proxies, and statically inspects the installed
module's mission templates/opcodes. It never launches the game, never writes to
game files, and never invents measurements: unavailable fields stay `None` and
are reported as `unknown`/gap.

This is the tooling half of the Ralph-style telemetry loop:

```
baseline bundle -> hypothesis -> probe/granularity change -> D sealed run
-> ingest -> perf/anomaly/compare -> keep/discard -> document -> repeat
```

Each iteration should leave a receipt (`report`), a gap list and a next
hypothesis. A metric heuristic (`better`/`worse`) is **not** an acceptance
claim; `runtime_verified` remains false until a sealed run demonstrates the
behaviour.

## Commands

```text
python -m tools.telemetry_studio schema
python -m tools.telemetry_studio ingest <bundle> [--allow-unsealed] [--json]
python -m tools.telemetry_studio perf <bundle> [--json]
python -m tools.telemetry_studio anomalies <bundle> [--json]
python -m tools.telemetry_studio compare <baseline> <candidate> [--json]
python -m tools.telemetry_studio tail <log> [--follow] [--from-start] [--json]
python -m tools.telemetry_studio inspect <installed-module-dir> [--json]
python -m tools.telemetry_studio report <baseline> [candidate] --out receipt.md \
    --hypothesis "..." --next "..." [--module <installed-module-dir>]
python -m tools.telemetry_studio balance <run1> [run2 ...] \
    [--params params.json] [--out balance.md] [--json]
python -m tools.telemetry_studio loop <baseline> [candidate] \
    --hypothesis "..." --next "..." [--decision pending|keep|discard] \
    [--out-dir telemetry/iterations] [--state state.json] [--module DIR]
```

`ingest`/`perf`/`anomalies` require a verified sealed bundle by default. Use
`--allow-unsealed` only for local, clearly-labelled raw logs; the gap list will
say `unsealed_bundle`.

## What it measures

- **Ingest:** ZDB1 event parsing via the canonical `tools/receipt_summary.py`
  parser; per-artifact line/event counts; duplicate-line detection across log
  copies; engine error patterns (`SCRIPT ERROR`, `Invalid Faction ID`,
  `Illegal lvalue`, stack traces) counted **per artifact**, with a max-across-
  copies to avoid double counting.
- **Performance proxies:** heartbeat count/tick cadence (missing intervals,
  non-monotonic ticks), agent samples per heartbeat, combat samples, event rates,
  log sizes, recorder `event_drops`/truncation, CPU seconds and peak memory only
  when the recorder receipt actually reports them. `ts_ms` (when present) is a
  **probe-relative** WSE2 `getTime()` value for within-run cadence only; it is
  not UTC/cross-run alignment, and older bundles without it stay `unknown`.
- **WSE2 stats options:** reads the local WSE2 `rgl_config.ini` if present
  (`bShowSimulationStats`, `bShowRenderStats`, `i*StatsLogInterval`,
  `bLogSpeedModifiers`) and reports `available: false` otherwise; it never turns
  them on.
- **Anomalies:** missing heartbeats, tick regressions, event drops, truncated or
  large logs, faction-error spam, `probe_failed`, low AI sample coverage.
- **Compare:** baseline/candidate metric deltas with heuristic direction labels;
  unknown fields are explicit.
- **Static inspect:** trigger count/delays, opcode counts for the probe-relevant
  ops (2093/502/1790/1791/3314/3343/522/5113), slow-894 slot writes, invalid
  faction literals, speed-op triggers, module receipt fields and the msfiles
  header opcode declarations.

## Bot-vs-bot balance analyzer

`balance` ingests one or more sealed bot-only bundles and reports:

- per-round observed outcomes: `team0_win` / `team1_win` only when one team's
  observed alive count is 0; `mutual_wipe`; `round_reset_no_wipe` when a round
  resets with both teams alive (no explicit round-end event exists); `unknown`;
- `wall_clock_seconds` is always `None` because ZDB1 has no timestamps (gap);
- troop/class contributions as a **lower bound** from max observed kills per
  sampled agent aggregated by troop (not per-hit/per-death attribution);
- a parameter-sensitivity matrix from an optional JSON mapping
  `run-root-or-name -> {parameter: value}`; correlation only, never causality,
  and `confidence=low` unless the variants are controlled;
- ranked small-change recommendations with explicit confidence/unknowns, and
  `gaps_as_tasks` for unmeasured facts (round-end event, hit attribution,
  wall-clock survival, parameter receipt, per-troop deaths).

No parameter metadata or fewer than two variants produces explicit
`parameter_metadata_missing` / `insufficient_runs_for_ranked_recommendations`
rather than a guessed recommendation.

## Fresh-loop runner

`loop` records one iteration receipt from a baseline/candidate pair, appends a
bounded entry to a JSON state file, and requires an explicit decision
(`pending`/`keep`/`discard`). It never launches/seals a game and never invents a
candidate: missing or unsealed bundles produce explicit gaps and stay pending.
`ts_ms` (when the probe provides it) makes `tick_cadence_seconds` and
`wall_clock_missing_intervals` measurable; older bundles remain `unknown`.

## Tests

`python -m unittest discover -s tests -p "test_telemetry_studio.py"`

Fixtures are synthetic; no game assets are read by tests.
