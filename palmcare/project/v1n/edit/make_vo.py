"""Lay the Kokoro narration lines onto the Video 1 timeline -> vo1n.wav (48 kHz stereo), level-matched, plus
estimated word timings (words_out.json) for the captions. Word timings: the line is split into phrases at its
punctuation, the longest silences in the audio are matched to those phrase breaks, and the words inside each phrase
share the phrase's speech time in proportion to their length."""
import json
import re
import sys

import numpy as np
import soundfile as sf
from scipy.signal import resample_poly

LINES_DIR = sys.argv[1]
PLACE = [float(x) for x in sys.argv[2].split(",")]      # output start time per line
TOTAL = float(sys.argv[3])
SR = 48000


def rms_db(x):
    return 20 * np.log10(np.sqrt(np.mean(x ** 2)) + 1e-9)


def speech_rms(x, sr):
    win = int(0.05 * sr)
    fr = np.array([np.sqrt(np.mean(x[i:i + win] ** 2)) for i in range(0, len(x) - win, win)])
    thr = fr.max() * 0.1
    sel = fr[fr > thr]
    return 20 * np.log10(np.sqrt(np.mean(sel ** 2)) + 1e-9)


def word_times(x, sr, text):
    win = int(0.01 * sr)
    env = np.array([np.sqrt(np.mean(x[i:i + win] ** 2)) for i in range(0, len(x) - win, win)])
    on = env > env.max() * 0.04
    idx = np.nonzero(on)[0]
    t0, t1 = idx[0] * 0.01, (idx[-1] + 1) * 0.01
    # silent runs inside the speech
    gaps = []
    run = None
    for i in range(idx[0], idx[-1] + 1):
        if not on[i]:
            run = i if run is None else run
        elif run is not None:
            gaps.append((run * 0.01, i * 0.01))
            run = None
    words = text.split()
    # phrase breaks after words ending in punctuation (not the last word)
    brk = [k for k, w in enumerate(words[:-1]) if re.search(r"[,.…!?]$|\.\.\.$", w)]
    # match each punctuation break to the silence nearest where it should fall (by character position), in order
    gaps = [g for g in gaps if g[1] - g[0] >= 0.05]
    clen = np.cumsum([len(w) + 1 for w in words])
    chosen, last = [], -1
    for k in brk:
        exp = t0 + (t1 - t0) * clen[k] / clen[-1]
        best = None
        for gi, g in enumerate(gaps):
            if gi <= last:
                continue
            d = abs((g[0] + g[1]) / 2 - exp) - 0.5 * (g[1] - g[0])
            if best is None or d < best[0]:
                best = (d, gi)
        if best is not None and best[0] < 0.8:
            chosen.append(gaps[best[1]])
            last = best[1]
        else:
            chosen.append(None)
    # breaks with no matching silence are dropped (their words join the next phrase)
    brk = [k for k, g in zip(brk, chosen) if g is not None]
    gaps = [g for g in chosen if g is not None]
    bounds = [t0] + [v for g in gaps for v in g] + [t1]
    groups, k0 = [], 0
    for k in brk[:len(gaps)] + [len(words) - 1]:
        groups.append(words[k0:k + 1])
        k0 = k + 1
    out = []
    for gi, grp in enumerate(groups):
        s, e = bounds[2 * gi], bounds[2 * gi + 1]
        wts = np.array([len(re.sub(r"[^A-Za-z0-9]", "", w)) + 2 for w in grp], float)
        edges = s + (e - s) * np.concatenate([[0], np.cumsum(wts) / wts.sum()])
        for w, a, b in zip(grp, edges[:-1], edges[1:]):
            out.append((w, float(a), float(b)))
    return out


meta = json.load(open(f"{LINES_DIR}/lines.json"))
mix = np.zeros((int(TOTAL * SR), 2), np.float32)
words = []
for m, at in zip(meta, PLACE):
    x, sr = sf.read(f"{LINES_DIR}/" + m["file"].split("/")[-1], dtype="float32")
    if x.ndim > 1:
        x = x.mean(1)
    x = resample_poly(x, SR, sr).astype(np.float32)
    x *= 10 ** ((-19 - speech_rms(x, SR)) / 20)
    i0 = int(at * SR)
    mix[i0:i0 + len(x), 0] += x[: len(mix) - i0]
    mix[i0:i0 + len(x), 1] += x[: len(mix) - i0]
    for w, a, b in word_times(x, SR, m["text"]):
        words.append({"text": w, "start": round(at + a, 3), "end": round(at + b, 3), "type": "word"})
    print(f"{at:6.2f}-{at + len(x) / SR:6.2f}  {m['text']}")
sf.write("vo1n.wav", np.clip(mix, -1, 1), SR, subtype="PCM_16")
json.dump({"words": words}, open("vo1n_words.json", "w"), indent=1)
