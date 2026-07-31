"""Synthesized layers: tuned sub drops, risers, dive bombs, choir pad fallback.

Sub drop spec (research): sine at the section root, pitch falling ~1 octave
over the tail, 60 ms fade-in so the kick transient wins, light saturation so
it reads on phones, mono.
"""

import numpy as np
from dsp import SR, db, soft_clip, lpf, hpf


def midi_hz(m):
    return 440.0 * 2 ** ((m - 69) / 12.0)


def sub_drop(pitch_midi, dur_s, vel=127, sr=SR):
    n = int(dur_s * sr)
    t = np.arange(n) / sr
    f0 = midi_hz(pitch_midi)
    # pitch envelope: hold 30%, then glide down one octave
    glide = np.clip((t - dur_s * 0.3) / (dur_s * 0.7), 0, 1)
    f = f0 * 2 ** (-glide)
    phase = 2 * np.pi * np.cumsum(f) / sr
    x = np.sin(phase)
    # amp: 60 ms fade-in (kick wins), exponential tail
    amp = np.minimum(t / 0.06, 1.0) * np.exp(-t / (dur_s * 0.55))
    x = x * amp * (vel / 127.0)
    x = soft_clip(x, drive_db=6.0) * 0.7      # 2nd/3rd harmonic content
    x = lpf(x, 220, sr)
    return np.vstack([x, x])


def riser(dur_s, sr=SR, to_hz=9000.0):
    """Filtered-noise sweep: HP cutoff climbs, amplitude swells."""
    n = int(dur_s * sr)
    x = np.random.default_rng(7).standard_normal(n) * 0.5
    # time-varying brightness via crossfaded filtered copies
    lo = hpf(lpf(x, 1200, sr), 200, sr)
    hi = hpf(x, 2500, sr)
    t = np.linspace(0, 1, n)
    swell = t ** 2.2
    x = (lo * (1 - t) + hi * t) * swell * 0.8
    x = lpf(x, to_hz, sr)
    st = np.vstack([x, np.roll(x, int(0.007 * sr))])  # wide
    return st


def dive_bomb(pitch_midi, dur_s, sr=SR):
    """Distorted octave dive under the final ring-out."""
    n = int(dur_s * sr)
    t = np.arange(n) / sr
    f0 = midi_hz(pitch_midi)
    f = f0 * 2 ** (-1.6 * np.clip(t / dur_s, 0, 1))
    phase = 2 * np.pi * np.cumsum(f) / sr
    x = np.sign(np.sin(phase)) * 0.4 + np.sin(phase) * 0.6  # square+sine
    x = soft_clip(x, drive_db=10.0)
    amp = np.exp(-t / (dur_s * 0.8))
    x = lpf(x * amp, 900, sr) * 0.8
    return np.vstack([x, x])


def impact(sr=SR):
    """Downbeat impact: sub thump + noise burst (industrial layer)."""
    n = int(0.9 * sr)
    t = np.arange(n) / sr
    f = 65 * 2 ** (-t * 3)
    phase = 2 * np.pi * np.cumsum(f) / sr
    body = np.sin(phase) * np.exp(-t * 7)
    noise = np.random.default_rng(3).standard_normal(n) * np.exp(-t * 28) * 0.5
    x = soft_clip(body + hpf(noise, 900, sr), 4.0)
    return np.vstack([x, x]) * 0.9


def choir_pad(pitch_midi, dur_s, vel=90, sr=SR):
    """Fallback formant-ish 'ah' pad if no choir samples are available:
    detuned saws through vowel resonances."""
    n = int(dur_s * sr)
    t = np.arange(n) / sr
    f0 = midi_hz(pitch_midi)
    x = np.zeros(n)
    rng = np.random.default_rng(int(pitch_midi))
    for det in (-0.12, -0.05, 0.0, 0.06, 0.11):
        f = f0 * 2 ** (det / 12) * (1 + 0.004 * np.sin(2 * np.pi * (5 + det) * t))
        ph = 2 * np.pi * np.cumsum(f) / sr + rng.uniform(0, 6.28)
        x += sig_saw(ph) * 0.2
    # vowel 'ah' formants: 800, 1150, 2900 Hz
    from scipy.signal import sosfiltfilt, butter
    y = np.zeros_like(x)
    for fc, g in ((800, 1.0), (1150, 0.63), (2900, 0.25)):
        sos = butter(2, [fc * 0.82, fc * 1.22], "bandpass", fs=sr, output="sos")
        y += sosfiltfilt(sos, x) * g
    y = y + x * 0.15
    a = np.minimum(t / 0.4, 1) * np.minimum((dur_s - t) / 0.6, 1).clip(0, 1)
    y = y * a * (vel / 127.0) * 0.5
    return np.vstack([y, np.roll(y, int(0.011 * sr))])


def sig_saw(phase):
    return 2 * ((phase / (2 * np.pi)) % 1.0) - 1.0
