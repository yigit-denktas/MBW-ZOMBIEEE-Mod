# Replay / A-B behavior caption protocol (task-74 follow-up)

**Status:** caption/interpretation protocol only. No dense-frame run exists yet; no
visual, causal, or acceptance claim. Formation branch `abc6e51` is frozen.

## Inputs required before captions

Each side (baseline and variant) must carry: run id; **build SHA** and **probe SHA**;
map/entries; **formation mode**; seed; sample cadence/frame count; spectator/overview
flag; alive/HP/class/division (when available); condition/round identity; sealed bundle
id and screenshot paths. Baseline vs variant must share map, seed, build/probe, formation
mode and cadence; **exactly one parameter may differ** and must be named
(e.g. `defender_target=4` vs `8`). Missing metadata is labelled **unknown**, never
inferred or silently matched.

## Caption structure per side

For each phase — **start/base**, **wave transition**, **fallback/regroup**, **end** —
write:

1. What is directly visible: survivor and team-1 occupancy, centroid/spread,
   anchor/post proximity, movement proxy, chokepoint candidates.
2. What is measured: sampled path length/net displacement/stationary ratio,
   northward displacement, cohesion proxies, condition counts (dataset-specific).
3. What is **not** observable: engine velocity, target choice, true formation order
   adoption, morale/rout, collision/LOS.
4. One bounded caption sentence, e.g. “Samples are consistent with X during phase P;
   this is descriptive and not proof of the ordered formation.”

## A-B comparison rules

- Compare the **same phase window** and the **same sample definition**; if cadence or
  agent counts differ, report that as a confound before any difference.
- Label the single changed parameter; state the expected direction and whether it was
  observed, not observed, or confounded.
- Report effect size and sample count; a difference smaller than the sparse-cadence
  uncertainty is “no distinguishable difference.”
- **Butterfly effects:** early divergence that amplifies into a different later phase is
  marked **descriptive, unreplicated**; do not attribute it to the changed parameter
  until at least **two independent seeds/runs per side** replicate the same phase
  direction.
- Distinguish **attrition/survivorship** shifts from formation/order shifts by reporting
  alive/HP and respawns; a survivor-set composition change alone is not a behavior change.
- No causal language (“causes”, “proves”, “fixes”); use “is consistent with”, “is not
  distinguishable from”, “replicated/not replicated”.

## Caption template

```text
Run A (baseline, param=<value>, build=<sha>, probe=<sha>, mode=<formation>, seed=<n>,
cadence=<s>, frames=<n>):
  start/base: <bounded caption>
  wave transition: <bounded caption>
  fallback/regroup: <bounded caption or "not sampled">
  end: <bounded caption>
  confounds: <metadata/sparsity/attrition>
Run B (variant, param=<value>, ...): same fields.
A-B: changed parameter=<name>; direction=<expected>; observed=<yes/no/confounded>;
  effect=<descriptive>; butterfly=<none/descriptive-unreplicated>; replication=<n runs>.
No visual/causal/acceptance claim.
```

## Gate

Captions can only be produced after D seals a **dense-frame, metadata-complete** run pair
with the changed parameter named. A reviews the spectator start/mid/end + formation
images; screenshots alone or sparse samples do not produce an acceptance verdict.
