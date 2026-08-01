"""Tab-first riff generator, grounded in the mined idiom DB (corpus/idiom.json)
and the humanness constraint spec (docs/13).

Composes in (string, fret) space on a real tuning, rhythm-first:
 1. rhythm mask sampled from REAL mined masks (tempo-band + kind filtered)
 2. accent slots derived from the mask (group starts)
 3. pitches walk the mined fret-bigram table, anchored to the open string,
    changing only on accents, within a 4-fret window
 4. wrapped in an Easley two-part scheme (statement + terminal alteration)
 5. palm-mute state machine; pinch squeals on mined slots
 6. rejection filters loop until a riff passes
Every riff renders to ASCII tab for human inspection.
"""

import os
import json
import random
from collections import Counter

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
IDIOM = json.load(open(os.path.join(REPO, "corpus", "idiom.json")))

# Drop A# 6-string, low->high MIDI
TUNING = [34, 41, 46, 51, 55, 60]


def midi_of(string, fret):
    """string: 0 = lowest."""
    return TUNING[string] + fret


def _mask_pool(band_name, min_on=1, max_on=16, require=None, forbid_wall=False):
    pool = []
    for mask, count in IDIOM["masks"].get(band_name, {}).items():
        n = mask.count("X")
        if not (min_on <= n <= max_on):
            continue
        if mask[0] != "X":              # anchor law: beat 1 is sacred
            continue
        if "m" in mask:
            continue
        if forbid_wall and n >= 15:
            continue
        if require and not require(mask):
            continue
        pool.append((mask, count))
    return pool


def sample_mask(rng, band_name, kind):
    if kind == "breakdown":
        pool = _mask_pool(band_name, 2, 8, forbid_wall=True)
    elif kind == "final_breakdown":
        pool = _mask_pool(band_name, 2, 6, forbid_wall=True)
    elif kind == "chug":
        pool = _mask_pool(band_name, 6, 14, forbid_wall=True)
    elif kind == "twostep":
        pool = _mask_pool(band_name, 4, 10, forbid_wall=True)
    else:  # tremolo/wall
        return "X" * 16
    total = sum(c for _, c in pool)
    r = rng.random() * total
    for mask, c in pool:
        r -= c
        if r <= 0:
            return mask
    return pool[0][0]


def accent_slots(mask):
    """Group starts: onset at 0, or onset preceded by a rest."""
    acc = []
    for i, ch in enumerate(mask):
        if ch != "X":
            continue
        if i == 0 or mask[i - 1] != "X":
            acc.append(i)
    return acc


BIGRAMS = {}
for k, v in IDIOM["fret_bigrams"].items():
    a, b = k.split(">")
    a, b = int(a), int(b)
    if 0 <= a <= 8 and 0 <= b <= 8:
        BIGRAMS.setdefault(a, Counter())[b] = v


def next_fret(rng, cur, allowed):
    table = BIGRAMS.get(cur, Counter({0: 1}))
    cands = [(f, c ** 0.7) for f, c in table.items() if f in allowed]
    if not cands:
        return 0
    total = sum(w for _, w in cands)
    r = rng.random() * total
    for f, w in cands:
        r -= w
        if r <= 0:
            return f
    return cands[0][0]


def assign_frets(rng, mask, max_pcs=4, window=4):
    """Walk the bigram table on the low string; pitch changes on accents only;
    everything else repeats the current fret (pedal law)."""
    acc = set(accent_slots(mask))
    frets = {}
    cur = 0
    used = {0}
    lo_w, hi_w = 0, 8
    for i, ch in enumerate(mask):
        if ch != "X":
            continue
        if i in acc and i != 0:
            allowed = set(range(max(lo_w, 0), min(hi_w, 8) + 1))
            allowed.add(0)                     # open string always legal
            if len(used) >= max_pcs:
                allowed &= used
            nf = next_fret(rng, cur, allowed)
            cur = nf
            used.add(nf)
            fretted = [f for f in used if f > 0]
            if fretted:
                lo_w = max(0, max(fretted) - window)
                hi_w = min(8, min(fretted) + window)
        frets[i] = cur
    return frets


def terminal_alter(rng, mask, frets):
    """Easley: statement + terminal alteration — change the LAST accent's
    pitch (chromatic neighbor or tritone stab) or append a pinch."""
    acc = accent_slots(mask)
    if not acc:
        return frets, None
    last = acc[-1]
    f2 = dict(frets)
    move = rng.choice(["b2", "tritone", "pinch", "drop"])
    if move == "b2":
        f2[last] = 1 if frets.get(last, 0) == 0 else max(0, frets[last] - 1)
        return f2, None
    if move == "tritone":
        f2[last] = 6
        return f2, None
    if move == "drop":                          # remove the last hit (rest)
        f2.pop(last, None)
        return f2, None
    return f2, last                             # pinch on the last accent


class Riff:
    def __init__(self, bars, tempo, kind, string=0):
        self.bars = bars          # list of (mask, frets{slot:fret}, pinch)
        self.tempo = tempo
        self.kind = kind
        self.string = string

    def tab(self):
        names = ["A#", "F", "A#", "D#", "G", "C"]
        lines = []
        for si in range(5, -1, -1):
            row = names[si].ljust(2) + "|"
            for mask, frets, pinch in self.bars:
                for i in range(16):
                    if si == self.string and i in frets:
                        cell = str(frets[i])
                        if pinch == i:
                            cell = "(" + cell + ")"
                        row += cell.ljust(2, "-")
                    else:
                        row += "--"
                row += "|"
            lines.append(row)
        return "\n".join(lines)


def validate(riff):
    """Rejection filters from the humanness spec."""
    for mask, frets, _ in riff.bars:
        vals = [frets[i] for i in sorted(frets)]
        if not vals:
            return False
        if len(set(vals)) > 5:
            return False                       # pitch budget
        anchor = sum(1 for v in vals if v == 0) / len(vals)
        fretted = [v for v in vals if v > 0]
        if fretted and max(fretted) - min(fretted) > 5:
            return False                       # hand window
        run = 1
        for a, b in zip(vals, vals[1:]):
            run = run + 1 if b == a + 1 or b == a - 1 else 1
            if run > 4:
                return False                   # scale-run wandering
    all_vals = [f for _, fr, _ in riff.bars for f in fr.values()]
    if sum(1 for v in all_vals if v == 0) / max(1, len(all_vals)) < 0.2:
        return False                           # open-string gravity
    return True


def make_riff(rng, kind, tempo, nbars=4, band=None, max_pcs=4):
    """4-bar hypermeasure: A A A B (initial repetition + contrast) or
    A A' A B (statement + terminal alteration), per corpus weights."""
    band = band or ("breakdown" if tempo <= 150 else
                    "mid" if tempo <= 205 else "blast")
    for _ in range(200):
        mask = sample_mask(rng, band, kind)
        frets = assign_frets(rng, mask, max_pcs=max_pcs)
        fB, pinchB = terminal_alter(rng, mask, frets)
        scheme = rng.random()
        if scheme < 0.45:                      # A A A B
            bars = [(mask, frets, None)] * 3 + [(mask, fB, pinchB)]
        elif scheme < 0.75:                    # A A' A B
            fA2, pA2 = terminal_alter(rng, mask, frets)
            bars = [(mask, frets, None), (mask, fA2, pA2),
                    (mask, frets, None), (mask, fB, pinchB)]
        else:                                  # A A B B (terminal repetition)
            bars = [(mask, frets, None)] * 2 + [(mask, fB, pinchB)] * 2
        r = Riff(bars[:nbars], tempo, kind)
        if validate(r):
            return r
    raise RuntimeError(f"no valid riff found for {kind}@{tempo}")


def make_tremolo(rng, tempo, nbars=4, string=2, base_fret=3):
    """AtG-style tremolo line: one string, natural-minor ladder from the
    mined contour logic (steps, anchored, <=4 distinct frets)."""
    minor_off = [0, 2, 3, 5, 7]
    for _ in range(100):
        anchor = base_fret
        degs = [0, 0, 2, 0, 3, 2, 0, 0]        # ladder cell
        rng_shift = rng.choice([0, 1, 2])
        contour = [minor_off[(d + rng_shift) % 5] for d in degs]
        bars = []
        for b in range(nbars):
            frets = {}
            cell = contour if b < nbars - 1 else contour[:-2] + [1, 0]
            for i in range(16):
                frets[i] = anchor + cell[(i // 2) % len(cell)]
            bars.append(("X" * 16, frets, None))
        r = Riff(bars, tempo, "tremolo", string=string)
        vals = set(f for _, fr, _ in bars for f in fr.values())
        if len(vals) <= 5 and max(vals) - min(vals) <= 5:
            return r
    raise RuntimeError("tremolo gen failed")
