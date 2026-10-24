#!/usr/bin/env python3
"""Reusable 2D AI movement/spatial analysis for sealed ZDB1 bundles.

Read-only, standard-library only. Ingests sealed recorder directories (or a
C-exported `zombieee.heatmap-input.v1` JSON dict) and emits:

* run metadata/coverage/gaps;
* per-cell occupancy + flow heatmap rows (team x wave x condition);
* per-agent movement/cohesion/routing proxy rows;
* per-team/wave/condition cohesion summaries;
* candidate chokepoint cells (positional proxy only, no collision/navmesh);
* optional SVG panels (descriptive only, not a visual/acceptance claim).

`tick` is the primary sequence; `ts_ms` is probe-relative only (never UTC).
Missing health/class/division/build/probe/seed/spectator fields stay explicit
gaps, not zeros.

Pre-analysis gate: run C's `probe-health <bundle> --json`
(`agent/c-probe-doctor` @ c7d58a0 or later) before this tool. It catches
registered-but-zero-heartbeat / missing-counter bundles that still export
points; this tool does not duplicate that check and will happily render a
non-evidence partial unless the caller gates it.
"""
from __future__ import annotations

import argparse
import csv
import json
import math
import sys
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from tools.receipt_summary import parse_zdbi, resolve_receipt_root, verify_manifest  # noqa: E402

SCHEMA = "zombieee.heatmap-analysis.v1"
INPUT_SCHEMA = "zombieee.heatmap-input.v1"
CITY_BOUNDS = (90.0, 220.0, 100.0, 205.0)  # x0,x1,y0,y1; fixed City analysis window
CELL = 5.0
POSTS = {2: (169.423, 169.376), 3: (185.190, 185.009), 4: (146.250, 183.491)}
ANCHOR = (167.718, 184.445)
ENTRIES = {"entry0": (168.528, 185.107), "entry1": (166.909, 183.782)}
CONDITIONS = ("all", "outnumbered", "advantage", "fallback", "even", "unknown")


def _num(value, default=None):
    try:
        fx = float(value)
    except (TypeError, ValueError):
        return default
    return fx if math.isfinite(fx) else default


def _int(value, default=None):
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def _bool(value):
    if value in (True, 1, "1", "true", "True"):
        return True
    if value in (False, 0, "0", "false", "False"):
        return False
    return None


def _dist(a, b):
    return math.hypot(a[0] - b[0], a[1] - b[1])


def _read_bundle(bundle: Path):
    root = resolve_receipt_root(bundle)
    info = verify_manifest(root)
    texts = []
    for name in info["members"]:
        if name.lower().endswith((".log", ".txt", ".jsonl", ".out")):
            texts.append((root / name).read_text(encoding="utf-8", errors="replace"))
    events = []
    for text in texts:
        events.extend(parse_zdbi(text))
    meta = json.loads((root / "recorder.json").read_text(encoding="utf-8"))
    return root, events, meta


def _load_input(path: Path):
    data = json.loads(path.read_text(encoding="utf-8"))
    if data.get("schema") != INPUT_SCHEMA:
        raise SystemExit("input schema must be " + INPUT_SCHEMA)
    points = []
    for p in data.get("points", []):
        points.append({
            "tick": _int(p.get("tick"), 0),
            "ts_ms": _num(p.get("ts_ms")),
            "agent_id": _int(p.get("agent_id"), -1),
            "team": _int(p.get("team"), -1),
            "troop": _int(p.get("troop")),
            "class_id": _int(p.get("class_id")),
            "division": _int(p.get("division")),
            "x": _num(p.get("x")), "y": _num(p.get("y")),
            "alive": _bool(p.get("alive")),
            "hp": _num(p.get("hp")),
            "wave": _int(p.get("wave"), -1),
            "round": _int(p.get("round"), -1),
            "mode": _int(p.get("mode"), -1),
        })
    heartbeats = []
    for h in data.get("heartbeats", []):
        heartbeats.append({
            "tick": _int(h.get("tick"), 0), "ts_ms": _num(h.get("ts_ms")),
            "wave": _int(h.get("wave"), -1), "round": _int(h.get("round"), -1),
            "mode": _int(h.get("mode"), -1),
            "team0": _int(h.get("team0")), "team1": _int(h.get("team1")),
            "alive0": _int(h.get("alive0")), "alive1": _int(h.get("alive1")),
        })
    # C's exporter carries canonical per-agent metadata even when some point
    # fields are null; fill the point fields from it where possible.
    agent_meta = data.get("agents") or {}
    for p in points:
        meta = agent_meta.get(str(p["agent_id"])) or agent_meta.get(p["agent_id"]) or {}
        if p["team"] not in (0, 1):
            p["team"] = _int(meta.get("team"), -1)
        for key, alt in (("troop", None), ("class_id", "class_id"), ("division", "division")):
            if p[key] is None:
                p[key] = _int(meta.get(key if alt is None else alt))
        if p["hp"] is None:
            p["hp"] = _num(meta.get("hp") if meta.get("hp") is not None else meta.get("last_hp"))
    return data.get("run", {}), points, heartbeats, list(data.get("gaps", []))


def _events_to_data(events, meta):
    points, heartbeats, seen = [], [], set()
    for ev in events:
        typ = ev["event"]
        f = ev["fields"]
        if typ in ("ai_sample", "agent_sample", "combat_sample"):
            x, y = _num(f.get("x")), _num(f.get("y"))
            tick = _int(f.get("tick"))
            aid = _int(f.get("id"))
            if x is None or y is None or tick is None or aid is None:
                continue
            key = (tick, aid)
            if key in seen:
                continue
            seen.add(key)
            div_raw = _int(f.get("division"))
            if div_raw is None:
                div_raw = _int(f.get("group"))
            if div_raw is not None and div_raw < 0:
                div_raw = None
            cls_raw = _int(f.get("class_id"))
            if cls_raw is not None and cls_raw < 0:
                cls_raw = None
            points.append({
                "tick": tick, "ts_ms": _num(f.get("ts_ms")),
                "agent_id": aid, "team": _int(f.get("team"), -1),
                "troop": _int(f.get("troop")), "class_id": cls_raw,
                "division": div_raw,
                "x": x, "y": y, "alive": _bool(f.get("alive")),
                "hp": _num(f.get("hp") or f.get("health")),
                "wave": _int(f.get("wave"), -1), "round": _int(f.get("round"), -1),
                "mode": _int(f.get("mode"), -1),
            })
        elif typ == "heartbeat":
            # ZDB1 heartbeats carry `count` (1-based sample), not `tick`.
            tick = _int(f.get("tick"))
            if tick is None:
                tick = _int(f.get("count"))
            if tick is None:
                continue
            heartbeats.append({
                "tick": tick, "ts_ms": _num(f.get("ts_ms")),
                "wave": _int(f.get("wave"), -1), "round": _int(f.get("round"), -1),
                "mode": _int(f.get("mode"), -1),
                "team0": _int(f.get("team0")), "team1": _int(f.get("team1")),
                "alive0": _int(f.get("alive_team0")), "alive1": _int(f.get("alive_team1")),
            })
    run = {
        "run_id": meta.get("session_id") or "", "build_sha": None, "probe_sha": None,
        "formation_mode": None, "map": "tbfc_invasion_4",
        "entry_ids": [0, 1, 2, 3, 4], "seed": None,
        "sample_interval_s": None, "spectator_or_overview": None,
    }
    cap = next((e["fields"] for e in events if e["event"] == "recorder_capabilities"), {})
    run["sample_interval_s"] = _num(cap.get("sampling_interval_s"))
    return run, points, heartbeats, []


def _condition_for(point, hb):
    if hb is None:
        return "unknown"
    if hb.get("mode") == 1:
        return "fallback"
    a0, a1 = hb.get("alive0"), hb.get("alive1")
    if a0 is None or a1 is None or a0 < 0 or a1 < 0:
        return "unknown"
    if a0 == 0 or a1 == 0:
        return "unknown"
    ratio = (a0 + 0.5) / (a1 + 0.5)
    if ratio < 0.75:
        return "outnumbered"
    if ratio > 1.25:
        return "advantage"
    return "even"


def _hb_at(tick, heartbeats):
    candidates = [h for h in heartbeats if h["tick"] <= tick]
    return max(candidates, key=lambda h: h["tick"]) if candidates else None


def _annotate(points, heartbeats):
    hbs = sorted(heartbeats, key=lambda h: h["tick"])
    first_tick_by_wave = {}
    for p in sorted(points, key=lambda p: p["tick"]):
        first_tick_by_wave.setdefault(p["wave"], p["tick"])
    prev_wave_by_agent = {}
    for p in sorted(points, key=lambda p: (p["agent_id"], p["tick"])):
        hb = _hb_at(p["tick"], hbs)
        p["condition"] = _condition_for(p, hb)
        p["hb_wave"] = hb.get("wave") if hb else None
        p["hb_round"] = hb.get("round") if hb else None
        p["hb_mode"] = hb.get("mode") if hb else None
        p["wave_transition"] = bool(
            hb is not None and p["wave"] in first_tick_by_wave
            and p["tick"] == first_tick_by_wave[p["wave"]]
            and p["wave"] not in (0, -1)
        )
        p["near_posts"] = {str(k): _dist((p["x"], p["y"]), v) <= 5.0 for k, v in POSTS.items()}
        p["near_anchor"] = _dist((p["x"], p["y"]), ANCHOR) <= 10.0
        p["near_entries"] = {k: _dist((p["x"], p["y"]), v) <= 8.0 for k, v in ENTRIES.items()}
    return points


def _cell(point, bounds, cell):
    x0, x1, y0, y1 = bounds
    gx = int((point["x"] - x0) // cell)
    gy = int((point["y"] - y0) // cell)
    nx = int(math.ceil((x1 - x0) / cell))
    ny = int(math.ceil((y1 - y0) / cell))
    if 0 <= gx < nx and 0 <= gy < ny:
        return gx, gy
    return None


def _analyze(run, points, heartbeats, gaps, bounds=CITY_BOUNDS, cell=CELL):
    points = _annotate(points, heartbeats)
    by_team = defaultdict(list)
    for p in points:
        if p["team"] in (0, 1):
            by_team[p["team"]].append(p)
    # occupancy/flow by team x condition (including all)
    cells = {}
    for team, pts in by_team.items():
        for condition in CONDITIONS:
            selected = [p for p in pts if condition == "all" or p["condition"] == condition]
            if not selected:
                continue
            buckets = defaultdict(list)
            for p in selected:
                c = _cell(p, bounds, cell)
                if c:
                    buckets[c].append(p)
            # flow from consecutive samples per agent
            by_agent = defaultdict(list)
            for p in pts:
                by_agent[p["agent_id"]].append(p)
            flow = defaultdict(list)
            steps = defaultdict(list)
            for agent_pts in by_agent.values():
                agent_pts.sort(key=lambda p: p["tick"])
                for a, b in zip(agent_pts, agent_pts[1:]):
                    if condition != "all" and b["condition"] != condition:
                        continue
                    c = _cell(b, bounds, cell)
                    if not c:
                        continue
                    dx, dy = b["x"] - a["x"], b["y"] - a["y"]
                    flow[c].append((dx, dy))
                    steps[c].append(math.hypot(dx, dy))
            for c, bucket in buckets.items():
                vecs = flow.get(c, [])
                mags = steps.get(c, [])
                cells[(team, condition, c)] = {
                    "team": team, "condition": condition,
                    "gx": c[0], "gy": c[1],
                    "x": bounds[0] + (c[0] + 0.5) * cell,
                    "y": bounds[2] + (c[1] + 0.5) * cell,
                    "count": len(bucket),
                    "share": len(bucket) / max(1, len(selected)),
                    "moving_ratio": (sum(1 for m in mags if m > 0.2) / len(mags)) if mags else None,
                    "flow_dx": (sum(v[0] for v in vecs) / len(vecs)) if vecs else None,
                    "flow_dy": (sum(v[1] for v in vecs) / len(vecs)) if vecs else None,
                    "mean_step": (sum(mags) / len(mags)) if mags else None,
                }
    # agent metrics: team-incarnation tracks (agent ids are reused across teams/
    # rounds, so unique-id movement would merge teleports); unique ids counted
    # separately in the run summary.
    agents = []
    agent_groups = defaultdict(list)
    for p in points:
        if p["team"] in (0, 1) and p["agent_id"] >= 0:
            agent_groups[(p["team"], p["agent_id"])].append(p)
    for (team, aid), pts in sorted(agent_groups.items()):
        pts.sort(key=lambda p: p["tick"])
        teams_seen = [team]
        path = sum(_dist((a["x"], a["y"]), (b["x"], b["y"])) for a, b in zip(pts, pts[1:]))
        net = _dist((pts[0]["x"], pts[0]["y"]), (pts[-1]["x"], pts[-1]["y"]))
        steps = [_dist((a["x"], a["y"]), (b["x"], b["y"])) for a, b in zip(pts, pts[1:])]
        stationary = sum(1 for s in steps if s < 0.5) / len(steps) if steps else None
        eff = (net / path) if path > 0 else None
        under = len(pts) >= 2 and (path < 2.0 or (stationary is not None and stationary > 0.8))
        over = len(pts) >= 2 and path >= 10.0 and (eff is not None and eff < 0.25)
        near_posts = {k: sum(1 for p in pts if p["near_posts"][str(k)]) / len(pts) for k in POSTS}
        agents.append({
            "team": team, "agent_id": aid, "teams_seen": json.dumps(teams_seen),
            "troop": next((p["troop"] for p in pts if p["troop"] is not None), None),
            "class_id": next((p["class_id"] for p in pts if p["class_id"] is not None), None),
            "division": next((p["division"] for p in pts if p["division"] is not None), None),
            "samples": len(pts), "first_tick": pts[0]["tick"], "last_tick": pts[-1]["tick"],
            "first_wave": pts[0]["wave"], "last_wave": pts[-1]["wave"],
            "path_length": round(path, 2), "net_displacement": round(net, 2),
            "path_efficiency": round(eff, 3) if eff is not None else None,
            "stationary_ratio": round(stationary, 3) if stationary is not None else None,
            "mean_step": round(sum(steps) / len(steps), 3) if steps else None,
            "net_dy": round(pts[-1]["y"] - pts[0]["y"], 2),
            "movement_class": "under_moving" if under else ("over_moving" if over else "mixed"),
            "near_posts": json.dumps(near_posts), "near_anchor_share": round(sum(1 for p in pts if p["near_anchor"]) / len(pts), 3),
            "health_sampled": any(p["hp"] is not None for p in pts),
            "last_hp": next((p["hp"] for p in reversed(pts) if p["hp"] is not None), None),
            "last_alive": next((p["alive"] for p in reversed(pts) if p["alive"] is not None), None),
            "conditions": json.dumps(dict(Counter(p["condition"] for p in pts))),
        })
    # cohesion
    cohesion = []
    for team in (0, 1):
        for wave in sorted({p["wave"] for p in points if p["team"] == team}):
            for condition in ("all",) + tuple(c for c in CONDITIONS[1:]):
                selected = [p for p in points if p["team"] == team and p["wave"] == wave
                            and (condition == "all" or p["condition"] == condition)]
                if not selected:
                    continue
                ticks = defaultdict(list)
                for p in selected:
                    ticks[p["tick"]].append(p)
                spreads, nns, pairs, counts = [], [], [], []
                for tick, pts in ticks.items():
                    cx = sum(p["x"] for p in pts) / len(pts)
                    cy = sum(p["y"] for p in pts) / len(pts)
                    spreads.append(math.sqrt(sum((p["x"] - cx) ** 2 + (p["y"] - cy) ** 2 for p in pts) / len(pts)))
                    counts.append(len(pts))
                    if len(pts) > 1:
                        nns.append(sum(min(_dist((p["x"], p["y"]), (q["x"], q["y"]))
                                           for q in pts if q is not p) for p in pts) / len(pts))
                        pairs.append(sum(_dist((a["x"], a["y"]), (b["x"], b["y"]))
                                         for i, a in enumerate(pts) for b in pts[i + 1:])
                                     / (len(pts) * (len(pts) - 1) / 2))
                cohesion.append({
                    "team": team, "wave": wave, "condition": condition,
                    "ticks": len(ticks), "samples": len(selected),
                    "mean_alive": round(sum(counts) / len(counts), 2),
                    "centroid_x": round(sum(p["x"] for p in selected) / len(selected), 2),
                    "centroid_y": round(sum(p["y"] for p in selected) / len(selected), 2),
                    "spread_rms_mean": round(sum(spreads) / len(spreads), 3),
                    "nearest_neighbor_mean": round(sum(nns) / len(nns), 3) if nns else None,
                    "pairwise_mean": round(sum(pairs) / len(pairs), 3) if pairs else None,
                    "near_anchor_share": round(sum(1 for p in selected if p["near_anchor"]) / len(selected), 3),
                })
    # candidate chokepoints: high occupancy, low movement (positional only)
    chokepoints = []
    for (team, condition, c), row in cells.items():
        if condition != "all" or row["count"] < 3:
            continue
        if row["share"] >= 0.05 and (row["moving_ratio"] is None or row["moving_ratio"] <= 0.15):
            chokepoints.append({
                "team": team, "cell_x": row["x"], "cell_y": row["y"],
                "occupancy_share": round(row["share"], 3), "count": row["count"],
                "moving_ratio": row["moving_ratio"],
                "candidate_reason": "high occupancy + low movement; positional proxy only (no collision/navmesh)",
            })
    chokepoints.sort(key=lambda r: (-r["occupancy_share"], r["team"]))
    # run summary
    health = any(p["hp"] is not None for p in points)
    cls = any(p["class_id"] is not None for p in points)
    div = any(p["division"] is not None for p in points)
    waves = sorted({p["wave"] for p in points if p["wave"] >= 0})
    unique_agent_ids = len({p["agent_id"] for p in points if p["agent_id"] >= 0 and p["team"] in (0, 1)})
    summary = {
        "schema": SCHEMA, "run": run, "points": len(points),
        "heartbeats": len(heartbeats), "agents": unique_agent_ids,
        "agent_tracks": len(agents), "waves": waves,
        "ticks": [min((p["tick"] for p in points), default=None), max((p["tick"] for p in points), default=None)],
        "ts_ms_range": [min((p["ts_ms"] for p in points if p["ts_ms"] is not None), default=None),
                        max((p["ts_ms"] for p in points if p["ts_ms"] is not None), default=None)],
        "health_sampled": health, "class_sampled": cls, "division_sampled": div,
        "conditions": dict(Counter(p["condition"] for p in points)),
        "gaps": sorted(set(gaps + [
            "health/HP absent" if not health else "health present in some samples",
            "class_id absent" if not cls else "class present in some samples",
            "division absent/unknown" if not div else "division present in some samples",
            "build/probe SHA not carried in this bundle unless supplied",
            "formation mode / seed / spectator status not carried in this bundle",
            "position sampling sparse (ai_sample cadence, not per-frame)",
            "no collision/navmesh/chokepoint ground truth; candidate chokepoints are positional proxies",
        ])),
    }
    return summary, cells, agents, cohesion, chokepoints


def _write_csv(path: Path, rows, fields):
    path.parent.mkdir(parents=True, exist_ok=True)
    if not fields and rows:
        fields = list(rows[0].keys())
    with path.open("w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=fields)
        w.writeheader()
        for row in rows:
            w.writerow({k: row.get(k) for k in fields})


def _svg_panel(summary, cells, outdir: Path):
    conditions = [c for c in CONDITIONS if any(c == key[1] for key in cells)]
    if not conditions:
        return None
    x0, x1, y0, y1 = CITY_BOUNDS
    ncols = len(conditions)
    cellpix = 7
    grid_w = int(math.ceil((x1 - x0) / CELL)) * cellpix
    grid_h = int(math.ceil((y1 - y0) / CELL)) * cellpix
    margin_l, margin_t, gap = 62, 38, 12
    width = margin_l + ncols * (grid_w + gap)
    height = margin_t + 2 * (grid_h + 30) + 20
    outdir.mkdir(parents=True, exist_ok=True)
    run_id = summary["run"].get("run_id", "run")
    path = outdir / ("spatial_panel_" + "".join(ch if ch.isalnum() or ch in "-_" else "_" for ch in run_id)[:40] + ".svg")
    parts = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">',
             '<rect width="100%" height="100%" fill="#111"/>',
             '<text x="8" y="18" fill="#fff" font-family="monospace" font-size="12">'
             + f'{run_id} - descriptive occupancy/flow panels (no visual/acceptance claim)</text>']
    for col, condition in enumerate(conditions):
        parts.append(f'<text x="{margin_l + col * (grid_w + gap)}" y="{margin_t - 8}" fill="#fff" font-family="monospace" font-size="11">{condition}</text>')
        for row, team in enumerate((0, 1)):
            xoff = margin_l + col * (grid_w + gap)
            yoff = margin_t + row * (grid_h + 30)
            parts.append(f'<rect x="{xoff}" y="{yoff}" width="{grid_w}" height="{grid_h}" fill="#181818" stroke="#333"/>')
            parts.append(f'<text x="{xoff}" y="{yoff + 12}" fill="#fff" font-family="monospace" font-size="10">team {team}</text>')
            rows = [v for (t, c, _), v in cells.items() if t == team and c == condition]
            maxshare = max((v["share"] for v in rows), default=0) or 1.0
            for v in rows:
                px = xoff + int((v["x"] - x0) / (x1 - x0) * grid_w)
                py = yoff + int((v["y"] - y0) / (y1 - y0) * grid_h)
                alpha = 0.15 + 0.8 * (v["share"] / maxshare)
                colour = "#3fa9f5" if team == 0 else "#f56c6c"
                parts.append(f'<rect x="{px}" y="{py}" width="{cellpix}" height="{cellpix}" fill="{colour}" fill-opacity="{alpha:.2f}"/>')
                if v["flow_dx"] is not None and v["flow_dy"] is not None:
                    tx = px + v["flow_dx"] * 1.5
                    ty = py - v["flow_dy"] * 1.5
                    parts.append(f'<line x1="{px + cellpix / 2}" y1="{py + cellpix / 2}" x2="{tx:.1f}" y2="{ty:.1f}" stroke="#fff" stroke-width="1" opacity="0.65"/>')
            parts.append(f'<text x="{xoff}" y="{yoff + grid_h + 12}" fill="#aaa" font-family="monospace" font-size="9">post2/3/4 + north anchor in report</text>')
    parts.append("</svg>")
    path.write_text("\n".join(parts), encoding="utf-8")
    return path


def analyze_bundles(bundles, out: Path, bounds=CITY_BOUNDS, cell=CELL, panels=False):
    out.mkdir(parents=True, exist_ok=True)
    run_rows, cell_rows, agent_rows, cohesion_rows, choke_rows = [], [], [], [], []
    for bundle in bundles:
        root, events, meta = _read_bundle(Path(bundle))
        run, points, heartbeats, gaps = _events_to_data(events, meta)
        run["run_id"] = run.get("run_id") or str(root.name)
        run["source_bundle"] = str(root)
        summary, cells, agents, cohesion, chokes = _analyze(run, points, heartbeats, gaps, bounds, cell)
        run_rows.append({
            "run_id": summary["run"]["run_id"], "source_bundle": summary["run"]["source_bundle"],
            "map": summary["run"]["map"], "formation_mode": summary["run"].get("formation_mode"),
            "build_sha": summary["run"].get("build_sha"), "probe_sha": summary["run"].get("probe_sha"),
            "seed": summary["run"].get("seed"), "spectator_or_overview": summary["run"].get("spectator_or_overview"),
            "sample_interval_s": summary["run"].get("sample_interval_s"),
            "points": summary["points"], "heartbeats": summary["heartbeats"],
            "agents": summary["agents"], "agent_tracks": summary["agent_tracks"],
            "waves": json.dumps(summary["waves"]),
            "tick_min": summary["ticks"][0], "tick_max": summary["ticks"][1],
            "health_sampled": summary["health_sampled"], "class_sampled": summary["class_sampled"],
            "division_sampled": summary["division_sampled"],
            "conditions": json.dumps(summary["conditions"]),
            "gaps": " | ".join(summary["gaps"]),
        })
        for v in cells.values():
            cell_rows.append({"run_id": summary["run"]["run_id"], **v})
        for a in agents:
            agent_rows.append({"run_id": summary["run"]["run_id"], **a})
        for c in cohesion:
            cohesion_rows.append({"run_id": summary["run"]["run_id"], **c})
        for ch in chokes:
            choke_rows.append({"run_id": summary["run"]["run_id"], **ch})
        if panels:
            _svg_panel(summary, cells, out / "panels")
    _write_csv(out / "spatial_runs.csv", run_rows, list(run_rows[0].keys()) if run_rows else [])
    _write_csv(out / "spatial_cells.csv", cell_rows, list(cell_rows[0].keys()) if cell_rows else [])
    _write_csv(out / "spatial_agents.csv", agent_rows, list(agent_rows[0].keys()) if agent_rows else [])
    _write_csv(out / "spatial_cohesion.csv", cohesion_rows, list(cohesion_rows[0].keys()) if cohesion_rows else [])
    _write_csv(out / "spatial_chokepoints.csv", choke_rows, list(choke_rows[0].keys()) if choke_rows else [])
    (out / "spatial_summary.json").write_text(json.dumps({"schema": SCHEMA, "runs": run_rows,
                                                          "cells": cell_rows, "agents": agent_rows,
                                                          "cohesion": cohesion_rows, "chokepoints": choke_rows},
                                                         indent=2), encoding="utf-8")
    return {"runs": run_rows, "cells": cell_rows, "agents": agent_rows,
            "cohesion": cohesion_rows, "chokepoints": choke_rows}


def _load_run_meta(path: Path):
    """Map D's heatmap-run-metadata.v1 into run fields + a sanitized summary."""
    data = json.loads(path.read_text(encoding="utf-8"))
    if data.get("schema") != "zombieee.heatmap-run-metadata.v1":
        raise SystemExit("unsupported run metadata schema")
    build = data.get("build") or {}
    mapinfo = data.get("map") or {}
    sampling = data.get("sampling") or {}
    join = data.get("join") or {}
    frames = data.get("frames") or {}
    run = {
        "run_id": data.get("run_tag"),
        "build_sha": build.get("mission_templates_sha256"),
        "probe_sha": build.get("probe_sha_reported_by_lead"),
        "formation_mode": None,
        "map": mapinfo.get("scene"),
        "entry_ids": None,
        "seed": None,
        "sample_interval_s": sampling.get("sampling_interval_s"),
        "spectator_or_overview": join.get("spectator"),
        "mission_template": mapinfo.get("mission_template"),
        "scripts_sha256": build.get("scripts_sha256"),
        "probe_head": build.get("probe_head"),
        "perspective": join.get("perspective"),
        "frames_count": frames.get("count"),
        "runtime_verified": data.get("runtime_verified"),
    }
    meta_summary = {
        "schema": data.get("schema"), "run_tag": data.get("run_tag"),
        "mission_templates_sha256": build.get("mission_templates_sha256"),
        "scripts_sha256": build.get("scripts_sha256"),
        "probe_version": build.get("probe_version"), "probe_head": build.get("probe_head"),
        "probe_sha_reported_by_lead": build.get("probe_sha_reported_by_lead"),
        "receipt": build.get("receipt"),
        "scene": mapinfo.get("scene"), "mission_template": mapinfo.get("mission_template"),
        "game_type": mapinfo.get("game_type"), "sampling_mode": sampling.get("mode"),
        "adaptive": sampling.get("adaptive"), "sample_interval_s": sampling.get("sampling_interval_s"),
        "frames_every_s": sampling.get("frames_every_s"), "frames_count": frames.get("count"),
        "perspective": join.get("perspective"), "spectator": join.get("spectator"),
        "team0_bots": join.get("team0_bots"), "team1_bots": join.get("team1_bots"),
        "screens": sampling.get("screenshots") or [],
        "runtime_verified": data.get("runtime_verified"), "notes": data.get("notes"),
    }
    return run, meta_summary


def analyze_input(path: Path, out: Path, bounds=CITY_BOUNDS, cell=CELL, panels=False, meta_path=None):
    run, points, heartbeats, gaps = _load_input(path)
    if meta_path:
        meta_run, meta_summary = _load_run_meta(meta_path)
        for key, value in meta_run.items():
            if value is not None:
                run[key] = value
        run["meta_summary"] = meta_summary
        gaps = list(gaps) + [
            "formation_mode absent from run metadata",
            "seed absent from run metadata",
            "entry_ids absent from run metadata",
            "mission/scripts SHA are in meta_summary but bundle export run fields were partial",
        ]
    summary, cells, agents, cohesion, chokes = _analyze(run, points, heartbeats, gaps, bounds, cell)
    out.mkdir(parents=True, exist_ok=True)
    (out / "spatial_summary.json").write_text(json.dumps({
        "schema": SCHEMA, "run": summary["run"], "summary": summary,
        "cells": list(cells.values()), "agents": agents, "cohesion": cohesion,
        "chokepoints": chokes}, indent=2), encoding="utf-8")
    _write_csv(out / "spatial_runs.csv", [{"run_id": summary["run"].get("run_id"),
                                          "source_bundle": "input-json", "map": summary["run"].get("map"),
                                          "formation_mode": summary["run"].get("formation_mode"),
                                          "build_sha": summary["run"].get("build_sha"),
                                          "probe_sha": summary["run"].get("probe_sha"),
                                          "seed": summary["run"].get("seed"),
                                          "spectator_or_overview": summary["run"].get("spectator_or_overview"),
                                          "mission_template": summary["run"].get("mission_template"),
                                          "scripts_sha256": summary["run"].get("scripts_sha256"),
                                          "probe_head": summary["run"].get("probe_head"),
                                          "perspective": summary["run"].get("perspective"),
                                          "frames_count": summary["run"].get("frames_count"),
                                          "runtime_verified": summary["run"].get("runtime_verified"),
                                          "sample_interval_s": summary["run"].get("sample_interval_s"),
                                          "points": summary["points"], "heartbeats": summary["heartbeats"],
                                          "agents": summary["agents"], "agent_tracks": summary["agent_tracks"],
                                          "waves": json.dumps(summary["waves"]),
                                          "tick_min": summary["ticks"][0], "tick_max": summary["ticks"][1],
                                          "health_sampled": summary["health_sampled"],
                                          "class_sampled": summary["class_sampled"],
                                          "division_sampled": summary["division_sampled"],
                                          "conditions": json.dumps(summary["conditions"]),
                                          "gaps": " | ".join(summary["gaps"])}], [])
    _write_csv(out / "spatial_cells.csv", list(cells.values()), list(next(iter(cells.values())).keys()) if cells else [])
    _write_csv(out / "spatial_agents.csv", agents, list(agents[0].keys()) if agents else [])
    _write_csv(out / "spatial_cohesion.csv", cohesion, list(cohesion[0].keys()) if cohesion else [])
    _write_csv(out / "spatial_chokepoints.csv", chokes, list(chokes[0].keys()) if chokes else [])
    if panels:
        _svg_panel(summary, cells, out / "panels")
    return {"summary": summary, "cells": cells, "agents": agents, "cohesion": cohesion, "chokepoints": chokes}


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--bundle", action="append", default=[], help="sealed recorder directory")
    ap.add_argument("--input", type=Path, help="zombieee.heatmap-input.v1 JSON")
    ap.add_argument("--meta", type=Path, help="optional zombieee.heatmap-run-metadata.v1 JSON")
    ap.add_argument("--out", type=Path, default=Path("telemetry/spatial_out"))
    ap.add_argument("--panels", action="store_true")
    ap.add_argument("--cell", type=float, default=CELL)
    ap.add_argument("--bounds", default="90,220,100,205")
    args = ap.parse_args()
    parts = [float(x) for x in args.bounds.split(",")]
    if len(parts) != 4:
        raise SystemExit("bounds must be x0,x1,y0,y1")
    if args.input:
        result = analyze_input(args.input, args.out, tuple(parts), args.cell, args.panels, args.meta)
        print(json.dumps(result["summary"], indent=2)[:3000])
    elif args.bundle:
        result = analyze_bundles(args.bundle, args.out, tuple(parts), args.cell, args.panels)
        print(json.dumps({"runs": len(result["runs"]), "cells": len(result["cells"]),
                          "agents": len(result["agents"]), "cohesion": len(result["cohesion"]),
                          "chokepoints": len(result["chokepoints"])}, indent=2))
    else:
        raise SystemExit("provide --bundle or --input")


if __name__ == "__main__":
    main()
