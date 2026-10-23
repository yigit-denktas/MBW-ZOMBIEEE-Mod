#!/usr/bin/env python3
"""Read-only source triage of the first observed dedicated-host City defects.

Two live log facts are frequently mis-attributed, so this tool separates what
the shipped native data can prove from what only an engine run can prove:

1. Four ``SCRIPT ERROR: Invalid Faction ID: -1`` messages at
   ``mst_multiplayer_iv`` trigger 14 consequences. This tool decodes the
   operation, resolves the faction/troop names, and checks whether the remaster
   preserved or introduced it.
2. The probe field ``mode=0``. That field is ``$zdr_defence_mode`` (our
   tactical fallback state), never ``$g_multiplayer_game_type``. This tool binds
   the probe field to its source global and checks the source initializer.

``runtime_verified`` is always false and ``causality`` is always ``unproven``:
native data order is not proof of engine execution order, of wave spawning, or
of why the observed dedicated host read zero team-1 agents.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from ai_wave_contract import decode_trigger
from patch_defenders import mission_bounds

FACTION_SET_SLOT = 502
MULTIPLAYER_IS_SERVER = 417
ASSIGN = 2133
ADD_VISITORS = 1265
TEAM_GET_FACTION = 458
FACTION_GET_SLOT = 522
BEFORE_MISSION_START = "-19.000000"
AFTER_MISSION_START = "-20.000000"
WAVE_CONTROLLER = 15
ORIGINAL_TRIGGERS = 25
INVADER_FACTION = "fac_kingdom_invaders"
GLOBAL_BASE = 144115188075855872
TROOP_BASE = 360287970189639680
FACTION_BASE = 432345564227567616

SCHEMA = "zombieee.city-runtime-triage.v1"


def mission_rows(module: Path) -> list[str]:
    """Return the mst_multiplayer_iv trigger rows as single-line strings."""
    path = Path(module) / "mission_templates.txt"
    lines = path.read_text(encoding="utf-8").splitlines(keepends=True)
    count_row, _, end = mission_bounds(lines)
    return [line.strip() for line in lines[count_row + 1:end]]


def named_table(path: Path, prefix: str) -> list[str]:
    """Extract positional names from a compiled Warband table."""
    tokens = Path(path).read_text(encoding="utf-8", errors="replace").split()
    return [token for token in tokens if token.startswith(prefix)]


def variable_names(module: Path) -> list[str]:
    return (Path(module) / "variables.txt").read_text(encoding="utf-8").splitlines()


def _name(table: list[str], index: int) -> str | None:
    if 0 <= index < len(table):
        return table[index]
    return None


def resolve_faction(operand: int, factions: list[str]) -> str | None:
    if operand < 0:
        return None
    return _name(factions, operand - FACTION_BASE)


def resolve_troop(operand: int, troops: list[str]) -> str | None:
    if operand < 0:
        return None
    return _name(troops, operand - TROOP_BASE)


def flatten(rows: list[str]) -> dict:
    """Decode every trigger once; names are resolved by the caller."""
    return {"rows": rows,
            "decoded": [decode_trigger(row) for row in rows]}


def analyse_defects(original_rows: list[str], module_rows: list[str],
                    factions: list[str], troops: list[str],
                    variables: list[str],
                    probe_text: str | None = None) -> dict:
    """Pure, path-free source assessment of the two observed defect classes."""
    checks: dict[str, bool] = {}
    problems: list[str] = []
    warnings: list[str] = []

    def require(name: str, condition: bool, problem: str) -> None:
        checks[name] = bool(condition)
        if not condition:
            problems.append(problem)

    # Semantics come from the module that would run; the pinned 2012 mission is
    # used only for provenance (prefix identity). A build that changes trigger 14
    # must be triaged on its own bytes, not on the historical ones.
    decoded = [decode_trigger(row) for row in module_rows]

    require("original_mission_25_triggers", len(original_rows) == ORIGINAL_TRIGGERS,
            "Pinned original invasion mission is not the historical 25 triggers")
    require("remaster_preserves_original_prefix",
            len(module_rows) >= ORIGINAL_TRIGGERS and
            module_rows[:ORIGINAL_TRIGGERS] == original_rows[:ORIGINAL_TRIGGERS],
            "Generated mission does not preserve the original trigger prefix")
    trigger_index = 14
    module_rows = list(module_rows)
    trigger_14 = module_rows[trigger_index] if len(module_rows) > trigger_index else ""
    original_14 = original_rows[trigger_index] if len(original_rows) > trigger_index else ""

    require("trigger_14_unchanged",
            bool(trigger_14) and trigger_14 == original_14,
            "Generated trigger 14 differs from the original Beta 0.4 trigger")
    require("trigger_14_before_mission_start",
            bool(trigger_14) and trigger_14.split()[0] == BEFORE_MISSION_START,
            "Trigger 14 is not a ti_before_mission_start event")

    condition_ops, consequence_ops = (decoded[trigger_index]
                                      if len(module_rows) > trigger_index
                                      else ([], []))
    faction_ops = [(index, opcode, args)
                   for index, (opcode, args) in enumerate(consequence_ops)
                   if opcode == FACTION_SET_SLOT]
    invalid = [(index, args) for index, _, args in faction_ops if args and args[0] < 0]
    invalid_indices = [index for index, _ in invalid]
    require("invalid_faction_ops_present",
            len(invalid) == 4 and all(len(args) == 3 for _, args in invalid),
            "Expected the four historical faction_set_slot operations")
    require("invalid_faction_ops_are_last",
            invalid_indices == list(range(len(consequence_ops) - 4, len(consequence_ops))),
            "Invalid faction writes are not the trailing operations of trigger 14")
    valid_writes = [(index, args) for index, _, args in faction_ops
                    if args and args[0] >= 0]
    require("preceding_faction_writes_valid",
            bool(valid_writes) and
            all(resolve_faction(args[0], factions) == INVADER_FACTION
                for _, args in valid_writes),
            "Earlier faction slot writes do not target " + INVADER_FACTION)
    failed_slot = invalid[0][1][1] if invalid else -1
    prior_valid = [(index, args) for index, args in valid_writes
                   if args[1] == failed_slot and index < (invalid_indices[0]
                                                         if invalid_indices else len(consequence_ops))]
    require("failed_slot_has_prior_valid_write",
            bool(prior_valid) and resolve_troop(prior_valid[0][1][2], troops) is not None,
            "The slot targeted by the invalid faction writes has no valid earlier troop value")

    if len(module_rows) > WAVE_CONTROLLER:
        wave_conditions, wave_effects = decoded[WAVE_CONTROLLER]
        require("wave_controller_unchanged",
                len(original_rows) > WAVE_CONTROLLER and
                module_rows[WAVE_CONTROLLER] == original_rows[WAVE_CONTROLLER],
                "Generated wave controller differs from the original trigger")
        require("wave_controller_periodic_one_second",
                module_rows[WAVE_CONTROLLER].split()[0] == "1.000000",
                "Wave controller is not the historical one-second periodic controller")
        require("wave_controller_server_gate_first",
                bool(wave_effects) and wave_effects[0] == (MULTIPLAYER_IS_SERVER, ()),
                "Wave controller is not gated by multiplayer_is_server first")
        require("wave_controller_free_of_invalid_faction_writes",
                not any(opcode == FACTION_SET_SLOT and args and args[0] < 0
                        for opcode, args in wave_conditions + wave_effects),
                "Wave controller contains an invalid faction write of its own")
    else:
        checks.update({"wave_controller_unchanged": False,
                       "wave_controller_periodic_one_second": False,
                       "wave_controller_server_gate_first": False,
                       "wave_controller_free_of_invalid_faction_writes": False})
        problems.append("Mission rows too short to inspect the wave controller")

    g_type = GLOBAL_BASE + variables.index("g_multiplayer_game_type")
    if len(module_rows) > 3:
        game_type_init = decoded[3][1]
        require("original_game_type_initialized_seven",
                bool(game_type_init) and game_type_init[0] == (ASSIGN, (g_type, 7)),
                "Mission trigger 3 does not initialize g_multiplayer_game_type to 7")
    else:
        checks["original_game_type_initialized_seven"] = False
        problems.append("Mission rows too short to inspect the game-type initializer")

    tactical_mode_initial = None
    if "zdr_defence_mode" in variables:
        g_mode = GLOBAL_BASE + variables.index("zdr_defence_mode")
        for row, (_, effects) in zip(module_rows, decoded):
            if row.split()[0] == AFTER_MISSION_START and (ASSIGN, (g_mode, 0)) in effects:
                tactical_mode_initial = 0
                break
    require("tactical_mode_initialized_zero",
            tactical_mode_initial == 0,
            "City build does not initialize zdr_defence_mode to 0 after mission start")

    probe_fields = {"analysed": probe_text is not None}
    if probe_text is not None:
        probe_fields["mode_global"] = "unknown"
        probe_fields["wave_global"] = "unknown"
        for field, global_name in (("mode", "zdr_defence_mode"),
                                   ("wave", "wave_number")):
            marker = field + '=" .. global_int("'
            if marker in probe_text:
                tail = probe_text.split(marker, 1)[1]
                probe_fields[field + "_global"] = tail.split('"', 1)[0]
        probe_fields["reads_game_type"] = "g_multiplayer_game_type" in probe_text
        probe_fields["role_uses_multiplayer_is_server"] = (
            "multiplayer_is_server" in probe_text)
        probe_fields["server_only_sampling_gated_on_role"] = (
            'role == "server"' in probe_text or "role == 'server'" in probe_text)
        require("probe_mode_is_tactical_state",
                probe_fields.get("mode_global") == "zdr_defence_mode",
                "Probe mode field is not bound to the tactical state global")
        if probe_fields["reads_game_type"]:
            warnings.append("Probe also exposes the engine game type; keep the "
                            "mode field distinct from it in evidence reports")
    else:
        warnings.append("Probe source not supplied; field interpretation is unverified")

    report = {
        "schema": SCHEMA,
        "scope": "source and probe-field analysis of the first observed City attempt",
        "runtime_verified": False,
        "causality": "unproven",
        "checks": checks,
        "problems": problems,
        "warnings": warnings,
        "defects": {
            "trigger_14": {
                "mission_template": "mst_multiplayer_iv",
                "trigger": trigger_index,
                "start": BEFORE_MISSION_START,
                "consequences": len(consequence_ops),
                "operation": "faction_set_slot",
                "opcode": FACTION_SET_SLOT,
                "invalid_faction_operand": -1,
                "invalid_ops": [
                    {"consequence_index": index,
                     "slot": args[1],
                     "intended_troop": resolve_troop(args[2], troops)}
                    for index, args in invalid],
                "introduced_by_remaster": not checks["trigger_14_unchanged"],
                "original_trigger_preserved": checks["trigger_14_unchanged"],
                "last_ops_of_trigger": checks["invalid_faction_ops_are_last"],
                "preceding_valid_faction": INVADER_FACTION,
                "preceding_valid_writes": len(valid_writes),
                "failed_slot_prior_valid_write": (
                    {"slot": failed_slot,
                     "faction": resolve_faction(prior_valid[0][1][0], factions),
                     "troop": resolve_troop(prior_valid[0][1][2], troops)}
                    if prior_valid else None),
            },
            "wave_controller": {
                "trigger": WAVE_CONTROLLER,
                "periodic_seconds": 1,
                "server_gate": "multiplayer_is_server",
                "preserved": checks.get("wave_controller_unchanged", False),
            },
            "probe_fields": probe_fields,
            "source_game_type": 7,
            "source_tactical_mode_initial": tactical_mode_initial,
        },
        "confounders": [
            "The observed probe decided role from a boolean engine binding and "
            "reported the dedicated host as client, so its server-only wave/defender/"
            "command sampling was silently skipped.",
            "The observed probe overlay lacked the operation metadata lists the "
            "engine needs to classify bound operations, so one bound read is logged "
            "by the engine as an illegal lvalue.",
            "The heartbeat still prints wave/mode regardless of role, but no "
            "independent server-side measurement of wave_number or team-1 agents "
            "exists in this attempt; a broken binding would also read as zero.",
            "Trigger-14 engine line numbers are zero-based consequence indices, which "
            "matches indices 24-27 of the trailing four operations.",
        ],
        "unknown_runtime_observations": [
            "live g_multiplayer_game_type on the dedicated host",
            "g_round_start_time and whether the round timer advanced",
            "whether the original one-second wave controller body executed server-side",
            "whether the invalid faction writes were the only script errors",
            "why no team-1 agent was replicated to the joined client",
        ],
        "disposition": "trigger14_original_non_causal_source_scope_only_engine_execution_unproven",
    }
    return report


def audit_observed_defects(original: Path, module: Path,
                           probe: Path | None = None) -> dict:
    """Read owned module copies; emit path-free evidence."""
    try:
        original_rows = mission_rows(Path(original))
        module_rows = mission_rows(Path(module))
        factions = named_table(Path(original) / "factions.txt", "fac_")
        troops = named_table(Path(original) / "troops.txt", "trp_")
        variables = variable_names(Path(module))
        probe_text = None
        if probe is not None:
            probe_text = Path(probe).read_text(encoding="utf-8", errors="replace")
        return analyse_defects(original_rows, module_rows, factions, troops,
                               variables, probe_text)
    except (OSError, ValueError, IndexError, KeyError) as exc:
        return {"schema": SCHEMA, "runtime_verified": False, "causality": "unproven",
                "problems": ["Static inspection error: " + type(exc).__name__ + ": " + str(exc)],
                "checks": {}, "defects": {},
                "disposition": "inspection_failed_not_evidence"}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--original", type=Path, required=True,
                        help="Owned unmodified Beta 0.4 module")
    parser.add_argument("--module", type=Path, required=True,
                        help="Fully built City module")
    parser.add_argument("--probe", type=Path,
                        help="Overlay Lua probe used by the observed attempt")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    report = audit_observed_defects(args.original, args.module, args.probe)
    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        passed = report.get("checks") and all(report["checks"].values())
        print("City runtime triage:", "OK (source scope only)" if passed else "PROBLEMS")
        defects = report.get("defects", {})
        trigger = defects.get("trigger_14", {})
        if trigger:
            print("Trigger 14:", trigger["operation"], "opcode", trigger["opcode"],
                  "/", len(trigger["invalid_ops"]), "invalid faction writes")
            print("  original preserved:", trigger["original_trigger_preserved"],
                  "/ last ops:", trigger["last_ops_of_trigger"])
        probe = defects.get("probe_fields", {})
        if probe.get("analysed"):
            print("Probe mode global:", probe.get("mode_global"),
                  "/ reads game type:", probe.get("reads_game_type"))
        for problem in report.get("problems", []):
            print("Problem:", problem)
        for warning in report.get("warnings", []):
            print("Warning:", warning)
        print("Causality:", report["causality"],
              "/ engine runtime: UNVERIFIED")
    return 0 if report.get("checks") and all(report["checks"].values()) else 2


if __name__ == "__main__":
    raise SystemExit(main())
