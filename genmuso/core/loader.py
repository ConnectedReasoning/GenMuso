"""
loader.py — Load compositions from JSON files.

This lets you define pieces as pure data without touching Python.
Drop a .json file in the compositions/ folder and run it:

    python main.py compositions/my_piece.json
"""

import json
import os
from composition import Composition, Section, VoiceConfig


def load_json(path: str) -> Composition:
    """
    Read a JSON file and return a Composition.

    Expected format:
    {
        "name": "My Piece",
        "ticks_per_beat": 480,
        "sections": [
            {
                "key": "D",
                "mode": "dorian",
                "bars": 16,
                "tempo": 90,
                "meter": "4/4",
                "swing": 0.0,
                "voices": [
                    {
                        "name": "melody",
                        "behavior": "random_walk",
                        "channel": 0,
                        "program": 73,
                        "low": 60,
                        "high": 84,
                        "density": 0.25,
                        "velocity_range": [55, 85],
                        "note_lengths": [2, 3, 4, 6],
                        "note_length_weights": [0.2, 0.4, 0.25, 0.15],
                        "phrase_length": 4,
                        "params": {"leap_probability": 0.08}
                    }
                ]
            }
        ]
    }
    """
    with open(path, 'r') as f:
        data = json.load(f)

    sections = []
    for s in data['sections']:
        voices = []
        for v in s.get('voices', []):
            voices.append(VoiceConfig(
                name=v['name'],
                behavior=v['behavior'],
                channel=v.get('channel', 0),
                program=v.get('program', 0),
                low=v.get('low', 48),
                high=v.get('high', 72),
                density=v.get('density', 0.3),
                velocity_range=tuple(v.get('velocity_range', [60, 100])),
                note_lengths=v.get('note_lengths', [1, 2, 3, 4]),
                note_length_weights=v.get('note_length_weights', [0.2, 0.4, 0.25, 0.15]),
                phrase_length=v.get('phrase_length', 4),
                params=v.get('params', {}),
            ))

        sections.append(Section(
            key=s['key'],
            mode=s['mode'],
            bars=s.get('bars', 8),
            tempo=s.get('tempo', 72),
            meter=s.get('meter', '4/4'),
            swing=s.get('swing', 0.0),
            voices=voices,
        ))

    return Composition(
        name=data.get('name', os.path.splitext(os.path.basename(path))[0]),
        sections=sections,
        ticks_per_beat=data.get('ticks_per_beat', 480),
        arc=data.get('arc', 'gradual_build'),
        breathing=data.get('breathing', 'swell'),
    )
