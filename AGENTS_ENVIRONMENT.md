# Environment / world / map design

**Status:** project guidance, not acceptance evidence. This file is the shared operating note for City
map layout, spawn protection, cover/barricade placement, lighting/visibility, collision and navmesh
work. It does not authorize installs, builds, game launches, scene edits or public claims. Scene changes
need owner approval, a new scene/SCO hash and D runtime validation.

## Scope

Covers the playable environment and its design evidence: survivor spawn protection, defensive hold
posts, cover/barricade and fallback/regroup layout, zombie entry ring and approach, line-of-sight,
lighting/visibility, collision/navmesh fit, scene-prop additions and the static/runtime gates for a scene
change. It does not cover AI order logic (`AGENTS_AI_COMBAT.md`), telemetry (`AGENTS_TELEMETRY.md`),
asset licensing specifics (`AGENTS_ASSETS.md`), runtime installs (`AGENTS_RUNTIME.md`) or acceptance.

## Assumptions (verify before relying on them)

1. **Baseline is read-only.** Existing City scene props (`spr_zombie_sandbag_wall`, barrels, `band_a`,
   plants, light poles) are native/original-ZOMBIEEE/third-party assets with no recorded redistribution
   right. The private/local build may reference them; a public/clean-room build must replace or omit them
   (`reference/LEGAL_RIGHTS_AND_CREDITS.md` R-03/R-05).
2. **Any scene edit changes identity.** Adding/moving props changes the scene/SCO byte identity; owner
   approval, a new hash and static/runtime revalidation are required. Do not hand-edit compiled scene
   files outside the normal build path.
3. **Collision is not just visual cover.** A barricade that changes walkable space needs a collision
   mesh and a navmesh/AI check; place it so it does not trap or block defender/zombie pathing.
4. **Spawn and entry distances are hard constraints.** The design uses a survivor spawn safe disc
   (SP1 radius 12 around the design midpoint) and ≥8 units from zombie entries; do not add props or
   orders that violate these without a new design decision.
5. **Lighting affects function.** Dark/bright conditions change reticle/icon visibility and target
   readability; lighting is part of the evidence, not decoration.
6. **Screenshots are required for visual claims.** No "looks right" claim without D-captured in-game
   frames from the same build/scene/camera and owner review.
7. **New props are licence-gated.** Any added environment asset follows `AGENTS_ASSETS.md` and the
   licence/intake skill; no native/original asset is bundled in a public artifact.
8. **One change per package.** Map/lighting/collision changes are not mixed with combat/telemetry
   packages; builders do not review peers.

## Procedures

### Design / analysis (no scene edit)
1. Read `reference/CITY_MAP_DEFENSE_DESIGN.md` and the current map/evidence; record the build SHA and
   observation date.
2. Decode/verify coordinates: survivor spawn, guard posts, zombie entry ring, hold/fallback sectors,
   existing cover and chokepoints. Keep coordinate tables reproducible.
3. State the design intention and the evidence class: decoded primary, inspected scene, design
   proposal, or unverified. Do not present a proposal as observed geometry.
4. Model the interaction: spawn protection → hold line → fallback → regroup; check multi-direction
   entry encirclement, line-of-sight/overwatch, retreat lanes and cover gaps.
5. For every proposed prop/barricade: classify as decorative or blocking; check collision, navmesh,
   scale, overlap and the SP1/entry constraints; record the asset decision (see `AGENTS_ASSETS.md`).
6. Mark owner-approval-required items explicitly. The baseline keeps **no new scene objects** until the
   owner approves optional additions.

### Scene/lighting/collision checks before handoff
- [ ] Coordinates and frame conventions consistent with `reference/CITY_MAP_DEFENSE_DESIGN.md` §1.
- [ ] No barricade inside the SP1 radius-12 disc or within 8 units of a zombie entry.
- [ ] No barricade in the central retreat/escape lane or blocking a hold-post exit.
- [ ] Collision mesh present and tested; no trap/overlap; props not floating or z-fighting.
- [ ] Navmesh/AI pathing check planned or completed; blocking props flagged as requiring D validation.
- [ ] Lighting/contrast checked for target and HUD/reticle readability on dark/bright/blood backgrounds.
- [ ] Scene/SCO hash recorded for any change; owner approval documented.
- [ ] Asset licence evidence recorded before any new prop (no binaries before approval).
- [ ] Screenshot matrix defined (same build/scene/camera; start/mid/end frames).

## Evidence and gates

| Claim | Minimum evidence | Gate |
| --- | --- | --- |
| Map layout/coordinates | reproducible coordinate table + frame convention + source (decoded/inspected/proposal) | no navigation claim from prose |
| Spawn protection design | SP1 radius/centre + entry distances + order constraints | owner/design approval; D validation |
| Cover/barricade placement | coordinates, collision/navmesh check, SP1/entry distances | owner approval before scene edit; D runtime |
| Lighting/visibility change | before/after in-game frames on required backgrounds | D capture + owner review |
| Scene edit is safe | new SCO/static hash + static tests + sealed D run | owner approval; no acceptance from static only |
| Visual result is acceptable | screenshot matrix + blind owner/E review | no claim without screenshots |

## Common failures

| Symptom | Likely cause | Required response |
| --- | --- | --- |
| Defenders/zombies get stuck or path oddly | barricade blocks navmesh or narrows retreat lane | remove/reposition; rerun navmesh check and D validation; do not call it "cover" if it traps AI |
| Barricade placed in spawn or entry zone | ignored SP1/entry constraints | move outside radius/entry distance; update design table |
| Props float, overlap or z-fight | no collision/scale/overlap check | fix transform/collision; re-check in screenshot pass |
| Scene changed without a gate | hand edit or unrecorded build step | restore last green scene; go through owner-approved build; record new hash |
| "Lighting looks fine" without frames | skipped screenshot evidence | withdraw claim; capture dark/bright/blood frames from the same build |
| Native/original props planned for public build | ignored redistribution boundary | replace with licence-cleared props or mark private-only |
| New prop added before licence check | skipped asset intake | remove; run `AGENTS_ASSETS.md` intake; no binary without gates |
| Visual acceptance claimed from design doc | design evidence treated as runtime proof | reclassify as UNKNOWN; require D screenshots + owner |

## Handoff / review

Handoff includes: design doc/coordinates, evidence class per claim, proposed prop/asset IDs (licence
status), checks run, scene/SCO hash (if any edit), screenshot status, unresolved unknowns and the exact
decision needed from the owner. A owns behavior, G owns asset/licence candidates, D owns runtime
screenshots/sealed validation, E/independent reviewer covers licence/claims, Lead integrates. Builders do
not review peers or self-approve; no scene edit, install or launch without explicit authorization.

## File map

| Path | Purpose |
| --- | --- |
| `AGENTS_ENVIRONMENT.md` | this guidance |
| `AGENTS_ASSETS.md` | asset/licence intake for props and cosmetics |
| `.agents/skills/asset-licence-intake/SKILL.md` | licence/intake discipline skill |
| `reference/CITY_MAP_DEFENSE_DESIGN.md` | City spawn protection, hold line, barricades, regroup design |
| `reference/FREE_ASSET_SOURCES.md` | environment/cover prop candidates, licence decisions, registers |
| `reference/ASSET_INTAKE_CHECKLIST.md` | intake checklist (pending merge; use the skill checklist meanwhile) |
| `docs/ICON_MAPPING.md` §10 | in-game screenshot comparison plan (visual claims) |
| `reference/LEGAL_RIGHTS_AND_CREDITS.md` | rights/re­distribution boundary (R-03/R-05) |
| `tools/verify_city_chain.py` | City static/trigger chain verification |
| `local/session/` | private sealed evidence and screenshots (gitignored) |
