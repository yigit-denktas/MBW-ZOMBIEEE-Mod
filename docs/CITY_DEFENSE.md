# City defence overlay — experimental v0.1.4

This is a **source-derived, opt-in** tactical upgrade for the 2012 ZOMBIEEE Beta 0.4 *City* map. It uses a local copy of the original scene and its AI navigation mesh. It does **not** import ZOMBIEEE2 content or publish the original binary .sco.

## Concrete findings from the supplied original 0.4 scene

| Map | SCO explicit entry points | AI-mesh vertices | Faces |
| --- | ---: | ---: | ---: |
| Granny's House | 41 | 3,589 | 3,691 |
| Bridge | 41 | 118 | 98 |
| Shipyard | 41 | 3,617 | 4,107 |
| **City** | **11** | **323** | **270** |
| Abandoned Town | 40 | 3,356 | 3,337 |

In City, survivor entry points **0 and 1** are present. Invader entries **32–40** are present. Entries **2, 3 and 4** were unused. The original City file contains 226 scene objects, including 11 placed entry points. Its navmesh has 323 vertices, 600 edges and 270 faces (218 vertices in the connected component containing the nearest survivor spawn). These are verified from the supplied original, not fabricated coordinates.

### Generated City guard-post candidates

| Entry | X | Y | Z | 2D distance from survivor entry 0 |
| --- | ---: | ---: | ---: | ---: |
| **2** — Forward | 165.500 | 169.267 | 3.191 | 16.1 m |
| **3** — Right flank | 183.272 | 191.292 | 3.191 | 16.0 m |
| **4** — Left flank | 153.814 | 188.910 | 3.191 | 15.2 m |

Positions are chosen deterministically from the centroids of navmesh faces in the survivor-connected component, about 9–24 m from survivor spawn, 28+ m from the closest zombie entry and at least 10 m apart. This is a **candidate tactic**, not proof of clear lines of sight or unobstructed movement. There may be walls or props that require later edits.

## What changes in the experimental build

- A new SCO entry point 2, 3 and 4 is inserted into a **copy** of the City scene, with existing objects, original entry points and AI mesh preserved. Original 226 objects become 229, and the original 115,408-byte scene becomes 115,660 bytes.
- The original 25 compiled invasion mission triggers are preserved verbatim.
- The experimental 0.1.2 survivor spawn trigger is retained but its **group** argument changes from 0 to divisions 5/6/7 (for four allies: 5, 6, 7, 5). Zombie team and original spawn operations are untouched.
- One additional, server-only mission trigger runs after ~5 seconds. It first checks that the **current scene is City**, obtains the position of each new entry point, and issues **hold** orders to the three survivor divisions using native opcodes.
- Mission trigger count becomes **27** (25 original + one survivor spawn + one tactical order). Normal/no-allies build remains 25; allies without City tactics remain 26.

Warband operations used: `store_current_scene` 2211, `entry_point_get_position` 1780, `team_set_order_position` 1791, `team_give_order` 1790 (movement `mordr_hold=0`). Scene parsing follows the published .SCO data structure. No WSE2-specific injection is required for the tactical commands.

## Build locally (Windows)

From the repository root, with the legally obtained original archive and WSE2 installed:

```powershell
py -3 tools\build.py --archive "C:\Downloads\ZOMBIEEEBeta04.rar" --out "C:\Games\MountBlade Warband\Modules\ZOMBIEEE_Remaster" --experimental-defenders 4 --city-guardposts
```

To inspect the scene blueprint without changing files:

```powershell
py -3 tools\scene_tactics.py --scene "C:\path\to\extracted\ZOMBIEEE\SceneObj\scn_tbfc_invasion_4.sco"
```

No flag means **no modification** to the original mission or City scene (only the existing Lua diagnostic overlay). `--experimental-defenders 4` alone creates the 26-trigger allies-only variant. `--experimental-defenders 4 --city-guardposts` produces the 27-trigger City tactical variant. `--city-guardposts` without allies is rejected.

## Verification status and risks

**Offline integration passed** with the actual uploaded original 0.4: five scenes decoded, City AI navmesh parsed, three reachable post centroids selected, .SCO round-trip preserved the original navmesh, original invasion triggers remained unchanged, new 27-trigger mission parsed, and patch reapplication was rejected.

**NOT YET VERIFIED IN ENGINE:** WSE2 launch, whether visitors spawn as assigned, whether group 5/6/7 hold orders work, lines of sight, local obstacle collisions, firearms behavior, performance, multiplayer replication and zombie wave completion. These belong in the final one-time Windows evidence session, not repeated user tests.

Sources: [Warband SCO binary format](https://mbmodwiki.github.io/SceneObj), [Warband operation definitions](https://github.com/Veehats/WarbandCoop/blob/main/header_operations.py), [Warband mission order constants](https://github.com/CaueVaranda/Warband-Module-System/blob/main/header_mission_templates.py).

The three new marker positions are a staging point for later interactive defend/rally/fallback commands and respawn waves, not the finished AI system. Original creators retain full credit and original assets remain outside Git.
