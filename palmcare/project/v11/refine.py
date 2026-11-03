"""Per-frame refinement of the jar body rectangle from real edges: the bottom of the gold band (top of the body) and the
jar's right edge (bright body -> darker background). Output qa/edges.json: [band_bottom_y, right_x] per frame."""
import json
import sys

import cv2
import numpy as np

sys.argv = [sys.argv[0], "x"]
from jarfix import F0, F1, frames, D

BOX0 = (16, 688, 180, 860)
TPL = (40, 692, 150, 845)
cx0, cy0 = (TPL[0] + TPL[2]) / 2, (TPL[1] + TPL[3]) / 2
tr = np.array(json.load(open(D + "v11/qa/track2.json")))
res = []
for i, fr in enumerate(frames()):
    if i < F0:
        continue
    if i > F1:
        break
    x, y, s, _ = tr[i - F0]
    bx, by = x + (BOX0[0] - cx0) * s, y + (BOX0[1] - cy0) * s
    bw, bh = (BOX0[2] - BOX0[0]) * s, (BOX0[3] - BOX0[1]) * s
    hsv = cv2.cvtColor(fr, cv2.COLOR_BGR2HSV).astype(np.float32)
    # band bottom: saturation profile over the label core columns, gold (high S) -> white (low S)
    c0, c1 = int(bx + 0.3 * bw), int(bx + 0.7 * bw)
    ys = np.arange(int(by + 0.30 * bh), int(by + 0.55 * bh))
    sp = hsv[ys, c0:c1, 1].mean(1)
    d = sp[:-3] - sp[3:]
    band_bottom = ys[int(np.argmax(d)) + 2]
    # right edge: value profile across columns in mid-body rows, bright jar -> darker background
    r0, r1 = int(by + 0.55 * bh), int(by + 0.75 * bh)
    xs = np.arange(int(bx + 0.8 * bw), min(fr.shape[1] - 4, int(bx + 1.15 * bw)))
    vp = hsv[r0:r1, xs, 2].mean(0)
    dv = vp[:-3] - vp[3:]
    right = xs[int(np.argmax(dv)) + 1]
    res.append([float(band_bottom), float(right)])
json.dump(res, open(D + "v11/qa/edges.json", "w"))
r = np.array(res)
print(r[::12].round(1).tolist())
