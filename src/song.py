"""WHERE LIGHT COMES TO DIE (v2) — blackened symphonic deathcore.

v2: the riffs actually riff. A 16th-grid riff DSL drives guitars+bass+kick
together; riffs use slides, pinch harmonics, chromatic turnarounds, 32nd
doubles, triplet bars, stop-time, whammy dives (real 24-semi pitch bend
samples), and a false-ending double tempo-drop final breakdown.

Key: G# minor (root = open drop string, Drop G# 7-string).
Tempo map: 130 core -> 100 final breakdown -> 88 for the re-drop.

Structure (bars, 4/4):
  intro          12  choir/strings leitmotif, band creeps in
  blast_a        16  blackened moving tremolo line, harmonized 2nd half
  verse1         16  the riff: chugs/slide-stabs/pinch/chromatic turnaround
  breakdown1      8  displaced grids -> triplet bars -> dive -> stop-time
  peak           24  hammer blast + leitmotif lead, bounce-grid tease
  verse2          8  slam: slide-in chords, pinch screams, gallop bursts
  bridge          8  clean arps + strings breath, riser
  solo            8  neoclassical lead over pedal chugs
  callout         2  unison stab into silence
  final_bd       20  100 BPM 8 bars -> FALSE ENDING -> 88 BPM re-drop
  outro           8  strings restate motif over ring-out
"""

from score import Score, Note, humanize, vel_ladder
import random

# ------------------------------------------------------------------ constants
ROOT = 32          # G#1
BASS_ROOT = 20
BPM_CORE = 130.0
BPM_BLAST = 160.0   # blast sections: 16th blasts here = 320-BPM equivalents
BPM_PEAK = 152.0
BPM_FINAL = 100.0
BPM_REDROP = 88.0

NAT_MINOR = [0, 2, 3, 5, 7, 8, 10]
HARM_MINOR = [0, 2, 3, 5, 7, 8, 11]
PHRYGIAN = [0, 1, 3, 5, 7, 8, 10]
PHRYG_DOM = [0, 1, 4, 5, 7, 8, 10]

CYCLE = [0, 8, 1, 7]                     # i - bVI - bII - V
CYCLE_QUAL = ["min", "maj", "maj", "maj"]

MOTIF = [(0, 2), (3, 1), (7, 1),
         (8, 2), (7, 1), (3, 1),
         (1, 2), (3, 1), (0, 1),
         (-1, 2), (0, 2)]

BAR = 4.0


def bars(n):
    return n * BAR


class Song:
    def __init__(self):
        self.s = Score()
        self.s.tempo_map = []
        self.s.set_tempo(0.0, BPM_CORE)
        lengths = dict(intro=12, blast_a=16, verse1=16, breakdown1=8,
                       peak=24, verse2=8, bridge=8, solo=8, callout=2,
                       final_bd=20, outro=8)
        self.sec = {}
        pos = 0.0
        for name, ln in lengths.items():
            self.sec[name] = pos
            pos += bars(ln)
        self.total_beats = pos
        # tempo gear changes — the deathcore way: blasts sprint, grooves sit,
        # breakdowns drop anchor
        self.s.set_tempo(self.sec["blast_a"], BPM_BLAST)
        self.s.set_tempo(self.sec["verse1"], BPM_CORE)
        self.s.set_tempo(self.sec["peak"], BPM_PEAK)
        self.s.set_tempo(self.sec["peak"] + bars(16), BPM_CORE)
        self.s.set_tempo(self.sec["final_bd"], BPM_FINAL)
        # the re-drop: even slower after the false ending
        self.s.set_tempo(self.sec["final_bd"] + bars(9), BPM_REDROP)
        # stepped ramp-down outro (the Lorna outro crawl: hard steps, not rit.)
        self.s.set_tempo(self.sec["outro"], 80.0)
        self.s.set_tempo(self.sec["outro"] + bars(4), 72.0)

        for nm in ("gtr_l", "gtr_r", "lead", "clean", "bass", "drums",
                   "strings", "strings_stac", "choir", "subdrop", "fx"):
            setattr(self, nm if nm != "subdrop" else "sub", self.s.track(nm))
        self.drums = self.s.track("drums")

    # ------------------------------------------------------------- helpers
    def drum(self, t, name, vel, dur=0.25, grid=False):
        tags = {name, "grid"} if grid else {name}
        self.drums.notes.append(Note(t, dur, 0, vel, frozenset(tags)))

    def gtr(self, t, dur, pitch, vel, *tags, track=None):
        for tr in ([self.gtr_l, self.gtr_r] if track is None else [track]):
            tr.add(t, dur, pitch, vel, *tags)

    def bassn(self, t, dur, pitch, vel, *tags):
        self.bass.add(t, dur, max(28, pitch), min(127, vel), *tags)

    # ------------------------------------------------- the riff DSL
    # one char per 16th slot (or per triplet slot when triplet=True):
    #   .  rest              c  chug (pm)          C  accent chug (pmx, hard)
    #   d  32nd double chug  x  choked dead chug   2  b2 stab   5  b5 stab
    #   3  b3 slide-stab     6  b6 stab            7  b7 stab   o  octave stab
    #   9  b9 dyad ring      p  pinch harmonic     f  slide-down fall
    #   D  dive (whammy, held; PB written by renderer)   r  low b2 chug
    def riff(self, t0, rows, root=None, kick=True, kick_snare_beat=None,
             vel=104, triplet_rows=()):
        root = ROOT if root is None else root
        stab = {"2": 1, "3": 3, "5": 6, "6": 8, "7": 10, "o": 12}
        for b, row in enumerate(rows):
            trip = b in triplet_rows
            slots = 12 if trip else 16
            sdur = (1.0 / 3.0) if trip else 0.25
            assert len(row) == slots, f"row {b} len {len(row)} != {slots}"
            for i, ch in enumerate(row):
                if ch == ".":
                    continue
                t = t0 + b * BAR + i * sdur
                if ch == "c":
                    self.gtr(t, sdur * 0.5, root, vel, "pm")
                    self.bassn(t, sdur * 0.55, root, vel + 6, "pm")
                elif ch == "C":
                    self.gtr(t, sdur * 0.5, root, vel + 10, "pmx")
                    self.bassn(t, sdur * 0.55, root, vel + 12, "pm")
                elif ch == "d":
                    for k in (0, 1):
                        self.gtr(t + k * sdur / 2, sdur * 0.3, root,
                                 vel + 4 - 6 * k, "pmx")
                        self.bassn(t + k * sdur / 2, sdur * 0.3, root,
                                   vel + 8 - 6 * k, "pm")
                        if kick:
                            self.drum(t + k * sdur / 2, "kick", 116 - 6 * k,
                                      dur=0.12, grid=True)
                elif ch == "x":
                    self.gtr(t, sdur * 0.22, root, vel - 14, "pmx")
                    self.bassn(t, sdur * 0.25, root, vel - 8, "pm")
                elif ch == "r":
                    self.gtr(t, sdur * 0.5, root + 1, vel + 6, "pmx")
                    self.bassn(t, sdur * 0.55, root + 1, vel + 10, "pm")
                elif ch in stab:
                    p = root + stab[ch]
                    tags = ("slide", "sus") if ch in ("3", "o") else ("sus",)
                    self.gtr(t, sdur * 1.6, p, vel + 12, *tags)
                    self.bassn(t, sdur * 1.4, p, vel + 10, "pick")
                elif ch == "9":
                    for tr in (self.gtr_l, self.gtr_r):
                        tr.add(t, BAR * 0.9, root, vel + 12, "sus")
                        tr.add(t, BAR * 0.9, root + 13, vel + 8, "sus")
                    self.bassn(t, BAR * 0.9, root, vel + 10, "sus")
                elif ch == "p":
                    self.gtr(t, sdur * 2.5, root + 24, 122, "pinch")
                    self.bassn(t, sdur * 0.55, root, vel + 4, "pm")
                elif ch == "f":
                    self.gtr(t, sdur * 2.0, root + 3, vel, "fall")
                elif ch == "D":
                    self.gtr(t, BAR * 0.95, root, 120, "dive", "sus")
                    self.bassn(t, BAR * 0.9, root, 116, "sus")
                if kick and ch in "cCr23567o9D":
                    self.drum(t, "kick", 118, dur=0.18, grid=True)
            if kick_snare_beat is not None:
                self.drum(t0 + b * BAR + kick_snare_beat, "snare", 123)

    # ------------------------------------------------------ drum patterns
    def blast_traditional(self, t0, nbars, cym="ride_bell", vel_s=108):
        for i in range(int(nbars * 8)):
            t = t0 + i * 0.5
            self.drum(t, "snare", vel_ladder(vel_s, i, (0, -8, -3, -10)))
            self.drum(t + 0.25, "kick", vel_ladder(104, i))
            self.drum(t, cym, 88 if i % 2 else 96)

    def blast_hammer(self, t0, nbars, cym="china", vel=110):
        for i in range(int(nbars * 8)):
            t = t0 + i * 0.5
            self.drum(t, "kick", vel_ladder(vel, i))
            self.drum(t, "snare", vel_ladder(vel - 2, i, (0, -6, -2, -8)))
            self.drum(t, cym, 84 if i % 2 else 92)

    def blast_bomb(self, t0, nbars, cym="china", vel=112):
        """K+S unison 16ths — maximum density, for escalations."""
        for i in range(int(nbars * 16)):
            t = t0 + i * 0.25
            self.drum(t, "kick", vel_ladder(vel, i))
            self.drum(t, "snare", vel_ladder(vel - 4, i, (0, -7, -3, -9)))
            if i % 2 == 0:
                self.drum(t, cym, 86 if i % 4 else 94)

    # ---- 16th-grid blasts at the 152-160 BPM sections = 300-320 equivalents
    # (grids verified against Lorna Shore / STP / SotS transcriptions:
    # kick-led alternation, flat grid-locked kicks, narrow snare band)
    def blast_trad16(self, t0, nbars, cym="ride_bell", vel_s=96, vel_k=114):
        """Traditional blast, kick-led: kick every 16th (flat, grid-locked),
        snare interleaved a 32nd behind, ride 8ths with the kick."""
        for i in range(int(nbars * 16)):
            t = t0 + i * 0.25
            self.drum(t, "kick", vel_k + (2 if i % 4 == 0 else 0),
                      dur=0.1, grid=True)
            self.drum(t + 0.125, "snare",
                      vel_ladder(vel_s, i, (4, -4, 0, -6)))
            if i % 2 == 0:
                self.drum(t, cym, 82 if i % 4 else 92)

    def blast_hammer16(self, t0, nbars, cym="china", vel=104):
        """Hammer at 16ths: kick+snare unison wall, sample-accurate unison
        (real triggers get edited to land together — no jitter)."""
        for i in range(int(nbars * 16)):
            t = t0 + i * 0.25
            self.drum(t, "kick", 114 + (2 if i % 4 == 0 else 0),
                      dur=0.1, grid=True)
            self.drum(t, "snare", vel_ladder(vel, i, (4, -3, 0, -5)),
                      grid=True)
            if i % 2 == 0:
                self.drum(t, cym, 84 if i % 4 else 93)

    def blast_bomb16(self, t0, nbars, vel=108):
        """Bomb blast: kick EVERY 32nd (flat wall, grid-locked), snare 16ths
        unison with the even kicks, china on-beat / crash off-8th
        alternating — the climax blast."""
        for i in range(int(nbars * 16)):
            t = t0 + i * 0.25
            self.drum(t, "snare", vel_ladder(vel, i, (4, -3, 0, -5)),
                      grid=True)
            self.drum(t, "kick", 114, dur=0.08, grid=True)
            self.drum(t + 0.125, "kick", 112, dur=0.08, grid=True)
            if i % 4 == 0:
                self.drum(t, "china", 104 if i % 8 else 112)
            elif i % 4 == 2:
                self.drum(t, "crash2", 98)

    def blast_gravity16(self, t0, nbars, vel=100):
        """Gravity blast: one-handed roll = snare every 32nd in strong/weak
        PAIRS (downstroke/upstroke), whole lane quieter than a normal blast;
        kick 16ths flat; free hand rides 8ths. The Olympics move."""
        for i in range(int(nbars * 16)):
            t = t0 + i * 0.25
            self.drum(t, "snare", vel_ladder(vel, i, (6, -2, 2, -4)))
            self.drum(t + 0.125, "snare",
                      vel_ladder(vel - 22, i, (0, -4, -2, -6)))
            self.drum(t, "kick", 112, dur=0.1, grid=True)
            if i % 2 == 0:
                self.drum(t, "ride", 96 if i % 4 else 106)

    def kick_burst32(self, t0, nbeats=2.0, vel=114):
        """Kick-only 32nd burst — announces a blast gear change (SotS m.22
        move). Ends ON the next downbeat; grid-locked."""
        n = int(nbeats * 8)
        for i in range(n):
            self.drum(t0 + i * 0.125, "kick", vel, dur=0.08, grid=True)

    def dkick16(self, t0, nbars, snare_beats=(1.0, 3.0), cym="ride_bell"):
        for i in range(int(nbars * 16)):
            self.drum(t0 + i * 0.25, "kick", vel_ladder(108, i))
        for b in range(int(nbars)):
            for sb in snare_beats:
                self.drum(t0 + b * BAR + sb, "snare", random.randint(114, 122))
            self.drum(t0 + b * BAR, cym, 96)
            for q in (1.0, 2.0, 3.0):
                self.drum(t0 + b * BAR + q, cym, 84)

    def fill_snare_burst(self, t0):
        for i in range(8):
            self.drum(t0 + i * 0.125, "snare", 70 + i * 7)

    def fill_cascade(self, t0):
        for j, d in enumerate(["snare", "tom1", "tom2", "tom_floor"]):
            for i in range(4):
                self.drum(t0 + j * 1.0 + i * 0.25, d, 100 + (i == 0) * 12)

    def fill_quads(self, t0):
        """One beat of KKSS quads into a downbeat."""
        for i, d in enumerate(["kick", "kick", "snare", "snare"] * 2):
            self.drum(t0 + i * 0.125, d, 104 + (i % 4 == 2) * 10)

    def fill_toms_over_wall(self, t0):
        """One bar: tom quads riding ON TOP of a continuing 32nd kick wall
        (the feet never stop — Hellfire m.27 move)."""
        for i in range(32):
            self.drum(t0 + i * 0.125, "kick", 113, dur=0.08, grid=True)
        seq = ["snare", "snare", "tom1", "tom1", "tom2", "tom2",
               "tom_floor", "tom_floor"] * 2
        for i, d in enumerate(seq):
            self.drum(t0 + i * 0.25, d, 102 + (i % 2 == 0) * 10)

    def kick_wall(self, t0, nbars):
        """Grid-locked 32nd kick wall under chugs — the tension engine."""
        for i in range(int(nbars * 32)):
            self.drum(t0 + i * 0.125, "kick", 113, dur=0.08, grid=True)

    def crash_downbeat(self, t, which="crash1", vel=112, with_kick=True):
        self.drum(t, which, vel)
        if with_kick:
            self.drum(t, "kick", 116)

    def china_quarters(self, t0, nbars, every=1.0, vel=106):
        for b in range(int(nbars)):
            q = 0.0
            while q < 4.0:
                self.drum(t0 + b * BAR + q, "china",
                          vel + (6 if q == 0 else 0))
                q += every

    def halftime_snare(self, t0, nbars, beat=2.0, vel=123):
        for b in range(int(nbars)):
            self.drum(t0 + b * BAR + beat, "snare", vel)

    # ------------------------------------------------------ orch helpers
    def motif_notes(self, t0, base_pitch, stretch=1.0, vel=100, tags=("sus",)):
        out, t = [], t0
        for off, d in MOTIF:
            out.append(Note(t, d * stretch, base_pitch + off, vel,
                            frozenset(tags)))
            t += d * stretch
        return out

    def strings_chord(self, t, dur, root_off, quality, vel=84, base=56):
        third = 4 if quality == "maj" else 3
        root = base + root_off
        for p in (root, root + 7, root + 12, root + 12 + third):
            self.strings.add(t, dur, p, vel, "sus")

    # ------------------------------------------------------------- build
    def build(self):
        self.intro(); self.blast_a(); self.verse1(); self.breakdown1()
        self.peak(); self.verse2(); self.bridge(); self.solo()
        self.callout(); self.final_breakdown(); self.outro()
        self.drums.notes = humanize(self.drums.notes, vel_jitter=5,
                                    time_jitter_beats=0.006,
                                    keep_grid=("grid",))
        for tr in (self.gtr_l, self.gtr_r):
            tr.notes = humanize(tr.notes, vel_jitter=5,
                                time_jitter_beats=0.005)
            # double-track realism: independent note-length scatter per side
            tr.notes = [Note(n.start, n.dur * random.uniform(0.92, 1.06),
                             n.pitch, n.vel, n.tags) for n in tr.notes]
        self.bass.notes = humanize(self.bass.notes, vel_jitter=4,
                                   time_jitter_beats=0.003)
        return self.s

    # ------------------------------------------------------------ sections
    def intro(self):
        t0 = self.sec["intro"]
        for rep in range(2):
            base = t0 + bars(4) * rep
            self.strings.extend(self.motif_notes(base, 68, vel=88 + rep * 8))
            for i, (roff, q) in enumerate(zip(CYCLE, CYCLE_QUAL)):
                self.strings_chord(base + bars(i), BAR, roff, q,
                                   vel=72 + rep * 10, base=44)
                third = 4 if q == "maj" else 3
                for p in (56 + roff, 56 + roff + third, 56 + roff + 7):
                    self.choir.add(base + bars(i), BAR, p, 64 + rep * 12, "sus")
        # band creeps in: low tremolo swell + tom pulse + snare-roll riser
        t = t0 + bars(8)
        for tr in (self.gtr_l, self.gtr_r):
            for i in range(4 * 16):
                v = 72 + int(i / 64 * 30) + (0 if i % 2 == 0 else -12)
                tr.add(t + i * 0.25, 0.24, 44, v, "trem")
        self.strings.extend(self.motif_notes(t, 68, vel=104))
        for i, (roff, q) in enumerate(zip(CYCLE, CYCLE_QUAL)):
            self.strings_chord(t + bars(i), BAR, roff, q, vel=92, base=44)
        for b in range(2):
            for i in range(8):
                self.drum(t + b * BAR + i * 0.5, "tom_floor", 78 + (i % 2) * 10)
        self.fill_cascade(t + bars(2))
        self.fill_snare_burst(t + bars(3) + 3.0)
        self.fx.add(t + bars(2), bars(2), 0, 100, "riser")
        self.sub.add(self.sec["blast_a"], 2.0, BASS_ROOT, 120)

    def blast_a(self):
        t0 = self.sec["blast_a"]
        self.crash_downbeat(t0)
        oct_ = 44
        # moving blackened tremolo line, 16 slots/bar of scale offsets
        line = [
            [0, 0, 0, 0, 1, 1, 1, 1, 0, 0, 0, 0, 10, 10, 8, 8],
            [0, 0, 0, 0, 3, 3, 3, 3, 1, 1, 1, 1, 0, 0, 0, 0],
            [8, 8, 8, 8, 8, 8, 8, 8, 7, 7, 7, 7, 8, 8, 8, 8],
            [1, 1, 1, 1, 1, 1, 1, 1, 7, 7, 7, 7, 7, 7, 11, 11],
        ]

        def play_line(tstart, nbars, tr, transpose=0, vel_base=98):
            for b in range(nbars):
                row = line[b % 4]
                for i in range(16):
                    t = tstart + b * BAR + i * 0.25
                    v = vel_base + (0 if i % 2 == 0 else -14) + [0, -4, -2, -6][i % 4]
                    tr.add(t, 0.24, oct_ + row[i] + transpose, max(40, v),
                           "trem")
        play_line(t0, 8, self.gtr_l)
        play_line(t0, 8, self.gtr_r)
        # 2nd half: R harmonizes a 5th up — blackened harmony
        play_line(t0 + bars(8), 8, self.gtr_l)
        play_line(t0 + bars(8), 8, self.gtr_r, transpose=7, vel_base=94)
        for b in range(16):
            row = line[b % 4]
            for i in range(8):
                self.bassn(t0 + b * BAR + i * 0.5, 0.45,
                           32 + row[i * 2], 102, "pick")
        # blast gear-box at 160: trad -> hammer -> trad -> kick-burst
        # announcement -> bomb -> GRAVITY (each gear adds limbs, per the
        # verified escalation arc)
        self.blast_trad16(t0, 4)
        self.blast_hammer16(t0 + bars(4), 2)
        self.blast_trad16(t0 + bars(6), 2, cym="china")
        self.blast_trad16(t0 + bars(8), 3.5)
        self.kick_burst32(t0 + bars(11) + 2.0, 2.0)   # gear-change spool-up
        self.blast_bomb16(t0 + bars(12), 2)
        self.blast_gravity16(t0 + bars(14), 2)     # the Olympics moment
        t = t0 + bars(8)
        for i in range(8 * 8):
            bar_i = (i // 8) % 4
            root = 68 + CYCLE[bar_i]
            fig = [0, 7, 8, 7][i % 4]
            self.strings_stac.add(t + i * 0.5, 0.4, root + fig, 92, "stac")
        for n in self.motif_notes(t, 80, stretch=2.0, vel=96):
            self.lead.notes.append(n)
        self.fill_snare_burst(t0 + bars(16) - 1.0)

    def verse1(self):
        t0 = self.sec["verse1"]
        self.crash_downbeat(t0, "china")
        # THE riff: 4-bar phrase (A A' A B-turnaround), played 4x with edits
        A_ = "c.c3c.c5c.c322p."
        A2 = "c.c3c.c5c.c366f."
        B_ = "ccccdd3.o.7.5.3."   # turnaround: chrom-ish descent + doubles
        B2 = "ccccdd3.76533221"   # full chromatic crawl variant
        for rep in range(4):
            rows = [A_, A2, A_, (B_ if rep % 2 == 0 else B2)]
            self.riff(t0 + bars(4 * rep), rows, kick=True)
        # groove drums: double-kick 16ths under, backbeat 2+4, ghosts
        self.dkick16(t0, 16, snare_beats=(1.0, 3.0))
        for b in range(16):
            for g in (1.75, 3.75):
                self.drum(t0 + b * BAR + g, "snare", random.randint(42, 62))
        self.fill_quads(t0 + bars(8) - 1.0)
        self.fill_cascade(t0 + bars(15))
        self.sub.add(self.sec["breakdown1"], 2.0, BASS_ROOT, 122)

    def breakdown1(self):
        t0 = self.sec["breakdown1"]
        # bars 1-4: displaced 16th grids w/ doubles; bar 4 ends in a DIVE
        self.riff(t0, [
            "C..C..C...dC.2f.",
            "C..C..C...dC.2..",
            "C..C..C.C..C.dd.",
            "C..C..r.r...D...",
        ], kick=True)
        self.china_quarters(t0, 4)
        self.halftime_snare(t0, 4)
        # bars 5-6: TRIPLET bars — the lurch
        self.riff(t0 + bars(4), [
            "C.CC.CC..C.C",
            "C.CC.C..CCCC",
        ], kick=True, triplet_rows=(0, 1))
        self.china_quarters(t0 + bars(4), 2)
        self.halftime_snare(t0 + bars(4), 2)
        # bar 7: bounce; bar 8: stop-time — ring, silence, 3 dry pickups
        self.riff(t0 + bars(6), ["C.C.CC..C.C.ddd."], kick=True)
        self.china_quarters(t0 + bars(6), 1)
        self.halftime_snare(t0 + bars(6), 1)
        t8 = t0 + bars(7)
        for tr in (self.gtr_l, self.gtr_r):
            tr.add(t8, 1.2, ROOT, 116, "sus")
            tr.add(t8, 1.2, ROOT + 13, 110, "sus")   # b9 ring
        self.bassn(t8, 1.2, ROOT, 114, "sus")
        self.drum(t8, "crash1_stop", 116)
        self.drum(t8, "kick", 122, grid=True)
        for k, tt in enumerate((3.0, 3.25, 3.5)):    # dry pickup chugs
            self.gtr(t8 + tt, 0.12, ROOT, 96 + k * 6, "pmx")
            self.bassn(t8 + tt, 0.12, ROOT, 104, "pm")
            self.drum(t8 + tt, "kick", 112, dur=0.12, grid=True)
        self.sub.add(t0, 2.0, BASS_ROOT, 124)
        self.sub.add(t0 + bars(4), 2.0, BASS_ROOT, 118)
        self.fx.add(t0 + bars(7), bars(1), 0, 100, "riser")

    def peak(self):
        t0 = self.sec["peak"]
        self.crash_downbeat(t0)
        oct_ = 44
        for b in range(16):
            roff = CYCLE[(b // 2) % 4]
            for i in range(16):
                t = t0 + b * BAR + i * 0.25
                v = 96 + (0 if i % 2 == 0 else -14) + [0, -4, -2, -6][i % 4]
                self.gtr_l.add(t, 0.24, oct_ + roff, max(40, v), "trem")
                self.gtr_r.add(t, 0.24, oct_ + roff + 7, max(40, v - 4), "trem")
            for i in range(8):
                self.bassn(t0 + b * BAR + i * 0.5, 0.45, 32 + roff, 104, "pick")
        for n in self.motif_notes(t0, 80, stretch=2.0, vel=112):
            self.lead.notes.append(n.tagged("vib"))
        for n in self.motif_notes(t0 + bars(8), 80, stretch=2.0, vel=114):
            self.lead.notes.append(n.tagged("vib"))
        for n in self.motif_notes(t0 + bars(8), 80, stretch=2.0, vel=104):
            off = (n.pitch - 80) % 12
            deg = HARM_MINOR.index(off) if off in HARM_MINOR else 0
            up = HARM_MINOR[(deg + 2) % 7] + (12 if (deg + 2) >= 7 else 0)
            self.lead.notes.append(Note(n.start, n.dur, 80 + up, 104,
                                        frozenset({"vib", "harm"})))
        self.blast_trad16(t0, 8)
        self.blast_hammer16(t0 + bars(8), 6)
        self.blast_bomb16(t0 + bars(14), 1)
        self.fill_toms_over_wall(t0 + bars(15))   # toms over the kick wall
        for rep in range(4):
            for i, (roff, q) in enumerate(zip(CYCLE, CYCLE_QUAL)):
                t = t0 + bars(rep * 4 + i)
                self.strings_chord(t, BAR, roff, q, vel=96, base=56)
                third = 4 if q == "maj" else 3
                for p in (68 + roff, 68 + roff + third):
                    self.choir.add(t, BAR, p, 88, "sus")
        # bars 17-24: half-time tease on a bounce grid + sustained lead
        t = t0 + bars(16)
        for rep in range(2):
            self.riff(t + bars(4 * rep), [
                "C.C.CC..C.C.CC..",
                "C.C.CC..C.C.ddC.",
                "C.C.CC..C.C.CC..",
                "C.C.CCr.r.dd2.f." if rep else "C.C.CC..CCdd22..",
            ], kick=True)
        self.china_quarters(t, 8)
        self.halftime_snare(t, 8)
        self.kick_wall(t + bars(6), 2)   # tension engine into verse2
        self.lead.add(t, bars(2), 80 + 8, 110, "vib")
        self.lead.add(t + bars(2), bars(2), 80 + 7, 108, "vib")
        self.lead.add(t + bars(4), bars(2), 80 + 3, 106, "vib")
        self.lead.add(t + bars(6), bars(1.5), 80 + 1, 110, "vib")
        self.lead.add(t + bars(7.5), bars(0.5), 80, 112, "vib")
        for i, (roff, q) in enumerate(zip(CYCLE, CYCLE_QUAL)):
            self.strings_chord(t + bars(i * 2), bars(2), roff, q, vel=80,
                               base=44)

    def verse2(self):
        t0 = self.sec["verse2"]
        self.crash_downbeat(t0, "china")
        # slam: slide-in low chords, tritone answers, pinch screams
        self.riff(t0, [
            "3...C...5...C.p.",
            "3...C...5...CCCC",
            "3...C...5...C.p.",
        ], kick=True)
        self.china_quarters(t0, 3, every=1.0)
        self.halftime_snare(t0, 3)
        # bar 4: b9 ring + snare burst
        self.riff(t0 + bars(3), ["9..............."], kick=True)
        self.drum(t0 + bars(3), "china", 114)
        self.fill_snare_burst(t0 + bars(3) + 3.0)
        # bars 5-7: gallop w/ kick triplets, china quarters
        for b in range(3):
            for beat in range(4):
                t = t0 + bars(4 + b) + beat
                self.gtr(t, 0.4, ROOT, 106, "pm")
                self.gtr(t + 0.5, 0.2, ROOT, 96, "pm")
                self.gtr(t + 0.75, 0.2, ROOT, 92, "pm")
                self.bassn(t, 0.45, ROOT, 112, "pm")
                self.bassn(t + 0.5, 0.2, ROOT, 102, "pm")
                self.bassn(t + 0.75, 0.2, ROOT, 98, "pm")
                for kt in (0.0, 0.5, 0.75):
                    self.drum(t + kt, "kick", 114, dur=0.15, grid=True)
            self.china_quarters(t0 + bars(4 + b), 1)
            self.halftime_snare(t0 + bars(4 + b), 1)
        # bar 8: b9 ring + quads into the bridge
        self.riff(t0 + bars(7), ["9..............."], kick=True)
        self.drum(t0 + bars(7), "crash2", 114)
        self.fill_quads(t0 + bars(7) + 3.0)

    def bridge(self):
        t0 = self.sec["bridge"]
        for rep in range(2):
            for i, (roff, q) in enumerate(zip(CYCLE, CYCLE_QUAL)):
                t = t0 + bars(rep * 4 + i)
                third = 4 if q == "maj" else 3
                arp = [56 + roff, 56 + roff + 7, 68 + roff, 68 + roff + third,
                       68 + roff + 7, 68 + roff + third, 68 + roff,
                       56 + roff + 7]
                for j, p in enumerate(arp):
                    self.clean.add(t + j * 0.5, 0.9, p, 78 + (j == 0) * 10,
                                   "clean")
                self.strings_chord(t, BAR, roff, q, vel=64, base=44)
                self.bassn(t, BAR, 32 + roff, 72, "sus")
        self.fx.add(t0 + bars(6), bars(2), 0, 100, "riser")
        for i in range(32):
            self.drum(t0 + bars(6) + i * 0.25, "snare", 40 + int(i * 2.5))

    def solo(self):
        t0 = self.sec["solo"]
        self.crash_downbeat(t0)
        # rhythm bed: 3+3+3+3+2+2 pedal grid (more push than straight 16ths)
        for b in range(8):
            for i in (0, 3, 6, 9, 12, 14):
                t = t0 + b * BAR + i * 0.25
                self.gtr(t, 0.4, ROOT, 96, "pm")
                self.bassn(t, 0.45, ROOT, 104, "pm")
        self.dkick16(t0, 8, snare_beats=(1.0, 3.0), cym="crash2")
        t = t0
        run = [56 + HARM_MINOR[i % 7] + 12 * (i // 7) for i in range(15)]
        for i, p in enumerate(run):
            self.lead.add(t + i * 0.25, 0.24, p, 100 + (i % 4 == 0) * 12,
                          "fast")
        t += bars(2)
        dim = [80 + x for x in (0, -3, -6, -9, -12, -15, -18, -21)]
        for i, p in enumerate(dim):
            self.lead.add(t + i * 0.5, 0.45, p, 108, "fast")
        t += bars(2)
        for i in range(16):
            p = 68 + (1 if i % 2 else 0)
            self.lead.add(t + i * 0.25, 0.22, p, 96 + (i % 4 == 0) * 10,
                          "fast")
        t += bars(2)
        climb = [68 + PHRYG_DOM[i % 7] + 12 * (i // 7) for i in range(8)]
        for i, p in enumerate(climb):
            self.lead.add(t + i * 0.5, 0.45, p, 104, "fast")
        self.lead.add(t + bars(1), bars(1), 92, 118, "vib")

    def callout(self):
        t0 = self.sec["callout"]
        for tr in (self.gtr_l, self.gtr_r):
            tr.add(t0, 1.0, ROOT, 120, "sus")
            tr.add(t0, 1.0, ROOT + 12, 116, "sus")
        self.bassn(t0, 1.0, ROOT, 118, "sus")
        self.drum(t0, "china", 118)
        self.drum(t0, "kick", 122)
        self.fx.add(t0 + bars(1), bars(1), 0, 110, "riser")
        self.sub.add(self.sec["final_bd"], 3.0, 18, 127)

    def final_breakdown(self):
        t0 = self.sec["final_bd"]
        R = ROOT - 2   # F# — the detune
        # ---- phase 1 (100 BPM, bars 1-8): displaced grids, escalating
        self.riff(t0, [
            "C.....C...C.....",
            "C.....C...C..2f.",
            "C.....C...C.....",
            "C.....C..dd..D..",
            "C..C....dC..C...",
            "C..C....dC..C2..",
            "C..C....dC..CC..",
            "C..C..dd..dd2.f.",
        ], root=R, kick=True)
        self.china_quarters(t0, 4, every=2.0, vel=110)
        self.china_quarters(t0 + bars(4), 4, every=1.0)
        for b in range(8):
            if b % 2 == 1:
                self.drum(t0 + b * BAR + 2.0, "snare", 123)
        # orchestral stabs sync bars 5-8
        for b in range(4, 8):
            for i in range(16):
                pass
        for b, row in enumerate(["C..C....dC..C...", "C..C....dC..C2..",
                                 "C..C....dC..CC..", "C..C..dd..dd2.f."]):
            for i, c in enumerate(row):
                if c in "Cd2":
                    t = t0 + bars(4 + b) + i * 0.25
                    for p in (54, 66):
                        self.strings_stac.add(t, 0.3, p, 104, "stac")
        # ---- FALSE ENDING: bar 9 = silence + feedback swell
        t9 = t0 + bars(8)
        self.gtr(t9, bars(1), R + 24, 70, "sus", track=self.gtr_l)
        self.fx.add(t9 + bars(0.5), bars(0.5), 0, 90, "riser")
        # ---- phase 2: RE-DROP at 88 BPM (bars 10-20), quarter-time filth
        t = t0 + bars(9)
        self.sub.add(t, 3.0, 18, 127)
        self.fx.add(t, 0.9, 0, 118, "impact")
        self.riff(t, [
            "C.......C...C...",
            "C.......C..dC.r.",
            "C.......C...C...",
            "C....ddC...dd.D.",
        ], root=R, kick=True)
        self.china_quarters(t, 4, every=2.0, vel=112)
        self.halftime_snare(t, 4, beat=2.0, vel=125)
        # leitmotif lead over the filth — beauty over brutality
        for n in self.motif_notes(t, 78, stretch=2.0, vel=116):
            self.lead.notes.append(n.tagged("vib"))
        # escalation: bounce grids + choir + bomb-blast burst
        t = t0 + bars(13)
        self.riff(t, [
            "C.C.CC..C.C.CCC.",
            "C.C.CC..C.C.ddd.",
            "CC..CC..CC..dddd",
        ], root=R, kick=True)
        self.china_quarters(t, 3, every=1.0)
        self.halftime_snare(t, 3)
        for i, (roff, q) in enumerate(zip(CYCLE, CYCLE_QUAL)):
            third = 4 if q == "maj" else 3
            tt = t0 + bars(12 + i * 2)
            for p in (64 + roff, 64 + roff + third, 64 + roff + 7):
                self.choir.add(tt, bars(2), p, 92 + i * 6, "sus")
        self.blast_bomb16(t0 + bars(16), 1)   # bomb chaos: 32nd kicks at 88
        self.riff(t0 + bars(16), ["................"], root=R, kick=False)
        for tr in (self.gtr_l, self.gtr_r):
            for i in range(16):
                tr.add(t0 + bars(16) + i * 0.25, 0.24, R + 24, 100, "trem")
        # bars 18-19: unison quarters, pinch layered
        self.riff(t0 + bars(17), [
            "C...C...C...C...",
            "C...C...C...C...",
        ], root=R, kick=True)
        for q in range(8):
            self.drum(t0 + bars(17) + q, "china", 116)
            if q % 2 == 0:
                self.lead.add(t0 + bars(17) + q, 0.9, R + 36, 118, "pinch")
        self.halftime_snare(t0 + bars(17), 2, vel=126)
        # bar 20: final hit -> ring -> dive out
        t_end = t0 + bars(19)
        for tr in (self.gtr_l, self.gtr_r):
            tr.add(t_end, 3.6, R, 122, "dive", "sus")
        self.bassn(t_end, 3.4, R, 118, "sus")
        self.drum(t_end, "china", 120)
        self.drum(t_end, "kick", 124)
        self.sub.add(t_end, 2.5, 18, 126)
        self.fx.add(t_end, 3.0, R, 110, "dive")

    def outro(self):
        t0 = self.sec["outro"]
        self.strings.extend(self.motif_notes(t0, 66, stretch=1.5, vel=92))
        for p in (30, 42, 49):
            self.gtr_l.add(t0, bars(6), p, 82, "sus")
            self.gtr_r.add(t0, bars(6), p, 82, "sus")
        self.bassn(t0, bars(6), 30, 84, "sus")
        self.strings_chord(t0 + bars(4), bars(4), -2, "min", vel=72, base=44)
        for p in (64, 67, 71):
            self.choir.add(t0 + bars(4), bars(4), p, 70, "sus")


def build_song():
    song = Song()
    score = song.build()
    return score, song.sec
