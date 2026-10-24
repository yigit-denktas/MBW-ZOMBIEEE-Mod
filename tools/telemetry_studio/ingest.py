"""Bundle ingestion: sealed recorder bundle -> parsed ZDB1 events + artifact stats."""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

from tools.receipt_summary import (
    ReceiptError,
    parse_zdbi,
    resolve_receipt_root,
    verify_manifest,
)

TEXT_SUFFIXES = (".log", ".txt", ".jsonl")
MAX_TEXT_BYTES = 8 * 1024 * 1024

ERROR_PATTERNS = {
    "script_error": re.compile(r"SCRIPT ERROR", re.IGNORECASE),
    "invalid_faction": re.compile(r"Invalid Faction ID", re.IGNORECASE),
    "invalid_faction_min": re.compile(r"Invalid Faction ID: -2147483648"),
    "invalid_faction_one": re.compile(r"Invalid Faction ID: -1\b"),
    "illegal_lvalue": re.compile(r"Illegal lvalue", re.IGNORECASE),
    "stack_trace": re.compile(r"\bTraceback|stack trace\b", re.IGNORECASE),
}


class IngestError(ValueError):
    """Raised when a bundle cannot be read safely."""


def read_zdbi_lines(text: str) -> list[dict[str, Any]]:
    """Parse ZDB1 lines from a log blob (delegates event parsing to the
    canonical summary parser so both tools agree on fields)."""
    return parse_zdbi(text)


def _candidate_texts(root: Path, members: list[str] | None, sealed: bool) -> list[Path]:
    if sealed:
        paths = [root / name for name in members or []]
    else:
        paths = [p for p in root.rglob("*") if p.is_file()]
    found = []
    for path in paths:
        if path.name == "manifest.json":
            continue
        if path.suffix.lower() not in TEXT_SUFFIXES:
            continue
        try:
            if path.stat().st_size > MAX_TEXT_BYTES:
                continue
        except OSError:
            continue
        found.append(path)
    return sorted(found)


def _read_text(path: Path) -> str:
    try:
        return path.read_bytes()[:MAX_TEXT_BYTES].decode("utf-8", errors="replace")
    except OSError as exc:
        raise IngestError(f"cannot read {path}: {exc}") from exc


def ingest_bundle(target: Path, *, allow_unsealed: bool = False) -> dict[str, Any]:
    """Ingest a sealed bundle (or, explicitly, a raw log directory).

    Returns a dict with parsed events, per-artifact stats, engine error counts,
    recorder receipt fields, schema problems and explicit gaps. Missing data
    stays ``None`` and is named in ``gaps``; nothing is synthesized.
    """
    target = Path(target).expanduser()
    sealed = False
    root = target
    manifest: dict[str, Any] | None = None
    gaps: list[str] = []
    try:
        root = resolve_receipt_root(target)
        manifest = verify_manifest(root)
        sealed = True
    except ReceiptError as exc:
        if not allow_unsealed:
            raise IngestError(f"bundle is not a verified sealed receipt: {exc}") from exc
        gaps.append("unsealed_bundle")
        if not target.is_dir():
            raise IngestError("ingest path is not a directory") from exc

    members = manifest["members"] if manifest else None
    events: list[dict[str, Any]] = []
    seen_lines: dict[str, list[str]] = {}
    artifacts: list[dict[str, Any]] = []
    error_counts: dict[str, dict[str, int]] = {}
    duplicate_line_count = 0

    for path in _candidate_texts(root, members, sealed):
        text = _read_text(path)
        rel = str(path.relative_to(root)).replace("\\", "/")
        parsed = read_zdbi_lines(text)
        zdbi_lines = [line.strip() for line in text.splitlines()
                      if line.strip().startswith("ZDB1|")]
        counts = {name: len(pattern.findall(text)) for name, pattern in ERROR_PATTERNS.items()}
        error_counts[rel] = counts
        artifacts.append({"name": rel, "bytes": len(text.encode("utf-8")),
                          "zdbi_lines": len(zdbi_lines), "events": len(parsed)})
        for event, line in zip(parsed, zdbi_lines):
            if line in seen_lines:
                duplicate_line_count += 1
                seen_lines[line].append(rel)
                continue
            seen_lines[line] = [rel]
            event = dict(event)
            event["sources"] = [rel]
            events.append(event)

    # Error counts repeat per duplicated log copy. Use the max across artifacts
    # (not the sum) so the same engine log copied twice is not double-counted.
    max_errors = {name: max((counts.get(name, 0) for counts in error_counts.values()),
                            default=0) for name in ERROR_PATTERNS}
    recorder = None
    recorder_path = root / "recorder.json"
    if recorder_path.is_file():
        try:
            data = json.loads(recorder_path.read_text(encoding="utf-8"))
            if isinstance(data, dict):
                recorder = data
        except (OSError, json.JSONDecodeError):
            gaps.append("recorder_receipt_unreadable")
    else:
        gaps.append("recorder_receipt_missing")

    problems: list[str] = []
    try:
        from .schema import validate_event
        for event in events:
            problems.extend(validate_event(event))
    except Exception as exc:  # schema problems are diagnostics, never fatal
        gaps.append(f"schema_check_failed:{type(exc).__name__}")
    unknown_kinds: dict[str, int] = {}
    for event in events:
        kind = str(event.get("event"))
        if kind not in unknown_kinds:
            unknown_kinds[kind] = 0
        unknown_kinds[kind] += 1
    if not events:
        gaps.append("no_zdb1_events")

    return {
        "schema": "zombieee.flight.v1",
        "root": str(root),
        "verified": sealed,
        "file_count": manifest["file_count"] if manifest else None,
        "generated_utc": None,
        "artifacts": artifacts,
        "events": events,
        "event_counts": unknown_kinds,
        "duplicate_lines_skipped": duplicate_line_count,
        "schema_problems": problems,
        "error_counts": error_counts,
        "max_errors": max_errors,
        "recorder": recorder,
        "gaps": gaps,
    }
