#!/usr/bin/env python3
"""City-build firearm accuracy profile: modest buff to automatic weapons only.

The 2012 module treats firearms as crossbow-type weapons; item accuracy is the
compiled numeric statistic in the item header. The automatic weapons share one
fixed item-flag mask (verified from the pinned module), so the allow-list is
derived from that mask anchored on ``itm_m16a2`` and ``itm_mp5`` instead of a
hand-maintained name list. Single-shot firearms (bolt-action rifle, break-action
shotgun, pistols) keep their original accuracy.

Accuracy delta: ``old + clamp(round(old * 0.15), 10, 20)`` - about +10..+20 points
on the pinned 80..97 range (tighter reticle/spread). Only the built module is patched; the original RAR
and every other item/faction/troop/mission file are untouched.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

AUTO_ANCHORS = ("itm_m16a2", "itm_mp5")
SINGLE_SHOT_GUARD = ("itm_remington_model_700", "itm_browning_cynergy",
                     "itm_beretta_92fs", "itm_sw_5904")
MIN_AUTO_GROUP = 8
ACCURACY_MIN_DELTA = 10
ACCURACY_MAX_DELTA = 20


class FirearmPatchError(ValueError):
    pass


def _item_tokens(line: str) -> tuple[str, int]:
    tokens = line.split()
    if len(tokens) < 8 or not tokens[0].startswith("itm_"):
        raise FirearmPatchError("Malformed compiled item header")
    try:
        meshes = int(tokens[3])
    except ValueError as exc:
        raise FirearmPatchError("Malformed item mesh count") from exc
    if not 1 <= meshes <= 8:
        raise FirearmPatchError("Implausible item mesh count")
    flags_index = 4 + 2 * meshes
    value_index = flags_index + 2
    accuracy_index = value_index + 6
    if accuracy_index >= len(tokens):
        raise FirearmPatchError("Truncated compiled item stats")
    return tokens, accuracy_index


def item_index(lines: list[str]) -> list[tuple[int, list[str], int]]:
    """Return (line index, tokens, accuracy token index) for every item."""
    result = []
    for index, raw in enumerate(lines):
        if raw.strip().startswith("itm_"):
            tokens, accuracy_index = _item_tokens(raw)
            result.append((index, tokens, accuracy_index))
    return result


def automatic_group(items: list[tuple[int, list[str], int]]) -> dict[str, int]:
    """Derive the automatic-weapon flag mask from the two anchor items."""
    flags = {}
    for _, tokens, _ in items:
        flags[tokens[0]] = tokens[4 + 2 * int(tokens[3])]
    anchors = {name: flags.get(name) for name in AUTO_ANCHORS}
    if not all(anchors.values()):
        raise FirearmPatchError("Automatic-weapon anchor items missing from the item table")
    if len(set(anchors.values())) != 1:
        raise FirearmPatchError("Automatic-weapon anchor items disagree on flags")
    mask = next(iter(anchors.values()))
    group = {name: flag for name, flag in flags.items() if flag == mask}
    if len(group) < MIN_AUTO_GROUP:
        raise FirearmPatchError("Automatic-weapon flag group is implausibly small")
    for name in SINGLE_SHOT_GUARD:
        if name not in flags:
            raise FirearmPatchError("Single-shot guard item missing: " + name)
        if flags[name] == mask:
            raise FirearmPatchError("Single-shot firearm shares the automatic flag mask: " + name)
    return group


def accuracy_delta(value: int) -> int:
    if value <= 0:
        raise FirearmPatchError("Automatic firearm has non-positive accuracy")
    return max(ACCURACY_MIN_DELTA, min(ACCURACY_MAX_DELTA, round(value * 0.15)))


def patch_text(text: str, profile: str = "default") -> tuple[str, dict]:
    lines = text.splitlines(keepends=True)
    items = item_index(lines)
    if len(items) < 100:
        raise FirearmPatchError("Item table is truncated")
    group = automatic_group(items)
    receipt = {
        "applied": profile == "default",
        "profile": profile,
        "item_count": len(items),
        "automatic_items": sorted(group),
        "single_shot_guards_unchanged": list(SINGLE_SHOT_GUARD),
        "changed": [],
        "runtime_verified": False,
        "warning": "Built-module stat profile only; gameplay feel requires runtime validation.",
    }
    if profile == "stock":
        receipt["sha256_after"] = hashlib.sha256(text.encode()).hexdigest()
        return text, receipt
    changed = 0
    for index, tokens, accuracy_index in items:
        if tokens[0] not in group:
            continue
        old = int(tokens[accuracy_index])
        new = old + accuracy_delta(old)
        if new == old:
            continue
        tokens[accuracy_index] = str(new)
        raw = lines[index]
        prefix = raw[:len(raw) - len(raw.lstrip())]
        newline = "\r\n" if raw.endswith("\r\n") else ("\n" if raw.endswith("\n") else "")
        lines[index] = prefix + " ".join(tokens) + newline
        receipt["changed"].append({"item": tokens[0], "before": old, "after": new,
                                   "delta": new - old})
        changed += 1
    if changed != len(group):
        raise FirearmPatchError("Not every automatic item was patched")
    receipt["changed_count"] = changed
    receipt["untouched_item_count"] = len(items) - changed
    return "".join(lines), receipt


def apply_module(module: Path, profile: str = "default") -> dict:
    module = Path(module)
    path = module / "item_kinds1.txt"
    original = path.read_bytes()
    changed, receipt = patch_text(original.decode("utf-8"), profile)
    result = dict(receipt)
    result["sha256_before"] = hashlib.sha256(original).hexdigest()
    result["sha256_after"] = hashlib.sha256(changed.encode("utf-8")).hexdigest()
    if profile == "default":
        path.write_bytes(changed.encode("utf-8"))
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--module", type=Path, required=True)
    parser.add_argument("--profile", choices=("default", "stock"), default="default")
    parser.add_argument("--apply", action="store_true")
    args = parser.parse_args()
    try:
        if args.apply:
            result = apply_module(args.module, args.profile)
        else:
            text = (args.module / "item_kinds1.txt").read_text(encoding="utf-8")
            _, result = patch_text(text, args.profile)
            result["dry_run"] = True
    except (OSError, ValueError, FirearmPatchError) as exc:
        print(json.dumps({"applied": False, "error": type(exc).__name__ + ": " + str(exc)}))
        return 2
    print(json.dumps(result, indent=2))
    return 0 if result.get("applied") else 2


if __name__ == "__main__":
    raise SystemExit(main())
