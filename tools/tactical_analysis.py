#!/usr/bin/env python3
"""Conservative offline tactical/wave diagnostics using WSE2 ZDB1 events.

A stationary guard is expected when holding a position. Flag a possible
movement fault only with optional samples around an actual state transition.
No game writes or engine control.
"""
from collections import defaultdict
import math


def integer(fields, key, default=-1):
    try:
        return int(fields.get(key, default))
    except (ValueError, TypeError, OverflowError):
        return default


def analyze_tactical_events(events, installed):
    beats, changes = [], []
    positions = defaultdict(list)
    for record in events:
        typ = record.get("event")
        data = record.get("fields", {})
        if typ == "heartbeat" and data.get("role") == "server":
            beats.append({k: integer(data, v) for k, v in (
                ("tick", "count"), ("wave", "wave"), ("mode", "mode"),
                ("team0", "team0"), ("team1", "team1"))})
        elif typ == "tactical_change":
            wave, mode, tick = (integer(data, k) for k in ("wave", "mode", "tick"))
            if mode in (0, 1) and tick > 0:
                changes.append({"wave": wave, "mode": mode, "tick": tick})
        elif typ == "agent_sample":
            agent, group, tick = (integer(data, k) for k in ("id", "group", "tick"))
            if not (0 <= agent < 10000 and 5 <= group <= 7 and tick > 0):
                continue
            try:
                x, y = float(data["x"]), float(data["y"])
            except (ValueError, KeyError, TypeError):
                continue
            if math.isfinite(x) and math.isfinite(y):
                positions[(agent, group)].append({"tick": tick, "x": x, "y": y})

    beats.sort(key=lambda r: r["tick"])
    changes.sort(key=lambda r: r["tick"])
    for rows in positions.values():
        rows.sort(key=lambda r: r["tick"])
    findings = []
    longest, streak, previous = 0, 0, None
    for beat in beats:
        possible = beat["tick"] > 0 and beat["wave"] >= 1 and beat["team1"] > 0
        if (possible and previous and previous["wave"] == beat["wave"]
                and beat["tick"] == previous["tick"] + 1):
            streak += 1
        else:
            streak = 1 if possible else 0
        longest = max(longest, streak)
        previous = beat
    if longest >= 9:
        findings.append({
            "id": "R019", "severity": "medium", "title": "Potentially stalled zombie wave",
            "action": "One wave persisted for nine or more 15-second samples with zombies present. A difficult wave can legitimately last this long; inspect wave completion."})

    for i in range(3, len(changes)):
        group = changes[i - 3:i + 1]
        if (group[-1]["tick"] - group[0]["tick"] <= 8
                and len({r["wave"] for r in group}) == 1
                and all(a["mode"] != b["mode"] for a, b in zip(group, group[1:]))):
            findings.append({
                "id": "R020", "severity": "medium", "title": "Tactical states alternate rapidly",
                "action": "Four fallback/regroup transitions on the same wave in approximately two minutes; inspect recovery thresholds and reinforcement timing."})
            break

    cfg = installed.get("tactical_recovery") or {}
    high = cfg.get("high_water", 3) if isinstance(cfg, dict) else 3
    if not isinstance(high, int) or not 2 <= high <= 8:
        high = 3
    streak, prev_tick = 0, -1
    for beat in beats:
        eligible = beat["mode"] == 1 and beat["team0"] >= high + 1
        streak = (streak + 1 if eligible and beat["tick"] == prev_tick + 1
                  else 1 if eligible else 0)
        prev_tick = beat["tick"]
        if streak >= 3:
            findings.append({
                "id": "R021", "severity": "medium",
                "title": "Fallback persists with apparently recovered team",
                "action": "Three samples show fallback and many team-0 agents; team counts can include players and other divisions. Verify the actual reserved non-player defenders."})
            break

    stationary = []
    for change in changes:
        for (agent, group), samples in positions.items():
            before = [p for p in samples if change["tick"] - 2 <= p["tick"] < change["tick"]]
            after = [p for p in samples if change["tick"] <= p["tick"] <= change["tick"] + 4]
            if not before or len(after) < 3:
                continue
            span = [before[-1], *after]
            if span[-1]["tick"] - span[0]["tick"] < 3:
                continue
            travelled = max(math.hypot(p["x"] - span[0]["x"], p["y"] - span[0]["y"])
                            for p in span[1:])
            if travelled < 1.0:
                stationary.append({"agent_id": agent, "group": group,
                                   "wave": change["wave"], "mode": change["mode"],
                                   "observed_ticks": span[-1]["tick"] - span[0]["tick"]})
        if stationary:
            break
    if stationary:
        findings.append({
            "id": "R022", "severity": "medium",
            "title": "Defender did not move after a tactical state change",
            "action": "Optional position samples show less than one metre of movement after a new order. This may be expected if the agent was already at its destination; inspect path, line of sight and collisions.",
            "examples": stationary[:5]})
    return {
        "observability": {
            "server_heartbeats": len(beats),
            "wave_known": any(b["wave"] >= 0 for b in beats),
            "tactical_changes": len(changes),
            "position_sampled_agents": len(positions),
        },
        "longest_unchanged_wave_samples": longest,
        "stationary_candidates": len(stationary),
        "findings": findings,
    }
