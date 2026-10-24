# AI movement heatmaps + spatial analysis - initial sample (issue #54)

**Status:** initial reusable tool + sample outputs. **No game launch; no visual or acceptance
claim.** Panels are descriptive occupancy/flow renderings with sparse samples; they are
not validated in-engine and are not a tactical/behavioral conclusion. Task-71 input
tooling is C's branch; this report is the E consumer side.

- **Tool:** `telemetry/spatial_analysis.py` (standard library; read-only).
- **Inputs:** sealed ZDB1 bundles (canonical `tools.receipt_summary` parser) and/or C's
  `zombieee.heatmap-input.v1` export
  (`agent/c-heatmap-input` @ `721b655`, `python -m tools.telemetry_studio heatmap-export
  <bundle> --out points.json`).
- **Sample data:** task45-wave2 (waves 0-4) and task55-p0; C export test on task45.
  Build/probe SHA, formation mode, seed and spectator status are **unknown** in these
  evidence bundles; health/class/division are absent until D seals a newer probe.

## 1. Run inventory and gaps

| Run | Source | Points | Heartbeats | Agents | Waves | Health | Class | Division |
| --- | --- | ---: | ---: | ---: | --- | --- | --- | --- |
| `d7bfc372` (task45-wave2) | C export | 692 | 42 | 53 | 0-4 | missing | missing | missing |
| `d7bfc372` (task45-wave2) | raw bundle | 526 | 42 | 47 | 0-4 | missing | missing | unknown |
| `257b29b1` (task55-p0) | raw bundle | 572 | 41 | 45 | 0-1 | missing | missing | unknown |

Common gaps (carried into every run row): no build/probe SHA, formation mode, seed or
spectator/overview flag; no health/HP, class or valid division in current bundles; sparse
15 s sample cadence (not per-frame); no collision/navmesh/oracle; no exact round-end
identity. `run_metadata_partial`, `missing_class`, `missing_division`, `missing_health`,
`no_ts_ms_probe_relative` are explicit where C's exporter reports them.

## 2. Method

- Fixed City analysis window **x 90-220, y 100-205**, **5-unit occupancy cells**.
  Occupancy is sample-share per team; flow is the mean displacement of the same agent
  between consecutive samples in the destination cell. This is a **sample flow**, not
  engine velocity.
- Conditions are joined from heartbeats: `fallback` if tactical `mode=1`, else
  `outnumbered` when alive-team0/alive-team1 < 0.75, `advantage` when > 1.25, `even`
  otherwise, `unknown` when counts are unavailable. `wave_transition` is flagged at the
  first sample of a non-zero wave. Condition labels are descriptive, not causal.
- Hold posts: **2=(169.423,169.376), 3=(185.190,185.009), 4=(146.250,183.491)**; north
  anchor **E0=(167.718,184.445)**, entries 0/1 as in
  [`reference/CITY_MAP_DEFENSE_DESIGN.md`](../reference/CITY_MAP_DEFENSE_DESIGN.md). These
  are static scene coordinates; no collision or navmesh check is implied.
- Cohesion: per tick, centroid, spread RMS, mean nearest-neighbour distance and pairwise
  mean. Agent movement: path length, net displacement, path efficiency, stationary
  ratio, northward displacement, post/anchor proximity. `under_moving` = <2 units path or
  >80% stationary steps; `over_moving` = >=10 units path with path efficiency <0.25;
  otherwise `mixed`; these are **proxies**.
- Candidate chokepoints: cells with >=3 samples, >=5% occupancy and <=15% moving steps.
  They are positional candidates only: no collision, blockers, LOS or pathfinding truth.
- **No health/morale measurement** exists in this sample. Morale/routing is not claimed;
  the report only exposes northward/fallback movement and cohesion proxies for A/D to
  interpret.

## 3. Initial observations (bounded)

- **Conditions are dominated by outnumbered windows** in these samples:
  task45 C export = 375 outnumbered / 198 even / 80 advantage / 39 unknown; task55 raw =
  388 outnumbered / 151 even / 33 unknown. No fallback-condition samples appear in these
  two bundles (mode/conditions sparse).
- **Task45 team-0 occupied the north/anchor area early, then sampled survivors drift
  east/south:** wave 0 centroid (165.2,178.6), spread 4.0, near-anchor share 0.79; wave 1
  centroid (181.6,180.8), spread 0.64, anchor share 0.11; wave 2 centroid (192.0,186.9),
  anchor share 0.0. This is a **survivor-sample** pattern after heavy attrition, not proof
  of a successful hold or of a specific post. Post 3 is the nearest post to the later
  centroid, but sparse agents and missing division/role data prevent a hold/role claim.
- **Team-1 stayed on the southern approaches:** wave 0 centroid (137.6,139.6), spread
  21.4; wave 1 (161.9,155.5), spread 13.5. This is consistent with the SW/S/SSE entry
  clusters and **not** a 360-degree encirclement. No north-side zombie entry is observed.
- **Movement class proxy:** 64 mixed, 24 over-moving, 4 under-moving across 92 sampled
  agents; team-1 accounts for 17 over-moving and team-0 for 7; all 4 under-moving are
  team-0. This is expected to be confounded by role, alive/dead sampling and target
  availability; no causal/tactical rank follows.
- **Chokepoint candidate:** task55 team-0 cell at (167.5,187.5), 15.9% occupancy, moving
  ratio 0.111. This is at the north base/apron, so it is more likely a spawn/base dwell
  cluster than a scene blocker; no collision/navmesh evidence exists.
- **Panels:** `telemetry/spatial_sample/panels/*.svg` (raw two runs) and
  `telemetry/spatial_sample_c/panels/*.svg` (C export). They are descriptive only.

### 3.1 A behavior interpretation (independent, branch `agent/a-heatmap-interpretation` @ `6408595`)

A's read-only interpretation (`reference/HEATMAP_BEHAVIOR_INTERPRETATION_2026-10-24.md`,
ready to merge) agrees with the bounded reading: early base/anchor dwell is **not** proof of
a hold; post-wave drift is attrition/survivorship-dominated; **no fallback condition and
no role/class separation** are observed; team-1 remains southern; the chokepoint candidate
is most likely spawn/base dwell. A's required gates (known build SHA, formation mode/seed,
class/division/HP/round, a real fallback window, A-reviewed spectator visuals) are
consistent with this report's section 6.

A applied the two corrections in `6408595`:

1. **Wave-2 mean alive is 8.0**, not "fewer" after the wave-1 low of 2.33 — later samples
   include respawns/new agents (wave 3 = 4.0, wave 4 = 6.0). The drift remains
   survivorship/combat displacement, but it is not a monotonic alive decline.
2. **Dataset counts are labelled:** raw task45 = 308 outnumbered / 526 points; C export of
   the same run = 375 / 692 points; task55 raw = 388 / 572 points. Cohesion now reads
   "sample composition, not an ordered formation"; counts are not mixed.

## 4. Outputs

- `telemetry/spatial_sample/` - raw-bundle sample (2 runs):
  `spatial_runs.csv`, `spatial_cells.csv` (518 rows), `spatial_agents.csv` (92 rows),
  `spatial_cohesion.csv` (44 rows), `spatial_chokepoints.csv`, `spatial_summary.json`,
  `panels/*.svg`.
- `telemetry/spatial_sample_c/` - C-export sample (task45, 692 points, 53 agents):
  same table set + SVG panel.
- The tool also accepts any sealed bundle path; C's export is optional.

## 5. Methods literature / community analogues reused

- Occupancy-grid representation and heatmap aggregation: standard robotics/game-AI
  occupancy-grid concept ([overview](https://en.wikipedia.org/wiki/Occupancy_grid_mapping));
  no new geometry engine was written.
- Flow-field/path-field idea for movement visualization, as used by community AI projects
  ([NativeFlowField](https://github.com/kingstone426/NativeFlowField)); we use a sampled
  displacement field, not a generated path field.
- Nearest-neighbour / point-pattern clustering principles for cohesion proxies
  ([SAS point-pattern overview](http://support.sas.com/resources/papers/proceedings15/SAS1332-2015.pdf)).
- Warband community formation/order analogue: Motomataru FormAI constants
  ([formAI_constants.py](https://raw.githubusercontent.com/cvlc/tgsmod/master/formAI_constants.py));
  project records [`reference/WARBAND_AI_COMMUNITY_SOURCES.md`](../reference/WARBAND_AI_COMMUNITY_SOURCES.md).
- Reused existing project pieces: canonical parser `tools/receipt_summary.py`;
  `tools/tactical_analysis.py` R019/R022 conservative movement checks;
  `tools/scene_tactics.py`/`reference/CITY_GUARD_HARDENING_2026-10-24.md` for post
  coordinates; no duplicate parser or map asset reads.

## 6. Gaps / next tasks

1. **Health/HP, class_id, division** are absent in current bundles. C's branch adds
   `store_agent_hit_points` 1720, `agent_get_class` 1772, `agent_get_division` 1773;
   D must seal a post-`721b655` run with those fields before health/morale/role analysis.
2. **Build/probe SHA, formation mode, seed, spectator/overview status** are missing from
   the evidence bundles; A/D must supply them for interpretable panels.
3. **Sparse sampling** (ai_sample cadence, 8-16 points/heartbeat) limits per-agent paths;
   no per-frame trajectories or true speed/threat inference.
4. **No collision/navmesh/LOS**; chokepoint/blocker claims are candidates only.
5. **No exact round-end/round identity**; condition/wave joins rely on heartbeat counts.
6. **No visual validation**; SVG panels are descriptive and must not be read as accepted
   visual behavior. D's heatmap-bearing run and A's behavior interpretation are pending.

## 7. Reproduction

```text
# raw sealed bundles
python telemetry/spatial_analysis.py \
  --bundle <sealed-run-1> --bundle <sealed-run-2> \
  --out telemetry/spatial_sample --panels

# C heatmap export input
python -m tools.telemetry_studio heatmap-export <sealed-run> --out points.json
python telemetry/spatial_analysis.py --input points.json \
  --out telemetry/spatial_sample_c --panels
```

No acceptance, legal clearance, visual validation or causal claim is made. Coordinate C
(input fields), D (sealed heatmap-bearing run), A (behavior interpretation). Issue #54 /
ledger `ZOM-DISC-74` remains open.
