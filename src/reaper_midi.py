"""Lightweight REAPER project: MIDI only, no rendering.

For dropping your own instruments onto a fully composed, tempo-mapped,
section-marked session — EZdrummer on DRUMS, EZbass on BASS, Odin 3 on
the SUB SYNTH track, whatever amp sim/library you want on the guitars.
No audio stems, no FX chains, no LSP — just notes.

Usage:  cd src && SONG=song6 python3 reaper_midi.py
        SONGDOC_PATH=../jam/archive/carrion_light/songdoc.json \\
            SONG=songband python3 reaper_midi.py

Bass ships at its TRUE composed pitch (not the +12 hack render.py applies
for our specific sample library's quirk — that offset is meaningless for
a generic bass VST). Drums are already GM-ish (kick=36, snare=38, closed
hat=42, crash=49/57, ride=51 — standard General MIDI drum-map numbers),
so most drum VSTs will read them sensibly out of the box. Guitar/lead
tracks carry the original keyswitch notes (very low pitches, easy to spot
and mute/delete in the piano roll) alongside the real performance notes —
useful if you ever load a similarly keyswitched sample library, harmless
otherwise.
"""

import os
import sys
import subprocess

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import songmod
import render as rnd

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REAPER = os.path.join(REPO, "tools", "reaper_linux_x86_64", "REAPER", "reaper")
SCRATCH = os.environ.get("SCRATCH", "/tmp")
SONGDIR = os.path.join(REPO, "songs", songmod.title())
RPP = os.path.join(SONGDIR, "reaper", songmod.title() + ".rpp")

ORDER = ["drums", "gtr_l", "gtr_r", "gtr_l2", "gtr_r2", "lead", "bass",
        "subbass", "subdrop", "fx", "strings", "choir"]
NAMES = {
    "drums": "DRUMS (MIDI, GM-ish map — see notes.txt)",
    "gtr_l": "GTR L (Odin III, keyswitches wired — see notes.txt)",
    "gtr_r": "GTR R (Odin III, keyswitches wired — see notes.txt)",
    "gtr_l2": "GTR L take 2 (Odin III)", "gtr_r2": "GTR R take 2 (Odin III)",
    "lead": "LEAD (Odin III)", "bass": "BASS",
    "subbass": "SUB SYNTH (MIDI)",
    "subdrop": "SUB DROP TRIGGERS (one-shot hits)",
    "fx": "FX TRIGGERS (impact/riser one-shots)",
    "strings": "STRINGS/DRONE (optional)", "choir": "CHOIR (optional)",
}
KEYSWITCH_TRACKS = {"gtr_l", "gtr_r", "gtr_l2", "gtr_r2", "lead"}

_NOTE_PC = {"C": 0, "C#": 1, "D": 2, "D#": 3, "E": 4, "F": 5,
            "F#": 6, "G": 7, "G#": 8, "A": 9, "A#": 10, "B": 11}


def _note(name):
    """'C-1' -> 0, 'C#0' -> 13, 'A1' -> 33 ... standard (octave+1)*12+pc,
    i.e. C-1 = MIDI note 0 (REAPER's own default piano-roll naming).
    Odin III's own keyswitch-list display might use a different middle-C
    reference (common on Kontakt-family instruments, often one octave
    lower) -- if every keyswitch below fires the wrong articulation by
    exactly one octave's worth, that's the cause; ODIN3_OCTAVE_SHIFT is
    the one-line fix."""
    if name[-2] == "-":
        pc_name, octave = name[:-2], int(name[-2:])
    else:
        pc_name, octave = name[:-1], int(name[-1])
    return (octave + 1) * 12 + _NOTE_PC[pc_name]


ODIN3_OCTAVE_SHIFT = 0

# Read directly off Odin III's own keyswitch list (Solemn Tones), three
# keyswitch octaves C-1..B1. Mapped onto our internal articulation names
# (render.KS) wherever a clean match exists. Deliberately left unmapped
# (falls back to our own placeholder pitch) where Odin's vocabulary
# doesn't line up cleanly: fretmute, dive, trill_ht/wt/m3/M3, bend_ht,
# bend_wh, ubend -- Odin's "Bend Up Fast/Slow" differentiate by picking
# speed, not by interval size the way our bend/trill tags do, so forcing
# a match would just be a guess dressed up as data.
ODIN3_KS_MAP = {
    "sus":       _note("C1"),    # Alternate Picked
    "pm":        _note("F#1"),   # Alternate Mute Closed (standard palm mute)
    "pmx":       _note("A1"),    # Alternate Mute Dead (tightest chug)
    "hammer":    _note("C#0"),   # Hammer-On
    "pull":      _note("D0"),    # Pull-Off
    "legato":    _note("C#0"),   # no direct match -> nearest is Hammer-On
    "slide_in":  _note("F#0"),   # *Auto Slide
    "slide_out": _note("F#0"),   # *Auto Slide (Odin doesn't split in/out)
    "porta":     _note("F#0"),   # *Auto Slide
    "nat_harm":  _note("A0"),    # Natural Harmonic
    "pinch":     _note("A#0"),   # Pinch Harmonic
    "fall":      _note("F#-1"),  # Slide Fast To Down (closest to a fall-off)
    "rake":      _note("G0"),    # Scrapes
    "scratch":   _note("G0"),    # Scrapes (Odin has only one scrape artic.)
}
ODIN3_KS_MAP = {k: v + ODIN3_OCTAVE_SHIFT for k, v in ODIN3_KS_MAP.items()}
_PITCH_TO_KS_NAME = {v: k for k, v in rnd.KS.items()}


def lua_quote(s):
    return '"' + str(s).replace("\\", "\\\\").replace('"', '\\"') + '"'


def note_events(score, track, transpose=0, keyswitches=False):
    if track not in score.tracks:
        return []
    evs = []
    notes = score.tracks[track].notes
    if keyswitches:
        for (st, du, pi, ve) in rnd.guitar_keyswitches(notes):
            if ODIN3_KS_MAP:
                name = _PITCH_TO_KS_NAME.get(pi)
                pi = ODIN3_KS_MAP.get(name, pi)
            evs.append((score.beats_to_seconds(st),
                        score.beats_to_seconds(st + du), pi, ve))
    for n in notes:
        evs.append((score.beats_to_seconds(n.start),
                    score.beats_to_seconds(n.start + n.dur),
                    n.pitch + transpose, n.vel))
    return sorted(evs)


def drum_events(score):
    if "drums" not in score.tracks:
        return []
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


DRUM_NOTES = """\
DRUMS track — MIDI pitch map (mostly standard GM drum-map numbers):
  35  kick (rim/alt)        42  closed hihat        51  ride
  36  kick                  43  floor tom            52  china
  38  snare                 47  tom (low-mid)         57  crash 2
  47  tom (low-mid)         48  tom (hi-mid)          59  ride bell
  49  crash 1               50  crash-1 CHOKE*        58  crash-2 CHOKE*
  * 50 and 58 are choke/stop triggers (cymbal muted immediately), not
    separate acoustic instruments — GM calls these High Tom / Vibraslap,
    so remap or ignore them if your drum VST doesn't support chokes.
Everything else lines up with plain GM (kick/snare/hihat/toms/crash/ride),
so most drum VSTs (EZdrummer included) should read this sensibly with
little or no remapping.
"""

GTR_NOTES = """\
GTR/LEAD tracks carry the real performance notes plus a low "keyswitch"
lane that now targets Odin III's own keyswitches directly (mapped from
its GUI keyswitch list): sus->Alternate Picked, pm->Alternate Mute
Closed, pmx->Alternate Mute Dead, hammer->Hammer-On, pull->Pull-Off,
nat_harm->Natural Harmonic, pinch->Pinch Harmonic, slide_in/slide_out/
porta->*Auto Slide, fall->Slide Fast To Down, rake/scratch->Scrapes.

A few rarer techniques (fret-mute, dive bombs, trills, the interval-
specific bends) don't have a clean Odin III equivalent and are left on
our own sample library's placeholder pitch (harmless — just won't
trigger anything useful in Odin III; mute/delete or hand-fix those few
notes in the piano roll if you use them).

Octave caveat: the mapping assumes Odin III's keyswitch-list note names
use the same middle-C reference as REAPER's default piano roll (C-1 =
MIDI note 0). If everything fires one articulation-row off from what the
GUI says, that's a one-octave (12-semitone) mismatch — flip
ODIN3_OCTAVE_SHIFT in src/reaper_midi.py by +/-12 and regenerate.

Odin III also has a velocity-triggered articulation mode (127=pinch
harmonic, 126-35=alt picking, 34-25=palm mute, 24-15=palm mute closed,
14-0=palm mute dead) that works without any keyswitch at all — an
alternative worth trying if the keyswitch octave proves fiddly.
"""

BASS_NOTES = """\
BASS track is at its true composed pitch (no transpose applied) — should
read correctly in EZbass or any standard bass VST/amp sim out of the box.
"""

SUB_NOTES = """\
SUB SYNTH / SUB DROP / FX TRIGGERS are one-shot/sustained hit markers for
a synth (Odin 3, etc.) rather than a "played" part — treat as trigger
points to design a sound around, not a melodic line.
"""


def write_notes(songdir, present):
    lines = [f"{songmod.title()} — REAPER project notes", "=" * 60, ""]
    if "drums" in present:
        lines.append(DRUM_NOTES)
    if any(k in present for k in ("gtr_l", "gtr_r", "gtr_l2", "gtr_r2", "lead")):
        lines.append(GTR_NOTES)
    if "bass" in present:
        lines.append(BASS_NOTES)
    if any(k in present for k in ("subbass", "subdrop", "fx")):
        lines.append(SUB_NOTES)
    with open(os.path.join(songdir, "reaper", "notes.txt"), "w") as f:
        f.write("\n".join(lines))


def build():
    os.makedirs(os.path.dirname(RPP), exist_ok=True)
    score, sec = songmod.build_song()
    end_s = score.beats_to_seconds(score.end_beat()) + 3.0

    tempo = [(score.beats_to_seconds(ts.start_beat), ts.bpm)
             for ts in score.tempo_map]
    regions = []
    order = sorted(sec.items(), key=lambda kv: kv[1])
    for i, (name, beat) in enumerate(order):
        t0 = score.beats_to_seconds(beat)
        t1 = score.beats_to_seconds(order[i + 1][1]) if i + 1 < len(order) \
            else end_s
        regions.append((t0, t1, name))

    midi_tracks = []
    present = [k for k in ORDER if k in score.tracks and score.tracks[k].notes]
    for key in present:
        if key == "drums":
            evs = drum_events(score)
        else:
            transpose = 0
            evs = note_events(score, key, transpose=transpose,
                              keyswitches=key in KEYSWITCH_TRACKS)
        if evs:
            midi_tracks.append((NAMES.get(key, key.upper()), evs))

    L = ["SONG = {"]
    L.append(f"  end_s = {end_s:.3f},")
    L.append(f"  rpp = {lua_quote(RPP)},")
    L.append("  tempo = {" + ", ".join(
        f"{{{t:.4f}, {bpm}}}" for t, bpm in tempo) + "},")
    L.append("  regions = {" + ", ".join(
        f"{{{a:.3f}, {b:.3f}, {lua_quote(n)}}}" for a, b, n in regions) + "},")
    L.append("  midi = {")
    for name, evs in midi_tracks:
        rows = ", ".join(f"{{{a:.4f}, {b:.4f}, {p}, {v}}}" for a, b, p, v
                         in evs)
        L.append(f"    {{name={lua_quote(name)}, notes={{{rows}}}}},")
    L.append("  },")
    L.append("}")
    data_path = os.path.join(SCRATCH, "midi_session_data.lua")
    with open(data_path, "w") as f:
        f.write("\n".join(L))
    write_notes(SONGDIR, present)
    print(f"{len(midi_tracks)} MIDI tracks, {len(regions)} sections, "
          f"{end_s:.1f}s -> {RPP}")
    return data_path


def main():
    data_path = build()
    build_lua = os.path.join(os.path.dirname(__file__), "reaper_midi_build.lua")
    env = dict(os.environ, SESSION_DATA=data_path)
    try:
        subprocess.run(["xvfb-run", "-a", REAPER, "-nosplash", build_lua],
                       env=env, timeout=120,
                       stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except subprocess.TimeoutExpired:
        pass
    subprocess.run(["pkill", "-f", "reaper_linux"], capture_output=True)
    if os.path.exists(RPP):
        print("saved:", RPP)
    else:
        print("FAILED — no .rpp written, check", SCRATCH + "/midi_build.log")


if __name__ == "__main__":
    main()
