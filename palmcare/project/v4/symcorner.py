"""Make a straight bottle's rounded corners symmetric: for every body row, both sides get the larger of the two insets
(measured from the straight body edges), so the shoulder and base round identically left and right. Usage: IN OUT"""
import sys
import numpy as np
from PIL import Image
im = np.asarray(Image.open(sys.argv[1]).convert("RGBA")).astype(np.float32)
a = im[..., 3] / 255
H, W = a.shape
low = [y for y in range(int(H * 0.55), int(H * 0.9)) if (a[y] > 0.5).any()]
Lm = float(np.median([np.nonzero(a[y] > 0.5)[0][0] for y in low])); Rm = float(np.median([np.nonzero(a[y] > 0.5)[0][-1] + 1 for y in low]))
bw = Rm - Lm
x = np.arange(W, dtype=np.float32)
wide = [(a[y] > 0.5).sum() > 0.7 * bw for y in range(H)]
y1 = max(y for y in range(H) if wide[y])
y0 = y1
while y0 > 0 and wide[y0 - 1]:
    y0 -= 1
for y in range(y0, y1 + 1):
    xs = np.nonzero(a[y] > 0.5)[0]
    if not len(xs):
        continue
    il, ir = max(0.0, xs[0] - Lm), max(0.0, Rm - (xs[-1] + 1))
    ins = max(il, ir)
    if ins > 0.5 and (y - y0 < 80 or y1 - y < 80):          # only in the corner zones, never the pump
        a[y] = np.minimum(a[y], np.clip(x - (Lm + ins) + 0.5, 0, 1) * np.clip((Rm - ins) - x + 0.5, 0, 1))
im[..., 3] = a * 255
Image.fromarray(np.clip(im, 0, 255).astype(np.uint8), "RGBA").save(sys.argv[2])
print("ok", Lm, Rm, y0, y1)
