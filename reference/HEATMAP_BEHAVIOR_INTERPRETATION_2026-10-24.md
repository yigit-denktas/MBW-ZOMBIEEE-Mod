# Heatmap behavior interpretation (task-74 / issue #54)

**Source:** E `agent/e-spatial-heatmaps` @ `3568a3d` (PR #58), sample
`telemetry/AI_MOVEMENT_HEATMAP_SAMPLE_2026-10-24.md`. Read-only interpretation by A.
**No game launch, no acceptance, no causal/tactical claim.** The plots are sparse
15 s occupancy/flow samples, not engine trajectories.

## Runs and provenance

| Run | Team-0 samples | Team-1 samples | Waves | Build/probe SHA | Formation mode | Class/division/HP |
| --- | --- | --- | --- | --- | --- | --- |
| `d7bfc372` task45-wave2 | 526 pts / 47 team-incarnation tracks (30 unique IDs) | same bundle | 0–4 | **unknown** | **unknown** | missing |
| `257b29b1` task55-p0 | 572 pts / 45 team-incarnation tracks (28 unique IDs) | same bundle | 0–1 | **unknown** | **unknown** | missing |

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
   forward-hold success: the wave-1 mean-alive low is 2.33, then later samples include
   respawns/new agents (wave 2 mean alive 8.0, wave 3 4.0, wave 4 6.0), so the drift is
   **survivorship/combat displacement**, not a monotonic alive decline. It is consistent
   with the nearest guard post 3 (185.2,185.0), but with no division/class data it cannot
   be called role-based occupation.
3. **No fallback condition is sampled.** These bundles contain no `mode=1`/fallback
   condition samples; the adaptive fallback branch (round-ended/outnumbered → base) is
   therefore **unobserved**, not validated. Outnumbered windows dominate, but counts are
   **dataset-specific**: raw task45 = 308 outnumbered / 526 points; C export of the same
   run = 375 / 692 points; task55 raw = 388 / 572 points. No northward regroup trace is
   distinguishable from attrition in either dataset.
4. **Cohesion proxies track sample composition, not an ordered formation.** Spread RMS
   drops 4.0 → 0.64 → near 0 as the sampled survivor set mixes deaths and respawns; this
   is a sampling/survivorship effect, not evidence that a tighter formation was ordered.
   Local superiority/advantage windows are too sparse to compare.
5. **Team-1 stays on the southern approaches.** Task45 team-1 centroids (137.6,139.6) →
   (161.9,155.5); no north-side entry appears. This supports the E map claim of SW/S/SSE
   clusters and **not** a 360° encirclement, but remains a sample-shape observation.
6. **Movement-class proxies are confounded and track-level.** 64 mixed / 24 over-moving /
   4 under-moving are **team-incarnation track** counts (58 unique IDs across the two raw
   runs; C export task45 = 31 unique / 53 tracks, raw task45 30/47, raw task55 28/45).
   Team-1 has 17 over-moving vs team-0 7, and all 4 under-moving are team-0. This is
   expected from role, alive/dead sampling and target availability; it does **not** rank
   “charging” or “too static” behavior and does not validate task-53.
7. **Chokepoint candidate (167.5,187.5)** at the north base/apron is more likely
   spawn/base dwell than a scene blocker; no collision/navmesh/LOS ground truth exists.

## Behavior interpretation (bounded)

- The plots are **consistent with a base/anchor phase followed by attrition-driven
  dispersal**, not with a proven formation hold or adaptive fallback.
- There is **no evidence for class/role separation** (commando/sniper/scout/lumberjack):
  the older samples have no class/division fields, and task76’s class/division are
  **source-troop fallback**, not verified role identities — any role/formation claim
  would be fabricated.
- There is **no evidence for the adaptive fallback/regroup path**, because no fallback
  condition and no round-end identity are present.
- The only map-level claim supportable is the **southern-cluster / north-safe** direction,
  and even that is descriptive.

## task76 baseline (first heartbeat-bearing sample; not A/B)

Metadata improved: mission `df21ae88…`, scripts `b6a7cdde…`, probe `bf39a37`/reported
`78AB1AE8`, map `tbfc_invasion_4`/`mst_multiplayer_iv`, fixed 15 s, survivor-idle
perspective, team 8/8, 31 frames, probe-health ok; 229 pts / 14 heartbeats / 20 unique
IDs / 28 tracks, waves 0–1, conditions 160 outnumbered / 61 even / 8 unknown. Still
missing: **formation_mode, seed, entry ids, round-end**; class/division values are
**source-troop fallback (0/1 only), not verified role identities**; screenshots are
faction-screen only (no usable visual); `runtime_verified=false`. Hit attribution is
broken (0/296) but does not affect the heatmap input.

Bounded reading:
- Team-0 wave 0 centroid (165.35,176.81), spread 6.81, mean alive 3.75, anchor share
  0.667; wave 1 centroid (166.33,152.62), spread 7.14, mean alive 2.55, anchor share
  **0.0**. This is **southward displacement away from the north anchor**, not a fallback
  toward it. It is consistent with combat/attrition/engagement drift (or survivor-idle
  sampling), **not** with a validated adaptive fallback or a forward-post hold.
- Team-1 wave 0 centroid (157.49,128.08), spread 27.25; wave 1 (164.87,151.99), spread
  11.32 — the two sampled masses move toward each other and team-1 tightens. This is a
  single sparse baseline; no 360° encirclement claim.
- 21 mixed / 7 over-moving / 0 under-moving across 28 tracks; no chokepoint cell survives
  threshold. No role separation can be claimed from source-troop-fallback divisions.
- **No fallback condition/round-end is present**, so task-53 adaptive fallback remains
  unobserved; this is a single baseline, not an A/B result.

## Required before a task-53/62 behavior verdict

1. D sealed run on a **known build SHA** (candidate `abc6e51` formation branch or P0
   base) with **formation mode recorded** (`rear`/`forward`/`adaptive`), seed and
   spectator/overview status.
2. Probe fields: verified `class_id`/`division` (not source-troop fallback), health/HP,
   round identity, and `ts_ms`/cadence; task76 has sampled HP/class/division but divisions
   are fallback-only, and it has no round-end — role and fallback claims remain blocked.
   Hit attribution must also be fixed (task76 is 0/296, param-invalid).
3. A **fallback event window** (round-ended or outnumbered → base) with enough samples to
   see northward displacement, plus a matched forward-hold window.
4. Spectator/overview **visual** start/mid/end + formation screenshots; A review before
   any result note.
5. Report division/group adoption status separately — C/H evidence says native groups
   26/28/29/31 are outside sub-class 0–9, so orders may be no-ops.

Until then: **descriptive only; no causal, behavior-acceptance, or task-53/62 completion
claim.**
