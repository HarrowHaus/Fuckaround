"""Recursive corpus-constrained riff engine (song 6+).

The corpus is used ONLY as constraints and fitness, never as material:
 - rhythm masks are GENERATED (density/offbeat priors measured from the
   mined tables), and any mask identical or near-identical (Hamming < 2)
   to a corpus mask is rejected — the opposite of riffgen.py's sampling
 - fret walks are generated within the hand-window laws; the mined bigram
   table scores idiomatic-ness as a log-likelihood, it is not a sampler
 - every riff is refined by an evolutionary loop: population -> fitness ->
   tournament selection -> mutation, for G generations (the riff improves
   on itself, measurably — fitness curves are logged)
 - sections develop recursively: each new section's riff starts from a
   TRANSFORMATION of the previous section's riff (augment / diminish /
   displace / thin / thicken / invert) and is then re-evolved under that
   section's role targets. One seed motif becomes the whole song.
"""

import math
import random
from collections import Counter

from riffgen import (IDIOM_TABLES, TUNINGS, Riff, set_dialect, midi_of,
                     accent_slots)

IDIOM = IDIOM_TABLES.get("modern", IDIOM_TABLES["2007"])

# ---- corpus-derived constraint targets (aggregate stats, not material)
_bg = IDIOM["fret_bigrams"]
_tot = sum(_bg.values())
OPEN_TARGET = sum(v for k, v in _bg.items() if k.startswith("0>")) / _tot
PEDAL_TARGET = sum(v for k, v in _bg.items()
                   if k.split(">")[0] == k.split(">")[1]) / _tot

CORPUS_MASKS = {band: set(d.keys()) for band, d in IDIOM["masks"].items()}


def _band_priors(band):
    """Density + offbeat-share distributions measured from the mined masks
    (weighted by observed counts)."""
    dens, off = Counter(), []
    for mask, cnt in IDIOM["masks"].get(band, {}).items():
        n = mask.count("X")
        if n == 0:
            continue
        dens[n] += cnt
        off.append((sum(1 for i, c in enumerate(mask)
                        if c == "X" and i % 2 == 1) / n, cnt))
    wsum = sum(c for _, c in off) or 1
    off_share = sum(s * c for s, c in off) / wsum
    return dens, off_share


BIGRAMS = {}
for k, v in _bg.items():
    a, b = k.split(">")
    a, b = int(a), int(b)
    if 0 <= a <= 8 and 0 <= b <= 8:
        BIGRAMS.setdefault(a, Counter())[b] = v


def bigram_loglik(frets_seq):
    """Mean log-probability of the fret walk under the mined transitions —
    high = idiomatic, without ever copying a walk."""
    if len(frets_seq) < 2:
        return 0.0
    ll = 0.0
    for a, b in zip(frets_seq, frets_seq[1:]):
        row = BIGRAMS.get(a, Counter({0: 1}))
        tot = sum(row.values())
        ll += math.log((row.get(b, 0) + 0.5) / (tot + 5))
    return ll / (len(frets_seq) - 1)


def hamming(a, b):
    return sum(1 for x, y in zip(a, b) if x != y)


def mask_novelty(mask, band):
    """Min Hamming distance to any corpus mask in the band (and the wall
    band, which every band contains)."""
    pool = CORPUS_MASKS.get(band, set())
    best = 16
    for m in pool:
        best = min(best, hamming(mask, m.replace("m", "X")))
        if best == 0:
            break
    return best


# --------------------------------------------------------------- genome
class Genome:
    """One bar in tab space: mask (16 slots) + fret per onset."""
    def __init__(self, mask, frets):
        self.mask = mask
        self.frets = dict(frets)

    def stats(self):
        vals = [self.frets[i] for i in sorted(self.frets)]
        n = len(vals) or 1
        return dict(
            density=len(vals) / 16.0,
            open_share=sum(1 for v in vals if v == 0) / n,
            pedal=sum(1 for a, b in zip(vals, vals[1:]) if a == b) /
            max(1, n - 1),
            pcs=len(set(vals)),
            span=(max(vals) - min(vals)) if vals else 0,
            offbeat=sum(1 for i in self.frets if i % 2 == 1) / n,
        )

    def clone(self):
        return Genome(self.mask, self.frets)


def random_genome(rng, density_ct, off_share):
    """Generate a mask from the measured priors (never sampled from the
    corpus itself) + a pedal-biased fret walk."""
    total = sum(density_ct.values()) or 1
    r = rng.random() * total
    n_on = 8
    for d, c in sorted(density_ct.items()):
        r -= c
        if r <= 0:
            n_on = d
            break
    n_on = max(2, min(14, n_on))
    slots = {0}
    while len(slots) < n_on:
        if rng.random() < off_share:
            cand = rng.choice([1, 3, 5, 7, 9, 11, 13, 15])
        else:
            cand = rng.choice([0, 2, 4, 6, 8, 10, 12, 14])
        slots.add(cand)
    mask = "".join("X" if i in slots else "." for i in range(16))
    # fret walk: pedal-dominant with accent moves
    acc = set(accent_slots(mask))
    cur = rng.choice([0, 0, 0, 1])
    frets = {}
    for i in sorted(slots):
        if i in acc and i != 0 and rng.random() < 0.55:
            cur = rng.choice([0, 0, 1, 1, 2, 3, 5, 6])
        frets[i] = cur
    return Genome(mask, frets)


def fitness(g, band, role):
    """Corpus-constraint closeness + novelty + role targets + idiom."""
    s = g.stats()
    f = 0.0
    # corpus-constraint terms (style laws, docs/13 + mined stats)
    f -= abs(s["open_share"] - OPEN_TARGET) * 2.0
    f -= abs(s["pedal"] - PEDAL_TARGET) * 2.0
    f -= max(0, s["pcs"] - 4) * 1.5          # pitch budget
    f -= max(0, s["span"] - 5) * 2.0         # hand window
    # role targets
    f -= abs(s["density"] - role["density"]) * 3.0
    f -= abs(s["offbeat"] - role.get("offbeat", 0.2)) * 1.2
    # idiom likelihood (not copying — scoring)
    vals = [g.frets[i] for i in sorted(g.frets)]
    f += max(-3.0, bigram_loglik(vals)) * 0.8
    # novelty demand: never a corpus mask, reward distance up to 4
    nov = mask_novelty(g.mask, band)
    if nov < 2:
        f -= 8.0
    else:
        f += min(nov, 4) * 0.3
    # internal coherence: self-similarity at half-bar lag
    same = sum(1 for i in range(8) if (g.mask[i] == g.mask[i + 8]))
    f += (same / 8.0) * 0.6
    if g.mask[0] != "X":
        f -= 10.0                             # beat-1 anchor law
    return f


def mutate(rng, g):
    g = g.clone()
    op = rng.random()
    slots = sorted(g.frets)
    if op < 0.3 and len(slots) > 2:           # drop an onset
        i = rng.choice(slots[1:])
        del g.frets[i]
    elif op < 0.55:                            # add an onset
        empty = [i for i in range(16) if i not in g.frets]
        if empty:
            i = rng.choice(empty)
            near = min(slots, key=lambda s: abs(s - i))
            g.frets[i] = g.frets[near]
    elif op < 0.8 and slots:                   # move a pitch
        i = rng.choice(slots)
        g.frets[i] = rng.choice([0, 0, 1, 1, 2, 3, 5, 6, 8])
    else:                                      # displace an onset by a 16th
        if len(slots) > 1:
            i = rng.choice(slots[1:])
            j = i + rng.choice([-1, 1])
            if 0 < j < 16 and j not in g.frets:
                g.frets[j] = g.frets.pop(i)
    g.mask = "".join("X" if i in g.frets else "." for i in range(16))
    if 0 not in g.frets:                       # re-anchor beat 1
        g.frets[0] = g.frets[min(g.frets)] if g.frets else 0
        g.mask = "X" + g.mask[1:]
    return g


def evolve(rng, band, role, seed=None, pop=48, gens=24, log=None):
    """The recursive-improvement core: population seeded from `seed` (a
    Genome, e.g. a transformation of the previous section) or from the
    measured priors; tournament + mutation until fitness plateaus."""
    dens, off = _band_priors(band)
    if not dens:
        dens, off = Counter({8: 1}), 0.2
    P = []
    for _ in range(pop):
        if seed and rng.random() < 0.6:
            g = seed.clone()
            for _ in range(rng.randint(1, 3)):
                g = mutate(rng, g)
            P.append(g)
        else:
            P.append(random_genome(rng, dens, off))
    best_hist = []
    for gen in range(gens):
        scored = sorted(P, key=lambda g: fitness(g, band, role),
                        reverse=True)
        best = scored[0]
        best_hist.append(round(fitness(best, band, role), 3))
        elite = scored[:max(4, pop // 8)]
        P = [e.clone() for e in elite]
        while len(P) < pop:
            a, b = rng.sample(elite, 2) if len(elite) > 1 else (elite[0],
                                                                elite[0])
            parent = a if fitness(a, band, role) > fitness(b, band,
                                                           role) else b
            P.append(mutate(rng, parent))
    if log is not None:
        log.append(best_hist)
    return sorted(P, key=lambda g: fitness(g, band, role), reverse=True)[0]


# ------------------------------------------------- motif transformations
def t_augment(g):
    """Half density: keep every other onset (breakdown-ward)."""
    keep = sorted(g.frets)[::2]
    frets = {i: g.frets[i] for i in keep}
    mask = "".join("X" if i in frets else "." for i in range(16))
    return Genome(mask, frets)


def t_diminish(rng, g):
    """Double density: echo each onset a 16th later where free."""
    frets = dict(g.frets)
    for i in sorted(g.frets):
        j = i + 1
        if j < 16 and j not in frets and rng.random() < 0.7:
            frets[j] = g.frets[i]
    mask = "".join("X" if i in frets else "." for i in range(16))
    return Genome(mask, frets)


def t_displace(rng, g):
    """Rotate the off-beat feel: shift all non-anchor onsets one 16th."""
    d = rng.choice([-1, 1])
    frets = {0: g.frets.get(0, 0)}
    for i in sorted(g.frets):
        if i == 0:
            continue
        j = min(15, max(1, i + d))
        if j not in frets:
            frets[j] = g.frets[i]
    mask = "".join("X" if i in frets else "." for i in range(16))
    return Genome(mask, frets)


def t_invert(g):
    """Mirror the fret contour inside the used window."""
    vals = [v for v in g.frets.values()]
    lo, hi = min(vals), max(vals)
    frets = {i: (hi + lo - v) for i, v in g.frets.items()}
    return Genome(g.mask, frets)


def t_thin(rng, g, n=2):
    frets = dict(g.frets)
    victims = [i for i in sorted(frets) if i != 0]
    for i in rng.sample(victims, min(n, len(victims))):
        del frets[i]
    mask = "".join("X" if i in frets else "." for i in range(16))
    return Genome(mask, frets)


TRANSFORMS = {
    "augment": lambda rng, g: t_augment(g),
    "diminish": t_diminish,
    "displace": t_displace,
    "invert": lambda rng, g: t_invert(g),
    "thin": lambda rng, g: t_thin(rng, g),
}


def develop(rng, prev, transform, band, role, log=None):
    """One recursion step: transform the previous material, then re-evolve
    it under the new section's role. Returns (genome, lineage_note)."""
    seed = TRANSFORMS[transform](rng, prev)
    g = evolve(rng, band, role, seed=seed, log=log)
    return g, transform


def genome_riff(g, tempo, kind, nbars=4, variant=None):
    """Genome -> 4-bar Riff (A A A B when a variant genome is given)."""
    barA = (g.mask, dict(g.frets), None)
    if variant is not None:
        barB = (variant.mask, dict(variant.frets), None)
    else:
        barB = barA
    return Riff([barA, barA, barA, barB][:nbars], tempo, kind)
