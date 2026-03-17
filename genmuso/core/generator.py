"""
generator.py — Turn a Composition into a MIDI file.

This is the orchestrator.  It walks through each section of the
composition, builds the rhythmic grid, resolves scales, dispatches
to voice behaviors, handles section offsets, and exports to MIDI.
"""

import os
import datetime
import numpy as np
import mido

from composition import Composition, Section, VoiceConfig
from scales import build_scale, root_note_in_range, NOTE_NAMES
from rhythm import build_grid, apply_swing, section_duration_ticks
from voices import Note, BEHAVIORS
from humanize import humanize, get_profile


def generate(comp: Composition, output_path: str = None,
             seed: int = None) -> str:
    """
    Generate a MIDI file from a Composition.

    Returns the path to the saved .mid file.
    """
    if seed is not None:
        np.random.seed(seed)

    tpb = comp.ticks_per_beat
    ticks_per_16th = tpb // 4

    # Collect notes per voice (keyed by voice name)
    voice_notes: dict[str, list[Note]] = {}
    voice_programs: dict[str, int] = {}
    voice_channels: dict[str, int] = {}
    tempo_map: list[tuple[int, int]] = []   # (tick, bpm)

    cumulative_tick = 0

    for section_idx, section in enumerate(comp.sections):
        # Build grid for this section
        grid = build_grid(section.bars, section.meter, tpb)
        if section.swing > 0:
            grid = apply_swing(grid, section.swing, tpb)

        sec_ticks = section_duration_ticks(section.bars, section.meter, tpb)

        # Record tempo change
        tempo_map.append((cumulative_tick, section.tempo))

        # Compute intensity for this section
        from dynamics import compute_section_intensity, intensity_to_modifiers
        intensity = compute_section_intensity(
            section_idx, len(comp.sections), comp.arc)
        mods = intensity_to_modifiers(intensity)

        # Generate each voice
        for vc in section.voices:
            # Resolve scale for this voice's range
            scale = build_scale(section.root_pc, section.mode, vc.low, vc.high)

            # Apply intensity modifiers to voice parameters
            adjusted_density = np.clip(vc.density * mods.density_mult, 0.02, 0.95)
            adjusted_vel_lo = int(np.clip(vc.velocity_range[0] + mods.velocity_offset, 1, 120))
            adjusted_vel_hi = int(np.clip(vc.velocity_range[1] + mods.velocity_offset, adjusted_vel_lo + 5, 127))

            # Prepare common kwargs
            common = dict(
                density=adjusted_density,
                velocity_range=(adjusted_vel_lo, adjusted_vel_hi),
                channel=vc.channel,
                ticks_per_16th=ticks_per_16th,
                phrase_length=vc.phrase_length,
                total_bars=section.bars,
            )

            # Dispatch to behavior
            behavior_fn = BEHAVIORS.get(vc.behavior)
            if behavior_fn is None:
                print(f"  Warning: unknown behavior '{vc.behavior}', skipping")
                continue

            if vc.behavior == 'drone':
                # Drone needs different args: sustained root (+ fifth)
                root = root_note_in_range(section.root_pc, vc.low, vc.high)
                drone_notes = [root]
                # Optionally add fifth
                if vc.params.get('include_fifth', False):
                    fifth = root + 7
                    if fifth <= vc.high:
                        drone_notes.append(fifth)
                # Add any explicit notes from params
                if 'notes' in vc.params:
                    drone_notes = vc.params['notes']

                notes = behavior_fn(
                    total_ticks=sec_ticks,
                    drone_notes=drone_notes,
                    velocity=vc.velocity_range[0],
                    channel=vc.channel,
                )

            elif vc.behavior == 'arpeggio':
                notes = behavior_fn(
                    grid=grid,
                    scale=scale,
                    root_pc=section.root_pc,
                    mode=section.mode,
                    low=vc.low,
                    high=vc.high,
                    **common,
                    **vc.params,
                )

            elif vc.behavior == 'bass':
                notes = behavior_fn(
                    grid=grid,
                    scale=scale,
                    root_pc=section.root_pc,
                    mode=section.mode,
                    low=vc.low,
                    high=vc.high,
                    **common,
                    **vc.params,
                )

            else:
                # random_walk, random_select, ostinato
                notes = behavior_fn(
                    grid=grid,
                    scale=scale,
                    note_lengths=vc.note_lengths,
                    note_length_weights=vc.note_length_weights,
                    **common,
                    **vc.params,
                )

            # Offset notes by cumulative section position
            for note in notes:
                note.start_tick += cumulative_tick

            # Accumulate
            if vc.name not in voice_notes:
                voice_notes[vc.name] = []
                voice_programs[vc.name] = vc.program
                voice_channels[vc.name] = vc.channel
            voice_notes[vc.name].extend(notes)

        cumulative_tick += sec_ticks

    # ── Humanize ─────────────────────────────────────────────────────
    # Apply per-voice humanization to smooth out the machine precision.
    # Each voice can specify a profile in params['humanize']:
    #   'natural', 'subtle', 'tight', 'expressive', 'legato', 'none'
    # Or provide individual values like params['legato'] = 0.4
    for voice_name, notes in voice_notes.items():
        if not notes:
            continue

        # Find the humanize settings for this voice from its config
        h_params = _resolve_humanize(comp, voice_name)
        humanize(notes, ticks_per_16th=ticks_per_16th, **h_params)

    # ── Export to MIDI ───────────────────────────────────────────────
    mid = mido.MidiFile(ticks_per_beat=tpb)

    # Track 0: tempo map
    tempo_track = mido.MidiTrack()
    tempo_track.name = 'tempo'
    prev_tick = 0
    for tick, bpm in tempo_map:
        delta = tick - prev_tick
        tempo_track.append(mido.MetaMessage(
            'set_tempo', tempo=mido.bpm2tempo(bpm), time=delta))
        prev_tick = tick
    mid.tracks.append(tempo_track)

    # One track per voice
    for voice_name, notes in voice_notes.items():
        track = _notes_to_track(
            notes,
            name=voice_name,
            program=voice_programs[voice_name],
            channel=voice_channels[voice_name],
        )
        mid.tracks.append(track)

    # Save
    if output_path is None:
        now = datetime.datetime.now()
        safe_name = comp.name.replace(' ', '_').replace('/', '-')
        output_path = (f"{safe_name}_{now.year}_{now.month:02d}_{now.day:02d}"
                       f"_{now.hour:02d}{now.minute:02d}{now.second:02d}.mid")

    os.makedirs(os.path.dirname(output_path) or '.', exist_ok=True)
    mid.save(output_path)

    # Summary
    total_notes = sum(len(n) for n in voice_notes.values())
    total_seconds = _ticks_to_seconds(cumulative_tick, tempo_map, tpb)
    minutes = int(total_seconds // 60)
    seconds = int(total_seconds % 60)

    print(f"\n  Generated: {output_path}")
    print(f"  Duration:  {minutes}:{seconds:02d}")
    print(f"  Sections:  {len(comp.sections)}")
    print(f"  Voices:    {', '.join(voice_notes.keys())}")
    print(f"  Notes:     {total_notes}")

    return output_path


def _notes_to_track(notes: list[Note], name: str = '',
                    program: int = 0, channel: int = 0) -> mido.MidiTrack:
    """Convert a list of Note objects to a mido MidiTrack."""
    track = mido.MidiTrack()
    track.name = name
    track.append(mido.Message(
        'program_change', program=program, channel=channel, time=0))

    # Build event list: (tick, type, pitch, velocity, channel)
    events = []
    for note in notes:
        events.append((note.start_tick, 'note_on', note.pitch,
                        note.velocity, note.channel))
        events.append((note.start_tick + note.duration_ticks, 'note_off',
                        note.pitch, 0, note.channel))

    # Sort by time, with note_off before note_on at same tick
    events.sort(key=lambda e: (e[0], 0 if e[1] == 'note_off' else 1))

    # Convert to delta times
    current_tick = 0
    for tick, msg_type, pitch, velocity, ch in events:
        delta = max(0, tick - current_tick)
        track.append(mido.Message(
            msg_type, note=pitch, velocity=velocity,
            time=delta, channel=ch))
        current_tick = tick

    return track


def _ticks_to_seconds(total_ticks: int, tempo_map: list[tuple[int, int]],
                      tpb: int) -> float:
    """Approximate duration in seconds from tempo map."""
    if not tempo_map:
        return 0.0

    seconds = 0.0
    for i, (tick, bpm) in enumerate(tempo_map):
        next_tick = tempo_map[i + 1][0] if i + 1 < len(tempo_map) else total_ticks
        section_ticks = next_tick - tick
        seconds += section_ticks * (60.0 / bpm / tpb)

    return seconds


def _resolve_humanize(comp: Composition, voice_name: str) -> dict:
    """
    Figure out the humanization settings for a voice.

    Priority:
      1. Explicit params like legato=0.4 in the voice's params dict
      2. A named profile like humanize='expressive' in params
      3. Default: 'natural' profile

    This scans all sections for the first occurrence of the voice
    and reads its params.
    """
    for section in comp.sections:
        for vc in section.voices:
            if vc.name == voice_name:
                # Check for a named profile
                profile_name = vc.params.get('humanize', 'natural')
                profile = get_profile(profile_name)

                # Override with any explicit values
                for key in ('legato', 'timing_feel', 'velocity_smooth',
                            'duration_vary'):
                    if key in vc.params:
                        profile[key] = vc.params[key]

                return profile

    return get_profile('natural')
