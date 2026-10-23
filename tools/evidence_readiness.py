"""Evidence-backed acceptance matrix for the final integrated WSE2 session.

Observations are deliberately not labelled 'passed' or 'failed': absence
of a recorded event may mean the game failed, the session was too short,
or the diagnostics API was unavailable.
"""
from collections import Counter


def number(event, key, default=-1):
    try:
        return int(event.get("fields", {}).get(key, default))
    except (TypeError, ValueError):
        return default


def matrix_for_session(events: list[dict], findings: list[dict],
                       module: dict, logs: int, combat: dict) -> dict:
    types = Counter(e.get("event") for e in events)
    server = [e for e in events if e.get("event") == "heartbeat"
              and e.get("fields", {}).get("role") == "server"]
    seen_waves = sorted({number(e, "wave") for e in server if number(e, "wave") >= 1})
    zombie_observed = any(number(e, "team1") > 0 for e in server)
    sampled_ai = combat.get("observability", {}).get("combat_samples", 0) > 0
    kills_observed = combat.get("observed_kill_increments", 0) > 0
    modes = [number(e, "mode") for e in events if e.get("event") == "tactical_change"]
    fallback_index = next((i for i, v in enumerate(modes) if v == 1), None)
    returned = (fallback_index is not None and any(v == 0 for v in modes[fallback_index + 1:]))
    err_codes = {f.get("id") for f in findings}

    checks = {
        "engine_boot_event": ("observed" if types["boot"] else "unknown",
                              "WSE2 Lua boot marker"),
        "invasion_mission_entered": ("observed" if types["mission_enter"] else "unknown",
                                     "multiplayer_iv entry marker"),
        "zombies_visible": ("observed" if zombie_observed else "unknown",
                            "server-side agent team-1 count"),
        "wave_progression": ("observed" if len(seen_waves) >= 2 else "unknown",
                             "distinct recorded invasion wave numbers"),
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
            "defender_loadout_profile": module.get("defender_loadout_profile", "unknown"),
            "experimental_defenders": module.get("experimental_defenders", "unknown"),
            "private_commands": (module.get("private_commands") or {}).get("enabled", False)
                                if isinstance(module.get("private_commands"), dict) else False,
        },
        "interpretation": "Observed events support individual claims only. Unknown is not failure. Final playability needs direct game verification.",
    }
