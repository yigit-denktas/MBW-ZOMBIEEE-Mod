"""Receipt "what happened" summary for a sealed flight-recorder directory.

Read-only, offline, bounded. The command verifies the recorder manifest
(SHA-256 over every sealed file) **before** interpreting anything and fails
closed on a tampered, incomplete or unsafe bundle.

The ZDB1 probe stream is parsed from any sealed text artifact that carries it
(the launcher/recorder must tee host stdout into the session directory; a
passive attach alone cannot capture another process's stdout). If no ZDB1
stream is sealed, the summary says so explicitly instead of inventing runtime
facts: ``runtime_verified`` stays false and ``runtime_status`` stays unknown.
"""
from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path

SCHEMA = "zombieee.flight.v1"
SUMMARY_SCHEMA = "zombieee.receipt-summary.v1"
MANIFEST_LIMIT = 1024 * 1024
ARTIFACT_LIMIT = 2 * 1024 * 1024
MAX_FILES = 24
MAX_EVENTS = 4096
MAX_HIST_ENTRIES = 16
MAX_LIFECYCLE = 32
MAX_ROUNDS = 32
TEXT_SUFFIXES = (".txt", ".log", ".jsonl", ".out")
# Roster classes for sealed AI evidence. Classification is by ID range:
# generic faction-default placeholders (873/874), the native Zombie block
# A's patch scans (894..911), appended defender clones (981..984) and the
# documented survivor/mercenary troops. Ids outside these stay unknown.
ROSTER_GENERIC = frozenset({873, 874})
ROSTER_NATIVE_ZOMBIE = frozenset(range(894, 912))
ROSTER_DEFENDER = frozenset(range(981, 985))
ROSTER_SURVIVOR = frozenset({875, 876, 877, 878, 32, 33})
# Native defender roster appended by A's patch; used as a bounded fallback
# when native bots are not in divisions 5-7.
DEFENDER_TROOPS = frozenset(range(981, 985))
TEXT_NAME_HINTS = ("stdout", "stderr")
LIFECYCLE_KINDS = ("player_joined", "player_died", "player_respawned",
                   "player_left", "round_started", "wave_started")
ERROR_CLASSES = (
    (re.compile(r"Invalid Faction ID: -1"), "invalid_faction_id_minus_one"),
    (re.compile(r"Illegal lvalue in statement"), "illegal_lvalue"),
    (re.compile(r"SCRIPT ERROR"), "script_error"),
    (re.compile(r"FATAL ERROR|unhandled exception", re.IGNORECASE), "fatal"),
)
HEX64 = re.compile(r"[0-9a-f]{64}")
HIST_ITEM = re.compile(r"^(\d{1,7}):(\d{1,7})$")
NAME_ITEM = re.compile(r"^(\d{1,7}):([A-Za-z0-9_\-]{1,32})$")


class ReceiptError(ValueError):
    """The bundle cannot be interpreted safely (fails closed)."""


def _bounded_int(value, minimum=-1, maximum=10 ** 9):
    if isinstance(value, bool) or value is None:
        return None
    try:
        number = int(value)
    except (TypeError, ValueError, OverflowError):
        return None
    if number < minimum or number > maximum:
        return None
    return number


def _safe_member(name):
    if not isinstance(name, str) or not name:
        raise ReceiptError("manifest entry is not a string")
    if "\\" in name or name.startswith("/") or name.startswith("../"):
        raise ReceiptError("unsafe manifest path")
    parts = Path(name).parts
    if any(part in ("", ".", "..") for part in parts):
        raise ReceiptError("unsafe manifest path component")
    if len(name) > 300:
        raise ReceiptError("oversized manifest path")
    return name


def resolve_receipt_root(target: Path) -> Path:
    target = Path(target).expanduser()
    if not target.is_dir():
        raise ReceiptError("receipt path is not a directory")
    if (target / "manifest.json").is_file():
        return target
    children = [p for p in target.iterdir() if p.is_dir() and (p / "manifest.json").is_file()]
    if len(children) == 1:
        return children[0]
    raise ReceiptError("no single sealed session directory with manifest.json")


def verify_manifest(root: Path) -> dict:
    """Verify the sealed recorder manifest; raise ReceiptError on any doubt."""
    manifest_path = root / "manifest.json"
    if manifest_path.is_symlink():
        raise ReceiptError("manifest is a symlink")
    if manifest_path.stat().st_size > MANIFEST_LIMIT:
        raise ReceiptError("oversized manifest")
    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ReceiptError("unreadable manifest: " + str(exc)) from exc
    if not isinstance(manifest, dict) or manifest.get("schema") != SCHEMA:
        raise ReceiptError("manifest schema mismatch")
    expected = manifest.get("sha256")
    if not isinstance(expected, dict) or not expected or len(expected) > MAX_FILES:
        raise ReceiptError("manifest digest table invalid")
    actual = {str(p.relative_to(root)).replace("\\", "/") for p in root.rglob("*")
              if p.is_file() and p.name != "manifest.json" and not p.name.endswith(".tmp")}
    if set(expected) != actual:
        raise ReceiptError("manifest entry set does not match sealed files")
    if "recorder.json" not in expected:
        raise ReceiptError("manifest has no recorder receipt")
    for name, digest in expected.items():
        _safe_member(name)
        if not isinstance(digest, str) or not HEX64.fullmatch(digest):
            raise ReceiptError("invalid digest metadata for " + name)
        path = root / name
        if path.is_symlink():
            raise ReceiptError("sealed file is a symlink: " + name)
        if hashlib.sha256(path.read_bytes()).hexdigest() != digest:
            raise ReceiptError("SHA-256 integrity failure for " + name)
    receipt = json.loads((root / "recorder.json").read_text(encoding="utf-8"))
    if not isinstance(receipt, dict) or receipt.get("schema") != SCHEMA:
        raise ReceiptError("recorder receipt schema mismatch")
    return {"verified": True, "file_count": len(expected),
            "members": sorted(expected), "receipt": receipt}


def _text_artifacts(root: Path, members) -> list[tuple[str, str]]:
    found = []
    for name in members:
        lowered = name.lower()
        if not lowered.endswith(TEXT_SUFFIXES) and not any(
                hint in Path(name).name.lower() for hint in TEXT_NAME_HINTS):
            continue
        path = root / name
        size = path.stat().st_size
        data = path.read_bytes()[:ARTIFACT_LIMIT]
        text = data.decode("utf-8", errors="replace")
        found.append((name, text[:ARTIFACT_LIMIT]))
    return found


def parse_zdbi(text: str) -> list[dict]:
    events = []
    for raw_line in text.splitlines():
        line = raw_line.strip()
        if not line.startswith("ZDB1|"):
            continue
        tokens = line.split("|")
        if len(tokens) < 2 or not tokens[1]:
            continue
        fields = {}
        for token in tokens[2:]:
            if "=" not in token:
                continue
            key, _, value = token.partition("=")
            if not key or len(key) > 48 or len(value) > 512:
                continue
            fields[key] = value
        events.append({"event": tokens[1][:48], "fields": fields})
        if len(events) >= MAX_EVENTS:
            break
    return events


def _histogram(text):
    if text is None or text in ("", "none", "-1"):
        return None
    result = {}
    for item in str(text).split(",")[:MAX_HIST_ENTRIES]:
        match = HIST_ITEM.match(item.strip())
        if match:
            troop, count = int(match.group(1)), int(match.group(2))
            if count > 0:
                result[troop] = count
    return result or None


def _troop_names(text):
    if text is None or text in ("", "none", "-1"):
        return None
    result = {}
    for item in str(text).split(",")[:MAX_HIST_ENTRIES]:
        match = NAME_ITEM.match(item.strip())
        if match:
            result[int(match.group(1))] = match.group(2)
    return result or None


def _classify_errors(artifacts) -> dict:
    counts = {label: 0 for _, label in ERROR_CLASSES}
    total = 0
    for _name, text in artifacts:
        for line in text.splitlines():
            if "SCRIPT ERROR" not in line and "FATAL ERROR" not in line:
                continue
            total += 1
            for pattern, label in ERROR_CLASSES:
                if pattern.search(line):
                    counts[label] += 1
                    break
    return {"total": total, "kinds": {k: v for k, v in counts.items() if v}}


def _lifecycle(events) -> dict:
    grouped = {kind: [] for kind in LIFECYCLE_KINDS}
    for event in events:
        kind = event["event"]
        if kind not in grouped or len(grouped[kind]) >= MAX_LIFECYCLE:
            continue
        fields = event["fields"]
        entry = {"count": _bounded_int(fields.get("count")),
                 "wave": _bounded_int(fields.get("wave")),
                 "round_start": _bounded_int(fields.get("round_start")),
                 "id": _bounded_int(fields.get("id"), minimum=0),
                 "observed": fields.get("observed", "unknown")[:32]}
        grouped[kind].append({k: v for k, v in entry.items() if v is not None})
    return grouped


def summarize_receipt(target: Path) -> dict:
    root = resolve_receipt_root(Path(target))
    verified = verify_manifest(root)
    receipt = verified["receipt"]
    artifacts = _text_artifacts(root, verified["members"])
    events = []
    for _name, text in artifacts:
        events.extend(parse_zdbi(text))
    events = events[:MAX_EVENTS]

    heartbeats = [e for e in events if e["event"] == "heartbeat"]
    entries = [e for e in events if e["event"] == "mission_enter"]
    pre_round = [e for e in events if e["event"] == "pre_round_sample"]
    capability = next((e for e in events if e["event"] == "recorder_capabilities"), None)
    samples = entries + heartbeats + pre_round

    def latest_field(key):
        for event in reversed(samples):
            value = event["fields"].get(key)
            if value not in (None, ""):
                return value
        return None

    probe = {
        "opmeta": _bounded_int(
            capability["fields"].get("opmeta"), minimum=0, maximum=1)
        if capability else None,
        "role": latest_field("role"),
        "game_type": _bounded_int(latest_field("game_type"), minimum=0),
        "ready_for_spawn": _bounded_int(latest_field("ready_for_spawn"), minimum=0),
        "template": latest_field("template"),
        "pre_round_samples": len(pre_round),
        "pre_round_only": bool(pre_round) and not heartbeats,
        "sampling_interval_s": _bounded_int(
            capability["fields"].get("sampling_interval_s")) if capability else None,
        "troop_map": _bounded_int(
            capability["fields"].get("troop_map"), minimum=0, maximum=64) if capability else None,
    }
    team0 = [_bounded_int(e["fields"].get("team0")) for e in samples]
    team1 = [_bounded_int(e["fields"].get("team1")) for e in samples]
    team0 = [v for v in team0 if v is not None and v >= 0]
    team1 = [v for v in team1 if v is not None and v >= 0]
    teams = {
        "max_team0": max(team0) if team0 else None,
        "max_team1": max(team1) if team1 else None,
        "last_team0": team0[-1] if team0 else None,
        "last_team1": team1[-1] if team1 else None,
        "samples": len(team0),
    }
    # Union view of every sealed sample: keep the largest count seen per troop
    # id so a later, thinner sample cannot hide an earlier full histogram.
    merged = {key: {} for key in ("team0", "team1")}
    merged_names = {key: {} for key in ("team0", "team1")}
    unknown_ids = 0
    truncated = 0
    hist_samples = 0
    for event in samples:
        fields = event["fields"]
        for key in ("team0", "team1"):
            hist = _histogram(fields.get(f"troops_{key}"))
            if hist is not None:
                hist_samples += 1
                for troop, count in hist.items():
                    merged[key][troop] = max(merged[key].get(troop, 0), count)
                for troop, name in (_troop_names(fields.get(f"troop_names_{key}")) or {}).items():
                    merged_names[key].setdefault(troop, name)
        unknown_ids = max(unknown_ids, _bounded_int(fields.get("troop_ids_unknown")) or 0)
        truncated = max(truncated, _bounded_int(fields.get("troops_truncated")) or 0)
    troops = {"team0": None, "team1": None, "names": None,
              "unknown_ids": None, "truncated": None, "samples": hist_samples}
    if hist_samples:
        def capped(hist):
            if not hist:
                return None
            return dict(sorted(hist.items(), key=lambda kv: (-kv[1], kv[0]))[:MAX_HIST_ENTRIES])

        over = sum(max(0, len(merged[key]) - MAX_HIST_ENTRIES) for key in ("team0", "team1"))
        troops = {
            "team0": capped(merged["team0"]),
            "team1": capped(merged["team1"]),
            "names": {key: (merged_names[key] or None) for key in ("team0", "team1")},
            "unknown_ids": unknown_ids,
            "truncated": truncated + over,
            "samples": hist_samples,
        }
        combined = {}
        for key in ("team0", "team1"):
            for troop, count in (troops[key] or {}).items():
                combined[troop] = combined.get(troop, 0) + count
        classes = {"generic": {}, "native_zombie": {}, "defender": {},
                   "survivor": {}, "unknown": {}}
        for troop, count in combined.items():
            if troop in ROSTER_GENERIC:
                bucket = "generic"
            elif troop in ROSTER_NATIVE_ZOMBIE:
                bucket = "native_zombie"
            elif troop in ROSTER_DEFENDER:
                bucket = "defender"
            elif troop in ROSTER_SURVIVOR:
                bucket = "survivor"
            else:
                bucket = "unknown"
            classes[bucket][troop] = classes[bucket].get(troop, 0) + count
        troops["classes"] = {
            name: dict(sorted(values.items(), key=lambda kv: (-kv[1], kv[0]))[:MAX_HIST_ENTRIES])
            for name, values in classes.items()}
        read_unknown_values = [_bounded_int(e["fields"].get("troop_read_unknown"), minimum=0)
                               for e in samples]
        read_unknown_values = [value for value in read_unknown_values
                               if value is not None]
        troops["read_unknown"] = max(read_unknown_values) if read_unknown_values else None
        troops["reliable"] = bool(troops["read_unknown"] in (0, None)
                                  and hist_samples > 0
                                  and (troops["team0"] or troops["team1"]))
        troops["roster"] = {
            "generic_observed": bool(classes["generic"]),
            "native_zombie_observed": bool(classes["native_zombie"]),
            "defender_observed": bool(classes["defender"]),
            "unknown_id_count": len(classes["unknown"]),
            "native_zombie_ids": sorted(classes["native_zombie"]),
            "generic_ids": sorted(classes["generic"]),
            "defender_ids": sorted(classes["defender"]),
        }
    else:
        troops["classes"] = None
        troops["roster"] = None
    waves = sorted({v for v in (
        _bounded_int(e["fields"].get("wave"), minimum=0) for e in events
        if e["event"] in ("heartbeat", "wave_change", "mission_enter", "wave_started")) if v is not None})
    # Division (agent_get_group) telemetry: bounded per-team group histograms and
    # sampled-bot groups, so hold/sector claims have a measured field. Defender
    # divisions are 5-7 by A's contract; absence is reported, never assumed.
    division_groups = {0: {}, 1: {}}
    for event in samples:
        for team in (0, 1):
            hist = _histogram(event["fields"].get(f"groups_team{team}"))
            for group, count in (hist or {}).items():
                division_groups[team][group] = max(
                    division_groups[team].get(group, 0), count)
    sampled_groups = {0: {}, 1: {}}
    for event in events:
        if event["event"] != "ai_sample":
            continue
        team = _bounded_int(event["fields"].get("team"), minimum=0, maximum=1)
        group = _bounded_int(event["fields"].get("group"), minimum=0, maximum=255)
        if team in (0, 1) and group is not None:
            sampled_groups[team][group] = sampled_groups[team].get(group, 0) + 1
    group_unknown_values = [_bounded_int(e["fields"].get("group_read_unknown"), minimum=0)
                            for e in samples]
    group_unknown_values = [value for value in group_unknown_values if value is not None]
    group_read_unknown = max(group_unknown_values) if group_unknown_values else None
    group_capability = next((e for e in events
                             if e["event"] == "probe_capability"
                             and "group_convention" in e["fields"]), None)
    group_convention = (group_capability["fields"].get("group_convention", "")[:32]
                        if group_capability else None)
    defender_groups = [group for group in (5, 6, 7)
                       if division_groups[0].get(group) or sampled_groups[0].get(group)]
    divisions = {
        "team0": (dict(sorted(division_groups[0].items(),
                              key=lambda kv: (-kv[1], kv[0]))[:MAX_HIST_ENTRIES]) or None),
        "team1": (dict(sorted(division_groups[1].items(),
                              key=lambda kv: (-kv[1], kv[0]))[:MAX_HIST_ENTRIES]) or None),
        "sampled_team0": (dict(sorted(sampled_groups[0].items(),
                                      key=lambda kv: (-kv[1], kv[0]))[:MAX_HIST_ENTRIES]) or None),
        "sampled_team1": (dict(sorted(sampled_groups[1].items(),
                                      key=lambda kv: (-kv[1], kv[0]))[:MAX_HIST_ENTRIES]) or None),
        "read_unknown": group_read_unknown,
        "convention": group_convention,
        "defender_groups_observed": defender_groups,
        "defender_divisions_observed": bool(defender_groups),
        "defenders_sampled": any(e["event"] == "combat_sample" for e in events),
        "note": ("agent_get_group per non-player bot; defender divisions 5-7 are "
                 "the hold-order candidates; absent divisions stay unobserved and "
                 "are never assumed to have adopted orders."),
    }

    # Team-0 defender telemetry: divisions 5-7, alive/kill evidence, and bounded
    # position/motion samples. guard_entries_reached is a coarse-position proxy,
    # never a guard-entry identity, and hold behaviour is never assumed.
    defender_samples = [event for event in events
                        if event["event"] == "ai_sample"
                        and _bounded_int(event["fields"].get("team")) == 0
                        and (_bounded_int(event["fields"].get("defender"),
                                          minimum=0, maximum=1) == 1
                             or _bounded_int(event["fields"].get("group"), minimum=0,
                                             maximum=255) in (5, 6, 7)
                             or _bounded_int(event["fields"].get("troop"), minimum=0)
                             in DEFENDER_TROOPS)]
    defender_positions = {}
    for event in defender_samples:
        agent = _bounded_int(event["fields"].get("id"), minimum=0)
        try:
            px = float(event["fields"].get("x"))
            py = float(event["fields"].get("y"))
        except (TypeError, ValueError):
            continue
        if agent is None or not (-100000 <= px <= 100000 and -100000 <= py <= 100000):
            continue
        defender_positions.setdefault(agent, set()).add((round(px), round(py)))
    coarse_positions = {point for points in defender_positions.values() for point in points}
    defender_divisions = {group: (division_groups[0].get(group)
                                  or sampled_groups[0].get(group) or 0)
                          for group in (5, 6, 7)}
    defender_troop_counts = (troops.get("classes") or {}).get("defender") or {}

    def _max_field(name):
        values = [_bounded_int(e["fields"].get(name), minimum=0) for e in samples]
        values = [value for value in values if value is not None]
        return max(values) if values else None

    defender_groups_seen = {}
    for event in defender_samples:
        group = _bounded_int(event["fields"].get("group"), minimum=0, maximum=255)
        if group is not None:
            defender_groups_seen[group] = defender_groups_seen.get(group, 0) + 1
    group_based = bool([group for group in defender_groups_seen if group in (5, 6, 7)]) \
        or bool(defender_groups)
    if group_based:
        division_source = "group"
    elif defender_samples:
        division_source = "troop-fallback"
    else:
        division_source = "unavailable"

    defender_alive = _max_field("defender_alive_team0")
    defender_kills = _max_field("defender_kills_team0")
    defender_read_unknown = _max_field("defender_read_unknown")
    defenders = {
        "observed": bool(sum(defender_divisions.values())) or bool(defender_troop_counts),
        "divisions": ({group: count for group, count in defender_divisions.items() if count}
                      or None),
        "bots": sum(defender_divisions.values()) or None,
        "troops": defender_troop_counts or None,
        "alive": defender_alive,
        "kills": defender_kills,
        "read_unknown": defender_read_unknown,
        "positions_sampled": len(defender_samples),
        "distinct_positions": len(coarse_positions),
        "guard_entries_reached": min(len(coarse_positions), 16),
        "moving": sum(1 for points in defender_positions.values() if len(points) >= 2),
        "hold_samples": len(defender_samples),
        "hold_behavior_observed": False,
        "groups": (dict(sorted(defender_groups_seen.items(),
                               key=lambda kv: (-kv[1], kv[0]))[:MAX_HIST_ENTRIES])
                   or None),
        "division_source": division_source,
        "note": ("team-0 non-player defenders; guard_entries_reached is a bounded "
                 "distinct-coarse-position proxy, not a guard-entry identity; "
                 "hold behaviour is not asserted from samples."),
    }

    # Round identity must not be inflated by a monotonically increasing
    # g_round_start_time: count a raw heartbeat/entry value only when it is
    # stable across samples, and always keep explicit round_started events.
    round_counts = {}
    for value in (_bounded_int(e["fields"].get("round_start"), minimum=0)
                  for e in events if e["event"] in ("heartbeat", "mission_enter")):
        if value is not None:
            round_counts[value] = round_counts.get(value, 0) + 1
    event_rounds = {v for v in (_bounded_int(e["fields"].get("round_start"), minimum=0)
                                for e in events if e["event"] == "round_started")
                    if v is not None}
    rounds = sorted({v for v, count in round_counts.items() if count >= 2} | event_rounds)
    round_anomaly = any(e["event"] == "probe_anomaly" for e in events)
    error_scan = _classify_errors(artifacts)
    lifecycle = _lifecycle(events)
    poll_failures = sum(1 for e in events if e["event"] == "log_unavailable")

    # Team composition (playerless AI-vs-AI aware): every category is a measured
    # per-team agent count; a category with no usable getter stays None.
    composition_keys = ("humans", "players", "bots", "horses")
    comp_max = {key: {0: None, 1: None} for key in composition_keys}
    def _composition_field(key, team):
        # The native bots_team1 global keeps its own ZDB1 field; AI bot counts
        # use bot_agents_teamX so the two meanings never collide.
        name = "bot_agents" if key == "bots" else key
        return f"{name}_team{team}"

    for event in samples:
        for team in (0, 1):
            for key in composition_keys:
                value = _bounded_int(event["fields"].get(_composition_field(key, team)))
                if value is not None and value >= 0:
                    current = comp_max[key][team]
                    comp_max[key][team] = value if current is None else max(current, value)
    team_comp = {team: {key: comp_max[key][team] for key in composition_keys}
                 for team in (0, 1)}
    players_known = (team_comp[0]["players"] is not None
                     and team_comp[1]["players"] is not None)
    if not players_known:
        comp_mode = "unknown"
    elif team_comp[0]["players"] == 0 and team_comp[1]["players"] == 0:
        others = sum((team_comp[team][key] or 0) for team in (0, 1)
                     for key in ("bots", "horses"))
        comp_mode = "no_human_player_observed" if others > 0 else "unknown_no_agents_observed"
    else:
        comp_mode = "human_present"
    composition = {
        "mode": comp_mode,
        "team0": team_comp[0],
        "team1": team_comp[1],
        "players_unknown": not players_known,
        "player_events_expected": comp_mode != "no_human_player_observed",
        "note": ("No human player observed; player_* lifecycle absence is expected "
                 "for this mode, not a measured zero."
                 if comp_mode == "no_human_player_observed" else
                 "Per-team agent categories from measured predicates; a missing "
                 "category stays unknown, never zero."),
    }

    def _max_field(prefix):
        values = {0: None, 1: None}
        for event in samples:
            for team in (0, 1):
                value = _bounded_int(event["fields"].get(f"{prefix}_team{team}"))
                if value is not None and value >= 0:
                    values[team] = value if values[team] is None else max(values[team], value)
        return values

    bots_max = _max_field("bot_agents")
    horses_max = _max_field("horses")
    alive_max = _max_field("alive")
    teams.update({
        "bots_team0": bots_max[0], "bots_team1": bots_max[1],
        "horses_team0": horses_max[0], "horses_team1": horses_max[1],
        "alive_team0": alive_max[0], "alive_team1": alive_max[1],
    })

    # no_player: explicit probe marker; None when the probe could not measure it.
    no_player = None
    for event in reversed(events):
        raw = _bounded_int(event["fields"].get("no_player"))
        if raw in (0, 1):
            no_player = raw == 1
            break
    if no_player is None and composition["mode"] == "no_human_player_observed":
        no_player = True
    elif no_player is None and composition["mode"] == "human_present":
        no_player = False

    def _max_kills(team):
        values = [v for v in (_bounded_int(e["fields"].get(f"kills_team{team}"), minimum=0)
                              for e in samples) if v is not None]
        return max(values) if values else None

    def _measured_flag(team):
        values = [_bounded_int(e["fields"].get(f"kills_measured_team{team}"),
                               minimum=-1, maximum=1) for e in samples]
        values = [value for value in values if value is not None]
        return values[-1] if values else None

    def _max_unknown(team):
        values = [_bounded_int(e["fields"].get(f"kills_unknown_team{team}"), minimum=0)
                  for e in samples]
        values = [value for value in values if value is not None]
        return max(values) if values else None

    measured0, measured1 = _measured_flag(0), _measured_flag(1)
    unknown0, unknown1 = _max_unknown(0), _max_unknown(1)
    kills0, kills1 = _max_kills(0), _max_kills(1)
    kills_reliable = bool(measured0 == 1 and measured1 == 1 and kills0 is not None
                          and kills1 is not None
                          and (unknown0 in (None, 0)) and (unknown1 in (None, 0)))
    engagement = {
        "kills_team0": kills0, "kills_team1": kills1,
        "measured_team0": measured0, "measured_team1": measured1,
        "unknown_agents_team0": unknown0, "unknown_agents_team1": unknown1,
        "reliable": kills_reliable,
        "note": ("kills_* are agent lifetime kill counters summed over observed "
                 "agents, not session kills; unknown/unreliable must not be read "
                 "as zero or as a victory claim."),
    }

    def _number_pair(raw):
        if not isinstance(raw, str):
            return None
        parts = raw.split(":")
        if len(parts) != 2:
            return None
        try:
            x, y = float(parts[0]), float(parts[1])
        except ValueError:
            return None
        if not (-100000 <= x <= 100000 and -100000 <= y <= 100000):
            return None
        return {"x": round(x, 3), "y": round(y, 3)}

    def _bbox(raw):
        if not isinstance(raw, str):
            return None
        parts = raw.split(":")
        if len(parts) != 4:
            return None
        try:
            values = [float(part) for part in parts]
        except ValueError:
            return None
        if any(not -100000 <= v <= 100000 for v in values):
            return None
        return {"min_x": round(values[0], 3), "min_y": round(values[1], 3),
                "max_x": round(values[2], 3), "max_y": round(values[3], 3)}

    ai_events = [e for e in events if e["event"] == "ai_sample"][:512]
    positions = {}
    for team in (0, 1):
        centroid = spread = sampled = None
        for event in reversed(samples):
            fields = event["fields"]
            if centroid is None:
                centroid = _number_pair(fields.get(f"pos_team{team}"))
            if spread is None:
                spread = _bbox(fields.get(f"bbox_team{team}"))
            if sampled is None:
                sampled = _bounded_int(fields.get(f"pos_sampled_team{team}"), minimum=0)
            if centroid is not None or spread is not None or sampled is not None:
                break
        tracks = {}
        for event in ai_events:
            if _bounded_int(event["fields"].get("team"), minimum=0, maximum=1) != team:
                continue
            agent = _bounded_int(event["fields"].get("id"), minimum=0)
            pair = _number_pair(event["fields"].get("x", "") + ":" + event["fields"].get("y", ""))
            if agent is None or pair is None:
                continue
            tracks.setdefault(agent, set()).add((pair["x"], pair["y"]))
        moving = sum(1 for points in tracks.values() if len(points) >= 2)
        positions[f"team{team}"] = {
            "centroid": centroid,
            "spread": spread,
            "sampled": sampled,
            "samples": sum(1 for event in ai_events
                           if _bounded_int(event["fields"].get("team"), minimum=0, maximum=1) == team),
            "distinct_bots": len(tracks),
            "moving_bots": moving if tracks else None,
        }

    event_counts = {}
    for event in events:
        kind = event["event"]
        event_counts[kind] = event_counts.get(kind, 0) + 1
    bounded_counts = dict(sorted(event_counts.items(), key=lambda kv: (-kv[1], kv[0]))[:24])
    event_section = {"zdbi_lines": len(events), "zdbi_sealed": bool(events),
                     "counts": bounded_counts,
                     "pre_round_only": bool(pre_round) and not heartbeats}

    if no_player is None:
        gaps_hint = ["player_presence_unknown"]
    else:
        gaps_hint = []
    if positions["team0"]["centroid"] is None and positions["team1"]["centroid"] is None:
        gaps_hint.append("position_telemetry_unavailable")
    if engagement["kills_team0"] is None and engagement["kills_team1"] is None:
        gaps_hint.append("kill_telemetry_unavailable")

    gaps = list(gaps_hint)
    if group_convention == "unknown":
        gaps.append("group_convention_unknown")
    if defenders["observed"] and not defenders["divisions"]:
        gaps.append("defender_division_unreadable")
    if not defenders["observed"]:
        gaps.append("defenders_not_observed")
    if defenders["observed"] and not defender_samples:
        gaps.append("defender_positions_unobserved")
    if defenders["read_unknown"]:
        gaps.append("defender_telemetry_unreliable")
    if (divisions["team0"] or divisions["team1"]) \
            and not divisions["defender_divisions_observed"]:
        gaps.append("defender_divisions_unobserved")
    if divisions["read_unknown"]:
        gaps.append("division_reads_unreliable")
    if not engagement["reliable"]:
        gaps.append("engagement_kills_unreliable")
    if troops.get("read_unknown"):
        gaps.append("troop_reads_unreliable")
    if round_anomaly:
        gaps.append("round_identity_unstable")
    roster_info = troops.get("roster")
    if roster_info is not None and not roster_info["native_zombie_observed"]:
        gaps.append("native_zombie_roster_not_observed")
    if not events:
        gaps.append("zdbi_stream_not_sealed")
    if composition["mode"] in ("unknown", "unknown_no_agents_observed"):
        gaps.append("team_composition_unknown")
    if probe["role"] in (None, "unknown"):
        gaps.append("probe_role_unknown")
    if not heartbeats:
        gaps.append("no_probe_heartbeats")
    if troops["team1"] is None and troops["team0"] is None:
        gaps.append("troop_histogram_unavailable")
    if receipt.get("exit_code_observed") is False:
        gaps.append("process_exit_not_observed_passive")
    if receipt.get("game_runtime") in (None, "unknown"):
        gaps.append("engine_runtime_unknown")
    if any(receipt.get("log_truncated") or []):
        gaps.append("engine_log_truncated")
    if any(v for v in (receipt.get("log_omitted_bytes") or [])):
        gaps.append("engine_log_omitted_bytes")
    if poll_failures:
        gaps.append("engine_log_poll_failures")
    duration = receipt.get("duration_seconds")
    duration = (round(float(duration), 3)
                if isinstance(duration, (int, float)) and not isinstance(duration, bool)
                and 0 <= float(duration) <= 10 ** 7 else None)
    summary = {
        "schema": SUMMARY_SCHEMA,
        "verified": verified["verified"],
        "file_count": verified["file_count"],
        "session_id": receipt.get("session_id"),
        "attempt_id": receipt.get("attempt_id"),
        "outcome": receipt.get("outcome"),
        "simulation": bool(receipt.get("simulation")),
        "watch_mode": receipt.get("watch_mode"),
        "duration_seconds": duration,
        "probe": probe,
        "teams": teams,
        "no_player": no_player,
        "composition": composition,
        "positions": positions,
        "engagement": engagement,
        "events": event_section,
        "troops": troops,
        "divisions": divisions,
        "defenders": defenders,
        "waves": {"observed": waves, "max": waves[-1] if waves else None,
                  "multiple_observed": len([w for w in waves if w >= 1]) >= 2},
        "rounds": {"round_starts": rounds[:MAX_ROUNDS],
                   "count": len(rounds),
                   "multiple_observed": len(rounds) >= 2,
                   "identity_unstable": round_anomaly},
        "lifecycle": lifecycle,
        "engine_errors": error_scan,
        "evidence_gaps": [gap for gap in gaps if gap],
        "runtime_verified": False,
        "runtime_status": "unknown",
        "interpretation": ("Sealed evidence only. Event markers support individual "
                           "observations; absent fields are unknown, never negative "
                           "evidence. No gameplay, wave-completion or AI acceptance "
                           "is implied by this summary."),
    }
    return summary


def format_summary(summary: dict) -> str:
    probe = summary["probe"]
    teams = summary["teams"]
    lines = [
        "ZOMBIEEE sealed receipt summary",
        "=" * 33,
        f"verified:        {summary['verified']} ({summary['file_count']} files)",
        f"session/attempt: {summary['session_id']} / {summary['attempt_id']}",
        f"outcome:         {summary['outcome']} (simulation={summary['simulation']}, "
        f"mode={summary['watch_mode']})",
        f"duration:        {summary['duration_seconds']} s",
        f"probe:           opmeta={probe['opmeta']} role={probe['role']} "
        f"game_type={probe['game_type']} ready_for_spawn={probe['ready_for_spawn']} "
        f"troop_map={probe['troop_map']}",
        f"teams:           max team0={teams['max_team0']} team1={teams['max_team1']}; "
        f"last team0={teams['last_team0']} team1={teams['last_team1']}",
    ]
    comp = summary["composition"]

    def _category(team, key):
        value = comp[team].get(key)
        return "unknown" if value is None else value

    for team in ("team0", "team1"):
        lines.append(
            f"composition {team}: humans={_category(team, 'humans')} "
            f"players={_category(team, 'players')} bots={_category(team, 'bots')} "
            f"horses={_category(team, 'horses')}")
    lines.append(f"composition mode: {comp['mode']}")
    lines.append(f"no_player:       {summary['no_player']}")
    if comp["mode"] == "no_human_player_observed" or summary["no_player"] is True:
        lines.append("playerless:      no human player observed; player_* lifecycle "
                     "events are absent by design, not measured zero")
    for team in ("team0", "team1"):
        position = summary["positions"][team]
        centroid = position["centroid"]
        spread = position["spread"]
        lines.append(
            f"positions {team}: centroid={centroid} spread={spread} "
            f"sampled={position['sampled']} distinct_bots={position['distinct_bots']} "
            f"moving_bots={position['moving_bots']}")
    engage = summary["engagement"]
    lines.append(f"engagement:      kills_team0={engage['kills_team0']} "
                 f"kills_team1={engage['kills_team1']} "
                 f"reliable={engage['reliable']}")
    lines.append("kill semantics:  lifetime kill counters summed over observed "
                 "agents; unreliable/unknown is never zero or a victory claim")
    lines.append(f"events:          {summary['events']['zdbi_lines']} ZDB1 lines "
                 f"{summary['events']['counts']}")
    if summary["events"].get("pre_round_only"):
        lines.append("pre-round:       no 15 s heartbeat reached mission time; "
                     "composition/positions come from bounded pre-round samples "
                     "(server waiting for players; wave evidence still needs a round)")
    troops = summary["troops"]
    if troops["team1"] or troops["team0"]:
        names = troops["names"] or {}
        def label(hist, key):
            if not hist:
                return "unknown"
            parts = []
            for troop, count in sorted(hist.items(), key=lambda kv: (-kv[1], kv[0])):
                name = (names.get(key) or {}).get(troop)
                parts.append(f"{troop}={'?' if not name else name}:{count}")
            return ", ".join(parts)
        lines.append(f"troops team0:    {label(troops['team0'], 'team0')}")
        lines.append(f"troops team1:    {label(troops['team1'], 'team1')}")
        lines.append(f"troop bounds:    unknown_ids={troops['unknown_ids']} "
                     f"truncated={troops['truncated']}")
        roster = troops.get("roster")
        if roster:
            lines.append(f"troop reads:     read_unknown={troops.get('read_unknown')} "
                     f"reliable={troops.get('reliable')}")
        lines.append(f"roster:          native_zombie={roster['native_zombie_ids']} "
                         f"generic={roster['generic_ids']} "
                         f"defender={roster['defender_ids']} "
                         f"unknown_id_count={roster['unknown_id_count']}")
    else:
        lines.append("troops:          unavailable (histogram not sealed)")
    lines.append(f"divisions:       convention={summary['divisions']['convention']} "
                 f"team0={summary['divisions']['team0']} "
                 f"team1={summary['divisions']['team1']} "
                 f"defender_groups={summary['divisions']['defender_groups_observed']} "
                 f"defenders_sampled={summary['divisions']['defenders_sampled']}")
    defend = summary["defenders"]
    lines.append(f"defenders:       observed={defend['observed']} divisions={defend['divisions']} "
                 f"alive={defend['alive']} kills={defend['kills']} "
                 f"positions_sampled={defend['positions_sampled']} "
                 f"guard_entries_reached={defend['guard_entries_reached']} "
                 f"division_source={defend['division_source']} groups={defend['groups']} "
                 f"moving={defend['moving']} hold_samples={defend['hold_samples']} "
                 f"hold_behavior_observed={defend['hold_behavior_observed']}")
    lines.append(f"waves:           observed={summary['waves']['observed']} "
                 f"max={summary['waves']['max']}")
    lines.append(f"rounds:          {summary['rounds']['count']} distinct "
                 f"round_start values")
    done = ", ".join(f"{kind}={len(items)}" for kind, items in summary["lifecycle"].items())
    lines.append(f"lifecycle:       {done}")
    errors = summary["engine_errors"]
    lines.append(f"engine errors:   {errors['total']} {errors['kinds']}")
    gaps = summary["evidence_gaps"]
    lines.append(f"evidence gaps:   {', '.join(gaps) if gaps else 'none detected'}")
    lines.extend([
        f"runtime:         verified={summary['runtime_verified']} "
        f"status={summary['runtime_status']}",
        "",
        summary["interpretation"],
    ])
    return "\n".join(lines)


if __name__ == "__main__":
    import argparse
    import sys

    parser = argparse.ArgumentParser(description="Summarize a sealed flight receipt")
    parser.add_argument("receipt", type=Path)
    parser.add_argument("--json", action="store_true", help="Emit JSON instead of text")
    args = parser.parse_args()
    try:
        summary = summarize_receipt(args.receipt)
    except ReceiptError as exc:
        print("Receipt verification failed: " + str(exc), file=sys.stderr)
        raise SystemExit(2)
    print(json.dumps(summary, indent=2, sort_keys=True)
          if args.json else format_summary(summary))
