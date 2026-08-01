"""Mine idiom statistics from the harvested tab canon (corpus/raw/*.json).

Outputs AGGREGATE statistics only (corpus/idiom.json — committable):
- rhythm onset/PM masks per tempo band with frequencies (the real grids)
- fret bigram/trigram tables for the low two strings
- open-string share, distinct-fret counts, register splits
- technique placement (pinch harmonics, slides, HO/PO) per 16th slot
- riff-unit repeat structure (how bars repeat and vary)
- tempo distribution
"""

import os
import json
import glob
from collections import Counter, defaultdict
from fractions import Fraction

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAW = os.path.join(REPO, "corpus", "raw")
OUT = os.path.join(REPO, "corpus", "idiom.json")


def tempo_at(automations, mi):
    bpm = 120
    for ev in (automations or {}).get("tempo", []):
        if ev["measure"] <= mi:
            bpm = ev["bpm"]
    return bpm


def band(bpm):
    if bpm <= 150:
        return "breakdown"
    if bpm <= 205:
        return "mid"
    return "blast"


def measure_events(measure):
    """Yield (pos_fraction, beat) with pos in whole-note units."""
    pos = Fraction(0)
    for b in measure["voices"][0]["beats"]:
        dur = Fraction(b["duration"][0], b["duration"][1])
        yield pos, b, dur
        pos += dur


def low_string_index(part):
    return part["strings"] - 1


def analyze_part(part, agg):
    lo = low_string_index(part)
    autom = part.get("automations")
    prev_fret = None
    bar_sigs = []
    for mi, m in enumerate(part["measures"]):
        sig = m.get("signature") or [4, 4]
        if sig != [4, 4]:
            bar_sigs.append(None)
            continue
        bpm = tempo_at(autom, mi)
        bd = band(bpm)
        agg["tempo_hist"][str(int(bpm // 10) * 10)] += 1
        onset = ["."] * 16
        pm = ["."] * 16
        frets_in_bar = []
        low_notes = 0
        all_notes = 0
        for pos, b, dur in measure_events(m):
            if b.get("rest") or not b.get("notes"):
                continue
            slot = int(pos * 16)
            if slot >= 16:
                continue
            real = [n for n in b["notes"] if not n.get("rest")
                    and "string" in n]
            if not real:
                continue
            all_notes += 1
            lowest = max(real, key=lambda n: n["string"])
            is_low = lowest["string"] >= lo - 1
            if is_low:
                low_notes += 1
                onset[slot] = "X"
                pm[slot] = "M" if b.get("palmMute") else "O"
                f = lowest["fret"]
                frets_in_bar.append(f)
                if prev_fret is not None:
                    agg["fret_bigrams"][f"{prev_fret}>{f}"] += 1
                prev_fret = f
                for n in real:
                    h = n.get("harmonic")
                    hs = h if isinstance(h, str) else \
                        (h or {}).get("type", "")
                    if hs and hs not in ("natural",):
                        agg["pinch_slots"][str(slot)] += 1
            else:
                onset[slot] = "m"       # melody-register event
        if all_notes == 0:
            bar_sigs.append(None)
            continue
        mask = "".join(onset)
        agg["masks"][bd][mask] += 1
        agg["pm_masks"][bd]["".join(pm)] += 1
        if frets_in_bar:
            agg["open_share_num"] += sum(1 for f in frets_in_bar if f == 0)
            agg["open_share_den"] += len(frets_in_bar)
            agg["distinct_frets"][str(min(8, len(set(frets_in_bar))))] += 1
            for a, b2, c in zip(frets_in_bar, frets_in_bar[1:],
                                frets_in_bar[2:]):
                agg["fret_trigrams"][f"{a}>{b2}>{c}"] += 1
        agg["low_share_num"] += low_notes
        agg["low_share_den"] += all_notes
        bar_sigs.append(mask + "|" + ",".join(map(str, frets_in_bar)))
    # riff repeat structure: how often does bar i repeat bar i-1 / vary?
    for a, b in zip(bar_sigs, bar_sigs[1:]):
        if a is None or b is None:
            continue
        if a == b:
            agg["bar_transition"]["repeat"] += 1
        elif a.split("|")[0] == b.split("|")[0]:
            agg["bar_transition"]["same_rhythm_new_pitch"] += 1
        else:
            agg["bar_transition"]["new"] += 1


def main():
    agg = dict(
        masks=dict(breakdown=Counter(), mid=Counter(), blast=Counter()),
        pm_masks=dict(breakdown=Counter(), mid=Counter(), blast=Counter()),
        fret_bigrams=Counter(), fret_trigrams=Counter(),
        pinch_slots=Counter(), distinct_frets=Counter(),
        tempo_hist=Counter(), bar_transition=Counter(),
        open_share_num=0, open_share_den=0,
        low_share_num=0, low_share_den=0,
    )
    nparts = 0
    for f in sorted(glob.glob(os.path.join(RAW, "*.json"))):
        song = json.load(open(f))
        for part in song["parts"]:
            if "Guitar" not in part.get("instrument", ""):
                continue
            if part.get("strings", 6) < 6:
                continue
            analyze_part(part, agg)
            nparts += 1
    out = {}
    for k, v in agg.items():
        if isinstance(v, dict) and all(isinstance(x, Counter)
                                       for x in v.values()):
            out[k] = {kk: dict(vv.most_common(60)) for kk, vv in v.items()}
        elif isinstance(v, Counter):
            out[k] = dict(v.most_common(120))
        else:
            out[k] = v
    out["n_guitar_parts"] = nparts
    out["open_string_share"] = round(
        agg["open_share_num"] / max(1, agg["open_share_den"]), 3)
    out["low_register_share"] = round(
        agg["low_share_num"] / max(1, agg["low_share_den"]), 3)
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, "w") as fp:
        json.dump(out, fp, indent=1)
    print(f"parts analyzed: {nparts}")
    print("open-string share:", out["open_string_share"],
          "| low-register share:", out["low_register_share"])
    print("bar transitions:", dict(agg["bar_transition"]))
    for bd in ("breakdown", "mid", "blast"):
        top = list(agg["masks"][bd].most_common(5))
        print(f"top {bd} masks:")
        for mask, c in top:
            print(f"   {mask}  x{c}")
    print("top fret bigrams:", dict(agg["fret_bigrams"].most_common(12)))


if __name__ == "__main__":
    main()
