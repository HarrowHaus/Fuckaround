# Riff humanness constraint spec (condensed; full agent report in PR history)
Sources: Shea 2023 GP-corpus study, Easley 2015 riff schemes (267-riff corpus),
Pieslak 2007, Lilja metal harmony, ShredGP, Riffhard/pedagogy consensus.

MOTOR: >=90% of consecutive fret deltas <=3 (hard cap 4 mid-phrase); shifts >3
frets only at phrase boundaries; 4-fret hand window (5 below 120bpm-16ths, +1
above fret 12); open string = zero cost anchor (30-60% of chug-riff notes);
>=85% of chug notes on strings 6-5; fretted notes mostly frets 1-7; power
chords are single shapes (root-position 5ths only under distortion); at 16ths
>=150bpm <=1 string change per beat; tremolo = 1 string.

PITCH: 3-6 distinct pitch classes (reject >7); anchor pitch >=40% of events,
riff starts/ends on anchor; interval weights steps~65%, {m2,M2,m3,P4,P5,TT,P8},
forbid M7/m9 leaps; chromatics only as +-1 neighbors or <=3-note fills; roots
from {1,b2,b3,4,b5,5,b6,b7}.

RHYTHM: rhythm-first ALWAYS (never sample pitch+rhythm independently); beat
cells = {gallop 8+16+16, revgallop, 8+8, 16x4, quarter, tremolo}; syncopation =
repeated grouping cells (3+3+2 etc) resolved at 4-bar boundary, never random
offbeats; NEW PITCHES ONLY ON ACCENTS (reject if >30% of pitch changes on
unaccented 16ths); PM state changes only at accent boundaries, min 2 notes per
state. Speed caps (16th equiv): downpicked 8ths ~160 (elite 212), alt 16ths
~150-200, tremolo ~180-250.

FORM: riff = 1-2 bar unit x4 hypermeasure; two-part schemes (Easley):
statement+terminal alteration (27%), initial repetition+contrast (23%),
statement+terminal repetition, model+sequence. Bars 2-4 share >=60% onsets
with bar 1; variation at the END. Call(chug)/response(<=25% duration, at end).

REJECTION FILTERS: scale-run wandering (>4 same-direction steps w/o anchor);
anchor share <20%; pitch churn on weak 16ths; >7 PCs; no repetition scheme OR
exact x4 (both machine-like); impossible motion; register confusion (chug
strings 6-5 frets 0-7 vs melody strings 4-2 frets 5-12, <=25% leakage);
uniform dynamics; root-motion outside dark-modal set; tempo-technique mismatch.
