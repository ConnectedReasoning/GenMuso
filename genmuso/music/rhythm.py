"""
rhythm.py — Metrical grid, beat weights, and phrase structure.

This is the biggest upgrade over GenMuso: notes are placed on a grid
where each position has a *weight* reflecting its metric strength.
Voices multiply their density by the weight to decide whether to
place a note.  Strong beats get notes at low density; weak subdivisions
only fill in at high density.  This gives pulse without rigidity.
"""

import numpy as np
from dataclasses import dataclass


# ── Beat weight tables ───────────────────────────────────────────────
# One entry per 16th-note position in a bar.
# 1.0 = strongest downbeat, 0.1 = weakest subdivision.

METERS = {
    '4/4': [
        # beat 1        beat 2        beat 3        beat 4
        1.0, 0.10, 0.30, 0.10,  0.50, 0.10, 0.30, 0.10,
        0.80, 0.10, 0.30, 0.10,  0.50, 0.10, 0.30, 0.10,
    ],
    '3/4': [
        # beat 1        beat 2        beat 3
        1.0, 0.10, 0.30, 0.10,  0.50, 0.10, 0.30, 0.10,
        0.50, 0.10, 0.30, 0.10,
    ],
    '6/8': [
        # dotted-quarter groupings of 3 eighth-notes each
        # group 1             group 2
        1.0, 0.15, 0.35,  0.70, 0.15, 0.35,
        0.85, 0.15, 0.35,  0.70, 0.15, 0.35,
    ],
    '5/4': [
        # 3 + 2 grouping
        1.0, 0.10, 0.30, 0.10,  0.50, 0.10, 0.30, 0.10,
        0.80, 0.10, 0.30, 0.10,  0.50, 0.10, 0.30, 0.10,
        0.70, 0.10, 0.30, 0.10,
    ],
    '7/8': [
        # 2 + 2 + 3 grouping
        1.0, 0.15, 0.35,  0.60, 0.15, 0.35,
        0.80, 0.15, 0.35,  0.60, 0.15, 0.35,
        0.70, 0.15, 0.35, 0.15,
    ],
}


@dataclass
class GridPosition:
    """A single slot on the rhythmic grid."""
    bar: int          # bar number (0-indexed)
    position: int     # position within bar (0-indexed)
    tick: int         # absolute tick from section start
    weight: float     # metric weight (0–1)


def build_grid(bars: int, meter: str = '4/4',
               ticks_per_beat: int = 480) -> list[GridPosition]:
    """
    Build the full rhythmic grid for a section.

    Returns one GridPosition per 16th-note slot, with absolute tick
    positions and metric weights.
    """
    weights = METERS[meter]
    positions_per_bar = len(weights)
    ticks_per_16th = ticks_per_beat // 4

    grid = []
    for bar in range(bars):
        for pos in range(positions_per_bar):
            absolute_tick = (bar * positions_per_bar + pos) * ticks_per_16th
            grid.append(GridPosition(
                bar=bar,
                position=pos,
                tick=absolute_tick,
                weight=weights[pos],
            ))
    return grid


def section_duration_ticks(bars: int, meter: str = '4/4',
                           ticks_per_beat: int = 480) -> int:
    """Total ticks for a section."""
    positions_per_bar = len(METERS[meter])
    ticks_per_16th = ticks_per_beat // 4
    return bars * positions_per_bar * ticks_per_16th


def apply_swing(grid: list[GridPosition], amount: float = 0.0,
                ticks_per_beat: int = 480) -> list[GridPosition]:
    """
    Apply swing feel by delaying the "and" of each beat.

    amount: 0.0 = straight, 1.0 = full triplet swing.
    Only affects positions 2, 6, 10, 14 in 4/4 (the upbeats).
    """
    if amount <= 0:
        return grid

    ticks_per_16th = ticks_per_beat // 4
    swing_ticks = int(amount * ticks_per_16th * 0.5)

    for gp in grid:
        if gp.position % 4 == 2:
            gp.tick += swing_ticks

    return grid


def phrase_weight(bar: int, phrase_length: int = 4) -> float:
    """
    Multiplier based on position within a phrase.

    Phrase boundaries get slightly different density:
      - First bar:  1.0  (strong entry)
      - Last bar:   0.7  (wind down / cadence)
      - Middle:     0.9  (steady)

    This creates natural breathing in the music.
    """
    pos = bar % phrase_length
    if pos == 0:
        return 1.0
    elif pos == phrase_length - 1:
        return 0.7
    return 0.9
