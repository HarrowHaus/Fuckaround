"""Riff-by-riff songwriting, step 1: generate real candidates, render them
through the actual amp chain, let the singer pick by ear instead of by tab.

This replaces "an agent drafts a whole skeleton" as the way a song starts
(jam/PROTOCOL.md). Usage:

    cd src && python3 riff_candidates.py --role mid --n 5 \\
        --density 0.55 --offbeat 0.25 --tempo 150 --out-tag opener

Outputs to jam/candidates/<out-tag>/: cand0.wav..candN.wav (amp'd, looped),
cand0.json..candN.json (the genome — mask/frets/stats, so a pick can be
dropped straight into a songdoc riff block), and an index.txt summary.

role: 'breakdown' | 'mid' | 'blast' | 'bounce' — see riffgen2.evolve's band
      argument. density/offbeat are role targets fed to the fitness fn.
discipline: pass --discipline for breakdown-style one-move-per-bar riffs.
"""

import os
import sys
import json
import random
import argparse

os.environ.setdefault("SONG", "songband")

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from riffgen import set_dialect, midi_of
set_dialect("modern")
import riffgen2 as r2

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
r2.set_reference(os.path.join(REPO, "corpus", "refs.json"))

from score import Score
import render as rnd
import dsp

OUT_ROOT = os.path.join(REPO, "jam", "candidates")


def render_candidate(genome, tempo, tag, workdir, reps=3):
    """Genome -> looped amp'd WAV via the real GTX -> NAM 5150 -> IR chain
    (same signal path as the shipped songs)."""
    sc = Score()
    sc.tempo_map = []
    sc.set_tempo(0.0, tempo)
    tr = sc.track("gtr_l")
    frets = genome.frets
    slots = sorted(frets)
    for rep in range(reps):
        base = rep * 4.0
        for idx, i in enumerate(slots):
            t = base + i * 0.25
            nxt = slots[idx + 1] if idx + 1 < len(slots) else 16
            gap = (nxt - i) * 0.25
            dur = min(gap * 0.85, 0.4 if gap <= 0.5 else 1.5)
            pitch = midi_of(0, frets[i])
            gp = pitch if pitch >= 30 else pitch + 12
            art = "sus" if gap > 0.75 else "pm"
            tr.add(t, dur, gp, 110 + (6 if i == 0 else 0), art)

    mid = os.path.join(workdir, f"{tag}.mid")
    rnd.write_guitar_midi(sc, "gtr_l", mid)
    di = os.path.join(workdir, f"{tag}_di.wav")
    rnd.render_sfz(rnd.GTX, mid, di)
    rnd.gain_stage(di, di, -6.0)
    x = dsp.load(di)
    dsp.save(di, dsp.hpf(x, 110, order=2))
    amp = os.path.join(workdir, f"{tag}_amp.wav")
    rnd.nam_process(di, amp, rnd.NAM_5150, in_gain_db=4.0)
    out = os.path.join(workdir, f"{tag}.wav")
    rnd.cab_ir(amp, out, [(rnd.IR_57, 0.0), (rnd.IR_421, -4.0)])
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--role", default="mid",
                    choices=["breakdown", "mid", "blast", "bounce"])
    ap.add_argument("--density", type=float, default=0.55)
    ap.add_argument("--offbeat", type=float, default=0.22)
    ap.add_argument("--tempo", type=float, default=150.0)
    ap.add_argument("--n", type=int, default=5)
    ap.add_argument("--discipline", action="store_true")
    ap.add_argument("--out-tag", default="cand")
    ap.add_argument("--seed", type=int, default=None)
    args = ap.parse_args()

    workdir = os.path.join(OUT_ROOT, args.out_tag)
    os.makedirs(workdir, exist_ok=True)
    role = dict(density=args.density, offbeat=args.offbeat,
               discipline=args.discipline)

    index = []
    for i in range(args.n):
        seed = (args.seed + i) if args.seed is not None else (900 + i * 37)
        rng = random.Random(seed)
        genome = r2.evolve(rng, args.role, role)
        stats = genome.stats()
        nov = r2.mask_novelty(genome.mask, args.role)
        from riffgen2 import genome_riff
        tab = genome_riff(genome, args.tempo, args.role).tab().split("\n")[-1]
        wav = render_candidate(genome, args.tempo, f"cand{i}", workdir)
        rec = dict(index=i, mask=genome.mask,
                  frets={str(k): v for k, v in genome.frets.items()},
                  tempo=args.tempo, role=args.role, density=stats["density"],
                  open_share=round(stats["open_share"], 2),
                  pedal=round(stats["pedal"], 2), novelty=nov, tab=tab,
                  wav=wav)
        with open(os.path.join(workdir, f"cand{i}.json"), "w") as f:
            json.dump(rec, f, indent=1)
        index.append(rec)
        print(f"candidate {i}: novelty={nov} open={rec['open_share']} "
              f"pedal={rec['pedal']} dens={rec['density']:.2f}\n  {tab}\n"
              f"  -> {wav}")

    with open(os.path.join(workdir, "index.txt"), "w") as f:
        for rec in index:
            f.write(f"== candidate {rec['index']} @ {rec['tempo']} BPM "
                    f"(novelty {rec['novelty']}, open {rec['open_share']}, "
                    f"pedal {rec['pedal']})\n{rec['tab']}\n\n")
    print(f"\n{args.n} candidates in {workdir}")


if __name__ == "__main__":
    main()
