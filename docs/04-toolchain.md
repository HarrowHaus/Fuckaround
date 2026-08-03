# Production Toolchain (all free, all headless, all verified working)

| Role | Tool | Why it was chosen |
|---|---|---|
| Drums | **DrumGizmo 0.9.20** + **The Aasimonster 2.1** kit (2.4 GB, CC-BY 4.0) | Superior-Drummer-class multi-mic engine: 16 mic channels (dual kicks + triggers, snare top/bottom+trigger, 4 toms, OH/ambience pairs, hihat/ride close mics), multi-velocity sampling recorded for a Danish death metal album. Built-in timing/velocity humanizers. Renders MIDI → per-mic WAVs headlessly. |
| Rhythm/lead guitar | **Unreal Instruments METAL-GTX** (1.3 GB SFZ, 7-string DI) via **sfizz_render** (built from source) | Real sampled 7-string DI with palm mutes, sustains, hammer-ons, pull-offs, slides, pinch harmonics, up to 18 round robins, alternating up/down picking — range F#1–E6 covers Drop G# and the F# detune. Keyswitch-driven articulations (PM=A#0, Sus=G0, HO=D1, PO=C#1). |
| Amp sim | **Neural Amp Modeler** (PyTorch, CPU) with real captures: Peavey **5150 Block Letter (boosted)** for guitar L, Peavey **6534+ w/ OD808** for guitar R (contrasting-pair convention), **EVH 5153 Red** for leads, **VOX AC30** for cleans | NAM WaveNet captures of real tube amps — actual amp nonlinearity/sag, not waveshaping. The boosted captures bake in the genre's tubescreamer-into-5150 front end. |
| Cab | **Kalthallen Cabs** IRs: SM57-on-V30-4x12 blended with MD421-on-V30-4x12 (60/40) | The literal genre convention per mix research (Mesa 4x12 V30, 57+421 blend). Long-time death metal community standard IR pack. |
| Bass | **Karoryfer Black & Blue Basses** (CC0) "babyblue" pick bass → split-band: clean lows + **Tech21 dUg DP3X (all dimed)** NAM capture for grit band | 5-string pick bass, multi-velocity/round-robin; the dUg DP3X is a real metal bass preamp pedal capture — the split-band clean-low/distorted-mid chain is the deathcore standard. |
| Orchestra | **Sonatina Symphonic Orchestra** (peastman fork, SFZ) | Violin/celli sections (sustain + staccato for chug-synced stabs), mixed chorus for the blackened choir swells. |
| Sub drops / risers / dive | Custom synthesis (`src/synths.py`) | Tuned to song key per research (G#0/F#0 fundamentals, 60 ms fade-in so kick wins, saturation for phone playback). |
| Mixing/mastering | **pedalboard** (Spotify) + custom DSP (`src/dsp.py`): sidechain ducking, band-split processing, soft clipper, transient shaper; **pyloudnorm** for LUFS | Full research-spec chain: per-bus EQ/comp, parallel drum crush, bus glue, clipper→true-peak limiter to −8 LUFS / −1 dBTP. |

## Render flow

```
src/song.py      composition (5,300 notes, tempo map, humanization)
src/render.py    → midi/*.mid (keyswitches, drum map, bass transposition)
                 → drumgizmo: 16 mic-channel drum WAVs
                 → sfizz_render: guitar/bass DIs, orchestra
                 → NAM (torch): DIs through real amp captures
                 → IR convolution: V30 4x12 57/421 blend
                 → synths: sub drops, risers, dive bomb
src/mix.py       → bus processing per docs/03 → mix/instrumental_vocal_ready.wav
                 → mastering chain → mix/where_light_comes_to_die_master.wav
```

Licensing notes: DrumGizmo kit CC-BY 4.0 ("Drum samples provided by DrumGizmo.org"); Karoryfer basses CC0; SSO CC Sampling Plus 1.0; METAL-GTX free for music use (no sample redistribution — samples are NOT committed to this repo); NAM captures GPLv3 (fine for rendered audio); Kalthallen IRs free per EULA (review before commercial release).
