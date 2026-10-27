# AI combat: early engagement and order discipline

**Status:** project guidance, not acceptance evidence. This file is the shared
operating note for City survivor/zombie combat changes. It does not authorize
installs, builds, game launches or public claims. Runtime claims require a
sealed D bundle and A/C review; owner acceptance remains separate.

## Scope

Covers survivor ranged engagement, hold/standoff behavior, fire-order scope,
invader wave/spawn arguments, and the evidence needed to say a combat change
works. It applies to City-only overlays such as `tools/city_defense.py`,
`tools/native_wave_patch.py`, `tools/wave_reinforcements.py`,
`tools/zombie_nerf.py`, `tools/zombie_head_armor.py` and related loader/build
paths. It does not cover map assets, legal/IP clearance, launcher UX or
progression design except where they gate a combat run.

## Assumptions (verify before relying on them)

1. Firearms are **crossbow-type** in the pinned 2012 module; AI weapon choice and
   proficiency follow crossbow behavior, not modern firearm code.
2. `mordr_hold`/`mordr_stand_ground` are **movement/stance orders**, not a hard
   no-chase leash. Local melee engagement can still occur; measure it.
3. `team_give_order`/`team_set_order_position` address **order sub-classes 0..9**.
   Native AI groups (observed 26/28/29/31) are not proven to map to those
   sub-classes; division/group adoption remains unverified.
4. `add_visitors_to_current_scene`'s 5th argument is the **MP leader/owner player
   id**, not a formation group. Passing 5..7 is the wrong type; sentinel `0`
   semantics remain unverified.
5. There is **no public target setter/focus-fire API** in the reviewed WSE2
   surface. We can order fire discipline and placement; we cannot prove "shoot
   the ally's target".
6. A single build/run cannot establish causality. Parameter A/B needs one named
   change, known build/probe SHA, formation/seed/spectator metadata and
   replication.

## Procedures

### Before a combat candidate
1. State one feature slice and the exact build flags in the candidate manifest.
2. Record base branch/SHA, build SHA, receipt SHA, probe SHA and test results.
3. Do not stack unrelated features in one manifest; use one package per slice.
4. Keep `runtime_verified=false` and `acceptance=none` until D seals.
5. Confirm no absolute local paths are committed in manifests/docs.

### Building and reviewing
1. Build from a pinned base; verify receipt fields, not only CLI output.
2. Run static tests and `verify_city_chain.py` for the exact build mode.
3. Check the mission trigger for the promised ops (fire orders, stances,
   speed/HP/shield changes) before asking for a run.
4. Hand off a single package path or private package label; never claim install.

### Runtime validation
1. D seals with the matching probe and summary; start/mid/end **spectator or
   overview** frames are required for every behavioral validation.
2. Fire volume is proven only by an **ammo-delta shot measurement without
   refill masking** (or a pre-refill sampler), never by attack-action counts
   alone. Report `shots`, `agents_fired_ratio`, `shots/min`, first-shot time and
   the measurement method.
3. Charge/stand-still claims are positional proxies until an engine behavior
   getter exists; report charge ratio and displacement windows, not causality.
4. UNKNOWN is a valid result. Never convert missing telemetry into a PASS.
5. A review-b2/E reviewer must re-check packages; builders do not self-approve
   peers or accept their own evidence.

## Evidence and gates

| Claim | Minimum evidence | Gate |
| --- | --- | --- |
| Fire volume improved | refill-off ammo-delta summary, sealed bundle, spectator frames | first shot <30 s, `agents_fired_ratio >= 0.4`, `shots/min >= 5` (provisional) |
| Stance/hold works | positions, charge/backward displacement, attack-action | no hard no-chase claim without repeated sealed runs |
| Order scope reaches bots | order readback/telemetry or observed fire from all classes | do not claim if adoption unproven |
| Speed/HP/shields changed | build receipt fields + troop/mission diff hashes | D validates runtime |
| Target focus/assist | engine target getter or replicated causal A/B | **blocked**: no public setter |
| Wave/spawn argument fixed | contract/static test + sealed spawn evidence | leader-id 0 kept; sentinel unverified |

## Common failures

| Symptom | Likely cause | Required response |
| --- | --- | --- |
| Zero shots after "hold" build | `stand_ground`/aggressiveness suppression, wrong order scope, fire order not reaching native group | remove suppressor, sweep sub-classes 0..9, reseal with refill off; do not claim a fix from kills |
| Only ~20% defenders fire | order scope or group mapping, target/range state, sampler coverage | separate order-scope vs range with forward variant; report UNKNOWN until proven |
| Refill build shows zero ammo burn | ammo refill masks ammo-delta shot inference | measurement build with refill disabled; never claim zero shots from masked data |
| `add_visitors` produces no allies | 5th arg passed as 5..7 instead of leader/owner id | use id 0 path; keep "do not pass 5..7"; sentinel still unverified |
| "Focus fire" claim | no target setter exists | delete claim; only order/placement/fire-at-will evidence allowed |
| Build path/tree hash mismatch | manifest stale or tree hash algorithm undocumented | rebuild manifest from package; document `package_tree_sha256` algorithm |
| Charge still visible | hold is not a leash; adoption unproven | measure charge ratio; do not claim no-chase |

## Handoff / review

Handoff must include: branch + SHA; package label/path (private); `included` and
`excluded` arrays; build flags; receipt SHA and key fields; tests run; known
gaps; `runtime_verified=false`; `acceptance=none`. Reviewers verify the package
and receipt independently; they may block for path leakage, feature stacking or
unverified hashes. D owns runtime sealing; A/C review claims; Lead/owner decides
acceptance. No install, merge or launch without explicit authorization.

## File map

| Path | Purpose |
| --- | --- |
| `AGENTS_AI_COMBAT.md` | this guidance |
| `.agents/skills/ai-combat-early-engagement/SKILL.md` | focused skill |
| `tools/city_defense.py` | City orders/formation/fire scope |
| `tools/native_wave_patch.py` | original trigger-14/15 table and speed |
| `tools/wave_reinforcements.py` | `add_visitors`/wave support |
| `tools/zombie_nerf.py`, `tools/zombie_head_armor.py` | invader HP/proficiency/head armor |
| `tools/zombie_block.py` | canonical shield policy |
| `tools/build.py` | City build flags/receipt |
| `tools/verify_city_chain.py` | static chain verifier |
| `launcher/release_gate.py` | privacy/release checks |
| `telemetry/` | heatmap/analysis inputs/outputs |
| `local/session/` | private sealed evidence and frames |
| `reference/` | research/design evidence (Rhodok stance, class matrix, map defense) |
| `builds/` | candidate manifests (no absolute paths) |
