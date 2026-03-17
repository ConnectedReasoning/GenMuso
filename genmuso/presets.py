"""
presets.py — Ready-made compositional plans.

Each preset returns a Composition object.  This is where creative
intent lives — the harmonic plan, voice assignments, density, tempo.

Think of these as "scores" that the generator interprets.
"""

from composition import Composition, Section, VoiceConfig


# ── Voice templates ──────────────────────────────────────────────────
# Reusable voice configs that can be tuned per-preset.

def _soprano_walk(**overrides):
    defaults = dict(
        name='soprano', behavior='random_walk', channel=0, program=48,
        low=72, high=96, density=0.25,
        velocity_range=(55, 85),
        note_lengths=[2, 3, 4, 6], note_length_weights=[0.15, 0.35, 0.3, 0.2],
        phrase_length=4, params={'leap_probability': 0.06},
    )
    defaults.update(overrides)
    return VoiceConfig(**defaults)


def _tenor_walk(**overrides):
    defaults = dict(
        name='tenor_walk', behavior='random_walk', channel=1, program=48,
        low=48, high=72, density=0.2,
        velocity_range=(50, 80),
        note_lengths=[3, 4, 6, 8], note_length_weights=[0.15, 0.3, 0.35, 0.2],
        phrase_length=4, params={'leap_probability': 0.05},
    )
    defaults.update(overrides)
    return VoiceConfig(**defaults)


def _tenor_random(**overrides):
    defaults = dict(
        name='tenor_random', behavior='random_select', channel=2, program=48,
        low=48, high=72, density=0.15,
        velocity_range=(45, 75),
        note_lengths=[4, 6, 8], note_length_weights=[0.3, 0.4, 0.3],
        phrase_length=4,
    )
    defaults.update(overrides)
    return VoiceConfig(**defaults)


def _bass_walk(**overrides):
    defaults = dict(
        name='bass', behavior='random_walk', channel=3, program=48,
        low=24, high=48, density=0.15,
        velocity_range=(50, 80),
        note_lengths=[4, 6, 8, 12], note_length_weights=[0.15, 0.3, 0.35, 0.2],
        phrase_length=4, params={'leap_probability': 0.04},
    )
    defaults.update(overrides)
    return VoiceConfig(**defaults)


def _drone(**overrides):
    defaults = dict(
        name='drone', behavior='drone', channel=4, program=52,
        low=36, high=60, density=1.0,
        velocity_range=(55, 55),
        phrase_length=4, params={'include_fifth': True},
    )
    defaults.update(overrides)
    return VoiceConfig(**defaults)


def _ostinato_bass(**overrides):
    defaults = dict(
        name='ostinato', behavior='ostinato', channel=3, program=33,
        low=36, high=55, density=0.45,
        velocity_range=(60, 85),
        note_lengths=[2], note_length_weights=[1.0],
        phrase_length=4,
        params={'note_length': 2, 'pattern_bars': 2, 'variation': 0.08},
    )
    defaults.update(overrides)
    return VoiceConfig(**defaults)


def _arp(**overrides):
    defaults = dict(
        name='arpeggio', behavior='arpeggio', channel=1, program=4,
        low=48, high=72, density=0.4,
        velocity_range=(50, 75),
        phrase_length=4,
        params={'pattern': 'up_down', 'note_length': 2, 'degree': 1},
    )
    defaults.update(overrides)
    return VoiceConfig(**defaults)


# ══════════════════════════════════════════════════════════════════════
# PRESET: Passion for the Heavens (remastered)
# ══════════════════════════════════════════════════════════════════════
#
# The harmonic plan from Bach's St. Matthew Passion: 46 movements,
# each mapped to ~1 minute of generative music.  The key sequence is
# the compositional DNA; the randomness operates within it.

PASSION_KEYS = [
    ('E',  'minor'),   # 1
    ('G',  'major'),   # 2
    ('B',  'minor'),   # 3
    ('D',  'major'),   # 4a
    ('C',  'major'),   # 4b
    ('A',  'minor'),   # 4c
    ('D',  'minor'),   # 4d
    ('Bb', 'minor'),   # 4e
    ('E',  'minor'),   # 5
    ('B',  'minor'),   # 5b
    ('F#', 'minor'),   # 6
    ('D',  'major'),   # 7
    ('B',  'minor'),   # 8
    ('G',  'major'),   # 9a
    ('C',  'major'),   # 9b
    ('F',  'minor'),   # 9c
    ('C',  'minor'),   # 9d
    ('Ab', 'major'),   # 10
    ('F',  'minor'),   # 11a
    ('G',  'major'),   # 11b
    ('E',  'minor'),   # 12a
    ('C',  'major'),   # 12b
    ('G',  'major'),   # 13
    ('B',  'minor'),   # 14
    ('E',  'major'),   # 15
    ('A',  'major'),   # 16a
    ('G',  'minor'),   # 16b
    ('Eb', 'major'),   # 17
    ('F',  'major'),   # 18a
    ('Ab', 'major'),   # 18b
    ('F',  'minor'),   # 19a
    ('G',  'major'),   # 19b
    ('C',  'minor'),   # 20
    ('B',  'major'),   # 21a
    ('G',  'major'),   # 21b
    ('D',  'minor'),   # 22a
    ('Bb', 'major'),   # 22b
    ('G',  'minor'),   # 23
    ('F',  'major'),   # 24a
    ('B',  'minor'),   # 24b
    ('D',  'major'),   # 25
    ('G',  'major'),   # 26
    ('E',  'minor'),   # 27
    ('F#', 'major'),   # 28a
    ('C#', 'minor'),   # 28b
    ('E',  'minor'),   # 29 — returns home
]


def passion_for_the_heavens() -> Composition:
    """
    46-section generative piece following the key sequence of
    Bach's St. Matthew Passion.  ~50 minutes at 60 BPM.
    """
    sections = []
    for key, mode in PASSION_KEYS:
        sections.append(Section(
            key=key, mode=mode,
            bars=16, tempo=60, meter='4/4',
            voices=[
                _soprano_walk(density=0.22),
                _tenor_walk(density=0.18),
                _tenor_random(density=0.12),
                _bass_walk(density=0.12),
                _drone(velocity_range=(50, 50)),
            ],
        ))

    return Composition(name='Passion_for_the_Heavens', sections=sections)


# ══════════════════════════════════════════════════════════════════════
# PRESET: Focus — for work
# ══════════════════════════════════════════════════════════════════════
#
# Calm, minimal, pentatonic.  Gentle key movement through relative
# keys.  Sparse enough to fade into background.

FOCUS_KEYS = [
    ('A',  'pentatonic_minor'),
    ('C',  'pentatonic_major'),
    ('G',  'pentatonic_major'),
    ('E',  'pentatonic_minor'),
    ('D',  'pentatonic_minor'),
    ('F',  'pentatonic_major'),
    ('A',  'pentatonic_minor'),
    ('E',  'pentatonic_minor'),
]


def focus() -> Composition:
    """
    ~30 minutes of gentle focus music.  Pentatonic scales,
    sparse density, slow tempo.  For deep work.
    """
    sections = []
    for key, mode in FOCUS_KEYS:
        sections.append(Section(
            key=key, mode=mode,
            bars=32, tempo=68, meter='4/4',
            voices=[
                _soprano_walk(
                    density=0.15, velocity_range=(40, 65), program=46,
                    note_lengths=[4, 6, 8, 12],
                    note_length_weights=[0.1, 0.3, 0.35, 0.25],
                ),
                _ostinato_bass(
                    density=0.35, velocity_range=(50, 70), program=33,
                    params={'note_length': 3, 'pattern_bars': 2, 'variation': 0.06},
                ),
                _drone(velocity_range=(40, 40), program=52),
            ],
        ))

    return Composition(name='Focus', sections=sections)


# ══════════════════════════════════════════════════════════════════════
# PRESET: Drive — for the road
# ══════════════════════════════════════════════════════════════════════
#
# More energy.  Dorian/mixolydian modes, arpeggiated movement,
# denser bass, higher tempo.

DRIVE_KEYS = [
    ('D', 'dorian'),
    ('G', 'mixolydian'),
    ('A', 'dorian'),
    ('E', 'minor'),
    ('C', 'mixolydian'),
    ('F', 'dorian'),
    ('G', 'minor'),
    ('D', 'dorian'),
    ('A', 'minor'),
    ('E', 'dorian'),
    ('B', 'minor'),
    ('D', 'dorian'),
]


def drive() -> Composition:
    """
    ~25 minutes of driving music.  More rhythmic energy,
    arpeggiated textures, modal harmony.
    """
    sections = []
    for key, mode in DRIVE_KEYS:
        sections.append(Section(
            key=key, mode=mode,
            bars=16, tempo=108, meter='4/4', swing=0.15,
            voices=[
                _soprano_walk(
                    density=0.3, velocity_range=(60, 95), program=81,
                    note_lengths=[1, 2, 3, 4],
                    note_length_weights=[0.25, 0.35, 0.25, 0.15],
                ),
                _arp(
                    density=0.45, velocity_range=(55, 80), program=4,
                    params={'pattern': 'up_down', 'note_length': 2, 'degree': 1},
                ),
                _ostinato_bass(
                    density=0.5, velocity_range=(65, 90), program=33,
                    params={'note_length': 2, 'pattern_bars': 2, 'variation': 0.1},
                ),
                _drone(velocity_range=(45, 45), program=52, low=24, high=48),
            ],
        ))

    return Composition(name='Drive', sections=sections)


# ══════════════════════════════════════════════════════════════════════
# PRESET: Garden — pastoral
# ══════════════════════════════════════════════════════════════════════
#
# Lydian and major modes for brightness.  Arpeggiated figures,
# gentle random walk.  Medium-slow tempo.

GARDEN_KEYS = [
    ('F',  'lydian'),
    ('C',  'major'),
    ('G',  'lydian'),
    ('D',  'major'),
    ('A',  'lydian'),
    ('E',  'major'),
    ('B',  'lydian'),
    ('F#', 'major'),
    ('C',  'lydian'),
    ('G',  'major'),
]


def garden() -> Composition:
    """
    ~25 minutes of pastoral music.  Bright modes, gentle arpeggios,
    medium-slow tempo.  For gardening, cooking, afternoon light.
    """
    sections = []
    for key, mode in GARDEN_KEYS:
        sections.append(Section(
            key=key, mode=mode,
            bars=24, tempo=76, meter='3/4',
            voices=[
                _soprano_walk(
                    density=0.2, velocity_range=(45, 70), program=73,
                    note_lengths=[3, 4, 6, 8],
                    note_length_weights=[0.15, 0.3, 0.35, 0.2],
                ),
                _arp(
                    density=0.35, velocity_range=(45, 65), program=46,
                    low=48, high=72,
                    params={'pattern': 'up', 'note_length': 2, 'degree': 1},
                ),
                _bass_walk(
                    density=0.12, velocity_range=(50, 70), program=48,
                    note_lengths=[6, 8, 12],
                    note_length_weights=[0.3, 0.4, 0.3],
                ),
                _drone(velocity_range=(40, 40), program=52),
            ],
        ))

    return Composition(name='Garden', sections=sections)


# ══════════════════════════════════════════════════════════════════════
# PRESET: Altairean Sunset (Arabic double harmonic)
# ══════════════════════════════════════════════════════════════════════
#
# Reviving the GenMuso original: long-form, exotic scale, meditative.

ALTAIREAN_KEYS = [
    ('G',  'arabic_double_harmonic'),
    ('C',  'arabic_double_harmonic'),
    ('D',  'arabic_double_harmonic'),
    ('G',  'harmonic_minor'),
    ('Bb', 'arabic_double_harmonic'),
    ('F',  'arabic_double_harmonic'),
    ('G',  'arabic_double_harmonic'),
]


def altairean_sunset() -> Composition:
    """
    ~20 minutes of meditative music in the Arabic double harmonic scale.
    A reimagining of GenMuso's AltaireanSunset.
    """
    sections = []
    for key, mode in ALTAIREAN_KEYS:
        sections.append(Section(
            key=key, mode=mode,
            bars=24, tempo=64, meter='4/4',
            voices=[
                _soprano_walk(
                    density=0.2, velocity_range=(50, 75), program=71,
                    low=60, high=84,
                    note_lengths=[4, 6, 8, 12],
                    note_length_weights=[0.1, 0.3, 0.35, 0.25],
                    params={'leap_probability': 0.1},
                ),
                _tenor_walk(
                    density=0.15, velocity_range=(45, 70), program=71,
                    note_lengths=[6, 8, 12, 16],
                    note_length_weights=[0.15, 0.3, 0.35, 0.2],
                ),
                _bass_walk(
                    density=0.1, velocity_range=(50, 70), program=48,
                    note_lengths=[8, 12, 16],
                    note_length_weights=[0.3, 0.4, 0.3],
                ),
                _drone(velocity_range=(50, 50), program=52),
            ],
        ))

    return Composition(name='Altairean_Sunset', sections=sections)


# ── Preset registry ──────────────────────────────────────────────────

PRESETS = {
    'passion':   passion_for_the_heavens,
    'focus':     focus,
    'drive':     drive,
    'garden':    garden,
    'altairean': altairean_sunset,
}
