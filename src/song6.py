"""OUROBOROS ENGINE
The recursive song (riffgen2): one seed motif, evolved under corpus
CONSTRAINTS (never corpus material — every mask is >=2 edits from every
mined mask), then developed section by section, each new section a scored
transformation of the previous one, re-evolved under its role targets.
The writing improves on itself and the log proves it (fitness curves and
the full lineage ship in docs/tabs-song6.txt).

Lineage:  seed -> diminish (verse A) -> displace (groove B)
          -> augment+thin (front breakdown) -> invert (verse A')
          -> augment (valley, bass alone) -> augment+gear-drop (final)
          -> seed restated (the snake bites its tail) -> dead stop.

Drop G 7-string, no cleans, no symphonics. modern2026 mix. ~2:50.
"""

from score import Score, Note, humanize
from riffgen import set_dialect, midi_of, panic_chord, TUNING
import random

set_dialect("modern")
import riffgen2 as r2
from riffgen2 import genome_riff
from drumgen import DrumBook

random.seed(67)
RNG = random.Random(67)

TITLE = "ouroboros_engine"
MIX_PROFILE = "modern2026"
QUAD = True          # four rhythm takes (docs/19 quad-tracking law)

BAR = 4.0
G_LO = TUNING[0]
F_LO = G_LO - 2


def bars(n):
    return n * BAR


class Ouro:
    def __init__(self):
        self.s = Score()
        self.s.tempo_map = []
        lengths = dict(coldopen=2, verseA=12, grooveB=8, frontbreak=8,
                       verseA2=12, valley=8, riser=2, finalbreak=12,
                       tail=2, out=1)
        self.sec = {}
        pos = 0.0
        for k, v in lengths.items():
            self.sec[k] = pos
            pos += bars(v)
        self.s.set_tempo(0.0, 160.0)
        self.s.set_tempo(self.sec["grooveB"], 118.0)
        self.s.set_tempo(self.sec["frontbreak"], 82.0)
        self.s.set_tempo(self.sec["verseA2"], 148.0)
        self.s.set_tempo(self.sec["valley"], 68.0)
        self.s.set_tempo(self.sec["finalbreak"], 74.0)
        self.s.set_tempo(self.sec["tail"], 160.0)
        for nm in ("gtr_l", "gtr_r", "lead", "bass", "drums",
                   "subdrop", "subbass", "fx"):
            setattr(self, nm, self.s.track(nm))
        self.book = DrumBook()
        self.tabs = []
        self.lineage = []
        self.fitlog = []
        self.roots = {}

    # --------------------------------------------------------- helpers
    def drum(self, t, name, vel, dur=0.2):
        self.drums.notes.append(Note(t, dur, 0, vel, frozenset({name,
                                                                "grid"})))

    def log_genome(self, label, tempo, g, note=""):
        riff = genome_riff(g, tempo, label)
        self.tabs.append((f"{label}{' — ' + note if note else ''}",
                          tempo, riff.tab().split("\n")[-1]))

    def play_genome(self, g, t0, nbars, tempo, vel=108, kick_follow=False,
                    detune=0, variant=None, label=""):
        riff = genome_riff(g, tempo, "sec", nbars=4, variant=variant)
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
                    dur = min(gap * 0.85, 0.4 if gap <= 0.5 else 1.5)
                    pitch = midi_of(0, frets[i]) + detune
                    gp = pitch if pitch >= 30 else pitch + 12
                    art = "sus" if gap > 0.75 else "pm"
                    for tr in (self.gtr_l, self.gtr_r):
                        tr.add(t, dur, gp, vel + (5 if i == 0 else 0), art)
                    self.bass.add(t, dur * 1.1, max(28, pitch - 12),
                                  vel + 8, "pm")
                    if kick_follow:
                        self.drum(t, "kick", 118, dur=0.1)

    def skronk(self, t, dur=1.2, vel=102):
        """Panic chord the corpus way: the RHYTHM guitars stab it (both
        players hit the cluster and let it ring over the low chug) — not a
        floating lead overdub."""
        for (st, fr) in panic_chord(RNG):
            p = midi_of(st, fr)
            self.gtr_l.add(t, dur, p, vel, "sus")
            self.gtr_r.add(t, dur, p, vel - 4, "sus")

    def sub_root(self, t0, nbars, root=None):
        for b in range(int(nbars)):
            base = t0 + b * BAR
            p = root if root is not None else self.roots.get(base, G_LO)
            self.subbass.add(base, BAR * 0.96, p, 110, "sub")

    # ----------------------------------------------------------- drums
    # Every groove bar is a REAL mined corpus bar (drumgen.DrumBook),
    # chosen by kick<->riff agreement (measured law: 0.755 coupling).
    def book_bars(self, t0, nbars, band, riff_mask, kick_lo=0, kick_hi=16,
                  prefer_cym=None, couple=True, union_riff=False,
                  vel=116, repeat_of=2, need_snare=True):
        """Write nbars of mined patterns; a pattern holds for `repeat_of`
        bars (drummers repeat), re-sampled after. union_riff forces the
        kick to also cover every riff onset (breakdown law)."""
        def dfn(t, name, v, dur):
            self.drum(t, name, v, dur)
        b = 0
        while b < int(nbars):
            pat = self.book.pick(RNG, band, riff_mask, kick_lo, kick_hi,
                                 need_snare=need_snare,
                                 prefer_cym=prefer_cym, couple=couple)[0]
            if union_riff:
                kick = "".join("X" if (pat["kick"][i] == "X"
                                       or riff_mask[i] == "X") else "."
                               for i in range(16))
                pat = dict(pat, kick=kick)
            for rep in range(min(repeat_of, int(nbars) - b)):
                self.book.write_bar(dfn, t0 + (b + rep) * BAR, pat, vel=vel)
            b += repeat_of

    # ----------------------------------------------------------- build
    def build(self):
        # ---- the seed motif: evolved from priors alone (no parent)
        seed = r2.evolve(RNG, "mid", dict(density=0.6, offbeat=0.25),
                         log=self.fitlog)
        self.lineage.append(("seed", "evolved from corpus priors",
                             self.fitlog[-1]))
        self.log_genome("M0 seed", 160, seed)

        # ---- recursion chain
        vA, tA = r2.develop(RNG, seed, "diminish", "mid",
                            dict(density=0.75, offbeat=0.2),
                            log=self.fitlog)
        self.lineage.append(("verse A", f"{tA}(seed)", self.fitlog[-1]))
        gB, tB = r2.develop(RNG, vA, "displace", "breakdown",
                            dict(density=0.45, offbeat=0.5),
                            log=self.fitlog)
        self.lineage.append(("groove B", f"{tB}(verse A)", self.fitlog[-1]))
        fb, tF = r2.develop(RNG, gB, "augment", "breakdown",
                            dict(density=0.25, offbeat=0.3,
                                 discipline=True),
                            log=self.fitlog)
        fb = r2.t_thin(RNG, fb, 1)
        self.lineage.append(("front breakdown", f"thin({tF}(groove B))",
                             self.fitlog[-1]))
        vA2, tV = r2.develop(RNG, vA, "invert", "mid",
                             dict(density=0.7, offbeat=0.25),
                             log=self.fitlog)
        self.lineage.append(("verse A'", f"{tV}(verse A)", self.fitlog[-1]))
        val, tVa = r2.develop(RNG, fb, "augment", "breakdown",
                              dict(density=0.2, offbeat=0.15,
                                   discipline=True),
                              log=self.fitlog)
        self.lineage.append(("valley", f"{tVa}(front breakdown)",
                             self.fitlog[-1]))
        fin, tFi = r2.develop(RNG, gB, "augment", "breakdown",
                              dict(density=0.22, offbeat=0.25,
                                   discipline=True),
                              log=self.fitlog)
        self.lineage.append(("final breakdown",
                             f"{tFi}(groove B) + gear drop -2",
                             self.fitlog[-1]))

        # ---- render the structure
        t = self.sec["coldopen"]
        self.gtr_l.add(t, 1.2, G_LO + 12, 100, "scratch")
        self.fx.add(t, bars(1), 0, 100, "impact")
        self.play_genome(seed, t + bars(1), 1, 160, vel=104,
                         label="cold open: M0 stated once, alone")
        self.drum(t + bars(1), "china", 110)

        t = self.sec["verseA"]
        self.drum(t, "crash1", 118)
        self.play_genome(vA, t, 12, 160, label="verse A = diminish(M0)")
        self.book_bars(t, 12, "mid", vA.mask, kick_lo=10,
                       prefer_cym="crash", repeat_of=4)
        self.sub_root(t, 12)
        for b in (3, 7):
            self.skronk(t + bars(b) + 2.0, dur=1.8)

        t = self.sec["grooveB"]
        self.drum(t, "crash2", 116)
        self.play_genome(gB, t, 8, 118, vel=106,
                         label="groove B = displace(verse A)")
        self.book_bars(t, 8, "breakdown", gB.mask, kick_lo=3, kick_hi=9,
                       prefer_cym="hat", repeat_of=2)
        self.sub_root(t, 8)

        t = self.sec["frontbreak"]
        self.subdrop.add(t, 2.0, G_LO, 120, "drop")
        self.fx.add(t, bars(1), 0, 110, "impact")
        self.play_genome(fb, t, 8, 82, vel=112,
                         label="front breakdown = thin(augment(groove B))")
        self.book_bars(t, 8, "breakdown", fb.mask, kick_lo=1, kick_hi=8,
                       prefer_cym="china", union_riff=True, vel=120,
                       repeat_of=2)
        self.sub_root(t, 8)
        self.skronk(t + bars(5), dur=2.5)

        t = self.sec["verseA2"]
        self.drum(t, "crash1", 116)
        self.play_genome(vA2, t, 12, 148,
                         label="verse A' = invert(verse A) — the motif "
                               "improved on itself")
        self.book_bars(t, 12, "mid", vA2.mask, kick_lo=10,
                       prefer_cym="crash", repeat_of=4)
        # the octave lead: doubles verse A's pitch moves two octaves up —
        # a lead line WITH a job (harmonizing the improved restatement),
        # sitting in the wall, not floating over it
        for rep in range(3):
            for b in range(4):
                base = t + (rep * 4 + b) * BAR
                prev = None
                for i in sorted(vA2.frets):
                    if vA2.frets[i] != prev:
                        prev = vA2.frets[i]
                        self.lead.add(base + i * 0.25, 1.1,
                                      midi_of(0, prev) + 24, 92, "sus")
        self.sub_root(t, 12)

        t = self.sec["valley"]
        # bass alone carries augment(front breakdown); feedback above
        riff = genome_riff(val, 68, "valley")
        self.tabs.append(("valley = augment(front breakdown), bass alone",
                          68, riff.tab()))
        for rep in range(2):
            for b, (mask, frets, _) in enumerate(riff.bars):
                base = t + (rep * 4 + b) * BAR
                for i in sorted(frets):
                    self.bass.add(base + i * 0.25, 0.5,
                                  max(28, midi_of(0, frets[i]) - 12),
                                  108, "pm")
                self.roots[base] = midi_of(0, frets[min(frets)])
        self.book_bars(t, 8, "breakdown", val.mask, kick_lo=1, kick_hi=4,
                       need_snare=False, prefer_cym="none", vel=106,
                       repeat_of=2)
        self.lead.add(t + bars(1), bars(2.5), G_LO + 31, 58, "vib")
        self.lead.add(t + bars(5), bars(2.5), G_LO + 26, 60, "vib")
        self.sub_root(t, 8)

        t = self.sec["riser"]
        self.fx.add(t, bars(2), 0, 100, "riser")
        for s in range(32):
            self.drum(t + s * 0.25, "kick", 96 + s, dur=0.08)

        t = self.sec["finalbreak"]
        self.subdrop.add(t, 2.4, F_LO, 124, "drop")
        self.fx.add(t, bars(1), 0, 115, "impact")
        self.play_genome(fin, t, 8, 74, vel=114, detune=-2,
                         label="final = augment(groove B) in drop F")
        self.book_bars(t, 8, "breakdown", fin.mask, kick_lo=1, kick_hi=6,
                       prefer_cym="china", union_riff=True, vel=122,
                       repeat_of=2)
        self.sub_root(t, 8, root=F_LO)
        for b in (1, 3, 5):
            self.gtr_l.add(t + bars(b) + 3.0, 1.0, F_LO + 36, 120, "pinch")
        # bars 9-12: density halves then quarters (the transform applied
        # to the arrangement itself)
        for b, tt_list in ((8, (0.0, 2.0)), (9, (0.0, 2.0)),
                           (10, (0.0,)), (11, (0.0,))):
            for tt in tt_list:
                for tr in (self.gtr_l, self.gtr_r):
                    tr.add(t + bars(b) + tt, 0.5, F_LO + 12, 118, "pm")
                self.bass.add(t + bars(b) + tt, 0.6, F_LO, 116, "pm")
                self.subbass.add(t + bars(b) + tt, 1.6, F_LO, 112, "sub")
                self.drum(t + bars(b) + tt, "kick", 122, dur=0.12)
                self.drum(t + bars(b) + tt, "china", 112)
            self.drum(t + bars(b) + 2.0, "snare", 124)

        # ---- tail: the seed returns, once, alone — recursion closed
        t = self.sec["tail"]
        self.play_genome(seed, t, 1, 160, vel=102,
                         label="tail: M0 restated — the snake bites its "
                               "tail")
        self.drum(t, "china", 108)

        t = self.sec["out"]
        for tr in (self.gtr_l, self.gtr_r):
            tr.add(t, 0.3, G_LO, 122, "pm")
        self.bass.add(t, 0.35, G_LO - 12 + 12, 120, "pm")
        self.subbass.add(t, 0.6, G_LO, 114, "sub")
        self.drum(t, "kick", 124, dur=0.12)
        self.drum(t, "china", 116)

        # 2026 grid-tight humanization
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
    o = Ouro()
    score = o.build()
    import os
    repo = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    with open(os.path.join(repo, "docs", "tabs-song6.txt"), "w") as f:
        f.write("OUROBOROS ENGINE — recursive development log\n"
                "(Drop G 7-string; final breakdown sounds in drop F)\n\n"
                "== LINEAGE (each section = scored transformation of the "
                "previous)\n")
        for name, derivation, curve in o.lineage:
            f.write(f"  {name:18s} <- {derivation}\n")
            f.write(f"  {'':18s}    fitness {curve[0]} -> {curve[-1]} "
                    f"over {len(curve)} generations\n")
        f.write("\nNo mask in this song exists in the corpus (novelty >= 2 "
                "edits enforced).\n\n== TABS\n\n")
        for label, tempo, tab in o.tabs:
            f.write(f"== {label} @ {tempo} BPM\n{tab}\n\n")
    return score, o.sec
