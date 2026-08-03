# NINE UNKNOWN MEN — local REAPER + MCP setup

This is a copy/paste checklist for getting the 8 finished songs from this
repo into REAPER on your own machine, with an AI assistant (via ReaperMCP)
able to see and drive the session directly. Everything below runs on
*your* PC — none of it can be executed from the cloud session that
produced these files.

## 1. Get the files

```
git clone --depth 1 -b claude/deathcore-song-production-rp38dh https://github.com/HarrowHaus/Fuckaround.git "C:\music\NINE UNKNOWN MEN"
```

`--depth 1` skips the older per-song audio-version history (several GB of
superseded FLAC masters) and just pulls the current snapshot (~750MB,
mostly the shipped masters in `songs/*/*.flac`/`.mp3`).

## 2. Install REAPER (if not already) and Reaper-MCP

- REAPER 7+: https://www.reaper.fm/download.php
- [Reaper-MCP](https://github.com/xDarkzx/Reaper-MCP) (xDarkzx) — recommended
  over the alternatives: it's a local file-based Lua bridge (no network port
  opened on your machine), 173 tools across composition/mixing/mastering/
  analysis, one-click Windows installer, cross-platform CI.
  1. Download/clone the repo.
  2. With REAPER open, run `install.bat` — it loads the Lua bridge script
     into REAPER and offers to auto-configure Claude Desktop.
  3. If it doesn't auto-configure, add this to
     `%APPDATA%\Claude\claude_desktop_config.json`:
     ```json
     { "mcpServers": { "reaper": { "command": "reaper-mcp" } } }
     ```

## 3. Install your instrument VSTs

- **EZdrummer** (Toontrack) — drums
- **Odin III** (Solemn Tones) — guitars/lead
- **EZbass** (Toontrack) — bass

## 4. Open a project

Each song has its own ready-to-go MIDI project:
```
songs\<slug>\reaper\<slug>.rpp
```
where `<slug>` is one of: `where_light_comes_to_die`, `six_feet_is_not_enough`,
`the_severed_crown`, `an_opulent_siege_upon_the_drunkard_king`, `curb_gospel`,
`ouroboros_engine`, `all_light_is_carrion`, `carrion_light`.

Read `songs\<slug>\reaper\notes.txt` before touching tracks — it documents
the drum GM pitch map and (on GTR L/R/LEAD) the Odin III keyswitch mapping,
including the one-octave-shift caveat if articulations trigger a row off
from what Odin's GUI shows.

## 5. Start the new chat

Open a **new local** Claude conversation (Desktop app or Claude Code CLI
running on this machine — not the cloud session that built these files;
that one has no path to your REAPER instance). Use the handoff prompt from
the conversation that set this up, or regenerate one by asking for it.
