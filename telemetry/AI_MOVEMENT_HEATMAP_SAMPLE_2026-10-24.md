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

| Run | Source | Points | Heartbeats | Unique IDs | Team tracks | Waves | Health | Class | Division |
| --- | --- | ---: | ---: | ---: | ---: | --- | --- | --- | --- |
| `task76-heatmap-hit` | C export + meta | **229** | **14** | **20** | **28** | 0-1 | **present (sampled)** | **present** | **present** |
| `d7bfc372` (task45-wave2) | C export | 692 | 42 | 31 | 53 | 0-4 | missing | missing | missing |
| `d7bfc372` (task45-wave2) | raw bundle | 526 | 42 | 30 | 47 | 0-4 | missing | missing | unknown |
| `257b29b1` (task55-p0) | raw bundle | 572 | 41 | 28 | 45 | 0-1 | missing | missing | unknown |

**ID accounting:** agent ids are reused across teams/rounds. **Unique IDs** match C's
`agents{}` count (31 for the C export); **team tracks** group by `(team, agent_id)` so
movement metrics do not merge cross-team teleports. Both are reported; do not compare
"agents" counts without saying which one.

Older bundles (task45/task55) lack build/probe SHA, formation mode, seed or
spectator/overview flag, and health/HP/class/valid division. **task76** carries
mission/scripts SHA, probe head/reported SHA, map/template, survivor-idle perspective,
8/8 bot config, frames count and probe-health ok — but still has **no formation_mode,
seed, entry ids or round-end**, and only wave 1. All samples are sparse 15 s cadence, no
collision/navmesh/oracle. `run_metadata_partial`, `missing_class`, `missing_division`,
`missing_health`, `no_ts_ms_probe_relative` are explicit where C's exporter reports them.

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
  otherwise `mixed`; these are **proxies** over team-incarnation tracks, not unique agents.
  Agent ids reused across teams would otherwise create false long paths/teleports.
- Candidate chokepoints: cells with >=3 samples, >=5% occupancy and <=15% moving steps.
  They are positional candidates only: no collision, blockers, LOS or pathfinding truth.
- **No health/morale measurement** exists in this sample. Morale/routing is not claimed;
  the report only exposes northward/fallback movement and cohesion proxies for A/D to
  interpret.

### 2.1 Pre-analysis gate: `probe-health`

Run C's gate (`agent/c-probe-doctor` @ `c7d58a0` or later) before `heatmap-export` or
this tool:

```text
python -m tools.telemetry_studio probe-health <sealed-bundle> --json
```

| Bundle | Status | Heartbeat | Key checks/gaps |
| --- | --- | --- | --- |
| task45-wave2 | **warn** (`ok=true`) | 42 | hit counters absent (old probe); `SCRIPT ERROR x4` |
| task55-p0 | **warn** (`ok=true`) | 41 | hit counters absent; no critical error family |
| **task76-heatmap-hit** | **ok** | **14** | adaptive active; hit 0 attempts/296 (broken, not heatmap blocker); no critical errors |
| D partial pre-round | **fail** (`ok=false`) | 0 | `no_heartbeat_events`; trigger registered but heartbeat path not emitting |

Gate rule: **zero heartbeats ⇒ stop, do not treat as heatmap evidence**. Warnings
(old-probe hit counters, script errors) are recorded and must be carried into the run
gaps; a `fail` is never converted into a pass by this analysis.

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
- **Movement class proxy:** 64 mixed, 24 over-moving, 4 under-moving across **92 team
  tracks** (58 unique IDs in the two raw runs; C export = 31 unique / 53 tracks); team-1
  accounts for 17 over-moving and team-0 for 7; all 4 under-moving are team-0. This is
  expected to be confounded by role, alive/dead sampling and target availability; no
  causal/tactical rank follows. Counts are track-level, not unique-agent-level.
- **Chokepoint candidate:** task55 team-0 cell at (167.5,187.5), 15.9% occupancy, moving
  ratio 0.111. This is at the north base/apron, so it is more likely a spawn/base dwell
  cluster than a scene blocker; no collision/navmesh evidence exists.
- **Panels:** `telemetry/spatial_sample/panels/*.svg` (raw two runs) and
  `telemetry/spatial_sample_c/panels/*.svg` (C export). They are descriptive only.

### 3.1 A behavior interpretation (independent, branch `agent/a-heatmap-interpretation` @ `ca9a357`)

A's read-only interpretation (`reference/HEATMAP_BEHAVIOR_INTERPRETATION_2026-10-24.md`,
ready to merge) agrees with the bounded reading: early base/anchor dwell is **not** proof of
a hold; post-wave drift is attrition/survivorship-dominated; **no fallback condition and
no role/class separation** are observed; team-1 remains southern; the chokepoint candidate
is most likely spawn/base dwell. A's required gates (known build SHA, formation mode/seed,
class/division/HP/round, a real fallback window, A-reviewed spectator visuals) are
consistent with this report's section 6.

A applied the two corrections in `6408595` and clarified the unique-ID/track distinction
in `ca9a357` (task45 C export 31 unique / 53 tracks; raw task45 30/47; raw task55 28/45;
movement classes are track-level):

1. **Wave-2 mean alive is 8.0**, not "fewer" after the wave-1 low of 2.33 — later samples
   include respawns/new agents (wave 3 = 4.0, wave 4 = 6.0). The drift remains
   survivorship/combat displacement, but it is not a monotonic alive decline.
2. **Dataset counts are labelled:** raw task45 = 308 outnumbered / 526 points; C export of
   the same run = 375 / 692 points; task55 raw = 388 / 572 points. Cohesion now reads
   "sample composition, not an ordered formation"; counts are not mixed.

### 3.2 Pipeline check on D's partial pre-round bundle (not evidence)

D supplied a sealed partial (`heatmap-preround-171455.json`): **56 points, 0 heartbeats,
8 unique IDs**, ticks 0-6, `health/class/division` present in some points, all conditions
`unknown`, gaps `run_metadata_partial`. **`probe-health` = fail
(`no_heartbeat_events`)**; our tool still renders it without error
(`telemetry/spatial_partial/`), confirming the C schema/consumer path. This is **not
heatmap evidence**: no round, waves, fallback, mode, build/probe SHA, formation, sample
interval or spectator metadata; D was blocked by the `hit_param_invalid` nil error in the
installed probe. The later task76 run below is the first heartbeat-bearing baseline.

### 3.3 task76 full baseline (heartbeat-bearing; not A/B)

D's sealed task76 bundle passes `probe-health` (**ok**, 14 heartbeats, adaptive active, no
critical errors) and exports **229 points / 14 heartbeats / 20 unique IDs / 28 team
tracks**, waves 0-1, class+division+HP sampled for all 28 tracks, conditions **160
outnumbered / 61 even / 8 unknown**, no fallback condition.

Run metadata (from `heatmap_run_metadata_task76.json`, sanitized into
`spatial_task76/spatial_summary.json`): mission SHA `df21ae88…`, scripts SHA `b6a7cdde…`,
probe head `bf39a37` / reported `78AB1AE8`, map `tbfc_invasion_4`, template
`mst_multiplayer_iv`, fixed 15 s sampling, survivor-idle perspective, team 8/8, 31 frames.
Missing: **formation_mode, seed, entry ids, round-ended event**; `runtime_verified=false`;
screenshots are faction-screen only (join clicks flaky) — **no usable visual frames**.

Bounded observations (descriptive only):

- team-0 wave 0 centroid (165.35,176.81), spread 6.81, mean alive 3.75, anchor share
  0.667; wave 1 (166.33,152.62), spread 7.14, mean alive 2.55, anchor share 0.0.
- team-1 wave 0 centroid (157.49,128.08), spread 27.25; wave 1 (164.87,151.99), spread
  11.32. Both teams remain south of the north anchor in the sampled wave-1 window; this is
  **not** a fallback validation (no fallback condition/round-end).
- Movement proxy: 21 mixed / 7 over-moving / 0 under-moving across 28 tracks; no candidate
  chokepoint cell survives the threshold. Class/division values are 0/1 only and D marks
  them **source-troop-fallback**, not verified role identities.
- Hit attribution: **hit_events=0 / attempts=296**, params invalid — heatmap input is
  unaffected, but this run does **not** validate hit attribution.

Panels: `telemetry/spatial_task76/panels/spatial_panel_task76-heatmap-hit.svg`. This is a
single baseline sample, **not** a baseline-vs-variant result; no visual/acceptance claim.

## 4. Outputs

- `telemetry/spatial_sample/` - raw-bundle sample (2 runs):
  `spatial_runs.csv`, `spatial_cells.csv` (518 rows), `spatial_agents.csv` (92 rows),
  `spatial_cohesion.csv` (44 rows), `spatial_chokepoints.csv`, `spatial_summary.json`,
  `panels/*.svg`.
- `telemetry/spatial_sample_c/` - C-export sample (task45, 692 points, **31 unique IDs /
  53 team tracks**): same table set + SVG panel.
- `telemetry/spatial_partial/` - D partial pre-round renderer check (56 points, 0
  heartbeats; **not** behavior evidence).
- `telemetry/spatial_task76/` - first heartbeat-bearing baseline (229 points, 14
  heartbeats, 20 unique IDs / 28 tracks, class/HP/division sampled; wave 1 max; no A/B).
- The tool also accepts any sealed bundle path; C's export is optional; `--meta` accepts
  D's `zombieee.heatmap-run-metadata.v1` JSON.

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
  --meta <heatmap-run-metadata.json> \
  --out telemetry/spatial_sample_c --panels
```

No acceptance, legal clearance, visual validation or causal claim is made. Coordinate C
(input fields), D (sealed heatmap-bearing run), A (behavior interpretation). Issue #54 /
ledger `ZOM-DISC-74` remains open.
