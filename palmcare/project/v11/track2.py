"""Robust jar tracking for clip 6: multi-scale template match of the jar (lid + band + label, fingers excluded) from
frame F0, searched around the previous position. Output per frame: (cx, bottom_y, scale) relative to BOX0."""
import json
import sys

import cv2
import numpy as np

sys.argv = [sys.argv[0], "x"]
from jarfix import F0, F1, frames, D

BOX0 = (16, 688, 180, 860)
TPL = (40, 692, 150, 845)            # inner patch (left fingers and right thumb excluded)
it = frames()
for _ in range(F0):
    next(it)
f0 = cv2.cvtColor(next(it), cv2.COLOR_BGR2GRAY)
tpl0 = f0[TPL[1]:TPL[3], TPL[0]:TPL[2]]
cx0, cy0 = (TPL[0] + TPL[2]) / 2, (TPL[1] + TPL[3]) / 2
pos, sc, out, sel = (cx0, cy0), 1.0, [(cx0, cy0, 1.0, 1.0)], []
for i, fr in enumerate(it, start=F0 + 1):
    if i > F1:
        break
    g = cv2.cvtColor(fr, cv2.COLOR_BGR2GRAY)
    best = (-1, None)
    for s in np.arange(sc - 0.06, sc + 0.061, 0.015):
        t = cv2.resize(tpl0, None, fx=s, fy=s, interpolation=cv2.INTER_AREA)
        th, tw = t.shape
        x0, y0 = int(pos[0] - tw / 2 - 50), int(pos[1] - th / 2 - 50)
        x0, y0 = max(0, x0), max(0, y0)
        win = g[y0:y0 + th + 100, x0:x0 + tw + 100]
        if win.shape[0] < th or win.shape[1] < tw:
            continue
        r = cv2.matchTemplate(win, t, cv2.TM_CCOEFF_NORMED)
        _, mv, _, ml = cv2.minMaxLoc(r)
        if mv > best[0]:
            best = (mv, (x0 + ml[0] + tw / 2, y0 + ml[1] + th / 2, s))
    pos, sc = best[1][:2], best[1][2]
    out.append((pos[0], pos[1], sc, best[0]))
    if i in (40, 80, 120, 150, 168, F1):
        v = fr.copy()
        w, h = (BOX0[2] - BOX0[0]) * sc, (BOX0[3] - BOX0[1]) * sc
        bx, by = pos[0] + (BOX0[0] - cx0) * sc, pos[1] + (BOX0[1] - cy0) * sc
        cv2.rectangle(v, (int(bx), int(by)), (int(bx + w), int(by + h)), (0, 255, 0), 2)
        cv2.putText(v, f"{i} {best[0]:.2f}", (10, 590), 0, 0.8, (0, 0, 255), 2)
        sel.append(cv2.resize(v[560:1000, 0:330], (198, 264)))
json.dump(out, open(D + "v11/qa/track2.json", "w"))
cv2.imwrite(D + "v11/qa/track2.jpg", np.hstack(sel))
print(min(o[3] for o in out), [round(o[3], 2) for o in out[::10]])
