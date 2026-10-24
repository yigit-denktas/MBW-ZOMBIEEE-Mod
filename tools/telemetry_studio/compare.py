"""Compare two ingested bundles (baseline vs candidate) without claiming success."""

from __future__ import annotations

from typing import Any

from .perf import analyze_performance

METRIC_DIRECTIONS = {
    "heartbeats": "higher_better",
    "ai_samples_per_heartbeat": "higher_better",
    "combat_samples_per_heartbeat": "higher_better",
    "missing_heartbeat_intervals": "lower_better",
    "non_monotonic_ticks": "lower_better",
    "engine_error_total": "lower_better",
    "max_log_bytes": "lower_better",
}


def _metric(ingest: dict[str, Any], key: str) -> Any:
    perf = analyze_performance(ingest)
    return perf.get(key)


def compare_ingests(baseline: dict[str, Any], candidate: dict[str, Any]) -> dict[str, Any]:
    """Return a metric delta table plus explicit unknown/unavailable fields.

    ``direction`` is a heuristic (lower/higher is better) and never an
    acceptance verdict: keep/discard still requires a hypothesis and a sealed run.
    """
    base_perf = analyze_performance(baseline)
    cand_perf = analyze_performance(candidate)
    deltas = {}
    for key, direction in METRIC_DIRECTIONS.items():
        before = base_perf.get(key)
        after = cand_perf.get(key)
        if isinstance(before, (int, float)) and isinstance(after, (int, float)):
            delta = after - before
            if direction == "lower_better":
                verdict = "better" if delta < 0 else "worse" if delta > 0 else "same"
            else:
                verdict = "better" if delta > 0 else "worse" if delta < 0 else "same"
        else:
            delta = None
            verdict = "unknown"
        deltas[key] = {"baseline": before, "candidate": after, "delta": delta,
                       "direction": direction, "verdict": verdict}

    baseline_errors = baseline.get("max_errors") or {}
    candidate_errors = candidate.get("max_errors") or {}
    return {
        "baseline": {
            "root": baseline.get("root"), "verified": baseline.get("verified"),
            "events": len(baseline.get("events") or []),
            "anomaly_errors": baseline_errors,
        },
        "candidate": {
            "root": candidate.get("root"), "verified": candidate.get("verified"),
            "events": len(candidate.get("events") or []),
            "anomaly_errors": candidate_errors,
        },
        "perf": {"baseline": base_perf, "candidate": cand_perf},
        "deltas": deltas,
        "unknown_deltas": [key for key, row in deltas.items() if row["verdict"] == "unknown"],
        "note": ("metric deltas only; verdicts are heuristic and no acceptance is implied"),
    }
