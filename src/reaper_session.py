"""Generate a full REAPER session from the active song, render it headless.

The composition layer moves INTO the DAW: tempo map, section regions, and
every part as MIDI items (guitars with keyswitches, bass, drums, sub layer).
Instrument audio is rendered by the existing offline stage (NAM captures
aren't hosted in-session yet — the DI MIDI tracks ship muted so a NAM VST3
on the user's machine can take over). The MIX is 100%% in-session: drum mic
items under bus parents, LSP EQ/comp chains carrying the modern2026 numbers
(docs/19), Dragonfly plate, JSFX clip/limit master, and an FX-param envelope
for the pre-drop vacuum sweep.

Flow: python (this file) emits data.lua + build.lua -> headless REAPER
builds the session, saves .RPP, renders master -> python measures LUFS/TP
and re-renders with an adjusted master trim until on target.
"""

import os
import sys
import glob
import json
import subprocess

sys.path.insert(0, os.path.dirname(__file__))
import numpy as np
import dsp
from dsp import SR

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REAPER = os.path.join(REPO, "tools", "reaper_linux_x86_64", "REAPER", "reaper")
SCRATCH = os.environ.get("SCRATCH", "/tmp")

import songmod
import render as rnd
from score import Note

SONGDIR = os.path.join(REPO, "songs", songmod.title())
STEMS = os.path.join(SONGDIR, "stems")
OUTDIR = os.path.join(SONGDIR, "reaper")
MIXDIR = SONGDIR
RPP = os.path.join(OUTDIR, songmod.title() + ".rpp")


def lua_quote(s):
    return '"' + str(s).replace("\\", "\\\\").replace('"', '\\"') + '"'


def stem_path(name):
    """Songs migrated to songs/<slug>/stems/ carry FLAC (re-encoded to
    save space); freshly rendered songs still have the original WAV."""
    flac = os.path.join(STEMS, name + ".flac")
    return flac if os.path.exists(flac) else os.path.join(STEMS, name + ".wav")


def note_events(score, track, transpose=0, keyswitches=False):
    """[(start_s, end_s, pitch, vel)] for a score track, with guitar
    keyswitch events merged in when asked (beat-space -> seconds)."""
    if track not in score.tracks:
        return []
    evs = []
    notes = score.tracks[track].notes
    if keyswitches:
        for (st, du, pi, ve) in rnd.guitar_keyswitches(notes):
            evs.append((score.beats_to_seconds(st),
                        score.beats_to_seconds(st + du), pi, ve))
    for n in notes:
        evs.append((score.beats_to_seconds(n.start),
                    score.beats_to_seconds(n.start + n.dur),
                    n.pitch + transpose, n.vel))
    return sorted(evs)


def drum_events(score):
    mapping = rnd.pick_drum_mapping(
        rnd.load_midimap(os.path.join(rnd.KIT_DIR, "midimap.xml")))
    evs = []
    for n in score.tracks["drums"].notes:
        name = next((t for t in n.tags if t in mapping), None)
        if name:
            evs.append((score.beats_to_seconds(n.start),
                        score.beats_to_seconds(n.start) + 0.25,
                        mapping[name], n.vel))
    return sorted(evs)


def active_rms_gain(files, target=-14.0):
    """Reproduce mix.py's norm_active bus staging: gain that brings the
    summed bus to target active-RMS."""
    xs = [dsp.load(f) for f in files if os.path.exists(f)]
    if not xs:
        return 0.0
    n = max(x.shape[1] for x in xs)
    s = np.zeros((2, n))
    for x in xs:
        s += dsp.pad_to(dsp.to_stereo(x), n)
    r = dsp.active_rms_db(s) if hasattr(dsp, "active_rms_db") else None
    if r is None:
        m = np.mean(s ** 2, axis=0)
        g = np.sqrt(np.maximum(m, 1e-12))
        gate = g > (10 ** (-45 / 20))
        r = 20 * np.log10(np.sqrt(np.mean(m[gate])) + 1e-12) if gate.any() \
            else -60.0
    return round(target - r, 2)


# FX descriptors: (add_name, {param_substring: raw_value})
def PEQ(bands, extra=None):
    """bands: list of (idx, type, freq, gain_db, q). type in
    {'bell','hipass','lopass','hishelf','loshelf'}"""
    d = {"_fx": "LSP Parametric Equalizer x8 Stereo",
         "_bands": bands}
    if extra:
        d.update(extra)
    return d


def COMP(thr_db, ratio, att_ms, rel_ms, makeup_db=0.0):
    return {"_fx": "LSP Compressor Stereo",
            "Attack time": att_ms, "Release time": rel_ms,
            "Ratio": ratio, "Threshold": 10 ** (thr_db / 20.0),
            "Makeup gain": 10 ** (makeup_db / 20.0)}


def LIMIT(thr_db):
    return {"_fx": "LSP Limiter Stereo",
            "Threshold": 10 ** (thr_db / 20.0), "Lookahead": 5.0,
            "Oversampling": 3, "Gain boost": 0}


def JSVOL(vol_db):
    # sliders: "Adjustment (dB)" (defaults +6!) and "Max Volume (dB)" clamp
    return {"_fx": "JS: utility/volume", "Adjustment": vol_db,
            "Max Volume": 150.0}


def CLIP(drive_db):
    """LSP Clipper: threshold-style soft clip; sigmoid function, dB in raw
    gain units. drive_db maps to how hard the signal leans on the ceiling."""
    # ceiling sits just under full scale; loudness comes from DRIVING into
    # it (the trim upstream), not from lowering the ceiling
    return {"_fx": "LSP Clipper Stereo",
            "Clipping threshold": 0.94}


def PLATE():
    return {"_fx": "Dragonfly Plate Reverb",
            "Dry Level": 0.0, "Wet Level": 100.0, "Decay": 1.5,
            "Low Cut": 450.0, "High Cut": 7500.0}


def build():
    os.makedirs(OUTDIR, exist_ok=True)
    score, sec = songmod.build_song()
    end_s = score.beats_to_seconds(score.end_beat()) + 3.0

    # ---- tempo map + regions
    tempo = [(score.beats_to_seconds(ts.start_beat), ts.bpm)
             for ts in score.tempo_map]
    regions = []
    order = sorted(sec.items(), key=lambda kv: kv[1])
    for i, (name, beat) in enumerate(order):
        t0 = score.beats_to_seconds(beat)
        t1 = score.beats_to_seconds(order[i + 1][1]) if i + 1 < len(order) \
            else end_s
        regions.append((t0, t1, name))

    # ---- MIDI source tracks (the composition, editable)
    midi_tracks = [
        ("MIDI gtr L (DI)", note_events(score, "gtr_l", keyswitches=True)),
        ("MIDI gtr R (DI)", note_events(score, "gtr_r", keyswitches=True)),
        ("MIDI lead (DI)", note_events(score, "lead", keyswitches=True)),
        ("MIDI bass", note_events(score, "bass", transpose=12)),
        ("MIDI drums", drum_events(score)),
        ("MIDI sub layer", note_events(score, "subbass")),
    ]

    # ---- drum mic items -> bus children
    dg = {}
    for pat in ("dg*.wav", "dg*.flac"):
        for f in glob.glob(os.path.join(STEMS, "drums", pat)):
            dg[os.path.basename(f).split(".")[0][2:].lower()] = f

    def picks(*keys, exclude=()):
        out = []
        for k, f in dg.items():
            if any(s in k for s in keys) and not any(e in k for e in exclude):
                out.append(f)
        return sorted(out)

    kick_files = picks("kdrum") + [(f, -4.0) for f in
                                   picks("trigger", exclude=("snare",))]
    # normalize to (file, vol) tuples
    def fv(lst, vol=0.0):
        out = []
        for x in lst:
            out.append(x if isinstance(x, tuple) else (x, vol))
        return out

    drum_children = [
        ("KICK", fv(picks("kdrum")) + fv(picks("trigger", exclude=("snare",)),
                                         -4.0), 0.0,
         [PEQ([(0, "hipass", 35, 0, 0.7), (1, "bell", 60, 3.0, 0.8),
               (2, "bell", 102, -3.0, 3.0), (3, "bell", 400, -4.0, 1.4),
               (4, "bell", 4200, 4.5, 0.8)]),
          COMP(-18, 4, 4, 60), CLIP(3.0)]),
        ("SNARE", fv(picks("snare_top", "snare_bottom")) +
         fv(picks("snare_trigger"), -8.0), 0.0,
         [PEQ([(0, "hipass", 90, 0, 0.7), (1, "bell", 200, 3.0, 1.2),
               (2, "bell", 500, -3.0, 1.6), (3, "bell", 5000, 4.0, 1.4)]),
          COMP(-16, 5, 18, 200)]),
        ("TOMS", fv(picks("tom")), -2.0,
         [PEQ([(0, "hipass", 70, 0, 0.7), (1, "bell", 350, -2.5, 1.4),
               (2, "bell", 5000, 3.0, 1.2)])]),
        ("CYMS", fv(picks("ohl"), 0.0) + fv(picks("ohr"), 0.0) +
         fv(picks("hihat", "ride"), -3.0), -6.0,
         [PEQ([(0, "hipass", 400, 0, 0.7), (1, "hishelf", 10000, 1.5, 0.7),
               (2, "bell", 4000, -2.5, 1.2)]),
          COMP(-24, 3, 25, 140)]),
        ("ROOM", fv(picks("ambl"), 0.0) + fv(picks("ambr"), 0.0), -10.0,
         [PEQ([(0, "hipass", 250, 0, 0.7)]), COMP(-30, 8, 2, 60)]),
    ]
    # hard pans for stereo mic pairs, keyed by filename fragment
    pans = {"ohl": -1.0, "ohr": 1.0, "ambl": -1.0, "ambr": 1.0}

    # ---- bus gain staging (reproduce mix.py norm_active offsets)
    g_drums = active_rms_gain(list(dg.values()))
    g_gtr = active_rms_gain([stem_path("gtr_l"),
                             stem_path("gtr_r")])
    g_bass = active_rms_gain([stem_path("bass_lo"),
                              stem_path("bass_hi")])
    g_sub = active_rms_gain([stem_path("subbass")], -16.0)
    g_lead = active_rms_gain([stem_path("lead")], -16.0)

    audio_buses = [
        ("GTRS", g_gtr - 2.5,
         [PEQ([(0, "hipass", 140, 0, 0.7), (1, "lopass", 10500, 0, 0.7),
               (2, "bell", 300, -1.5, 1.1), (3, "bell", 4000, -3.0, 5.0),
               (4, "bell", 2800, -1.0, 1.5)]), JSVOL(0.0)],
         [("GTR L", [(stem_path("gtr_l"), 0.0)], 0.0, [], -1.0),
          ("GTR R", [(stem_path("gtr_r"), 0.0)], 0.0, [], 1.0),
          ("LEAD", [(stem_path("lead"), 0.0)],
           g_lead - g_gtr + 1.0, [PEQ([(0, "hipass", 160, 0, 0.7),
                                       (1, "lopass", 9000, 0, 0.7)])], 0.0)]),
        ("BASS", g_bass - 5.5,
         [COMP(-20, 4, 10, 80)],
         [("BASS LO", [(stem_path("bass_lo"), 0.0)], -10.0,
           [], 0.0),
          ("BASS GRIND", [(stem_path("bass_hi"), 0.0)], 0.0,
           [PEQ([(0, "hipass", 250, 0, 0.7), (1, "bell", 400, -2.0, 1.4),
                 (2, "bell", 1100, 2.0, 1.2)])], 0.0)]),
        ("LOW", 0.0, [],
         [("SUBDROPS", [(stem_path("subdrops"), 0.0)], -8.0,
           [], 0.0),
          ("SUB LAYER", [(stem_path("subbass"), 0.0)],
           g_sub - 4.5, [CLIP(4.0), PEQ([(0, "lopass", 150, 0, 0.7)])], 0.0),
          ("FX", [(stem_path("fx"), 0.0)], -12.0, [], 0.0)]),
    ]

    # ---- rides (docs/18: automation-driven dynamics) as JS volume envs
    starts = {k: score.beats_to_seconds(v) for k, v in sec.items()}
    ends = {name: t1 for (t0, t1, name) in regions}
    def pts(names, amt):
        out = []
        for nm in names:
            if nm in starts:
                out += [(starts[nm] - 0.05, 0.0), (starts[nm], amt),
                        (ends[nm] - 0.05, amt), (ends[nm], 0.0)]
        return sorted(out)

    gtr_ride = pts(["finalbreak"], 0.7)
    vacuum = []
    for nm in ("frontbreak", "finalbreak"):
        if nm in starts:
            t = starts[nm]
            vacuum += [(t - 3.0, 20.0), (t - 0.06, 380.0), (t, 20.0)]

    master_fx = [
        PEQ([(0, "hipass", 30, 0, 0.7), (1, "loshelf", 80, 1.0, 0.7),
             (2, "bell", 350, -1.2, 1.1), (3, "bell", 3000, 1.2, 1.0),
             (4, "hishelf", 8500, 2.0, 0.7)]),
        COMP(-16, 2, 30, 150),
        JSVOL(0.0),          # convergence trim: drives INTO the clipper
        CLIP(4.5),
        LIMIT(-1.2),
    ]

    # ------------------------------------------------------- emit data.lua
    L = []
    L.append("SONG = {")
    L.append(f"  end_s = {end_s:.3f},")
    L.append(f"  rpp = {lua_quote(RPP)},")
    L.append(f"  render_dir = {lua_quote(MIXDIR)},")
    L.append(f"  render_pattern = {lua_quote(songmod.title() + '_reaper_master')},")
    L.append("  tempo = {" + ", ".join(
        f"{{{t:.4f}, {bpm}}}" for t, bpm in tempo) + "},")
    L.append("  regions = {" + ", ".join(
        f"{{{a:.3f}, {b:.3f}, {lua_quote(n)}}}" for a, b, n in regions) + "},")

    def emit_fx(fxlist):
        parts = []
        for f in fxlist:
            kv = []
            for k, v in f.items():
                if k == "_fx":
                    kv.append(f"fx={lua_quote(v)}")
                elif k == "_bands":
                    bb = ", ".join(
                        f"{{{i}, {lua_quote(ty)}, {fr}, {gn}, {q}}}"
                        for (i, ty, fr, gn, q) in v)
                    kv.append("bands={" + bb + "}")
                else:
                    kv.append(f"params_{len(kv)}={{name={lua_quote(k)}, "
                              f"value={v}}}")
            # collect params into array
            pl = [x.split("=", 1)[1] for x in kv if x.startswith("params_")]
            head = [x for x in kv if not x.startswith("params_")]
            parts.append("{" + ", ".join(head) +
                         (", params={" + ", ".join(pl) + "}" if pl else "") +
                         "}")
        return "{" + ", ".join(parts) + "}"

    def emit_items(items, pans_map=None):
        out = []
        for f, vol in items:
            pan = 0.0
            if pans_map:
                base = os.path.basename(f).lower()
                for frag, p in pans_map.items():
                    if frag in base:
                        pan = p
            out.append(f"{{file={lua_quote(f)}, vol={vol}, pan={pan}}}")
        return "{" + ", ".join(out) + "}"

    L.append("  drum_bus_vol = %.2f," % g_drums)
    L.append("  drums = {")
    for name, items, vol, fxl in drum_children:
        L.append(f"    {{name={lua_quote(name)}, vol={vol}, "
                 f"items={emit_items(items, pans)}, fx={emit_fx(fxl)}}},")
    L.append("  },")
    L.append("  drum_glue = " + emit_fx([COMP(-14, 4, 20, 110),
                                         CLIP(2.5)]) + ",")
    L.append("  buses = {")
    for name, vol, fxl, children in audio_buses:
        L.append(f"    {{name={lua_quote(name)}, vol={vol}, "
                 f"fx={emit_fx(fxl)}, children={{")
        for cn, items, cvol, cfx, cpan in children:
            L.append(f"      {{name={lua_quote(cn)}, vol={cvol}, "
                     f"pan={cpan}, items={emit_items(items)}, "
                     f"fx={emit_fx(cfx)}}},")
        L.append("    }},")
    L.append("  },")
    L.append("  plate_fx = " + emit_fx([PLATE()]) + ",")
    L.append("  master_fx = " + emit_fx(master_fx) + ",")
    L.append("  master_trim = %s," % os.environ.get("MASTER_TRIM", "0.0"))
    L.append("  gtr_ride = {" + ", ".join(
        f"{{{t:.3f}, {v}}}" for t, v in gtr_ride) + "},")
    L.append("  vacuum = {" + ", ".join(
        f"{{{t:.3f}, {v}}}" for t, v in vacuum) + "},")
    L.append("  midi = {")
    for name, evs in midi_tracks:
        rows = ", ".join(f"{{{a:.4f}, {b:.4f}, {p}, {v}}}"
                         for a, b, p, v in evs)
        L.append(f"    {{name={lua_quote(name)}, notes={{{rows}}}}},")
    L.append("  },")
    L.append("}")
    data_path = os.path.join(SCRATCH, "session_data.lua")
    with open(data_path, "w") as f:
        f.write("\n".join(L))
    print(f"data.lua: {len(L)} lines, drums buses gain {g_drums} dB, "
          f"gtr {g_gtr}, bass {g_bass}")
    return data_path, end_s


def run_reaper(data_path):
    build_lua = os.path.join(os.path.dirname(__file__), "reaper_build.lua")
    env = dict(os.environ, SESSION_DATA=data_path)
    try:
        subprocess.run(["xvfb-run", "-a", REAPER, "-nosplash", build_lua],
                       env=env, timeout=900,
                       stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except subprocess.TimeoutExpired:
        pass                       # quit can hang; output file is the truth
    subprocess.run(["pkill", "-f", "reaper_linux"], capture_output=True)


def main():
    data_path, end_s = build()
    out_wav = os.path.join(MIXDIR, songmod.title() + "_reaper_master.wav")
    target = -6.2
    trim = 10.0
    for it in range(4):
        os.environ["MASTER_TRIM"] = str(round(trim, 2))
        data_path, _ = build()
        if os.path.exists(out_wav):
            os.remove(out_wav)
        run_reaper(data_path)
        log = os.path.join(SCRATCH, "reaper_build.log")
        if os.path.exists(log):
            print(open(log).read()[-2000:])
        if not os.path.exists(out_wav):
            raise RuntimeError("render produced no output")
        x = dsp.load(out_wav)
        lufs = dsp.lufs(x)
        tp = dsp.true_peak_db(x)
        print(f"pass {it}: LUFS {lufs:.2f}  TP {tp:.2f}  trim {trim:.2f}")
        if abs(lufs - target) < 0.5:
            break
        trim += min(4.0, target - lufs)
    print("session:", RPP)


if __name__ == "__main__":
    main()
