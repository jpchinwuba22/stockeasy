import sys, cv2, numpy as np
sys.path.insert(0, "v2x"); from linesearch import frame, edges
R = {"C2": (2.5, 580, 1360, 370, 740), "C1B": (1.0, 690, 1470, 350, 724), "C3": (1.6, 690, 1470, 346, 724),
     "C4": (2.5, 760, 1470, 386, 700), "C5": (1.5, 740, 1470, 344, 696)}
out = []
for c, (t, y0, y1, xl, xr) in R.items():
    f = frame(f"v2x/src/{c}.mp4", t); (a, b), ym = edges(f, y0, y1, xl, xr)
    for s, k, m in (a, b):
        cv2.line(f, (int(m + k * (y0 - ym)), y0), (int(m + k * (y1 - ym)), y1), (0, 0, 255), 1)
    for x in (xl - 22, xl + 22, xr - 22, xr + 22): cv2.line(f, (x, y0), (x, y0 + 40), (255, 0, 0), 1)
    out.append(f[y0 - 150:y1 + 50, 260:820])
h = min(o.shape[0] for o in out); cv2.imwrite("v2x/lsviz.jpg", np.hstack([o[:h] for o in out]))
