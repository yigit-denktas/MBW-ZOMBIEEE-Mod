"""Fresh-loop runner for the telemetry auto-research loop.

Records an iteration receipt from a baseline/candidate pair, appends to a
workspace state file, and requires an explicit decision. It never launches or
seals the game; D supplies sealed bundles. Absence of a candidate/parameters or
a failed bundle leaves the iteration ``pending`` — it is not fabricated.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .anomaly import detect_anomalies
from .compare import compare_ingests
from .ingest import ingest_bundle
from .perf import analyze_performance
from .report import render_iteration_report

LOOP_SCHEMA = "zombieee.telemetry-loop.v1"
DECISIONS = ("pending", "keep", "discard")


def run_iteration(
    baseline: Path,
    candidate: Path | None,
    *,
    hypothesis: str,
    next_hypothesis: str,
    decision: str = "pending",
    out_dir: Path | None = None,
    state_path: Path | None = None,
    allow_unsealed: bool = False,
    module: Path | None = None,
) -> dict[str, Any]:
    if decision not in DECISIONS:
        raise ValueError(f"decision must be one of {DECISIONS}")
    base_ingest = ingest_bundle(baseline, allow_unsealed=allow_unsealed)
    cand_ingest = (ingest_bundle(candidate, allow_unsealed=allow_unsealed)
                   if candidate is not None else None)
    comparison = compare_ingests(base_ingest, cand_ingest) if cand_ingest else None
    use = cand_ingest or base_ingest
    perf = analyze_performance(use)
    anomalies = detect_anomalies(use, perf)
    static = None
    if module is not None:
        from .static_inspect import inspect_module
        static = inspect_module(module)
    text = render_iteration_report(
        base_ingest, cand_ingest, hypothesis=hypothesis,
        next_hypothesis=next_hypothesis, compare=comparison, perf=perf,
        anomalies=anomalies, static=static,
        notes=("Generator: tools.telemetry_studio.loop. Decision is explicit; "
               "no acceptance/causality claim."))
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    out_dir = Path(out_dir) if out_dir else Path("telemetry/iterations")
    out_dir.mkdir(parents=True, exist_ok=True)
    receipt_path = out_dir / f"iteration-{stamp}.md"
    receipt_path.write_text(text, encoding="utf-8")
    state_path = Path(state_path) if state_path else out_dir / "loop-state.json"
    state = {"schema": LOOP_SCHEMA, "iterations": []}
    if state_path.is_file():
        try:
            loaded = json.loads(state_path.read_text(encoding="utf-8"))
            if isinstance(loaded, dict) and isinstance(loaded.get("iterations"), list):
                state = loaded
                state["schema"] = LOOP_SCHEMA
        except (OSError, ValueError):
            pass
    entry = {
        "iteration": len(state["iterations"]) + 1,
        "generated_utc": stamp,
        "hypothesis": hypothesis,
        "next_hypothesis": next_hypothesis,
        "decision": decision,
        "baseline": {"root": base_ingest.get("root"),
                     "verified": base_ingest.get("verified")},
        "candidate": ({"root": cand_ingest.get("root"),
                       "verified": cand_ingest.get("verified")}
                      if cand_ingest else None),
        "receipt": str(receipt_path),
        "gaps": sorted(set(
            (base_ingest.get("gaps") or [])
            + ((cand_ingest.get("gaps") or []) if cand_ingest else []))),
        "metrics": {key: perf.get(key) for key in (
            "heartbeats", "tick_cadence_seconds", "missing_heartbeat_intervals",
            "wall_clock_missing_intervals", "engine_error_total",
            "ai_samples_per_heartbeat")},
        "not_acceptance": True,
    }
    state["iterations"].append(entry)
    state_path.write_text(json.dumps(state, indent=2, sort_keys=True) + "\n",
                          encoding="utf-8")
    return {"schema": LOOP_SCHEMA, "receipt": str(receipt_path),
            "state": str(state_path), "entry": entry}
