"""Heatmap-ready ZDB1 input extraction (schema v1).

This module only reshapes existing recorder events into a stable per-agent
point schema for E's heatmap tooling. It does not render or validate a visual
heatmap: coordinates are engine-world units, timestamps are probe-relative
(``ts_ms``/tick), and missing samples stay explicit gaps.
"""

from __future__ import annotations

from collections import defaultdict
from typing import Any

HEATMAP_SCHEMA = "zombieee.heatmap-input.v1"
EXPECTED_SAMPLE_SECONDS = 15.0


def _int(value: Any, default: int | None = None) -> int | None:
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def _float(value: Any) -> float | None:
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _points_from_events(events: list[dict]) -> tuple[list[dict], dict[str, int]]:
    points: list[dict] = []
    gaps = defaultdict(int)
    # combat_sample carries team-0 defender HP/class/division but no x/y; join
    # it to agent_sample by (tick, id) when possible.
    combat: dict[tuple[int, int], dict] = {}
    for event in events:
        if event.get("event") != "combat_sample":
            continue
        fields = event.get("fields") or {}
        tick, agent = _int(fields.get("tick")), _int(fields.get("id"))
        if tick is not None and agent is not None:
            combat[(tick, agent)] = fields
    for event in events:
        kind = event.get("event")
        fields = event.get("fields") or {}
        tick = _int(fields.get("tick"))
        agent = _int(fields.get("id"))
        x, y = _float(fields.get("x")), _float(fields.get("y"))
        if kind not in ("ai_sample", "agent_sample"):
            continue
        if tick is None or agent is None:
            gaps["missing_tick_or_agent"] += 1
            continue
        if x is None or y is None:
            gaps["missing_position"] += 1
            continue
        team = _int(fields.get("team"))
        if team is None and kind == "agent_sample":
            team = 0  # sample_defenders currently samples team 0 only
        if team is None:
            gaps["unknown_team"] += 1
        troop = _int(fields.get("troop"))
        agent_class = _int(fields.get("class"))
        division = _int(fields.get("division"))
        hp = _int(fields.get("hp"))
        alive = fields.get("alive")
        ts_ms = _int(fields.get("ts_ms"))
        if kind == "agent_sample":
            match = combat.get((tick, agent), {})
            agent_class = _int(match.get("class"), agent_class)
            division = _int(match.get("division"), division)
            hp = _int(match.get("hp"), hp)
            if alive is None:
                alive = match.get("alive")
        if hp is None:
            gaps["missing_health"] += 1
        if agent_class is None:
            gaps["missing_class"] += 1
        if division is None:
            gaps["missing_division"] += 1
        if ts_ms is None:
            gaps["missing_ts_ms"] += 1
        points.append({
            "agent_id": agent, "team": team, "troop": troop,
            "class_id": agent_class, "division": division,
            "tick": tick, "ts_ms": ts_ms,
            "x": x, "y": y, "hp": hp,
            "alive": (bool(_int(alive)) if _int(alive) is not None else None),
            "wave": _int(fields.get("wave")),
            "round": _int(fields.get("round")),
            "mode": _int(fields.get("mode")),
            "source": kind,
        })
    return points, dict(gaps)


def _anchor_and_deltas(points: list[dict]) -> tuple[dict, dict, list[dict]]:
    """Team anchor per tick, per-point distance-to-anchor, and per-agent deltas."""
    by_tick_team: dict[tuple[int, int | None], list[dict]] = defaultdict(list)
    by_agent: dict[int, list[dict]] = defaultdict(list)
    for point in points:
        by_tick_team[(point["tick"], point["team"])].append(point)
        by_agent[point["agent_id"]].append(point)
    anchors: dict[str, dict] = {}
    for (tick, team), rows in by_tick_team.items():
        if not rows:
            continue
        cx = sum(row["x"] for row in rows) / len(rows)
        cy = sum(row["y"] for row in rows) / len(rows)
        spread = (sum((row["x"] - cx) ** 2 + (row["y"] - cy) ** 2
                      for row in rows) / len(rows)) ** 0.5
        key = f"{team}:{tick}"
        anchors[key] = {"team": team, "tick": tick,
                        "anchor_x": round(cx, 3), "anchor_y": round(cy, 3),
                        "cohesion_rms": round(spread, 3), "agents": len(rows)}
        for row in rows:
            row["anchor_x"] = round(cx, 3)
            row["anchor_y"] = round(cy, 3)
            row["dist_to_anchor"] = round(
                ((row["x"] - cx) ** 2 + (row["y"] - cy) ** 2) ** 0.5, 3)
    totals: dict[int, dict] = {}
    for agent, rows in by_agent.items():
        rows.sort(key=lambda row: (row["tick"], row["ts_ms"] if row["ts_ms"] is not None else -1))
        moved = 0.0
        for previous, current in zip(rows, rows[1:]):
            dx = current["x"] - previous["x"]
            dy = current["y"] - previous["y"]
            distance = (dx * dx + dy * dy) ** 0.5
            current["dx"] = round(dx, 3)
            current["dy"] = round(dy, 3)
            current["distance"] = round(distance, 3)
            current["dt_ticks"] = current["tick"] - previous["tick"]
            if previous["ts_ms"] is not None and current["ts_ms"] is not None:
                current["dt_ms"] = current["ts_ms"] - previous["ts_ms"]
            else:
                current["dt_ms"] = None
            moved += distance
        totals[agent] = {
            "team": rows[0]["team"],
            "troop": rows[0]["troop"],
            "class_id": rows[-1]["class_id"],
            "division": rows[-1]["division"],
            "samples": len(rows),
            "first_tick": rows[0]["tick"],
            "last_tick": rows[-1]["tick"],
            "movement_total": round(moved, 3),
            "last_hp": rows[-1]["hp"],
            "last_alive": rows[-1]["alive"],
        }
    return anchors, totals, points


def _density(points: list[dict]) -> dict[str, Any]:
    ticks = sorted({point["tick"] for point in points})
    stamps = sorted({point["ts_ms"] for point in points if point["ts_ms"] is not None})
    gaps: list[str] = []
    tick_gap = max((b - a for a, b in zip(ticks, ticks[1:])), default=0)
    ts_gap = max((b - a for a, b in zip(stamps, stamps[1:])), default=0)
    counts = [sum(1 for point in points if point["tick"] == tick) for tick in ticks]
    density = {
        "unique_ticks": len(ticks),
        "points": len(points),
        "agents": len({point["agent_id"] for point in points}),
        "points_per_tick_mean": round(sum(counts) / len(counts), 3) if counts else None,
        "points_per_tick_min": min(counts) if counts else None,
        "points_per_tick_max": max(counts) if counts else None,
        "expected_sample_interval_s": EXPECTED_SAMPLE_SECONDS,
        "max_tick_gap": tick_gap,
        "max_ts_ms_gap": ts_gap if stamps else None,
        "ts_source": "probe_relative_getTime_ms" if stamps else None,
    }
    if not points:
        gaps.append("no_position_points")
    if not stamps:
        gaps.append("no_ts_ms_probe_relative")
    if tick_gap > 1:
        gaps.append("tick_gap_gt_1")
    if ts_gap and ts_gap > EXPECTED_SAMPLE_SECONDS * 1000 * 1.5:
        gaps.append("wall_gap_gt_1.5x_expected")
    density["gaps"] = gaps
    return density


def _heartbeats(events: list[dict]) -> list[dict]:
    rows = []
    for event in events:
        if event.get("event") != "heartbeat":
            continue
        f = event.get("fields") or {}
        rows.append({
            "tick": _int(f.get("count")),
            "ts_ms": _int(f.get("ts_ms")),
            "wave": _int(f.get("wave")),
            "round": _int(f.get("round")),
            "mode": _int(f.get("mode")),
            "team0": _int(f.get("team0")),
            "team1": _int(f.get("team1")),
            "alive0": _int(f.get("alive_team0")),
            "alive1": _int(f.get("alive_team1")),
        })
    return rows


def extract_heatmap(ingest: dict[str, Any]) -> dict[str, Any]:
    """Return a heatmap-ready schema dict from one ingested bundle."""
    events = ingest.get("events") or []
    points, raw_gaps = _points_from_events(events)
    anchors, agents, points = _anchor_and_deltas(points)
    gaps = []
    for key, count in sorted(raw_gaps.items()):
        gaps.append(f"{key}:{count}")
    density = _density(points)
    gaps.extend(density.get("gaps") or [])
    if not points:
        gaps.append("heatmap_has_no_points")
    recorder = ingest.get("recorder") or {}
    root = ingest.get("root")
    run_id = recorder.get("session_id") if isinstance(recorder, dict) else None
    if not run_id and root:
        run_id = str(root).replace("\\", "/").rstrip("/").split("/")[-1]
    run = {
        "run_id": run_id,
        "build_sha": recorder.get("build_sha") if isinstance(recorder, dict) else None,
        "probe_sha": recorder.get("probe_sha") if isinstance(recorder, dict) else None,
        "formation_mode": None,
        "map": None,
        "entry_ids": None,
        "seed": None,
        "sample_interval_s": EXPECTED_SAMPLE_SECONDS,
        "spectator_or_overview": None,
    }
    if not any(run.get(key) is not None for key in
               ("build_sha", "probe_sha", "formation_mode", "map")):
        gaps.append("run_metadata_partial")
    return {
        "schema": HEATMAP_SCHEMA,
        "run": run,
        "points": points,
        "heartbeats": _heartbeats(events),
        "anchors": list(anchors.values()),
        "agents": {str(agent): meta for agent, meta in sorted(agents.items())},
        "sampling_density": density,
        "gaps": sorted(set(gaps)),
        "not_visual_validation": True,
        "note": ("Heatmap-ready input only; no visual/gameplay validation. "
                 "tick is primary; ts_ms is probe-relative only. Missing "
                 "health/class/division/timestamps remain unknown in gaps."),
    }
