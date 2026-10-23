#!/usr/bin/env python3
"""Retrospective AI combat and private-command diagnostics for ZDB1 events.

Read-only, missing metrics remain unknown. Agent IDs may be reused across
respawns; individual combat progress is evaluated within one wave only.
"""
from collections import defaultdict


def integer(fields, key, default=-1):
    try:
        return int(fields.get(key, default))
    except (TypeError, ValueError, OverflowError):
        return default


def analyze_combat_events(events, installed):
    samples = defaultdict(list)
    heartbeats = {}
    command_events = []
    for record in events:
        event = record.get("event")
        values = record.get("fields", {})
        if event == "heartbeat" and values.get("role") == "server":
            tick = integer(values, "count")
            if tick > 0:
                heartbeats[tick] = {"wave": integer(values, "wave"),
                                    "zombies": integer(values, "team1")}
        elif event == "combat_sample":
            tick, agent, group, wave = (integer(values, k) for k in
                                        ("tick", "id", "group", "wave"))
            if not (tick > 0 and 0 <= agent < 10000 and 5 <= group <= 7):
                continue
            sample = {"tick": tick, "agent": agent, "group": group, "wave": wave,
                      "kills": integer(values, "kills"),
                      "ammo": integer(values, "ammo"),
                      "weapon": integer(values, "weapon")}
            samples[(wave, agent, group)].append(sample)
        elif event == "command_exec":
            command_events.append({
                "command": str(values.get("cmd", ""))[:40],
                "count": integer(values, "count"),
                "delta": integer(values, "delta"),
            })

    findings = []
    observed = [record for series in samples.values() for record in series]
    known_kills = sum(r["kills"] >= 0 for r in observed)
    known_ammo = sum(r["ammo"] >= 0 for r in observed)
    known_weapon = sum(r["weapon"] >= 0 for r in observed)
    positive_kill_steps = 0
    dry_agents = []
    for key, series in samples.items():
        series.sort(key=lambda r: r["tick"])
        prior, empty_streak, dry_ticks = None, 0, []
        for rec in series:
            if (prior is not None and rec["kills"] >= 0 and prior["kills"] >= 0
                    and rec["kills"] > prior["kills"]):
                positive_kill_steps += rec["kills"] - prior["kills"]
            zombies_present = heartbeats.get(rec["tick"], {}).get("zombies", -1) > 0
            if (zombies_present and rec["ammo"] == 0 and rec["weapon"] >= 0
                    and (prior is None or rec["tick"] == prior["tick"] + 1)):
                empty_streak += 1
                dry_ticks.append(rec["tick"])
            else:
                empty_streak = 1 if zombies_present and rec["ammo"] == 0 and rec["weapon"] >= 0 else 0
                dry_ticks = [rec["tick"]] if empty_streak else []
            if empty_streak >= 3:
                dry_agents.append({"agent": key[1], "group": key[2], "wave": key[0],
                                   "ticks": dry_ticks[-3:]})
                break
            prior = rec
    if dry_agents:
        findings.append({
            "id": "R023", "severity": "medium", "title": "Defender may be out of ammunition",
            "action": "A reserved AI defender has zero observed ammo across at least three consecutive samples with zombies present and a valid weapon ID. Verify ammunition compatibility, reloads and resupply.",
            "examples": dry_agents[:5],
        })

    active_ticks = sorted({
        r["tick"] for r in observed
        if r["kills"] >= 0 and heartbeats.get(r["tick"], {}).get("zombies", -1) > 0
    })
    active_agents = {
        (r["agent"], r["group"]) for r in observed
        if r["kills"] >= 0 and r["tick"] in active_ticks
    }
    if len(active_ticks) >= 6 and len(active_agents) >= 2 and positive_kill_steps == 0:
        findings.append({
            "id": "R024", "severity": "medium",
            "title": "No observed AI kills across an extended engagement",
            "action": "At least two observed defenders and hostile bots were present during six samples without any recorded increase in kill count. This may reflect cover, low difficulty, missed intervals or agent-ID reuse; inspect actual combat footage.",
        })

    enabled = isinstance(installed.get("private_commands"), dict) and (
        installed["private_commands"].get("enabled") is True)
    if command_events and not enabled:
        findings.append({
            "id": "R025", "severity": "high",
            "title": "Command execution markers disagree with build manifest",
            "action": "Private-command events appear even though the manifest does not enable them. Check stale/mixed logs, module selection and build provenance before treating commands as authorised.",
        })

    if installed.get("experimental_defenders") and heartbeats and not observed:
        findings.append({
            "id": "R026", "severity": "medium",
            "title": "AI combat telemetry unavailable",
            "action": "The session has server heartbeats but no reserved-defender combat samples. Check WSE2 operation/header availability, recorder logs and whether defenders actually spawned; do not infer zero kills or ammo.",
        })

    return {
        "observability": {
            "combat_samples": len(observed),
            "observed_agent_waves": len(samples),
            "known_kill_samples": known_kills,
            "known_ammo_samples": known_ammo,
            "known_weapon_samples": known_weapon,
            "available": bool(observed),
        },
        "observed_kill_increments": positive_kill_steps,
        "potentially_empty_ammo_agents": len(dry_agents),
        "confirmed_command_events": command_events[:80],
        "findings": findings,
        "caveat": "These are sampled signals. No recorded kill is not proof that the AI did not shoot or engage.",
    }
