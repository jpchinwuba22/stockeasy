"""Clamp a matted bottle to its straight body: every row at/below the shoulder (matte width > 85% of the body) loses any
pixels outside the body's straight left/right edges. Rounded corners are inside the edges and are kept. Usage: IN OUT"""
import sys
import numpy as np
from PIL import Image
im = np.asarray(Image.open(sys.argv[1]).convert("RGBA")).astype(np.float32)
a = im[..., 3] / 255
H, W = a.shape
rows = [(y, np.nonzero(a[y] > 0.5)[0]) for y in range(H)]
low = [(y, xs) for y, xs in rows if len(xs) and int(H * 0.55) <= y <= int(H * 0.9)]
Lm = float(np.median([xs[0] for _, xs in low])); Rm = float(np.median([xs[-1] + 1 for _, xs in low]))
bw = Rm - Lm
x = np.arange(W, dtype=np.float32)
inside = np.clip(x - Lm + 0.5, 0, 1) * np.clip(Rm - x + 0.5, 0, 1)
n = 0
wide = [len(xs) > 0 and (xs[-1] - xs[0]) > 0.85 * bw for _, xs in rows]
ys0 = H - 1
while ys0 > 0 and wide[ys0 - 1] or (ys0 > 0 and not wide[ys0]):
    ys0 -= 1
for y, xs in rows:
    if y >= ys0 and len(xs) and (xs[-1] - xs[0]) > 0.85 * bw:
        a[y] = np.minimum(a[y], inside); n += 1
im[..., 3] = a * 255
Image.fromarray(np.clip(im, 0, 255).astype(np.uint8), "RGBA").save(sys.argv[2])
out = np.asarray(Image.open(sys.argv[2]))[..., 3] > 128
ws = [np.ptp(np.nonzero(out[y])[0]) for y in range(H) if out[y].sum() > 0.85 * bw]
print(sys.argv[2], "edges", Lm, Rm, "rows clamped", n, "body width range", min(ws), max(ws))
