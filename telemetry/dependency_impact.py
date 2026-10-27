"""Structural dependency impact for `progress/ledger.json`.

Answers "what depends on this item, directly and transitively?" and ranks
unresolved items by how much open work sits downstream. It also reports owner
and queue rollups, dangling/duplicate edges and dependency cycles.

The ledger carries no duration, effort, start/finish, float or critical-path
data, so this module does **not** estimate dates or schedules. The JSON report
contains an explicit ``schedule_unknown`` gap and ``schedule.status`` is
``unknown``; a cycle is reported as undefined dependency order, not as a
schedule conclusion. Descriptive analysis only: ``done`` is not acceptance.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, Iterable

SCHEMA = "zombieee.dependency-impact.v1"
SCHEDULE_UNKNOWN = "schedule_unknown"
UNASSIGNED = "unassigned"

_DEFAULT_SOURCE = "progress/ledger.json"
_PRIORITY_ORDER = {"P0": 0, "P1": 1, "P2": 2, "P3": 3}


def _text(value: Any, default: str = "") -> str:
    if value is None:
        return default
    text = str(value).strip()
    return text or default


def _string_list(value: Any) -> list[str]:
    """Unique, non-empty strings in input order."""
    if value is None:
        return []
    if not isinstance(value, (list, tuple, set)):
        value = [value]
    seen: set[str] = set()
    out: list[str] = []
    for entry in value:
        text = _text(entry)
        if text and text not in seen:
            seen.add(text)
            out.append(text)
    return out


def _state(item: dict) -> str:
    return _text(item.get("state"), "unknown").lower()


def _priority_rank(priority: str) -> int:
    return _PRIORITY_ORDER.get(priority.upper(), 9)


def _owner(item: dict) -> str:
    return _text(item.get("owner"), UNASSIGNED)


def _queue(item: dict) -> str:
    # The ledger field is implementationLane; "queue" is the handoff term.
    return _text(item.get("implementationLane"), UNASSIGNED)


def load_ledger(path: str | Path) -> dict:
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError("ledger root must be a JSON object")
    if not isinstance(data.get("items"), list):
        raise ValueError("ledger 'items' must be a list")
    return data


def ledger_digest(ledger: dict) -> str:
    """Deterministic content digest (not a byte hash of the source file)."""
    canonical = json.dumps(ledger, sort_keys=True, separators=(",", ":"),
                           ensure_ascii=True)
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def _closure(start: str, edges: dict[str, Iterable[str]]) -> set[str]:
    """Nodes reachable from ``start`` (excluding ``start`` itself)."""
    seen: set[str] = set()
    stack = list(edges.get(start, ()))
    while stack:
        node = stack.pop()
        if node in seen:
            continue
        seen.add(node)
        stack.extend(edges.get(node, ()))
    seen.discard(start)
    return seen


def _strong_components(nodes: list[str],
                       adjacency: dict[str, Iterable[str]]) -> list[list[str]]:
    """Kosaraju SCCs, iterative and deterministic (sorted traversal)."""
    order: list[str] = []
    visited: set[str] = set()
    for root in nodes:
        if root in visited:
            continue
        visited.add(root)
        stack: list[tuple[str, Iterable[str]]] = [
            (root, iter(sorted(adjacency.get(root, ()))))]
        while stack:
            node, neighbours = stack[-1]
            advanced = False
            for neighbour in neighbours:
                if neighbour not in visited:
                    visited.add(neighbour)
                    stack.append((neighbour,
                                  iter(sorted(adjacency.get(neighbour, ())))))
                    advanced = True
                    break
            if not advanced:
                order.append(node)
                stack.pop()

    reverse: dict[str, set[str]] = defaultdict(set)
    for node in nodes:
        for neighbour in adjacency.get(node, ()):
            reverse[neighbour].add(node)

    assigned: set[str] = set()
    components: list[list[str]] = []
    for root in reversed(order):
        if root in assigned:
            continue
        assigned.add(root)
        component: list[str] = []
        stack = [root]
        while stack:
            node = stack.pop()
            component.append(node)
            for neighbour in sorted(reverse.get(node, ())):
                if neighbour not in assigned:
                    assigned.add(neighbour)
                    stack.append(neighbour)
        components.append(sorted(component))
    components.sort()
    return components


def _md_cell(value: Any) -> str:
    return _text(value).replace("|", "\\|").replace("\n", " ")


def analyze(ledger: dict, *, source_path: str = _DEFAULT_SOURCE,
            top_n: int = 15) -> dict[str, Any]:
    """Build the structural dependency-impact report.

    ``top_n`` only limits the Markdown blocker table; JSON always contains the
    complete ranking.
    """
    if not isinstance(ledger, dict):
        raise ValueError("ledger root must be a JSON object")
    raw_items = ledger.get("items")
    if not isinstance(raw_items, list):
        raise ValueError("ledger 'items' must be a list")

    by_id: dict[str, dict] = {}
    duplicate_ids: list[str] = []
    malformed: list[int] = []
    for index, raw in enumerate(raw_items):
        if not isinstance(raw, dict):
            malformed.append(index)
            continue
        item_id = _text(raw.get("id"))
        if not item_id:
            malformed.append(index)
            continue
        if item_id in by_id:
            duplicate_ids.append(item_id)
            continue
        by_id[item_id] = raw

    nodes = sorted(by_id)
    state_of = {node: _state(by_id[node]) for node in nodes}
    priority_of = {node: _text(by_id[node].get("priority")) for node in nodes}
    required_of = {node: bool(by_id[node].get("required", False))
                   for node in nodes}
    owner_of = {node: _owner(by_id[node]) for node in nodes}
    queue_of = {node: _queue(by_id[node]) for node in nodes}

    depends_on: dict[str, list[str]] = {}
    unmapped: dict[str, list[str]] = {}
    dangling: list[dict[str, str]] = []
    for node in nodes:
        raw = by_id[node]
        declared = _string_list(raw.get("dependsOn"))
        known: list[str] = []
        for dependency in declared:
            if dependency in by_id:
                known.append(dependency)
            else:
                dangling.append({"item": node, "dependency": dependency})
        depends_on[node] = sorted(set(known))
        unmapped[node] = _string_list(raw.get("unmappedDependencies"))

    dependents: dict[str, set[str]] = defaultdict(set)
    for node in nodes:
        for dependency in depends_on[node]:
            dependents[dependency].add(node)

    transitive_dependents = {
        node: _closure(node, dependents) for node in nodes}
    transitive_prerequisites = {
        node: _closure(node, depends_on) for node in nodes}

    direct_dependents = {
        node: sorted(dependents.get(node, ())) for node in nodes}
    unresolved_prerequisites = {
        node: sorted(p for p in transitive_prerequisites[node]
                     if state_of[p] != "done")
        for node in nodes}

    components = _strong_components(
        nodes, {node: sorted(dependents.get(node, ())) for node in nodes})
    cycles: list[dict[str, Any]] = []
    cycle_of: dict[str, str] = {}
    for component in components:
        self_loop = (len(component) == 1
                     and component[0] in depends_on[component[0]])
        if len(component) < 2 and not self_loop:
            continue
        cycle_id = f"CYCLE-{len(cycles) + 1}"
        members = set(component)
        edges = sorted(
            [left, right]
            for left in component
            for right in dependents.get(left, ())
            if right in members
        )
        external_dependents = sorted(
            {dependent for member in component
             for dependent in transitive_dependents[member]
             if dependent not in members}
        )
        for member in component:
            cycle_of[member] = cycle_id
        cycles.append({
            "cycle_id": cycle_id,
            "members": sorted(component),
            "size": len(component),
            "edges": edges,
            "note": ("dependency order is undefined inside this cycle; "
                     "no schedule or ordering conclusion can be drawn"),
            "blocked_members": sorted(
                member for member in component if by_id[member].get("blocked")),
            "open_members": sorted(
                member for member in component if state_of[member] != "done"),
            "external_dependents": external_dependents,
        })

    def open_dependent_count(node: str) -> int:
        return sum(1 for dependent in transitive_dependents[node]
                   if state_of[dependent] != "done")

    def required_open_dependent_count(node: str) -> int:
        return sum(1 for dependent in transitive_dependents[node]
                   if state_of[dependent] != "done" and required_of[dependent])

    items: list[dict[str, Any]] = []
    for node in nodes:
        raw = by_id[node]
        item = {
            "id": node,
            "title": _text(raw.get("title")),
            "state": state_of[node],
            "blocked": bool(raw.get("blocked", False)),
            "required": required_of[node],
            "priority": priority_of[node],
            "owner": owner_of[node],
            "queue": queue_of[node],
            "group_id": _text(raw.get("groupId")),
            "milestone_id": _text(raw.get("milestoneId")),
            "depends_on": depends_on[node],
            "unmapped_dependencies": unmapped[node],
            "direct_dependents": direct_dependents[node],
            "direct_dependents_count": len(direct_dependents[node]),
            "transitive_dependents_count": len(transitive_dependents[node]),
            "open_transitive_dependents_count": open_dependent_count(node),
            "required_open_transitive_dependents_count":
                required_open_dependent_count(node),
            "unresolved_prerequisites": unresolved_prerequisites[node],
            "impacted": (state_of[node] != "done"
                         and bool(unresolved_prerequisites[node])),
            "in_cycle": node in cycle_of,
            "cycle_id": cycle_of.get(node),
        }
        items.append(item)

    # Consequential blockers: unresolved items with open work downstream.
    candidates: list[dict[str, Any]] = []
    for node in nodes:
        if state_of[node] == "done":
            continue
        open_dependents = open_dependent_count(node)
        if open_dependents == 0:
            continue
        candidates.append({
            "id": node,
            "title": _text(by_id[node].get("title")),
            "state": state_of[node],
            "blocked": bool(by_id[node].get("blocked", False)),
            "priority": priority_of[node],
            "owner": owner_of[node],
            "queue": queue_of[node],
            "direct_dependents": direct_dependents[node],
            "direct_dependents_count": len(direct_dependents[node]),
            "transitive_dependents_count": len(transitive_dependents[node]),
            "open_transitive_dependents_count": open_dependents,
            "required_open_transitive_dependents_count":
                required_open_dependent_count(node),
            "in_cycle": node in cycle_of,
            "cycle_id": cycle_of.get(node),
        })
    candidates.sort(key=lambda row: (
        -row["open_transitive_dependents_count"],
        -row["required_open_transitive_dependents_count"],
        0 if row["blocked"] else 1,
        _priority_rank(row["priority"]),
        row["id"],
    ))
    for rank, row in enumerate(candidates, start=1):
        row["rank"] = rank

    def rollup(key_name: str, key_of: dict[str, str]) -> list[dict[str, Any]]:
        grouped: dict[str, list[str]] = defaultdict(list)
        for node in nodes:
            grouped[key_of[node]].append(node)
        rows: list[dict[str, Any]] = []
        for name in sorted(grouped):
            members = grouped[name]
            direct_union: set[str] = set()
            transitive_union: set[str] = set()
            for member in members:
                direct_union.update(direct_dependents[member])
                transitive_union.update(transitive_dependents[member])
            open_union = {node for node in transitive_union
                          if state_of[node] != "done"}
            rows.append({
                key_name: name,
                "items": len(members),
                "open": sum(1 for member in members
                            if state_of[member] != "done"),
                "done": sum(1 for member in members
                            if state_of[member] == "done"),
                "blocked": sum(1 for member in members
                               if by_id[member].get("blocked")),
                "impacted": sum(
                    1 for member in members
                    if state_of[member] != "done"
                    and unresolved_prerequisites[member]),
                "in_cycle": sum(1 for member in members
                                if member in cycle_of),
                "items_with_dependents": sum(
                    1 for member in members if transitive_dependents[member]),
                "direct_dependents": len(direct_union),
                "transitive_dependents": len(transitive_union),
                "open_transitive_dependents": len(open_union),
            })
        return rows

    owners = rollup("owner", owner_of)
    queues = rollup("queue", queue_of)

    queue_groups: dict[tuple[str, str], list[str]] = defaultdict(list)
    for node in nodes:
        queue_groups[(owner_of[node], queue_of[node])].append(node)
    owner_queue = []
    for (owner, queue), members in sorted(queue_groups.items()):
        owner_queue.append({
            "owner": owner,
            "queue": queue,
            "items": len(members),
            "open": sum(1 for member in members if state_of[member] != "done"),
            "blocked": sum(1 for member in members if by_id[member].get("blocked")),
            "impacted": sum(
                1 for member in members
                if state_of[member] != "done"
                and unresolved_prerequisites[member]),
        })

    state_counts = Counter(state_of.values())
    done_with_open_prereqs = sorted(
        node for node in nodes
        if state_of[node] == "done" and unresolved_prerequisites[node])
    missing_owner_or_queue = sorted(
        node for node in nodes
        if owner_of[node] == UNASSIGNED or queue_of[node] == UNASSIGNED)
    blocked_without_open_dependents = sorted(
        node for node in nodes
        if by_id[node].get("blocked") and not open_dependent_count(node))

    gaps: list[dict[str, Any]] = [{
        "code": SCHEDULE_UNKNOWN,
        "message": ("The ledger has no duration, effort, start/finish, float or "
                    "critical-path data. This report is structural dependency "
                    "impact only; no schedule, date, effort or float is estimated."),
        "details": {
            "fields_unavailable": ["duration", "effort", "start", "finish",
                                   "float", "critical_path"],
            "durations_used": False,
            "effort_estimated": False,
            "float_computed": False,
            "cpm_computed": False,
        },
    }]
    if not nodes:
        gaps.append({
            "code": "ledger_has_no_items",
            "message": "The ledger contains no usable items; impact is unknown.",
        })
    if malformed:
        gaps.append({
            "code": "malformed_item",
            "message": f"{len(malformed)} ledger entries are not objects with an id.",
            "details": {"item_indexes": malformed},
        })
    if duplicate_ids:
        gaps.append({
            "code": "duplicate_item_id",
            "message": "Duplicate ids were ignored after the first occurrence.",
            "details": {"ids": sorted(set(duplicate_ids))},
        })
    if dangling:
        gaps.append({
            "code": "dangling_dependency",
            "message": ("Some dependsOn ids do not exist in the ledger; those "
                        "edges are excluded, so downstream impact through them "
                        "is unknown."),
            "details": {"dependencies": dangling},
        })
    unmapped_entries = [
        {"item": node, "dependencies": unmapped[node]}
        for node in nodes if unmapped[node]
    ]
    if unmapped_entries:
        gaps.append({
            "code": "unmapped_dependency",
            "message": ("Some items declare unmappedDependencies; they are not "
                        "connectable to ledger nodes and are not counted as edges."),
            "details": {"items": unmapped_entries},
        })
    if cycles:
        gaps.append({
            "code": "dependency_cycle",
            "message": ("Dependency cycles make topological order undefined; "
                        "cycle members are reported without a schedule conclusion."),
            "details": {"cycles": [cycle["cycle_id"] for cycle in cycles]},
        })
    if done_with_open_prereqs:
        gaps.append({
            "code": "done_item_with_unresolved_prerequisite",
            "message": ("Some items are marked done while a transitive "
                        "prerequisite is not done; this is a ledger integrity gap."),
            "details": {"ids": done_with_open_prereqs},
        })
    if missing_owner_or_queue:
        gaps.append({
            "code": "missing_owner_or_queue",
            "message": ("Some items have no owner or no implementationLane; they "
                        "are rolled up as 'unassigned'."),
            "details": {"ids": missing_owner_or_queue},
        })

    return {
        "schema": SCHEMA,
        "source": {
            "path": source_path,
            "contract_version": ledger.get("contractVersion"),
            "ledger_sha256": ledger_digest(ledger),
        },
        "definitions": {
            "dependency_edge": ("dependent -> prerequisite (ledger dependsOn); "
                                "impact flows prerequisite -> dependent"),
            "direct_dependents": "items that list this item in dependsOn",
            "transitive_dependents": ("all items reachable through the reversed "
                                      "dependsOn graph, excluding self"),
            "impacted": ("an open item (state != done) with at least one "
                         "transitive prerequisite not state=done; impacted does "
                         "not mean blocked, failed or undelivered"),
            "done": "state == 'done'; done is not acceptance",
            "consequential_blocker": ("not done and has at least one not-done "
                                      "transitive dependent"),
            "blocker_ranking": ("open transitive dependents desc, required open "
                                "transitive dependents desc, explicit blocked "
                                "first, priority P0..P3, then id. Integer graph "
                                "counts only; no duration/effort/float/CPM"),
            "cycle": ("strongly connected component in the dependency graph; "
                      "dependency order inside it is undefined"),
        },
        "schedule": {
            "status": "unknown",
            "reason": ("No durations or effort exist in the ledger; no schedule, "
                       "float or critical path is computed."),
            "fields_unavailable": ["duration", "effort", "start", "finish",
                                   "float", "critical_path"],
            "durations_used": False,
            "effort_estimated": False,
            "float_computed": False,
            "cpm_computed": False,
        },
        "summary": {
            "items": len(nodes),
            "dependencies": sum(len(depends_on[node]) for node in nodes),
            "items_with_dependencies": sum(1 for node in nodes
                                           if depends_on[node]),
            "items_with_dependents": sum(1 for node in nodes
                                         if transitive_dependents[node]),
            "roots": sum(1 for node in nodes if not depends_on[node]),
            "leaves": sum(1 for node in nodes if not direct_dependents[node]),
            "states": dict(sorted(state_counts.items())),
            "done": state_counts.get("done", 0),
            "open": len(nodes) - state_counts.get("done", 0),
            "blocked": sum(1 for node in nodes if by_id[node].get("blocked")),
            "impacted": sum(
                1 for node in nodes
                if state_of[node] != "done"
                and unresolved_prerequisites[node]),
            "in_cycle": len(cycle_of),
            "cycles": len(cycles),
            "consequential_blockers": len(candidates),
            "dangling_dependencies": len(dangling),
            "unmapped_dependencies": sum(len(unmapped[node]) for node in nodes),
            "owners": len(owners),
            "queues": len(queues),
        },
        "gaps": gaps,
        "items": items,
        "consequential_blockers": candidates,
        "cycles": cycles,
        "dangling_dependencies": dangling,
        "owners": owners,
        "queues": queues,
        "owner_queue": owner_queue,
        "integrity": {
            "duplicate_item_ids": sorted(set(duplicate_ids)),
            "malformed_item_indexes": malformed,
            "done_with_unresolved_prerequisites": done_with_open_prereqs,
            "missing_owner_or_queue": missing_owner_or_queue,
            "blocked_without_open_dependents": blocked_without_open_dependents,
        },
        "markdown_top_n": max(0, int(top_n)),
    }


def render_markdown(report: dict, *, top_n: int | None = None) -> str:
    summary = report["summary"]
    limit = report.get("markdown_top_n", 15) if top_n is None else max(0, top_n)
    lines: list[str] = [
        "# Dependency impact (structural; schedule unknown)",
        "",
        f"- source: `{report['source']['path']}` "
        f"(contract {report['source'].get('contract_version')}, "
        f"sha256 `{report['source']['ledger_sha256'][:16]}...`)",
        f"- schema: `{report['schema']}`",
        f"- items: {summary['items']} | dependencies: {summary['dependencies']} "
        f"| open: {summary['open']} | cycles: {summary['cycles']}",
        "",
        "> **Schedule unknown.** No duration, effort, start/finish, float or "
        "critical path is computed. This is structural impact only; a cycle is "
        "undefined dependency order, not a schedule conclusion.",
        "",
        "## Summary",
        "",
        f"- states: {summary['states']}",
        f"- done: {summary['done']} | open: {summary['open']} | "
        f"blocked flag: {summary['blocked']} | impacted: {summary['impacted']}",
        f"- roots: {summary['roots']} | leaves: {summary['leaves']} | "
        f"cycle members: {summary['in_cycle']}",
        f"- consequential blockers: {summary['consequential_blockers']} | "
        f"dangling deps: {summary['dangling_dependencies']} | "
        f"unmapped deps: {summary['unmapped_dependencies']}",
        "",
        "## Consequential blockers",
        "",
        "Ranking: open transitive dependents, required open dependents, explicit "
        "blocked flag, priority, id. Counts are graph facts, not effort or "
        "duration.",
        "",
        "| # | item | state | blocked | owner | queue | direct | transitive | "
        "open trans. | required open |",
        "| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |",
    ]
    blockers = report.get("consequential_blockers") or []
    shown = blockers[:limit]
    for row in shown:
        lines.append(
            f"| {row['rank']} | `{_md_cell(row['id'])}` "
            f"{_md_cell(row['title'])} | {_md_cell(row['state'])} | "
            f"{'yes' if row['blocked'] else 'no'} | {_md_cell(row['owner'])} | "
            f"{_md_cell(row['queue'])} | {row['direct_dependents_count']} | "
            f"{row['transitive_dependents_count']} | "
            f"{row['open_transitive_dependents_count']} | "
            f"{row['required_open_transitive_dependents_count']} |")
    if not blockers:
        lines.append("| - | no consequential blockers | - | - | - | - | - | - | - | - |")
    if len(blockers) > len(shown):
        lines.append("")
        lines.append(f"Showing {len(shown)} of {len(blockers)} blockers; the JSON "
                     "report contains the full ranking.")
    lines += ["", "## Cycles", ""]
    if report.get("cycles"):
        for cycle in report["cycles"]:
            edges = ", ".join(f"`{left}` -> `{right}`"
                              for left, right in cycle["edges"])
            lines.append(f"- `{cycle['cycle_id']}`: members "
                         f"{', '.join(f'`{member}`' for member in cycle['members'])}"
                         f"; edges (prerequisite -> dependent): {edges}")
            lines.append(f"  - {cycle['note']}")
    else:
        lines.append("- none")
    lines += ["", "## Owner rollup", "",
              "| owner | items | open | blocked | impacted | cycle | direct deps | "
              "transitive deps | open transitive |",
              "| --- | --- | --- | --- | --- | --- | --- | --- | --- |"]
    for row in report.get("owners") or []:
        lines.append(
            f"| {_md_cell(row['owner'])} | {row['items']} | {row['open']} | "
            f"{row['blocked']} | {row['impacted']} | {row['in_cycle']} | "
            f"{row['direct_dependents']} | {row['transitive_dependents']} | "
            f"{row['open_transitive_dependents']} |")
    lines += ["", "## Queue rollup (implementationLane)", "",
              "| queue | items | open | blocked | impacted | cycle | direct deps | "
              "transitive deps | open transitive |",
              "| --- | --- | --- | --- | --- | --- | --- | --- | --- |"]
    for row in report.get("queues") or []:
        lines.append(
            f"| {_md_cell(row['queue'])} | {row['items']} | {row['open']} | "
            f"{row['blocked']} | {row['impacted']} | {row['in_cycle']} | "
            f"{row['direct_dependents']} | {row['transitive_dependents']} | "
            f"{row['open_transitive_dependents']} |")
    lines += ["", "## Gaps", ""]
    for gap in report.get("gaps") or []:
        lines.append(f"- `{gap['code']}`: {_md_cell(gap['message'])}")
    lines += ["", "## Integrity notes", ""]
    integrity = report.get("integrity") or {}
    notes = [
        ("duplicate item ids", integrity.get("duplicate_item_ids")),
        ("done with unresolved prerequisites",
         integrity.get("done_with_unresolved_prerequisites")),
        ("missing owner/queue", integrity.get("missing_owner_or_queue")),
        ("blocked without open dependents",
         integrity.get("blocked_without_open_dependents")),
    ]
    for label, ids in notes:
        lines.append(f"- {label}: {', '.join(f'`{entry}`' for entry in ids) or 'none'}")
    lines += ["", "Structural report only: `done` is not acceptance, and no "
                  "runtime or schedule claim is made.", ""]
    return "\n".join(lines)


def write_outputs(report: dict, *, json_path: str | Path | None = None,
                  md_path: str | Path | None = None,
                  top_n: int | None = None) -> dict[str, str]:
    written: dict[str, str] = {}
    if json_path is not None:
        path = Path(json_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n",
                        encoding="utf-8")
        written["json"] = str(path)
    if md_path is not None:
        path = Path(md_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(render_markdown(report, top_n=top_n), encoding="utf-8")
        written["markdown"] = str(path)
    return written


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Structural dependency impact from progress/ledger.json "
                    "(no schedule/float/CPM estimation)")
    parser.add_argument("--ledger", type=Path, default=Path(_DEFAULT_SOURCE))
    parser.add_argument("--json-out", type=Path, default=None)
    parser.add_argument("--md-out", type=Path, default=None)
    parser.add_argument("--top", type=int, default=15,
                        help="blocker rows in Markdown (JSON keeps all)")
    args = parser.parse_args(argv)

    ledger = load_ledger(args.ledger)
    report = analyze(ledger, source_path=str(args.ledger), top_n=args.top)
    if args.json_out is None and args.md_out is None:
        print(json.dumps(report, indent=2, sort_keys=True))
        return 0
    written = write_outputs(report, json_path=args.json_out,
                            md_path=args.md_out, top_n=args.top)
    print(json.dumps(written, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
