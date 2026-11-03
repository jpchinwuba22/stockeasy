"""Make a bottle cutout a true rectangle: rows of the body that flare wider than the straight lower body are scaled
back (about the body axis) to exactly the body width. Pump/cap rows are untouched."""
import sys
import numpy as np
import cv2
from PIL import Image
src, dst = sys.argv[1], sys.argv[2]
im = np.asarray(Image.open(src).convert("RGBA")).astype(np.float32)
a = im[..., 3] > 128
H, W = a.shape
L = np.full(H, -1.0); R = np.full(H, -1.0)
for y in range(H):
    xs = np.nonzero(a[y])[0]
    if len(xs): L[y], R[y] = xs[0], xs[-1]
w = R - L
lower = slice(int(H * 0.5), int(H * 0.9))
bw = np.median(w[lower]); bc = np.median((L[lower] + R[lower]) / 2)
body = np.nonzero(w > 0.85 * bw)[0]
y0 = body[0]
print("body width", bw, "axis", bc, "body starts", y0, "max flare", w[body].max() - bw)
mx = np.tile(np.arange(W, dtype=np.float32), (H, 1)); my = np.repeat(np.arange(H, dtype=np.float32)[:, None], W, 1)
for y in range(y0, H):
    if w[y] > bw + 0.5 and w[y] > 0.85 * bw:
        s = w[y] / bw                     # >1: sample wider source into body width
        c = (L[y] + R[y]) / 2
        mx[y] = c + (np.arange(W) - bc) * s
out = cv2.remap(im, mx, my, cv2.INTER_CUBIC, borderMode=cv2.BORDER_CONSTANT, borderValue=0)
# nothing of the body may stick out past the straight body edges (shoulder lips above the corrected rows)
lo, hi = int(round(bc - bw / 2)) - 1, int(round(bc + bw / 2)) + 2
out[max(0, y0 - 80):, :max(0, lo), 3] = 0
out[max(0, y0 - 80):, hi:, 3] = 0
Image.fromarray(np.clip(out, 0, 255).astype(np.uint8), "RGBA").save(dst)
b = out[..., 3] > 128
ws = [np.ptp(np.nonzero(b[y])[0]) for y in range(y0, int(H * 0.95)) if b[y].any()]
print("after: width range over body", min(ws), max(ws))
