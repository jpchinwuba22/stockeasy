"""Label stickiness: the replaced banner must move exactly with the AI banner it covers (which moves with the bottle).
Reports per-frame offset of fixed-banner centre minus source-banner centre; its spread = drift/shake.
Usage: jitter.py SRC FIX label roi t0 t1"""
import sys
import numpy as np
sys.path.insert(0, "labelfix")
import labelpatch as lp, fixclip3 as f3
from fixclip2 import read_frames
src, fix, name, roi, t0, t1 = sys.argv[1], sys.argv[2], sys.argv[3], [int(v) for v in sys.argv[4].split(",")], float(sys.argv[5]), float(sys.argv[6])
f3.use_mask(name)
A, B = read_frames(src), read_frames(fix)
d = []
for i in range(int(t0 * 24), min(len(A), int(t1 * 24))):
    a = lp.find_banner(A[i], roi, close=6, min_fill=0.55)
    b = lp.find_banner(B[i], roi, close=6, min_fill=0.55)
    if a and b:
        d.append(((b[0] + b[2]) / 2 - (a[0] + a[2]) / 2, (b[1] + b[3]) / 2 - (a[1] + a[3]) / 2))
d = np.array(d)
if len(d) < 3:
    print("too few", len(d)); sys.exit()
dd = np.diff(d, axis=0)
print(f"{len(d)} frames  offset mean ({d[:,0].mean():+.1f},{d[:,1].mean():+.1f})  spread x {np.ptp(d[:,0]):.1f} y {np.ptp(d[:,1]):.1f}  frame-to-frame jitter p95 {np.percentile(np.abs(dd),95):.2f}px")
