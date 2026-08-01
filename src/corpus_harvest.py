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


def get(url, binary=False):
    req = urllib.request.Request(url, headers={"User-Agent": "research/1.0"})
    with urllib.request.urlopen(req, timeout=30) as r:
        data = r.read()
    if binary:
        return data
    return json.loads(data)


def norm(s):
    return "".join(c for c in s.lower() if c.isalnum())


def harvest_song(artist, title):
    slug = f"{norm(artist)}__{norm(title)}"
    out = os.path.join(RAW, slug + ".json")
    if os.path.exists(out):
        return "cached"
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
    meta = get(f"https://www.songsterr.com/api/meta/{hit['songId']}")
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
    ok = 0
    for artist, title in CANON:
        try:
            r = harvest_song(artist, title)
        except Exception as e:
            r = f"ERR {e}"
        print(f"{artist} - {title}: {r}")
        if r.startswith("ok"):
            ok += 1
        time.sleep(1.2)
    print(f"harvested {ok}/{len(CANON)}")


if __name__ == "__main__":
    import urllib.parse
    main()
