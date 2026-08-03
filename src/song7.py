"""ALL LIGHT IS CARRION
The reference-locked song. User-locked targets (docs/17 numbering):
  #3  Lorna Shore - Sun//Eater            (blast architecture, tremolo melody)
  #17 Signs of the Swarm - Amongst the Low & Empty   (slam groove brutality)
  #35 Black Tongue - Second Death          (downtempo crush finale)

Everything anchors to THESE three songs' mined laws (corpus/refs.json:
open-string share 0.49, pedal share 0.82 — twice the corpus average), not
the 39-song mean. Novelty still enforced against the full corpus AND the
refs: their laws outrank the average, their bars are never copied.

Arc = the triangle: drone intro -> Sun//Eater blast movement w/ tremolo
melody -> Low&Empty slam -> blast reprise (inverted) -> slam develops ->
Second Death doom finale (breakdown-as-song-body, ends massive, ring-out
not dead-stop). Recursive development chain throughout. Drop G, quad wall,
atmospheric string bed permitted (Sun//Eater was chosen knowingly).
"""

import os
from score import Score, Note, humanize
from riffgen import set_dialect, midi_of, panic_chord, TUNING, make_tremolo
import random

set_dialect("modern")
import riffgen2 as r2
from riffgen2 import genome_riff

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
r2.set_reference(os.path.join(REPO, "corpus", "refs.json"))
from drumgen import DrumBook

random.seed(71)
RNG = random.Random(71)
SEED_STREAM = 2      # candidate index chosen by the audio critic cull

TITLE = "all_light_is_carrion"
MIX_PROFILE = "modern2026"
QUAD = True

BAR = 4.0
G_LO = TUNING[0]


def bars(n):
    return n * BAR


class Carrion:
    def __init__(self):
        self.s = Score()
        self.s.tempo_map = []
        lengths = dict(intro=4, blastA=24, slamB=16, reprise=8,
                       slamB2=12, doomC=14, tail=2)
        self.sec = {}
        pos = 0.0
        for k, v in lengths.items():
            self.sec[k] = pos
            pos += bars(v)
        self.s.set_tempo(0.0, 70.0)
        self.s.set_tempo(self.sec["blastA"], 240.0)
        self.s.set_tempo(self.sec["slamB"], 142.0)
        self.s.set_tempo(self.sec["reprise"], 240.0)
        self.s.set_tempo(self.sec["slamB2"], 142.0)
        self.s.set_tempo(self.sec["doomC"], 66.0)
        for nm in ("gtr_l", "gtr_r", "lead", "bass", "drums", "strings",
                   "subdrop", "subbass", "fx"):
            setattr(self, nm, self.s.track(nm))
        self.book = DrumBook("refs")
        self.tabs = []
        self.lineage = []
        self.fitlog = []
        self.roots = {}

    # --------------------------------------------------------- helpers
    def drum(self, t, name, vel, dur=0.2):
        self.drums.notes.append(Note(t, dur, 0, vel, frozenset({name,
                                                                "grid"})))

    def play_genome(self, g, t0, nbars, tempo, vel=108, detune=0,
                    ring=False, label=""):
        riff = genome_riff(g, tempo, "sec")
        self.tabs.append((label, tempo, riff.tab()))
        nb = len(riff.bars)
        for rep in range(int(nbars // nb)):
            for b, (mask, frets, _) in enumerate(riff.bars):
                base = t0 + (rep * nb + b) * BAR
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
                    for tr in (self.gtr_l, self.gtr_r):
                        tr.add(t, dur, gp, vel + (5 if i == 0 else 0), art)
                    self.bass.add(t, dur * 1.1, max(28, pitch - 12),
                                  vel + 8, "pm")

    def book_bars(self, t0, nbars, riff_mask, kick_lo=0, kick_hi=16,
                  prefer_cym=None, union_riff=False, vel=116,
                  repeat_of=2, need_snare=True):
        def dfn(t, name, v, dur):
            self.drum(t, name, v, dur)
        b = 0
        while b < int(nbars):
            pat = self.book.pick(RNG, "*", riff_mask, kick_lo, kick_hi,
                                 need_snare=need_snare,
                                 prefer_cym=prefer_cym)[0]
            if union_riff:
                kick = "".join("X" if (pat["kick"][i] == "X"
                                       or riff_mask[i] == "X") else "."
                               for i in range(16))
                pat = dict(pat, kick=kick)
            for rep in range(min(repeat_of, int(nbars) - b)):
                self.book.write_bar(dfn, t0 + (b + rep) * BAR, pat, vel=vel)
            b += repeat_of

    def blast_kit(self, t0, nbars):
        """Sun//Eater blast law at REAL tempo (tabs are half-time notated,
        so translate: 8th-note snare/kick engine + ride, phrase crashes)."""
        for b in range(int(nbars)):
            base = t0 + b * BAR
            for e in range(8):
                self.drum(base + e * 0.5, "snare", 108 + (e == 0) * 8)
                self.drum(base + e * 0.5, "kick", 112, dur=0.08)
                self.drum(base + e * 0.5, "ride", 84)
            if b % 4 == 0:
                self.drum(base, "crash1", 116)

    def sub_root(self, t0, nbars, root=None):
        for b in range(int(nbars)):
            base = t0 + b * BAR
            p = root if root is not None else self.roots.get(base, G_LO)
            self.subbass.add(base, BAR * 0.96, p, 110, "sub")

    def drone(self, t0, nbars, root, vel=72):
        """Atmospheric string bed: root+fifth+octave above the wall."""
        for p in (root + 24, root + 31, root + 36):
            self.strings.add(t0, bars(nbars) * 0.98, p, vel)

    # ----------------------------------------------------------- build
    def build(self):
        rng = random.Random(700 + SEED_STREAM)
        seed = r2.evolve(rng, "mid", dict(density=0.55, offbeat=0.2),
                         log=self.fitlog)
        self.lineage.append(("seed (blast A)", "critic-culled candidate "
                             f"#{SEED_STREAM}", self.fitlog[-1]))
        slam, tS = r2.develop(RNG, seed, "displace", "mid",
                              dict(density=0.5, offbeat=0.35),
                              log=self.fitlog)
        self.lineage.append(("slam B", f"{tS}(seed)", self.fitlog[-1]))
        repr_, tR = r2.develop(RNG, seed, "invert", "mid",
                               dict(density=0.55, offbeat=0.2),
                               log=self.fitlog)
        self.lineage.append(("reprise", f"{tR}(seed)", self.fitlog[-1]))
        doom, tD = r2.develop(RNG, slam, "augment", "breakdown",
                              dict(density=0.18, offbeat=0.1,
                                   discipline=True),
                              log=self.fitlog)
        self.lineage.append(("doom C", f"{tD}(slam B)", self.fitlog[-1]))

        # ---- intro: drone + two Black Tongue crush hits per bar
        t = self.sec["intro"]
        self.drone(t, 4, G_LO)
        self.fx.add(t, bars(1), 0, 90, "impact")
        for b in range(2, 4):
            for tt in (0.0, 2.5):
                for tr in (self.gtr_l, self.gtr_r):
                    tr.add(t + bars(b) + tt, 1.8, G_LO, 112, "sus")
                self.bass.add(t + bars(b) + tt, 2.0, max(28, G_LO - 12),
                              114, "pm")
                self.drum(t + bars(b) + tt, "kick", 118, dur=0.12)
                self.drum(t + bars(b) + tt, "china", 106)
            self.drum(t + bars(b) + 2.0, "snare", 118)
        self.sub_root(t + bars(2), 2, root=G_LO)

        # ---- blast A: Sun//Eater movement, tremolo melody as co-lead
        t = self.sec["blastA"]
        self.drum(t, "crash1", 120)
        self.play_genome(seed, t, 24, 240, vel=106,
                         label="blast A: ref-locked seed")
        self.blast_kit(t, 24)
        self.sub_root(t, 24)
        trem = make_tremolo(RNG, 240, nbars=4, string=2, base_fret=5)
        self.tabs.append(("blast A tremolo melody (lead)", 240, trem.tab()))
        for rep in range(6):
            for b, (mask, frets, _) in enumerate(trem.bars):
                base = t + (rep * 4 + b) * BAR
                for i in range(16):
                    p = midi_of(2, frets[i])
                    v = 92 + (0 if i % 2 == 0 else -10)
                    self.lead.add(base + i * 0.25, 0.24, p, max(40, v),
                                  "trem")
        self.drone(t + bars(16), 8, G_LO, vel=64)

        # ---- slam B: Low & Empty movement
        t = self.sec["slamB"]
        self.subdrop.add(t, 2.0, G_LO, 118, "drop")
        self.fx.add(t, bars(1), 0, 105, "impact")
        self.play_genome(slam, t, 16, 142, vel=110,
                         label="slam B = displace(seed)")
        self.book_bars(t, 16, slam.mask, kick_lo=3, kick_hi=12,
                       prefer_cym="china", union_riff=True, vel=118)
        self.sub_root(t, 16)

        # ---- blast reprise: inverted seed, strings swell back in
        t = self.sec["reprise"]
        self.fx.add(t - bars(2), bars(2), 0, 95, "riser")
        self.drum(t, "crash2", 120)
        self.play_genome(repr_, t, 8, 240, vel=106,
                         label="reprise = invert(seed)")
        self.blast_kit(t, 8)
        self.sub_root(t, 8)
        self.drone(t, 8, G_LO, vel=70)

        # ---- slam B develops (pinch answers, skronk ring)
        t = self.sec["slamB2"]
        self.play_genome(slam, t, 12, 142, vel=112,
                         label="slam B' (develops, squeal answers)")
        self.book_bars(t, 12, slam.mask, kick_lo=3, kick_hi=12,
                       prefer_cym="china", union_riff=True, vel=120)
        self.sub_root(t, 12)
        for b in (3, 7, 11):
            self.gtr_l.add(t + bars(b) + 3.0, 0.9, G_LO + 36, 118, "pinch")

        # ---- doom C: Second Death finale — the breakdown IS the song body
        t = self.sec["doomC"]
        self.subdrop.add(t, 2.6, G_LO, 124, "drop")
        self.fx.add(t, bars(1), 0, 115, "impact")
        self.play_genome(doom, t, 12, 66, vel=114, ring=True,
                         label="doom C = augment(slam B), let ring")
        self.book_bars(t, 12, doom.mask, kick_lo=1, kick_hi=6,
                       prefer_cym="china", union_riff=True, vel=122,
                       need_snare=True)
        self.sub_root(t, 14)
        self.drone(t, 14, G_LO, vel=66)
        for b in (2, 6, 10):
            self.gtr_l.add(t + bars(b) + 3.5, 1.2, G_LO + 24, 118, "pinch")
        # last 2 bars: half density, everything rings
        for b, tts in ((12, (0.0, 2.0)), (13, (0.0,))):
            for tt in tts:
                for tr in (self.gtr_l, self.gtr_r):
                    tr.add(t + bars(b) + tt, 2.4, G_LO, 118, "sus")
                self.bass.add(t + bars(b) + tt, 2.6, max(28, G_LO - 12),
                              116, "pm")
                self.drum(t + bars(b) + tt, "kick", 122, dur=0.12)
                self.drum(t + bars(b) + tt, "china", 112)
            self.drum(t + bars(b) + 2.0, "snare", 122)

        # ---- tail: ring-out + feedback (Black Tongue ends massive)
        t = self.sec["tail"]
        self.lead.add(t, bars(2), G_LO + 31, 60, "vib")
        self.drone(t, 2, G_LO, vel=58)

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
    c = Carrion()
    score = c.build()
    with open(os.path.join(REPO, "docs", "tabs-song7.txt"), "w") as f:
        f.write("ALL LIGHT IS CARRION — reference-locked development log\n"
                "(refs: Sun//Eater / Amongst the Low & Empty / Second "
                "Death; open 0.49, pedal 0.82)\n\n== LINEAGE\n")
        for name, deriv, curve in c.lineage:
            f.write(f"  {name:16s} <- {deriv}\n")
            f.write(f"  {'':16s}    fitness {curve[0]} -> {curve[-1]}\n")
        f.write("\n== TABS\n\n")
        for label, tempo, tab in c.tabs:
            f.write(f"== {label} @ {tempo} BPM\n{tab}\n\n")
    return score, c.sec
