"""
bass.py — Dedicated bass voice behavior with configurable style.

Bass isn't just another voice — it's the foundation.  Different
styles demand fundamentally different approaches:

  root_lock   — Plays root notes on strong beats, fifth on
                secondary beats.  Absolutely steady.  U2, disco,
                ambient.  Never leaves home.

  walking     — Stepwise through the scale, always moving, always
                connected.  Jazz, soul.  Every note leads to the
                next one.

  ostinato    — Short repeating pattern (1–2 bars) with minimal
                variation.  Electronic, pop.  The sequenced bass
                of Depeche Mode, Pet Shop Boys.

  melodic     — An independent voice with its own motif development.
                Rush, classical counterpoint, Yes.  The bass has
                opinions.

  pulse       — Steady eighth or quarter notes on the root/fifth.
                Motorik, krautrock, minimalism.  Hypnotic.

All styles share one rule: the bass is ALWAYS PRESENT.  No gaps.
Every beat has a bass note.  The style just determines which notes
and how they move.
"""

import numpy as np
from genmuso.music.voices import Note
from genmuso.music.rhythm import GridPosition, phrase_weight
from genmuso.music.scales import (
    build_scale, root_note_in_range, chord_tones as _chord_tones,
    nearest_in_scale,
)
from genmuso.music.motifs import generate_motif, apply_transform, PLANS


def bass_voice(
    grid: list[GridPosition],
    scale: list[int],
    density: float = 0.5,
    velocity_range: tuple = (60, 90),
    channel: int = 0,
    ticks_per_16th: int = 120,
    phrase_length: int = 4,
    total_bars: int = 8,
    # Bass-specific
    style: str = 'root_lock',
    root_pc: int = 0,
    mode: str = 'minor',
    low: int = 36,
    high: int = 55,
    note_length: int = 4,
    **kwargs,
) -> list[Note]:
    """
    Generate a bass line that fills the entire section with no gaps.

    style:
        'root_lock'  — root/fifth on strong beats (U2, disco, ambient)
        'walking'    — stepwise scale motion (jazz, soul)
        'ostinato'   — repeating pattern (DM, PSB, electronic)
        'melodic'    — motif development (Rush, classical, prog)
        'pulse'      — steady repeated notes (motorik, minimal)
    """
    dispatch = {
        'root_lock': _root_lock,
        'walking':   _walking,
        'ostinato':  _ostinato,
        'melodic':   _melodic,
        'pulse':     _pulse,
    }

    fn = dispatch.get(style, _root_lock)
    return fn(
        grid=grid, scale=scale, density=density,
        velocity_range=velocity_range, channel=channel,
        ticks_per_16th=ticks_per_16th, phrase_length=phrase_length,
        total_bars=total_bars, root_pc=root_pc, mode=mode,
        low=low, high=high, note_length=note_length, **kwargs,
    )


# ── Style: Root Lock ─────────────────────────────────────────────────
# Plays root on downbeats, fifth on secondary beats.  Absolutely solid.

def _root_lock(
    grid, scale, velocity_range, channel, ticks_per_16th,
    phrase_length, total_bars, root_pc, low, high,
    note_length=4, density=0.5, **kwargs,
) -> list[Note]:
    notes = []
    root = root_note_in_range(root_pc, low, high)
    fifth = root + 7 if root + 7 <= high else root

    i = 0
    while i < len(grid):
        gp = grid[i]

        # Always play on strong beats (weight >= 0.5)
        # Sometimes play on medium beats based on density
        if gp.weight >= 0.5 or (gp.weight >= 0.3 and np.random.random() < density):
            # Root on strongest beats, fifth on secondary
            if gp.weight >= 0.8:
                pitch = root
                vel_boost = 8
            elif gp.weight >= 0.5:
                pitch = fifth if np.random.random() < 0.4 else root
                vel_boost = 0
            else:
                pitch = root
                vel_boost = -5

            vel = np.random.randint(velocity_range[0], velocity_range[1]) + vel_boost
            vel = int(np.clip(vel, 1, 127))

            dur = note_length * ticks_per_16th
            notes.append(Note(
                pitch=pitch, start_tick=gp.tick,
                duration_ticks=dur, velocity=vel, channel=channel,
            ))
            i += note_length
            continue

        i += 1

    return notes


# ── Style: Walking ───────────────────────────────────────────────────
# Stepwise motion through the scale, one note per beat.

def _walking(
    grid, scale, velocity_range, channel, ticks_per_16th,
    phrase_length, total_bars, note_length=4,
    density=0.6, **kwargs,
) -> list[Note]:
    if not scale:
        return []

    notes = []
    idx = len(scale) // 4  # start in lower range
    i = 0

    while i < len(grid):
        gp = grid[i]

        # Walk bass typically plays on every beat (every 4 16th-notes)
        if gp.position % 4 == 0 or (np.random.random() < density * 0.3):
            # Step: mostly ±1, occasionally ±2
            step = np.random.choice([-2, -1, 1, 2], p=[0.1, 0.4, 0.4, 0.1])
            idx = max(0, min(len(scale) - 1, idx + step))
            pitch = scale[idx]

            vel = np.random.randint(velocity_range[0], velocity_range[1])
            if gp.weight >= 0.8:
                vel = min(127, vel + 8)

            dur = note_length * ticks_per_16th
            notes.append(Note(
                pitch=pitch, start_tick=gp.tick,
                duration_ticks=dur, velocity=vel, channel=channel,
            ))
            i += note_length
            continue

        i += 1

    return notes


# ── Style: Ostinato ──────────────────────────────────────────────────
# Short repeating pattern, DM/PSB style.

def _ostinato(
    grid, scale, velocity_range, channel, ticks_per_16th,
    phrase_length, total_bars, note_length=2,
    density=0.5, pattern_bars=2, variation=0.06, **kwargs,
) -> list[Note]:
    if not scale:
        return []

    # Build a base pattern for pattern_bars
    positions_per_bar = len([gp for gp in grid if gp.bar == 0])
    base_grid = [gp for gp in grid if gp.bar < pattern_bars]
    idx = len(scale) // 4

    pattern = []
    pos = 0
    while pos < len(base_grid):
        gp = base_grid[pos]
        if gp.weight >= 0.3 or np.random.random() < density:
            step = np.random.randint(-1, 2)
            idx = max(0, min(len(scale) - 1, idx + step))
            pattern.append((gp.position + gp.bar * positions_per_bar,
                            scale[idx], note_length))
            pos += note_length
        else:
            pos += 1

    if not pattern:
        pattern = [(0, scale[len(scale) // 4], note_length)]

    # Stamp the pattern across all bars
    notes = []
    pattern_ticks = pattern_bars * positions_per_bar * ticks_per_16th
    total_ticks = grid[-1].tick + ticks_per_16th if grid else 0
    rep = 0

    while rep * pattern_ticks < total_ticks:
        tick_offset = rep * pattern_ticks
        for rel_pos, pitch, dur in pattern:
            actual_tick = tick_offset + rel_pos * ticks_per_16th
            if actual_tick >= total_ticks:
                break

            # Subtle variation
            actual_pitch = pitch
            if np.random.random() < variation:
                try:
                    si = scale.index(pitch)
                    si += np.random.choice([-1, 1])
                    si = max(0, min(len(scale) - 1, si))
                    actual_pitch = scale[si]
                except ValueError:
                    pass

            vel = np.random.randint(velocity_range[0], velocity_range[1])
            notes.append(Note(
                pitch=actual_pitch, start_tick=actual_tick,
                duration_ticks=dur * ticks_per_16th,
                velocity=vel, channel=channel,
            ))
        rep += 1

    return notes


# ── Style: Melodic ───────────────────────────────────────────────────
# Motif-based development that LOOPS to fill the section.

def _melodic(
    grid, scale, velocity_range, channel, ticks_per_16th,
    phrase_length, total_bars, density=0.6,
    motif_length=4, plan='gradual_evolution',
    step_range=(-2, 3), **kwargs,
) -> list[Note]:
    if not scale or not grid:
        return []

    seed = generate_motif(
        length=motif_length,
        step_range=tuple(step_range) if isinstance(step_range, list) else step_range,
        duration_choices=[3, 4, 6],
        duration_weights=[0.3, 0.4, 0.3],
        name='bass_seed',
    )

    plan_fn = PLANS.get(plan, PLANS['gradual_evolution'])
    dev_plan = plan_fn('bass_seed')
    mid_idx = len(scale) // 4

    notes = []
    current_tick = 0
    end_tick = grid[-1].tick + ticks_per_16th

    # KEY DIFFERENCE: loop through the plan until the section is full
    while current_tick < end_tick:
        for step in dev_plan.steps:
            if current_tick >= end_tick:
                break

            transformed = apply_transform(seed, step.transform, **step.transform_args)

            for rep in range(step.repeat):
                if current_tick >= end_tick:
                    break

                for mn in transformed.notes:
                    if current_tick >= end_tick:
                        break

                    target_idx = mid_idx + mn.degree
                    target_idx = max(0, min(len(scale) - 1, target_idx))
                    pitch = scale[target_idx]
                    dur_ticks = mn.duration * ticks_per_16th

                    if np.random.random() < density * 1.5:
                        base_vel = np.random.randint(velocity_range[0], velocity_range[1])
                        vel = int(np.clip(base_vel + mn.velocity_offset, 1, 127))

                        notes.append(Note(
                            pitch=pitch, start_tick=current_tick,
                            duration_ticks=dur_ticks, velocity=vel,
                            channel=channel,
                        ))

                    current_tick += dur_ticks

                current_tick += ticks_per_16th  # breath between reps

    return notes


# ── Style: Pulse ─────────────────────────────────────────────────────
# Steady repeated notes on root. Motorik / minimalist.

def _pulse(
    grid, scale, velocity_range, channel, ticks_per_16th,
    phrase_length, total_bars, root_pc=0, low=36, high=55,
    note_length=2, density=0.8, **kwargs,
) -> list[Note]:
    root = root_note_in_range(root_pc, low, high)
    notes = []
    i = 0

    while i < len(grid):
        gp = grid[i]

        # Pulse plays almost every subdivision
        if np.random.random() < density:
            # Slight velocity accent on strong beats
            vel = np.random.randint(velocity_range[0], velocity_range[1])
            if gp.weight >= 0.8:
                vel = min(127, vel + 10)
            elif gp.weight < 0.3:
                vel = max(1, vel - 8)

            dur = note_length * ticks_per_16th
            notes.append(Note(
                pitch=root, start_tick=gp.tick,
                duration_ticks=dur, velocity=vel, channel=channel,
            ))
            i += note_length
            continue

        i += 1

    return notes
