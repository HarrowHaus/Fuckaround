"""Mine DRUM vocabulary from the harvested corpus (corpus/raw_modern).

Output: corpus/drums_modern.json — aggregate statistics only:
 - per tempo band: the observed (kick_mask, snare_mask, cym) bar patterns
   with counts (16-slot grids, GM drum notes bucketed to kit roles)
 - kick<->guitar coupling: how much of the guitar onset grid the kick
   doubles in breakdown-band bars (the "kick rides the chug" law, measured)

This is how the drums stop being hand-invented: song writers pick real
mined bar patterns whose kick agrees with the riff, instead of patterns I
made up.
"""

import os
import json
import glob
from fractions import Fraction
from collections import Counter

from riffdb import tempo_at, band, measure_events

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAW = os.path.join(REPO, "corpus", "raw_modern")
OUT = os.path.join(REPO, "corpus", "drums_modern.json")

KICK = {35, 36}
SNARE = {37, 38, 40}
CHINA = {52}
CRASH = {49, 55, 57}
RIDE = {51, 53, 59}
HAT = {42, 44, 46}
TOM = {41, 43, 45, 47, 48, 50}


def grid_of(measure):
    """16-slot grids per role for one 4/4-ish bar."""
    g = {k: ["."] * 16 for k in ("kick", "snare", "china", "crash",
                                 "ride", "hat", "tom")}
    try:
        for pos, b, dur in measure_events(measure):
            slot = int(pos * 16)
            if slot >= 16 or b.get("rest"):
                continue
            for n in b.get("notes", []):
                v = n.get("fret")
                if v in KICK:
                    g["kick"][slot] = "X"
                elif v in SNARE:
                    g["snare"][slot] = "X"
                elif v in CHINA:
                    g["china"][slot] = "X"
                elif v in CRASH:
                    g["crash"][slot] = "X"
                elif v in RIDE:
                    g["ride"][slot] = "X"
                elif v in HAT:
                    g["hat"][slot] = "X"
                elif v in TOM:
                    g["tom"][slot] = "X"
    except Exception:
        return None
    return {k: "".join(v) for k, v in g.items()}


def dominant_cym(g):
    counts = [(g[k].count("X"), k) for k in ("china", "crash", "ride",
                                             "hat")]
    counts.sort(reverse=True)
    return counts[0][1] if counts[0][0] > 0 else "none"


def main():
    patterns = {b: Counter() for b in ("breakdown", "mid", "blast")}
    couple_hits, couple_tot = 0, 0
    songs = 0
    for f in sorted(glob.glob(os.path.join(RAW, "*.json"))):
        song = json.load(open(f))
        drum_parts = [p for p in song["parts"]
                      if str(p.get("_trackmeta", {}).get("instrument"))
                      == "Drums"]
        gtr_parts = [p for p in song["parts"]
                     if "Guitar" in str(p.get("_trackmeta",
                                              {}).get("instrument", ""))
                     and "clean" not in str(p.get("_trackmeta",
                                                  {}).get("instrument",
                                                          "")).lower()]
        if not drum_parts:
            continue
        songs += 1
        dp = drum_parts[0]
        autom = dp.get("automations")
        # guitar onset grids for coupling (first guitar part)
        gtr_grids = {}
        if gtr_parts:
            for mi, m in enumerate(gtr_parts[0]["measures"]):
                try:
                    grid = ["."] * 16
                    for pos, b, dur in measure_events(m):
                        slot = int(pos * 16)
                        if slot < 16 and not b.get("rest") and b.get("notes"):
                            grid[slot] = "X"
                    gtr_grids[mi] = "".join(grid)
                except Exception:
                    pass
        for mi, m in enumerate(dp["measures"]):
            bpm = tempo_at(autom, mi)
            g = grid_of(m)
            if g is None or g["kick"].count("X") + g["snare"].count("X") == 0:
                continue
            bnd = band(bpm)
            cym = dominant_cym(g)
            cym_mask = g[cym] if cym != "none" else "." * 16
            patterns[bnd][json.dumps([g["kick"], g["snare"], cym,
                                      cym_mask])] += 1
            # kick<->guitar coupling in breakdown-band bars
            if bnd == "breakdown" and mi in gtr_grids:
                gg = gtr_grids[mi]
                gon = [i for i, c in enumerate(gg) if c == "X"]
                if len(gon) >= 2:
                    couple_tot += len(gon)
                    couple_hits += sum(1 for i in gon
                                       if g["kick"][i] == "X")
    out = {
        "songs": songs,
        "kick_guitar_coupling": round(couple_hits / max(1, couple_tot), 3),
        "patterns": {b: {k: c for k, c in patterns[b].most_common(120)}
                     for b in patterns},
    }
    with open(OUT, "w") as fp:
        json.dump(out, fp, indent=1)
    print(f"songs {songs}  coupling {out['kick_guitar_coupling']}")
    for b in patterns:
        top = patterns[b].most_common(3)
        print(f"{b}: {sum(patterns[b].values())} bars, top:")
        for k, c in top:
            kick, snare, cym, cmask = json.loads(k)
            print(f"  x{c}  K {kick}  S {snare}  {cym} {cmask}")


if __name__ == "__main__":
    main()
