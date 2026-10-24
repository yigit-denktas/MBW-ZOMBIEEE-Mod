"""Probe health / doctor: catch recorder regressions before using evidence.

Why this exists: a probe can register triggers yet emit zero heartbeats (a Lua
runtime error), or register a hit/adaptive trigger yet produce no samples. This
tool checks the sealed ZDB1 stream itself — capability line, trigger
registrations/failures, heartbeat presence/caps, counter visibility, error
spam, and an event/log budget estimate — so D/E/A see a red flag before
heatmap/balance analysis.

It never launches the game and never invents a pass: missing fields are gaps.
"""

from __future__ import annotations

from typing import Any

PROBE_HEALTH_SCHEMA = "zombieee.probe-health.v1"
REQUIRED_BASE_CAPS = ("opmeta", "group_getter", "alive_getter")


def _int(value: Any) -> int | None:
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def _latest(events: list[dict], kinds: tuple[str, ...]) -> dict:
    for event in reversed(events):
        if event.get("event") in kinds:
            return event.get("fields") or {}
    return {}


def _capabilities(events: list[dict]) -> dict[str, str]:
    caps: dict[str, str] = {}
    for event in events:
        if event.get("event") not in ("recorder_capabilities", "probe_capability"):
            continue
        for key, value in (event.get("fields") or {}).items():
            caps[str(key)] = str(value)
    return caps


def _check(checks, check_id, status, detail):
    checks.append({"id": check_id, "status": status, "detail": detail})


def probe_health(ingest: dict[str, Any]) -> dict[str, Any]:
    events = ingest.get("events") or []
    caps = _capabilities(events)
    registered = [event.get("fields") or {} for event in events
                  if event.get("event") == "probe_registered"]
    failed = [event.get("fields") or {} for event in events
              if event.get("event") == "probe_failed"]
    heartbeat = [event for event in events if event.get("event") == "heartbeat"]
    hits = [event for event in events if event.get("event") == "hit_sample"]
    adaptive = [event for event in events
                if event.get("event") in ("adaptive_sample", "adaptive_event")]
    checks: list[dict] = []
    gaps: list[str] = []

    if not ingest.get("verified"):
        _check(checks, "sealed_bundle", "warn",
               "bundle is not manifest-verified")
        gaps.append("unsealed_bundle")
    else:
        _check(checks, "sealed_bundle", "ok", "manifest verified")

    if not registered and not failed:
        _check(checks, "trigger_registrations", "fail",
               "no probe_registered/probe_failed events")
        gaps.append("trigger_registrations_missing")
    else:
        kinds = [str(row.get("kind")) for row in registered]
        missing = [kind for kind in ("entry", "heartbeat") if kind not in kinds]
        if missing:
            _check(checks, "trigger_registrations", "fail",
                   f"missing registration kinds={missing}; registered={kinds}")
            gaps.append("required_trigger_missing")
        else:
            _check(checks, "trigger_registrations", "ok",
                   f"registered={kinds}")
    if failed:
        _check(checks, "trigger_failures", "fail",
               f"probe_failed events={len(failed)}")
        gaps.append("probe_failed")
    else:
        _check(checks, "trigger_failures", "ok", "no probe_failed events")

    missing_caps = [key for key in REQUIRED_BASE_CAPS if key not in caps]
    for key in missing_caps:
        gaps.append(f"capability_missing:{key}")
    if missing_caps:
        _check(checks, "base_capabilities", "warn",
               f"missing={missing_caps}")
    else:
        _check(checks, "base_capabilities", "ok",
               "opmeta/group/alive capabilities present")

    if not heartbeat:
        _check(checks, "heartbeat", "fail",
               "zero heartbeat events; recorder/lua heartbeat path is not emitting")
        gaps.append("no_heartbeat_events")
    else:
        _check(checks, "heartbeat", "ok", f"heartbeats={len(heartbeat)}")

    latest_hb = _latest(events, ("heartbeat",))
    if latest_hb:
        for key in ("hit_attempts", "hit_events", "hit_param_invalid"):
            if key not in latest_hb:
                gaps.append(f"heartbeat_field_missing:{key}")
                _check(checks, "hit_counters", "warn",
                       "hit counters absent from heartbeat (old probe?)")
                break
        else:
            _check(checks, "hit_counters", "ok",
                   f"hit_attempts={latest_hb.get('hit_attempts')} "
                   f"hit_events={latest_hb.get('hit_events')} "
                   f"hit_param_invalid={latest_hb.get('hit_param_invalid')}")

    if caps.get("adaptive_sampling") == "1":
        if not adaptive:
            _check(checks, "adaptive_samples", "fail",
                   "capability says adaptive_sampling=1 but no adaptive events")
            gaps.append("adaptive_samples_missing")
        else:
            _check(checks, "adaptive_samples", "ok",
                   f"adaptive_points={len(adaptive)}")
        for key in ("adaptive_ticks", "adaptive_samples", "adaptive_events",
                    "adaptive_skips", "adaptive_active_ticks"):
            if key not in latest_hb:
                gaps.append(f"heartbeat_field_missing:{key}")
        if any(gap.startswith("heartbeat_field_missing:adaptive") for gap in gaps):
            _check(checks, "adaptive_counters", "fail",
                   "adaptive capability present but adaptive heartbeat counters absent")
        else:
            _check(checks, "adaptive_counters", "ok",
                   "adaptive heartbeat counters present")

    if caps.get("hit_trigger") == "-28":
        attempts = _int(latest_hb.get("hit_attempts")) or 0
        hit_event_count = _int(latest_hb.get("hit_events")) or 0
        invalid = _int(latest_hb.get("hit_param_invalid")) or 0
        if attempts > 0 and (hit_event_count == 0 or invalid > 0 or not hits):
            _check(checks, "hit_trigger", "fail",
                   f"attempts={attempts} events={hit_event_count} invalid={invalid} "
                   f"hit_samples={len(hits)}; params not decoding")
            gaps.append("hit_params_invalid")
            if not hits:
                gaps.append("hit_samples_zero")
        elif hit_event_count > attempts:
            _check(checks, "hit_trigger", "fail",
                   f"impossible counters: hit_events={hit_event_count} > attempts={attempts}")
            gaps.append("hit_counter_inconsistent")
        elif attempts == 0:
            _check(checks, "hit_trigger", "warn",
                   "hit trigger registered but no hits/attempts observed yet")
        else:
            _check(checks, "hit_trigger", "ok",
                   f"hit_samples={len(hits)} attempts={attempts} events={hit_event_count}")

    errors = ingest.get("max_errors") or {}
    spam = {key: value for key, value in errors.items()
            if key in ("script_error", "invalid_faction", "invalid_faction_min",
                       "illegal_lvalue") and value}
    if spam.get("invalid_faction_min"):
        _check(checks, "engine_errors", "fail",
               f"Invalid Faction ID:-2147483648 x{spam['invalid_faction_min']}")
        gaps.append("invalid_faction_negative_spam")
    elif spam.get("script_error"):
        _check(checks, "engine_errors", "warn",
               f"SCRIPT ERROR x{spam['script_error']}")
        gaps.append("script_error_present")
    else:
        _check(checks, "engine_errors", "ok", "no critical error family detected")

    log_bytes = max((artifact.get("bytes", 0)
                     for artifact in ingest.get("artifacts") or []), default=0)
    event_count = len(events)
    budget = {
        "events": event_count,
        "heartbeats": len(heartbeat),
        "hits": len(hits),
        "adaptive_points": len(adaptive),
        "max_log_bytes": log_bytes,
        "bytes_per_event": round(log_bytes / event_count, 2) if event_count else None,
        "estimated_log_bytes_per_1000_events": (
            round(log_bytes / event_count * 1000, 2) if event_count else None),
        "note": "estimated from this bundle; adaptive/1 s runs may grow much faster",
    }
    if log_bytes > 2 * 1024 * 1024:
        gaps.append("large_log_artifact")
        _check(checks, "log_budget", "warn", f"max log artifact={log_bytes} bytes")
    else:
        _check(checks, "log_budget", "ok",
               f"max log artifact={log_bytes} bytes")

    failures = [c for c in checks if c["status"] == "fail"]
    warnings = [c for c in checks if c["status"] == "warn"]
    return {
        "schema": PROBE_HEALTH_SCHEMA,
        "ok": not failures,
        "status": ("fail" if failures else "warn" if warnings else "ok"),
        "checks": checks,
        "gaps": sorted(set(gaps)),
        "budget": budget,
        "capabilities": caps,
        "registered_kinds": [str(row.get("kind")) for row in registered],
        "note": "Probe health only; no gameplay/acceptance claim.",
    }
