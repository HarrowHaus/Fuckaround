# JAM THREAD — song 2 (untitled, band names it once a riff sticks)

SINGER: CARRION LIGHT is decent. Standing note, applies to everything
from here on: I hate the symphonic stuff — no strings, no drone, no
choir, ever, even in sections drawn from a reference that has them.
Archived at jam/archive/carrion_light/.

New process for this song: I audition riff candidates before anything
else gets written. src/riff_candidates.py generates real rendered
options; I pick one riff at a time; the room only gets a skeleton to
iterate on once I've built it out of riffs I actually chose.

MODERATOR: Room's open for song 2. Reference lock unchanged (Sun//Eater
minus its orchestra / Amongst the Low & Empty / Second Death). Drop G.
First candidate batch: an opening/seed riff, mid-tempo, ref-locked,
no assumptions about section role yet — whichever one the singer likes
becomes the trunk the rest of the song grows from.

---

SINGER: picking candidate 1 (`1-1-1---1---1-0---0-0---0-------`,
G#→G, a half-step falling to the tuning's actual root — that's the
seed). Direction, not a suggestion: half-time breakdown, two rhythm
guitars on this exact riff, and a lead — Archspire density crossed with
Black Dahlia Murder contour, sweep-adjacent but NOT straight sweeps.

Section is in the songdoc as `the_halving`, 8 bars @ 96 BPM. I wrote
the lead myself (new engine capability, `lead: "techlead"` in
songband.py) rather than leave it to RIFT's usual tab-space method,
since sweep/legato phrasing needs finer time resolution than the
16-slot riff grid supports: harmonic-minor and diminished figures,
ordered non-monotonically (skips, direction changes — not one
string-per-fret), grouped 5/6/7/4 notes-per-beat so the line runs
polymetric against the riff instead of locking to its grid, legato
hammer-on/pull-off on the tight intervals, one trill or bend flourish
closing every other bar. Rooted at the open string, two octaves up.

GRAVES: this needs a REAL half-time feel — snare on 3 only, not the
usual 2-and-4 backbeat, kick following the riff's onsets (9 of them,
kick_lo/hi left wide at 6-12 as a hint, not a lock). I left china as
the preferred cymbal (breakdown convention) but the exact pattern is
yours.

MARROW: standard breakdown doctrine applies — grind-glue bass on
`follow`, sub on, subdrop on the downbeat. Your call if that's still
right once you hear the lead sitting on top; if the lead needs the low
end to duck out of its way anywhere, say so.

The riff itself does not move — it's the chosen candidate, unedited.
Critique the drums, the bass, and the lead's execution; don't relitigate
the riff.

— SINGER

---

SINGER: the_halving rebuilt to spec — half-time backbone (kick 1, snare
3), china escalates 4-then-8 three times before the sweep enters at bar
6, sweep built from candidate 1's own onsets/pitches as accents inside
a fast diminished cascade. Approved as section 1.

Next: candidate 3 (`1---1-1-1-----1-----0-0-0-----0-`). Two new sections:

- `the_reckoning` — ultra-fast BDM/Archspire tech-death. Candidate 3 at
  235 BPM, kick+snare glued to the riff exactly (unison wall, Archspire
  style), ride quarters. A riffsweep flourish in the last 2 bars as the
  transition into the drop.
- `the_dead_reach` — the ending. NOT a fresh riff: candidate 3's genome
  run through `t_augment` twice (recursive derivation, same mechanism
  as CARRION LIGHT's section chain) — 9 onsets down to 3 (slots 0, 7,
  15), at 44 BPM. That's real dead space: multi-second silence between
  hits. New engine capability `riff_burst`: each isolated hit gets a
  fast 2-note chromatic approach immediately before it lands, so the
  hits themselves stay technical even though the section is almost
  entirely silence — the 2026/Lorna Shore ending-breakdown move.

GRAVES: the_reckoning's drums are hand-written (kick=snare=riff mask,
unison, at 235 BPM) rather than book-mode — didn't want the corpus
sampler softening an intentionally mechanical/glued-to-the-riff wall.
the_dead_reach's kick+china land only on the riff's 3 surviving onsets,
nothing else. Both are open for your critique/revision same as any
other drum part.

MARROW: bass stays `follow` on both — grind-glue on the fast wall,
naturally near-silent on the sparse breakdown since it locks to the
riff. Your call if that's still right once you hear it.

— SINGER
