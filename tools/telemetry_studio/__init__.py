"""Telemetry Studio: schema, ingest, compare, anomalies, performance and static inspection.

A Ralph-loop toolkit for the ZOMBIEEE telemetry work. It only reads sealed
recorder bundles and module text; it never launches the game and never invents
measurements. Any field that cannot be measured is reported as unknown (None),
not as zero.
"""

from .schema import EVENT_SPECS, SCHEMA, validate_event, schema_catalog
from .ingest import IngestError, ingest_bundle, read_zdbi_lines
from .perf import analyze_performance
from .anomaly import detect_anomalies
from .compare import compare_ingests
from .static_inspect import inspect_module
from .report import render_iteration_report
from .balance import analyze_balance, render_balance_report

__all__ = [
    "EVENT_SPECS",
    "SCHEMA",
    "validate_event",
    "schema_catalog",
    "IngestError",
    "ingest_bundle",
    "read_zdbi_lines",
    "analyze_performance",
    "detect_anomalies",
    "compare_ingests",
    "inspect_module",
    "render_iteration_report",
    "analyze_balance",
    "extract_heatmap",
    "HEATMAP_SCHEMA",
    "probe_health",
    "PROBE_HEALTH_SCHEMA",
    "render_balance_report",
]
