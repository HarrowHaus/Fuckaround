"""Score -> per-instrument MIDI files for the renderers.

Beats map to ticks linearly (quarter note = 480 ticks); the tempo map is
embedded as set_tempo events so DrumGizmo/sfizz place events identically.
"""

import mido
from mido import MidiFile, MidiTrack, Message, MetaMessage

TPB = 480


def _tempo_events(score):
    evs = []
    for span in score.tempo_map:
        evs.append((span.start_beat * TPB, "tempo", int(60_000_000 / span.bpm)))
    return evs


def write_track_midi(score, track, path, pitch_of=None, vel_of=None,
                     chan=0, extra_notes=None, absolute_seconds=False,
                     bends=None):
    """Write one Track to a single-track MIDI file.

    pitch_of/vel_of: optional callables (note) -> int for remapping
    (drum name -> note number, keyswitch injection, etc.).
    extra_notes: additional (start_beat, dur, pitch, vel) tuples to merge
    (used for keyswitches).
    absolute_seconds: DrumGizmo's midifile engine plays files at exactly half
    the spec tempo (calibrated empirically: 60 bpm renders 2.00 s/beat,
    120 bpm renders 1.00 s/beat). So for DrumGizmo we bake the tempo map in
    as tick = seconds * TPB and declare 120 bpm, which renders 1 written
    second per real second.
    """
    if absolute_seconds:
        def t2t(beat):
            return score.beats_to_seconds(beat) * TPB
    else:
        def t2t(beat):
            return beat * TPB
    events = []  # (tick, order, msg)
    if absolute_seconds:
        events.append((0, 0, MetaMessage("set_tempo", tempo=500_000, time=0)))
    else:
        for tick, kind, val in _tempo_events(score):
            events.append((tick, 0, MetaMessage("set_tempo", tempo=val, time=0)))
    notes = list(track.notes)
    for n in notes:
        pitch = pitch_of(n) if pitch_of else n.pitch
        if pitch is None:
            continue
        vel = vel_of(n) if vel_of else n.vel
        on_t = max(0, int(round(t2t(n.start))))
        off_t = max(on_t + 8, int(round(t2t(n.start + n.dur))))
        events.append((on_t, 2, Message("note_on", note=pitch, velocity=vel,
                                        channel=chan, time=0)))
        events.append((off_t, 1, Message("note_off", note=pitch, velocity=0,
                                         channel=chan, time=0)))
    # pitch-wheel ramps: (start_beat, dur_beats, target_value); ramp over the
    # first 85% of the note, then snap back to center after it ends
    for (s, d, target) in (bends or []):
        steps = 28
        for k in range(steps + 1):
            frac = k / steps
            t = s + d * 0.85 * frac
            val = int(target * (frac ** 1.5))       # accelerating fall
            events.append((int(round(t2t(t))), 1,
                           Message("pitchwheel", pitch=max(-8192, min(8191, val)),
                                   channel=chan, time=0)))
        events.append((int(round(t2t(s + d + 0.05))), 1,
                       Message("pitchwheel", pitch=0, channel=chan, time=0)))
    for (s, d, p, v) in (extra_notes or []):
        on_t = max(0, int(round(t2t(s))))
        off_t = max(on_t + 8, int(round(t2t(s + d))))
        events.append((on_t, 2, Message("note_on", note=p, velocity=v,
                                        channel=chan, time=0)))
        events.append((off_t, 1, Message("note_off", note=p, velocity=0,
                                         channel=chan, time=0)))
    events.sort(key=lambda e: (e[0], e[1]))

    mid = MidiFile(ticks_per_beat=TPB)
    tr = MidiTrack()
    mid.tracks.append(tr)
    last = 0
    for tick, _, msg in events:
        msg.time = int(tick - last)
        tr.append(msg)
        last = tick
    tr.append(MetaMessage("end_of_track", time=TPB * 8))  # tail for ring-out
    mid.save(path)
    return path
