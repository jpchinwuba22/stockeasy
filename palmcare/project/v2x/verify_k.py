"""Verify straightening: for every 4th frame of the range, predict where the corrected body edges must be (axis
c0 +- widest-row/2 from the saved raw edges) and line-search them in a tight band on the OUTPUT clip."""
import sys, cv2, numpy as np
from scipy.ndimage import gaussian_filter1d, median_filter
sys.path.insert(0, "v2x"); sys.path.insert(0, "labelfix")
from linesearch import edges
from fixclip2 import read_frames
out, t0, y0, y1 = sys.argv[1], float(sys.argv[2]), int(sys.argv[3]), int(sys.argv[4])
raw = np.load(out.replace(".mp4", "_edges.npy"))
P = raw.copy()
for j in range(4):
    P[:, j] = gaussian_filter1d(median_filter(P[:, j], 9, mode="nearest"), 3, mode="nearest")
F = read_frames(out)
i0 = int(round(t0 * 24)); ym = (y0 + y1) / 2
res = []
for n in range(0, len(P), 4):
    kl, ml, kr, mr = P[n]
    yc = np.array([y0, y1], float)
    w = (mr + kr * (yc - ym)) - (ml + kl * (yc - ym))
    c0 = (ml + mr) / 2
    half = w.max() / 2
    f = cv2.cvtColor(F[i0 + n], cv2.COLOR_RGB2BGR)
    (a, b), _ = edges(f, y0, y1, c0 - half, c0 + half, band=10)
    res.append((np.degrees(np.arctan(a[1])), np.degrees(np.arctan(b[1]))))
r = np.array(res)
if len(sys.argv) > 5:
    for n, (l, rr) in zip(range(0, len(P), 4), res): print(f"  frame {i0 + n:3d}  L {l:+.2f}  R {rr:+.2f}  raw L {np.degrees(np.arctan(raw[n,0])):+.2f} R {np.degrees(np.arctan(raw[n,2])):+.2f}")
print(f"{out}: after L {r[:,0].min():+.2f}..{r[:,0].max():+.2f}  R {r[:,1].min():+.2f}..{r[:,1].max():+.2f}  (mean |angle| {np.abs(r).mean():.2f})")
