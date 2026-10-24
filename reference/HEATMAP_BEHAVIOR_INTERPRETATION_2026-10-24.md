# Heatmap behavior interpretation (task-74 / issue #54)

**Source:** E `agent/e-spatial-heatmaps` @ `3568a3d` (PR #58), sample
`telemetry/AI_MOVEMENT_HEATMAP_SAMPLE_2026-10-24.md`. Read-only interpretation by A.
**No game launch, no acceptance, no causal/tactical claim.** The plots are sparse
15 s occupancy/flow samples, not engine trajectories.

## Runs and provenance

| Run | Team-0 samples | Team-1 samples | Waves | Build/probe SHA | Formation mode | Class/division/HP |
| --- | --- | --- | --- | --- | --- | --- |
| `d7bfc372` task45-wave2 | 526 pts / 47 agents | same bundle | 0–4 | **unknown** | **unknown** | missing |
| `257b29b1` task55-p0 | 572 pts / 45 agents | same bundle | 0–1 | **unknown** | **unknown** | missing |

Because build SHA and formation mode are absent, **none of these panels can be tied to
the task-53/62 formation branch `abc6e51` or to a rear/forward/adaptive build**. They are
baseline observations only.

## What the plots are consistent with

1. **Early base/anchor dwell is present, not proof of a hold.** Task45 wave 0 team-0
   centroid (165.2,178.6), spread RMS 4.0, near-anchor share 0.79, mean alive 4.69. This
   is compatible with the rear/base anchor and native spawn behaviour, but the same
   signature would appear from spawn/base dwell. No `formation_mode` or order-adoption
   evidence explains it.
2. **Survivor sample drifts east/south after wave 0.** Wave 1 centroid (181.6,180.8),
   anchor share 0.11; wave 2 centroid (192.0,186.9), anchor share 0.0. This is **not** a
   forward-hold success: mean alive fell to 2.33 and then fewer, so it is dominated by
   **survivorship/combat displacement**. It is consistent with the nearest guard post 3
   (185.2,185.0), but with no division/class data it cannot be called role-based
   occupation.
3. **No fallback condition is sampled.** These bundles contain no `mode=1`/fallback
   condition samples; the adaptive fallback branch (round-ended/outnumbered → base) is
   therefore **unobserved**, not validated. Outnumbered windows dominate (task45: 308
   outnumbered; task55: 388), yet no northward regroup trace is distinguishable from
   attrition.
4. **Cohesion proxies collapse with attrition.** Spread RMS drops 4.0 → 0.64 → near 0 as
   survivors die; this is a sampling/survivorship effect, not evidence that a tighter
   formation was ordered. Local superiority/advantage windows are too sparse to compare.
5. **Team-1 stays on the southern approaches.** Task45 team-1 centroids (137.6,139.6) →
   (161.9,155.5); no north-side entry appears. This supports the E map claim of SW/S/SSE
   clusters and **not** a 360° encirclement, but remains a sample-shape observation.
6. **Movement-class proxies are confounded.** 64 mixed / 24 over-moving / 4 under-moving;
   team-1 has 17 over-moving vs team-0 7, and all 4 under-moving are team-0. This is
   expected from role, alive/dead sampling and target availability; it does **not** rank
   “charging” or “too static” behavior and does not validate task-53.
7. **Chokepoint candidate (167.5,187.5)** at the north base/apron is more likely
   spawn/base dwell than a scene blocker; no collision/navmesh/LOS ground truth exists.

## Behavior interpretation (bounded)

- The plots are **consistent with a base/anchor phase followed by attrition-driven
  dispersal**, not with a proven formation hold or adaptive fallback.
- There is **no evidence for class/role separation** (commando/sniper/scout/lumberjack):
  class and division fields are absent, so any role/formation claim would be fabricated.
- There is **no evidence for the adaptive fallback/regroup path**, because no fallback
  condition and no round-end identity are present.
- The only map-level claim supportable is the **southern-cluster / north-safe** direction,
  and even that is descriptive.

## Required before a task-53/62 behavior verdict

1. D sealed run on a **known build SHA** (candidate `abc6e51` formation branch or P0
   base) with **formation mode recorded** (`rear`/`forward`/`adaptive`), seed and
   spectator/overview status.
2. Probe fields: `class_id`/`division`, health/HP, round identity, and `ts_ms`/cadence;
   otherwise role and fallback claims are blocked.
3. A **fallback event window** (round-ended or outnumbered → base) with enough samples to
   see northward displacement, plus a matched forward-hold window.
4. Spectator/overview **visual** start/mid/end + formation screenshots; A review before
   any result note.
5. Report division/group adoption status separately — C/H evidence says native groups
   26/28/29/31 are outside sub-class 0–9, so orders may be no-ops.

Until then: **descriptive only; no causal, behavior-acceptance, or task-53/62 completion
claim.**
