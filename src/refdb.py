"""Reference lock: mine the THREE chosen songs deeply, not the corpus
average. (User-locked references: Lorna Shore 'Sun//Eater', Signs of the
Swarm 'Amongst the Low & Empty', Black Tongue 'Second Death'.)

Outputs corpus/refs.json (aggregate stats only):
 - masks/bigrams/bar-transitions mined from ONLY these songs
 - each reference's structure curve: per-measure onset density + tempo
   (the shape of the song, for structure templating)
 - drum patterns from ONLY these songs (same grid format as drumdb)

Novelty checks still run against the FULL corpus — anchoring to three
songs must not mean copying them; it means their laws outrank the average.
"""

import os
import json
from fractions import Fraction
from collections import Counter

from riffdb import tempo_at, band, measure_events, low_string_index
from drumdb import grid_of, dominant_cym

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAW = os.path.join(REPO, "corpus", "raw_modern")
OUT = os.path.join(REPO, "corpus", "refs.json")

REFS = [
    ("lornashore__suneater.json", "suneater"),
    ("signsoftheswarm__amongstthelowandempty.json", "lowempty"),
    ("blacktongue__seconddeath.json", "seconddeath"),
]


def mine_guitar(part, agg, structure):
    lo = low_string_index(part)
    autom = part.get("automations")
    for mi, m in enumerate(part["measures"]):
        bpm = tempo_at(autom, mi)
        bnd = band(bpm)
        mask = ["."] * 16
        frets = []
        try:
            for pos, b, dur in measure_events(m):
                slot = int(pos * 16)
                if slot >= 16 or b.get("rest"):
                    continue
                notes = b.get("notes", [])
                if not notes:
                    continue
                mask[slot] = "X"
                for n in notes:
                    if n.get("string") == lo and isinstance(n.get("fret"),
                                                            int):
                        frets.append(n["fret"])
        except Exception:
            continue
        msk = "".join(mask)
        n_on = msk.count("X")
        if n_on:
            agg["masks"].setdefault(bnd, Counter())[msk] += 1
        structure.append(dict(measure=mi, bpm=bpm, density=n_on / 16.0))
        for a, b2 in zip(frets, frets[1:]):
            if 0 <= a <= 9 and 0 <= b2 <= 9:
                agg["fret_bigrams"][f"{a}>{b2}"] += 1


def main():
    refs = {}
    for fname, key in REFS:
        path = os.path.join(RAW, fname)
        song = json.load(open(path))
        agg = dict(masks={}, fret_bigrams=Counter())
        structure = []
        gtr = [p for p in song["parts"]
               if "Guitar" in str(p.get("_trackmeta", {}).get("instrument",
                                                              ""))]
        if gtr:
            mine_guitar(gtr[0], agg, structure)
        drums = {b: Counter() for b in ("breakdown", "mid", "blast")}
        dparts = [p for p in song["parts"]
                  if str(p.get("_trackmeta", {}).get("instrument"))
                  == "Drums"]
        if dparts:
            dp = dparts[0]
            autom = dp.get("automations")
            for mi, m in enumerate(dp["measures"]):
                g = grid_of(m)
                if g is None or (g["kick"].count("X")
                                 + g["snare"].count("X")) == 0:
                    continue
                bpm = tempo_at(autom, mi)
                cym = dominant_cym(g)
                cmask = g[cym] if cym != "none" else "." * 16
                drums[band(bpm)][json.dumps([g["kick"], g["snare"], cym,
                                             cmask])] += 1
        refs[key] = dict(
            artist=song["artist"], title=song["title"],
            masks={b: dict(c) for b, c in agg["masks"].items()},
            fret_bigrams=dict(agg["fret_bigrams"]),
            structure=structure[:400],
            drums={b: {k: v for k, v in c.most_common(60)}
                   for b, c in drums.items()},
        )
        dens = [s["density"] for s in structure]
        print(f"{key}: {len(structure)} bars, mean density "
              f"{sum(dens)/max(1,len(dens)):.2f}, tempo range "
              f"{min(s['bpm'] for s in structure)}-"
              f"{max(s['bpm'] for s in structure)}")

    # merged reference idiom (union, count-weighted) for the generator
    merged = dict(masks={}, fret_bigrams=Counter())
    for key, r in refs.items():
        for b, mm in r["masks"].items():
            tgt = merged["masks"].setdefault(b, Counter())
            for m, c in mm.items():
                tgt[m] += c
        for k, v in r["fret_bigrams"].items():
            merged["fret_bigrams"][k] += v
    merged_drums = {b: Counter() for b in ("breakdown", "mid", "blast")}
    for key, r in refs.items():
        for b, dd in r["drums"].items():
            for k, v in dd.items():
                merged_drums[b][k] += v
    out = dict(
        refs=refs,
        merged=dict(masks={b: dict(c) for b, c in merged["masks"].items()},
                    fret_bigrams=dict(merged["fret_bigrams"])),
        merged_drums={b: dict(c.most_common(120))
                      for b, c in merged_drums.items()},
    )
    with open(OUT, "w") as fp:
        json.dump(out, fp)
    tot = sum(merged["fret_bigrams"].values())
    open_share = sum(v for k, v in merged["fret_bigrams"].items()
                     if k.startswith("0>")) / max(1, tot)
    pedal = sum(v for k, v in merged["fret_bigrams"].items()
                if k.split(">")[0] == k.split(">")[1]) / max(1, tot)
    print(f"merged: open={open_share:.2f} pedal={pedal:.2f} "
          f"bigrams={tot}")


if __name__ == "__main__":
    main()
