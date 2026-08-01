"""Harvest the MySpace-era deathcore tab canon from Songsterr's public API
(research use). Saves per-song guitar-track JSONs to corpus/raw/ (gitignored —
we commit only aggregate idiom statistics, never the transcriptions)."""

import os
import sys
import json
import gzip
import time
import urllib.request

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAW = os.path.join(REPO, "corpus", "raw")

CDN = ["dqsljvtekg760", "d34shlm8p2ums2", "d3cqchs6g3b5ew"]

# (artist, title) canon — era deathcore riff-language sources
CANON = [
    ("Suicide Silence", "Unanswered"),
    ("Suicide Silence", "No Pity For A Coward"),
    ("Suicide Silence", "Bludgeoned To Death"),
    ("Suicide Silence", "Wake Up"),
    ("Job For A Cowboy", "Entombment Of A Machine"),
    ("Job For A Cowboy", "Knee Deep"),
    ("Carnifex", "Slit Wrist Savior"),
    ("Carnifex", "Lie To My Face"),
    ("Carnifex", "Hell Chose Me"),
    ("Whitechapel", "This Is Exile"),
    ("Whitechapel", "Possession"),
    ("Whitechapel", "The Somatic Defilement"),
    ("Whitechapel", "Vicer Exciser"),
    ("Despised Icon", "MVP"),
    ("Despised Icon", "Furtive Monologue"),
    ("Oceano", "District Of Misery"),
    ("As Blood Runs Black", "In Dying Days"),
    ("As Blood Runs Black", "My Fears Have Become Phobias"),
    ("Bring Me The Horizon", "Pray For Plagues"),
    ("Bring Me The Horizon", "Diamonds Arent Forever"),
    ("All Shall Perish", "Eradication"),
    ("All Shall Perish", "The Day Of Justice"),
    ("Annotations Of An Autopsy", "Welcome To Sludge City"),
    ("Waking The Cadaver", "Chased Through The Woods By A Rapist"),
    ("Emmure", "10 Signs You Should Leave"),
    ("Salt The Wound", "Carnal Repercussions"),
]


# Modern canon (2018–2026), Songsterr IDs verified via live API survey
# (docs/17). Buckets: symphonic / slam / nu / techdeath / downtempo-skronk.
MODERN = [
    ("Lorna Shore", "To The Hellfire", 486572),
    ("Lorna Shore", "Pain Remains I Dancing Like Flames", 519743),
    ("Lorna Shore", "Sun Eater", 510139),
    ("Lorna Shore", "Pain Remains III In A Sea Of Fire", 532662),
    ("Lorna Shore", "Oblivion", 1508430),
    ("Shadow Of Intent", "The Heretic Prevails", 1158073),
    ("Shadow Of Intent", "Intensified Genocide", 954231),
    ("Shadow Of Intent", "From Ruin We Rise", 954346),
    ("Worm Shepherd", "The River Ov Knives", 501808),
    ("Ov Sulfur", "Death Ov Circumstance", 583912),
    ("Slaughter To Prevail", "Baba Yaga", 496758),
    ("Slaughter To Prevail", "Bratva", 489752),
    ("Slaughter To Prevail", "Viking", 545423),
    ("Peelingflesh", "Shoot 2 Kill", 671490),
    ("Peelingflesh", "Perc 3000", 695639),
    ("Peelingflesh", "211 187 FFWAS", 567688),
    ("Signs Of The Swarm", "Amongst The Low And Empty", 553863),
    ("Signs Of The Swarm", "Death Whistle", 492296),
    ("AngelMaker", "Leech", 539809),
    ("Alpha Wolf", "Akudama", 467953),
    ("Alpha Wolf", "60cm Of Steel", 565179),
    ("Paleface Swiss", "The Orphan", 550066),
    ("Paleface Swiss", "River Of Sorrows", 895976),
    ("Knocked Loose", "Suffocate", 604956),
    ("Knocked Loose", "Blinding Faith", 591561),
    ("Knocked Loose", "Deep In The Willow", 551773),
    ("Bodysnatcher", "King Of The Rats", 709801),
    ("Whitechapel", "When A Demon Defiles A Witch", 451069),
    ("Whitechapel", "Hymns In Dissonance", 928410),
    ("Rivers Of Nihil", "The Silent Life", 446552),
    ("Rivers Of Nihil", "Where Owls Know My Name", 458926),
    ("First Fragment", "Gloire Eternelle", 527069),
    ("Fit For An Autopsy", "Two Towers", 882903),
    ("Fit For An Autopsy", "Your Pain Is Mine", 496499),
    ("Black Tongue", "Second Death", 481677),
    ("Black Tongue", "The Eternal Return To Ruin", 468287),
    ("Distant", "Exofilth", 523326),
    ("Enterprise Earth", "Psalm Of Agony", 533253),
    ("Humanitys Last Breath", "Abyssal Mouth", 443209),
]

ERA = os.environ.get("ERA", "2007")
if ERA == "modern":
    RAW = os.path.join(REPO, "corpus", "raw_modern")


def get(url, binary=False):
    req = urllib.request.Request(url, headers={"User-Agent": "research/1.0"})
    with urllib.request.urlopen(req, timeout=30) as r:
        data = r.read()
    if binary:
        return data
    return json.loads(data)


def norm(s):
    return "".join(c for c in s.lower() if c.isalnum())


def harvest_song(artist, title, song_id=None):
    slug = f"{norm(artist)}__{norm(title)}"
    out = os.path.join(RAW, slug + ".json")
    if os.path.exists(out):
        return "cached"
    if song_id is None:
        q = urllib.parse.quote(f"{artist} {title}")
        hits = get(f"https://www.songsterr.com/api/songs?pattern={q}&size=10")
        hit = None
        for h in hits:
            if norm(h["artist"]) == norm(artist) and norm(title) in norm(h["title"]):
                hit = h
                break
        if hit is None:
            for h in hits:
                if norm(artist) in norm(h["artist"]):
                    hit = h
                    break
        if hit is None:
            return "notfound"
        song_id = hit["songId"]
    meta = get(f"https://www.songsterr.com/api/meta/{song_id}")
    image = meta.get("image")
    rev = meta["revisionId"]
    song = dict(artist=meta["artist"], title=meta["title"],
                songId=meta["songId"], revisionId=rev, parts=[])
    for pid, tr in enumerate(meta["tracks"]):
        if tr.get("isEmpty"):
            continue
        inst = tr.get("instrument", "")
        if "Guitar" not in inst and "Drums" not in inst and "Bass" not in inst:
            continue
        for k, dom in enumerate(CDN):
            try:
                raw = get(f"https://{dom}.cloudfront.net/"
                          f"{meta['songId']}/{rev}/{image}/{pid}.json",
                          binary=True)
                if raw[:2] == b"\x1f\x8b":
                    raw = gzip.decompress(raw)
                part = json.loads(raw)
                part["_trackmeta"] = tr
                song["parts"].append(part)
                break
            except Exception:
                if k == len(CDN) - 1:
                    pass
        time.sleep(0.8)
    with open(out, "w") as f:
        json.dump(song, f)
    return f"ok ({len(song['parts'])} parts)"


def main():
    os.makedirs(RAW, exist_ok=True)
    import urllib.parse
    canon = [(a, t, None) for a, t in CANON]
    if ERA == "modern":
        canon = MODERN
    ok = 0
    for artist, title, song_id in canon:
        try:
            r = harvest_song(artist, title, song_id)
        except Exception as e:
            r = f"ERR {e}"
        print(f"{artist} - {title}: {r}")
        if r.startswith("ok"):
            ok += 1
        time.sleep(1.2)
    print(f"harvested {ok}/{len(canon)}")


if __name__ == "__main__":
    import urllib.parse
    main()
