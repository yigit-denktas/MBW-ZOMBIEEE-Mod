# City map defense design - spawn protection, hold line, barricades, fallback/regroup

**Status:** static map/geometry design proposal. **Docs-only:** no scene/SCO edit, no
prop or entry-point change, no binary asset, no game launch. Any scene change needs
explicit owner approval and the normal City static/runtime gates. This document makes
**no** runtime, visual, LOS, collision, pathing or acceptance claim.

- **Observed:** 2026-10-24, from branch `agent/e-city-map-defense` (base `main` 0e4b01b).
- **Owner task:** task-63 (City map/environment design).
- **Related:** [City guard hardening](CITY_GUARD_HARDENING_2026-10-24.md),
  [survivor AI behavior contract](CITY_SURVIVOR_AI_BEHAVIOR_CONTRACT_2026-10-24.md),
  [City defence overlay](../docs/CITY_DEFENSE.md),
  [tactical recovery](../docs/TACTICAL_RECOVERY.md),
  [zombie entry/wave audit](CITY_AI_WAVE_AUDIT_2026-10-23.md),
  [round/wave lifecycle](CITY_ROUND_WAVE_LIFECYCLE_2026-10-24.md).

**Non-claims.** The original ZOMBIEEE and Warband assets remain native/third-party
material with no recorded redistribution right; this design does not clear them. City
outcomes stay **0/23**, milestones **0/5**, `runtime_verified=false`; no ledger leaf is
accepted by this document. Coordinates are **scene-local**, not geospatial.

## 1. Coordinate frame and evidence

- Frame: Warband scene-local X/Y/Z. **X increases east, Y increases north, Z is elevation.**
  Distances below are 2D X/Y scene units; the project's docs call them metres, but this is
  a convention, not a surveyed geospatial measurement.
- Bearings are **0 = +X/east, 90 = +Y/north, 180 = west, 270 = south**.
- Evidence classes: **decoded-primary** (SCO bytes decoded below), **source-doc**
  (existing project records), **proposal** (this document; unverified in engine).

| Evidence | Value |
| --- | --- |
| Original City SCO | `local/original-beta04/ZOMBIEEE/SceneObj/scn_tbfc_invasion_4.sco`, 115,408 bytes, SHA-256 `6766ba3a1bf1d3f5eda8ec922517f1149a070b3e60ba860a49be549e00889cca` |
| Overlaid City SCO (built module) | 115,660 bytes, SHA-256 `96159fa818b5c7d1c43e9bfc4e2d15e7b0edd4aa3e4e069409f76dd417a85a42` |
| Original objects / entries | 226 scene objects; 11 explicit entries (0, 1, 32-40) |
| Overlay objects / entries | 229 objects; adds reserved guard entries 2, 3, 4; original entries unchanged |
| Navmesh | 323 vertices, 600 edges, 270 faces; 218 vertices / 201 faces in the survivor-spawn connected component (`tools/scene_tactics.py` `plan_city`) |
| Decoder / planner | `tools/scene_tactics.py` (`decode_scene`, `plan_city`); hardened placement documented in `reference/CITY_GUARD_HARDENING_2026-10-24.md` lines 20-26 |
| Build behavior | `tools/build.py` line 98 (`defensive_line` default `"rear"`), line 254 (`REAR_HOLD_ENTRIES` vs `GUARD_ENTRIES`); `tools/city_defense.py` lines 31-37 |
| Current runtime state | `runtime_verified=false`; no engine observation in this task |

**Documentation discrepancy:** `docs/CITY_DEFENSE.md` still shows the **pre-hardening**
guard coordinates (165.500/169.267 etc.). The hardened coordinates used here are the
current deterministic `plan_city`/build-receipt values in
`CITY_GUARD_HARDENING_2026-10-24.md`; the older table should not be used for placement.

## 2. Map skeleton

### 2.1 Survivor spawn and guard line

| Point | Entry | X | Y | Z | Distance from entry 0 | Role |
| --- | ---: | ---: | ---: | ---: | ---: | --- |
| Survivor spawn A | 0 | 168.528 | 185.107 | 3.135 | 0.0 | rear spawn / fallback point |
| Survivor spawn B | 1 | 166.909 | 183.782 | 4.160 | 2.09 | rear spawn |
| Spawn midpoint (anchor) | - | **167.718** | **184.445** | 3.135 | 1.06 | proposed primary anchor / regroup centre |
| Forward screen centre | 2 | 169.423 | 169.376 | 3.191 | 15.76 | centre sector; sandbag cover 3.24 north |
| Right/east flank | 3 | 185.190 | 185.009 | 3.191 | 16.66 | east sector; light/pole/trash/sandbag cover |
| Left/west flank | 4 | 146.250 | 183.491 | 3.191 | 22.34 | west sector; light/pole/spiky-plant cover |

Guard pair separation: **2-3 = 22.20**, **2-4 = 27.13**, **3-4 = 38.97** scene units.
All three posts sit at Z 3.191; spawn midpoint is 0.06 lower. The forward line is
**15.8-22.3 units south/east/west of spawn**, spanning approximately X 146-185, Y 169-185.
Bearings from entry 0: post 2 = 273.3 (south), post 3 = 359.7 (east), post 4 = 184.2 (west).

### 2.2 Zombie entry ring (decoded primary)

Only entries **32-40** exist for invaders. They form **three tight clusters in the south**,
all far below the survivor spawn line (Y 113-129 vs spawn Y 184):

| Cluster | Entries | X range | Y range | Z | Distance from spawn midpoint | Bearing range | Nearest guard |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| A - south-west | 32, 33, 34 | 106.394-108.024 | 128.491-128.933 | 3.094-3.095 | 81.52-83.01 | 222.4-222.9 | 4 (66.6) |
| B - south | 35, 36, 37 | 156.022-158.113 | 113.294-113.511 | 3.653 | 71.75-71.93 | 260.6-262.3 | 2 (57.5) |
| C - south-east | 38, 39, 40 | 201.504-203.705 | 116.004-116.166 | 3.446 | 76.33-77.18 | 296.3-297.8 | 2 (62.7); 3 (71.0) |

Entry spacing inside each cluster is **0.7-2.4 units**; cluster centres are roughly
(107.2, 128.7), (157.0, 113.4), (202.6, 116.1). There is **no zombie entry in the north,
east or west half** of the scene. The original 25 mission triggers and entries 32-40 are
untouched by the City guard overlay.

### 2.3 Existing cover and structures near the line

Decoded prop origins (not collision bounds; a prop can be wider than its origin and LOS is
not measured):

| Object | X | Y | Z | Useful relation |
| --- | ---: | ---: | ---: | --- |
| `spr_zombie_sandbag_wall` | 169.390 | 172.612 | 3.0 | 3.24 north/rear of post 2; between post 2 and spawn |
| `spr_zombie_barrel` | 163.641 | 166.990 | 3.64 | 6.25 south-west of post 2 |
| `spr_zombie_barrel` | 153.220 | 169.440 | 3.64 | west approach; between posts 2 and 4 |
| `spr_zombie_barrel` | 186.160 | 170.840 | 3.39 | east approach; south of post 3 |
| `spr_zombie_sandbag_wall` | 158.552 | 174.279 | 3.0 | west-centre cover; ~15 from post 4, ~12 from post 2 |
| `spr_zombie_sandbag_wall` | 180.120 | 186.919 | 3.0 | 5.42 west/rear of post 3 |
| `spr_band_a` row | 155.88-156.01 | 171.08-186.96 | 3.04 | west street barrier line (N-S) |
| `spr_band_a` row | 179.89-180.28 | 171.66-187.51 | 3.04 | east street barrier line (N-S) |
| `spr_zombie_scn_prop_trash_bin_1` | 183.277 | 189.999 | 3.0 | 5.34 north of post 3 |
| `spr_zombie_scn_prop_light_pole` | 184.112 | 189.937 | 3.0 | 5.04 north of post 3 |
| `spr_light` | 183.980 | 187.810 | 7.293 | 3.05 from post 3 (elevated lamp origin) |
| `spr_light` | 150.028 | 185.858 | 7.425 | 4.46 from post 4 |
| `spiky_plant` (3) | 140.48-140.62 | 178.73-187.67 | 3.0 | west flank near post 4 |
| `spr_zombie_supermarket` | 166.880 | 199.380 | 3.0 | 14.4 north of spawn; rear landmark |
| `spr_zombie_high_rise7` | 180.950 | 134.080 | 3.0 | south of post 2 (central approach mass) |
| `spr_zombie_high_rise6` | 211.490 | 172.600 | 3.0 | east of post 3 |
| `spr_zombie_high_rise9` | 237.010 | 171.440 | 3.0 | far east |
| `spr_sack` / `spr_box_a` / `spr_tbfc_box4/5` | 170.03-171.98 | 188.54-189.45 | 2.96-3.79 | supply/loot props 4.4-5.2 east of spawn; **do not treat as cover or block them** |

The two `spr_band_a` rows form a rough pair of north-south street barriers around
X ~156 and X ~180 with the central corridor between them. This is a **static origin
reading**, not a measured street/LOS map; D must observe actual paths.

## 3. What "multi-direction encirclement" actually is here

The owner brief asks to explain multi-direction zombie encirclement. On this original
map the honest reading is **three converging southern approach axes, not a 360-degree
ring**:

- **A (south-west, 222-223 degrees)**: 3 entries at ~82 units; closest post 4 (66.6).
- **B (south, 261-262 degrees)**: 3 entries at ~72 units; closest post 2 (57.5) - the
  shortest approach to the forward line.
- **C (south-east, 296-298 degrees)**: 3 entries at ~77 units; closest post 2 (62.7) and
  post 3 (71.0).

All nine entries are south of Y 129; the survivor spawn is at Y 184. The rear (north,
toward the supermarket at Y 199) and the outer east/west flanks are **not zombie entry
directions**. Pressure becomes "encircling" only through **convergent pathing**: three
groups advancing north/north-east/north-west through the street grid, with the central
post 2 exposed to B and (secondarily) C, while 3 and 4 each face one flank.
Consequences:

1. The **north/rear is the safe anchor and fallback direction**, not a defended side.
2. The **centre is the pinch point**: post 2 is nearest to two clusters (57.5 and 62.7)
   and has the shortest time-to-contact if pathing is direct.
3. A full 360-degree encirclement would require **new zombie entries and scene edits**
   (owner approval, static + runtime revalidation); it is **not** assumed or proposed as
   the baseline here.
4. If waves activate all three clusters simultaneously, a three-sector screen can be
   pinched at the centre; the design therefore keeps a **north anchor + fallback** rather
   than committing every survivor to the forward line.

## 4. Spawn protection design

These are **behavior/geometry rules**, not engine capabilities. Warband/WSE2 does not
expose a proven "no-spawn radius" opcode here; if a rule cannot be enforced natively, it
must remain a design requirement for A/D or be dropped, not claimed.

| ID | Rule | Geometry / implementation | Status |
| --- | --- | --- | --- |
| SP1 | Survivor spawn safe disc | Radius **12** around midpoint (167.718, 184.445); no new prop/barricade, no forward hold order, no scripted survivor destination inside except spawn/regroup | proposal; guard posts are 15.8+ away so the disc does not swallow the forward line |
| SP2 | No zombie entry inside safe disc | All original zombie entries are 71.75+ away; keep it that way (no new entry within 12 of spawn) | decoded + design constraint |
| SP3 | Zombie entry exclusion for survivor orders | No survivor hold/scripted destination within **8** of entries 32-40 (prevents spawn camping and path blocking); current posts are 57+ away | proposal |
| SP4 | Wave spread gating | Until D proves pathing/performance, spawn/activate at most **one or two clusters per wave**, alternating A/B/C; do not drive all three simultaneously | behavior proposal for A |
| SP5 | No zombie scripted destination inside SP1 | If any scripted zombie destination/order is added later, clamp it outside the 12-unit disc | behavior proposal for A; engine support unverified |
| SP6 | Spawn exit lanes | Keep the three exit lanes (west via X ~155, centre via X ~169, east via X ~180) free of new props; no enclosure walls around spawn | design constraint |

Spawn disc rationale: guard posts at 15.8/16.7/22.3 are outside 12, so a player/survivor
can spawn, rearm at the item props 4-5 units east, and move to the line without crossing
a barricade. The supermarket 14.4 north is outside the disc. **Do not** add sandbags or
vehicles inside the disc merely to "protect spawn"; that would trap the spawn and block
the existing weapon/loot props.

## 5. Survivor anchor and defensive-line layout

Recommended three-echelon layout, from rear to front:

```
Y (north)
199 |  supermarket (166.9, 199.4)                      rear landmark
185 |  spawn 0 (168.5,185.1)   spawn 1 (166.9,183.8)   E0 anchor / regroup apron
183 |  post 4 (146.3,183.5)  [west street]  post 3 (185.2,185.0)   E1 flanks
172 |  sandbag (169.4,172.6)  barrel  band_a rows X~156 / X~180
169 |  post 2 (169.4,169.4)  centre forward screen    E1 centre
134 |  high_rise7 (180.9,134.1)                        south approach mass
129 |  A (107,129)          B (157,113)          C (202.6,116)   zombie clusters
     +X east ->
```

- **E0 - primary anchor (north apron):** centre (167.718,184.445), radius 6-8 for
  regrouping; fallback point is entry 0 (168.528,185.107). This is the **anchor of last
  resort**, not the forward line. It is co-located with the existing survivor spawn and
  the tactical-recovery fallback entry 0.
- **E1 - forward screen (three sectors):** post 2 centre (169.423,169.376), post 3 east
  (185.190,185.009), post 4 west (146.250,183.491). Recommended baseline assignment:
  division 5 -> post 2, division 6 -> post 3, division 7 -> post 4. A reserve survivor
  stays at/behind E0 when the defender count allows.
- **E2 - optional barricade/cover line:** existing sandbags/barrels/`band_a` rows and
  plants only; no new props in the baseline (section 6).
- **Fallback:** from E1 to E0 along the three street lanes. Existing
  `tactical_recovery` fallback entry is 0 with low-water 1; keep that destination.
- **Between-wave regroup:** assemble at E0 apron centre (167.718,184.445), inside radius
  6-8, **not** at post 2. Re-occupy E1 only after the wave transition/round start and a
  short settle delay; do not regroup in the exposed centre.
- **Rally points:** R0 = E0 centre; R1 = entry 0; R2 = post 2 only as a **forward rally**
  after a wave, not as a casualty fallback.
- **Why anchor north, not on the guard line:** the forward posts have no supply/cover
  depth, the centre is pinch-exposed, and the only player/survivor spawn and existing
  fallback entry are north. Anchoring at E0 keeps a retreat lane and avoids fighting with
  the back to the zombie clusters.

**Current behavior context:** `tools/city_defense.py` defines forward `GUARD_ENTRIES=(2,3,4)`
but `REAR_HOLD_ENTRIES=(0,1,0)`, and `tools/build.py` defaults `defensive_line="rear"`
(line 98); the build only uses 2/3/4 when `--defensive-line forward` is selected (line 254).
So the **default build profile** keeps survivors on rear entries and does **not** defend
the forward line; the forward entries are only used with `--defensive-line forward`. This
design proposes a staged choice (section 7), not a claim about any already-built artifact.

## 6. Barricade and cover plan

### 6.1 Baseline: no new scene objects

Use the existing props in section 2.3. They already provide:

- **Post 2 centre:** sandbag wall north/rear (169.390,172.612), barrel south-west
  (163.641,166.990), side barrier rows at X ~156 and X ~180.
- **Post 3 east:** sandbag wall west/rear (180.120,186.919), light/post/trash cluster
  north (183.3-184.1,189.9-190.0), barrel south (186.160,170.840).
- **Post 4 west:** light pole/light north (150.0,185.9), spiky plants west
  (140.5,178.7-187.7), trash bin north-east (152.0,188.1), barrel east (153.2,169.4).

This is the safest option: **no SCO edit, no new SHA, no new asset licence, no path
blocking**. Existing props are origin-clearance only; D must still validate collision
and LOS.

### 6.2 Optional owner-approved additions (not approved, not implemented)

If the owner wants stronger flank cover, these are **candidate slots**, not edits. They
must be checked for zombie pathing (keep >=4-unit gaps), navmesh placement, collision,
LOS and asset licence; any change requires owner approval and a new SCO hash/static gate.

| Slot | Candidate XY (Z ~3.0) | Purpose | Constraint |
| --- | --- | --- | --- |
| W1 | ~152.0, 177.5 | shield post 4's south-west approach, outside the west `band_a` row | keep >=4 gap to band_a at X 155.9; do not block west exit lane |
| E1 | ~188.0, 177.5 | shield post 3's south-east approach, outside the east `band_a` row | keep >=4 gap to band_a at X 180.0; do not block east exit lane |
| C1 | existing sandbag 169.390,172.612 | rear cover for post 2 | **no new prop**; do not add a centre barricade across the X ~156-180 corridor |
| A1 | ~164.0, 171.0 (optional barrel/sandbag) | rear-side cover for post 2 near existing barrel | risk of narrowing the central retreat lane; D must prove passable |

**Do not** place barricades: inside the SP1 12-unit spawn disc; within 8 of zombie entries;
across the central X ~156-180 corridor; on top of the item/loot props around
(170.0-172.0, 188.5-189.5); or in a way that seals all three lanes. Do not copy native
Warband/ZOMBIEEE props or any unlicensed asset.

**Overwatch:** the map has high-rise/military-HQ props but no decoded walkable roofs or
proven elevated AI-mesh access in this task. Do not assume roof overwatch; if the owner
wants it, A/D must prove navmesh access and collision first.

## 7. Behavior contract for Agent A

Proposed staged behavior (requires A implementation; no new native opcode is implied):

| State | Trigger | Destination | Notes |
| --- | --- | --- | --- |
| HOLD-FORWARD | >=3 living AI defenders, wave active | divisions 5/6/7 -> entries 2/3/4 hold-fire | baseline fixed sectors; optional parity rotation only if D confirms all sectors are covered each wave |
| FALLBACK | <=1 living AI defender | entry 0 (168.528,185.107) hold | existing `tactical_recovery` low-water behavior; keep |
| REGROUP | >=3 living AI defenders after fallback | E0 apron (167.718,184.445), then re-issue HOLD-FORWARD after a settle delay | design recommends regroup at the apron, not on the exposed forward line |
| SPAWN-LOCK | always | no survivor scripted destination inside SP1 radius 12; clamp orders outside | behavior guard; engine support for zombie side unverified |
| WAVE-SPREAD | wave start | activate 1-2 zombie clusters per wave, alternating A/B/C | behavior/runtime gating; D validates pathing/performance |

Open questions for A:

1. Can the existing order trigger carry a staged fallback/regroup pair without adding
   triggers/opcodes? Current code already has hold, fallback entry 0 and sector rotation.
2. Should baseline use fixed sectors (5->2, 6->3, 7->4) or keep the parity rotation?
   Fixed is easier to validate; rotation risks a sector being uncovered mid-wave.
3. Can SP1/SP3 clamping be enforced in the order trigger for survivor destinations?
   For zombie destinations/spawn radius, state clearly if the engine/WSE2 cannot enforce
   it - do not claim a spawn-safe radius without D evidence.
4. Coordinate the forward/rear build flag (`--defensive-line`) with the new staged mode;
   do not silently change the existing default without owner sign-off.

## 8. Asset/licence handoff for Agent G

- Baseline uses **existing scene props only**; no new asset, no binary, no licence change.
- If owner approves optional barricades, use only licence-cleared assets (CC0 preferred;
  CC BY with attribution) from G's catalogue, with source URL, author, licence/version,
  observation date, SHA-256 of the source download, modifications, and a
  `THIRD_PARTY_NOTICES.md`/credits entry. No native Warband/ZOMBIEEE props, no ripped or
  unattributed assets, no AI-generated asset claim without documented terms.
- Barricade assets must fit Warband/OpenBRF + collision/navmesh workflow; G supplies
  candidates and licence evidence, **not** committed binaries in this design task.
- Any added prop changes the City SCO byte identity; owner approval + D validation required.

## 9. Validation plan for Agent D (sealed, no-client)

Static (can be reproduced now): original/overlay SCO SHA-256; entry coordinates 0/1/2/3/4
and 32-40; guard-post coordinates; 323/600/270 navmesh; 201 reachable survivor faces;
distance/bearing tables in sections 2-3.

Sealed runtime observations requested (must remain **unknown** until observed):

| Measurement | Why |
| --- | --- |
| Actual survivor spawn positions from entries 0/1; whether add_visitors/native bot path produces agents | spawn mechanism is still not engine-verified |
| Actual zombie spawn entries 32-40 used per wave; whether approaches follow A/B/C or other lanes | validates the three-axis model, not just static coordinates |
| Survivor positions at posts 2/3/4; distance moved; hold duration | proves E1 deployment |
| Fallback/regroup transitions (mode global, entry 0 vs apron) | proves staged behavior |
| Stuck agents, blocked paths, collision at sandbags/barrels/band_a rows | barricade/cover safety |
| LOS/cover from posts; whether props actually block | origin proximity is not collision/LOS |
| Spawn-safety violations (zombies/orders inside SP1; camping near entries) | verifies or falsifies SP1-SP5 |
| Wave timing/performance with 1 vs 2 vs 3 active clusters | supports SP4 gating |

Acceptance boundary: this design is **static geometry + proposals only**; it does not
award a City gate, telemetry acceptance or `runtime_verified`. D's evidence must be sealed
and bounded; no game launch by E; unknown measurements stay unknown.

## 10. Risks and unknowns

- Coordinates are 2D scene-local and derived from prop origins; **collision extents, LOS and
  actual streets are unmeasured**. A prop origin can be 3+ units from the walkable face and
  still block a doorway.
- The navmesh decode gives connected faces, not movement proof; AI can fail to path even on
  connected faces.
- The three-cluster model is a static reading; wave visitors may path differently or use
  engine-spawned positions not represented by entries.
- No engine-proven spawn-protection radius; SP1-SP5 are design requirements until A/D show
  enforcement or mark them unsupported.
- Forward hold/rotation can uncover a sector; fixed sectors vs parity rotation is an open
  decision.
- Adding barricades can block zombie pathing, survivor retreat or loot props, and changes
  City SCO identity; owner approval and static/runtime revalidation required.
- The stale `docs/CITY_DEFENSE.md` guard table (pre-hardening coordinates) can mislead;
  update it to the hardened values before any build/placement work.
- No acceptance, legal clearance, redistribution right or runtime claim is made here.

## 11. Reproducible evidence

```text
python -c "from tools.scene_tactics import decode_scene, plan_city; \
  d=open('local/original-beta04/ZOMBIEEE/SceneObj/scn_tbfc_invasion_4.sco','rb').read(); \
  s=decode_scene(d); p=plan_city(d); \
  print([(o['entry'],o['position']) for o in s['objects'] if o['type']==1]); \
  print(p['guard_posts'])"
```

Expected: entries 0/1/32-40 as in section 2; guard posts 2/3/4 at the hardened coordinates
(169.423,169.376,3.191), (185.190,185.009,3.191), (146.250,183.491,3.191); 201 reachable
faces; original SCO SHA-256 as table 1. The build overlay adds exactly three objects
(226 -> 229) and preserves all original entries.

## 12. Decisions requested

1. **Owner:** approve the design direction (north E0 anchor + three-sector E1 screen +
   north fallback/regroup, no new props baseline). Choose **rear / forward / staged**;
   explicitly approve any scene prop or entry change before implementation.
2. **A:** confirm staged hold/fallback/regroup feasibility and sector assignment; state
   which spawn-protection rules the native order layer can enforce; coordinate
   `--defensive-line` behavior.
3. **G:** no assets required for baseline; if owner approves barricades, supply
   licence-cleared candidates and attribution evidence only.
4. **D:** sealed validation of the measurements in section 9; no acceptance claim before
   evidence.
5. **Docs owner:** update the stale City guard table and record the hardened coordinates.

**No map asset edits were made. No game was launched. No acceptance is claimed.**
