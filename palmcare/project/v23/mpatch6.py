# Molecular Glow, final: real label (true proportions, balanced on the bottle face, following its lean) over a CLEAN
# bottle plate (Flow sticker inpainted from the surrounding bottle shading - no visible rectangle), tracked per frame by
# direct ECC to the reference (chained only as the start guess), checked for tilt, smoothed.
import cv2, numpy as np, os
REF, N0, N1 = 373, 355, 392
r = cv2.imread('../remo/public/p/molecular_cut.png', cv2.IMREAD_UNCHANGED).astype(np.float32)
ref = cv2.imread(f'frm/{REF:04d}.png').astype(np.float32)
H, W = ref.shape[:2]
xl = lambda y: 296 - (y - 700) * (12 / 500)
xr = lambda y: 699 - (y - 700) * (33 / 950)
# clean plate: wipe the whole Flow sticker inside the face, inpaint at low res for smooth shading
WM = np.zeros((H, W), np.uint8)
cv2.fillConvexPoly(WM, np.int32([[xl(648) + 10, 648], [xr(648) - 10, 648], [xr(1708) - 10, 1708], [xl(1708) + 10, 1708]]), 255)
sm = cv2.resize(ref, (W // 4, H // 4), interpolation=cv2.INTER_AREA)
smm = cv2.resize(WM, (W // 4, H // 4), interpolation=cv2.INTER_NEAREST)
inp = cv2.inpaint(np.clip(sm, 0, 255).astype(np.uint8), smm, 12, cv2.INPAINT_TELEA).astype(np.float32)
inp = cv2.GaussianBlur(inp, (0, 0), 3)
plate_fill = cv2.resize(inp, (W, H), interpolation=cv2.INTER_CUBIC)
rw = np.median(r[880:980, 80:400, :3].reshape(-1, 3), 0)
ratio = np.clip(r[..., :3] / rw, 0, 1.15); ratio[r[..., 3] < 200] = 1; ratio[:, :34] = 1; ratio[:, 444:] = 1; ratio[:395] = 1; ratio[1305:] = 1
paper = (ratio.min(2) > 0.93); ratio[paper] = 1
s = (xr(1170) - xl(1170)) / 471.0
yc = (656 + 1687) / 2; ht = s * (1350 - 339); y_t, y_b = yc - ht / 2, yc + ht / 2
RL = np.float32([[0, 339], [471, 339], [471, 1350], [0, 1350]])
FL = np.float32([[xl(y_t), y_t], [xr(y_t), y_t], [xr(y_b), y_b], [xl(y_b), y_b]])
Wr = cv2.warpPerspective(ratio, np.load('H_lab373.npy'), (W, H), flags=cv2.INTER_AREA, borderValue=(1, 1, 1))   # real label in the bottle face's own perspective (anchored on the orange box)
M = cv2.GaussianBlur(WM.astype(np.float32) / 255, (0, 0), 4)
patch = ref * (1 - M[..., None]) + plate_fill * Wr * M[..., None]
M = np.clip(M * 1.0, 0, 1)
# tracking: SIFT features of Flow's own sticker + bottle, ref -> each frame directly (no chaining), RANSAC homography
sift = cv2.SIFT_create(6000)
fm = np.zeros((H, W), np.uint8); fm[560:1740, 240:780] = 255
kr, dr = sift.detectAndCompute(cv2.imread(f'frm/{REF:04d}.png', 0), fm)
HD = {}
for n in range(N0, N1):
    g = cv2.imread(f'frm/{n:04d}.png', 0)
    kn, dn = sift.detectAndCompute(g, None)
    mm = [x for x, y in cv2.BFMatcher().knnMatch(dr, dn, k=2) if x.distance < 0.75 * y.distance]
    pa = np.float32([kr[m.queryIdx].pt for m in mm]); pb = np.float32([kn[m.trainIdx].pt for m in mm])
    Hh, inl = cv2.findHomography(pa, pb, cv2.RANSAC, 3.0)
    HD[n] = Hh.astype(np.float32)
    if n % 6 == 1: print(n, 'matches', len(mm), 'inliers', int(inl.sum()))
Q = np.float32([[300, 640], [700, 640], [700, 1704], [300, 1704]]).reshape(-1, 1, 2)
C = np.array([cv2.perspectiveTransform(Q, HD[n]).reshape(-1) for n in range(N0, N1)])
k = np.array([1, 2, 3, 4, 3, 2, 1], np.float32); k /= k.sum()
Cs = np.array([np.convolve(np.pad(C[:, j], 3, mode='edge'), k, 'valid') for j in range(8)]).T
for i, n in enumerate(range(N0, N1)):
    c = Cs[i].reshape(4, 2); tilt = np.degrees(np.arctan2(c[1, 1] - c[0, 1], c[1, 0] - c[0, 0]))
    if i % 6 == 0 or n == N0: print(n, 'top-edge tilt deg', round(float(tilt), 2), 'top-left', c[0].round(0))
os.makedirs('fxm6', exist_ok=True)
for i, n in enumerate(range(N0, N1)):
    f = cv2.imread(f'frm/{n:04d}.png').astype(np.float32)
    Hn = cv2.getPerspectiveTransform(Q.reshape(-1, 2), Cs[i].reshape(4, 2).astype(np.float32))
    P = cv2.warpPerspective(patch, Hn, (W, H), flags=cv2.INTER_CUBIC, borderMode=cv2.BORDER_REPLICATE)
    m = cv2.warpPerspective(M, Hn, (W, H))[..., None]
    ring = (cv2.dilate((m[..., 0] > 0.02).astype(np.uint8), np.ones((25, 25), np.uint8)) > 0) & (m[..., 0] < 0.02)
    Pr = cv2.warpPerspective(ref, Hn, (W, H))                        # gain: frame vs warped ref just outside the patch
    gm = (f[ring].mean(0) / np.maximum(Pr[ring].mean(0), 1)) if ring.sum() > 100 else np.ones(3)
    P = P * np.clip(gm, 0.85, 1.15)
    out = f * (1 - m) + P * m + np.random.normal(0, 1.3, f.shape).astype(np.float32) * m
    cv2.imwrite(f'fxm6/{n:04d}.png', np.clip(out, 0, 255).astype(np.uint8))
print('done')
