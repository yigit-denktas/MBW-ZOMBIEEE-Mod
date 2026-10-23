"""Explicit survivor-support difficulty, preserving original zombie parameters.

Adjusts reinforcement start wave and fallback thresholds only; this is not a
claim that original zombie health/damage/wave sizes have been rebalanced.
"""
from dataclasses import dataclass


@dataclass(frozen=True)
class Difficulty:
    name: str
    first_reinforcement_wave: int
    fallback_at_or_below: int
    regroup_at_or_above: int
    description: str


PROFILES = {
    "story": Difficulty("story", 1, 2, 3, "Earlier help, proactive fallback"),
    "standard": Difficulty("standard", 2, 1, 3, "Original experimental balance"),
    "hard": Difficulty("hard", 3, 1, 3, "Reinforcements delayed to wave 3"),
    "nightmare": Difficulty("nightmare", 4, 0, 3, "Reinforcements delayed to wave 4"),
}


def profile(name: str) -> Difficulty:
    try:
        return PROFILES[name]
    except KeyError as exc:
        raise ValueError("Unknown difficulty: " + name) from exc
