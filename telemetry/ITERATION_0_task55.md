# Telemetry Studio iteration receipt

**Status:** auto-research iteration; no acceptance, no fabricated data. `runtime_verified` remains false until a sealed run demonstrates the claim.

## Receipt

- baseline: `<local-bundle>/d7bfc37218e78d896784ecec2ae59441` (verified=True, events=1125)
- candidate: `<local-bundle>/6ad7c273c60ecb07de25af9e8f0a83cf` (verified=True, events=1070)
- hypothesis: Encoded faction operand in task-55's faction-slot readback causes engine error spam and log/cadence corruption; raw faction id + server/City gating should remove it.

## Gaps / unknown

- perf_unknown:cpu_seconds
- perf_unknown:peak_memory_kib
- perf_unknown:tick_cadence_seconds

## Metric deltas (baseline -> candidate)

| metric | baseline | candidate | delta | heuristic |
| --- | ---: | ---: | ---: | --- |
| heartbeats | 42 | 20 | -22 | worse |
| ai_samples_per_heartbeat | 9.023809523809524 | 18.8 | 9.776190476190477 | better |
| combat_samples_per_heartbeat | 7.4523809523809526 | 15.3 | 7.847619047619048 | better |
| missing_heartbeat_intervals | 0 | 17 | 17 | worse |
| non_monotonic_ticks | 0 | 0 | 0 | same |
| engine_error_total | 4 | 3234 | 3230 | worse |
| max_log_bytes | 295436 | 796802 | 501366 | worse |

_Note: metric deltas only; verdicts are heuristic and no acceptance is implied_

## Performance proxies

- duration_seconds: 630.422
- heartbeats: 20
- heartbeat_coverage: 0.4758717176748273
- missing_heartbeat_intervals: 17
- ai_samples_per_heartbeat: 18.8
- combat_samples_per_heartbeat: 15.3
- agents_mean: 23.5
- engine_error_total: 3234
- engine_error_breakdown: {'script_error': 3234, 'invalid_faction': 3234, 'invalid_faction_min': 3230, 'invalid_faction_one': 4, 'illegal_lvalue': 0, 'stack_trace': 0}
- engine_errors_per_second: 5.1298971165346385
- max_log_bytes: 796802
- cpu_seconds: unknown
- peak_memory_kib: unknown
- wse2_stats_available: True

## Anomalies

- [medium] missing_heartbeat_intervals: 17 heartbeat tick gaps
- [high] invalid_faction_negative_spam: 3230 x Invalid Faction ID: -2147483648
- [high] script_error_spam: 3234 x SCRIPT ERROR lines

## Static module inspection

- trigger-like lines (all mission templates): 1948; top delays: 1.0x151, 0.0x128, 3.0x63, 2.0x52, -21.0x50, 10.0x44, -25.0x42, -19.0x41
- slow 894 slot writes: 93 (first slots ['200', '201', '202', '200', '201', '202', '203', '204', '205', '206', '207', '208']...)
- invalid faction literals (`502 3 -1`): 0
- 2093 speed triggers: 1
- gaps: []

## Next hypothesis

Merge task-55 faction-fix, rebuild probe, D re-seals; verify 0 x -2147483648/opcode 522, heartbeat coverage restored, wave_faction_slots present server-side. Then run controlled A/B with identical behavior knobs.

## Notes

Iteration-0 scope: baseline = D task45-wave2 sealed bundle (build before the
task-55 probe readback); candidate = D task55-wave2 sealed bundle (task-55
readback present). These are not a controlled A/B — the probe overlay/installed
build differs — so deltas are diagnostic, not causal.

Probe/granularity change under test: task-55 added faction_get_slot(522) /
store_current_scene(2211) readback of wave slots 200/221/231/241/245 and the
current scene. The candidate bundle shows the encoded faction operand producing
Invalid Faction ID: -2147483648 from the probe's Lua condition callbacks; that is
the regression this iteration isolates, not a gameplay change.

Keep/discard decision: DISCARD the encoded-operand call (fixed in
`agent/c-task55-faction-fix` 07c85e4: raw faction id 16, operand bounds
validation, server+City heartbeat gating). KEEP the slot/scene readback once
re-sealed.

Performance: duration/heartbeat coverage/event rates are measured from recorder
data; CPU seconds and peak memory are unknown (recorder metrics source
unavailable); WSE2 stats options are present in rgl_config.ini but were not
enabled, so no engine-side stall measurement is claimed. tick_cadence_seconds is
unknown because ZDB1 lines carry no wall-clock timestamps; heartbeat gaps are
inferred from count deltas only.

Static inspection is of the CURRENT installed module (post A trigger-14 guard),
not necessarily the exact build used for either bundle: 31 final triggers, 93
slow-894 slot writes across two triggers, 0 invalid faction literals after the
guard, 1 speed trigger (2093).

Next: merge 07c85e4 + rebuild probe, D re-seals the same installed build;
expected 0 x Invalid Faction ID:-2147483648 / opcode 522, restored heartbeat
coverage, and wave_faction_slots only on server heartbeats. Then run a controlled
A/B with identical behavior knobs.
