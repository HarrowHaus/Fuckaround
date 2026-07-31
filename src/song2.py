"""SIX FEET IS NOT ENOUGH — the all-breakdown song.

One long breakdown, seven movements, built verbatim from
docs/07-breakdown-anatomy.md: engineered emptiness, the anchor law, mutation
operators, a tempo staircase (84 -> 72 -> 62 quarter-time), a pitch staircase
(G#1 -> F#1 -> F1, one-way ratchet), a valley, a false ending, and a final
form that is the nastiest variation, not the busiest. First sound = last
sound (bookend: one lone chug + feedback).

Movement map (bars, 4/4):
  intro        4   @84  feedback + 3 lone unaccompanied chugs (the motif)
  bounce      12   @84  3+3+2 family, china quarters, snare 3, swing 54%
  lurch       12   @84  unequal-gap grids, snare on 4, b9 ring, callout bar
  sludge      12   @72  drop #1: sludge-bounce hybrid, choir enters, stutters
  slam         6   @72  ride-bell swagger detour, scrapes, ends full-bar choke
  valley       8   @72  drums-only -> drone + lone chugs, NO cymbals
  false_end    4   @66  rit ring-out, feedback, near-silence, lone 808 tail
  final       16   @62  QUARTER-TIME, root drops to F1, orch stabs on anchors,
                        late-feel, full stop w/ a-cappella hole, dive
  outro        4   @56  density halves per bar -> one lone chug + feedback
"""

from score import Score, Note, humanize
import random

random.seed(41)

TITLE = "six_feet_is_not_enough"

ROOT_A = 32   # G#1 — movements I-II
ROOT_B = 30   # F#1 — movements III-V (pitch staircase step 1)
ROOT_C = 29   # F1  — final form (step 2; one-way ratchet)

BAR = 4.0


def bars(n):
    return n * BAR


class Breakdown:
    def __init__(self):
        self.s = Score()
        self.s.tempo_map = []
        lengths = dict(intro=4, bounce=12, lurch=12, sludge=12, slam=6,
                       valley=8, false_end=4, final=16, outro=4)
        self.sec = {}
        pos = 0.0
        for k, v in lengths.items():
            self.sec[k] = pos
            pos += bars(v)
        self.total = pos
        self.s.set_tempo(0.0, 84.0)
        self.s.set_tempo(self.sec["sludge"], 72.0)
        # ritardando into the false ending (engine dying: stepped -5..8%)
        self.s.set_tempo(self.sec["false_end"], 68.0)
        self.s.set_tempo(self.sec["false_end"] + bars(2), 64.0)
        self.s.set_tempo(self.sec["final"], 62.0)
        self.s.set_tempo(self.sec["outro"], 56.0)

        for nm in ("gtr_l", "gtr_r", "lead", "clean", "bass", "drums",
                   "strings", "strings_stac", "choir", "subdrop", "fx"):
            setattr(self, nm if nm != "subdrop" else "sub", self.s.track(nm))
        self.drums = self.s.track("drums")

    # ------------------------------------------------------------- helpers
    def drum(self, t, name, vel, dur=0.25, grid=False):
        tags = {name, "grid"} if grid else {name}
        self.drums.notes.append(Note(t, dur, 0, vel, frozenset(tags)))

    def gtr(self, t, dur, pitch, vel, *tags):
        for tr in (self.gtr_l, self.gtr_r):
            tr.add(t, dur, pitch, vel, *tags)

    def bassn(self, t, dur, pitch, vel, *tags):
        self.bass.add(t, dur, max(28, pitch), min(127, vel), *tags)

    def feedback(self, t, dur, root, interval=6, vel=76):
        """Feedback bed: tritone (or b2) squeal two octaves up, lead track."""
        self.lead.add(t, dur, root + 24 + interval, vel, "vib")

    def sub808(self, t, root, dur=2.5, vel=124):
        self.sub.add(t, dur, root - 12, vel)

    # ------------------------------------------------ the breakdown DSL
    # 16-slot rows (or 32-slot when stut=True). Symbols:
    #   .  engineered emptiness      X  chug impact (choke)     x  soft chug
    #   H  half-mute chug (djent attack, ~250ms)                O  ring-out
    #   9  b9 cluster ring           5  fifth dyad ring         T  tritone slide-down
    #   /  b2 slide up-back          #  dead-note scrape        q  squeal answer
    #   D  dive ring                 r  b2 low chug
    # Drum policy per call: snare_beat (None|2.0|3.0|'alt3'), cym
    # ('quarters'|'halves'|'accents'|'bell8'|'none'), kick mirrors impacts.
    def rows(self, t0, rows, root, snare_beat=3.0, cym="quarters",
             stut=False, late=0.0, swing=0.0, vel=112, kick=True,
             china_vel=106, bar_offset=0):
        imp = "XxHO95T/rD"
        for b, row in enumerate(rows):
            slots = 32 if stut else 16
            sdur = 0.125 if stut else 0.25
            assert len(row) == slots, f"bar {b}: {len(row)} != {slots}"
            bt = t0 + b * BAR
            for i, ch in enumerate(row):
                if ch == ".":
                    continue
                t = bt + i * sdur
                if swing and (i % 2 == 1):
                    t += swing * sdur          # delayed off-16ths
                gt = t + late                  # guitars/snare sit behind kick
                if ch == "X":
                    self.gtr(gt, sdur * 0.55, root, vel + 6, "pm")
                    self.bassn(t, sdur * 0.7, root, vel + 8, "pm")
                elif ch == "x":
                    self.gtr(gt, sdur * 0.4, root, vel - 12, "pm")
                    self.bassn(t, sdur * 0.5, root, vel - 6, "pm")
                elif ch == "H":
                    self.gtr(gt, sdur * 1.1, root, vel + 2, "pm")
                    self.bassn(t, sdur * 1.1, root, vel + 4, "pm")
                elif ch == "O":
                    self.gtr(gt, 1.75, root, vel + 10, "sus")
                    self.bassn(t, 1.75, root, vel + 8, "sus")
                elif ch == "9":
                    for tr in (self.gtr_l, self.gtr_r):
                        tr.add(gt, 1.75, root, vel + 10, "sus")
                        tr.add(gt, 1.75, root + 13, vel + 4, "sus")
                    self.bassn(t, 1.75, root, vel + 8, "sus")
                elif ch == "5":
                    for tr in (self.gtr_l, self.gtr_r):
                        tr.add(gt, 1.75, root, vel + 10, "sus")
                        tr.add(gt, 1.75, root + 7, vel + 6, "sus")
                    self.bassn(t, 1.75, root, vel + 8, "sus")
                elif ch == "T":
                    self.gtr(gt, sdur * 1.6, root + 6, vel + 8, "slide", "sus")
                    self.bassn(t, sdur * 1.4, root + 6, vel + 6, "pick")
                elif ch == "/":
                    self.gtr(gt, sdur * 1.6, root + 1, vel + 4, "slide", "sus")
                    self.bassn(t, sdur * 1.4, root + 1, vel + 4, "pick")
                elif ch == "r":
                    self.gtr(gt, sdur * 0.55, root + 1, vel + 4, "pm")
                    self.bassn(t, sdur * 0.6, root + 1, vel + 6, "pm")
                elif ch == "#":
                    self.gtr(gt, 0.07, root, 58, "pmx")
                elif ch == "q":
                    self.gtr(gt, sdur * 2.5, root + 24, 120, "pinch")
                elif ch == "D":
                    self.gtr(gt, 3.2, root, vel + 10, "dive", "sus")
                    self.bassn(t, 3.0, root, vel + 6, "sus")
                # kick mirrors every impact, grid-locked (the law)
                if kick and ch in imp and ch != "q":
                    self.drum(t, "kick", 118 if ch in "XO95TD" else 108,
                              dur=0.15, grid=True)
                    if cym == "accents" and ch in "XO95TD":
                        self.drum(t, "china", china_vel)
            # snare policy
            gb = bar_offset + b
            if snare_beat == "alt3":
                if gb % 2 == 1:
                    self.drum(bt + 2.0 + late, "snare", 124)
            elif snare_beat is not None:
                self.drum(bt + snare_beat + late, "snare", 122)
            # cymbal clock
            if cym == "quarters":
                for q in range(4):
                    self.drum(bt + q, "china", china_vel + (6 if q == 0 else 0))
            elif cym == "halves":
                for q in (0.0, 2.0):
                    self.drum(bt + q, "china", china_vel + 4)
            elif cym == "bell8":
                for e in range(8):
                    self.drum(bt + e * 0.5, "ride_bell",
                              100 if e % 2 == 0 else 88)

    # ------------------------------------------------------------ sections
    def build(self):
        self.intro(); self.bounce(); self.lurch(); self.sludge()
        self.slam(); self.valley(); self.false_end(); self.final()
        self.outro()
        # humanize: guitars/bass only; drums keep grid (kicks locked to chugs)
        self.drums.notes = humanize(self.drums.notes, vel_jitter=4,
                                    time_jitter_beats=0.005,
                                    keep_grid=("grid",))
        for tr in (self.gtr_l, self.gtr_r):
            tr.notes = humanize(tr.notes, vel_jitter=5,
                                time_jitter_beats=0.004)
            tr.notes = [Note(n.start, n.dur * random.uniform(0.94, 1.05),
                             n.pitch, n.vel, n.tags) for n in tr.notes]
        self.bass.notes = humanize(self.bass.notes, vel_jitter=4,
                                   time_jitter_beats=0.003)
        return self.s

    def intro(self):
        """Feedback + three lone unaccompanied chugs — the bookend motif."""
        t0 = self.sec["intro"]
        self.feedback(t0, bars(2), ROOT_A, interval=6)
        # the motif: 1 . . (3) | . (2and) . . — three lone hits, no drums
        for i, (tt, v) in enumerate([(0.0, 112), (2.0, 108), (5.5, 116)]):
            self.gtr(t0 + tt, 0.5, ROOT_A, v, "pm")
        self.feedback(t0 + bars(2), bars(2), ROOT_A, interval=1, vel=82)
        self.fx.add(t0 + bars(3), bars(1), 0, 96, "riser")   # pick-scrape-ish
        self.sub808(t0 + bars(3) + 3.0, ROOT_A, dur=1.5, vel=110)

    def bounce(self):
        """Movement I: 3+3+2 family at 84, china quarters, snare 3.
        Mutations every 4 bars: add hit -> displace -> stutter-double."""
        t0 = self.sec["bounce"]
        self.drum(t0, "crash1", 116); self.drum(t0, "china", 112)
        A = "X..X..X.X...X..."
        A_add = "X..X..X.X..XX..."          # op1: add one hit
        A_dis = "X..X..X..X..X..."          # op2: displace the 3rd anchor
        A_end = "X..X..X.X....../"          # op5: pitch-mutate last event
        self.rows(t0, [A, A, A_add, A_end], ROOT_A, swing=0.055)
        self.rows(t0 + bars(4), [A_dis, A_add, A_dis, "X..X..X.X..q...."],
                  ROOT_A, swing=0.055, bar_offset=4)
        # bars 9-12: stutter doubles + first quarter-stop breath (bar 12
        # beat 4 empty, sub tail through it)
        S1 = "X.......X.X.X...X...........XX.."
        S2 = "X.......X.X.X...X..........XXXX."
        self.rows(t0 + bars(8), [S1], ROOT_A, stut=True, bar_offset=8)
        self.rows(t0 + bars(9), [A_add], ROOT_A, swing=0.055, bar_offset=9)
        self.rows(t0 + bars(10), [S2], ROOT_A, stut=True, bar_offset=10)
        self.rows(t0 + bars(11), ["X..X..X.O......."], ROOT_A, bar_offset=11)
        for b in (0, 2, 4, 6, 8, 10):
            self.sub808(t0 + bars(b), ROOT_A, dur=1.8, vel=118)
        self.sub808(t0 + bars(11) + 2.0, ROOT_A, dur=3.0, vel=124)

    def lurch(self):
        """Movement II: unequal gaps, snare on 4, b9 ring, callout bar."""
        t0 = self.sec["lurch"]
        L1 = "X......X....X.O."
        L2 = "X......X..#.X../"
        L3 = "X......X....X.T."
        L4 = "X......X.#.#..9."
        self.rows(t0, [L1, L2, L1, L4], ROOT_A, snare_beat=3.5, cym="halves")
        self.rows(t0 + bars(4), [L3, L2, L1, "X......X....X.q."],
                  ROOT_A, snare_beat=3.5, cym="halves", bar_offset=4)
        # bars 9-10: guitar answers get tom replies in the gaps
        self.rows(t0 + bars(8), [L1, L2], ROOT_A, snare_beat=3.5,
                  cym="halves", bar_offset=8)
        for b in (8, 9):
            for tt, d in ((1.25, "tom2"), (1.75, "tom_floor")):
                self.drum(t0 + bars(b) + tt, d, 104)
        # bars 11-12: THE CALLOUT — drums out, one dry chug per beat + vox
        for beat in range(8):
            self.gtr(t0 + bars(10) + beat * 1.0, 0.4, ROOT_A, 104, "pm")
            self.bassn(t0 + bars(10) + beat * 1.0, 0.5, ROOT_A, 108, "pm")
        self.feedback(t0 + bars(10), bars(2), ROOT_A, interval=1, vel=74)
        self.sub808(t0, ROOT_A); self.sub808(t0 + bars(4), ROOT_A)
        self.sub808(t0 + bars(8), ROOT_A)

    def sludge(self):
        """Movement III: tempo drop #1 (84->72), pitch step G#->F#, sludge-
        bounce hybrid, choir enters, 32nd stutters appear late."""
        t0 = self.sec["sludge"]
        self.drum(t0, "crash2", 116); self.drum(t0, "china", 114)
        R = ROOT_B
        S1 = "O.......X...X..."
        S2 = "O.......X..XX../"
        S3 = "X..X....X...O..."
        S4 = "O.......X....../"
        self.rows(t0, [S1, S2, S1, S4], R, snare_beat=3.0, cym="quarters")
        self.rows(t0 + bars(4), [S3, S2, S3, "X..X....X..#.q.."], R,
                  snare_beat=3.0, cym="quarters", bar_offset=4)
        ST = "X...........X.X.X...........XXXX"
        self.rows(t0 + bars(8), [S1], R, bar_offset=8)
        self.rows(t0 + bars(9), [ST], R, stut=True, bar_offset=9)
        self.rows(t0 + bars(10), [S4], R, bar_offset=10)
        self.rows(t0 + bars(11), ["X.X.X...X.X.O..."], R, bar_offset=11)
        # choir layer (single dimension added this movement)
        for b in range(0, 12, 2):
            for p in (54 + (R - 30), 61 + (R - 30), 66 + (R - 30)):
                self.choir.add(t0 + bars(b), bars(2), p, 62 + b, "sus")
        for b in (0, 2, 4, 6, 8, 10):
            self.sub808(t0 + bars(b), R, dur=2.2, vel=120)

    def slam(self):
        """Movement IV: ride-bell slam detour (swing 55%), scrapes, audible
        bass; ends in a FULL-BAR choke-stop with 808 tail only."""
        t0 = self.sec["slam"]
        G1 = "X.XX..X..XX...X."
        G2 = "X.XX..X..X#.#.X."
        G3 = "X.XX..X..XX..q.."
        self.rows(t0, [G1, G2, G1, G3, G2], ROOT_B, snare_beat=3.0,
                  cym="bell8", swing=0.06)
        # bar 6: the stop — one ring choked on beat 2, then NOTHING but sub
        t5 = t0 + bars(5)
        self.gtr(t5, 1.4, ROOT_B, 120, "sus")
        self.gtr(t5, 1.4, ROOT_B + 13, 112, "sus")
        self.bassn(t5, 1.4, ROOT_B, 116, "sus")
        self.drum(t5, "kick", 122, grid=True)
        self.drum(t5, "crash1_stop", 118)
        self.sub808(t5, ROOT_B, dur=3.4, vel=126)   # empty-sub through silence
        for b in (0, 2, 4):
            self.sub808(t0 + bars(b), ROOT_B, dur=1.8, vel=116)

    def valley(self):
        """Movement V: strip everything. 2 bars drums-only, then drone +
        lone chugs, whispered space, zero cymbals."""
        t0 = self.sec["valley"]
        # bars 1-2: drums alone carry the lurch pattern (no guitars at all)
        pat = [0.0, 1.75, 3.0]
        for b in range(2):
            for tt in pat:
                self.drum(t0 + bars(b) + tt, "kick", 112, grid=True)
            self.drum(t0 + bars(b) + 3.0, "snare", 118)
            self.drum(t0 + bars(b) + 1.0, "tom_floor", 96)
            self.drum(t0 + bars(b) + 2.5, "tom_floor", 90)
        # bars 3-8: bass drone + lone guitar chugs in oceans of space
        self.bassn(t0 + bars(2), bars(4), ROOT_B - 12, 86, "sus")
        lone = [(2, 0.0, 112), (2, 2.5, 100), (3, 1.0, 106), (4, 0.0, 114),
                (4, 3.5, 96), (5, 2.0, 108), (6, 0.0, 116), (6, 1.75, 104),
                (6, 3.5, 100)]
        for b, tt, v in lone:
            self.gtr(t0 + bars(b) + tt, 0.45, ROOT_B, v, "pm")
            self.drum(t0 + bars(b) + tt, "kick", 104, grid=True)
        for b in range(2, 7):
            self.drum(t0 + bars(b) + (3.0 if b % 2 == 0 else 1.0),
                      "tom_floor", 84)
        self.feedback(t0 + bars(4), bars(3), ROOT_B, interval=6, vel=68)
        # bar 8: rebuild pickup — kick doubles under a ring (motion in stillness)
        t7 = t0 + bars(7)
        self.gtr(t7, 1.75, ROOT_B, 112, "sus")
        self.bassn(t7, 1.75, ROOT_B, 110, "sus")
        for tt in (0.0, 0.75, 1.0, 2.0, 2.75, 3.0, 3.5, 3.75):
            self.drum(t7 + tt, "kick", 110, grid=True)
        self.drum(t7 + 3.5, "snare", 100)
        self.drum(t7 + 3.75, "snare", 112)

    def false_end(self):
        """Ending-shaped gesture: rit ring-out, feedback, near-silence with a
        lone 808 tail. Then the real thing."""
        t0 = self.sec["false_end"]
        self.gtr(t0, 3.0, ROOT_B, 118, "sus")
        self.gtr(t0, 3.0, ROOT_B + 7, 110, "sus")
        self.bassn(t0, 3.0, ROOT_B, 112, "sus")
        self.drum(t0, "china", 116); self.drum(t0, "kick", 122, grid=True)
        self.gtr(t0 + bars(1), 2.8, ROOT_B, 108, "fall")
        self.feedback(t0 + bars(1), bars(2.5), ROOT_B, interval=1, vel=78)
        self.sub808(t0 + bars(2), ROOT_B, dur=6.0, vel=122)  # the lone tail
        self.fx.add(t0 + bars(3), bars(1), 0, 104, "riser")

    def final(self):
        """FINAL FORM at 62 quarter-time, root drops to F1: sparsest grid,
        biggest hits, orch stabs on anchors only, late-feel throughout,
        a-cappella hole at bar 10, dive out. Nastiest, not busiest."""
        t0 = self.sec["final"]
        R = ROOT_C
        late = 0.028   # ~+27ms behind the kick at 62 BPM
        self.fx.add(t0, 0.9, 0, 118, "impact")
        self.sub808(t0, R, dur=3.5, vel=127)
        F1 = "X.......X.....X."
        F2 = "X.......X...../."
        F3 = "X.......X..X..T."
        F4 = "O...........XXX."
        self.rows(t0, [F1, F2, F1, F4], R, snare_beat="alt3", cym="accents",
                  late=late, vel=116)
        self.rows(t0 + bars(4), [F3, F2, F3, "O...........X.9."], R,
                  snare_beat="alt3", cym="accents", late=late, vel=116,
                  bar_offset=4)
        # orchestral stabs double ONLY the anchors; second 808 an octave down
        for b in range(8):
            self.strings_stac.add(t0 + bars(b), 0.4, 41 + (R - 29), 106, "stac")
            self.strings_stac.add(t0 + bars(b), 0.4, 53 + (R - 29), 100, "stac")
        for p in (53, 60, 65):
            self.choir.add(t0, bars(8), p + (R - 29), 88, "sus")
        # one bar of imported blast contrast (research: >=4:1 event ratio)
        t8 = t0 + bars(8)
        for i in range(16):
            self.drum(t8 + i * 0.25, "kick", 114, dur=0.1, grid=True)
            self.drum(t8 + i * 0.25 + 0.125, "snare", 92 + (i % 2) * 6)
            if i % 2 == 0:
                self.drum(t8 + i * 0.25, "china", 96)
        for i in range(16):
            self.gtr(t8 + i * 0.25, 0.24, R + 12, 96, "trem")
        # bar 10: THE HOLE — full-band stop, a-cappella space, sub only
        t9 = t0 + bars(9)
        self.gtr(t9, 0.5, R, 122, "pm")
        self.bassn(t9, 0.5, R, 118, "pm")
        self.drum(t9, "kick", 124, grid=True)
        self.drum(t9, "crash2_stop", 120)
        self.sub808(t9, R, dur=3.8, vel=127)
        # bars 11-14: rebuild, nastier (dyads on anchors, kick doubles)
        F5 = "X.......X.X...X."
        F6 = "X..X....X.X.../."
        self.rows(t0 + bars(10), [F5, F6, F5, "X..X....X.XXXXX."], R,
                  snare_beat="alt3", cym="accents", late=late, vel=118,
                  bar_offset=0)
        for b in range(10, 14):
            self.strings_stac.add(t0 + bars(b), 0.4, 41 + (R - 29), 110, "stac")
            self.sub808(t0 + bars(b), R, dur=1.6, vel=120)
        for q in (0, 2):
            self.drum(t0 + bars(13) + q, "china", 112)
        # bars 15-16: the disgusting event — b9 ring + squeal + DIVE out
        t14 = t0 + bars(14)
        for tr in (self.gtr_l, self.gtr_r):
            tr.add(t14, 1.75, R, 122, "sus")
            tr.add(t14, 1.75, R + 13, 114, "sus")
        self.bassn(t14, 1.75, R, 118, "sus")
        self.drum(t14, "kick", 124, grid=True); self.drum(t14, "china", 118)
        self.gtr(t14 + 2.0, 0.5, R + 24, 120, "pinch")
        t15 = t0 + bars(15)
        for tr in (self.gtr_l, self.gtr_r):
            tr.add(t15, 3.6, R, 122, "dive", "sus")
        self.bassn(t15, 3.4, R, 116, "sus")
        self.drum(t15, "kick", 126, grid=True)
        self.drum(t15, "china", 120)
        self.sub808(t15, R, dur=3.5, vel=127)
        self.fx.add(t15, 3.2, R, 112, "dive")

    def outro(self):
        """Density halves each bar until the bookend: one lone chug +
        the intro's feedback pitch."""
        t0 = self.sec["outro"]
        R = ROOT_C
        self.rows(t0, ["X.....X.....X..."], R, snare_beat="alt3",
                  cym="accents", vel=110)
        self.rows(t0 + bars(1), ["X.......X......."], R, snare_beat=None,
                  cym="none", vel=106)
        self.gtr(t0 + bars(2), 0.5, R, 102, "pm")
        self.drum(t0 + bars(2), "kick", 108, grid=True)
        # the last sound = the first sound
        self.gtr(t0 + bars(3), 0.6, R, 114, "pm")
        self.feedback(t0 + bars(3), bars(1), R, interval=6, vel=72)
        self.sub808(t0 + bars(3), R, dur=3.0, vel=118)


def build_song():
    b = Breakdown()
    score = b.build()
    return score, b.sec
