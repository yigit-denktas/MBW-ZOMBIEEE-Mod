#!/usr/bin/env python3
"""Offline ZOMBIEEE diagnostics: collect redacted logs, verify hashes, triage evidence.

No network I/O, elevation, process injection, or game-control operations.
Python 3.10+, standard library only. All published evidence is opt-in.
"""
from __future__ import annotations
import argparse
from collections import Counter
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import platform
import re
import sys
import zipfile
from tactical_analysis import analyze_tactical_events
from combat_analysis import analyze_combat_events
from evidence_readiness import matrix_for_session, capability_snapshot

SCHEMA = 1
MAX_LOG_BYTES = 8 * 1024 * 1024
HEAD_LOG_BYTES = 256 * 1024
MAX_FILES = 25
EVENT_PREFIX = "ZDB1|"
LOG_NAMES = ("rgl_log.txt", "wse2_log.txt", "server_log.txt", "server_config.log", "crash.log")


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def scrub(text: str) -> str:
    """Best-effort privacy filters; cannot guarantee removal of custom player names."""
    text = re.sub(r"(?im)^\s*(set_pass_admin|password|passwd|token|api[_-]?key|auth[_-]?token)\s*(?:[:=]|\s)\s*\S+.*$",
                  r"\1 <REDACTED>", text)
    text = re.sub(r"(?i)\b(?:[a-z]:\\Users\\|/Users/|/home/)[^\\/\s\"']+", "<USER_HOME>", text)
    text = re.sub(r"(?i)\b(?:steam[_ -]?id|steamid)\s*[:=]?\s*\d{8,20}", "SteamID:<REDACTED>", text)
    text = re.sub(r"(?<!\d)7656119\d{10}(?!\d)", "<STEAM_ID>", text)
    text = re.sub(r"\b[A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Za-z]{2,}\b", "<EMAIL>", text)
    text = re.sub(r"(?<![\d.])(?:\d{1,3}\.){3}\d{1,3}(?::\d{1,5})?(?![\d.])", "<IP_ADDRESS>", text)
    text = re.sub(r"(?i)\b(?:Bearer\s+)[A-Za-z0-9._~+/\-]{12,}", "Bearer <REDACTED>", text)
    return text


def privacy_audit(payload: dict[str, bytes]) -> dict:
    """Heuristic disclosure check. Clean matches NEVER mean safe to publish."""
    patterns = {
        "email": re.compile(r"\b[A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Za-z]{2,}\b"),
        "ipv4": re.compile(r"(?<![\d.])(?:\d{1,3}\.){3}\d{1,3}(?![\d.])"),
        "steam_id": re.compile(r"(?<!\d)7656119\d{10}(?!\d)"),
        "home_path": re.compile(r"(?i)(?:[a-z]:\\Users\\|/Users/|/home/)[^\s]+"),
        "credential_label": re.compile(r"(?i)\b(?:api[_-]?key|auth[_-]?token|authorization|password|passwd)\b\s*[:=]\s*(?!<REDACTED>)\S+"),
    }
    counts = {key: 0 for key in patterns}
    for name, data in payload.items():
        if name == "manifest.json" or name == "module_hashes.json":
            continue
        if not (name.endswith(".txt") or name.endswith(".json") or name.endswith(".jsonl")):
            continue
        decoded = data.decode("utf-8", errors="replace")
        for key, pattern in patterns.items():
            counts[key] += len(pattern.findall(decoded))
    return {"automatic_review": "potential_disclosure" if any(counts.values()) else "no_known_patterns_found",
            "manual_review_required": True,
            "potential_patterns": counts,
            "caveat": "Pattern checks and redaction are not exhaustive. Do not publish raw logs or assume a clean scan guarantees privacy."}


def candidate_logs(game_root: Path | None, extra: list[Path]) -> list[Path]:
    bases: list[Path] = []
    if game_root:
        bases += [game_root, game_root / "Logs", game_root / "WSE2", game_root / "WSE2" / "Logs"]
    userhome = Path.home()
    doc = userhome / "Documents"
    bases += [doc / "Mount&Blade Warband WSE2", doc / "Mount&Blade Warband WSE2" / "Logs",
              doc / "Mount&Blade Warband", doc / "Mount&Blade Warband" / "Logs"]
    if os.environ.get("USERPROFILE"):
        doc = Path(os.environ["USERPROFILE"]) / "Documents"
        bases += [doc / "Mount&Blade Warband WSE2", doc / "Mount&Blade Warband WSE2" / "Logs",
                  doc / "Mount&Blade Warband", doc / "Mount&Blade Warband" / "Logs"]
    if os.environ.get("APPDATA"):
        bases += [Path(os.environ["APPDATA"]) / "Mount&Blade Warband WSE2"]
    options = [base / name for base in bases for name in LOG_NAMES]
    options += extra
    found, seen = [], set()
    for path in options:
        try:
            resolved = path.expanduser().resolve()
            if resolved.is_file() and resolved not in seen:
                found.append(resolved)
                seen.add(resolved)
        except (OSError, RuntimeError):
            pass
    return found[:MAX_FILES]


def extract_events(log: str, log_file: str) -> list[dict]:
    events = []
    for line_num, line in enumerate(log.splitlines(), 1):
        idx = line.find(EVENT_PREFIX)
        if idx < 0:
            continue
        raw = line[idx + len(EVENT_PREFIX):].strip()
        parts = raw.split("|")
        if not parts or not re.fullmatch(r"[a-z][a-z0-9_]{0,40}", parts[0]):
            continue
        fields = {}
        for part in parts[1:]:
            if "=" not in part:
                continue
            key, value = part.split("=", 1)
            if re.fullmatch(r"[a-z][a-z0-9_]{0,31}", key):
                fields[key] = value[:128]
        events.append({"event": parts[0], "fields": fields, "source": log_file, "line": line_num})
    return events



def verified_flight(root: Path) -> tuple[dict, list[Path], bytes]:
    """Read C's completed, hashed external recorder without trusting paths."""
    root = root.expanduser().resolve()
    manifest = json.loads((root / "manifest.json").read_text(encoding="utf-8"))
    if manifest.get("schema") != "zombieee.flight.v1":
        raise ValueError("Unknown flight-recorder schema")
    hashes = manifest.get("sha256")
    if not isinstance(hashes, dict) or len(hashes) > 20:
        raise ValueError("Invalid flight-recorder manifest")
    actual = {str(p.relative_to(root)).replace(os.sep, "/")
              for p in root.rglob("*") if p.is_file() and not p.name.endswith(".tmp")
              and p.name != "manifest.json"}
    if set(hashes) != actual or "recorder.json" not in hashes:
        raise ValueError("Flight-recorder entry mismatch")
    total_bytes = 0
    for name, expected in hashes.items():
        if (not isinstance(name, str) or name.startswith("/")
                or "\\" in name or ".." in Path(name).parts):
            raise ValueError("Unsafe flight-recorder path")
        file = root / name
        if file.is_symlink() or not file.is_file():
            raise ValueError("Unsafe flight-recorder file: " + name)
        size = file.stat().st_size
        total_bytes += size
        if size > MAX_LOG_BYTES or total_bytes > 12 * MAX_LOG_BYTES + 4 * 1024 * 1024:
            raise ValueError("Flight-recorder size exceeds safety limit")
        if sha256(file.read_bytes()) != expected:
            raise ValueError("Flight-recorder integrity failure: " + name)
    receipt = json.loads((root / "recorder.json").read_text(encoding="utf-8"))
    if receipt.get("schema") != "zombieee.flight.v1":
        raise ValueError("Flight-recorder receipt mismatch")
    public = {k: receipt.get(k) for k in (
        "schema", "session_id", "start_utc", "end_utc", "outcome", "exit_code",
        "exit_code_observed", "log_count", "log_truncated",
        "log_bytes_limit_each", "event_count", "event_drops", "metrics",
        "launcher", "caveat")}
    # No original command line, source paths, PIDs or raw process data.
    safe = json.dumps(public, indent=2, sort_keys=True)
    logs = sorted((root / "logs").glob("log_*.txt"))
    events = (root / "events.jsonl").read_bytes() if "events.jsonl" in hashes else b""
    return public, logs, scrub(events.decode("utf-8", errors="replace")).encode("utf-8")


def collect(game_root: Path | None, module: Path | None, output: Path,
            extra_logs: list[Path], session: str = "final-check",
            flight_root: Path | None = None) -> dict:
    if not re.fullmatch(r"[A-Za-z0-9_.-]{1,64}", session):
        raise ValueError("Invalid session label")
    output = output.expanduser().resolve()
    if output.suffix.lower() != ".zip":
        raise ValueError("Output path must end with .zip")
    output.parent.mkdir(parents=True, exist_ok=True)
    if output.exists():
        raise FileExistsError("Evidence ZIP already exists: " + str(output))
    entries: dict[str, bytes] = {}
    flight = None
    flight_events = b""
    if flight_root is not None:
        flight, recorder_logs, flight_events = verified_flight(flight_root)
        # Final-session snapshots are trusted for time window, not historical
        # auto-discovery. Include only these and explicitly opted-in extras.
        sources, seen = [], set()
        for path in [*recorder_logs, *extra_logs]:
            try:
                candidate = path.expanduser().resolve()
                if candidate.is_file() and candidate not in seen:
                    sources.append(candidate)
                    seen.add(candidate)
            except (OSError, RuntimeError):
                pass
        sources = sources[:MAX_FILES]
    else:
        sources = candidate_logs(game_root, extra_logs)
    if flight is not None:
        entries["flight_recorder.json"] = (json.dumps(flight, indent=2, sort_keys=True) + "\n").encode()
        entries["flight_events.jsonl"] = flight_events
    if module:
        marker = module / "ZOMBIEEE_REMASTER.json"
        if marker.is_file():
            try:
                parsed = json.loads(marker.read_text(encoding="utf-8"))
                safe = {k: parsed.get(k) for k in (
                    "remaster_version", "source_archive_sha256", "target", "runtime_verified",
                    "archive_crc_verified", "original_mission_trigger_count", "final_trigger_count",
                    "defender_loadout_profile", "difficulty")}
                assist = parsed.get("solo_assist")
                if isinstance(assist, dict):
                    safe["solo_assist"] = {
                        "enabled": assist.get("enabled") is True,
                        "solo_only": assist.get("solo_only") is True,
                        "host_only": assist.get("host_only") is True,
                        "period_seconds": assist.get("period_seconds"),
                    }
                else:
                    safe["solo_assist"] = None
                clones = parsed.get("ai_only_loadout_clones")
                if isinstance(clones, dict):
                    safe["ai_loadout_clone_count"] = clones.get("patched_count", 981) - 981
                private = parsed.get("private_commands")
                if isinstance(private, dict):
                    safe["private_commands"] = {"enabled": private.get("enabled") is True,
                        "server_only": private.get("server_only") is True,
                        "dedicated_allowed": private.get("dedicated_allowed"),
                        "max_active_players": private.get("max_active_players")}
                params = parsed.get("difficulty_parameters")
                if isinstance(params, dict):
                    safe["difficulty_parameters"] = {
                        key: params.get(key) for key in
                        ("first_reinforcement_wave", "fallback_at_or_below",
                         "regroup_at_or_above")}
                defender = parsed.get("experimental_defender_patch")
                if isinstance(defender, dict):
                    safe["experimental_defenders"] = defender.get("experimental_defenders")
                preflight = parsed.get("preflight")
                if isinstance(preflight, dict):
                    safe["preflight_ok"] = preflight.get("ok")
                    mission = preflight.get("mission") or {}
                    safe["original_trigger_count"] = mission.get("triggers")
                tactical = parsed.get("experimental_tactical_recovery")
                if isinstance(tactical, dict):
                    safe["tactical_recovery"] = {
                        key: tactical.get(key) for key in
                        ("enabled", "low_water", "high_water", "fallback_entry", "reevaluation_seconds")
                    }
                entries["module.json"] = (json.dumps(safe, indent=2, sort_keys=True) + "\n").encode()
            except (OSError, ValueError, TypeError):
                pass
    if module:
        fingerprints = {}
        for name in ("module.ini", "mission_templates.txt", "troops.txt", "scripts.txt",
                     "variables.txt", "lua/main.lua",
                     *(f"SceneObj/scn_tbfc_invasion_{i}.sco" for i in range(1, 6))):
            candidate = module / name
            if candidate.is_file():
                with candidate.open("rb") as file_handle:
                    fingerprints[name] = sha256(file_handle.read())
        if fingerprints:
            entries["module_hashes.json"] = (json.dumps(fingerprints, indent=2, sort_keys=True) + "\n").encode()
    fileinfo = []
    for i, path in enumerate(sources):
        with path.open("rb") as fh:
            fh.seek(0, 2)
            length = fh.tell()
            if length > MAX_LOG_BYTES:
                fh.seek(0)
                head = fh.read(HEAD_LOG_BYTES)
                fh.seek(length - (MAX_LOG_BYTES - HEAD_LOG_BYTES))
                tail = fh.read(MAX_LOG_BYTES - HEAD_LOG_BYTES)
                gap = length - MAX_LOG_BYTES
                data = head + (f"\n[ZDB1-TRUNCATED {gap} BYTES BETWEEN HEAD AND TAIL]\n").encode() + tail
            else:
                fh.seek(0)
                data = fh.read()
        text = scrub(data.decode("utf-8-sig", errors="replace"))
        stored = f"logs/log_{i+1:02d}.txt"
        entries[stored] = text.encode("utf-8")
        fileinfo.append({"file": stored, "source_kind": path.name.lower() if path.name.lower() in LOG_NAMES else "custom_log",
                         "original_bytes": length, "truncation": "head_and_tail" if length > MAX_LOG_BYTES else "none",
                         "modified_utc": datetime.fromtimestamp(path.stat().st_mtime, timezone.utc).isoformat()})
    event_records = []
    for info in fileinfo:
        event_records.extend(extract_events(entries[info["file"]].decode("utf-8"), info["file"]))
    entries["events.jsonl"] = ("".join(json.dumps(v, sort_keys=True) + "\n" for v in event_records)).encode()
    metadata = {"schema": SCHEMA, "session": session,
                "captured_utc": datetime.now(timezone.utc).isoformat(),
                "environment": {"os": platform.system(), "release": platform.release(),
                                "architecture": platform.machine(), "python": platform.python_version()},
                "files": fileinfo, "event_count": len(event_records),
                "raw_logs_included": False, "network_upload": False,
                "privacy": "Best-effort redaction; inspect any bundle before sharing."}
    entries["session.json"] = (json.dumps(metadata, indent=2, sort_keys=True) + "\n").encode()
    manifest = {"schema": SCHEMA, "sha256": {k: sha256(v) for k, v in sorted(entries.items())}}
    entries["manifest.json"] = (json.dumps(manifest, indent=2, sort_keys=True) + "\n").encode()
    with zipfile.ZipFile(output, "x", compression=zipfile.ZIP_DEFLATED, compresslevel=7) as zf:
        for key, value in sorted(entries.items()):
            zf.writestr(key, value)
    return {"output": str(output), "log_count": len(sources), "event_count": len(event_records),
            "bundle_sha256": sha256(output.read_bytes()), "warning": metadata["privacy"]}


def read_bundle(path: Path) -> dict[str, bytes]:
    with zipfile.ZipFile(path) as zf:
        names = zf.namelist()
        if len(names) != len(set(names)) or len(names) > MAX_FILES + 8:
            raise ValueError("Duplicate or excessive entries")
        for name in names:
            if name.startswith("/") or ".." in Path(name).parts or "\\" in name:
                raise ValueError("Unsafe bundle entry name")
        if sum(zf.getinfo(k).file_size for k in names) > (MAX_FILES + 2) * MAX_LOG_BYTES:
            raise ValueError("Evidence ZIP exceeds safety limit")
        payload = {k: zf.read(k) for k in names}
    if "manifest.json" not in payload:
        raise ValueError("Missing manifest")
    manifest = json.loads(payload.pop("manifest.json"))
    if manifest.get("schema") != SCHEMA:
        raise ValueError("Unknown schema version")
    if set(manifest.get("sha256", {})) != set(payload):
        raise ValueError("Manifest entry mismatch")
    for name, value in payload.items():
        if sha256(value) != manifest["sha256"][name]:
            raise ValueError("SHA-256 integrity failure: " + name)
    return payload


RULES = (
    ("R001", "critical", re.compile(r"(?i)(unable to open file|cannot load resource|unable to find resource|cannot open texture|failed to load.*\.brf)"), "Asset/resource loading failed", "Check module.ini, BRFs, DDS texture references, archive CRC."),
    ("R002", "critical", re.compile(r"(?i)(assertion failed|access violation|unhandled exception|segmentation fault|fatal error)"), "Engine crash or fatal exception", "Inspect preceding log lines and crash dumps locally; compare default vs patched module."),
    ("R003", "high", re.compile(r"(?i)(script error|invalid opcode|illegal operation|stack overflow|invalid troop|invalid agent)"), "Compiled script or operation error", "Locate the first failing opcode and its associated mission trigger."),
    ("R004", "high", re.compile(r"(?i)(error.*lua|lua.*error|main\.lua:\d+)"), "WSE2 Lua startup or trigger failure", "Inspect bootstrap and WSE2 Lua support/version."),
    ("R005", "medium", re.compile(r"(?i)(missing (?:texture|sound|mesh|resource)|could not load (?:texture|sound))"), "Missing media reference", "Inspect resource paths and original archive integrity."),
)


def analyze(payload: dict[str, bytes]) -> dict:
    session = json.loads(payload.get("session.json", b"{}").decode())
    installed = json.loads(payload.get("module.json", b"{}").decode())
    flight = json.loads(payload.get("flight_recorder.json", b"{}").decode())
    privacy = privacy_audit(payload)
    logs = {k: data.decode("utf-8", errors="replace") for k, data in payload.items()
            if k.startswith("logs/") and k.endswith(".txt")}
    events = [json.loads(line) for line in payload.get("events.jsonl", b"").decode().splitlines() if line.strip()]
    eventcounts = Counter(record.get("event", "unknown") for record in events)
    findings = []
    for code, severity, regex, title, advice in RULES:
        hits = []
        for name, log in logs.items():
            for i, line in enumerate(log.splitlines(), 1):
                if regex.search(line):
                    hits.append({"file": name, "line": i, "excerpt": line[:220]})
                    if len(hits) >= 8:
                        break
            if len(hits) >= 8:
                break
        if hits:
            findings.append({"id": code, "severity": severity, "title": title,
                             "count_at_least": len(hits), "examples": hits, "action": advice})
    if any(ev.get("event") in {"probe_failed", "probe_unavailable"} for ev in events):
        findings.append({"id": "R016", "severity": "high", "title": "Lua diagnostic registration failed",
                         "action": "Examine WSE2 Lua version, runtime bootstrap and trigger API compatibility."})
    if session.get("captured_utc"):
        capture_time = datetime.fromisoformat(session["captured_utc"])
        for item in session.get("files", []):
            if not item.get("modified_utc"):
                continue
            age = (capture_time - datetime.fromisoformat(item["modified_utc"])).total_seconds()
            if age > 7 * 86400:
                findings.append({"id": "R015", "severity": "medium", "title": "Old engine logs may be unrelated",
                                 "action": "Review log modification times and collect immediately after the final game session."})
                break
    if not logs:
        findings.append({"id": "R010", "severity": "high", "title": "No engine logs collected",
                         "action": "Run the game and collect after exit; pass --log for non-standard paths."})
    elif not eventcounts.get("boot"):
        findings.append({"id": "R011", "severity": "medium", "title": "Diagnostic bootstrap not observed",
                         "action": "Confirm WSE2 runs the remaster lua/main.lua and diagnostic log was included."})
    if eventcounts.get("boot") and not eventcounts.get("mission_enter"):
        findings.append({"id": "R012", "severity": "medium", "title": "Invasion mission entry not observed",
                         "action": "Check server mission=multiplayer_iv, scene selection and Lua trigger registration."})
    if eventcounts.get("mission_enter") and not eventcounts.get("heartbeat"):
        findings.append({"id": "R013", "severity": "medium", "title": "Mission entered but no heartbeat observed",
                         "action": "Check whether the mission immediately ended or periodic callbacks failed."})
    if not installed:
        findings.append({"id": "R017", "severity": "medium", "title": "No installation manifest found",
                         "action": "Point --module to ZOMBIEEE_Remaster or re-run the guarded build."})
    expected = installed.get("final_trigger_count")
    if expected is None and installed:
        expected = 26 if installed.get("experimental_defenders") else 25
    for e in events:
        if e.get("event") == "boot" and "triggers" in e.get("fields", {}):
            try:
                observed = int(e["fields"]["triggers"])
                if expected is not None and observed >= 0 and observed != expected:
                    findings.append({"id": "R014", "severity": "high", "title": "Trigger count differs from build manifest",
                                     "action": f"Expected {expected} original/experimental triggers; WSE reported {observed}."})
            except ValueError:
                pass
            break
    known_sides = []
    for event in events:
        fields = event.get("fields", {})
        if event.get("event") not in ("mission_enter", "heartbeat"):
            continue
        if fields.get("role") != "server":
            continue
        try:
            side0, side1 = int(fields.get("team0", "-1")), int(fields.get("team1", "-1"))
        except ValueError:
            continue
        if side0 >= 0 and side1 >= 0:
            known_sides.append((side0, side1))
    team_evidence = {
        "server_samples": len(known_sides),
        "max_survivor_team0": max((v[0] for v in known_sides), default=None),
        "max_zombie_team1": max((v[1] for v in known_sides), default=None),
        "available": bool(known_sides),
    }
    if installed.get("experimental_defenders") and len(known_sides) >= 2:
        if not any(side0 > 0 for side0, _ in known_sides) and any(side1 > 0 for _, side1 in known_sides):
            findings.append({"id": "R018", "severity": "medium",
                             "title": "Allied survivor team absent in sampled server frames",
                             "action": "Check mission-start visitor spawns, team assignment, and WSE2 team-query availability. Samples alone cannot prove why."})
    if flight:
        if flight.get("outcome") == "timeout":
            findings.append({"id": "R027", "severity": "high",
                             "title": "External flight recorder timed out",
                             "action": "Inspect actual process lifecycle and final event snapshot; timeout alone is not an engine crash."})
        if flight.get("exit_code_observed") is True and isinstance(flight.get("exit_code"), int) and flight["exit_code"] != 0:
            findings.append({"id": "R028", "severity": "medium",
                             "title": "Observed child exited with a nonzero status",
                             "action": "Correlate process exit with nearby crash logs; nonzero exit alone does not identify a Warband fault."})
    tactical_report = analyze_tactical_events(events, installed)
    findings.extend(tactical_report["findings"])
    combat_report = analyze_combat_events(events, installed)
    findings.extend(combat_report["findings"])
    readiness = matrix_for_session(events, findings, installed, len(logs), combat_report)
    capabilities = capability_snapshot(events)
    return {"session": session.get("session", "unknown"), "module": installed,
            "flight_recorder": flight, "privacy": privacy,
            "capability_evidence": capabilities,
            "event_counts": dict(eventcounts), "events": events[:500], "team_evidence": team_evidence,
            "tactical_evidence": {k: v for k, v in tactical_report.items() if k != "findings"},
            "combat_evidence": {k: v for k, v in combat_report.items() if k != "findings"},
            "evidence_matrix": readiness,
            "findings": findings,
            "evidence": {"logs": len(logs), "events": len(events)},
            "status": "critical" if any(f["severity"] == "critical" for f in findings) else
                      "warning" if findings else "inconclusive_no_errors_detected",
            "caveat": "Absence of matched errors is not proof of playability, allied AI or wave completion."}


def aggregate(paths: list[Path]) -> dict:
    """Compare multiple independently verified bundles, ordered as provided."""
    if not paths:
        raise ValueError("At least one evidence ZIP is required")
    runs = []
    for path in paths:
        report = analyze(read_bundle(path))
        runs.append({"session": report["session"],
                     "version": report["module"].get("remaster_version"),
                     "defenders": report["module"].get("experimental_defenders", 0),
                     "events": report["event_counts"],
                     "status": report["status"],
                     "finding_ids": [item["id"] for item in report["findings"]]})
    first, last = runs[0], runs[-1]
    recurrence = Counter(code for run in runs for code in set(run["finding_ids"]))
    return {"runs": runs, "count": len(runs),
            "first_version": first["version"], "last_version": last["version"],
            "persistent_issue_codes": sorted(code for code, n in recurrence.items() if n == len(runs)),
            "new_issues_in_last": sorted(set(last["finding_ids"]) - set(first["finding_ids"])),
            "resolved_issues_since_first": sorted(set(first["finding_ids"]) - set(last["finding_ids"])),
            "warning": "Comparisons depend on which logs each bundle actually captured."}


def to_markdown(report: dict) -> str:
    lines = ["# ZOMBIEEE diagnostic report", "", f"Session: {report['session']}",
             f"Status: **{report['status']}**", "", "## Evidence", "",
             f"- Log files: {report['evidence']['logs']}", f"- Parsed telemetry events: {report['evidence']['events']}",
             f"- Event counts: {json.dumps(report['event_counts'], sort_keys=True)}",
             f"- External recorder: {json.dumps(report.get('flight_recorder', {}), sort_keys=True)}",
             f"- WSE2 binding declarations: {json.dumps(report.get('capability_evidence', {}), sort_keys=True)}",
             f"- Privacy inspection: {json.dumps(report.get('privacy', {}), sort_keys=True)}",
             f"- Tactical evidence: {json.dumps(report.get('tactical_evidence', {}), sort_keys=True)}",
             f"- Combat evidence: {json.dumps(report.get('combat_evidence', {}), sort_keys=True)}",
             "", "## Acceptance evidence matrix", "",
             "| Signal | Observation | Evidence |", "| --- | --- | --- |",
             *[f"| {key} | {value['status']} | {value['basis']} |"
               for key, value in report.get("evidence_matrix", {}).get("checks", {}).items()],
             "", "## Findings", ""]
    if not report["findings"]:
        lines.append("No known error pattern detected; runtime remains unverified.")
    for f in report["findings"]:
        lines.extend([f"### {f['id']} — {f['title']} ({f['severity']})", "", f"Action: {f['action']}", ""])
        for ex in f.get("examples", [])[:3]:
            # Native log findings carry file/line/excerpt. Tactical and combat
            # heuristics instead carry agent IDs, groups and wave numbers.
            # They must not crash the final Markdown report.
            if all(key in ex for key in ("file", "line", "excerpt")):
                lines.append(f"- {ex['file']}:{ex['line']} — {str(ex['excerpt']).replace(chr(96), chr(39))}")
            else:
                lines.append("- " + json.dumps(ex, sort_keys=True))
        lines.append("")
    lines.extend(["## Interpretation", "", report["caveat"], "",
                  "Bundle contains redacted logs only. Review contents before sharing.", ""])
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    col = sub.add_parser("collect", help="Make one local, redacted, checksummed evidence ZIP")
    col.add_argument("--game-root", type=Path)
    col.add_argument("--module", type=Path)
    col.add_argument("--log", action="append", type=Path, default=[])
    col.add_argument("--output", type=Path, required=True)
    col.add_argument("--session", default="final-check")
    col.add_argument("--flight-root", type=Path, help="Optional completed Agent C recorder folder")
    an = sub.add_parser("analyze", help="Offline diagnosis; no game required")
    an.add_argument("bundle", type=Path)
    an.add_argument("--report", type=Path)
    many = sub.add_parser("compare", help="Compare two or more local evidence bundles")
    many.add_argument("bundles", type=Path, nargs="+")
    ve = sub.add_parser("verify", help="SHA-256 verification and safety check")
    ve.add_argument("bundle", type=Path)
    args = parser.parse_args()
    try:
        if args.command == "collect":
            result = collect(args.game_root, args.module, args.output, args.log, args.session,
                             flight_root=args.flight_root)
        elif args.command == "compare":
            result = aggregate(args.bundles)
        else:
            data = read_bundle(args.bundle)
            if args.command == "verify":
                result = {"verified": True, "files": len(data), "privacy": privacy_audit(data)}
            else:
                result = analyze(data)
                if args.report:
                    args.report.write_text(to_markdown(result), encoding="utf-8")
        print(json.dumps(result, indent=2))
        return 0
    except (OSError, ValueError, zipfile.BadZipFile, json.JSONDecodeError) as exc:
        print("Diagnostic error: " + str(exc), file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
