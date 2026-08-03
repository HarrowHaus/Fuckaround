"""DSP utilities implementing the research mix recipes.

pedalboard supplies EQ/comp/convolution/limiting; this module adds what it
lacks: sidechain ducking, band splitting, soft clipping, LUFS normalization,
and stem alignment helpers.
"""

import numpy as np
import scipy.signal as sig
import soundfile as sf
import pyloudnorm as pyln

SR = 48000


def load(path, sr=SR):
    x, fs = sf.read(path, always_2d=True)
    x = x.T.astype(np.float64)  # (ch, n)
    if fs != sr:
        n = int(round(x.shape[1] * sr / fs))
        x = sig.resample(x, n, axis=1)
    return x


def save(path, x, sr=SR, subtype="FLOAT"):
    sf.write(path, np.asarray(x).T, sr, subtype=subtype)


def to_stereo(x):
    x = np.atleast_2d(x)
    if x.shape[0] == 1:
        return np.vstack([x, x])
    return x[:2]


def pad_to(x, n):
    if x.shape[1] >= n:
        return x[:, :n]
    return np.pad(x, ((0, 0), (0, n - x.shape[1])))


def mix_stems(stems_gains, n=None):
    """stems_gains: list of (array, gain_db). Returns summed stereo."""
    n = n or max(s.shape[1] for s, _ in stems_gains)
    out = np.zeros((2, n))
    for s, g in stems_gains:
        s = pad_to(to_stereo(s), n)
        out += s * db(g)
    return out


def db(x):
    return 10.0 ** (x / 20.0)


def peak_db(x):
    p = np.max(np.abs(x)) + 1e-12
    return 20 * np.log10(p)


def rms_db(x):
    return 20 * np.log10(np.sqrt(np.mean(x ** 2)) + 1e-12)


def active_rms_db(x, gate_db=-60.0):
    """RMS over active regions only (100 ms blocks above the gate), so sparse
    stems aren't penalized by their silence when normalizing."""
    m = np.mean(np.atleast_2d(x) ** 2, axis=0)
    blk = int(0.1 * SR)
    nb = len(m) // blk
    if nb == 0:
        return rms_db(x)
    b = m[:nb * blk].reshape(nb, blk).mean(axis=1)
    keep = b > (10 ** (gate_db / 10.0))
    if not np.any(keep):
        return rms_db(x)
    return 10 * np.log10(b[keep].mean() + 1e-24)


def norm_active(x, target_db):
    """Scale so active RMS hits target_db."""
    return x * db(target_db - active_rms_db(x))


# ------------------------------------------------------------------ filters

def butter_split(x, freq, sr=SR, order=4):
    """Linkwitz-style band split: returns (low, high), phase-coherent enough
    for parallel processing when both bands are recombined."""
    sos_lo = sig.butter(order, freq, "low", fs=sr, output="sos")
    sos_hi = sig.butter(order, freq, "high", fs=sr, output="sos")
    return sig.sosfiltfilt(sos_lo, x, axis=-1), sig.sosfiltfilt(sos_hi, x, axis=-1)


def hpf(x, freq, sr=SR, order=4):
    sos = sig.butter(order, freq, "high", fs=sr, output="sos")
    return sig.sosfiltfilt(sos, x, axis=-1)


def lpf(x, freq, sr=SR, order=4):
    sos = sig.butter(order, freq, "low", fs=sr, output="sos")
    return sig.sosfiltfilt(sos, x, axis=-1)


def mono_below(x, freq, sr=SR):
    """Research rule: mono below ~120 Hz."""
    lo, hi = butter_split(x, freq, sr)
    lo_m = np.mean(lo, axis=0, keepdims=True)
    return np.vstack([lo_m, lo_m]) + hi


# ------------------------------------------------------------ dynamics

def envelope(x, sr=SR, attack_ms=5.0, release_ms=60.0, decim=8):
    """Peak envelope follower (mono reduction of the key signal).
    Runs at sr/decim via block-max decimation for speed; ducking control
    signals don't need full-rate resolution."""
    key = np.max(np.abs(np.atleast_2d(x)), axis=0)
    n = len(key)
    pad = (-n) % decim
    kd = np.pad(key, (0, pad)).reshape(-1, decim).max(axis=1)
    esr = sr / decim
    a_a = np.exp(-1.0 / (esr * attack_ms / 1000.0))
    a_r = np.exp(-1.0 / (esr * release_ms / 1000.0))
    env = np.empty_like(kd)
    e = 0.0
    for i in range(len(kd)):
        v = kd[i]
        coef = a_a if v > e else a_r
        e = coef * e + (1 - coef) * v
        env[i] = e
    return np.repeat(env, decim)[:n]


def sc_duck(target, key, amount_db=3.0, thresh_db=-30.0,
            attack_ms=2.0, release_ms=50.0, sr=SR, band=None):
    """Sidechain duck `target` from `key`. If band=(lo,hi) only that band of
    the target is ducked (dynamic-EQ style, per research)."""
    env = envelope(key, sr, attack_ms, release_ms)
    env_db = 20 * np.log10(env + 1e-9)
    over = np.clip((env_db - thresh_db) / max(1e-9, -thresh_db), 0, 1)
    gain = 10 ** ((-amount_db * over) / 20.0)
    if band is None:
        return target * gain
    lo, rest = butter_split(target, band[1], sr)
    if band[0] > 20:
        sub, lo_mid = butter_split(lo, band[0], sr)
        return sub + lo_mid * gain + rest
    return lo * gain + rest


def soft_clip(x, drive_db=0.0, ceiling_db=0.0):
    """tanh soft clipper — the modern metal loudness engine (research §5)."""
    c = db(ceiling_db)
    g = db(drive_db)
    return np.tanh(x * g / c) * c


def transient_shape(x, attack_gain_db=3.0, sr=SR):
    """Simple transient enhancer: fast-minus-slow envelope drives gain."""
    fast = envelope(x, sr, 0.5, 30.0)
    slow = envelope(x, sr, 12.0, 120.0)
    diff = np.clip((fast - slow) / (slow + 1e-9), 0, 3.0)
    gain = 1.0 + (db(attack_gain_db) - 1.0) * (diff / 3.0)
    return x * gain


# ------------------------------------------------------------ loudness

def lufs(x, sr=SR):
    meter = pyln.Meter(sr)
    return meter.integrated_loudness(np.asarray(x).T)


def normalize_lufs(x, target=-8.0, sr=SR):
    cur = lufs(x, sr)
    return x * db(target - cur), cur


def ride(x, points, sr=SR, ramp_s=0.15):
    """Fader automation: points = [(t_seconds, gain_db), ...] step targets;
    each step ramps over ramp_s. Returns x with the ride applied."""
    n = np.atleast_2d(x).shape[1]
    env = np.zeros(n)
    pts = sorted(points)
    cur = 0.0
    idx = 0
    for t, g in pts:
        i = min(n, max(0, int(t * sr)))
        env[idx:i] = cur
        j = min(n, i + int(ramp_s * sr))
        if j > i:
            env[i:j] = np.linspace(cur, g, j - i)
        cur = g
        idx = j
    env[idx:] = cur
    return np.atleast_2d(x) * (10.0 ** (env / 20.0))[None, :]


def bandpass(x, lo, hi, sr=SR, order=2):
    from scipy.signal import butter, sosfiltfilt
    sos = butter(order, [lo / (sr / 2), hi / (sr / 2)], btype="band",
                 output="sos")
    return sosfiltfilt(sos, np.atleast_2d(x), axis=1)


def dynamic_eq(x, lo, hi, thresh_db=-28.0, max_cut_db=5.0,
               attack_ms=4.0, release_ms=90.0, sr=SR):
    """Dynamic band cut: attenuates [lo,hi] only when that band is hot —
    de-harsh / de-bloom that breathes instead of a static notch."""
    band = bandpass(x, lo, hi, sr)
    env = envelope(band, sr, attack_ms, release_ms)
    env_db = 20 * np.log10(env + 1e-9)
    over = np.clip(env_db - thresh_db, 0.0, None)
    cut_db = np.clip(over * 0.8, 0.0, max_cut_db)
    gain = 10.0 ** (-cut_db / 20.0)
    return x - band + band * gain[None, :]


def vacuum_sweep(x, drop_times, bar_s, sr=SR, f_hi=350.0):
    """Pre-drop momentum: over the bar before each drop, crossfade the full
    mix into a high-passed version (the 'air gets sucked out' move), then
    snap back to full weight exactly ON the drop."""
    y = np.atleast_2d(x).copy()
    filt = hpf(y, f_hi, order=2)
    n = y.shape[1]
    for td in drop_times:
        i1 = int(td * sr)
        i0 = int((td - bar_s) * sr)
        if i0 < 0 or i1 > n or i1 <= i0:
            continue
        fade = np.linspace(0.0, 1.0, i1 - i0) ** 1.5
        y[:, i0:i1] = y[:, i0:i1] * (1 - fade) + filt[:, i0:i1] * fade
    return y


def true_peak_db(x, sr=SR):
    up = sig.resample_poly(x, 4, 1, axis=-1)
    return peak_db(up)
