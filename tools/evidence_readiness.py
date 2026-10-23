"""Evidence-backed acceptance matrix for the final integrated WSE2 session.

Observations are deliberately not labelled 'passed' or 'failed'. Client
markers or other mission templates cannot attest the dedicated server's
City invasion; absence or malformed fields remain unknown.
"""
from collections import Counter

INVASION_TEMPLATES = frozenset(("multiplayer_iv", "mst_multiplayer_iv"))
CITY_SCENES = frozenset(("tbfc_invasion_4", "scn_tbfc_invasion_4"))


def fields_of(event):
    fields = event.get("fields", {}) if isinstance(event, dict) else {}
    return fields if isinstance(fields, dict) else {}


def observed_server_invasion(event):
    fields = fields_of(event)
    return (fields.get("role") == "server"
            and fields.get("template") in INVASION_TEMPLATES)



def number(event, key, default=-1):
    try:
        value = fields_of(event).get(key, default)
        return default if type(value) is bool else int(value)
    except (TypeError, ValueError, OverflowError, AttributeError):
        return default



CAPABILITY_KEYS = ("agents_it", "team_getter", "group_getter", "npc_getter",
                   "position_getter", "weapon_getter", "ammo_getter", "kills_getter")


def capability_snapshot(events: list[dict]) -> dict:
    """Availability of Lua bindings, distinct from actual measurement success."""
    record = next((ev for ev in reversed(events)
                   if ev.get("event") == "recorder_capabilities"), None)
    if record is None:
        return {"status": "unknown", "bindings": {k: "unknown" for k in CAPABILITY_KEYS},
                "limits": {}, "interpretation": "No capability declaration observed."}
    result = {}
    for key in CAPABILITY_KEYS:
        observed = number(record, key)
        result[key] = "binding_present" if observed == 1 else (
            "binding_absent" if observed == 0 else "unknown")
    return {
        "status": "declared", "bindings": result,
        "limits": {k: number(record, k) for k in
                   ("sampling_interval_s", "max_heartbeats", "max_defenders")},
        "interpretation": "Function binding presence is not proof a getter executed or yielded usable values.",
    }


def matrix_for_session(events: list[dict], findings: list[dict],
                       module: dict, logs: int, combat: dict) -> dict:
    events = [e for e in events if isinstance(e, dict)]
    types = Counter(e.get("event") for e in events)
    server = [e for e in events if e.get("event") == "heartbeat"
              and observed_server_invasion(e)]
    entries = [e for e in events if e.get("event") == "mission_enter"
               and observed_server_invasion(e)]
    city_entries = [e for e in entries if fields_of(e).get("scene") in CITY_SCENES]
    seen_waves = sorted({number(e, "wave") for e in server if number(e, "wave") >= 1})
    zombie_observed = any(number(e, "team1") > 0 for e in server)
    sampled_ai = combat.get("observability", {}).get("combat_samples", 0) > 0
    kills_observed = combat.get("observed_kill_increments", 0) > 0
    modes = [number(e, "mode") for e in events if e.get("event") == "tactical_change"]
    fallback_index = next((i for i, v in enumerate(modes) if v == 1), None)
    returned = (fallback_index is not None and any(v == 0 for v in modes[fallback_index + 1:]))
    err_codes = {f.get("id") for f in findings if isinstance(f, dict)}

    checks = {
        "engine_boot_event": ("observed" if types["boot"] else "unknown",
                              "WSE2 Lua boot marker"),
        "invasion_mission_entered": ("observed" if entries else "unknown",
                                     "explicit server-side multiplayer_iv entry marker"),
        "city_scene_observed": ("observed" if city_entries else "unknown",
                                "explicit server-side City invasion scene marker"),
        "zombies_visible": ("observed" if zombie_observed else "unknown",
                            "server invasion heartbeat with living team-1 count"),
        "wave_progression": ("observed" if len(seen_waves) >= 2 else "unknown",
                             "distinct server invasion heartbeat wave markers"),
        "reserved_ai_seen": ("observed" if sampled_ai else "unknown",
                             "AI-only division 5-7 combat samples"),
        "ai_kills_increased": ("observed" if kills_observed else "unknown",
                               "same-agent sampled kill counter increased"),
        "fallback_entered": ("observed" if fallback_index is not None else "unknown",
                              "tactical state switched to fallback"),
        "regroup_after_fallback": ("observed" if returned else "unknown",
                                   "tactical state switched back to hold"),
        "private_command_executed": ("observed" if types["command_exec"] else "unknown",
                                     "native command counter increased"),
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
            "experimental_map_scope": module.get("experimental_map_scope", "unknown"),
            "defender_loadout_profile": module.get("defender_loadout_profile", "unknown"),
            "experimental_defenders": module.get("experimental_defenders", "unknown"),
            "private_commands": (module.get("private_commands") or {}).get("enabled", False)
                                if isinstance(module.get("private_commands"), dict) else False,
        },
        "interpretation": ("Observed event markers support individual claims only. "
                           "Server invasion entry requires explicit role and template; "
                           "City scene also requires an explicit matching server scene. "
                           "Absent markers are unknown, not negative or gameplay proof."),
    }
