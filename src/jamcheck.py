"""Band members' preview tool: validate + print the current songdoc.

Usage: python3 jamcheck.py            # whole doc
       python3 jamcheck.py <section>  # one section

Prints per section: the tab, ref-law stats (open/pedal vs the locked
targets 0.49/0.82), playability violations, and drum info. Members run
this after editing jam/songdoc.json and BEFORE presenting to the band.
"""

import os
import sys
import json

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from riffgen import set_dialect, midi_of
set_dialect("modern")
import riffgen2 as r2

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
r2.set_reference(os.path.join(REPO, "corpus", "refs.json"))
from riffgen2 import Genome, genome_riff, mask_novelty

SONGDOC_PATH = os.environ.get("SONGDOC_PATH",
                              os.path.join(REPO, "jam", "songdoc.json"))
DOC = json.load(open(SONGDOC_PATH))

only = sys.argv[1] if len(sys.argv) > 1 else None
total_s = 0.0
for sec in DOC["sections"]:
    dur = sec["bars"] * 4 * 60.0 / sec["bpm"]
    t0 = total_s
    total_s += dur
    if only and sec["name"] != only:
        continue
    print(f"== {sec['name']}  @{sec['bpm']} BPM  {sec['bars']} bars  "
          f"[{int(t0//60)}:{t0%60:04.1f} - {int(total_s//60)}:"
          f"{total_s%60:04.1f}]")
    r = sec.get("riff")
    if not r:
        print("   (no riff)")
        continue
    frets = {int(k): v for k, v in r["frets"].items()}
    g = Genome(r["mask"], frets)
    s = g.stats()
    problems = []
    if r["mask"][0] != "X":
        problems.append("BEAT-1 ANCHOR MISSING")
    if s["pcs"] > 4:
        problems.append(f"pitch budget blown ({s['pcs']} > 4)")
    if s["span"] > 5:
        problems.append(f"hand window blown (span {s['span']} > 5)")
    nov = mask_novelty(r["mask"], "mid")
    if nov < 2:
        problems.append(f"MASK EXISTS IN CORPUS (novelty {nov}) — rewrite")
    for i in frets:
        if not (0 <= frets[i] <= 9):
            problems.append(f"fret {frets[i]} out of range at slot {i}")
    print(genome_riff(g, sec["bpm"], "sec").tab().split("\n")[-1])
    print(f"   open={s['open_share']:.2f} (target {r2.OPEN_TARGET:.2f})  "
          f"pedal={s['pedal']:.2f} (target {r2.PEDAL_TARGET:.2f})  "
          f"density={s['density']:.2f}  novelty={nov}")
    d = sec.get("drums", {})
    print(f"   drums: {d.get('mode', 'book')} "
          f"{'(union kick w/ riff)' if d.get('union_riff') else ''} "
          f"cym={d.get('prefer_cym')}  lead={sec.get('lead', 'none')}")
    if problems:
        print("   !! " + " | ".join(problems))
print(f"\ntotal: {int(total_s // 60)}:{total_s % 60:04.1f}")
