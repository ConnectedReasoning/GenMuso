# GenMuso2 — Generative Music Engine

A declarative generative music system that produces long-form MIDI compositions. Define a harmonic plan and voice behaviors; the engine handles the rest.

## Quick Start

```bash
pip install mido numpy
python main.py focus        # 15 min focus music for work
python main.py drive        # 7 min driving music
python main.py garden       # 9 min pastoral music
python main.py altairean    # 10 min Arabic double harmonic meditation
python main.py passion      # 49 min — Bach St. Matthew Passion key sequence
```

Add `--seed 42` for reproducible output. Add `--list` to see all presets.

## How It Works

A **Composition** is a sequence of **Sections**, each with a key, mode, tempo, and set of **Voices**. Each voice has a **behavior** that determines how it moves through pitch and time:

- **random_walk** — stepwise motion with occasional leaps (melodic lines)
- **random_select** — random notes from the scale (textural middle voices)
- **drone** — sustained tones for harmonic anchoring
- **arpeggio** — cycle through scale-derived chord tones
- **ostinato** — short repeating pattern with subtle variation (rhythmic backbone)

Notes are placed on a **rhythmic grid** where each 16th-note position has a metric weight. Strong beats (downbeats) are more likely to receive notes; weak subdivisions only fill in at higher densities. This gives pulse without rigidity.

## Architecture

```
scales.py        Music theory: modes, scale construction, chord tones
rhythm.py        Metrical grid, beat weights, swing, phrase structure
voices.py        Voice behaviors (the creative core)
composition.py   Data model: Composition → Section → VoiceConfig
generator.py     Orchestrator: plan → notes → MIDI
presets.py       Ready-made compositional plans
main.py          CLI entry point
```

A new piece is just a new data structure in presets.py — no new code needed.

## Creating Your Own Compositions

```python
from composition import Composition, Section, VoiceConfig
from generator import generate

comp = Composition(name='MyPiece', sections=[
    Section(key='D', mode='dorian', bars=16, tempo=90, voices=[
        VoiceConfig(name='melody', behavior='random_walk', 
                    low=60, high=84, density=0.3, channel=0, program=73),
        VoiceConfig(name='bass', behavior='ostinato',
                    low=36, high=55, density=0.4, channel=1, program=33,
                    params={'pattern_bars': 2, 'note_length': 2}),
        VoiceConfig(name='pad', behavior='drone',
                    low=48, high=60, channel=2, program=52),
    ]),
])

generate(comp, output_path='my_piece.mid')
```

## Lineage

GenMuso2 inherits its creative DNA from GenMuso (2024), which generated a 46-movement piece by mapping the key sequence of Bach's St. Matthew Passion onto algorithmic voices. The ideas — harmonic blueprints from existing works, drone as connective tissue, random walk as melodic behavior — originate there. GenMuso2 adds rhythmic structure, proper architecture, and an extensible composition format.
