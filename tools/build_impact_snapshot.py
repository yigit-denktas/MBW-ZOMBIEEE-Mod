#!/usr/bin/env python3
"""Build the committed Pages dependency-impact snapshot.

The site panel only needs the structural summary, the top consequential
blockers, cycles and the explicit ``schedule_unknown`` gap, so this wrapper
projects those fields out of :func:`telemetry.dependency_impact.analyze`
instead of publishing every ledger row.

The output is deterministic (sorted keys, no timestamp, no absolute paths) and
is checked into ``progress/dependency-impact.json``. ``--check`` fails when the
committed snapshot no longer matches the ledger.

The ledger has no duration, effort, start/finish, float or critical-path data.
This tool does not read, infer or invent any of them.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from telemetry import dependency_impact as di  # noqa: E402

SNAPSHOT_SCHEMA = "zombieee.dependency-impact.snapshot.v1"
DEFAULT_LEDGER = ROOT / "progress" / "ledger.json"
DEFAULT_OUT = ROOT / "progress" / "dependency-impact.json"

_BLOCKER_FIELDS = (
    "rank",
    "id",
    "title",
    "state",
    "blocked",
    "priority",
    "owner",
    "queue",
    "direct_dependents_count",
    "transitive_dependents_count",
    "open_transitive_dependents_count",
    "required_open_transitive_dependents_count",
    "in_cycle",
    "cycle_id",
)


def _display_path(path: Path) -> str:
    """Repo-relative POSIX path, never an absolute local path."""
    resolved = Path(path).resolve()
    try:
        return resolved.relative_to(ROOT).as_posix()
    except ValueError:
        return resolved.name


def _blocker(row: dict) -> dict:
    return {key: row.get(key) for key in _BLOCKER_FIELDS}


def _cycle(cycle: dict) -> dict:
    return {
        "cycle_id": cycle.get("cycle_id"),
        "members": cycle.get("members", []),
        "size": cycle.get("size", 0),
        "edges": cycle.get("edges", []),
        "note": cycle.get("note"),
        "blocked_members": cycle.get("blocked_members", []),
        "open_members": cycle.get("open_members", []),
        "external_dependents": cycle.get("external_dependents", []),
    }


def build_snapshot(ledger_path: str | Path = DEFAULT_LEDGER,
                   *, top: int = 10) -> dict:
    """Return the compact, deterministic snapshot for ``ledger_path``."""
    if top < 0:
        raise ValueError("top must be >= 0")
    ledger = di.load_ledger(ledger_path)
    report = di.analyze(ledger, source_path=_display_path(Path(ledger_path)))
    blockers = report.get("consequential_blockers") or []
    definitions = report.get("definitions") or {}
    return {
        "schema": SNAPSHOT_SCHEMA,
        "report_schema": report["schema"],
        "generated_by": "tools/build_impact_snapshot.py",
        "source": report["source"],
        "method": {
            "analysis": "structural dependency graph only",
            "impacted": definitions.get("impacted"),
            "consequential_blocker": definitions.get("consequential_blocker"),
            "blocker_ranking": definitions.get("blocker_ranking"),
            "cycle": definitions.get("cycle"),
        },
        "schedule": report["schedule"],
        "summary": report["summary"],
        "top_blockers": [_blocker(row) for row in blockers[:top]],
        "blockers_total": len(blockers),
        "top_blockers_limit": top,
        "cycles": [_cycle(cycle) for cycle in report.get("cycles") or []],
        "gaps": report.get("gaps") or [],
    }


def render_snapshot(snapshot: dict) -> str:
    return json.dumps(snapshot, indent=2, sort_keys=True) + "\n"


def write_snapshot(snapshot: dict, out: str | Path = DEFAULT_OUT) -> Path:
    path = Path(out)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(render_snapshot(snapshot), encoding="utf-8")
    return path


def snapshot_matches(out: str | Path, snapshot: dict) -> bool:
    path = Path(out)
    if not path.is_file():
        return False
    return path.read_text(encoding="utf-8") == render_snapshot(snapshot)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Build the committed Pages dependency-impact snapshot "
                    "(structural counts only; no schedule data).")
    parser.add_argument("--ledger", type=Path, default=DEFAULT_LEDGER)
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT)
    parser.add_argument("--top", type=int, default=10,
                        help="consequential blocker rows kept in the snapshot")
    parser.add_argument("--check", action="store_true",
                        help="exit 1 if the committed snapshot is stale")
    args = parser.parse_args(argv)

    try:
        snapshot = build_snapshot(args.ledger, top=args.top)
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        print(f"impact snapshot: FAILED: {exc}", file=sys.stderr)
        return 2

    if args.check:
        if snapshot_matches(args.out, snapshot):
            print(f"impact snapshot: up to date ({args.out})")
            return 0
        print(
            f"impact snapshot: STALE ({args.out}); regenerate with "
            f"`python tools/build_impact_snapshot.py`",
            file=sys.stderr,
        )
        return 1

    path = write_snapshot(snapshot, args.out)
    print(json.dumps({
        "out": str(path),
        "items": snapshot["summary"]["items"],
        "impacted": snapshot["summary"]["impacted"],
        "blockers_total": snapshot["blockers_total"],
        "top_blockers_limit": snapshot["top_blockers_limit"],
        "cycles": snapshot["summary"]["cycles"],
    }, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
