"""Event schema and granularity catalog for the ZDB1 recorder stream."""

from __future__ import annotations

from typing import Any

SCHEMA = "zombieee.flight.v1"

# Minimal contract: what each event must carry, and which integer fields are
# bounded. Unknown extra fields are allowed and reported, never silently
# interpreted. This is deliberately a small schema: the recorder remains the
# source of truth and the schema documents only what downstream tools rely on.
EVENT_SPECS: dict[str, dict[str, Any]] = {
    "heartbeat": {
        "required": ("count", "role"),
        "integers": {
            "count": (0, 1000000), "agents": (0, 100000),
            "team0": (0, 100000), "team1": (0, 100000),
            "wave": (0, 1000), "round": (-1, 1),
            "game_type": (-1, 1000), "mode": (-1, 1000),
        },
        "roles": ("server", "client", "unknown"),
        "granularity": "15 s periodic snapshot",
    },
    "ai_sample": {
        "required": ("tick", "team", "id"),
        "integers": {
            "tick": (0, 1000000), "team": (0, 1), "id": (0, 100000),
            "group": (-1, 255), "troop": (-1, 100000),
            "kills": (-1, 10000), "speed": (-1, 10000),
            "time_multiplier": (-1, 100000), "action_speed": (-1, 100000),
        },
        "granularity": "bounded per-heartbeat bot sample (max 8)",
    },
    "combat_sample": {
        "required": ("tick", "id", "troop"),
        "integers": {
            "tick": (0, 1000000), "id": (0, 100000), "troop": (-1, 100000),
            "group": (-1, 255), "kills": (-1, 10000),
            "ammo": (-1, 100000), "weapon": (-1, 100000),
        },
        "granularity": "bounded defender sample (max 16 per heartbeat)",
    },
    "wave_started": {"required": ("wave",), "integers": {"wave": (0, 1000)},
                     "granularity": "transition event"},
    "wave_change": {"required": ("wave",), "integers": {"wave": (0, 1000)},
                    "granularity": "transition event"},
    "round_started": {"required": (), "integers": {},
                      "granularity": "transition event"},
    "probe_anomaly": {"required": ("kind",), "integers": {},
                      "granularity": "bounded one-shot diagnostics"},
    "probe_failed": {"required": ("kind",), "integers": {},
                     "granularity": "error event (bounded)"},
    "probe_capability": {"required": (), "integers": {},
                         "granularity": "one-shot capability line"},
    "recorder_capabilities": {"required": (), "integers": {},
                              "granularity": "boot-time capability line"},
}


def schema_catalog() -> dict[str, Any]:
    """Machine-readable schema/granularity summary for tools and docs."""
    return {
        "schema": SCHEMA,
        "events": {
            name: {
                "required": list(spec["required"]),
                "integers": {key: list(bounds) for key, bounds in spec["integers"].items()},
                "granularity": spec["granularity"],
            }
            for name, spec in EVENT_SPECS.items()
        },
    }


def _bounded_int(value: str) -> int | None:
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def validate_event(event: dict[str, Any]) -> list[str]:
    """Return schema problems for one parsed ZDB1 event ([] means valid).

    Unknown event kinds and unknown fields are reported, not rejected: the
    recorder may add fields before the schema is updated. Integer fields that
    are present but outside their documented bounds are rejected.
    """
    problems: list[str] = []
    kind = event.get("event")
    fields = event.get("fields") or {}
    if not isinstance(kind, str) or not kind:
        return ["event kind missing"]
    spec = EVENT_SPECS.get(kind)
    if spec is None:
        return [f"unknown event kind: {kind}"]
    for name in spec["required"]:
        if name not in fields:
            problems.append(f"{kind}: missing required field {name}")
    for name, (low, high) in spec["integers"].items():
        if name not in fields:
            continue
        value = _bounded_int(fields[name])
        if value is None:
            problems.append(f"{kind}: {name} is not an integer: {fields[name]!r}")
        elif not low <= value <= high:
            problems.append(f"{kind}: {name}={value} outside {low}..{high}")
    roles = spec.get("roles")
    if roles and fields.get("role") not in roles:
        problems.append(f"{kind}: role {fields.get('role')!r} not in {roles}")
    return problems
