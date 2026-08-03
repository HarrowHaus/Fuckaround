# Modern Deathcore / Tech-Death Corpus Candidates (2018–2026) — Songsterr Verified

Live-API survey (2026-08-01) for the second idiom table: the **modern dialect**
to complement the 2006–2010 canon already mined in `src/riffdb.py`. Raw scan
JSON for all 28 queried artists: `corpus/modern_scan_seed.json`.

## API observations (harvester notes)

- Endpoint `https://www.songsterr.com/api/songs?pattern=<query>&size=N` confirmed working. Response is a JSON array with `songId`, `artistId`, `artist`, `title`, `tracks[]` (each with `instrumentId`, `tuning` as MIDI-note array high→low, `difficulty`, `views`, `hash`), `defaultTrack`, `isJunk`.
- **BPM is NOT in the search response.** Tempo lives in the per-revision Guitar Pro data the harvester already pulls — BPMs below are approximate, marked `~`. Treat revision data as authoritative.
- Tunings decoded from actual `tuning` arrays (e.g. `[62,57,53,48,43,38,31]` = G1 D2 G2 C3 F3 A3 D4 = 7-string drop G).
- Junk pollution: search matches on substring — "Distant", "Black Tongue", "Mental Cruelty" return Rush/Mastodon/meme tabs. Filter by `artistId` after first hit. Exclude titles containing "AI" (auto-transcribed).
- Peelingflesh exists under TWO artist spellings: "Peelingflesh" (high-view originals) and "PeelingFlesh" — harvest both.
- Archspire is a takedown casualty: no tabs under the real name; community re-uploads live under "Archfire"/"Archspir"/"Misc covers". Single-source — treat skeptically.

## Candidate list

Format: **Artist — Title** | songId | observed tuning | ~BPM | notes

### modern-symphonic
1. **Lorna Shore — To The Hellfire** | 486572 | 7-str drop G (G1 D2 G2 C3 F3 A3 D4) | ~250 | 11 tracks incl. bass/drums/synths, 196k views
2. **Lorna Shore — Pain Remains I: Dancing Like Flames** | 519743 | 7-str drop G | ~180 | 15 tracks, 205k views
3. **Lorna Shore — Sun//Eater** | 510139 | 7-str drop G | ~220 | 17 tracks
4. **Lorna Shore — Pain Remains III: In a Sea of Fire** | 532662 | 7-str drop G | ~240 | 18 tracks
5. **Lorna Shore — Oblivion** (2025) | 1508430 | 7-str drop G | ~200 | 10 tracks — newest album era
6. **Shadow of Intent — The Heretic Prevails** | 1158073 | 6-str drop A# | ~230 | 37k views
7. **Shadow of Intent — Barren and Breathless Macrocosm** | 533934 | 6-str drop B | ~210
8. **Shadow of Intent — Intensified Genocide** | 954231 | 6-str drop B | ~260 | 14 tracks
9. **Shadow of Intent — From Ruin We Rise** | 954346 | 6-str drop A# | ~250 | official "SH Tab Book" series (IDs 1516709–1928391) is band-sourced — prefer those revisions
10. **Mental Cruelty — Symphony of a Dying Star** | 539283 | 7-str drop G | ~230
11. **Mental Cruelty — Ultima Hypocrita** | 832246 | 6-str D-standard-ish | ~200
12. **Mental Cruelty — Zwielicht** | 537074 | 7-str drop A | ~220
13. **Worm Shepherd — The River Ov Knives** | 501808 | 7-str drop E | ~150 | 11 tracks
14. **Ov Sulfur — Death ov Circumstance** | 583912 | 7-str drop G | ~190 | 10 tracks

### slam / -core slam hybrid
15. **Slaughter to Prevail — Baba Yaga** | 496758 | 7-str drop A | ~140 | 9 tracks
16. **Slaughter to Prevail — Bratva** | 489752 | 7-str drop A | ~120 | 78k views
17. **Slaughter to Prevail — Viking** | 545423 | 7-str drop A | ~150 | 11 tracks incl. 2 bass
18. **Slaughter to Prevail — 1984** | 516087 | 7-str drop A | ~165
19. **Brand of Sacrifice — Lifeblood** | 482251 | 7-str drop A | ~150 | 9 tracks — the only well-viewed BoS tab
20. **Brand of Sacrifice — Demon King** | 541400 | 7-str drop E | ~140
21. **Brand of Sacrifice — Altered Eyes** | 521226 | 7-str drop F | ~155
22. **Peelingflesh — Shoot 2 Kill** | 671490 | 6-str drop A | ~100 slams / ~230 blasts | 159k views
23. **Peelingflesh — Perc 3000** | 695639 | 6-str drop A | ~110 | 90k views
24. **Peelingflesh — 211/187 & F.F.W.A.S.** | 567688 | 6-str drop A | ~120 | 37k views
25. **Signs of the Swarm — Amongst the Low & Empty** | 553863 | 7-str drop G | ~200
26. **Signs of the Swarm — Cesspool of Ignorance** | 445774 | 7-str drop A | ~240
27. **Signs of the Swarm — Death Whistle** | 492296 | 7-str drop G | ~210 | 11 tracks

### nu-deathcore
28. **Alpha Wolf — Akudama** | 467953 | 7-str drop G variant (G1 D2 G2 C3 **E3** A3 D4 — custom maj-3rd tuning) | ~120
29. **Alpha Wolf — 60cm of Steel** | 565179 | 7-str drop G variant | ~130
30. **Alpha Wolf — Sub-Zero** | 1458322 | 7-str drop F | ~140
31. **Paleface Swiss — The Orphan** | 550066 | 7-str drop G# | ~110 | 5 tracks
32. **Paleface Swiss — River of Sorrows** | 895976 | 6-str drop G# | ~120 | 23k views
33. **Paleface Swiss — Nail to the Tooth** | 1132444 | 7-str drop G# | ~130
34. **Knocked Loose — Suffocate** | 604956 | 7-str A standard | ~120 | 102k views
35. **Knocked Loose — Blinding Faith** | 591561 | 7-str A standard | ~190
36. **Knocked Loose — Deep in the Willow** | 551773 | 7-str A standard | ~150
37. **ten56. — Boy** | 886097 | 7-str drop G | ~110
38. **ten56. — Earwig** | 1174705 | 7-str A-std variant | ~120 (thin coverage — see flags)
39. **Whitechapel — When a Demon Defiles a Witch** | 451069 | 7-str drop G | ~170 | 10 tracks (The Valley, 2019)
40. **Whitechapel — Hymns in Dissonance** | 928410 | 7-str drop G | ~230 | 2025 album, 24k views
41. **Whitechapel — A Bloodsoaked Symphony** | 495113 | 7-str drop G | ~150 (Kin, 2021)

### techdeath
42. **Rivers of Nihil — The Silent Life** | 446552 | 7-str drop F# | ~140 | 30k views
43. **Rivers of Nihil — Where Owls Know My Name** | 458926 | 7-str drop F# | ~150 | 16 tracks
44. **Rivers of Nihil — Focus** | 560684 | 7-str drop F# | ~130 (The Work, 2021)
45. **Archspire — Limb of Leviticus** (as "Archfire") | 4680442 / 5285736 | 8-str E1 std | ~112 (16ths at blast ≈ feels ~380)
46. **Archspire — Bleed the Future** (as "Misc covers", E-std TRANSPOSED) | 2889778 | 6-str E std | ~185 | 30k views — original is drop C# 8-str
47. **Archspire — Acrid Canon** (as "Archfire") | 547659 | 8-str drop E | ~200
48. **First Fragment — Gloire Éternelle** | 527069 | 7-str drop G# | ~180 | 13 tracks (2021)

### skronk / diss-core / downtempo
49. **Fit for an Autopsy — Two Towers** | 882903 | 7-str drop G | ~140 | also: Your Pain Is Mine 496499, Hostage 683402, No Man Is Without Fear 476166 — all 7–10 tracks, drop A/G
50. **Black Tongue — Second Death** | 481677 | 6-str drop C1 (octave-down) | ~70 | 19k views
51. **Black Tongue — The Eternal Return to Ruin** | 468287 | 7-str C1 | ~65
52. **Black Tongue — In the Wake ov the Wolf** | 464196 | 6-str D1 octave-down | ~75
53. **Distant — Exofilth** | 523326 | 7-str drop F | ~130 | 14 tracks, best Distant tab
54. **Distant — Oedipism** | 501243 | 7-str drop F | ~120 | 9 tracks
55. **Enterprise Earth — Psalm of Agony** | 533253 | 8-str drop D1 variants | ~190 | 17 tracks; also Unleash Hell 573315, Overpass 539948
56. **Humanity's Last Breath — Abyssal Mouth** | 443209 | thall tuning (E1 B1 E2 A2 G#3 A3) | ~100 | 14 tracks
57. **Vildhjarta — Den Helige Anden** | 463766 | thall | ~95 | 11 tracks

## Under-tabbed flags and substitutes

| Band | Status | Recommendation |
|---|---|---|
| **Archspire** | RED — takedown; only renamed re-uploads, several transposed | Use Archfire IDs but verify vs audio; backfill techdeath with **First Fragment** (Gula 437244, La Veuve et le Martyr 543665), **Obscura** (Akróasis 409380, 53k views), **Beyond Creation** (Omnipresent Perception 91389, 43k views) |
| **ten56.** | YELLOW — ~15 tabs, nearly all 3–4-track, <2k views, inconsistent tunings | Substitute with more Alpha Wolf / Paleface Swiss, or **Bodysnatcher** (King of the Rats 709801, Twelve/Seventeen 1347500, drop G#) |
| **Brand of Sacrifice** | YELLOW — Lifeblood solid; rest low-view, tunings vary wildly per tab | Take Lifeblood + Demon King + Altered Eyes only; backfill symphonic-slam with Worm Shepherd / Ov Sulfur |
| **Mental Cruelty** | YELLOW — mostly 4-track, <2.5k views | Keep 2–3; add **AngelMaker** (Leech 539809 38k views, A Dark Omen 486581 21k views, drop A 7-str) |
| **Distant** | YELLOW-GREEN — top 3 legit, tail thin, search polluted | Usable with artistId filter |
| **Signs of the Swarm** | GREEN-ish | Usable |
| Lorna Shore, Shadow of Intent, STP, Whitechapel, FFAA, Knocked Loose, Alpha Wolf, Paleface Swiss, Peelingflesh, Rivers of Nihil, Black Tongue, Enterprise Earth | GREEN — deep multi-instrument coverage, high views | Harvest freely |

Quality note: Shadow of Intent "(SH Tab Book)" series and Rivers of Nihil
"Official" series (IDs 2050689–2050744) appear band/book-sourced — prefer those
revisions over fan duplicates when both exist.

## Tuning landscape takeaway (writing implications)

The modern corpus is overwhelmingly **7-string drop G territory** (G1 = 24.5 Hz
fundamental — a fourth below our 2007-era drop A#), with distinct dialect
clusters: drop A 7-string for slam (STP, AngelMaker), drop G#/F for nu-deathcore,
A-standard-no-drop for Knocked Loose skronk, octave-down C1/D1 for downtempo,
and drop F#/E 8-string for techdeath. Song 5 should live in 7-string drop G
with the low-tuned bass program, not the 6-string drop A# world of song 4.
