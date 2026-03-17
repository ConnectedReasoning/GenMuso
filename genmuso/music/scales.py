"""
scales.py — Music theory: scales, modes, and chord construction.

Every pitch operation in GenMuso2 flows through this module.
Scales are represented as lists of MIDI note numbers so that voices
can index directly into them without worrying about theory.
"""

# ── Note names ↔ pitch classes ────────────────────────────────────────

NOTE_NAMES = {
    'C': 0, 'C#': 1, 'Db': 1, 'D': 2, 'D#': 3, 'Eb': 3,
    'E': 4, 'F': 5, 'F#': 6, 'Gb': 6, 'G': 7, 'G#': 8,
    'Ab': 8, 'A': 9, 'A#': 10, 'Bb': 10, 'B': 11,
}

PITCH_CLASS_NAMES = {
    0: 'C', 1: 'C#', 2: 'D', 3: 'Eb', 4: 'E', 5: 'F',
    6: 'F#', 7: 'G', 8: 'Ab', 9: 'A', 10: 'Bb', 11: 'B',
}


# ── Mode interval patterns ───────────────────────────────────────────
# Each mode is a list of semitone offsets from the root.

MODES = {
    # Diatonic modes
    'major':                [0, 2, 4, 5, 7, 9, 11],
    'minor':                [0, 2, 3, 5, 7, 8, 10],
    'dorian':               [0, 2, 3, 5, 7, 9, 10],
    'phrygian':             [0, 1, 3, 5, 7, 8, 10],
    'lydian':               [0, 2, 4, 6, 7, 9, 11],
    'mixolydian':           [0, 2, 4, 5, 7, 9, 10],
    'aeolian':              [0, 2, 3, 5, 7, 8, 10],
    'locrian':              [0, 1, 3, 5, 6, 8, 10],

    # Pentatonic
    'pentatonic_major':     [0, 2, 4, 7, 9],
    'pentatonic_minor':     [0, 3, 5, 7, 10],

    # Harmonic / melodic
    'harmonic_minor':       [0, 2, 3, 5, 7, 8, 11],
    'melodic_minor':        [0, 2, 3, 5, 7, 9, 11],

    # Exotic
    'arabic_double_harmonic': [0, 1, 4, 5, 7, 8, 11],
    'whole_tone':           [0, 2, 4, 6, 8, 10],
    'blues':                [0, 3, 5, 6, 7, 10],
    'japanese':             [0, 1, 5, 7, 8],
    'hungarian_minor':      [0, 2, 3, 6, 7, 8, 11],
}


def note_to_midi(name: str, octave: int = 4) -> int:
    """Convert note name + octave to MIDI number.  'C4' → 60."""
    return NOTE_NAMES[name] + (octave + 1) * 12


def midi_to_name(midi_note: int) -> str:
    """Convert MIDI number to readable name.  60 → 'C4'."""
    octave = (midi_note // 12) - 1
    pc = midi_note % 12
    return f"{PITCH_CLASS_NAMES[pc]}{octave}"


def build_scale(root_pc: int, mode: str, low: int = 0, high: int = 127) -> list[int]:
    """
    Build a list of MIDI note numbers for a root pitch class and mode,
    filtered to [low, high].

    root_pc: pitch class 0–11 (C=0, C#=1, … B=11)
             or a MIDI note number (mod 12 is taken)
    mode:    key into MODES
    """
    intervals = MODES[mode]
    pc = root_pc % 12
    return [n for n in range(low, high + 1) if (n - pc) % 12 in intervals]


def scale_in_range(root_pc: int, mode: str, low: int, high: int) -> list[int]:
    """Convenience alias for build_scale with explicit range."""
    return build_scale(root_pc, mode, low, high)


def chord_tones(root_pc: int, mode: str, degree: int = 1,
                low: int = 36, high: int = 84) -> list[int]:
    """
    Build triad tones from a scale degree (1-indexed).

    The chord quality (major/minor/diminished) emerges naturally from
    the scale — no hard-coded major triads.  This fixes GenMuso's bug
    where chords were always major regardless of mode.

    Returns MIDI notes in [low, high] that belong to the triad.
    """
    intervals = MODES[mode]
    pc = root_pc % 12
    n = len(intervals)
    idx = (degree - 1) % n

    # Triad = root, third, fifth of the scale built on this degree
    triad_pcs = set()
    for offset in (0, 2, 4):
        triad_pcs.add((pc + intervals[(idx + offset) % n]) % 12)

    return [m for m in range(low, high + 1) if m % 12 in triad_pcs]


def seventh_tones(root_pc: int, mode: str, degree: int = 1,
                  low: int = 36, high: int = 84) -> list[int]:
    """Same as chord_tones but adds the 7th for richer harmony."""
    intervals = MODES[mode]
    pc = root_pc % 12
    n = len(intervals)
    idx = (degree - 1) % n

    chord_pcs = set()
    for offset in (0, 2, 4, 6):
        chord_pcs.add((pc + intervals[(idx + offset) % n]) % 12)

    return [m for m in range(low, high + 1) if m % 12 in chord_pcs]


def nearest_in_scale(pitch: int, scale: list[int]) -> int:
    """Snap a pitch to the nearest note in the scale."""
    if not scale:
        return pitch
    return min(scale, key=lambda n: abs(n - pitch))


def root_note_in_range(root_pc: int, low: int, high: int) -> int:
    """Find the lowest occurrence of root_pc in [low, high]."""
    pc = root_pc % 12
    for n in range(low, high + 1):
        if n % 12 == pc:
            return n
    return low
