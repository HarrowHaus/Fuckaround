# State of the Art: Deathcore Mixing & Mastering, 2024–2026

Research agent field report (compiled 2026-08-01) for the automated pipeline.
Documented claims cited inline; scene-consensus marked as such.

## 1. Who mixes the big records

| Engineer | Recent flagship credits |
|---|---|
| **Josh Schroeder** | Lorna Shore *Pain Remains* + *I Feel the Everblack Festering Within Me* (2025) — produced, mixed AND mastered |
| **Will Putney** | Fit For An Autopsy *The Nothing That Is* (2024); STL Tonality signature suite |
| **Buster Odeholm** | Humanity's Last Breath *Ashen*, Vildhjarta, Allt; own plugin line (thall amp) |
| **Christian Donaldson** | Despised Icon *Shadow Work* (2025); Cryptopsy, Ingested, Shadow of Intent catalog |
| **Dave Otero** | Shadow of Intent *Imperium Delirium* (2025, mix+master) |

Structural trend: **one person does production+mix+master** (Schroeder, Odeholm, Donaldson, Otero) — no separate mastering engineer arguing for dynamics. Whitechapel *Hymns in Dissonance* (2025) self-produced by guitarist Zach Householder — in-band production growing.

### Published chains
**Schroeder kick** (NTM): Slate **Kick 10** one-shot; sustain envelope "almost a vertical line" so 250+ BPM stays articulate; narrow cut at 102 Hz; parallel RAT-style distortion (pre-dist low roll-off); Pro-Q dynamic bands auto-ducking lows 1–2 dB during fast patterns AND dynamically taming the click as density rises. Aggressive gating, ultra-short releases.

**Schroeder vocals** (NTM): hardware comp + clipping + Neve saturation AT TRACKING; bus: de-esser (targets harshness, not just esses) → Pro-MB (stop guitar-clash buildups) → Pro-Q → stereo doubler → safety comp → NY plate. Section-based panning automation: verses narrow/mono, breakdowns wide, transitions masked with delay throws.

**Odeholm**: deliberate "overproduction" as aesthetic; distortion-as-EQ on drums (distorting individual snare frequency bands); parallel distortion + automated processing on guitar DIs; 28" baritones over an octave below E; **bone-dry vocals** (CLA-76 + Waves LoFi, NO reverb); mixes on calibrated headphones, checks on AirPods Pro.

## 2. Loudness and the master bus

**Real numbers (Dynamic Range DB):** Lorna Shore *Everblack* (2025) = **DR3**; *Pain Remains* = DR4 (vinyl masters DR9–12, separate). DR3–4 ≈ **−5 to −7 LUFS integrated** — the 2025 flagship is LOUDER than the 2010s "-8 average." The "-14 LUFS for Spotify" advice is ignored by working deathcore engineers. **Pipeline target: ≈ −6 LUFS-I ±1, DR3–5.**

**True peak**: published standard ≤ −1.0 dBTP (Spotify recommends −2.0 for masters louder than −8 LUFS); many loud masters ship −0.1 to −0.3 sample peak accepting intersample overs. Safe compromise: **−0.5 to −1.0 dBTP**.

**Clipper-first chain** is THE 2-bus fashion: clip before limit so the limiter only catches 1–2 dB.
- SIR **StandardCLIP**: transparency workhorse, ≥16× oversampling, shave 1–2 dB before the limiter
- Kazrog **KClip 3**: metal-community favorite; drum bus in Saturate mode / Crisp algorithm, 2–3 dB
- Schwabe **Gold Clip**: prestige finisher (clip + GOLD saturation + ALCHEMY HF contour)
- Clipping is applied PER-STAGE: drum bus, kick/snare one-shots (often pre-clipped in the sample), even screamed vocals (3–4 dB pre-compression)
- Limiter: **Pro-L 2** (Modern/Aggressive) de-facto standard
- **Saturn 2** Warm Tape at 5–10% mix on the master; or 3-band (~1.5k/6k crossovers) clean-tube on mids for snare presence
- M/S on master: slight side high-shelf lift + mono-below-~100 Hz enforcement

## 3. Drums

**Samples**: GGD dominates (Modern & Massive 2 ships a 4-layer one-shot stacker — stacking is a product feature now); Slate one-shots persist at the top (Kick 10 on Lorna Shore); SD3 Death & Darkness = realism pole; boutique tier = producer one-shots (Odeholm Audio, JST). **Snare fashion: two coexisting camps** — polished modern (200 Hz thump + 5–8 kHz crack) and revivalist "2008 tin-can clanky" riding MySpace nostalgia.

**Blend architecture** (Odeholm/Allt, NTM): (1) dynamic natural-ish multisample layer carries realism/ghosts; (2) heavily processed velocity-INVARIANT one-shot underneath as backbone; (3) phase-lock trigger keyed on beater transient with 300 Hz detection HPF; (4) HPF both at ~35 Hz, top boost on natural layer only; (5) multiband comp on kick lows during fast double-kick; (6) separate saturated kick-room send.

**Kick click 2026 vs 2015**: smack = 3–5 kHz, click = 6–8 kHz. The 2015 djent kick over-indexed a narrow ~4 kHz "typewriter" spike; current fashion = broader 3–6 kHz smack with **click dynamically reduced as kick density rises (tempo-adaptive click)** — highly automatable.

**Blasts at 250+**: velocities DOWN during blasts (humans can't hit hard at 280), accent phrase-heads, small random variation; quantize 90–95%; near-zero sustain envelopes; snare bus cut 400–600 boxiness / boost 5–8k snap / fast 1176; **reverb near-zero on fast sections (automate by density)**; never ride the close snare mic up in blasts (drags cymbal bleed) — use the sample layer for level.

**Cymbals**: sampled cymbals normalized in programmed productions (velocity-invariance = the realism risk); SD3 bleed controls re-inject realism; snare/kick-keyed cymbal ducking during blasts = common practice; parallel drum-bus comp + KClip 2–3 dB standard.

## 4. Guitars

- **Quad-tracked is the norm** (panned ~100/80 per side); dual when definition beats girth (8-string material); six-track = quad + center-ish thick pair on breakdowns. Pipeline default: quad, drop to dual for fast tech riffing.
- **NAM has won the capture war**: free/open, 2025 Architecture 2 wins blind tests vs Neural DSP V2/ToneX; hardware (Blackstar, Darkglass, HeadRush) loads NAM. Captured-amp canon unchanged: **5150/6505, Recto, ENGL, Revv, Fortin**. NAM 5150 + good IR = record-ready.
- **IR meta**: Mesa OS cabs + V30s, SM57-centric. Leaders: GGD Zilla (Nolly), **York Audio MES 212/412 OS-V2** ("most accurate V30s"), Bogren Signature (pre-blended multi-mic). Practice: blend two IRs (body + bite), HPF 80–120, LPF 8–12k.
- **Low tunings (drop F/E, 9-str)**: guitar-bus HPF pushed to **100→150→200 Hz**; bass doesn't own the sub either — kick + synth sub layer own <100 Hz. Multiband clamps palm-mute low-mid bloom.
- **Width**: hard-panned quads = width backbone; center = kick/snare/bass/vox; density-adaptive width automation (narrow verses, wide breakdowns).

## 5. Bass

**Multiband split architecture**: clean/tight low band + heavily driven mid "grind" + optional top click (Parallax archetype: drive mids hard, keep lows clean; Darkglass = hardware version; RAT/HM-2 parallel blends for crunch). In lowest-tuned productions: **HPF the bass guitar itself to 200–300 Hz** — pure harmonic grind gluing guitars to drums — and hand sub duties to a **synth sub layer tracking roots** (JST Sub Destroyer category). Odeholm re-tunes so roots land on open strings.

**Slam/G-code differences**: denser mid-heavy percussive wall, 808/sub drops sidechained to kick under downbeats, lo-fi-tolerant vs the surgical Schroeder/Odeholm aesthetic.

## 6. Low-end architecture

- Tuned sub drops pitched to song key, pitch envelopes for drops/risers
- **Ownership first, sidechain second**: decide kick-vs-sub ownership of the deep fundamental, then sidechain barely works. Kick→sub numbers: attack 0–10 ms, release 40–150 ms
- HPF even kick samples ~35 Hz; <30 Hz = limiter-eating rumble earbuds can't play. Pipeline: steep HPF 28–35 Hz on mix bus, mono <100–120 Hz, **saturate the sub so its 2nd/3rd harmonics (60–120 Hz) carry the note on small speakers**

## 7. Vocal production

- Core convention: **simultaneous low guttural + high scream layers**; verses = 1 main mid scream; hooks/breakdowns = main + low + high (3 timbres), sometimes L/R low doubles; progressively aggressive HPF/low-mid cuts per added layer
- EQ numbers: HPF screams 120–150 Hz; cut 250–400 (3–6 dB narrow); presence 1–2k; bite 3–5k then de-ess; shelf from 8k; **LPF distorted screams 12–15 kHz to kill fizz**
- SM7B standard mic. Two poles: Schroeder (plate + doubler + automation) vs Odeholm (completely dry demon vocals)
- Delay throws on phrase tails + as functional transition masks; formant/pitch-drop ear candy on breakdown calls

## 8. Spatial

Atmos adoption in deathcore ≈ zero (genre optimizes for earbuds + YouTube stereo). Width fashion: density-adaptive, mono-enforced lows, M/S side-sheen on master, AirPods checking is A-list practice.

## Pipeline cheat-sheet (synthesis)

- **Master**: clipper (16×+ OS, 1–2 dB) → Pro-L-2-class limiter → **−6 LUFS-I ±1, ≤−1 dBTP** (DR3–5); multiband tape sat 5–10% upstream; mono <100 Hz; HPF ~30 Hz
- **Drums**: multisample + phase-locked one-shot (beater detect, 300 Hz det-HPF); kick cut ~100 narrow, smack 3–6k dynamically reduced when fast; velocities down + 90–95% quantize on blasts; reverb ducked in dense sections; 2–3 dB drum-bus clip
- **Guitars**: quad, NAM 5150/Recto, 2 blended V30 IRs, bus HPF 100–200 by tuning, LPF 8–12k, multiband on PM lows
- **Bass**: 3-band — sub clean (or synth-replaced, real bass HPF 200–300 in drop-E land), Darkglass-grind mids, kick-sidechained sub (att ≤10 ms, rel 40–150 ms)
- **Vocals**: low+high stacks on hooks, single mid verses; HPF 120–150, cut 250–400, bite 3–5k, LPF 12–15k; clip → comp → plate or bone-dry; delay throws at boundaries

Sources: nailthemix.com (Lorna Shore kick/vocal breakdowns, Odeholm guides, blast-beat/low-tuned/clipper/IR/NAM guides), dr.loudness-war.info, joeysturgistones.com, odeholm-audio.com, stltones.com, tone3000.com (NAM A2), yorkaudio.co, fabfilter.com, melodigging.com, Wikipedia release pages, gearspace.com, sevenstring.org, talkbass.com, immersiveaudioalbum.com.
