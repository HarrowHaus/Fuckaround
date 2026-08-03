# Modern Deathcore Mixing & Mastering Recipe (2024–2026 Standards)

A concrete, code-implementable starting-point recipe compiled from Nail The Mix, URM Academy, Chernobyl Audio, izotope, Sage Audio, and practitioner forums. All numbers are starting points intended for a headless DSP chain (EQ / compression / convolution / saturation / limiting); tune by ear/meter after.

---

## 1. Rhythm Guitars

### Tracking / layering
- **Double-tracking (2 takes, hard-panned) is the modern default.** Quad-tracking is used, but the consensus warning: 4 tracks mush transients and reduce chunk unless performances are machine-tight. If your "takes" are programmed/identical, quad only helps if the tones differ.
- Panning schemes (Chernobyl Audio's three canonical options):
  1. **All four at 100L/100R** — works best when the two pairs are contrasting tones (one darker/mid-focused amp, one scooped/aggressive).
  2. **Outer pair 100/100, inner pair ~80/80** — fills intermediate stereo space; good for fuller arrangements.
  3. **All hard-panned, second pair 3–6 dB quieter** — adds thickness via depth; cited as "probably the most effective."
- For double-tracking: just 100L/100R, matched levels within ~0.5 dB.

### Amp chain (5150/Rectifier style)
- **Tubescreamer boost in front of the amp — non-negotiable for deathcore.** Its purpose is EQ, not distortion: the TS circuit rolls off bass below ~300 Hz (this is what tightens flubby drop-tuned low end), humps mids around ~720 Hz, and rolls treble above ~4 kHz (tames fizz).
  - **Drive: 0** (minimum). **Level: 75–100%** (3 o'clock to max). **Tone: ~10 o'clock to 1 o'clock** — the tone knob matters more than level; below noon kills pick clarity, above 3 o'clock adds fizz.
  - DSP equivalent: HPF ~300 Hz (1st order) → mild soft-clip/od stage → slight mid bump ~720 Hz → LPF ~4–5 kHz shelf-ish rolloff → into amp sim, output gain pushing amp input +6–10 dB.
- **Amp gain LOWER than you think:** 5150-style gain at ~10 o'clock (roughly 35–45% of range). The TS boost restores saturation while keeping palm mutes tight. Lows ~noon, mids 11–1 o'clock, highs ~10 o'clock, presence moderate. Excess preamp gain = mush, especially quad-tracked (gain accumulates across layers).

### Cab / IR (convolution)
- Convention: **Mesa 4x12 with Celestion V30s**, close-miked. Standard blend: **SM57 + MD421**, both slightly off-center of the cap, edge-of-cap position; mix 50/50 to 60/40 (57 forward). If you only pick one IR, an SM57-on-V30 edge-of-cap IR is *the* genre sound.
- Note: a V30+SM57 IR is already bright and mid-forward — factor that into post-EQ (don't double-boost presence).

### Post-EQ (per guitar bus)
| Move | Freq | Amount | Q |
|---|---|---|---|
| HPF | 80–120 Hz (drop tunings: 70–90 Hz; leave room for bass) | 24 dB/oct | — |
| LPF | 9–12 kHz (10 kHz typical) | 12–24 dB/oct | — |
| Mud cut | 300–500 Hz (sweep; ~400 Hz common) | −2 to −4 dB | 1.0–1.5 |
| Fizz notches | sweep 3–6 kHz; classic SM57 fizz ~4 kHz | −3 to −6 dB | 4–8 (narrow) |
| Optional presence | 2–3 kHz | +1–2 dB only if buried | 1.5 |
- **Dynamic EQ / multiband on the guitar bus:** dynamic cut at 100–180 Hz (threshold so it only clamps palm-mute chug blooms, ~2–4 dB GR) keeps chugs consistent. A second dynamic band at 3–4 kHz catches harsh pick-scrape spikes.
- Compression on rhythm guitars: minimal or none (the amp already compresses). If any: 4:1, slow attack 30 ms, fast release, 1–2 dB GR max.

---

## 2. Drums

Deathcore drums are **sample-reinforced or fully sampled** — blast beats at 250+ BPM demand per-hit consistency that mics alone can't give. When blending samples with shells, subtractive-EQ the sample where the live drum is already strong so they read as one drum. Align sample phase/timing to the transient (sample-accurate, check polarity).

### Kick
- EQ (per Nail The Mix numbers):
  - HPF 30–40 Hz.
  - **Sub/thump: +2–4 dB, wide bell, 50–80 Hz** (60 Hz typical).
  - **Box scoop: −3–6 dB somewhere 250–600 Hz** (300–500 Hz usual), medium-narrow Q.
  - **Click: medium-narrow boost in 2–8 kHz.** 2–4 kHz = "thwack"; **5–8 kHz = modern clicky metal attack** (4–6 kHz, +4–6 dB is the deathcore starting point).
- Compression: fast peak control, 4:1, attack 5–10 ms, release 50–100 ms, 2–4 dB GR (mostly for consistency; skip if fully sampled).
- **Interlock with bass:** coordinated narrow cuts — e.g., kick owns 50–60 Hz, bass owns 80–120 Hz; cut each out of the other by 2–3 dB.

### Snare
- EQ: HPF ~80–100 Hz; **body +2–4 dB at 150–250 Hz** (200 Hz classic); box cut −2–4 dB at 400–600 Hz; **crack/snap +3–6 dB at 2–5 kHz** (5 kHz for modern zing); optional air shelf +2 dB at 10 kHz.
- Compression: **4:1 to 8:1, slow attack (10–30 ms) to let the crack through, medium-slow release (~150–250 ms) to bring up body**, 3–6 dB GR. A transient shaper (attack +2–4 dB) before or instead of the compressor is standard for blast-beat articulation.

### Parallel drum compression (the "smash bus")
- Send kick+snare+toms (often full kit) to a parallel bus: **high ratio (8:1–20:1 / all-buttons), fast attack (<1 ms–5 ms), fast release (~50 ms), 10–20 dB GR**, then blend in 6–10 dB below the dry bus. Optionally EQ smiley (+ lows/+ highs) on the crushed bus.

### Overheads / rooms for fast metal
- OH: HPF 350–500 Hz (they're cymbal mics in this genre, not kit mics), gentle high shelf +1–2 dB @ 10 kHz, de-ess/dynamic-EQ harsh 3–5 kHz wash if blasting. Level: cymbals audible but clearly under kick/snare.
- Room mics: heavily compressed (as parallel above) but **gated or ducked during blast sections** — fast metal drowns in room wash. Many deathcore mixes use a short sampled room instead (see reverb section).

### Drum bus glue
- SSL-style bus comp on the drum bus: **ratio 4:1, attack 10–30 ms, release ~100 ms or auto, 2–3 dB GR** on loudest sections.
- Soft-clip the drum bus (or kick/snare individually): shave 2–4 dB of transient peaks with a soft/tanh clipper. This is *the* modern trick for loud masters — peaks get clipped here so the master limiter doesn't pump.

### Level relationships (deathcore convention)
- Kick and snare sit **on top of** the wall of guitars — this genre mixes drums forward. Practical starting point: peaks of snare ~equal or up to +3–5 dB over kick perception; kick click clearly audible through full guitars. If you calibrate: guitars bus around −6 to −8 dB below the level where kick/snare peak, i.e., snare/kick transients should read ~3–5 dB above the guitar wall on a short-term meter during full sections.

---

## 3. Bass

### Split-band processing (the genre-standard chain)
Split the DI into 2–3 bands:
- **Low band: LPF at ~150–250 Hz.** Keep clean. Heavy compression for consistency: 4:1–8:1, fast-ish attack, aim for a nearly flat low end (or multiband comp only below ~100–150 Hz).
- **Mid/high band: HPF 150–250 Hz, LPF ~5 kHz. Obliterate with distortion** (SansAmp/Darkglass-style saturation, heavy drive). This band supplies grind, clank, and audibility on small speakers.
- Optional third band above 5 kHz for string noise/clank, lighter drive.
- Recombine; the distorted band typically sits 3–6 dB under the clean low band.

### Fit with drop-tuned guitars
- Bass owns **sub through ~120 Hz**; guitars are HPF'd at 80–120 Hz so bass fills underneath. Bass mids (700 Hz–2 kHz) poke through the guitar scoop.
- Mono below ~120 Hz. Cut bass 300–500 Hz a couple dB (same mud region as guitars).
- **Sidechain to kick: yes, subtly.** Compressor on bass keyed from kick: 2–4 dB GR, fast attack (1–5 ms), release 30–80 ms — or better, a dynamic EQ duck of just the sub band (30–100 Hz) by 2–3 dB per kick hit. With blast beats keep release fast or the bass never recovers.
- Level: bass sits roughly **−3 to −6 dB under the guitar bus** in perceived level, but its low band is what dominates the sub octave — check on a spectrum meter that 40–100 Hz energy comes from bass+kick, not guitars.

---

## 4. 808s / Sub Drops

- **Tune to the song key** — always. Transpose the sample so the fundamental lands on the root (or the current chord root) of the drop.
- Envelope: short 808s (50–200 ms decay) reinforce kick hits; **big sub drops = 500 ms–2 s+ decay**.
- Collision handling (Nail The Mix's dense-metal method):
  - **Fade in the 808 over 50–100 ms** so the kick transient punches first — this alone solves most kick/808 masking.
  - Limit the 808's initial spike so smaller speakers hear modulation, not a thump.
  - **Automate the 808 level upward as it decays/pitch-drops** so it stays audible down to 15–20 Hz.
  - Duck bass guitar under the 808: dynamic EQ on bass, keyed from the 808, acting **below ~150 Hz** only.
  - If kick and 808 must coexist sustained: sidechain 808 from kick, attack 1–5 ms, release 30–50 ms, 3–5 dB GR.
- Mono the 808 entirely. Add light saturation (2nd/3rd harmonic) so the note reads on phones.
- Goal check: the 808 should cause **< ~0.5 dB extra GR on the mix-bus compressor**.

---

## 5. Mix Bus & Mastering

### Mix bus (print chain)
1. **SSL-style bus compressor: 2:1 (up to 4:1), attack 10–30 ms (slow — protect kick/snare transients), release 100 ms or auto, 2–3 dB GR max on the loudest sections.** More than ~4 dB kills punch.
2. **Tape/console saturation:** gentle — drive for low single-digit % THD; tape-style HF soft compression tames cymbal harshness and fattens 50–100 Hz. Keep it subtle.
3. Optional bus EQ: broad tilt only (±1 dB).
4. Leave **3–6 dB headroom** into mastering.

### Mastering chain (in order)
1. **EQ:** corrective first — HPF 20–25 Hz; typical modern-metal tilt is a slight smile: +0.5–1 dB shelf below ~100 Hz, +0.5–1.5 dB shelf above ~8–10 kHz, and if the mix is honky, −0.5–1 dB around 300–500 Hz. Keep moves ≤1.5 dB.
2. **Multiband compression (optional, gentle):** mostly the low band — compress below ~120 Hz, 2:1, slow attack, 1–2 dB GR to keep chugs+kick from pumping the limiter.
3. **Saturation/console glue** (if not already on mix bus).
4. **Clipper before limiter — this is the modern metal loudness engine.** Soft clipper shaving 2–4 dB off drum transients (much of this ideally already done at drum-bus level). Threshold so only kick/snare peaks clip; program material should not audibly distort.
5. **True-peak limiter:** ceiling **−1.0 dBTP** for streaming safety (many metal engineers run −0.3 to −0.5 dBTP accepting slight ISP risk for loudness). Fast-ish release/auto, 2–5 dB GR on peaks.

### Loudness targets
- **Commercial deathcore/djent releases actually measure ≈ −6 to −8 LUFS integrated** (djent often pushes −6). This is despite platform normalization at −14 LUFS.
- Pragmatic 2024–2026 target: **−7.5 to −9 LUFS integrated, ≤ −1.0 dBTP**, short-term peaks in choruses/breakdowns hitting −6 to −7 LUFS-S. PSR/crest of ~5–7 dB is normal for the genre.

---

## 6. Orchestral / Synth Layers (Lorna Shore style)

- **HPF aggressively: strings/choir/pads high-passed at 200–400 Hz** (300 Hz is a safe default under a wall of guitars).
- Notch the orchestral bus **200–400 Hz an extra 2–3 dB during dense sections**.
- Arrange by register: high strings/choir coexist fine with guitars; low brass/low strings clash — either drop them or accept they'll only read in breakdowns/intros.
- **Sidechain the orchestral bus:** (a) subtly to kick (1–2 dB GR), and/or (b) a dynamic EQ cut 2–4 dB in 2–5 kHz keyed from lead guitars/vocals.
- Reverb: **long hall on orchestra only** (2.5–4 s decay, pre-delay 20–40 ms, HPF the reverb return at 300–400 Hz, LPF ~8 kHz). Guitars/drums keep short/dry spaces — separate reverb worlds keeps orchestra "huge" while the band stays tight.
- Level: symphonics sit ~6–10 dB under the guitar bus in full sections — felt, not heard. Automate them up hard in intros/breaks; hard automation cuts (no tail, no fade) when slamming from melodic section into breakdown.
- Stereo: keep symphonics wide (they can occupy the sides above 300 Hz since rhythm guitars are hard-panned but midrange-dense).

## 7. Reverb / Delay Conventions

- **Global rule: keep the low end dry.** HPF every reverb/delay return at 300–500 Hz. No reverb on kick, bass, 808s, or rhythm guitars (rhythm guitars stay 100% dry in deathcore).
- **Snare plate:** decay **1.2–2.0 s** (tight modern: 0.8–1.2 s), **pre-delay 20–40 ms**, return HPF 400–500 Hz, LPF ~7–8 kHz. Send snare only (maybe toms).
- **Drum room (short):** 0.3–0.8 s room on kick+snare+toms for "shell glue," compressed hard, tucked low; duck/gate it during blasts.
- **Lead guitar delay:** dual delay — one side **quarter note**, other side **dotted eighth**, **feedback ~25%**, mix ~15–25% as a send. HPF return 400 Hz, LPF 6–8 kHz, duck the delay return with the dry lead. A small plate/hall (1.5–2 s) behind leads, tucked under the delay.
- Cymbals/OH: usually dry or share the short room.

## 8. Leaving Space for Vocals (instrumental deliverable)

- **The vocal pocket is 1–5 kHz, centered on 2–4 kHz** (harsh deathcore vocals are almost entirely mid/upper-mid energy — screams have no fundamental to protect, so the *presence* band is everything). Also watch 250 Hz: excess low-mid buildup masks 2–5 kHz perceptually.
- Static prep on the instrumental:
  - Don't boost guitar bus 2–4 kHz; if anything, keep guitars at −1 to −2 dB in that band.
  - Keep the 300–500 Hz mud cuts described above — they double as vocal clarity.
  - Center channel discipline: keep leads/synths that occupy 1–4 kHz off dead-center or automated down when vocals will be present.
- **Headroom: leave 3–5 dB.** Deliver the instrumental peaking around −6 dBFS with the mix bus comp printed but **no mastering limiter** (send both a "vocal-up-ready" unmastered pass and a reference-loud master). The vocal will sit on top and the final master happens after the vocal is in.

---

## Quick-Reference Implementation Table

| Element | Chain (in order) | Key numbers |
|---|---|---|
| Rhythm gtr (x2, 100L/100R) | TS-sim (HPF300, drive 0, level max) → amp (gain ~40%) → V30/57+421 IR → HPF 80–120 → LPF 10k → cut 400 Hz −3 → notch ~4 kHz −4 (Q6) → dyn EQ 100–180 Hz | — |
| Kick | sample blend → HPF 35 → +3 @ 60 → −4 @ 400 → +5 @ 4–6k → comp 4:1/5ms/80ms → clip 2–3 dB | forward of guitars |
| Snare | sample blend → +3 @ 200 → −3 @ 500 → +4 @ 5k → transient +3 → comp 6:1/20ms/200ms → plate send (1.5 s, 30 ms PD) | ~+3 dB over kick |
| Drum bus | glue 4:1/10–30ms/auto, 2–3 dB GR → soft clip 2–4 dB | + parallel crush 10–20 dB GR blended −8 dB |
| Bass | split 150–250 Hz: low=clean+heavy comp, high=distorted → recombine → sidechain-duck sub band 2–3 dB from kick → mono <120 Hz | −3 to −6 dB under gtrs |
| 808 | tune to key → limiter on spike → 50–100 ms fade-in → duck bass <150 Hz → automate up through decay | mono, saturated |
| Symphonics | HPF 300 → dyn cut 2–5 kHz from leads → hall 3 s (return HPF 350) → sidechain kick 1–2 dB | −6 to −10 dB under gtrs |
| Mix bus | SSL 2:1/30ms/auto 2–3 dB → tape sat | leave 3–6 dB headroom |
| Master | EQ (≤1.5 dB tilt) → MB comp lows 1–2 dB → clipper 2–4 dB → TP limiter | **−7.5 to −9 LUFS-I, −1.0 dBTP** |
| Vocal space | dyn EQ −2 to −3 dB @ 2–4 kHz on gtr bus | instrumental peaks ~−6 dBFS |

Sources: Chernobyl Audio (quad panning), Nail The Mix (kick EQ, parallel compression, LUFS, 808s in dense metal, guitar EQ, SSL bus comp, Lorna Shore/Schroeder guitars, delay, plate reverb, vocal EQ), URM Academy (bass), Sage Audio (kick & 808, vocal space), izotope (mastering metal), Fader & Knob (Tube Screamer), Gearspace/SevenString/Ultimate Metal loudness threads, Riffhard (mixing death metal).
