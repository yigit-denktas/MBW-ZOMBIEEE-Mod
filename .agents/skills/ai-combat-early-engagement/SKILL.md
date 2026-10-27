---
name: ai-combat-early-engagement
description: Use when survivors charge instead of firing, fire volume is zero or low, survivors stand idle at range, fire orders appear not to reach AI bots, a combat "fix" is being claimed from kills/attack-actions alone, or a wave/spawn argument is involved in a City combat candidate.
---

# AI combat early engagement

**Type:** discipline-enforcing technique (ranged survival AI). **Baseline:** a
City build added hold/stand-ground and "no-chase" intentions; defenders held
position but fired **zero** shots, and a later build produced only ~20%
defenders firing with first shot ~67–187 s. Killing counts (18/8, 16/8) masked
the failure. Root lessons: hold is not a leash, order scope must be proven,
ammo refill masks shot inference, and there is no target setter.

## Iron rule

**Do not call a combat change effective until a refill-off, ammo-delta shot
measurement shows defenders actually fire early and repeatedly.** Position,
attack-action counts, kills or "they held" are not fire evidence.

## Required sequence (one feature slice at a time)

1. **Name one change only** (order scope, stance, spawn argument, speed/HP,
   shield/head-armor, etc.) and pin the base branch/SHA.
2. **Check order scope before behavior claims.** `team_give_order` addresses
   sub-classes 0..9; native AI groups (e.g. 26/28/29/31) are not proven to map
   there. If fire is low, sweep fire_at_will/use_ranged across sub-classes 0..9
   and report whether the order was observed—do not assert adoption.
3. **Do not use `mordr_stand_ground` or aggressive-0 as a no-chase proof.**
   Stand-ground is a halt corrective; it can suppress engagement. Keep
   hold + fire_at_will + use_ranged; measure charge/backward displacement as a
   proxy.
4. **No refill during shot measurement.** Build a measurement variant with
   ammo refill disabled, or sample pre-refill ammo. Otherwise `ammo_burn=0` is
   ambiguous; report `shot_measurement.proven=false`.
5. **Ammo/spawn argument:** `add_visitors_to_current_scene` 5th arg is the MP
   leader/owner player id — **do not pass 5..7**; use the 0 path and mark the
   sentinel unverified.
6. **No target-setter claim.** The engine chooses targets; only placement,
   fire_at_will/use_ranged and order scope are ours. Describe "focus fire" as
   UNKNOWN/blocked, never as implemented.
7. **Evidence package:** branch/SHA, receipt SHA, included/excluded arrays,
   static tests, sealed bundle, **spectator/overview start/mid/end frames**, and
   `runtime_verified=false`/`acceptance=none`.

## Pressure scenario (GREEN test)

An owner run shows survivors standing behind sandbags, zombies at the line, no
muzzle fire; telemetry says `ammo_burn=0`, `attack_actions` nonzero, kills are
15/7, and the prior build had 4 shots. A tempting move is to ship the build
because "they held and won the fight."

**Correct behavior:** stop; classify fire volume as **UNKNOWN**; check whether
stand_ground/aggressiveness was enabled; check order-scope sweep; require a
refill-off reseal with `shots`, `agents_fired_ratio`, `shots/min`, first-shot
time; do not claim a fix, do not infer shots from attack actions or kills, do
not install. If the reseal still shows zero, do not add more normalizers:
diff the actual order path and use the forward/short-range variant to separate
order scope from range/timing.

## Checklist

- [ ] One named feature slice; base + build SHAs pinned
- [ ] No absolute local paths in manifest/docs
- [ ] Fire orders issued (hold/fire_at_will/use_ranged), no 1730 scripted charge
- [ ] Order scope checked (sub-classes 0..9); adoption marked unverified
- [ ] No stand_ground/aggressiveness used as no-chase proof
- [ ] Measurement build has ammo refill off (or pre-refill sampler)
- [ ] `add_visitors` leader/owner id 0 path; 5..7 never passed
- [ ] No target-setter/focus-fire claim
- [ ] Refill-off reseal: shots > 0, first shot < 30 s, `agents_fired_ratio >= 0.4`, `shots/min >= 5` (provisional)
- [ ] Spectator/overview start/mid/end frames reviewed
- [ ] Receipt and package hashes independently verified; no feature stacking
- [ ] `runtime_verified=false`; acceptance left to owner/Lead

## Red flags (stop and reclassify)

- "They held position, so the fix works." (Hold ≠ fire.)
- "Kills improved, so the guns work." (Kills can be melee/native.)
- "attack_actions/release_actions prove shots." (They do not; no engine shot event.)
- "Refill build has zero ammo burn, so zero shots." (Refill masks ammo deltas.)
- "We set stand_ground and 1737=0, so they cannot chase." (No hard leash.)
- "Reinforcements use group 5..7 for team 0." (That arg is a leader id.)
- "Focus fire is implemented." (No target setter.)

## One lesson

**Prove fire with a refill-off ammo-delta reseal and spectator frames before
attributing any survivor engagement change to stance, order scope or spawn
arguments.**
