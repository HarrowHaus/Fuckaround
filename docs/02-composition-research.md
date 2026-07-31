# Blackened Deathcore / Deathcore Composition — MIDI Production Reference

Compiled from web research (Riffhard, Melodigging genre deep-dives, Nail The Mix, drum-programming guides, blast-beat references, the *Metal Music Studies* analysis of Lorna Shore's "To the Hellfire") plus standard genre convention. Notation used below: 16th-note grids where `X` = accented hit, `x` = normal hit, `o` = ghost/soft, `-` = rest. One grid line = 1 bar of 4/4 in 16ths (16 chars) unless noted.

**Global parameters first:** Tuning: Drop G, Drop F#, or lower (7/8-string territory); everything below assumes tonal center = the open low string (call it scale degree 1). Fast sections 180–260 BPM; breakdowns *feel like* 60–90 BPM via half-time. Blackened blast sections sit around 220–260 BPM feel.

---

## 1. Riff Writing

### Scales/modes (in priority order for the genre)
- **Phrygian** (1 b2 b3 4 5 b6 b7) — the b2 is the genre's core color. Riffs hammer 1→b2→1.
- **Phrygian dominant** (1 b2 3 4 5 b6 b7) — "exotic/evil" flavor, great for leads over chugs.
- **Harmonic minor** (1 2 b3 4 5 b6 7) — cited repeatedly as the deathcore favorite; the b6→7 aug-2nd leap is signature. Use for symphonic/lead lines.
- **Locrian** (1 b2 b3 4 b5 b6 b7) — b2 *and* b5 against the pedal; maximum instability for verse riffs.
- **Diminished/octatonic** (half-whole: 1 b2 b3 3 b5 5 6 b7) — for tech runs and diminished arpeggio sweeps (1–b3–b5–6 stacked minor 3rds).
- **Chromatic** — semitone crawls between chug clusters; connective tissue, especially in breakdowns.

### Interval vocabulary
The three load-bearing dissonances: **minor 2nd (b2/b9)**, **tritone (b5)**, **minor 6th (b6)**. Concrete uses:
- **b9 dissonance:** sustain open low string, play b2 one octave + semitone up (the "b9 stab"). Classic blackened chord punch.
- **Tritone dyad:** root + b5 instead of root + 5 power chord on accented hits.
- Melodic cells that always work over a 1-pedal: `1–b2–1–b7`, `1–b3–b2–1`, `1–b5–4–b2`, `5–b6–5–1`.

### Riff archetypes (directly MIDI-able)

**A. Pedal-tone riff (verse workhorse).** Palm-muted open-string 16ths; every 4th–6th hit replaced by a dyad/single note from Phrygian on strings above. Pattern (P = palm-muted pedal 1, N = melody note from {b2, b3, b5, b6}):
```
P P P N  P P N N  P P P N  P N N N     <- vary which slots get N each bar
```
Keep pedal velocity 85–100, melody notes 105–118 so accents pop.

**B. Tremolo riff (blackened).** Straight 16ths (or 32nds at slower BPM), one pitch per 8–16 hits, changing on chord-rhythm boundaries. Construction: pick 4 chord tones outlining i–bII, i–bvi, or i–bII–bvii–i; tremolo each for 2 beats or 1 bar. Melodic minor-key contours that read as "black metal": ascending 1–b3–b6–5, or 1–b2–b3–b2 (claustrophobic). MIDI: alternate velocities 92/78/88/74… (down/up-pick simulation), never flat.

**C. Low-string chug pattern.** All open lowest string, palm mute. Groupings of **3+3+2** or **3+3+3+3+2+2** across 16ths create the push-pull:
```
X--X--X-  X--X--X-      (3-3-2 twice = one bar)
X--X--X--X--X-X-        (3-3-3-3-2-2)
```
- **D. Gallop/burst riff:** `X-xx X-xx X-xx X-xx` (8th + two 16ths) or reverse gallop `xxX- xxX-` (death-metal staple).
- **E. Slam riff:** quarter/8th-note chugs with pitch slides: 1 hit, slide up b2 or b3, back down. Sparse, caveman, quarter-note china over it.

### Dissonant chord voicings (MIDI note stacks, low string = G1 example)
- **Minor 2nd cluster:** root + b2 same octave (G1+Ab1) — muddy/evil low, or root + b9 (G1+Ab2) — clearer, preferred.
- **Tritone dyad:** G1+Db2. **Open-voiced dissonance (blackened):** root + 5 + b9 + b3 spread over 2 octaves (G1–D2–Ab2–Bb2); let ring, no palm mute.
- **Dim triad stabs:** 1–b3–b5. **Augmented** for eerie transitions: 1–3–#5.

### Accents
- **Pinch harmonics:** on the last note of a phrase or beat-4 accent, pitch = 12th/7th/5th-fret harmonic (octave, octave+5th, 2 octaves up). In MIDI: use the sampled "pinch/squeal" articulation or a note 1–2 octaves up with heavy vibrato + high velocity (120+).
- **Octave slides / dive accents:** drop a chord and pitch-bend down a whole step over 1 beat into silence.

---

## 2. Breakdown Writing

Core principle (from every source): **strip to rhythm**. One pitch (open string) or two (root + b2/b5). The riff *is* the rhythm grid. Half-time drums make the section feel 60–90 BPM even if the project tempo doesn't change.

### Syncopation grids (16th base, all single low-string chugs; `D` = downbeat anchor)
```
Basic:        X--X--X---X-X---
Displaced:    X--X--X--X--X---   (three 3s then land)
Off-beat:     -X-X--X--X---X--   (avoid beat 1 after bar 1 — displacement)
Stab+rest:    X---------X-X---   (silence is the instrument)
Busy 2nd half:X--X----X-XX-XX-
```
Rule of thumb: bar 1 establishes, bar 2 repeats, bar 3 repeats, bar 4 varies the last 2 beats (fill/flourish/extra stabs). 4- or 8-bar phrases; total breakdown 8–16 bars.

### 32nd-note "stutter"/bounce patterns
Doubled hits inside a 16th grid (write as two 32nds). The modern "bounce" is chugs with 32nd doubles + rests, often with a slide-up note as the "answer":
```
16th grid with doubles (d = 32nd pair):
d-X--d-X---dd-X-    ->  in 32nds: XX--X---XX--X-----XXXX--X---
Bounce:  X-X-XX--X-X-XXX-   (canonical)
```

### Triplet breakdowns
Switch grid to 8th-note triplets (12 slots/bar). Two standard moves:
```
Full triplet chug:   X-X X-X X-X X-X    (swung, relentless)
Triplet w/ holes:    X-- X-X --X X--
```
Even heavier: keep drums in straight half-time while guitars play triplets (3:2 rub), or metric-modulate so the triplet becomes the new pulse for 2 bars.

### Standard toolkit
- **Half-time feel:** snare moves to beat 3 only. Instant "breakdown" signal.
- **Palm-mute choke:** short staccato chugs (gate note length to ~50–60% of a 16th); occasional fully choked hit (very short + noise articulation).
- **Stops/silence:** 1–2 full beats of total silence before the drop or mid-phrase; also the "false ending" — 1 bar silence, then the real breakdown returns slower.
- **Tension release valve:** alternate 1-bar of chugs with 1-bar of ringing dissonant chord (b9 cluster).
- **Pitch dive:** on the downbeat, whammy/pitch-shift dive (MIDI: pitch bend from 0 to -12 semitones over 1–2 beats on a sustained low note, or dedicated "dive bomb" sample).
- **Callout:** 1 bar before the breakdown, everything stops except a vocal bark ("callout") + maybe one drum hit — cited as a deathcore-specific convention.

### The final/climax breakdown (Lorna Shore model)
Research on "To the Hellfire" confirms heaviness = "contrast and dynamic development towards a climax" with "unconventionally placed breakdowns." Formula for the final breakdown (last 25% of the song):
1. **Setup:** strip texture (ambient/orchestral only, or isolated vocal) for 2–4 bars; riser/swell underneath.
2. **Callout + silence** (½–1 bar).
3. **Drop:** slower than any prior section (drop project tempo 10–20 BPM or go double-half-time), sub drop on beat 1, china quarter notes, kick doubling guitar.
4. **Escalate every 4 bars:** add orchestra/choir layer → add high dissonant tremolo lead over the chugs → add drum 32nd bursts → final 2 bars: everything hits quarter notes in unison, ring out or hard cut.

---

## 3. Drum Writing

### Blast beats (grid = 16ths at 180–260 BPM; K=kick, S=snare, C=cymbal)
- **Traditional blast:** alternating K and S on consecutive 16ths, cymbal with kick: `K-S-K-S-...` (kick on the "e/a", snare on 8ths, or snare-led — either). It's a single-stroke roll split between kick and snare.
- **Hammer blast:** K+S in unison on every 8th note, cymbal unison. Flatter, more brutal wall.
- **Bomb/cannibal blast:** K+S unison on every 16th (kick often doubled 32nds underneath in modern programming). Maximum density.
- **Gravity blast:** snare on every 16th (freehand technique) + kick on 8ths; in MIDI, snare 16ths at reduced, slightly alternating velocity (e.g. 96/84) reads as gravity.
- Cymbal choice during blasts: tight ride bell or closed hat keeps articulation; switch to china for the last 2 bars of a blast section to signal transition. Production note from research: keep blasts articulate — avoid wash.

### Double kick
- Straight 16ths under groove riffs; 32nds for intensity peaks (200+ BPM 16ths ≈ keep 16ths; below ~180, 32nds are playable).
- **Burst vocabulary:** 6-note 32nd burst into a downbeat (`----------KKKKKK|K`), 4-note bursts on beat 4, kick follows guitar gallop exactly.
- Velocity ladder for realism (from programming guides): repeating pattern like **112, 107, 110, 105** ±3, plus 1–3 ms timing jitter; alternate two kick articulations (L/R) if the library has them.

### Breakdown drums (the codified pattern, per Core Wiki + Drumeo)
- **China (or crash) quarter notes** — the timekeeper. Half notes for ultra-slow breakdowns; 8ths for busier ones.
- **Snare on beat 3 only** (half-time). For 2-bar phrases, sometimes snare only on beat 3 of bar 2 (quarter-time feel).
- **Kick copies the guitar chug grid 1:1** — this is the single most important deathcore programming rule. Take the guitar rhythm grid and paste it to the kick, minus hits that collide with the snare.
```
Guitar: X--X--X---X-X---
Kick:   K--K--K---K-K---
Snare:  --------S-------
China:  C---C---C---C---
```

### China vs crash
- **China:** breakdowns, accents on syncopated stabs, "evil" sections, the last cycle of a blast. Trashy/fast decay = rhythmic clarity.
- **Crash:** section downbeats, melodic/soaring sections, transitions. Crash on beat 1 of every new 4/8-bar phrase; china carries interior accents.
- Ride bell: verse grooves and blasts. Open hat 8ths: punky/black-metal d-beat sections.

### Fill vocabulary (1-beat to 1-bar, into a downbeat crash)
- 16th snare→toms cascade: `SSSS TTTT FFFF` (high→floor).
- 32nd single-stroke snare burst on beat 4: `ssssssss` crescendo (velocities ramp 70→120).
- Quads: KKSS or SSKK repeated across toms.
- The "deathcore stutter": full stop, then solo double-kick 32nd burst leads back in.
- Half-bar china choke + silence before a drop.

### Velocities / humanization (consensus from programming guides)
- **Accented snare (backbeat/breakdown):** 110–127. **Blast snare:** 100–115, *not* pinned at 127 — alternate e.g. 115/125.
- **Ghost notes:** 40–70 (put on the "e" and "a" around groove backbeats).
- **Kick:** 105–118 groove, 95–112 during fast doubles; ladder pattern as above.
- **Cymbals:** china/crash 100–120; hat/ride 75–100 with accent pattern (accent the quarter, soften off-beats ~-15).
- Randomize velocity ±5–10 and timing ±1–3 ms (≤8% humanize); quantize feel ~90% strength, not 100%. Keep kick nearly grid-tight in breakdowns (it must lock to guitar); loosen hands slightly more than feet.

---

## 4. Song Structure

Deathcore avoids strict verse-chorus; it's **riff blocks interleaved with momentum-resetting breakdowns**, dynamic arc toward a final climax. Two templates:

**Template A — modern blackened deathcore (Lorna Shore-style, ~5–6 min at 200–240 BPM):**

| Section | Bars | Content |
|---|---|---|
| Symphonic intro | 8–16 | Strings/choir/organ states the main theme; drums enter last 2–4 bars (tom build or blast fade-in); riser into downbeat |
| Blast section A | 16 | Tremolo riff + traditional blast; orchestra sustains pads |
| Groove verse | 8–16 | Pedal-tone riff, double-kick 16ths, ride bell |
| Breakdown #1 (mid-weight) | 8 | Half-time, no orchestra; short |
| Blast section B / melodic peak | 16 | New tremolo theme, harmonized lead, hammer blast |
| Bridge / clean-ambient | 8–16 | Drop to clean guitar/strings/whispered vox; the "breath" |
| Solo or tech section | 8 | Optional; harmonic minor / diminished lead |
| Setup + callout | 2–4 | Strip out, riser, vocal callout, ½–1 bar silence |
| **Final breakdown** | 16–24 | Slowest, heaviest; escalates every 4 bars (see §2) |
| Outro | 4–8 | Orchestra alone restating intro theme, or hard cut on the last chug |

**Template B — classic deathcore (~3.5–4 min):** Intro riff (4–8) → Verse riff (16) → Breakdown 1 (8) → Verse 2/variation (16) → Chorus-ish melodic section (8–16) → Bridge/slam (8) → Callout → Final breakdown (16) → Outro = last breakdown ring-out.

**Transitions:**
- Drum fill (1 beat–1 bar) + crash on new section's beat 1 — default.
- **Stop-time:** all instruments hit beat 1, silence for 3 beats, next section starts — use before breakdowns.
- Risers: reversed cymbal/orchestral swell over last 2 bars of the prior section; snare-roll crescendo for symphonic entrances.
- Metric modulation / tempo drop (-10–20 BPM) reserved for the final breakdown.
- Sub drop straddles every major transition into a heavy section.

---

## 5. Bass Writing

- **Default: double the guitar riff 1:1, one octave below** guitar's written pitch (in drop-G land the bass often ends up at the same sounding octave — just track it tight to the guitar grid). Match note lengths and rests exactly; sloppiness here kills tightness.
- **Divergence points:** (a) during tremolo/blast sections, bass may simplify to root 8th notes while guitars tremolo 16ths; (b) breakdown bar 4: bass adds a slide or octave drop the guitar doesn't play; (c) under clean/ambient bridges, bass holds low pedal whole notes.
- **808/sub drop:** a pitched sine/808 drop on **beat 1 of the breakdown** (and optionally beat 1 of each 8-bar cycle). MIDI: note at root pitch ~G0–C1, pitch envelope falling ~1 octave over 0.5–1.5 s, or dedicated sub-drop sample. Rules from production research: use *sparingly* (breakdown entrances, intros, under clean parts); **shape/cut the tail so it ends before the next kick hit** or it smears the downbeat; leave mix headroom; sidechain the sustained low end to the kick.
- Punchy short 808 "impacts" can also accent individual stop-time hits, not just section starts.

---

## 6. Blackened Elements Specifically

- **Tremolo + blast coupling:** tremolo-picked 16th guitars + traditional/hammer blast is *the* blackened texture. Guitars unmuted (no palm mute), open-voiced chords or single-note lines high on the neck; harmony moves i–bII, i–bvi–bVII, or diminished cycles. Repetition is intentional — repeat a 2-bar tremolo cell 4–8x for the trance effect, changing one note per repeat.
- **Orchestral/choir layering:** strings/choir/pipe-organ sustain the underlying chords of the tremolo riff (whole/half notes), wide stereo, long dark reverb. Automate a swell (velocity/CC1 crescendo) into every breakdown and section change. Choir "ahs/oohs" on the climax breakdown; staccato string 8ths can double chug rhythms for cinematic punch. Sidechain orchestral low end to kick/bass.
- **Dissonant open-voiced chords:** instead of clustered low dissonance, spread it: root low + b9/b5/b13 an octave-plus up, let ring under tremolo. Slide a fixed minor-chord shape up/down while the open low string drones (parallel dissonance against the pedal — canonical black-metal move).
- **Eerie leads over chugs:** while rhythm guitars chug the breakdown grid, a single high lead plays a slow (half/whole-note) melody from **harmonic minor or Phrygian dominant**, 1.5–2 octaves up, light vibrato, drenched in reverb/delay. Target tones: b2, b6, 7, and the b5 — resolve down by semitone. This "beauty over brutality" contrast is the genre's signature climax device.
- **Pedal tones + contrary motion** under sustained blasts (orchestra rises while guitar line falls) keeps long blast sections developing.
- Aesthetic glue: minor-key leitmotif introduced in the symphonic intro, quoted in the melodic peak, then restated by the lead guitar *over* the final breakdown.

---

## Quick MIDI checklist
1. Kick mirrors guitar chugs everywhere except under snare hits.
2. Snare on 3 in breakdowns; china quarters; crash on phrase downbeats.
3. Blast velocities 100–115 snare, humanize ±5–10 vel / 1–3 ms, ~90% quantize; ghost notes 40–70.
4. Chug note lengths ~50–60% of grid value (palm-mute choke); tremolo notes full legato 16ths with alternating velocities.
5. Sub drop on breakdown beat 1, tail gated before next kick.
6. b2 and b5 against an open-string pedal = instant genre authenticity; harmonic minor for leads.
7. Escalate the final breakdown in 4-bar layers; precede it with callout + silence.

**Sources:** Riffhard (deathcore riffs/song/breakdown/black metal guides), Melodigging genre analyses (blackened deathcore, deathcore, dissonant black metal), Mastering.com & Slam Tracks MIDI drum programming guides, Nail The Mix 808 guides, Drumlessons.com & Soulkiller blast-beat references, Core Wiki breakdowns, Drumeo metal guide, *Metal Music Studies* — "Lorna Shore's 'To the Hellfire': A Study in Heaviness" (University of Huddersfield), Ultimate Guitar deathcore lessons.
