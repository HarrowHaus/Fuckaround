"""Corpus-lawful drum writing: every bar is a REAL mined pattern
(corpus/drums_modern.json), chosen by how well its kick agrees with the
riff being played (the measured 0.755 kick<->guitar coupling law), then
the section's cymbal role is rendered faithfully.

No more hand-invented beats: the book only contains bars that occur in
the 37-song corpus, weighted by how often the scene actually plays them.
"""

import os
import json
import random

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BOOK = json.load(open(os.path.join(REPO, "corpus", "drums_modern.json")))

CYM_MAP = {"china": "china", "crash": "crash1", "ride": "ride",
           "hat": "hihat_closed", "none": None}


def _jaccard(a, b):
    A = {i for i, c in enumerate(a) if c == "X"}
    B = {i for i, c in enumerate(b) if c == "X"}
    if not A and not B:
        return 0.0
    return len(A & B) / max(1, len(A | B))


def _coverage(kick, riff):
    """Share of riff onsets doubled by the kick (the mined law is 0.755)."""
    R = [i for i, c in enumerate(riff) if c == "X"]
    if not R:
        return 0.0
    return sum(1 for i in R if kick[i] == "X") / len(R)


class DrumBook:
    def __init__(self, source="corpus"):
        """source='refs' loads only the user-locked reference songs'
        patterns (corpus/refs.json merged_drums)."""
        book = BOOK["patterns"]
        if source == "refs":
            p = os.path.join(REPO, "corpus", "refs.json")
            book = json.load(open(p))["merged_drums"]
        self.bands = {}
        for band, pats in book.items():
            rows = []
            for key, count in pats.items():
                kick, snare, cym, cmask = json.loads(key)
                rows.append(dict(kick=kick, snare=snare, cym=cym,
                                 cmask=cmask, count=count,
                                 kd=kick.count("X")))
            self.bands[band] = rows

    def pick(self, rng, band, riff_mask="X...............",
             kick_lo=0, kick_hi=16, need_snare=True, prefer_cym=None,
             couple=True, k=1):
        """Sample k bar patterns. couple=True scores kick-riff agreement
        per the mined coupling law."""
        pool = (sum(self.bands.values(), []) if band == "*"
                else self.bands.get(band, []))
        rows = [r for r in pool
                if kick_lo <= r["kd"] <= kick_hi
                and (not need_snare or "X" in r["snare"])]
        if not rows:
            rows = pool[:20] if pool else sum(self.bands.values(), [])[:20]
        scored = []
        for r in rows:
            w = r["count"] ** 0.5
            if couple:
                w *= (0.35 + _coverage(r["kick"], riff_mask)
                      + 0.5 * _jaccard(r["kick"], riff_mask))
            if prefer_cym and r["cym"] == prefer_cym:
                w *= 1.8
            scored.append((w, r))
        total = sum(w for w, _ in scored)
        out = []
        for _ in range(k):
            x = rng.random() * total
            for w, r in scored:
                x -= w
                if x <= 0:
                    out.append(r)
                    break
            else:
                out.append(scored[0][1])
        return out

    def write_bar(self, drum_fn, base, pat, vel=118, cym_vel=100,
                  snare_vel=None):
        """Emit one mined bar via the song's drum() callback (slot = 16ths
        of a 4-beat bar)."""
        for i, c in enumerate(pat["kick"]):
            if c == "X":
                drum_fn(base + i * 0.25, "kick", vel, 0.1)
        for i, c in enumerate(pat["snare"]):
            if c == "X":
                sv = snare_vel if snare_vel else (122 if i in (4, 8, 12)
                                                  else 96)
                drum_fn(base + i * 0.25, "snare", sv, 0.2)
        cym = CYM_MAP.get(pat["cym"])
        if cym:
            for i, c in enumerate(pat["cmask"]):
                if c == "X":
                    drum_fn(base + i * 0.25, cym,
                            cym_vel + (8 if i == 0 else 0), 0.2)
