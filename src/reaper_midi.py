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
    "gtr_l": "GTR L", "gtr_r": "GTR R",
    "gtr_l2": "GTR L (take 2)", "gtr_r2": "GTR R (take 2)",
    "lead": "LEAD", "bass": "BASS",
    "subbass": "SUB SYNTH (MIDI — e.g. Odin 3)",
    "subdrop": "SUB DROP TRIGGERS (one-shot hits)",
    "fx": "FX TRIGGERS (impact/riser one-shots)",
    "strings": "STRINGS/DRONE (optional)", "choir": "CHOIR (optional)",
}
KEYSWITCH_TRACKS = {"gtr_l", "gtr_r", "gtr_l2", "gtr_r2", "lead"}


def lua_quote(s):
    return '"' + str(s).replace("\\", "\\\\").replace('"', '\\"') + '"'


def note_events(score, track, transpose=0, keyswitches=False):
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
GTR/LEAD tracks carry the real performance notes plus a handful of very
low "keyswitch" notes (pitch 5-29) — these trigger articulation switches
(palm mute, technique) on our own sample library and are meaningless to
most guitar VSTs/amp sims. They're easy to spot in the piano roll (they
sit far below the lowest played note) — mute or delete that lane if your
plugin doesn't use keyswitches, or remap them if it does.
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
