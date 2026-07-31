"""WHERE LIGHT COMES TO DIE — blackened symphonic deathcore, 2026 blueprint.

Key: G# minor (root = open drop string, Drop G# 7-string convention).
Tempo map: 130 BPM core (blasts feel ~260), final breakdown drops to 100 BPM
AND detunes a whole step to F# (the Whitechapel 'Hymns in Dissonance' move).

Structure (bars, 4/4):
  intro          12  choir/strings state the leitmotif, drums enter late
  blast_a        16  blackened tremolo, i-bVI-bII-V, traditional blast
  verse1         16  Phrygian pedal riff 3+3+3+3+2+2, double kick
  breakdown1      8  half-time bounce, sub drop
  peak           24  hammer blast + leitmotif lead (harmonized), then tease
  verse2          8  slam groove, tritone stabs, b9 cluster rings
  bridge          8  ambient breath: clean arps, strings, riser
  solo            8  harmonic minor / diminished neoclassical lead
  callout         2  unison stab into silence (vocal callout space)
  final_bd       20  100 BPM, detuned to F#, escalating 4-bar layers
  outro           8  strings restate motif over ring-out
"""

from score import Score, Note, humanize, vel_ladder
import random

# ------------------------------------------------------------------ constants
ROOT = 32          # G#1, open 7th string in Drop G#
BASS_ROOT = 20     # G#0
BPM_CORE = 130.0
BPM_FINAL = 100.0

NAT_MINOR = [0, 2, 3, 5, 7, 8, 10]
HARM_MINOR = [0, 2, 3, 5, 7, 8, 11]
PHRYGIAN = [0, 1, 3, 5, 7, 8, 10]
PHRYG_DOM = [0, 1, 4, 5, 7, 8, 10]

# chord cycle of the song: i - bVI - bII - V  (G#m - E - A - D#)
CYCLE = [0, 8, 1, 7]
CYCLE_QUAL = ["min", "maj", "maj", "maj"]

# Leitmotif: degrees over 4 bars — the b2 in bar 3 is the blackened hook.
# (offset_semitones, duration_beats)
MOTIF = [(0, 2), (3, 1), (7, 1),
         (8, 2), (7, 1), (3, 1),
         (1, 2), (3, 1), (0, 1),
         (-1, 2), (0, 2)]

BAR = 4.0  # beats


def bars(n):
    return n * BAR


class Song:
    def __init__(self):
        self.s = Score()
        self.s.tempo_map = []
        self.s.set_tempo(0.0, BPM_CORE)
        # section start beats
        lengths = dict(intro=12, blast_a=16, verse1=16, breakdown1=8,
                       peak=24, verse2=8, bridge=8, solo=8, callout=2,
                       final_bd=20, outro=8)
        self.sec = {}
        pos = 0.0
        for name, ln in lengths.items():
            self.sec[name] = pos
            pos += bars(ln)
        self.total_beats = pos
        self.s.set_tempo(self.sec["final_bd"], BPM_FINAL)

        self.gtr_l = self.s.track("gtr_l")
        self.gtr_r = self.s.track("gtr_r")
        self.lead = self.s.track("lead")
        self.clean = self.s.track("clean")
        self.bass = self.s.track("bass")
        self.drums = self.s.track("drums")
        self.strings = self.s.track("strings")
        self.strings_stac = self.s.track("strings_stac")
        self.choir = self.s.track("choir")
        self.sub = self.s.track("subdrop")
        self.fx = self.s.track("fx")

    # ------------------------------------------------------------- helpers
    def drum(self, t, name, vel, dur=0.25):
        self.drums.notes.append(Note(t, dur, 0, vel, frozenset({name})))

    def chug(self, t, dur, pitch, vel, both=True):
        """Palm-muted chug on both rhythm guitars + bass lock."""
        for tr in (self.gtr_l, self.gtr_r):
            tr.add(t, dur * 0.55, pitch, vel, "pm")
        self.bass.add(t, dur * 0.6, pitch, min(127, vel + 5), "pm")

    def ring(self, t, dur, pitches, vel):
        """Open ringing chord on both guitars + bass root."""
        for tr in (self.gtr_l, self.gtr_r):
            for p in pitches:
                tr.add(t, dur, p, vel, "sus")
        self.bass.add(t, dur, pitches[0], vel, "sus")

    def trem(self, tr, t0, nbars, pitch_fn, vel_base=96):
        """Tremolo-picked 16ths; alternating velocities simulate down/up."""
        n16 = int(nbars * 16)
        for i in range(n16):
            t = t0 + i * 0.25
            v = vel_base + (0 if i % 2 == 0 else -14) + [0, -4, -2, -6][i % 4]
            tr.add(t, 0.24, pitch_fn(i), max(40, v), "trem")

    def blast_traditional(self, t0, nbars, cym="ride_bell", vel_s=108):
        """Kick on 16th offbeats, snare on 8ths, cymbal with snare."""
        for i in range(int(nbars * 8)):
            t = t0 + i * 0.5
            self.drum(t, "snare", vel_ladder(vel_s, i, (0, -8, -3, -10)))
            self.drum(t + 0.25, "kick", vel_ladder(104, i))
            self.drum(t, cym, 88 if i % 2 else 96)

    def blast_hammer(self, t0, nbars, cym="china", vel=110):
        """Kick+snare unison 8ths, cymbal unison — the wall."""
        for i in range(int(nbars * 8)):
            t = t0 + i * 0.5
            self.drum(t, "kick", vel_ladder(vel, i))
            self.drum(t, "snare", vel_ladder(vel - 2, i, (0, -6, -2, -8)))
            self.drum(t, cym, 84 if i % 2 else 92)

    def dkick16(self, t0, nbars, snare_beats=(1.0, 3.0), cym="ride_bell"):
        """Double-kick 16ths groove with backbeat snare."""
        for i in range(int(nbars * 16)):
            t = t0 + i * 0.25
            self.drum(t, "kick", vel_ladder(108, i))
        for b in range(int(nbars)):
            for sb in snare_beats:
                self.drum(t0 + b * BAR + sb, "snare", random.randint(114, 122))
            self.drum(t0 + b * BAR, cym, 96)
            for q in (1.0, 2.0, 3.0):
                self.drum(t0 + b * BAR + q, cym, 84)

    def fill_snare_burst(self, t0):
        """32nd snare burst crescendo on beat 4 into a downbeat."""
        for i in range(8):
            self.drum(t0 + i * 0.125, "snare", 70 + i * 7)

    def fill_cascade(self, t0):
        """One-beat-per-drum 16th cascade: snare -> tom1 -> tom2 -> floor."""
        for j, d in enumerate(["snare", "tom1", "tom2", "tom_floor"]):
            for i in range(4):
                self.drum(t0 + j * 1.0 + i * 0.25, d, 100 + (i == 0) * 12)

    def crash_downbeat(self, t, which="crash1", vel=112, with_kick=True):
        self.drum(t, which, vel)
        if with_kick:
            self.drum(t, "kick", 116)

    def motif_notes(self, t0, base_pitch, stretch=1.0, vel=100, tags=("sus",)):
        out, t = [], t0
        for off, d in MOTIF:
            out.append(Note(t, d * stretch, base_pitch + off, vel,
                            frozenset(tags)))
            t += d * stretch
        return out

    def strings_chord(self, t, dur, root_off, quality, vel=84, base=56):
        """Voiced strings pad: root, 5th, octave, 3rd on top."""
        third = 4 if quality == "maj" else 3
        root = base + root_off
        for p in (root, root + 7, root + 12, root + 12 + third):
            self.strings.add(t, dur, p, vel, "sus")

    # ------------------------------------------------------------- sections
    def build(self):
        self.intro(); self.blast_a(); self.verse1(); self.breakdown1()
        self.peak(); self.verse2(); self.bridge(); self.solo()
        self.callout(); self.final_breakdown(); self.outro()
        # global humanization: hands loose, feet tighter, breakdowns grid-tight
        self.drums.notes = humanize(self.drums.notes, vel_jitter=5,
                                    time_jitter_beats=0.006,
                                    keep_grid=("grid",))
        for tr in (self.gtr_l, self.gtr_r):
            tr.notes = humanize(tr.notes, vel_jitter=4,
                                time_jitter_beats=0.004)
        self.bass.notes = humanize(self.bass.notes, vel_jitter=4,
                                   time_jitter_beats=0.003)
        return self.s

    def intro(self):
        t0 = self.sec["intro"]
        # choir pedal swells under the motif (strings state it twice)
        for rep in range(2):
            base = t0 + bars(4) * rep
            self.strings.extend(self.motif_notes(base, 68, vel=88 + rep * 8))
            for i, (roff, q) in enumerate(zip(CYCLE, CYCLE_QUAL)):
                self.strings_chord(base + bars(i), BAR, roff, q,
                                   vel=72 + rep * 10, base=44)
                third = 4 if q == "maj" else 3
                for p in (56 + roff, 56 + roff + third, 56 + roff + 7):
                    self.choir.add(base + bars(i), BAR, p, 64 + rep * 12, "sus")
        # bars 9-12: band creeps in — low trem guitar swell + tom build
        t = t0 + bars(8)
        self.trem(self.gtr_l, t, 4, lambda i: 44, vel_base=78)
        self.trem(self.gtr_r, t, 4, lambda i: 44, vel_base=78)
        self.strings.extend(self.motif_notes(t, 68, vel=104))
        for i, (roff, q) in enumerate(zip(CYCLE, CYCLE_QUAL)):
            self.strings_chord(t + bars(i), BAR, roff, q, vel=92, base=44)
        for b in range(2):  # tom pulse
            for i in range(8):
                self.drum(t + b * BAR + i * 0.5, "tom_floor", 78 + (i % 2) * 10)
        self.fill_cascade(t + bars(2))
        self.fill_snare_burst(t + bars(3) + 3.0)
        self.fx.add(t + bars(2), bars(2), 0, 100, "riser")
        self.sub.add(self.sec["blast_a"], 2.0, BASS_ROOT, 120)

    def blast_a(self):
        t0 = self.sec["blast_a"]
        self.crash_downbeat(t0)
        # tremolo roots of the cycle, one bar each, walking approach in bar 4
        oct_ = 44  # G#2 register
        cycle_p = [oct_ + o for o in CYCLE]

        def trem_pitch(i):
            bar_i = (i // 16) % 4
            pos = i % 16
            if bar_i == 3 and pos >= 12:      # walk-up back to i: 5, 7 deg
                return oct_ + [7, 7, 11, 11][pos - 12]
            return cycle_p[bar_i]
        for tr in (self.gtr_l, self.gtr_r):
            self.trem(tr, t0, 16, trem_pitch, vel_base=98)
        # bass: driving 8ths on roots
        for i in range(16 * 8):
            bar_i = (i // 8) % 4
            self.bass.add(t0 + i * 0.5, 0.45, 32 + CYCLE[bar_i],
                          102, "pick")
        # drums: traditional blast; china for last 2 bars of each 8
        self.blast_traditional(t0, 6)
        self.blast_traditional(t0 + bars(6), 2, cym="china")
        self.blast_traditional(t0 + bars(8), 6)
        self.blast_traditional(t0 + bars(14), 2, cym="china")
        # second half: strings baroque ostinato 8ths (root-5-b6-5 figure)
        t = t0 + bars(8)
        for i in range(8 * 8):
            bar_i = (i // 8) % 4
            root = 68 + CYCLE[bar_i]
            fig = [0, 7, 8, 7][i % 4]
            self.strings_stac.add(t + i * 0.5, 0.4, root + fig, 92, "stac")
        # lead ghost of the motif floats over bars 9-16
        for n in self.motif_notes(t, 80, stretch=2.0, vel=96):
            self.lead.notes.append(n)
        self.fill_snare_burst(t0 + bars(16) - 1.0)

    def verse1(self):
        t0 = self.sec["verse1"]
        self.crash_downbeat(t0, "china")
        # Phrygian pedal riff: 3+3+3+3+2+2 accent grid over PM 16ths
        accents = {0: None, 3: 45, 6: None, 9: 38, 12: None, 14: 33}
        # slots hit on every 16th; accents replace pedal w/ dissonant stabs
        for b in range(16):
            for i in range(16):
                t = t0 + b * BAR + i * 0.25
                hit3322 = i in (0, 3, 6, 9, 12, 14)
                if not hit3322:
                    continue
                acc = accents.get(i)
                variant = (b % 4 == 3)
                if acc and (b % 2 == 1 or variant):
                    for tr in (self.gtr_l, self.gtr_r):
                        tr.add(t, 0.4, acc, 112, "sus")
                    self.bass.add(t, 0.4, 33 if acc == 45 else 38,
                                  110, "pick")
                else:
                    self.chug(t, 0.5, ROOT, 100)
        # drums: double kick 16ths, backbeat 2+4, ghost notes
        self.dkick16(t0, 16, snare_beats=(1.0, 3.0))
        for b in range(16):
            for g in (1.75, 3.75):
                self.drum(t0 + b * BAR + g, "snare", random.randint(42, 62))
        self.fill_cascade(t0 + bars(15))
        self.sub.add(self.sec["breakdown1"], 2.0, BASS_ROOT, 122)

    def breakdown1(self):
        t0 = self.sec["breakdown1"]
        # grids (16th chars): research patterns; bar4 variant; 2nd half bounce
        g_a = "X--X--X---X-X---"
        g_a4 = "X--X--X--X--XX--"
        bounce = "X-X-XX--X-X-XXX-"
        rows = [g_a, g_a, g_a, g_a4, bounce, bounce, g_a, "X-X-XX--XXXX----"]
        for b, row in enumerate(rows):
            for i, c in enumerate(row):
                if c != "X":
                    continue
                t = t0 + b * BAR + i * 0.25
                # last accent of bars 4/8: b2 slide stab
                if b in (3, 7) and i >= 12:
                    self.chug(t, 0.5, ROOT + 1, 116)
                else:
                    self.chug(t, 0.5, ROOT, 112)
                self.drum(t, "kick", 118, dur=0.2)
                self.drums.notes[-1] = self.drums.notes[-1].tagged("grid")
            # china quarters, snare on 3 (half-time)
            for q in range(4):
                self.drum(t0 + b * BAR + q, "china", 104 if q else 112)
            self.drum(t0 + b * BAR + 2.0, "snare", 121)
        self.sub.add(t0, 2.0, BASS_ROOT, 124)
        self.sub.add(t0 + bars(4), 2.0, BASS_ROOT, 118)
        self.fx.add(t0 + bars(7), bars(1), 0, 100, "riser")

    def peak(self):
        t0 = self.sec["peak"]
        self.crash_downbeat(t0)
        # 24 bars: 8 motif lead, 8 harmonized + hammer blast, 8 half-time tease
        # rhythm: tremolo root+5 dyads through the cycle
        def dyad_trem(tr, t_start, nbars, det=0):
            def pf(i):
                return 44 + CYCLE[(i // 16) % 4] + det
            self.trem(tr, t_start, nbars, pf, vel_base=96)
        dyad_trem(self.gtr_l, t0, 16)
        dyad_trem(self.gtr_r, t0, 16, det=7)   # R plays the 5th — wide wall
        for i in range(16 * 8):
            self.bass.add(t0 + i * 0.5, 0.45, 32 + CYCLE[(i // 8) % 4],
                          104, "pick")
        # lead: motif stretched (half-time feel), then harmonized a 3rd up
        for n in self.motif_notes(t0, 80, stretch=2.0, vel=112):
            self.lead.notes.append(n.tagged("vib"))
        for n in self.motif_notes(t0 + bars(8), 80, stretch=2.0, vel=114):
            self.lead.notes.append(n.tagged("vib"))
        for n in self.motif_notes(t0 + bars(8), 80, stretch=2.0, vel=104):
            # diatonic third above in harmonic minor
            deg = HARM_MINOR.index(((n.pitch - 80) % 12)
                                   ) if ((n.pitch - 80) % 12) in HARM_MINOR else 0
            up = HARM_MINOR[(deg + 2) % 7] + (12 if (deg + 2) >= 7 else 0)
            self.lead.notes.append(Note(n.start, n.dur,
                                        80 + up, 104, frozenset({"vib", "harm"})))
        # drums: trad blast 8, hammer blast 8
        self.blast_traditional(t0, 8)
        self.blast_hammer(t0 + bars(8), 8)
        # strings + choir carry the cycle big
        for rep in range(4):
            for i, (roff, q) in enumerate(zip(CYCLE, CYCLE_QUAL)):
                t = t0 + bars(rep * 4 + i)
                self.strings_chord(t, BAR, roff, q, vel=96, base=56)
                third = 4 if q == "maj" else 3
                for p in (68 + roff, 68 + roff + third):
                    self.choir.add(t, BAR, p, 88, "sus")
        # bars 17-24: half-time tease — chugs + sustained lead b6->5 resolve
        t = t0 + bars(16)
        grid = "X--X--X-X---X---"
        for b in range(8):
            for i, c in enumerate(grid):
                if c == "X":
                    tt = t + b * BAR + i * 0.25
                    self.chug(tt, 0.5, ROOT if b % 4 != 3 else ROOT + 1, 108)
                    self.drum(tt, "kick", 116, dur=0.2)
            for q in range(4):
                self.drum(t + b * BAR + q, "china", 102)
            self.drum(t + b * BAR + 2.0, "snare", 119)
        self.lead.add(t, bars(2), 80 + 8, 110, "vib")          # b6
        self.lead.add(t + bars(2), bars(2), 80 + 7, 108, "vib")  # 5
        self.lead.add(t + bars(4), bars(2), 80 + 3, 106, "vib")
        self.lead.add(t + bars(6), bars(1.5), 80 + 1, 110, "vib")
        self.lead.add(t + bars(7.5), bars(0.5), 80, 112, "vib")
        for i, (roff, q) in enumerate(zip(CYCLE, CYCLE_QUAL)):
            self.strings_chord(t + bars(i * 2), bars(2), roff, q, vel=80, base=44)

    def verse2(self):
        t0 = self.sec["verse2"]
        self.crash_downbeat(t0, "china")
        # slam groove: 8th chugs, tritone stabs, gallop bars 5-7, b9 ring 4/8
        for b in range(8):
            if b in (3, 7):
                self.ring(t0 + b * BAR, bars(1), [ROOT, ROOT + 13], 114)
                self.drum(t0 + b * BAR, "china", 114)
                self.drum(t0 + b * BAR, "kick", 118)
                self.fill_snare_burst(t0 + b * BAR + 3.0)
                continue
            if 4 <= b <= 6:   # gallop: 8th + two 16ths per beat (X-xx)
                for beat in range(4):
                    t = t0 + b * BAR + beat
                    self.chug(t, 0.5, ROOT, 106)
                    self.chug(t + 0.5, 0.25, ROOT, 96)
                    self.chug(t + 0.75, 0.25, ROOT, 92)
                    for kt in (0.0, 0.5, 0.75):
                        self.drum(t + kt, "kick", 114, dur=0.15)
            else:
                for i in range(8):
                    t = t0 + b * BAR + i * 0.5
                    p = ROOT + (6 if i in (3, 6) and b % 2 else 0)  # tritone stab
                    self.chug(t, 0.5, p, 108 if p != ROOT else 102)
                    self.drum(t, "kick", 114, dur=0.2)
            for q in (0.0, 1.0, 2.0, 3.0):
                self.drum(t0 + b * BAR + q, "china", 100)
            self.drum(t0 + b * BAR + 2.0, "snare", 120)

    def bridge(self):
        t0 = self.sec["bridge"]
        # ambient breath: clean arps over strings, bass pedal, no drums
        for rep in range(2):
            for i, (roff, q) in enumerate(zip(CYCLE, CYCLE_QUAL)):
                t = t0 + bars(rep * 4 + i)
                third = 4 if q == "maj" else 3
                arp = [56 + roff, 56 + roff + 7, 68 + roff, 68 + roff + third,
                       68 + roff + 7, 68 + roff + third, 68 + roff, 56 + roff + 7]
                for j, p in enumerate(arp):
                    self.clean.add(t + j * 0.5, 0.9, p, 78 + (j == 0) * 10, "clean")
                self.strings_chord(t, BAR, roff, q, vel=64, base=44)
                self.bass.add(t, BAR, 32 + roff, 72, "sus")
        # riser: strings crescendo + snare roll last 2 bars
        self.fx.add(t0 + bars(6), bars(2), 0, 100, "riser")
        for i in range(32):
            self.drum(t0 + bars(6) + i * 0.25, "snare", 40 + int(i * 2.5))

    def solo(self):
        t0 = self.sec["solo"]
        self.crash_downbeat(t0)
        # rhythm bed: pedal 16th chugs; drums double-kick w/ backbeat
        for b in range(8):
            for i in range(16):
                if i % 4 != 3:
                    self.chug(t0 + b * BAR + i * 0.25, 0.4, ROOT, 96)
        self.dkick16(t0, 8, snare_beats=(1.0, 3.0), cym="crash2")
        # neoclassical lead: harm minor ascent, dim7 descent, phryg-dom trill,
        # climb to screaming sustained bend
        t = t0
        run = [56 + HARM_MINOR[i % 7] + 12 * (i // 7) for i in range(15)]
        for i, p in enumerate(run):                       # bars 1-2 ascent
            self.lead.add(t + i * 0.25, 0.24, p, 100 + (i % 4 == 0) * 12, "fast")
        t += bars(2)
        dim = [80 + x for x in (0, -3, -6, -9, -12, -15, -18, -21)]
        for i, p in enumerate(dim):                       # bars 3-4 dim7 fall
            self.lead.add(t + i * 0.5, 0.45, p, 108, "fast")
        t += bars(2)
        for i in range(16):                               # bars 5-6 b9 trill
            p = 68 + (1 if i % 2 else 0)
            self.lead.add(t + i * 0.25, 0.22, p, 96 + (i % 4 == 0) * 10, "fast")
        t += bars(2)
        climb = [68 + PHRYG_DOM[i % 7] + 12 * (i // 7) for i in range(8)]
        for i, p in enumerate(climb):                     # bar 7 climb
            self.lead.add(t + i * 0.5, 0.45, p, 104, "fast")
        self.lead.add(t + bars(1), bars(1), 92, 118, "vib")  # screaming G#5+12

    def callout(self):
        t0 = self.sec["callout"]
        # unison stab beat 1, then silence — the vocalist owns this space
        self.ring(t0, 1.0, [ROOT, ROOT + 12], 120)
        self.drum(t0, "china", 118)
        self.drum(t0, "kick", 122)
        self.fx.add(t0 + bars(1), bars(1), 0, 110, "riser")
        self.sub.add(self.sec["final_bd"], 3.0, 18, 127)  # F#0 — detuned world

    def final_breakdown(self):
        t0 = self.sec["final_bd"]
        R = ROOT - 2  # F#1 — the whole-step detune
        rows = [
            # bars 1-4: sparse quarter-time devastation
            "X-----X---X-----", "X-----X---X-----",
            "X-----X---X-----", "X-----X---X-X-X-",
            # bars 5-8: displacement + 32nd doubles
            "X--X----XX--X---", "X--X----XX--X---",
            "X--X----XX--X---", "X--X---XX--XXX--",
            # bars 9-12: lead enters (leitmotif over the chugs)
            "X-X---X---X-X---", "X-X---X---X-X---",
            "X-X---X---X-X---", "X-X---X-XXXX----",
            # bars 13-16: escalation
            "X-X-XX--X-X-XXX-", "X-X-XX--X-X-XXX-",
            "XX--XX--XX--XX--", "X---X---X---X---",
            # bars 17-20: unison quarters into the last hit
            "X---X---X---X---", "X---X---X---X---",
            "X---X---X---X---", "X---------------",
        ]
        for b, row in enumerate(rows):
            dbl = b in (7, 11, 12, 13)
            for i, c in enumerate(row):
                if c != "X":
                    continue
                t = t0 + b * BAR + i * 0.25
                pitch = R + (1 if (b in (3, 11) and i >= 12) else 0)
                self.chug(t, 0.5, pitch, 116)
                self.drum(t, "kick", 120, dur=0.2)
                self.drums.notes[-1] = self.drums.notes[-1].tagged("grid")
                if dbl and c == "X" and i % 4 == 0:
                    self.drum(t + 0.125, "kick", 106, dur=0.12)
                    self.drums.notes[-1] = self.drums.notes[-1].tagged("grid")
            half = b < 8 or b >= 16
            for q in ((0.0, 2.0) if half else (0.0, 1.0, 2.0, 3.0)):
                self.drum(t0 + b * BAR + q, "china", 108 if q else 116)
            if b % 2 == 1 and b < 16:
                self.drum(t0 + b * BAR + 2.0, "snare", 123)
            elif b >= 16:
                self.drum(t0 + b * BAR + 2.0, "snare", 125)
        # orchestral stabs sync with chugs bars 5-12 (staccato octaves)
        for b in range(4, 12):
            for i, c in enumerate(rows[b]):
                if c == "X":
                    t = t0 + b * BAR + i * 0.25
                    for p in (54 + 0, 54 + 12):  # F#3/F#4 stabs
                        self.strings_stac.add(t, 0.3, p, 104, "stac")
        # the climax lead: leitmotif in whole notes, transposed to F# world
        for n in self.motif_notes(t0 + bars(8), 78, stretch=2.0, vel=116):
            self.lead.notes.append(n.tagged("vib"))
        # choir swell through the escalation
        for i, (roff, q) in enumerate(zip(CYCLE, CYCLE_QUAL)):
            third = 4 if q == "maj" else 3
            t = t0 + bars(12 + i * 2)
            for p in (66 + roff - 2, 66 + roff - 2 + third, 66 + roff - 2 + 7):
                self.choir.add(t, bars(2), p, 92 + i * 6, "sus")
        # sub drops at each 4-bar escalation
        for bb, vel in ((0, 127), (4, 120), (8, 122), (12, 124), (16, 126)):
            self.sub.add(t0 + bars(bb), 2.5, 18, vel)
        # bar 20: single hit beat 1... silence... final ring w/ dive
        t_end = t0 + bars(19)
        self.ring(t_end, 3.0, [R, R + 12], 120)
        self.drum(t_end, "china", 120)
        self.drum(t_end, "kick", 124)
        self.fx.add(t_end, 3.0, R, 110, "dive")

    def outro(self):
        t0 = self.sec["outro"]
        # strings restate the motif over a ringing detuned chord; slow fade
        self.strings.extend(self.motif_notes(t0, 66, stretch=1.5, vel=92))
        for p in (30, 42, 49):   # F#1 5th stack ring
            self.gtr_l.add(t0, bars(6), p, 82, "sus")
            self.gtr_r.add(t0, bars(6), p, 82, "sus")
        self.bass.add(t0, bars(6), 30, 84, "sus")
        self.strings_chord(t0 + bars(4), bars(4), -2, "min", vel=72, base=44)
        for p in (64, 67, 71):
            self.choir.add(t0 + bars(4), bars(4), p, 70, "sus")


def build_song():
    song = Song()
    score = song.build()
    return score, song.sec
