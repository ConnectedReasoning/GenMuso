"""
humanize.py — Make generated notes feel like they were played, not computed.

The raw output of the voice behaviors is rhythmically precise and
dynamically abrupt.  This module applies post-processing to fix that:

  legato       — extend notes so they overlap slightly with the next one
  sustain      — notes on strong beats hold longer
  timing_feel  — micro-shifts to start times (not quantized to grid)
  velocity_smooth — consecutive notes don't jump wildly in dynamics
  duration_vary — small random variation in how long each note rings

These are applied per-voice after generation, before MIDI export.
"""

import numpy as np
from voices import Note


def humanize(notes: list[Note], ticks_per_16th: int = 120,
             legato: float = 0.3,
             timing_feel: float = 0.02,
             velocity_smooth: float = 0.3,
             duration_vary: float = 0.15,
             min_duration_ticks: int = 60,
             ) -> list[Note]:
    """
    Apply humanization to a list of notes from a single voice.

    Parameters:
        legato:          0.0 = notes end exactly on grid (choppy)
                         0.3 = notes extend 30% into the next gap (natural)
                         0.7 = very connected, almost overlapping
                         1.0 = full overlap with next note start

        timing_feel:     0.0 = perfectly quantized
                         0.02 = very subtle drift (2% of a 16th note)
                         0.05 = noticeable looseness
                         0.1 = sloppy (intentionally human)

        velocity_smooth: 0.0 = no smoothing (raw random velocities)
                         0.3 = moderate smoothing (natural dynamics)
                         0.7 = very smooth (gentle, even)

        duration_vary:   0.0 = exact durations
                         0.15 = subtle variation (natural)
                         0.3 = noticeable variation

    Returns the same list, modified in place.
    """
    if not notes or len(notes) < 2:
        return notes

    # Sort by start time for sequential processing
    notes.sort(key=lambda n: n.start_tick)

    # ── Pass 1: Velocity smoothing ───────────────────────────────────
    # Each note's velocity blends toward the previous note's velocity.
    # This prevents jarring jumps like 55 → 98 → 42.
    if velocity_smooth > 0:
        for i in range(1, len(notes)):
            prev_vel = notes[i - 1].velocity
            curr_vel = notes[i].velocity
            blended = curr_vel + velocity_smooth * (prev_vel - curr_vel)
            notes[i].velocity = int(np.clip(blended, 1, 127))

    # ── Pass 2: Duration variation ───────────────────────────────────
    # Small random stretch or shrink to each note's length.
    if duration_vary > 0:
        for note in notes:
            factor = 1.0 + np.random.uniform(-duration_vary, duration_vary)
            new_dur = int(note.duration_ticks * factor)
            note.duration_ticks = max(min_duration_ticks, new_dur)

    # ── Pass 3: Legato extension ─────────────────────────────────────
    # Extend each note's duration to partially fill the gap before
    # the next note.  This is the biggest fix for "jaggedy" sound.
    if legato > 0:
        for i in range(len(notes) - 1):
            curr = notes[i]
            next_note = notes[i + 1]
            gap = next_note.start_tick - (curr.start_tick + curr.duration_ticks)

            if gap > 0:
                # Extend into the gap
                extension = int(gap * legato)
                curr.duration_ticks += extension
            elif gap < 0:
                # Notes already overlap — leave them
                pass

        # Last note: extend by a fixed amount
        notes[-1].duration_ticks = int(notes[-1].duration_ticks * (1 + legato * 0.5))

    # ── Pass 4: Timing micro-shifts ──────────────────────────────────
    # Nudge start times by a tiny random amount.  Preserves the feel
    # of the grid while removing machine precision.
    if timing_feel > 0:
        max_shift = int(ticks_per_16th * timing_feel)
        for note in notes:
            shift = np.random.randint(-max_shift, max_shift + 1)
            note.start_tick = max(0, note.start_tick + shift)
            # Keep duration unchanged — only the attack moves

    return notes


# ── Preset humanization profiles ─────────────────────────────────────
# These can be referenced by name in voice params.

PROFILES = {
    'subtle': {
        'legato': 0.2,
        'timing_feel': 0.015,
        'velocity_smooth': 0.2,
        'duration_vary': 0.1,
    },
    'natural': {
        'legato': 0.35,
        'timing_feel': 0.025,
        'velocity_smooth': 0.3,
        'duration_vary': 0.15,
    },
    'expressive': {
        'legato': 0.5,
        'timing_feel': 0.04,
        'velocity_smooth': 0.15,
        'duration_vary': 0.2,
    },
    'tight': {
        'legato': 0.15,
        'timing_feel': 0.01,
        'velocity_smooth': 0.25,
        'duration_vary': 0.08,
    },
    'legato': {
        'legato': 0.7,
        'timing_feel': 0.02,
        'velocity_smooth': 0.35,
        'duration_vary': 0.12,
    },
    'none': {
        'legato': 0.0,
        'timing_feel': 0.0,
        'velocity_smooth': 0.0,
        'duration_vary': 0.0,
    },
}


def get_profile(name: str) -> dict:
    """Look up a humanization profile by name."""
    return PROFILES.get(name, PROFILES['natural'])
