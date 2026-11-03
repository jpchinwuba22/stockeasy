"""Lock the straight body sides of a matted bottle to exact vertical lines (sub-pixel AA), only on rows where the
matte is within 1.5% of the body width, so rounded corners and the pump keep their true shape. Usage: IN OUT"""
import sys
import numpy as np
from PIL import Image
im = np.asarray(Image.open(sys.argv[1]).convert("RGBA")).astype(np.float32)
a = im[..., 3] / 255
from scipy import ndimage
a = ndimage.grey_erosion(a, size=(5, 5))          # drop the 2-px dark studio rim all round
H, W = a.shape
L = np.full(H, np.nan); R = np.full(H, np.nan)
for y in range(H):
    xs = np.nonzero(a[y] > 0.5)[0]
    if len(xs): L[y], R[y] = xs[0], xs[-1] + 1
w = R - L
low = slice(int(H * 0.6), int(H * 0.9))
bw = np.nanmedian(w[low]); Lm = np.nanmedian(L[low]) + 1; Rm = np.nanmedian(R[low]) - 3   # inside the dark rim
x = np.arange(W, dtype=np.float32)
locked = 0
for y in range(H):
    if not np.isnan(w[y]) and abs(w[y] - bw) <= 0.015 * bw:
        a[y] = np.clip(x - Lm + 0.5, 0, 1) * np.clip(Rm - x + 0.5, 0, 1); locked += 1
im[..., 3] = a * 255
ys, xs = np.nonzero(a > 0.01)
out = im[ys.min():ys.max() + 1, xs.min():xs.max() + 1]
Image.fromarray(np.clip(out, 0, 255).astype(np.uint8), "RGBA").save(sys.argv[2])
print(sys.argv[2], "body width", bw, "edges", Lm, Rm, "rows locked", locked, "of", H)
