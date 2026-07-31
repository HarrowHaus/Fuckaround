"""Mix + master: implements docs/03-mixing-research.md as a deterministic chain.

Every number here traces to the research doc (Nail The Mix / URM / Sage Audio
consensus values): kick 60 Hz thump +3, 400 Hz scoop -4, 4.5k click +5;
snare 200 body +3, 500 box -3, 5k crack +4, plate 1.5 s; parallel drum crush
blended -8 dB; guitars HPF 90 / LPF 10k / -3 @ 400 / -4 notch @ 4k, hard-panned;
bass split at 180 Hz w/ dUg grit -4 dB under clean lows, sub band kick-ducked;
orchestra HPF 300 + hall + kick duck; bus glue 2:1 @ 30 ms; master = tilt EQ ->
low-band comp -> soft clip -> TP limiter, target -8 LUFS / -1.0 dBTP.
"""

import os
import sys
import glob
import json
import numpy as np

sys.path.insert(0, os.path.dirname(__file__))
import dsp
from dsp import SR, db

from pedalboard import (Pedalboard, Compressor, HighpassFilter, LowpassFilter,
                        HighShelfFilter, LowShelfFilter, PeakFilter, Reverb,
                        Delay, Chorus, Gain, Limiter, NoiseGate)

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
STEMS = os.path.join(REPO, "stems")
MIX = os.path.join(REPO, "mix")


def fx(board, x):
    return board(np.asarray(x, dtype=np.float32), SR).astype(np.float64)


def stem(name):
    p = os.path.join(STEMS, name + ".wav")
    return dsp.load(p) if os.path.exists(p) else None


# ------------------------------------------------------------------ drums

def build_drums():
    """Sum DrumGizmo's mic channels into kick/snare/tom/cymbal/room buses,
    process each per research, add the parallel smash bus, glue + clip."""
    chans = {}
    for f in glob.glob(os.path.join(STEMS, "drums", "dg*.wav")):
        base = os.path.basename(f)[2:-4].lower()   # e.g. "ohl-0", "kdruml-7"
        chans[base] = dsp.load(f)
    if not chans:
        raise RuntimeError("no drum channels rendered")
    n = max(c.shape[1] for c in chans.values())

    def bus(*keys, exclude=()):
        out = np.zeros((2, n))
        got = []
        for name, x in chans.items():
            if any(k in name for k in keys) and not any(e in name for e in exclude):
                out += dsp.pad_to(dsp.to_stereo(x), n)
                got.append(name)
        return out, got

    # Aasimonster channels: KdrumL/R, Trigger (kick click), Snare_top/bottom,
    # Snare_trigger, Tom1-4, OHL/OHR, AmbL/AmbR, Hihat, Ride
    kick, got_k = bus("kdrum")
    ktrig, _ = bus("trigger", exclude=("snare",))
    kick = kick + dsp.pad_to(dsp.to_stereo(ktrig), n) * db(-4.0)
    snare, got_s = bus("snare_top", "snare_bottom")
    strig, _ = bus("snare_trigger")
    snare = snare + dsp.pad_to(dsp.to_stereo(strig), n) * db(-8.0)
    toms, got_t = bus("tom")

    def pair(lkey, rkey):
        out = np.zeros((2, n))
        for name, x in chans.items():
            m = np.mean(dsp.pad_to(dsp.to_stereo(x), n), axis=0)
            if lkey in name:
                out[0] += m
            elif rkey in name:
                out[1] += m
        return out
    ohs = pair("ohl", "ohr"); got_c = ["ohl", "ohr"]
    amb = pair("ambl", "ambr"); got_a = ["ambl", "ambr"]
    hats, got_h = bus("hihat", "ride")
    print("drum buses:", dict(kick=got_k, snare=got_s, toms=got_t,
                              oh=got_c, amb=got_a, close_cym=got_h))
    # stereo-place OH pair; room compressed low; close cymbal mics tucked in
    cyms = ohs + hats * db(-3.0)
    room = fx(Pedalboard([Compressor(threshold_db=-30, ratio=8, attack_ms=2,
                                     release_ms=60), HighpassFilter(250)]),
              amb) * db(-10.0)
    cyms = cyms + room

    kick = fx(Pedalboard([
        HighpassFilter(35),
        PeakFilter(60, 3.0, 0.8),
        PeakFilter(400, -4.0, 1.4),
        PeakFilter(4500, 5.0, 1.6),
        Compressor(threshold_db=-18, ratio=4, attack_ms=6, release_ms=80),
    ]), kick)
    kick = dsp.soft_clip(kick, drive_db=3.0)

    snare_dry = fx(Pedalboard([
        HighpassFilter(90),
        PeakFilter(200, 3.0, 1.2),
        PeakFilter(500, -3.0, 1.6),
        PeakFilter(5000, 4.0, 1.4),
        Compressor(threshold_db=-16, ratio=5, attack_ms=18, release_ms=200),
    ]), snare)
    snare_dry = dsp.transient_shape(snare_dry, 2.5)
    plate = fx(Pedalboard([
        Reverb(room_size=0.45, damping=0.55, wet_level=1.0, dry_level=0.0,
               width=0.9),
        HighpassFilter(450), LowpassFilter(7500),
    ]), snare_dry)
    # 30 ms pre-delay on the plate
    pd = int(0.03 * SR)
    plate = np.pad(plate, ((0, 0), (pd, 0)))[:, :snare_dry.shape[1]]
    snare_out = snare_dry + plate * db(-14)

    toms = fx(Pedalboard([
        HighpassFilter(70), PeakFilter(350, -2.5, 1.4),
        PeakFilter(5000, 3.0, 1.2),
        NoiseGate(threshold_db=-38, ratio=4, release_ms=120),
    ]), toms)

    cyms = fx(Pedalboard([
        HighpassFilter(400),
        PeakFilter(3800, -2.5, 2.0),      # blast wash de-harsh
        HighShelfFilter(10000, 1.5),
    ]), cyms)

    shells = kick * db(0.0) + snare_out * db(0.0) + toms * db(-2.0)
    smash = fx(Pedalboard([
        Compressor(threshold_db=-34, ratio=12, attack_ms=1.0, release_ms=50),
        LowShelfFilter(90, 2.0), HighShelfFilter(8000, 2.0),
    ]), shells)
    drums = shells + cyms * db(-6.0) + smash * db(-8.0)

    drums = fx(Pedalboard([
        Compressor(threshold_db=-14, ratio=4, attack_ms=20, release_ms=110),
    ]), drums)
    drums = dsp.soft_clip(drums, drive_db=2.5)
    return drums, kick  # kick returned as sidechain key


# ------------------------------------------------------------------ guitars

def build_guitars():
    l = stem("gtr_l"); r = stem("gtr_r")
    n = max(l.shape[1], r.shape[1])
    post = Pedalboard([
        HighpassFilter(90), LowpassFilter(10000),
        PeakFilter(400, -3.0, 1.2),
        PeakFilter(4000, -4.0, 6.0),
        PeakFilter(140, -1.5, 1.4),        # chug bloom control
        PeakFilter(2800, -1.5, 1.5),       # vocal pocket prep
    ])
    l = fx(post, dsp.pad_to(l, n)); r = fx(post, dsp.pad_to(r, n))
    wall = np.zeros((2, n))
    wall[0] += np.mean(l, axis=0)          # hard pan L
    wall[1] += np.mean(r, axis=0)          # hard pan R
    return wall


def build_lead(bpm=130.0):
    x = stem("lead")
    if x is None:
        return None
    q = 60.0 / bpm
    board = Pedalboard([
        HighpassFilter(160), LowpassFilter(9000),
        PeakFilter(3500, -2.0, 3.0),
        Compressor(threshold_db=-20, ratio=3, attack_ms=15, release_ms=120),
    ])
    x = fx(board, x)
    mono = np.mean(x, axis=0)
    dl = fx(Pedalboard([Delay(delay_seconds=q, feedback=0.25, mix=1.0),
                        HighpassFilter(400), LowpassFilter(7000)]),
            np.vstack([mono, mono]))
    dr = fx(Pedalboard([Delay(delay_seconds=q * 0.75, feedback=0.25, mix=1.0),
                        HighpassFilter(400), LowpassFilter(7000)]),
            np.vstack([mono, mono]))
    verb = fx(Pedalboard([Reverb(room_size=0.6, damping=0.5, wet_level=1.0,
                                 dry_level=0.0),
                          HighpassFilter(400), LowpassFilter(8000)]), x)
    out = x.copy()
    out[0] += dl[0] * db(-14); out[1] += dr[1] * db(-14)
    out += verb * db(-16)
    return out


def build_clean():
    x = stem("clean")
    if x is None:
        return None
    x = fx(Pedalboard([HighpassFilter(180), LowpassFilter(9500),
                       Chorus(rate_hz=0.6, depth=0.35, mix=0.4),
                       Reverb(room_size=0.7, damping=0.4, wet_level=0.35,
                              dry_level=0.75)]), x)
    return x


# ------------------------------------------------------------------ bass

def build_bass(kick_key):
    lo = stem("bass_lo"); hi = stem("bass_hi")
    n = max(lo.shape[1], hi.shape[1])
    lo = dsp.pad_to(lo, n); hi = dsp.pad_to(hi, n)
    lo = fx(Pedalboard([Compressor(threshold_db=-26, ratio=6, attack_ms=8,
                                   release_ms=90)]), lo)
    hi = fx(Pedalboard([PeakFilter(400, -2.0, 1.4), PeakFilter(1100, 2.0, 1.2),
                        Compressor(threshold_db=-20, ratio=4, attack_ms=10,
                                   release_ms=80)]), hi)
    bass = lo + hi * db(-4.0)
    k = dsp.pad_to(kick_key, n)
    bass = dsp.sc_duck(bass, k, amount_db=2.5, thresh_db=-24,
                       attack_ms=2, release_ms=45, band=(20, 110))
    bass = dsp.mono_below(bass, 120)
    return bass


# ------------------------------------------------------------------ orchestra

def build_orchestra(kick_key):
    out = {}
    hall = Pedalboard([Reverb(room_size=0.85, damping=0.45, wet_level=0.5,
                              dry_level=0.6, width=1.0),
                       HighpassFilter(320), LowpassFilter(8500)])
    for name, hp in (("strings", 300), ("strings_stac", 260), ("choir", 300)):
        x = stem(name)
        if x is None:
            continue
        x = fx(Pedalboard([HighpassFilter(hp), PeakFilter(3000, -2.0, 1.6)]), x)
        x = fx(hall, x)
        if kick_key is not None:
            k = dsp.pad_to(kick_key, x.shape[1])
            x = dsp.sc_duck(x, k, amount_db=1.5, thresh_db=-24,
                            attack_ms=3, release_ms=60)
        out[name] = x
    return out


# ------------------------------------------------------------------ main mix

def main():
    os.makedirs(MIX, exist_ok=True)
    drums, kick_key = build_drums()
    guitars = build_guitars()
    lead = build_lead()
    clean = build_clean()
    bass = build_bass(kick_key)
    orch = build_orchestra(kick_key)
    subs = stem("subdrops")
    fxs = stem("fx")

    # normalize each bus to a common active-RMS reference so the static gain
    # structure below is meaningful regardless of amp-capture output levels
    drums = dsp.norm_active(drums, -14.0)
    guitars = dsp.norm_active(guitars, -14.0)
    bass = dsp.norm_active(bass, -14.0)
    if lead is not None:
        lead = dsp.norm_active(lead, -16.0)
    if clean is not None:
        clean = dsp.norm_active(clean, -18.0)
    for k in list(orch):
        orch[k] = dsp.norm_active(orch[k], -18.0)
    if subs is not None:
        subs = subs * dsp.db(-6.0 - dsp.peak_db(subs))
    if fxs is not None:
        fxs = fxs * dsp.db(-6.0 - dsp.peak_db(fxs))

    if subs is not None:
        subs = dsp.mono_below(subs, 300)
        subs = fx(Pedalboard([Limiter(threshold_db=-6), LowpassFilter(160)]),
                  subs)

    # --------- static gain structure (drums forward, per research)
    # relative gains on top of the normalized buses (research level map:
    # drums forward, guitars the wall just under them, bass -3..-6 under
    # guitars, symphonics -6..-10 under guitars, leads ride above the wall)
    stems_gains = [(drums, 0.0), (guitars, -2.5), (bass, -5.5)]
    if lead is not None:
        stems_gains.append((lead, 1.0))
    if clean is not None:
        stems_gains.append((clean, -2.0))
    for nm, g in (("strings", -5.0), ("strings_stac", -4.0),
                  ("choir", -6.0)):
        if nm in orch:
            stems_gains.append((orch[nm], g))
    if subs is not None:
        stems_gains.append((subs, -2.0))
    if fxs is not None:
        stems_gains.append((fxs, -6.0))

    mixbus = dsp.mix_stems(stems_gains)

    # --------- mix bus: glue + gentle tape-ish saturation
    mixbus = fx(Pedalboard([Compressor(threshold_db=-16, ratio=2.0,
                                       attack_ms=30, release_ms=150)]), mixbus)
    mixbus = dsp.soft_clip(mixbus, drive_db=1.5)
    mixbus = mixbus * db(-6.0 - dsp.peak_db(mixbus))    # -6 dBFS headroom
    dsp.save(os.path.join(MIX, "instrumental_vocal_ready.wav"), mixbus)

    # --------- mastering
    m = fx(Pedalboard([
        HighpassFilter(24),
        LowShelfFilter(100, 0.8),
        PeakFilter(400, -0.8, 1.2),
        HighShelfFilter(9000, 1.2),
    ]), mixbus)
    lo, hi = dsp.butter_split(m, 120)
    lo = fx(Pedalboard([Compressor(threshold_db=-24, ratio=2.0, attack_ms=25,
                                   release_ms=180)]), lo)
    m = lo + hi
    m = dsp.soft_clip(m, drive_db=3.0)

    # push into target loudness with clip+limit iterations
    target = -8.0
    for _ in range(4):
        cur = dsp.lufs(m)
        m = m * db(min(6.0, target - cur))
        m = dsp.soft_clip(m, drive_db=1.5)
        m = fx(Pedalboard([Limiter(threshold_db=-1.5, release_ms=60)]), m)
        if abs(dsp.lufs(m) - target) < 0.4:
            break
    # true peak safety
    tp = dsp.true_peak_db(m)
    if tp > -1.0:
        m = m * db(-1.0 - tp)

    dsp.save(os.path.join(MIX, "where_light_comes_to_die_master.wav"), m)

    report = {
        "master_lufs_integrated": round(dsp.lufs(m), 2),
        "master_true_peak_dbtp": round(dsp.true_peak_db(m), 2),
        "master_peak_dbfs": round(dsp.peak_db(m), 2),
        "vocal_ready_peak_dbfs": round(dsp.peak_db(mixbus), 2),
        "duration_s": round(m.shape[1] / SR, 1),
    }
    with open(os.path.join(MIX, "report.json"), "w") as f:
        json.dump(report, f, indent=2)
    print(json.dumps(report, indent=2))

    # 320 kbps MP3 of the master for easy listening
    import subprocess
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error",
                    "-i", os.path.join(MIX, "where_light_comes_to_die_master.wav"),
                    "-codec:a", "libmp3lame", "-b:a", "320k",
                    os.path.join(MIX, "where_light_comes_to_die_master.mp3")],
                   check=True)
    print("mp3 written")


if __name__ == "__main__":
    main()
