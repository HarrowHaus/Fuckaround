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
from song import build_song
from midi_out import write_track_midi
from score import Note
import dsp
from dsp import SR

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SAMPLES = os.path.join(REPO, "samples")
TOOLS = os.path.join(REPO, "tools")
MIDI_DIR = os.path.join(REPO, "midi")
STEMS = os.path.join(REPO, "stems")

SFIZZ = os.path.join(TOOLS, "sfizz/build/library/bin/sfizz_render")
GTX = os.path.join(SAMPLES, "UI_METAL-GTX/Programs/01-METAL-GTX Full.sfz")
BASS_SFZ = os.path.join(SAMPLES, "bnb/Programs/03-babyblue_all.sfz")
KIT_DIR = os.path.join(SAMPLES, "aasimonster")

NAM_5150 = os.path.join(TOOLS, "NAM_models/Helga B 5150 BlockLetter - Boosted.nam")
NAM_6534 = os.path.join(TOOLS, "NAM_models/Helga B 6534+ OD808.nam")
NAM_5153 = os.path.join(TOOLS, "IR/_NAM/5153-Red-DailyDriver/5153-Red-DailyDriver.nam")
NAM_AC30 = os.path.join(TOOLS, "IR/_NAM/VOX AC30 CH/WARM")  # dir; pick file inside
NAM_DUG = os.path.join(TOOLS, "NAM_models/Jason Z Tech21 dUg DP3X bass preamp pedal all dimed no shift.nam")

IR_57 = os.path.join(SAMPLES, "kalthallen/KalthallenCabsIR/Kalthallen IRs/001a-SM57-V30-4x12.wav")
IR_421 = os.path.join(SAMPLES, "kalthallen/KalthallenCabsIR/Kalthallen IRs/013c-MD421-V30-4x12.wav")

SSO_DIR = os.path.join(SAMPLES, "sso/Sonatina Symphonic Orchestra")

# METAL-GTX keyswitches (SFZ c-1 = 0)
KS = dict(pm=22, sus=19, hammer=26, pull=25, slide_in=27, legato=29,
          pinch=10, nat_harm=9)


# ------------------------------------------------------------------ MIDI

def guitar_keyswitches(notes):
    """Emit a keyswitch note whenever the required articulation changes.
    pm -> Mute_Alt; everything else -> Sus_Alt; 'fast' runs get hammer-on /
    pull-off keyswitches based on melodic direction (real legato playing)."""
    ks_events = []
    notes = sorted(notes, key=lambda n: n.start)
    cur = None
    prev_pitch = None
    prev_end = -10.0
    for n in notes:
        if "pm" in n.tags:
            want = "pm"
        elif "fast" in n.tags and prev_pitch is not None \
                and n.start - prev_end < 0.20 and abs(n.pitch - prev_pitch) <= 4:
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
    write_track_midi(score, tr, path, extra_notes=ks)


def load_midimap(path):
    root = ET.parse(path).getroot()
    out = {}
    for m in root:
        if m.tag == "map":
            out.setdefault(m.get("instr"), int(m.get("note")))
    return out


def pick_drum_mapping(midimap):
    """Map our symbolic drum names onto this kit's instrument names."""
    names = list(midimap.keys())

    def find(*cands):
        for c in cands:
            for n in names:
                if c.lower() == n.lower():
                    return n
        for c in cands:
            for n in names:
                if c.lower() in n.lower():
                    return n
        return None

    m = {
        "kick_l": find("KdrumL", "KickL", "Kdrum_L", "kick"),
        "kick_r": find("KdrumR", "KickR", "Kdrum_R", "kick"),
        "snare": find("Snare"),
        "china": find("China1", "China"),
        "china2": find("China2", "China"),
        "crash1": find("Crash1", "Crash"),
        "crash2": find("Crash2", "Crash"),
        "ride_bell": find("RideB", "Bell", "Ride"),
        "ride": find("Ride"),
        "hihat_closed": find("HihatC", "HiHatC", "Hihat"),
        "tom1": find("Tom1", "Tom2", "Tom"),
        "tom2": find("Tom2", "Tom3", "Tom"),
        "tom_floor": find("FTom", "Ftom", "FloorTom", "Tom4"),
    }
    return {k: midimap[v] for k, v in m.items() if v}


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
    write_track_midi(score, tr, path, pitch_of=pitch_of, chan=9)


def write_all_midis():
    os.makedirs(MIDI_DIR, exist_ok=True)
    score, sec = build_song()
    write_guitar_midi(score, "gtr_l", f"{MIDI_DIR}/gtr_l.mid")
    write_guitar_midi(score, "gtr_r", f"{MIDI_DIR}/gtr_r.mid")
    write_guitar_midi(score, "lead", f"{MIDI_DIR}/lead.mid")
    write_guitar_midi(score, "clean", f"{MIDI_DIR}/clean.mid")
    # bass lib maps at written pitch (verified: key 44 sounds G#1 52 Hz),
    # so transpose +12 to sound in unison with the guitars' low register
    write_track_midi(score, score.tracks["bass"], f"{MIDI_DIR}/bass.mid",
                     pitch_of=lambda n: n.pitch + 12)
    write_drum_midi(score, f"{MIDI_DIR}/drums.mid",
                    os.path.join(KIT_DIR, "Midimap.xml"))
    for name in ("strings", "strings_stac", "choir"):
        write_track_midi(score, score.tracks[name], f"{MIDI_DIR}/{name}.mid")
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
         "-I", f"file={MIDI_DIR}/drums.mid,midimap={KIT_DIR}/Midimap.xml",
         "-o", "wavfile", "-O", f"file={out_prefix},srate={SR}",
         kit_xml])


# ------------------------------------------------------------------ amp sim

def nam_process(in_wav, out_wav, nam_path, in_gain_db=0.0, out_gain_db=0.0):
    """Mono-process a DI through a .nam capture (WaveNet on CPU)."""
    import types
    tkstub = types.ModuleType("tkinter"); tkstub.__file__ = "/dev/null/tk.py"
    sys.modules.setdefault("tkinter", tkstub)
    import torch
    from nam.models import init_from_nam

    x = dsp.load(in_wav)
    mono = np.mean(x, axis=0).astype(np.float32) * dsp.db(in_gain_db)
    with open(nam_path) as fp:
        model = init_from_nam(json.load(fp))
    model.eval()
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
        ("gtr_l", GTX, NAM_5150, [(IR_57, 0.0), (IR_421, -4.0)]),
        ("gtr_r", GTX, NAM_6534, [(IR_57, 0.0), (IR_421, -4.0)]),
        ("lead",  GTX, find_nam_in(NAM_5153), [(IR_421, 0.0), (IR_57, -3.0)]),
    ]
    if stage in ("all", "guitars"):
        for name, sfz, nam, irs in jobs:
            di = f"{STEMS}/{name}_di.wav"
            render_sfz(sfz, f"{MIDI_DIR}/{name}.mid", di)
            gain_stage(di, di, -10.0)
            x = dsp.load(di)
            x = dsp.hpf(x, 110, order=2)     # pre-amp tightener
            dsp.save(di, x)
            amped = f"{STEMS}/{name}_amp.wav"
            nam_process(di, amped, nam, in_gain_db=0.0)
            cab_ir(amped, f"{STEMS}/{name}.wav", irs)

        # clean guitar: DI -> AC30 warm -> 421 IR light
        di = f"{STEMS}/clean_di.wav"
        render_sfz(GTX, f"{MIDI_DIR}/clean.mid", di)
        gain_stage(di, di, -14.0)
        nam_process(di, f"{STEMS}/clean_amp.wav", find_nam_in(NAM_AC30))
        cab_ir(f"{STEMS}/clean_amp.wav", f"{STEMS}/clean.wav", [(IR_421, 0.0)])

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
        for note in score.tracks["subdrop"].notes:
            t = score.beats_to_seconds(note.start)
            x = sub_drop(note.pitch + 12, 2.2, note.vel)   # pitch: G#1/F#1 fund.
            i0 = int(t * SR)
            seg = x[:, :max(0, n - i0)]
            subs[:, i0:i0 + seg.shape[1]] += seg
        dsp.save(f"{STEMS}/subdrops.wav", subs)

        fxb = np.zeros((2, n))
        for note in score.tracks["fx"].notes:
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
