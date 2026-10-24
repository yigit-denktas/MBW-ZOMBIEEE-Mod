"""Anomaly detection over ingested events and performance metrics."""

from __future__ import annotations

from typing import Any

ERROR_SPAM_THRESHOLD = 20
MAX_REASONABLE_LOG_BYTES = 2 * 1024 * 1024


def detect_anomalies(ingest: dict[str, Any], perf: dict[str, Any]) -> list[dict[str, Any]]:
    """Return bounded, explicit anomalies; no anomaly is inferred from absent data."""
    findings: list[dict[str, Any]] = []

    def add(code: str, severity: str, detail: str) -> None:
        findings.append({"code": code, "severity": severity, "detail": detail})

    if not ingest.get("verified"):
        add("unsealed_bundle", "high", "bundle is not a verified sealed receipt")
    if not perf.get("heartbeats"):
        add("no_heartbeats", "high", "no heartbeat events in the bundle")
    if perf.get("missing_heartbeat_intervals"):
        add("missing_heartbeat_intervals", "medium",
            f"{perf['missing_heartbeat_intervals']} heartbeat tick gaps")
    if perf.get("non_monotonic_ticks"):
        add("non_monotonic_ticks", "medium",
            f"{perf['non_monotonic_ticks']} heartbeat count regressions")
    if perf.get("event_drops"):
        add("event_drops", "high", f"recorder reported {perf['event_drops']} dropped events")
    if any(perf.get("log_truncated") or []):
        add("log_truncated", "medium", "recorder reported a truncated log")
    if any(perf.get("log_omitted_bytes") or []):
        add("log_omitted_bytes", "medium", "recorder omitted log bytes")

    errors = ingest.get("max_errors") or {}
    if errors.get("invalid_faction_min", 0) >= ERROR_SPAM_THRESHOLD:
        add("invalid_faction_negative_spam", "high",
            f"{errors['invalid_faction_min']} x Invalid Faction ID: -2147483648")
    if errors.get("invalid_faction_one", 0) >= ERROR_SPAM_THRESHOLD:
        add("invalid_faction_minus_one_spam", "high",
            f"{errors['invalid_faction_one']} x Invalid Faction ID: -1")
    if errors.get("script_error", 0) >= ERROR_SPAM_THRESHOLD:
        add("script_error_spam", "high",
            f"{errors['script_error']} x SCRIPT ERROR lines")
    if errors.get("illegal_lvalue", 0):
        add("illegal_lvalue", "high",
            f"{errors['illegal_lvalue']} x Illegal lvalue lines")
    if (perf.get("max_log_bytes") or 0) > MAX_REASONABLE_LOG_BYTES:
        add("large_engine_log", "medium",
            f"largest log artifact is {perf['max_log_bytes']} bytes")

    event_counts = ingest.get("event_counts") or {}
    if event_counts.get("probe_failed"):
        add("probe_failed_events", "high",
            f"{event_counts['probe_failed']} probe_failed events")
    if perc := (perf.get("ai_samples_per_heartbeat")):
        if perc < 0.25:
            add("low_ai_sample_coverage", "medium",
                f"only {perc:.2f} ai_samples per heartbeat")
    if ingest.get("gaps"):
        for gap in ingest["gaps"]:
            add(f"ingest_gap:{gap}", "info", "reported by ingest")
    return findings
