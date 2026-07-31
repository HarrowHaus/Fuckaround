"""Quality control: objective checks of the master against modern deathcore
reference characteristics (loudness, crest, spectral tilt, stereo image,
section dynamics, vocal pocket headroom)."""

import os
import sys
import json
import numpy as np

sys.path.insert(0, os.path.dirname(__file__))
import dsp
from dsp import SR

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def band_db(x, lo, hi):
    m = np.mean(x, axis=0)
    f = np.fft.rfftfreq(len(m), 1 / SR)
    S = np.abs(np.fft.rfft(m * np.hanning(len(m)))) ** 2
    sel = (f >= lo) & (f < hi)
    return 10 * np.log10(S[sel].mean() + 1e-24)


def main():
    import songmod
    x = dsp.load(os.path.join(REPO, "mix", songmod.title() + "_master.wav"))
    n = x.shape[1]
    out = {}
    out["lufs_integrated"] = round(dsp.lufs(x), 2)
    out["true_peak_dbtp"] = round(dsp.true_peak_db(x), 2)
    rms = dsp.rms_db(x)
    out["crest_db"] = round(dsp.peak_db(x) - rms, 1)

    # spectral balance relative to 400-1k mids (typical mastered metal:
    # lows +6..+12, presence -2..-8, air -10..-25)
    ref = band_db(x, 400, 1000)
    for name, (lo, hi) in dict(sub=(25, 60), low=(60, 150), lowmid=(150, 400),
                               himid=(1000, 3000), presence=(3000, 6000),
                               air=(8000, 16000)).items():
        out["spectrum_" + name] = round(band_db(x, lo, hi) - ref, 1)

    # stereo: correlation + side level (guitars hard-panned -> corr ~0.3-0.8)
    l, r = x[0], x[1]
    corr = np.corrcoef(l, r)[0, 1]
    side = (l - r) / 2
    mid = (l + r) / 2
    out["stereo_correlation"] = round(float(corr), 2)
    out["side_mid_db"] = round(dsp.rms_db(side) - dsp.rms_db(mid), 1)
    lo_band, _ = dsp.butter_split(x, 120)
    ls, rs = lo_band[0], lo_band[1]
    out["low_band_correlation"] = round(float(np.corrcoef(ls, rs)[0, 1]), 2)

    # section dynamics: short-term LUFS at landmarks
    import pyloudnorm as pyln
    meter = pyln.Meter(SR)
    from songmod import build_song
    score, sec = build_song()
    marks = {name: score.beats_to_seconds(beat) + 2.0
             for name, beat in sec.items()}
    for name, t in marks.items():
        i0 = int(t * SR)
        seg = x[:, i0:i0 + 3 * SR]
        if seg.shape[1] > SR:
            try:
                out["st_lufs_" + name] = round(meter.integrated_loudness(seg.T), 1)
            except Exception:
                pass

    # vocal pocket: energy in 2-4k vs total (want room for screams)
    total = band_db(x, 60, 12000)
    out["pocket_2k4k_vs_total_db"] = round(band_db(x, 2000, 4000) - total, 1)

    print(json.dumps(out, indent=2))
    with open(os.path.join(REPO, "mix", "qc.json"), "w") as f:
        json.dump(out, f, indent=2)


if __name__ == "__main__":
    main()
