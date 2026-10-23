#!/usr/bin/env python3
"""Map call_script references from compiled Warband scripts and invasion mission.

Only identifiers are extracted; neither engine behaviour nor opcodes are modified.
"""
import argparse
import json
import re
from pathlib import Path
from preflight import MISSION

SCRIPT_BASE = 936748722493063168
CALL_SCRIPT = 1
SCRIPT_HEADER = re.compile(r"^([a-zA-Z][\w]*) -1$")


def decode_operations(values, start, count):
    pos, calls = start, []
    for _ in range(count):
        if pos + 1 >= len(values):
            raise ValueError("Truncated operation header")
        opcode, argc = int(values[pos]), int(values[pos + 1])
        pos += 2
        if argc < 0 or pos + argc > len(values):
            raise ValueError("Invalid/truncated operation arguments")
        if opcode == CALL_SCRIPT and argc:
            script_id = int(values[pos]) - SCRIPT_BASE
            if script_id >= 0:
                calls.append(script_id)
        pos += argc
    return pos, calls


def read_scripts(path):
    lines = Path(path).read_text(encoding="utf-8", errors="replace").splitlines()
    result = []
    for index, line in enumerate(lines):
        match = SCRIPT_HEADER.fullmatch(line.strip())
        if not match:
            continue
        if index + 1 >= len(lines):
            raise ValueError("Missing body for " + match.group(1))
        body = list(map(int, lines[index + 1].split()))
        if not body:
            raise ValueError("Empty script body: " + match.group(1))
        position, called = decode_operations(body, 1, body[0])
        if position != len(body):
            raise ValueError("Unconsumed script body: " + match.group(1))
        result.append((match.group(1), called))
    return result


def read_mission_calls(path):
    lines = Path(path).read_text(encoding="utf-8", errors="replace").splitlines()
    headers = [i for i, line in enumerate(lines) if line.startswith(MISSION + " ")]
    if len(headers) != 1:
        raise ValueError("Missing or ambiguous invasion mission")
    cursor = headers[0] + 1
    while cursor < len(lines) and not lines[cursor].strip():
        cursor += 1
    cursor += 1  # Description
    while cursor < len(lines) and not lines[cursor].strip():
        cursor += 1
    entries = int(lines[cursor].split()[0])
    cursor += entries  # First entry and the count share a line.
    count = int(lines[cursor].strip())
    result = []
    for trigger in range(count):
        cursor += 1
        parts = lines[cursor].split()
        if len(parts) < 4:
            raise ValueError("Truncated invasion trigger")
        position = 3  # Timing values
        conditions = int(parts[position]); position += 1
        position, called_in_conditions = decode_operations(parts, position, conditions)
        if position >= len(parts):
            raise ValueError("Missing consequence count")
        consequences = int(parts[position]); position += 1
        position, called_in_consequences = decode_operations(parts, position, consequences)
        if position != len(parts):
            raise ValueError("Unconsumed invasion trigger tokens")
        result.append({"trigger_index": trigger,
                       "script_indices": called_in_conditions + called_in_consequences})
    return result


def trace(module_dir):
    root = Path(module_dir)
    scripts = read_scripts(root / "scripts.txt")
    names = [name for name, _ in scripts]
    calls = read_mission_calls(root / "mission_templates.txt")

    def labels(indices):
        return [names[i] for i in sorted(set(indices)) if i < len(names)]

    direct = labels([index for trigger in calls for index in trigger["script_indices"]])
    return {
        "scripts_total": len(scripts),
        "mission_trigger_count": len(calls),
        "direct_mission_calls": direct,
        "calls_by_trigger": [
            {"trigger_index": row["trigger_index"], "scripts": labels(row["script_indices"])}
            for row in calls if row["script_indices"]
        ],
        "bot_scripts_directly_called": [name for name in direct if "bot" in name],
        "note": "Static call references, not evidence of executed branches or bot behaviour.",
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--module", required=True, type=Path)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    data = trace(args.module)
    if args.json:
        print(json.dumps(data, indent=2))
    else:
        print("Invasion:", data["mission_trigger_count"], "triggers;",
              data["scripts_total"], "compiled scripts")
        print("Direct bot-script calls:", ", ".join(data["bot_scripts_directly_called"]))
        for call in data["calls_by_trigger"]:
            if any("bot" in name for name in call["scripts"]):
                print("Trigger", call["trigger_index"], "=>", ", ".join(call["scripts"]))
        print(data["note"])


if __name__ == "__main__":
    main()
