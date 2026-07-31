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
                     chan=0, extra_notes=None):
    """Write one Track to a single-track MIDI file.

    pitch_of/vel_of: optional callables (note) -> int for remapping
    (drum name -> note number, keyswitch injection, etc.).
    extra_notes: additional (start_beat, dur, pitch, vel) tuples to merge
    (used for keyswitches).
    """
    events = []  # (tick, order, msg)
    for tick, kind, val in _tempo_events(score):
        events.append((tick, 0, MetaMessage("set_tempo", tempo=val, time=0)))
    notes = list(track.notes)
    for n in notes:
        pitch = pitch_of(n) if pitch_of else n.pitch
        if pitch is None:
            continue
        vel = vel_of(n) if vel_of else n.vel
        on_t = max(0, int(round(n.start * TPB)))
        off_t = max(on_t + 8, int(round((n.start + n.dur) * TPB)))
        events.append((on_t, 2, Message("note_on", note=pitch, velocity=vel,
                                        channel=chan, time=0)))
        events.append((off_t, 1, Message("note_off", note=pitch, velocity=0,
                                         channel=chan, time=0)))
    for (s, d, p, v) in (extra_notes or []):
        on_t = max(0, int(round(s * TPB)))
        off_t = max(on_t + 8, int(round((s + d) * TPB)))
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
