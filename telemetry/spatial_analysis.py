"""Spatial/heatmap consumer for `zombieee.heatmap-input.v1`.

Turns heatmap-ready points into reusable occupancy/flow tables, per-team/wave
panels, coalesced situation panels (outnumbered/advantage/even), movement
classes, cohesion and chokepoint *candidates*. It also emits a small SVG grid
for inspection. No visual/gameplay validation: labels are descriptive, unknown
stays unknown, and no acceptance claim is made.
"""

from __future__ import annotations

import json
import math
from collections import defaultdict
from pathlib import Path
from typing import Any

SPATIAL_SCHEMA = "zombieee.spatial-analysis.v1"
DEFAULT_BIN = 5.0


def _num(value: Any) -> float | None:
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _int(value: Any) -> int | None:
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def _grid(points: list[dict], bin_size: float) -> dict[str, Any]:
    cells: dict[tuple[int, int], dict[str, Any]] = {}
    xs, ys = [], []
    for point in points:
        x, y = _num(point.get("x")), _num(point.get("y"))
        if x is None or y is None:
            continue
        xs.append(x)
        ys.append(y)
        key = (int(math.floor(x / bin_size)), int(math.floor(y / bin_size)))
        cell = cells.setdefault(key, {"x": key[0], "y": key[1], "count": 0,
                                     "dx_sum": 0.0, "dy_sum": 0.0, "flow_n": 0})
        cell["count"] += 1
        dx, dy = _num(point.get("dx")), _num(point.get("dy"))
        if dx is not None and dy is not None:
            cell["dx_sum"] += dx
            cell["dy_sum"] += dy
            cell["flow_n"] += 1
    total = sum(cell["count"] for cell in cells.values()) or 1
    rows = []
    for cell in cells.values():
        n = cell["flow_n"]
        rows.append({
            "gx": cell["x"], "gy": cell["y"],
            "count": cell["count"],
            "density": round(cell["count"] / total, 4),
            "mean_dx": round(cell["dx_sum"] / n, 3) if n else None,
            "mean_dy": round(cell["dy_sum"] / n, 3) if n else None,
        })
    rows.sort(key=lambda row: (-row["count"], row["gx"], row["gy"]))
    return {
        "points": len(xs),
        "bbox": ([round(min(xs), 2), round(min(ys), 2),
                  round(max(xs), 2), round(max(ys), 2)] if xs else None),
        "centroid": ([round(sum(xs) / len(xs), 2), round(sum(ys) / len(ys), 2)]
                     if xs else None),
        "cells": rows,
    }


def analyze(heatmap: dict, *, bin_size: float = DEFAULT_BIN) -> dict[str, Any]:
    if heatmap.get("schema") != "zombieee.heatmap-input.v1":
        raise ValueError("expected zombieee.heatmap-input.v1")
    points = [point for point in heatmap.get("points") or []
              if _num(point.get("x")) is not None and _num(point.get("y")) is not None]
    run = heatmap.get("run") or {}
    gaps = list(heatmap.get("gaps") or [])
    by_team_wave: dict[tuple[int, int], list[dict]] = defaultdict(list)
    by_team_round: dict[tuple[int, int], list[dict]] = defaultdict(list)
    by_team: dict[int, list[dict]] = defaultdict(list)
    for point in points:
        team = _int(point.get("team"))
        if team not in (0, 1):
            continue
        by_team[team].append(point)
        wave = _int(point.get("wave"))
        if wave is not None:
            by_team_wave[(team, wave)].append(point)
        round_no = _int(point.get("round"))
        if round_no is not None:
            by_team_round[(team, round_no)].append(point)

    occupancy = []
    for (team, wave), rows in sorted(by_team_wave.items()):
        occupancy.append({"team": team, "wave": wave,
                          "grid": _grid(rows, bin_size)})
    round_panels = []
    for (team, round_no), rows in sorted(by_team_round.items()):
        round_panels.append({"team": team, "round": round_no,
                             "grid": _grid(rows, bin_size)})

    # Cohesion from input anchors/dist-to-anchor.
    cohesion = {}
    for team in (0, 1):
        rows = by_team.get(team) or []
        distances = [_num(point.get("dist_to_anchor")) for point in rows]
        distances = [d for d in distances if d is not None]
        spread = [_num(point.get("cohesion_rms")) for point in rows]
        spread = [s for s in spread if s is not None]
        cohesion[f"team{team}"] = {
            "points": len(rows),
            "mean_dist_to_anchor": (round(sum(distances) / len(distances), 3)
                                    if distances else None),
            "mean_cohesion_rms": (round(sum(spread) / len(spread), 3)
                                  if spread else None),
        }

    # Per-agent movement classes (track-level, ID reuse across rounds is a gap).
    agents = heatmap.get("agents") or {}
    movement = []
    for agent, meta in agents.items():
        total = _num(meta.get("movement_total"))
        if total is not None:
            movement.append({"agent": agent, "team": _int(meta.get("team")),
                             "movement_total": total,
                             "samples": _int(meta.get("samples"))})
    totals = sorted(row["movement_total"] for row in movement)
    median = (totals[len(totals) // 2] if totals else None)
    for row in movement:
        row["class"] = ("unknown" if median is None or median == 0 else
                        "over" if row["movement_total"] > median * 1.5 else
                        "under" if row["movement_total"] < median * 0.5 else
                        "mixed")
    movement_classes = defaultdict(int)
    for row in movement:
        movement_classes[f"{row['team']}:{row['class']}"] += 1

    # Situation panels from heartbeats: outnumbered/advantage/even.
    situations = defaultdict(list)
    for hb in heatmap.get("heartbeats") or []:
        alive0, alive1 = _int(hb.get("alive0")), _int(hb.get("alive1"))
        label = "unknown"
        if alive0 is not None and alive1 is not None:
            if alive0 < alive1:
                label = "outnumbered"
            elif alive0 > alive1:
                label = "advantage"
            else:
                label = "even"
        situations[label].append(hb)
    situation_panels = []
    for label, rows in situations.items():
        wave_points = [point for point in points
                       if label == "unknown" or True]
        # Join situations to points by wave when available; otherwise descriptive only.
        waves = {_int(row.get("wave")) for row in rows} - {None}
        selected = [point for point in points if _int(point.get("wave")) in waves]
        situation_panels.append({
            "situation": label, "heartbeats": len(rows),
            "waves": sorted(waves), "points": len(selected),
            "grid": _grid(selected, bin_size) if selected else None,
        })

    # Chokepoint candidates: cells occupied by both teams in the same wave.
    candidates = []
    for wave in sorted({w for _team, w in by_team_wave}):
        cells_by_team = {}
        for team in (0, 1):
            rows = by_team_wave.get((team, wave), [])
            cells_by_team[team] = {(cell["gx"], cell["gy"]): cell["count"]
                                   for cell in _grid(rows, bin_size)["cells"]}
        for key in set(cells_by_team[0]) & set(cells_by_team[1]):
            total = cells_by_team[0][key] + cells_by_team[1][key]
            candidates.append({"wave": wave, "gx": key[0], "gy": key[1],
                               "team0": cells_by_team[0][key],
                               "team1": cells_by_team[1][key],
                               "total": total})
    candidates.sort(key=lambda row: (-row["total"], row["wave"], row["gx"], row["gy"]))

    health_points = sum(1 for point in points if point.get("hp") is not None)
    class_points = sum(1 for point in points if point.get("class_id") is not None)
    if not points:
        gaps.append("spatial_has_no_points")
    if not heatmap.get("heartbeats"):
        gaps.append("heartbeats_missing_for_situations")
    if not health_points:
        gaps.append("health_not_available_for_spatial")
    if not class_points:
        gaps.append("class_not_available_for_spatial")
    return {
        "schema": SPATIAL_SCHEMA,
        "run": run,
        "bin_size": bin_size,
        "points": len(points),
        "occupancy": occupancy,
        "round_panels": round_panels,
        "cohesion": cohesion,
        "movement": {"agents": movement,
                     "classes": dict(sorted(movement_classes.items())),
                     "median_track_movement": median,
                     "level": "track-level; IDs reused across rounds is a gap"},
        "situations": situation_panels,
        "chokepoint_candidates": candidates[:40],
        "coverage": {"health_points": health_points,
                     "class_points": class_points,
                     "heartbeats": len(heatmap.get("heartbeats") or [])},
        "gaps": sorted(set(gaps)),
        "not_visual_validation": True,
        "note": ("Descriptive spatial tables only; no visual/gameplay validation. "
                 "Chokepoints are occupancy candidates, not proven blockers. "
                 "Situation labels come from heartbeat counts, not intent."),
    }


def _svg_grid(grid: dict, title: str) -> str:
    if not grid or not grid.get("cells"):
        return ""
    cells = grid["cells"]
    max_count = max(cell["count"] for cell in cells) or 1
    scale = 20
    width = (max(cell["gx"] for cell in cells) + 1) * scale + 40
    height = (max(cell["gy"] for cell in cells) + 1) * scale + 40
    min_gx = min(cell["gx"] for cell in cells)
    min_gy = min(cell["gy"] for cell in cells)
    parts = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}">',
             f'<text x="10" y="20" font-family="monospace">{title}</text>']
    for cell in cells:
        alpha = round(0.15 + 0.85 * cell["count"] / max_count, 3)
        x = (cell["gx"] - min_gx) * scale + 10
        y = (cell["gy"] - min_gy) * scale + 30
        parts.append(f'<rect x="{x}" y="{y}" width="{scale - 1}" height="{scale - 1}" '
                     f'fill="rgba(200,40,40,{alpha})"/>')
        parts.append(f'<text x="{x + 1}" y="{y + 11}" font-size="8" '
                     f'font-family="monospace">{cell["count"]}</text>')
    parts.append("</svg>")
    return "\n".join(parts)


def write_outputs(result: dict, out_dir: Path) -> dict:
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    json_path = out_dir / "spatial-analysis.json"
    json_path.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n",
                         encoding="utf-8")
    svg_paths = []
    for panel in result.get("occupancy") or []:
        title = f"team{panel['team']} wave{panel['wave']}"
        svg = _svg_grid(panel["grid"], title)
        if svg:
            path = out_dir / f"occupancy-team{panel['team']}-wave{panel['wave']}.svg"
            path.write_text(svg, encoding="utf-8")
            svg_paths.append(str(path))
    lines = ["# Spatial analysis (descriptive only)", "",
             f"Points: {result['points']} | bin={result['bin_size']} | "
             f"gaps: {', '.join(result['gaps']) or 'none'}", "",
             "## Cohesion", ""]
    for team, row in (result.get("cohesion") or {}).items():
        lines.append(f"- {team}: {row}")
    lines += ["", "## Movement classes", "",
              f"- {result['movement']['classes']}",
              f"- median track movement: {result['movement']['median_track_movement']}",
              f"- {result['movement']['level']}", "",
              "## Situations", ""]
    for panel in result.get("situations") or []:
        lines.append(f"- {panel['situation']}: heartbeats={panel['heartbeats']} "
                     f"waves={panel['waves']} points={panel['points']}")
    lines += ["", "## Chokepoint candidates (occupancy only)", ""]
    for row in result.get("chokepoint_candidates", [])[:10]:
        lines.append(f"- wave {row['wave']} cell {row['gx']},{row['gy']}: "
                     f"team0={row['team0']} team1={row['team1']}")
    lines += ["", "No visual/acceptance claim; UNKNOWN never passes."]
    md_path = out_dir / "SPATIAL_ANALYSIS.md"
    md_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return {"json": str(json_path), "markdown": str(md_path), "svg": svg_paths}


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Analyze heatmap input")
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--out-dir", type=Path, default=Path("telemetry/spatial_out"))
    parser.add_argument("--bin-size", type=float, default=DEFAULT_BIN)
    args = parser.parse_args()
    data = json.loads(args.input.read_text(encoding="utf-8"))
    result = analyze(data, bin_size=args.bin_size)
    outputs = write_outputs(result, args.out_dir)
    print(json.dumps(outputs, indent=2))
