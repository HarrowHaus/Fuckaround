"""CURB GOSPEL
Full 2026 underground dialect (docs/17-20). No symphonics, no cleans.

Drop G 7-string. Every riff generated from the MODERN idiom corpus
(idiom_modern.json — 39 songs, 2018-2026): fretted-pedal dominance, off-beat
displacement bounce, half-step obsession. Skronk stabs are Knocked Loose
tritone clusters (panic_chord). Structure follows docs/20's underground laws:
cold open, front-loaded breakdown inside the first minute, glitch-edit
transition, non-clean valley (bass grind + feedback, no clean guitar), riser
into an EARNED final breakdown that pulls the Whitechapel drop-F gear change
(bass + sub own F1; guitars octave-double at F2 — the 9-string translation
law), density-halving, dead stop. ~2:40. Grid-tight (DAW-native era).

The riff is an arrangement object: guitar + tuned sub drop + edit (docs/20).
"""

from score import Score, Note, humanize
from riffgen import (make_riff, midi_of, panic_chord, set_dialect, TUNING)
import random

set_dialect("modern")

random.seed(56)
RNG = random.Random(56)

TITLE = "curb_gospel"
MIX_PROFILE = "modern2026"

BAR = 4.0
G_LO = TUNING[0]                # G1 = 31 (49 Hz)
F_LO = G_LO - 2                 # the drop-F gear change (F1 fundamental)


def bars(n):
    return n * BAR


class Curb:
    def __init__(self):
        self.s = Score()
        self.s.tempo_map = []
        lengths = dict(coldopen=2, bounce1=8, blastverse=12, frontbreak=8,
                       verse2=12, glitch=1, valley=8, riser=2,
                       finalbreak=12, out=1)
        self.sec = {}
        pos = 0.0
        for k, v in lengths.items():
            self.sec[k] = pos
            pos += bars(v)
        self.s.set_tempo(0.0, 112.0)
        self.s.set_tempo(self.sec["blastverse"], 165.0)
        self.s.set_tempo(self.sec["frontbreak"], 84.0)
        self.s.set_tempo(self.sec["verse2"], 140.0)
        self.s.set_tempo(self.sec["valley"], 70.0)
        self.s.set_tempo(self.sec["finalbreak"], 76.0)
        for nm in ("gtr_l", "gtr_r", "lead", "bass", "drums",
                   "subdrop", "subbass", "fx"):
            setattr(self, nm, self.s.track(nm))
        self.tabs = []
        self.roots = {}          # beat -> root pitch for the sub layer

    # ------------------------------------------------------------- helpers
    def drum(self, t, name, vel, dur=0.2):
        # 2026 = DAW-native: everything on the grid
        self.drums.notes.append(Note(t, dur, 0, vel, frozenset({name, "grid"})))

    def play_riff(self, riff, t0, reps=1, vel=108, kick_follow=False,
                  label="", detune=0):
        """Render a Riff onto both guitars + bass; log bar roots for the
        sub layer. detune=-2 renders the drop-F gear (guitars octave up
        when below the F#1 sampler floor — the 9-string translation law)."""
        self.tabs.append((label or riff.kind, riff.tempo, riff.tab()))
        nb = len(riff.bars)
        for rep in range(reps):
            for b, (mask, frets, pinch) in enumerate(riff.bars):
                base = t0 + (rep * nb + b) * BAR
                slots = sorted(frets)
                if slots:
                    root = midi_of(riff.string, frets[slots[0]]) + detune
                    self.roots[base] = root
                for idx, i in enumerate(slots):
                    t = base + i * 0.25
                    nxt = slots[idx + 1] if idx + 1 < len(slots) else 16
                    gap = (nxt - i) * 0.25
                    dur = min(gap * 0.85, 0.4 if gap <= 0.5 else 1.5)
                    pitch = midi_of(riff.string, frets[i]) + detune
                    gpitch = pitch if pitch >= 30 else pitch + 12
                    ring = gap > 0.75
                    art = "sus" if ring else "pm"
                    for tr in (self.gtr_l, self.gtr_r):
                        tr.add(t, dur, gpitch, vel + (5 if i == 0 else 0)
                               + (4 if ring else 0), art)
                    if pinch == i:
                        self.gtr_l.add(t + 0.02, 1.0, gpitch + 24, 119,
                                       "pinch")
                    self.bass.add(t, dur * 1.1, max(28, pitch - 12),
                                  vel + 8, "pm")
                    if kick_follow:
                        self.drum(t, "kick", 118, dur=0.1)

    def skronk(self, t, dur=1.2, vel=96):
        """Panic-chord stab: tritone cluster rings on the leads while the
        rhythm wall keeps chugging under it."""
        for (st, fr) in panic_chord(RNG):
            self.lead.add(t, dur, midi_of(st, fr), vel, "sus")
            self.lead.add(t, dur, midi_of(st, fr), vel - 8, "vib")

    def sub_root(self, t0, nbars, root=None):
        """Synth sub layer: one sustained fundamental per bar (the mix HPFs
        the real bass to grind; this owns <100 Hz — docs/19)."""
        for b in range(int(nbars)):
            base = t0 + b * BAR
            p = root if root is not None else self.roots.get(base, G_LO)
            self.subbass.add(base, BAR * 0.96, p, 110, "sub")

    # ---------------------------------------------------------- 2026 drums
    def bounce_beat(self, t0, nbars, ghost=True):
        """Nu-deathcore half-time bounce: snare 3, kick syncopated with the
        riff's displacement, tight hats with an open lift on the &4."""
        for b in range(int(nbars)):
            base = t0 + b * BAR
            self.drum(base + 2.0, "snare", 122)
            for tt in (0.0, 0.75, 1.5, 2.75, 3.25):
                self.drum(base + tt, "kick", 116, dur=0.1)
            for e in range(8):
                self.drum(base + e * 0.5, "hihat_closed", 82 - (e % 2) * 14)
            if ghost and b % 2 == 1:
                self.drum(base + 3.5, "snare", 62)
            self.drum(base + 3.5, "hihat_open", 92)

    def modern_verse(self, t0, nbars):
        """165 BPM engine: 16th double-kick under snare 2+4 for 8 bars,
        gravity-tight blast (snare 8ths, kick 8ths) for the last 4."""
        groove = int(nbars) - 4
        for b in range(groove):
            base = t0 + b * BAR
            for s in range(16):
                self.drum(base + s * 0.25, "kick", 112, dur=0.08)
            self.drum(base + 1.0, "snare", 121)
            self.drum(base + 3.0, "snare", 121)
            for q in range(4):
                self.drum(base + q, "china" if b % 4 == 3 else "ride", 88)
        for b in range(groove, int(nbars)):
            base = t0 + b * BAR
            for e in range(8):
                self.drum(base + e * 0.5, "snare", 108 + (e == 0) * 8)
                self.drum(base + e * 0.5, "kick", 112, dur=0.08)
                self.drum(base + e * 0.5, "ride", 84)

    def breakdown_kit(self, t0, nbars, china=True):
        for b in range(int(nbars)):
            base = t0 + b * BAR
            self.drum(base + 2.0, "snare", 123)
            if china:
                for q in range(4):
                    self.drum(base + q, "china", 102 + (q == 0) * 10)

    def fill(self, t0):
        for i, d in enumerate(("snare", "tom2", "tom3", "tom_floor")):
            self.drum(t0 + i * 0.25, d, 104 + i * 4)

    # ------------------------------------------------------------- build
    def build(self):
        self.coldopen(); self.bounce1(); self.blastverse(); self.frontbreak()
        self.verse2(); self.glitch(); self.valley(); self.riser_sec()
        self.finalbreak(); self.outro()
        # 2026 = tight: tiny velocity life, no timing drift, drums stay grid
        self.drums.notes = humanize(self.drums.notes, vel_jitter=4,
                                    time_jitter_beats=0.0,
                                    keep_grid=("grid",))
        for tr in (self.gtr_l, self.gtr_r):
            tr.notes = humanize(tr.notes, vel_jitter=4,
                                time_jitter_beats=0.003)
        self.bass.notes = humanize(self.bass.notes, vel_jitter=3,
                                   time_jitter_beats=0.002)
        return self.s

    def coldopen(self):
        """Hard cold open (raw-lane law): scrape, one bounce tease bar."""
        t0 = self.sec["coldopen"]
        self.gtr_l.add(t0, 1.5, G_LO + 12, 100, "scratch")
        self.fx.add(t0, bars(1), 0, 100, "impact")
        self.r_bounce = make_riff(RNG, "bounce", 112, max_pcs=4)
        self.play_riff(self.r_bounce, t0 + bars(1), reps=0 or 1, vel=104,
                       label="cold-open tease")
        self.bounce_beat(t0 + bars(1), 1, ghost=False)

    def bounce1(self):
        """The bounce groove proper — displacement riff, full band."""
        t0 = self.sec["bounce1"]
        self.drum(t0, "crash1", 118)
        self.play_riff(self.r_bounce, t0, reps=2, label="bounce groove")
        self.bounce_beat(t0, 8)
        self.sub_root(t0, 8)
        self.skronk(t0 + bars(3) + 3.0)
        self.skronk(t0 + bars(7) + 3.0)
        self.fill(t0 + bars(7) + 3.0)

    def blastverse(self):
        """165 engine verse: modern chug riff, skronk answers every 4th bar."""
        t0 = self.sec["blastverse"]
        self.drum(t0, "crash2", 116)
        r = make_riff(RNG, "chug", 165, max_pcs=4)
        self.play_riff(r, t0, reps=3, label="blast verse chug")
        self.modern_verse(t0, 12)
        self.sub_root(t0, 12)
        for b in (3, 7):
            self.skronk(t0 + bars(b) + 2.0, dur=1.8)

    def frontbreak(self):
        """FRONT-LOADED breakdown (skip-rate law: inside the first minute).
        Tuned sub drop on the first hit, china quarters, sparse mined grid."""
        t0 = self.sec["frontbreak"]
        self.subdrop.add(t0, 2.0, G_LO, 120, "drop")
        self.fx.add(t0, bars(1), 0, 110, "impact")
        r = make_riff(RNG, "breakdown", 84, max_pcs=3)
        self.play_riff(r, t0, reps=2, kick_follow=True, vel=112,
                       label="front breakdown")
        self.breakdown_kit(t0, 8)
        self.sub_root(t0, 8)
        self.skronk(t0 + bars(5), dur=2.5)     # dissonance over the chug

    def verse2(self):
        """140 groove — same bounce DNA displaced; half-time flip last 2."""
        t0 = self.sec["verse2"]
        self.drum(t0, "crash1", 116)
        r = make_riff(RNG, "bounce", 140, max_pcs=4)
        self.play_riff(r, t0, reps=2, vel=106, label="verse2 displacement")
        self.bounce_beat(t0, 10)
        self.play_riff(r, t0 + bars(10), reps=0 or 1, vel=112,
                       label="half-time flip (same riff, doubled values)")
        self.breakdown_kit(t0 + bars(10), 2, china=True)
        self.sub_root(t0, 12)

    def glitch(self):
        """One bar of stutter edit: 32nd retrigger + tape-stop dive."""
        t0 = self.sec["glitch"]
        for i in range(8):
            v = 118 - i * 6
            for tr in (self.gtr_l, self.gtr_r):
                tr.add(t0 + i * 0.125, 0.1, G_LO, max(60, v), "pmx")
            self.bass.add(t0 + i * 0.125, 0.1, G_LO - 12 + 12, max(60, v),
                          "pm")
            self.drum(t0 + i * 0.125, "kick", max(70, 118 - i * 5), dur=0.06)
        self.fx.add(t0 + 1.0, bars(0.75), G_LO + 24, 90, "dive")

    def valley(self):
        """The non-clean big quiet: bass grind carries the riff alone,
        feedback swells above, sparse kit. Earning the final breakdown."""
        t0 = self.sec["valley"]
        r = make_riff(RNG, "breakdown", 70, max_pcs=3)
        self.tabs.append(("valley (bass only)", 70, r.tab()))
        nb = len(r.bars)
        for rep in range(2):
            for b, (mask, frets, _) in enumerate(r.bars):
                base = t0 + (rep * nb + b) * BAR
                for i in sorted(frets):
                    self.bass.add(base + i * 0.25, 0.5,
                                  max(28, midi_of(0, frets[i]) - 12),
                                  108, "pm")
                self.roots[base] = midi_of(0, frets[min(frets)])
        for b in range(8):
            base = t0 + b * BAR
            self.drum(base, "kick", 106, dur=0.1)
            self.drum(base + 2.0, "snare", 96)
            self.drum(base + 3.5, "tom_floor", 80)
        # feedback swells, not cleans
        self.lead.add(t0 + bars(1), bars(2.5), G_LO + 31, 58, "vib")
        self.lead.add(t0 + bars(5), bars(2.5), G_LO + 26, 60, "vib")
        self.sub_root(t0, 8)

    def riser_sec(self):
        """2-bar build: noise riser + double-kick ramp; the mix vacuum
        (filter collapse) hits the last bar before the drop."""
        t0 = self.sec["riser"]
        self.fx.add(t0, bars(2), 0, 100, "riser")
        for s in range(32):
            self.drum(t0 + s * 0.25, "kick", 96 + s, dur=0.08)
        for q in range(4):
            self.drum(t0 + bars(1) + q, "snare", 100 + q * 6)

    def finalbreak(self):
        """THE earned breakdown — drop-F gear change (docs/20's Whitechapel
        law): bass + sub own F1, guitars octave-translate. Pinch squeals as
        call-response, density halves, dead stop."""
        t0 = self.sec["finalbreak"]
        self.subdrop.add(t0, 2.4, F_LO, 124, "drop")
        self.fx.add(t0, bars(1), 0, 115, "impact")
        r = make_riff(RNG, "final_breakdown", 76, max_pcs=3)
        self.play_riff(r, t0, reps=2, kick_follow=True, vel=114,
                       detune=-2, label="final breakdown (drop F gear)")
        self.breakdown_kit(t0, 8)
        self.sub_root(t0, 8, root=F_LO)
        for b in (1, 3, 5):
            self.gtr_l.add(t0 + bars(b) + 3.0, 1.0, F_LO + 36, 120, "pinch")
            self.skronk(t0 + bars(b) + 3.5, dur=0.5, vel=100)
        # bars 9-12: half density -> quarter density, all on F
        for b, tt_list in ((8, (0.0, 2.0)), (9, (0.0, 2.0)),
                           (10, (0.0,)), (11, (0.0,))):
            for tt in tt_list:
                for tr in (self.gtr_l, self.gtr_r):
                    tr.add(t0 + bars(b) + tt, 0.5, F_LO + 12, 118, "pm")
                self.bass.add(t0 + bars(b) + tt, 0.6, F_LO, 116, "pm")
                self.subbass.add(t0 + bars(b) + tt, 1.6, F_LO, 112, "sub")
                self.drum(t0 + bars(b) + tt, "kick", 122, dur=0.12)
                self.drum(t0 + bars(b) + tt, "china", 112)
            self.drum(t0 + bars(b) + 2.0, "snare", 124)

    def outro(self):
        """Dead stop. One staccato hit on the downbeat, then nothing
        (hard-cut law; fades are extinct)."""
        t0 = self.sec["out"]
        for tr in (self.gtr_l, self.gtr_r):
            tr.add(t0, 0.3, F_LO + 12, 122, "pm")
        self.bass.add(t0, 0.35, F_LO, 120, "pm")
        self.subbass.add(t0, 0.6, F_LO, 114, "sub")
        self.drum(t0, "kick", 124, dur=0.12)
        self.drum(t0, "china", 116)


def build_song():
    c = Curb()
    score = c.build()
    import os
    repo = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    with open(os.path.join(repo, "docs", "tabs-song5.txt"), "w") as f:
        f.write("CURB GOSPEL — generated tabs (modern dialect)\n"
                "(Drop G 7-string: G-D-G-C-F-A-D low to high; final "
                "breakdown sounds a whole step lower — drop F gear)\n\n")
        for label, tempo, tab in c.tabs:
            f.write(f"== {label} @ {tempo} BPM\n{tab}\n\n")
    return score, c.sec
