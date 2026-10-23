"""City-only forensic incident report; source facts never masquerade as gameplay.

Consumes ALREADY VERIFIED diagnostics bundle data. It does not open original
assets, run WSE2, infer absent values as zero, upload or read game memory.
The two timelines are independent: ZDB1 lines have source/line ordering while
C's recorder uses wall-clock UTC. Never manufacture global chronology.
"""
from __future__ import annotations

from collections import Counter
import re

SCHEMA = "zombieee.city-incident.v1"
CITY = "tbfc_invasion_4"
CITY_RE = re.compile(r"(?:scn_)?tbfc_invasion_[1-5]\Z")
LOG_RE = re.compile(r"logs/log_[0-9]{2}\.txt\Z")
TRACKED = {
    "boot", "mission_enter", "heartbeat", "wave_change", "tactical_change",
    "combat_sample", "command_exec", "recorder_capabilities", "probe_failed",
}
RECORDER_TRACKED = {
    "recorder_ready", "recorder_listening", "process_attached", "control_rejected",
    "log_rotated", "log_limit", "log_unavailable", "process_started",
    "process_finished", "process_start_failed",
}
MAX_TRACKED = 96
MAX_OBSERVATIONS = 50000
MAX_SOURCES = 25


def measured(value, *, minimum=0, maximum=1000000):
    """Strict integer observation; no bools, floats, -1 or 'unknown'."""
    if type(value) is bool or value is None:
        return None
    if type(value) is int:
        parsed = value
    elif isinstance(value, str) and re.fullmatch(r"-?[0-9]{1,12}", value):
        parsed = int(value)
    else:
        return None
    return parsed if minimum <= parsed <= maximum else None


def source_reference(event):
    """No client-supplied paths or log excerpts in a published timeline."""
    src = event.get("source")
    return src if isinstance(src, str) and LOG_RE.fullmatch(src) else "unattributed_log"


def clean_scene(value):
    if not isinstance(value, str) or not CITY_RE.fullmatch(value):
        return None
    return value.removeprefix("scn_")


def bounded_source(items, limit=MAX_OBSERVATIONS):
    """Inspect beginning and end of long input, accounting for missing middle."""
    if len(items) <= limit:
        return items, 0
    early = max(1, limit // 4)
    return items[:early] + items[-(limit - early):], len(items) - limit


def limited_timeline(items, limit=MAX_TRACKED):
    """Preserve early boot and late crash/exit while making dropped count explicit."""
    if len(items) <= limit:
        return items, 0
    head = max(1, limit // 4)
    return items[:head] + items[-(limit - head):], len(items) - limit


def build_status(installed):
    """Allowlist path-free build evidence; never treat source as runtime."""
    output = {"city_scope": installed.get("experimental_map_scope") == "city-only",
              "static": "unknown", "final": "unknown",
              "original_invasion_game_type": None,
              "source_receipt_claims_passed": False,
              "independently_reverified": False, "game_runtime": "unknown",
              "round_aware_source_contract_verified": False}
    static = installed.get("city_static_acceptance")
    if isinstance(static, dict):
        checks = static.get("checks")
        summary_keys = ("check_count", "passed_checks", "failed_checks", "checks_valid")
        # The ZIP collector removes individual check names and keeps ONE
        # aggregate bit. That bit is NOT the number of source audit checks.
        summarized = (any(key in static for key in summary_keys)
                      or isinstance(checks, dict) and "all_checks_passed" in checks)
        if summarized:
            count = measured(static.get("check_count"), minimum=1, maximum=100)
            passed = measured(static.get("passed_checks"), minimum=0, maximum=100)
            failed = measured(static.get("failed_checks"), minimum=0, maximum=100)
            collapsed = (checks.get("all_checks_passed")
                         if isinstance(checks, dict) else None)
            consistent = (
                count is not None and passed is not None and failed is not None
                and passed + failed == count
                and static.get("checks_valid") is True
                and isinstance(checks, dict)
                and set(checks) == {"all_checks_passed"}
                and type(collapsed) is bool
                and collapsed is (failed == 0)
            )
            output["static_summary_consistent"] = consistent
            if consistent:
                output["static_check_count"] = count
                output["static_passed_checks"] = passed
                output["static_failed_checks"] = failed
                output["static"] = ("source_checked" if failed == 0
                                    else "source_check_failed")
            else:
                # Invalid/missing/inconsistent counters cannot become source proof.
                output["static"] = "source_check_failed"
                output["static_check_count"] = None
                output["static_failed_checks"] = None
        elif isinstance(checks, dict):
            # Direct, non-collected synthetic inputs can carry original checks.
            # Still bound size and require actual booleans, never truthiness.
            valid = bool(checks) and len(checks) <= 100 and all(
                type(value) is bool for value in checks.values())
            output["static"] = ("source_checked" if valid and all(checks.values())
                                else "source_check_failed")
            output["static_check_count"] = len(checks) if valid else None
            output["static_failed_checks"] = (sum(value is False for value in checks.values())
                                               if valid else None)
        gtype = measured(static.get("original_invasion_game_type"), maximum=20)
        output["original_invasion_game_type"] = gtype
    final = installed.get("city_final_acceptance")
    if isinstance(final, dict):
        verdict = final.get("passed")
        output["final"] = ("source_checked" if verdict is True else
                           "source_check_failed" if verdict is False else "unknown")
        mode = final.get("control_mode")
        if mode in ("none", "solo-assist", "private-commands", "invalid"):
            output["control_mode"] = mode
    output["source_receipt_claims_passed"] = (output["city_scope"]
                                 and output["static"] == "source_checked"
                                 and output["final"] == "source_checked"
                                 and output["original_invasion_game_type"] == 7)
    return output


def incident_for_session(events, recorder_events, installed, flight, findings,
                         scene_evidence=None, logs=None):
    """Evidence-led narrative without pretending that game telemetry has a clock."""
    events = events if isinstance(events, list) else []
    recorder_events = recorder_events if isinstance(recorder_events, list) else []
    installed = installed if isinstance(installed, dict) else {}
    flight = flight if isinstance(flight, dict) else {}
    scene_evidence = scene_evidence if isinstance(scene_evidence, dict) else {}
    findings = findings if isinstance(findings, list) else []
    logs = logs if isinstance(logs, dict) else {}
    build = build_status(installed)
    log_entries = []
    waves = set()
    wave_sequence = {}
    teams = {"allies_max": None, "zombies_max": None}
    mode_seen = set()
    refilled = set()
    # Native round identities must be read from WSE2 runtime globals.
    # "round" alone is g_round_ended (boolean), NOT a round identity.
    rounds = set()
    reinforced_rounds = set()
    waves_in_round = {}
    observed_scenes = set()
    observed_server_mission = False
    observed_boot = False
    combat_sample_count = 0
    commands = 0
    suspected_wave_regression = False

    engine_input, engine_unread = bounded_source(events)
    recorder_input, recorder_unread = bounded_source(recorder_events)
    for event in engine_input:
        if not isinstance(event, dict):
            continue
        kind = event.get("event")
        if kind not in TRACKED:
            continue
        fields = event.get("fields") or {}
        if not isinstance(fields, dict):
            continue
        source = source_reference(event)
        line = measured(event.get("line"), minimum=1)
        observed_boot |= kind == "boot"
        is_server = fields.get("role") == "server"
        if kind == "mission_enter" and is_server:
            observed_server_mission = True
        if kind in ("heartbeat", "mission_enter") and is_server:
            scene = clean_scene(fields.get("scene"))
            if scene is not None:
                observed_scenes.add(scene)
        point = {"kind": kind, "source": source, "line": line,
                 "clock": "log_line_order_only"}
        for key in ("wave", "mode", "refilled", "team0", "team1", "count"):
            minimum = 0 if key not in ("team0", "team1") else 0
            val = measured(fields.get(key), minimum=minimum)
            if val is not None:
                point[key] = val
        if kind in ("heartbeat", "mission_enter") and is_server:
            point["role"] = "server"
            for key, target in (("team0", "allies_max"), ("team1", "zombies_max")):
                v = measured(fields.get(key))
                if v is not None:
                    teams[target] = max(v, teams[target]) if teams[target] is not None else v
        # wave_change was server-only in the old Lua probe (and is now
        # explicitly role=server). Do not accept optional round identities
        # from unauthenticated client-side events.
        server_wave = kind == "wave_change" and fields.get("role") in (None, "server")
        # Legacy Lua wave_change had no role; retain its low-confidence wave
        # marker for backwards compatibility, but NEVER elevate its optional
        # round_start fields into high-confidence server global observations.
        round_sample = (kind in ("mission_enter", "heartbeat", "wave_change")
                        and is_server)
        round_start = measured(fields.get("round_start")) if round_sample else None
        reinforced_round_start = (
            measured(fields.get("refilled_round_start")) if round_sample else None)
        if round_start is not None:
            rounds.add(round_start)
            point["round_start"] = round_start
        if reinforced_round_start is not None:
            reinforced_rounds.add(reinforced_round_start)
            point["refilled_round_start"] = reinforced_round_start
        if kind in ("heartbeat", "wave_change") and (is_server or server_wave):
            wave = measured(fields.get("wave"), minimum=1)
            if wave is not None:
                waves.add(wave)
                if round_start is not None:
                    waves_in_round.setdefault(round_start, set()).add(wave)
                # A's original mission resets wave_number at round changes.
                # A lower wave in the SAME observed round is suspicious;
                # a lower wave with an observed new round is normal.
                # Missing round identity leaves only a noncausal candidate.
                prev = wave_sequence.get(source)
                if (prev is not None and wave < prev[0]
                        and not (prev[1] is not None
                                 and round_start is not None
                                 and prev[1] != round_start)):
                    suspected_wave_regression = True
                wave_sequence[source] = (wave, round_start)
        if kind in ("heartbeat", "tactical_change") and (is_server or kind == "tactical_change"):
            mode = measured(fields.get("mode"), maximum=1)
            if mode is not None:
                mode_seen.add(mode)
        if kind == "heartbeat" and is_server:
            fill = measured(fields.get("refilled"), minimum=1)
            if fill is not None:
                refilled.add(fill)
        if kind == "combat_sample":
            combat_sample_count += 1
            # No fabricated kills or movement; the detailed combat analyzer
            # owns paired observations and its per-wave ID reuse caveats.
            if "kills" in fields:
                point["kills"] = measured(fields.get("kills"))
        if kind == "command_exec":
            commands += 1
        if kind == "mission_enter" and is_server:
            scene = clean_scene(fields.get("scene"))
            if scene:
                point["scene"] = scene
        if kind == "tactical_change" and "mode" in point:
            point["mode_name"] = "fallback" if point["mode"] == 1 else "hold"
        # All other field names and client strings are dropped.
        log_entries.append(point)

    recorder_entries = []
    for event in recorder_input:
        if not isinstance(event, dict) or event.get("event") not in RECORDER_TRACKED:
            continue
        point = {"kind": event["event"], "clock": "recorder_utc"}
        utc = event.get("utc")
        if isinstance(utc, str) and re.fullmatch(r"[0-9T:+.\-Z]{16,40}", utc):
            point["utc"] = utc
        for key in ("log_index", "omitted_bytes", "claimed_process_count"):
            v = measured(event.get(key))
            if v is not None:
                point[key] = v
        # Known machine-generated reason labels, never unbounded diagnostics text.
        reason = event.get("reason")
        if reason in ("invalid_mac", "ValueError", "unsafe_file", "invalid_pid",
                      "pid_reuse_suspected", "game_process_not_confirmed_exited"):
            point["reason"] = reason
        recorder_entries.append(point)

    log_timeline, log_omitted = limited_timeline(log_entries)
    recorder_timeline, recorder_omitted = limited_timeline(recorder_entries)
    codes = {x.get("id") for x in findings if isinstance(x, dict)}
    log_gap = any("ZDB1-OMITTED" in v or "ZDB1-TRUNCATED" in v for v in logs.values())
    omitted_sizes = flight.get("log_omitted_bytes")
    receipt_gap = (any(measured(v, minimum=1) is not None for v in omitted_sizes)
                   if isinstance(omitted_sizes, list) else False)
    dropped_events = measured(flight.get("event_drops"), minimum=1) is not None
    gap = (log_gap or receipt_gap or dropped_events or log_omitted > 0
           or engine_unread > 0 or recorder_unread > 0)

    # Each distinct (round, wave) is counted once, linear in bounded input.
    round_frequency = Counter(wave for markers in waves_in_round.values()
                              for wave in markers)
    repeated_across_rounds = sorted(
        wave for wave, count in round_frequency.items() if count >= 2)
    within_round_progress = any(len(seen) >= 2 for seen in waves_in_round.values())
    runtime = {
        "boot": "observed_marker" if observed_boot else "unknown",
        "server_city_entry": ("observed_marker" if observed_server_mission and CITY in observed_scenes
                              else "unknown"),
        "server_mission_entry": "observed_marker" if observed_server_mission else "unknown",
        "scene": (sorted(observed_scenes) if observed_scenes else None),
        "wave_numbers": sorted(waves), "wave_progression":
            "observed_markers" if len(waves) >= 2 else "unknown",
        "last_reinforced_waves": sorted(refilled) if refilled else None,
        "round_start_observations": sorted(rounds)[:24] if rounds else None,
        "round_start_observation_count": len(rounds),
        "last_reinforced_round_starts": (
            sorted(reinforced_rounds)[:24] if reinforced_rounds else None),
        "round_identity": "observed_engine_global" if rounds else "unknown",
        "round_aware_reinforcement_verified": False,
        "wave_progression_within_one_round": (
            "observed_markers" if within_round_progress else "unknown"),
        "repeated_wave_across_distinct_rounds": (
            repeated_across_rounds[:24] if rounds else None),
        "tactical_modes": sorted(mode_seen) if mode_seen else None,
        "survivor_team0_max": teams["allies_max"],
        "zombie_team1_max": teams["zombies_max"],
        "reserved_combat_sample_count": combat_sample_count,
        "command_execution_markers": commands,
        "gameplay_verified": False,
    }
    if flight.get("simulation") is True:
        runtime["simulation"] = True
    elif flight.get("simulation") is False:
        runtime["simulation"] = False
    else:
        runtime["simulation"] = "unknown"

    leads = []
    def add(code, title, evidence, confidence, next_step):
        leads.append({"code": code, "title": title, "evidence": evidence,
                      "confidence": confidence, "next_step": next_step,
                      "cause": "unknown"})
    if "R002" in codes:
        add("CITY-I01", "Fatal text pattern in bounded log",
            ["diagnostics:R002"], "direct_text_match_cause_unknown",
            "Inspect local original crash context, then compare native/engine versions")
    if flight.get("outcome") in ("timeout", "interrupted", "start_failed"):
        add("CITY-I02", "Recorder did not finish an ordinary session",
            ["flight_recorder.json:outcome"], "recorder_receipt_only",
            "Inspect local incomplete snapshots; never infer game process failure")
    if gap:
        add("CITY-I03", "Telemetry has omitted or unobserved intervals",
            ["recording_gap_or_bounded_timeline"], "missing_evidence_known",
            "Avoid asserting event absence across the gap")
    if suspected_wave_regression:
        add("CITY-I04", "Wave number decreased without a measured new round",
            ["ZDB1:wave"], "sampled_sequence_cause_unknown",
            "Check intentional wave restart, rematch and stale log concatenation")
    if build["static"] == "source_check_failed" or build["final"] == "source_check_failed":
        add("CITY-I05", "City source integrity check failed",
            ["module.json:city_acceptance"], "source_receipt_only",
            "Rebuild from pinned original with A's verifier before runtime testing")
    if build["original_invasion_game_type"] not in (None, 7):
        add("CITY-I06", "Recorded source invasion game type differs from 7",
            ["module.json:city_static_acceptance.original_invasion_game_type"],
            "source_receipt_only", "Rerun A's latest source-native City audit")
    if "R029" in codes or (build["city_scope"] and observed_scenes
                            and any(v != CITY for v in observed_scenes)):
        add("CITY-I07", "Observed scene differs from City-only scope",
            ["ZDB1:server.scene", "module.json:experimental_map_scope"],
            "runtime_marker_vs_source_scope_cause_unknown",
            "Verify loaded scene getter, module selection and session correlation")

    unknowns = []
    if not rounds:
        unknowns.append("round_start_global_unobserved")
    if not reinforced_rounds:
        unknowns.append("last_reinforced_round_start_global_unobserved")
    if runtime["scene"] is None:
        unknowns.append("actual_runtime_scene_unobserved")
    if len(waves) < 2:
        unknowns.append("complete_wave_progression_unverified")
    if teams["allies_max"] is None:
        unknowns.append("survivor_team_measurement_unavailable")
    if combat_sample_count == 0:
        unknowns.append("reserved_defender_combat_unobserved")
    if not observed_server_mission:
        unknowns.append("server_mission_entry_unobserved")
    if flight.get("exit_code_observed") is not True:
        unknowns.append("game_process_exit_code_unknown")
    if runtime["simulation"] is True:
        unknowns.append("synthetic_session_not_gameplay")
    if not build["source_receipt_claims_passed"]:
        unknowns.append("complete_city_static_and_final_source_receipts_unavailable")
    if gap:
        unknowns.append("truncated_or_missing_observation_intervals")
    if scene_evidence.get("status") == "mismatch_observed" and not any(
            x["code"] == "CITY-I07" for x in leads):
        unknowns.append("scene_evidence_conflict_review_needed")
    return {
        "schema": SCHEMA, "scope": "city_only", "build": build,
        "runtime": runtime, "incident_leads": leads,
        "unknowns": sorted(set(unknowns)), "recording_gap": gap,
        "timeline": {
            "engine": {"ordering": "per_file_line_only",
                       "events": log_timeline, "omitted_middle": log_omitted,
                       "uninspected_input_records": engine_unread},
            "recorder": {"ordering": "recorder_utc_only",
                         "events": recorder_timeline, "omitted_middle": recorder_omitted,
                         "uninspected_input_records": recorder_unread},
            "cross_lane_order": "unknown_without_shared_clock",
        },
        "privacy": {"raw_paths": False, "raw_log_excerpts": False,
                    "manual_review_required": True},
        "caveat": ("Incident leads are source-backed hypotheses, not causal findings. "
                   "Installer source receipts are claims unless independently replayed; " 
                   "build static checks are not WSE2 runtime observations. "
                   "Log-source order and recorder UTC are not a common clock. "
                   "Wave resets may be legitimate new rounds; source contracts "
                   "cannot substitute for instrumented round globals."),
    }
