"""
voices.py — Voice behaviors for generative composition.

Each behavior takes a rhythmic grid, a scale, and config parameters,
and returns a list of Note objects.  Behaviors define *how* a voice
moves through pitch and time:

  random_walk    — stepwise motion with occasional leaps (GenMuso's best idea)
  random_select  — pick notes at random from the scale (textural)
  drone          — sustained tones for the section duration (harmonic anchor)
  arpeggio       — cycle through chord tones in patterns
  ostinato       — short repeating pattern with subtle variation (rhythmic backbone)
"""

import numpy as np
from dataclasses import dataclass
from rhythm import GridPosition, phrase_weight
from scales import chord_tones as _chord_tones, nearest_in_scale


@dataclass
class Note:
    """Internal note representation, independent of MIDI format."""
    pitch: int            # MIDI note number (0–127)
    start_tick: int       # absolute tick from piece start
    duration_ticks: int   # how long the note lasts
    velocity: int         # 0–127
    channel: int = 0      # MIDI channel


# ── Behavior: Random Walk ────────────────────────────────────────────

def random_walk(
    grid: list[GridPosition],
    scale: list[int],
    density: float = 0.3,
    velocity_range: tuple = (60, 100),
    note_lengths: list = None,
    note_length_weights: list = None,
    channel: int = 0,
    ticks_per_16th: int = 120,
    phrase_length: int = 4,
    total_bars: int = 8,
    leap_probability: float = 0.08,
    **kwargs,
) -> list[Note]:
    """
    Step through the scale by ±1–2 degrees with occasional larger leaps.
    This produces the most melodically coherent lines.
    """
    if not scale or not grid:
        return []

    note_lengths = note_lengths or [1, 2, 3, 4]
    note_length_weights = note_length_weights or [0.2, 0.4, 0.25, 0.15]
    # Normalize weights
    wt = np.array(note_length_weights[:len(note_lengths)], dtype=float)
    wt /= wt.sum()

    notes = []
    idx = len(scale) // 2  # start in the middle of the range
    i = 0

    while i < len(grid):
        gp = grid[i]
        pw = phrase_weight(gp.bar, phrase_length)
        prob = density * gp.weight * pw

        if np.random.random() < prob:
            # Choose step size
            if np.random.random() < leap_probability:
                step = np.random.choice([-4, -3, 3, 4, 5])
            else:
                step = np.random.randint(-2, 3)  # -2 to +2

            idx = max(0, min(len(scale) - 1, idx + step))
            pitch = scale[idx]

            # Duration: longer on strong beats
            dur_16ths = int(np.random.choice(note_lengths, p=wt))
            if gp.weight >= 0.8:
                dur_16ths = min(dur_16ths + 1, max(note_lengths))

            # Velocity: accent strong beats
            vel = np.random.randint(velocity_range[0], velocity_range[1])
            if gp.weight >= 0.8:
                vel = min(127, vel + 10)

            notes.append(Note(
                pitch=pitch,
                start_tick=gp.tick,
                duration_ticks=dur_16ths * ticks_per_16th,
                velocity=vel,
                channel=channel,
            ))
            i += dur_16ths
            continue

        i += 1

    return notes


# ── Behavior: Random Select ─────────────────────────────────────────

def random_select(
    grid: list[GridPosition],
    scale: list[int],
    density: float = 0.2,
    velocity_range: tuple = (55, 90),
    note_lengths: list = None,
    note_length_weights: list = None,
    channel: int = 0,
    ticks_per_16th: int = 120,
    phrase_length: int = 4,
    total_bars: int = 8,
    **kwargs,
) -> list[Note]:
    """
    Pick notes at random from the scale.  Less melodic coherence but
    creates interesting texture, especially in middle voices.
    """
    if not scale or not grid:
        return []

    note_lengths = note_lengths or [2, 3, 4, 6]
    note_length_weights = note_length_weights or [0.2, 0.3, 0.3, 0.2]
    wt = np.array(note_length_weights[:len(note_lengths)], dtype=float)
    wt /= wt.sum()

    notes = []
    i = 0

    while i < len(grid):
        gp = grid[i]
        pw = phrase_weight(gp.bar, phrase_length)
        prob = density * gp.weight * pw

        if np.random.random() < prob:
            pitch = scale[np.random.randint(0, len(scale))]
            dur_16ths = int(np.random.choice(note_lengths, p=wt))
            vel = np.random.randint(velocity_range[0], velocity_range[1])

            notes.append(Note(
                pitch=pitch,
                start_tick=gp.tick,
                duration_ticks=dur_16ths * ticks_per_16th,
                velocity=vel,
                channel=channel,
            ))
            i += dur_16ths
            continue

        i += 1

    return notes


# ── Behavior: Drone ──────────────────────────────────────────────────

def drone(
    total_ticks: int,
    drone_notes: list[int],
    velocity: int = 70,
    channel: int = 0,
    **kwargs,
) -> list[Note]:
    """
    Sustained tones held for the entire section.
    The harmonic anchor — this is the thread that held Passion
    for the Heavens together across 46 key changes.
    """
    return [
        Note(pitch=p, start_tick=0, duration_ticks=total_ticks,
             velocity=velocity, channel=channel)
        for p in drone_notes
    ]


# ── Behavior: Arpeggio ──────────────────────────────────────────────

def arpeggio(
    grid: list[GridPosition],
    scale: list[int],
    root_pc: int = 0,
    mode: str = 'minor',
    degree: int = 1,
    density: float = 0.5,
    velocity_range: tuple = (55, 85),
    pattern: str = 'up',        # 'up', 'down', 'up_down', 'random'
    note_length: int = 2,
    channel: int = 0,
    ticks_per_16th: int = 120,
    low: int = 48,
    high: int = 72,
    phrase_length: int = 4,
    total_bars: int = 8,
    **kwargs,
) -> list[Note]:
    """
    Cycle through chord tones (triad derived from the scale) in a
    configurable pattern.  Chord quality is determined by the mode —
    no more hard-coded major triads.
    """
    tones = _chord_tones(root_pc, mode, degree, low, high)
    if not tones:
        return random_walk(grid, scale, density, velocity_range,
                           channel=channel, ticks_per_16th=ticks_per_16th,
                           phrase_length=phrase_length, total_bars=total_bars)

    # Build the cycle
    if pattern == 'down':
        cycle = list(reversed(tones))
    elif pattern == 'up_down':
        cycle = tones + list(reversed(tones[1:-1])) if len(tones) > 2 else tones
    elif pattern == 'random':
        cycle = tones  # will randomize below
    else:
        cycle = tones

    notes = []
    tone_idx = 0
    i = 0

    while i < len(grid):
        gp = grid[i]
        pw = phrase_weight(gp.bar, phrase_length)
        prob = density * gp.weight * pw

        if np.random.random() < prob:
            if pattern == 'random':
                pitch = tones[np.random.randint(0, len(tones))]
            else:
                pitch = cycle[tone_idx % len(cycle)]
                tone_idx += 1

            vel = np.random.randint(velocity_range[0], velocity_range[1])
            notes.append(Note(
                pitch=pitch,
                start_tick=gp.tick,
                duration_ticks=note_length * ticks_per_16th,
                velocity=vel,
                channel=channel,
            ))
            i += note_length
            continue

        i += 1

    return notes


# ── Behavior: Ostinato ───────────────────────────────────────────────

def ostinato(
    grid: list[GridPosition],
    scale: list[int],
    density: float = 0.5,
    velocity_range: tuple = (65, 90),
    note_length: int = 2,
    pattern_bars: int = 1,
    variation: float = 0.08,
    channel: int = 0,
    ticks_per_16th: int = 120,
    phrase_length: int = 4,
    total_bars: int = 8,
    **kwargs,
) -> list[Note]:
    """
    Generate a short melodic/rhythmic cell and repeat it with subtle
    variation.  This is the backbone of rhythmic focus music — provides
    a consistent pulse while staying alive through micro-changes.
    """
    if not scale or not grid:
        return []

    # Figure out how many positions per bar from the grid
    bars_in_grid = max(gp.bar for gp in grid) + 1
    positions_per_bar = len([gp for gp in grid if gp.bar == 0])

    # Generate base pattern from the first pattern_bars
    base_grid = [gp for gp in grid if gp.bar < pattern_bars]
    base = []
    idx = len(scale) // 2
    pos = 0

    while pos < len(base_grid):
        gp = base_grid[pos]
        prob = density * gp.weight
        if np.random.random() < prob:
            step = np.random.randint(-1, 2)
            idx = max(0, min(len(scale) - 1, idx + step))
            base.append((gp.position, scale[idx], note_length))
            pos += note_length
        else:
            pos += 1

    if not base:
        # Fallback: at least one note
        base = [(0, scale[len(scale) // 2], note_length)]

    # Stamp out the pattern across all bars
    notes = []
    repetitions = total_bars // max(pattern_bars, 1)

    for rep in range(repetitions):
        tick_offset = rep * pattern_bars * positions_per_bar * ticks_per_16th

        for bar_pos, pitch, dur in base:
            # Variation: occasionally shift pitch
            actual_pitch = pitch
            if np.random.random() < variation:
                try:
                    si = scale.index(pitch)
                    si += np.random.choice([-1, 1])
                    si = max(0, min(len(scale) - 1, si))
                    actual_pitch = scale[si]
                except ValueError:
                    actual_pitch = nearest_in_scale(pitch, scale)

            # Variation: occasionally skip a note
            if np.random.random() < variation * 0.5:
                continue

            vel = np.random.randint(velocity_range[0], velocity_range[1])
            notes.append(Note(
                pitch=actual_pitch,
                start_tick=tick_offset + bar_pos * ticks_per_16th,
                duration_ticks=dur * ticks_per_16th,
                velocity=vel,
                channel=channel,
            ))

    return notes


# ── Behavior: Develop (motif-based) ──────────────────────────────────

def develop(
    grid: list[GridPosition],
    scale: list[int],
    density: float = 0.3,
    velocity_range: tuple = (60, 100),
    channel: int = 0,
    ticks_per_16th: int = 120,
    phrase_length: int = 4,
    total_bars: int = 8,
    # Motif-specific params
    motif_length: int = 5,
    plan: str = 'gradual_evolution',
    step_range: tuple = (-2, 3),
    motif_durations: list = None,
    motif_duration_weights: list = None,
    **kwargs,
) -> list[Note]:
    """
    Generate a random motif, then develop it through classical
    transformations to build the entire voice part.

    This is the key behavioral difference from random_walk: instead of
    independently choosing each note, this voice generates ONE short
    idea and then builds everything from it.  You'll hear the same
    melodic shape recurring in transposed, inverted, augmented, and
    fragmented forms — the way Bach builds a fugue from a subject.

    Params:
        motif_length:   notes in the seed motif (3–8)
        plan:           development plan name:
                        'aba', 'sequence_descent',
                        'fugue_exposition', 'gradual_evolution'
        step_range:     (min, max) scale degree steps for motif generation
        motif_durations: duration choices for motif notes
        motif_duration_weights: probability weights for durations
    """
    from motifs import (generate_motif, apply_transform,
                        PLANS, DevelopmentPlan)

    if not scale or not grid:
        return []

    # 1. Generate the seed motif
    seed = generate_motif(
        length=motif_length,
        step_range=step_range,
        duration_choices=motif_durations or [2, 3, 4],
        duration_weights=motif_duration_weights or [0.3, 0.4, 0.3],
        name='seed',
    )

    # 2. Get the development plan
    plan_fn = PLANS.get(plan)
    if plan_fn is None:
        plan_fn = PLANS['gradual_evolution']
    dev_plan = plan_fn('seed')

    # 3. Execute the plan: transform motifs and render to notes
    notes = []
    current_tick = 0
    end_tick = grid[-1].tick + ticks_per_16th if grid else 0

    # Choose a starting position in the scale (near the middle)
    mid_idx = len(scale) // 2

    # Loop through the plan until the section is full.
    # First pass plays the full plan; subsequent passes cycle through
    # to fill remaining time (so the development keeps evolving).
    while current_tick < end_tick:
        for step in dev_plan.steps:
            if current_tick >= end_tick:
                break

            # Apply the transformation
            transformed = apply_transform(seed, step.transform, **step.transform_args)

            for rep in range(step.repeat):
                if current_tick >= end_tick:
                    break

                for mn in transformed.notes:
                    if current_tick >= end_tick:
                        break

                    # Convert scale degree to actual pitch
                    target_idx = mid_idx + mn.degree
                    target_idx = max(0, min(len(scale) - 1, target_idx))
                    pitch = scale[target_idx]

                    # Duration
                    dur_ticks = mn.duration * ticks_per_16th

                    # Velocity with offset
                    base_vel = np.random.randint(velocity_range[0], velocity_range[1])
                    vel = int(np.clip(base_vel + mn.velocity_offset, 1, 127))

                    # Density gate: skip some notes to breathe
                    if np.random.random() > density * 1.5:
                        current_tick += dur_ticks
                        continue

                    notes.append(Note(
                        pitch=pitch,
                        start_tick=current_tick,
                        duration_ticks=dur_ticks,
                        velocity=vel,
                        channel=channel,
                    ))

                    current_tick += dur_ticks

                # Small gap between repetitions
                current_tick += ticks_per_16th

    return notes


from bass import bass_voice


# ── Behavior dispatch ────────────────────────────────────────────────

BEHAVIORS = {
    'random_walk':   random_walk,
    'random_select': random_select,
    'drone':         drone,
    'arpeggio':      arpeggio,
    'ostinato':      ostinato,
    'develop':       develop,
    'bass':          bass_voice,
}
