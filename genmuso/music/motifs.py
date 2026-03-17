"""
motifs.py — Motif generation, transformation, and development.

This is the bridge between randomness and composition.  The system:

  1. Generates short melodic fragments (motifs) randomly
  2. Transforms them using classical techniques (Bach's toolkit)
  3. Builds phrases and sections by combining transformed motifs

The randomness seeds the ideas.  The development gives them structure.

Transformation catalog (from Bach's practice):
  transpose     — shift the whole motif up or down by scale degrees
  invert        — flip intervals (up becomes down, down becomes up)
  retrograde    — play the motif backwards
  augment       — stretch durations (slower, more majestic)
  diminish      — compress durations (faster, more urgent)
  sequence      — repeat the motif starting on successive scale degrees
  fragment      — take a piece of the motif and repeat it
  ornament      — add passing tones and neighbor tones
  rhythmic_shift — keep the pitches, change the rhythm
"""

import numpy as np
from dataclasses import dataclass, field
from copy import deepcopy


@dataclass
class MotifNote:
    """
    A note within a motif, represented as scale degrees and relative
    durations so the motif is portable across keys and tempos.

    degree:   scale degree offset from the motif's starting note (0-indexed)
              e.g., [0, 2, 4, 3, 1] = root, third, fifth, fourth, second
    duration: relative duration in 16th notes
    velocity_offset: relative to the voice's base velocity (-20 to +20)
    """
    degree: int
    duration: int
    velocity_offset: int = 0


@dataclass
class Motif:
    """A short melodic idea: the atomic unit of musical structure."""
    notes: list[MotifNote]
    name: str = ''

    @property
    def length(self) -> int:
        """Total duration in 16th notes."""
        return sum(n.duration for n in self.notes)

    def degrees(self) -> list[int]:
        return [n.degree for n in self.notes]

    def durations(self) -> list[int]:
        return [n.duration for n in self.notes]

    def __repr__(self):
        degs = self.degrees()
        return f"Motif({self.name}: degrees={degs}, len={self.length})"


# ══════════════════════════════════════════════════════════════════════
# MOTIF GENERATION — the random seed
# ══════════════════════════════════════════════════════════════════════

def generate_motif(
    length: int = 4,
    step_range: tuple = (-2, 3),
    duration_choices: list = None,
    duration_weights: list = None,
    name: str = '',
) -> Motif:
    """
    Create a random motif of `length` notes using stepwise motion.

    This is where randomness enters the system.  Everything after this
    is deterministic transformation.
    """
    duration_choices = duration_choices or [1, 2, 3, 4]
    duration_weights = duration_weights or [0.2, 0.4, 0.25, 0.15]
    wt = np.array(duration_weights[:len(duration_choices)], dtype=float)
    wt /= wt.sum()

    notes = []
    current_degree = 0

    for i in range(length):
        if i > 0:
            step = np.random.randint(step_range[0], step_range[1])
            current_degree += step

        dur = int(np.random.choice(duration_choices, p=wt))
        vel_offset = np.random.randint(-8, 9)

        # First note slightly accented
        if i == 0:
            vel_offset = abs(vel_offset)

        notes.append(MotifNote(
            degree=current_degree,
            duration=dur,
            velocity_offset=vel_offset,
        ))

    return Motif(notes=notes, name=name or f"motif_{np.random.randint(1000)}")


# ══════════════════════════════════════════════════════════════════════
# TRANSFORMATIONS — Bach's toolkit
# ══════════════════════════════════════════════════════════════════════

def transpose(motif: Motif, degrees: int) -> Motif:
    """
    Shift every note up or down by `degrees` scale degrees.

    transpose(motif, 2) moves the whole motif up a third.
    transpose(motif, -1) moves it down a second.

    Bach used this constantly — stating a subject in the tonic,
    then the dominant, then the relative minor.
    """
    m = deepcopy(motif)
    for note in m.notes:
        note.degree += degrees
    m.name = f"{motif.name}_t{degrees:+d}"
    return m


def invert(motif: Motif) -> Motif:
    """
    Flip all intervals: ascending becomes descending and vice versa.

    If the original goes [0, 2, 4, 3], the inversion goes [0, -2, -4, -3].

    Bach's fugues use this extensively — the subject's mirror image
    creates contrast while maintaining recognizability.
    """
    m = deepcopy(motif)
    base = m.notes[0].degree
    for note in m.notes:
        note.degree = base - (note.degree - base)
    m.name = f"{motif.name}_inv"
    return m


def retrograde(motif: Motif) -> Motif:
    """
    Reverse the order of notes (pitches AND durations).

    The motif played backwards.  Bach's crab canons use this.
    """
    m = deepcopy(motif)
    m.notes = list(reversed(m.notes))
    m.name = f"{motif.name}_ret"
    return m


def retrograde_invert(motif: Motif) -> Motif:
    """Invert then retrograde.  The most distant transformation."""
    m = invert(motif)
    m = retrograde(m)
    m.name = f"{motif.name}_retinv"
    return m


def augment(motif: Motif, factor: int = 2) -> Motif:
    """
    Multiply all durations by `factor`.

    augment(motif, 2) = twice as slow.  Bach uses this to create
    a sense of grandeur, often in the bass voice of a fugue's final
    statement (stretto).
    """
    m = deepcopy(motif)
    for note in m.notes:
        note.duration *= factor
    m.name = f"{motif.name}_aug{factor}"
    return m


def diminish(motif: Motif, factor: int = 2) -> Motif:
    """
    Divide all durations by `factor` (minimum 1).

    diminish(motif, 2) = twice as fast.  Creates urgency.
    Bach stacks diminished entries on top of augmented ones
    in fugue stretti.
    """
    m = deepcopy(motif)
    for note in m.notes:
        note.duration = max(1, note.duration // factor)
    m.name = f"{motif.name}_dim{factor}"
    return m


def sequence(motif: Motif, steps: list[int]) -> list[Motif]:
    """
    Create a melodic sequence: the motif repeated at successive
    scale degree offsets.

    sequence(motif, [0, -1, -2]) gives the original, then down a
    second, then down a third.  This is one of the most common
    development techniques in all tonal music.
    """
    return [transpose(motif, s) for s in steps]


def fragment(motif: Motif, start: int = 0, length: int = None) -> Motif:
    """
    Extract a portion of the motif.

    fragment(motif, 0, 2) takes the first two notes — the "head motif."
    Bach often develops just the opening gesture of a subject.
    """
    if length is None:
        length = max(1, len(motif.notes) // 2)
    end = min(start + length, len(motif.notes))
    m = Motif(
        notes=deepcopy(motif.notes[start:end]),
        name=f"{motif.name}_frag{start}:{end}",
    )
    return m


def ornament(motif: Motif, density: float = 0.3) -> Motif:
    """
    Add passing tones and neighbor tones between existing notes.

    density: probability of inserting an ornament between each pair.
    Ornamental notes get shorter durations and softer velocities.
    """
    m = deepcopy(motif)
    new_notes = [m.notes[0]]

    for i in range(1, len(m.notes)):
        if np.random.random() < density:
            prev_deg = m.notes[i - 1].degree
            next_deg = m.notes[i].degree

            # Passing tone: midway between
            if abs(next_deg - prev_deg) >= 2:
                passing = (prev_deg + next_deg) // 2
            else:
                # Neighbor tone: step away and back
                passing = prev_deg + np.random.choice([-1, 1])

            # Steal time from the previous note
            stolen = max(1, m.notes[i - 1].duration // 2)
            new_notes[-1].duration -= stolen

            new_notes.append(MotifNote(
                degree=passing,
                duration=stolen,
                velocity_offset=-10,  # softer
            ))

        new_notes.append(m.notes[i])

    m.notes = new_notes
    m.name = f"{motif.name}_orn"
    return m


def rhythmic_shift(motif: Motif, new_durations: list[int] = None) -> Motif:
    """
    Keep the pitches but change the rhythm.

    If new_durations is None, shuffles the existing durations randomly.
    """
    m = deepcopy(motif)
    if new_durations:
        for i, note in enumerate(m.notes):
            note.duration = new_durations[i % len(new_durations)]
    else:
        durs = [n.duration for n in m.notes]
        np.random.shuffle(durs)
        for note, dur in zip(m.notes, durs):
            note.duration = dur
    m.name = f"{motif.name}_rhy"
    return m


# ══════════════════════════════════════════════════════════════════════
# DEVELOPMENT PLANS — how to build structure from motifs
# ══════════════════════════════════════════════════════════════════════

@dataclass
class DevelopmentStep:
    """One instruction in a development plan."""
    motif_name: str              # which motif to use
    transform: str               # transformation to apply
    transform_args: dict = field(default_factory=dict)
    repeat: int = 1              # how many times to play the result


@dataclass
class DevelopmentPlan:
    """
    A sequence of steps that builds a phrase or section from motifs.

    This is the 'score' that tells the motif voice what to play.
    Each step references a motif by name, specifies a transformation,
    and says how many times to repeat the result.
    """
    steps: list[DevelopmentStep]


# ── Catalog of available transforms ──────────────────────────────────

TRANSFORMS = {
    'original':         lambda m, **kw: deepcopy(m),
    'transpose':        lambda m, **kw: transpose(m, kw.get('degrees', 0)),
    'invert':           lambda m, **kw: invert(m),
    'retrograde':       lambda m, **kw: retrograde(m),
    'retrograde_invert': lambda m, **kw: retrograde_invert(m),
    'augment':          lambda m, **kw: augment(m, kw.get('factor', 2)),
    'diminish':         lambda m, **kw: diminish(m, kw.get('factor', 2)),
    'fragment':         lambda m, **kw: fragment(m, kw.get('start', 0), kw.get('length', None)),
    'ornament':         lambda m, **kw: ornament(m, kw.get('density', 0.3)),
    'rhythmic_shift':   lambda m, **kw: rhythmic_shift(m, kw.get('new_durations', None)),
}


def apply_transform(motif: Motif, transform_name: str, **kwargs) -> Motif:
    """Look up and apply a named transformation."""
    fn = TRANSFORMS.get(transform_name)
    if fn is None:
        raise ValueError(f"Unknown transform: {transform_name}")
    return fn(motif, **kwargs)


# ══════════════════════════════════════════════════════════════════════
# PRESET DEVELOPMENT PLANS
# ══════════════════════════════════════════════════════════════════════

def plan_aba(motif_name: str = 'A') -> DevelopmentPlan:
    """Simple ABA: state, develop, restate."""
    return DevelopmentPlan(steps=[
        DevelopmentStep(motif_name, 'original', repeat=2),
        DevelopmentStep(motif_name, 'transpose', {'degrees': 3}),
        DevelopmentStep(motif_name, 'invert'),
        DevelopmentStep(motif_name, 'transpose', {'degrees': -2}),
        DevelopmentStep(motif_name, 'original'),
        DevelopmentStep(motif_name, 'ornament', {'density': 0.3}),
    ])


def plan_sequence_descent(motif_name: str = 'A') -> DevelopmentPlan:
    """Descending sequence — one of the most common Baroque patterns."""
    return DevelopmentPlan(steps=[
        DevelopmentStep(motif_name, 'original'),
        DevelopmentStep(motif_name, 'transpose', {'degrees': -1}),
        DevelopmentStep(motif_name, 'transpose', {'degrees': -2}),
        DevelopmentStep(motif_name, 'transpose', {'degrees': -3}),
        DevelopmentStep(motif_name, 'fragment', {'length': 2}),
        DevelopmentStep(motif_name, 'transpose', {'degrees': -4}),
        DevelopmentStep(motif_name, 'original'),
    ])


def plan_fugue_exposition(motif_name: str = 'A') -> DevelopmentPlan:
    """Simplified fugue exposition: subject, answer, development."""
    return DevelopmentPlan(steps=[
        # Subject
        DevelopmentStep(motif_name, 'original', repeat=2),
        # Answer (up a fifth = 4 scale degrees)
        DevelopmentStep(motif_name, 'transpose', {'degrees': 4}, repeat=2),
        # Episode: sequence descending
        DevelopmentStep(motif_name, 'fragment', {'length': 2}),
        DevelopmentStep(motif_name, 'transpose', {'degrees': -1}),
        DevelopmentStep(motif_name, 'transpose', {'degrees': -2}),
        # Subject returns, inverted
        DevelopmentStep(motif_name, 'invert', repeat=2),
        # Stretto: diminished subject over augmented subject (stacked in the voice)
        DevelopmentStep(motif_name, 'diminish', {'factor': 2}, repeat=2),
        # Final statement
        DevelopmentStep(motif_name, 'original'),
        DevelopmentStep(motif_name, 'augment', {'factor': 2}),
    ])


def plan_gradual_evolution(motif_name: str = 'A') -> DevelopmentPlan:
    """Start simple, gradually add complexity. Good for ambient development."""
    return DevelopmentPlan(steps=[
        DevelopmentStep(motif_name, 'original', repeat=3),
        DevelopmentStep(motif_name, 'transpose', {'degrees': 2}),
        DevelopmentStep(motif_name, 'original', repeat=2),
        DevelopmentStep(motif_name, 'ornament', {'density': 0.2}),
        DevelopmentStep(motif_name, 'transpose', {'degrees': -1}),
        DevelopmentStep(motif_name, 'ornament', {'density': 0.3}),
        DevelopmentStep(motif_name, 'invert'),
        DevelopmentStep(motif_name, 'transpose', {'degrees': 4}),
        DevelopmentStep(motif_name, 'fragment', {'length': 3}),
        DevelopmentStep(motif_name, 'transpose', {'degrees': -2}),
        DevelopmentStep(motif_name, 'original', repeat=2),
        DevelopmentStep(motif_name, 'augment', {'factor': 2}),
    ])


PLANS = {
    'aba':                plan_aba,
    'sequence_descent':   plan_sequence_descent,
    'fugue_exposition':   plan_fugue_exposition,
    'gradual_evolution':  plan_gradual_evolution,
}
