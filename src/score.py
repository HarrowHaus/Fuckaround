"""Score model for the deathcore production pipeline.

Everything is composed against an abstract timeline in beats (quarter notes).
A tempo map converts beats -> seconds at render time. Notes carry articulation
tags ("pm" palm mute, "trem", "sus", "choke", ...) that the MIDI writers map to
each renderer's conventions (SFZ keyswitches, DrumGizmo note numbers, synth
patches).
"""

from dataclasses import dataclass, field
import random

random.seed(0xDEC0DE)  # deterministic renders


@dataclass
class Note:
    start: float          # beats from song start
    dur: float            # beats
    pitch: int            # MIDI note number
    vel: int              # 1..127
    tags: frozenset = frozenset()

    def tagged(self, *tags):
        return Note(self.start, self.dur, self.pitch, self.vel,
                    self.tags | frozenset(tags))


@dataclass
class Track:
    name: str
    notes: list = field(default_factory=list)

    def add(self, start, dur, pitch, vel, *tags):
        self.notes.append(Note(start, dur, pitch, vel, frozenset(tags)))

    def extend(self, notes):
        self.notes.extend(notes)

    def end(self):
        return max((n.start + n.dur for n in self.notes), default=0.0)


@dataclass
class TempoSpan:
    start_beat: float
    bpm: float


class Score:
    def __init__(self):
        self.tracks = {}
        self.tempo_map = [TempoSpan(0.0, 120.0)]

    def track(self, name):
        if name not in self.tracks:
            self.tracks[name] = Track(name)
        return self.tracks[name]

    def set_tempo(self, start_beat, bpm):
        self.tempo_map.append(TempoSpan(start_beat, bpm))
        self.tempo_map.sort(key=lambda t: t.start_beat)

    def beats_to_seconds(self, beat):
        """Convert a beat position to absolute seconds through the tempo map."""
        t = 0.0
        spans = self.tempo_map
        for i, span in enumerate(spans):
            nxt = spans[i + 1].start_beat if i + 1 < len(spans) else None
            if nxt is not None and beat >= nxt:
                t += (nxt - span.start_beat) * 60.0 / span.bpm
            else:
                t += (beat - span.start_beat) * 60.0 / span.bpm
                return t
        return t

    def end_beat(self):
        return max((tr.end() for tr in self.tracks.values()), default=0.0)


# ---------------------------------------------------------------- humanization

def humanize(notes, vel_jitter=6, time_jitter_beats=0.006, keep_grid=()):
    """Research numbers: velocity +/-5-10, timing +/-1-3 ms (~0.004-0.01 beats
    at 130bpm), ~90% quantize. Notes whose tags intersect keep_grid stay
    time-locked (e.g. breakdown kicks locking to guitar chugs)."""
    out = []
    for n in notes:
        vj = random.randint(-vel_jitter, vel_jitter)
        tj = 0.0
        if not (n.tags & frozenset(keep_grid)):
            tj = random.uniform(-time_jitter_beats, time_jitter_beats)
        out.append(Note(max(0.0, n.start + tj), n.dur, n.pitch,
                        max(1, min(127, n.vel + vj)), n.tags))
    return out


def vel_ladder(base, i, spread=(0, -5, -2, -7)):
    """Repeating velocity ladder (112,107,110,105-style) for fast doubles."""
    return max(1, min(127, base + spread[i % len(spread)]))
