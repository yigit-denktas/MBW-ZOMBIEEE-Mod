"""Evidence-backed acceptance matrix for the final integrated WSE2 session.

An observed marker is not independent proof of engine behavior. In particular,
a client mission marker cannot prove the dedicated host entered City.
Absent, malformed and foreign-mission telemetry remains UNKNOWN.
"""
from collections import Counter

MISSION_TEMPLATES = frozenset(("multiplayer_iv", "mst_multiplayer_iv"))
CITY_SCENES = frozenset(("tbfc_invasion_4", "scn_tbfc_invasion_4"))


def number(event, key, default=-1):
    try:
        fields = event.get("fields", {})
        if not isinstance(fields, dict) or isinstance(fields.get(key), bool):
            return default
        return int(fields.get(key, default))
    except (TypeError, ValueError, OverflowError, AttributeError):
        return default


def fields_of(event):
    fields = event.get("fields", {}) if isinstance(event, dict) else {}
    return fields if isinstance(fields, dict) else {}


def server_invasion(event):
    """Require an observed server role AND a matching invasion template."""
    fields = fields_of(event)
    return (fields.get("role") == "server"
            and fields.get("template") in MISSION_TEMPLATES)


def matrix_for_session(events: list[dict], findings: list[dict],
                       module: dict, logs: int, combat: dict) -> dict:
    events = [e for e in events if isinstance(e, dict)]
    types = Counter(e.get("event") for e in events)
    server = [e for e in events if e.get("event") == "heartbeat" and server_invasion(e)]
    mission_entries = [e for e in events if e.get("event") == "mission_enter" and server_invasion(e)]
    scene_entries = [e for e in mission_entries
                     if fields_of(e).get("scene") in CITY_SCENES]
    seen_waves = sorted({number(e, "wave") for e in server if number(e, "wave") >= 1})
    zombie_observed = any(number(e, "team1") > 0 for e in server)
    observed_city = bool(scene_entries)
    sampled_ai = combat.get("observability", {}).get("combat_samples", 0) > 0
    kills_observed = combat.get("observed_kill_increments", 0) > 0
    modes = [number(e, "mode") for e in events if e.get("event") == "tactical_change"]
    fallback_index = next((i for i, v in enumerate(modes) if v == 1), None)
    returned = (fallback_index is not None and any(v == 0 for v in modes[fallback_index + 1:]))
    err_codes = {f.get("id") for f in findings if isinstance(f, dict)}
    checks = {
        "engine_boot_event": ("observed" if types["boot"] else "unknown",
                              "WSE2 Lua boot marker; may be client only"),
        "invasion_mission_entered": ("observed" if mission_entries else "unknown",
                                     "explicit server-side multiplayer_iv entry marker"),
        "city_scene_observed": ("observed" if observed_city else "unknown",
                                "explicit server-side tbfc_invasion_4 scene marker"),
        "zombies_visible": ("observed" if zombie_observed else "unknown",
                            "server-side invasion heartbeat with living team-1 agent count"),
        "wave_progression": ("observed" if len(seen_waves) >= 2 else "unknown",
                             "distinct server-side invasion heartbeat wave values; not wave completion"),
        "reserved_ai_seen": ("observed" if sampled_ai else "unknown",
                             "AI-only division 5-7 combat samples; separately source-scoped"),
        "ai_kills_increased": ("observed" if kills_observed else "unknown",
                               "same-agent sampled kill counter increased"),
        "fallback_entered": ("observed" if fallback_index is not None else "unknown",
                              "tactical state switched to fallback"),
        "regroup_after_fallback": ("observed" if returned else "unknown",
                                   "tactical state switched back to hold"),
        "private_command_executed": ("observed" if types["command_exec"] else "unknown",
                                     "native command-counter delta marker"),
        "fatal_error_in_log": ("detected" if "R002" in err_codes else
                               "not_detected" if logs else "unknown",
                               "rule-based error scan; absence is not proof of stability"),
    }
    evidence = {key: {"status": state, "basis": basis}
                for key, (state, basis) in checks.items()}
    return {
        "checks": evidence, "observed_waves": seen_waves,
        "observed_check_count": sum(v["status"] == "observed" for v in evidence.values()),
        "unknown_check_count": sum(v["status"] == "unknown" for v in evidence.values()),
        "build_flags": {
            "difficulty": module.get("difficulty", "unknown"),
            "defender_loadout_profile": module.get("defender_loadout_profile", "unknown"),
            "experimental_defenders": module.get("experimental_defenders", "unknown"),
            "private_commands": (module.get("private_commands") or {}).get("enabled", False)
                                if isinstance(module.get("private_commands"), dict) else False,
        },
        "interpretation": ("Observed events support individual claims only. "
                           "Server invasion and City scene require explicit role/template/scene markers. "
                           "Absent scene telemetry is unknown, not confirmed City entry. "
                           "Final playability needs direct game verification."),
    }
