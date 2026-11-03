"""Per-frame bottle straightening. The AI re-shapes the bottle slightly over a shot, so the outer body edges are
measured on EVERY frame of the product range (line search, tracked from frame to frame), smoothed over time
(median then Gaussian, so the correction itself can never wobble), and each frame gets its own row map from
kfix.maps (rows only ever widen about the bottle axis: no zoom, no crop).
Usage: kfix2.py SRC OUT 't0,t1,y0,y1,xl,xr'"""
import subprocess, sys
import cv2, numpy as np
from scipy.ndimage import gaussian_filter1d, median_filter
sys.path.insert(0, "v2x"); sys.path.insert(0, "labelfix")
from linesearch import edges
from kfix import maps
from fixclip2 import read_frames, W, H, FPS

src, dst, spec = sys.argv[1], sys.argv[2], sys.argv[3]
t0, t1, y0, y1, xl, xr = map(float, spec.split(","))
F = read_frames(src)
i0, i1 = int(round(t0 * 24)), min(len(F), int(round(t1 * 24)))
P = []
for i in range(i0, i1):
    f = cv2.cvtColor(F[i], cv2.COLOR_RGB2BGR)
    (a, b), ym = edges(f, int(y0), int(y1), xl, xr, band=14)
    P.append((a[1], a[2], b[1], b[2]))
    xl, xr = a[2], b[2]                                   # track
P = np.array(P)
raw = P.copy()
for j in range(4):
    P[:, j] = gaussian_filter1d(median_filter(P[:, j], 9, mode="nearest"), 3, mode="nearest")
deg = np.degrees(np.arctan(raw[:, [0, 2]]))
print(f"raw edge angles: L {deg[:,0].min():+.2f}..{deg[:,0].max():+.2f}  R {deg[:,1].min():+.2f}..{deg[:,1].max():+.2f}")
out = list(F)
for n, i in enumerate(range(i0, i1)):
    kl, ml, kr, mr = P[n]
    mx, my, s, c0 = maps(kl, ml, kr, mr, ym, y0, y1)
    out[i] = cv2.remap(F[i], mx, my, cv2.INTER_CUBIC, borderMode=cv2.BORDER_REPLICATE)
chk = []
for i in range(i0, i1, 6):
    f = cv2.cvtColor(out[i], cv2.COLOR_RGB2BGR)
    n = i - i0
    w = P[n, 3] - P[n, 1]
    c = (P[n, 1] + P[n, 3]) / 2
    sc = 1 / (1 - 0)  # widths are kept at the widest row
    (a, b), _ = edges(f, int(y0), int(y1), c - (P[n, 3] - P[n, 1]) * 0.5 - 0, c + (P[n, 3] - P[n, 1]) * 0.5, band=30)
    chk.append((np.degrees(np.arctan(a[1])), np.degrees(np.arctan(b[1]))))
chk = np.array(chk)
print(f"after (every 6th frame): L {chk[:,0].min():+.2f}..{chk[:,0].max():+.2f}  R {chk[:,1].min():+.2f}..{chk[:,1].max():+.2f}")
pr = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS),
                       "-i", "-", "-i", src, "-map", "0:v", "-map", "1:a?", "-c:v", "libx264", "-crf", "8", "-preset", "medium",
                       "-pix_fmt", "yuv420p", "-c:a", "copy", "-shortest", dst], stdin=subprocess.PIPE)
for f in out:
    pr.stdin.write(np.ascontiguousarray(f).tobytes())
pr.stdin.close(); pr.wait()
np.save(dst.replace(".mp4", "_edges.npy"), raw)
