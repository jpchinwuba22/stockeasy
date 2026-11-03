"""Place the Video 2 narration phrase by phrase on the beat-locked timeline -> vo.wav + vo_words.json.
Each phrase is cut from its recorded line at the recorded phrase boundaries (with breathing room) and placed at its
own start time, so every phrase lands on its shot. Words share their phrase's time by length (for captions).
Usage: make_vo.py LINES_DIR TOTAL"""
import json
import re
import sys

import numpy as np
import soundfile as sf
from scipy.signal import resample_poly

sys.path.insert(0, "../../remake")
import tl2  # noqa: E402

LINES_DIR, TOTAL = sys.argv[1], float(sys.argv[2])
SR = 48000


def speech_rms(x):
    win = int(0.05 * SR)
    fr = np.array([np.sqrt(np.mean(x[i:i + win] ** 2)) for i in range(0, len(x) - win, win)])
    sel = fr[fr > fr.max() * 0.1]
    return 20 * np.log10(np.sqrt(np.mean(sel ** 2)) + 1e-9)


meta = json.load(open(f"{LINES_DIR}/lines.json"))
lines = []
for m in meta:
    x, sr = sf.read(f"{LINES_DIR}/" + m["file"].split("/")[-1], dtype="float32")
    x = resample_poly(x, SR, sr).astype(np.float32)
    x *= 10 ** ((-19 - speech_rms(x)) / 20)
    lines.append((x, m["phrases"]))

mix = np.zeros((int(TOTAL * SR), 2), np.float32)
words, pid = [], 0
for (li, pi, at) in tl2.VO_PLACE:
    x, phr = lines[li]
    text, s, e = phr[pi]
    a, b = max(0, int((s - 0.03) * SR)), min(len(x), int((e + 0.12) * SR))
    seg = x[a:b].copy()
    f = int(0.012 * SR)
    seg[:f] *= np.linspace(0, 1, f)
    seg[-int(0.05 * SR):] *= np.linspace(1, 0, int(0.05 * SR))
    i0 = int((at - (s - a / SR)) * SR)          # 'at' is where the first word starts
    mix[i0:i0 + len(seg)] += seg[:, None]
    ws = text.split()
    wts = np.array([len(re.sub(r"[^A-Za-z0-9]", "", w)) + 2 for w in ws], float)
    edges = at + (e - s) * np.concatenate([[0], np.cumsum(wts) / wts.sum()])
    for w, p, q in zip(ws, edges[:-1], edges[1:]):
        words.append({"text": w, "start": round(p, 3), "end": round(q, 3), "phrase": pid, "type": "word"})
    print(f"{at:6.2f}-{at + e - s:6.2f}  {text}")
    pid += 1
sf.write("vo.wav", np.clip(mix, -1, 1), SR, subtype="PCM_16")
json.dump({"words": words}, open("vo_words.json", "w"), indent=1)
