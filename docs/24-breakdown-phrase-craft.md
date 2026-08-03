# Breakdown Phrase Craft — mined data + research (2026-08-02)

Prompted by feedback that our breakdowns needed to "study more" — the
engine was writing one 16-slot mask and repeating it identically for
every bar of a section. Real breakdowns don't do that. Two independent
sources converged on the same answer.

## 1. Corpus mining: real multi-bar phrase sequences

Mined 98 consecutive-bar breakdown-tempo runs (≥4 bars) directly from the
raw tab data behind `corpus/refs.json`'s source songs (Leech, Second
Death, The Eternal Return To Ruin, King of the Rats). Each run's bars
were reduced to letters by mask identity to reveal the macro-shape:

```
Leech (82 bars):  AAABAAABCDCDCDCDCDDDEDDDECCFGFHFGFHFGFHGGGGIJIKIJIKCLCECEDECLCECEDEMNMNMNMNCCCDCCO
Second Death (68): ABCDABCEEEEEEEEFGHGFGHGFGHGFGHGIGHGFGHGICCCCCCCCJJJCJJJKJJJKABLMABLN
Eternal Return (69): AAABAAABAAABAAACAAABAAABAAABAAABDEFGHFGIJAKLAKLLAAKAMAKAMDNDOODDNDOOD
King of the Rats (8): ABACABAC
```

**AAAB chained repeatedly is the single dominant shape** — three bars of
one pattern, one bar of a turn, over and over (Leech, Eternal Return to
Ruin both open this way). **ABAC** (alternating call/response where the
*response itself varies*) is the other recurring shape (King of the
Rats). Long breakdowns (60+ bars) develop through a slow succession of
these blocks, reusing earlier letters later (recapitulation), not one
loop held the whole time.

## 2. Research: what the turn/response actually is

A research pass (tab-level transcription analysis, not just genre
essays) refined this further:

- **The "response" is usually a perturbation of the call, not a fresh
  riff.** Whitechapel's "This Is Exile" Breakdown 1: the whole phrase
  sits on the pedal note for every hit *except the final 1–2 sixteenth
  slots*, which jump a half-step before the loop restarts. Same mask,
  answer note only at the tail — cheaper and more idiomatic than writing
  an unrelated second pattern.
- **Phrase groups** (`ABC×4`) are real too — "This Is Exile" Breakdown 3
  cycles three genuinely distinct 1-bar patterns as a repeating unit.
- **In-bar density ramps**: a single repeated bar that itself goes
  sparse-to-dense within its own 16 slots (a micro-crescendo baked into
  the loop, re-played every repetition) — "This Is Exile" 9/4 Breakdown
  2.
- **Squeals/pinch harmonics and callouts land on the response bar or the
  top of the phrase group** — not scattered uniformly through pedal call
  bars. They mark the same structural seam as the pitch answer-note.
- **Named rhythm-cell vocabulary**: gallop (8th+16th+16th over a pedal),
  quadruplet (4-against-3 vs. a triplet-feel kick), two-step/skank
  (syncopated bounce, often used as a *contrasting section* rather than
  an in-breakdown device).
- **Escalation across a long breakdown** happens via mutation operators
  walked forward bar to bar (add a hit / displace a hit / halve density
  / stutter-burst) — not a real tempo change mid-section; save actual
  BPM shifts for section boundaries.

## 3. What shipped

`src/songband.py` now supports `phrase` (a letter sequence, e.g.
`["A","A","A","B","A","A","A","B"]`) and `phrase_riffs` (dict of
letter → riff-dict for anything other than "A", which always falls back
to the section's own `riff`) — directly implementing the AAAB/ABAC
macro-shape and the "response = perturbed call" convention. `the_dead_reach`
was rebuilt this way: pattern A is the recursively-derived sparse riff,
pattern B is the SAME mask with its pitches inverted (the half-step
answer, corpus-attested), phrase = `AAABAAAB`.

Not yet implemented (candidates for the next pass): explicit `LOOP` /
`CALL_RESPONSE` / `PHRASE_GROUP` / `ARC` form labels, in-bar density
ramps, and named rhythm-cell generators (gallop/quadruplet) as first-class
mask primitives rather than emergent from the general mask sampler.
