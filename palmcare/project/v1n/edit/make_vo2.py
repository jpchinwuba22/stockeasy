"""Lay the phrase-paced Kokoro lines onto the timeline -> vo1n2.wav + words (with phrase ids) for captions.
Word times come from the exact phrase boundaries recorded at synthesis; inside a phrase, words share its time by length.
Usage: make_vo2.py LINES_DIR START1,START2,... TOTAL"""
import json
import re
import sys

import numpy as np
import soundfile as sf
from scipy.signal import resample_poly

LINES_DIR, PLACE, TOTAL = sys.argv[1], [float(x) for x in sys.argv[2].split(",")], float(sys.argv[3])
SR = 48000


def speech_rms(x):
    win = int(0.05 * SR)
    fr = np.array([np.sqrt(np.mean(x[i:i + win] ** 2)) for i in range(0, len(x) - win, win)])
    sel = fr[fr > fr.max() * 0.1]
    return 20 * np.log10(np.sqrt(np.mean(sel ** 2)) + 1e-9)


meta = json.load(open(f"{LINES_DIR}/lines.json"))
mix = np.zeros((int(TOTAL * SR), 2), np.float32)
words, pid = [], 0
for m, at in zip(meta, PLACE):
    x, sr = sf.read(f"{LINES_DIR}/" + m["file"].split("/")[-1], dtype="float32")
    x = resample_poly(x, SR, sr).astype(np.float32)
    x *= 10 ** ((-19 - speech_rms(x)) / 20)
    i0 = int(at * SR)
    seg = x[: len(mix) - i0]
    mix[i0:i0 + len(seg)] += seg[:, None]
    for text, s, e in m["phrases"]:
        ws = text.split()
        wts = np.array([len(re.sub(r"[^A-Za-z0-9]", "", w)) + 2 for w in ws], float)
        edges = s + (e - s) * np.concatenate([[0], np.cumsum(wts) / wts.sum()])
        for w, a, b in zip(ws, edges[:-1], edges[1:]):
            words.append({"text": w, "start": round(at + a, 3), "end": round(at + b, 3), "phrase": pid, "type": "word"})
        pid += 1
    print(f"{at:6.2f}-{at + len(x) / SR:6.2f}  {m['text']}")
sf.write("vo1n2.wav", np.clip(mix, -1, 1), SR, subtype="PCM_16")
json.dump({"words": words}, open("vo1n2_words.json", "w"), indent=1)
