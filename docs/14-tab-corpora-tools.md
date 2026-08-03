# Tab corpora + tools survey (condensed)
- HuggingFace vldsavelyev/guitar_tab: 47,299 songs as alphaTex, 75MB, one
  command, no gate. Primary bulk corpus.
- Songsterr JSON API (no auth, verified live): /api/songs?pattern=,
  /api/meta/{id}, CloudFront part JSONs with per-note string/fret/duration/
  PM/harmonics/slides + tuning arrays + drum tracks. Research use only.
- DadaGP (26k GP songs, string/fret/technique tokens): request-gated via
  email to Dadabots/Pedro Sarmento. ProgGP (173 prog-metal): same. GOAT
  (played DI + tabs): Zenodo request. No public mirrors.
- GProTab.net (~70k GP files, per-file crawlable) as gap-fill; archive.org.
- Parsing: PyGuitarPro 0.11 (gp3-5, full technique model) [installed OK];
  alphaTab (Node) for GP6/7/8 + alphaTex; MuseScore CLI for GP->MusicXML.
- Method prior art: LooperGP (riff/loop extraction code, public), GTR-CTRL
  (genre conditioning), ShredGP (style feature analysis), MIDI-to-Tab,
  Fretting-Transformer/open-fret; playability: Hori L-inf Viterbi, PDL,
  noahbaculi/guitar-tab-generator (readable cost model), Wiggins&Kim
  co-occurrence feasibility prior (rebuildable from our own mined subset).
