# WHERE LIGHT COMES TO DIE
### Blackened symphonic deathcore — composed, performed, and produced entirely in code

A production-ready deathcore instrumental engineered to 2026 scene standards, built by a
fully headless pipeline: researched → composed → rendered through real sampled instruments
and neural amp captures → mixed and mastered to commercial loudness.

**Deliverables (in `mix/`):**
- `where_light_comes_to_die_master.wav` / `.mp3` — the master (−8 LUFS integrated, −1.0 dBTP)
- `instrumental_vocal_ready.wav` — unlimited version peaking at −6 dBFS for vocal tracking
- `report.json`, `qc.json` — loudness/QC metrics

**The song:** G# minor, Drop G# 7-string, 130 BPM core (blast sections feel ~260), with the
final breakdown dropping to 100 BPM *and* detuning a whole step to F# — 4:23 of
symphonic-blackened deathcore following the composition blueprint distilled from
Lorna Shore / Whitechapel / Signs of the Swarm / Disembodied Tyrant's 2025–2026 output.
See `docs/05-vocalist-guide.md` for the section-by-section vocal map.

## How it was made

1. **Research** (`docs/01–04`): four parallel research passes — the 2025–2026 deathcore
   landscape (tunings, tempos, structures of the year's biggest songs), blackened deathcore
   composition technique (riff grammars, blast vocabulary, breakdown grids, humanization
   numbers), the modern deathcore mix recipe (every EQ/compression/loudness number used by
   `src/mix.py`), and the free headless tooling landscape.
2. **Composition** (`src/song.py`): ~5,300 notes over an 11-section arc with a leitmotif
   that recurs in the intro strings, the melodic peak, and over the final breakdown.
   Research-derived drum programming (traditional/hammer blasts, kick-follows-guitar
   breakdown law, velocity ladders, ±1–3 ms human timing).
3. **Performance** (`src/render.py`):
   - Drums: **DrumGizmo** + **The Aasimonster** death metal kit — 16 real mic channels,
     alternating kick feet, multi-velocity hits.
   - Guitars: **UI METAL-GTX** 7-string DI samples with keyswitched palm mutes,
     hammer-ons/pull-offs on legato runs, round-robin picking → **Neural Amp Modeler**
     captures of a Peavey 5150 Block Letter (boosted) and 6534+ w/ OD808 (contrasting
     hard-panned pair), JSX Ultra for leads → **SM57+MD421 on V30 4x12** impulse responses.
   - Bass: Karoryfer 5-string pick bass → split-band chain (clean lows + Tech21 dUg grit).
   - Orchestra/choir: Sonatina Symphonic Orchestra; tuned sub drops, risers, and the
     dive bomb are synthesized to the song key.
4. **Mix/master** (`src/mix.py`): the full research recipe — per-bus EQ and compression,
   snare plate, parallel drum crush, kick-keyed sidechain ducking on bass and orchestra,
   mono-below-120 discipline, bus glue, then tilt EQ → low-band compression → soft clip →
   true-peak limiting. The 2–4 kHz scream pocket is deliberately kept clear.

## Reproduce

```
apt install drumgizmo ffmpeg python3-tk unar
pip install mido pedalboard pyloudnorm soundfile numpy scipy neural-amp-modeler==0.10.0 gdown
# build sfizz (tools/sfizz), download sample libraries into samples/ (see docs/04-toolchain.md)
python3 src/render.py     # MIDI + all stems (drums, amped guitars, bass, orchestra, synths)
python3 src/mix.py        # mix + master + mp3
python3 src/qc.py         # objective QC report
```

`samples/`, `tools/`, and `stems/` are gitignored (multi-GB); `docs/04-toolchain.md` lists
every download URL and license.
