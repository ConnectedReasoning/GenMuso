# GenMuso2 — Parameter Reference

## The Three Levels

Everything in GenMuso2 is controlled at three levels:

1. **Composition** — the whole piece (name, number of sections)
2. **Section** — one segment (key, mode, tempo, meter, length)
3. **Voice** — one instrument within a section (behavior, range, density, note lengths)

---

## Section Parameters

These control the harmonic and temporal feel of each segment.

### key
The root note. Determines what scale gets built.

Values: `C`, `C#`, `Db`, `D`, `D#`, `Eb`, `E`, `F`, `F#`, `Gb`, `G`, `G#`, `Ab`, `A`, `A#`, `Bb`, `B`

```python
Section(key='D', ...)    # D is the root
Section(key='Bb', ...)   # B-flat is the root
```

### mode
The scale type. Combined with key, this determines every note available to voices.

| Mode | Intervals | Feel |
|------|-----------|------|
| `major` | 0 2 4 5 7 9 11 | bright, resolved |
| `minor` | 0 2 3 5 7 8 10 | dark, emotional |
| `dorian` | 0 2 3 5 7 9 10 | minor but warm, jazzy |
| `phrygian` | 0 1 3 5 7 8 10 | Spanish, dark |
| `lydian` | 0 2 4 6 7 9 11 | bright, dreamy, floating |
| `mixolydian` | 0 2 4 5 7 9 10 | bluesy major, rock |
| `aeolian` | 0 2 3 5 7 8 10 | natural minor |
| `locrian` | 0 1 3 5 6 8 10 | unstable, tense |
| `pentatonic_major` | 0 2 4 7 9 | simple, open, safe |
| `pentatonic_minor` | 0 3 5 7 10 | bluesy, ambient |
| `harmonic_minor` | 0 2 3 5 7 8 11 | classical, dramatic |
| `melodic_minor` | 0 2 3 5 7 9 11 | jazz minor |
| `arabic_double_harmonic` | 0 1 4 5 7 8 11 | Middle Eastern, exotic |
| `whole_tone` | 0 2 4 6 8 10 | dreamlike, ambiguous |
| `blues` | 0 3 5 6 7 10 | blues |
| `japanese` | 0 1 5 7 8 | sparse, Eastern |
| `hungarian_minor` | 0 2 3 6 7 8 11 | dramatic, Eastern European |

```python
Section(key='D', mode='dorian', ...)      # D Dorian
Section(key='G', mode='arabic_double_harmonic', ...)  # the Altairean sound
Section(key='A', mode='pentatonic_minor', ...)  # calm, ambient
```

### tempo
Beats per minute. Controls the speed of everything.

| Range | Feel |
|-------|------|
| 50–65 | very slow, meditative, ambient |
| 66–80 | slow, calm, focus music |
| 81–100 | moderate, walking pace |
| 101–120 | energetic, driving |
| 121–140 | fast, intense |

```python
Section(tempo=64, ...)   # meditative
Section(tempo=108, ...)  # driving
```

### bars
How many bars this section lasts. Combined with tempo and meter, determines duration in seconds.

Rough duration formula for 4/4:
- `bars × 4 beats ÷ tempo × 60 = seconds`
- 16 bars at 60 BPM = 64 seconds (~1 minute)
- 32 bars at 68 BPM = ~113 seconds (~2 minutes)
- 24 bars at 76 BPM = ~76 seconds (~1.3 minutes)

```python
Section(bars=16, ...)   # shorter section
Section(bars=32, ...)   # longer section
```

### meter
Time signature. Determines the rhythmic grid and which beats are strong/weak.

| Meter | Beats per bar | Slots per bar | Feel |
|-------|---------------|---------------|------|
| `4/4` | 4 | 16 | standard, steady |
| `3/4` | 3 | 12 | waltz, flowing |
| `6/8` | 2 (dotted) | 12 | rolling, compound |
| `5/4` | 5 | 20 | odd, progressive |
| `7/8` | uneven | 16 | asymmetric, driving |

```python
Section(meter='3/4', ...)   # waltz feel (used in Garden preset)
Section(meter='7/8', ...)   # asymmetric groove
```

### swing
How much to delay upbeats. 0.0 = perfectly straight, 1.0 = full triplet swing.

| Value | Feel |
|-------|------|
| 0.0 | straight, mechanical |
| 0.1–0.2 | subtle lilt |
| 0.3–0.5 | moderate swing |
| 0.6–0.8 | heavy swing |
| 1.0 | full triplet (jazz) |

```python
Section(swing=0.15, ...)  # subtle swing (used in Drive preset)
Section(swing=0.0, ...)   # perfectly straight
```

---

## Voice Parameters

Each section has a list of voices. Each voice is a `VoiceConfig`.

### name
Just a label. Becomes the MIDI track name in your DAW.
```python
VoiceConfig(name='melody', ...)
VoiceConfig(name='bass', ...)
```

### behavior
How this voice chooses notes. This is the most important creative decision.

| Behavior | What it does | Best for |
|----------|-------------|----------|
| `random_walk` | Steps ±1–2 scale degrees with occasional leaps | melody, tenor, bass lines |
| `random_select` | Picks notes at random from the scale | texture, pad-like middle voices |
| `drone` | Holds notes for the entire section | harmonic anchor, pads |
| `arpeggio` | Cycles through chord tones (triad from the scale) | rhythmic movement, accompaniment |
| `ostinato` | Short repeating pattern with subtle variation | rhythmic backbone, bass riffs |

```python
VoiceConfig(behavior='random_walk', ...)
VoiceConfig(behavior='ostinato', ...)
```

### channel
MIDI channel (0–15). Each voice should have a unique channel so your DAW separates them onto different tracks.

Channel 9 is reserved for drums in General MIDI (not currently used but worth avoiding).

```python
VoiceConfig(channel=0, ...)  # first instrument
VoiceConfig(channel=1, ...)  # second instrument
```

### program
General MIDI program number. This is the default sound — you'll override it in Logic, but it gives a starting point.

Some useful GM programs:
| Number | Sound |
|--------|-------|
| 0 | Acoustic Grand Piano |
| 4 | Electric Piano |
| 33 | Electric Bass (finger) |
| 46 | Orchestral Harp |
| 48 | String Ensemble |
| 52 | Choir Aahs |
| 71 | Clarinet |
| 73 | Flute |
| 81 | Lead Synth (square) |
| 89 | Pad (warm) |

### low / high
MIDI note range for this voice. Controls the register.

| MIDI | Note | Register |
|------|------|----------|
| 24 | C1 | very low bass |
| 36 | C2 | bass |
| 48 | C3 | low tenor |
| 60 | C4 | middle C |
| 72 | C5 | soprano |
| 84 | C6 | high soprano |
| 96 | C7 | very high |

```python
VoiceConfig(low=24, high=48, ...)   # bass register
VoiceConfig(low=60, high=84, ...)   # mid-to-high register
VoiceConfig(low=72, high=96, ...)   # soprano register
```

### density
Probability scaling (0.0–1.0). How likely a note is placed at each grid position. The actual probability is `density × beat_weight × phrase_weight`, so even high density won't fill every slot — strong beats are still favored.

| Value | Result |
|-------|--------|
| 0.05–0.12 | very sparse, occasional notes |
| 0.15–0.25 | moderate, breathing room (good for melody) |
| 0.30–0.45 | active, rhythmic (good for ostinato, arpeggio) |
| 0.50–0.70 | dense, busy |
| 0.80+ | very dense, almost every strong beat |

```python
VoiceConfig(density=0.15, ...)   # sparse background
VoiceConfig(density=0.45, ...)   # active rhythm
```

### velocity_range
Tuple of (min, max) MIDI velocity. Controls dynamics.

| Range | Feel |
|-------|------|
| (30, 50) | very quiet, whisper |
| (40, 65) | soft, background |
| (55, 85) | moderate |
| (65, 100) | present, confident |
| (90, 120) | loud, assertive |

Strong beats automatically get a +10 velocity accent on top of this range.

```python
VoiceConfig(velocity_range=(40, 65), ...)   # soft
VoiceConfig(velocity_range=(65, 100), ...)  # confident
```

### note_lengths / note_length_weights
How long notes last, measured in 16th notes. The weights control probability.

| 16th notes | At 60 BPM | At 120 BPM | Musical value |
|------------|-----------|------------|---------------|
| 1 | 0.25s | 0.125s | sixteenth note |
| 2 | 0.5s | 0.25s | eighth note |
| 3 | 0.75s | 0.375s | dotted eighth |
| 4 | 1.0s | 0.5s | quarter note |
| 6 | 1.5s | 0.75s | dotted quarter |
| 8 | 2.0s | 1.0s | half note |
| 12 | 3.0s | 1.5s | dotted half |
| 16 | 4.0s | 2.0s | whole note |

```python
# Short, rhythmic notes
VoiceConfig(note_lengths=[1, 2, 3, 4], note_length_weights=[0.25, 0.35, 0.25, 0.15], ...)

# Long, sustained notes
VoiceConfig(note_lengths=[4, 6, 8, 12], note_length_weights=[0.1, 0.3, 0.35, 0.25], ...)

# Mix of short and long
VoiceConfig(note_lengths=[2, 4, 8], note_length_weights=[0.3, 0.4, 0.3], ...)
```

### phrase_length
Bars per phrase. Affects density: first bar of a phrase is stronger, last bar thins out.

```python
VoiceConfig(phrase_length=4, ...)   # standard 4-bar phrases
VoiceConfig(phrase_length=8, ...)   # longer, more gradual breathing
```

---

## Behavior-Specific Parameters (via params dict)

### random_walk params
| Param | Default | What it does |
|-------|---------|-------------|
| `leap_probability` | 0.08 | Chance of a ±3–5 degree jump instead of ±1–2 step |

```python
VoiceConfig(behavior='random_walk', params={'leap_probability': 0.15}, ...)  # more leaps
```

### drone params
| Param | Default | What it does |
|-------|---------|-------------|
| `include_fifth` | False | Add the fifth above the root |
| `notes` | (auto) | Explicit list of MIDI notes to sustain |

```python
VoiceConfig(behavior='drone', params={'include_fifth': True}, ...)
VoiceConfig(behavior='drone', params={'notes': [48, 55, 60]}, ...)  # specific chord
```

### arpeggio params
| Param | Default | What it does |
|-------|---------|-------------|
| `pattern` | 'up' | Direction: `up`, `down`, `up_down`, `random` |
| `note_length` | 2 | Duration of each arp note in 16ths |
| `degree` | 1 | Scale degree for the chord (1=root triad, 4=IV chord, 5=V chord) |

```python
VoiceConfig(behavior='arpeggio', params={'pattern': 'up_down', 'note_length': 2, 'degree': 1}, ...)
```

### ostinato params
| Param | Default | What it does |
|-------|---------|-------------|
| `note_length` | 2 | Duration of each note in the pattern |
| `pattern_bars` | 1 | How many bars the repeating pattern spans |
| `variation` | 0.08 | Chance of micro-changes per repetition (0 = exact loop) |

```python
VoiceConfig(behavior='ostinato', params={'pattern_bars': 2, 'note_length': 2, 'variation': 0.06}, ...)
```

---

## Putting It Together — Example

```python
from composition import Composition, Section, VoiceConfig
from generator import generate

comp = Composition(name='MidnightStudy', sections=[
    # Section 1: calm D minor
    Section(key='D', mode='minor', bars=32, tempo=68, meter='4/4', voices=[
        VoiceConfig(
            name='melody', behavior='random_walk', channel=0, program=73,
            low=60, high=84, density=0.18, velocity_range=(45, 70),
            note_lengths=[4, 6, 8, 12], note_length_weights=[0.1, 0.3, 0.35, 0.25],
            params={'leap_probability': 0.06},
        ),
        VoiceConfig(
            name='bass_pulse', behavior='ostinato', channel=1, program=33,
            low=36, high=55, density=0.4, velocity_range=(55, 75),
            params={'pattern_bars': 2, 'note_length': 3, 'variation': 0.05},
        ),
        VoiceConfig(
            name='pad', behavior='drone', channel=2, program=52,
            low=48, high=60, velocity_range=(40, 40),
            params={'include_fifth': True},
        ),
    ]),

    # Section 2: shift to F major — brighter, slightly more active
    Section(key='F', mode='major', bars=32, tempo=72, meter='4/4', voices=[
        VoiceConfig(
            name='melody', behavior='random_walk', channel=0, program=73,
            low=60, high=84, density=0.22, velocity_range=(50, 75),
            note_lengths=[3, 4, 6, 8], note_length_weights=[0.15, 0.3, 0.35, 0.2],
            params={'leap_probability': 0.08},
        ),
        VoiceConfig(
            name='bass_pulse', behavior='ostinato', channel=1, program=33,
            low=36, high=55, density=0.4, velocity_range=(55, 75),
            params={'pattern_bars': 2, 'note_length': 2, 'variation': 0.08},
        ),
        VoiceConfig(
            name='arp', behavior='arpeggio', channel=3, program=46,
            low=48, high=72, density=0.3, velocity_range=(40, 60),
            params={'pattern': 'up', 'note_length': 2},
        ),
        VoiceConfig(
            name='pad', behavior='drone', channel=2, program=52,
            low=48, high=60, velocity_range=(40, 40),
            params={'include_fifth': True},
        ),
    ]),
])

generate(comp, output_path='midnight_study.mid', seed=42)
```
