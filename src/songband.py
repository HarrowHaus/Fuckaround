"""The band's song: plays whatever is in jam/songdoc.json.

This is the shared rehearsal room. Band-member agents (guitarist, drummer,
bassist) edit the songdoc through jam rounds — proposals, critiques,
revisions — and this player turns the current state into a full render at
any moment (the 'playthrough' for the singer).

songdoc schema (per section):
  name, bars, bpm
  riff:  {mask: 16-char 'X./' grid, frets: {slot: fret}, detune, ring}
         riff_burst: bool — each onset gets a fast 2-note chromatic
         approach run before it lands (both rhythm guitars, unison).
         For sparse/ultra-slow riffs: isolated hits still read as
         technical, not just slow (the 2026 dead-space-breakdown move).
  drums: {mode: 'book'|'bars', prefer_cym, kick_lo, kick_hi, union_riff,
          bars: [{kick, snare, cym, cmask}, ...]}   # bars mode = literal
  lead:  'none' | 'trem:<base_fret>' | 'octave' | 'feedback' | 'techlead'
         | 'riffsweep'
         # techlead: diminished/harmonic-minor shred line, irregular note
         # groupings per beat (polymetric against the riff), hammer-on/
         # pull-off legato + one trill/bend flourish per figure. Rooted at
         # the section's open-string pitch. Archspire-density x Black
         # Dahlia Murder-contour, never a straight up/down sweep.
         # riffsweep: a fast sweep built FROM the section's own riff — the
         # riff's onset slots/pitches become accented landmark notes at
         # their original relative positions, connected by fast diminished-
         # arpeggio fill notes (legato-tagged) so the riff is audible
         # inside the cascade. Each bar sequences up a minor third.
  lead_start_bar: int, bars into the section before the lead enters
                  (default 0). Rhythm/drums/bass play from bar 0 either way.
  bass:  'follow' | 'follow+fills'
  skronk: [bar indices], pinch: [bar indices]
  subdrop: bool, drone: bool, impact: bool, riser_in: bool
"""

import os
import json
from score import Score, Note, humanize
from riffgen import set_dialect, midi_of, panic_chord, TUNING, make_tremolo
import random

set_dialect("modern")
import riffgen2 as r2

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
r2.set_reference(os.path.join(REPO, "corpus", "refs.json"))
from drumgen import DrumBook

SONGDOC_PATH = os.environ.get("SONGDOC_PATH",
                              os.path.join(REPO, "jam", "songdoc.json"))
DOC = json.load(open(SONGDOC_PATH))

random.seed(81)
RNG = random.Random(81)

TITLE = DOC.get("slug", "band_song")
MIX_PROFILE = "modern2026"
QUAD = True
BAR = 4.0
G_LO = TUNING[0]


def bars(n):
    return n * BAR


class Player:
    def __init__(self):
        self.s = Score()
        self.s.tempo_map = []
        self.sec = {}
        pos = 0.0
        for sec in DOC["sections"]:
            self.sec[sec["name"]] = pos
            self.s.set_tempo(pos, float(sec["bpm"]))
            pos += bars(sec["bars"])
        for nm in ("gtr_l", "gtr_r", "lead", "bass", "drums", "strings",
                   "subdrop", "subbass", "fx"):
            setattr(self, nm, self.s.track(nm))
        self.book = DrumBook("refs")
        self.tabs = []
        self.roots = {}

    def drum(self, t, name, vel, dur=0.2):
        self.drums.notes.append(Note(t, dur, 0, vel,
                                     frozenset({name, "grid"})))

    def play_riff(self, sec, t0):
        r = sec.get("riff")
        if not r:
            return
        mask = r["mask"]
        frets = {int(k): v for k, v in r["frets"].items()}
        detune = r.get("detune", 0)
        ring = r.get("ring", False)
        g = r2.Genome(mask, frets)
        from riffgen2 import genome_riff
        self.tabs.append((sec["name"], sec["bpm"],
                          genome_riff(g, sec["bpm"], "sec").tab()))
        vel = r.get("vel", 110)
        burst = sec.get("riff_burst", False)
        for b in range(int(sec["bars"])):
            base = t0 + b * BAR
            slots = sorted(frets)
            if slots:
                self.roots[base] = midi_of(0, frets[slots[0]]) + detune
            for idx, i in enumerate(slots):
                t = base + i * 0.25
                nxt = slots[idx + 1] if idx + 1 < len(slots) else 16
                gap = (nxt - i) * 0.25
                dur = min(gap * (0.95 if ring else 0.85),
                          1.2 if ring else (0.4 if gap <= 0.5 else 1.5))
                pitch = midi_of(0, frets[i]) + detune
                gp = pitch if pitch >= 30 else pitch + 12
                art = "sus" if (ring or gap > 0.75) else "pm"
                if burst:
                    # isolated hit gets a fast chromatic run INTO the
                    # landing pitch — "insane speed" inside the dead
                    # space, the 2026-breakdown move (docs/18)
                    step = min(0.045, gap / 6)
                    pre = [gp - 5, gp - 2]
                    tt = t - step * len(pre)
                    for gpitch in pre:
                        for tr in (self.gtr_l, self.gtr_r):
                            tr.add(tt, step * 0.9, gpitch, vel - 12, "fast")
                        tt += step
                for tr in (self.gtr_l, self.gtr_r):
                    tr.add(t, dur, gp, vel + (5 if i == 0 else 0), art)
                if sec.get("bass", "follow").startswith("follow"):
                    self.bass.add(t, dur * 1.1, max(28, pitch - 12),
                                  vel + 8, "pm")
            if sec.get("bass") == "follow+fills" and b % 4 == 3:
                # bassist's fill: chromatic walk into the next bar
                for j, f in enumerate((3, 2, 1)):
                    self.bass.add(base + 3.0 + j * 0.25, 0.22,
                                  max(28, G_LO - 12 + f), 106, "pm")

    def play_drums(self, sec, t0):
        d = sec.get("drums", {})
        mask = sec.get("riff", {}).get("mask", "X...............")
        if d.get("mode") == "bars" and d.get("bars"):
            pats = d["bars"]
            for b in range(int(sec["bars"])):
                pat = dict(pats[b % len(pats)])
                pat.setdefault("cmask", pat.get("cym_mask", "." * 16))
                self.book.write_bar(
                    lambda t, n, v, du: self.drum(t, n, v, du),
                    t0 + b * BAR, pat, vel=d.get("vel", 118))
        else:
            b = 0
            rep = d.get("repeat_of", 2)
            while b < int(sec["bars"]):
                pat = self.book.pick(
                    RNG, "*", mask, d.get("kick_lo", 0),
                    d.get("kick_hi", 16),
                    need_snare=d.get("need_snare", True),
                    prefer_cym=d.get("prefer_cym"))[0]
                if d.get("union_riff"):
                    kick = "".join(
                        "X" if (pat["kick"][i] == "X" or mask[i] == "X")
                        else "." for i in range(16))
                    pat = dict(pat, kick=kick)
                for k in range(min(rep, int(sec["bars"]) - b)):
                    self.book.write_bar(
                        lambda t, n, v, du: self.drum(t, n, v, du),
                        t0 + (b + k) * BAR, pat, vel=d.get("vel", 118))
                b += rep
        for fill_bar in d.get("fills", []):
            base = t0 + fill_bar * BAR + 3.0
            for i, dr in enumerate(("snare", "tom2", "tom3", "tom_floor")):
                self.drum(base + i * 0.25, dr, 106 + i * 4)

    def techlead(self, sec, t0, nb):
        """Archspire-density x Black Dahlia Murder-contour lead: diminished
        and harmonic-minor figures, ORDERED NON-MONOTONICALLY (skips and
        direction changes, never a plain one-string-per-fret sweep),
        grouped in irregular note-counts per beat (5/6/7/4 cycling) so the
        line runs polymetric against the riff's on-the-grid chugs instead
        of locking to it. Small intervals get the 'fast' tag -> render.py's
        keyswitch logic reads that as a real hammer-on/pull-off, so dense
        runs come out legato (hybrid sweep-legato), not all-picked. One
        trill or bend flourish closes every other bar."""
        root = G_LO + sec.get("riff", {}).get("detune", 0) + 24
        HM = [0, 2, 3, 5, 7, 8, 11]                  # harmonic minor
        HM2 = HM + [12 + d for d in HM] + [24]
        FIGURES = [
            [0, 7, 3, 11, 7, 15, 10, 19, 15, 23],     # broken i7 arp, skips
            list(reversed(HM2))[:12],                 # HM descent w/ a turn
            [0, 9, 3, 12, 6, 15, 9, 18, 12, 21],       # symmetric dim leaps
            [7, 10, 7, 3, 0, -2, 0, 3, 7],             # melodic hook, held
        ]
        GROUPS = [5, 6, 7, 4]
        prev_pitch = None
        for bar in range(nb):
            fig = FIGURES[bar % len(FIGURES)]
            base = t0 + bar * BAR
            t = base
            note_i = 0
            for beat in range(4):
                g = GROUPS[(bar + beat) % len(GROUPS)]
                slot = 1.0 / g
                for k in range(g):
                    off = fig[note_i % len(fig)]
                    p = min(79, root + off)
                    is_flourish = (beat == 3 and k == g - 1
                                  and note_i == len(fig) - 1)
                    if is_flourish:
                        tag = "trill_m3" if bar % 2 == 0 else "bend_wh"
                        note_len = min(1.6, slot * 3)
                        vel = 108
                    elif prev_pitch is not None and abs(p - prev_pitch) <= 4:
                        tag = "fast"
                        note_len = slot * 0.95
                        vel = 96 + (6 if k == 0 else 0)
                    else:
                        tag = "sus"
                        note_len = slot * 0.9
                        vel = 100 + (6 if k == 0 else 0)
                    self.lead.add(t, note_len, p, vel, tag)
                    prev_pitch = p
                    t += slot
                    note_i += 1

    def riffsweep(self, sec, t0, nb):
        """A sweep built FROM the section's riff, not alongside it. The
        riff's own onset slots and pitches (G#/G in this riff) become
        accented landmark notes at their original relative positions
        inside the phrase; the space between them fills with fast
        diminished-7 arpeggio runs sharing the same root tension, tagged
        so tight intervals resolve to legato hammer-on/pull-off (the
        'sweep' sound is picked attack on landmarks, slurred cascade
        between them). Sequences up a minor third each bar — same
        harmonic world throughout (diminished symmetry), rising energy
        instead of a static loop. One trill closes the phrase."""
        r = sec.get("riff", {})
        frets = {int(k): v for k, v in r.get("frets", {}).items()}
        start_bar = sec.get("lead_start_bar", 0)
        if not frets or start_bar >= nb:
            return
        root = G_LO + r.get("detune", 0) + 31
        spine = sorted(frets)
        FILL = [0, 6, 3, 9, 6, 0, 9, 3]              # diminished-7, skips
        fill_i = 0
        prev_pitch = None
        for bar in range(start_bar, nb):
            trans = (3 * (bar - start_bar)) % 12      # rising minor 3rds
            base = t0 + bar * BAR
            for idx, slot in enumerate(spine):
                onset_t = base + slot * 0.25
                accent = min(79, root + trans + frets[slot])
                if idx + 1 < len(spine):
                    gap = (spine[idx + 1] - slot) * 0.25
                elif bar + 1 < nb:
                    gap = (16 - slot) * 0.25 + spine[0] * 0.25
                else:
                    gap = (16 - slot) * 0.25
                is_final = (bar == nb - 1 and idx == len(spine) - 1)
                if is_final:
                    self.lead.add(onset_t, 1.4, accent, 110, "trill_m3")
                    continue
                acc_len = min(gap * 0.4, 0.2)
                tag = ("fast" if prev_pitch is not None
                      and abs(accent - prev_pitch) <= 4 else "sus")
                self.lead.add(onset_t, acc_len, accent, 114, tag)
                prev_pitch = accent
                remain = gap - acc_len
                if remain > 0.02:
                    k = max(1, round(remain / 0.06))
                    step = remain / k
                    tt = onset_t + acc_len
                    for _ in range(k):
                        off = FILL[fill_i % len(FILL)]
                        fill_i += 1
                        p = min(79, root + trans + off)
                        ftag = ("fast" if abs(p - prev_pitch) <= 4
                               else "sus")
                        self.lead.add(tt, step * 0.9, p, 90, ftag)
                        prev_pitch = p
                        tt += step

    def play_extras(self, sec, t0):
        nb = int(sec["bars"])
        lead = sec.get("lead", "none")
        if lead.startswith("trem"):
            base_fret = int(lead.split(":")[1]) if ":" in lead else 5
            trem = make_tremolo(RNG, sec["bpm"], nbars=4, string=2,
                                base_fret=base_fret)
            self.tabs.append((sec["name"] + " lead trem", sec["bpm"],
                              trem.tab()))
            for rep in range(nb // 4):
                for b, (m, fr, _) in enumerate(trem.bars):
                    base = t0 + (rep * 4 + b) * BAR
                    for i in range(16):
                        p = midi_of(2, fr[i])
                        self.lead.add(base + i * 0.25, 0.24, p,
                                      max(40, 92 - (i % 2) * 10), "trem")
        elif lead == "octave":
            r = sec.get("riff", {})
            frets = {int(k): v for k, v in r.get("frets", {}).items()}
            for b in range(nb):
                base = t0 + b * BAR
                prev = None
                for i in sorted(frets):
                    if frets[i] != prev:
                        prev = frets[i]
                        self.lead.add(base + i * 0.25, 1.1,
                                      midi_of(0, prev) + 24, 92, "sus")
        elif lead == "feedback":
            self.lead.add(t0 + bars(1), bars(min(2.5, nb - 1)),
                          G_LO + 31, 58, "vib")
        elif lead == "techlead":
            self.techlead(sec, t0, nb)
        elif lead == "riffsweep":
            self.riffsweep(sec, t0, nb)
        for b in sec.get("skronk", []):
            for (st, fr) in panic_chord(RNG):
                p = midi_of(st, fr)
                self.gtr_l.add(t0 + b * BAR + 2.0, 1.5, p, 102, "sus")
                self.gtr_r.add(t0 + b * BAR + 2.0, 1.5, p, 98, "sus")
        for b in sec.get("pinch", []):
            self.gtr_l.add(t0 + b * BAR + 3.0, 1.0, G_LO + 36, 118, "pinch")
        if sec.get("subdrop"):
            self.subdrop.add(t0, 2.2,
                             G_LO + sec.get("riff", {}).get("detune", 0),
                             122, "drop")
        if sec.get("impact"):
            self.fx.add(t0, bars(1), 0, 108, "impact")
        if sec.get("riser_in"):
            self.fx.add(t0 - bars(2), bars(2), 0, 96, "riser")
        if sec.get("drone"):
            root = G_LO + sec.get("riff", {}).get("detune", 0)
            for p in (root + 24, root + 31, root + 36):
                self.strings.add(t0, bars(nb) * 0.98, p,
                                 sec.get("drone_vel", 66))
        if sec.get("sub", True) and sec.get("riff"):
            for b in range(nb):
                base = t0 + b * BAR
                p = self.roots.get(base, G_LO)
                self.subbass.add(base, BAR * 0.96, p, 110, "sub")

    def build(self):
        for sec in DOC["sections"]:
            t0 = self.sec[sec["name"]]
            self.play_riff(sec, t0)
            self.play_drums(sec, t0)
            self.play_extras(sec, t0)
        self.drums.notes = humanize(self.drums.notes, vel_jitter=4,
                                    time_jitter_beats=0.0,
                                    keep_grid=("grid",))
        for tr in (self.gtr_l, self.gtr_r):
            tr.notes = humanize(tr.notes, vel_jitter=4,
                                time_jitter_beats=0.003)
        self.bass.notes = humanize(self.bass.notes, vel_jitter=3,
                                   time_jitter_beats=0.002)
        return self.s


def build_song():
    p = Player()
    score = p.build()
    with open(os.path.join(REPO, "docs", "tabs-band.txt"), "w") as f:
        f.write(f"{DOC.get('title', 'BAND SONG')} — current jam state\n\n")
        for label, tempo, tab in p.tabs:
            f.write(f"== {label} @ {tempo} BPM\n{tab}\n\n")
    return score, p.sec
