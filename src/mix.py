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
import songmod
STEMS = os.path.join(REPO, "stems", songmod.title())
MIX = os.path.join(REPO, "mix")
MASTER_NAME = songmod.title() + "_master"


def fx(board, x):
    return board(np.asarray(x, dtype=np.float32), SR).astype(np.float64)


def stem(name):
    p = os.path.join(STEMS, name + ".wav")
    if not os.path.exists(p):
        return None
    x = dsp.load(p)
    if dsp.peak_db(x) < -70.0:      # rendered but silent (track unused)
        return None
    return x


# ------------------------------------------------------------------ drums

def build_drums(rides=None):
    """Sum DrumGizmo's mic channels into kick/snare/tom/cymbal/room buses,
    process each per research, add the parallel smash bus, glue + clip.
    rides: dict of automation point-lists (seconds, dB) — 'smash' rides the
    parallel crush + room, 'plate' rides the snare plate throw, 'cym' rides
    the cymbal bus."""
    rides = rides or {}
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
    toms, got_t = bus("tom1", "tom2", "tom3", "tom4")

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
    # room mics go to the rideable smash path, not the cymbal bus
    room = fx(Pedalboard([Compressor(threshold_db=-30, ratio=8, attack_ms=2,
                                     release_ms=60), HighpassFilter(250)]),
              amb) * db(-10.0)

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
    # 30 ms pre-delay on the plate; the plate return is RIDDEN — bigger
    # throws in half-time/breakdown sections, tucked during blasts
    pd = int(0.03 * SR)
    plate = np.pad(plate, ((0, 0), (pd, 0)))[:, :snare_dry.shape[1]]
    plate = plate * db(-14)
    if "plate" in rides:
        plate = dsp.ride(plate, rides["plate"])
    snare_out = snare_dry + plate

    toms = fx(Pedalboard([
        HighpassFilter(70), PeakFilter(350, -2.5, 1.4),
        PeakFilter(5000, 3.0, 1.2),
        NoiseGate(threshold_db=-38, ratio=4, release_ms=120),
    ]), toms)

    # cymbal bus gets MIXED, not leveled: wash compression (slow attack lets
    # the stick through, clamps the bloom), dynamic de-harsh that only bites
    # when 3-5k actually piles up, and snare-keyed ducking so the crack
    # always wins over the wash
    cyms = fx(Pedalboard([
        HighpassFilter(400),
        HighShelfFilter(10000, 1.5),
        Compressor(threshold_db=-24, ratio=3.0, attack_ms=25, release_ms=140),
    ]), cyms)
    cyms = dsp.dynamic_eq(cyms, 3000, 5200, thresh_db=-30, max_cut_db=5.0)
    cyms = dsp.sc_duck(cyms, snare_dry, amount_db=2.5, thresh_db=-24,
                       attack_ms=2, release_ms=90)
    if "cym" in rides:
        cyms = dsp.ride(cyms, rides["cym"])

    shells = kick * db(0.0) + snare_out * db(0.0) + toms * db(-2.0)
    smash = fx(Pedalboard([
        Compressor(threshold_db=-34, ratio=12, attack_ms=1.0, release_ms=50),
        LowShelfFilter(90, 2.0), HighShelfFilter(8000, 2.0),
    ]), shells)
    smash = smash * db(-8.0) + room * db(-2.0)
    if "smash" in rides:
        smash = dsp.ride(smash, rides["smash"])
    drums = shells + cyms * db(-6.0) + smash

    drums = fx(Pedalboard([
        Compressor(threshold_db=-14, ratio=4, attack_ms=20, release_ms=110),
    ]), drums)
    drums = dsp.soft_clip(drums, drive_db=2.5)
    return drums, kick  # kick returned as sidechain key


# ------------------------------------------------------------------ guitars

def build_guitars(gtr_ride=None):
    l = stem("gtr_l"); r = stem("gtr_r")
    n = max(l.shape[1], r.shape[1])
    post = Pedalboard([
        HighpassFilter(90), LowpassFilter(10000),
        PeakFilter(400, -3.0, 1.2),
        PeakFilter(4000, -4.0, 6.0),
        PeakFilter(2800, -1.5, 1.5),       # vocal pocket prep
    ])
    l = fx(post, dsp.pad_to(l, n)); r = fx(post, dsp.pad_to(r, n))
    # chug bloom controlled DYNAMICALLY — only compresses 100-230 Hz when a
    # chug actually blooms, instead of a permanent EQ hole
    l = dsp.dynamic_eq(l, 100, 230, thresh_db=-26, max_cut_db=4.5,
                       attack_ms=6, release_ms=120)
    r = dsp.dynamic_eq(r, 100, 230, thresh_db=-26, max_cut_db=4.5,
                       attack_ms=6, release_ms=120)
    wall = np.zeros((2, n))
    wall[0] += np.mean(l, axis=0)          # hard pan L
    wall[1] += np.mean(r, axis=0)          # hard pan R
    # amp-in-the-room: a tiny dark early-reflection bed glued under the wall
    # (kills the 'DI into a plugin' dryness that reads as fake)
    room = fx(Pedalboard([
        Reverb(room_size=0.12, damping=0.7, wet_level=1.0, dry_level=0.0,
               width=1.0),
        HighpassFilter(200), LowpassFilter(5500),
    ]), wall)
    wall = wall + room * db(-20.0)
    if gtr_ride:
        wall = dsp.ride(wall, gtr_ride)
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

# per-song mix moves, keyed by section names (an engineer's ride sheet):
# cym_tame = pull cymbal wash in dense blast sections; smash_up = push the
# parallel crush + room in breakdowns; gtr_up = lean the wall into climaxes;
# plate_up = bigger snare throws in half-time; drops = vacuum-sweep targets
RIDE_PLAN = {
    "where_light_comes_to_die": dict(
        cym_tame=["blast_a", "peak"],
        smash_up=["breakdown1", "verse2", "final_bd"],
        gtr_up=["peak", "final_bd"],
        plate_up=["breakdown1", "verse2", "final_bd"],
        drops=["breakdown1", "final_bd"]),
    "six_feet_is_not_enough": dict(
        cym_tame=[],
        smash_up=["slam", "final"],
        gtr_up=["final"],
        plate_up=["sludge", "final"],
        drops=["bounce", "final"]),
}


def section_map():
    """Section spans in seconds from the active song's score."""
    score, sec = songmod.build_song()
    starts = {k: score.beats_to_seconds(v) for k, v in sec.items()}
    order = sorted(starts.items(), key=lambda kv: kv[1])
    total = score.beats_to_seconds(score.end_beat())
    ends = {k: (order[i + 1][1] if i + 1 < len(order) else total)
            for i, (k, _) in enumerate(order)}
    bar_s = {k: score.beats_to_seconds(sec[k]) -
             score.beats_to_seconds(max(0.0, sec[k] - 4.0))
             for k in sec}
    return starts, ends, bar_s


def ride_pts(names, starts, ends, amount_db):
    pts = []
    for nm in names:
        if nm in starts:
            pts += [(starts[nm], amount_db), (ends[nm], 0.0)]
    return sorted(pts)


def main():
    os.makedirs(MIX, exist_ok=True)
    starts, ends, bar_s = section_map()
    plan = RIDE_PLAN.get(songmod.title(), {})
    drum_rides = dict(
        smash=ride_pts(plan.get("smash_up", []), starts, ends, 3.0),
        cym=ride_pts(plan.get("cym_tame", []), starts, ends, -2.0),
        plate=ride_pts(plan.get("plate_up", []), starts, ends, 5.0),
    )
    drum_rides = {k: v for k, v in drum_rides.items() if v}
    gtr_ride = ride_pts(plan.get("gtr_up", []), starts, ends, 0.7) or None
    drums, kick_key = build_drums(drum_rides)
    guitars = build_guitars(gtr_ride)
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
        stems_gains.append((clean, -8.0))   # the bridge must breathe
    for nm, g in (("strings", -5.0), ("strings_stac", -4.0),
                  ("choir", -6.0)):
        if nm in orch:
            stems_gains.append((orch[nm], g))

    mixbus = dsp.mix_stems(stems_gains)

    # momentum: the bar before each drop gets the air sucked out of it
    # (band HPF-sweeps up, snaps back to full weight ON the downbeat);
    # subs and fx risers live OUTSIDE the vacuum so 808 tails survive stops
    drops = [starts[nm] for nm in plan.get("drops", []) if nm in starts]
    if drops:
        mixbus = dsp.vacuum_sweep(mixbus, drops,
                                  bar_s.get(plan["drops"][0], 2.0))
    low_gains = []
    if subs is not None:
        low_gains.append((subs, -2.0))
    if fxs is not None:
        low_gains.append((fxs, -6.0))
    if low_gains:
        n = max([mixbus.shape[1]] + [x.shape[1] for x, _ in low_gains])
        mixbus = dsp.pad_to(mixbus, n)
        for x, g in low_gains:
            mixbus = mixbus + dsp.pad_to(dsp.to_stereo(x), n) * db(g)

    # --------- mix bus: glue + gentle tape-ish saturation
    mixbus = fx(Pedalboard([Compressor(threshold_db=-16, ratio=2.0,
                                       attack_ms=30, release_ms=150)]), mixbus)
    mixbus = dsp.soft_clip(mixbus, drive_db=1.5)
    mixbus = mixbus * db(-6.0 - dsp.peak_db(mixbus))    # -6 dBFS headroom
    dsp.save(os.path.join(MIX, songmod.title() + "_vocal_ready.wav"), mixbus)

    # --------- mastering
    m = fx(Pedalboard([
        HighpassFilter(24),
        LowShelfFilter(100, 0.8),
        PeakFilter(400, -0.8, 1.2),
        PeakFilter(4500, 1.8, 0.9),      # presence lift (QC: was -10 rel mids)
        HighShelfFilter(9000, 1.8),
    ]), mixbus)
    lo, hi = dsp.butter_split(m, 120)
    lo = fx(Pedalboard([Compressor(threshold_db=-24, ratio=2.0, attack_ms=25,
                                   release_ms=180)]), lo)
    # clip highs only: clipping sub sines squares them off and creates huge
    # intersample overshoot that no sample-peak limiter can catch
    m = lo + dsp.soft_clip(hi, drive_db=3.0)

    # push into target loudness with clip+limit iterations, converging LUFS
    # and true peak TOGETHER (sub-heavy material creates intersample peaks
    # the sample-peak limiter can't see; correcting TP outside the loop
    # would leave the master quiet)
    target = -8.0
    for _ in range(6):
        cur = dsp.lufs(m)
        m = m * db(min(6.0, target - cur))
        mlo, mhi = dsp.butter_split(m, 100)
        mlo = fx(Pedalboard([Compressor(threshold_db=-12, ratio=6.0,
                                        attack_ms=8, release_ms=120)]), mlo)
        m = mlo + dsp.soft_clip(mhi, drive_db=1.5)
        m = fx(Pedalboard([Limiter(threshold_db=-1.5, release_ms=60)]), m)
        tp = dsp.true_peak_db(m)
        if tp > -1.0:
            m = m * db(-1.0 - tp)
        if abs(dsp.lufs(m) - target) < 0.4 and dsp.true_peak_db(m) <= -0.95:
            break

    dsp.save(os.path.join(MIX, MASTER_NAME + ".wav"), m)

    report = {
        "master_lufs_integrated": round(dsp.lufs(m), 2),
        "master_true_peak_dbtp": round(dsp.true_peak_db(m), 2),
        "master_peak_dbfs": round(dsp.peak_db(m), 2),
        "vocal_ready_peak_dbfs": round(dsp.peak_db(mixbus), 2),
        "duration_s": round(m.shape[1] / SR, 1),
    }
    with open(os.path.join(MIX, "report_" + songmod.title() + ".json"), "w") as f:
        json.dump(report, f, indent=2)
    print(json.dumps(report, indent=2))

    # 320 kbps MP3 of the master for easy listening
    import subprocess
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error",
                    "-i", os.path.join(MIX, MASTER_NAME + ".wav"),
                    "-codec:a", "libmp3lame", "-b:a", "320k",
                    os.path.join(MIX, MASTER_NAME + ".mp3")],
                   check=True)
    print("mp3 written")


if __name__ == "__main__":
    main()
