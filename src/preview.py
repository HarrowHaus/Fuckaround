"""Fast preview render for MIDI iteration: real DrumGizmo drums + DI guitars
through a cheap static amp (waveshaper + real cab IR) instead of NAM, quick
static mix. ~2-3 min total vs ~20 min for the full pipeline.

Usage: python3 preview.py [t0 t1]   (optional crop, seconds)
"""

import os
import sys
import subprocess
import numpy as np

sys.path.insert(0, os.path.dirname(__file__))
import dsp
from dsp import SR
from render import (REPO, MIDI_DIR, KIT_DIR, write_all_midis,
                    render_sfz, GTX, BASS_SFZ, IR_57, IR_421)
from song import build_song

STEMS = os.path.join(REPO, "stems", "preview")


def cheap_amp(x):
    """Static high-gain stand-in: tighten lows, 3 asymmetric clip stages,
    presence tilt, then the same real V30 IR blend as the full chain."""
    from pedalboard import Pedalboard, PeakFilter
    y = np.mean(x, axis=0, keepdims=True)
    y = dsp.hpf(y, 110, order=2)               # tubescreamer-ish tighten
    y = Pedalboard([PeakFilter(800, 4.0, 0.9)])(y.astype(np.float32), SR)
    for gain, bias in ((28.0, 0.06), (14.0, -0.04), (6.0, 0.02)):
        y = np.tanh(y * gain + bias)
        y = dsp.hpf(y, 60, order=1)
    y = Pedalboard([PeakFilter(2200, 2.5, 0.8)])(y.astype(np.float32), SR)
    y = dsp.lpf(y, 9500, order=2)
    from scipy.signal import fftconvolve
    ir = np.mean(dsp.load(IR_57), axis=0) * dsp.db(-2.5)
    ir2 = np.mean(dsp.load(IR_421), axis=0)
    m = y[0]
    y = (fftconvolve(m, ir)[None, :len(m)]
         + fftconvolve(m, ir2)[None, :len(m)] * dsp.db(-4.0))
    return y * dsp.db(-dsp.peak_db(y) - 6.0)


def main():
    os.makedirs(STEMS, exist_ok=True)
    score, sec = build_song()
    write_all_midis()

    # drums (the thing we're iterating on) — real DrumGizmo render
    for f in os.listdir(STEMS):
        if f.startswith("dg"):
            os.remove(os.path.join(STEMS, f))
    subprocess.run(["drumgizmo", "-i", "midifile",
                    "-I", f"file={MIDI_DIR}/drums_dg.mid,midimap={KIT_DIR}/midimap.xml",
                    "-o", "wavfile", "-O", f"file={STEMS}/dg,srate={SR}",
                    os.path.join(KIT_DIR, "aasimonster-minimal.xml")],
                   check=True, capture_output=True)

    # guitars/bass: sfizz DI (fast) + cheap amp
    gl = f"{STEMS}/gl_di.wav"; render_sfz(GTX, f"{MIDI_DIR}/gtr_l.mid", gl)
    gr = f"{STEMS}/gr_di.wav"; render_sfz(GTX, f"{MIDI_DIR}/gtr_r.mid", gr)
    bs = f"{STEMS}/bass_di.wav"; render_sfz(BASS_SFZ, f"{MIDI_DIR}/bass.mid", bs)
    L = cheap_amp(dsp.load(gl))
    R = cheap_amp(dsp.load(gr))
    B = dsp.load(bs)
    B = np.mean(B, axis=0, keepdims=True)
    Blo, Bhi = dsp.butter_split(B, 600)
    B = Blo * dsp.db(2) + np.tanh(Bhi * 12.0) * dsp.db(-8)

    # drums quick bus: sum all mics with kick/snare forward
    n = 0
    mics = {}
    for f in sorted(os.listdir(STEMS)):
        if f.startswith("dg") and f.endswith(".wav"):
            x = dsp.load(os.path.join(STEMS, f))
            mics[f[2:-4].lower()] = x
            n = max(n, x.shape[1])

    def get(*keys, gain=0.0):
        out = np.zeros((2, n))
        for k, x in mics.items():
            if any(q in k for q in keys):
                out[:, :x.shape[1]] += dsp.to_stereo(x)[:, :n]
        return out * dsp.db(gain)
    drums = (get("kdrum", "trigger", gain=4) + get("snare", gain=3)
             + get("tom", gain=0) + get("oh", "amb", gain=-2)
             + get("hihat", "ride", gain=-4))
    drums = dsp.norm_active(drums, -14.0)

    def pad(x):
        y = np.zeros((2, n))
        s = dsp.to_stereo(x)
        y[:, :min(n, s.shape[1])] = s[:, :min(n, s.shape[1])]
        return y
    wall = np.zeros((2, n))
    wall[0, :min(n, L.shape[1])] = L[0, :min(n, L.shape[1])]
    wall[1, :min(n, R.shape[1])] = R[0, :min(n, R.shape[1])]
    wall = dsp.norm_active(dsp.highpass(wall, 90), -14.0)
    bass = dsp.norm_active(pad(B), -14.0)

    mix = drums + wall * dsp.db(-2.0) + bass * dsp.db(-6.0)

    # synth layers (subs matter for breakdown feel): reuse render.py stage
    try:
        subprocess.run([sys.executable, os.path.join(REPO, "src", "render.py"),
                        "synths"], check=True, capture_output=True)
        x = dsp.load(os.path.join(REPO, "stems", "subdrops.wav"))
        mix += pad(x) * dsp.db(-8.0)
    except Exception as e:
        print("synth preview skipped:", e)

    mix = dsp.soft_clip(mix * dsp.db(6.0))
    mix = mix * dsp.db(-1.0 - dsp.true_peak_db(mix))
    if len(sys.argv) >= 3:
        t0, t1 = float(sys.argv[1]), float(sys.argv[2])
        mix = mix[:, int(t0 * SR):int(t1 * SR)]
    out = os.path.join(REPO, "mix", "preview.wav")
    dsp.save(out, mix)
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", out,
                    "-b:a", "192k", out.replace(".wav", ".mp3")], check=True)
    print("preview written:", out.replace(".wav", ".mp3"))


if __name__ == "__main__":
    main()
