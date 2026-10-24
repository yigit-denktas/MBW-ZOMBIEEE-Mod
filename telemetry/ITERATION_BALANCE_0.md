# Bot-vs-bot balance analysis

Schema: `zombieee.balance-analysis.v1` | acceptance: **none** | runtime_verified: **False** | causality: **not established**

## Runs

| run | verified | rounds | team0 wins | team0 wipes | max wave |
| --- | --- | ---: | ---: | ---: | ---: |
| `6e5fe46149fc8022f5eac830e3aaed34` | True | 8 | 0 | 0 | 1 |
| `257b29b1d9b62da9755f54bef063c0a9` | True | 29 | 0 | 2 | 1 |

## Troop/class contributions (lower bound)

- `6e5fe46149fc8022f5eac830e3aaed34`: team0=[] kills_lower_bound=0; team1=[] kills_lower_bound=0
- `257b29b1d9b62da9755f54bef063c0a9`: team0=[{'troop': 984, 'name': None, 'agents_sampled': 9, 'kills_lower_bound': 12, 'kills_share': 0.522}, {'troop': 982, 'name': None, 'agents_sampled': 2, 'kills_lower_bound': 7, 'kills_share': 0.304}, {'troop': 983, 'name': None, 'agents_sampled': 1, 'kills_lower_bound': 3, 'kills_share': 0.13}, {'troop': 981, 'name': None, 'agents_sampled': 6, 'kills_lower_bound': 1, 'kills_share': 0.043}] kills_lower_bound=23; team1=[{'troop': 894, 'name': None, 'agents_sampled': 27, 'kills_lower_bound': 17, 'kills_share': 1.0}] kills_lower_bound=17

## Parameter sensitivity (correlational, not causal)

- unavailable: parameter_metadata_missing

## Ranked small-change recommendations (confidence/unknowns explicit)

- none (insufficient runs/parameter variants; not evidence of no effect)

## Gaps (become new tasks)

- hit_attribution_unavailable
- insufficient_runs_for_ranked_recommendations
- kill_causality_not_established
- parameter_metadata_missing
- per_troop_death_unavailable
- perf_unknown:cpu_seconds
- perf_unknown:heartbeat_count
- perf_unknown:peak_memory_kib
- perf_unknown:tick_cadence
- perf_unknown:tick_cadence_seconds
- round_end_event_missing
- wall_clock_round_survival_unknown

## Gaps as tasks

- add an explicit round-end/wipe event or a documented round boundary — round_end_event_missing
- trace per-hit/per-death attribution or a kill-event stream — hit_attribution_unavailable
- record wall-clock round survival time — wall_clock_round_survival_unknown
- carry the build/parameter receipt (fire_mode, defender_target, speed, ammo) into every sealed bundle — parameter_metadata_missing
- record per-troop deaths/alive counts — per_troop_death_unavailable

_wipe/win is called only when an observed alive count is zero; rounds without an explicit end are labelled no-wipe/reset; sensitivity is correlational and frozen unless parameters were carried with the run. Recommendations require a new sealed run._
