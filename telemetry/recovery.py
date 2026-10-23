"""Read-only inspection of recoverable local recorder sessions.

A process terminated by the OS may leave redacted snapshots but no final
manifest. Such a session is INCOMPLETE and must NEVER be treated as a
hash-verified shareable flight recording. Nothing is modified or uploaded.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from .flight_recorder import refuse_links_in_tree, verify_recording

MAX_INSPECTED_FILES = 24
MAX_INSPECTED_BYTES = 32 * 1024 * 1024


def inspect_recording(root: Path) -> dict:
    root = Path(root).expanduser().absolute()
    refuse_links_in_tree(root)
    if not root.is_dir():
        raise ValueError("Recorder session not found")
    entries = [p for p in root.rglob("*") if p.is_file()]
    if len(entries) > MAX_INSPECTED_FILES:
        raise ValueError("Recorder session exceeds recovery file limit")
    if sum(p.stat().st_size for p in entries) > MAX_INSPECTED_BYTES:
        raise ValueError("Recorder session exceeds recovery byte limit")
    manifest = root / "manifest.json"
    safe = {
        "schema": "zombieee.flight.recovery.v1",
        "session_complete": False,
        "integrity_verified": False,
        "shareable_without_review": False,
        "manual_privacy_review_required": True,
        "game_runtime": "unknown",
        "simulation": "unknown",
        "observation": "incomplete_recorder_session",
        "available_snapshot_files": sorted(p.name for p in entries
                                            if p.name in ("events.jsonl", "recorder.json")
                                            or p.name.startswith("log_")),
        "caveat": "Partial data is unsealed; missing tail, loss and modification cannot be excluded.",
    }
    if not manifest.exists():
        return safe
    try:
        check = verify_recording(root)
    except (OSError, ValueError, json.JSONDecodeError):
        safe["observation"] = "final_manifest_invalid"
        return safe
    safe.update({
        "session_complete": True,
        "integrity_verified": True,
        "observation": "complete_hash_verified",
        "file_count": check["file_count"],
        "caveat": "SHA-256 verifies local snapshot integrity, not game readiness, authenticity or privacy.",
    })
    try:
        receipt = json.loads((root / "recorder.json").read_text(encoding="utf-8"))
        safe["simulation"] = receipt.get("simulation", "unknown")
        safe["game_runtime"] = receipt.get("game_runtime", "unknown")
    except (OSError, ValueError):
        pass
    return safe


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("session_root", type=Path)
    args = parser.parse_args()
    try:
        report = inspect_recording(args.session_root)
    except (OSError, ValueError) as error:
        print(json.dumps({"schema": "zombieee.flight.recovery.v1",
                          "observation": "inspection_refused",
                          "reason": type(error).__name__}))
        return 2
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0 if report["session_complete"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
