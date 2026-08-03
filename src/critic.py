"""Machine ears: Audiobox-Aesthetics as an automatic critic.

Scores any render on CE (content enjoyment), CU (usefulness), PC
(production complexity), PQ (production quality), ~1-10. Used three ways:
 1. master regression gate (did this revision beat the last one?)
 2. candidate culling: score N section-loop renders, keep the top few
 3. A/B between mix profiles / engine changes

Usage: python3 critic.py file1.wav [file2.wav ...]
"""

import sys
import soundfile as sf
import torch
import audiobox_aesthetics.infer as ab


def _read_wav(item):
    path = item["path"] if isinstance(item, dict) else item
    data, sr = sf.read(str(path), always_2d=True)
    return torch.tensor(data.T, dtype=torch.float32), sr


ab.read_wav = _read_wav
_pred = None


def predictor():
    global _pred
    if _pred is None:
        _pred = ab.initialize_predictor()
    return _pred


def score(path):
    return predictor().forward([{"path": str(path)}])[0]


def main():
    for f in sys.argv[1:]:
        r = score(f)
        print(f"{f}: CE={r['CE']:.2f} CU={r['CU']:.2f} "
              f"PC={r['PC']:.2f} PQ={r['PQ']:.2f}")


if __name__ == "__main__":
    main()
