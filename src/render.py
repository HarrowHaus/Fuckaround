"""Render pipeline: Score -> MIDI -> DI/drum stems -> amped stems.

Instruments:
  drums    -> DrumGizmo (The Aasimonster, 16 mic channels)
  gtr_l/r  -> METAL-GTX SFZ (keyswitched articulations) -> NAM 5150/6534 -> V30 IRs
  lead     -> METAL-GTX -> NAM 5153 Red -> IR (+ delay/verb at mix)
  clean    -> METAL-GTX sus -> NAM VOX AC30 warm
  bass     -> Black & Blue 'babyblue' pick bass -> split-band dUg DP3X grit
  strings  -> Sonatina Symphonic Orchestra sections
  choir    -> SSO Chorus (fallback: formant pad synth)
  subdrop/fx -> synthesized (synths.py)
"""

import os
import sys
import json
import subprocess
import xml.etree.ElementTree as ET
import numpy as np

sys.path.insert(0, os.path.dirname(__file__))
import songmod
from songmod import build_song
from midi_out import write_track_midi
from score import Note
import dsp
from dsp import SR

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SAMPLES = os.path.join(REPO, "samples")
TOOLS = os.path.join(REPO, "tools")
MIDI_DIR = os.path.join(REPO, "midi")
STEMS = os.path.join(REPO, "stems", songmod.title())

SFIZZ = os.path.join(TOOLS, "sfizz/build/library/bin/sfizz_render")
GTX = os.path.join(SAMPLES, "UI_METAL-GTX/Programs/01-METAL-GTX Full.sfz")
BASS_SFZ = os.path.join(SAMPLES, "bnb/Programs/03-babyblue_all.sfz")
# songs can pick a different bass program (e.g. "01-darkblack_keysw.sfz"
# for keyswitched lead bass) via a BASS_PROGRAM module attribute
_bp = getattr(songmod.get_song(), "BASS_PROGRAM", None)
if _bp:
    BASS_SFZ = os.path.join(SAMPLES, "bnb/Programs", _bp)
KIT_DIR = os.path.join(SAMPLES, "aasimonster")

NAM_5150 = os.path.join(TOOLS, "NAM_models/Helga B 5150 BlockLetter - Boosted.nam")
NAM_6534 = os.path.join(TOOLS, "NAM_models/Helga B 6534+ OD808.nam")
NAM_JSX = os.path.join(TOOLS, "NAM_models/Helga B JSX Ultra - OD808.nam")
NAM_CRUNCH = os.path.join(TOOLS, "NAM_models/Helga B JSX-Crunch-NoBoost-0,004.nam")
NAM_DUG = os.path.join(TOOLS, "NAM_models/Jason Z Tech21 dUg DP3X bass preamp pedal all dimed no shift.nam")

IR_57 = os.path.join(SAMPLES, "kalthallen/KalthallenCabsIR/Kalthallen IRs/001a-SM57-V30-4x12.wav")
IR_421 = os.path.join(SAMPLES, "kalthallen/KalthallenCabsIR/Kalthallen IRs/013c-MD421-V30-4x12.wav")

SSO_DIR = os.path.join(SAMPLES, "sso/Sonatina Symphonic Orchestra")

# METAL-GTX keyswitches (SFZ c-1 = 0)
KS = dict(pm=22, pmx=20, sus=19, hammer=26, pull=25, slide_in=27, legato=29,
          pinch=10, nat_harm=9, fall=5, dive=110,   # dive = Sus_PBR24
          trill_ht=111, trill_wt=112, trill_m3=113, trill_M3=114,
          bend_ht=103, bend_wh=104, ubend=106,      # unison bend (auto)
          rake=13, scratch=8, fretmute=16, porta=108, slide_out=28)

# tag -> keyswitch priority for guitar articulation resolution
KS_PRIORITY = (("dive", "dive"), ("trill_ht", "trill_ht"),
               ("trill_wt", "trill_wt"), ("trill_m3", "trill_m3"),
               ("trill_M3", "trill_M3"), ("bend_ht", "bend_ht"),
               ("bend_wh", "bend_wh"), ("ubend", "ubend"),
               ("nat_harm", "nat_harm"), ("pinch", "pinch"),
               ("rake", "rake"), ("scratch", "scratch"),
               ("fretmute", "fretmute"), ("porta", "porta"),
               ("slide_out", "slide_out"), ("fall", "fall"),
               ("slide", "slide_in"), ("legato", "legato"),
               ("pmx", "pmx"), ("pm", "pm"))

# darkblack lead bass (01-darkblack_keysw.sfz) keyswitches
BASS_KS = dict(bsus=27, bbtb=28, bstac=29, bghost=30, bpluck=31)


def guitar_keyswitches(notes):
    """Emit a keyswitch note whenever the required articulation changes.
    Priority: dive > pinch > fall > slide > pmx > pm; 'fast' runs get
    hammer-on / pull-off keyswitches by melodic direction (real legato)."""
    ks_events = []
    notes = sorted(notes, key=lambda n: n.start)
    cur = None
    prev_pitch = None
    prev_end = -10.0
    for n in notes:
        want = None
        for tag, name in KS_PRIORITY:
            if tag in n.tags:
                want = name
                break
        if want is None:
            if "fast" in n.tags and prev_pitch is not None \
                    and n.start - prev_end < 0.20 \
                    and abs(n.pitch - prev_pitch) <= 4:
                want = "hammer" if n.pitch > prev_pitch else "pull"
            else:
                want = "sus"
        if want != cur:
            ks_events.append((max(0.0, n.start - 0.06), 0.04, KS[want], 100))
            cur = want
        prev_pitch, prev_end = n.pitch, n.start + n.dur
    return ks_events


def write_guitar_midi(score, track_name, path):
    tr = score.tracks[track_name]
    ks = guitar_keyswitches(tr.notes)
    # whammy dives: pitch wheel ramps on 'dive' notes (Sus_PBR24 = ±24 semi
    # bend range, so -8192 = 2 octaves down, -4096 = 1 octave)
    bends = []
    for n in tr.notes:
        if "dive" in n.tags:
            depth = -8192 if n.dur >= 2.0 else -4096
            bends.append((n.start, n.dur, depth))
    write_track_midi(score, tr, path, extra_notes=ks, bends=bends)


def load_midimap(path):
    root = ET.parse(path).getroot()
    out = {}
    for m in root:
        if m.tag == "map":
            out.setdefault(m.get("instr"), int(m.get("note")))
    return out


def pick_drum_mapping(midimap):
    """Map our symbolic drum names onto The Aasimonster's instrument names."""
    want = {
        "kick_l": "kick_l", "kick_r": "kick_r",
        "snare": "snare_on_center",
        "china": "china_18_inch",
        "crash1": "crash1", "crash2": "crash2",
        "crash1_stop": "crash1_stop", "crash2_stop": "crash2_stop",
        "ride_bell": "ride_bell1", "ride": "ride",
        "hihat_closed": "hihat_closed1",
        "tom1": "tom_1", "tom2": "tom_2", "tom_floor": "tom_4",
    }
    return {k: midimap[v] for k, v in want.items() if v in midimap}


def write_drum_midi(score, path, midimap_path):
    midimap = load_midimap(midimap_path)
    mapping = pick_drum_mapping(midimap)
    print("drum mapping:", mapping)
    tr = score.tracks["drums"]
    kick_alt = [0]

    def pitch_of(n):
        name = next(iter(n.tags - {"grid"}), None)
        if name == "kick":
            # alternate feet on fast doubles for realism
            kick_alt[0] ^= 1
            key = "kick_l" if kick_alt[0] else "kick_r"
            return mapping.get(key, mapping.get("kick_l"))
        if name in mapping:
            return mapping[name]
        return None
    # spec-correct file for DAW use
    write_track_midi(score, tr, path, pitch_of=pitch_of, chan=9)
    kick_alt[0] = 0
    # DrumGizmo-calibrated file (its midifile engine runs at half tempo)
    write_track_midi(score, tr, path.replace(".mid", "_dg.mid"),
                     pitch_of=pitch_of, chan=9, absolute_seconds=True)


def write_all_midis():
    os.makedirs(MIDI_DIR, exist_ok=True)
    score, sec = build_song()
    write_guitar_midi(score, "gtr_l", f"{MIDI_DIR}/gtr_l.mid")
    write_guitar_midi(score, "gtr_r", f"{MIDI_DIR}/gtr_r.mid")
    write_guitar_midi(score, "lead", f"{MIDI_DIR}/lead.mid")
    if "clean" in score.tracks:
        write_guitar_midi(score, "clean", f"{MIDI_DIR}/clean.mid")
    elif os.path.exists(f"{MIDI_DIR}/clean.mid"):
        os.remove(f"{MIDI_DIR}/clean.mid")     # stale from another song

    # QUAD tracking (docs/19: "most modern metal albums are quad tracked"):
    # second take per side = same part, independent micro-timing/velocity —
    # a real double, not a copy
    if getattr(songmod.get_song(), "QUAD", False):
        import random as _r
        for src_name, take2 in (("gtr_l", "gtr_l2"), ("gtr_r", "gtr_r2")):
            rng = _r.Random(hash(take2) & 0xffff)
            tr = score.tracks[src_name]
            t2 = type(tr)(take2)
            t2.notes = [Note(max(0.0, n.start + rng.uniform(-0.006, 0.006)),
                             n.dur * rng.uniform(0.96, 1.04), n.pitch,
                             max(30, min(127,
                                         n.vel + rng.randint(-5, 5))),
                             n.tags)
                        for n in tr.notes]
            score.tracks[take2] = t2
            write_guitar_midi(score, take2, f"{MIDI_DIR}/{take2}.mid")
            del score.tracks[take2]
    else:
        for f2 in (f"{MIDI_DIR}/gtr_l2.mid", f"{MIDI_DIR}/gtr_r2.mid"):
            if os.path.exists(f2):
                os.remove(f2)
    # bass lib maps at written pitch (verified: key 44 sounds G#1 52 Hz),
    # so transpose +12 to sound in unison with the guitars' low register.
    # Lead-bass songs (darkblack_keysw) get articulation keyswitches too.
    bass_ks = []
    if getattr(songmod.get_song(), "BASS_PROGRAM", None):
        cur = None
        for n in sorted(score.tracks["bass"].notes, key=lambda x: x.start):
            want = next((BASS_KS[t] for t in
                         ("bstac", "bghost", "bpluck", "bbtb", "bsus")
                         if t in n.tags), BASS_KS["bsus"])
            if want != cur:
                bass_ks.append((max(0.0, n.start - 0.06), 0.04, want, 100))
                cur = want
    write_track_midi(score, score.tracks["bass"], f"{MIDI_DIR}/bass.mid",
                     pitch_of=lambda n: n.pitch + 12, extra_notes=bass_ks)
    write_drum_midi(score, f"{MIDI_DIR}/drums.mid",
                    os.path.join(KIT_DIR, "midimap.xml"))
    for name in ("strings", "strings_stac", "choir"):
        if name in score.tracks:
            write_track_midi(score, score.tracks[name],
                             f"{MIDI_DIR}/{name}.mid")
        else:
            p = f"{MIDI_DIR}/{name}.mid"
            if os.path.exists(p):
                os.remove(p)       # stale MIDI from another song
    return score, sec


# ------------------------------------------------------------------ renderers

def run(cmd, **kw):
    print("+", " ".join(str(c) for c in cmd))
    subprocess.run([str(c) for c in cmd], check=True, **kw)


def render_sfz(sfz, midi, wav, polyphony=256):
    run([SFIZZ, "--sfz", sfz, "--midi", midi, "--wav", wav,
         "-s", SR, "-q", "2", "-p", polyphony])


def render_drums():
    kit_xml = None
    for f in os.listdir(KIT_DIR):
        if f.endswith(".xml") and "idimap" not in f:
            kit_xml = os.path.join(KIT_DIR, f)
    assert kit_xml, "kit xml not found"
    out_prefix = os.path.join(STEMS, "drums", "dg")
    os.makedirs(os.path.dirname(out_prefix), exist_ok=True)
    run(["drumgizmo", "-i", "midifile",
         "-I", f"file={MIDI_DIR}/drums_dg.mid,midimap={KIT_DIR}/midimap.xml",
         "-o", "wavfile", "-O", f"file={out_prefix},srate={SR}",
         kit_xml])


# ------------------------------------------------------------------ amp sim

def load_nam_model(nam_path):
    """Load a .nam capture. Supports the WaveNet 0.5.0 export format used by
    the Helga B / Jason Z community captures (config keys: layers/head/
    head_scale -> nam 0.10's layers_configs/head_config/head_scale)."""
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), "_stubs"))
    import torch
    from nam.models import wavenet
    with open(nam_path) as fp:
        d = json.load(fp)
    if d.get("architecture") != "WaveNet":
        raise ValueError(f"unsupported architecture {d.get('architecture')}")
    cfg = d["config"]
    m = wavenet.WaveNet(layers_configs=cfg["layers"],
                        head_config=cfg.get("head"),
                        head_scale=cfg.get("head_scale", 1.0),
                        sample_rate=d.get("sample_rate"))
    m.import_weights(torch.tensor(d["weights"]))
    m.eval()
    return m


def nam_process(in_wav, out_wav, nam_path, in_gain_db=0.0, out_gain_db=0.0):
    """Mono-process a DI through a .nam capture (WaveNet on CPU)."""
    import torch
    x = dsp.load(in_wav)
    mono = np.mean(x, axis=0).astype(np.float32) * np.float32(dsp.db(in_gain_db))
    model = load_nam_model(nam_path)
    with torch.no_grad():
        y = model(torch.from_numpy(mono), pad_start=True).numpy()
    y = np.asarray(y, dtype=np.float64) * dsp.db(out_gain_db)
    if len(y) < mono.shape[0]:
        y = np.pad(y, (0, mono.shape[0] - len(y)))
    dsp.save(out_wav, np.vstack([y, y]))
    return out_wav


def cab_ir(in_wav, out_wav, ir_paths_gains, predelay_trim=True):
    """Convolve with a blend of cab IRs (57/421 blend per research)."""
    x = dsp.load(in_wav)
    mono = np.mean(x, axis=0)
    out = np.zeros_like(mono)
    for path, gain_db in ir_paths_gains:
        ir = np.mean(dsp.load(path), axis=0)
        ir = ir[:int(0.1 * SR)]
        y = np.convolve(mono, ir)[:len(mono)]
        out += y * dsp.db(gain_db)
    dsp.save(out_wav, np.vstack([out, out]))
    return out_wav


def find_nam_in(path_or_dir):
    if os.path.isfile(path_or_dir):
        return path_or_dir
    for f in sorted(os.listdir(path_or_dir)):
        if f.endswith(".nam"):
            return os.path.join(path_or_dir, f)
    raise FileNotFoundError(path_or_dir)


def gain_stage(in_wav, out_wav, peak_target_db=-10.0):
    x = dsp.load(in_wav)
    x = x * dsp.db(peak_target_db - dsp.peak_db(x))
    dsp.save(out_wav, x)


# ------------------------------------------------------------------ main

def main(stage="all"):
    os.makedirs(STEMS, exist_ok=True)
    score, sec = write_all_midis()
    print("MIDIs written")

    if stage in ("midi",):
        return

    # ---- drums
    if stage in ("all", "drums"):
        render_drums()

    # ---- guitars: DI -> gain-stage -> tight HPF -> NAM -> IR blend
    jobs = [
        ("gtr_l", GTX, NAM_5150, 4.0, [(IR_57, 0.0), (IR_421, -4.0)]),
        ("gtr_r", GTX, NAM_6534, 4.0, [(IR_57, 0.0), (IR_421, -4.0)]),
        ("lead",  GTX, NAM_JSX, 2.0, [(IR_421, 0.0), (IR_57, -3.0)]),
    ]
    if os.path.exists(f"{MIDI_DIR}/gtr_l2.mid"):
        # quad: each side gets both amp flavors (take 2 crosses over)
        jobs += [
            ("gtr_l2", GTX, NAM_6534, 4.0, [(IR_421, 0.0), (IR_57, -4.0)]),
            ("gtr_r2", GTX, NAM_5150, 4.0, [(IR_421, 0.0), (IR_57, -4.0)]),
        ]
    if stage in ("all", "guitars"):
        for name, sfz, nam, gin, irs in jobs:
            di = f"{STEMS}/{name}_di.wav"
            render_sfz(sfz, f"{MIDI_DIR}/{name}.mid", di)
            gain_stage(di, di, -6.0)
            x = dsp.load(di)
            x = dsp.hpf(x, 110, order=2)     # pre-amp tightener
            dsp.save(di, x)
            amped = f"{STEMS}/{name}_amp.wav"
            nam_process(di, amped, nam, in_gain_db=gin)
            cab_ir(amped, f"{STEMS}/{name}.wav", irs)

        # clean guitar: DI -> JSX crunch at low input (edge of breakup);
        # songs with no clean track (song5+) skip and clear stale stems
        if os.path.exists(f"{MIDI_DIR}/clean.mid"):
            di = f"{STEMS}/clean_di.wav"
            render_sfz(GTX, f"{MIDI_DIR}/clean.mid", di)
            gain_stage(di, di, -16.0)
            nam_process(di, f"{STEMS}/clean_amp.wav", NAM_CRUNCH)
            cab_ir(f"{STEMS}/clean_amp.wav", f"{STEMS}/clean.wav",
                   [(IR_421, 0.0)])
        else:
            for st in ("clean_di", "clean_amp", "clean"):
                p = f"{STEMS}/{st}.wav"
                if os.path.exists(p):
                    os.remove(p)

    # ---- bass: DI -> split: lows clean / mids dUg grit
    if stage in ("all", "bass"):
        di = f"{STEMS}/bass_di.wav"
        render_sfz(BASS_SFZ, f"{MIDI_DIR}/bass.mid", di)
        gain_stage(di, di, -8.0)
        nam_process(di, f"{STEMS}/bass_grit_raw.wav", NAM_DUG, in_gain_db=4.0)
        x_di = dsp.load(di)
        x_grit = dsp.load(f"{STEMS}/bass_grit_raw.wav")
        n = max(x_di.shape[1], x_grit.shape[1])
        lo = dsp.lpf(dsp.pad_to(x_di, n), 180)
        hi = dsp.hpf(dsp.pad_to(x_grit, n), 180)
        hi = dsp.lpf(hi, 6000)
        dsp.save(f"{STEMS}/bass_lo.wav", lo)
        dsp.save(f"{STEMS}/bass_hi.wav", hi)

    # ---- orchestra
    if stage in ("all", "orch"):
        sso = {
            "strings": ["Strings - Performance/1st Violins Sustain.sfz",
                        "Strings - Performance/Celli Sustain.sfz"],
            "strings_stac": ["Strings - Performance/1st Violins Staccato.sfz",
                             "Strings - Performance/Celli Staccato.sfz"],
            "choir": ["Chorus - Performance/Mixed Chorus.sfz"],
        }
        for track, files in sso.items():
            found = []
            for f in files:
                p = os.path.join(SSO_DIR, f)
                if os.path.exists(p):
                    found.append(p)
            if not found:  # search fuzzily
                import glob
                pat = {"strings": "*Violins*Sustain*.sfz",
                       "strings_stac": "*Violins*Staccato*.sfz",
                       "choir": "*horus*.sfz"}[track]
                found = glob.glob(os.path.join(SSO_DIR, "**", pat),
                                  recursive=True)[:2]
            outs = []
            for i, p in enumerate(found):
                w = f"{STEMS}/{track}_{i}.wav"
                render_sfz(p, f"{MIDI_DIR}/{track}.mid", w)
                outs.append(dsp.load(w))
            if outs:
                n = max(o.shape[1] for o in outs)
                mixdown = sum(dsp.pad_to(o, n) for o in outs) / len(outs)
                dsp.save(f"{STEMS}/{track}.wav", mixdown)
            else:
                print(f"WARN: no SSO patches for {track}")

    # ---- synth layers
    if stage in ("all", "synths"):
        from synths import sub_drop, riser, dive_bomb, impact, choir_pad
        end_s = score.beats_to_seconds(score.end_beat()) + 8.0
        n = int(end_s * SR)
        subs = np.zeros((2, n))
        for note in score.tracks.get("subdrop",
                                     type("E", (), {"notes": []})()).notes:
            t = score.beats_to_seconds(note.start)
            x = sub_drop(note.pitch + 12, 2.2, note.vel)   # pitch: G#1/F#1 fund.
            i0 = int(t * SR)
            seg = x[:, :max(0, n - i0)]
            subs[:, i0:i0 + seg.shape[1]] += seg
        dsp.save(f"{STEMS}/subdrops.wav", subs)

        from synths import sub_note
        sb = np.zeros((2, n))
        for note in score.tracks.get("subbass",
                                     type("E", (), {"notes": []})()).notes:
            t0s = score.beats_to_seconds(note.start)
            t1s = score.beats_to_seconds(note.start + note.dur)
            x = sub_note(note.pitch, max(0.12, t1s - t0s), note.vel)
            i0 = int(t0s * SR)
            seg = x[:, :max(0, n - i0)]
            sb[:, i0:i0 + seg.shape[1]] += seg
        dsp.save(f"{STEMS}/subbass.wav", sb)

        fxb = np.zeros((2, n))
        for note in score.tracks.get("fx",
                                     type("E", (), {"notes": []})()).notes:
            t0 = score.beats_to_seconds(note.start)
            t1 = score.beats_to_seconds(note.start + note.dur)
            i0 = int(t0 * SR)
            if "riser" in note.tags:
                x = riser(max(0.5, t1 - t0))
            elif "dive" in note.tags:
                x = dive_bomb(note.pitch, max(1.0, t1 - t0))
            else:
                x = impact()
            seg = x[:, :max(0, n - i0)]
            fxb[:, i0:i0 + seg.shape[1]] += seg
        dsp.save(f"{STEMS}/fx.wav", fxb)
    print("RENDER COMPLETE")


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "all")
