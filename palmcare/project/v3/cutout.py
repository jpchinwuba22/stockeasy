"""Cut the straight product photo out of its grey studio background.
GrabCut (seeded with a box + certain background border) gives the silhouette; then the body is forced to the
measured straight edges (one vertical line per side, rounded corners kept from the cut), so the outline is
perfectly straight. Edge alpha is anti-aliased by guided feathering. Usage: cutout.py IN.png OUT.png"""
import sys
import numpy as np
import cv2
src, dst = sys.argv[1], sys.argv[2]
im = cv2.imread(src)
H, W = im.shape[:2]
g = cv2.cvtColor(im, cv2.COLOR_BGR2GRAY).astype(np.float32)
gx = np.abs(cv2.Sobel(cv2.GaussianBlur(g, (0, 0), 1.2), cv2.CV_32F, 1, 0, ksize=3))
# body edges: most common strongest-gradient column per side over the lower body rows
rows = range(int(H * 0.80), int(H * 0.9))      # below the label art: only the true bottle edges exist here
Ls = [int(np.argmax(gx[y, :W // 2])) for y in rows]; Rs = [W // 2 + int(np.argmax(gx[y, W // 2:])) for y in rows]
yy = np.array(list(rows), float)
kl, ml = np.polyfit(yy, Ls, 1); kr, mr = np.polyfit(yy, Rs, 1)
print("edge slopes deg", np.degrees(np.arctan(kl)), np.degrees(np.arctan(kr)))
# grabcut
mask = np.full((H, W), cv2.GC_PR_BGD, np.uint8)
x0, x1 = int(min(Ls) - 40), int(max(Rs) + 40)
mask[:, :max(0, x0 - 60)] = cv2.GC_BGD; mask[:, min(W, x1 + 60):] = cv2.GC_BGD; mask[:8] = cv2.GC_BGD; mask[-8:] = cv2.GC_BGD
mask[20:H - 60, x0:x1] = cv2.GC_PR_FGD
cxm = (np.median(Ls) + np.median(Rs)) / 2
mask[int(H * 0.3):int(H * 0.88), int(np.median(Ls)) + 20:int(np.median(Rs)) - 20] = cv2.GC_FGD
bgd, fgd = np.zeros((1, 65), np.float64), np.zeros((1, 65), np.float64)
cv2.grabCut(im, mask, None, bgd, fgd, 6, cv2.GC_INIT_WITH_MASK)
fg = np.isin(mask, (cv2.GC_FGD, cv2.GC_PR_FGD)).astype(np.uint8)
n, lab, st, _ = cv2.connectedComponentsWithStats(fg)
fg = (lab == 1 + np.argmax(st[1:, 4])).astype(np.uint8)
fg = cv2.morphologyEx(fg, cv2.MORPH_CLOSE, np.ones((5, 5), np.uint8))
# force the straight body: rows where the cut is close to the body width get exactly [L, R] (vertical lines)
Lm, Rm = float(np.median(Ls)), float(np.median(Rs)) + 1
bw = Rm - Lm
for y in range(H):
    xs = np.nonzero(fg[y])[0]
    if len(xs) and (xs[-1] - xs[0]) > 0.9 * bw:
        fg[y] = 0
        fg[y, int(round(Lm)):int(round(Rm))] = 1
a = cv2.GaussianBlur(fg.astype(np.float32), (0, 0), 0.8)
# exact sub-pixel straight edges on body rows
body = [y for y in range(H) if fg[y].sum() >= 0.9 * bw]
for y in body:
    a[y, int(Lm) - 2:int(Lm) + 3] = np.clip(np.arange(int(Lm) - 2, int(Lm) + 3) - Lm + 0.5, 0, 1)
    a[y, int(Rm) - 3:int(Rm) + 2] = np.clip(Rm - np.arange(int(Rm) - 3, int(Rm) + 2) - 0.5, 0, 1)
out = np.dstack([im, (np.clip(a, 0, 1) * 255).astype(np.uint8)])
ys, xs = np.nonzero(a > 0.02)
out = out[ys.min():ys.max() + 1, xs.min():xs.max() + 1]
cv2.imwrite(dst, out)
print("saved", out.shape, "body rows", len(body), "width", bw)
