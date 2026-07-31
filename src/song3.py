"""THE SEVERED CROWN — Archspire x Netherwalker hybrid.

Tech-death precision inside a medieval-fantasy cinematic frame, built from
docs/11-archspire-study.md + docs/09-netherwalker-brief.md:
- DAW 175 core ("350"), climax at 200 ("400"), through-composed with
  recapitulation; THEME stated as clean 2-voice counterpoint first (the
  tavern cold open), at speed harmonized later, rubato before the climax.
- 5/7-note 32nd bursts, stutter masks in band unison (kick copies 1:1),
  3+3+2 stabs with vocal gatling gaps, pedal lattices, dim7 sweeps, a
  3-voice tap canon, blast species rotating every 2-4 bars, hard gated stops.
- Netherwalker: choir/strings cinematics, blackened gallop bridge, one
  tavern-leveling half-time breakdown, heroic harmonized THEME.
- Bass = lead voice (darkblack keyswitch program): unison bursts, tapped
  triplet fills answering every 2nd stab silence, 4-bar feature.
- Humanize: velocities only (the genre is grid-tight by definition).

Key: A minor (A1 = 33 pedal; low E1 = 28 for double-drop moments).
"""

from score import Score, Note, humanize
import random

random.seed(43)

TITLE = "the_severed_crown"
MIX_PROFILE = "techdeath"
BASS_PROGRAM = "01-darkblack_keysw.sfz"

A1 = 33
E1 = 28
BAR = 4.0

AEOLIAN = [0, 2, 3, 5, 7, 8, 10]
HARM = [0, 2, 3, 5, 7, 8, 11]
DIM7 = [0, 3, 6, 9]

# THE THEME (A harmonic minor, heroic-grim): scale-degree offsets + beats
THEME = [(0, 1.5), (7, 0.5), (8, 1.0), (7, 0.5), (3, 0.5),
         (5, 1.0), (3, 0.5), (2, 0.5), (0, 1.0), (-1, 1.0), (0, 2.0)]


def bars(n):
    return n * BAR


class Crown:
    def __init__(self):
        self.s = Score()
        self.s.tempo_map = []
        lengths = dict(taverne=8, themeA=16, stabs1=6, latticeB=12,
                       twinC=10, gallop=10, crownfall=10, solo=8, tapcanon=4,
                       recapA=8, reverie=4, climax=14, outro=2)
        self.sec = {}
        pos = 0.0
        for k, v in lengths.items():
            self.sec[k] = pos
            pos += bars(v)
        self.total = pos
        self.s.set_tempo(0.0, 96.0)                    # tavern counterpoint
        self.s.set_tempo(self.sec["themeA"], 175.0)     # "350"
        self.s.set_tempo(self.sec["crownfall"], 87.5)   # half-time feel drop
        self.s.set_tempo(self.sec["solo"], 175.0)
        self.s.set_tempo(self.sec["reverie"], 80.0)     # rubato breath
        self.s.set_tempo(self.sec["climax"], 200.0)     # "400"
        self.s.set_tempo(self.sec["outro"], 175.0)

        for nm in ("gtr_l", "gtr_r", "lead", "clean", "bass", "drums",
                   "strings", "strings_stac", "choir", "subdrop", "fx"):
            setattr(self, nm if nm != "subdrop" else "sub", self.s.track(nm))
        self.drums = self.s.track("drums")

    # ------------------------------------------------------------- helpers
    def drum(self, t, name, vel, dur=0.2, grid=True):
        tags = {name, "grid"} if grid else {name}
        self.drums.notes.append(Note(t, dur, 0, vel, frozenset(tags)))

    def gtr(self, t, dur, pitch, vel, *tags, both=True, right=False):
        trs = [self.gtr_l, self.gtr_r] if both else \
            ([self.gtr_r] if right else [self.gtr_l])
        for tr in trs:
            tr.add(t, dur, pitch, vel, *tags)

    def bassn(self, t, dur, pitch, vel, *tags):
        self.bass.add(t, dur, max(28, pitch), min(127, vel), *tags)

    def deg(self, scale, d, base=A1 + 12):
        return base + scale[d % 7] + 12 * (d // 7)

    # ----------------------------------------------- Archspire machinery
    def burst(self, t, n32, pitch, vel=108, trill=None, kick=True):
        """A 5/7/3-note 32nd tremolo burst; optionally a real trill patch.
        Kick quads copy the burst 1:1 (the law)."""
        if trill:
            self.gtr(t, n32 * 0.125 * 0.95, pitch, vel, trill)
            self.bassn(t, n32 * 0.125, pitch - 12, vel, "bsus")
        else:
            for i in range(n32):
                v = vel - (0 if i % 2 == 0 else 10) - (i // 4) * 2
                self.gtr(t + i * 0.125, 0.11, pitch, v, "pm")
                self.bassn(t + i * 0.125, 0.11, pitch - 12, v + 4, "bstac")
        if kick:
            for i in range(n32):
                self.drum(t + i * 0.125, "kick", 112, dur=0.08)

    def stutter(self, t, mask, pitch, vel=112, china=False):
        """16th-grid stutter mask in band unison; kick copies exactly."""
        for i, c in enumerate(mask):
            if c != "X":
                continue
            tt = t + i * 0.25
            self.gtr(tt, 0.14, pitch, vel, "pm")
            self.bassn(tt, 0.16, pitch - 12, vel + 4, "bstac")
            self.drum(tt, "kick", 116, dur=0.08)
            if china:
                self.drum(tt, "china", 102)

    def stab(self, t, pitch, vel=118, cluster=None, china=True, dur=0.4):
        for tr in (self.gtr_l, self.gtr_r):
            tr.add(t, dur, pitch, vel, "sus")
            if cluster:
                tr.add(t, dur, pitch + cluster, vel - 6, "sus")
        self.bassn(t, dur * 1.2, pitch - 12, vel, "bsus")
        self.drum(t, "kick", 122, dur=0.1)
        if china:
            self.drum(t, "china", 114)

    def bass_fill(self, t, root, beats=1.0):
        """Tapped triplet fill (dim7/chromatic) answering a stab silence,
        ending a half-step above the next root."""
        n = int(beats * 6)                     # 16th triplets
        cells = [root + 12 + DIM7[i % 4] + (i // 4) * 12 for i in range(n - 1)]
        for i, p in enumerate(cells):
            self.bassn(t + i * (beats / n), beats / n * 0.9, p,
                       100 + (i % 3 == 0) * 12, "bpluck")
        self.bassn(t + (n - 1) * (beats / n), 0.3, root + 13, 112, "bpluck")

    def quad_fill(self, t):
        for i, d in enumerate(("tom1", "tom1", "tom2", "tom2",
                               "tom_floor", "tom_floor", "snare", "snare")):
            self.drum(t + i * 0.125, d, 104 + (i % 2 == 0) * 8)

    def hard_stop(self, t):
        self.drum(t, "crash1_stop", 110)

    # ---------------------------------------------------- blast rotations
    def blast_trad(self, t0, nbars, cym="ride_bell"):
        for i in range(int(nbars * 16)):
            t = t0 + i * 0.25
            self.drum(t, "kick", 114 + (2 if i % 4 == 0 else 0), dur=0.08)
            self.drum(t + 0.125, "snare", 96 + [4, -4, 0, -6][i % 4])
            if i % 2 == 0:
                self.drum(t, cym, 80 if i % 4 else 90)

    def blast_hyper(self, t0, nbars):
        for i in range(int(nbars * 16)):
            t = t0 + i * 0.25
            self.drum(t, "kick", 114, dur=0.08)
            if i % 2 == 0:
                self.drum(t, "snare", 100 + [4, 0][(i // 2) % 2])
                self.drum(t, "china", 84 if i % 4 else 92)

    def blast_gravity(self, t0, nbars):
        for i in range(int(nbars * 16)):
            t = t0 + i * 0.25
            self.drum(t, "snare", 98 + [6, -2, 2, -4][i % 4])
            self.drum(t + 0.125, "snare", 76 + [0, -4][i % 2])
            self.drum(t, "kick", 112, dur=0.08)
            if i % 2 == 0:
                self.drum(t, "ride", 92 if i % 4 else 100)

    def blast_switch(self, t0, nbars):
        """Switch blast: 32nd snare 4-strokes with a once-per-8th hat pulse."""
        for i in range(int(nbars * 8)):
            t = t0 + i * 0.5
            for k in range(4):
                self.drum(t + k * 0.125, "snare",
                          88 - k * 4 + (8 if i % 2 == 0 else 0))
            self.drum(t, "hihat_closed", 96)
            self.drum(t, "kick", 112, dur=0.08)
            self.drum(t + 0.25, "kick", 110, dur=0.08)

    # ------------------------------------------------------------ sections
    def build(self):
        self.taverne(); self.themeA(); self.stabs1(); self.latticeB()
        self.twinC(); self.gallop(); self.crownfall(); self.solo()
        self.tapcanon(); self.recapA(); self.reverie(); self.climax()
        self.outro_()
        # genre law: grid-tight timing, humanize velocities ONLY
        for tr in (self.gtr_l, self.gtr_r, self.bass):
            tr.notes = humanize(tr.notes, vel_jitter=6, time_jitter_beats=0.0)
        self.drums.notes = humanize(self.drums.notes, vel_jitter=5,
                                    time_jitter_beats=0.0,
                                    keep_grid=("grid",))
        return self.s

    def taverne(self):
        """The tavern cold open: THEME as 2-voice clean counterpoint,
        staccato strings underneath — fantasy exposition."""
        t0 = self.sec["taverne"]
        t = t0
        for d, dur in THEME:
            self.clean.add(t, dur * 0.95, self.deg(HARM, d, A1 + 24), 88,
                           "clean")
            t += dur
        # counter-voice: contrary motion a 6th below, offset half a beat
        t = t0 + 0.5
        for d, dur in THEME:
            self.clean.add(t, dur * 0.9, self.deg(HARM, -d // 2 + 2, A1 + 12),
                           74, "clean")
            t += dur
        t = t0 + bars(4)
        for d, dur in THEME:
            self.clean.add(t, dur * 0.95, self.deg(HARM, d, A1 + 24), 92,
                           "clean")
            self.strings_stac.add(t, 0.3, self.deg(HARM, d, A1 + 36), 78,
                                  "stac")
            t += dur
        for i, (roff, third) in enumerate(((0, 3), (8, 4), (5, 3), (7, 4))):
            self.strings.add(t0 + bars(4 + i), BAR, 45 + roff, 60 + i * 6, "sus")
            self.choir.add(t0 + bars(4 + i), BAR, 57 + roff, 50 + i * 8, "sus")
        # last half-bar: snare-roll pickup — the blast is coming
        for i in range(8):
            self.drum(t0 + bars(8) - 1.0 + i * 0.125, "snare", 54 + i * 9,
                      grid=False)
        self.fx.add(t0 + bars(7), bars(1), 0, 92, "riser")

    def themeA(self):
        """A: burst-riff theme at 175. Bursts of 5/7 32nds, pitch changes
        between bursts walking the THEME degrees; blast rotates 2-4 bars."""
        t0 = self.sec["themeA"]
        self.drum(t0, "crash1", 116); self.drum(t0, "china", 110)
        walk = [0, 0, 7, 8, 7, 3, 5, 3, 2, 0, -1, 0, 1, 0, 7, 0]
        for b in range(16):
            base = t0 + b * BAR
            root = self.deg(AEOLIAN, walk[b], A1)
            if b % 4 < 3:
                self.burst(base, 5, root, kick=False)
                self.gtr(base + 0.75, 0.14, A1, 104, "pm")
                self.bassn(base + 0.75, 0.16, A1 - 12, 108, "bstac")
                self.burst(base + 1.0, 3, root, kick=False)
                self.burst(base + 1.75, 7, root, kick=False,
                           trill="trill_ht" if b % 8 >= 4 else None)
                self.burst(base + 3.0, 5, self.deg(AEOLIAN, walk[b] + 1, A1),
                           kick=False)
            else:
                self.stutter(base, "XX.XX.X.", A1, china=True)
                self.stutter(base + 2.0, "X.XX.XX.", A1, china=True)
        self.blast_trad(t0, 4)
        self.blast_hyper(t0 + bars(4), 2)
        self.blast_trad(t0 + bars(6), 2, cym="china")
        self.blast_switch(t0 + bars(8), 2)
        self.blast_trad(t0 + bars(10), 2)
        self.blast_hyper(t0 + bars(12), 2)
        self.blast_gravity(t0 + bars(14), 1)
        self.quad_fill(t0 + bars(15) + 3.0)
        for b in (0, 4, 8, 12):
            self.sub.add(t0 + bars(b), 1.2, A1 - 24, 112)

    def stabs1(self):
        """Unison stabs, 3+3+2 + long gaps; the vocal gatling slots. Bass
        answers the SECOND silence (the law)."""
        t0 = self.sec["stabs1"]
        for rep in range(3):
            base = t0 + bars(2 * rep)
            for tt in (0.0, 0.75, 1.5, 2.0):
                self.stab(base + tt, A1, cluster=13 if tt == 2.0 else None)
            self.hard_stop(base + 2.4)
            # bar 2: two stabs then THE GAP
            self.stab(base + BAR, E1, cluster=6)
            self.stab(base + BAR + 1.75, A1)
            self.hard_stop(base + BAR + 2.15)
            if rep % 2 == 1:
                self.bass_fill(base + BAR + 2.5, A1, beats=1.5)
            # even gaps belong to the vocalist

    def latticeB(self):
        """B: pedal lattice (PPMPPMPM) over low A, switch/hyper blast, with
        the heroic THEME harmonized above (Netherwalker mode)."""
        t0 = self.sec["latticeB"]
        mel = [3, 5, 7, 8, 7, 5, 3, 2, 8, 7, 5, 3]
        for b in range(12):
            base = t0 + b * BAR
            m = self.deg(AEOLIAN, mel[b], A1 + 12)
            for i in range(16):
                t = base + i * 0.25
                if i % 8 in (2, 5, 7):
                    self.gtr(t, 0.22, m if i % 8 != 7 else m + 3, 106, "pm")
                    self.bassn(t, 0.2, A1 - 12, 104, "bstac")
                else:
                    self.gtr(t, 0.13, A1, 100, "pm")
                    self.bassn(t, 0.13, A1 - 12, 104, "bstac")
                self.drum(t, "kick", 112, dur=0.08)
        self.blast_switch(t0, 4)
        self.blast_hyper(t0 + bars(4), 4)
        self.blast_trad(t0 + bars(8), 4, cym="china")
        t = t0
        for d, dur in THEME:
            s = dur * (48.0 / 14.0)
            self.lead.add(t, s * 0.95, self.deg(HARM, d, A1 + 24), 108, "vib")
            self.lead.add(t, s * 0.95, self.deg(HARM, d + 2, A1 + 24), 98,
                          "harm", "vib")
            t += s
        for b in range(0, 12, 2):
            for p in (57, 64, 69):
                self.choir.add(t0 + bars(b), bars(2), p, 62 + b * 2, "sus")

    def twinC(self):
        """C: harmonized twin-guitar 16th runs (3rds), string-skip answers."""
        t0 = self.sec["twinC"]
        for b in range(10):
            base = t0 + b * BAR
            if b % 2 == 0:
                for i in range(16):
                    d = [0, 2, 3, 5, 7, 5, 3, 2][i % 8] + (i // 8) * 2
                    self.gtr(base + i * 0.25, 0.22,
                             self.deg(AEOLIAN, d, A1 + 12), 104, "legato",
                             "fast", both=False)
                    self.gtr(base + i * 0.25, 0.22,
                             self.deg(AEOLIAN, d + 2, A1 + 12), 100, "legato",
                             "fast", both=False, right=True)
                    self.bassn(base + i * 0.25, 0.2, A1 - 12, 102, "bstac")
            else:
                for i in range(8):
                    lo = self.deg(AEOLIAN, i % 4, A1)
                    hi = lo + (16 if i % 2 == 0 else 15)
                    self.gtr(base + i * 0.5, 0.4, lo if i % 2 == 0 else hi,
                             106, "sus")
                    self.bassn(base + i * 0.5, 0.4, lo - 12, 104, "bpluck")
        self.blast_trad(t0, 3)
        self.quad_fill(t0 + bars(3) + 3.0)
        self.blast_gravity(t0 + bars(4), 2)
        self.blast_trad(t0 + bars(6), 2, cym="china")
        self.blast_switch(t0 + bars(8), 2)

    def gallop(self):
        """Blackened gallop bridge (Netherwalker): tremolo + choir wall."""
        t0 = self.sec["gallop"]
        self.drum(t0, "crash2", 114)
        prog = [0, 8, 5, 7, 3]
        for b in range(10):
            base = t0 + b * BAR
            root = self.deg(AEOLIAN, prog[(b // 2) % 5], A1 + 12)
            for i in range(16):
                v = 100 + (0 if i % 2 == 0 else -14) + [0, -4, -2, -6][i % 4]
                self.gtr(base + i * 0.25, 0.24, root, max(40, v), "trem")
            for i in range(4):
                self.bassn(base + i * 1.0, 0.9, root - 12, 102, "bsus")
        self.blast_hyper(t0, 4)
        self.blast_trad(t0 + bars(4), 4)
        self.blast_hyper(t0 + bars(8), 2)
        for b in range(0, 10, 2):
            for p in (57, 61, 64, 69):
                self.choir.add(t0 + bars(b), bars(2), p, 78, "sus")
            self.strings.add(t0 + bars(b), bars(2), 45 + prog[(b // 2) % 5],
                             80, "sus")

    def crownfall(self):
        """THE tavern-leveler: half-time feel breakdown at 87.5, stutter
        masks as breakdown grids, orchestral stabs on anchors, subs."""
        t0 = self.sec["crownfall"]
        self.fx.add(t0, 0.9, 0, 116, "impact")
        self.sub.add(t0, 3.0, A1 - 24, 126)
        masks = ["X..X..X.X.......", "X..X..X.X....X..",
                 "X.....X...X.....", "X..X..X.X..XX...",
                 "X..X..X.X.......", "X..X..XX..X..X..",
                 "X.....X...XX....", "X..X..X.XX.XX.X."]
        for b, mask in enumerate(masks):
            base = t0 + b * BAR
            self.stutter(base, mask, A1 if b < 6 else E1, vel=116, china=True)
            self.drum(base + 2.0, "snare", 123)
            if b in (1, 5):
                self.gtr(base + 3.5, 0.4, A1 + 24, 118, "pinch")
            if b == 3:
                self.bass_fill(base + 3.0, A1, beats=1.0)
            if b in (0, 2, 4, 6):
                self.sub.add(base, 1.6, (A1 if b < 6 else E1) - 24, 120)
            for i, c in enumerate(mask):
                if c == "X" and i % 2 == 0:
                    self.strings_stac.add(base + i * 0.25, 0.3, 45, 100, "stac")
                    self.strings_stac.add(base + i * 0.25, 0.3, 57, 96, "stac")
        # bars 9-10: stop-time — ring + silence + vocal hole + pickup
        t8 = t0 + bars(8)
        for tr in (self.gtr_l, self.gtr_r):
            tr.add(t8, 1.5, E1, 120, "sus")
            tr.add(t8, 1.5, E1 + 13, 112, "sus")
        self.bassn(t8, 1.5, E1, 116, "bsus")
        self.drum(t8, "kick", 124); self.drum(t8, "crash2_stop", 118)
        self.sub.add(t8, 3.5, E1 - 12, 127)
        for k, tt in enumerate((3.0, 3.25, 3.5, 3.75)):
            self.gtr(t0 + bars(9) + tt, 0.12, A1, 100 + k * 5, "pm")
            self.bassn(t0 + bars(9) + tt, 0.12, A1 - 12, 106, "bstac")
            self.drum(t0 + bars(9) + tt, "kick", 114, dur=0.08)

    def solo(self):
        """Sweep solo over pedal lattice: dim7 ascending sextuplets with
        tapped extensions, harmonic-minor runs, one screaming bend."""
        t0 = self.sec["solo"]
        self.drum(t0, "crash1", 114)
        for b in range(8):
            base = t0 + b * BAR
            for i in (0, 3, 6, 9, 12, 14):
                self.gtr(base + i * 0.25, 0.2, A1, 98, "pm")
                self.bassn(base + i * 0.25, 0.2, A1 - 12, 102, "bstac")
                self.drum(base + i * 0.25, "kick", 112, dur=0.08)
        self.blast_trad(t0, 4, cym="ride_bell")
        self.blast_hyper(t0 + bars(4), 4)
        t = t0
        for rep in range(3):                       # dim7 sweep, m3 pivots
            for i in range(12):
                p = A1 + 24 + DIM7[i % 4] + (i // 4) * 12 + rep * 3
                self.lead.add(t + i / 6.0, 0.15, p, 104 + (i % 4 == 0) * 10,
                              "fast")
            t += 2.0
            for i in range(11, -1, -1):
                p = A1 + 24 + DIM7[i % 4] + (i // 4) * 12 + rep * 3
                self.lead.add(t + (11 - i) / 6.0, 0.15, p, 100, "fast")
            t += 2.0
        run = [self.deg(HARM, i, A1 + 24) for i in range(14)]
        for i, p in enumerate(run):
            self.lead.add(t + i * 0.25, 0.24, p, 102 + (i % 4 == 0) * 10,
                          "fast")
        t += 3.5
        self.lead.add(t, 0.5, run[-1], 108, "fast")
        t = t0 + bars(6)
        self.lead.add(t, bars(1), A1 + 36 - 2, 118, "bend_wh")
        self.lead.add(t + bars(1), bars(0.9), A1 + 36, 116, "vib")

    def tapcanon(self):
        """The circus act: 3-voice tap canon — gtr1 on the beat, gtr2 an
        8th behind, bass the third voice below."""
        t0 = self.sec["tapcanon"]
        cell = [0, 4, 7, 0, 4, 7]           # tap-pull-hammer triplet cells
        for b in range(4):
            base = t0 + b * BAR
            broot = self.deg(AEOLIAN, [0, 5, 6, 4][b], A1 + 12)
            for i in range(12):
                p = broot + cell[i % 6] + 12 * (i // 6 % 2)
                self.gtr(base + i / 3.0, 0.28, p + 12, 102, "legato", "fast",
                         both=False)
                self.gtr(base + i / 3.0 + 0.5, 0.28, p + 7 + 12, 96,
                         "legato", "fast", both=False, right=True)
                self.bassn(base + i / 3.0, 0.28, p - 12, 106, "bpluck")
            self.drum(base, "china", 104)
            self.drum(base + 2.0, "snare", 116)
            for q in range(4):
                self.drum(base + q, "kick", 110, dur=0.1)
        self.quad_fill(t0 + bars(3) + 3.0)

    def recapA(self):
        """A' recap: same burst rhythm, transposed up a minor 3rd (the one
        allowed mutation), half-time drums first 4 bars then hyper."""
        t0 = self.sec["recapA"]
        self.drum(t0, "crash1", 116)
        walk = [0, 0, 7, 8, 7, 3, 5, 3]
        for b in range(8):
            base = t0 + b * BAR
            root = self.deg(AEOLIAN, walk[b], A1 + 3)
            if b % 4 < 3:
                self.burst(base, 5, root, kick=False)
                self.gtr(base + 0.75, 0.14, A1 + 3, 104, "pm")
                self.bassn(base + 0.75, 0.16, A1 - 9, 108, "bstac")
                self.burst(base + 1.0, 3, root, kick=False)
                self.burst(base + 1.75, 7, root, kick=False)
                self.burst(base + 3.0, 5,
                           self.deg(AEOLIAN, walk[b] + 1, A1 + 3), kick=False)
            else:
                self.stutter(base, "XX.XX.X.", A1 + 3, china=True)
                self.stutter(base + 2.0, "XXX.X.X.", A1 + 3, china=True)
        for b in range(4):                     # half-time under full-speed riff
            self.drum(t0 + bars(b) + 2.0, "snare", 122)
            for q in (0.0, 1.0, 2.0, 3.0):
                self.drum(t0 + bars(b) + q, "china", 104)
            for i in range(16):
                self.drum(t0 + bars(b) + i * 0.25, "kick", 110, dur=0.08)
        self.blast_hyper(t0 + bars(4), 4)

    def reverie(self):
        """The breath: THEME rubato, clean, with choir — 4 bars at 80."""
        t0 = self.sec["reverie"]
        t = t0
        for d, dur in THEME:
            s = dur * (16.0 / 14.0)
            self.clean.add(t, s * 0.95, self.deg(HARM, d, A1 + 24), 84,
                           "clean")
            self.clean.add(t + s * 0.4, s * 0.55,
                           self.deg(HARM, d - 5, A1 + 12), 68, "clean")
            t += s
        for p in (57, 64, 69):
            self.choir.add(t0, bars(4), p, 66, "sus")
        self.fx.add(t0 + bars(3), bars(1), 0, 100, "riser")

    def climax(self):
        """D at 200 ('400'): fastest material — THEME at speed in bursts,
        gravity blast peaks, ends on stabs into the hard cut."""
        t0 = self.sec["climax"]
        self.drum(t0, "crash1", 118); self.drum(t0, "china", 114)
        walk = [0, 7, 8, 7, 3, 5, 3, 2, 0, -1]
        for b in range(12):
            base = t0 + b * BAR
            root = self.deg(AEOLIAN, walk[b % 10], A1)
            self.burst(base, 7, root, kick=False)
            self.burst(base + 1.0, 5, root + 12, kick=False)
            self.gtr(base + 2.0, 0.14, A1, 106, "pm")
            self.bassn(base + 2.0, 0.16, A1 - 12, 108, "bstac")
            self.burst(base + 2.25, 7, root, kick=False,
                       trill="trill_wt" if b % 3 == 2 else None)
        self.blast_hyper(t0, 4)
        self.blast_gravity(t0 + bars(4), 2)
        self.blast_hyper(t0 + bars(6), 2)
        self.blast_gravity(t0 + bars(8), 2)
        self.blast_hyper(t0 + bars(10), 2)
        for b in range(0, 12, 2):
            for p in (57, 64, 69):
                self.choir.add(t0 + bars(b), bars(2), p, 82, "sus")
            self.strings_stac.add(t0 + bars(b), 0.3, 69, 104, "stac")
        # bars 11-12: final stabs + THE gap + last hit
        t10 = t0 + bars(12)
        for tt in (0.0, 0.75, 1.5):
            self.stab(t10 + tt, A1, cluster=13 if tt == 1.5 else None)
        self.hard_stop(t10 + 1.9)
        self.bass_fill(t10 + 2.5, A1, beats=1.5)
        self.stab(t10 + BAR, E1, cluster=6, dur=0.5)
        self.stab(t10 + BAR + 2.0, A1, dur=0.3)
        self.hard_stop(t10 + BAR + 2.4)
        self.sub.add(t10 + BAR + 2.0, 2.0, A1 - 24, 124)

    def outro_(self):
        """Archspire hard cut: one bar of silence, one final unison hit."""
        t0 = self.sec["outro"]
        self.stab(t0 + bars(1), A1, cluster=13, dur=1.2, china=True)
        self.drum(t0 + bars(1), "crash1", 120)
        self.sub.add(t0 + bars(1), 2.5, A1 - 24, 120)
        self.fx.add(t0 + bars(1), 2.5, A1, 100, "dive")


def build_song():
    c = Crown()
    score = c.build()
    return score, c.sec
