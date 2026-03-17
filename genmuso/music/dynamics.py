"""
dynamics.py — Emotional arc and intensity shaping.

This module operates at two levels:

  1. COMPOSITION ARC — shapes the whole piece
     Each section gets an intensity value (0.0–1.0) that scales
     density, velocity, and note lengths.  A typical arc might be:
       intro (0.3) → build (0.5) → peak (1.0) → breathe (0.4) → 
       climax (0.9) → resolve (0.2)

  2. SECTION BREATHING — shapes individual sections
     Within a section, intensity can swell and recede across bars,
     creating phrases that breathe rather than sitting flat.

The intensity value modifies voices through multipliers:
  - density:    scaled by intensity (quiet = fewer notes)
  - velocity:   scaled by intensity (quiet = softer)
  - note_length: inversely scaled (quiet = longer, more sustained)
"""

import numpy as np
from dataclasses import dataclass


# ══════════════════════════════════════════════════════════════════════
# ARC CURVES — predefined shapes for a composition
# ══════════════════════════════════════════════════════════════════════
#
# Each curve is a function that takes a position (0.0–1.0 through the
# piece) and returns an intensity (0.0–1.0).

def arc_gradual_build(position: float) -> float:
    """Starts quiet, builds steadily, peaks near the end, resolves."""
    if position < 0.15:
        return 0.3 + position * 2.0        # intro: 0.3 → 0.6
    elif position < 0.7:
        return 0.5 + (position - 0.15) * 0.7  # build: 0.5 → 0.9
    elif position < 0.85:
        return 0.9 + (position - 0.7) * 0.7   # peak: 0.9 → 1.0
    else:
        return 1.0 - (position - 0.85) * 4.0  # resolve: 1.0 → 0.4


def arc_wave(position: float) -> float:
    """Two swells: builds, breathes, builds higher, resolves."""
    return 0.3 + 0.5 * np.sin(position * 2 * np.pi - np.pi / 2) * 0.5 + 0.5 * (
        0.3 * np.sin(position * 4 * np.pi) + 0.4
    )


def arc_peak_middle(position: float) -> float:
    """Quiet start, peaks in the middle, quiet end.  Classic arch form."""
    # Parabola peaking at 0.5
    return 0.25 + 0.75 * (1.0 - (2.0 * position - 1.0) ** 2)


def arc_slow_burn(position: float) -> float:
    """Very gradual build — barely perceptible increase until the end."""
    return 0.25 + 0.65 * (position ** 1.8)


def arc_bookend(position: float) -> float:
    """Strong start, dip in middle, strong finish."""
    if position < 0.2:
        return 0.8
    elif position < 0.5:
        return 0.8 - (position - 0.2) * 2.0  # dip to 0.2
    elif position < 0.8:
        return 0.2 + (position - 0.5) * 2.7  # build to 1.0
    else:
        return 1.0 - (position - 0.8) * 2.0  # resolve


def arc_flat(position: float) -> float:
    """No arc — everything at even intensity.  The current behavior."""
    return 0.6


def arc_terraced(position: float) -> float:
    """Step changes — like Baroque dynamics.  Sudden shifts."""
    if position < 0.25:
        return 0.4
    elif position < 0.5:
        return 0.7
    elif position < 0.75:
        return 1.0
    else:
        return 0.5


ARCS = {
    'gradual_build':  arc_gradual_build,
    'wave':           arc_wave,
    'peak_middle':    arc_peak_middle,
    'slow_burn':      arc_slow_burn,
    'bookend':        arc_bookend,
    'flat':           arc_flat,
    'terraced':       arc_terraced,
}


# ══════════════════════════════════════════════════════════════════════
# SECTION BREATHING — within-section intensity variation
# ══════════════════════════════════════════════════════════════════════

def section_breathing(bar: int, total_bars: int,
                      pattern: str = 'swell') -> float:
    """
    Returns a multiplier (0.5–1.0) for a given bar within a section.

    Patterns:
        'swell'    — builds from start to ~3/4, then eases
        'breathe'  — gentle sine wave, in and out
        'steady'   — flat, no variation
        'fadeout'   — full at start, fading to end
        'fadein'   — quiet at start, building to end
    """
    if total_bars <= 1:
        return 1.0

    pos = bar / (total_bars - 1)  # 0.0 to 1.0

    if pattern == 'swell':
        if pos < 0.75:
            return 0.6 + 0.4 * (pos / 0.75)
        else:
            return 1.0 - 0.3 * ((pos - 0.75) / 0.25)

    elif pattern == 'breathe':
        return 0.65 + 0.35 * np.sin(pos * np.pi)

    elif pattern == 'fadeout':
        return 1.0 - 0.4 * pos

    elif pattern == 'fadein':
        return 0.5 + 0.5 * pos

    else:  # 'steady'
        return 1.0


# ══════════════════════════════════════════════════════════════════════
# INTENSITY APPLICATION — how intensity modifies voice parameters
# ══════════════════════════════════════════════════════════════════════

@dataclass
class IntensityModifiers:
    """The actual multipliers applied to voice parameters."""
    density_mult: float = 1.0       # multiply voice density by this
    velocity_offset: int = 0        # add to velocity range
    note_length_mult: float = 1.0   # multiply note durations by this


def intensity_to_modifiers(intensity: float) -> IntensityModifiers:
    """
    Convert a 0.0–1.0 intensity to concrete parameter modifiers.

    Low intensity (0.2):  fewer notes, softer, longer/more sustained
    Mid intensity (0.5):  normal
    High intensity (1.0): denser, louder, shorter/more active

    The mapping is non-linear — you don't want the quiet sections
    to be completely empty.
    """
    # Density: 0.4x at intensity 0.0, 1.0x at intensity 0.5, 1.4x at 1.0
    density_mult = 0.4 + intensity * 1.0

    # Velocity: -20 at low, 0 at mid, +15 at high
    velocity_offset = int(-20 + intensity * 35)

    # Note lengths: 1.5x at low (longer), 1.0x at mid, 0.7x at high (shorter)
    note_length_mult = 1.5 - intensity * 0.8

    return IntensityModifiers(
        density_mult=density_mult,
        velocity_offset=velocity_offset,
        note_length_mult=note_length_mult,
    )


def compute_section_intensity(
    section_index: int,
    total_sections: int,
    arc: str = 'gradual_build',
) -> float:
    """
    Compute the intensity for a given section based on the
    composition's arc curve.
    """
    if total_sections <= 1:
        return 0.6

    position = section_index / (total_sections - 1)
    arc_fn = ARCS.get(arc, arc_flat)
    raw = arc_fn(position)

    return float(np.clip(raw, 0.1, 1.0))
