"""Bot-vs-bot balance analyzer over sealed ZDB1 bundles.

Read-only analysis: round outcomes/wipe detection from observed team counts,
troop/class contributions, a parameter-sensitivity matrix from run metadata,
and ranked small-change recommendations with explicit confidence and unknowns.
Nothing here invents a winner, a hit, a death cause or causality: values not
observed stay ``None``/``unknown`` and become gaps-as-tasks.

The analyzer is deliberately conservative about rounds: ZDB1 has no explicit
round-end event, so an outcome is only called a wipe when one team's observed
alive count is 0 while the other is >0; a round that resets with both teams
alive is ``round_reset_no_wipe`` (not a win).
"""

from __future__ import annotations

from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

from .anomaly import detect_anomalies
from .perf import analyze_performance

BALANCE_SCHEMA = "zombieee.balance-analysis.v1"
MAX_ROUNDS = 200


def _int(value: Any) -> int | None:
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def _round_samples(ingest: dict[str, Any]) -> list[dict[str, Any]]:
    samples = []
    for event in ingest.get("events") or []:
        kind = event.get("event")
        fields = event.get("fields") or {}
        if kind not in ("heartbeat", "round_started", "wave_started", "wave_change"):
            continue
        samples.append({
            "kind": kind,
            "round": _int(fields.get("round")),
            "round_start": _int(fields.get("round_start")),
            "wave": _int(fields.get("wave")),
            "team0": _int(fields.get("team0")),
            "team1": _int(fields.get("team1")),
            "alive0": _int(fields.get("alive_team0")),
            "alive1": _int(fields.get("alive_team1")),
            "kills0": _int(fields.get("kills_team0")),
            "kills1": _int(fields.get("kills_team1")),
            "tick": _int(fields.get("count")),
        })
    return samples


def _segment_rounds(samples: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Split samples into round segments using round/round_start transitions."""
    rounds: list[dict[str, Any]] = []
    current: list[dict[str, Any]] = []
    current_key = None
    for sample in samples:
        key = sample.get("round")
        if key is None:
            key = sample.get("round_start")
        if key is None:
            key = "unknown"
        if current and key != current_key:
            rounds.append({"key": current_key, "samples": current})
            current = []
            if len(rounds) >= MAX_ROUNDS:
                break
        current_key = key
        current.append(sample)
    if current and len(rounds) < MAX_ROUNDS:
        rounds.append({"key": current_key, "samples": current})
    return rounds


def _round_outcome(samples: list[dict[str, Any]]) -> dict[str, Any]:
    first = samples[0] if samples else {}
    last = samples[-1] if samples else {}
    team0_wipes = team1_wipes = mutual = 0
    basis = "unknown"
    for sample in samples:
        alive0, alive1 = sample.get("alive0"), sample.get("alive1")
        if alive0 == 0 and alive1 and alive1 > 0:
            team0_wipes += 1
            basis = "observed_team0_alive_zero"
            break
        if alive1 == 0 and alive0 and alive0 > 0:
            team1_wipes += 1
            basis = "observed_team1_alive_zero"
            break
        if alive0 == 0 and alive1 == 0:
            mutual += 1
            basis = "observed_both_zero"
            break
    if basis == "unknown" and len(samples) > 1:
        basis = "round_reset_no_observed_wipe"
    outcome = "unknown"
    if team1_wipes:
        outcome = "team0_win"
    elif team0_wipes:
        outcome = "team1_win"
    elif mutual:
        outcome = "mutual_wipe"
    elif basis == "round_reset_no_observed_wipe":
        outcome = "round_reset_no_wipe"
    return {
        "outcome": outcome,
        "basis": basis,
        "team0_wipes": team0_wipes,
        "team1_wipes": team1_wipes,
        "mutual_wipes": mutual,
        "max_wave": max((s.get("wave") or 0) for s in samples) if samples else None,
        "start_team0": first.get("team0"),
        "start_team1": first.get("team1"),
        "end_team0": last.get("team0"),
        "end_team1": last.get("team1"),
        "end_alive0": last.get("alive0"),
        "end_alive1": last.get("alive1"),
        "end_kills0": last.get("kills0"),
        "end_kills1": last.get("kills1"),
        "wall_clock_seconds": None,
    }


def _troop_contributions(ingest: dict[str, Any]) -> dict[str, Any]:
    """Aggregate per-agent final kills by troop from bounded samples.

    This is a lower bound: only sampled agents are visible and only their max
    observed kill count is used; it is not a per-hit or per-death attribution.
    """
    best: dict[tuple[int, int], int] = {}
    names: dict[str, str] = {}
    for event in ingest.get("events") or []:
        fields = event.get("fields") or {}
        for name_key in ("troop_names_team0", "troop_names_team1"):
            raw = fields.get(name_key)
            if not raw:
                continue
            for item in str(raw).split(","):
                if ":" in item:
                    troop_id, name = item.split(":", 1)
                    if troop_id.isdigit():
                        names[troop_id] = name
    for event in ingest.get("events") or []:
        fields = event.get("fields") or {}
        troop = _int(fields.get("troop"))
        team = _int(fields.get("team"))
        agent = _int(fields.get("id"))
        if troop is None or team is None or agent is None:
            continue
        key = (team, agent)
        kills = _int(fields.get("kills"))
        if kills is not None and kills >= 0:
            best[key] = max(best.get(key, 0), kills)
    by_troop: dict[tuple[int, int], int] = defaultdict(int)
    agents_by_troop: dict[tuple[int, int], int] = defaultdict(int)
    for (team, _agent), kills in best.items():
        # troop is recovered separately; rebuild from agent key map below
        pass
    agents: dict[tuple[int, int], int] = {}
    for event in ingest.get("events") or []:
        fields = event.get("fields") or {}
        troop = _int(fields.get("troop"))
        team = _int(fields.get("team"))
        agent = _int(fields.get("id"))
        if troop is None or team is None or agent is None:
            continue
        agents[(team, agent)] = troop
    for (team, agent), kills in best.items():
        troop = agents.get((team, agent))
        if troop is None:
            continue
        by_troop[(team, troop)] += kills
        agents_by_troop[(team, troop)] += 1
    def render(team: int) -> dict[str, Any]:
        rows = []
        for (t, troop), kills in sorted(by_troop.items(), key=lambda kv: (-kv[1], kv[0])):
            if t != team:
                continue
            rows.append({"troop": troop, "name": names.get(str(troop)),
                         "agents_sampled": agents_by_troop[(t, troop)],
                         "kills_lower_bound": kills})
        total = sum(row["kills_lower_bound"] for row in rows)
        for row in rows:
            row["kills_share"] = (round(row["kills_lower_bound"] / total, 3)
                                  if total else None)
        return {"troops": rows, "kills_total_lower_bound": total}
    return {"team0": render(0), "team1": render(1),
            "basis": "max_observed_kills_per_sampled_agent_by_troop",
            "lower_bound": True}


def _run_metrics(ingest: dict[str, Any]) -> dict[str, Any]:
    perf = analyze_performance(ingest)
    samples = _round_samples(ingest)
    rounds = [{"key": seg["key"], **_round_outcome(seg["samples"])}
              for seg in _segment_rounds(samples)]
    outcomes = Counter(row["outcome"] for row in rounds)
    team0_wins = outcomes.get("team0_win", 0)
    team0_wipes = outcomes.get("team1_win", 0)
    known = team0_wins + team0_wipes + outcomes.get("mutual_wipe", 0)
    return {
        "root": ingest.get("root"),
        "verified": ingest.get("verified"),
        "event_count": len(ingest.get("events") or []),
        "rounds": rounds,
        "rounds_observed": len(rounds),
        "outcomes": dict(outcomes),
        "team0_win_rate_known_rounds": (round(team0_wins / known, 3)
                                        if known else None),
        "team0_wipe_rate_known_rounds": (round(team0_wipes / known, 3)
                                         if known else None),
        "max_wave": max((row.get("max_wave") or 0) for row in rounds) if rounds else None,
        "performance": perf,
        "troop_contributions": _troop_contributions(ingest),
    }


def _sensitivity(runs: list[dict[str, Any]], params: dict[str, dict[str, Any]] | None) -> dict[str, Any]:
    if not params:
        return {"available": False, "matrix": [],
                "gaps": ["parameter_metadata_missing"]}
    variants: dict[str, list[tuple[Any, dict[str, Any]]]] = defaultdict(list)
    for run in runs:
        root = str(run.get("root"))
        run_params = params.get(root) or params.get(run.get("name", ""))
        if not run_params:
            continue
        for key, value in run_params.items():
            if isinstance(value, (int, float, str, bool)):
                variants[key].append((value, run))
    matrix = []
    for key, rows in sorted(variants.items()):
        values = sorted({str(value) for value, _run in rows})
        if len(values) < 2:
            continue
        grid = []
        for value in values:
            selected = [run for val, run in rows if str(val) == value]
            outcomes = Counter()
            survivors = []
            waves = []
            for run in selected:
                metrics = run["metrics"]
                outcomes.update(metrics["outcomes"])
                survivors.extend([row.get("end_alive0") for row in metrics["rounds"]
                                  if row.get("end_alive0") is not None])
                waves.append(metrics.get("max_wave") or 0)
            grid.append({
                "value": value,
                "runs": len(selected),
                "team0_win_rate": (round(outcomes.get("team0_win", 0) /
                                         max(1, sum(outcomes.values())), 3)),
                "team0_wipe_rate": (round(outcomes.get("team1_win", 0) /
                                          max(1, sum(outcomes.values())), 3)),
                "survivors_mean": (round(sum(survivors) / len(survivors), 2)
                                   if survivors else None),
                "max_wave_mean": (round(sum(waves) / len(waves), 2) if waves else None),
            })
        win_rates = [row["team0_win_rate"] for row in grid]
        matrix.append({
            "parameter": key,
            "values": grid,
            "sensitivity_team0_win_rate": round(max(win_rates) - min(win_rates), 3),
            "confidence": "low" if min(len(grid), 2) < 2 else "low (confounded if >1 parameter varies)",
            "causal": False,
        })
    matrix.sort(key=lambda row: -row["sensitivity_team0_win_rate"])
    return {"available": bool(matrix), "matrix": matrix,
            "gaps": [] if matrix else ["insufficient_parameter_variants"]}


def analyze_balance(runs: list[dict[str, Any]], params: dict[str, dict[str, Any]] | None = None) -> dict[str, Any]:
    """Analyze ingested bot-vs-bot bundles; returns a receipt dict."""
    analysed = []
    for index, ingest in enumerate(runs):
        metrics = _run_metrics(ingest)
        anomalies = detect_anomalies(ingest, metrics["performance"])
        analysed.append({"name": ingest.get("name") or f"run-{index}",
                         "root": ingest.get("root"), "metrics": metrics,
                         "anomalies": anomalies})
    sensitivity = _sensitivity(analysed, params)
    gaps: list[str] = []
    for row in analysed:
        if not row["metrics"]["verified"]:
            gaps.append("unsealed_bundle")
        if not row["metrics"]["rounds"]:
            gaps.append("no_rounds_observed")
        if any(round_row["wall_clock_seconds"] is None
               for round_row in row["metrics"]["rounds"]):
            gaps.append("wall_clock_round_survival_unknown")
        if row["metrics"]["performance"].get("unknown"):
            gaps.extend(f"perf_unknown:{name}"
                        for name in row["metrics"]["performance"]["unknown"])
    gaps.extend(sensitivity.get("gaps") or [])
    gaps.extend(["round_end_event_missing", "hit_attribution_unavailable",
                 "per_troop_death_unavailable",
                 "kill_causality_not_established"])
    recommendations = []
    for rank, row in enumerate(sensitivity.get("matrix", [])[:3], 1):
        values = row["values"]
        best = max(values, key=lambda item: item["team0_win_rate"])
        recommendations.append({
            "rank": rank,
            "suggestion": f"try a small step of {row['parameter']} toward {best['value']}",
            "parameter": row["parameter"],
            "target_value": best["value"],
            "observed_team0_win_rate": best["team0_win_rate"],
            "confidence": "low-correlational",
            "causal": False,
            "unknowns": ["confounding from other parameters/build differences",
                         "small run count; no round-end event",
                         "execution evidence must come from a new sealed run"],
            "not_acceptance": True,
        })
    if not recommendations:
        gaps.append("insufficient_runs_for_ranked_recommendations")
    gaps_as_tasks = [
        {"suggestion": "add an explicit round-end/wipe event or a documented round boundary",
         "why": "round_end_event_missing"},
        {"suggestion": "trace per-hit/per-death attribution or a kill-event stream",
         "why": "hit_attribution_unavailable"},
        {"suggestion": "record wall-clock round survival time", "why": "wall_clock_round_survival_unknown"},
        {"suggestion": "carry the build/parameter receipt (fire_mode, defender_target, speed, ammo) into every sealed bundle",
         "why": "parameter_metadata_missing"},
        {"suggestion": "record per-troop deaths/alive counts", "why": "per_troop_death_unavailable"},
    ]
    return {
        "schema": BALANCE_SCHEMA,
        "acceptance": "none",
        "runtime_verified": False,
        "causality": "not established",
        "runs": analysed,
        "sensitivity": sensitivity,
        "recommendations": recommendations,
        "gaps": sorted(set(gaps)),
        "gaps_as_tasks": gaps_as_tasks,
        "note": ("wipe/win is called only when an observed alive count is zero; "
                 "rounds without an explicit end are labelled no-wipe/reset; "
                 "sensitivity is correlational and frozen unless parameters were "
                 "carried with the run. Recommendations require a new sealed run."),
    }


def render_balance_report(result: dict[str, Any]) -> str:
    """Markdown iteration receipt for a balance analysis (no acceptance)."""
    lines = ["# Bot-vs-bot balance analysis", "",
             f"Schema: `{result.get('schema')}` | acceptance: **{result.get('acceptance')}** "
             f"| runtime_verified: **{result.get('runtime_verified')}** "
             f"| causality: **{result.get('causality')}**", ""]
    lines.append("## Runs")
    lines.append("")
    lines.append("| run | verified | rounds | team0 wins | team0 wipes | max wave |")
    lines.append("| --- | --- | ---: | ---: | ---: | ---: |")
    for run in result.get("runs", []):
        m = run["metrics"]
        lines.append(f"| `{Path(str(run.get('root') or run.get('name'))).name}` | "
                     f"{m.get('verified')} | {m.get('rounds_observed')} | "
                     f"{m.get('outcomes', {}).get('team0_win', 0)} | "
                     f"{m.get('outcomes', {}).get('team1_win', 0)} | "
                     f"{m.get('max_wave')} |")
    lines.append("")
    lines.append("## Troop/class contributions (lower bound)")
    lines.append("")
    for run in result.get("runs", []):
        c = run["metrics"].get("troop_contributions", {})
        lines.append(f"- `{Path(str(run.get('root') or run.get('name'))).name}`: "
                     f"team0={c.get('team0', {}).get('troops')} "
                     f"kills_lower_bound={c.get('team0', {}).get('kills_total_lower_bound')}; "
                     f"team1={c.get('team1', {}).get('troops')} "
                     f"kills_lower_bound={c.get('team1', {}).get('kills_total_lower_bound')}")
    lines.append("")
    lines.append("## Parameter sensitivity (correlational, not causal)")
    lines.append("")
    sens = result.get("sensitivity", {})
    if sens.get("matrix"):
        lines.append("| parameter | values | win-rate range | confidence | causal |")
        lines.append("| --- | --- | ---: | --- | --- |")
        for row in sens["matrix"]:
            values = ", ".join(f"{v.get('value')}x{v.get('runs')}" for v in row["values"])
            lines.append(f"| {row['parameter']} | {values} | "
                         f"{row['sensitivity_team0_win_rate']} | {row['confidence']} | "
                         f"{row['causal']} |")
    else:
        lines.append("- unavailable: " + ", ".join(sens.get("gaps") or ["no parameter metadata"]))
    lines.append("")
    lines.append("## Ranked small-change recommendations (confidence/unknowns explicit)")
    lines.append("")
    if result.get("recommendations"):
        for rec in result["recommendations"]:
            lines.append(f"{rec['rank']}. {rec['suggestion']} — "
                         f"confidence **{rec['confidence']}**, causal={rec['causal']}; "
                         f"unknowns: {'; '.join(rec['unknowns'])}")
    else:
        lines.append("- none (insufficient runs/parameter variants; not evidence of no effect)")
    lines.append("")
    lines.append("## Gaps (become new tasks)")
    lines.append("")
    for gap in result.get("gaps", []):
        lines.append(f"- {gap}")
    lines.append("")
    lines.append("## Gaps as tasks")
    lines.append("")
    for task in result.get("gaps_as_tasks", []):
        lines.append(f"- {task['suggestion']} — {task['why']}")
    lines.append("")
    lines.append("_" + result.get("note", "") + "_")
    return "\n".join(lines) + "\n"
