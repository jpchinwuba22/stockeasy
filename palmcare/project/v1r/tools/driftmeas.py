"""Drift of the replaced label relative to the bottle: the AI's own banner in the source clip moves with the bottle,
so (patched banner - source banner) should stay constant. Prints per-frame offsets and the spread.
Usage: driftmeas.py SRC.mp4 FIXED.mp4 x0,y0,x1,y1 t0 t1"""
import sys
import numpy as np
sys.path.insert(0, "labelfix")
import labelpatch as lp
from fixclip2 import read_frames
src, fix, roi, t0, t1 = sys.argv[1], sys.argv[2], [int(v) for v in sys.argv[3].split(",")], float(sys.argv[4]), float(sys.argv[5])
A, B = read_frames(src), read_frames(fix)
rows = []
for i in range(int(t0 * 24), min(len(A), int(t1 * 24))):
    a = lp.find_banner(A[i], roi, close=6, min_fill=0.6)
    b = lp.find_banner(B[i], roi, close=6, min_fill=0.6)
    if a is None or b is None:
        print(i, "miss", a is None, b is None)
        continue
    ca = np.array([(a[0] + a[2]) / 2, (a[1] + a[3]) / 2, a[2] - a[0]])
    cb = np.array([(b[0] + b[2]) / 2, (b[1] + b[3]) / 2, b[2] - b[0]])
    rows.append((i, *ca, *(cb - ca)))
R = np.array(rows)
for r in R[::3]:
    print(f"f{int(r[0]):3d} src c=({r[1]:6.1f},{r[2]:6.1f}) w={r[3]:5.1f}  patch-src d=({r[4]:+5.1f},{r[5]:+5.1f}) dw={r[6]:+5.1f}")
print("src motion range x %.1f y %.1f" % (np.ptp(R[:, 1]), np.ptp(R[:, 2])))
print("RELATIVE drift range x %.1f y %.1f w %.1f   std x %.2f y %.2f" % (np.ptp(R[:, 4]), np.ptp(R[:, 5]), np.ptp(R[:, 6]), R[:, 4].std(), R[:, 5].std()))
