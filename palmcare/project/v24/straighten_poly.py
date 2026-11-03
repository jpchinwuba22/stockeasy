# Level the real jar label WITHOUT changing letter shapes: one smooth displacement field (cubic in x, linear in y)
# least-squares fitted to the measured baselines of every line on the phone photo (the label's lower right curls up).
# No piecewise kinks, so glyphs keep their exact form. Real pixels only.
import cv2, numpy as np
D = '/tmp/claude-0/-home-user-stockeasy/ae1b3550-c976-5b71-9f6e-2d57965fb3f7/scratchpad/'
j = cv2.imread(D + 'v24/jar_cut_orig.png', -1).astype(np.float32)
h, w = j.shape[:2]
# (x, y on photo, y target) - baselines read off the gridded close-up
P = [(229, 509, 507.5), (491, 506, 507.5),                                       # PalmCare
     (330, 539, 539), (480, 539, 539),                                           # VITAMIN C
     (227, 571, 571), (350, 569, 571), (479, 562, 571),                          # FACE MOISTURISER
     (227, 579, 579), (350, 575, 579), (460, 562, 579), (535, 550, 579), (591, 532, 579),   # rule
     (229, 600, 600), (350, 598, 600), (460, 594, 600), (491, 584, 600), (540, 572, 600), (591, 553, 600),  # Brightening..
     (229, 625, 625), (391, 624, 625),                                           # 30 mL
     (60, 470, 470), (60, 620, 620), (150, 470, 470), (150, 620, 620)]           # leaf column stays put
P = np.array(P, np.float64)
X, Ys, Yt = P[:, 0] / w, P[:, 1] / h, P[:, 2] / h
def basis(x, y): return np.stack([np.ones_like(x), x, x**2, x**3, y, x*y, x**2*y, x**3*y, x**2*y**2, x**3*y**2, x**4*y], -1)
# solve for d(x, y_target) = y_src - y_target
c, *_ = np.linalg.lstsq(basis(X, Yt), (Ys - Yt), rcond=None)
print('fit residual px', np.round((basis(X, Yt) @ c - (Ys - Yt)) * h, 1))
xx, yy = np.meshgrid(np.arange(w, dtype=np.float64) / w, np.arange(h, dtype=np.float64) / h)
d = basis(xx, yy) @ c
wy = np.clip((yy * h - 430) / 30, 0, 1)                                         # collar / lid untouched
my = (yy * h + d * h * wy).astype(np.float32); mx = (xx * w).astype(np.float32)
out = cv2.remap(np.ascontiguousarray(j), mx, my, cv2.INTER_CUBIC, borderMode=cv2.BORDER_REPLICATE)
cv2.imwrite(D + 'v24/jar_straight.png', np.clip(out, 0, 255).astype(np.uint8))
