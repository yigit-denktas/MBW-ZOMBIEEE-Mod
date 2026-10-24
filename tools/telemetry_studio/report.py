"""Markdown iteration receipt for the telemetry auto-research loop."""

from __future__ import annotations

from typing import Any


def _fmt(value: Any) -> str:
    return "unknown" if value is None else str(value)


def _safe_root(value: Any) -> str:
    """Never put a personal/local absolute path in a committable receipt."""
    if not value:
        return "unknown"
    text = str(value).replace("\\", "/")
    parts = [part for part in text.split("/") if part]
    base = parts[-1] if parts else text
    if text.startswith("/") or (len(parts) > 1 and ":" in parts[0]):
        return f"<local-bundle>/{base}"
    return text


def render_iteration_report(
    baseline: dict[str, Any],
    candidate: dict[str, Any] | None = None,
    *,
    hypothesis: str = "",
    next_hypothesis: str = "",
    compare: dict[str, Any] | None = None,
    perf: dict[str, Any] | None = None,
    anomalies: list[dict[str, Any]] | None = None,
    static: dict[str, Any] | None = None,
    notes: str = "",
) -> str:
    lines: list[str] = []
    lines.append("# Telemetry Studio iteration receipt")
    lines.append("")
    lines.append("**Status:** auto-research iteration; no acceptance, no fabricated data. "
                 "`runtime_verified` remains false until a sealed run demonstrates the claim.")
    lines.append("")
    lines.append("## Receipt")
    lines.append("")
    lines.append(f"- baseline: `{_safe_root(baseline.get('root'))}` "
                 f"(verified={_fmt(baseline.get('verified'))}, "
                 f"events={len(baseline.get('events') or [])})")
    if candidate:
        lines.append(f"- candidate: `{_safe_root(candidate.get('root'))}` "
                     f"(verified={_fmt(candidate.get('verified'))}, "
                     f"events={len(candidate.get('events') or [])})")
    if hypothesis:
        lines.append(f"- hypothesis: {hypothesis}")
    lines.append("")

    lines.append("## Gaps / unknown")
    lines.append("")
    gaps = list(baseline.get("gaps") or [])
    if candidate:
        gaps.extend(candidate.get("gaps") or [])
    if perf and perf.get("unknown"):
        gaps.extend(f"perf_unknown:{name}" for name in perf["unknown"])
    if gaps:
        for gap in sorted(set(gaps)):
            lines.append(f"- {gap}")
    else:
        lines.append("- none reported")
    lines.append("")

    if compare:
        lines.append("## Metric deltas (baseline -> candidate)")
        lines.append("")
        lines.append("| metric | baseline | candidate | delta | heuristic |")
        lines.append("| --- | ---: | ---: | ---: | --- |")
        for key, row in compare.get("deltas", {}).items():
            lines.append(f"| {key} | {_fmt(row['baseline'])} | {_fmt(row['candidate'])} | "
                         f"{_fmt(row['delta'])} | {row['verdict']} |")
        lines.append("")
        lines.append(f"_Note: {compare.get('note', 'deltas are not acceptance')}_")
        lines.append("")

    if perf:
        lines.append("## Performance proxies")
        lines.append("")
        for key in ("duration_seconds", "heartbeats", "heartbeat_coverage",
                    "missing_heartbeat_intervals",
                    "ai_samples_per_heartbeat", "combat_samples_per_heartbeat",
                    "agents_mean", "engine_error_total", "engine_error_breakdown",
                    "engine_errors_per_second", "max_log_bytes",
                    "cpu_seconds", "peak_memory_kib"):
            lines.append(f"- {key}: {_fmt(perf.get(key))}")
        stats = perf.get("wse2_stats") or {}
        lines.append(f"- wse2_stats_available: {_fmt(stats.get('available'))}")
        lines.append("")

    if anomalies is not None:
        lines.append("## Anomalies")
        lines.append("")
        if anomalies:
            for item in anomalies:
                lines.append(f"- [{item.get('severity')}] {item.get('code')}: {item.get('detail')}")
        else:
            lines.append("- none detected")
        lines.append("")

    if static:
        lines.append("## Static module inspection")
        lines.append("")
        delays = static.get("trigger_delays") or {}
        top = sorted(delays.items(), key=lambda kv: (-int(kv[1]), kv[0]))[:8]
        lines.append(f"- trigger-like lines (all mission templates): "
                     f"{_fmt(static.get('trigger_count'))}; top delays: "
                     f"{', '.join(f'{k}x{v}' for k, v in top) or 'unknown'}")
        slots = static.get("slow_894_slots") or []
        lines.append(f"- slow 894 slot writes: {_fmt(static.get('slow_894_slot_writes'))} "
                     f"(first slots {slots[:12]}{'...' if len(slots) > 12 else ''})")
        lines.append(f"- invalid faction literals (`502 3 -1`): "
                     f"{_fmt(static.get('invalid_faction_literal_ops'))}")
        lines.append(f"- 2093 speed triggers: {_fmt(static.get('speed_trigger_count'))}")
        lines.append(f"- gaps: {_fmt(static.get('gaps'))}")
        lines.append("")

    lines.append("## Next hypothesis")
    lines.append("")
    lines.append(next_hypothesis or "unknown — waiting for a sealed run")
    lines.append("")
    if notes:
        lines.append("## Notes")
        lines.append("")
        lines.append(notes)
        lines.append("")
    return "\n".join(lines) + "\n"
