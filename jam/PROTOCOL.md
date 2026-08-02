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

## The rules of the room
1. You own your instrument. You do not write another member's part; you
   critique it in THREAD.md (specific: section, bar, what, why).
2. A critique addressed to you gets a response: revise the songdoc and
   say what you changed, or push back with a musical reason. No silence.
3. Every riff must pass jamcheck (playability laws + novelty vs corpus).
4. Serve the song over your part. A drummer who won't simplify for the
   breakdown gets overruled by the room.
5. The singer's notes (posted into THREAD.md as SINGER) are law.
