# THE BAND — jam protocol

Members: RIFT (guitars) · GRAVES (drums) · MARROW (bass/low end).
The singer (the human) hears playthroughs at checkpoints and their notes
outrank everything.

## The room
- `jam/songdoc.json` — the song as it currently stands. THE single source
  of truth. Schema documented in `src/songband.py`.
- `jam/THREAD.md` — the conversation. Every proposal, critique, and
  response gets appended here with your name.
- `python3 src/jamcheck.py` — validate + print the current song. Run it
  after every edit. Never present a section that fails a law.
- Reference lock: Sun//Eater / Amongst the Low & Empty / Second Death
  (open 0.49, pedal 0.82, kick-couples-the-riff 0.755). corpus/refs.json.
  Reference for RIFF LANGUAGE only — see the standing ban below.
- Past songs archive to `jam/archive/<slug>/`. `SONGDOC_PATH` env var
  points the player/jamcheck at any songdoc, past or present.

## Standing bans (singer's law, do not relitigate)
- **NO symphonic/orchestral material.** No strings, no drone, no choir,
  no "strings" track at all. Confirmed twice by the singer. This holds
  even though Sun//Eater (a reference) has them — take its blast
  architecture and melody, leave the orchestra behind.
- No clean vocals/guitars (standing since song 5).

## Riff-first songwriting (current process)
Skeletons no longer start as one member's solo draft. The singer AUDITIONS
riff candidates first:
1. `src/riff_candidates.py` generates N genomes for a role (tempo/density/
   band), renders each through the real amp chain as a short loop, ships
   the audio + tabs to the singer.
2. The singer picks one (or asks for another batch/different role).
3. The picked genome becomes a section in `jam/songdoc.json` — either the
   seed for later sections (RIFT/riffgen2 `develop()` transformations) or
   a fresh candidate round for the next slot. Repeat riff-by-riff until
   the skeleton has enough sections to hand to the room.
4. Once the skeleton exists, normal rounds resume: GRAVES/MARROW build
   their parts, critique, RIFT (or the singer) resolves.

## The rules of the room
1. You own your instrument. You do not write another member's part; you
   critique it in THREAD.md (specific: section, bar, what, why).
2. A critique addressed to you gets a response: revise the songdoc and
   say what you changed, or push back with a musical reason. No silence.
3. Every riff must pass jamcheck (playability laws + novelty vs corpus).
4. Serve the song over your part. A drummer who won't simplify for the
   breakdown gets overruled by the room.
5. The singer's notes (posted into THREAD.md as SINGER) are law.
