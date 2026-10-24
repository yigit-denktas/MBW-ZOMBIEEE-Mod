"""Command line entry point for the Telemetry Studio."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from .anomaly import detect_anomalies
from .compare import compare_ingests
from .ingest import IngestError, ingest_bundle
from .perf import analyze_performance
from .report import render_iteration_report
from .schema import schema_catalog
from .static_inspect import inspect_module
from .tail import tail_events


def _dump(data) -> None:
    print(json.dumps(data, indent=2, sort_keys=True))


def _ingest(path: Path, allow_unsealed: bool):
    ingest = ingest_bundle(path, allow_unsealed=allow_unsealed)
    perf = analyze_performance(ingest)
    return ingest, perf


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="python -m tools.telemetry_studio",
                                     description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)

    p_ingest = sub.add_parser("ingest", help="ingest a sealed bundle (or raw log dir)")
    p_ingest.add_argument("bundle", type=Path)
    p_ingest.add_argument("--allow-unsealed", action="store_true")
    p_ingest.add_argument("--json", action="store_true")

    p_perf = sub.add_parser("perf", help="performance/cadence proxies")
    p_perf.add_argument("bundle", type=Path)
    p_perf.add_argument("--allow-unsealed", action="store_true")
    p_perf.add_argument("--json", action="store_true")

    p_anom = sub.add_parser("anomalies", help="anomaly list for a bundle")
    p_anom.add_argument("bundle", type=Path)
    p_anom.add_argument("--allow-unsealed", action="store_true")
    p_anom.add_argument("--json", action="store_true")

    p_cmp = sub.add_parser("compare", help="compare baseline and candidate bundles")
    p_cmp.add_argument("baseline", type=Path)
    p_cmp.add_argument("candidate", type=Path)
    p_cmp.add_argument("--allow-unsealed", action="store_true")
    p_cmp.add_argument("--json", action="store_true")

    p_tail = sub.add_parser("tail", help="parse/print ZDB1 events from a log")
    p_tail.add_argument("log", type=Path)
    p_tail.add_argument("--follow", action="store_true")
    p_tail.add_argument("--from-start", action="store_true")
    p_tail.add_argument("--max-events", type=int, default=None)
    p_tail.add_argument("--json", action="store_true")

    p_inspect = sub.add_parser("inspect", help="static module/trigger inspection")
    p_inspect.add_argument("module", type=Path)
    p_inspect.add_argument("--json", action="store_true")

    p_schema = sub.add_parser("schema", help="event schema/granularity catalog")
    p_schema.add_argument("--json", action="store_true")

    p_report = sub.add_parser("report", help="render an iteration receipt")
    p_report.add_argument("baseline", type=Path)
    p_report.add_argument("candidate", type=Path, nargs="?")
    p_report.add_argument("--out", type=Path, default=None)
    p_report.add_argument("--hypothesis", default="")
    p_report.add_argument("--next", default="")
    p_report.add_argument("--module", type=Path, default=None)
    p_report.add_argument("--allow-unsealed", action="store_true")
    p_report.add_argument("--notes", default="",
                          help="free-form iteration notes (no invented data)")

    args = parser.parse_args(argv)
    try:
        if args.command == "schema":
            return _print(schema_catalog(), args.json)
        if args.command == "tail":
            count = 0
            for event in tail_events(args.log, follow=args.follow,
                                     from_start=args.from_start,
                                     max_events=args.max_events):
                count += 1
                print(json.dumps(event, sort_keys=True) if args.json else event)
            return 0
        if args.command == "inspect":
            return _print(inspect_module(args.module), args.json)
        if args.command == "ingest":
            ingest, _perf = _ingest(args.bundle, args.allow_unsealed)
            ingest.pop("events", None)  # too large for a CLI dump
            return _print(ingest, args.json)
        if args.command == "perf":
            _ingest_data, perf = _ingest(args.bundle, args.allow_unsealed)
            return _print(perf, args.json)
        if args.command == "anomalies":
            ingest, perf = _ingest(args.bundle, args.allow_unsealed)
            return _print(detect_anomalies(ingest, perf), args.json)
        if args.command == "compare":
            base, _ = _ingest(args.baseline, args.allow_unsealed)
            cand, _ = _ingest(args.candidate, args.allow_unsealed)
            return _print(compare_ingests(base, cand), args.json)
        if args.command == "report":
            base, base_perf = _ingest(args.baseline, args.allow_unsealed)
            cand = cand_perf = comparison = None
            if args.candidate:
                cand, cand_perf = _ingest(args.candidate, args.allow_unsealed)
                comparison = compare_ingests(base, cand)
            anomalies = detect_anomalies(cand or base, cand_perf or base_perf)
            static = inspect_module(args.module) if args.module else None
            text = render_iteration_report(
                base, cand, hypothesis=args.hypothesis, next_hypothesis=args.next,
                compare=comparison, perf=cand_perf or base_perf,
                anomalies=anomalies, static=static, notes=args.notes)
            if args.out:
                args.out.parent.mkdir(parents=True, exist_ok=True)
                args.out.write_text(text, encoding="utf-8")
                print(f"wrote {args.out}")
            else:
                print(text)
            return 0
    except (IngestError, OSError, ValueError) as exc:
        print(f"telemetry_studio: {exc}", file=sys.stderr)
        return 2
    return 0


def _print(data, as_json: bool) -> int:
    if as_json:
        _dump(data)
    else:
        if isinstance(data, dict):
            for key, value in data.items():
                print(f"{key}: {value}")
        else:
            print(data)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
