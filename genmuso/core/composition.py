"""
composition.py — Declarative composition format.

A Composition is a sequence of Sections, each with a key, mode,
tempo, and set of voice configurations.  This is the data model
that replaces GenMuso's per-song Python scripts — a new piece is
just a new data structure, not new code.
"""

from dataclasses import dataclass, field
from genmuso.music.scales import NOTE_NAMES


@dataclass
class VoiceConfig:
    """Configuration for a single voice within a section."""

    name: str                    # e.g. 'soprano', 'bass', 'drone'
    behavior: str                # 'random_walk', 'random_select', 'drone',
                                 # 'arpeggio', 'ostinato'
    channel: int = 0             # MIDI channel (0–15)
    program: int = 0             # General MIDI program number
    low: int = 48                # lowest MIDI note
    high: int = 72               # highest MIDI note
    density: float = 0.3         # probability scaling (0–1)
    velocity_range: tuple = (60, 100)
    note_lengths: list = field(default_factory=lambda: [1, 2, 3, 4])
    note_length_weights: list = field(default_factory=lambda: [0.2, 0.4, 0.25, 0.15])
    phrase_length: int = 4       # bars per phrase

    # Behavior-specific overrides (passed as **kwargs)
    params: dict = field(default_factory=dict)


@dataclass
class Section:
    """One segment of a composition: a key, mode, duration, and voices."""

    key: str                     # note name: 'C', 'F#', 'Bb', etc.
    mode: str                    # key into scales.MODES
    bars: int = 8
    tempo: int = 72              # BPM
    meter: str = '4/4'
    swing: float = 0.0           # 0.0–1.0
    voices: list = field(default_factory=list)  # list of VoiceConfig

    @property
    def root_pc(self) -> int:
        """Pitch class (0–11) of the key."""
        return NOTE_NAMES[self.key]


@dataclass
class Composition:
    """
    A complete composition: metadata plus an ordered list of sections.

    This is the top-level object you hand to the generator.
    """

    name: str
    sections: list               # list of Section
    ticks_per_beat: int = 480
    arc: str = 'gradual_build'   # dynamics curve: 'gradual_build', 'wave',
                                 # 'peak_middle', 'slow_burn', 'bookend',
                                 # 'flat', 'terraced'
    breathing: str = 'swell'     # within-section: 'swell', 'breathe',
                                 # 'steady', 'fadeout', 'fadein'

    @property
    def total_bars(self) -> int:
        return sum(s.bars for s in self.sections)

    def summary(self) -> str:
        from genmuso.music.dynamics import compute_section_intensity
        lines = [f"Composition: {self.name}"]
        lines.append(f"  Sections: {len(self.sections)}  |  Arc: {self.arc}  |  Breathing: {self.breathing}")
        lines.append(f"  Total bars: {self.total_bars}")
        for i, s in enumerate(self.sections):
            intensity = compute_section_intensity(i, len(self.sections), self.arc)
            bar = '█' * int(intensity * 10) + '░' * (10 - int(intensity * 10))
            voices = ', '.join(v.name for v in s.voices)
            lines.append(f"  [{i+1:>3}] {s.key} {s.mode:<20s} "
                         f"{s.bars} bars @ {s.tempo} BPM  {bar}  {voices}")
        return '\n'.join(lines)
