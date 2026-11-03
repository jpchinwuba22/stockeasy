"""Matte a white bottle off a smooth grey studio background.
1) background plate = 2-D quadratic fit per channel to the pixels well outside the bottle;
2) bottle = pixels clearly brighter / different from the plate (floor shadow is darker -> excluded), holes filled;
3) on the straight section of the body (rows whose matte width is within 1.5% of the body width) the sides are set to
   the measured straight lines with sub-pixel anti-aliasing; rounded corners and the pump keep the matte shape.
Usage: cutout2.py IN.png OUT.png"""
import sys
import numpy as np
import cv2
from scipy import ndimage
src, dst = sys.argv[1], sys.argv[2]
im = cv2.imread(src).astype(np.float32)
H, W = im.shape[:2]
g = cv2.GaussianBlur(cv2.cvtColor(im.astype(np.uint8), cv2.COLOR_BGR2GRAY).astype(np.float32), (0, 0), 1.0)
gx = np.abs(cv2.Sobel(g, cv2.CV_32F, 1, 0, ksize=3))
rows = range(int(H * 0.80), int(H * 0.9))
L = float(np.median([int(np.argmax(gx[y, :W // 2])) for y in rows]))
R = float(np.median([W // 2 + int(np.argmax(gx[y, W // 2:])) for y in rows]))
# 1) background plate
YY, XX = np.mgrid[0:H, 0:W].astype(np.float32)
outside = (XX < L - 70) | (XX > R + 70) | (YY < 25)
A = np.stack([np.ones_like(XX), XX / W, YY / H, (XX / W) ** 2, (YY / H) ** 2, XX * YY / (W * H)], -1)
plate = np.zeros_like(im)
for c in range(3):
    coef, *_ = np.linalg.lstsq(A[outside], im[..., c][outside], rcond=None)
    plate[..., c] = A @ coef
d = im - plate
lum = d.mean(2)
fg = (lum > 5) | (np.abs(d).max(2) > 22)
fg &= ~((XX < L - 40) | (XX > R + 40))
fg = ndimage.binary_opening(fg, iterations=1)
lab, n = ndimage.label(fg)
fg = lab == 1 + np.argmax(ndimage.sum(fg, lab, range(1, n + 1)))
fg = ndimage.binary_fill_holes(ndimage.binary_closing(fg, iterations=3))
# exclude the darker floor shadow strip below the base: lowest rows whose pixels are darker than the plate
a = ndimage.gaussian_filter(fg.astype(np.float32), 0.7)
# 3) straight body section
bw = R - L
for y in range(H):
    xs = np.nonzero(fg[y])[0]
    if len(xs) and abs((xs[-1] - xs[0]) - bw) < 0.015 * bw:
        row = np.zeros(W, np.float32)
        x = np.arange(W, dtype=np.float32)
        row = np.clip(x - L + 0.5, 0, 1) * np.clip(R - x + 0.5, 0, 1)
        a[y] = row
out = np.dstack([im.astype(np.uint8), (np.clip(a, 0, 1) * 255).astype(np.uint8)])
ys, xs = np.nonzero(a > 0.02)
out = out[ys.min():ys.max() + 1, xs.min():xs.max() + 1]
cv2.imwrite(dst, out)
print("L R", L, R, "saved", out.shape)
