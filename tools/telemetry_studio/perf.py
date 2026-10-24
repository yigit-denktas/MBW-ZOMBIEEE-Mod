"""Performance and cadence analysis from an ingested bundle.

Everything here is a *proxy* from recorded data. Tick cadence is measured from
the recorder heartbeat sequence; CPU/memory only if the recorder receipt
reports them; WSE2 stats options only if a local config file is readable.
Unmeasurable fields stay None and are listed in ``unknown``.
"""

from __future__ import annotations

import statistics
from pathlib import Path
from typing import Any

EXPECTED_HEARTBEAT_SECONDS = 15.0
WSE2_CONFIG = Path.home() / "Documents" / "Mount&Blade Warband WSE2" / "rgl_config.ini"
WSE2_STATS_KEYS = (
    "bShowSimulationStats",
    "bShowRenderStats",
    "iSimulationStatsLogInterval",
    "iRenderStatsLogInterval",
    "bLogSpeedModifiers",
)


def _int(value: Any) -> int | None:
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def _read_wse2_stats() -> dict[str, Any]:
    if not WSE2_CONFIG.is_file():
        return {"available": False, "path": str(WSE2_CONFIG), "options": None}
    options: dict[str, str] = {}
    try:
        for line in WSE2_CONFIG.read_text(encoding="utf-8", errors="replace").splitlines():
            if "=" not in line:
                continue
            key, _, value = line.partition("=")
            if key.strip() in WSE2_STATS_KEYS:
                options[key.strip()] = value.strip()
    except OSError:
        return {"available": False, "path": str(WSE2_CONFIG), "options": None}
    return {"available": True, "path": str(WSE2_CONFIG), "options": options}


def analyze_performance(ingest: dict[str, Any]) -> dict[str, Any]:
    events = ingest.get("events") or []
    heartbeats = [e for e in events if e.get("event") == "heartbeat"]
    ai_samples = [e for e in events if e.get("event") == "ai_sample"]
    combat_samples = [e for e in events if e.get("event") == "combat_sample"]
    recorder = ingest.get("recorder") or {}
    duration = recorder.get("duration_seconds")
    duration = float(duration) if isinstance(duration, (int, float)) and duration > 0 else None

    tick_values = []
    timestamp_values = []
    for index, event in enumerate(heartbeats):
        fields = event.get("fields") or {}
        count = _int(fields.get("count"))
        tick_values.append(count if count is not None else index)
        timestamp = _int(fields.get("ts_ms"))
        if timestamp is not None and timestamp >= 0:
            timestamp_values.append(timestamp)
    tick_values.sort()
    deltas = [b - a for a, b in zip(tick_values, tick_values[1:]) if b >= a]
    missing_intervals = sum(max(delta - 1, 0) for delta in deltas)
    non_monotonic = sum(1 for a, b in zip(tick_values, tick_values[1:]) if b < a)
    wall_deltas_ms = [b - a for a, b in zip(timestamp_values, timestamp_values[1:])
                      if b >= a]
    wall_cadence = ((sum(wall_deltas_ms) / len(wall_deltas_ms) / 1000.0)
                    if wall_deltas_ms else None)
    wall_missing = (sum(max(int(round(delta / (EXPECTED_HEARTBEAT_SECONDS * 1000))) - 1, 0)
                         for delta in wall_deltas_ms) if wall_deltas_ms else None)
    agents = [_int((e.get("fields") or {}).get("agents")) for e in heartbeats]
    agents = [v for v in agents if v is not None]

    runtime_metrics = recorder.get("metrics") if isinstance(recorder.get("metrics"), dict) else {}
    cpu_seconds = runtime_metrics.get("cpu_seconds")
    peak_memory_kib = runtime_metrics.get("peak_memory_kib")

    unknown: list[str] = []
    if not heartbeats:
        unknown.append("heartbeat_count")
    if not any(isinstance(cpu_seconds, (int, float)) for _ in (0,)):
        unknown.append("cpu_seconds")
    if not isinstance(peak_memory_kib, (int, float)):
        unknown.append("peak_memory_kib")
    if duration is None:
        unknown.append("duration_seconds")
    if not any(tick_values):
        unknown.append("tick_cadence")
    if wall_cadence is None:
        unknown.append("tick_cadence_seconds")
    if not ai_samples:
        unknown.append("ai_sample_rate")

    log_bytes = [a.get("bytes") for a in ingest.get("artifacts") or []
                 if isinstance(a.get("bytes"), int)]
    max_errors = ingest.get("max_errors") or {}
    # SCRIPT ERROR, Invalid Faction ID and Illegal lvalue patterns overlap on the
    # same physical lines; take the max instead of summing them.
    error_total = max(max_errors.get("script_error", 0),
                      max_errors.get("invalid_faction", 0),
                      max_errors.get("illegal_lvalue", 0))
    expected_heartbeats = (duration / EXPECTED_HEARTBEAT_SECONDS) if duration else None
    coverage = (len(heartbeats) / expected_heartbeats) if expected_heartbeats else None
    return {
        "duration_seconds": duration,
        "event_rate_per_second": (len(events) / duration) if duration else None,
        "heartbeats": len(heartbeats),
        "expected_heartbeats_by_duration": expected_heartbeats,
        "heartbeat_coverage": coverage,
        "heartbeat_ticks": tick_values[:32],
        "heartbeat_deltas": deltas[:32],
        "missing_heartbeat_intervals": missing_intervals,
        "non_monotonic_ticks": non_monotonic,
        "expected_heartbeat_seconds": EXPECTED_HEARTBEAT_SECONDS,
        "tick_cadence_seconds": wall_cadence,
        "wall_clock_heartbeat_intervals_ms": wall_deltas_ms[:32],
        "wall_clock_missing_intervals": wall_missing,
        "timestamp_source": ("probe_relative_getTime_ms (within-run only; semantics unverified)") if wall_cadence is not None else None,
        "agents_mean": statistics.fmean(agents) if agents else None,
        "agents_max": max(agents) if agents else None,
        "ai_sample_count": len(ai_samples),
        "combat_sample_count": len(combat_samples),
        "ai_samples_per_heartbeat": (len(ai_samples) / len(heartbeats)) if heartbeats else None,
        "combat_samples_per_heartbeat": (len(combat_samples) / len(heartbeats)) if heartbeats else None,
        "max_log_bytes": max(log_bytes) if log_bytes else None,
        "engine_error_total": error_total,
        "engine_error_breakdown": max_errors,
        "engine_errors_per_second": (error_total / duration) if duration else None,
        "cpu_seconds": cpu_seconds if isinstance(cpu_seconds, (int, float)) else None,
        "peak_memory_kib": peak_memory_kib if isinstance(peak_memory_kib, (int, float)) else None,
        "cpu_source": (runtime_metrics.get("source") if isinstance(runtime_metrics, dict) else None),
        "event_drops": recorder.get("event_drops"),
        "log_truncated": recorder.get("log_truncated"),
        "log_omitted_bytes": recorder.get("log_omitted_bytes"),
        "wse2_stats": _read_wse2_stats(),
        "unknown": unknown,
    }
