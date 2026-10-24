"""Static module/trigger inspection: no game launch, text only."""

from __future__ import annotations

import json
import re
from collections import Counter
from pathlib import Path
from typing import Any

TRIGGER_LINE = re.compile(r"^(-?\d+(?:\.\d+)?)\s+(-?\d+(?:\.\d+)?)\s+(-?\d+(?:\.\d+)?)\s+(\d+)\s*(.*)$")
TARGET_OPS = ("2093", "502", "1790", "1791", "3314", "3343", "522", "5113")
INVADER_FACTION = "432345564227567632"
SLOW_ZOMBIE_TROOP = "360287970189640574"  # TROOP_BASE + 894


def _read(path: Path) -> str | None:
    try:
        return path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return None


def inspect_module(target: Path) -> dict[str, Any]:
    """Inspect an installed module directory (or mission_templates.txt path)."""
    target = Path(target).expanduser()
    module = target if target.is_dir() else target.parent
    mission_path = module / "mission_templates.txt" if target.is_dir() else target
    gaps: list[str] = []
    text = _read(mission_path)
    if text is None:
        return {"ok": False, "gaps": ["mission_templates_unreadable"], "path": str(mission_path)}

    trigger_lines: list[dict[str, Any]] = []
    for line_no, line in enumerate(text.splitlines(), 1):
        match = TRIGGER_LINE.match(line)
        if not match:
            continue
        delay = float(match.group(1))
        tokens = [(line_no, delay, line, token) for token in line.split()[3:]]
        trigger_lines.append({"line": line_no, "delay": delay, "line_text": line})
    op_counts = Counter()
    for row in trigger_lines:
        for token in row["line_text"].split()[3:]:
            if token in TARGET_OPS:
                op_counts[token] += 1

    slot_writes = []
    invalid_faction = 0
    for row in trigger_lines:
        tokens = row["line_text"].split()
        for index, token in enumerate(tokens):
            if token == "502" and index + 4 < len(tokens):
                faction, slot, value = tokens[index + 2], tokens[index + 3], tokens[index + 4]
                if faction == "-1":
                    invalid_faction += 1
                if faction == INVADER_FACTION and value == SLOW_ZOMBIE_TROOP:
                    slot_writes.append(slot)
    speed_triggers = []
    for row in trigger_lines:
        tokens = row["line_text"].split()
        if "2093" in tokens:
            index = tokens.index("2093")
            speed_triggers.append({
                "line": row["line"], "delay": row["delay"],
                "context": " ".join(tokens[max(0, index - 12):index + 8]),
            })
    variables = module / "variables.txt"
    variable_text = _read(variables)
    variables_count = len(variable_text.splitlines()) if variable_text else None
    if variables_count is None:
        gaps.append("variables_unreadable")

    receipt = None
    receipt_path = module / "ZOMBIEEE_REMASTER.json"
    if receipt_path.is_file():
        try:
            data = json.loads(receipt_path.read_text(encoding="utf-8"))
            city = (data.get("experimental_city_guardposts") or {}) if isinstance(data, dict) else {}
            receipt = {
                "city": {key: city.get(key) for key in (
                    "zombie_speed", "wave_visitors", "game_type", "defender_orders",
                    "defender_target", "defender_target_cap", "survivor_growth_per_round")},
                "final_trigger_count": data.get("final_trigger_count"),
                "runtime_verified": data.get("runtime_verified"),
            }
        except (OSError, json.JSONDecodeError):
            gaps.append("receipt_unreadable")
    else:
        gaps.append("receipt_missing")

    header = module / "lua" / "msfiles" / "header_operations.py"
    header_text = _read(header)
    header_ops: dict[str, int] = {}
    if header_text:
        for match in re.finditer(r"^\s*([a-z_]+)\s*=\s*(\d+)\s*$", header_text, re.MULTILINE):
            header_ops[match.group(1)] = int(match.group(2))
        header_lhs = "lhs_operations" in header_text
    else:
        header_lhs = None
        gaps.append("msfiles_header_missing")

    return {
        "ok": True,
        "path": str(module),
        "mission_templates": str(mission_path),
        "trigger_count": len(trigger_lines),
        "trigger_delays": dict(Counter(str(row["delay"]) for row in trigger_lines)),
        "op_counts": {key: op_counts.get(key, 0) for key in TARGET_OPS},
        "slow_894_slot_writes": len(slot_writes),
        "slow_894_slots": slot_writes[:60],
        "invalid_faction_literal_ops": invalid_faction,
        "speed_trigger_count": len(speed_triggers),
        "speed_triggers": speed_triggers[:4],
        "lua_condition_refs_5113": op_counts.get("5113", 0),
        "variables_count": variables_count,
        "receipt": receipt,
        "msfiles": {"path": str(header), "ops": header_ops, "has_lhs_list": header_lhs},
        "gaps": gaps,
        "note": ("static text inspection only; runtime Lua triggers (5113) are "
                 "added by the overlay and do not appear in mission_templates.txt"),
    }
